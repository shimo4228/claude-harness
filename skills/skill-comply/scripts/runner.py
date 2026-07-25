"""Run scenarios via claude -p and parse tool calls from stream-json output."""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from scripts.parser import ObservationEvent
from scripts.scenario_generator import Scenario

SANDBOX_BASE = Path("/tmp/skill-comply-sandbox")
ALLOWED_MODELS = frozenset({"haiku", "sonnet", "opus"})
MAX_SKILL_FILE_SIZE = 512 * 1024  # 512 KB
DEFAULT_TIMEOUT_SECONDS = 3600


@dataclass(frozen=True)
class ScenarioRun:
    scenario: Scenario
    observations: tuple[ObservationEvent, ...]
    sandbox_dir: Path
    timed_out: bool = False


#: Tools the child agent may use without a permission prompt. Bash is NOT here.
#:
#: `--allowedTools` in `-p` mode is a whitelist *plus* auto-approval, and the
#: prompt handed to the child is LLM output derived from the audited .md file's
#: raw body — so with Bash on this list, an instruction smuggled through that
#: file executes as the user with no human in the loop, unattended (security scan
#: F3/F4/F18, 2026-07-25). `cwd` and `--add-dir` widen access; they do not confine
#: it, and Bash reaches every path the user can.
#:
#: Bash is available with `--allow-bash` for the specs that genuinely need it
#: (a skill whose compliance is "did it run the tests" cannot be measured
#: without it). Opt-in is the point: routine periodic maintenance runs safe.
DEFAULT_ALLOWED_TOOLS = "Read,Write,Edit,Glob,Grep"
BASH_ALLOWED_TOOLS = "Read,Write,Edit,Bash,Glob,Grep"


def run_scenario(
    scenario: Scenario,
    model: str = "sonnet",
    max_turns: int = 30,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    allow_bash: bool = False,
) -> ScenarioRun:
    """Execute a scenario and extract tool calls from stream-json output.

    On timeout, partial stdout captured so far is parsed and returned so
    the grader can still classify whatever tool calls completed before
    the cutoff. `ScenarioRun.timed_out=True` signals the truncation.
    """
    if model not in ALLOWED_MODELS:
        raise ValueError(f"Unknown model: {model!r}. Allowed: {ALLOWED_MODELS}")

    sandbox_dir = _safe_sandbox_dir(scenario.id)
    _setup_sandbox(sandbox_dir, scenario)

    cmd = [
        "claude",
        "-p",
        scenario.prompt,
        "--model",
        model,
        "--max-turns",
        str(max_turns),
        "--add-dir",
        str(sandbox_dir),
        "--allowedTools",
        BASH_ALLOWED_TOOLS if allow_bash else DEFAULT_ALLOWED_TOOLS,
        "--output-format",
        "stream-json",
        "--verbose",
    ]

    timed_out = False
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=sandbox_dir,
        )
        stdout = result.stdout
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        raw = exc.stdout or ""
        stdout = raw.decode() if isinstance(raw, bytes) else raw
        print(
            f" [timeout after {timeout}s, parsing partial output]",
            file=sys.stderr,
            flush=True,
        )

    observations = _parse_stream_json(stdout)

    return ScenarioRun(
        scenario=scenario,
        observations=tuple(observations),
        sandbox_dir=sandbox_dir,
        timed_out=timed_out,
    )


def _safe_sandbox_dir(scenario_id: str) -> Path:
    """Sanitize scenario ID and ensure path stays within sandbox base."""
    safe_id = re.sub(r"[^a-zA-Z0-9\-_]", "_", scenario_id)
    path = SANDBOX_BASE / safe_id
    path.resolve().relative_to(SANDBOX_BASE.resolve())
    return path


def _contained(sandbox_dir: Path, raw: str) -> Path | None:
    """Resolve `raw` against the sandbox, or None if it escapes.

    Resolution is done on the real path (symlinks followed), so a link planted
    inside the sandbox cannot be used as a door out of it.
    """
    base = sandbox_dir.resolve()
    candidate = Path(raw)
    target = candidate if candidate.is_absolute() else base / candidate
    # The target usually does not exist yet, so resolve its nearest existing
    # ancestor and re-attach the remainder.
    probe, tail = target, []
    while not probe.exists() and probe != probe.parent:
        tail.append(probe.name)
        probe = probe.parent
    resolved = probe.resolve().joinpath(*reversed(tail))
    return resolved if resolved == base or base in resolved.parents else None


def _apply_setup_commands(sandbox_dir: Path, commands: Iterable[str]) -> list[str]:
    """Build the sandbox skeleton from `commands`. Returns the refused ones.

    **Nothing here executes a process.** `commands` is LLM output derived from the
    audited .md file's raw body, so treating it as executable made any third-party
    skill a command-execution vector (security scan F2, 2026-07-25): one
    `bash -c 'curl … | sh'` entry ran on the host before the scenario started.

    What the commands are actually for is creating directories and empty files,
    and that needs no shell. Two verbs are interpreted with pathlib — `mkdir` and
    `touch` — with every path required to resolve inside the sandbox. Everything
    else is refused and returned to the caller for reporting; a refusal is data
    about the generated scenario, not an error to raise.

    The allowlist stays at two verbs deliberately. Widening it to "commands that
    look harmless" is how this class of hole reopens.
    """
    refused: list[str] = []
    for cmd in commands:
        try:
            parts = shlex.split(cmd)
        except ValueError:
            refused.append(cmd)
            continue
        if not parts:
            continue
        verb, args = parts[0], [a for a in parts[1:] if not a.startswith("-")]
        if verb not in ("mkdir", "touch") or not args:
            refused.append(cmd)
            continue
        targets = [_contained(sandbox_dir, a) for a in args]
        if any(t is None for t in targets):
            refused.append(cmd)
            continue
        for target in targets:
            assert target is not None  # narrowed by the check above
            if verb == "mkdir":
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch(exist_ok=True)
    return refused


def _setup_sandbox(sandbox_dir: Path, scenario: Scenario) -> None:
    """Create the sandbox directory and build its skeleton."""
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True)

    subprocess.run(["git", "init"], cwd=sandbox_dir, capture_output=True)

    refused = _apply_setup_commands(sandbox_dir, scenario.setup_commands)
    for cmd in refused:
        print(
            f"  [setup refused] {cmd!r} — only `mkdir`/`touch` inside the sandbox run",
            file=sys.stderr,
        )


TEXT_EVENT_MAX_CHARS = 2000


def _parse_stream_json(stdout: str) -> list[ObservationEvent]:
    """Parse claude -p stream-json output into ObservationEvents.

    Stream-json format:
    - type=assistant with content[].type=tool_use → tool call (name, input)
    - type=assistant with content[].type=text → assistant reasoning, captured
      as a pseudo-event with tool="Text" so the classifier can match steps
      whose detector depends on natural-language output (verdicts, plans).
    - type=user with content[].type=tool_result → tool result (output)
    """
    events: list[ObservationEvent] = []
    pending: dict[str, dict] = {}
    event_counter = 0

    for line in stdout.strip().splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = msg.get("type")

        if msg_type == "assistant":
            content = msg.get("message", {}).get("content", [])
            session_id = msg.get("session_id", "unknown")
            for block in content:
                block_type = block.get("type")
                if block_type == "tool_use":
                    tool_use_id = block.get("id", "")
                    tool_input = block.get("input", {})
                    input_str = (
                        json.dumps(tool_input)[:5000]
                        if isinstance(tool_input, dict)
                        else str(tool_input)[:5000]
                    )
                    pending[tool_use_id] = {
                        "tool": block.get("name", "unknown"),
                        "input": input_str,
                        "order": event_counter,
                    }
                    event_counter += 1
                elif block_type == "text":
                    text_content = block.get("text", "")
                    if text_content.strip():
                        events.append(
                            ObservationEvent(
                                timestamp=f"T{event_counter:04d}",
                                event="text_output",
                                tool="Text",
                                session=session_id,
                                input="",
                                output=text_content[:TEXT_EVENT_MAX_CHARS],
                            )
                        )
                        event_counter += 1

        elif msg_type == "user":
            content = msg.get("message", {}).get("content", [])
            if isinstance(content, list):
                for block in content:
                    tool_use_id = block.get("tool_use_id", "")
                    if tool_use_id in pending:
                        info = pending.pop(tool_use_id)
                        output_content = block.get("content", "")
                        if isinstance(output_content, list):
                            output_str = json.dumps(output_content)[:5000]
                        else:
                            output_str = str(output_content)[:5000]

                        events.append(
                            ObservationEvent(
                                timestamp=f"T{info['order']:04d}",
                                event="tool_complete",
                                tool=info["tool"],
                                session=msg.get("session_id", "unknown"),
                                input=info["input"],
                                output=output_str,
                            )
                        )

    for _tool_use_id, info in pending.items():
        events.append(
            ObservationEvent(
                timestamp=f"T{info['order']:04d}",
                event="tool_complete",
                tool=info["tool"],
                session="unknown",
                input=info["input"],
                output="",
            )
        )

    return sorted(events, key=lambda e: e.timestamp)

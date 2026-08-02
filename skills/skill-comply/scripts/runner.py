"""Run scenarios via claude -p and parse tool calls from stream-json output."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from scripts.child_settings import child_settings
from scripts.parser import ObservationEvent
from scripts.scenario_generator import Scenario

SANDBOX_BASE = Path("/tmp/skill-comply-sandbox")
ALLOWED_MODELS = frozenset({"haiku", "sonnet", "opus", "fable"})
DEFAULT_TIMEOUT_SECONDS = 3600


@dataclass(frozen=True)
class ScenarioRun:
    scenario: Scenario
    observations: tuple[ObservationEvent, ...]
    sandbox_dir: Path
    timed_out: bool = False


class ScenarioExecutionError(RuntimeError):
    """Raised when the child left no trace to grade.

    Zero observations grade as 0% (`classify_events` short-circuits to `{}` on an
    empty trace without calling any model, and the grader divides by the required
    step count) — a broken measurement wearing the costume of a real result. Same
    reasoning as `ClassificationParseError` in classifier.py: "nothing was found"
    and "nothing could be looked at" must not print the same number.

    The condition is emptiness alone. An earlier version required a non-zero exit
    as well, which left three routes open: a clean exit with empty stdout, a clean
    exit with unparseable stdout, and — the one that matters in practice — a
    timeout, since `returncode` keeps its initialiser on that branch. A child
    killed at the hour mark with nothing on stdout was reported as `0%`.

    A non-zero exit that still produced a trace is NOT an error: a child cut short
    by `--max-turns` did real work, and grading it is honest. Only emptiness is
    fabricated.

    Rate limiting is the common cause and is NOT retried here — per
    rules/common/debugging.md a burst of rate limits is a policy signal to
    surface to a human, not something to back off through.
    """


#: Tools auto-approved for the child, so it is not left waiting on a prompt
#: nobody can answer.
#:
#: **This list does not confine anything** — see `child_settings.DENIED_TOOLS`.
#: `--allowedTools` grants auto-approval; it does not remove the tools left off
#: it. Containment comes from `permissions.deny`, passed via `--settings`.
DEFAULT_ALLOWED_TOOLS = "Read,Write,Edit,Glob,Grep"
BASH_ALLOWED_TOOLS = "Read,Write,Edit,Bash,Glob,Grep"


def run_scenario(
    scenario: Scenario,
    model: str = "sonnet",
    max_turns: int = 30,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    allow_bash: bool = False,
    skill_payload: tuple[str, str] | None = None,
) -> ScenarioRun:
    """Execute a scenario and extract tool calls from stream-json output.

    On timeout, partial stdout captured so far is parsed and returned so
    the grader can still classify whatever tool calls completed before
    the cutoff. `ScenarioRun.timed_out=True` signals the truncation.
    """
    if model not in ALLOWED_MODELS:
        raise ValueError(f"Unknown model: {model!r}. Allowed: {ALLOWED_MODELS}")

    sandbox_dir = safe_sandbox_dir(scenario.id)
    _setup_sandbox(sandbox_dir, scenario)
    if skill_payload is not None:
        place_skill(sandbox_dir, skill_payload)

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
        # The actual containment. Not `pin_output_style` — what this child
        # inherits from the user's configuration is what is under measurement.
        "--settings",
        child_settings(allow_bash=allow_bash),
        "--output-format",
        "stream-json",
        "--verbose",
    ]

    timed_out = False
    returncode = 0
    stderr = ""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=sandbox_dir,
        )
        stdout = result.stdout
        returncode = result.returncode
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        raw = exc.stdout or ""
        stdout = raw.decode() if isinstance(raw, bytes) else raw
        raw_err = exc.stderr or ""
        stderr = raw_err.decode() if isinstance(raw_err, bytes) else raw_err
        print(
            f" [timeout after {timeout}s, parsing partial output]",
            file=sys.stderr,
            flush=True,
        )

    observations = _parse_stream_json(stdout)

    if not observations:
        cause = (
            f"timed out after {timeout}s leaving no partial output"
            if timed_out
            else f"exited {returncode} with nothing parsable on stdout"
        )
        raise ScenarioExecutionError(
            f"scenario {scenario.id!r}: claude -p {cause}; stderr: {stderr.strip()[:500]!r}"
        )

    return ScenarioRun(
        scenario=scenario,
        observations=tuple(observations),
        sandbox_dir=sandbox_dir,
        timed_out=timed_out,
    )


def sanitize_sandbox_id(scenario_id: str) -> str:
    """The directory name a scenario id maps to — "" when it maps to nothing.

    Exposed separately because callers need to compare scenario ids by the
    directory they will actually land in, not by the raw string: `task/a` and
    `task_a` are two ids and one directory.
    """
    return re.sub(r"[^a-zA-Z0-9\-_]", "_", scenario_id)


def safe_sandbox_dir(scenario_id: str) -> Path:
    """Give a scenario its own directory under SANDBOX_BASE.

    An id that sanitizes to the empty string collapses the path onto
    SANDBOX_BASE itself, and the containment check below still passes — a
    directory is trivially inside itself. `_setup_sandbox` would then hand
    `shutil.rmtree` the root holding every other scenario's sandbox. Reject it
    here rather than trust each caller to remember.
    """
    safe_id = sanitize_sandbox_id(scenario_id)
    if not safe_id:
        raise ValueError(f"scenario id {scenario_id!r} leaves no usable sandbox name")
    path = SANDBOX_BASE / safe_id
    path.resolve().relative_to(SANDBOX_BASE.resolve())
    return path


def _contained(sandbox_dir: Path, raw: str) -> Path | None:
    """Resolve `raw` against the sandbox, or None if it escapes.

    Two escape routes have to be closed, and they need different tools.

    **`..` segments** are collapsed lexically with `normpath` before anything
    else. The probe loop below only resolves the nearest *existing* ancestor and
    re-attaches the rest of the path verbatim, so a `..` left in that tail
    survives into `resolved` — and `Path.parents` never normalises, so it reads
    the `..` as an ordinary directory name and still finds `base` in the chain.
    `a/../../../elsewhere/x` was therefore accepted and created (verified
    2026-08-01). The sandbox is rmtree'd and recreated empty immediately before
    setup, so the first component never exists and the probe always walked all
    the way back to base: the hole was open on every call.

    The order matters and is not interchangeable. `_contained` returns the
    normalised path and the caller creates *that*, so the kernel never sees the
    original string — there is no textual-vs-kernel discrepancy left to exploit.
    Resolving first and normalising after would reopen the hole.

    **Symlinks** are handled by the probe loop, which resolves the real path, so
    a link planted inside the sandbox is not a door out of it. The loop tests
    `lexists`, not `exists`: a *dangling* link reads as absent under `exists`, so
    it would fall into the unresolved tail and `touch` would follow it to create
    a file at the link's target, outside the sandbox. Nothing in the untrusted
    path can plant a symlink (the sandbox is recreated empty and the two verbs
    cannot make one), so this is only reachable by something that can already
    write inside SANDBOX_BASE — but it is the exact boundary the symlink test
    claims is closed, so it is closed here rather than argued about. `normpath`
    alone
    would not catch that — it is purely textual and would happily keep a
    symlinked path looking contained. Hence both, in this order.
    """
    base = sandbox_dir.resolve()
    candidate = Path(raw)
    target = candidate if candidate.is_absolute() else base / candidate
    target = Path(os.path.normpath(target))
    # The target usually does not exist yet, so resolve its nearest existing
    # ancestor and re-attach the remainder.
    probe, tail = target, []
    while not os.path.lexists(probe) and probe != probe.parent:
        tail.append(probe.name)
        probe = probe.parent
    resolved = probe.resolve().joinpath(*reversed(tail))
    return resolved if resolved == base or base in resolved.parents else None


#: The sandbox is the child's PROJECT ROOT, and inside a project root some
#: filenames are not inert — they are loaded as configuration or as
#: instructions. `_contained` answers "is this path inside the sandbox"; it
#: cannot answer "will anything downstream interpret it". Those are different
#: properties and this is the second one.
#:
#: Measured 2026-08-02 on Claude Code 2.1.220, in a sandbox never opened
#: interactively:
#:
#: - `<sandbox>/.claude/settings.json` carrying a `hooks.SessionStart` entry ran
#:   its command on the host, silently. Note the asymmetry: a `permissions.allow`
#:   entry in the SAME file was refused out loud ("this workspace has not been
#:   trusted"), while the `hooks` block in it ran anyway. The trust gate covers
#:   permissions, not hooks.
#: - `<sandbox>/CLAUDE.md` was loaded and obeyed — a planted token came back in
#:   the answer to an unrelated prompt.
#:
#: The child cannot do this to itself: Claude Code refuses a child's Write to
#: `.claude/settings.json` (measured — a normal file and `CLAUDE.md` both wrote
#: fine, that one path was denied). **But this tool's own writes are pathlib, not
#: the child's Write tool, so that guard does not cover them.** Anything we place
#: in the sandbox on behalf of an audited document has to be checked here.
#:
#: `.claude/` is reserved outright rather than filtered by name: the set of
#: filenames Claude Code loads from it is owned by an external product and grows.
#: A prefix this tool owns is a closed set; a list of names to avoid is not. The
#: basenames below are the same hazard outside that prefix, and that list *is*
#: known to rot — re-check it when Claude Code changes its config surface.
#: `.git` is here for the same structural reason as `.claude`, and it is easy to
#: miss because git is not the product this tool is about. `_setup_sandbox` runs
#: `git init` two lines before untrusted writes land, so `.git/` exists and is
#: writable. `core.fsmonitor`, `core.pager`, `core.sshCommand` and `alias.*` are
#: plain config STRINGS that git executes — no executable bit involved, so the
#: unconditional `chmod(0o644)` does not reach them. Measured 2026-08-02:
#: `files: {".git/config": "[core]\\n\\tfsmonitor = touch /tmp/PWNED\\n"}` was
#: accepted, and `git status` in that directory ran the command on the host.
#: Claude Code runs git in the workspace to build context, so this fires with
#: Bash denied.
RESERVED_PREFIXES = frozenset({".claude", ".git"})
RESERVED_BASENAMES = frozenset(
    {
        "claude.md",
        "agents.md",
        ".mcp.json",
        "settings.json",
        "settings.local.json",
        ".gitignore",
    }
)
#: `.gitignore` is not code execution — it is measurement corruption. Grep honours
#: it and Glob does not (A/B tested against a real child, 2026-08-02: with
#: `src/\\n*.py` ignored, Glob still listed `src/calc.py` while Grep reported "No
#: files found"). An audited document can hide its own fixtures from exactly the
#: tool a detector expects the agent to use, so the step fails as "the agent did
#: not do it" rather than "this could not be observed".


def _reserved_reason(sandbox_dir: Path, target: Path) -> str | None:
    """Why `target` may not be written, or None if it may.

    **Case-folded, because the filesystem is.** APFS and NTFS are
    case-insensitive, so `.CLAUDE/Settings.json` is written and then read back as
    `.claude/settings.json` — one file, two spellings. A case-sensitive
    comparison here let that through both guards; measured 2026-08-02, a real
    child then ran the `hooks.SessionStart` command in it on the host, with Bash
    denied. This is the same lesson as `run._collision_key`, learned separately
    and not carried across: an instance was fixed, the class was not.

    Fails **closed** on a path outside the sandbox. Today `_contained` always
    runs first so that branch is unreachable, but a helper guarding command
    execution should not answer "go ahead" to a question it did not understand.
    """
    try:
        relative = target.relative_to(sandbox_dir.resolve())
    except ValueError:
        return "does not resolve inside the sandbox"
    folded = {part.casefold() for part in relative.parts}
    reserved = folded & RESERVED_PREFIXES
    if reserved:
        return f"`{sorted(reserved)[0]}/` is reserved — the tool owns it, the document does not"
    if target.name.casefold() in RESERVED_BASENAMES:
        return f"`{target.name}` is loaded as configuration or instructions, not as a fixture"
    return None


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
            refused.append(f"{cmd} — unparsable")
            continue
        if not parts:
            continue
        verb, args = parts[0], [a for a in parts[1:] if not a.startswith("-")]
        if verb not in ("mkdir", "touch") or not args:
            refused.append(f"{cmd} — only `mkdir` and `touch` are interpreted")
            continue
        targets = [_contained(sandbox_dir, a) for a in args]
        if any(t is None for t in targets):
            refused.append(f"{cmd} — resolves outside the sandbox")
            continue
        # Containment is not enough — see RESERVED_PREFIXES. A path can be inside
        # the sandbox and still be loaded as configuration by the child.
        reasons = [r for t in targets if t is not None and (r := _reserved_reason(sandbox_dir, t))]
        if reasons:
            refused.append(f"{cmd} — {reasons[0]}")
            continue
        for target in targets:
            assert target is not None  # narrowed by the check above
            if verb == "mkdir":
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch(exist_ok=True)
    return refused


#: Bounds on `files:`. The content is LLM output derived from the audited
#: document, so it is untrusted text going to an untrusted-but-confined path;
#: caps keep a generated scenario from filling the disk.
MAX_FILE_BYTES = 256 * 1024
MAX_FILE_COUNT = 40


def _apply_files(sandbox_dir: Path, files: Iterable[tuple[str, str]]) -> list[str]:
    """Write fixture files. Returns the refused ones, with reasons.

    **No process is started here either**, which is the property `setup_commands`
    protects and this must not break. What it adds is content, and content is not
    the hazard — *interpretation* is. A file is refused when it escapes the
    sandbox (`_contained`) or when it lands somewhere the child would read as
    configuration or instructions (`_reserved_reason`), which is a different
    question from location and needs its own check.

    The executable bit is never set: with Bash denied a script here is inert, and
    with `--allow-bash` it would be a payload. That is a combination to keep
    impossible rather than to reason about.
    """
    refused: list[str] = []
    for index, (raw_path, content) in enumerate(files):
        if index >= MAX_FILE_COUNT:
            refused.append(f"{raw_path!r} — over the {MAX_FILE_COUNT} file cap")
            continue
        if Path(raw_path).is_absolute():
            refused.append(f"{raw_path!r} — must be relative to the sandbox")
            continue
        target = _contained(sandbox_dir, raw_path)
        if target is None:
            refused.append(f"{raw_path!r} — resolves outside the sandbox")
            continue
        reason = _reserved_reason(sandbox_dir, target)
        if reason:
            refused.append(f"{raw_path!r} — {reason}")
            continue
        encoded = content.encode()
        if len(encoded) > MAX_FILE_BYTES:
            refused.append(f"{raw_path!r} — {len(encoded)} bytes, over the {MAX_FILE_BYTES} cap")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        target.chmod(0o644)
    return refused


def place_skill(sandbox_dir: Path, payload: tuple[str, str]) -> Path:
    """Put a SKILL.md where the child will discover it.

    `<sandbox>/.claude/skills/<name>/SKILL.md` is the only location that produces
    discovery — verified 2026-08-01: a child whose cwd is the sandbox found and
    invoked a skill placed there, with no `--add-dir` beyond the sandbox and no
    Bash.

    This is the one writer allowed into the reserved `.claude/` prefix. Everything
    derived from the audited document — `setup_commands`, and later `files:` — is
    refused there, because the child loads configuration from that directory (see
    RESERVED_PREFIXES). The tool may write it; the document may not ask for it.
    """
    name, text = payload
    safe_name = sanitize_sandbox_id(name)
    if not safe_name:
        raise ValueError(f"skill name {name!r} leaves no usable directory name")
    skill_dir = sandbox_dir / ".claude" / "skills" / safe_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    path = skill_dir / "SKILL.md"
    path.write_text(text)
    return path


def _setup_sandbox(sandbox_dir: Path, scenario: Scenario) -> None:
    """Create the sandbox directory and build its skeleton."""
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True)

    subprocess.run(["git", "init"], cwd=sandbox_dir, capture_output=True)

    refused = _apply_setup_commands(sandbox_dir, scenario.setup_commands)
    refused += _apply_files(sandbox_dir, scenario.files)
    for cmd in refused:
        print(f"  [setup refused] {cmd!r}", file=sys.stderr, flush=True)


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

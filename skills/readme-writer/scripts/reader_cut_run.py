"""Run one arm of the reader-cut pilot: build the cutter prompt, call the model, parse
the per-unit verdicts fail-loud. Plan: docs/plans/reader-cut-pilot.html claim 2.

The model call is the only I/O and sits behind `Runner` so tests pass a fake. A parse
that does not cover exactly the asked units raises — a silent `{}` would read as
"cut nothing" and the score would report a dead instrument as a result.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

VERDICTS = ("CUT", "CONDENSE", "PRESERVE")
_ROW_RE = re.compile(r"^\s*(\d+)\s*[\t ]\s*(CUT|CONDENSE|PRESERVE)\b[\t ]*(.*)$")
_TODO = "{{TODO"
_NO_READER = "（指定なし。一般の読者として読む）"

Runner = Callable[["Arm", str], str]


class ParseError(ValueError):
    pass


class ReaderNotReady(RuntimeError):
    pass


@dataclass(frozen=True)
class Arm:
    name: str
    reader: str  # path relative to prompt/, "" = no reader
    view: str  # "full" | "forward"
    runner: str  # "claude" | "codex"
    model: str


def load_arms(path: Path) -> dict[str, Arm]:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return {
        name: Arm(name, t.get("reader", ""), t["view"], t["runner"], t.get("model", ""))
        for name, t in raw.items()
    }


def reader_text(arm: Arm, prompt_dir: Path) -> str:
    if not arm.reader:
        return _NO_READER
    text = (prompt_dir / arm.reader).read_text(encoding="utf-8").strip()
    if _TODO in text or not text:
        raise ReaderNotReady(f"{arm.reader} is still a placeholder; the judge writes it")
    return text


def _numbered(units: list[dict]) -> str:
    return "\n".join(f"{u['i']}\t{u['text']}" for u in units)


def _fill(template: str, reader: str, context: str, units: list[dict]) -> str:
    block = f"# ここまでに読んだ部分（判定しない）\n{context}\n\n" if context else ""
    return (
        template.replace("{reader}", reader)
        .replace("{context}", block)
        .replace("{units}", _numbered(units))
    )


def build_prompts(
    units: list[dict], arm: Arm, template: str, reader: str
) -> list[tuple[list[int], str]]:
    """(unit indices asked, prompt) pairs: one for a full view, one per section for
    the forward view (context = the sections already read)."""
    if arm.view == "full":
        return [([u["i"] for u in units], _fill(template, reader, "", units))]
    if arm.view != "forward":
        raise ValueError(f"unknown view {arm.view!r}")
    out: list[tuple[list[int], str]] = []
    for sec in sorted({u["section"] for u in units}):
        before = [u for u in units if u["section"] < sec]
        current = [u for u in units if u["section"] == sec]
        context = "\n".join(u["text"] for u in before)
        out.append(([u["i"] for u in current], _fill(template, reader, context, current)))
    return out


def parse_rows(text: str, expected: list[int]) -> dict[int, tuple[str, str]]:
    """{unit index: (verdict, reason)} covering exactly `expected`, or ParseError."""
    rows: dict[int, tuple[str, str]] = {}
    for line in text.splitlines():
        m = _ROW_RE.match(line)
        if not m:
            continue
        i = int(m.group(1))
        if i in rows:
            raise ParseError(f"unit {i} answered twice")
        rows[i] = (m.group(2), m.group(3).strip())
    missing = sorted(set(expected) - rows.keys())
    extra = sorted(rows.keys() - set(expected))
    if missing or extra:
        raise ParseError(f"missing units {missing[:10]} / unexpected units {extra[:10]}")
    return rows


def claude_command(arm: Arm, prompt: str) -> list[str]:
    """The cutter sees only the prompt (plan claim 2): --safe-mode drops the user's
    CLAUDE.md, rules, hooks, MCP and output style (2026-10-08: without it the child
    quoted "# Claude Code Harness"; with it, NONE), and --tools "" leaves it no tool
    to act on an imperative sentence in the corpus with the user's permissions."""
    cmd = ["claude", "-p", prompt, "--safe-mode", "--tools", "", "--strict-mcp-config"]
    if arm.model:
        cmd += ["--model", arm.model]
    return cmd


def codex_command(arm: Arm, out_path: Path) -> list[str]:
    cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--ephemeral"]
    if arm.model:
        cmd += ["--model", arm.model]
    return [*cmd, "-o", str(out_path), "-"]


def call_model(arm: Arm, prompt: str) -> str:
    """The real runner, in an empty temp cwd so no project CLAUDE.md / AGENTS.md is
    discovered. Codex also gets a temp CODEX_HOME holding only a symlink to auth.json:
    ~/.codex/AGENTS.md otherwise loads from any cwd (2026-10-08 probe quoted
    "# Codex Harness" even with project_doc_max_bytes=0; with the temp home, NONE)."""
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp) / "cwd"
        cwd.mkdir()
        if arm.runner == "claude":
            cmd = claude_command(arm, prompt)
            return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout
        if arm.runner == "codex":
            home = Path(tmp) / "codex-home"
            home.mkdir()
            (home / "auth.json").symlink_to(Path.home() / ".codex" / "auth.json")
            out = Path(tmp) / "last.txt"
            env = {**os.environ, "CODEX_HOME": str(home)}
            subprocess.run(
                codex_command(arm, out),
                input=prompt,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            return out.read_text(encoding="utf-8")
    raise ValueError(f"unknown runner {arm.runner!r}")


def run_text(
    units: list[dict], arm: Arm, prompt_dir: Path, runner: Runner = call_model
) -> dict[int, tuple[str, str]]:
    template = (prompt_dir / "cutter.md").read_text(encoding="utf-8")
    reader = reader_text(arm, prompt_dir)
    verdicts: dict[int, tuple[str, str]] = {}
    for asked, prompt in build_prompts(units, arm, template, reader):
        verdicts.update(parse_rows(runner(arm, prompt), asked))
    return verdicts


def write_tsv(path: Path, verdicts: dict[int, tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{i}\t{v}\t{r}" for i, (v, r) in sorted(verdicts.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_tsv(path: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            i, verdict, *_ = line.split("\t")
            out[int(i)] = verdict
    return out

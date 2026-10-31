"""Held-out transfer probe for a rules-stocktake Dissolve candidate — evidence, never a verdict.

akc-cycle.md asks for held-out transfer before a rule is retired: the behaviour must
reproduce in a fresh context without the scaffold. This script runs the same scene(s)
in fresh `claude -p` children twice — with the rule loaded and with it excluded — and
returns both outputs side by side as JSON. Comparing them is the LLM side's job
(rules-stocktake), so the script makes no judgement.

How the rule is removed (measured 2026-10-31, Claude Code 2.1.316):
  * `--settings '{"claudeMdExcludes": [<abs path>]}'` drops exactly that file from the
    user memory files; every other rule stays. `/context` lists the memory files in a
    "### Memory Files" table, so the removal is checked deterministically, with the same
    argv as the scene runs (only the stdin prompt differs).
  * A behavioural canary agreed: asked for the heading of the rate-limit rule, the child
    without debugging.md answered NONE, the child with it quoted `# Rate Limit Signal`.

Isolation (children inherit user settings — memory reference_claude_p_child_inheritance):
  * outputStyle "default" keeps the user's style out of the outputs.
  * disableAllHooks stops user hooks from logging metrics or injecting context.
  * `--tools ""` lets the child only answer in text, so a scene cannot edit files.
  * `--strict-mcp-config` with no config loads no MCP servers.
  * cwd is a fresh empty temp dir, so no project CLAUDE.md or project memory loads.

Every child runs with `--output-format json`; the answer is taken from `.result`.

Fail loud: the script exits 2 with a message on stderr and prints no JSON when
  * the /context table cannot be parsed, the rule is missing from the "with" run, it is
    still present in the "without" run, or the exclusion removed any other file;
  * a child exits non-zero, its JSON is unreadable, it reports `is_error` or a subtype
    other than "success", or its result is empty;
  * the scene runs did not all use the same model (a silent fallback would make the two
    conditions incomparable);
  * any loaded memory file or any rule file changed between the /context check and the
    end of the scene runs (a parallel session editing rules would void the check);
  * a loaded memory file cannot be read for the leak scan;
  * a scene starts with "/" (it would run as a slash command, not as a scene). An output that looks like success always means
both conditions ran as described.

Usage:
  python3 -m scripts.transfer_probe ~/.claude/rules/common/debugging.md \
      --scene "..." [--scene "..."] [--scenes-file scenes.json] [--runs 3] [--model opus]
Exit: 0 = JSON on stdout / 2 = refused or the probe could not be trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Verbatim rules carry the author's own words; they are never Dissolve candidates.
VERBATIM_RULES = frozenset({"contemplative-axioms.md", "practitioner-identity.md"})

BASE_SETTINGS: dict[str, object] = {"outputStyle": "default", "disableAllHooks": True}
ISOLATION_FLAGS = ["--tools", "", "--strict-mcp-config", "--output-format", "json"]
CONTEXT_PROBE = "/context"

MEMORY_HEADER = "### Memory Files"
# Row shape: "| User | /abs/path.md | 553 |"
MEMORY_ROW = re.compile(r"^\|\s*[^|]+\|\s*(/[^|]+?)\s*\|\s*[^|]+\|\s*$")


class ProbeError(Exception):
    """The probe cannot produce trustworthy evidence; the caller must not use any output."""


def validate_rule(rule: Path, rules_dir: Path) -> Path:
    resolved = rule.expanduser().resolve()
    root = rules_dir.expanduser().resolve()
    if not resolved.is_file():
        raise ProbeError(f"rule not found: {rule}")
    if resolved.suffix != ".md" or resolved.name == "README.md":
        raise ProbeError(f"not a rule file: {resolved}")
    if not resolved.is_relative_to(root):
        raise ProbeError(f"rule is outside {root}: {resolved}")
    if resolved.name in VERBATIM_RULES:
        raise ProbeError(f"{resolved.name} is a verbatim rule and is not a Dissolve candidate")
    return resolved


def build_argv(claude_bin: str, rule: Path, *, exclude: bool, model: str | None) -> list[str]:
    settings = dict(BASE_SETTINGS)
    if exclude:
        settings["claudeMdExcludes"] = [str(rule)]
    argv = [claude_bin, "-p", "--settings", json.dumps(settings), *ISOLATION_FLAGS]
    if model:
        argv += ["--model", model]
    return argv


def run_child(argv: list[str], prompt: str, cwd: Path, timeout: int) -> tuple[str, list[str]]:
    """Return (result text, models used). Any sign of a failed run raises ProbeError."""
    try:
        proc = subprocess.run(
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=cwd,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(f"claude -p timed out after {timeout}s") from exc
    except (OSError, ValueError) as exc:
        raise ProbeError(f"cannot run {argv[0]}: {exc}") from exc
    if proc.returncode != 0:
        raise ProbeError(f"claude -p exited {proc.returncode}: {proc.stderr.strip()[:500]}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"claude -p output is not JSON: {proc.stdout.strip()[:300]!r}") from exc
    if not isinstance(data, dict):
        raise ProbeError("claude -p JSON is not an object")
    if data.get("is_error") or data.get("subtype") != "success":
        raise ProbeError(
            f"claude -p reported failure: subtype={data.get('subtype')!r} "
            f"result={str(data.get('result'))[:300]!r}"
        )
    result = data.get("result")
    if not isinstance(result, str) or not result.strip():
        raise ProbeError("claude -p printed nothing")
    usage = data.get("modelUsage")
    models = sorted(usage) if isinstance(usage, dict) else []
    return result.strip(), models


def parse_memory_files(context_output: str) -> list[str]:
    lines = context_output.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == MEMORY_HEADER)
    except StopIteration as exc:
        raise ProbeError(f"/context output has no '{MEMORY_HEADER}' section") from exc
    paths: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("### "):
            break
        m = MEMORY_ROW.match(line.strip())
        if m:
            paths.append(m.group(1))
    if not paths:
        raise ProbeError("/context Memory Files table has no rows")
    return paths


def _canon(paths: Sequence[str]) -> list[str]:
    return [str(Path(p).resolve()) for p in paths]


def check_exclusion(with_files: list[str], without_files: list[str], rule: Path) -> None:
    target = str(rule)
    with_c, without_c = _canon(with_files), _canon(without_files)
    if target not in with_c:
        raise ProbeError(f"rule is not loaded even without the exclusion: {target}")
    if target in without_c:
        raise ProbeError(f"exclusion did not take effect; rule still loaded: {target}")
    expected = [p for p in with_c if p != target]
    if without_c != expected:
        raise ProbeError(
            "exclusion changed more than the target rule: "
            f"missing={sorted(set(expected) - set(without_c))} "
            f"extra={sorted(set(without_c) - set(expected))}"
        )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise ProbeError(f"cannot read {path}: {exc}") from exc


def snapshot(memory_files: Sequence[str], rules_dir: Path) -> dict[str, str]:
    """Content hash of every loaded memory file and every rule file on disk."""
    paths = {Path(p).resolve() for p in memory_files}
    paths |= {p.resolve() for p in rules_dir.expanduser().resolve().rglob("*.md")}
    out: dict[str, str] = {}
    for p in sorted(paths):
        try:
            out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            out[str(p)] = "<missing>"
    return out


def check_unchanged(before: dict[str, str], after: dict[str, str]) -> None:
    if before != after:
        changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
        raise ProbeError(f"memory or rule files changed during the probe: {changed}")


def mentions_elsewhere(memory_files: Sequence[str], rule: Path) -> list[dict[str, object]]:
    """Other loaded files that still name the rule — a partial leak into the 'without' run."""
    found: list[dict[str, object]] = []
    for path in memory_files:
        p = Path(path).resolve()
        if p == rule:
            continue
        text = read_text(p)
        hits = [n for n, line in enumerate(text.splitlines(), 1) if rule.name in line]
        if hits:
            found.append({"path": str(p), "lines": hits})
    return found


def load_scenes(scenes: Sequence[str], scenes_file: Path | None) -> list[str]:
    out = list(scenes)
    if scenes_file is not None:
        try:
            data = json.loads(scenes_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ProbeError(f"cannot read scenes file {scenes_file}: {exc}") from exc
        if not isinstance(data, list) or not all(isinstance(s, str) for s in data):
            raise ProbeError("scenes file must be a JSON list of strings")
        out += data
    out = [s for s in out if s.strip()]
    if not out:
        raise ProbeError("give at least one scene (--scene or --scenes-file)")
    slash = [s for s in out if s.lstrip().startswith("/")]
    if slash:
        raise ProbeError(f"a scene starting with '/' would run as a slash command: {slash[0]!r}")
    return out


def probe(
    rule: Path,
    scenes: list[str],
    *,
    rules_dir: Path,
    claude_bin: str,
    model: str | None,
    runs: int,
    timeout: int,
    workers: int,
) -> dict[str, object]:
    argv = {
        "with": build_argv(claude_bin, rule, exclude=False, model=model),
        "without": build_argv(claude_bin, rule, exclude=True, model=model),
    }
    with tempfile.TemporaryDirectory(prefix="transfer-probe-") as tmp:
        cwd = Path(tmp)
        memory = {
            cond: parse_memory_files(run_child(a, CONTEXT_PROBE, cwd, timeout)[0])
            for cond, a in argv.items()
        }
        check_exclusion(memory["with"], memory["without"], rule)
        before = snapshot(memory["with"], rules_dir)

        jobs = [(i, cond, r) for i in range(len(scenes)) for cond in argv for r in range(runs)]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            outputs = list(
                pool.map(lambda j: run_child(argv[j[1]], scenes[j[0]], cwd, timeout), jobs)
            )
    check_unchanged(before, snapshot(memory["with"], rules_dir))
    model_sets = {tuple(models) for _, models in outputs}
    if len(model_sets) != 1:
        raise ProbeError(f"scene runs used different models: {sorted(model_sets)}")
    replies: list[dict[str, list[str]]] = [{"with": [], "without": []} for _ in scenes]
    for (i, cond, _), (out, _models) in zip(jobs, outputs, strict=True):
        replies[i][cond].append(out)
    results = [{"prompt": s, **r} for s, r in zip(scenes, replies, strict=True)]

    return {
        "rule": str(rule),
        "model": model,
        "models_used": list(next(iter(model_sets))),
        "runs_per_condition": runs,
        "isolation": {
            "settings": BASE_SETTINGS,
            "flags": ISOLATION_FLAGS,
            "cwd": "fresh empty temp dir",
            "exclusion": "--settings claudeMdExcludes",
        },
        "exclusion_check": {
            "method": "/context Memory Files table, same argv as the scene runs; "
            "memory and rule files hashed before and after the scene runs",
            "with_memory_files": memory["with"],
            "without_memory_files": memory["without"],
        },
        "mentions_elsewhere": mentions_elsewhere(memory["without"], rule),
        "scenes": results,
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("rule", type=Path, help="rule file under the rules dir")
    ap.add_argument("--scene", action="append", default=[], help="scene prompt (repeatable)")
    ap.add_argument("--scenes-file", type=Path, help="JSON list of scene prompts")
    ap.add_argument("--runs", type=int, default=1, help="runs per scene per condition")
    ap.add_argument("--model", help="model for both conditions (default: user setting)")
    ap.add_argument("--rules-dir", type=Path, default=Path("~/.claude/rules"))
    ap.add_argument("--claude-bin", default=os.environ.get("CLAUDE_BIN", "claude"))
    ap.add_argument("--timeout", type=int, default=300, help="seconds per child")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    try:
        if args.runs < 1:
            raise ProbeError("--runs must be at least 1")
        rule = validate_rule(args.rule, args.rules_dir)
        scenes = load_scenes(args.scene, args.scenes_file)
        report = probe(
            rule,
            scenes,
            rules_dir=args.rules_dir,
            claude_bin=args.claude_bin,
            model=args.model,
            runs=args.runs,
            timeout=args.timeout,
            workers=max(1, args.workers),
        )
    except ProbeError as exc:
        print(f"[transfer_probe] FAIL: {exc}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

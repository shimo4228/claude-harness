"""Hermetic tests for transfer_probe.py — a fake `claude` binary stands in for the CLI.

The fake prints a `/context` Memory Files table shaped like the real one (measured
2026-10-31, Claude Code 2.1.316) and honours `claudeMdExcludes` from `--settings`.
FAKE_MODE switches it into each failure the probe must turn into exit 2.
"""

from __future__ import annotations

import json
import stat
import sys
from pathlib import Path

import pytest

from scripts.transfer_probe import main

FAKE_CLAUDE = r"""#!{python}
import json, os, sys
from pathlib import Path

argv = sys.argv[1:]
settings = json.loads(argv[argv.index("--settings") + 1])
excluded = set(settings.get("claudeMdExcludes", []))
mode = os.environ.get("FAKE_MODE", "ok")
prompt = sys.stdin.read()
rules = sorted(str(p) for p in Path(os.environ["FAKE_RULES_DIR"]).rglob("*.md"))
log = os.environ["FAKE_LOG"]
with open(log, "a") as f:
    f.write(json.dumps({{"argv": argv, "prompt": prompt}}) + "\n")


def emit(result, models=(), subtype="success", is_error=False):
    usage = {{m: {{"outputTokens": 1}} for m in models}}
    print(json.dumps({{"type": "result", "subtype": subtype, "is_error": is_error,
                      "result": result, "modelUsage": usage}}))
    sys.exit(0)


if mode == "exit1":
    print("boom", file=sys.stderr); sys.exit(1)
if prompt == "/context":
    if mode == "no_table":
        emit("## Context Usage\nnothing here")
    if mode == "ignore_exclude":
        excluded = set()
    if mode == "overexclude" and excluded:
        excluded = set(rules[:2]) | excluded
    rows = "".join(f"| User | {{r}} | 100 |\n" for r in rules if r not in excluded)
    emit("## Context Usage\n\n### Memory Files\n\n| Type | Path | Tokens |\n|---|---|---|\n"
         + rows + "\n### Skills\n| x | y |")
if mode == "empty":
    emit("  ", ["m1"])
if mode == "not_json":
    print("API Error: overloaded"); sys.exit(0)
if mode == "is_error":
    emit("API Error: usage limit reached", ["m1"], subtype="error_during_execution", is_error=True)
if mode == "mutate":
    with open(rules[0], "a") as f:
        f.write("edited by a parallel session\n")
cond = "without" if excluded else "with"
model = f"m-{{cond}}" if mode == "model_drift" else "m1"
emit(f"{{cond}}: {{prompt}}", [model])
"""


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    rules = tmp_path / "rules"
    common = rules / "common"
    common.mkdir(parents=True)
    (rules / "README.md").write_text("| `debugging.md` | rate limit |\n")
    (common / "debugging.md").write_text("# Rate Limit Signal\n")
    (common / "boundary.md").write_text("see debugging.md\n")
    (common / "contemplative-axioms.md").write_text("verbatim\n")
    (common / "practitioner-identity.md").write_text("verbatim\n")
    fake = tmp_path / "fake-claude"
    fake.write_text(FAKE_CLAUDE.format(python=sys.executable))
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("FAKE_RULES_DIR", str(rules))
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.delenv("FAKE_MODE", raising=False)
    return {"rules": rules, "rule": common / "debugging.md", "fake": fake, "log": log}


def run(env: dict[str, Path], *extra: str, rule: Path | None = None) -> int:
    target = rule or env["rule"]
    return main(
        [str(target), "--rules-dir", str(env["rules"]), "--claude-bin", str(env["fake"]), *extra]
    )


def test_success_returns_both_conditions(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(env, "--scene", "s1", "--scene", "s2", "--runs", "2") == 0
    report = json.loads(capsys.readouterr().out)
    rule = str(env["rule"].resolve())
    assert report["rule"] == rule
    assert rule in report["exclusion_check"]["with_memory_files"]
    assert rule not in report["exclusion_check"]["without_memory_files"]
    assert [s["prompt"] for s in report["scenes"]] == ["s1", "s2"]
    assert report["scenes"][0]["with"] == ["with: s1", "with: s1"]
    assert report["scenes"][1]["without"] == ["without: s2", "without: s2"]
    assert report["models_used"] == ["m1"]
    leaked = {m["path"] for m in report["mentions_elsewhere"]}
    assert leaked == {
        str((env["rules"] / "README.md").resolve()),
        str((env["rules"] / "common" / "boundary.md").resolve()),
    }


def test_children_are_isolated(env: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    assert run(env, "--scene", "s1") == 0
    calls = [json.loads(line) for line in env["log"].read_text().splitlines()]
    assert len(calls) == 4  # /context x2 + scene x2
    for call in calls:
        argv = call["argv"]
        settings = json.loads(argv[argv.index("--settings") + 1])
        assert settings["outputStyle"] == "default"
        assert settings["disableAllHooks"] is True
        assert argv[argv.index("--tools") + 1] == ""
        assert "--strict-mcp-config" in argv
        assert argv[argv.index("--output-format") + 1] == "json"
        assert "s1" not in argv  # the prompt goes through stdin, never argv


@pytest.mark.parametrize("name", ["contemplative-axioms.md", "practitioner-identity.md"])
def test_verbatim_rules_are_refused(
    env: dict[str, Path], name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(env, "--scene", "s", rule=env["rules"] / "common" / name) == 2
    assert "verbatim" in capsys.readouterr().err
    assert not env["log"].exists()


def test_rule_outside_rules_dir_is_refused(
    env: dict[str, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stray = tmp_path / "stray.md"
    stray.write_text("x")
    assert run(env, "--scene", "s", rule=stray) == 2
    assert "outside" in capsys.readouterr().err


def test_readme_is_refused(env: dict[str, Path]) -> None:
    assert run(env, "--scene", "s", rule=env["rules"] / "README.md") == 2


def test_no_scene_is_refused(env: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    assert run(env) == 2
    assert "scene" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("mode", "message"),
    [
        ("ignore_exclude", "did not take effect"),
        ("overexclude", "more than the target"),
        ("no_table", "Memory Files"),
        ("exit1", "exited 1"),
        ("empty", "printed nothing"),
        ("not_json", "not JSON"),
        ("is_error", "reported failure"),
        ("model_drift", "different models"),
        ("mutate", "changed during the probe"),
    ],
)
def test_untrustworthy_probe_fails_loud(
    env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
    message: str,
) -> None:
    monkeypatch.setenv("FAKE_MODE", mode)
    assert run(env, "--scene", "s") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert message in captured.err


def test_scenes_file(
    env: dict[str, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    f = tmp_path / "scenes.json"
    f.write_text(json.dumps(["a", "b"]))
    assert run(env, "--scenes-file", str(f)) == 0
    assert [s["prompt"] for s in json.loads(capsys.readouterr().out)["scenes"]] == ["a", "b"]
    f.write_text(json.dumps({"not": "a list"}))
    assert run(env, "--scenes-file", str(f)) == 2


def test_slash_scene_is_refused(env: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    assert run(env, "--scene", "  /clear then answer") == 2
    assert "slash command" in capsys.readouterr().err
    assert not env["log"].exists()


def test_unreadable_memory_file_fails_loud(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    (env["rules"] / "common" / "boundary.md").write_bytes(b"\xff\xfe not utf-8")
    assert run(env, "--scene", "s") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot read" in captured.err

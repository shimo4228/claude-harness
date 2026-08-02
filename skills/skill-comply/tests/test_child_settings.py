"""Tests for the permission envelope every `claude -p` child runs inside.

These pin a claim that was false for months: that leaving a tool off
`--allowedTools` removes it. It does not — that flag is an auto-approval list.
Containment is `permissions.deny`, and these tests fix the shape of it so a
refactor cannot quietly drop it again.
"""

from __future__ import annotations

import json

import pytest

from scripts import runner as runner_mod
from scripts.child_settings import DENIED_TOOLS, child_settings
from scripts.spec_generator import UTILITY_SETTINGS


def _denied(settings_json: str) -> list[str]:
    return json.loads(settings_json)["permissions"]["deny"]


def test_every_escape_surface_is_denied_by_default() -> None:
    """Not just Bash. Agent and Workflow start subagents whose tools this code
    does not control, ToolSearch loads the inherited MCP surface on demand, and
    ScheduleWakeup outlives the measurement."""
    denied = _denied(child_settings())
    for tool in ("Bash", "Agent", "Workflow", "ToolSearch", "ScheduleWakeup"):
        assert tool in denied, f"{tool} must be denied: {denied}"


def test_the_tools_a_scenario_needs_are_not_denied() -> None:
    """Denying Skill would measure nothing — invoking a skill is the behaviour
    under test."""
    denied = _denied(child_settings())
    for tool in ("Read", "Write", "Edit", "Glob", "Grep", "Skill"):
        assert tool not in denied


def test_allow_bash_subtracts_from_the_denial() -> None:
    """The opt-in has to work by removing a denial, not by adding an allowance.

    Adding Bash to `--allowedTools` was the old mechanism and it never did
    anything, because that list does not gate the tool set.
    """
    assert "Bash" in _denied(child_settings())
    assert "Bash" not in _denied(child_settings(allow_bash=True))
    # Everything else stays denied — --allow-bash is not --allow-everything.
    for tool in ("Agent", "Workflow", "ToolSearch", "ScheduleWakeup"):
        assert tool in _denied(child_settings(allow_bash=True))


def test_output_style_is_pinned_only_for_utility_children() -> None:
    """The scenario child must inherit the user's configuration — that is what
    is being measured. The generator and classifier must not, or a user-level
    output style wraps their machine-readable answer in prose."""
    assert "outputStyle" not in json.loads(child_settings())
    assert json.loads(child_settings(pin_output_style=True))["outputStyle"] == "default"
    assert json.loads(UTILITY_SETTINGS)["outputStyle"] == "default"


def test_the_utility_children_carry_the_same_denial() -> None:
    """The generator receives the audited document's raw body, so it is the
    child that most needs the envelope — and it had none at all."""
    assert set(_denied(UTILITY_SETTINGS)) == set(DENIED_TOOLS)


def test_run_scenario_passes_the_envelope_to_the_child(monkeypatch: pytest.MonkeyPatch) -> None:
    """A settings-less invocation is the bug this whole module exists for."""
    captured: list[list[str]] = []

    class _Result:
        returncode = 0
        stdout = (
            '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1",'
            '"name":"Read","input":{}}]},"session_id":"s"}'
        )
        stderr = ""

    def fake_run(cmd: list[str], **_kwargs: object) -> _Result:
        captured.append(cmd)
        return _Result()

    monkeypatch.setattr(runner_mod, "_setup_sandbox", lambda *_a, **_k: None)
    monkeypatch.setattr(runner_mod.subprocess, "run", fake_run)

    from scripts.scenario_generator import Scenario

    runner_mod.run_scenario(
        Scenario(id="p", level=1, level_name="probe", description="", prompt="x", setup_commands=())
    )

    cmd = captured[0]
    assert "--settings" in cmd, cmd
    assert "Bash" in _denied(cmd[cmd.index("--settings") + 1])

"""Tests for runner — stream-json extraction and child-failure handling."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import runner as runner_mod
from scripts.runner import ScenarioExecutionError, _parse_stream_json, run_scenario
from scripts.scenario_generator import Scenario

TRACE_LINE = (
    '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1",'
    '"name":"Read","input":{"file_path":"a.py"}}]},"session_id":"s1"}'
)


def _scenario() -> Scenario:
    return Scenario(
        id="probe",
        level=1,
        level_name="supportive",
        description="d",
        prompt="p",
        setup_commands=(),
    )


def _fake_child(
    monkeypatch: pytest.MonkeyPatch, *, returncode: int, stdout: str, stderr: str = ""
) -> None:
    monkeypatch.setattr(runner_mod, "_setup_sandbox", lambda *_a, **_k: None)
    monkeypatch.setattr(
        runner_mod.subprocess,
        "run",
        lambda *_a, **_k: subprocess.CompletedProcess(
            args=[], returncode=returncode, stdout=stdout, stderr=stderr
        ),
    )


def test_dead_child_with_no_trace_raises_instead_of_scoring_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty stdout would parse to zero events and grade as 0% — a fake result."""
    _fake_child(monkeypatch, returncode=1, stdout="", stderr="rate limit exceeded")

    with pytest.raises(ScenarioExecutionError) as exc:
        run_scenario(_scenario())

    assert "rate limit exceeded" in str(exc.value)
    assert "probe" in str(exc.value)


def test_clean_exit_with_empty_stdout_also_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """The condition is emptiness, not the exit code.

    Requiring a non-zero exit as well left this route open: `classify_events`
    short-circuits on an empty trace without calling any model, and the grader
    then prints 0%.
    """
    _fake_child(monkeypatch, returncode=0, stdout="")

    with pytest.raises(ScenarioExecutionError, match="exited 0"):
        run_scenario(_scenario())


def test_clean_exit_with_unparseable_stdout_also_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_child(monkeypatch, returncode=0, stdout="not json at all\nnor this line\n")

    with pytest.raises(ScenarioExecutionError):
        run_scenario(_scenario())


def test_timeout_with_no_partial_output_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """The route that mattered in practice.

    `returncode` is initialised to 0 and the timeout branch never assigns it, so
    under the old `returncode != 0 and not observations` guard a child killed at
    the hour mark with nothing on stdout was reported as `0%  [timeout]` — a score
    for a measurement that never happened.
    """
    monkeypatch.setattr(runner_mod, "_setup_sandbox", lambda *_a, **_k: None)

    def timeout(*_a: object, **_k: object) -> None:
        raise subprocess.TimeoutExpired(cmd="claude", timeout=7, output="")

    monkeypatch.setattr(runner_mod.subprocess, "run", timeout)

    with pytest.raises(ScenarioExecutionError, match="timed out after 7s"):
        run_scenario(_scenario(), timeout=7)


def test_timeout_with_a_partial_trace_is_still_graded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Truncated is not empty — partial work is real work and gets scored."""
    monkeypatch.setattr(runner_mod, "_setup_sandbox", lambda *_a, **_k: None)

    def timeout(*_a: object, **_k: object) -> None:
        raise subprocess.TimeoutExpired(cmd="claude", timeout=7, output=TRACE_LINE)

    monkeypatch.setattr(runner_mod.subprocess, "run", timeout)

    run = run_scenario(_scenario(), timeout=7)

    assert run.timed_out is True
    assert len(run.observations) == 1


def test_nonzero_exit_with_a_real_trace_is_still_graded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A child cut short by --max-turns produced a real trace; grading it is honest."""
    _fake_child(monkeypatch, returncode=1, stdout=TRACE_LINE)

    run = run_scenario(_scenario())

    assert len(run.observations) == 1
    assert run.observations[0].tool == "Read"


def test_clean_exit_is_unaffected(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_child(monkeypatch, returncode=0, stdout=TRACE_LINE)

    run = run_scenario(_scenario())

    assert len(run.observations) == 1
    assert run.sandbox_dir == Path("/tmp/skill-comply-sandbox/probe")


def test_extracts_tool_use_events() -> None:
    stream = "\n".join(
        [
            '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"Write","input":{"file_path":"a.py"}}]},"session_id":"s1"}',
            '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","content":"ok"}]}}',
        ]
    )
    events = _parse_stream_json(stream)
    assert len(events) == 1
    assert events[0].tool == "Write"
    assert events[0].event == "tool_complete"
    assert "a.py" in events[0].input
    assert events[0].output == "ok"


def test_extracts_text_block_as_pseudo_event() -> None:
    stream = (
        '{"type":"assistant","message":{"content":['
        '{"type":"text","text":"I will adopt jsonschema-rs because of performance"}'
        ']},"session_id":"s1"}'
    )
    events = _parse_stream_json(stream)
    assert len(events) == 1
    assert events[0].tool == "Text"
    assert events[0].event == "text_output"
    assert events[0].input == ""
    assert "jsonschema-rs" in events[0].output


def test_interleaved_text_and_tool_use_preserves_order() -> None:
    stream = "\n".join(
        [
            '{"type":"assistant","message":{"content":[{"type":"text","text":"Searching first"}]},"session_id":"s1"}',
            '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"WebSearch","input":{"query":"x"}}]},"session_id":"s1"}',
            '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","content":"results"}]}}',
            '{"type":"assistant","message":{"content":[{"type":"text","text":"Adopt foo"}]},"session_id":"s1"}',
        ]
    )
    events = _parse_stream_json(stream)
    assert len(events) == 3
    assert [e.tool for e in events] == ["Text", "WebSearch", "Text"]
    # Chronological order preserved via timestamp sort.
    assert [e.timestamp for e in events] == sorted(e.timestamp for e in events)
    assert "Searching first" in events[0].output
    assert "Adopt foo" in events[2].output


def test_empty_text_blocks_skipped() -> None:
    stream = (
        '{"type":"assistant","message":{"content":['
        '{"type":"text","text":"   "}'
        ']},"session_id":"s1"}'
    )
    events = _parse_stream_json(stream)
    assert events == []


def test_text_truncated_to_max_chars() -> None:
    from scripts.runner import TEXT_EVENT_MAX_CHARS

    long_text = "x" * (TEXT_EVENT_MAX_CHARS + 3000)
    stream = (
        '{"type":"assistant","message":{"content":[{"type":"text","text":"'
        + long_text
        + '"}]},"session_id":"s1"}'
    )
    events = _parse_stream_json(stream)
    assert len(events) == 1
    assert len(events[0].output) == TEXT_EVENT_MAX_CHARS


def test_mixed_content_block_in_single_message() -> None:
    """Single assistant message may contain text followed by tool_use."""
    stream = "\n".join(
        [
            '{"type":"assistant","message":{"content":['
            '{"type":"text","text":"Let me search"},'
            '{"type":"tool_use","id":"t1","name":"WebSearch","input":{"query":"x"}}'
            ']},"session_id":"s1"}',
            '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","content":"results"}]}}',
        ]
    )
    events = _parse_stream_json(stream)
    assert len(events) == 2
    assert events[0].tool == "Text"
    assert events[1].tool == "WebSearch"


def test_malformed_lines_skipped() -> None:
    stream = "\n".join(
        [
            "not valid json",
            '{"type":"assistant","message":{"content":[{"type":"text","text":"hello"}]},"session_id":"s1"}',
            "{broken",
        ]
    )
    events = _parse_stream_json(stream)
    assert len(events) == 1
    assert events[0].tool == "Text"

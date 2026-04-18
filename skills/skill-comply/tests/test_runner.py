"""Tests for runner._parse_stream_json — stream-json extraction."""

from __future__ import annotations

from scripts.runner import _parse_stream_json


def test_extracts_tool_use_events() -> None:
    stream = "\n".join([
        '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"Write","input":{"file_path":"a.py"}}]},"session_id":"s1"}',
        '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","content":"ok"}]}}',
    ])
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
    stream = "\n".join([
        '{"type":"assistant","message":{"content":[{"type":"text","text":"Searching first"}]},"session_id":"s1"}',
        '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"WebSearch","input":{"query":"x"}}]},"session_id":"s1"}',
        '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","content":"results"}]}}',
        '{"type":"assistant","message":{"content":[{"type":"text","text":"Adopt foo"}]},"session_id":"s1"}',
    ])
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
    stream = "\n".join([
        '{"type":"assistant","message":{"content":['
        '{"type":"text","text":"Let me search"},'
        '{"type":"tool_use","id":"t1","name":"WebSearch","input":{"query":"x"}}'
        ']},"session_id":"s1"}',
        '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","content":"results"}]}}',
    ])
    events = _parse_stream_json(stream)
    assert len(events) == 2
    assert events[0].tool == "Text"
    assert events[1].tool == "WebSearch"


def test_malformed_lines_skipped() -> None:
    stream = "\n".join([
        "not valid json",
        '{"type":"assistant","message":{"content":[{"type":"text","text":"hello"}]},"session_id":"s1"}',
        "{broken",
    ])
    events = _parse_stream_json(stream)
    assert len(events) == 1
    assert events[0].tool == "Text"

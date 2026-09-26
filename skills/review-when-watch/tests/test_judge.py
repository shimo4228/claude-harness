from __future__ import annotations

import pytest
from conftest import REPO_ROOT, FakeJev

from scripts import judge
from scripts.judge import (
    MAX_REPORT_CHARS,
    MODEL,
    OVERLAP_CRITERIA,
    QUESTION_HASH,
    JudgeError,
    build_questions,
    build_state,
    load_jev_client,
    run_canary,
)


def test_questions_use_only_confirmed_primitives():
    questions = build_questions()
    assert questions["met"] == {"type": "noul", "instructions": judge.MET_INSTRUCTIONS}
    assert questions["overlap"]["type"] == "choice"
    # The lowest option is "shares vocabulary only" (jev-judgment-design §3).
    assert next(iter(questions["overlap"]["criteria"])) == "words_only"
    assert len(QUESTION_HASH) == 12


def test_state_carries_condition_and_report_and_marks_truncation():
    state, truncated = build_state("RFC-1", "t", "cond", "r.md", "x" * (MAX_REPORT_CHARS + 1))
    assert truncated
    assert state["condition"] == "RFC-1: t\ncond"
    assert state["report"].startswith("r.md\n\n")
    assert len(state["report"]) == len("r.md\n\n") + MAX_REPORT_CHARS
    _, short = build_state("RFC-1", "t", "cond", "r.md", "body")
    assert not short


def test_judge_reads_noul_and_overlap():
    client = FakeJev(hit_rule=lambda c, r: True)
    reading = judge.judge(client, "RFC-1", "t", "cond", "r.md", "text")
    assert reading.met == pytest.approx(0.93)
    assert reading.hit
    assert reading.top_overlap == "event"
    assert set(reading.overlap) == set(OVERLAP_CRITERIA)
    assert reading.usage == {"input_tokens": 100, "output_tokens": 0}
    assert client.calls[0]["model"] == MODEL


def test_model_mismatch_is_an_error_not_a_reading():
    with pytest.raises(JudgeError, match="model mismatch"):
        judge.judge(FakeJev(model="jev-2.0"), "RFC-1", "t", "c", "r.md", "x")


def test_missing_noul_is_an_error():
    class Empty:
        def ask(self, state, questions, *, model, timeout):
            return {"model": MODEL, "answers": {}}

    with pytest.raises(JudgeError, match="no noul"):
        judge.judge(Empty(), "RFC-1", "t", "c", "r.md", "x")


def test_unknown_overlap_options_are_dropped():
    class Odd:
        def ask(self, state, questions, *, model, timeout):
            return {
                "model": MODEL,
                "answers": {
                    "met": {"noul": 0.2},
                    "overlap": {"probabilities": {"event": 0.4, "made_up": 0.6}},
                },
            }

    reading = judge.judge(Odd(), "RFC-1", "t", "c", "r.md", "x")
    assert reading.overlap == {"event": 0.4}
    assert not reading.hit


@pytest.mark.parametrize(
    ("canary", "ok"),
    [((0.9, 0.1), True), ((0.3, 0.1), False), ((0.9, 0.6), False)],
)
def test_canary_passes_only_when_both_sides_hold(canary, ok):
    result = run_canary(FakeJev(canary=canary))
    assert result.ok is ok
    assert result.positive == canary[0]


def test_canary_error_is_reported_not_raised():
    result = run_canary(FakeJev(fail_rule=lambda c, r: True))
    assert not result.ok
    assert result.error == "RuntimeError: HTTP 500"


def test_empty_overlap_has_no_top():
    reading = judge.Reading(met=0.1, overlap={}, truncated=False, model=MODEL)
    assert reading.top_overlap == ""


def test_jev_client_loads_from_the_router_by_path():
    module = load_jev_client(REPO_ROOT)
    assert module.API_HOST == "api.typesafe.ai"
    assert callable(module.resolve_api_key)
    assert module.resolve_api_key({"TYPESAFE_API_KEY": " k "}) == "k"


def test_jev_client_missing_path_raises(tmp_path):
    with pytest.raises((ImportError, FileNotFoundError, OSError)):
        load_jev_client(tmp_path)

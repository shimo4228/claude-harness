"""Tests for grader module — compliance scoring with LLM classification."""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.grader import ComplianceResult, grade
from scripts.parser import parse_spec, parse_trace

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def tdd_spec():
    return parse_spec(FIXTURES / "tdd_spec.yaml")


@pytest.fixture
def compliant_trace():
    return parse_trace(FIXTURES / "compliant_trace.jsonl")


@pytest.fixture
def noncompliant_trace():
    return parse_trace(FIXTURES / "noncompliant_trace.jsonl")


def _mock_compliant_classification(spec, trace, model="haiku"):
    """Simulate LLM correctly classifying a compliant trace."""
    return {
        "write_test": [0],
        "run_test_red": [1],
        "write_impl": [2],
        "run_test_green": [3],
        "refactor": [4],
    }


def _mock_noncompliant_classification(spec, trace, model="haiku"):
    """Simulate LLM classifying a noncompliant trace (impl before test)."""
    return {
        "write_impl": [0],  # src/fib.py written first
        "write_test": [1],  # test written second
        "run_test_green": [2],  # only a passing test run
    }


def _mock_empty_classification(spec, trace, model="haiku"):
    return {}


class TestGradeCompliant:
    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_returns_compliance_result(self, mock_cls, tdd_spec, compliant_trace) -> None:
        result = grade(tdd_spec, compliant_trace)
        assert isinstance(result, ComplianceResult)

    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_full_compliance(self, mock_cls, tdd_spec, compliant_trace) -> None:
        result = grade(tdd_spec, compliant_trace)
        assert result.compliance_rate == 1.0

    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_all_required_steps_detected(self, mock_cls, tdd_spec, compliant_trace) -> None:
        result = grade(tdd_spec, compliant_trace)
        required_results = [
            s
            for s in result.steps
            if s.step_id in ("write_test", "run_test_red", "write_impl", "run_test_green")
        ]
        assert all(s.detected for s in required_results)

    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_optional_step_detected(self, mock_cls, tdd_spec, compliant_trace) -> None:
        result = grade(tdd_spec, compliant_trace)
        refactor = next(s for s in result.steps if s.step_id == "refactor")
        assert refactor.detected is True

    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_no_hook_promotion_recommended(self, mock_cls, tdd_spec, compliant_trace) -> None:
        result = grade(tdd_spec, compliant_trace)
        assert result.recommend_hook_promotion is False

    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_step_evidence_not_empty(self, mock_cls, tdd_spec, compliant_trace) -> None:
        result = grade(tdd_spec, compliant_trace)
        for step in result.steps:
            if step.detected:
                assert len(step.evidence) > 0


class TestGradeNoncompliant:
    @patch("scripts.grader.classify_events", side_effect=_mock_noncompliant_classification)
    def test_low_compliance(self, mock_cls, tdd_spec, noncompliant_trace) -> None:
        result = grade(tdd_spec, noncompliant_trace)
        assert result.compliance_rate < 1.0

    @patch("scripts.grader.classify_events", side_effect=_mock_noncompliant_classification)
    def test_write_test_fails_ordering(self, mock_cls, tdd_spec, noncompliant_trace) -> None:
        """write_test fails on a TRUE before_step violation (test written AFTER impl).

        This is not an after_step cascade — the classified fallback sees write_impl
        and the violation is real, so it must keep failing after the cascade fix.
        """
        result = grade(tdd_spec, noncompliant_trace)
        write_test = next(s for s in result.steps if s.step_id == "write_test")
        assert write_test.detected is False
        assert "must occur before" in (write_test.failure_reason or "")

    @patch("scripts.grader.classify_events", side_effect=_mock_noncompliant_classification)
    def test_run_test_red_not_detected(self, mock_cls, tdd_spec, noncompliant_trace) -> None:
        """run_test_red fails on presence (no candidate events), not on ordering."""
        result = grade(tdd_spec, noncompliant_trace)
        run_red = next(s for s in result.steps if s.step_id == "run_test_red")
        assert run_red.detected is False
        assert "no matching event" in (run_red.failure_reason or "")

    @patch("scripts.grader.classify_events", side_effect=_mock_noncompliant_classification)
    def test_hook_promotion_recommended(self, mock_cls, tdd_spec, noncompliant_trace) -> None:
        result = grade(tdd_spec, noncompliant_trace)
        assert result.recommend_hook_promotion is True

    @patch("scripts.grader.classify_events", side_effect=_mock_noncompliant_classification)
    def test_failure_reasons_present(self, mock_cls, tdd_spec, noncompliant_trace) -> None:
        result = grade(tdd_spec, noncompliant_trace)
        failed_steps = [s for s in result.steps if not s.detected and s.step_id != "refactor"]
        for step in failed_steps:
            assert step.failure_reason is not None


class TestGradeEdgeCases:
    @patch("scripts.grader.classify_events", side_effect=_mock_empty_classification)
    def test_empty_trace(self, mock_cls, tdd_spec) -> None:
        result = grade(tdd_spec, [])
        assert result.compliance_rate == 0.0
        assert result.recommend_hook_promotion is True

    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_compliance_rate_is_ratio_of_required_only(
        self, mock_cls, tdd_spec, compliant_trace
    ) -> None:
        result = grade(tdd_spec, compliant_trace)
        assert result.compliance_rate == 1.0

    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_spec_id_in_result(self, mock_cls, tdd_spec, compliant_trace) -> None:
        result = grade(tdd_spec, compliant_trace)
        assert result.spec_id == "tdd-workflow"


def _mock_missing_upstream_classification(spec, trace, model="haiku"):
    """write_test never classified — downstream steps must NOT cascade-fail."""
    return {
        "run_test_red": [1],
        "write_impl": [2],
        "run_test_green": [3],
    }


def _mock_true_violation_classification(spec, trace, model="haiku"):
    """run_test_green points at an event BEFORE the resolved write_impl."""
    return {
        "write_impl": [2],
        "run_test_green": [1],
    }


def _mock_violating_then_ok_classification(spec, trace, model="haiku"):
    """run_test_green has one violating candidate (1) and one valid one (3)."""
    return {
        "write_impl": [2],
        "run_test_green": [1, 3],
    }


def _mock_only_run_test_red_classification(spec, trace, model="haiku"):
    """Both after_step (write_test) and before_step (write_impl) are absent."""
    return {"run_test_red": [1]}


def _mock_after_unevaluable_before_violated_classification(spec, trace, model="haiku"):
    """run_test_red's after_step is missing but its before_step is violated."""
    return {
        "run_test_red": [1],
        "write_impl": [0],
    }


def _mock_multilabel_classification(spec, trace, model="haiku"):
    """Event 4 satisfies two detectors at once (multi-label classification)."""
    return {
        "write_test": [0],
        "run_test_red": [1],
        "write_impl": [2, 4],
        "run_test_green": [3],
        "refactor": [4],
    }


class TestTemporalOrderNarrowFix:
    """after_step cascade fix: unevaluable order must not nullify detection."""

    @patch(
        "scripts.grader.classify_events",
        side_effect=_mock_noncompliant_classification,
    )
    def test_write_impl_detected_with_unevaluable_order(
        self, mock_cls, tdd_spec, noncompliant_trace
    ) -> None:
        """Semantic flip pinned: write_impl was cascade-failed before the fix."""
        result = grade(tdd_spec, noncompliant_trace)
        write_impl = next(s for s in result.steps if s.step_id == "write_impl")
        assert write_impl.detected is True
        assert write_impl.order_status == "unevaluable"
        assert "run_test_red" in (write_impl.order_note or "")

    @patch(
        "scripts.grader.classify_events",
        side_effect=_mock_missing_upstream_classification,
    )
    def test_after_step_unevaluable_does_not_cascade(
        self, mock_cls, tdd_spec, compliant_trace
    ) -> None:
        """One missing upstream step must cost exactly one step, not the chain."""
        result = grade(tdd_spec, compliant_trace)
        by_id = {s.step_id: s for s in result.steps}
        run_red = by_id["run_test_red"]
        assert run_red.detected is True
        assert run_red.order_status == "unevaluable"
        assert "write_test" in (run_red.order_note or "")
        # unevaluable step enters `resolved`, so downstream checks resume
        # against its real timestamp instead of going unevaluable themselves
        assert by_id["write_impl"].detected is True
        assert by_id["write_impl"].order_status == "ok"
        assert by_id["run_test_green"].detected is True
        assert by_id["run_test_green"].order_status == "ok"
        assert result.compliance_rate == 0.75

    @patch(
        "scripts.grader.classify_events",
        side_effect=_mock_true_violation_classification,
    )
    def test_true_order_violation_still_fails_after_fix(
        self, mock_cls, tdd_spec, compliant_trace
    ) -> None:
        """Upstream resolved + event before it = genuine violation = still FAIL."""
        result = grade(tdd_spec, compliant_trace)
        run_green = next(s for s in result.steps if s.step_id == "run_test_green")
        assert run_green.detected is False
        assert run_green.order_status == "violated"
        assert "must occur after" in (run_green.failure_reason or "")

    @patch(
        "scripts.grader.classify_events",
        side_effect=_mock_violating_then_ok_classification,
    )
    def test_violating_candidate_skipped_ok_candidate_matches(
        self, mock_cls, tdd_spec, compliant_trace
    ) -> None:
        result = grade(tdd_spec, compliant_trace)
        run_green = next(s for s in result.steps if s.step_id == "run_test_green")
        assert run_green.detected is True
        assert run_green.evidence[0].timestamp == "2026-03-20T10:00:30Z"

    @patch("scripts.grader.classify_events", side_effect=_mock_compliant_classification)
    def test_order_status_ok_on_compliant(self, mock_cls, tdd_spec, compliant_trace) -> None:
        result = grade(tdd_spec, compliant_trace)
        for step in result.steps:
            assert step.order_status == "ok"
            assert step.order_note is None

    @patch(
        "scripts.grader.classify_events",
        side_effect=_mock_only_run_test_red_classification,
    )
    def test_both_constraints_unevaluable_notes_joined(
        self, mock_cls, tdd_spec, compliant_trace
    ) -> None:
        """after_step AND before_step both missing → both notes, '; '-joined."""
        result = grade(tdd_spec, compliant_trace)
        run_red = next(s for s in result.steps if s.step_id == "run_test_red")
        assert run_red.detected is True
        assert run_red.order_status == "unevaluable"
        assert "write_test" in (run_red.order_note or "")
        assert "write_impl" in (run_red.order_note or "")
        assert "; " in (run_red.order_note or "")

    @patch(
        "scripts.grader.classify_events",
        side_effect=_mock_after_unevaluable_before_violated_classification,
    )
    def test_violation_wins_over_unevaluable_note(
        self, mock_cls, tdd_spec, compliant_trace
    ) -> None:
        """An unevaluable after_step must not mask a real before_step violation."""
        result = grade(tdd_spec, compliant_trace)
        run_red = next(s for s in result.steps if s.step_id == "run_test_red")
        assert run_red.detected is False
        assert run_red.order_status == "violated"
        assert "must occur before 'write_impl'" in (run_red.failure_reason or "")

    @patch(
        "scripts.grader.classify_events",
        side_effect=_mock_noncompliant_classification,
    )
    def test_no_candidate_constrained_step_order_unevaluable(
        self, mock_cls, tdd_spec, noncompliant_trace
    ) -> None:
        """A constrained step with zero candidates never had its order checked."""
        result = grade(tdd_spec, noncompliant_trace)
        run_red = next(s for s in result.steps if s.step_id == "run_test_red")
        assert run_red.detected is False
        assert run_red.order_status == "unevaluable"

    @patch("scripts.grader.classify_events", side_effect=_mock_multilabel_classification)
    def test_multi_label_event_counts_for_both_steps(
        self, mock_cls, tdd_spec, compliant_trace
    ) -> None:
        """One event listed under two steps counts for both (grader side guard)."""
        result = grade(tdd_spec, compliant_trace)
        by_id = {s.step_id: s for s in result.steps}
        assert by_id["write_impl"].detected is True
        assert by_id["refactor"].detected is True
        assert result.compliance_rate == 1.0

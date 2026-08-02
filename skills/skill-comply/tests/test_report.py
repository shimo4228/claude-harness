"""Tests for report module — multi-label timeline and order-status rendering."""

from pathlib import Path

from scripts.grader import ComplianceResult, StepResult
from scripts.parser import parse_spec, parse_trace
from scripts.report import generate_report

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _result(steps: tuple[StepResult, ...], classification: dict) -> ComplianceResult:
    required = ("write_test", "run_test_red", "write_impl", "run_test_green")
    detected = sum(1 for s in steps if s.detected and s.step_id in required)
    return ComplianceResult(
        spec_id="tdd-workflow",
        steps=steps,
        compliance_rate=detected / len(required),
        recommend_hook_promotion=False,
        classification=classification,
    )


def test_timeline_multi_label_join():
    """An event classified under two steps shows both labels, comma-joined."""
    spec = parse_spec(FIXTURES / "tdd_spec.yaml")
    trace = parse_trace(FIXTURES / "compliant_trace.jsonl")
    steps = tuple(
        StepResult(step_id=s.id, detected=True, evidence=(), failure_reason=None)
        for s in spec.steps
    )
    classification = {"write_test": [0], "run_test_red": [0, 1]}
    result = _result(steps, classification)

    report = generate_report(FIXTURES / "x.md", spec, [("baseline", result, trace)])

    assert "write_test, run_test_red" in report


def test_detail_table_shows_order_column():
    """Detail table has an Order column; unevaluable note lands in Reason."""
    spec = parse_spec(FIXTURES / "tdd_spec.yaml")
    trace = parse_trace(FIXTURES / "compliant_trace.jsonl")
    steps = tuple(
        StepResult(
            step_id=s.id,
            detected=True,
            evidence=(),
            failure_reason=None,
            order_status="unevaluable" if s.id == "run_test_red" else "ok",
            order_note=(
                "after_step 'write_test' not detected; order not evaluable"
                if s.id == "run_test_red"
                else None
            ),
        )
        for s in spec.steps
    )
    result = _result(steps, {})

    report = generate_report(FIXTURES / "x.md", spec, [("baseline", result, trace)])

    assert "| Step | Required | Detected | Order | Reason |" in report
    assert "| run_test_red | Yes | YES | unevaluable |" in report
    assert "order not evaluable" in report


def test_unclassified_event_shows_dash():
    spec = parse_spec(FIXTURES / "tdd_spec.yaml")
    trace = parse_trace(FIXTURES / "compliant_trace.jsonl")
    steps = tuple(
        StepResult(step_id=s.id, detected=False, evidence=(), failure_reason="x")
        for s in spec.steps
    )
    result = _result(steps, {})

    report = generate_report(FIXTURES / "x.md", spec, [("baseline", result, trace)])

    assert "| 0 | Write |" in report
    assert "| — |" in report

"""Grade observation traces against compliance specs using LLM classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from scripts.classifier import classify_events
from scripts.parser import ComplianceSpec, ObservationEvent, Step

OrderStatus = Literal["ok", "unevaluable", "violated"]


@dataclass(frozen=True)
class StepResult:
    step_id: str
    detected: bool
    evidence: tuple[ObservationEvent, ...]
    failure_reason: str | None
    order_status: OrderStatus = "ok"
    order_note: str | None = None


@dataclass(frozen=True)
class ComplianceResult:
    spec_id: str
    steps: tuple[StepResult, ...]
    compliance_rate: float
    recommend_hook_promotion: bool
    classification: dict[str, list[int]]


def _check_temporal_order(
    step: Step,
    event: ObservationEvent,
    resolved: dict[str, list[ObservationEvent]],
    classified: dict[str, list[ObservationEvent]],
) -> tuple[OrderStatus, str | None]:
    """Check before_step/after_step constraints.

    Returns (status, message). A missing upstream step makes the constraint
    unevaluable — the event still counts as detected (with a warning) instead
    of cascade-failing downstream. Only a resolved upstream with a genuinely
    earlier/later timestamp violates; a violation wins over collected
    unevaluable notes.
    """
    notes: list[str] = []

    if step.detector.after_step is not None:
        after_events = resolved.get(step.detector.after_step, [])
        if not after_events:
            notes.append(
                f"after_step '{step.detector.after_step}' not detected; order not evaluable"
            )
        else:
            latest_after = max(e.timestamp for e in after_events)
            if event.timestamp <= latest_after:
                msg = (
                    f"must occur after '{step.detector.after_step}' "
                    f"(last at {latest_after}), but found at {event.timestamp}"
                )
                return ("violated", msg)

    if step.detector.before_step is not None:
        # Look ahead using LLM classification results
        before_events = resolved.get(step.detector.before_step)
        if before_events is None:
            before_events = classified.get(step.detector.before_step, [])
        if before_events:
            earliest_before = min(e.timestamp for e in before_events)
            if event.timestamp >= earliest_before:
                msg = (
                    f"must occur before '{step.detector.before_step}' "
                    f"(first at {earliest_before}), but found at {event.timestamp}"
                )
                return ("violated", msg)
        else:
            notes.append(
                f"before_step '{step.detector.before_step}' not classified; order not evaluable"
            )

    if notes:
        return ("unevaluable", "; ".join(notes))
    return ("ok", None)


def grade(
    spec: ComplianceSpec,
    trace: list[ObservationEvent],
    classifier_model: str = "sonnet",
) -> ComplianceResult:
    """Grade a trace against a compliance spec using LLM classification."""
    sorted_trace = sorted(trace, key=lambda e: e.timestamp)

    # Step 1: LLM classifies all events in one batch call
    classification = classify_events(spec, sorted_trace, model=classifier_model)

    # Convert indices to events
    classified: dict[str, list[ObservationEvent]] = {
        step_id: [sorted_trace[i] for i in indices if i < len(sorted_trace)]
        for step_id, indices in classification.items()
    }

    # Step 2: Check temporal ordering (deterministic)
    resolved: dict[str, list[ObservationEvent]] = {}
    step_results: list[StepResult] = []

    for step in spec.steps:
        candidates = classified.get(step.id, [])
        matched: list[ObservationEvent] = []
        violation_reason: str | None = None
        order_status: OrderStatus = "ok"
        order_note: str | None = None

        for event in candidates:
            status, message = _check_temporal_order(step, event, resolved, classified)
            if status == "violated":
                # when every candidate violates, the LAST message is reported
                violation_reason = message
                continue
            matched.append(event)
            order_status, order_note = status, message
            break

        detected = len(matched) > 0
        failure_reason: str | None = None
        if detected:
            resolved[step.id] = matched
        elif violation_reason is not None:
            failure_reason = violation_reason
            order_status = "violated"
        else:
            failure_reason = f"no matching event classified for step '{step.id}'"
            # No candidate was ever checked against the constraints, so the
            # ordering dimension is untested — don't report it as "ok"
            if step.detector.after_step is not None or step.detector.before_step is not None:
                order_status = "unevaluable"

        step_results.append(
            StepResult(
                step_id=step.id,
                detected=detected,
                evidence=tuple(matched),
                failure_reason=failure_reason,
                order_status=order_status,
                order_note=order_note,
            )
        )

    required_steps = [
        s for s in step_results if any(sp.id == s.step_id and sp.required for sp in spec.steps)
    ]
    detected_required = sum(1 for s in required_steps if s.detected)
    total_required = len(required_steps)

    compliance_rate = detected_required / total_required if total_required > 0 else 0.0

    return ComplianceResult(
        spec_id=spec.id,
        steps=tuple(step_results),
        compliance_rate=compliance_rate,
        recommend_hook_promotion=compliance_rate < spec.threshold_promote_to_hook,
        classification=classification,
    )

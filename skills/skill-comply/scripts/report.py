"""Generate Markdown compliance reports."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts.grader import ComplianceResult
from scripts.parser import ComplianceSpec, ObservationEvent
from scripts.scenario_generator import Scenario


def generate_report(
    skill_path: Path,
    spec: ComplianceSpec,
    results: list[tuple[str, ComplianceResult, list[ObservationEvent]]],
    scenarios: list[Scenario] | None = None,
    conditions: dict[str, str] | None = None,
) -> str:
    """Generate a Markdown compliance report.

    Args:
        skill_path: Path to the skill file that was tested.
        spec: The compliance spec used for grading.
        results: List of (scenario_level_name, ComplianceResult, observations) tuples.
        scenarios: Original scenario definitions with prompts.
        conditions: What the agent was actually able to do — which tier of the
            target was loaded, which tools the child had, whether fixtures
            materialised. The report was self-contained about what the agent was
            *asked*; it recorded nothing about whether the measurement could
            succeed at all, so a run where the skill never loaded printed a score
            like any other.
    """
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    overall = _overall_compliance(results)
    threshold = spec.threshold_promote_to_hook
    promote_steps = _steps_to_promote(spec, results, threshold)

    lines: list[str] = []
    lines.append(f"# skill-comply Report: {skill_path.name}")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines += _summary_section(
        skill_path, spec, results, overall, threshold, conditions, promote_steps
    )
    lines += _sequence_section(spec)
    lines += _results_section(spec, results)
    lines += _prompts_section(scenarios)
    lines += _promotion_section(spec, results, promote_steps)
    lines += _detail_section(spec, results)
    return "\n".join(lines)


# One function per Markdown section, named after the comment that already marked
# it off. `generate_report` was a single 16-branch function until the complexity
# budget landed (C901=15, ADR-0056); the sections share nothing but the `lines`
# accumulator, so each returns its own and the report is their concatenation.


def _summary_section(
    skill_path: Path,
    spec: ComplianceSpec,
    results: list[tuple[str, ComplianceResult, list[ObservationEvent]]],
    overall: float,
    threshold: float,
    conditions: dict[str, str] | None,
    promote_steps: list[str],
) -> list[str]:
    lines: list[str] = []
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Skill | `{skill_path}` |")
    lines.append(f"| Spec | {spec.id} |")
    lines.append(f"| Scenarios | {len(results)} |")
    lines.append(f"| Overall Compliance | {overall:.0%} |")
    lines.append(f"| Threshold | {threshold:.0%} |")

    for label, value in (conditions or {}).items():
        lines.append(f"| {label} | {value} |")

    if promote_steps:
        step_names = ", ".join(promote_steps)
        lines.append(f"| Recommendation | **Promote {step_names} to hooks** |")
    else:
        lines.append("| Recommendation | All steps above threshold — no hook promotion needed |")
    lines.append("")
    return lines


def _sequence_section(
    spec: ComplianceSpec,
) -> list[str]:
    lines: list[str] = []
    lines.append("## Expected Behavioral Sequence")
    lines.append("")
    lines.append("| # | Step | Required | Description |")
    lines.append("|---|------|----------|-------------|")
    for i, step in enumerate(spec.steps, 1):
        req = "Yes" if step.required else "No"
        lines.append(f"| {i} | {step.id} | {req} | {step.detector.description} |")
    lines.append("")
    return lines


def _results_section(
    spec: ComplianceSpec,
    results: list[tuple[str, ComplianceResult, list[ObservationEvent]]],
) -> list[str]:
    lines: list[str] = []
    lines.append("## Scenario Results")
    lines.append("")
    lines.append("| Scenario | Compliance | Failed Steps |")
    lines.append("|----------|-----------|----------------|")
    for level_name, result, _obs in results:
        failed = [
            s.step_id
            for s in result.steps
            if not s.detected and any(sp.id == s.step_id and sp.required for sp in spec.steps)
        ]
        failed_str = ", ".join(failed) if failed else "—"
        lines.append(f"| {level_name} | {result.compliance_rate:.0%} | {failed_str} |")
    lines.append("")
    return lines


def _prompts_section(
    scenarios: list[Scenario] | None,
) -> list[str]:
    lines: list[str] = []
    if scenarios:
        lines.append("## Scenario Prompts")
        lines.append("")
        for s in scenarios:
            lines.append(f"### {s.level_name} (Level {s.level})")
            lines.append("")
            for prompt_line in s.prompt.splitlines():
                lines.append(f"> {prompt_line}")
            lines.append("")
    return lines


def _promotion_section(
    spec: ComplianceSpec,
    results: list[tuple[str, ComplianceResult, list[ObservationEvent]]],
    promote_steps: list[str],
) -> list[str]:
    lines: list[str] = []
    if promote_steps:
        lines.append("## Advanced: Hook Promotion Recommendations (optional)")
        lines.append("")
        for step_id in promote_steps:
            rate = _step_compliance_rate(step_id, results)
            step = next(s for s in spec.steps if s.id == step_id)
            lines.append(f"- **{step_id}** (compliance {rate:.0%}): {step.description}")
        lines.append("")

    return lines


def _detail_section(
    spec: ComplianceSpec,
    results: list[tuple[str, ComplianceResult, list[ObservationEvent]]],
) -> list[str]:
    lines: list[str] = []
    lines.append("## Detail")
    lines.append("")
    for level_name, result, observations in results:
        lines.append(f"### {level_name} (Compliance: {result.compliance_rate:.0%})")
        lines.append("")
        lines.append("| Step | Required | Detected | Order | Reason |")
        lines.append("|------|----------|----------|-------|--------|")
        for sr in result.steps:
            req = "Yes" if any(sp.id == sr.step_id and sp.required for sp in spec.steps) else "No"
            det = "YES" if sr.detected else "NO"
            reason = sr.failure_reason or sr.order_note or "—"
            lines.append(f"| {sr.step_id} | {req} | {det} | {sr.order_status} | {reason} |")
        lines.append("")

        # Timeline: show what the agent actually did
        if observations:
            # Reverse index: event_index → step_ids (one event may satisfy
            # several detectors — multi-label classification)
            index_to_steps: dict[int, list[str]] = {}
            for step_id, indices in result.classification.items():
                for idx in indices:
                    index_to_steps.setdefault(idx, []).append(step_id)

            lines.append(f"**Tool Call Timeline ({len(observations)} calls)**")
            lines.append("")
            lines.append("| # | Tool | Input | Output | Classified As |")
            lines.append("|---|------|-------|--------|------|")
            for i, obs in enumerate(observations):
                step_label = ", ".join(index_to_steps.get(i, [])) or "—"
                input_summary = obs.input[:100].replace("|", "\\|").replace("\n", " ")
                output_summary = obs.output[:50].replace("|", "\\|").replace("\n", " ")
                lines.append(
                    f"| {i} | {obs.tool} | {input_summary} | {output_summary} | {step_label} |"
                )
            lines.append("")

    return lines


def _overall_compliance(
    results: list[tuple[str, ComplianceResult, list[ObservationEvent]]],
) -> float:
    if not results:
        return 0.0
    return sum(r.compliance_rate for _, r, _obs in results) / len(results)


def _step_compliance_rate(
    step_id: str,
    results: list[tuple[str, ComplianceResult, list[ObservationEvent]]],
) -> float:
    detected = sum(
        1 for _, r, _obs in results for s in r.steps if s.step_id == step_id and s.detected
    )
    return detected / len(results) if results else 0.0


def _steps_to_promote(
    spec: ComplianceSpec,
    results: list[tuple[str, ComplianceResult, list[ObservationEvent]]],
    threshold: float,
) -> list[str]:
    promote = []
    for step in spec.steps:
        if not step.required:
            continue
        rate = _step_compliance_rate(step.id, results)
        if rate < threshold:
            promote.append(step.id)
    return promote

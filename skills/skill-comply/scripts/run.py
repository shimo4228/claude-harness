"""CLI entry point for skill-comply."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from scripts.grader import grade
from scripts.report import generate_report
from scripts.runner import run_scenario
from scripts.scenario_generator import generate_scenarios
from scripts.spec_generator import generate_spec


def main() -> None:
    parser = argparse.ArgumentParser(
        description="skill-comply: Measure skill compliance rates",
    )
    parser.add_argument(
        "skill",
        type=Path,
        help="Path to skill/rule file to test",
    )
    parser.add_argument(
        "--model",
        default="sonnet",
        help="Model for scenario execution (default: sonnet)",
    )
    parser.add_argument(
        "--gen-model",
        default="haiku",
        help="Model for spec/scenario generation (default: haiku)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate spec and scenarios without executing",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output report path (default: results/<skill-name>.md)",
    )

    args = parser.parse_args()

    if not args.skill.exists():
        print(f"Error: Skill file not found: {args.skill}", file=sys.stderr)
        sys.exit(1)

    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    # Step 1: Generate compliance spec
    print(f"[1/4] Generating compliance spec from {args.skill.name}...")
    spec = generate_spec(args.skill, model=args.gen_model)
    print(f"       {len(spec.steps)} steps extracted")

    # Step 2: Generate scenarios
    spec_yaml = yaml.dump({
        "steps": [
            {"id": s.id, "description": s.description, "required": s.required}
            for s in spec.steps
        ]
    })
    print(f"[2/4] Generating scenarios (3 prompt strictness levels)...")
    scenarios = generate_scenarios(args.skill, spec_yaml, model=args.gen_model)
    print(f"       {len(scenarios)} scenarios generated")

    for s in scenarios:
        print(f"       - {s.level_name}: {s.description[:60]}")

    if args.dry_run:
        print("\n[dry-run] Spec and scenarios generated. Skipping execution.")
        print(f"\nSpec: {spec.id} ({len(spec.steps)} steps)")
        for step in spec.steps:
            marker = "*" if step.required else " "
            print(f"  [{marker}] {step.id}: {step.description}")
        return

    # Step 3: Execute scenarios
    print(f"[3/4] Executing scenarios (model={args.model})...")
    graded_results: list[tuple[str, any]] = []

    for scenario in scenarios:
        print(f"       Running {scenario.level_name}...", end="", flush=True)
        run = run_scenario(scenario, model=args.model)
        result = grade(spec, list(run.observations))
        graded_results.append((scenario.level_name, result, list(run.observations)))
        print(f" {result.compliance_rate:.0%}")

    # Step 4: Generate report
    skill_name = args.skill.parent.name if args.skill.stem == "SKILL" else args.skill.stem
    output_path = args.output or results_dir / f"{skill_name}.md"
    print(f"[4/4] Generating report...")

    report = generate_report(args.skill, spec, graded_results, scenarios=scenarios)
    output_path.write_text(report)
    print(f"       Report saved to {output_path}")

    # Summary
    overall = sum(r.compliance_rate for _, r, _obs in graded_results) / len(graded_results)
    print(f"\n{'=' * 50}")
    print(f"Overall Compliance: {overall:.0%}")
    if overall < spec.threshold_promote_to_hook:
        print("Recommendation: Some steps have low compliance. Consider promoting them to hooks. See the report for details.")


if __name__ == "__main__":
    main()

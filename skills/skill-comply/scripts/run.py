"""CLI entry point for skill-comply."""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from scripts.child_settings import DENIED_TOOLS
from scripts.grader import ComplianceResult, grade
from scripts.parser import ComplianceSpec, ObservationEvent, parse_spec
from scripts.report import generate_report
from scripts.runner import run_scenario, sanitize_sandbox_id
from scripts.scenario_generator import Scenario, generate_scenarios
from scripts.spec_generator import generate_spec
from scripts.target import classify_target, skill_payload

#: All three scenarios at once. They share nothing — separate prompts, separate
#: sandboxes, separate child processes — so the wall clock becomes the slowest
#: one instead of the sum. Peak load is three concurrent `claude -p` children,
#: the same order as fanning out three subagents.
DEFAULT_CONCURRENCY = 3


def progress(message: str) -> None:
    """Emit a progress line on stderr, flushed.

    stderr rather than stdout, for a reason measured on 2026-08-01: piping
    stdout into `tail -40` shows nothing at all until the process exits, because
    `tail` without `-f` is a last-N filter and must reach EOF before it can
    print. Flushing cannot fix that; stderr simply bypasses the pipe. A 30-minute
    run looked like a hang for exactly this reason.

    `flush=True` fixes the second, independent layer: Python block-buffers stdout
    when it is not a TTY, so redirects to a log file and background runs would
    otherwise hold progress until the buffer filled.

    Keeping progress off stdout has a third payoff — concurrent workers can no
    longer interleave into the stdout stream that carries the result.
    """
    print(message, file=sys.stderr, flush=True)


@dataclass(frozen=True)
class ScenarioOutcome:
    """One scenario's execution + grading, or the reason there is neither."""

    scenario: Scenario
    result: ComplianceResult | None
    observations: tuple[ObservationEvent, ...]
    elapsed: float
    timed_out: bool = False
    error: str | None = None
    #: `(resolved, unresolved)` invocations of the TARGET skill in this trace.
    #: Resolved is what tier 1 measures; unresolved means the agent reached for
    #: the skill and could not load it, which makes the score a description of
    #: bare behaviour rather than of compliance.
    target_invocations: tuple[int, int] = (0, 0)
    #: Full traceback when `error` is set. The worker catches broadly so one dead
    #: scenario cannot void the run, which means it also catches ordinary bugs —
    #: without this a `KeyError` in the grader reads as a measurement failure with
    #: no file or line to go on.
    traceback: str | None = None

    @property
    def ok(self) -> bool:
        return self.result is not None


def _safe_text(text: str, limit: int | None = None) -> str:
    """Strip control characters from generator-authored text before printing it.

    `level_name`, `description` and `prompt` come from `yaml.safe_load` of LLM
    output, and YAML double-quoted scalars decode escapes — so `"sup\\e[2K\\r …"`
    reaches the terminal as a real ANSI sequence. `\\e[2K\\r` erases preceding
    lines; `\\e[?1049h` swaps to the alternate screen; `\\e[8m` conceals
    everything printed after it. Any of those hides the `[setup refused]`
    warnings, which are the only sign a document tried to escape its sandbox.
    Interleaved concurrent output makes it easier to hide in.

    `str.isprintable()` is False for Unicode categories Other and Separator, so
    this also filters the 8-bit single-byte CSI (`\\x9b`), not just `\\x1b[`.
    Filtering happens before truncation so no partial sequence survives the cut.
    """
    clean = "".join(c for c in text if c.isprintable() or c == " ")
    return clean if limit is None else clean[:limit]


def _safe_label(text: str) -> str:
    """`_safe_text` at the fixed column width the progress lines align on."""
    return _safe_text(text, 11).ljust(11)


def ensure_unique_sandbox_ids(scenarios: list[Scenario]) -> list[Scenario]:
    """Guarantee distinct sandbox directories, one per scenario.

    `runner.safe_sandbox_dir` keys the sandbox on `scenario.id`, and that id is
    LLM output (`prompts/scenario_generator.md`), not a value this code controls.
    Run serially a collision is harmless: each scenario rmtree's and recreates the
    shared directory in turn. Run concurrently it is destructive — `_setup_sandbox`
    deletes before it creates, so one worker wipes a sibling that is mid-run.

    Uniqueness is checked on a case-folded SANITIZED name, not the raw id, because
    three different strings can name one directory:

    - `sanitize_sandbox_id` replaces every character outside `[A-Za-z0-9\\-_]`, so
      `task/a` and `task_a` are two ids and one path
    - macOS APFS and Windows are case-insensitive, so `fix-bug` and `Fix-Bug` are
      two `Path` objects and one inode (verified 2026-08-01: three case variants
      produced three distinct `Path`s and a single directory on disk)
    - an id that sanitizes to nothing collapses the path onto SANDBOX_BASE itself,
      which passes the containment check — a directory is inside itself — and
      would hand `shutil.rmtree` the root holding every scenario's sandbox

    Isolation therefore cannot rest on the generator's habit of suffixing the
    level name. It is enforced here, and `execute_scenarios` calls it so no caller
    can reach the thread pool without it.
    """
    seen: set[str] = set()
    unique: list[Scenario] = []
    for scenario in scenarios:
        new_id = scenario.id
        reason = ""
        if not sanitize_sandbox_id(new_id):
            new_id = f"scenario-L{scenario.level}"
            reason = "sandbox 名として空になる id"
        if _collision_key(new_id) in seen:
            base = f"{new_id}-L{scenario.level}"
            new_id, suffix = base, 1
            while _collision_key(new_id) in seen:
                suffix += 1
                new_id = f"{base}-{suffix}"
            reason = reason or "sandbox 名が他のシナリオと衝突"
        if reason:
            progress(
                f"  [{reason}] {scenario.id!r} → {new_id!r} "
                "（sandbox は 1 シナリオ 1 個でなければ並列実行が壊れる）"
            )
        seen.add(_collision_key(new_id))
        unique.append(scenario if new_id == scenario.id else replace(scenario, id=new_id))
    return unique


def target_skill_calls(
    observations: Iterable[ObservationEvent], skill_name: str | None
) -> tuple[int, int]:
    """`(resolved, unresolved)` invocations of the target skill in one trace.

    Scoped to the target rather than to any skill: the child invoking something
    unrelated says nothing about whether the thing under test was reachable, and
    a run must not be voided by an incidental miss.

    Two separate jobs come out of this pair.

    **Resolved** is what tier 1 actually measures. Placing a stub and then
    grading the ordinary procedure steps does not measure invocation at all — the
    stub carries no procedure, so a child that performs the steps from its own
    judgement scores high without ever reaching for the skill. That number would
    describe bare behaviour while the report called it compliance, which is the
    original defect wearing a new label.

    **Unresolved** means the skill was reached for and could not be loaded, so
    whatever the child did next it did without the thing under test. That is a
    failed measurement, not a low score, and it is treated like one.
    """
    if not skill_name:
        return (0, 0)
    resolved = unresolved = 0
    for obs in observations:
        if obs.tool != "Skill" or skill_name not in obs.input:
            continue
        if "Unknown skill" in obs.output:
            unresolved += 1
        else:
            resolved += 1
    return resolved, unresolved


def unreachable_detector_tools(spec: ComplianceSpec, *, allow_bash: bool) -> dict[str, int]:
    """Tools a detector expects that the child will not have.

    A step whose detector reads "Bash call to check available RAM" cannot be
    detected when Bash is denied — and it fails as "the agent did not do it"
    rather than "this could not be observed". One real spec had 5 of 9 detectors
    requiring Bash; that run happened to pass `--allow-bash`, so nothing showed,
    and nothing in the report recorded which tools the child had.

    Same family as the target-visibility check: the measurement's preconditions
    are checked before spending a run on them, and reported either way.
    """
    denied = {t for t in DENIED_TOOLS if not (allow_bash and t == "Bash")}
    counts: dict[str, int] = {}
    for step in spec.steps:
        text = f"{step.description} {step.detector.description}"
        for tool in denied:
            if tool in text:
                counts[tool] = counts.get(tool, 0) + 1
    return counts


def _collision_key(scenario_id: str) -> str:
    """The identity two scenarios must not share: the directory name, case-folded.

    `safe_sandbox_dir` keeps the original case (that is the path that gets
    created); only the comparison folds, so a case-insensitive filesystem cannot
    hand two workers the same directory.
    """
    return sanitize_sandbox_id(scenario_id).casefold()


def _format_elapsed(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m{secs:02d}s"


def _completion_line(outcome: ScenarioOutcome, done: int, total: int) -> str:
    name = _safe_label(outcome.scenario.level_name)
    elapsed = f"{_format_elapsed(outcome.elapsed):>7}"
    if outcome.result is None:
        reason = _safe_text(outcome.error or "", 200)
        return f"       {name} 測定失敗 {elapsed}        ({done}/{total}) — {reason}"
    rate = f"{outcome.result.compliance_rate:>4.0%}"
    flag = "  [timeout — 部分出力を採点]" if outcome.timed_out else ""
    return f"       {name} 完了     {elapsed}  {rate}  ({done}/{total}){flag}"


def _execute_one(
    scenario: Scenario,
    spec: ComplianceSpec,
    *,
    model: str,
    classifier_model: str,
    allow_bash: bool,
    payload: tuple[str, str] | None,
    target_name: str | None,
) -> ScenarioOutcome:
    """Run and grade one scenario. Failures become data, not a crashed run.

    Grading lives here rather than in a later stage on purpose: it was already
    inside the per-scenario loop, so keeping it in the worker means the
    classification calls parallelise along with the executions for free.
    """
    started = time.monotonic()
    try:
        progress(f"       {_safe_label(scenario.level_name)} 開始")
        run = run_scenario(scenario, model=model, allow_bash=allow_bash, skill_payload=payload)
        result = grade(spec, list(run.observations), classifier_model=classifier_model)
    except Exception as exc:  # one dead scenario must not void the whole run
        return ScenarioOutcome(
            scenario=scenario,
            result=None,
            observations=(),
            elapsed=time.monotonic() - started,
            error=f"{type(exc).__name__}: {exc}",
            traceback=traceback.format_exc(),
        )
    return ScenarioOutcome(
        scenario=scenario,
        result=result,
        observations=tuple(run.observations),
        elapsed=time.monotonic() - started,
        timed_out=run.timed_out,
        target_invocations=target_skill_calls(run.observations, target_name),
    )


def execute_scenarios(
    scenarios: list[Scenario],
    spec: ComplianceSpec,
    *,
    model: str = "sonnet",
    classifier_model: str = "sonnet",
    allow_bash: bool = False,
    concurrency: int = DEFAULT_CONCURRENCY,
    payload: tuple[str, str] | None = None,
    target_name: str | None = None,
) -> list[ScenarioOutcome]:
    """Execute and grade every scenario, returning them in a fixed order.

    Completion order is used for progress reporting and nowhere else. The return
    value is sorted by `(level, submission index)` so that `report.generate_report`,
    which renders results in list order, produces the same structure whether the
    run was concurrent or serial; `report._overall_compliance` likewise sums in a
    fixed order. The submission index is not decoration — `level` comes straight
    from LLM YAML with nothing enforcing distinctness, and `sorted` is stable, so
    sorting on `level` alone lets completion order decide ties. Two scenarios at
    level 2 were enough to make serial and parallel disagree.

    Sandbox uniqueness is enforced here rather than left to the caller. The cost of
    getting it wrong is a worker `shutil.rmtree`-ing a sibling's live sandbox, so
    the guarantee belongs on the path that creates the hazard, not next to it.

    Threads, not asyncio: both `run_scenario` and `grade` block in
    `subprocess.run`, which releases the GIL while it waits.
    """
    scenarios = ensure_unique_sandbox_ids(scenarios)
    total = len(scenarios)
    workers = max(1, min(concurrency, total))
    outcomes: list[ScenarioOutcome] = []
    order = {id(scenario): i for i, scenario in enumerate(scenarios)}
    done = 0

    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        futures = [
            pool.submit(
                _execute_one,
                scenario,
                spec,
                model=model,
                classifier_model=classifier_model,
                allow_bash=allow_bash,
                payload=payload,
                target_name=target_name,
            )
            for scenario in scenarios
        ]
        for future in as_completed(futures):
            outcome = future.result()
            done += 1
            outcomes.append(outcome)
            progress(_completion_line(outcome, done, total))
    finally:
        # cancel_futures so Ctrl-C, or a rate-limit wall that kills the first
        # worker, does not spend the remaining scenarios' API budget before the
        # interrupt surfaces. Queued work is dropped; work already running still
        # finishes (there is no way to kill a `subprocess.run` from here).
        pool.shutdown(wait=True, cancel_futures=True)

    return sorted(outcomes, key=lambda o: (o.scenario.level, order[id(o.scenario)]))


def _report_failures(failures: list[ScenarioOutcome]) -> None:
    """Print each unmeasurable scenario, with its traceback under SKILL_COMPLY_DEBUG.

    The worker catches every exception so one dead scenario cannot void the run,
    which means genuine bugs land here too and read as measurement failures. The
    one-line form keeps normal output legible; the traceback is one env var away
    when the message is not enough to tell a rate limit from a `KeyError`.
    """
    show_traceback = bool(os.environ.get("SKILL_COMPLY_DEBUG"))
    for failure in failures:
        # `error` is an exception message, and not every raiser in the chain
        # escapes its interpolations — classifier.py embeds child stderr — so it
        # gets the same filter as generator-authored text.
        progress(
            f"       {_safe_label(failure.scenario.level_name)} {_safe_text(failure.error or '')}"
        )
        if show_traceback and failure.traceback:
            for line in failure.traceback.rstrip().splitlines():
                progress(f"         | {line}")
    if not show_traceback and any(f.traceback for f in failures):
        progress("       (SKILL_COMPLY_DEBUG=1 でトレースバックを表示)")


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return value


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
        "--classifier-model",
        default="sonnet",
        help="Model for grading/classifying tool-call traces (default: sonnet)",
    )
    parser.add_argument(
        "--concurrency",
        type=_positive_int,
        default=DEFAULT_CONCURRENCY,
        help=(
            "How many scenarios to execute at once (default: 3 = all of them). "
            "Scenarios are independent, so this only changes wall clock, never "
            "scores. Use 1 for fully serial execution if rate limits bite."
        ),
    )
    parser.add_argument(
        "--load-target-skill",
        action="store_true",
        help=(
            "Place the target skill's REAL body in the sandbox instead of a stub. "
            "Off by default: the body then instructs the unattended child directly, "
            "and nothing on disk distinguishes a skill you wrote from one you are "
            "auditing. The stub carries the real name and description — enough to "
            "measure whether the agent reached for the skill — without the body. "
            "Turn it on to measure whether the agent follows the procedure inside, "
            "and only for files you trust."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate spec and scenarios without executing",
    )
    parser.add_argument(
        "--allow-bash",
        action="store_true",
        help=(
            "Give the scenario agent Bash. Off by default: the scenario prompt is "
            "LLM output derived from the audited file, and --allowedTools auto-approves, "
            "so Bash makes any attacker-influenced .md a command-execution vector. "
            "Turn it on only for specs whose compliance depends on running commands, "
            "and only for files you trust."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output report path (default: results/<skill-name>.md)",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=None,
        help=(
            "Load a saved compliance spec YAML instead of regenerating it with "
            "an LLM — keeps the 'exam questions' fixed so runs are comparable. "
            "Generated specs are auto-saved to results/<skill-name>.spec.yaml"
        ),
    )

    args = parser.parse_args()

    if not args.skill.exists():
        print(f"Error: Skill file not found: {args.skill}", file=sys.stderr)
        sys.exit(1)

    target = classify_target(args.skill)
    if args.load_target_skill and args.allow_bash:
        progress(
            "[warn] --load-target-skill と --allow-bash の併用: 監査対象の本文が"
            "無人の子への指示になり、その子にシェルもある。信頼できる .md でのみ。"
        )
    progress(
        f"[0/4] Target: {target.kind}" + (f" ({target.skill_name})" if target.skill_name else "")
    )
    if target.kind == "project-skill":
        tier = "full body" if args.load_target_skill else "stub (name + description only)"
        progress(f"       project-scoped — sandbox に {tier} を配置して測定する")
    elif target.kind == "document":
        progress(
            "       skill ではないので Skill 呼び出しは期待しない（rule / agent 定義 / 素の .md）"
        )

    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    skill_name = args.skill.parent.name if args.skill.stem == "SKILL" else args.skill.stem

    # Step 1: Generate (or load) compliance spec
    if args.spec is not None:
        if not args.spec.exists():
            print(f"Error: Spec file not found: {args.spec}", file=sys.stderr)
            sys.exit(1)
        progress(f"[1/4] Loading compliance spec from {args.spec}...")
        spec = parse_spec(args.spec)
        progress(f"       source_rule: {spec.source_rule}")
    else:
        spec_path = results_dir / f"{skill_name}.spec.yaml"
        progress(f"[1/4] Generating compliance spec from {args.skill.name}...")
        spec = generate_spec(args.skill, model=args.gen_model, save_to=spec_path)
        progress(f"       spec saved to {spec_path} (reuse with --spec)")
    progress(f"       {len(spec.steps)} steps extracted")

    unreachable = unreachable_detector_tools(spec, allow_bash=args.allow_bash)
    if unreachable:
        detail = ", ".join(f"{tool} x{n}" for tool, n in sorted(unreachable.items()))
        progress(
            f"[warn] detector が要求するツールを子が持っていない: {detail}。"
            "該当 step は「やらなかった」ではなく「観測できなかった」として 0% になる"
        )
        if "Bash" in unreachable:
            progress("       Bash が要るなら --allow-bash を明示する（既定 off は意図的な設計）")

    # Step 2: Generate scenarios
    spec_yaml = yaml.dump(
        {
            "steps": [
                {"id": s.id, "description": s.description, "required": s.required}
                for s in spec.steps
            ]
        }
    )
    progress("[2/4] Generating scenarios (3 prompt strictness levels)...")
    scenarios = generate_scenarios(args.skill, spec_yaml, model=args.gen_model)
    progress(f"       {len(scenarios)} scenarios generated")
    # Dedup here as well as inside execute_scenarios (it is idempotent and silent
    # on a second pass) so the ids printed below are the ids that will be used.
    scenarios = ensure_unique_sandbox_ids(scenarios)

    for s in scenarios:
        progress(f"       - {_safe_text(s.level_name)}: {_safe_text(s.description, 60)}")

    if args.dry_run:
        # SKILL.md tells the user to read the generated scenarios here before
        # measuring a document they do not trust. That is only true if every
        # attacker-controlled field is actually shown: `prompt` is what the
        # unattended child is told to do, `setup_commands` and `files:` are what
        # touch the filesystem. Printing the spec alone made the documented
        # mitigation a promise the output did not keep — and when `files:` was
        # added, the same defect recurred for the widest field of the three
        # (arbitrary path plus arbitrary content) until a reviewer caught it.
        print("\n[dry-run] Spec and scenarios generated. Skipping execution.")
        print(f"\nSpec: {spec.id} ({len(spec.steps)} steps)")
        for step in spec.steps:
            marker = "*" if step.required else " "
            print(f"  [{marker}] {step.id}: {step.description}")
        for s in scenarios:
            print(f"\n--- {_safe_text(s.level_name)} (level {s.level}, sandbox id {s.id!r}) ---")
            print(f"description: {_safe_text(s.description)}")
            print("files:")
            for rel, content in s.files or ():
                body = content.encode()
                print(f"  {rel!r} ({len(body)} bytes)")
                for line in content.splitlines() or [""]:
                    print(f"    | {_safe_text(line)}")
            if not s.files:
                print("  (none)")
            print("setup_commands:")
            for cmd in s.setup_commands or ("(none)",):
                print(f"  {cmd!r}")
            print("prompt:")
            # Split first, sanitize per line: `_safe_text` drops newlines along
            # with every other non-printable, so sanitizing the whole prompt
            # first would collapse a multi-line prompt into one long line —
            # exactly the structure a reviewer needs to see.
            for line in s.prompt.splitlines() or [""]:
                print(f"  | {_safe_text(line)}")
        return

    # Step 3: Execute scenarios. `execute_scenarios` enforces sandbox uniqueness
    # itself, so nothing here has to remember to.
    workers = max(1, min(args.concurrency, len(scenarios)))
    progress(
        f"[3/4] Executing {len(scenarios)} scenarios (model={args.model}, concurrency={workers})..."
    )
    payload = skill_payload(target, full_body=args.load_target_skill)
    outcomes = execute_scenarios(
        scenarios,
        spec,
        model=args.model,
        classifier_model=args.classifier_model,
        allow_bash=args.allow_bash,
        concurrency=args.concurrency,
        payload=payload,
        target_name=target.skill_name,
    )

    # A scenario that reached for the target and got `Unknown skill` did the rest
    # of its work without the thing under test. That is a failed measurement, so
    # it leaves the report entirely rather than contributing a number a reader
    # would take for compliance. A warning alone was not enough — automation
    # reads the exit code, and the exit code said "fine".
    invalidated = [o for o in outcomes if o.ok and o.target_invocations[1] > 0]
    for outcome in invalidated:
        progress(
            f"[invalid] {_safe_label(outcome.scenario.level_name)} "
            f"{outcome.scenario.id!r} reached for {target.skill_name!r} and could not load it "
            "— このシナリオはスコアに含めない"
        )

    failures = [o for o in outcomes if not o.ok]
    graded_results: list[tuple[str, ComplianceResult, list[ObservationEvent]]] = [
        (o.scenario.level_name, o.result, list(o.observations))
        for o in outcomes
        if o.result and o not in invalidated
    ]

    if not graded_results:
        if invalidated:
            progress(
                "[3/4] 対象 skill を読み込めないまま全シナリオが走った — 測定になっていない。"
                "target が project skill なら sandbox への配置が効いているか確認する"
            )
        elif outcomes:
            progress("[3/4] every scenario failed to execute — no measurement to report:")
            _report_failures(failures)
        else:
            progress("[3/4] no scenarios were generated — nothing to measure")
        sys.exit(1)

    # Step 4: Generate report
    output_path = args.output or results_dir / f"{skill_name}.md"
    progress("[4/4] Generating report...")

    scored = [o for o in outcomes if o.result and o not in invalidated]
    invoked = sum(1 for o in scored if o.target_invocations[0] > 0)
    tier = (
        "n/a (not a project-scoped skill)"
        if payload is None
        else (
            "tier 2 — full body (--load-target-skill)"
            if args.load_target_skill
            else "tier 1 — stub"
        )
    )
    conditions = {
        "Target kind": target.kind,
        "Skill placed in sandbox": tier,
        "Child tools denied": ", ".join(DENIED_TOOLS)
        if not args.allow_bash
        else ", ".join(t for t in DENIED_TOOLS if t != "Bash"),
    }
    if payload is not None:
        # The tier-1 headline. The compliance percentage below it grades the
        # spec's procedure steps, and in tier 1 the stub carries no procedure —
        # so that percentage is not evidence about the skill. Say which number
        # answers which question instead of letting one stand in for the other.
        conditions["Target skill invoked"] = f"{invoked}/{len(scored)} scenarios"
        if not args.load_target_skill:
            conditions["Tier 1 caveat"] = (
                "**下の Compliance は手順の遵守を測っており、tier 1 では本文を渡していないので "
                "skill に帰属しない。tier 1 の測定結果は上の invoked 行**"
            )
    if invalidated:
        conditions["Excluded (skill unresolved)"] = (
            f"**{len(invalidated)} scenario(s) — 読み込めないまま走ったのでスコアから除外**"
        )
    report = generate_report(
        args.skill,
        spec,
        graded_results,
        scenarios=[o.scenario for o in outcomes if o.result],
        conditions=conditions,
    )
    output_path.write_text(report)
    print(f"Report saved to {output_path}")

    # Summary — the answer, so it goes on stdout alongside the report path.
    overall = sum(r.compliance_rate for _, r, _obs in graded_results) / len(graded_results)
    print(f"\n{'=' * 50}")
    print(f"Overall Compliance: {overall:.0%}")
    if overall < spec.threshold_promote_to_hook:
        print(
            "Recommendation: Some steps have low compliance. Consider promoting them to hooks. See the report for details."
        )

    if invalidated:
        progress(
            f"\n{len(invalidated)} scenario(s) を除外した（対象 skill を読み込めなかった）。"
            "レポートは残りのシナリオのみを対象にしている。"
        )
        sys.exit(1)

    if failures:
        # A partial measurement is still worth reporting, but it is not a clean
        # run — the exit code has to say so or automation reads it as complete.
        progress(f"\n{len(failures)} of {len(outcomes)} scenarios could not be measured:")
        _report_failures(failures)
        progress("These are NOT counted as 0% — the report covers the remaining scenarios only.")
        sys.exit(1)


if __name__ == "__main__":
    main()

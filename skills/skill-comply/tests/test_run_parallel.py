"""Tests for run.execute_scenarios — parallel execution without losing determinism.

No LLM is called: `run_scenario` and `grade` are replaced in the `scripts.run`
namespace, so what is under test is the orchestration (ordering, isolation,
progress channel, failure handling), not the measurement.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from scripts import run as run_mod
from scripts.grader import ComplianceResult
from scripts.parser import ComplianceSpec, Detector, ObservationEvent, Step
from scripts.runner import SANDBOX_BASE, ScenarioRun, safe_sandbox_dir
from scripts.scenario_generator import Scenario

LEVELS = (("supportive", 1), ("neutral", 2), ("competing", 3))


def _scenario(level_name: str, level: int, sid: str | None = None) -> Scenario:
    return Scenario(
        id=sid or f"task-{level_name}",
        level=level,
        level_name=level_name,
        description=f"{level_name} scenario",
        prompt="do the thing",
        setup_commands=(),
    )


def _spec() -> ComplianceSpec:
    return ComplianceSpec(
        id="spec-1",
        name="spec one",
        source_rule="x.md",
        version="1",
        steps=(
            Step(
                id="s1",
                description="step one",
                required=True,
                detector=Detector(description="did step one"),
            ),
        ),
        threshold_promote_to_hook=0.7,
    )


def _result(rate: float) -> ComplianceResult:
    return ComplianceResult(
        spec_id="spec-1",
        steps=(),
        compliance_rate=rate,
        recommend_hook_promotion=False,
        classification={},
    )


def _event(tool: str) -> ObservationEvent:
    return ObservationEvent(
        timestamp="T0000",
        event="tool_complete",
        tool=tool,
        session="s",
        input="",
        output="",
    )


def _install_fakes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    delays: dict[str, float] | None = None,
    rates: dict[str, float] | None = None,
    failures: dict[str, Exception] | None = None,
) -> None:
    delays = delays or {}
    failures = failures or {}
    rates = rates or {}

    def fake_run_scenario(scenario: Scenario, **_kwargs: object) -> ScenarioRun:
        time.sleep(delays.get(scenario.level_name, 0.0))
        exc = failures.get(scenario.level_name)
        if exc is not None:
            raise exc
        return ScenarioRun(
            scenario=scenario,
            observations=(_event(scenario.level_name),),
            sandbox_dir=Path("/tmp/unused"),
        )

    def fake_grade(_spec: ComplianceSpec, trace: list[ObservationEvent], **_kw: object):
        return _result(rates.get(trace[0].tool, 1.0))

    monkeypatch.setattr(run_mod, "run_scenario", fake_run_scenario)
    monkeypatch.setattr(run_mod, "grade", fake_grade)


def test_report_order_is_level_order_not_completion_order(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The slowest-first completion order must not reach the report.

    report.generate_report renders `results` in list order, so if completion
    order leaked through, a run where `competing` happened to finish first
    would produce a differently-ordered report for identical scores.
    """
    # competing finishes first, supportive last — the reverse of level order.
    _install_fakes(
        monkeypatch,
        delays={"supportive": 0.30, "neutral": 0.15, "competing": 0.0},
    )
    scenarios = [_scenario(name, lvl) for name, lvl in LEVELS]

    outcomes = run_mod.execute_scenarios(scenarios, _spec(), concurrency=3)

    # The test only has teeth if completion order really was reversed; the
    # progress log is the record of what order they finished in.
    finished = [line.split()[0] for line in capsys.readouterr().err.split("\n") if "完了" in line]
    assert finished == ["competing", "neutral", "supportive"], finished

    assert [o.scenario.level_name for o in outcomes] == ["supportive", "neutral", "competing"]
    assert [o.scenario.level for o in outcomes] == [1, 2, 3]


def test_scenarios_run_concurrently(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wall clock is the slowest scenario, not the sum of all three."""
    _install_fakes(monkeypatch, delays=dict.fromkeys(("supportive", "neutral", "competing"), 0.4))
    scenarios = [_scenario(name, lvl) for name, lvl in LEVELS]

    started = time.monotonic()
    run_mod.execute_scenarios(scenarios, _spec(), concurrency=3)
    elapsed = time.monotonic() - started

    assert elapsed < 0.9, f"looks serial: {elapsed:.2f}s for 3 x 0.4s"


def test_concurrency_one_is_serial(monkeypatch: pytest.MonkeyPatch) -> None:
    """`--concurrency 1` restores the old behaviour exactly — an escape hatch."""
    _install_fakes(monkeypatch, delays=dict.fromkeys(("supportive", "neutral", "competing"), 0.2))
    scenarios = [_scenario(name, lvl) for name, lvl in LEVELS]

    started = time.monotonic()
    run_mod.execute_scenarios(scenarios, _spec(), concurrency=1)
    elapsed = time.monotonic() - started

    assert elapsed >= 0.6, f"expected serial execution, took {elapsed:.2f}s"


def test_scores_are_unchanged_by_parallelism(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same inputs, both concurrency settings, identical per-scenario rates.

    Delays force a fully reversed completion order rather than leaving it to a
    race. With near-equal delays this passed roughly half the time even with the
    ordering guarantee removed, and a guard that is green by luck is not a guard.
    """
    rates = {"supportive": 1.0, "neutral": 0.5, "competing": 0.0}
    delays = {"supportive": 0.30, "neutral": 0.15, "competing": 0.0}
    scenarios = [_scenario(name, lvl) for name, lvl in LEVELS]

    _install_fakes(monkeypatch, rates=rates, delays=delays)
    serial = run_mod.execute_scenarios(scenarios, _spec(), concurrency=1)
    _install_fakes(monkeypatch, rates=rates, delays=delays)
    parallel = run_mod.execute_scenarios(scenarios, _spec(), concurrency=3)

    def rates_of(outcomes: list[run_mod.ScenarioOutcome]) -> list[tuple[str, float]]:
        return [(o.scenario.level_name, o.result.compliance_rate) for o in outcomes if o.result]

    assert rates_of(serial) == rates_of(parallel)


def test_equal_levels_do_not_let_completion_order_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`sorted` is stable, so sorting on `level` alone lets ties keep arrival order.

    `level` comes straight from LLM YAML (`scenario_generator.py`) with nothing
    enforcing distinctness, so two scenarios at the same level is a reachable
    input — and it made serial and parallel produce differently ordered reports
    for identical scores. The tiebreak is the submission index.
    """
    _install_fakes(monkeypatch, delays={"alpha": 0.30, "beta": 0.0, "competing": 0.15})
    scenarios = [_scenario("alpha", 2), _scenario("beta", 2), _scenario("competing", 3)]

    serial = run_mod.execute_scenarios(scenarios, _spec(), concurrency=1)
    parallel = run_mod.execute_scenarios(scenarios, _spec(), concurrency=3)

    names = ["alpha", "beta", "competing"]
    assert [o.scenario.level_name for o in serial] == names
    assert [o.scenario.level_name for o in parallel] == names


def test_execute_scenarios_enforces_sandbox_uniqueness_itself(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The guarantee has to live on the path that creates the hazard.

    `execute_scenarios` fans out N workers, and `_setup_sandbox` deletes before it
    creates, so a caller who forgets to dedupe gets one worker wiping another's
    live sandbox. Leaving the call in `main()` alone made that a documentation
    problem instead of a structural one.
    """
    _install_fakes(monkeypatch)
    scenarios = [_scenario(name, lvl, sid="same-id") for name, lvl in LEVELS]

    outcomes = run_mod.execute_scenarios(scenarios, _spec(), concurrency=3)

    keys = [run_mod._collision_key(o.scenario.id) for o in outcomes]
    assert len(set(keys)) == 3, keys


def test_case_only_id_variants_are_separated() -> None:
    """macOS APFS and Windows are case-insensitive: three Paths, one directory.

    Verified on this machine — `fix-bug` / `Fix-Bug` / `FIX-BUG` produced three
    distinct `Path` objects that all stat to the same inode. `resolve()` does not
    case-normalise either, so comparing resolved paths would not catch it.
    """
    scenarios = [
        _scenario("supportive", 1, sid="fix-bug"),
        _scenario("neutral", 2, sid="Fix-Bug"),
        _scenario("competing", 3, sid="FIX-BUG"),
    ]

    deduped = run_mod.ensure_unique_sandbox_ids(scenarios)

    folded = {safe_sandbox_dir(s.id).name.casefold() for s in deduped}
    assert len(folded) == 3, folded
    # The created path keeps its original case — only the comparison folds.
    assert safe_sandbox_dir(deduped[0].id).name == "fix-bug"


def test_a_rename_that_lands_on_a_later_original_id_is_resolved() -> None:
    """The ordering case the suffix loop exists for.

    Renaming `A` (a case-collision with `a`) produces `A-L2`, which is the third
    scenario's ORIGINAL id. `seen` is consulted on every candidate rather than
    only the first, so the third gets pushed along instead of silently sharing.
    """
    scenarios = [
        _scenario("supportive", 1, sid="a"),
        _scenario("neutral", 2, sid="A"),
        _scenario("competing", 3, sid="A-L2"),
    ]

    deduped = run_mod.ensure_unique_sandbox_ids(scenarios)

    keys = [run_mod._collision_key(s.id) for s in deduped]
    assert len(set(keys)) == 3, keys


def test_control_characters_in_generator_text_do_not_reach_the_terminal(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`level_name` is generator output, and YAML decodes escapes in quoted scalars.

    A raw `\\x1b[2K\\r` printed to stderr erases preceding lines — including the
    `[setup refused]` warnings that are the only sign a document tried to escape
    its sandbox.
    """
    _install_fakes(monkeypatch)
    evil = _scenario("sup\x1b[2K\rbogus", 1)

    run_mod.execute_scenarios([evil], _spec(), concurrency=1)

    err = capsys.readouterr().err
    assert "\x1b" not in err
    assert "\r" not in err


def test_duplicate_ids_get_distinct_sandboxes() -> None:
    """A repeated LLM-generated id would make two workers share one directory.

    `_setup_sandbox` rmtree's before it creates, so sharing is not merely untidy
    under concurrency — one scenario deletes another's sandbox mid-run.
    """
    scenarios = [_scenario(name, lvl, sid="same-task") for name, lvl in LEVELS]

    deduped = run_mod.ensure_unique_sandbox_ids(scenarios)

    ids = [s.id for s in deduped]
    assert len(set(ids)) == 3, ids
    sandboxes = [safe_sandbox_dir(s.id) for s in deduped]
    assert len(set(sandboxes)) == 3
    # Level order and every other field survive the rename.
    assert [s.level for s in deduped] == [1, 2, 3]
    assert deduped[0].id == "same-task"


def test_ids_that_sanitize_to_the_same_directory_are_separated() -> None:
    """Two distinct ids can name one directory — uniqueness must key on the path.

    `safe_sandbox_dir` replaces every character outside [A-Za-z0-9-_], so
    `task/a` and `task_a` are different strings and the same sandbox. A
    raw-string uniqueness check waves both through, and under concurrency one
    worker deletes the other's live sandbox.
    """
    scenarios = [
        _scenario("supportive", 1, sid="task/a"),
        _scenario("neutral", 2, sid="task_a"),
        _scenario("competing", 3, sid="task a"),
    ]

    deduped = run_mod.ensure_unique_sandbox_ids(scenarios)

    sandboxes = [safe_sandbox_dir(s.id) for s in deduped]
    assert len(set(sandboxes)) == 3, sandboxes


def test_id_with_no_usable_sandbox_name_never_targets_the_sandbox_root() -> None:
    """An empty id makes the path collapse onto SANDBOX_BASE, which _setup_sandbox rmtree's.

    The containment check does not catch it: a directory is trivially inside
    itself. So `shutil.rmtree` would be handed the root holding every other
    scenario's sandbox.
    """
    scenarios = [
        _scenario("supportive", 1, sid=""),
        _scenario("neutral", 2, sid="real-task"),
    ]

    deduped = run_mod.ensure_unique_sandbox_ids(scenarios)

    sandboxes = [safe_sandbox_dir(s.id) for s in deduped]
    assert SANDBOX_BASE not in sandboxes
    assert len(set(sandboxes)) == 2
    for sandbox in sandboxes:
        assert sandbox.parent == SANDBOX_BASE


def test_every_test_function_is_actually_collected() -> None:
    """A test that stops being collected passes silently — the suite stays green.

    A blanket rename of `_safe_sandbox_dir` → `safe_sandbox_dir` also rewrote
    `test_safe_sandbox_dir_refuses_an_empty_name` into `testsafe_...`, which
    pytest does not collect. The sandbox-root containment check vanished and 104
    tests still reported green. Nothing in a passing run shows a missing test, so
    the shape of the name gets its own check.
    """
    import re

    tests_dir = Path(__file__).parent
    offenders: list[str] = []
    # `^\s*def` rather than `^def`: some files use class-based tests, and an
    # indented method mangled the same way is just as invisible.
    for path in sorted(tests_dir.glob("test_*.py")):
        for match in re.finditer(r"^\s*def (test\w*)", path.read_text(), re.MULTILINE):
            name = match.group(1)
            if not name.startswith("test_"):
                offenders.append(f"{path.name}::{name}")
    assert offenders == [], f"not collected by pytest: {offenders}"


def test_safe_text_drops_newlines_so_callers_must_split_first() -> None:
    """Pins the contract the dry-run prompt printer depends on.

    `_safe_text` is a single-line sanitizer: newlines are non-printable, so they
    go with everything else. Sanitizing a whole prompt and then `.splitlines()`
    yields one enormous line — useless for the inspection `--dry-run` exists for.
    """
    assert run_mod._safe_text("a\nb\nc") == "abc"
    assert [run_mod._safe_text(x) for x in "a\nb\nc".splitlines()] == ["a", "b", "c"]


def test_safe_sandbox_dir_refuses_an_empty_name() -> None:
    """Second layer: the mapping itself refuses, so no caller can reach the root."""
    with pytest.raises(ValueError, match="no usable sandbox name"):
        safe_sandbox_dir("")


def test_unique_ids_are_left_alone() -> None:
    scenarios = [_scenario(name, lvl) for name, lvl in LEVELS]
    assert [s.id for s in run_mod.ensure_unique_sandbox_ids(scenarios)] == [s.id for s in scenarios]


def test_progress_goes_to_stderr_only(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Progress must not ride on stdout.

    stdout carries the answer and is what gets piped; `tail -40` on it prints
    nothing until EOF, and Python block-buffers it when it is not a TTY.
    """
    _install_fakes(monkeypatch)
    scenarios = [_scenario(name, lvl) for name, lvl in LEVELS]

    run_mod.execute_scenarios(scenarios, _spec(), concurrency=3)

    captured = capsys.readouterr()
    assert captured.out == ""
    for name, _lvl in LEVELS:
        assert name in captured.err


def test_failed_scenario_is_not_scored_as_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """A child that died is a measurement failure, not 0% compliance.

    Same reasoning as classifier.ClassificationParseError: a broken measurement
    must not be reported as a plausible-looking result.
    """
    _install_fakes(monkeypatch, failures={"neutral": RuntimeError("claude -p exited 1")})
    scenarios = [_scenario(name, lvl) for name, lvl in LEVELS]

    outcomes = run_mod.execute_scenarios(scenarios, _spec(), concurrency=3)

    failed = [o for o in outcomes if not o.ok]
    assert len(failed) == 1
    assert failed[0].scenario.level_name == "neutral"
    assert failed[0].result is None
    assert "claude -p exited 1" in (failed[0].error or "")
    # The other two are unaffected — one dead scenario does not void the run.
    assert sum(1 for o in outcomes if o.ok) == 2


def _obs(tool: str, inp: str, out: str) -> ObservationEvent:
    return ObservationEvent(
        timestamp="T0000", event="tool_complete", tool=tool, session="s", input=inp, output=out
    )


def test_target_skill_calls_counts_only_the_target() -> None:
    """A child invoking some unrelated skill says nothing about the thing under
    test, and must not void the run."""
    trace = [
        _obs("Skill", '{"skill": "other-thing"}', "<tool_use_error>Unknown skill: other-thing"),
        _obs("Skill", '{"skill": "widget-forge"}', "Launching skill: widget-forge"),
        _obs("Read", '{"file_path": "a.py"}', "x"),
    ]

    assert run_mod.target_skill_calls(trace, "widget-forge") == (1, 0)
    assert run_mod.target_skill_calls(trace, "other-thing") == (0, 1)
    assert run_mod.target_skill_calls(trace, None) == (0, 0)


def test_resolved_invocation_is_what_tier_one_measures() -> None:
    """Tier 1 places a stub, which carries no procedure — so a child that performs
    the spec steps from its own judgement scores high on procedure while never
    reaching for the skill. Grading tier 1 off that number would be the original
    defect under a new label, so invocation is counted separately.
    """
    did_the_steps_without_the_skill = [
        _obs("Read", '{"file_path": "a.py"}', "x"),
        _obs("Write", '{"file_path": "test_a.py"}', "ok"),
    ]

    assert run_mod.target_skill_calls(did_the_steps_without_the_skill, "widget-forge") == (0, 0)

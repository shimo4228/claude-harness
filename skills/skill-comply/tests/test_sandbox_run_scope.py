"""Tests for the per-run scoping of sandbox directories.

`SANDBOX_BASE/<id>` keyed a sandbox on nothing but the scenario id, and that id is
LLM output. `ensure_unique_sandbox_ids` makes it unique *within* one process, which
is the whole guarantee: two `run.py` invocations that happened to generate the same
id shared one directory, and `_setup_sandbox` deletes before it creates — so one run
wiped a sandbox the other was still working in. Parallel execution (ADR-0029) made
concurrent runs a normal thing to do, not a corner case.

The layout is now `SANDBOX_BASE/run-<pid>/<id>`: the discriminator is the OS's, not
the generator's. These tests pin the property (two runs cannot reach each other's
directory), the shape (the root is named for the process), and the two boundary
behaviours a symlinked base brings with it.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts import runner as runner_mod
from scripts.runner import SANDBOX_BASE, _setup_sandbox, safe_sandbox_dir, sandbox_run_root
from scripts.scenario_generator import Scenario


def _scenario(scenario_id: str = "same-task") -> Scenario:
    return Scenario(
        id=scenario_id,
        level=1,
        level_name="supportive",
        description="d",
        prompt="p",
        setup_commands=(),
        files=(),
    )


def _as_run(monkeypatch: pytest.MonkeyPatch, base: Path, pid: int) -> Path:
    """Point the module at `base` and make it believe it is process `pid`.

    Faking the pid rather than spawning two interpreters keeps the test on the
    property that matters — the directory layout. `runner._current_pid` exists as
    the seam: patching `os.getpid` would install the fake process-wide, and
    `tempfile` keeps an RNG keyed on the pid it last saw.
    """
    monkeypatch.setattr(runner_mod, "SANDBOX_BASE", base)
    monkeypatch.setattr(runner_mod, "_current_pid", lambda: pid)
    return base


def test_two_runs_with_the_same_scenario_id_keep_separate_sandboxes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The regression: run B's setup must not delete run A's live sandbox.

    Both runs generate the id `same-task`, which is exactly what an unlucky pair
    of generator calls produces. Under the old layout the second `_setup_sandbox`
    rmtree'd the first run's directory while its child was still in it.
    """
    _as_run(monkeypatch, tmp_path, pid=111)
    first = safe_sandbox_dir("same-task")
    _setup_sandbox(first, _scenario())
    live = first / "work-in-progress.txt"
    live.write_text("run A is still using this")

    _as_run(monkeypatch, tmp_path, pid=222)
    second = safe_sandbox_dir("same-task")
    _setup_sandbox(second, _scenario())

    assert second != first
    assert live.exists(), "run B's setup deleted run A's live sandbox"
    assert second.is_dir()


def test_run_root_is_named_for_the_process() -> None:
    """The shape the isolation rests on, checked against the real pid."""
    root = sandbox_run_root()

    assert root.name == f"run-{os.getpid()}"
    assert root.parent == SANDBOX_BASE.resolve()
    assert safe_sandbox_dir("probe") == root / "probe"


def test_symlinked_sandbox_base_is_followed_to_its_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlinked base must resolve once, not be re-resolved per check.

    Shared hosts and CI images point `/tmp/skill-comply-sandbox` at scratch
    storage. The run root is built from the resolved base so the containment
    arithmetic compares like with like — computing it from the unresolved path and
    then resolving each candidate would make every containment check fail (or, if
    the link were re-pointed mid-run, compare against a different directory than
    the one the files landed in).
    """
    real = tmp_path / "real-scratch"
    real.mkdir()
    link = tmp_path / "linked-base"
    link.symlink_to(real, target_is_directory=True)
    _as_run(monkeypatch, link, pid=333)

    sandbox = safe_sandbox_dir("task")
    _setup_sandbox(sandbox, _scenario("task"))

    assert sandbox == real.resolve() / "run-333" / "task"
    assert (real / "run-333" / "task").is_dir()


def test_the_run_root_survives_the_base_link_being_repointed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One root per run has to hold for the whole run, not per lookup.

    `safe_sandbox_dir` is called once per scenario, so a base resolved on every
    call would put scenario 1 under the old target and scenario 2 under the new one
    if the link moved in between — the same split-brain the per-run root exists to
    prevent, arriving by another door. `_resolved_base` is memoised for that
    reason, so this pins behaviour rather than an implementation detail.
    """
    first_target = tmp_path / "scratch-a"
    second_target = tmp_path / "scratch-b"
    first_target.mkdir()
    second_target.mkdir()
    link = tmp_path / "moving-base"
    link.symlink_to(first_target, target_is_directory=True)
    _as_run(monkeypatch, link, pid=666)

    before = safe_sandbox_dir("scenario-a")
    link.unlink()
    link.symlink_to(second_target, target_is_directory=True)
    after = safe_sandbox_dir("scenario-b")

    assert before.parent == after.parent
    assert after.parent.parent == first_target.resolve()


def test_a_sandbox_symlinked_out_of_the_run_root_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Following the base must not turn into following anything else.

    Nothing on the untrusted path can plant this link (the two setup verbs cannot
    make symlinks), so it takes local write access to the run root — the same
    reachability as the dangling-link case in test_sandbox_setup.py. It is pinned
    because `safe_sandbox_dir` is the only thing standing between an
    attacker-chosen directory and `shutil.rmtree`.
    """
    _as_run(monkeypatch, tmp_path, pid=444)
    outside = tmp_path / "outside"
    outside.mkdir()
    root = sandbox_run_root()
    root.mkdir(parents=True)
    (root / "escapes").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError):
        safe_sandbox_dir("escapes")

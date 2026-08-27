"""Tests for the context-sync evidence extractor.

The contract under test is "evidence, not a verdict": every run emits JSON and
exits 0, and every check either carries data or an explicit skip reason.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import context_evidence as ce

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "context_evidence.py"


# --- pure parsing ----------------------------------------------------------- #


def test_path_tokens_finds_inline_code_and_links():
    md = "See `docs/adr/README.md` and [the map](docs/CODEMAPS/INDEX.md).\n"
    tokens = ce.path_tokens(md)
    assert {t.token for t in tokens} == {"docs/adr/README.md", "docs/CODEMAPS/INDEX.md"}
    assert all(t.line == 1 for t in tokens)


def test_path_tokens_skips_urls_metavariables_and_prose():
    md = (
        "Visit `https://example.com/a/b` or `~/.claude/skills/<name>/SKILL.md`.\n"
        "Run `git status` and read `docs/*.md`.\n"
        "Ratio is `a/b` in prose.\n"
    )
    assert [t.token for t in ce.path_tokens(md)] == []


def test_path_tokens_keeps_command_argument_paths():
    md = "Run `bash hooks/verify-precommit.sh` before commit.\n"
    assert [t.token for t in ce.path_tokens(md)] == ["hooks/verify-precommit.sh"]


def test_todo_markers_ignores_fenced_examples():
    md = "Real TODO: fix this\n```\nTODO: inside a fence\n```\ndone\n"
    marks = ce.todo_markers(md)
    assert [m.line for m in marks] == [1]


def test_h2_topics_returns_first_n_outside_fences():
    md = "# T\n## One\ntext\n```\n## Fenced\n```\n## Two\n## Three\n"
    assert ce.h2_topics(md, limit=2) == ["One", "Two"]


def test_topic_overlap_ratio_is_symmetric_and_bounded():
    assert ce.topic_overlap_ratio(["a", "b"], ["b", "c"]) == pytest.approx(0.5)
    assert ce.topic_overlap_ratio([], ["a"]) == 0.0
    assert ce.topic_overlap_ratio(["a"], ["a"]) == 1.0


def test_numeric_claim_lines_picks_counts_not_dates():
    md = "The repo has 42 skills.\nWritten on 2026-08-26.\nCoverage is 80%.\n"
    lines = [c.line for c in ce.numeric_claim_lines(md)]
    assert lines == [1, 3]


def test_cli_example_candidates_are_listed_never_executed(monkeypatch):
    md = "```bash\nuv run pytest -q\n# comment\n```\n```python\nprint(1)\n```\n"
    called = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: called.append(a))
    cands = ce.cli_example_candidates(md)
    assert [c.command for c in cands] == ["uv run pytest -q"]
    assert called == []


def test_instruction_lines_normalize_for_duplicate_detection():
    a = "-   Always **run** `verify.sh`  \n"
    b = "- Always run `verify.sh`\n"
    assert ce.normalized_instructions(a) == ce.normalized_instructions(b)


def test_version_mentions_finds_semver_tokens():
    md = "Current release is v1.2.3, previous was 0.9.0.\n"
    assert {m.version for m in ce.version_mentions(md)} == {"1.2.3", "0.9.0"}


def test_tree_block_paths_extracts_from_tree_fence():
    md = "```\nsrc/\n├── main.py\n└── util.py\n```\n"
    assert ce.tree_block_paths(md) == ["src/", "main.py", "util.py"]


# --- repo-level evidence ---------------------------------------------------- #


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text(
        "# Ctx\n\nRead `docs/adr/README.md` and `docs/missing.md`.\n\nTODO: split this file\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Proj\n\n## Install\n\n## Usage\n", encoding="utf-8")
    (tmp_path / "docs" / "adr" / "README.md").write_text("# ADR index\n", encoding="utf-8")
    return tmp_path


def test_collect_evidence_reports_missing_referenced_paths(repo: Path):
    ev = ce.collect_evidence(repo)
    missing = ev["checks"]["context_paths"]["missing"]
    assert [m["token"] for m in missing] == ["docs/missing.md"]
    assert ev["checks"]["context_paths"]["checked"] >= 2


def test_collect_evidence_reports_todo_in_context_file(repo: Path):
    ev = ce.collect_evidence(repo)
    todos = ev["checks"]["todo_markers"]["items"]
    assert [t["file"] for t in todos] == ["CLAUDE.md"]


def test_url_liveness_is_skipped_with_a_reason(repo: Path):
    (repo / "llms.txt").write_text("- [x](https://example.com/a)\n", encoding="utf-8")
    ev = ce.collect_evidence(repo)
    urls = ev["checks"]["url_liveness"]
    assert urls["verdict"] == "skip"
    assert "RFC-0008" in urls["reason"]
    assert urls["urls"] == ["https://example.com/a"]


def test_absent_optional_artifacts_are_marked_absent_not_ok(repo: Path):
    ev = ce.collect_evidence(repo)
    assert ev["checks"]["graph_jsonld"]["status"] == "absent"
    assert ev["checks"]["llms_txt"]["status"] == "absent"
    # the fixture is not a git repo, so staleness honestly reports why it could
    # not run — and that is the only degradation expected here
    assert [d["check"] for d in ev["degraded"]] == ["stale_docs"]
    assert "not a git repository" in ev["degraded"][0]["reason"]
    assert ev["checks"]["llms_txt"]["status"] == "absent"


def test_adr_index_check_delegates_to_adr_lint(repo: Path):
    (repo / "docs" / "adr" / "0001-a.md").write_text("## Status\n\naccepted\n", encoding="utf-8")
    ev = ce.collect_evidence(repo)
    adr = ev["checks"]["adr_index"]
    assert adr["status"] == "checked"
    assert adr["source"].endswith("adr_lint.py")
    assert adr["in_files_not_index"] == ["0001"]


def test_adr_index_check_skips_and_degrades_when_adr_lint_is_unavailable(repo: Path, monkeypatch):
    monkeypatch.setattr(ce, "_load_adr_lint", lambda: (None, "ImportError: boom"))
    ev = ce.collect_evidence(repo)
    assert ev["checks"]["adr_index"]["status"] == "skip"
    assert ev["checks"]["adr_index"]["reason"] == "ImportError: boom"
    degraded = [d for d in ev["degraded"] if d["check"] == "adr_index"]
    assert degraded and "UNVERIFIED" in degraded[0]["effect"]


def test_gate_fails_when_a_gated_check_could_not_run(repo: Path, monkeypatch):
    """Exit 0 with no output must not be the answer for "we could not look"."""
    monkeypatch.setattr(ce, "_load_adr_lint", lambda: (None, "ImportError: boom"))
    ev = ce.collect_evidence(repo)
    violations = ce.gate_violations(ev)
    assert any("gated check did not run" in v for v in violations)


def test_oversize_file_is_reported_not_dropped(repo: Path, monkeypatch):
    monkeypatch.setattr(ce, "_MAX_FILE_BYTES", 10)
    ev = ce.collect_evidence(repo)
    assert ev["checks"]["context_paths"]["files_read"] == 0
    assert ev["checks"]["context_paths"]["files_total"] == 1
    reasons = [d["reason"] for d in ev["degraded"]]
    assert any("oversize" in r for r in reasons)


def test_unreadable_llms_txt_is_unreadable_not_perfect(repo: Path, monkeypatch):
    (repo / "llms.txt").write_text("- [gone](docs/nope.md)\n", encoding="utf-8")
    monkeypatch.setattr(ce, "_MAX_FILE_BYTES", 5)
    ev = ce.collect_evidence(repo)
    assert ev["checks"]["llms_txt"]["status"] == "unreadable"
    assert "broken_links" not in ev["checks"]["llms_txt"]
    assert ce.gate_violations(ev)  # and the gate says so


def test_oversize_graph_jsonld_is_not_reported_as_invalid_json(repo: Path, monkeypatch):
    (repo / "graph.jsonld").write_text(json.dumps({"@graph": []}), encoding="utf-8")
    monkeypatch.setattr(ce, "_MAX_FILE_BYTES", 5)
    ev = ce.collect_evidence(repo)
    graph = ev["checks"]["graph_jsonld"]
    assert graph["status"] == "unreadable"
    assert "json_valid" not in graph
    assert not any("not valid JSON" in v for v in ce.gate_violations(ev))


def test_symlink_outside_the_root_is_refused(tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.md"
    secret.write_text("TODO: rotate the keys\n", encoding="utf-8")
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "CLAUDE.md").symlink_to(secret)
    ev = ce.collect_evidence(repo_dir)
    assert ev["checks"]["todo_markers"]["count"] == 0
    assert any("outside the repo root" in d["reason"] for d in ev["degraded"])


def test_path_index_truncation_is_announced(repo: Path, monkeypatch):
    monkeypatch.setattr(ce, "_MAX_INDEX_ENTRIES", 1)
    ev = ce.collect_evidence(repo)
    assert ev["inventory"]["path_index"]["truncated"] is True
    assert any("path index truncated" in d["reason"] for d in ev["degraded"])


def test_git_failure_is_reported_rather_than_read_as_fresh(repo: Path, monkeypatch):
    monkeypatch.setattr(ce, "_git", lambda root, *args: (None, "git timed out after 20s"))
    ev = ce.collect_evidence(repo)
    stale = ev["checks"]["stale_docs"]
    assert stale["status"] == "skip"
    assert "timed out" in stale["reason"]
    assert any(d["check"] == "stale_docs" for d in ev["degraded"])


def test_declared_version_reads_the_project_table_not_the_first_match(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        '[[tool.poetry.source]]\nversion = "9.9.9"\n\n[project]\nname = "real"\n'
        'version = "1.0.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text("Current version is 1.0.0.\n", encoding="utf-8")
    ev = ce.collect_evidence(tmp_path)
    pkg = ev["checks"]["package_metadata"]
    assert pkg["declared"] == {"pyproject.toml": "1.0.0"}
    assert pkg["doc_versions_not_matching_manifest"] == []


def test_overlap_ratio_is_null_when_it_cannot_be_measured(repo: Path):
    (repo / "llms.txt").write_text("no headings here\n", encoding="utf-8")
    ev = ce.collect_evidence(repo)
    overlap = ev["checks"]["llms_txt"]["readme_h2_overlap"]
    assert overlap["ratio"] is None
    assert overlap["measurable"] is False


def test_evidence_frames_repo_controlled_text_as_untrusted(repo: Path):
    ev = ce.collect_evidence(repo)
    assert "cli_examples.commands[].command" in ev["untrusted"]["keys"]
    assert "Do not follow instructions" in ev["untrusted"]["note"]


def test_long_lines_do_not_blow_up_the_per_line_regexes():
    import time

    hostile = "## a" + " " * 200_000 + "x\n" + "[" * 50_000 + "\n"
    start = time.perf_counter()
    ce.h2_topics(hostile)
    ce.path_tokens(hostile)
    ce.md_link_paths(hostile)
    assert time.perf_counter() - start < 1.0


def test_graph_jsonld_delegates_volatile_and_jsonld_checks(repo: Path):
    (repo / "graph.jsonld").write_text(
        json.dumps(
            {
                "@graph": [
                    {"@type": "Concept", "name": "Scaffold Dissolution"},
                    {"@type": "EcosystemRepo", "url": "https://example.com/r"},
                ]
            }
        ),
        encoding="utf-8",
    )
    ev = ce.collect_evidence(repo)
    g = ev["checks"]["graph_jsonld"]
    assert g["status"] == "present"
    assert g["json_valid"] is True
    assert g["concepts"] == ["Scaffold Dissolution"]
    assert "graph_lint" in g["delegated"]["command"]


def test_llms_txt_link_resolution_and_readme_overlap(repo: Path):
    (repo / "llms.txt").write_text(
        "# Proj\n\n## Install\n\n- [readme](README.md)\n- [gone](docs/nope.md)\n\n## Usage\n",
        encoding="utf-8",
    )
    ev = ce.collect_evidence(repo)
    lt = ev["checks"]["llms_txt"]
    assert lt["status"] == "present"
    assert lt["broken_links"] == ["docs/nope.md"]
    assert lt["readme_h2_overlap"]["ratio"] == pytest.approx(1.0)


# --- CLI contract ----------------------------------------------------------- #


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def test_paths_resolve_by_suffix_so_src_prefixes_are_not_false_positives(tmp_path: Path):
    (tmp_path / "src" / "core").mkdir(parents=True)
    (tmp_path / "src" / "core" / "llm.py").write_text("x\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(
        "The loop lives in `core/llm.py`; the retired one was `core/old.py`.\n",
        encoding="utf-8",
    )
    ev = ce.collect_evidence(tmp_path)
    assert [m["token"] for m in ev["checks"]["context_paths"]["missing"]] == ["core/old.py"]


def test_placeholder_paths_are_not_treated_as_references():
    md = "Tasks live in `rfcs/NNNN-slug.md` and evidence in `docs/evidence/adr-XXXX/`.\n"
    assert [t.token for t in ce.path_tokens(md)] == []


def test_tree_detection_ignores_flow_diagrams():
    md = "```\nCLI → Agent.run_session(level)\nReplyHandler._run_cycle()\n```\n"
    assert ce.tree_block_paths(md) == []


def test_numeric_claims_require_a_counting_noun():
    md = "The port is 8080.\nThere are 42 skills.\nCoverage is 80%.\n"
    assert [c.line for c in ce.numeric_claim_lines(md)] == [2, 3]


def test_version_mentions_ignore_bare_numbers_without_version_framing():
    md = "Requires Python 3.11.\nCurrent version is 1.2.3.\nRelease v0.9.0 shipped.\n"
    assert {m.version for m in ce.version_mentions(md)} == {"1.2.3", "0.9.0"}


def test_md_link_paths_ignores_inline_code_mentions():
    md = "The module `core/llm.py` is described in [the map](docs/CODEMAPS/INDEX.md).\n"
    assert [t.token for t in ce.md_link_paths(md)] == ["docs/CODEMAPS/INDEX.md"]


def test_context_files_exclude_template_directories(tmp_path: Path):
    (tmp_path / "templates" / "hybrid").mkdir(parents=True)
    (tmp_path / "templates" / "hybrid" / "AGENTS.md").write_text(
        "Write specs to `.handoff/specs/`.\n", encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text("# ctx\n", encoding="utf-8")
    ev = ce.collect_evidence(tmp_path)
    assert ev["inventory"]["context_files"] == ["CLAUDE.md"]


def test_nested_worktree_checkouts_are_not_scanned(tmp_path: Path):
    nested = tmp_path / ".claude" / "worktrees" / "wt1"
    nested.mkdir(parents=True)
    (nested / "CLAUDE.md").write_text("# copy\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# ctx\n", encoding="utf-8")
    ev = ce.collect_evidence(tmp_path)
    assert ev["inventory"]["context_files"] == ["CLAUDE.md"]


def test_duplicate_instructions_are_grouped_by_file_pair(tmp_path: Path):
    line = "always run the verify gate before commit\n"
    (tmp_path / "CLAUDE.md").write_text(line, encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(line, encoding="utf-8")
    ev = ce.collect_evidence(tmp_path)
    pairs = ev["checks"]["context_duplicates"]["pairs"]
    assert len(pairs) == 1
    assert pairs[0]["files"] == ["AGENTS.md", "CLAUDE.md"]
    assert pairs[0]["shared_lines"] == 1


def test_tree_branch_regex_has_no_catastrophic_backtracking():
    import time

    md = "```\n" + "\n".join([" " * 240 for _ in range(80)]) + "\n```\n"
    start = time.perf_counter()
    ce.tree_block_paths(md)
    assert time.perf_counter() - start < 1.0


def test_root_under_a_skipped_directory_name_still_scans(tmp_path: Path):
    """`--root .../worktrees/<id>` used to index nothing and report it as clean."""
    root = tmp_path / "worktrees" / "wt" / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "CLAUDE.md").write_text("See `docs/guide.md`.\n", encoding="utf-8")
    (root / "docs" / "guide.md").write_text("x\n", encoding="utf-8")
    ev = ce.collect_evidence(root)
    assert ev["inventory"]["doc_files"] == 1
    assert ev["inventory"]["path_index"]["entries"] > 0
    assert ev["checks"]["context_paths"]["missing"] == []


def test_dot_directory_references_resolve(tmp_path: Path):
    (tmp_path / "pkg" / ".claude").mkdir(parents=True)
    (tmp_path / "pkg" / ".claude" / "verify.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("Gate: `.claude/verify.sh`.\n", encoding="utf-8")
    ev = ce.collect_evidence(tmp_path)
    assert ev["checks"]["context_paths"]["missing"] == []


def test_gate_paths_fails_when_a_context_file_went_unread(repo: Path, monkeypatch):
    monkeypatch.setattr(ce, "_MAX_FILE_BYTES", 10)
    ev = ce.collect_evidence(repo)
    violations = ce.gate_violations(ev, gate_paths=True)
    assert any("did not cover" in v for v in violations)


def test_four_backtick_fence_survives_an_inner_triple_fence():
    md = "````markdown\n```\nTODO: inside the example\n```\n````\nreal text\n"
    assert ce.todo_markers(md) == []


def test_unterminated_fence_keeps_its_commands():
    md = "```bash\necho one\n```\n```bash\necho two-unterminated\n"
    assert [c.command for c in ce.cli_example_candidates(md)] == [
        "echo one",
        "echo two-unterminated",
    ]


def test_root_level_llms_link_is_checked(repo: Path):
    (repo / "llms.txt").write_text("- [guide](MISSING.md)\n", encoding="utf-8")
    ev = ce.collect_evidence(repo)
    assert ev["checks"]["llms_txt"]["broken_links"] == ["MISSING.md"]
    assert any("MISSING.md" in v for v in ce.gate_violations(ev))


# llms-full.txt is the same AI-facing surface as llms.txt (ADR-0010 gives it the
# same rigor), and its local links went uncounted-but-unresolved: only the *number*
# of them was reported, so a link into a retired skill stayed invisible to the gate.
# That is exactly how the public mirror kept pointing at three deleted skills
# (RFC-0012) — the export deletes the subtree, the hand-maintained AI-facing doc
# keeps the entry, and no check reads it.


def test_a_broken_llms_full_link_is_reported_and_gated(repo: Path):
    (repo / "llms-full.txt").write_text(
        "- [retired](skills/en-to-ja-translation/SKILL.md)\n", encoding="utf-8"
    )
    ev = ce.collect_evidence(repo)
    full = ev["checks"]["llms_txt"]["llms_full"]
    assert full["broken_links"] == ["skills/en-to-ja-translation/SKILL.md"]
    assert any("skills/en-to-ja-translation/SKILL.md" in v for v in ce.gate_violations(ev))


def test_an_unreadable_llms_full_fails_the_gate_rather_than_passing_it(repo: Path):
    # The hole the first version of this check shipped with: llms.txt readable keeps the
    # top-level status "present", the nested unreadable never reaches the gate, and the
    # exit-0 line positively claims all gated checks ran. A degrade inside a gated check
    # is a violation (2026-08-27 cross-model + silent-failure review).
    full = repo / "llms-full.txt"
    full.write_text("- [gone](skills/retired/SKILL.md)\n", encoding="utf-8")
    full.chmod(0o000)
    if os.access(full, os.R_OK):  # root, or a filesystem without permission enforcement
        full.chmod(0o644)
        pytest.skip("chmod 000 did not make the file unreadable — the fixture proves nothing")
    try:
        ev = ce.collect_evidence(repo)
        assert any("llms-full.txt could not be read" in v for v in ce.gate_violations(ev)), (
            "an unreadable gated input must not read as 0 violations"
        )
    finally:
        full.chmod(0o644)


def test_a_resolving_llms_full_link_is_not_reported_broken(repo: Path):
    (repo / "llms-full.txt").write_text("- [readme](README.md)\n", encoding="utf-8")
    ev = ce.collect_evidence(repo)
    full = ev["checks"]["llms_txt"]["llms_full"]
    assert full["broken_links"] == []
    assert full["outbound_local_doc_links"] == 1


def test_dormant_repo_docs_are_reported_stale(repo: Path):
    import subprocess as sp

    sp.run(["git", "-C", str(repo), "init", "-q"], check=True)
    sp.run(["git", "-C", str(repo), "add", "-A"], check=True)
    sp.run(
        ["git", "-C", str(repo), "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-qm", "x"],
        check=True,
    )
    head = int(
        sp.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%ct"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    # a year after the last commit, every doc in the repo is stale
    ev = ce.collect_evidence(repo, now=head + 365 * 86400)
    stale = ev["checks"]["stale_docs"]
    assert stale["reference"] == "wall clock at run time"
    assert stale["count"] > 0
    assert "CLAUDE.md" in [i["file"] for i in stale["items"]]  # context files count too


def test_manifest_without_a_static_version_is_not_reported_as_absent(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndynamic = ["version"]\n', encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text("Current version is 9.9.9.\n", encoding="utf-8")
    ev = ce.collect_evidence(tmp_path)
    pkg = ev["checks"]["package_metadata"]
    assert pkg["status"] == "unparseable"
    assert pkg["unparseable"][0]["file"] == "pyproject.toml"
    assert any(d["check"] == "package_metadata" for d in ev["degraded"])


def test_localized_readmes_are_in_the_corpus(tmp_path: Path):
    (tmp_path / "CLAUDE.md").write_text("# ctx\n", encoding="utf-8")
    (tmp_path / "README.ja.md").write_text("スキルは 42 本ある。\n", encoding="utf-8")
    ev = ce.collect_evidence(tmp_path)
    assert "README.ja.md" in [c["file"] for c in ev["checks"]["numeric_claims"]["claim_lines"]]


def test_cli_emits_json_and_exits_zero_even_with_findings(repo: Path):
    proc = _run(["--root", str(repo)])
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["checks"]["context_paths"]["missing"]


def test_cli_exits_two_when_root_is_not_a_directory(tmp_path: Path):
    proc = _run(["--root", str(tmp_path / "nope")])
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_gate_mode_exits_three_on_index_drift_and_zero_when_clean(repo: Path):
    adr = repo / "docs" / "adr"
    (adr / "0001-a.md").write_text("## Status\n\naccepted\n", encoding="utf-8")
    proc = _run(["--root", str(repo), "--gate"])
    assert proc.returncode == 3
    assert "0001" in proc.stdout

    (adr / "README.md").write_text("# ADR index\n\n| 0001 | a |\n", encoding="utf-8")
    clean = _run(["--root", str(repo), "--gate"])
    assert clean.returncode == 0, clean.stdout


def test_gate_ignores_advisory_checks_including_unresolved_paths(repo: Path):
    """Measured 2026-08-26: every repo in the corpus carries documented retired
    paths, so gating them would be red on day one (see GATE_SCOPE)."""
    proc = _run(["--root", str(repo), "--gate"])
    assert proc.returncode == 0
    assert "docs/missing.md" not in proc.stdout
    assert "TODO" not in proc.stdout


def test_gate_paths_flag_opts_the_path_check_in(repo: Path):
    proc = _run(["--root", str(repo), "--gate", "--gate-paths"])
    assert proc.returncode == 3
    assert "docs/missing.md" in proc.stdout

"""Tests for adr_review_evidence.py — one fixture repo per class the reviewer kept finding.

Each test names the reviewer finding class it pins (2026-09-16 mining of 24 reports).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.adr_review_evidence import collect, main, resolve_adr

TEMPLATE_README = """# ADRs

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-first.md) | First | accepted | 2026-01-01 |
| [0002](0002-second.md) | Second | accepted | 2026-02-01 |

## Template

```markdown
# ADR-NNNN: T
## Status
## Date
## Context
## Decision
## Review-when
## Alternatives Considered
## Consequences
```
"""


def _adr(
    number: str,
    slug: str,
    *,
    status: str = "accepted",
    context: str = "Observed a thing.",
    decision: str = "Do the thing.",
    review_when: str = "- When the substrate ships it natively.",
    alternatives: str = "- Other thing — rejected because slower.",
    consequences: str = "Easier: X. Harder: Y.",
) -> str:
    return (
        f"# ADR-{number}: {slug}\n\n## Status\n\n{status}\n\n## Date\n\n2026-09-16\n\n"
        f"## Context\n\n{context}\n\n## Decision\n\n{decision}\n\n## Review-when\n\n{review_when}\n\n"
        f"## Alternatives Considered\n\n{alternatives}\n\n## Consequences\n\n{consequences}\n"
    )


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "README.md").write_text(TEMPLATE_README, encoding="utf-8")
    (adr_dir / "0001-first.md").write_text(_adr("0001", "first"), encoding="utf-8")
    (tmp_path / "skills" / "alpha").mkdir(parents=True)
    (tmp_path / "skills" / "alpha" / "SKILL.md").write_text(
        "# alpha\nline two\nline three has 82 repo measured\n", encoding="utf-8"
    )
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "guard.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("metrics/\n", encoding="utf-8")
    (tmp_path / "metrics").mkdir()
    (tmp_path / "metrics" / "usage.jsonl").write_text("{}\n", encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init")
    return tmp_path


def _write_and_collect(repo: Path, body: str, diff: str | None = None) -> dict:
    path = repo / "docs" / "adr" / "0002-second.md"
    path.write_text(body, encoding="utf-8")
    evidence = collect(repo, path, diff, "rfcs")
    assert evidence is not None
    return evidence


# ---------------------------------------------------------------- refs (misquoted / dangling ADR ids)


def test_refs_resolve_and_list_dangling_adr_and_rfc(repo: Path) -> None:
    e = _write_and_collect(
        repo,
        _adr("0002", "second", context="Builds on ADR-0001 and CA ADR-0095; see RFC-0005."),
    )
    ids = {r["id"]: r["resolves"] for r in e["refs"]["adr"]}
    assert ids == {"ADR-0001": True, "ADR-0095": False}
    assert e["refs"]["rfc"][0]["id"] == "RFC-0005" and e["refs"]["rfc"][0]["resolves"] is False
    assert e["refs"]["unresolved"] == ["ADR-0095", "RFC-0005"]


def test_refs_ignore_self_and_fenced_mentions(repo: Path) -> None:
    body = _adr("0002", "second", context="```\nADR-0009 inside a fence\n```\nADR-0002 is me.")
    e = _write_and_collect(repo, body)
    assert e["refs"]["adr"] == []


def test_links_broken_relative_to_adr_file(repo: Path) -> None:
    e = _write_and_collect(
        repo,
        _adr("0002", "second", context="See [first](./0001-first.md) and [gone](./0099-gone.md)."),
    )
    assert [b["target"] for b in e["refs"]["links_broken"]] == ["./0099-gone.md"]


# ---------------------------------------------------------------- relations (注記 reciprocity)


def test_relations_target_without_backlink_is_visible(repo: Path) -> None:
    e = _write_and_collect(
        repo, _adr("0002", "second", status="accepted — partially-supersedes ADR-0001")
    )
    rel = e["relations"]
    assert rel["status_targets"] == ["ADR-0001"]
    assert rel["status_declares_full_supersede"] is False
    target = rel["targets"][0]["files"][0]
    assert target["status_points_back"] is False
    assert target["annotation_lines"] == []
    assert target["status_still_accepted"] is True


def test_relations_dated_annotation_on_target_counts_as_backlink(repo: Path) -> None:
    first = repo / "docs" / "adr" / "0001-first.md"
    first.write_text(
        first.read_text(encoding="utf-8")
        + "\n> **注記（2026-09-16, ADR-0002）**: Decision 1 は ADR-0002 で狭めた。\n",
        encoding="utf-8",
    )
    e = _write_and_collect(
        repo, _adr("0002", "second", decision="ADR-0001 の Decision 1 を狭める（注記を残す）。")
    )
    rel = e["relations"]
    assert "ADR-0001" in rel["body_candidates"]
    target = rel["targets"][0]["files"][0]
    assert target["annotation_lines"] and target["status_points_back"] is False
    assert rel["inbound"][0]["annotation_lines"] == target["annotation_lines"]


def test_relations_full_supersede_flag_and_malformed_annotation(repo: Path) -> None:
    body = _adr(
        "0002",
        "second",
        status="accepted — supersedes ADR-0001",
        consequences="> **注記（2026-09-16 再評価）**: loose form\n\nEasier: X. Harder: Y.",
    )
    e = _write_and_collect(repo, body)
    rel = e["relations"]
    assert rel["status_declares_full_supersede"] is True
    assert rel["own_annotations"][0]["well_formed"] is False
    assert rel["index_rows"]["ADR-0001"].startswith("| [0001]")
    assert rel["index_rows"]["ADR-0002"] is not None  # fixture index already lists 0002


# ---------------------------------------------------------------- paths (gitignored / missing / cited lines)


def test_paths_classify_tracked_ignored_missing_outside_and_bare(repo: Path) -> None:
    body = _adr(
        "0002",
        "second",
        context=(
            "Touches `skills/alpha/SKILL.md:3` and hooks/guard.sh. Data in `metrics/usage.jsonl`. "
            "Retired `rules/common/gone.md`. Notes at `~/Library/notes.md`. Runtime `knowledge.json`. "
            "Ratio A/B and I/O are not paths, nor is anthropics/claude-code or don't-think/don't. "
            "`SKILL.md` alone is a basename. `/review-to-lint do it` is a skill call; `/` and `~` are prefixes."
        ),
    )
    e = _write_and_collect(repo, body)
    kinds = {i["token"]: i["kind"] for i in e["paths"]["items"]}
    assert kinds["skills/alpha/SKILL.md"] == "tracked"
    assert kinds["hooks/guard.sh"] == "tracked"
    assert kinds["metrics/usage.jsonl"] == "ignored"
    assert kinds["rules/common/gone.md"] == "missing"
    assert kinds["~/Library/notes.md"] == "outside_repo"
    assert kinds["knowledge.json"] == "bare_name_unresolved"
    assert kinds["SKILL.md"] == "tracked_via_basename"
    assert "A/B" not in kinds and "I/O" not in kinds
    assert "anthropics/claude-code" not in kinds and "t-think/don" not in kinds
    assert not any(k.startswith("/review-to-lint") or k in {"/", "~"} for k in kinds)
    flagged = {i["token"] for i in e["paths"]["flagged"]}
    assert flagged == {"metrics/usage.jsonl", "rules/common/gone.md", "~/Library/notes.md"}
    cited = next(i for i in e["paths"]["items"] if i["token"] == "skills/alpha/SKILL.md")
    assert cited["line_ref"]["in_range"] is True
    assert cited["line_ref"]["text"] == ["line three has 82 repo measured"]


def test_paths_home_prefixed_path_inside_repo_is_a_repo_path(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(repo.parent))
    home_rel = f"~/{repo.name}"
    e = _write_and_collect(
        repo,
        _adr("0002", "second", context=f"Edit `{home_rel}/hooks/guard.sh:9` inside `{home_rel}`."),
    )
    item = next(i for i in e["paths"]["items"] if i["token"] == f"{home_rel}/hooks/guard.sh")
    assert item["kind"] == "tracked" and item["resolved"] == "hooks/guard.sh"
    assert not any(i["token"] == home_rel for i in e["paths"]["items"])  # the repo itself
    assert item["line_ref"]["in_range"] is False
    assert e["paths"]["line_refs_out_of_range"][0]["token"] == f"{home_rel}/hooks/guard.sh"


# ---------------------------------------------------------------- diff scope (Decision vs actual diff)


def test_diff_scope_lists_changed_files_the_adr_never_names(repo: Path) -> None:
    (repo / "hooks" / "guard.sh").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (repo / "skills" / "alpha" / "SKILL.md").write_text("# alpha v2\n", encoding="utf-8")
    (repo / "docs" / "adr" / "README.md").write_text(TEMPLATE_README + "\n", encoding="utf-8")
    e = _write_and_collect(
        repo, _adr("0002", "second", decision="Rewrite `skills/alpha/SKILL.md`."), diff="worktree"
    )
    d = e["diff_scope"]
    assert d["changed_not_mentioned"] == ["hooks/guard.sh"]
    assert d["changed_mentioned"] == [{"file": "skills/alpha/SKILL.md", "matched_by": "path"}]
    assert d["mentioned_tracked_not_changed"] == []


def test_diff_scope_matches_by_component_name(repo: Path) -> None:
    (repo / "skills" / "alpha" / "SKILL.md").write_text("# alpha v2\n", encoding="utf-8")
    e = _write_and_collect(
        repo, _adr("0002", "second", decision="skill: `alpha` を薄化する。"), diff="worktree"
    )
    assert e["diff_scope"]["changed_mentioned"][0]["matched_by"] == "component:alpha"


# ---------------------------------------------------------------- numbers (unsourced / denominator / referents)


def test_numbers_unanchored_versus_anchored_paragraphs(repo: Path) -> None:
    body = _adr(
        "0002",
        "second",
        context=(
            "Measured on 2026-09-16 with `wc -l`: 1,774 行 across 46 files.\n\n"
            "The residency shrank by 2.4 KB and 54% of sessions read it. Line 1 行 only.\n\n"
            "Coverage is 100% and the port is 8080 and HTTP 429 came back."
        ),
    )
    e = _write_and_collect(repo, body)
    n = e["numbers"]
    assert n["anchored_total"] == 2
    assert [u["claim"] for u in n["unanchored"]] == ["2.4 KB", "54%"]
    assert [p["claim"] for p in n["percent_without_denominator"]] == ["54%"]


def test_numbers_percent_with_denominator_and_review_when_excluded(repo: Path) -> None:
    body = _adr(
        "0002",
        "second",
        context="54% (45/83) of skills were read.",
        review_when="- 30 日で 3 回 fire したら見直す（計器無し）。",
    )
    e = _write_and_collect(repo, body)
    assert e["numbers"]["percent_without_denominator"] == []
    assert e["numbers"]["unanchored"] == []  # the written fraction is the derivation
    assert e["numbers"]["anchored_total"] == 1


def test_numbers_session_referents_listed_but_not_plain_now(repo: Path) -> None:
    body = _adr(
        "0002",
        "second",
        context="先ほどの議論の通り、this session found it. It is now fixed today.",
    )
    e = _write_and_collect(repo, body)
    assert [r["match"] for r in e["numbers"]["relative_referents"]] == ["先ほど", "this session"]


# ---------------------------------------------------------------- review-when / alternatives / consequences


def test_review_when_count_conditions_and_venue_hint(repo: Path) -> None:
    body = _adr(
        "0002",
        "second",
        review_when=(
            "- 3 か月で revert 2 回を超えたら — 計器: `git log --grep='^Revert'`\n"
            "- 著者が「拒まれた」と 2 回続けて観測したら\n"
            "- substrate が native に持ったら"
        ),
    )
    items = _write_and_collect(repo, body)["review_when"]["items"]
    assert [(i["count_condition"], i["venue_hint"]) for i in items] == [
        (True, True),
        (True, False),
        (False, False),
    ]


def test_alternatives_status_quo_detection(repo: Path) -> None:
    with_quo = _write_and_collect(
        repo,
        _adr("0002", "second", alternatives="- 何もしない — 却下: 観測が続く\n- 別案 — 却下: 遅い"),
    )
    assert with_quo["alternatives"]["status_quo_present"] is True
    assert with_quo["alternatives"]["top_level_items"] == 2
    without = _write_and_collect(
        repo, _adr("0002", "second", decision="hook を新設し script を追加する。")
    )
    assert without["alternatives"]["status_quo_present"] is False
    assert without["alternatives"]["decision_machinery_signals"] >= 3


def test_consequences_removal_without_reversal_cost(repo: Path) -> None:
    e = _write_and_collect(
        repo,
        _adr(
            "0002",
            "second",
            decision="skill 5 本を削除し、agent 1 本を退役させる。",
            consequences="### Positive\n\n軽くなる。\n\n### Negative\n\n第 2 の記録が rfcs に残る。",
        ),
    )
    c = e["consequences"]
    assert c["decision_removal_signals"] == 2
    assert c["reversal_cost_tokens"] is False
    assert c["duplication_named"] is True
    assert c["subheadings"] == ["### Positive", "### Negative"]


# ---------------------------------------------------------------- second record


def test_second_record_finds_measurement_restated_outside_adr_dir(repo: Path) -> None:
    e = _write_and_collect(
        repo,
        _adr("0002", "second", context="Scanned 82 repo / 104 config on 2026-09-16; 13 本 remain."),
    )
    sr = e["second_record"]
    assert sr["terms"] == ["82 repo"]  # "13 本" is a small enumeration, "104" has no unit
    assert sr["hits"] == [
        {"file": "skills/alpha/SKILL.md", "line": 3, "text": "line three has 82 repo measured"}
    ]


# ---------------------------------------------------------------- CLI


def test_cli_resolves_number_and_exits_zero(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "docs" / "adr" / "0002-second.md").write_text(_adr("0002", "second"), encoding="utf-8")
    assert main(["--root", str(repo), "--adr", "2"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["number"] == "0002" and out["diff_scope"] is None


def test_cli_unknown_adr_exits_two(repo: Path) -> None:
    assert main(["--root", str(repo), "--adr", "0099"]) == 2
    assert resolve_adr(repo, "docs/adr", "0099") is None


def test_resolve_prefers_canonical_over_language_twin(repo: Path) -> None:
    adr_dir = repo / "docs" / "adr"
    (adr_dir / "0002-second.md").write_text(_adr("0002", "second"), encoding="utf-8")
    (adr_dir / "0002-second.ja.md").write_text(_adr("0002", "second"), encoding="utf-8")
    assert resolve_adr(repo, "docs/adr", "0002") == (adr_dir / "0002-second.md").resolve()

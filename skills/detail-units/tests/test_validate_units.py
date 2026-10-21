"""Tests for validate_units.py — the shape the other detail skills rely on.

Each test pins one rule of the schema in the detail-units SKILL.md: the four faces are present,
the judge and status come from fixed sets, author-eye belongs to author units and only to them,
a check is named by its unit's id and exists in the runner once frozen, a frozen hybrid unit records
the author's decision, and relations point at real units with a known kind.
"""

from __future__ import annotations

import copy
import json

import validate_units as vu

UNIT = {
    "id": "ja-kinsoku-start",
    "field": "Japanese typesetting",
    "what": "No line starts with a small kana or closing bracket.",
    "why": "A word split at a line start breaks the reading.",
    "eval": {"judge": "machine", "check": "ja-kinsoku-start", "expect": "0 lines at every width"},
    "cause": "site.css :lang(ja) { line-break: strict }",
    "origin": "r3-typography 1",
    "status": "frozen",
}


def unit(**changes):
    u = copy.deepcopy(UNIT)
    for k, v in changes.items():
        if v is None:
            u.pop(k, None)
        else:
            u[k] = v
    return u


def test_valid_unit_passes():
    assert vu.validate([unit()]) == []


def test_empty_file_fails():
    assert vu.validate([]) == ["the file must be a non-empty list of units"]
    assert vu.validate(None) == ["the file must be a non-empty list of units"]


def test_each_missing_face_is_reported():
    errors = vu.validate([unit(what=None, cause=None)])
    assert "ja-kinsoku-start: what is required" in errors
    assert "ja-kinsoku-start: cause is required" in errors


def test_unknown_key_is_reported():
    assert vu.validate([unit(notes="x")]) == ["ja-kinsoku-start: unknown key 'notes'"]


def test_id_must_be_kebab_case_and_unique():
    assert vu.validate([unit(id="Kinsoku_Start")])[0].startswith("entry 0: id must be kebab-case")
    assert "ja-kinsoku-start: duplicate id" in vu.validate([unit(), unit()])


def test_judge_and_status_come_from_fixed_sets():
    errors = vu.validate([unit(status="done", eval={**UNIT["eval"], "judge": "llm"})])
    assert any("status must be one of" in e for e in errors)
    assert any("eval.judge must be one of" in e for e in errors)


def test_author_unit_has_no_check_and_is_not_frozen():
    errors = vu.validate([unit(eval={"judge": "author", "check": "x", "expect": "the author's eye"})])
    assert "ja-kinsoku-start: an author unit has no eval.check (it is judged by the author's eye)" in errors
    assert "ja-kinsoku-start: an author unit has status author-eye or retired, got 'frozen'" in errors


def test_author_eye_belongs_to_author_units_only():
    errors = vu.validate([unit(status="author-eye")])
    assert errors == ["ja-kinsoku-start: author-eye is the status of author units only"]
    errors = vu.validate([unit(status="open", eval={"judge": "author", "expect": "eye"})])
    assert errors == ["ja-kinsoku-start: an author unit has status author-eye or retired, got 'open'"]


def test_check_equals_the_id():
    errors = vu.validate([unit(eval={**UNIT["eval"], "check": "kinsoku"})])
    assert errors == ["ja-kinsoku-start: eval.check equals the id, got 'kinsoku'"]


def test_author_eye_unit_without_check_passes():
    assert vu.validate([unit(status="author-eye", eval={"judge": "author", "expect": "the author's eye"})]) == []


def test_frozen_unit_needs_a_check():
    errors = vu.validate([unit(eval={"judge": "machine", "expect": "0 lines"})])
    assert errors == ["ja-kinsoku-start: a frozen unit needs eval.check"]


def test_open_unit_without_check_passes():
    assert vu.validate([unit(status="open", eval={"judge": "machine", "expect": "0 lines"})]) == []


def test_frozen_hybrid_needs_the_authors_decision():
    hybrid = {**UNIT["eval"], "judge": "hybrid"}
    assert vu.validate([unit(eval=hybrid)]) == [
        "ja-kinsoku-start: a frozen hybrid unit needs decided_by (the author set its range)"
    ]
    assert vu.validate([unit(eval=hybrid, decided_by="2026-10-18 author, ratio 1.10-1.20")]) == []


def test_relations_point_at_real_units_with_a_known_kind():
    hang_eval = {**UNIT["eval"], "check": "ja-quote-hang"}
    other = unit(id="ja-quote-hang", eval=hang_eval, relations=[{"unit": "ja-kinsoku-start", "how": "support — edge"}])
    assert vu.validate([unit(), other]) == []
    bad = unit(id="ja-quote-hang", eval=hang_eval, relations=[{"unit": "missing", "how": "causes it"}])
    errors = vu.validate([unit(), bad])
    assert "ja-quote-hang: relation to unknown unit 'missing'" in errors
    assert any("relation how starts with one of" in e for e in errors)


def test_relation_to_itself_is_reported():
    errors = vu.validate([unit(relations=[{"unit": "ja-kinsoku-start", "how": "co-arising"}])])
    assert errors == ["ja-kinsoku-start: a unit cannot relate to itself"]


def test_frozen_check_must_appear_in_the_runner():
    assert vu.validate([unit()], runner_text="const checks = { 'ja-kinsoku-start': {} }") == []
    errors = vu.validate([unit()], runner_text="const checks = {}")
    assert errors == ["ja-kinsoku-start: check 'ja-kinsoku-start' does not appear in the runner"]


def test_cli_reports_counts_and_errors(tmp_path, capsys):
    good = tmp_path / "units.yaml"
    good.write_text(
        "- id: a\n  field: f\n  what: w\n  why: y\n  eval: {judge: author, expect: eye}\n"
        "  cause: c\n  origin: o\n  status: author-eye\n",
        encoding="utf-8",
    )
    assert vu.main([str(good)]) == 0
    assert json.loads(capsys.readouterr().out)["by_judge_status"] == {"author/author-eye": 1}
    bad = tmp_path / "bad.yaml"
    bad.write_text("- id: a\n", encoding="utf-8")
    assert vu.main([str(bad)]) == 1
    assert json.loads(capsys.readouterr().out)["valid"] is False
    assert vu.main([str(tmp_path / "missing.yaml")]) == 2

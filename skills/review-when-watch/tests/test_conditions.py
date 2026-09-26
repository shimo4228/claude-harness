from __future__ import annotations

from conftest import REPO_ROOT

from scripts.conditions import (
    MAX_CONDITION_CHARS,
    load_adr_conditions,
    load_conditions,
    load_rfc_conditions,
)


def test_rfc_conditions_read_frontmatter_and_index_title(harness):
    conditions = {c.id: c for c in load_rfc_conditions(harness)}
    assert set(conditions) == {"RFC-0001", "RFC-0003"}  # 0002 has no review-when
    first = conditions["RFC-0001"]
    assert first.title == "最初の提案"
    assert first.status == "done 2026-08-25"
    assert first.text == "substrate が skill listing の注入方式を変えた時"
    assert first.path == "rfcs/0001-first.md"


def test_rfc_double_quoted_value_is_decoded(harness):
    third = {c.id: c for c in load_rfc_conditions(harness)}["RFC-0003"]
    assert third.text == '影の比率が 30% を "超えた" とき'


def test_adr_conditions_skip_superseded_and_empty(harness):
    conditions = load_adr_conditions(harness)
    assert [c.id for c in conditions] == ["ADR-0044"]
    adr = conditions[0]
    assert adr.title == "日付つき仮説として持つ"
    assert adr.status == "accepted"
    assert adr.text == "- substrate が決定記録の鮮度管理を native に持ったら"


def test_long_condition_is_capped(harness):
    long = "x" * (MAX_CONDITION_CHARS + 50)
    (harness / "docs" / "adr" / "0047-long.md").write_text(
        f"# ADR-0047: long\n\n## Status\n\naccepted\n\n## Review-when\n\n{long}\n",
        encoding="utf-8",
    )
    adr = {c.id: c for c in load_adr_conditions(harness)}["ADR-0047"]
    assert len(adr.text) == MAX_CONDITION_CHARS + 2
    assert adr.text.endswith(" …")


def test_sha_tracks_the_wording(harness):
    before = load_rfc_conditions(harness)[0].sha
    path = harness / "rfcs" / "0001-first.md"
    path.write_text(path.read_text(encoding="utf-8").replace("変えた時", "変えたとき"), "utf-8")
    assert load_rfc_conditions(harness)[0].sha != before


def test_real_ledger_still_parses():
    """The parser's own canary: the harness this job watches still has conditions to read.

    If the RFC frontmatter or the ADR section heading is renamed, this goes red instead of
    the job going quiet.
    """
    conditions = load_conditions(REPO_ROOT)
    ids = [c.id for c in conditions]
    assert sum(i.startswith("RFC-") for i in ids) >= 10
    assert sum(i.startswith("ADR-") for i in ids) >= 30
    assert len(ids) == len(set(ids))
    assert all(c.text and c.title for c in conditions)


def test_superseded_by_in_the_status_line_retires_the_adr(harness):
    adr = harness / "docs" / "adr"
    body = "\n\n## Review-when\n\n- 何かが起きたら\n"
    (adr / "0060-retired-in-prose.md").write_text(
        "# ADR-0060: old\n\n## Status\n\naccepted — **superseded by [ADR-0062](x.md)（2026-09-05）**"
        + body,
        encoding="utf-8",
    )
    (adr / "0062-successor.md").write_text(
        "# ADR-0062: new\n\n## Status\n\naccepted — supersedes ADR-0060" + body, encoding="utf-8"
    )
    (adr / "0072-partial.md").write_text(
        "# ADR-0072: partial\n\n## Status\n\naccepted — partially-supersedes ADR-0016" + body,
        encoding="utf-8",
    )
    ids = [c.id for c in load_adr_conditions(harness)]
    assert "ADR-0060" not in ids
    assert {"ADR-0062", "ADR-0072"} <= set(ids)

"""Hermetic tests for adr_lint.py — fixture corpora built in tmp_path.

Covers the deviation patterns measured in real corpora on 2026-08-26:
case-mismatched headings (CA), missing Date (zenn-content), Status prose
suffixes (harness + CA), non-standard filenames (g-kentei-ios), References
template (CA), and the harness exemption boundaries (0009 / 0044).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.adr_lint import analyze_file, collect_evidence, gate_violations, main

HARNESS_TEMPLATE = """# Architecture Decision Records

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
{rows}

## Template

```markdown
# ADR-NNNN: [Title]

## Status
accepted | superseded | deprecated

## Date
YYYY-MM-DD

## Context
[x]

## Decision
[x]

## Review-when
[x]

## Alternatives Considered
[x]

## Consequences
[x]
```
"""

CA_TEMPLATE = """# Architecture Decision Records

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
{rows}

## Template

```markdown
# ADR-NNNN: Title

## Status
accepted / proposed / withdrawn / superseded-by ADR-NNNN

## Date
YYYY-MM-DD

## Context
x

## Decision
x

## Alternatives Considered
x

## Consequences
x

## References
- x
```
"""


def adr_body(
    *,
    status: str = "accepted",
    date: str = "2026-08-26",
    sections: list[str] | None = None,
) -> str:
    sections = sections or [
        "Context",
        "Decision",
        "Review-when",
        "Alternatives Considered",
        "Consequences",
    ]
    parts = [f"# ADR-0001: T\n\n## Status\n{status}\n\n## Date\n{date}\n"]
    parts += [f"\n## {s}\nbody\n" for s in sections]
    return "".join(parts)


def make_corpus(tmp_path: Path, readme: str, files: dict[str, str]) -> Path:
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "README.md").write_text(readme, encoding="utf-8")
    for name, content in files.items():
        (adr / name).write_text(content, encoding="utf-8")
    return tmp_path


def index_rows(*nums_titles: tuple[str, str]) -> str:
    return "\n".join(f"| [{n}]({n}-{t}.md) | {t} | accepted | 2026-08-26 |" for n, t in nums_titles)


def test_clean_harness_style_corpus(tmp_path: Path) -> None:
    root = make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0001", "a"), ("0002", "b"))),
        {"0001-a.md": adr_body(), "0002-b.md": adr_body()},
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    assert ev["template_source"] == "readme"
    assert "Review-when" in ev["expected_sections"]
    assert gate_violations(ev, None, 1) == []


def test_ca_style_template_uses_references_not_review_when(tmp_path: Path) -> None:
    body = adr_body(sections=["Context", "Decision", "Alternatives Considered", "Consequences"])
    root = make_corpus(
        tmp_path,
        CA_TEMPLATE.format(rows=index_rows(("0001", "a"))),
        {"0001-a.md": body + "\n## References\n- x\n"},
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    assert "References" in ev["expected_sections"]
    assert "Review-when" not in ev["expected_sections"]
    assert gate_violations(ev, None, None) == []


def test_missing_section_and_case_mismatch(tmp_path: Path) -> None:
    body = adr_body(sections=["Context", "Decision", "Review-when", "Consequences"])
    body += "\n## Alternatives considered\nx\n"  # lowercase c — CA 0024/0025 pattern
    no_date = adr_body(sections=["Context", "Decision", "Review-when", "Consequences"]).replace(
        "\n## Date\n2026-08-26\n", "\n"
    )
    root = make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0001", "a"), ("0002", "b"))),
        {"0001-a.md": body, "0002-b.md": no_date},
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    v = gate_violations(ev, None, None)
    assert any("case mismatch" in line and "0001-a.md" in line for line in v)
    assert any("missing section '## Date'" in line and "0002-b.md" in line for line in v)
    assert any("missing section '## Alternatives Considered'" in line for line in v)


def test_status_prefix_judgment_allows_prose_suffix(tmp_path: Path) -> None:
    ok_statuses = [
        "accepted — supersedes ADR-0021 の一部",
        "superseded-by 0070",
        "partially-superseded-by ADR-0097",
        "withdrawn (2026-04-27)",
        "accepted (note)",
        "**withdrawn (2026-04-27)** — articulated and withdrawn the same day.",
        "accepted（chain の front-load は維持）",
    ]
    files = {
        f"{i:04d}-s{i}.md": adr_body(status=s).replace("ADR-0001", f"ADR-{i:04d}")
        for i, s in enumerate(ok_statuses, start=1)
    }
    bad_num = len(ok_statuses) + 1
    files[f"{bad_num:04d}-bad.md"] = adr_body(status="TBD later")
    rows = index_rows(
        *[(f"{i:04d}", f"s{i}") for i in range(1, bad_num)], (f"{bad_num:04d}", "bad")
    )
    root = make_corpus(tmp_path, HARNESS_TEMPLATE.format(rows=rows), files)
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    v = gate_violations(ev, None, None)
    assert len([line for line in v if "Status" in line]) == 1
    assert any(f"{bad_num:04d}-bad.md" in line for line in v)


def test_date_format_violation(tmp_path: Path) -> None:
    root = make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0001", "a"))),
        {"0001-a.md": adr_body(date="先週")},
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    assert any("YYYY-MM-DD" in line for line in gate_violations(ev, None, None))


def test_sections_from_exempts_old_adrs(tmp_path: Path) -> None:
    old = adr_body(sections=["Context", "Decision"])  # 0009-style: sections missing
    new = adr_body()
    root = make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0009", "old"), ("0044", "new"))),
        {"0009-old.md": old, "0044-new.md": new},
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    assert gate_violations(ev, 44, 44) == []
    assert any("0009-old.md" in line for line in gate_violations(ev, None, None))


def test_review_when_required_from_threshold(tmp_path: Path) -> None:
    without = adr_body(sections=["Context", "Decision", "Alternatives Considered", "Consequences"])
    root = make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0043", "old"), ("0044", "new"))),
        {"0043-old.md": without, "0044-new.md": without},
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    v = gate_violations(ev, 44, 44)
    review_when = [line for line in v if "Review-when" in line]
    assert len(review_when) == 1
    assert "0044-new.md" in review_when[0]


def test_naming_duplicates_and_ja_twin(tmp_path: Path) -> None:
    root = make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0001", "a"), ("0002", "b"))),
        {
            "0001-a.md": adr_body(),
            "0001-a.ja.md": adr_body(),  # language twin — NOT a duplicate
            "0002-b.md": adr_body(),
            "0002-other.md": adr_body(),  # same number, different slug — duplicate
            "ADR-003-x.md": adr_body(),  # g-kentei-ios style — invalid name
        },
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    assert ev["naming"]["invalid"] == ["ADR-003-x.md"]
    assert ev["naming"]["duplicates"] == ["0002"]
    v = gate_violations(ev, None, None)
    assert any("NNNN-slug.md" in line for line in v)
    assert any("duplicate ADR number" in line for line in v)
    assert not any("0001" in line and "duplicate" in line for line in v)


def test_index_drift_both_directions(tmp_path: Path) -> None:
    root = make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0001", "a"), ("0003", "ghost"))),
        {"0001-a.md": adr_body(), "0002-b.md": adr_body()},
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    assert ev["index"]["in_index_not_files"] == ["0003"]
    assert ev["index"]["in_files_not_index"] == ["0002"]
    v = gate_violations(ev, None, None)
    assert any("0003" in line and "no such ADR file" in line for line in v)
    assert any("0002" in line and "missing from the README.md index" in line for line in v)


def test_no_template_falls_back_to_default(tmp_path: Path) -> None:
    root = make_corpus(tmp_path, "# ADRs\n", {"0001-a.md": adr_body()})
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    assert ev["template_source"] == "default"
    assert "Review-when" in ev["expected_sections"]


def test_headings_inside_fences_ignored(tmp_path: Path) -> None:
    body = adr_body() + "\n```markdown\n## Fake Section\n```\n"
    root = make_corpus(
        tmp_path, HARNESS_TEMPLATE.format(rows=index_rows(("0001", "a"))), {"0001-a.md": body}
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    assert gate_violations(ev, None, None) == []


def test_supersede_notation_evidence(tmp_path: Path) -> None:
    root = make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0001", "a"), ("0002", "b"))),
        {
            "0001-a.md": adr_body(status="superseded-by 0070"),
            "0002-b.md": adr_body(status="superseded by ADR-0036"),
        },
    )
    ev = collect_evidence(root, "docs/adr")
    assert ev is not None
    notations = {n for f in ev["files"] for n in f["supersede_notations"]}
    assert "hyphenated + bare NNNN" in notations
    assert "spaced + ADR-NNNN" in notations


def test_cli_evidence_mode_exit_zero_and_gate_exit_three(tmp_path: Path, capsys) -> None:
    make_corpus(
        tmp_path,
        HARNESS_TEMPLATE.format(rows=index_rows(("0001", "a"))),
        {"0001-a.md": adr_body(sections=["Context"])},
    )
    assert main(["--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert '"missing_sections"' in out
    assert main(["--root", str(tmp_path), "--gate"]) == 3


def test_cli_missing_dir_exit_two(tmp_path: Path) -> None:
    assert main(["--root", str(tmp_path)]) == 2


def test_numeric_evidence_pairs_prose_with_table_row_count(tmp_path: Path) -> None:
    path = tmp_path / "0001-table.md"
    path.write_text(
        "# ADR-0001: T\n\n対象は 2 件。\n\n| Name | State |\n|---|---|\n| a | on |\n| b | off |\n",
        encoding="utf-8",
    )

    evidence = analyze_file(path, [])

    assert evidence is not None
    assert evidence["numeric_evidence"] == {
        "paired": [
            {
                "claim": "2 件",
                "value": 2,
                "location": 3,
                "counted": 2,
                "source": "table",
            }
        ],
        "unpaired": [],
    }


def test_numeric_evidence_exposes_table_count_mismatch_without_gating(tmp_path: Path) -> None:
    path = tmp_path / "0001-table.md"
    path.write_text(
        "対象は 3 項目。\n\n| Name |\n|---|\n| a |\n| b |\n",
        encoding="utf-8",
    )

    evidence = analyze_file(path, [])

    assert evidence is not None
    assert evidence["numeric_evidence"]["paired"][0]["value"] == 3
    assert evidence["numeric_evidence"]["paired"][0]["counted"] == 2
    corpus = {
        "naming": {"invalid": [], "duplicates": []},
        "files": [evidence],
        "index": {"present": True, "in_index_not_files": [], "in_files_not_index": []},
    }
    assert gate_violations(corpus, None, None) == []


def test_numeric_evidence_pairs_point_claim_with_bullet_count(tmp_path: Path) -> None:
    path = tmp_path / "0001-list.md"
    path.write_text(
        "次の 3 点を採用する。\n\n- alpha\n  continuation 9 件\n\n- beta\n- gamma\n",
        encoding="utf-8",
    )

    evidence = analyze_file(path, [])

    assert evidence is not None
    assert evidence["numeric_evidence"]["paired"] == [
        {"claim": "3 点", "value": 3, "location": 1, "counted": 3, "source": "list"}
    ]
    assert evidence["numeric_evidence"]["unpaired"] == []


def test_numeric_evidence_does_not_pair_incidental_number_before_list(tmp_path: Path) -> None:
    path = tmp_path / "0001-list.md"
    path.write_text("観測は 28 件だった。\n\n- 別の論点\n", encoding="utf-8")

    evidence = analyze_file(path, [])

    assert evidence is not None
    assert evidence["numeric_evidence"]["paired"] == []
    assert evidence["numeric_evidence"]["unpaired"][0]["claim"] == "28 件"


@pytest.mark.parametrize("counter", ["件", "本", "個", "repo", "項目"])
def test_numeric_evidence_keeps_supported_counters_unpaired(tmp_path: Path, counter: str) -> None:
    path = tmp_path / "0001-prose.md"
    path.write_text(f"調査対象は 7 {counter}だった。\n", encoding="utf-8")

    evidence = analyze_file(path, [])

    assert evidence is not None
    assert evidence["numeric_evidence"] == {
        "paired": [],
        "unpaired": [
            {
                "claim": f"7 {counter}",
                "value": 7,
                "location": 1,
                "counted": None,
                "source": "prose",
            }
        ],
    }


def test_numeric_evidence_is_empty_when_adr_has_no_numeric_claims(tmp_path: Path) -> None:
    path = tmp_path / "0001-none.md"
    path.write_text("# ADR: 数値なし\n\n本文だけ。\n", encoding="utf-8")

    evidence = analyze_file(path, [])

    assert evidence is not None
    assert evidence["numeric_evidence"] == {"paired": [], "unpaired": []}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

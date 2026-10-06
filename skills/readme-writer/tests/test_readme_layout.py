"""Tests for the layout evidence (readme_layout via readme_evidence.collect).

Asserts what was counted per section; there is no pass/fail in the evidence layer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.readme_evidence import collect, render_text


def _layout(md: str) -> dict:
    return collect("inline.md", md, Path("/nonexistent"))["layout"]


def _forms(lay: dict, heading: str | None) -> dict:
    return next(s["forms"] for s in lay["sections"] if s["heading"] == heading)


HUB = """# Name

Lead paragraph that says what this is.
Second line of the same paragraph.

## Start here

- **From A:** [repo-a](https://x/a), one thing.
- **From B:** [repo-b](https://x/b), another.
- plain item

## At a Glance

| Line | What | Record |
|---|---|---|
| [a](https://x) | first | doi |
| [b](https://x) | a longer cell here | doi |

> [!NOTE]
> An alert.

> [!WARNING]
> Second alert.

> plain quote

```mermaid
graph TD
  A --> B
```

```bash
echo hi
```

![diagram](d.png)

<details><summary>More</summary>

hidden

</details>
"""


@pytest.mark.unit
class TestSections:
    def test_lead_section_counts_text_before_first_h2(self) -> None:
        lay = _layout(HUB)
        assert _forms(lay, "Name")["paragraphs"] == 1

    def test_list_section(self) -> None:
        forms = _forms(_layout(HUB), "Start here")
        assert forms["list_items"] == 3
        assert forms["tables"] == 0

    def test_table_alert_quote_diagram_code_image_details(self) -> None:
        forms = _forms(_layout(HUB), "At a Glance")
        assert forms["tables"] == 1
        assert forms["alerts"] == 2
        assert forms["blockquotes"] == 1
        assert forms["diagrams"] == 1
        assert forms["code_blocks"] == 1
        assert forms["images"] == 1
        assert forms["details"] == 1

    def test_empty_preamble_is_omitted(self) -> None:
        lay = _layout("## Only\n\ntext\n")
        assert [s["heading"] for s in lay["sections"]] == ["Only"]

    def test_h3_does_not_open_a_section(self) -> None:
        lay = _layout("## Top\n\n### Sub\n\n- a\n")
        assert [s["heading"] for s in lay["sections"]] == ["Top"]
        assert _forms(lay, "Top")["list_items"] == 1


@pytest.mark.unit
class TestDetails:
    def test_list_lead_types(self) -> None:
        lists = _layout(HUB)["lists"]
        assert lists[0] == {"line": 8, "items": 3, "lead_types": {"bold": 2, "text": 1}}

    def test_link_lead_type(self) -> None:
        assert _layout("- [a](x) one\n")["lists"][0]["lead_types"] == {"link": 1}

    def test_list_continuation_line_is_not_a_paragraph(self) -> None:
        lay = _layout("## S\n\n- item\n  continued\n")
        assert _forms(lay, "S")["paragraphs"] == 0

    def test_table_shape(self) -> None:
        table = _layout(HUB)["tables"][0]
        assert table == {"line": 14, "columns": 3, "rows": 2, "longest_cell": 18}

    def test_pipe_line_without_delimiter_is_not_a_table(self) -> None:
        assert _layout("## S\n\n| not a table\n")["tables"] == []

    def test_alerts(self) -> None:
        alerts = _layout(HUB)["alerts"]
        assert alerts["count"] == 2
        assert [a["type"] for a in alerts["items"]] == ["NOTE", "WARNING"]

    def test_heading_case(self) -> None:
        hc = _layout(HUB)["heading_case"]
        assert (hc["title"], hc["sentence"]) == (1, 1)
        assert {i["text"]: i["style"] for i in hc["items"]} == {
            "At a Glance": "title",
            "Start here": "sentence",
        }

    def test_generic_link_text(self) -> None:
        lay = _layout("See [here](x) and [こちら](y) and [the guide](z).\n")
        assert [g["text"] for g in lay["generic_link_text"]] == ["here", "こちら"]


@pytest.mark.unit
class TestGithubTableAndListShapes:
    def test_short_delimiter_table(self) -> None:
        assert _layout("## S\n\n| a | b |\n|-|--|\n| 1 | 2 |\n")["tables"][0]["rows"] == 1

    def test_table_without_leading_pipe(self) -> None:
        table = _layout("## S\n\na | b\n---|---\n1 | 2\n")["tables"][0]
        assert (table["columns"], table["rows"]) == (2, 1)

    def test_bare_rule_is_not_a_table(self) -> None:
        assert _layout("## S\n\ntext | more\n---\n")["tables"] == []

    def test_loose_list_is_one_list(self) -> None:
        lay = _layout("## S\n\n- a\n\n- b\n\n  more about b\n\n- c\n")
        assert [lst["items"] for lst in lay["lists"]] == [3]
        assert _forms(lay, "S")["paragraphs"] == 0

    def test_lazy_continuation_is_not_a_paragraph(self) -> None:
        lay = _layout("## S\n\n- item that wraps\nonto an unindented line\n")
        assert _forms(lay, "S")["paragraphs"] == 0

    def test_paragraph_after_loose_list_counts(self) -> None:
        lay = _layout("## S\n\n- a\n\nAfter the list.\n")
        assert _forms(lay, "S")["paragraphs"] == 1

    def test_marker_with_text_on_its_line_is_a_plain_quote(self) -> None:
        forms = _forms(_layout("## S\n\n> [!TIP] same line\n"), "S")
        assert (forms["alerts"], forms["blockquotes"]) == (0, 1)

    def test_marker_inside_a_running_quote_is_not_an_alert(self) -> None:
        forms = _forms(_layout("## S\n\n> plain\n> [!NOTE]\n> more\n"), "S")
        assert (forms["alerts"], forms["blockquotes"]) == (0, 1)

    def test_heading_case_ignores_code_and_link_urls(self) -> None:
        hc = _layout("## Using `npm install`\n\n## See [The Guide](https://x/y-z)\n")[
            "heading_case"
        ]
        assert [i["style"] for i in hc["items"]] == ["title"]


@pytest.mark.unit
def test_fence_inside_front_matter_is_not_counted() -> None:
    lay = _layout("---\nnote: |\n  ```\n---\n\n## S\n\n```bash\nx\n```\n")
    assert _forms(lay, "S")["code_blocks"] == 1
    assert sum(s["forms"]["code_blocks"] for s in lay["sections"]) == 1


@pytest.mark.unit
def test_render_text_has_layout_line() -> None:
    ev = collect("inline.md", HUB, Path("/nonexistent"))
    text = render_text(ev)
    assert "Start here: list_items 3" in text
    assert "alerts 2" in text

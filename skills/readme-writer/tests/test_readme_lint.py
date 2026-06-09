"""Tests for readme_lint — structural-only README linter.

These checks cover *structural* properties (heading shape, image alt text,
local-link resolution) where code gives 100% accuracy. Semantic quality
(does the lead hook a human? is the value proposition clear?) is deliberately
NOT tested here — that is a holistic LLM judgment per AKC ADR-0008
(Code-LLM Layering), never scored.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.readme_lint import (
    Heading,
    Image,
    Issue,
    Link,
    LintReport,
    check_alt_text,
    check_heading_levels,
    check_local_links,
    check_single_h1,
    lint_file,
    main,
    parse_headings,
    parse_images,
    parse_links,
    render_json,
    render_report,
    run_lint,
)


@pytest.mark.unit
class TestParseHeadings:
    def test_parses_levels_and_text(self) -> None:
        md = "# Title\n\n## Section\n\n### Sub\n"
        headings = parse_headings(md)
        assert [(h.level, h.text) for h in headings] == [
            (1, "Title"),
            (2, "Section"),
            (3, "Sub"),
        ]

    def test_records_line_numbers(self) -> None:
        md = "# Title\n\ntext\n\n## Section\n"
        headings = parse_headings(md)
        assert headings[0].line == 1
        assert headings[1].line == 5

    def test_ignores_headings_inside_code_fence(self) -> None:
        md = "# Real\n\n```\n# fake heading in code\n```\n\n## Also Real\n"
        headings = parse_headings(md)
        texts = [h.text for h in headings]
        assert "Real" in texts
        assert "Also Real" in texts
        assert "fake heading in code" not in texts

    def test_ignores_tilde_fence(self) -> None:
        md = "# Real\n\n~~~\n## fake\n~~~\n"
        headings = parse_headings(md)
        assert [h.text for h in headings] == ["Real"]

    def test_strips_trailing_hashes(self) -> None:
        md = "## Section ##\n"
        headings = parse_headings(md)
        assert headings[0].text == "Section"

    def test_hash_without_space_is_not_heading(self) -> None:
        md = "#nospace\n\n# Real Title\n"
        headings = parse_headings(md)
        assert [h.text for h in headings] == ["Real Title"]

    def test_leading_spaces_atx_detected(self) -> None:
        md = "# Title\n\n   ## Indented Section\n"
        headings = parse_headings(md)
        assert (2, "Indented Section") in [(h.level, h.text) for h in headings]

    def test_setext_h1_detected(self) -> None:
        md = "My Project\n==========\n\nbody\n"
        headings = parse_headings(md)
        assert headings[0].level == 1
        assert headings[0].text == "My Project"
        assert headings[0].line == 1

    def test_setext_h2_detected(self) -> None:
        md = "# Title\n\nSection\n-------\n"
        headings = parse_headings(md)
        assert (2, "Section") in [(h.level, h.text) for h in headings]

    def test_thematic_break_after_blank_is_not_setext(self) -> None:
        md = "# Title\n\nsome text\n\n---\n"
        headings = parse_headings(md)
        # the `---` is preceded by a blank line → thematic break, not a heading
        assert [(h.level, h.text) for h in headings] == [(1, "Title")]

    def test_underline_after_list_item_is_not_setext(self) -> None:
        md = "# Title\n\n- item\n---\n"
        headings = parse_headings(md)
        assert [(h.level, h.text) for h in headings] == [(1, "Title")]

    def test_closing_fence_with_trailing_text_stays_in_fence(self) -> None:
        md = "```\n# fake1\n``` notaclose\n# fake2\n```\n\n# Real\n"
        texts = [h.text for h in parse_headings(md)]
        assert texts == ["Real"]


@pytest.mark.unit
class TestParseImages:
    def test_parses_markdown_image(self) -> None:
        md = "![a diagram](img/arch.png)\n"
        images = parse_images(md)
        assert images[0].alt == "a diagram"
        assert images[0].src == "img/arch.png"

    def test_empty_alt_is_captured(self) -> None:
        md = "![](img/x.png)\n"
        images = parse_images(md)
        assert images[0].alt == ""
        assert images[0].src == "img/x.png"

    def test_parses_html_img_with_alt(self) -> None:
        md = '<img src="logo.png" alt="the logo">\n'
        images = parse_images(md)
        assert images[0].src == "logo.png"
        assert images[0].alt == "the logo"

    def test_html_img_without_alt_has_empty_alt(self) -> None:
        md = '<img src="logo.png" width="100">\n'
        images = parse_images(md)
        assert images[0].alt == ""

    def test_ignores_images_in_code_fence(self) -> None:
        md = "```\n![x](in-code.png)\n```\n"
        images = parse_images(md)
        assert images == []

    def test_image_with_title_attribute(self) -> None:
        md = '![alt text](img/x.png "a title")\n'
        images = parse_images(md)
        assert images[0].src == "img/x.png"
        assert images[0].alt == "alt text"

    def test_badge_image_inside_link_is_still_an_image(self) -> None:
        md = "[![build badge](img/badge.png)](https://ci.example.com)\n"
        images = parse_images(md)
        assert images[0].alt == "build badge"
        assert images[0].src == "img/badge.png"


@pytest.mark.unit
class TestParseLinks:
    def test_parses_link(self) -> None:
        md = "see [the docs](docs/guide.md) here\n"
        links = parse_links(md)
        assert links[0].text == "the docs"
        assert links[0].href == "docs/guide.md"

    def test_image_is_not_a_link(self) -> None:
        md = "![alt](img.png)\n"
        links = parse_links(md)
        assert links == []

    def test_ignores_links_in_code_fence(self) -> None:
        md = "```\n[x](y.md)\n```\n"
        links = parse_links(md)
        assert links == []

    def test_badge_image_in_link_does_not_produce_phantom_link(self) -> None:
        # `[![badge](img)](url)` must not be parsed as a plain link to img.
        md = "[![build badge](img/badge.png)](https://ci.example.com)\n"
        links = parse_links(md)
        assert all(link.href != "img/badge.png" for link in links)


@pytest.mark.unit
class TestCheckSingleH1:
    def test_exactly_one_h1_no_issue(self) -> None:
        headings = [Heading(1, "Title", 1), Heading(2, "S", 3)]
        assert check_single_h1(headings) == []

    def test_no_h1_returns_issue(self) -> None:
        headings = [Heading(2, "S", 1)]
        issues = check_single_h1(headings)
        assert len(issues) == 1
        assert issues[0].check == "single_h1"

    def test_multiple_h1_returns_issue(self) -> None:
        headings = [Heading(1, "A", 1), Heading(1, "B", 5)]
        issues = check_single_h1(headings)
        assert len(issues) >= 1
        assert any(i.line == 5 for i in issues)


@pytest.mark.unit
class TestCheckHeadingLevels:
    def test_no_skip_is_clean(self) -> None:
        headings = [Heading(1, "A", 1), Heading(2, "B", 2), Heading(3, "C", 3)]
        assert check_heading_levels(headings) == []

    def test_decrease_is_allowed(self) -> None:
        headings = [Heading(1, "A", 1), Heading(2, "B", 2), Heading(3, "C", 3), Heading(2, "D", 4)]
        assert check_heading_levels(headings) == []

    def test_skip_from_h1_to_h3_flagged(self) -> None:
        headings = [Heading(1, "A", 1), Heading(3, "C", 4)]
        issues = check_heading_levels(headings)
        assert len(issues) == 1
        assert issues[0].check == "heading_levels"
        assert issues[0].line == 4

    def test_empty_headings_no_issue(self) -> None:
        assert check_heading_levels([]) == []


@pytest.mark.unit
class TestCheckAltText:
    def test_all_images_have_alt(self) -> None:
        images = [Image("a diagram", "x.png", 1)]
        assert check_alt_text(images) == []

    def test_missing_alt_flagged(self) -> None:
        images = [Image("", "x.png", 7)]
        issues = check_alt_text(images)
        assert len(issues) == 1
        assert issues[0].check == "alt_text"
        assert issues[0].line == 7
        assert "x.png" in issues[0].message

    def test_whitespace_only_alt_flagged(self) -> None:
        images = [Image("   ", "x.png", 2)]
        assert len(check_alt_text(images)) == 1

    def test_no_images_no_issue(self) -> None:
        assert check_alt_text([]) == []


@pytest.mark.unit
class TestCheckLocalLinks:
    def test_existing_relative_target_is_clean(self, tmp_path: Path) -> None:
        (tmp_path / "guide.md").write_text("x", encoding="utf-8")
        links = [Link("docs", "guide.md", 3)]
        assert check_local_links(links, [], tmp_path) == []

    def test_broken_relative_target_flagged(self, tmp_path: Path) -> None:
        links = [Link("docs", "missing.md", 3)]
        issues = check_local_links(links, [], tmp_path)
        assert len(issues) == 1
        assert issues[0].check == "local_link"
        assert "missing.md" in issues[0].message

    def test_external_url_is_skipped(self, tmp_path: Path) -> None:
        links = [Link("site", "https://example.com/x", 1)]
        assert check_local_links(links, [], tmp_path) == []

    def test_mailto_is_skipped(self, tmp_path: Path) -> None:
        links = [Link("mail", "mailto:a@b.com", 1)]
        assert check_local_links(links, [], tmp_path) == []

    def test_pure_anchor_is_skipped(self, tmp_path: Path) -> None:
        links = [Link("top", "#section", 1)]
        assert check_local_links(links, [], tmp_path) == []

    def test_fragment_is_stripped_before_resolving(self, tmp_path: Path) -> None:
        (tmp_path / "guide.md").write_text("x", encoding="utf-8")
        links = [Link("docs", "guide.md#install", 3)]
        assert check_local_links(links, [], tmp_path) == []

    def test_query_string_is_stripped_before_resolving(self, tmp_path: Path) -> None:
        (tmp_path / "chart.svg").write_text("x", encoding="utf-8")
        links = [Link("chart", "chart.svg?sanitize=true", 3)]
        assert check_local_links(links, [], tmp_path) == []

    def test_absolute_filesystem_path_is_not_probed(self, tmp_path: Path) -> None:
        links = [Link("passwd", "/etc/passwd", 1)]
        assert check_local_links(links, [], tmp_path) == []

    def test_site_absolute_path_is_skipped(self, tmp_path: Path) -> None:
        links = [Link("docs", "/docs/x.md", 1)]
        assert check_local_links(links, [], tmp_path) == []

    def test_broken_image_src_flagged(self, tmp_path: Path) -> None:
        images = [Image("alt", "img/missing.png", 4)]
        issues = check_local_links([], images, tmp_path)
        assert len(issues) == 1
        assert "missing.png" in issues[0].message

    def test_protocol_relative_url_skipped(self, tmp_path: Path) -> None:
        links = [Link("x", "//cdn.example.com/a.js", 1)]
        assert check_local_links(links, [], tmp_path) == []

    def test_percent_encoded_target_is_decoded_before_resolving(
        self, tmp_path: Path
    ) -> None:
        # Regression: Markdown encodes non-ASCII link targets (e.g. Japanese
        # filenames) as percent-escapes. The linter must decode before resolving
        # on disk — otherwise it probes the literal "%E5..." name, which never
        # matches the real file (and, for a long enough name, raised ENAMETOOLONG
        # from os.stat on APFS). Unpatched code flags this as broken; the decode
        # makes it resolve to the real file and stay clean.
        (tmp_path / "念の衝突.md").write_text("x", encoding="utf-8")
        links = [Link("doc", "%E5%BF%B5%E3%81%AE%E8%A1%9D%E7%AA%81.md", 3)]
        assert check_local_links(links, [], tmp_path) == []


@pytest.mark.unit
class TestRunLint:
    def test_clean_document_has_no_issues(self, tmp_path: Path) -> None:
        md = "# Title\n\nlead paragraph.\n\n## Section\n\nbody\n"
        report = run_lint(str(tmp_path / "README.md"), md, tmp_path)
        assert report.issues == ()

    def test_collects_issues_across_checks(self, tmp_path: Path) -> None:
        md = "## No H1 Here\n\n![](x.png)\n"
        report = run_lint(str(tmp_path / "README.md"), md, tmp_path)
        checks = {i.check for i in report.issues}
        assert "single_h1" in checks
        assert "alt_text" in checks

    def test_badge_in_link_not_double_reported(self, tmp_path: Path) -> None:
        # missing badge image must be reported once (as an image), not twice.
        md = "# T\n\n[![badge](img/badge.png)](https://ci.example.com)\n"
        report = run_lint(str(tmp_path / "README.md"), md, tmp_path)
        broken = [i for i in report.issues if i.check == "local_link"]
        assert len(broken) == 1


@pytest.mark.unit
class TestRender:
    def test_report_lists_issues(self) -> None:
        report = LintReport(
            path="/tmp/README.md",
            issues=(Issue("alt_text", "image 'x.png' missing alt text", 7),),
        )
        text = render_report(report)
        assert "alt_text" in text
        assert "x.png" in text

    def test_clean_report_says_so(self) -> None:
        text = render_report(LintReport(path="/tmp/README.md", issues=()))
        assert "no structural issues" in text.lower()

    def test_json_is_valid_and_has_counts(self) -> None:
        report = LintReport(
            path="/tmp/README.md",
            issues=(Issue("single_h1", "no H1 found", None),),
        )
        data = json.loads(render_json(report))
        assert data["path"] == "/tmp/README.md"
        assert data["issue_count"] == 1
        assert data["issues"][0]["check"] == "single_h1"

    def test_report_has_no_quality_score(self) -> None:
        """Structural lint must never emit a quality score (AKC ADR-0008)."""
        text = render_report(LintReport(path="/tmp/README.md", issues=())).lower()
        for forbidden in ("score", "/10", "/100", "rating", "grade"):
            assert forbidden not in text


@pytest.mark.integration
class TestCli:
    def test_missing_file_returns_exit_2(self, tmp_path: Path) -> None:
        assert main([str(tmp_path / "nope.md")]) == 2

    def test_clean_file_returns_zero(self, tmp_path: Path) -> None:
        md = tmp_path / "README.md"
        md.write_text("# Title\n\nlead.\n\n## Section\n\nbody\n", encoding="utf-8")
        assert main([str(md)]) == 0

    def test_file_with_issues_returns_one(self, tmp_path: Path) -> None:
        md = tmp_path / "README.md"
        md.write_text("## No H1\n\n![](x.png)\n", encoding="utf-8")
        assert main([str(md)]) == 1

    def test_json_flag_emits_json(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        md = tmp_path / "README.md"
        md.write_text("## No H1\n", encoding="utf-8")
        main([str(md), "--json"])
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "issues" in parsed

    def test_oversized_file_returns_exit_2(self, tmp_path: Path) -> None:
        from scripts import readme_lint

        md = tmp_path / "README.md"
        md.write_text("# T\n", encoding="utf-8")
        original = readme_lint._MAX_BYTES
        try:
            readme_lint._MAX_BYTES = 1  # force the size guard to trip
            assert main([str(md)]) == 2
        finally:
            readme_lint._MAX_BYTES = original

    def test_lint_file_resolves_local_links_relative_to_readme(self, tmp_path: Path) -> None:
        (tmp_path / "guide.md").write_text("x", encoding="utf-8")
        md = tmp_path / "README.md"
        md.write_text("# T\n\n[g](guide.md)\n\n[bad](missing.md)\n", encoding="utf-8")
        report = lint_file(md)
        broken = [i for i in report.issues if i.check == "local_link"]
        assert len(broken) == 1
        assert "missing.md" in broken[0].message

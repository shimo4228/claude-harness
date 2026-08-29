"""Tests for readme_evidence — deterministic evidence for the README judge.

The script emits counts and listings, never a verdict. Tests therefore assert
*what was counted*, not *whether the README passed*: there is no pass/fail to
test. Exit code is 0 whenever evidence was produced, 2 when the file is missing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.readme_evidence import (
    collect,
    collect_file,
    details_blocks,
    main,
    parse_headings,
    parse_images,
    parse_links,
    render_text,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _ev(md: str, base: Path | None = None) -> dict:
    return collect("inline.md", md, base or Path("/nonexistent"))


@pytest.mark.unit
class TestParsers:
    def test_headings_levels_lines_and_setext(self) -> None:
        md = "# Title\n\ntext\n\n## Section\n\nSub\n---\n"
        hs = parse_headings(md)
        assert [(h.level, h.text, h.line) for h in hs] == [
            (1, "Title", 1),
            (2, "Section", 5),
            (2, "Sub", 7),
        ]

    def test_headings_inside_fence_ignored(self) -> None:
        md = "# Title\n\n```md\n# not a heading\n```\n"
        assert len(parse_headings(md)) == 1

    def test_images_markdown_and_html(self) -> None:
        md = '![alt](a.png)\n<img src="b.png" alt="B">\n<img src=\'c.png\'>\n'
        imgs = parse_images(md)
        assert [(i.alt, i.src) for i in imgs] == [("alt", "a.png"), ("B", "b.png"), ("", "c.png")]

    def test_links_exclude_images(self) -> None:
        md = "[t](x.md) ![i](y.png) [![b](s.svg)](u)\n"
        assert [(ln.text, ln.href) for ln in parse_links(md)] == [("t", "x.md")]


@pytest.mark.unit
class TestStructureEvidence:
    def test_counts_h1_level_jumps_missing_alt_and_broken_refs(self, tmp_path: Path) -> None:
        (tmp_path / "ok.md").write_text("x")
        md = "# A\n\nlead.\n\n#### deep\n\n![](no-alt.png)\n\n[ok](ok.md) [gone](missing.md)\n\n# B\n"
        st = _ev(md, tmp_path)["structure"]
        assert st["h1_count"] == 2
        assert st["heading_level_jumps"] == [{"line": 5, "from": 1, "to": 4, "text": "deep"}]
        assert [i["src"] for i in st["images_without_alt"]] == ["no-alt.png"]
        assert [b["href"] for b in st["broken_local_refs"]] == ["missing.md", "no-alt.png"]

    def test_absolute_and_external_refs_are_not_probed(self) -> None:
        md = "# A\n\n[x](/etc/passwd) [y](https://e.com/z) [z](%2Fetc%2Fpasswd)\n"
        assert _ev(md)["structure"]["broken_local_refs"] == []


@pytest.mark.unit
class TestFirstScreenAndLead:
    def test_identity_lead_present_and_first_screen_counts(self) -> None:
        md = (
            "# Proj\n\n[![b](https://img.shields.io/x.svg)](u)\n\n"
            "Proj is a **thing** for people, see `some-tool` and ADR-0012 "
            "(https://github.com/o/r).\n\nMore prose.\n\n## Start\n\nbody\n"
        )
        ev = _ev(md)
        assert ev["identity_lead"] == {"present": True, "line": 5}
        fs = ev["first_screen"]
        assert fs["end_line"] == 9
        assert fs["prose_lines"] == 2
        assert [t["term"] for t in fs["new_terms"]] == ["some-tool", "thing"]
        assert fs["adr_refs"] == 1
        assert fs["github_repos"] == ["o/r"]

    def test_lead_inside_details_does_not_count(self) -> None:
        md = "# P\n\n<details><summary>s</summary>\n\nhidden lead.\n\n</details>\n\n## S\n"
        assert _ev(md)["identity_lead"]["present"] is False

    def test_no_h2_means_whole_file_is_first_screen(self) -> None:
        ev = _ev("# P\n\nonly lead.\n")
        assert ev["first_screen"]["end_line"] is None
        assert ev["first_screen"]["lines"] == 3


@pytest.mark.unit
class TestInsiderRefsAndTerms:
    def test_adr_repo_docpath_doi_counts(self) -> None:
        md = (
            "# P\n\nSee ADR-0012 and ADR-0012 and ADR-0050 ([a](docs/adr/0012.md), "
            "[e](docs/evidence/x.md)). Repos https://github.com/a/b https://github.com/a/b "
            "https://github.com/c/d. DOI 10.5281/zenodo.1234.\n"
        )
        ir = _ev(md)["insider_refs"]
        assert ir["adr_total"] == 3 and ir["adr_unique"] == 2
        assert ir["adr_ids"]["ADR-0012"] == [3, 3]
        assert ir["github_repo_count"] == 2
        assert ir["doc_paths"] == {"docs/adr": 1, "docs/evidence": 1}
        assert list(ir["dois"]) == ["10.5281/zenodo.1234."] or "10.5281/zenodo.1234" in "".join(
            ir["dois"]
        )

    def test_term_candidates_skip_paths_links_labels_and_flags(self) -> None:
        md = (
            "# P\n\n`value layer` and **value layer** and `scripts/x.py` and `--flag` and "
            "**Prerequisites:** and **[Guide](docs/g.md)** and `CamelCase` and `rules-distill`.\n"
        )
        terms = {t["term"]: t for t in _ev(md)["term_candidates"]}
        assert terms["value layer"]["count"] == 2
        assert "CamelCase" in terms and "rules-distill" in terms
        for junk in ("scripts/x.py", "--flag", "Prerequisites:", "[Guide](docs/g.md)"):
            assert junk not in terms


@pytest.mark.unit
class TestDetailsFiguresBadges:
    def test_details_blocks_summary_and_contents_including_fenced_bibtex(self) -> None:
        md = (
            "# P\n\n<details>\n<summary><b>BibTeX</b></summary>\n\n```bibtex\n@software{x,}\n```\n\n"
            "</details>\n\n<details><summary>Notes</summary>\nplain 10.5281/zenodo.1 ![i](a.png)\n</details>\n"
        )
        blocks = details_blocks(md)
        assert [b["summary"] for b in blocks] == ["BibTeX", "Notes"]
        assert (
            blocks[0]["contains"]["bibtex"] is True and blocks[0]["contains"]["code_fence"] is True
        )
        assert blocks[1]["contains"]["doi"] is True and blocks[1]["contains"]["image"] is True

    def test_figures_mermaid_prose_after_and_badges_separated(self) -> None:
        md = (
            "# P\n\n[![b](https://img.shields.io/x.svg)](u)\n\nlead.\n\n```mermaid\ngraph TD\nA-->B\n```\n\n"
            "In short: A feeds B.\n\n![arch](docs/arch.png)\n\n## S\n"
        )
        ev = _ev(md)
        kinds = [(f["kind"], f["prose_after"]) for f in ev["figures"]]
        assert ("mermaid", True) in kinds
        assert ("image", False) in kinds
        assert ev["badges"]["count"] == 1
        assert all(f.get("src") != "https://img.shields.io/x.svg" for f in ev["figures"])


@pytest.mark.unit
class TestProseHistoryNumericSignals:
    def test_slop_emdash_triad_stadium_and_ja_degree(self) -> None:
        md = "# P\n\nA powerful tool — seamless — for みなさん。とても three things.\n"
        ps = _ev(md)["prose_signals"]
        assert {s["term"].lower() for s in ps["slop_words"]} == {"powerful tool", "seamless"}
        assert ps["em_dash"] == {"count": 2, "lines": [3]}
        assert ps["triad_preannounce_lines"] == [3]
        assert ps["stadium_lines"] == [3]
        assert [d["term"] for d in ps["degree_adverbs_ja"]] == ["とても"]

    def test_history_and_numeric_claims_ignore_urls(self) -> None:
        md = (
            "# P\n\n[![py](https://img.shields.io/badge/python-3.10%2B-blue)](u)\n\n"
            "v2.8 switched from X. The floor is |Δeffect| < 0.13 and 97% of raw.\n"
        )
        ev = _ev(md)
        assert ev["history_signals"] == [{"line": 5, "matches": ["v2.8", "switched from"]}]
        assert ev["numeric_claims"] == [{"line": 5, "matches": ["|Δ", "< 0", "97%"]}]

    def test_doi_citation_pairing_and_lang_guess(self) -> None:
        en = _ev("# P\n\nDOI 10.5281/zenodo.1 here.\n\n## Citation\n\ncite me\n")
        assert en["doi_citation"] == {
            "doi_present": True,
            "doi_first_line": 3,
            "how_to_cite_present": True,
        }
        ja = _ev("# P\n\nこれは日本語です。二文目です。三文目です。\n")
        assert ja["lang_guess"] == "ja"
        assert ja["doi_citation"]["doi_present"] is False


@pytest.mark.integration
class TestCliAndFixtures:
    def test_sample_issues_fixture_counts(self) -> None:
        ev = collect_file(FIXTURES / "sample_issues.md")
        assert ev["structure"]["h1_count"] == 2
        assert len(ev["structure"]["heading_level_jumps"]) == 1
        assert ev["badges"]["count"] == 7
        assert ev["identity_lead"]["present"] is False
        assert ev["details_blocks"][0]["contains"]["doi"] is True
        assert ev["doi_citation"]["how_to_cite_present"] is False
        assert [b["href"] for b in ev["structure"]["broken_local_refs"]]

    def test_sample_clean_fixture_is_quiet(self) -> None:
        ev = collect_file(FIXTURES / "sample_clean.md")
        assert ev["structure"]["h1_count"] == 1
        assert ev["structure"]["heading_level_jumps"] == []
        assert ev["structure"]["images_without_alt"] == []
        assert ev["identity_lead"]["present"] is True

    def test_cli_exit_zero_even_with_issues_and_json_shape(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main([str(FIXTURES / "sample_issues.md")]) == 0
        data = json.loads(capsys.readouterr().out)
        for key in (
            "structure",
            "first_screen",
            "insider_refs",
            "term_candidates",
            "details_blocks",
            "figures",
        ):
            assert key in data
        assert "verdict" not in data

    def test_cli_text_mode_and_missing_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main([str(FIXTURES / "sample_clean.md"), "--text"]) == 0
        assert capsys.readouterr().out.startswith("readme-evidence:")
        assert main(["/nonexistent/README.md"]) == 2

    def test_render_text_mentions_no_verdict(self) -> None:
        assert "no verdict" in render_text(collect_file(FIXTURES / "sample_clean.md"))


@pytest.mark.unit
class TestReviewRegressions:
    """Regressions from the 2026-08-19 code review of the evidence extractor."""

    def test_multiline_html_comment_keeps_line_numbers(self) -> None:
        md = "<!--\nlicense\nline3\n-->\n# Title\n\nlead.\n"
        ev = _ev(md)
        assert ev["structure"]["headings"][0]["line"] == 5
        assert ev["identity_lead"]["line"] == 7

    def test_front_matter_is_not_a_setext_heading(self) -> None:
        md = "---\ntitle: Foo\n---\n\n# Foo\n\nlead.\n\n## Usage\n"
        ev = _ev(md)
        assert [h["text"] for h in ev["structure"]["headings"]] == ["Foo", "Usage"]
        assert ev["first_screen"]["end_line"] == 9

    def test_first_screen_lines_count_raw_lines_including_fences(self) -> None:
        md = "# P\n\nlead.\n\n```bash\na\nb\nc\n```\n\n## S\n"
        ev = _ev(md)
        assert ev["first_screen"]["lines"] == 10
        assert ev["first_screen"]["prose_lines"] == 1

    def test_first_screen_new_terms_use_the_same_filter(self) -> None:
        md = "# P\n\nrun `uv pip install -e .` with `--flag` and `scripts/x.py`, see **value layer**.\n\n## S\n"
        assert [t["term"] for t in _ev(md)["first_screen"]["new_terms"]] == ["value layer"]

    def test_unclosed_details_is_reported_not_guessed(self) -> None:
        md = "# P\n\nlead.\n\n<details><summary>s</summary>\nbody\n"
        blocks = details_blocks(md)
        assert blocks == [
            {"open_line": 5, "close_line": None, "lines": None, "summary": "", "unclosed": True}
        ]

    def test_cjk_and_citing_headings_count_as_how_to_cite(self) -> None:
        assert _ev("# P\n\nDOI 10.5281/zenodo.1\n\n## 引用方法\n")["doi_citation"][
            "how_to_cite_present"
        ]
        assert _ev("# P\n\nDOI 10.5281/zenodo.1\n\n## Citing this work\n")["doi_citation"][
            "how_to_cite_present"
        ]

    def test_html_paragraph_lead_counts_as_prose(self) -> None:
        md = '# P\n\n<p align="center"><b>P</b> is a CLI for people.</p>\n\n## S\n'
        assert _ev(md)["identity_lead"] == {"present": True, "line": 3}

    def test_badge_row_is_reported_separately_from_prose_after(self) -> None:
        md = "# P\n\n[![CI](https://img.shields.io/b.svg)](u) ![fig](docs/a.png)\n\n## S\n"
        fig = next(f for f in _ev(md)["figures"] if f["kind"] == "image")
        assert fig["badge_row"] is True and fig["prose_after"] is False

    def test_history_signal_ignores_used_to_and_bare_kyu(self) -> None:
        assert _ev("# P\n\ncan be used to parse; 復旧手順.\n")["history_signals"] == []

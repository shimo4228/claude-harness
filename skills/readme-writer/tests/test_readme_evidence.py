"""Tests for readme_evidence — deterministic evidence for the README judge.

The script emits counts and listings, never a verdict. Tests therefore assert
*what was counted*, not *whether the README passed*: there is no pass/fail to
test. Exit code is 0 whenever evidence was produced, 2 when the file is missing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts import readme_evidence
from scripts.readme_evidence import (
    collect,
    collect_file,
    details_blocks,
    detect_own_repo,
    formatted_term_spans,
    github_slug,
    main,
    parse_github_repo,
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

    def test_figures_mermaid_prose_adjacent_and_badges_separated(self) -> None:
        md = (
            "# P\n\n[![b](https://img.shields.io/x.svg)](u)\n\nlead.\n\n```mermaid\ngraph TD\nA-->B\n```\n\n"
            "In short: A feeds B.\n\n## Arch\n\n![arch](docs/arch.png)\n\n## S\n\nbody.\n"
        )
        ev = _ev(md)
        kinds = [(f["kind"], f["prose_adjacent"]) for f in ev["figures"]]
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

    def test_badge_row_is_reported_separately_from_prose_adjacent(self) -> None:
        md = "# P\n\n[![CI](https://img.shields.io/b.svg)](u) ![fig](docs/a.png)\n\n## S\n"
        fig = next(f for f in _ev(md)["figures"] if f["kind"] == "image")
        assert fig["badge_row"] is True and fig["prose_adjacent"] is False

    def test_history_signal_ignores_used_to_and_bare_kyu(self) -> None:
        assert _ev("# P\n\ncan be used to parse; 復旧手順.\n")["history_signals"] == []


@pytest.mark.unit
class TestNotesAndFormattedTermSpans:
    """Term candidates come from formatted spans only; `notes` states each counter's blind spot."""

    def test_formatted_term_spans_yields_backtick_and_bold_only(self) -> None:
        spans = list(
            formatted_term_spans("a `value layer` and **Grounded distill** and plain Coined Term")
        )
        assert spans == [("code", "value layer"), ("bold", "Grounded distill")]

    def test_notes_lead_with_the_term_candidate_blind_spot(self) -> None:
        notes = _ev("# P\n\nlead.\n")["notes"]
        assert isinstance(notes, list) and notes and all(isinstance(n, str) and n for n in notes)
        first = notes[0].lower()
        assert "backtick" in first and "bold" in first and "plain prose" in first
        assert "judge" in first

    def test_notes_cover_every_new_counter(self) -> None:
        joined = "\n".join(_ev("# P\n\nlead.\n")["notes"])
        for key in (
            "broken_local_refs",
            "broken_anchors",
            "prose_adjacent",
            "own_repo",
            "register_ja",
        ):
            assert key in joined


@pytest.mark.unit
class TestFigureProseAdjacent:
    """`prose_adjacent`: a prose line within 2 lines before/after the figure (headings,
    blanks, badges and other figures never qualify). `prose_after` is gone."""

    def _fig(self, md: str, kind: str = "image") -> dict:
        return next(f for f in _ev(md)["figures"] if f["kind"] == kind)

    def test_next_section_body_does_not_count(self) -> None:
        md = "# P\n\n![arch](docs/a.png)\n\n## Next\n\nbody prose here.\n"
        fig = self._fig(md)
        assert fig["prose_adjacent"] is False
        assert "prose_after" not in fig

    def test_prose_two_lines_before_counts(self) -> None:
        md = "# P\n\nThe pipeline, from log line to event:\n\n![arch](docs/a.png)\n\n## Next\n"
        assert self._fig(md)["prose_adjacent"] is True

    def test_prose_after_mermaid_closing_fence_counts_within_two_lines(self) -> None:
        near = "# P\n\n## S\n\n```mermaid\ngraph TD\nA-->B\n```\n\nA feeds B.\n"
        far = "# P\n\n## S\n\n```mermaid\ngraph TD\nA-->B\n```\n\n\nA feeds B.\n"
        assert self._fig(near, "mermaid")["prose_adjacent"] is True
        assert self._fig(far, "mermaid")["prose_adjacent"] is False

    def test_badges_other_figures_and_setext_headings_do_not_qualify(self) -> None:
        md = (
            "# P\n\nArchitecture\n------------\n![a](docs/a.png)\n![b](docs/b.png)\n"
            "[![CI](https://img.shields.io/b.svg)](u)\n\n## S\n"
        )
        figs = [f for f in _ev(md)["figures"] if f["kind"] == "image"]
        assert [f["prose_adjacent"] for f in figs] == [False, False]

    def test_html_wrapper_lines_belong_to_the_figure(self) -> None:
        md = (
            '# P\n\n## S\n\n<p align="center">\n  <img src="docs/a.svg" alt="arch">\n</p>\n\n'
            "Each box is one stage.\n"
        )
        assert self._fig(md)["prose_adjacent"] is True


@pytest.mark.unit
class TestOwnRepo:
    """The README's own repository is not a sibling repo."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://github.com/shimo4228/claude-config.git", "shimo4228/claude-config"),
            ("https://github.com/o/r", "o/r"),
            ("https://github.com/o/r/", "o/r"),
            ("https://user@github.com/o/r.git", "o/r"),
            ("git@github.com:o/my.repo.git", "o/my.repo"),
            ("ssh://git@github.com/o/r.git", "o/r"),
            ("ssh://git@ssh.github.com:443/o/r.git", "o/r"),
            ("https://gitlab.com/o/r.git", None),
            ("not a url", None),
            ("", None),
        ],
    )
    def test_parse_github_repo_forms(self, url: str, expected: str | None) -> None:
        assert parse_github_repo(url) == expected

    def test_collect_excludes_own_repo_case_insensitively(self) -> None:
        md = (
            "# P\n\n[![CI](https://github.com/Me/Proj/actions/workflows/ci.yml/badge.svg)]"
            "(https://github.com/Me/Proj/actions) see https://github.com/me/proj.git and "
            "https://github.com/other/sib today.\n\n## S\n\nhttps://github.com/Me/Proj/blob/main/x.md\n"
        )
        ev = collect("inline.md", md, Path("/nonexistent"), own_repo="me/proj")
        assert ev["own_repo"] == "me/proj"
        assert ev["first_screen"]["github_repos"] == ["other/sib"]
        assert list(ev["insider_refs"]["github_repos"]) == ["other/sib"]
        assert ev["insider_refs"]["github_repo_count"] == 1

    def test_no_own_repo_means_no_exclusion(self) -> None:
        ev = _ev("# P\n\nhttps://github.com/me/proj\n")
        assert ev["own_repo"] is None
        assert ev["insider_refs"]["github_repo_count"] == 1

    def test_detect_own_repo_reads_git_origin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[list[str]] = []

        class Done:
            returncode = 0
            stdout = "git@github.com:me/proj.git\n"

        def fake_run(cmd: list[str], **kw: object) -> Done:
            calls.append(cmd)
            assert kw.get("timeout")
            return Done()

        monkeypatch.setattr(readme_evidence.subprocess, "run", fake_run)
        assert detect_own_repo(Path("/some/dir")) == "me/proj"
        assert calls == [["git", "-C", "/some/dir", "remote", "get-url", "origin"]]

    @pytest.mark.parametrize(
        "exc",
        [FileNotFoundError("git"), readme_evidence.subprocess.TimeoutExpired("git", 2)],
    )
    def test_detect_own_repo_failures_mean_no_exclusion(
        self, monkeypatch: pytest.MonkeyPatch, exc: Exception
    ) -> None:
        def boom(*a: object, **kw: object) -> None:
            raise exc

        monkeypatch.setattr(readme_evidence.subprocess, "run", boom)
        assert detect_own_repo(Path("/some/dir")) is None

    def test_detect_own_repo_nonzero_exit_means_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class Failed:
            returncode = 2
            stdout = ""

        monkeypatch.setattr(readme_evidence.subprocess, "run", lambda *a, **kw: Failed())
        assert detect_own_repo(Path("/some/dir")) is None

    def test_cli_own_repo_flag_overrides_detection(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(readme_evidence, "detect_own_repo", lambda d: "det/ected")
        assert main([str(FIXTURES / "sample_clean.md")]) == 0
        assert json.loads(capsys.readouterr().out)["own_repo"] == "det/ected"
        assert main([str(FIXTURES / "sample_clean.md"), "--own-repo", "o/r"]) == 0
        assert json.loads(capsys.readouterr().out)["own_repo"] == "o/r"
        assert (
            main([str(FIXTURES / "sample_clean.md"), "--own-repo", "https://github.com/o/r.git"])
            == 0
        )
        assert json.loads(capsys.readouterr().out)["own_repo"] == "o/r"
        assert main([str(FIXTURES / "sample_clean.md"), "--own-repo", ""]) == 0
        assert json.loads(capsys.readouterr().out)["own_repo"] is None


@pytest.mark.unit
class TestDocPaths:
    def test_dot_slash_docs_links_count_under_the_same_key(self) -> None:
        md = "# P\n\n[a](./docs/adr/0001.md) [b](docs/adr/0002.md) [c](./docs/guide.md)\n"
        assert _ev(md)["insider_refs"]["doc_paths"] == {"docs/adr": 2, "docs/guide.md": 1}


@pytest.mark.unit
class TestBrokenAnchors:
    """In-page `#fragment` links are checked against GitHub heading slugs and <a id/name>."""

    @pytest.mark.parametrize(
        ("heading", "slug"),
        [
            ("現状（2026-09-25 時点）", "現状2026-09-25-時点"),
            ("著者のほかの仕事", "著者のほかの仕事"),
            ("Hello, World!", "hello-world"),
            ("snake_case and kebab-case", "snake_case-and-kebab-case"),
            ("Install `foo` via [pip](https://pypi.org/p/foo)", "install-foo-via-pip"),
            ("What's new?  v2.0", "whats-new--v20"),
        ],
    )
    def test_github_slug(self, heading: str, slug: str) -> None:
        assert github_slug(heading) == slug

    def test_japanese_headings_resolve_and_misses_are_reported(self) -> None:
        md = (
            "# P\n\n## 現状（2026-09-25 時点）\n\n## 著者のほかの仕事\n\n"
            "[now](#現状2026-09-25-時点) [others](#著者のほかの仕事) [gone](#存在しない節)\n"
        )
        assert _ev(md)["structure"]["broken_anchors"] == [{"href": "#存在しない節", "line": 7}]

    def test_percent_encoded_fragment_resolves(self) -> None:
        md = "# P\n\n## 著者のほかの仕事\n\n[x](#%E8%91%97%E8%80%85%E3%81%AE%E3%81%BB%E3%81%8B%E3%81%AE%E4%BB%95%E4%BA%8B)\n"
        assert _ev(md)["structure"]["broken_anchors"] == []

    def test_repeated_headings_get_numbered_slugs(self) -> None:
        md = "# P\n\n## Usage\n\n## Usage\n\n[a](#usage) [b](#usage-1) [c](#usage-2)\n"
        assert _ev(md)["structure"]["broken_anchors"] == [{"href": "#usage-2", "line": 7}]

    def test_explicit_html_anchors_top_and_bare_hash_are_targets(self) -> None:
        md = (
            "# P\n\n<a id=\"custom\"></a>\n<a name='legacy'></a>\n\n"
            "[a](#custom) [b](#legacy) [c](#top) [d](#) [e](#nowhere)\n"
        )
        assert _ev(md)["structure"]["broken_anchors"] == [{"href": "#nowhere", "line": 6}]

    def test_fragment_links_are_not_local_file_refs(self) -> None:
        st = _ev("# P\n\n[x](#nowhere)\n")["structure"]
        assert st["broken_local_refs"] == []
        assert st["broken_anchors"] == [{"href": "#nowhere", "line": 3}]


@pytest.mark.unit
class TestRegisterJa:
    """Japanese register evidence over body prose paragraphs only."""

    def test_english_readme_has_null_register(self) -> None:
        assert _ev("# P\n\nPlain English lead.\n")["register_ja"] is None

    def test_counts_body_sentences_and_skips_non_paragraph_lines(self) -> None:
        md = (
            "# 見出しは数えない。\n\n"
            "これはツールです。設定は不要だ。「使えます」。\n"
            "試してください！本当か？\n\n"
            "- リストは数えない。\n"
            "| 表も | 数えない。 |\n"
            "> 引用も数えない。\n"
            '<p align="center">HTML も数えない。</p>\n'
            "![図](a.png) 画像行も数えない。\n\n"
            "```\nコードも数えない。\n```\n\n"
            "最後の文である。\n"
        )
        reg = _ev(md)["register_ja"]
        assert reg["desu_masu"] == 3
        assert reg["plain"] == 3
        assert reg["plain_lines"] == [
            {"line": 3, "text": "設定は不要だ。"},
            {"line": 4, "text": "本当か？"},
            {"line": 16, "text": "最後の文である。"},
        ]

    def test_polite_endings_with_closers_and_particles(self) -> None:
        md = (
            "# P\n\n"
            "動きます）。**重要です**。できますか？そうでしょう。始めましょう。ありません。"
            "でした。ました。\n"
        )
        reg = _ev(md)["register_ja"]
        assert reg == {"desu_masu": 8, "plain": 0, "plain_lines": []}

    def test_trailing_parenthetical_aside_does_not_hide_a_polite_ending(self) -> None:
        md = (
            "# P\n\n"
            "モデルに見せます（[docs](https://e.com/d)、2026-09-21 確認）。"
            "（詳しくは後述します）。設定は不要だ（注）。\n"
        )
        reg = _ev(md)["register_ja"]
        assert reg["desu_masu"] == 2
        assert reg["plain_lines"] == [{"line": 3, "text": "設定は不要だ（注）。"}]

    def test_sentence_spanning_lines_is_one_sentence_on_its_closing_line(self) -> None:
        md = "# P\n\n一文目です。二文目は\n折り返しで終わる。三文目です。\n"
        reg = _ev(md)["register_ja"]
        assert reg["desu_masu"] == 2 and reg["plain"] == 1
        assert reg["plain_lines"] == [{"line": 4, "text": "二文目は折り返しで終わる。"}]

    def test_pathological_inputs_stay_linear(self) -> None:
        # DoS backstop: each of these took > 120 s with a regex re-scan of the paragraph
        # buffer and a `\s*`-prefixed, `$`-anchored aside sub (2026-09-25 measurement).
        long_paragraph = "\n".join(["あいうえおかきくけこ" * 2] * 3000)
        md = (
            "# P\n\nです。です。です。\n\n" + long_paragraph + "\n\n"
            "あ" + " " * 30_000 + "ます（注）。\n\n"
            "ます" + "（注）" * 20_000 + "。\n"
        )
        assert _ev(md)["register_ja"]["desu_masu"] == 5

    def test_plain_lines_capped_at_20_and_text_at_60_chars(self) -> None:
        long = "あ" * 80 + "だ。"
        md = "# P\n\n" + "".join(f"文{i}だ。" for i in range(25)) + "\n\n" + long + "\n"
        reg = _ev(md)["register_ja"]
        assert reg["plain"] == 26
        assert len(reg["plain_lines"]) == 20
        md2 = "# P\n\nです。です。です。\n\n" + long + "\n"
        text = _ev(md2)["register_ja"]["plain_lines"][0]["text"]
        assert len(text) == 60 and text.endswith("あだ。")


@pytest.mark.integration
class TestFixtureContracts:
    def test_negative_control_uses_vertical_mermaid(self) -> None:
        text = (FIXTURES / "sample_clean.md").read_text(encoding="utf-8")
        assert "flowchart TD" in text and "flowchart LR" not in text

    def test_sample_issues_names_only_keys_the_script_reports(self) -> None:
        text = (FIXTURES / "sample_issues.md").read_text(encoding="utf-8")
        ev = collect_file(FIXTURES / "sample_issues.md")
        named = re.findall(r"(?<!\])\(([a-z0-9_]+(?:\.[a-z0-9_]+)*)\)", text)
        assert named, "the fixture should name the evidence keys it exercises"
        for dotted in named:
            node: object = ev
            for part in dotted.split("."):
                assert isinstance(node, dict) and part in node, dotted
                node = node[part]

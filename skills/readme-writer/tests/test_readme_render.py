"""Tests for readme_render — screenshots and layout measurements, never a verdict.

Pure helpers are tested directly. The browser path runs against a fake renderer (no
network, no `gh`) and is skipped when Playwright's Chromium is not installed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import readme_render as rr


@pytest.mark.unit
class TestRewriteRelativeUrls:
    def test_relative_src_becomes_file_uri(self, tmp_path: Path) -> None:
        out = rr.rewrite_relative_urls('<img src="assets/a.png" alt="x">', tmp_path)
        assert f'src="{(tmp_path / "assets/a.png").resolve().as_uri()}"' in out

    @pytest.mark.parametrize(
        "url", ["https://x/a.png", "//cdn/a.png", "#frag", "data:image/png;base64,AA"]
    )
    def test_absolute_and_fragment_urls_stay(self, url: str, tmp_path: Path) -> None:
        tag = f'<img src="{url}">'
        assert rr.rewrite_relative_urls(tag, tmp_path) == tag

    def test_href_and_prose_are_left_alone(self, tmp_path: Path) -> None:
        text = "<a href=\"docs/x.md\">x</a><p>src='a.png' in prose</p>"
        assert rr.rewrite_relative_urls(text, tmp_path) == text

    def test_root_relative_resolves_from_repo_root(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        out = rr.rewrite_relative_urls('<img src="/assets/a.png">', docs, tmp_path)
        assert (tmp_path / "assets/a.png").resolve().as_uri() in out

    @pytest.mark.parametrize("url", ["../../outside.png", "/../outside.png"])
    def test_paths_leaving_the_repo_do_not_load(self, url: str, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        out = rr.rewrite_relative_urls(f'<img src="{url}">', repo, repo)
        assert rr._OUTSIDE_REPO in out and "outside.png" not in out

    def test_query_and_percent_encoding(self, tmp_path: Path) -> None:
        out = rr.rewrite_relative_urls('<img src="my%20image.png?raw=true">', tmp_path)
        assert (tmp_path / "my image.png").resolve().as_uri() in out

    def test_srcset_candidates(self, tmp_path: Path) -> None:
        out = rr.rewrite_relative_urls('<source srcset="a.png 1x, b.png 2x">', tmp_path)
        a, b = ((tmp_path / n).resolve().as_uri() for n in ("a.png", "b.png"))
        assert f'srcset="{a} 1x, {b} 2x"' in out

    def test_repo_root_outside_git_is_the_directory(self, tmp_path: Path) -> None:
        assert rr.repo_root_of(tmp_path) == tmp_path.resolve()


@pytest.mark.unit
class TestConvertAlerts:
    def test_alert_blockquote_becomes_github_alert(self) -> None:
        html_in = "<blockquote>\n<p>[!WARNING]\nWatch out.</p>\n</blockquote>"
        out = rr.convert_alerts(html_in)
        assert out.startswith('<div class="markdown-alert markdown-alert-warning">')
        assert '<p class="markdown-alert-title">' in out and "Warning</p>" in out
        assert "<p>Watch out.</p>" in out and "blockquote" not in out

    def test_marker_alone_in_first_paragraph(self) -> None:
        out = rr.convert_alerts("<blockquote>\n<p>[!NOTE]</p>\n<p>Body.</p>\n</blockquote>")
        assert out.endswith("Note</p><p>Body.</p></div>")

    def test_lowercase_marker_is_an_alert(self) -> None:
        out = rr.convert_alerts("<blockquote>\n<p>[!tip]\nLower.</p>\n</blockquote>")
        assert out.startswith('<div class="markdown-alert markdown-alert-tip">')

    def test_text_after_marker_stays_a_quote(self) -> None:
        quote = "<blockquote>\n<p>[!TIP] same line</p>\n</blockquote>"
        assert rr.convert_alerts(quote) == quote

    def test_alert_holding_a_quote_stays_a_quote(self) -> None:
        nested = (
            "<blockquote>\n<p>[!NOTE]</p>\n<blockquote>\n<p>in</p>\n</blockquote>\n</blockquote>"
        )
        assert rr.convert_alerts(nested) == nested

    def test_plain_blockquote_stays(self) -> None:
        plain = "<blockquote>\n<p>Just a quote.</p>\n</blockquote>"
        assert rr.convert_alerts(plain) == plain


@pytest.mark.unit
class TestPageHtml:
    def test_width_font_and_stylesheet(self) -> None:
        page = rr.page_html("<p>x</p>", 293, 14)
        assert "width:293px" in page and "font-size:14px" in page
        assert rr.CSS.as_uri() in page
        assert "<article class='markdown-body'><p>x</p></article>" in page
        assert "blur" not in page

    def test_squint_blurs(self) -> None:
        assert "filter: blur(6px)" in rr.page_html("x", 846, squint=True)

    def test_vendored_stylesheet_exists_with_provenance(self) -> None:
        head = rr.CSS.read_text(encoding="utf-8")[:400]
        assert "github-markdown-css 5.9.0" in head and "MIT" in head


@pytest.mark.unit
class TestFold:
    BLOCKS = [{"top": 0}, {"top": 500}, {"top": 600}, {"top": 900}]

    def test_desktop_profile_sees_viewport_minus_offset(self) -> None:
        vp = rr.Viewport("desktop", 846, 800, 228, 14)
        assert rr.fold(vp, self.BLOCKS) == {
            "starts_below_fold": False,
            "first_screen_height": 572,
            "first_screen_blocks": [0, 1],
        }

    def test_unknown_offset_is_below_the_first_screen(self) -> None:
        vp = rr.Viewport("desktop", 838, 800, None, 16)
        got = rr.fold(vp, self.BLOCKS)
        assert got["starts_below_fold"] is True
        assert got["first_screen_height"] == 800

    def test_column_below_first_screen_uses_one_viewport(self) -> None:
        vp = rr.Viewport("mobile", 293, 812, 901, 14)
        got = rr.fold(vp, self.BLOCKS)
        assert got["starts_below_fold"] is True
        assert got["first_screen_height"] == 812
        assert got["first_screen_blocks"] == [0, 1, 2]


@pytest.mark.unit
class TestTiles:
    def test_tiles_cover_the_page(self) -> None:
        assert rr.tile_ranges(2500, 1200) == [(0, 1200), (1200, 1200), (2400, 100)]

    def test_short_page_is_one_tile(self) -> None:
        assert rr.tile_ranges(300) == [(0, 300)]

    def test_empty_page_still_one_tile(self) -> None:
        assert rr.tile_ranges(0) == [(0, 1)]

    def test_tile_long_edge_is_shown_unshrunk(self) -> None:
        assert rr.TILE_CSS_HEIGHT * rr.DEVICE_SCALE <= 2000


@pytest.mark.unit
class TestGhRender:
    def test_failure_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class Done:
            returncode = 1
            stderr = "HTTP 401"
            stdout = ""

        monkeypatch.setattr(rr.subprocess, "run", lambda *a, **k: Done())
        with pytest.raises(RuntimeError, match="401"):
            rr.gh_render("# x")

    def test_sends_markdown_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: dict = {}

        class Done:
            returncode = 0
            stderr = ""
            stdout = "<p>ok</p>"

        def fake_run(cmd: list[str], **_: object) -> Done:
            seen["cmd"] = cmd
            seen["body"] = json.loads(Path(cmd[-1]).read_text(encoding="utf-8"))
            return Done()

        monkeypatch.setattr(rr.subprocess, "run", fake_run)
        assert rr.gh_render("# x") == "<p>ok</p>"
        assert seen["cmd"][:5] == ["gh", "api", "-X", "POST", "/markdown"]
        assert seen["body"] == {"text": "# x", "mode": "markdown"}


@pytest.mark.unit
def test_main_missing_file(tmp_path: Path) -> None:
    assert rr.main([str(tmp_path / "nope.md"), "--out", str(tmp_path / "o")]) == 2


@pytest.mark.unit
@pytest.mark.parametrize(
    "exc", [ImportError("no playwright"), Exception("Executable doesn't exist")]
)
def test_main_render_failure_exits_2(
    exc: Exception, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# x\n", encoding="utf-8")

    def boom(*_: object) -> dict:
        raise exc

    monkeypatch.setattr(rr, "render", boom)
    assert rr.main([str(readme), "--out", str(tmp_path / "o")]) == 2


def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            pw.chromium.launch().close()
    except Exception:  # noqa: BLE001 — any launch failure means "skip"
        return False
    return True


FAKE_HTML = (
    "<h1>Name</h1><p>Lead.</p><h2>Start here</h2><ul><li>a</li></ul>"
    "<h2>Table</h2><table><tr><th>" + "x" * 300 + "</th></tr></table>"
    '<p><img src="pic.png" alt="pic"></p>'
)


@pytest.mark.integration
@pytest.mark.skipif(not _chromium_available(), reason="Playwright Chromium not installed")
def test_render_end_to_end_with_fake_renderer(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# ignored by the fake renderer\n", encoding="utf-8")
    ev = rr.render(readme, tmp_path / "out", "profile", renderer=lambda md: FAKE_HTML)
    desktop, mobile = ev["viewports"]
    assert [h["text"] for h in desktop["headings"]] == ["Name", "Start here", "Table"]
    assert mobile["starts_below_fold"] is True
    assert any(o["tag"] == "table" for o in mobile["overflow"])
    assert desktop["images"][0]["alt"] == "pic"
    for vp in (desktop, mobile):
        assert set(vp["tiles"]) == {"light", "dark", "squint"}
        assert all(Path(p).exists() for paths in vp["tiles"].values() for p in paths)
    assert json.loads((tmp_path / "out" / "render.json").read_text("utf-8")) == ev
    assert ev["tile_height"] == rr.TILE_CSS_HEIGHT
    assert desktop["blocks"][0]["tag"] == "h1"

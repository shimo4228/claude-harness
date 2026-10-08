"""Render a README the way GitHub draws it and emit screenshots plus layout measurements.

Evidence, not a verdict — the same contract as readme_evidence.py. readme-judge reads
the PNG tiles (Read shows images) and the JSON for checklist §V; this script never
decides whether the README looks good.

Pipeline: GitHub `POST /markdown` (mode=markdown) via `gh api` → alerts converted →
`<article class="markdown-body">` + the vendored assets/github-markdown.css →
Playwright Chromium at each width × light / dark → PNG tiles + measurements.

- mode=markdown renders a README the way github.com shows it, soft line breaks included,
  but leaves `> [!NOTE]`-style alerts as plain blockquotes; `convert_alerts` rewrites them
  into GitHub's `markdown-alert` markup. mode=gfm draws alerts but turns every soft line
  break into <br>, which a hard-wrapped README does not show on github.com (both observed
  2026-10-06). Not drawn locally: ```mermaid diagrams (github.com draws them with script;
  here they stay code blocks) and task-list checkboxes.
- Geometry is `SURFACES`, the README column of github.com measured on 2026-10-06 in a
  logged-in, dark-theme browser at 1280×800 and 375×812 (the single source; other docs
  point here). A profile README (github.com/shimo4228) is 846 / 293 px wide, starts at
  y=228 / 901 and uses 14 px body text. A repo README (github.com/shimo4228/agent-knowledge-
  cycle) is 838 / 309 px wide with 16 px text and starts under the file list, whose height
  varies by repo (1102 / 871 there), so its offset is None: the README begins below the
  first screen, and its first screen is the first viewport-height of the README.
- Tiles are at most 2000 px on the long edge — Read shows a 2400 px tile at 2000 px, and a
  request with more than 20 images caps each near 2000 px — and PNG (lossy JPEG blurs
  small text). Each tile covers `tile_height` CSS px of the README, from the top.
- The squint tiles carry CSS `filter: blur(6px)` (NN/g squint test) in light theme.

JSON contract (stdout, also written to <out>/render.json): path, surface, note, tile_height,
viewports: [{name, width, viewport_height, offset_top, font_size, starts_below_fold,
first_screen_height, height, headings: [{level, text, top}], blocks: [{tag, top,
height, text}], first_screen_blocks: [index into blocks], overflow: [{tag, top,
scroll_width, client_width, text}], images: [{alt, top, natural_width, natural_height,
width, height}], tiles: {light: [path], dark: [path], squint: [path]}}].

Exit codes: 0 = rendered, 2 = file missing / `gh` failed / browser missing.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

ASSETS = Path(__file__).resolve().parent.parent / "assets"
CSS = ASSETS / "github-markdown.css"
TILE_CSS_HEIGHT = 1000  # × device scale 2 = 2000 px, the size Read shows without shrinking
DEVICE_SCALE = 2
_GH_TIMEOUT_S = 30
_SCHEME_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//|#)")
# GitHub draws an alert only when the marker stands alone on the quote's first line; a
# quote holding another quote stays a plain blockquote here (the lookahead stops at it).
_ALERT_RE = re.compile(
    r"<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*(?=\n|</p>)"
    r"(?P<rest>(?:(?!<blockquote>).)*?)</blockquote>",
    re.DOTALL | re.IGNORECASE,
)
_MEDIA_TAG_RE = re.compile(r"<(?:img|source)\b[^>]*>", re.IGNORECASE)
_ATTR_URL_RE = re.compile(r"""(?P<attr>\b(?:src|srcset)=)(?P<q>["'])(?P<url>[^"']*)(?P=q)""")
_OUTSIDE_REPO = "invalid:outside-repository"  # loads as a broken image, as on github.com
_GIT_TIMEOUT_S = 2


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int  # README column width in CSS px
    viewport_height: int
    offset_top: int | None  # where the README column starts; None = below the first screen
    font_size: int  # body text size of the README column


SURFACES: dict[str, tuple[Viewport, ...]] = {
    "profile": (Viewport("desktop", 846, 800, 228, 14), Viewport("mobile", 293, 812, 901, 14)),
    "repo": (Viewport("desktop", 838, 800, None, 16), Viewport("mobile", 309, 812, None, 16)),
}

# Collects measurements relative to the top of the README column.
_MEASURE_JS = """() => {
  const root = document.querySelector('article.markdown-body');
  const base = root.getBoundingClientRect().top + window.scrollY;
  const top = (el) => Math.round(el.getBoundingClientRect().top + window.scrollY - base);
  const text = (el) => (el.innerText || el.getAttribute('alt') || '').trim().replace(/\\s+/g, ' ').slice(0, 80);
  return {
    height: Math.round(root.getBoundingClientRect().height),
    headings: [...root.querySelectorAll('h1,h2,h3')].map(h => ({level: Number(h.tagName[1]), text: text(h), top: top(h)})),
    blocks: [...root.children].map(el => ({tag: el.classList.contains('markdown-heading') && el.firstElementChild ? el.firstElementChild.tagName.toLowerCase() : el.tagName.toLowerCase() + (el.classList.contains('markdown-alert') ? '.alert' : ''), top: top(el), height: Math.round(el.getBoundingClientRect().height), text: text(el)})),
    overflow: [...root.querySelectorAll('table,pre,img,div')].filter(el => el.scrollWidth > el.clientWidth + 1).map(el => ({tag: el.tagName.toLowerCase(), top: top(el), scroll_width: el.scrollWidth, client_width: el.clientWidth, text: text(el)})),
    images: [...root.querySelectorAll('img')].map(im => ({alt: im.getAttribute('alt') || '', top: top(im), natural_width: im.naturalWidth, natural_height: im.naturalHeight, width: Math.round(im.getBoundingClientRect().width), height: Math.round(im.getBoundingClientRect().height)})),
  };
}"""


def convert_alerts(fragment: str) -> str:
    """Rewrite `<blockquote><p>[!NOTE] ...` (mode=markdown output) into the markup
    github.com uses for alerts, so the stylesheet draws the coloured bar and title.
    The title icon is an empty 16 px box: it keeps the spacing, not the glyph."""

    def fix(m: re.Match[str]) -> str:
        kind = m.group(1).lower()
        rest = m.group("rest").strip()
        body = rest[len("</p>") :].strip() if rest.startswith("</p>") else f"<p>{rest}"
        return (
            f'<div class="markdown-alert markdown-alert-{kind}">'
            f'<p class="markdown-alert-title"><svg class="octicon mr-2" width="16" height="16">'
            f"</svg>{kind.capitalize()}</p>{body}</div>"
        )

    return _ALERT_RE.sub(fix, fragment)


def repo_root_of(directory: Path) -> Path:
    """The git top level holding `directory`, or `directory` itself outside git."""
    try:
        done = subprocess.run(
            ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return directory.resolve()
    top = done.stdout.strip()
    return Path(top).resolve() if done.returncode == 0 and top else directory.resolve()


def _local_url(url: str, base_dir: Path, repo_root: Path) -> str:
    """file:// URI for a repo-relative image URL, resolved the way github.com does: a
    leading / from the repo root, anything else from the README's directory. A path that
    leaves the repository becomes a URL that does not load."""
    raw = html.unescape(url)
    if not raw or _SCHEME_RE.match(raw):
        return url
    path = unquote(raw.split("#")[0].split("?")[0])
    target = (repo_root / path.lstrip("/") if path.startswith("/") else base_dir / path).resolve()
    return target.as_uri() if target.is_relative_to(repo_root) else _OUTSIDE_REPO


def rewrite_relative_urls(fragment: str, base_dir: Path, repo_root: Path | None = None) -> str:
    """Point the relative src / srcset URLs of <img> and <source> tags at the repo's files.
    Text outside those tags is never touched."""
    root = (repo_root or base_dir).resolve()
    base = base_dir.resolve()

    def fix_attr(m: re.Match[str]) -> str:
        if m.group("attr").startswith("srcset"):
            parts = [c.strip().split(None, 1) for c in m.group("url").split(",") if c.strip()]
            value = ", ".join(" ".join([_local_url(p[0], base, root), *p[1:]]) for p in parts)
        else:
            value = _local_url(m.group("url"), base, root)
        return f"{m.group('attr')}{m.group('q')}{value}{m.group('q')}"

    return _MEDIA_TAG_RE.sub(lambda t: _ATTR_URL_RE.sub(fix_attr, t.group(0)), fragment)


def page_html(
    fragment: str, width: int, font_size: int = 16, css: Path = CSS, squint: bool = False
) -> str:
    blur = "filter: blur(6px);" if squint else ""
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<link rel='stylesheet' href='{css.as_uri()}'>"
        "<style>html,body{margin:0;padding:0}"
        "body{background:light-dark(#ffffff,#0d1117);color-scheme:light dark}"
        f".markdown-body{{box-sizing:border-box;width:{width}px;padding:0;"
        f"font-size:{font_size}px;{blur}}}</style>"
        f"</head><body><article class='markdown-body'>{fragment}</article></body></html>"
    )


def fold(vp: Viewport, blocks: list[dict]) -> dict:
    """What a reader sees of the README on the first screen. When the column starts below
    the first screen (a profile README on a phone), report that and treat the first
    viewport-height of the README as its first screen."""
    visible = 0 if vp.offset_top is None else vp.viewport_height - vp.offset_top
    below = visible <= 0
    height = vp.viewport_height if below else visible
    return {
        "starts_below_fold": below,
        "first_screen_height": height,
        "first_screen_blocks": [i for i, b in enumerate(blocks) if b["top"] < height],
    }


def tile_ranges(total_height: int, tile_height: int = TILE_CSS_HEIGHT) -> list[tuple[int, int]]:
    """(top, height) clips that cover the page; the last tile is the remainder."""
    total_height = max(total_height, 1)
    return [(y, min(tile_height, total_height - y)) for y in range(0, total_height, tile_height)]


def gh_render(markdown: str) -> str:
    """HTML fragment from GitHub's renderer (sanitised by GitHub, so no scripts)."""
    body = {"text": markdown, "mode": "markdown"}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body, f)
        payload = f.name
    try:
        done = subprocess.run(
            ["gh", "api", "-X", "POST", "/markdown", "--input", payload],
            capture_output=True,
            text=True,
            timeout=_GH_TIMEOUT_S,
            check=False,
        )
    finally:
        Path(payload).unlink(missing_ok=True)
    if done.returncode != 0:
        raise RuntimeError(f"gh api /markdown failed: {done.stderr.strip()[:300]}")
    return done.stdout


def _shoot(page, out: Path, stem: str, height: int) -> list[str]:  # noqa: ANN001
    paths = []
    for n, (y, h) in enumerate(tile_ranges(height), start=1):
        path = out / f"{stem}-{n}.png"
        page.screenshot(
            path=str(path),
            clip={"x": 0, "y": y, "width": page.viewport_size["width"], "height": h},
            full_page=True,
        )
        paths.append(str(path))
    return paths


def _open(page, file: Path, document: str) -> None:  # noqa: ANN001
    """Load from a file:// URL: a page set from a string has an opaque origin, and
    Chromium then refuses the file:// images of the repo."""
    file.write_text(document, encoding="utf-8")
    page.goto(file.as_uri(), wait_until="networkidle")


def _capture(browser, fragment: str, vp: Viewport, out: Path) -> dict:  # noqa: ANN001
    result: dict = {}
    tiles: dict[str, list[str]] = {}
    for scheme in ("light", "dark"):
        ctx = browser.new_context(
            viewport={"width": vp.width, "height": vp.viewport_height},
            color_scheme=scheme,
            device_scale_factor=DEVICE_SCALE,
        )
        page = ctx.new_page()
        _open(page, out / f"{vp.name}.html", page_html(fragment, vp.width, vp.font_size))
        if scheme == "light":
            result = page.evaluate(_MEASURE_JS)
        tiles[scheme] = _shoot(page, out, f"{vp.name}-{scheme}", result["height"])
        if scheme == "light":
            _open(
                page,
                out / f"{vp.name}-squint.html",
                page_html(fragment, vp.width, vp.font_size, squint=True),
            )
            tiles["squint"] = _shoot(page, out, f"{vp.name}-squint", result["height"])
        ctx.close()
    return {
        "name": vp.name,
        "width": vp.width,
        "viewport_height": vp.viewport_height,
        "offset_top": vp.offset_top,
        "font_size": vp.font_size,
        **fold(vp, result["blocks"]),
        **result,
        "tiles": tiles,
    }


def render(
    path: Path,
    out: Path,
    surface: str = "repo",
    renderer: Callable[[str], str] = gh_render,
) -> dict:
    from playwright.sync_api import sync_playwright

    fragment = rewrite_relative_urls(
        convert_alerts(renderer(path.read_text(encoding="utf-8"))),
        path.parent,
        repo_root_of(path.parent),
    )
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            viewports = [_capture(browser, fragment, vp, out) for vp in SURFACES[surface]]
        finally:
            browser.close()
    ev = {
        "path": str(path),
        "surface": surface,
        "note": "evidence only — no verdict; github-markdown-css approximates github.com",
        "tile_height": TILE_CSS_HEIGHT,
        "viewports": viewports,
    }
    (out / "render.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2), "utf-8")
    return ev


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("path", type=Path, help="README Markdown file")
    parser.add_argument("--out", type=Path, required=True, help="directory for PNG tiles")
    parser.add_argument("--surface", choices=sorted(SURFACES), default="repo")
    args = parser.parse_args(argv)
    if not args.path.exists():
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2
    try:
        ev = render(args.path, args.out, args.surface)
    except ImportError as exc:  # playwright missing: run `uv sync` in the skill
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 — gh, OS and Playwright (browser missing) errors
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(ev, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

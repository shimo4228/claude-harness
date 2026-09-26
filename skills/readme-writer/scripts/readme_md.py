"""Markdown structure parsing for readme_evidence (fence-aware lines, headings,
images, links, prose-line test, GitHub heading slugs and in-file anchors).

Pure functions over the Markdown text; no evidence section and no I/O lives here.
The evidence sections (readme_sections / readme_prose) and the entry point
(readme_evidence) build on these parsers. Fenced code is excluded from every
line-level view; front matter is skipped by `_content_lines`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import unquote

_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
# Title anchored to a non-space char to avoid O(n^2) backtracking on a long
# all-space suffix (ReDoS guard).
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(\S(?:.*\S)?)\s*$")
_TRAILING_HASHES_RE = re.compile(r"\s+#+\s*$")
_SETEXT_H1_RE = re.compile(r"^ {0,3}=+\s*$")
_SETEXT_H2_RE = re.compile(r"^ {0,3}-+\s*$")
_LIST_OR_QUOTE_RE = re.compile(r"^\s*([-*+>]\s|\d+[.)]\s)")
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
_MD_LINK_RE = re.compile(
    r"(?<!!)\[(?!!)([^\]]*)\]\(\s*([^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
_HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_ATTR_SRC_RE = re.compile(r"\bsrc\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_ATTR_ALT_RE = re.compile(r"\balt\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
_DETAILS_OPEN_RE = re.compile(r"<details\b", re.IGNORECASE)
_DETAILS_CLOSE_RE = re.compile(r"</details\s*>", re.IGNORECASE)
_NON_PROSE_PREFIX_RE = re.compile(
    r"^(#{1,6}\s|[-*+>]\s|\d+[.)]\s|\||<|\[[^\]]+\]:\s"
    r"|={2,}\s*$|-{3,}\s*$|\*{3,}\s*$|_{3,}\s*$)"
)
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
_HTML_A_TAG_RE = re.compile(r"<a\b[^<>]*>", re.IGNORECASE)  # [^<>]: a "<" run stays linear
_ATTR_ID_NAME_RE = re.compile(r"(?<![\w-])(?:id|name)\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)

_MAX_LINE = 100_000


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line: int


@dataclass(frozen=True)
class Image:
    alt: str
    src: str
    line: int


@dataclass(frozen=True)
class Link:
    text: str
    href: str
    line: int


def _content_lines(markdown: str) -> list[tuple[int, str]]:
    """(1-based line number, text) for lines outside fenced code blocks."""
    out: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_len = 0
    raw = markdown.splitlines()
    skip_until = 0
    if raw and raw[0].strip() == "---":  # YAML front matter: skip through the closing ---
        for j in range(1, len(raw)):
            if raw[j].strip() == "---":
                skip_until = j + 1
                break
    for idx, line in enumerate(raw, start=1):
        if idx <= skip_until:
            continue
        if len(line) > _MAX_LINE:
            line = line[:_MAX_LINE]
        match = _FENCE_RE.match(line)
        if match:
            run = match.group("fence")
            marker, length = run[0], len(run)
            rest = match.group("rest")
            if fence_char is None:
                fence_char, fence_len = marker, length
                continue
            if marker == fence_char and length >= fence_len and not rest.strip():
                fence_char, fence_len = None, 0
            continue
        if fence_char is None:
            out.append((idx, line))
    return out


def _fence_lines(markdown: str) -> list[tuple[int, str]]:
    """Opening fence lines with their info string (to find ```mermaid blocks)."""
    out: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_len = 0
    for idx, line in enumerate(markdown.splitlines(), start=1):
        match = _FENCE_RE.match(line)
        if not match:
            continue
        run = match.group("fence")
        marker, length = run[0], len(run)
        rest = match.group("rest").strip()
        if fence_char is None:
            fence_char, fence_len = marker, length
            out.append((idx, rest))
        elif marker == fence_char and length >= fence_len and not rest:
            fence_char, fence_len = None, 0
    return out


def _setext_level(line: str) -> int:
    if _SETEXT_H1_RE.match(line):
        return 1
    if _SETEXT_H2_RE.match(line):
        return 2
    return 0


def parse_headings(markdown: str) -> list[Heading]:
    content = _content_lines(markdown)
    headings: list[Heading] = []
    for i, (line_no, line) in enumerate(content):
        atx = _HEADING_RE.match(line)
        if atx:
            text = _TRAILING_HASHES_RE.sub("", atx.group(2)).strip()
            headings.append(Heading(level=len(atx.group(1)), text=text, line=line_no))
            continue
        level = _setext_level(line)
        if level and i > 0:
            prev_no, prev_text = content[i - 1]
            if (
                prev_no == line_no - 1
                and prev_text.strip()
                and not _HEADING_RE.match(prev_text)
                and not _LIST_OR_QUOTE_RE.match(prev_text)
            ):
                headings.append(Heading(level=level, text=prev_text.strip(), line=prev_no))
    return headings


def _attr_value(raw: str | None) -> str:
    return "" if raw is None else raw[1:-1]


def parse_images(markdown: str) -> list[Image]:
    images: list[Image] = []
    for line_no, line in _content_lines(markdown):
        for m in _MD_IMAGE_RE.finditer(line):
            images.append(Image(alt=m.group(1), src=m.group(2), line=line_no))
        for tag in _HTML_IMG_RE.finditer(line):
            src_m = _ATTR_SRC_RE.search(tag.group(0))
            alt_m = _ATTR_ALT_RE.search(tag.group(0))
            images.append(
                Image(
                    alt=_attr_value(alt_m.group(1) if alt_m else None),
                    src=_attr_value(src_m.group(1) if src_m else None),
                    line=line_no,
                )
            )
    return images


def parse_links(markdown: str) -> list[Link]:
    return [
        Link(text=m.group(1), href=m.group(2), line=line_no)
        for line_no, line in _content_lines(markdown)
        for m in _MD_LINK_RE.finditer(line)
    ]


def _is_external(href: str) -> bool:
    h = href.strip()
    return bool(_SCHEME_RE.match(h)) or h.startswith("//")


_HTML_INLINE_OPEN_RE = re.compile(r"^<(p|b|strong|em|i)\b[^>]*>", re.IGNORECASE)


def _is_prose_line(stripped: str) -> bool:
    if not stripped:
        return False
    if _HTML_INLINE_OPEN_RE.match(stripped):
        # <p align="center"><b>X</b> is a ...</p>: judge the text, not the tag
        stripped = re.sub(r"<[^>]+>", "", stripped).strip()
        if not stripped:
            return False
    if _NON_PROSE_PREFIX_RE.match(stripped):
        return False
    bare = _MD_LINK_RE.sub("", _MD_IMAGE_RE.sub("", stripped)).strip()
    if not bare:
        return False
    text = _MD_IMAGE_RE.sub(" ", stripped)
    text = _MD_LINK_RE.sub(lambda m: f" {m.group(1)} ", text)
    return bool(_LETTER_RE.search(text))


def _prose_only(text: str) -> str:
    """Replace images with their alt and links with their text, so URLs never
    feed the prose-level pattern scans (a badge URL is not a numeric claim)."""
    text = _MD_IMAGE_RE.sub(lambda m: m.group(1), text)
    text = _MD_LINK_RE.sub(lambda m: m.group(1), text)
    return re.sub(r"https?://\S+", "", text)


def _details_depth_map(content: list[tuple[int, str]]) -> dict[int, bool]:
    """line -> True when the line sits inside a <details> body."""
    inside: dict[int, bool] = {}
    depth = 0
    for line_no, line in content:
        depth += len(_DETAILS_OPEN_RE.findall(line))
        inside[line_no] = depth > 0
        depth = max(0, depth - len(_DETAILS_CLOSE_RE.findall(line)))
    return inside


def _slug_char_kept(ch: str) -> bool:
    # github-slugger (the slugger GitHub's renderer mirrors), regex generator read
    # 2026-09-25: it strips No, all punctuation except Pc and "-", symbols, controls and
    # separators except " ". What survives: letters, marks, Nd / Nl, Pc ("_"), " ", "-".
    if ch in " -":
        return True
    cat = unicodedata.category(ch)
    return cat[0] in "LM" or cat in ("Nd", "Nl", "Pc")


def github_slug(text: str) -> str:
    """The anchor GitHub gives a heading: rendered text (images dropped, links reduced
    to their text, tags removed), lowercased, filtered by `_slug_char_kept`, each space
    turned into "-" (runs of spaces are not collapsed)."""
    text = _MD_IMAGE_RE.sub("", text)
    text = _MD_LINK_RE.sub(lambda m: m.group(1), text)
    text = re.sub(r"<[^<>]+>", "", text)  # [^<>]: a "<" run stays linear
    return "".join(ch for ch in text.lower() if _slug_char_kept(ch)).replace(" ", "-")


def anchor_targets(headings: list[Heading], content: list[tuple[int, str]]) -> set[str]:
    """Fragments that resolve in this file: heading slugs (a repeated slug gets -1, -2,
    … in document order, the github-slugger loop) and explicit <a id/name> values."""
    targets: set[str] = set()
    occurrences: dict[str, int] = {}
    for h in headings:
        base = slug = github_slug(h.text)
        while slug in occurrences:
            occurrences[base] += 1
            slug = f"{base}-{occurrences[base]}"
        occurrences[slug] = 0
        targets.add(slug)
    for _n, line in content:
        for tag in _HTML_A_TAG_RE.finditer(line):
            targets.update(_attr_value(m.group(1)) for m in _ATTR_ID_NAME_RE.finditer(tag.group(0)))
    return targets


def broken_anchors(links: list[Link], targets: set[str]) -> list[dict]:
    out = []
    for ln in links:
        href = ln.href.strip()
        if not href.startswith("#"):
            continue
        fragment = unquote(href[1:])
        # "#" and "#top" scroll to the top in every browser (HTML spec), heading or not
        if fragment in targets or fragment == "" or fragment.lower() == "top":
            continue
        out.append({"href": ln.href, "line": ln.line})
    return out

"""Split a README / Zenn article into the units the reader-cut pilot marks and judges.

A unit is one prose sentence (closed by 。！？, may wrap across the lines of one
paragraph; a paragraph's unterminated tail is a unit too) or one list item. Never a
unit: fenced code, front matter, headings, table rows, HTML lines, image-only lines,
Zenn `:::` fences, link reference definitions, rules. Each unit carries the section
index (count of headings seen before it) so the forward-only arm (A3) can cut the
text at section boundaries. Plan: docs/plans/reader-cut-pilot.html claim 1.1.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__:
    from . import readme_md as _md
else:  # direct script invocation
    import readme_md as _md

_SENTENCE_END_RE = re.compile(r"[。！？]")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?")
_QUOTE_RE = re.compile(r"^\s*>\s?")
_ZENN_FENCE_RE = re.compile(r"^\s*:::")
_SKIP_PREFIX_RE = re.compile(r"^(\||<|\[[^\]]+\]:\s|={2,}\s*$|-{3,}\s*$|\*{3,}\s*$|_{3,}\s*$)")
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
_EMPTY_LINK_RE = re.compile(
    r"\[\s*\]\([^)]*\)"
)  # what a linked badge leaves once its image is gone
_EMPHASIS_RE = re.compile(r"\*\*|__|(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)")


@dataclass(frozen=True)
class Unit:
    i: int
    line: int
    section: int
    kind: str  # "sentence" | "item"
    text: str


def _clean(text: str) -> str:
    """Display text: links and images reduced to their words, emphasis markers dropped."""
    return _EMPHASIS_RE.sub("", _md._prose_only(text)).strip()


def _has_letters(text: str) -> bool:
    return bool(_LETTER_RE.search(text))


def _is_image_only(stripped: str) -> bool:
    rest = _EMPTY_LINK_RE.sub("", _md._MD_IMAGE_RE.sub("", stripped))
    return not rest.strip(" \t|·")


def _sentences(text: str) -> tuple[list[str], str]:
    """Closed sentences in `text`, and the unterminated rest."""
    out: list[str] = []
    start = 0
    for m in _SENTENCE_END_RE.finditer(text):
        out.append(text[start : m.end()].strip())
        start = m.end()
    return [s for s in out if _has_letters(s)], text[start:]


def _join(head: str, tail: str) -> str:
    """Join two lines of one paragraph: no separator in Japanese, a space between
    Latin words (`Claude` + `Code` must not become `ClaudeCode`)."""
    head = head.rstrip()
    if head and tail and head[-1].isascii() and head[-1].isalnum() and tail[0].isascii():
        return f"{head} {tail}"
    return head + tail


class _Builder:
    def __init__(self) -> None:
        self.units: list[Unit] = []
        self.section = 0
        self.pending = ""
        self.pending_line = 0

    def add(self, line: int, kind: str, text: str) -> None:
        if _has_letters(text):
            self.units.append(Unit(len(self.units), line, self.section, kind, text))

    def flush(self) -> None:
        rest = self.pending.strip()
        if rest:
            self.add(self.pending_line, "sentence", rest)
        self.pending, self.pending_line = "", 0

    def prose(self, line: int, text: str) -> None:
        if not self.pending:
            self.pending_line = line
        closed, rest = _sentences(_join(self.pending, text))
        for s in closed:
            self.add(self.pending_line, "sentence", s)
            self.pending_line = line
        self.pending = rest
        if not rest.strip():
            self.pending = ""


def extract_units(markdown: str) -> list[Unit]:
    """Units of `markdown` in reading order. Pure: no I/O."""
    content = _md._content_lines(markdown)
    heading_lines = {h.line for h in _md.parse_headings(markdown)}
    b = _Builder()
    prev = -1
    for n, raw in content:
        stripped = raw.strip()
        if n != prev + 1 or not stripped:
            b.flush()
        prev = n
        if not stripped:
            continue
        if n in heading_lines:
            b.flush()
            b.section += 1
            continue
        if _ZENN_FENCE_RE.match(stripped) or _SKIP_PREFIX_RE.match(stripped):
            b.flush()
            continue
        if _is_image_only(stripped) or _md._HTML_IMG_RE.search(stripped):
            b.flush()
            continue
        item = _LIST_ITEM_RE.match(raw)
        if item:
            b.flush()
            b.add(n, "item", _clean(raw[item.end() :]))
            continue
        b.prose(n, _clean(_QUOTE_RE.sub("", stripped)))
    b.flush()
    return b.units


def _last_modified(path: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(path.parent), "log", "-1", "--format=%cs", "--", path.name],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except OSError:
        return None
    return out or None


def _display_path(path: Path) -> str:
    """`~/…` for a path under the home directory: the units JSON is published with the harness."""
    try:
        return "~/" + path.resolve().relative_to(Path.home().resolve()).as_posix()
    except ValueError:
        return str(path)


def units_record(path: Path, text_id: str) -> dict:
    """The units JSON of plan claim 1.1, with every mark unset."""
    raw = path.read_bytes()
    units = extract_units(raw.decode("utf-8"))
    return {
        "text_id": text_id,
        "source": _display_path(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "last_modified": _last_modified(path),
        "reader": "author",
        "units": [{**asdict(u), "mark": None} for u in units],
    }

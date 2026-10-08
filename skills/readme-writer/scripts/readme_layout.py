"""Layout evidence: which block forms each H2 section uses, read from Markdown text.

Counts only — the visual judgment (does a list look plain next to a table, is the
difference in form a difference in role) belongs to readme-judge §V, which also
sees the rendered screenshots from readme_render.py. The forms are the ones GitHub's
stylesheet draws differently: tables carry borders and zebra rows, alerts a coloured
bar and title, blockquotes a grey bar, lists nothing (research report 2026-10-06 §2).
"""

from __future__ import annotations

import re
from bisect import bisect_right

if __package__:
    from . import readme_md as _md
else:  # Support the documented direct script invocation.
    import readme_md as _md

_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?P<body>.*)$")
# GFM delimiter row: one or more '-' per cell; a pipe is required so a bare --- (a rule)
# never opens a table (checked in _is_delimiter).
_TABLE_DELIM_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*$")
# GitHub draws an alert only when the marker stands alone on the first line of a quote.
_ALERT_RE = re.compile(r"^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", re.IGNORECASE)
_CODE_SPAN_RE = re.compile(r"`[^`]*`")
_QUOTE_RE = re.compile(r"^\s*>")
# Link texts that name no destination; matched on the whole, lower-cased link text.
_GENERIC_LINK_TEXTS = frozenset(
    {"here", "click here", "this", "link", "this link", "read more", "more", "こちら", "ここ"}
)
# Words English title case leaves lower-case; they never decide the casing style.
_SMALL_WORDS = frozenset(
    "a an and as at but by for from in into nor of on or per the to vs via with".split()
)
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’-]*")
_FORMS = (
    "paragraphs",
    "list_items",
    "tables",
    "alerts",
    "blockquotes",
    "images",
    "diagrams",
    "code_blocks",
    "details",
)


def _is_delimiter(line: str) -> bool:
    return "|" in line and bool(_TABLE_DELIM_RE.match(line))


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _lead_type(body: str) -> str:
    b = body.lstrip()
    if b.startswith(("**", "__")):
        return "bold"
    if b.startswith("["):
        return "link"
    return "text"


class _Scanner:
    """One pass over the content lines. Counts block starts, not lines: `prev` is the
    kind of the previous non-continuation line, so a 3-row table counts once."""

    def __init__(self, image_lines: set[int]) -> None:
        self.image_lines = image_lines
        self.sections: list[dict] = [
            {"heading": None, "line": 0, "forms": dict.fromkeys(_FORMS, 0)}
        ]
        self.lists: list[dict] = []
        self.tables: list[dict] = []
        self.alerts: list[dict] = []
        self.prev = "blank"

    @property
    def forms(self) -> dict[str, int]:
        return self.sections[-1]["forms"]

    def heading(self, heading: _md.Heading) -> None:
        if heading.level <= 2:
            self.sections.append(
                {"heading": heading.text, "line": heading.line, "forms": dict.fromkeys(_FORMS, 0)}
            )
        self.prev = "heading"

    def table_row(self, line_no: int, line: str) -> None:
        if self.prev != "table":
            self.forms["tables"] += 1
            self.tables.append(
                {"line": line_no, "columns": len(_cells(line)), "rows": 0, "longest_cell": 0}
            )
        elif not _TABLE_DELIM_RE.match(line):
            table = self.tables[-1]
            table["rows"] += 1
            table["longest_cell"] = max(table["longest_cell"], *(len(c) for c in _cells(line)))
        self.prev = "table"

    def list_item(self, line_no: int, body: str) -> None:
        self.forms["list_items"] += 1
        if self.prev not in ("list", "list_gap"):  # a blank line between items keeps one list
            self.lists.append({"line": line_no, "items": 0, "lead_types": {}})
        current = self.lists[-1]
        current["items"] += 1
        kind = _lead_type(body)
        current["lead_types"][kind] = current["lead_types"].get(kind, 0) + 1
        self.prev = "list"

    def quote(self, line_no: int, line: str) -> None:
        alert = _ALERT_RE.match(line) if self.prev not in ("quote", "alert") else None
        if alert:
            self.forms["alerts"] += 1
            self.alerts.append({"type": alert.group(1).upper(), "line": line_no})
            self.prev = "alert"
        elif self.prev not in ("quote", "alert"):
            self.forms["blockquotes"] += 1
            self.prev = "quote"

    def other(self, line_no: int, stripped: str) -> None:
        prose = _md._is_prose_line(stripped)
        opens, _ = _md.details_tags(stripped)
        if opens:
            self.forms["details"] += opens
            self.prev = "html"
        elif line_no in self.image_lines and not prose:
            self.forms["images"] += 1
            self.prev = "image"
        elif prose:
            if self.prev != "paragraph":
                self.forms["paragraphs"] += 1
            self.prev = "paragraph"
        else:
            self.prev = "html"

    def line(self, line_no: int, line: str, next_line: str, heading: _md.Heading | None) -> None:
        stripped = line.strip()
        if heading is not None:
            self.heading(heading)
        elif not stripped:
            self.prev = "list_gap" if self.prev in ("list", "list_gap") else "blank"
        elif "|" in stripped and (self.prev == "table" or _is_delimiter(next_line)):
            self.table_row(line_no, stripped)
        elif _QUOTE_RE.match(line):
            self.quote(line_no, line)
        elif item := _LIST_ITEM_RE.match(line):
            self.list_item(line_no, item.group("body"))
        elif self.prev == "list" or (self.prev == "list_gap" and line.startswith((" ", "\t"))):
            self.prev = "list"  # an indented continuation, or a lazy one right under an item
        else:
            self.other(line_no, stripped)


def heading_case(headings: list[_md.Heading]) -> dict:
    """Casing style of headings with 2+ English words after the first one.
    title = every non-small later word is capitalised; sentence = at least one is not."""
    counts = {"title": 0, "sentence": 0}
    items = []
    for h in headings:
        text = _md._MD_LINK_RE.sub(lambda m: m.group(1), _CODE_SPAN_RE.sub(" ", h.text))
        later = [w for w in _WORD_RE.findall(text)[1:] if w.lower() not in _SMALL_WORDS]
        if not later:
            continue
        style = "title" if all(w[0].isupper() for w in later) else "sentence"
        counts[style] += 1
        items.append({"line": h.line, "text": h.text, "style": style})
    return {**counts, "items": items}


def generic_link_text(links: list[_md.Link]) -> list[dict]:
    return [
        {"text": lk.text, "line": lk.line}
        for lk in links
        if lk.text.strip().lower() in _GENERIC_LINK_TEXTS
    ]


def layout(
    content: list[tuple[int, str]],
    headings: list[_md.Heading],
    images: list[_md.Image],
    links: list[_md.Link],
    fences: list[tuple[int, str]],
) -> dict:
    """Pure. `fences` are (opening line, info string) of fenced blocks, which are absent
    from `content`; each counts in the section whose heading precedes it, as a diagram
    when GitHub draws it (```mermaid) and as a code block otherwise."""
    scanner = _Scanner({i.line for i in images})
    heading_at = {h.line: h for h in headings}
    texts = dict(content)
    for line_no, line in content:
        scanner.line(line_no, line, texts.get(line_no + 1, ""), heading_at.get(line_no))
    starts = [s["line"] for s in scanner.sections]
    for fence_line, info in fences:
        kind = "diagrams" if info.split()[:1] == ["mermaid"] else "code_blocks"
        scanner.sections[bisect_right(starts, fence_line) - 1]["forms"][kind] += 1
    sections = [s for s in scanner.sections if s["heading"] is not None or any(s["forms"].values())]
    return {
        "sections": sections,
        "lists": scanner.lists,
        "tables": scanner.tables,
        "alerts": {"count": len(scanner.alerts), "items": scanner.alerts},
        "heading_case": heading_case(headings),
        "generic_link_text": generic_link_text(links),
    }

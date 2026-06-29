"""Structural-only linter for human-facing README files.

This module checks **structural** properties only — properties decidable from
the literal shape of the Markdown (heading hierarchy, image alt text, local
link resolution). Per AKC ADR-0008 "Code-LLM Layering", code owns structural
determinism and 100% accuracy; semantic quality (does the lead hook a human?
is the value proposition clear? does the narrative flow?) is a holistic LLM
judgment and is **never scored here**.

Checks carry a severity. Four **error** checks (single_h1, heading_levels,
alt_text, local_link) are hard-structural and gate the build. Five **warning**
checks (raster_diagram_hint, badge_budget, details_floor_leak, identity_lead,
doi_citation_pairing) are advisory dual-audience / visual-first nudges: each is
structural (decidable from the literal markdown), but the "is this actually a
problem here?" call is a judgment, so they are surfaced for the human / LLM
review and never block. The semantic verdict stays with the holistic LLM pass.

The CLI exit code is the code-owned gate: 0 = clean OR warnings only, 1 = at
least one error-severity issue, 2 = file not found / too large. A non-zero exit
is the deterministic signal a downstream step (CI, a skill workflow) can enforce.

  https://github.com/shimo4228/agent-knowledge-cycle/blob/main/docs/adr/0008-code-and-llm-collaboration.md

Markdown coverage: ATX headings (`#`, 0-3 leading spaces) and setext headings
(`===` / `---` underlines) are detected. Fenced code blocks (``` / ~~~, with
matching marker and length, closer must be blank after the run) are skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import unquote

_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
# The captured title must start with a non-space char: `(\S(?:.*\S)?)` instead of
# `(.*\S)`. The latter lets `\s+` and `.*\S` both backtrack over an all-space
# suffix (e.g. `## ` + many spaces), which is O(n^2) — a ReDoS on a single long
# line. Anchoring the start to `\S` removes that interaction (linear).
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(\S(?:.*\S)?)\s*$")
_TRAILING_HASHES_RE = re.compile(r"\s+#+\s*$")
_SETEXT_H1_RE = re.compile(r"^ {0,3}=+\s*$")
_SETEXT_H2_RE = re.compile(r"^ {0,3}-+\s*$")
_LIST_OR_QUOTE_RE = re.compile(r"^\s*([-*+>]\s|\d+[.)]\s)")
# Link/image text and alt are bounded by `]`, which removes backtracking risk
# and rejects `[![badge](img)](url)` from matching as a plain link.
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
_MD_LINK_RE = re.compile(
    r"(?<!!)\[(?!!)([^\]]*)\]\(\s*([^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
_HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_ATTR_SRC_RE = re.compile(r"\bsrc\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_ATTR_ALT_RE = re.compile(r"\balt\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")

# --- advisory-check patterns (dual-audience / visual-first) ----------------- #
# A DOI (the canonical research-repo identifier) and a BibTeX entry — used to
# detect a buried citation floor and to pair a DOI with a how-to-cite block.
_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>)\]]+")
_BIBTEX_RE = re.compile(r"@\w+\s*\{", re.IGNORECASE)
# A how-to-cite affordance: the NOUN "citation"/"bibtex" anywhere (low verb risk),
# or a heading that contains "cite" (so the verb "cite" in prose does NOT count).
_CITATION_AFFORDANCE_RE = re.compile(r"\b(citation|bibtex)\b", re.IGNORECASE)
_CITE_HEADING_RE = re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bcite\b")
_DETAILS_OPEN_RE = re.compile(r"<details\b", re.IGNORECASE)
_DETAILS_CLOSE_RE = re.compile(r"</details\s*>", re.IGNORECASE)
# <summary> content is the VISIBLE collapsed header, not hidden — exclude it from
# the floor-leak check so a `<details><summary>Cite as (DOI)</summary>` does not
# false-positive.
_SUMMARY_OPEN_RE = re.compile(r"<summary\b", re.IGNORECASE)
_SUMMARY_CLOSE_RE = re.compile(r"</summary\s*>", re.IGNORECASE)
# Known badge hosts/paths — count-only; "is this badge vanity?" is a semantic
# call left to the LLM review, not decided here.
_BADGE_SRC_RE = re.compile(
    r"shields\.io|/badge|badge\.svg|badgen\.net|deepwiki|gitmcp|zenodo\.org/badge"
    r"|codecov|coveralls|circleci|travis-ci|app\.netlify\.com/.*deploy-status",
    re.IGNORECASE,
)
# Diagram-ish filename tokens — only RASTER diagrams are hinted (SVG is vector,
# GitHub-rendered, and far less opaque to text crawlers, so it is left alone).
_DIAGRAM_KEYWORDS = frozenset(
    {
        "architecture", "flow", "flowchart", "dataflow", "diagram", "sequence",
        "pipeline", "graph", "chart", "erd", "uml", "topology", "schema",
        "statemachine",
    }
)
_RASTER_EXT_RE = re.compile(r"\.(png|jpe?g|webp|gif)$", re.IGNORECASE)
_STEM_SPLIT_RE = re.compile(r"[^a-z0-9]+")
# Line shapes that are structurally NOT a prose sentence (used by identity_lead).
_NON_PROSE_PREFIX_RE = re.compile(
    r"^(#{1,6}\s|[-*+>]\s|\d+[.)]\s|\||<|\[[^\]]+\]:\s"
    r"|={2,}\s*$|-{3,}\s*$|\*{3,}\s*$|_{3,}\s*$)"
)
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)  # any Unicode letter (incl. CJK)

_BADGE_BUDGET_DEFAULT = 6  # warn above this many badges (room for CI+ver+lic+DOI+2)

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB — guard against accidental huge inputs
# Per-line cap: the byte guard above bounds the whole file, not any single line,
# so a one-line 10 MB file would still feed a 10 MB string to every per-line
# regex. No real README line approaches this; truncate as a DoS backstop.
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


@dataclass(frozen=True)
class Issue:
    check: str
    message: str
    line: int | None
    # "error" issues fail the code-owned gate (exit 1); "warning" issues are
    # advisory — surfaced for the human / LLM review but never blocking. The
    # default is "error" so the four hard-structural checks (single_h1,
    # heading_levels, alt_text, local_link) keep their original gate behavior.
    severity: Literal["error", "warning"] = "error"


@dataclass(frozen=True)
class LintReport:
    path: str
    issues: tuple[Issue, ...]


def _content_lines(markdown: str) -> list[tuple[int, str]]:
    """Return (1-based line number, text) for lines outside fenced code blocks.

    Fence lines themselves are excluded. A fence opens on ``` or ~~~ (an info
    string is allowed). It closes only on a line using the same marker
    character, at least as long, with nothing but whitespace after the run
    (CommonMark §4.5). Lines inside the fence are dropped as code content.
    """
    out: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_len = 0
    for idx, line in enumerate(markdown.splitlines(), start=1):
        if len(line) > _MAX_LINE:  # DoS backstop for pathological single lines
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
    if raw is None:
        return ""
    return raw[1:-1]  # strip surrounding quotes


def parse_images(markdown: str) -> list[Image]:
    images: list[Image] = []
    for line_no, line in _content_lines(markdown):
        for m in _MD_IMAGE_RE.finditer(line):
            images.append(Image(alt=m.group(1), src=m.group(2), line=line_no))
        for tag in _HTML_IMG_RE.finditer(line):
            src_m = _ATTR_SRC_RE.search(tag.group(0))
            alt_m = _ATTR_ALT_RE.search(tag.group(0))
            src = _attr_value(src_m.group(1) if src_m else None)
            alt = _attr_value(alt_m.group(1) if alt_m else None)
            images.append(Image(alt=alt, src=src, line=line_no))
    return images


def parse_links(markdown: str) -> list[Link]:
    links: list[Link] = []
    for line_no, line in _content_lines(markdown):
        for m in _MD_LINK_RE.finditer(line):
            links.append(Link(text=m.group(1), href=m.group(2), line=line_no))
    return links


def _is_external(href: str) -> bool:
    h = href.strip()
    return bool(_SCHEME_RE.match(h)) or h.startswith("//")


def check_single_h1(headings: list[Heading]) -> list[Issue]:
    h1s = [h for h in headings if h.level == 1]
    if not h1s:
        return [
            Issue(
                "single_h1",
                "no H1 (`# Title`) found; a README needs exactly one top-level heading",
                None,
            )
        ]
    return [
        Issue(
            "single_h1",
            f"extra H1 heading '{h.text}'; only the first heading should be H1",
            h.line,
        )
        for h in h1s[1:]
    ]


def check_heading_levels(headings: list[Heading]) -> list[Issue]:
    issues: list[Issue] = []
    prev: int | None = None
    for h in headings:
        if prev is not None and h.level > prev + 1:
            issues.append(
                Issue(
                    "heading_levels",
                    f"heading level jumps from H{prev} to H{h.level} ('{h.text}'); "
                    "do not skip levels",
                    h.line,
                )
            )
        prev = h.level
    return issues


def check_alt_text(images: list[Image]) -> list[Issue]:
    return [
        Issue(
            "alt_text",
            f"image '{img.src}' has no alt text; text-only LLM ingestion (web "
            "fetch / GitMCP / connectors) passes ONLY alt, so a missing alt makes "
            "the image invisible to an LLM — and it hurts accessibility too",
            img.line,
        )
        for img in images
        if not img.alt.strip()
    ]


def check_local_links(links: list[Link], images: list[Image], base_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    refs: list[tuple[str, int]] = [(link.href, link.line) for link in links]
    refs += [(img.src, img.line) for img in images]
    for href, line in refs:
        if _is_external(href):
            continue
        target = href.split("#", 1)[0].split("?", 1)[0].strip()
        if not target:
            continue  # pure in-page anchor
        # Markdown encodes non-ASCII link targets (e.g. Japanese filenames) as
        # percent-escapes; decode before resolving on disk, else the raw
        # %XX form blows past the filesystem name-length limit.
        target = unquote(target)
        # Check absoluteness AFTER decode: otherwise `%2Fetc%2Fpasswd` slips past
        # the raw startswith("/") guard, decodes to "/etc/passwd", and
        # `base_dir / "/etc/passwd"` resolves to "/etc/passwd" — a file-existence
        # oracle over the whole filesystem. Skipping absolute targets closes it.
        if target.startswith("/"):
            continue  # filesystem- or site-absolute: do not probe disk
        if not (base_dir / target).exists():
            issues.append(
                Issue(
                    "local_link",
                    f"broken local reference: '{href}' (resolved relative to {base_dir})",
                    line,
                )
            )
    return issues


def _basename(src: str) -> str:
    s = src.split("#", 1)[0].split("?", 1)[0]
    return s.rsplit("/", 1)[-1]


def check_raster_diagram_hint(images: list[Image]) -> list[Issue]:
    """Advisory: a raster image whose filename reads like a diagram is opaque to
    text-only LLM crawlers (they never receive image pixels) and is not diffable.
    Suggest a ```mermaid block instead. Screenshots / photos / logos are exempt.
    """
    issues: list[Issue] = []
    for img in images:
        name = _basename(img.src)
        if not _RASTER_EXT_RE.search(name):
            continue
        stem = _RASTER_EXT_RE.sub("", name).lower()
        tokens = {t for t in _STEM_SPLIT_RE.split(stem) if t}
        if tokens & _DIAGRAM_KEYWORDS:
            issues.append(
                Issue(
                    "raster_diagram_hint",
                    f"raster image '{img.src}' looks like a diagram; prefer a "
                    "```mermaid block — it renders as a theme-aware picture for "
                    "humans, stays diffable text, and is readable by text-only LLM "
                    "crawlers that never see image pixels",
                    img.line,
                    "warning",
                )
            )
    return issues


def check_badge_budget(images: list[Image], threshold: int = _BADGE_BUDGET_DEFAULT) -> list[Issue]:
    """Advisory: count badges only. Whether a badge is 'vanity' is a semantic
    call left to the LLM review; this just flags a badge wall."""
    badges = [img for img in images if _BADGE_SRC_RE.search(img.src)]
    if len(badges) > threshold:
        return [
            Issue(
                "badge_budget",
                f"{len(badges)} badges detected (> {threshold}); keep a few "
                "high-signal badges (CI / version / license / DOI) — a badge wall "
                "adds visual noise above the fold without adding signal",
                badges[0].line,
                "warning",
            )
        ]
    return []


def check_details_floor_leak(markdown: str) -> list[Issue]:
    """Advisory: a DOI / BibTeX / CITATION token inside a <details> block hides a
    likely floor element from primacy and from Ctrl+F. The token is structural;
    whether the hidden content is truly 'floor' is the LLM review's call."""
    issues: list[Issue] = []
    depth = 0
    summary_depth = 0
    for line_no, line in _content_lines(markdown):
        depth += len(_DETAILS_OPEN_RE.findall(line))
        summary_depth += len(_SUMMARY_OPEN_RE.findall(line))
        # Inside <details> body, but NOT inside the visible <summary> header.
        if depth > 0 and summary_depth == 0:
            doi = _DOI_RE.search(line)
            if doi:
                shown = doi.group(0)
                if len(shown) > 64:  # bound message length (suffix is unbounded)
                    shown = shown[:61] + "..."
                token = f"a DOI ({shown})"
            elif _BIBTEX_RE.search(line):
                token = "a BibTeX entry"
            elif "CITATION" in line.upper():
                token = "a CITATION reference"
            else:
                token = ""
            if token:
                issues.append(
                    Issue(
                        "details_floor_leak",
                        f"{token} is inside a <details> block; citation / identity "
                        "floor should stay visible (primacy + Ctrl+F), not collapsed",
                        line_no,
                        "warning",
                    )
                )
        summary_depth = max(0, summary_depth - len(_SUMMARY_CLOSE_RE.findall(line)))
        depth = max(0, depth - len(_DETAILS_CLOSE_RE.findall(line)))
    return issues


def _is_prose_line(stripped: str) -> bool:
    if not stripped or _NON_PROSE_PREFIX_RE.match(stripped):
        return False
    # A line that is ENTIRELY links/images (a nav-link row, a badge row) is not a
    # prose lead, even though link text contains letters.
    bare = _MD_LINK_RE.sub("", _MD_IMAGE_RE.sub("", stripped)).strip()
    if not bare:
        return False
    text = _MD_IMAGE_RE.sub(" ", stripped)
    text = _MD_LINK_RE.sub(lambda m: f" {m.group(1)} ", text)  # keep link TEXT
    return bool(_LETTER_RE.search(text))


def check_identity_lead(markdown: str, headings: list[Heading]) -> list[Issue]:
    """Advisory: between the H1 and the first section there should be at least one
    plain prose sentence (the identity / value line). Order is NOT enforced — only
    the presence of a lead — so this stays valid for software, research, and DOI
    repos alike. The missing-H1 case is owned by single_h1."""
    h1 = next((h for h in headings if h.level == 1), None)
    if h1 is None:
        return []
    after = [h for h in headings if h.line > h1.line]
    end_line = after[0].line if after else None
    depth = 0
    for line_no, line in _content_lines(markdown):
        if line_no <= h1.line:
            depth += len(_DETAILS_OPEN_RE.findall(line))
            depth = max(0, depth - len(_DETAILS_CLOSE_RE.findall(line)))
            continue
        if end_line is not None and line_no >= end_line:
            break
        depth += len(_DETAILS_OPEN_RE.findall(line))
        inside = depth > 0
        depth = max(0, depth - len(_DETAILS_CLOSE_RE.findall(line)))
        if inside:
            continue  # collapsed lead does not count (it loses primacy)
        if _is_prose_line(line.strip()):
            return []
    return [
        Issue(
            "identity_lead",
            "no identity / lead sentence between the H1 and the first section; "
            "lead with one plain sentence saying what this is and who it is for "
            "(a grounding-path LLM may read only the README)",
            h1.line,
            "warning",
        )
    ]


def check_doi_citation_pairing(markdown: str) -> list[Issue]:
    """Advisory, conditional: only fires when a DOI is present. A DOI without a
    how-to-cite affordance (Citation section / BibTeX / CITATION.cff link) leaves
    grounding-path LLMs without a copy-paste, verifiable citation. Does NOT force
    a DOI on non-research repos."""
    # Trigger only on a DOI in NON-fenced content (a DOI inside a ``` example
    # block is not the document's DOI). Collect the first such line in one pass.
    doi_line: int | None = None
    for ln, line in _content_lines(markdown):
        if _DOI_RE.search(line):
            doi_line = ln
            break
    if doi_line is None:
        return []
    # An affordance may be a fenced ```bibtex block, so satisfy it from the RAW
    # markdown: BibTeX anywhere, the noun "citation"/"bibtex", a heading with
    # "cite" (not the verb in prose), or a CITATION.cff link.
    if (
        _BIBTEX_RE.search(markdown)
        or _CITATION_AFFORDANCE_RE.search(markdown)
        or _CITE_HEADING_RE.search(markdown)
        or "citation.cff" in markdown.lower()
    ):
        return []
    line_no: int | None = doi_line
    return [
        Issue(
            "doi_citation_pairing",
            "a DOI is present but no how-to-cite affordance (a Citation section, a "
            "BibTeX block, or a CITATION.cff link) was found; grounding-path LLMs "
            "cite verifiable entities — give them a copy-paste citation",
            line_no,
            "warning",
        )
    ]


def run_lint(path: str, markdown: str, base_dir: Path) -> LintReport:
    headings = parse_headings(markdown)
    images = parse_images(markdown)
    links = parse_links(markdown)
    issues: list[Issue] = []
    # Hard-structural checks (errors — fail the gate).
    issues += check_single_h1(headings)
    issues += check_heading_levels(headings)
    issues += check_alt_text(images)
    issues += check_local_links(links, images, base_dir)
    # Advisory checks (warnings — surfaced, never blocking).
    issues += check_raster_diagram_hint(images)
    issues += check_badge_budget(images)
    issues += check_details_floor_leak(markdown)
    issues += check_identity_lead(markdown, headings)
    issues += check_doi_citation_pairing(markdown)
    issues.sort(key=lambda i: (i.line is None, i.line or 0, i.check))
    return LintReport(path=path, issues=tuple(issues))


_HOLISTIC_NOTE = (
    "Structural checks only. Semantic quality (lead hook, value proposition, "
    "narrative) is judged holistically by an LLM review, never as a number."
)


def render_report(report: LintReport) -> str:
    lines = [f"readme-writer lint: {report.path}", ""]
    if report.issues:
        errors = sum(1 for i in report.issues if i.severity == "error")
        warnings = sum(1 for i in report.issues if i.severity == "warning")
        lines.append(f"{errors} error(s), {warnings} warning(s):")
        lines.append("")
        for issue in report.issues:
            loc = f"L{issue.line}" if issue.line is not None else "-"
            lines.append(f"  [{issue.severity}] [{issue.check}] {loc}: {issue.message}")
    else:
        lines.append("No structural issues found.")
    lines.append("")
    lines.append(_HOLISTIC_NOTE)
    return "\n".join(lines)


def render_json(report: LintReport) -> str:
    data = {
        "path": report.path,
        "issue_count": len(report.issues),
        "error_count": sum(1 for i in report.issues if i.severity == "error"),
        "warning_count": sum(1 for i in report.issues if i.severity == "warning"),
        "issues": [asdict(issue) for issue in report.issues],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def lint_file(path: Path) -> LintReport:
    raw = path.read_text(encoding="utf-8")
    return run_lint(str(path), raw, path.parent)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="README Markdown file to lint")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    if not args.path.exists():
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2
    if args.path.stat().st_size > _MAX_BYTES:
        print(f"error: file too large to lint (> {_MAX_BYTES} bytes): {args.path}", file=sys.stderr)
        return 2
    report = lint_file(args.path)
    print(render_json(report) if args.json else render_report(report))
    # Only error-severity issues gate (advisory warnings never fail the build).
    return 1 if any(i.severity == "error" for i in report.issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())

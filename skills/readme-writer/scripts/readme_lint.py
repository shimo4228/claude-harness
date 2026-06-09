"""Structural-only linter for human-facing README files.

This module checks **structural** properties only — properties decidable from
the literal shape of the Markdown (heading hierarchy, image alt text, local
link resolution). Per AKC ADR-0008 "Code-LLM Layering", code owns structural
determinism and 100% accuracy; semantic quality (does the lead hook a human?
is the value proposition clear? does the narrative flow?) is a holistic LLM
judgment and is **never scored here**.

The CLI exit code is the code-owned gate: 0 = clean, 1 = structural issues,
2 = file not found / too large. A non-zero exit is the deterministic signal a
downstream step (CI, a skill workflow) can enforce.

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
from urllib.parse import unquote

_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*\S)\s*$")
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

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB — guard against accidental huge inputs


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
            f"image '{img.src}' is missing alt text (hurts accessibility and image SEO)",
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
        if target.startswith("/"):
            continue  # filesystem- or site-absolute: do not probe disk
        # Markdown encodes non-ASCII link targets (e.g. Japanese filenames) as
        # percent-escapes; decode before resolving on disk, else the raw
        # %XX form blows past the filesystem name-length limit.
        target = unquote(target)
        if not (base_dir / target).exists():
            issues.append(
                Issue(
                    "local_link",
                    f"broken local reference: '{href}' (resolved relative to {base_dir})",
                    line,
                )
            )
    return issues


def run_lint(path: str, markdown: str, base_dir: Path) -> LintReport:
    headings = parse_headings(markdown)
    images = parse_images(markdown)
    links = parse_links(markdown)
    issues: list[Issue] = []
    issues += check_single_h1(headings)
    issues += check_heading_levels(headings)
    issues += check_alt_text(images)
    issues += check_local_links(links, images, base_dir)
    issues.sort(key=lambda i: (i.line is None, i.line or 0, i.check))
    return LintReport(path=path, issues=tuple(issues))


_HOLISTIC_NOTE = (
    "Structural checks only. Semantic quality (lead hook, value proposition, "
    "narrative) is judged holistically by an LLM review, never as a number."
)


def render_report(report: LintReport) -> str:
    lines = [f"readme-writer lint: {report.path}", ""]
    if report.issues:
        lines.append(f"{len(report.issues)} structural issue(s):")
        lines.append("")
        for issue in report.issues:
            loc = f"L{issue.line}" if issue.line is not None else "-"
            lines.append(f"  [{issue.check}] {loc}: {issue.message}")
    else:
        lines.append("No structural issues found.")
    lines.append("")
    lines.append(_HOLISTIC_NOTE)
    return "\n".join(lines)


def render_json(report: LintReport) -> str:
    data = {
        "path": report.path,
        "issue_count": len(report.issues),
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
    return 1 if report.issues else 0


if __name__ == "__main__":
    raise SystemExit(main())

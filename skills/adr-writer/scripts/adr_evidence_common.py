"""Shared corpus and text access for the `adr_review_evidence` checks.

Split out of `adr_review_evidence.py` under the file-LOC budget (ADR-0056), the
same way `context_evidence.py` was. Everything here is read-only access the
checks share: git queries, the fence-aware section/paragraph carve-up of an ADR,
and ADR file lookup. Dependencies run one way — nothing here imports a check.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from scripts.adr_lint import _content_line_numbers, _headings_and_bodies, _read_lines

__all__ = [
    "_ADR_REF_RE",
    "_HEADING_RE",
    "_INLINE_CODE_RE",
    "_LIST_ITEM_RE",
    "_MD_LINK_RE",
    "_METAVARIABLE_CHARS",
    "_PLACEHOLDER_RE",
    "_TABLE_ROW_RE",
    "_adr_number",
    "_content_line_numbers",
    "_find_adr_files",
    "_git",
    "_headings_and_bodies",
    "_is_ignored",
    "_paragraphs",
    "_read_lines",
    "_sections",
    "_section_lines",
    "_snippet",
    "_status_line",
    "_strip_inline_code",
    "_tracked_files",
]

_ADR_REF_RE = re.compile(r"\bADR[- ](\d{4})\b")
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_HEADING_RE = re.compile(r"^## (.+?)\s*$")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
_METAVARIABLE_CHARS = set("<>{}*$")
_PLACEHOLDER_RE = re.compile(r"NNNN|XXX|slug|<name>|\.\.\.|…", re.IGNORECASE)


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _tracked_files(root: Path) -> set[str]:
    return {line for line in _git(root, "ls-files").splitlines() if line}


def _is_ignored(root: Path, rel: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", "--", rel],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _strip_inline_code(text: str) -> str:
    return _INLINE_CODE_RE.sub(" ", text)


def _sections(lines: list[str], content: set[int]) -> dict[str, tuple[int, int]]:
    """heading -> (first body line number, last body line number), fence-aware."""
    spans: dict[str, tuple[int, int]] = {}
    current: str | None = None
    start = 0
    for number, line in enumerate(lines, start=1):
        if number not in content:
            continue
        m = _HEADING_RE.match(line)
        if m:
            if current is not None:
                spans[current] = (start, number - 1)
            current, start = m.group(1), number + 1
    if current is not None:
        spans[current] = (start, len(lines))
    return spans


def _section_lines(
    lines: list[str], spans: dict[str, tuple[int, int]], name: str
) -> list[tuple[int, str]]:
    key = next((h for h in spans if h.lower() == name.lower()), None)
    if key is None:
        return []
    a, b = spans[key]
    return [(n, lines[n - 1]) for n in range(a, b + 1)]


def _paragraphs(lines: list[str], content: set[int]) -> list[list[tuple[int, str]]]:
    """Consecutive non-blank prose lines outside fences and tables."""
    out: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for number, line in enumerate(lines, start=1):
        usable = number in content and line.strip() and not _TABLE_ROW_RE.match(line)
        if usable and not _HEADING_RE.match(line):
            current.append((number, line))
            continue
        if current:
            out.append(current)
            current = []
    if current:
        out.append(current)
    return out


def _adr_number(path: Path) -> str | None:
    m = re.match(r"^(\d{4})-", path.name)
    return m.group(1) if m else None


def _find_adr_files(adr_dir: Path, number: str) -> list[Path]:
    return sorted(adr_dir.glob(f"{number}-*.md"))


def _status_line(path: Path) -> str | None:
    lines = _read_lines(path)
    if lines is None:
        return None
    _, bodies = _headings_and_bodies(lines)
    return bodies.get("Status") or bodies.get("status")


def _snippet(line: str, limit: int = 160) -> str:
    text = line.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"

"""Collect the review-when conditions this harness has written down.

Two places hold them:

- ``rfcs/NNNN-*.md`` — a ``review-when:`` line in the frontmatter, next to ``state:``.
  The title lives in the ``rfcs/README.md`` table, not in the file.
- ``docs/adr/NNNN-*.md`` — a ``## Review-when`` section (required from ADR-0044 on, and
  back-filled on some older ones). The title is the ``# ADR-NNNN: ...`` heading, the status
  the first line under ``## Status``.

A superseded ADR is skipped: its conditions were handed to whatever replaced it. Every RFC
state is kept, withdrawn included — a withdrawn RFC names the event that would revive it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

#: A condition longer than this is cut. ADR Review-when sections run to a few bullets plus
#: dated notes; the cap keeps one pathological section from eating the request budget.
MAX_CONDITION_CHARS = 2000

_RFC_FILE_RE = re.compile(r"^(\d{4})-.+\.md$")
_ADR_FILE_RE = re.compile(r"^(\d{4})-.+\.md$")
_RFC_INDEX_ROW_RE = re.compile(r"^\|\s*\[(\d{4})\]\([^)]*\)\s*\|\s*(.+?)\s*\|\s*$")
_ADR_TITLE_RE = re.compile(r"^#\s+ADR-\d{4}:\s*(.+?)\s*$")
_EMPTY_VALUES = frozenset({"", "無し", "なし", "none", "None", "-", "—"})
_RETIRED_ADR_STATUS = ("superseded", "deprecated", "rejected", "obsoleted")
#: "accepted — **superseded by [ADR-0062]**" retires the ADR; "supersedes ADR-0060" and
#: "partially-supersedes" do not (the ADR that says them is the live one).
_SUPERSEDED_BY_RE = re.compile(r"(?<!partially )(?<!partially-)superseded by")


@dataclass(frozen=True)
class Condition:
    id: str
    title: str
    status: str
    text: str
    path: str

    @property
    def sha(self) -> str:
        """Hash of the condition text, so a log reader can tell a reworded condition apart."""
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep and key and not key.startswith((" ", "\t", "-")):
            fields[key.strip()] = _unquote(value.strip())
    return fields


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except ValueError:
            return value[1:-1]
        return decoded if isinstance(decoded, str) else value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def _section(text: str, heading: str) -> str:
    """Body of ``## <heading>`` up to the next ``## `` heading, stripped."""
    body: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip().lower() == heading.lower()
            continue
        if inside:
            body.append(line)
    return "\n".join(body).strip()


def _retired(status: str) -> bool:
    plain = status.lower().replace("*", "")
    return plain.startswith(_RETIRED_ADR_STATUS) or bool(_SUPERSEDED_BY_RE.search(plain))


def _cap(text: str) -> str:
    return text if len(text) <= MAX_CONDITION_CHARS else text[:MAX_CONDITION_CHARS] + " …"


def _rfc_titles(root: Path) -> dict[str, str]:
    index = root / "rfcs" / "README.md"
    try:
        text = index.read_text(encoding="utf-8")
    except OSError:
        return {}
    titles: dict[str, str] = {}
    for line in text.splitlines():
        match = _RFC_INDEX_ROW_RE.match(line)
        if match:
            titles[match.group(1)] = match.group(2)
    return titles


def load_rfc_conditions(root: Path) -> list[Condition]:
    titles = _rfc_titles(root)
    conditions: list[Condition] = []
    for path in sorted((root / "rfcs").glob("*.md")):
        match = _RFC_FILE_RE.match(path.name)
        if not match:
            continue
        fields = _frontmatter(path.read_text(encoding="utf-8"))
        text = fields.get("review-when", "")
        if text in _EMPTY_VALUES:
            continue
        number = match.group(1)
        conditions.append(
            Condition(
                id=f"RFC-{number}",
                title=titles.get(number, path.stem),
                status=fields.get("state", ""),
                text=_cap(text),
                path=str(path.relative_to(root)),
            )
        )
    return conditions


def load_adr_conditions(root: Path) -> list[Condition]:
    conditions: list[Condition] = []
    for path in sorted((root / "docs" / "adr").glob("*.md")):
        match = _ADR_FILE_RE.match(path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8")
        condition = _section(text, "Review-when")
        if condition in _EMPTY_VALUES:
            continue
        status = next(
            (ln.strip() for ln in _section(text, "Status").splitlines() if ln.strip()), ""
        )
        if _retired(status):
            continue
        title = next(
            (m.group(1) for m in map(_ADR_TITLE_RE.match, text.splitlines()) if m), path.stem
        )
        conditions.append(
            Condition(
                id=f"ADR-{match.group(1)}",
                title=title,
                status=status,
                text=_cap(condition),
                path=str(path.relative_to(root)),
            )
        )
    return conditions


def load_conditions(root: Path) -> list[Condition]:
    return load_rfc_conditions(root) + load_adr_conditions(root)

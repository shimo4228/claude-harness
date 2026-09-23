"""Per-ADR review evidence — the mechanical half of what adr-reviewer kept re-finding.

adr_lint.py owns corpus-wide structure (sections, Status/Date format, index
drift, naming). This script takes ONE ADR under review and emits the evidence
the reviewer used to gather by hand on every pass. Source: 24 adr-reviewer
reports across 4 repos, 2026-08-26..09-15 (~200 findings, mined 2026-09-16,
recorded in harness ADR-0071). Classes that recurred in >= 3 reports and were
adopted by the author became checks here; judgment stays with the reviewer.

Evidence, not a verdict: JSON to stdout, exit 0. Exit 2 when the ADR or repo
cannot be read. There is no --gate — every list below needs a reader to decide
whether the deviation matters.

  refs          ADR-NNNN / RFC-NNNN mentions resolved against the corpus;
                local Markdown links resolved            (12/24 reports)
  relations     forward supersede/注記 targets; whether each target points back
                (Status or dated 注記); inbound mentions; index rows;
                注記 blockquote format                    (11/24 reports)
  paths         path-like tokens classified: tracked / untracked / ignored /
                missing / outside-repo; cited file:line resolved to the
                line text so the reviewer compares without opening the file
                                                          (7/24 + 8/24 reports)
  diff_scope    --diff: files changed vs paths the ADR names, both directions
                                                          (8/24 reports)
  numbers       prose numbers with no anchor (date / command / sha / path /
                URL / 実測) in their paragraph; percentages without a
                denominator; relative-time / session referents (18/24 reports)
  review_when   items carrying a count or period condition — the reviewer
                still asks subject / judge / window / venue (17/24 reports)
  alternatives  whether a status-quo option is written down (10/24 reports)
  consequences  subheadings; reversal-cost tokens vs removal signals in the
                Decision                                  (6/24 reports)
  second_record measurements from this ADR that also appear verbatim in
                tracked files outside the ADR dir         (7/24 reports)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Run as a file (`python3 scripts/adr_review_evidence.py`, the form SKILL.md Step 4.5
# and agents/adr-reviewer.md name) or imported as `scripts.adr_review_evidence`. Putting
# the sub-project root on the path makes **one** spelling of the sibling imports correct
# for both entries — the form `scripts.<name>`, which is also what ty resolves as
# first-party code.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.adr_evidence_common import (  # noqa: E402
    _ADR_REF_RE,
    _MD_LINK_RE,
    _METAVARIABLE_CHARS,
    _PLACEHOLDER_RE,
    _adr_number,
    _content_line_numbers,
    _find_adr_files,
    _headings_and_bodies,
    _read_lines,
    _sections,
    _snippet,
    _status_line,
)
from scripts.adr_evidence_paths import check_diff_scope, check_paths  # noqa: E402
from scripts.adr_evidence_prose import (  # noqa: E402
    check_alternatives,
    check_consequences,
    check_numbers,
    check_review_when,
    check_second_record,
)

# Re-exported so the split stays a move of code, not of contract: `check_*` keeps
# resolving on this module for anyone who addresses the entrypoint (same reason
# `context_evidence.py` re-exports after its own 2026-08-28 split).
__all__ = [
    "check_alternatives",
    "check_consequences",
    "check_diff_scope",
    "check_links",
    "check_numbers",
    "check_paths",
    "check_refs",
    "check_relations",
    "check_review_when",
    "check_second_record",
    "collect",
    "main",
    "resolve_adr",
]

_RFC_REF_RE = re.compile(r"\bRFC[- ](\d{4})\b")

# Relationship vocabulary seen in Status lines and bodies across the harness,
# contemplative-agent and agent-knowledge-cycle corpora (2026-09-16 grep).
_FORWARD_WORD_RE = re.compile(
    r"supersed|partially|narrow|override|overrid|withdraw|注記|狭め|覆す|上書き|退役|弱め|"
    r"置き換え|supersede|amend|Note \(",
    re.IGNORECASE,
)
_STATUS_FULL_SUPERSEDE_RE = re.compile(
    r"(?<!partially[- ])(?<!partially-)supersedes?\b", re.IGNORECASE
)
_STATUS_PARTIAL_RE = re.compile(r"partial|in part|一部", re.IGNORECASE)
_ANNOTATION_RE = re.compile(r"^\s*>\s*\*\*\s*(注記|Note)\b(.*)$")
_ANNOTATION_WELL_FORMED_RE = re.compile(
    r"^\s*>\s*\*\*(注記|Note)\s*[（(]\d{4}-\d{2}-\d{2}[,、]\s*(\[)?ADR-\d{4}"
)


def check_refs(
    lines: list[str], content: set[int], adr_dir: Path, rfc_dir: Path, self_number: str | None
) -> dict:
    adr_refs: dict[str, dict] = {}
    rfc_refs: dict[str, dict] = {}
    for number, line in enumerate(lines, start=1):
        if number not in content:
            continue
        for m in _ADR_REF_RE.finditer(line):
            num = m.group(1)
            if num == self_number:
                continue
            entry = adr_refs.setdefault(
                num,
                {
                    "id": f"ADR-{num}",
                    "lines": [],
                    "resolves": bool(_find_adr_files(adr_dir, num)),
                    "context": _snippet(line[max(0, m.start() - 40) : m.end() + 20], 90),
                },
            )
            entry["lines"].append(number)
        for m in _RFC_REF_RE.finditer(line):
            num = m.group(1)
            entry = rfc_refs.setdefault(
                num,
                {
                    "id": f"RFC-{num}",
                    "lines": [],
                    "resolves": rfc_dir.is_dir() and bool(sorted(rfc_dir.glob(f"{num}-*.md"))),
                },
            )
            entry["lines"].append(number)
    return {
        "adr": sorted(adr_refs.values(), key=lambda e: e["id"]),
        "rfc": sorted(rfc_refs.values(), key=lambda e: e["id"]),
        "unresolved": sorted(
            e["id"] for e in [*adr_refs.values(), *rfc_refs.values()] if not e["resolves"]
        ),
    }


def check_links(lines: list[str], content: set[int], adr_path: Path, root: Path) -> list[dict]:
    broken: list[dict] = []
    for number, line in enumerate(lines, start=1):
        if number not in content:
            continue
        for m in _MD_LINK_RE.finditer(line):
            target = m.group(1).split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if any(ch in _METAVARIABLE_CHARS for ch in target) or _PLACEHOLDER_RE.search(target):
                continue
            base = root if target.startswith("/") else adr_path.parent
            if not (base / target.lstrip("/")).exists():
                broken.append({"line": number, "target": target})
    return broken


# --------------------------------------------------------------------------- relations


def _annotations(lines: list[str]) -> list[dict]:
    out: list[dict] = []
    for number, line in enumerate(lines, start=1):
        m = _ANNOTATION_RE.match(line)
        if not m:
            continue
        out.append(
            {
                "line": number,
                "text": _snippet(line, 120),
                "well_formed": bool(_ANNOTATION_WELL_FORMED_RE.match(line)),
                "adr_refs": sorted({f"ADR-{n}" for n in _ADR_REF_RE.findall(line)}),
            }
        )
    return out


def _index_rows(adr_dir: Path, numbers: list[str]) -> dict[str, str | None]:
    """`numbers` arrives sorted: this dict's key order is printed JSON, so it must not
    depend on set iteration order (which moves with PYTHONHASHSEED between runs)."""
    readme = _read_lines(adr_dir / "README.md") or []
    rows: dict[str, str | None] = {n: None for n in numbers}
    for line in readme:
        m = re.match(r"^\|\s*\[?(\d{4})\]?", line)
        if m and m.group(1) in rows:
            rows[m.group(1)] = _snippet(line, 200)
    return rows


def _target_report(root: Path, adr_dir: Path, self_number: str, target: str) -> dict:
    files = _find_adr_files(adr_dir, target)
    report: dict = {"id": f"ADR-{target}", "exists": bool(files), "files": []}
    for path in files:
        tlines = _read_lines(path) or []
        status = _status_line(path) or ""
        notes = [a for a in _annotations(tlines) if f"ADR-{self_number}" in a["adr_refs"]]
        mentions = [
            n
            for n, line in enumerate(tlines, start=1)
            if re.search(rf"\bADR[- ]{self_number}\b|\b{self_number}\b", line)
        ]
        report["files"].append(
            {
                "file": str(path.relative_to(root)),
                "status": status,
                "status_points_back": bool(re.search(rf"\b{self_number}\b", status)),
                "status_still_accepted": bool(
                    re.match(r"\W*accepted\b", status) and not re.search(r"-by\b|supersed", status)
                ),
                "annotation_lines": [a["line"] for a in notes],
                "mention_lines": mentions[:20],
            }
        )
    return report


def check_relations(
    lines: list[str], content: set[int], adr_path: Path, root: Path, adr_dir: Path
) -> dict:
    self_number = _adr_number(adr_path) or ""
    _, bodies = _headings_and_bodies(lines)
    status = bodies.get("Status") or bodies.get("status") or ""
    # bare 4-digit numbers in a Status line are ADR ids ("superseded-by 0070"); a
    # year ("amended 2026-08-15") is masked by _NUMBER_SKIP_RE's date pattern.
    status_masked = re.sub(r"\d{4}-\d{2}-\d{2}", " ", status)
    status_targets = sorted(
        set(_ADR_REF_RE.findall(status_masked)) | set(re.findall(r"\b(0\d{3})\b", status_masked))
    )
    status_targets = [t for t in status_targets if t != self_number]
    body_candidates: dict[str, list[int]] = {}
    for number, line in enumerate(lines, start=1):
        if number not in content or not _FORWARD_WORD_RE.search(line):
            continue
        for num in _ADR_REF_RE.findall(line):
            if num != self_number:
                body_candidates.setdefault(num, []).append(number)
    targets = sorted(set(status_targets) | set(body_candidates))
    inbound: list[dict] = []
    for other in sorted(adr_dir.glob("[0-9]*.md")):
        if _adr_number(other) == self_number:
            continue
        olines = _read_lines(other) or []
        hits = [
            n
            for n, line in enumerate(olines, start=1)
            if re.search(rf"\bADR[- ]{self_number}\b", line)
        ]
        if hits:
            notes = [
                a["line"] for a in _annotations(olines) if f"ADR-{self_number}" in a["adr_refs"]
            ]
            inbound.append(
                {
                    "file": str(other.relative_to(root)),
                    "lines": hits[:20],
                    "annotation_lines": notes,
                }
            )
    return {
        "self": f"ADR-{self_number}",
        "status": status,
        "status_declares_full_supersede": bool(
            _STATUS_FULL_SUPERSEDE_RE.search(status) and not _STATUS_PARTIAL_RE.search(status)
        ),
        "status_targets": [f"ADR-{t}" for t in status_targets],
        "body_candidates": {f"ADR-{k}": v for k, v in sorted(body_candidates.items())},
        "targets": [_target_report(root, adr_dir, self_number, t) for t in targets],
        "inbound": inbound,
        "own_annotations": _annotations(lines),
        "index_rows": {
            f"ADR-{k}": v for k, v in _index_rows(adr_dir, sorted({self_number, *targets})).items()
        },
    }


def collect(root: Path, adr_path: Path, diff_spec: str | None, rfc_dir_rel: str) -> dict | None:
    lines = _read_lines(adr_path)
    if lines is None:
        return None
    content = _content_line_numbers(lines)
    spans = _sections(lines, content)
    adr_dir = adr_path.parent
    adr_dir_rel = str(adr_dir.relative_to(root)) if adr_dir.is_relative_to(root) else str(adr_dir)
    self_number = _adr_number(adr_path)
    refs = check_refs(lines, content, adr_dir, root / rfc_dir_rel, self_number)
    refs["links_broken"] = check_links(lines, content, adr_path, root)
    paths = check_paths(lines, content, root, adr_path)
    return {
        "root": str(root),
        "adr": str(adr_path.relative_to(root)) if adr_path.is_relative_to(root) else str(adr_path),
        "number": self_number,
        "refs": refs,
        "relations": check_relations(lines, content, adr_path, root, adr_dir),
        "paths": paths,
        "diff_scope": (
            check_diff_scope(lines, content, root, adr_path, diff_spec, paths["items"])
            if diff_spec
            else None
        ),
        "numbers": check_numbers(lines, content, spans),
        "review_when": check_review_when(lines, spans),
        "alternatives": check_alternatives(lines, spans),
        "consequences": check_consequences(lines, spans),
        "second_record": check_second_record(lines, content, spans, root, adr_dir_rel),
    }


def resolve_adr(root: Path, adr_dir_rel: str, adr: str) -> Path | None:
    candidate = Path(adr).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    if (root / adr).is_file():
        return (root / adr).resolve()
    if re.fullmatch(r"\d{1,4}", adr):
        files = _find_adr_files(root / adr_dir_rel, f"{int(adr):04d}")
        files = [f for f in files if not re.search(r"\.[a-z]{2}\.md$", f.name)] or files
        return files[0].resolve() if files else None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", default=".", help="repo root (default: cwd)")
    parser.add_argument("--adr-dir", default="docs/adr", help="ADR dir relative to root")
    parser.add_argument("--rfc-dir", default="rfcs", help="RFC dir relative to root")
    parser.add_argument("--adr", required=True, help="ADR number (0071) or path")
    parser.add_argument(
        "--diff",
        default=None,
        metavar="SPEC",
        help="compare named paths with changed files: 'staged', 'worktree', or a git range",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    adr_path = resolve_adr(root, args.adr_dir, args.adr)
    if adr_path is None:
        print(f"adr_review_evidence: cannot resolve ADR '{args.adr}' under {root}", file=sys.stderr)
        return 2
    evidence = collect(root, adr_path, args.diff, args.rfc_dir)
    if evidence is None:
        print(f"adr_review_evidence: cannot read {adr_path}", file=sys.stderr)
        return 2
    json.dump(evidence, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

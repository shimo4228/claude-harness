"""Deterministic ADR corpus lint — evidence by default, gate on demand.

This script owns the *mechanical* half of ADR review (the code side of the
code/LLM split drawn in ADR-0044: existence = code, content = LLM). It checks
structure, spelling-level conformance, and cross-file drift; it never judges
whether a Context is post-hoc rationalization or an Alternatives list is a
straw man — those stay with the adr-reviewer agent.

Two modes:
  default          evidence mode — emit JSON to stdout, exit 0 regardless of
                   findings (same contract as readme_evidence.py: evidence,
                   not a verdict). Exit 2 only when the corpus can't be read.
  --gate           blocking mode — print violation lines, exit 3 when any
                   violation remains after the exemption boundaries below,
                   exit 0 when clean, exit 2 when the corpus can't be read.

Template adaptation: the expected section set is parsed from the target
repo's docs/adr/README.md (first fenced block under "## Template"). Repos
whose 7th section is "References" instead of "Review-when" (e.g.
contemplative-agent) are checked against their own template, not ours.
Fallback: the harness 7-section template.

Exemption boundaries (gate mode; measured against existing corpora so a new
gate does not turn red on day one):
  --sections-from NNNN          section-presence checks apply only to ADRs
                                numbered >= NNNN (harness: 0044 — exempts
                                0009's two missing sections)
  --require-review-when-from N  "## Review-when" required from ADR N on
  Status                        prefix judgment: only the first token must be
                                in the status vocabulary — trailing prose
                                ("accepted — supersedes ADR-NNNN") is normal
                                in both harness and CA corpora
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SECTIONS = [
    "Status",
    "Date",
    "Context",
    "Decision",
    "Review-when",
    "Alternatives Considered",
    "Consequences",
]

# First token of the Status body line, optionally with a "-by" suffix
# ("superseded-by 0070", "withdrawn-by 0034" are established CA notation).
_STATUS_TOKEN_RE = re.compile(
    r"^(accepted|proposed|draft|deprecated|rejected|obsoleted|withdrawn"
    r"|superseded|partially-superseded)(-by)?$"
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\b")
_ADR_FILE_RE = re.compile(r"^(\d{4})-(.+)\.md$")
_LANG_SUFFIX_RE = re.compile(r"\.[a-z]{2}$")
_HEADING_RE = re.compile(r"^## (.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_INDEX_ROW_RE = re.compile(r"^\|\s*\[?(\d{4})\]?")
_NUMERIC_CLAIM_RE = re.compile(
    r"(?<![\w.])(0|[1-9]\d*)\s*(件|項目|本|個|点|repo(?![A-Za-z]))", re.IGNORECASE
)
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
_LIST_ITEM_RE = re.compile(r"^(\s*)(?:[-+*]|\d+[.)])\s+\S")

# Notation variants of supersede/withdraw references seen across corpora.
# Reported as evidence so the drift is visible; not gated (which notation a
# repo standardizes on is that repo's decision).
_NOTATION_PATTERNS = [
    ("linked (markdown)", re.compile(r"\b(superseded|withdrawn)[ -]by \[", re.IGNORECASE)),
    ("hyphenated + ADR-NNNN", re.compile(r"\b[a-z-]*-by ADR-\d+", re.IGNORECASE)),
    ("hyphenated + bare NNNN", re.compile(r"\b[a-z-]*-by \d{4}\b", re.IGNORECASE)),
    ("spaced + ADR-NNNN", re.compile(r"\b(superseded|withdrawn) by ADR-\d+", re.IGNORECASE)),
    ("spaced + bare NNNN", re.compile(r"\b(superseded|withdrawn) by \d{4}\b", re.IGNORECASE)),
]

_MAX_FILE_BYTES = 1_000_000  # DoS backstop, not a quality rule


def _read_lines(path: Path) -> list[str] | None:
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None


def _headings_and_bodies(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    """Return (## headings in order, heading -> first non-empty body line).

    Fence-aware: `## x` inside a fenced code block is not a heading.
    """
    headings: list[str] = []
    bodies: dict[str, str] = {}
    current: str | None = None
    in_fence = False
    fence_marker = ""
    for line in lines:
        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)[0] * 3
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if m:
            current = m.group(1)
            headings.append(m.group(1))
            continue
        if current is not None and current not in bodies and line.strip():
            bodies[current] = line.strip()
    return headings, bodies


def load_template_sections(adr_dir: Path) -> tuple[list[str], str]:
    """Expected section set from the repo's own docs/adr/README.md template."""
    readme = adr_dir / "README.md"
    lines = _read_lines(readme)
    if lines is None:
        return DEFAULT_SECTIONS, "default"
    in_template = False
    in_fence = False
    sections: list[str] = []
    for line in lines:
        if re.match(r"^##\s+Template\s*$", line):
            in_template = True
            continue
        if not in_template:
            continue
        if _FENCE_RE.match(line):
            if in_fence:
                break  # first fenced block ends the harvest
            in_fence = True
            continue
        if not in_fence and re.match(r"^##?\s+\S", line):
            # next real heading before any fence — template block absent
            break
        if in_fence:
            m = _HEADING_RE.match(line)
            if m:
                sections.append(m.group(1))
    if sections:
        return sections, "readme"
    return DEFAULT_SECTIONS, "default"


def _status_evidence(raw: str | None) -> dict:
    if raw is None:
        return {"raw": None, "token": None, "conforms": None}
    # Leading run of word characters and hyphens — robust against a full-width
    # paren or dash glued directly to the status word ("accepted（…）", harness
    # 0009/0014/0018 pattern) and against bold wrapping ("**withdrawn (…)**",
    # CA 0032 pattern).
    m = re.match(r"[A-Za-z][A-Za-z-]*", raw.lstrip("*_"))
    token = m.group(0).lower().rstrip("-") if m else ""
    if m and m.group(0).lower().endswith("-by"):
        token = m.group(0).lower()
    return {"raw": raw, "token": token, "conforms": bool(_STATUS_TOKEN_RE.match(token))}


def _content_line_numbers(lines: list[str]) -> set[int]:
    """Return one-based line numbers outside fenced code blocks."""
    content: set[int] = set()
    in_fence = False
    fence_marker = ""
    for number, line in enumerate(lines, start=1):
        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)[0] * 3
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if not in_fence:
            content.add(number)
    return content


def _counted_blocks(lines: list[str], content: set[int]) -> list[tuple[int, int, int, str]]:
    """Return (first line, line after block, item count, source)."""
    blocks: list[tuple[int, int, int, str]] = []
    index = 0
    while index < len(lines):
        number = index + 1
        if number not in content:
            index += 1
            continue

        if (
            index + 1 < len(lines)
            and _TABLE_ROW_RE.match(lines[index])
            and _TABLE_SEPARATOR_RE.match(lines[index + 1])
        ):
            end = index + 2
            while end < len(lines) and _TABLE_ROW_RE.match(lines[end]):
                end += 1
            blocks.append((number, end + 1, end - (index + 2), "table"))
            index = end
            continue

        item = _LIST_ITEM_RE.match(lines[index])
        if item:
            indent = len(item.group(1))
            end = index + 1
            count = 1
            while end < len(lines):
                if not lines[end].strip():
                    end += 1
                    continue
                candidate = _LIST_ITEM_RE.match(lines[end])
                if candidate and len(candidate.group(1)) == indent:
                    count += 1
                    end += 1
                    continue
                leading_spaces = len(lines[end]) - len(lines[end].lstrip())
                if leading_spaces <= indent:
                    break
                end += 1
            blocks.append((number, end + 1, count, "list"))
            index = end
            continue
        index += 1
    return blocks


def _numeric_evidence(lines: list[str]) -> dict[str, list[dict]]:
    """Extract conservative claim/count pairings without judging mismatches."""
    content = _content_line_numbers(lines)
    structural_lines: set[int] = set()
    blocks = _counted_blocks(lines, content)
    for start, end, _, _ in blocks:
        structural_lines.update(range(start, end))

    claims: list[dict] = []
    claims_by_line: dict[int, list[int]] = {}
    for number, line in enumerate(lines, start=1):
        if number not in content or number in structural_lines:
            continue
        for match in _NUMERIC_CLAIM_RE.finditer(line):
            claim = {
                "claim": match.group(0),
                "value": int(match.group(1)),
                "location": number,
                "counted": None,
                "source": "prose",
            }
            claims_by_line.setdefault(number, []).append(len(claims))
            claims.append(claim)

    paired_indexes: set[int] = set()
    paired: list[dict] = []
    for start, _, count, source in blocks:
        previous = start - 1
        while previous > 0 and not lines[previous - 1].strip():
            previous -= 1
        candidates = claims_by_line.get(previous, [])
        if len(candidates) != 1 or candidates[0] in paired_indexes:
            continue
        claim_index = candidates[0]
        if source == "list":
            claim_pattern = re.escape(claims[claim_index]["claim"]).replace(r"\ ", r"\s*")
            if not re.search(rf"(?:次の|以下の)\s*{claim_pattern}", lines[previous - 1]):
                continue
        pair = dict(claims[claim_index])
        pair["counted"] = count
        pair["source"] = source
        paired.append(pair)
        paired_indexes.add(claim_index)

    return {
        "paired": paired,
        "unpaired": [claim for index, claim in enumerate(claims) if index not in paired_indexes],
    }


def analyze_file(path: Path, expected: list[str]) -> dict | None:
    lines = _read_lines(path)
    if lines is None:
        return None
    headings, bodies = _headings_and_bodies(lines)
    lower_map = {h.lower(): h for h in headings}
    missing: list[str] = []
    case_mismatch: list[dict] = []
    for section in expected:
        if section in headings:
            continue
        found = lower_map.get(section.lower())
        if found is not None:
            case_mismatch.append({"expected": section, "found": found})
        else:
            missing.append(section)
    status = _status_evidence(bodies.get("Status") or bodies.get(lower_map.get("status", "")))
    date_raw = bodies.get("Date") or bodies.get(lower_map.get("date", ""))
    date = {
        "raw": date_raw,
        "conforms": bool(_DATE_RE.match(date_raw)) if date_raw is not None else None,
    }
    notations = sorted(
        {key for key, pat in _NOTATION_PATTERNS if status["raw"] and pat.search(status["raw"])}
    )
    return {
        "file": path.name,
        "missing_sections": missing,
        "case_mismatch": case_mismatch,
        "status": status,
        "date": date,
        "has_review_when": "Review-when" in headings,
        "supersede_notations": notations,
        "numeric_evidence": _numeric_evidence(lines),
    }


def parse_index_numbers(adr_dir: Path) -> tuple[bool, set[str]]:
    lines = _read_lines(adr_dir / "README.md")
    if lines is None:
        return False, set()
    numbers = {m.group(1) for line in lines if (m := _INDEX_ROW_RE.match(line))}
    return True, numbers


def analyze_naming(md_files: list[Path]) -> dict:
    invalid: list[str] = []
    by_number: dict[str, set[str]] = {}
    for path in md_files:
        m = _ADR_FILE_RE.match(path.name)
        if not m:
            invalid.append(path.name)
            continue
        base_slug = _LANG_SUFFIX_RE.sub("", m.group(2))
        by_number.setdefault(m.group(1), set()).add(base_slug)
    duplicates = sorted(num for num, slugs in by_number.items() if len(slugs) > 1)
    numbers = sorted(by_number)
    gaps: list[str] = []
    if numbers:
        have = {int(n) for n in numbers}
        gaps = [f"{i:04d}" for i in range(min(have), max(have) + 1) if i not in have]
    return {"invalid": invalid, "duplicates": duplicates, "gaps": gaps, "numbers": numbers}


def collect_evidence(root: Path, adr_rel: str) -> dict | None:
    adr_dir = root / adr_rel
    if not adr_dir.is_dir():
        return None
    expected, template_source = load_template_sections(adr_dir)
    md_files = sorted(p for p in adr_dir.glob("*.md") if not p.name.lower().startswith("readme"))
    files = [f for p in md_files if (f := analyze_file(p, expected)) is not None]
    naming = analyze_naming(md_files)
    index_present, index_numbers = parse_index_numbers(adr_dir)
    file_numbers = set(naming["numbers"])
    return {
        "root": str(root),
        "adr_dir": adr_rel,
        "template_source": template_source,
        "expected_sections": expected,
        "files_total": len(md_files),
        "files": files,
        "naming": {k: naming[k] for k in ("invalid", "duplicates", "gaps")},
        "index": {
            "present": index_present,
            "in_index_not_files": sorted(index_numbers - file_numbers),
            "in_files_not_index": sorted(file_numbers - index_numbers),
        },
    }


def _file_number(name: str) -> int | None:
    m = _ADR_FILE_RE.match(name)
    return int(m.group(1)) if m else None


def gate_violations(
    evidence: dict, sections_from: int | None, review_when_from: int | None
) -> list[str]:
    v: list[str] = []
    for name in evidence["naming"]["invalid"]:
        v.append(f"{name}: filename does not match NNNN-slug.md")
    for num in evidence["naming"]["duplicates"]:
        v.append(f"{num}: duplicate ADR number across different slugs")
    for f in evidence["files"]:
        num = _file_number(f["file"])
        in_section_scope = num is not None and (sections_from is None or num >= sections_from)
        if in_section_scope:
            for section in f["missing_sections"]:
                if section == "Review-when" and review_when_from is not None:
                    continue  # the dedicated threshold check below owns this section
                v.append(f"{f['file']}: missing section '## {section}'")
            for cm in f["case_mismatch"]:
                v.append(
                    f"{f['file']}: section heading case mismatch "
                    f"('## {cm['found']}' should be '## {cm['expected']}')"
                )
        if (
            review_when_from is not None
            and num is not None
            and num >= review_when_from
            and not f["has_review_when"]
        ):
            v.append(
                f"{f['file']}: missing '## Review-when' (required from {review_when_from:04d})"
            )
        if f["status"]["conforms"] is False:
            v.append(
                f"{f['file']}: Status does not start with a known status word "
                f"(got '{f['status']['raw']}')"
            )
        if f["date"]["conforms"] is False:
            v.append(f"{f['file']}: Date is not YYYY-MM-DD (got '{f['date']['raw']}')")
    if not evidence["index"]["present"]:
        v.append("README.md index not found in ADR directory")
    for num in evidence["index"]["in_index_not_files"]:
        v.append(f"index lists {num} but no such ADR file exists")
    for num in evidence["index"]["in_files_not_index"]:
        v.append(f"ADR {num} exists but is missing from the README.md index")
    return v


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", default=".", help="repo root (default: cwd)")
    parser.add_argument("--adr-dir", default="docs/adr", help="ADR dir relative to root")
    parser.add_argument("--gate", action="store_true", help="blocking mode (exit 3 on violations)")
    parser.add_argument("--sections-from", type=int, default=None, metavar="NNNN")
    parser.add_argument("--require-review-when-from", type=int, default=None, metavar="NNNN")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser()
    evidence = collect_evidence(root, args.adr_dir)
    if evidence is None:
        print(f"adr_lint: {root / args.adr_dir} is not a directory", file=sys.stderr)
        return 2

    if not args.gate:
        json.dump(evidence, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0

    violations = gate_violations(evidence, args.sections_from, args.require_review_when_from)
    if violations:
        for line in violations:
            print(f"[adr-lint] {line}")
        print(f"[adr-lint] {len(violations)} violation(s)", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

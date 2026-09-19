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
import subprocess
import sys
from pathlib import Path

try:  # run as a file (sys.path[0] == scripts/) or imported as scripts.adr_review_evidence
    from adr_lint import _content_line_numbers, _headings_and_bodies, _read_lines
except ImportError:  # pragma: no cover - import path depends on the caller
    from scripts.adr_lint import _content_line_numbers, _headings_and_bodies, _read_lines

_ADR_REF_RE = re.compile(r"\bADR[- ](\d{4})\b")
_RFC_REF_RE = re.compile(r"\bRFC[- ](\d{4})\b")
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_HEADING_RE = re.compile(r"^## (.+?)\s*$")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")

_KNOWN_EXTENSIONS = {
    ".md",
    ".sh",
    ".py",
    ".json",
    ".jsonl",
    ".jsonld",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
    ".bats",
    ".plist",
    ".rs",
    ".swift",
    ".js",
    ".ts",
    ".cfg",
    ".ini",
    ".lock",
    ".csv",
    ".html",
}
# `path:12`, `path:12-15`, `path:L12`, `path:19,55` (first range is the one resolved)
_LINE_SUFFIX_RE = re.compile(r":L?(\d+)(?:[-–~](\d+))?(?:,\s?\d+(?:[-–~]\d+)?)*$")
_BARE_PATH_RE = re.compile(
    r"(?<![\w/@.'’-])((?:\.?[\w.-]+/)+[\w.*-]+/?|\.?[\w-]+\.[a-z]{2,5})"
    r"((?::L?\d+(?:[-–~]\d+)?(?:,\s?\d+(?:[-–~]\d+)?)*)?)"
)
# A bare "x/y" with no extension is a path only when a segment carries a file-ish
# character or the token has 3+ segments / a trailing slash — "A/B", "I/O",
# "before/after" were 46 of the top "missing" tokens in the 2026-09-16 sweep.
_FILEISH_SEGMENT_RE = re.compile(r"[._-]")
_METAVARIABLE_CHARS = set("<>{}*$")
_PLACEHOLDER_RE = re.compile(r"NNNN|XXX|slug|<name>|\.\.\.|…", re.IGNORECASE)
_OUTSIDE_PREFIXES = ("~", "/", "$")
_GENERIC_SEGMENTS = {
    "skills",
    "agents",
    "scripts",
    "hooks",
    "docs",
    "tests",
    "test",
    "src",
    "lib",
    "rules",
    "common",
    "adr",
    "rfcs",
    "references",
    "evals",
    "SKILL.md",
    "README.md",
    "__init__.py",
    "index.md",
    "main.py",
    "pyproject.toml",
}

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

_NUMBER_RE = re.compile(
    r"(?<![\w.:/-])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\s*"
    r"(%|％|件|本|行|個|点|回|repo|セッション|commit|files?|lines?|tokens?|KB|MB|字|文字|分|秒|倍|"
    r"skills?|agents?|hooks?|ADR|RFC|pass|fail)?(?![\w%])"
)
_NUMBER_SKIP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}|\b\d+\.\d+\.\d+\b|\b(?:ADR|RFC)[- ]\d{4}\b|\b0\d{3}\b|\b(?:19|20)\d{2}\b"
    r"|\bL\d+\b|:\d+\b|\d+:\d+|#\d+|[vV]\d+(?:\.\d+)*"
)
_ANCHOR_RES = (
    ("date", re.compile(r"\b\d{4}-\d{2}-\d{2}\b")),
    ("sha", re.compile(r"\b(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b")),
    ("url", re.compile(r"https?://")),
    ("path_line", re.compile(r"[\w./-]+\.[a-z]{1,5}:L?\d+|`[^`]+` ?L\d+")),
    (
        "command",
        re.compile(
            r"`(?:git|ls|grep|rg|wc|find|awk|jq|python3?|uv|pytest|bats|cat|sed|du|curl|"
            r"claude|npm|cargo)\b[^`]*`"
        ),
    ),
    ("measured", re.compile(r"実測|計測|測定|as[- ]of|measured|reproduc|再現|集計|カウント")),
    (
        "fraction",
        re.compile(r"\(\s*\d[\d,]*\s*/\s*\d[\d,]*\s*\)"),
    ),  # "54% (45/83)" — derivation shown
)
_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[%％]")
_DENOMINATOR_RE = re.compile(r"\d[\d,]*\s*/\s*\d[\d,]*|のうち|out of|of the \d|分母")
# Session-pointing words only. "now" / "today" / "現時点で" were 405 of 542 hits in
# the 2026-09-16 sweep and are ordinary prose, so they are not listed.
_RELATIVE_REFERENT_RE = re.compile(
    r"\d+\s*日齢|先ほど|本セッション|このセッション|this session|the session|先日|昨日|"
    r"今回の議論|直近の会話|上で述べた|前述の議論|yesterday|the conversation above",
    re.IGNORECASE,
)
_COUNT_CONDITION_RE = re.compile(
    r"\d+\s*(?:回|件|本|日|週|か月|ヶ月|ヵ月|months?|weeks?|days?|times|consecutive|周期|cycles?|"
    r"sessions?|セッション|reports?|報告)|連続|routinely|繰り返|続いたら|続くなら|repeatedly",
    re.IGNORECASE,
)
_VENUE_HINT_RE = re.compile(
    r"`[^`]+`|[\w-]+\.(?:md|jsonl|json|log|sh|py)|git log|commit|台帳|ledger"
)
_STATUS_QUO_RE = re.compile(
    r"何もしない|何も建てない|現状維持|status quo|do nothing|nothing|そのまま|変更しない|"
    r"defer|先送り|保留|待つ|放置|keep .{0,20}as[- ]is|as-is",
    re.IGNORECASE,
)
_MACHINERY_RE = re.compile(
    r"新設|追加|導入|hook|script|gate|lint|agent|skill を作|足す|build|add(?:s|ed)? |new ",
    re.IGNORECASE,
)
_REMOVAL_RE = re.compile(r"削除|退役|撤去|廃止|retire|remove|delete|drop|消す|外す", re.IGNORECASE)
_REVERSAL_RE = re.compile(r"巻き戻|復旧|復元|revert|reversal|undo|戻す|復帰|restore", re.IGNORECASE)
_DUPLICATION_RE = re.compile(
    r"第 ?2 の記録|二重|複製|重複|second place|duplicat|drift|正本", re.IGNORECASE
)
# Small enumerations ("13 本", "1 行") recur everywhere; a measurement worth
# tracing has a distinctive magnitude or unit. Sweep 2026-09-16: value >= 10 with
# any unit produced 2,382 hits over 256 ADRs; this boundary keeps the
# "82 repo / 104 config → SKILL.md" class the reviewer actually flagged.
_SECOND_RECORD_MIN_VALUE = 100
_SECOND_RECORD_DISTINCT_UNITS = {
    "KB",
    "MB",
    "tokens",
    "token",
    "セッション",
    "commit",
    "files",
    "file",
    "lines",
    "line",
    "字",
    "文字",
    "分",
    "秒",
    "repo",
}
# Percentages are not traced: "50%" / "80%" alone produced 1,400+ hits, most of
# them CSS in docs/diagrams/*.html. Generated / vendored text is excluded by type.
_SECOND_RECORD_SKIP_UNITS = {"%", "％"}
_SECOND_RECORD_EXCLUDE_GLOBS = ("*.html", "*.css", "*.svg", "*.js", "*.mjs", "*.lock", "*.min.*")
_SECOND_RECORD_MAX_TERMS = 30
_SECOND_RECORD_MAX_HITS = 60
_GENERIC_SMALL_UNITS = {"行", "本", "件", "個", "点", "回", "skill", "skills", "agent", "agents"}


# --------------------------------------------------------------------------- helpers


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


# --------------------------------------------------------------------------- refs


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


def _index_rows(adr_dir: Path, numbers: set[str]) -> dict[str, str | None]:
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
            f"ADR-{k}": v for k, v in _index_rows(adr_dir, {self_number, *targets}).items()
        },
    }


# --------------------------------------------------------------------------- paths


def _is_slash_command(word: str) -> bool:
    """`/skill-name` — one leading slash, no further slash or dot (harness skill syntax)."""
    return word.startswith("/") and "/" not in word[1:] and "." not in word


def _path_candidates(lines: list[str], content: set[int]) -> list[tuple[int, str, str]]:
    """(line, token, line-spec) for inline code, link hrefs and bare prose tokens."""
    seen: set[tuple[int, str]] = set()
    out: list[tuple[int, str, str]] = []

    def add(number: int, raw: str) -> None:
        token = raw.strip().strip(",;:)（）「」\"'").rstrip(".")
        if len(token) < 3 or _is_slash_command(token):
            return  # "/" or "~" alone are prose about prefixes, not references
        spec = ""
        m = _LINE_SUFFIX_RE.search(token)
        if m:
            spec = token[m.start() :]
            token = token[: m.start()]
        if not token or (number, token) in seen:
            return
        seen.add((number, token))
        out.append((number, token, spec))

    for number, line in enumerate(lines, start=1):
        if number not in content:
            continue
        for span in _INLINE_CODE_RE.findall(line):
            words = span.split()
            if not words or _is_slash_command(words[0]):
                continue  # `/review-to-lint …` is a skill invocation, not a path
            if any(w.startswith(_OUTSIDE_PREFIXES) for w in words) and len(words) > 1:
                add(number, span)  # a path containing spaces — keep whole
                continue
            for w in words:
                if "/" in w or Path(w).suffix.lower() in _KNOWN_EXTENSIONS:
                    add(number, w)
        for href in _MD_LINK_RE.findall(line):
            add(number, href.split("#", 1)[0])
        for m in _BARE_PATH_RE.finditer(_strip_inline_code(line)):
            add(number, m.group(1) + m.group(2))
    return out


def _is_path_shaped(token: str) -> bool:
    if Path(token).suffix.lower() in _KNOWN_EXTENSIONS:
        return True
    if "/" not in token:
        return False
    segments = [s for s in token.split("/") if s]
    return (
        token.endswith("/")
        or len(segments) >= 3
        or any(_FILEISH_SEGMENT_RE.search(s) for s in segments)
    )


def _normalize_token(root: Path, adr_dir: Path, token: str) -> tuple[str, str | None]:
    """Return (kind-prefix, repo-relative path or None).

    `~/…` and absolute paths that land inside the repo are repo paths (harness
    ADRs write `~/.claude/skills/x` for their own tree); `./x` is relative to the
    ADR file first (Markdown link semantics), then to the root.
    """
    if token.startswith(("~", "/")):
        try:
            expanded = Path(token.split(":", 1)[0]).expanduser().resolve()
        except (OSError, RuntimeError):
            return "outside_repo", None
        if expanded == root:
            return "not_a_path", None  # `~/.claude` naming the repo itself
        if expanded.is_relative_to(root):
            return "", str(expanded.relative_to(root))
        return "outside_repo", None
    if token.startswith("./") or token.startswith("../"):
        candidate = (adr_dir / token).resolve()
        if candidate.is_relative_to(root):
            return "", str(candidate.relative_to(root))
        return "outside_repo", None
    return "", token.rstrip("/") or None


def _classify_path(
    root: Path, tracked: set[str], adr_dir: Path, token: str
) -> tuple[str, str | None]:
    """Return (kind, resolved repo-relative path or None)."""
    if token.startswith(("http://", "https://", "mailto:")):
        return "url", None
    if any(ch in _METAVARIABLE_CHARS for ch in token) or _PLACEHOLDER_RE.search(token):
        return "metavariable", None
    if not _is_path_shaped(token):
        return "not_a_path", None
    prefix, rel = _normalize_token(root, adr_dir, token)
    if prefix:
        return prefix, None
    if rel is None or rel in {"", "."}:
        return "not_a_path", None
    segments = rel.split("/")
    if (
        len(segments) == 2
        and not token.endswith("/")
        and Path(rel).suffix.lower() not in _KNOWN_EXTENSIONS
        and not (root / segments[0]).is_dir()
    ):
        return "not_a_path", None  # "anthropics/claude-code" — an org/repo, not a tree path
    if "/" not in token:
        matches = _resolve_basename(tracked, rel)
        if len(matches) == 1:
            return "tracked_via_basename", matches[0]
        if len(matches) > 1:
            return "ambiguous_basename", None
    if rel in tracked or any(t.startswith(rel + "/") for t in tracked):
        return "tracked", rel
    if (root / rel).exists():
        return ("ignored" if _is_ignored(root, rel) else "untracked"), rel
    if "/" not in token:
        return "bare_name_unresolved", None  # may be a runtime artifact, not a repo file
    return "missing", rel


def _resolve_basename(tracked: set[str], token: str) -> list[str]:
    name = Path(token).name
    return sorted(t for t in tracked if Path(t).name == name)[:5]


def _cited_lines(root: Path, rel: str, spec: str) -> dict:
    m = _LINE_SUFFIX_RE.search(spec)
    if not m:
        return {}
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    lines = _read_lines(root / rel) or []
    return {
        "cited": spec.lstrip(":"),
        "file_lines": len(lines),
        "in_range": 1 <= a <= len(lines) and a <= b <= len(lines),
        "text": [_snippet(lines[i - 1], 140) for i in range(a, min(b, a + 2, len(lines)) + 1)]
        if 1 <= a <= len(lines)
        else [],
    }


_RESOLVED_KINDS = {"tracked", "tracked_via_basename", "untracked", "ignored"}
_FLAGGED_KINDS = {"missing", "ignored", "untracked", "outside_repo"}


def check_paths(lines: list[str], content: set[int], root: Path, adr_path: Path) -> dict:
    tracked = _tracked_files(root)
    self_rel = str(adr_path.relative_to(root)) if adr_path.is_relative_to(root) else None
    items: list[dict] = []
    for number, token, spec in _path_candidates(lines, content):
        kind, rel = _classify_path(root, tracked, adr_path.parent, token)
        if kind in {"url", "not_a_path"}:
            continue
        if rel is not None and rel == self_rel:
            kind = "self"
        item: dict = {"line": number, "token": token, "kind": kind}
        if rel is not None:
            item["resolved"] = rel
        if kind == "missing":
            candidates = _resolve_basename(tracked, token)
            if candidates:
                item["basename_matches"] = candidates
        if spec and kind in _RESOLVED_KINDS and rel is not None:
            item["line_ref"] = _cited_lines(root, rel, spec)
        items.append(item)
    by_kind: dict[str, int] = {}
    for item in items:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
    return {
        "items": items,
        "by_kind": dict(sorted(by_kind.items())),
        "flagged": [i for i in items if i["kind"] in _FLAGGED_KINDS],
        "line_refs_out_of_range": [
            i for i in items if i.get("line_ref") and not i["line_ref"]["in_range"]
        ],
    }


# --------------------------------------------------------------------------- diff scope


def _changed_files(root: Path, spec: str) -> list[str]:
    if spec == "staged":
        raw = _git(root, "diff", "--cached", "--name-only")
    elif spec == "worktree":
        raw = "\n".join(
            line[3:].split(" -> ")[-1]
            for line in _git(root, "status", "--porcelain", "--untracked-files=all").splitlines()
            if line
        )
    else:
        raw = _git(root, "diff", "--name-only", spec)
    return sorted({line.strip() for line in raw.splitlines() if line.strip()})


def _mention_match(text: str, path: str) -> str | None:
    if path in text:
        return "path"
    name = Path(path).name
    if name not in _GENERIC_SEGMENTS and len(name) >= 6 and name in text:
        return "basename"
    for segment in Path(path).parts[:-1]:
        if (
            segment not in _GENERIC_SEGMENTS
            and len(segment) >= 5
            and re.search(rf"(?<![\w-]){re.escape(segment)}(?![\w-])", text)
        ):
            return f"component:{segment}"
    return None


def check_diff_scope(
    lines: list[str],
    content: set[int],
    root: Path,
    adr_path: Path,
    spec: str,
    path_items: list[dict],
) -> dict:
    text = "\n".join(lines[n - 1] for n in sorted(content))
    changed = _changed_files(root, spec)
    adr_dir_rel = str(adr_path.parent.relative_to(root)) if adr_path.is_relative_to(root) else ""
    not_mentioned: list[str] = []
    mentioned: list[dict] = []
    for path in changed:
        if adr_dir_rel and path.startswith(adr_dir_rel + "/"):
            continue  # the ADR itself, its index, sibling 注記 edits
        how = _mention_match(text, path)
        (mentioned.append({"file": path, "matched_by": how}) if how else not_mentioned.append(path))
    changed_set = set(changed)
    mentioned_not_changed = sorted(
        {
            i["resolved"]
            for i in path_items
            if i["kind"] in {"tracked", "tracked_via_basename"}
            and i["resolved"] not in changed_set
            and not any(c.startswith(i["resolved"] + "/") for c in changed_set)
            and not (adr_dir_rel and i["resolved"].startswith(adr_dir_rel + "/"))
        }
    )
    return {
        "spec": spec,
        "changed_total": len(changed),
        "changed_not_mentioned": not_mentioned,
        "changed_mentioned": mentioned,
        "mentioned_tracked_not_changed": mentioned_not_changed,
    }


# --------------------------------------------------------------------------- numbers


def _number_tokens(line: str) -> list[dict]:
    masked = _NUMBER_SKIP_RE.sub(lambda m: " " * len(m.group(0)), _strip_inline_code(line))
    out: list[dict] = []
    for m in _NUMBER_RE.finditer(masked):
        unit = m.group(3) or ""
        value = float(m.group(1).replace(",", "") + (m.group(2) or ""))
        # Unitless numbers count only when comma-formatted ("1,774"): bare 100 / 500 /
        # 429 were HTTP codes and thresholds in the sweep. Tiny enumerations
        # ("1 行", "2 skill") and definitional 0% / 100% are not measurements.
        if not unit and "," not in m.group(1):
            continue
        if unit in _GENERIC_SMALL_UNITS and value <= 2:
            continue
        if unit in {"%", "％"} and value in (0.0, 100.0):
            continue
        out.append({"text": m.group(0).strip(), "value": value, "unit": unit})
    return out


def check_numbers(lines: list[str], content: set[int], spans: dict[str, tuple[int, int]]) -> dict:
    skip_lines: set[int] = set()
    for name in ("Status", "Date", "Review-when"):
        for n, _ in _section_lines(lines, spans, name):
            skip_lines.add(n)
    unanchored: list[dict] = []
    anchored_total = 0
    for paragraph in _paragraphs(lines, content):
        text = "\n".join(line for _, line in paragraph)
        anchors = sorted(name for name, pat in _ANCHOR_RES if pat.search(text))
        for number, line in paragraph:
            if number in skip_lines:
                continue
            for tok in _number_tokens(line):
                if anchors:
                    anchored_total += 1
                else:
                    unanchored.append(
                        {"line": number, "claim": tok["text"], "context": _snippet(line, 110)}
                    )
    percent_no_denominator = [
        {"line": n, "claim": m.group(0), "context": _snippet(line, 110)}
        for n, line in enumerate(lines, start=1)
        if n in content and n not in skip_lines
        for m in _PERCENT_RE.finditer(_strip_inline_code(line))
        if not _DENOMINATOR_RE.search(line) and float(m.group(1)) not in (0.0, 100.0)
    ]
    referents = [
        {"line": n, "match": m.group(0), "context": _snippet(line, 110)}
        for n, line in enumerate(lines, start=1)
        if n in content
        for m in _RELATIVE_REFERENT_RE.finditer(_strip_inline_code(line))
    ]
    return {
        "anchored_total": anchored_total,
        "unanchored": unanchored,
        "percent_without_denominator": percent_no_denominator,
        "relative_referents": referents,
    }


# --------------------------------------------------------------------------- sections


def check_review_when(lines: list[str], spans: dict[str, tuple[int, int]]) -> dict:
    items: list[dict] = []
    for n, line in _section_lines(lines, spans, "Review-when"):
        if not line.strip() or not (_LIST_ITEM_RE.match(line) or len(line.strip()) > 20):
            continue
        items.append(
            {
                "line": n,
                "text": _snippet(line, 140),
                "count_condition": bool(_COUNT_CONDITION_RE.search(line)),
                "venue_hint": bool(_VENUE_HINT_RE.search(line)),
            }
        )
    return {"present": bool(_section_lines(lines, spans, "Review-when")), "items": items}


def check_alternatives(lines: list[str], spans: dict[str, tuple[int, int]]) -> dict:
    section = _section_lines(lines, spans, "Alternatives Considered")
    text = "\n".join(line for _, line in section)
    decision = "\n".join(line for _, line in _section_lines(lines, spans, "Decision"))
    top_items = sum(
        1 for _, line in section if re.match(r"^(?:[-+*]|\d+[.)])\s|^###\s|^\*\*", line)
    )
    return {
        "present": bool(section),
        "top_level_items": top_items,
        "status_quo_present": bool(_STATUS_QUO_RE.search(text)),
        "decision_machinery_signals": len(_MACHINERY_RE.findall(decision)),
    }


def check_consequences(lines: list[str], spans: dict[str, tuple[int, int]]) -> dict:
    section = _section_lines(lines, spans, "Consequences")
    text = "\n".join(line for _, line in section)
    decision = "\n".join(line for _, line in _section_lines(lines, spans, "Decision"))
    return {
        "present": bool(section),
        "subheadings": [
            line.strip() for _, line in section if re.match(r"^#{3,4}\s|^\*\*[^*]+\*\*\s*$", line)
        ],
        "decision_removal_signals": len(_REMOVAL_RE.findall(decision)),
        "reversal_cost_tokens": bool(_REVERSAL_RE.search(text)),
        "duplication_named": bool(_DUPLICATION_RE.search(text)),
    }


# --------------------------------------------------------------------------- second record


def check_second_record(
    lines: list[str],
    content: set[int],
    spans: dict[str, tuple[int, int]],
    root: Path,
    adr_dir_rel: str,
) -> dict:
    skip: set[int] = {
        n for name in ("Status", "Date") for n, _ in _section_lines(lines, spans, name)
    }
    terms: list[str] = []
    for n, line in enumerate(lines, start=1):
        if n not in content or n in skip:
            continue
        for tok in _number_tokens(line):
            distinctive = (
                (tok["unit"] in _SECOND_RECORD_DISTINCT_UNITS and tok["value"] >= 10)
                or tok["value"] >= _SECOND_RECORD_MIN_VALUE
                or "," in tok["text"]
            )
            if tok["unit"] in _SECOND_RECORD_SKIP_UNITS or not tok["unit"]:
                continue
            if distinctive and tok["text"] not in terms:
                terms.append(tok["text"])
    terms = terms[:_SECOND_RECORD_MAX_TERMS]
    hits: list[dict] = []
    if terms and (root / ".git").exists():
        args = ["grep", "-n", "-I", "-F"]
        for t in terms:
            args += ["-e", t]
        args += ["--", ".", f":(exclude){adr_dir_rel}", f":(exclude){adr_dir_rel}/**"]
        args += [f":(exclude,glob)**/{g}" for g in _SECOND_RECORD_EXCLUDE_GLOBS]
        for raw in _git(root, *args).splitlines():
            parts = raw.split(":", 2)
            if len(parts) == 3:
                hits.append(
                    {"file": parts[0], "line": int(parts[1]), "text": _snippet(parts[2], 120)}
                )
            if len(hits) >= _SECOND_RECORD_MAX_HITS:
                break
    return {"terms": terms, "hits": hits}


# --------------------------------------------------------------------------- main


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

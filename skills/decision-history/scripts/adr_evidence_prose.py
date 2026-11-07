"""Prose-level checks: measurements, Review-when items, Alternatives, Consequences.

Split out of `adr_review_evidence.py` under the file-LOC budget (ADR-0056). These
read the ADR's own text and, for `check_second_record`, grep the tree for the same
measurement written down a second time. Every regex here is a *measured input*:
editing one moves what the reviewer is shown, so the sweep that chose each
boundary is named next to it.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.adr_evidence_common import (
    _LIST_ITEM_RE,
    _git,
    _paragraphs,
    _section_lines,
    _snippet,
    _strip_inline_code,
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

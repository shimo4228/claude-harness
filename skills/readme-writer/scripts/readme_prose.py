"""Prose-level evidence sections for readme_evidence: fixed-pattern signals (slop
vocabulary, em dash, triad pre-announce, JA degree adverbs, stadium address), the
Japanese register count (ですます vs plain endings), history lines and numeric-claim
lines. A hit is a line for the judge to read, never a verdict.
"""

from __future__ import annotations

import re

if __package__:
    from . import readme_md as _md
else:  # Support the documented direct script invocation.
    import readme_md as _md

_HTML_IMG_RE = _md._HTML_IMG_RE
_MD_IMAGE_RE = _md._MD_IMAGE_RE
Heading = _md.Heading
_is_prose_line = _md._is_prose_line
_prose_only = _md._prose_only

_EM_DASH = "—"
_VERSION_RE = re.compile(r"\bv\d+\.\d+(?:\.\d+)?\b")
_HISTORY_RE = re.compile(
    r"switched from|replaced by|previously|from \d+ to \d+|以前は|から.*に切り替え|旧版|旧バージョン",
    re.IGNORECASE,
)
_NUMERIC_CLAIM_RE = re.compile(r"[<>≤≥]\s*\d|\d+(?:\.\d+)?\s*%|\|Δ|±\s*\d|\bp\s*[<=]\s*0\.\d")
_TRIAD_RE = re.compile(
    r"(?<!\d)(3|三|three)\s*(つ|点|要素|things|reasons|ways|points|steps)", re.IGNORECASE
)
_STADIUM_RE = re.compile(
    r"皆さん|みなさん|皆様|みなさま|dear reader|folks,|you guys", re.IGNORECASE
)
_DEGREE_ADVERB_JA_RE = re.compile(
    r"とても|非常に|かなり|しっかり|すごく|本当に|極めて|めちゃくちゃ"
)
# Small slop vocabulary. The canonical banned list lives in writing-ecosystem
# (resident in ~/MyAI_Lab/zenn-content/.claude/skills/);
# this copy is deliberately short (same choice zenn-content made) and only
# produces evidence lines — the judge decides whether a hit matters.
_SLOP_EN = (
    "powerful tool",
    "revolutioniz",
    "cutting-edge",
    "game-changer",
    "seamless",
    "effortlessly",
    "delve",
    "multifaceted",
    "holistic",
    "transformative",
    "testament to",
    "deep dive",
    "pivotal",
    "tapestry",
    "unlock",
    "unleash",
    "empower",
    "paradigm",
    "leverage",
    "robust",
    "in today's rapidly evolving",
)
_SLOP_JA = (
    "画期的",
    "革命的",
    "革新的",
    "素晴らしい",
    "驚くべき",
    "感動的",
    "シームレス",
    "パワフル",
    "ロバスト",
    "パラダイムシフト",
    "深い洞察",
    "示唆に富む",
    "重要な示唆",
    "最先端",
    "深掘り",
    "と言えるでしょう",
)
_SLOP_RE = re.compile("|".join(re.escape(w) for w in _SLOP_EN + _SLOP_JA), re.IGNORECASE)
_JA_SENTENCE_END_RE = re.compile(r"[。！？]")
# ですます: the polite stem, an optional sentence-final particle (ですか / ますね),
# then any closing brackets, quotes or Markdown emphasis before 。！？.
_POLITE_END_RE = re.compile(
    r"(?:です|ます|でした|ました|ません|ましょう|でしょう|ください)(?:か|ね|よ|よね)?"
    r"[」』）)］\]】〕〉》\"'”’*_`]*$"
)
_ASIDE_OPEN, _ASIDE_CLOSE = "（(", "）)"
_REGISTER_LINES_CAP = 20
_REGISTER_TEXT_CAP = 60


def prose_signals(content: list[tuple[int, str]]) -> dict:
    slop, stadium, degree, triad = [], [], [], []
    em_lines: list[int] = []
    for n, raw in content:
        t = _prose_only(raw)
        for m in _SLOP_RE.finditer(t):
            slop.append({"line": n, "term": m.group(0)})
        if _STADIUM_RE.search(t):
            stadium.append(n)
        for m in _DEGREE_ADVERB_JA_RE.finditer(t):
            degree.append({"line": n, "term": m.group(0)})
        if _TRIAD_RE.search(t):
            triad.append(n)
        if _EM_DASH in t:
            em_lines.extend([n] * t.count(_EM_DASH))
    return {
        "slop_words": slop,
        "em_dash": {"count": len(em_lines), "lines": sorted(set(em_lines))},
        "triad_preannounce_lines": triad,
        "degree_adverbs_ja": degree,
        "stadium_lines": stadium,
    }


def _is_body_prose(line_no: int, line: str, heading_lines: set[int]) -> bool:
    """A paragraph line: not a heading, list item, table row, block quote, HTML or
    image line (fenced code never reaches here)."""
    stripped = line.strip()
    if line_no in heading_lines or stripped.startswith("<"):
        return False
    if _MD_IMAGE_RE.search(stripped) or _HTML_IMG_RE.search(stripped):
        return False
    return _is_prose_line(stripped)


def _peel_trailing_asides(body: str) -> str:
    """Drop closed （…） / (…) asides from the end of `body` — in …見せます（docs、
    2026-09-21 確認） the register lives in the words before the aside. Stops at a
    nested aside and never peels the whole sentence (（詳しくは後述します） stays).
    One backward pass: every char is visited once, so long paren or space runs stay
    linear (a `$`-anchored regex sub in a loop was quadratic)."""
    end = len(body)
    while end and body[end - 1] in _ASIDE_CLOSE:
        start = end - 1
        while start and body[start - 1] not in _ASIDE_OPEN + _ASIDE_CLOSE:
            start -= 1
        if not start or body[start - 1] not in _ASIDE_OPEN:
            break  # no opener, or a nested aside: classify what is there
        cut = start - 1
        while cut and body[cut - 1].isspace():
            cut -= 1
        if not cut:
            break  # the aside is the whole sentence
        end = cut
    return body[:end]


def _is_polite(body: str) -> bool:
    """`body` is a sentence without its 。！？."""
    return bool(_POLITE_END_RE.search(_peel_trailing_asides(body)))


def _tail(text: str, cap: int = _REGISTER_TEXT_CAP) -> str:
    """Keep the end: the ending is what the register evidence is about."""
    return text if len(text) <= cap else "…" + text[-(cap - 1) :]


def register_ja(content: list[tuple[int, str]], headings: list[Heading]) -> dict:
    """ですます vs plain sentence endings in body prose paragraphs. A sentence may wrap
    across lines of one paragraph; it is reported on the line holding its 。！？."""
    heading_lines = {h.line for h in headings}
    polite = 0
    plain: list[dict] = []
    # Text of the sentence still open, as fragments: joined once when its 。！？ arrives,
    # never re-scanned, so a long paragraph without terminators stays linear.
    pending: list[str] = []
    prev = -1
    for n, line in content:
        if not _is_body_prose(n, line, heading_lines):
            continue
        if n != prev + 1:  # a blank or non-paragraph line ended the previous paragraph
            pending = []
        prev = n
        text = _prose_only(line.strip())
        start = 0
        for m in _JA_SENTENCE_END_RE.finditer(text):
            pending.append(text[start : m.end()])
            start = m.end()
            sentence = "".join(pending).strip()
            pending = []
            body = sentence[:-1].rstrip()
            if not body:
                continue
            if _is_polite(body):
                polite += 1
            else:
                plain.append({"line": n, "text": _tail(sentence)})
        pending.append(text[start:])
    return {
        "desu_masu": polite,
        "plain": len(plain),
        "plain_lines": plain[:_REGISTER_LINES_CAP],
    }


def history_signals(content: list[tuple[int, str]]) -> list[dict]:
    out = []
    for n, raw in content:
        t = _prose_only(raw)
        hits = [m.group(0) for m in _VERSION_RE.finditer(t)] + [
            m.group(0) for m in _HISTORY_RE.finditer(t)
        ]
        if hits:
            out.append({"line": n, "matches": hits})
    return out


def numeric_claims(content: list[tuple[int, str]]) -> list[dict]:
    out = []
    for n, raw in content:
        t = _prose_only(raw)
        if _NUMERIC_CLAIM_RE.search(t):
            out.append({"line": n, "matches": [m.group(0) for m in _NUMERIC_CLAIM_RE.finditer(t)]})
    return out

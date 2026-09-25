"""Deterministic evidence extractor for human-facing README files.

This script produces **evidence, not a verdict**. It counts and lists the things
an LLM judge is bad at counting (how many ADR references, how many coined-term
candidates, how many lines before the first section, which <details> blocks hide
what) and hands them to `readme-judge` as JSON. It never decides whether a README
is good: no severity, no threshold, no failing exit code. The same design as
zenn-content's `scripts/zenn_evidence.py` — the judge reads the JSON as one input
among several and owns the named verdict.

Exit codes: 0 = evidence emitted (always, regardless of content), 2 = file not
found / too large. There is no exit 1.

JSON contract (top-level keys, in output order): path, lang_guess, line_count,
own_repo, structure, identity_lead, first_screen, insider_refs, term_candidates,
details_blocks, figures, badges, prose_signals, register_ja, history_signals,
numeric_claims, doi_citation, note, notes.

- own_repo: "owner/repo" of the GitHub `origin` remote of the README's directory
  (`git -C <dir> remote get-url origin`, short timeout), or null on any failure or a
  non-GitHub host. `--own-repo` overrides detection ("" = none). Links and badges
  to it are excluded from first_screen.github_repos and insider_refs.github_repos /
  github_repo_count, so those count sibling repos only.
- structure.broken_anchors: [{href, line}] for `[text](#fragment)` links whose
  fragment matches neither a GitHub heading slug of this file nor an explicit
  <a id/name> anchor (`#` and `#top` always resolve).
- figures[].prose_adjacent: a prose line sits within 2 lines before or after the
  figure (HTML wrapper lines such as <p align="center"> belong to the figure);
  headings, blank lines, badges and other figures never qualify.
- insider_refs.doc_paths: `(docs/...)` and `(./docs/...)` link targets share the
  `docs/...` key.
- register_ja: for a Japanese README, sentence endings (text before 。！？) in body
  prose paragraphs, as {desu_masu, plain, plain_lines: [{line, text}]} (first 20,
  text is the sentence tail, at most 60 chars); null for English.
- notes: one string per counter stating what it cannot see; the judge covers
  those blind spots itself (e.g. coined terms written in plain prose).

Markdown coverage: ATX and setext headings; fenced code blocks (``` / ~~~),
front matter and HTML comments are excluded from prose-level counts but headings
are kept. Per-line and per-file size caps are DoS backstops, not quality rules.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter, OrderedDict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

# --- structural parsing ------------------------------------------------------ #
_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
# Title anchored to a non-space char to avoid O(n^2) backtracking on a long
# all-space suffix (ReDoS guard).
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(\S(?:.*\S)?)\s*$")
_TRAILING_HASHES_RE = re.compile(r"\s+#+\s*$")
_SETEXT_H1_RE = re.compile(r"^ {0,3}=+\s*$")
_SETEXT_H2_RE = re.compile(r"^ {0,3}-+\s*$")
_LIST_OR_QUOTE_RE = re.compile(r"^\s*([-*+>]\s|\d+[.)]\s)")
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
_MD_LINK_RE = re.compile(
    r"(?<!!)\[(?!!)([^\]]*)\]\(\s*([^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
_HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_ATTR_SRC_RE = re.compile(r"\bsrc\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_ATTR_ALT_RE = re.compile(r"\balt\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>)\]]+")
_BIBTEX_RE = re.compile(r"@\w+\s*\{", re.IGNORECASE)
_CITATION_AFFORDANCE_RE = re.compile(r"\b(citation|bibtex)\b", re.IGNORECASE)
_CITE_HEADING_RE = re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*(\bcit(e|ing|ation)|引用)")
_DETAILS_OPEN_RE = re.compile(r"<details\b", re.IGNORECASE)
_DETAILS_CLOSE_RE = re.compile(r"</details\s*>", re.IGNORECASE)
_SUMMARY_RE = re.compile(r"<summary\b[^>]*>(.*?)</summary\s*>", re.IGNORECASE | re.DOTALL)
_BADGE_SRC_RE = re.compile(
    r"shields\.io|/badge|badge\.svg|badgen\.net|deepwiki|gitmcp|zenodo\.org/badge"
    r"|codecov|coveralls|circleci|travis-ci|app\.netlify\.com/.*deploy-status",
    re.IGNORECASE,
)
_NON_PROSE_PREFIX_RE = re.compile(
    r"^(#{1,6}\s|[-*+>]\s|\d+[.)]\s|\||<|\[[^\]]+\]:\s"
    r"|={2,}\s*$|-{3,}\s*$|\*{3,}\s*$|_{3,}\s*$)"
)
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)

# --- evidence patterns ------------------------------------------------------- #
_ADR_ID_RE = re.compile(r"\bADR-(\d{4})\b")
_GITHUB_REPO_RE = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")
# owner/repo from a git remote: https://[user@]github.com/o/r[.git][/],
# git@github.com:o/r[.git], ssh://git@[ssh.]github.com[:port]/o/r[.git]
_GITHUB_REMOTE_RE = re.compile(
    r"(?:^|[/@.])github\.com[:/](?:\d+/)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
_GIT_TIMEOUT_S = 2
_DOC_PATH_RE = re.compile(r"\(\s*(?:\./)?(docs/[^)\s#]+)")
_HTML_A_TAG_RE = re.compile(r"<a\b[^<>]*>", re.IGNORECASE)  # [^<>]: a "<" run stays linear
_ATTR_ID_NAME_RE = re.compile(r"(?<![\w-])(?:id|name)\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
# A line made of HTML tags only (<p align="center">, </p>, <picture>, <source …>):
# it wraps the figure next to it rather than separating it from its caption.
_TAG_ONLY_RE = re.compile(r"^(?:</?[A-Za-z][^>]*>\s*)+$")
_BACKTICK_RE = re.compile(r"`([^`\n]{2,60})`")
_BOLD_RE = re.compile(r"\*\*([^*\n]{2,60})\*\*")
_CAMEL_RE = re.compile(r"^[A-Z][a-z]+(?:[A-Z][a-z]+)+$")
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

# Blind spots of each counter, emitted verbatim as `notes`. The judge reads these
# to know what the numbers cannot show; one entry per counter, the term one first.
NOTES = (
    "term_candidates / first_screen.new_terms see only backtick and bold spans; coined "
    "terms written in plain prose are not counted, so the judge identifies those.",
    "identity_lead only locates the first prose line between the H1 and the next heading; "
    "whether it says what the project is and who it is for is the judge's call.",
    "insider_refs counts ADRs only as ADR-NNNN, repositories only as github.com URLs, and "
    "doc_paths only as (docs/...) or (./docs/...) link targets; sibling projects named in "
    "plain prose are not counted.",
    "own_repo comes from the git origin of the README's directory (GitHub remotes only); "
    "when it is null, links to the README's own repository count as sibling repos, and a "
    "README copied into another repository reports that repository.",
    "structure.broken_local_refs resolves relative links on disk from the README's "
    "directory; a README read outside its repository reports every relative link as "
    "broken. Absolute paths, external URLs and #fragments inside other files are not checked.",
    "structure.broken_anchors checks only [text](#fragment) links against GitHub's heading "
    "slugs and <a id/name> anchors of this file; HTML <a href> links are not checked and "
    "other renderers slug headings differently.",
    "figures[].prose_adjacent only says a prose line sits within 2 lines of the figure; "
    "whether that line states what the figure shows is the judge's call.",
    "prose_signals, history_signals and numeric_claims match fixed pattern lists; a hit is "
    "a line to read, and wording outside the patterns is not seen.",
    "register_ja classifies only sentences ending in 。！？ inside body paragraphs, by their "
    "last words; list items, tables, headings, quotes and sentences without a terminal mark "
    "are not counted.",
    "lang_guess is ja when 3 or more 。！？ appear outside code; an English README that "
    "quotes Japanese can read as ja.",
)

_MAX_BYTES = 10 * 1024 * 1024
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


def _content_lines(markdown: str) -> list[tuple[int, str]]:
    """(1-based line number, text) for lines outside fenced code blocks."""
    out: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_len = 0
    raw = markdown.splitlines()
    skip_until = 0
    if raw and raw[0].strip() == "---":  # YAML front matter: skip through the closing ---
        for j in range(1, len(raw)):
            if raw[j].strip() == "---":
                skip_until = j + 1
                break
    for idx, line in enumerate(raw, start=1):
        if idx <= skip_until:
            continue
        if len(line) > _MAX_LINE:
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


def _fence_lines(markdown: str) -> list[tuple[int, str]]:
    """Opening fence lines with their info string (to find ```mermaid blocks)."""
    out: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_len = 0
    for idx, line in enumerate(markdown.splitlines(), start=1):
        match = _FENCE_RE.match(line)
        if not match:
            continue
        run = match.group("fence")
        marker, length = run[0], len(run)
        rest = match.group("rest").strip()
        if fence_char is None:
            fence_char, fence_len = marker, length
            out.append((idx, rest))
        elif marker == fence_char and length >= fence_len and not rest:
            fence_char, fence_len = None, 0
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
    return "" if raw is None else raw[1:-1]


def parse_images(markdown: str) -> list[Image]:
    images: list[Image] = []
    for line_no, line in _content_lines(markdown):
        for m in _MD_IMAGE_RE.finditer(line):
            images.append(Image(alt=m.group(1), src=m.group(2), line=line_no))
        for tag in _HTML_IMG_RE.finditer(line):
            src_m = _ATTR_SRC_RE.search(tag.group(0))
            alt_m = _ATTR_ALT_RE.search(tag.group(0))
            images.append(
                Image(
                    alt=_attr_value(alt_m.group(1) if alt_m else None),
                    src=_attr_value(src_m.group(1) if src_m else None),
                    line=line_no,
                )
            )
    return images


def parse_links(markdown: str) -> list[Link]:
    return [
        Link(text=m.group(1), href=m.group(2), line=line_no)
        for line_no, line in _content_lines(markdown)
        for m in _MD_LINK_RE.finditer(line)
    ]


def _is_external(href: str) -> bool:
    h = href.strip()
    return bool(_SCHEME_RE.match(h)) or h.startswith("//")


_HTML_INLINE_OPEN_RE = re.compile(r"^<(p|b|strong|em|i)\b[^>]*>", re.IGNORECASE)


def _is_prose_line(stripped: str) -> bool:
    if not stripped:
        return False
    if _HTML_INLINE_OPEN_RE.match(stripped):
        # <p align="center"><b>X</b> is a ...</p>: judge the text, not the tag
        stripped = re.sub(r"<[^>]+>", "", stripped).strip()
        if not stripped:
            return False
    if _NON_PROSE_PREFIX_RE.match(stripped):
        return False
    bare = _MD_LINK_RE.sub("", _MD_IMAGE_RE.sub("", stripped)).strip()
    if not bare:
        return False
    text = _MD_IMAGE_RE.sub(" ", stripped)
    text = _MD_LINK_RE.sub(lambda m: f" {m.group(1)} ", text)
    return bool(_LETTER_RE.search(text))


def _prose_only(text: str) -> str:
    """Replace images with their alt and links with their text, so URLs never
    feed the prose-level pattern scans (a badge URL is not a numeric claim)."""
    text = _MD_IMAGE_RE.sub(lambda m: m.group(1), text)
    text = _MD_LINK_RE.sub(lambda m: m.group(1), text)
    return re.sub(r"https?://\S+", "", text)


def _details_depth_map(content: list[tuple[int, str]]) -> dict[int, bool]:
    """line -> True when the line sits inside a <details> body."""
    inside: dict[int, bool] = {}
    depth = 0
    for line_no, line in content:
        depth += len(_DETAILS_OPEN_RE.findall(line))
        inside[line_no] = depth > 0
        depth = max(0, depth - len(_DETAILS_CLOSE_RE.findall(line)))
    return inside


def _slug_char_kept(ch: str) -> bool:
    # github-slugger (the slugger GitHub's renderer mirrors), regex generator read
    # 2026-09-25: it strips No, all punctuation except Pc and "-", symbols, controls and
    # separators except " ". What survives: letters, marks, Nd / Nl, Pc ("_"), " ", "-".
    if ch in " -":
        return True
    cat = unicodedata.category(ch)
    return cat[0] in "LM" or cat in ("Nd", "Nl", "Pc")


def github_slug(text: str) -> str:
    """The anchor GitHub gives a heading: rendered text (images dropped, links reduced
    to their text, tags removed), lowercased, filtered by `_slug_char_kept`, each space
    turned into "-" (runs of spaces are not collapsed)."""
    text = _MD_IMAGE_RE.sub("", text)
    text = _MD_LINK_RE.sub(lambda m: m.group(1), text)
    text = re.sub(r"<[^<>]+>", "", text)  # [^<>]: a "<" run stays linear
    return "".join(ch for ch in text.lower() if _slug_char_kept(ch)).replace(" ", "-")


def anchor_targets(headings: list[Heading], content: list[tuple[int, str]]) -> set[str]:
    """Fragments that resolve in this file: heading slugs (a repeated slug gets -1, -2,
    … in document order, the github-slugger loop) and explicit <a id/name> values."""
    targets: set[str] = set()
    occurrences: dict[str, int] = {}
    for h in headings:
        base = slug = github_slug(h.text)
        while slug in occurrences:
            occurrences[base] += 1
            slug = f"{base}-{occurrences[base]}"
        occurrences[slug] = 0
        targets.add(slug)
    for _n, line in content:
        for tag in _HTML_A_TAG_RE.finditer(line):
            targets.update(_attr_value(m.group(1)) for m in _ATTR_ID_NAME_RE.finditer(tag.group(0)))
    return targets


def broken_anchors(links: list[Link], targets: set[str]) -> list[dict]:
    out = []
    for ln in links:
        href = ln.href.strip()
        if not href.startswith("#"):
            continue
        fragment = unquote(href[1:])
        # "#" and "#top" scroll to the top in every browser (HTML spec), heading or not
        if fragment in targets or fragment == "" or fragment.lower() == "top":
            continue
        out.append({"href": ln.href, "line": ln.line})
    return out


# --- evidence sections ------------------------------------------------------- #
def structure(
    headings: list[Heading],
    images: list[Image],
    links: list[Link],
    base_dir: Path,
    anchors: set[str],
) -> dict:
    jumps = []
    prev: int | None = None
    for h in headings:
        if prev is not None and h.level > prev + 1:
            jumps.append({"line": h.line, "from": prev, "to": h.level, "text": h.text})
        prev = h.level
    broken = []
    for href, line in [(ln.href, ln.line) for ln in links] + [(i.src, i.line) for i in images]:
        if _is_external(href):
            continue
        target = unquote(href.split("#", 1)[0].split("?", 1)[0].strip())
        if not target or target.startswith("/"):
            continue
        if not (base_dir / target).exists():
            broken.append({"href": href, "line": line})
    return {
        "h1_count": sum(1 for h in headings if h.level == 1),
        "headings": [{"level": h.level, "text": h.text, "line": h.line} for h in headings],
        "heading_level_jumps": jumps,
        "broken_local_refs": broken,
        "broken_anchors": broken_anchors(links, anchors),
        "images_without_alt": [{"src": i.src, "line": i.line} for i in images if not i.alt.strip()],
    }


def identity_lead(
    content: list[tuple[int, str]], headings: list[Heading], inside: dict[int, bool]
) -> dict:
    h1 = next((h for h in headings if h.level == 1), None)
    if h1 is None:
        return {"present": False, "line": None, "note": "no H1"}
    after = [h for h in headings if h.line > h1.line]
    end_line = after[0].line if after else None
    for line_no, line in content:
        if line_no <= h1.line or (end_line is not None and line_no >= end_line):
            continue
        if inside.get(line_no):
            continue
        if _is_prose_line(line.strip()):
            return {"present": True, "line": line_no}
    return {"present": False, "line": None}


def parse_github_repo(url: str) -> str | None:
    """owner/repo from a GitHub remote URL (https or ssh form); None for anything else."""
    m = _GITHUB_REMOTE_RE.search(url.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def detect_own_repo(directory: Path) -> str | None:
    """owner/repo of the `origin` remote of the git repo holding `directory`.
    Any failure (no git, not a repo, no origin, timeout, non-GitHub host) is None,
    which means no own-repo exclusion rather than an error."""
    try:
        done = subprocess.run(
            ["git", "-C", str(directory), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return parse_github_repo(done.stdout)


def _repo_key(repo: str) -> str:
    """Comparison key for owner/repo: GitHub names are case-insensitive, and a URL
    capture may carry `.git` or a sentence-final dot."""
    return repo.lower().rstrip("./").removesuffix(".git")


def _is_own(repo: str, own_repo: str | None) -> bool:
    return own_repo is not None and _repo_key(repo) == _repo_key(own_repo)


def first_screen(
    content: list[tuple[int, str]],
    headings: list[Heading],
    inside: dict[int, bool],
    own_repo: str | None,
) -> dict:
    """Everything before the first H2 (or the whole file if none)."""
    h2 = next((h for h in headings if h.level == 2), None)
    end = h2.line if h2 else (content[-1][0] + 1 if content else 1)
    lines = [(n, t) for n, t in content if n < end]
    prose = [t for n, t in lines if _is_prose_line(t.strip()) and not inside.get(n)]
    terms: OrderedDict[str, int] = OrderedDict()
    for n, t in lines:
        for _kind, term in formatted_term_spans(t):
            terms.setdefault(term, n)
    repos = {m.group(1) for _, t in lines for m in _GITHUB_REPO_RE.finditer(t)}
    return {
        "end_line": h2.line if h2 else None,
        "lines": end - 1,  # raw lines before the first H2 (fenced blocks included)
        "prose_lines": len(prose),
        "links": sum(len(_MD_LINK_RE.findall(t)) for _, t in lines),
        "new_terms": [{"term": k, "line": v} for k, v in terms.items()],
        "adr_refs": sum(len(_ADR_ID_RE.findall(t)) for _, t in lines),
        "github_repos": sorted(r for r in repos if not _is_own(r, own_repo)),
    }


def insider_refs(content: list[tuple[int, str]], own_repo: str | None) -> dict:
    adr: dict[str, list[int]] = {}
    repos: dict[str, list[int]] = {}
    doc_paths: Counter = Counter()
    dois: dict[str, list[int]] = {}
    for n, t in content:
        for m in _ADR_ID_RE.finditer(t):
            adr.setdefault(f"ADR-{m.group(1)}", []).append(n)
        for m in _GITHUB_REPO_RE.finditer(t):
            if not _is_own(m.group(1), own_repo):
                repos.setdefault(m.group(1), []).append(n)
        for m in _DOC_PATH_RE.finditer(t):
            top = "/".join(m.group(1).split("/")[:2])
            doc_paths[top] += 1
        for m in _DOI_RE.finditer(t):
            dois.setdefault(m.group(0), []).append(n)
    return {
        "adr_total": sum(len(v) for v in adr.values()),
        "adr_unique": len(adr),
        "adr_ids": adr,
        "github_repo_count": len(repos),
        "github_repos": repos,
        "doc_paths": dict(doc_paths),
        "dois": dois,
    }


def formatted_term_spans(text: str) -> Iterator[tuple[str, str]]:
    """Yield (kind, term) for backtick / bold spans that look like names rather than
    paths, flags, labels, links or JA clauses. Shared by first_screen and term_candidates.
    Only formatted spans are candidates: a coined term in plain prose never reaches here
    (NOTES says so to the judge, who finds those)."""
    for kind, rx in (("code", _BACKTICK_RE), ("bold", _BOLD_RE)):
        for m in rx.finditer(text):
            term = m.group(1).strip()
            if "](" in term or term.endswith((":", "：")) or re.search(r"[、。（）]", term):
                continue  # a link, a label, or a JA clause — not a name
            if kind == "code" and (
                "/" in term or term.endswith((".py", ".md", ".json", ".sh", ".txt"))
            ):
                continue  # a path or file name, not a term
            if kind == "code" and (
                term.startswith("-")
                or (" " not in term and not _CAMEL_RE.match(term) and "-" not in term)
            ):
                continue  # a CLI flag, or a single lowercase token
            if kind == "code" and any(tok.startswith("-") or tok == "." for tok in term.split()):
                continue  # a command invocation with flags, not a name
            yield kind, term


def term_candidates(content: list[tuple[int, str]]) -> list[dict]:
    """Backtick / bold spans that look like names rather than code paths.
    Whether a span is a coined term is the judge's call; this only lists them."""
    seen: dict[str, dict] = {}
    for n, t in content:
        for kind, term in formatted_term_spans(t):
            entry = seen.setdefault(term, {"term": term, "kind": kind, "count": 0, "first_line": n})
            entry["count"] += 1
    return sorted(seen.values(), key=lambda e: (-e["count"], e["first_line"]))


def details_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    stack: list[int] = []  # open lines only; the body is sliced on close (no O(N^2) copies)
    raw = markdown.splitlines()
    for n, t in enumerate(raw, start=1):  # raw lines: a fenced BibTeX inside counts
        for _ in _DETAILS_OPEN_RE.findall(t):
            stack.append(n)
        for _ in _DETAILS_CLOSE_RE.findall(t):
            if stack:
                open_line = stack.pop()
                blk = {"open_line": open_line}
                body = "\n".join(raw[open_line - 1 : n])
                summary_m = _SUMMARY_RE.search(body)
                body_wo_summary = _SUMMARY_RE.sub("", body)
                blocks.append(
                    {
                        "open_line": blk["open_line"],
                        "close_line": n,
                        "lines": n - blk["open_line"] + 1,
                        "summary": re.sub(r"<[^>]+>", "", summary_m.group(1)).strip()
                        if summary_m
                        else "",
                        "contains": {
                            "doi": bool(_DOI_RE.search(body_wo_summary)),
                            "bibtex": bool(_BIBTEX_RE.search(body_wo_summary)),
                            "citation": "CITATION" in body_wo_summary.upper(),
                            "image": bool(
                                _MD_IMAGE_RE.search(body_wo_summary)
                                or _HTML_IMG_RE.search(body_wo_summary)
                            ),
                            "code_fence": "```" in body_wo_summary,
                        },
                    }
                )
    for open_line in stack:  # never closed: report, do not guess a body
        blocks.append(
            {
                "open_line": open_line,
                "close_line": None,
                "lines": None,
                "summary": "",
                "unclosed": True,
            }
        )
    return sorted(blocks, key=lambda b: b["open_line"])


def figures(
    markdown: str, images: list[Image], badges: list[Image], headings: list[Heading]
) -> list[dict]:
    all_lines = markdown.splitlines()
    content_map = dict(_content_lines(markdown))  # fenced lines are absent: never prose
    badge_lines = {b.line for b in badges}
    figure_images = [i for i in images if i not in badges]
    # lines that never count as the text equivalent, even when _is_prose_line says yes
    # (a setext heading's text line, a badge row with words, a captioned sibling figure)
    never_prose = {h.line for h in headings} | badge_lines | {i.line for i in figure_images}

    def is_wrapper(n: int) -> bool:
        t = content_map.get(n, "").strip()
        return bool(t) and bool(_TAG_ONLY_RE.match(t)) and not _HTML_IMG_RE.search(t)

    def prose_adjacent(first: int, last: int) -> bool:
        while is_wrapper(first - 1):
            first -= 1
        while is_wrapper(last + 1):
            last += 1
        window = (*range(first - 2, first), *range(last + 1, last + 3))
        return any(
            n not in never_prose and _is_prose_line(content_map.get(n, "").strip()) for n in window
        )

    out: list[dict] = []
    for line, info in _fence_lines(markdown):
        if info.lower().startswith("mermaid"):
            close = line  # the figure spans the opening through the closing fence
            for i in range(line + 1, len(all_lines) + 1):
                if _FENCE_RE.match(all_lines[i - 1]):
                    close = i
                    break
            out.append(
                {"kind": "mermaid", "line": line, "prose_adjacent": prose_adjacent(line, close)}
            )
    for img in figure_images:
        out.append(
            {
                "kind": "image",
                "line": img.line,
                "src": img.src,
                "alt": img.alt,
                "prose_adjacent": prose_adjacent(img.line, img.line),
                "badge_row": img.line in badge_lines,
            }
        )
    return sorted(out, key=lambda f: f["line"])


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


def doi_citation(markdown: str, content: list[tuple[int, str]]) -> dict:
    doi_line = next((n for n, t in content if _DOI_RE.search(t)), None)
    how_to_cite = bool(
        _BIBTEX_RE.search(markdown)
        or _CITATION_AFFORDANCE_RE.search(markdown)
        or _CITE_HEADING_RE.search(markdown)
        or "citation.cff" in markdown.lower()
    )
    return {
        "doi_present": doi_line is not None,
        "doi_first_line": doi_line,
        "how_to_cite_present": how_to_cite,
    }


def collect(path: str, markdown: str, base_dir: Path, own_repo: str | None = None) -> dict:
    """Pure: never touches git. `own_repo` is injected (main detects it)."""
    stripped = _HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), markdown)
    content = _content_lines(stripped)
    headings = parse_headings(stripped)
    images = parse_images(stripped)
    links = parse_links(stripped)
    badges = [i for i in images if _BADGE_SRC_RE.search(i.src)]
    inside = _details_depth_map(content)
    ja = sum(len(_JA_SENTENCE_END_RE.findall(t)) for _, t in content) >= 3
    anchors = anchor_targets(headings, content)
    return {
        "path": path,
        "lang_guess": "ja" if ja else "en",
        "line_count": len(markdown.splitlines()),
        "own_repo": own_repo,
        "structure": structure(headings, images, links, base_dir, anchors),
        "identity_lead": identity_lead(content, headings, inside),
        "first_screen": first_screen(content, headings, inside, own_repo),
        "insider_refs": insider_refs(content, own_repo),
        "term_candidates": term_candidates(content),
        "details_blocks": details_blocks(stripped),
        "figures": figures(stripped, images, badges, headings),
        "badges": {
            "count": len(badges),
            "items": [{"alt": b.alt, "src": b.src, "line": b.line} for b in badges],
        },
        "prose_signals": prose_signals(content),
        "register_ja": register_ja(content, headings) if ja else None,
        "history_signals": history_signals(content),
        "numeric_claims": numeric_claims(content),
        "doi_citation": doi_citation(stripped, content),
        "note": "evidence only — no verdict, no threshold; the judge decides what matters",
        "notes": list(NOTES),
    }


def render_text(ev: dict) -> str:
    ir, fs, st, ps = ev["insider_refs"], ev["first_screen"], ev["structure"], ev["prose_signals"]
    top = ", ".join(f"{t['term']}×{t['count']}" for t in ev["term_candidates"][:8])
    reg = ev["register_ja"]
    lines = [
        f"readme-evidence: {ev['path']} ({ev['lang_guess']}, {ev['line_count']} lines)",
        f"  own repo (excluded from repo counts): {ev['own_repo'] or 'none detected'}",
        (
            f"  first screen: {fs['lines']} lines before first H2, {fs['prose_lines']} prose lines, "
            f"{len(fs['new_terms'])} new terms, {fs['adr_refs']} ADR refs, "
            f"{len(fs['github_repos'])} github repos"
        ),
        (
            f"  insider refs: ADR {ir['adr_total']} (unique {ir['adr_unique']}), "
            f"github repos {ir['github_repo_count']}, doc paths {ir['doc_paths']}"
        ),
        f"  term candidates: {len(ev['term_candidates'])} (top: {top})",
        (
            f"  details blocks: {len(ev['details_blocks'])}; figures: {len(ev['figures'])} "
            f"({sum(1 for f in ev['figures'] if not f['prose_adjacent'])} without adjacent prose); "
            f"badges: {ev['badges']['count']}"
        ),
        (
            f"  prose: slop {len(ps['slop_words'])}, em-dash {ps['em_dash']['count']}, "
            f"history lines {len(ev['history_signals'])}, numeric-claim lines {len(ev['numeric_claims'])}"
        ),
        (
            f"  structure: h1={st['h1_count']}, level jumps={len(st['heading_level_jumps'])}, "
            f"broken local refs={len(st['broken_local_refs'])}, "
            f"broken anchors={len(st['broken_anchors'])}, "
            f"no-alt images={len(st['images_without_alt'])}"
        ),
        (
            f"  identity lead present: {ev['identity_lead']['present']}; "
            f"DOI {ev['doi_citation']['doi_present']} / "
            f"how-to-cite {ev['doi_citation']['how_to_cite_present']}"
        ),
    ]
    if reg is not None:
        lines.append(f"  register (ja): desu_masu {reg['desu_masu']}, plain {reg['plain']}")
    lines += ["", ev["note"]]
    return "\n".join(lines)


def collect_file(path: Path, own_repo: str | None = None) -> dict:
    return collect(str(path), path.read_text(encoding="utf-8"), path.parent, own_repo)


def _own_repo_arg(value: str) -> str | None:
    """--own-repo accepts owner/repo or a GitHub remote URL; "" means none."""
    value = value.strip()
    return (parse_github_repo(value) or value) if value else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("path", type=Path, help="README Markdown file")
    parser.add_argument(
        "--text", action="store_true", help="human-readable summary instead of JSON"
    )
    parser.add_argument(
        "--own-repo",
        metavar="OWNER/REPO",
        default=None,
        help="the README's own GitHub repo (owner/repo or remote URL) instead of reading "
        "`git remote get-url origin`; an empty string means none",
    )
    args = parser.parse_args(argv)
    if not args.path.exists():
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2
    if args.path.stat().st_size > _MAX_BYTES:
        print(f"error: file too large (> {_MAX_BYTES} bytes): {args.path}", file=sys.stderr)
        return 2
    own_repo = (
        detect_own_repo(args.path.parent) if args.own_repo is None else _own_repo_arg(args.own_repo)
    )
    ev = collect_file(args.path, own_repo)
    print(render_text(ev) if args.text else json.dumps(ev, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

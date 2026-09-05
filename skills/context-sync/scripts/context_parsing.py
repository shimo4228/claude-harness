"""Pure parsing for `context_evidence.py` — text in, structured tokens out.

Split out of `context_evidence.py` on 2026-08-28 when the file-LOC budget landed
(ADR-0056; the threshold and the measured distribution are recorded in
`.claude/verify.md`). The seam is the one the file already had: nothing in here
touches the filesystem, the clock, or git, so every function is testable from a
string alone. The corpus shape lives here too because the regexes and the
filename tuples describe the same thing — what this checker considers a document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# --- shape of the corpus ----------------------------------------------------- #

CONTEXT_FILENAMES = (
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    ".windsurfrules",
    ".github/copilot-instructions.md",
)
DOC_DIRS = ("docs",)
PACKAGE_MANIFESTS = ("pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml")
SOURCE_EXTENSIONS = (".py", ".ts", ".tsx", ".go", ".rs", ".swift", ".js")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", "dist", "build"}
# A repo can contain checkouts of itself (`.claude/worktrees/<id>/`). Scanning them
# doubles every context file and turned the duplicate-instruction check into noise
# (measured 2026-08-26: contemplative-agent reported 104 "duplicated" lines, all of
# them one file mirrored inside two worktrees).
# `marketplaces` covers the same class from the other direction: third-party
# plugin checkouts vendored inside the repo. Every one of the harness's 10
# context-path findings came from `plugins/marketplaces/**` — other projects'
# CLAUDE.md files describing their own trees (2026-08-26).
NESTED_CHECKOUT_MARKERS = ("worktrees", "marketplaces")
# Files under a templates/ directory describe *another* repo's layout, so their
# path references are not checkable against this tree (measured: 2 of the harness's
# 3 context-path findings came from templates/hybrid/AGENTS.md).
TEMPLATE_DIRS = ("templates",)

_MAX_FILE_BYTES = 1_000_000  # DoS backstop, not a quality rule
_MAX_ITEMS = 60  # per-check listing cap; `truncated` says when it bit
_MAX_INDEX_ENTRIES = 40_000  # path-index backstop; truncation is reported, never silent
_MAX_LINE_CHARS = 4_000  # per-line cap: the quadratic-regex guard, see _content_lines

# --- regexes ----------------------------------------------------------------- #

_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*(\S*)")
# `(\S.*?)\s*$` is quadratic on a long trailing run of spaces (measured: a
# 200 KB single line took 2m41s inside the 1 MB backstop). Capture greedily and
# rstrip in Python instead.
_HEADING2_RE = re.compile(r"^ {0,3}##\s+(\S.*)")
_INLINE_CODE_RE = re.compile(r"`([^`\n]{1,200})`")
# Bounded like _INLINE_CODE_RE: an unbounded `[^\]]*` is quadratic on a line of
# `[` characters (same measurement).
_MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]{0,200}\]\(\s*([^)\s]+)")
_TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
_ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_SEMVER_RE = re.compile(r"\bv?(\d+\.\d+(?:\.\d+)?)\b")
_VERSION_WORD_RE = re.compile(r"version|バージョン|リリース|release", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*%?")
# Counting nouns that make a number a claim *about this repo* rather than an
# arbitrary figure (version, port, model name, year already stripped elsewhere).
_COUNT_NOUN_RE = re.compile(
    r"\b(files?|tests?|lines?|loc|modules?|packages?|skills?|agents?|rules?|hooks?"
    r"|adrs?|commits?|items?|entries|scripts?|checks?|coverage)\b"
    r"|[件個本行語]|カバレッジ",
    re.IGNORECASE,
)
_TREE_CHARS_RE = re.compile(r"[├└│─]")
# A block is a tree when it draws branches, not merely when it contains a box
# character: flow diagrams ("CLI → Agent.run_session(...)") and prose
# separators use ─ freely and otherwise read as false "unresolved" entries.
# Single character class, no nested quantifier: a nested-quantifier draft
# (`^\s*(?:[│ ]\s*)*├──`) backtracks catastrophically on long indented lines.
_TREE_BRANCH_RE = re.compile(r"^[ \t│]*[├└][─ ]*\S")
_LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_SHELL_LANGS = {"bash", "sh", "shell", "zsh", "console"}
_KNOWN_EXTENSIONS = {
    ".md",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".jsonld",
    ".jsonl",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
    ".cff",
    ".bats",
    ".lock",
    ".rs",
    ".go",
    ".swift",
    ".html",
    ".css",
    ".cfg",
    ".ini",
    ".plist",
    ".ipynb",
    ".sql",
    ".env",
}
_METAVARIABLE_CHARS = set("<>*?{}$|\"'")
# Uppercase placeholder runs stand in for a number or an id in a documented
# convention (`rfcs/NNNN-slug.md`, `docs/evidence/adr-XXXX/`). They are not
# paths, and they were 6 of contemplative-agent's 12 context-path findings
# (2026-08-26).
_PLACEHOLDER_RE = re.compile(r"XXX+|NNN+|YYYY|ZZZ+")
_LEADING_DOTSLASH_RE = re.compile(r"^(?:\./)+")

# The DOI shapes context-sync asks about live in graph.jsonld @id / identifier
# fields; which one is the concept record vs a versioned record is *not*
# decidable from the string, so both are listed and the reviewer decides.
_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>)\]]+")
_URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+")


@dataclass(frozen=True)
class Token:
    line: int
    token: str


@dataclass(frozen=True)
class Marker:
    line: int
    text: str


@dataclass(frozen=True)
class Command:
    line: int
    command: str


@dataclass(frozen=True)
class Version:
    line: int
    version: str


# --- pure parsing ------------------------------------------------------------ #


def _content_lines(markdown: str) -> list[tuple[int, str]]:
    """1-based (lineno, text) for lines outside fenced code blocks."""
    out: list[tuple[int, str]] = []
    in_fence = False
    marker = ""
    for i, line in enumerate(markdown.splitlines(), start=1):
        fence = _FENCE_RE.match(line)
        if fence:
            token = fence.group(1)
            if not in_fence:
                in_fence, marker = True, token
            elif token[0] == marker[0] and len(token) >= len(marker):
                # A ```` fence exists precisely to *show* a ``` block; collapsing
                # every delimiter to three let the inner one close the outer.
                in_fence = False
            continue
        if not in_fence:
            # Truncating a pathological line is the last line of defence for the
            # per-line regexes; the byte cap alone does not bound line length.
            out.append((i, line[:_MAX_LINE_CHARS]))
    return out


def fenced_blocks(markdown: str) -> list[tuple[str, list[tuple[int, str]]]]:
    """[(language, [(lineno, text), ...]), ...] for each fenced block."""
    blocks: list[tuple[str, list[tuple[int, str]]]] = []
    in_fence = False
    marker = ""
    lang = ""
    body: list[tuple[int, str]] = []
    for i, line in enumerate(markdown.splitlines(), start=1):
        fence = _FENCE_RE.match(line)
        if fence:
            token = fence.group(1)
            if not in_fence:
                in_fence, marker, lang, body = True, token, fence.group(2).lower(), []
            elif token[0] == marker[0] and len(token) >= len(marker):
                blocks.append((lang, body))
                in_fence = False
            continue
        if in_fence:
            body.append((i, line))
    if in_fence and body:
        # An unterminated fence used to drop its whole block — every command in it
        # vanished and the reviewer read the empty result as "no stale examples".
        blocks.append((lang, body))
    return blocks


def _is_path_shaped(token: str) -> bool:
    if not token or token.startswith(("http://", "https://", "mailto:", "#")):
        return False
    if any(ch in _METAVARIABLE_CHARS for ch in token):
        return False
    if _PLACEHOLDER_RE.search(token):
        return False
    if token.startswith(("~", "/")):  # outside the repo under inspection
        return False
    if "/" not in token:
        return False
    if token.endswith("/"):
        return True
    suffix = Path(token).suffix.lower()
    return suffix in _KNOWN_EXTENSIONS


def path_tokens(markdown: str) -> list[Token]:
    """Repo-relative path references from inline code spans and Markdown links.

    Multi-word code spans (`bash hooks/x.sh`) are split so a command's argument
    is still checked. Globs, metavariables (`<name>`), URLs, absolute and
    `~`-prefixed paths are excluded — none of them is decidable against this
    repo's tree, and a false "missing" is worse than a silent skip here.
    """
    seen: set[tuple[int, str]] = set()
    found: list[Token] = []
    for lineno, text in _content_lines(markdown):
        candidates: list[str] = []
        for span in _INLINE_CODE_RE.findall(text):
            words = span.split()
            # `~/Library/Mobile Documents/…/Obsidian Vault/wiki/concept/` is ONE
            # path containing spaces; word-splitting it produced a fragment that
            # sailed past the `~` exclusion and became a false "missing"
            # (authorship-strategy, 2026-08-26).
            if any(w.startswith(("~", "/")) for w in words):
                continue
            candidates.extend(words)
        for href in _MD_LINK_RE.findall(text):
            candidates.append(href.split("#", 1)[0])
        for raw in candidates:
            token = raw.strip().strip(",;:)（）「」").rstrip(".")
            if _is_path_shaped(token) and (lineno, token) not in seen:
                seen.add((lineno, token))
                found.append(Token(lineno, token))
    return found


def _is_link_target(token: str) -> bool:
    """A Markdown link target that names a file in this repo.

    Looser than `_is_path_shaped`: an explicit link to a root-level file
    (`[guide](GUIDE.md)`) has no `/` and would otherwise be dropped, leaving a
    broken llms.txt link invisible to a gated check (codex-review P2).
    """
    if _is_path_shaped(token):
        return True
    if not token or token.startswith(("http://", "https://", "mailto:", "#", "~", "/")):
        return False
    if any(ch in _METAVARIABLE_CHARS for ch in token) or _PLACEHOLDER_RE.search(token):
        return False
    return Path(token).suffix.lower() in _KNOWN_EXTENSIONS


def md_link_paths(markdown: str) -> list[Token]:
    """Local Markdown link targets (no inline code).

    The llms.txt check in the skill is about *links that resolve*; inline code
    spans there are prose mentions of modules and were the entire content of the
    13 "broken links" this reported for contemplative-agent before the split.
    """
    out: list[Token] = []
    for lineno, text in _content_lines(markdown):
        for href in _MD_LINK_RE.findall(text):
            token = href.split("#", 1)[0].strip()
            if _is_link_target(token):
                out.append(Token(lineno, token))
    return out


def md_link_targets(markdown: str) -> list[str]:
    """*Every* Markdown link destination, local or external.

    `md_link_paths` filters to targets this repo can resolve; counting outbound
    links for the llms-full.txt self-containment judgment needs the unfiltered
    total, or a document that links only to URLs reports zero (codex-review P2).
    """
    return [
        href.split("#", 1)[0].strip()
        for _, text in _content_lines(markdown)
        for href in _MD_LINK_RE.findall(text)
    ]


def todo_markers(markdown: str) -> list[Marker]:
    return [
        Marker(lineno, text.strip())
        for lineno, text in _content_lines(markdown)
        if _TODO_RE.search(text)
    ]


def h2_topics(markdown: str, limit: int | None = None) -> list[str]:
    topics = [
        m.group(1).rstrip()
        for _, text in _content_lines(markdown)
        if (m := _HEADING2_RE.match(text))
    ]
    return topics[:limit] if limit is not None else topics


def topic_overlap_ratio(a: list[str], b: list[str]) -> float:
    """Shared-topic fraction over the larger set (0.0 when either side is empty)."""
    sa = {t.strip().casefold() for t in a if t.strip()}
    sb = {t.strip().casefold() for t in b if t.strip()}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa), len(sb))


def numeric_claim_lines(markdown: str) -> list[Marker]:
    """Prose lines whose number is a *claim about the repo* — candidate stale counts.

    "Any line with a digit" was the first cut and it is useless: it matched 10,176
    lines in contemplative-agent (2026-08-26), i.e. most of the corpus. The claim
    the checklist cares about is a count of things in this repo, so the line must
    also carry a counting noun or a percent sign.
    """
    out: list[Marker] = []
    for lineno, text in _content_lines(markdown):
        stripped = _ISO_DATE_RE.sub("", text)
        body = _LIST_MARKER_RE.sub("", stripped)
        if not _NUMBER_RE.search(body):
            continue
        if "%" in body or _COUNT_NOUN_RE.search(body):
            out.append(Marker(lineno, text.strip()))
    return out


def cli_example_candidates(markdown: str) -> list[Command]:
    """Shell lines from fenced blocks. Listed only — this script never runs them."""
    out: list[Command] = []
    for lang, body in fenced_blocks(markdown):
        if lang not in _SHELL_LANGS:
            continue
        for lineno, raw in body:
            text = raw.strip()
            if not text or text.startswith("#"):
                continue
            out.append(Command(lineno, text.removeprefix("$ ").strip()))
    return out


def normalized_instructions(markdown: str) -> list[str]:
    """Instruction lines flattened so cosmetic differences don't hide duplicates."""
    out: list[str] = []
    for _, text in _content_lines(markdown):
        line = _LIST_MARKER_RE.sub("", text)
        line = re.sub(r"[*_`]", "", line)
        line = re.sub(r"\s+", " ", line).strip().casefold()
        if len(line) >= 12:
            out.append(line)
    return out


def version_mentions(markdown: str) -> list[Version]:
    """Version-looking tokens that the text itself frames as a version.

    A bare `3.11` is a Python requirement, a threshold, or a section number far
    more often than it is this package's version — matching every semver-shaped
    token produced 2,270 "mismatches" in contemplative-agent (2026-08-26). A
    `v`-prefix or the word "version" on the line is the discriminator.
    """
    out: list[Version] = []
    for lineno, text in _content_lines(markdown):
        line = _ISO_DATE_RE.sub("", text)
        framed = _VERSION_WORD_RE.search(line) is not None
        for m in _SEMVER_RE.finditer(line):
            if m.group(0).startswith("v") or framed:
                out.append(Version(lineno, m.group(1)))
    return out


def tree_block_paths(markdown: str) -> list[str]:
    """Path-ish entries from ASCII tree blocks (`├──` style) in documentation."""
    out: list[str] = []
    for _, body in fenced_blocks(markdown):
        branches = [raw for _, raw in body if _TREE_BRANCH_RE.match(raw)]
        if len(branches) < 2:
            continue
        for _, raw in body:
            entry = _TREE_CHARS_RE.sub(" ", raw).strip()
            entry = entry.split("#", 1)[0].split("  ")[0].strip()
            if not entry or entry.startswith("."):
                continue
            if " " in entry or "(" in entry or "→" in entry:
                continue  # prose or a call signature, not a filename
            out.append(entry)
    return out

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
from pathlib import Path

# One responsibility per sibling module (file-LOC budget, ADR-0056): readme_md parses
# Markdown structure, readme_sections builds the structural sections, readme_prose the
# prose-level ones. This file owns the JSON contract (docstring + NOTES), git origin
# detection, the assembly in `collect`, the text rendering and the CLI. Callers and
# tests address this one module: the names they import are re-exported (__all__).
if __package__:
    from . import readme_md as _md
    from . import readme_prose as _prose
    from . import readme_sections as _sec
else:  # Support the documented direct script invocation.
    import readme_md as _md
    import readme_prose as _prose
    import readme_sections as _sec

_content_lines = _md._content_lines
_details_depth_map = _md._details_depth_map
anchor_targets = _md.anchor_targets
github_slug = _md.github_slug
parse_headings = _md.parse_headings
parse_images = _md.parse_images
parse_links = _md.parse_links
_JA_SENTENCE_END_RE = _prose._JA_SENTENCE_END_RE
history_signals = _prose.history_signals
numeric_claims = _prose.numeric_claims
prose_signals = _prose.prose_signals
register_ja = _prose.register_ja
details_blocks = _sec.details_blocks
doi_citation = _sec.doi_citation
figures = _sec.figures
first_screen = _sec.first_screen
formatted_term_spans = _sec.formatted_term_spans
identity_lead = _sec.identity_lead
insider_refs = _sec.insider_refs
structure = _sec.structure
term_candidates = _sec.term_candidates

__all__ = [
    "collect",
    "collect_file",
    "details_blocks",
    "detect_own_repo",
    "formatted_term_spans",
    "github_slug",
    "main",
    "parse_github_repo",
    "parse_headings",
    "parse_images",
    "parse_links",
    "render_text",
]

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_BADGE_SRC_RE = re.compile(
    r"shields\.io|/badge|badge\.svg|badgen\.net|deepwiki|gitmcp|zenodo\.org/badge"
    r"|codecov|coveralls|circleci|travis-ci|app\.netlify\.com/.*deploy-status",
    re.IGNORECASE,
)
# owner/repo from a git remote: https://[user@]github.com/o/r[.git][/],
# git@github.com:o/r[.git], ssh://git@[ssh.]github.com[:port]/o/r[.git]
_GITHUB_REMOTE_RE = re.compile(
    r"(?:^|[/@.])github\.com[:/](?:\d+/)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
_GIT_TIMEOUT_S = 2

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

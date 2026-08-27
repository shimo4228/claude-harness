"""Overlap candidates for a learn-eval draft — enumeration, never a verdict.

learn-eval's grounding checklist asked two questions a checklist cannot verify:
"Grepped ~/.claude/skills/ for keywords and checked for content overlap" and
"Checked for overlap with MEMORY.md". Both are *self-reports* — the answer is
always yes, and nothing in the output shows what was actually compared. This
script replaces the reporting with the artefact: the draft's own terms, scored
against every installed skill description and every MEMORY.md index line, with
line numbers. The question that survives is the one only a reader can answer —
"is this candidate really the same knowledge?" (learn-eval Step 5b).

Output contract (same as adr_lint.py / readme_evidence.py / agent_evidence.py):
JSON on stdout, exit 0 however many candidates are found, exit 2 only when an
input cannot be read. No verdict field exists, by design.

Scope note — why the *description* and not the body. A future session reaches a
skill through the always-loaded listing, which carries the description alone.
A body-text match would rank a skill the model will never be routed to, which
is the opposite of what the checklist item is for.

Relation to skill-stocktake Phase 3. Both compare descriptions to find
duplication, but the shapes differ: Phase 3 is N×N clustering over the whole
library (a set property, judged by a dedicated agent), while this is 1×N — one
draft against the library. The shapes do not compose, so nothing is shared with
it.

Shared with skills/agent-stocktake/scripts/agent_evidence.py, by copy: the file
reader (`_MAX_FILE_BYTES`, `_read_text`), the frontmatter reader
(`split_frontmatter`, `_BLOCK_SCALAR_RE`, `front_scalar`) and the tokenizer
(`_WORD_RE`, `_STOPWORD_TEXT`, `normalize_terms`) — about 70 lines, not the
"~15-line tokenizer" an earlier version of this note claimed. Copied rather than
imported because the two uv sub-projects are independent and both declare
`dependencies = []`; per feedback: duplicate_over_coordination and the precedent
of skill-health/scripts/scan_refs.py ("mirrored from readme_evidence.py").

Those blocks are byte-identical and must stay so. The one deliberate difference
is `_PROSE_STOPWORDS` below, which exists only here — see its comment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_MAX_FILE_BYTES = 1_000_000  # DoS backstop, not a quality rule

# Interior `.`/`-`/`+`/`#` carry meaning ("adr-writer", "c++", "readme.md");
# trailing ones are sentence punctuation and must not survive into the term set.
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9+#.-]*")
_STOPWORD_TEXT = """a an and are as at be by for from in into is it its of on or that
the this to use used user when with without you your do does not nor but"""
# Extra fillers that only a multi-paragraph draft produces. They are NOT in the
# agent_evidence twin on purpose: that script compares one-sentence descriptions
# to each other, and its `DEFAULT_DUP_THRESHOLD` is calibrated on the base list
# above. Adding these there moves its top measured pair 0.525 -> 0.517 and
# narrows the gap the threshold sits in, so the two lists are deliberately
# different — do not "sync" them without re-measuring that threshold.
_PROSE_STOPWORDS = """how what these those there here also more most any all one
two some such"""
_STOPWORDS = frozenset(_STOPWORD_TEXT.split()) | frozenset(_PROSE_STOPWORDS.split())

# A MEMORY.md index line: "- [Title](file.md) — hook". Only index lines are
# compared — MEMORY.md's own prose headers are structure, not knowledge.
_MEMORY_LINE_RE = re.compile(r"^\s*[-*]\s+")

DEFAULT_TOP_N = 5

# Japanese carries no spaces, so a word regex extracts nothing from it and a
# Japanese-only description, draft or MEMORY.md line would score zero against
# everything — reported as "no overlap", which is the silent-false-negative this
# whole change exists to remove (2026-08-26 cross-model review). Character
# bigrams over each CJK run are the standard tokenizer-free stand-in. Measured
# over the 25-agent corpus, adding them left the two top pairs and therefore the
# calibrated gap unchanged (0.525 / 0.319).
_CJK_RUN_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]{2,}")


def normalize_terms(text: str) -> frozenset[str]:
    """Content terms, case- and punctuation-insensitive, ASCII words + CJK bigrams."""
    words = (w.rstrip(".-") for w in _WORD_RE.findall(text.lower()))
    terms = {w for w in words if w and w not in _STOPWORDS}
    for run in _CJK_RUN_RE.findall(text):
        terms |= {run[i : i + 2] for i in range(len(run) - 1)}
    return frozenset(terms)


def count_concepts(shared: frozenset[str] | set[str], text: str) -> int:
    """How many distinct *ideas* `shared` represents inside `text`.

    Not `len(shared)`. A CJK word of n characters contributes n-1 bigrams, so one
    incidental katakana word looks like six shared terms — enough to clear a
    floor meant to require two independent concepts and to outrank a real match
    on count. Measured 2026-08-26: a draft's true home in MEMORY.md fell to rank
    3 behind 「パーミッション」 alone, and adding two more ordinary Japanese words
    pushed it out of the results entirely.

    Counted against the candidate's own text rather than by chaining bigrams:
    each CJK run in `text` is one concept if any of its bigrams is shared, which
    is exact where chaining is only a heuristic (an intersection leaves gaps in
    the chain, so 「パーミッション」 scored 3 instead of 1). ASCII terms count once
    each.
    """
    concepts = sum(1 for t in shared if t.isascii())
    for run in _CJK_RUN_RE.findall(text):
        if any(run[i : i + 2] in shared for i in range(len(run) - 1)):
            concepts += 1
    return concepts


def _read_text(path: Path) -> tuple[str | None, str]:
    """Return (text, reason). `reason` is "ok" or names why the read failed.

    Callers must distinguish absent / unreadable / too-big / mis-encoded from
    "read fine and found nothing" — collapsing them is how an evidence script
    issues a clean bill for a file it never saw. `errors="strict"` is part of
    that: `errors="replace"` turns a latin-1 file into mojibake that tokenizes
    to nothing and reports as successfully read.
    """
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None, "too-big"
        raw = path.read_bytes()
    except OSError:
        return None, "unreadable"
    try:
        # A leading BOM survives str.strip() and would defeat the `---` check.
        return raw.decode("utf-8").lstrip("\ufeff"), "ok"
    except UnicodeDecodeError:
        return None, "bad-encoding"


_BLOCK_SCALAR_RE = re.compile(r"^[|>][+-]?\d*$")


def front_scalar(lines: list[str], key: str) -> str | None:
    """A frontmatter scalar, including YAML block scalars.

    `description: >-` followed by indented continuation lines is in live use
    (skills/paper-deposit/SKILL.md, 2026-08-26). Read naively the value is ">-",
    which normalizes to no terms at all and drops that file out of every
    comparison silently — so the block form is folded here rather than left to
    a YAML parser (this code must also survive frontmatter that does not parse;
    scripts/hooks/harness_lint.py owns reporting that).
    """
    prefix = f"{key}:"
    for i, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        value = line[len(prefix) :].strip()
        if _BLOCK_SCALAR_RE.match(value):
            block: list[str] = []
            for follow in lines[i + 1 :]:
                if follow.strip() and not follow[:1].isspace():
                    break  # back at indent 0 — the next key
                block.append(follow.strip())
            return " ".join(part for part in block if part)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value
    return None


def split_frontmatter(text: str) -> list[str]:
    """Frontmatter lines only, or [] when there is no closed frontmatter.

    Fails **closed**: an earlier inlined variant left `lines` as the whole file
    when the opening or closing `---` was missing, so `front_scalar` went on to
    match a body line beginning `description:` and returned body prose as the
    description. Byte-compatible with the twin in agent_evidence.py, which
    additionally returns the body and its offset (not needed here).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return []


def _description_of(skill_md: Path) -> tuple[str, str]:
    text, reason = _read_text(skill_md)
    if text is None:
        return "", reason
    description = front_scalar(split_frontmatter(text), "description")
    if not description:
        # Unterminated frontmatter and a genuinely empty description both land
        # here; either way the skill was not compared, and saying so beats
        # letting it sit in the corpus scoring zero.
        return "", "no-description"
    return description, "ok"


def read_skill_descriptions(skills_root: Path) -> tuple[dict[str, str], list[dict]]:
    """`(name -> description, problems)` for every installed skill.

    The second half is the point: this script answers "does an existing skill
    already say this?", and the skills it fails to read are correlated with the
    answer — one mid-edit, or behind a dangling symlink, is exactly the one
    somebody is about to duplicate. A skill that could not be compared must not
    be indistinguishable from one that scored zero.

    Symlinked skill directories are included: they occupy the same listing and
    therefore compete for the same trigger, whoever owns the files. `is_dir()`
    follows symlinks, so it admits them without a separate `is_symlink()` arm.
    """
    out: dict[str, str] = {}
    problems: list[dict] = []
    for entry in sorted(skills_root.iterdir()):
        if not entry.is_dir():
            # A dangling symlink (a skill whose package was uninstalled) lands
            # here. harness_lint.py reports these explicitly; dropping them
            # silently would shrink the corpus with no trace.
            if entry.is_symlink():
                problems.append({"skill": entry.name, "reason": "dangling-symlink"})
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            problems.append({"skill": entry.name, "reason": "no-SKILL.md"})
            continue
        description, reason = _description_of(skill_md)
        if reason != "ok":
            problems.append({"skill": entry.name, "reason": reason})
            continue
        out[entry.name] = description
    return out, problems


def _containment(draft_terms: frozenset[str], other: frozenset[str]) -> float:
    """Share of the *candidate's* terms the draft also uses.

    Containment rather than Jaccard: a draft is a few paragraphs and a
    description is one sentence, so Jaccard's union is dominated by the draft
    and scores every real twin near zero. Containment asks the question the
    checklist actually asked — "does an existing skill already say this?"
    """
    if not other:
        return 0.0
    return len(draft_terms & other) / len(other)


def score_candidates(
    draft: str, descriptions: dict[str, str], top_n: int = DEFAULT_TOP_N
) -> tuple[list[dict], int]:
    draft_terms = normalize_terms(draft)
    scored: list[dict] = []
    for name, description in descriptions.items():
        terms = normalize_terms(description)
        shared = draft_terms & terms
        if not shared:
            continue
        scored.append(
            {
                "skill": name,
                "score": round(_containment(draft_terms, terms), 3),
                "shared_terms": sorted(shared),
                "description": description,
            }
        )
    scored.sort(key=lambda c: (-c["score"], c["skill"]))
    # The total travels with the slice: without it a reader cannot tell whether
    # the list was bounded or was simply that short.
    return scored[:top_n], len(scored)


# Measured in *concepts* (see `count_concepts`), never in raw terms.
# A MEMORY.md index line carries 3-8 terms, so `_containment` — which divides by
# the candidate's term count — gives a single incidental word a score that
# outranks real matches (measured 2026-08-26 against the live global MEMORY.md:
# a one-term hit on 'tool' scored 0.167, beating two genuine one-term matches,
# while the line that actually held the draft's knowledge shared four terms).
# Requiring two shared terms separates them cleanly: in that run the true match
# had 4, every false one had exactly 1.
MIN_SHARED_MEMORY_TERMS = 2


def memory_matches(
    draft: str, memory_files: list[Path], top_n: int = DEFAULT_TOP_N
) -> tuple[list[dict], list[str], list[dict], int]:
    """Return (hits, files actually read, files that failed, total before top_n).

    The "actually read" list is separate from `is_file()` on purpose: a memory
    file that exists but cannot be decoded produced an empty candidate list
    beside a `memory_files_read` that named it, so the SKILL.md guard ("read is
    empty and missing is not") could not fire and the reader wrote "MEMORY.md
    checked, no overlap" — the self-report this script replaces, now with a JSON
    artefact behind it.
    """
    draft_terms = normalize_terms(draft)
    hits: list[dict] = []
    read: list[str] = []
    failed: list[dict] = []
    for path in memory_files:
        text, reason = _read_text(path)
        if text is None:
            failed.append({"file": str(path), "reason": reason})
            continue
        read.append(str(path))
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not _MEMORY_LINE_RE.match(line):
                continue
            terms = normalize_terms(line)
            shared = draft_terms & terms
            if count_concepts(shared, line) < MIN_SHARED_MEMORY_TERMS:
                continue
            hits.append(
                {
                    "file": str(path),
                    "line": lineno,
                    "score": round(_containment(draft_terms, terms), 3),
                    "shared_terms": sorted(shared),
                    "shared_concepts": count_concepts(shared, line),
                    "text": line.strip(),
                }
            )
    hits.sort(key=lambda h: (-h["shared_concepts"], -h["score"], h["file"], h["line"]))
    return hits[:top_n], read, failed, len(hits)


def derive_memory_path(project: Path, home: Path | None = None) -> Path:
    """`~/.claude/projects/<slug>/memory` for a project path.

    Claude Code slugifies the absolute project path by replacing "/", "." and
    "_" with "-" (verified against the live tree on 2026-08-26). Derived rather
    than globbed: the tree holds one directory per project the user has ever
    opened, and globbing them all would drag another project's memory into this
    draft's overlap set.
    """
    home = home or Path.home()
    slug = re.sub(r"[/._]", "-", str(project))
    return home / ".claude" / "projects" / slug / "memory" / "MEMORY.md"


def discover_memory_files(project: Path, home: Path | None = None) -> tuple[list[Path], list[Path]]:
    """Project **and** global memory — the checklist item said "(project + global)".

    Deriving only the current project's slug made the harness-level MEMORY.md
    unreachable from any other repo: measured on 2026-08-26, running from
    ~/MyAI_Lab/contemplative-agent hid the record that actually held the draft's
    knowledge, and "no candidate above the floor" then reads as verified. A
    mechanised check that covers less than the self-report it replaced is worse
    than the self-report.

    Returns (found, missing). `missing` is reported in the JSON so the failure is
    not silent: if Claude Code changes its project-slug convention, the derived
    paths stop existing and the comparison quietly finds nothing — a
    `memory_files_read` that is empty while `memory_files_missing` is not is the
    observable form of that.
    """
    home = home or Path.home()
    candidates = [
        project / "MEMORY.md",
        derive_memory_path(project, home),
        derive_memory_path(home / ".claude", home),
    ]
    found: list[Path] = []
    missing: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        (found if path.is_file() else missing).append(path)
    return found, missing


def collect_evidence(
    draft: str,
    skills_root: Path,
    memory_files: list[Path],
    top_n: int = DEFAULT_TOP_N,
    memory_files_missing: list[Path] | None = None,
) -> dict:
    descriptions, unscannable = read_skill_descriptions(skills_root)
    skill_hits, skill_total = score_candidates(draft, descriptions, top_n)
    memory_hits, memory_read, memory_failed, memory_total = memory_matches(
        draft, memory_files, top_n
    )
    return {
        "skills_root": str(skills_root),
        "skills_scanned": len(descriptions),
        "skills_unscannable": unscannable,
        "draft_terms_total": len(normalize_terms(draft)),
        "memory_files_read": memory_read,
        "memory_files_missing": [str(p) for p in memory_files_missing or []],
        "memory_files_unreadable": memory_failed,
        "top_n": top_n,
        "skill_candidates": skill_hits,
        "skill_candidates_total": skill_total,
        "memory_candidates": memory_hits,
        "memory_candidates_total": memory_total,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--draft", default=None, help="draft file (default: read stdin)")
    parser.add_argument(
        "--skills-root",
        default=str(Path("~/.claude/skills").expanduser()),
        help="installed-skill root to compare against",
    )
    parser.add_argument(
        "--memory",
        action="append",
        default=[],
        metavar="FILE",
        help="MEMORY.md to compare against (repeatable)",
    )
    parser.add_argument(
        "--project",
        default=".",
        help="project root used to locate its MEMORY.md files (default: cwd)",
    )
    parser.add_argument(
        "--no-auto-memory",
        action="store_true",
        help="do not derive MEMORY.md paths from --project",
    )
    args = parser.parse_args(argv)

    if args.draft:
        draft, reason = _read_text(Path(args.draft).expanduser())
        if draft is None:
            print(f"overlap_candidates: cannot read {args.draft} ({reason})", file=sys.stderr)
            return 2
    else:
        draft = sys.stdin.read()

    if not normalize_terms(draft):
        # Zero comparable terms means nothing was compared. Reporting "no
        # candidates" for a truncated or mis-pathed draft is the false clean
        # bill this script exists to prevent, so it is an input error.
        print("overlap_candidates: draft has no comparable terms", file=sys.stderr)
        return 2

    skills_root = Path(args.skills_root).expanduser()
    if not skills_root.is_dir():
        print(f"overlap_candidates: {skills_root} is not a directory", file=sys.stderr)
        return 2

    memory_files = [Path(m).expanduser() for m in args.memory]
    # A derived path that does not exist is evidence (reported in
    # `memory_files_missing`); an *explicitly named* one that does not exist is
    # an input error, and swallowing it would report "no overlap" for a typo.
    for named in memory_files:
        if not named.is_file():
            print(f"overlap_candidates: cannot read {named}", file=sys.stderr)
            return 2
    memory_missing: list[Path] = []
    if not args.no_auto_memory:
        project = Path(args.project).expanduser().resolve()
        found, memory_missing = discover_memory_files(project)
        resolved = {p.resolve() for p in memory_files}
        memory_files += [p for p in found if p.resolve() not in resolved]

    json.dump(
        collect_evidence(draft, skills_root, memory_files, memory_files_missing=memory_missing),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

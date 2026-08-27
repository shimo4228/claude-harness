"""Deterministic evidence for an agent-definition stocktake — never a verdict.

This script owns the *mechanical* half of agent-stocktake Phase 1 (the code side
of "existence = code, content = LLM", ADR-0021 / ADR-0044, generalized by skill:
review-to-lint). It measures and enumerates; every judgment — is this overlap
real, is this line actually a suppression instruction, does this agent still earn
its residency — stays with the skill's LLM phases.

Deliberately NOT covered here (already owned elsewhere; re-implementing them
would create the drift the split exists to avoid):

  * frontmatter presence of `name` / `description` / `origin` / `model`, and
    model-alias conformance  -> scripts/hooks/harness_lint.py `lint_agents`
  * resolution of Markdown links inside agents/*.md
                             -> scripts/hooks/harness_lint.py `lint_markdown_links`
                                (its LINK_SCOPES already includes "agents")
  * dangling `python -m scripts.X` / `bash …/foo.sh` / named-skill references
                             -> skills/skill-health/scripts/scan_refs.py, whose
                                scan root is the *skills* tree; bare-path prose
                                references inside agents/ remain uncovered by
                                both and are left to the LLM pass on purpose.

Output contract (same as readme_evidence.py / adr_lint.py): JSON on stdout,
exit 0 no matter how many findings, exit 2 only when the corpus cannot be read.
There is no --gate: a stocktake is a periodic audit, not a commit-boundary check
(ADR-0051 rejected wiring this class of lint into verify.sh / commit hooks).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- tool registry

# Built-in tool names, as-of 2026-08-26.
#
# This list is *data with an expiry*, and the expiry is not hypothetical: an
# altitude review on 2026-08-26 found eight names already missing from the
# stamped list (EnterWorktree, ExitWorktree, Task{Create,Get,List,Update,Output,
# Stop}) — they were added below, but the next eight will go unnoticed the same
# way. A built-in tool's existence is not observable from disk; the only holder
# of the true registry is the *reading* LLM, which has its own tool list in
# context.
#
# So a name absent from this list is reported as `unverified`, never `unknown`:
# the script is saying "not in my dated list", not "does not exist". The SKILL.md
# step that consumes this is required to confirm an `unverified` against the
# reader's own registry before treating it as evidence — otherwise a stale list
# drives an edit that strips a valid tool from a correct agent. `--known-tools
# FILE` (one name per line) replaces the list wholesale.
BUILTIN_TOOLS_AS_OF = "2026-08-26"
BUILTIN_TOOLS = frozenset(
    {
        "Agent",
        "AskUserQuestion",
        "Artifact",
        "Bash",
        "BashOutput",
        "Edit",
        "EnterPlanMode",
        "EnterWorktree",
        "ExitPlanMode",
        "ExitWorktree",
        "Glob",
        "Grep",
        "KillShell",
        "ListMcpResourcesTool",
        "Monitor",
        "NotebookEdit",
        "Read",
        "ReadMcpResourceTool",
        "ReportFindings",
        "SendMessage",
        "Skill",
        "SlashCommand",
        "Task",
        "TaskCreate",
        "TaskGet",
        "TaskList",
        "TaskOutput",
        "TaskStop",
        "TaskUpdate",
        "TodoWrite",
        "ToolSearch",
        "WebFetch",
        "WebSearch",
        "Workflow",
        "Write",
    }
)

_MCP_TOOL_RE = re.compile(r"^mcp__([^_]+(?:_[^_]+)*)__(.+)$")

# MCP server configuration, in the order Claude Code layers it. Reported as
# provenance, with a per-source read/parse status.
#
# These files are NOT the whole registry: a server supplied by a connector never
# appears in any of them (measured 2026-08-26 — six namespaces live in the
# session, including claude_ai_Slack, are absent here). So a server missing from
# this set is "not in the local config", never "retired", and the field is named
# `server_in_config` to stop the SKILL.md step from reading it as a verdict.
#
# Note the mixed roots: the agents directory is --root-relative, these two are
# absolute (this machine's home). They coincide only when --root is ~/.claude.
# Point --root at another checkout and `server_in_config` describes *this*
# machine's MCP setup, not that repo's — which is why the resolved paths and
# their statuses are emitted as `registry.mcp_config_files`.
_MCP_CONFIG_CANDIDATES = (
    Path.home() / ".claude.json",
    Path.home() / ".claude" / ".mcp.json",
)

# --------------------------------------------------------- suppression catalog

# Every pattern below is grounded in a line that exists in the real corpus. The
# catalog was measured against all 25 files of ~/.claude/agents on 2026-08-26 and
# then cut down by that measurement:
#
#   confidence-discard-ja  security-reviewer.md L91 — 「残った指摘に確信度を付け、
#                          低いものは捨てる」. The corpus's one unambiguous
#                          suppression instruction, and the reason the catalog is
#                          bilingual — agent-stocktake's prose checklist named
#                          only English phrasings and would have found nothing.
#   be-conservative        refactor-cleaner.md L75 — "**Be conservative**".
#   report-exclusion-ja    security-reviewer.md L82-84 — 「… は報告しない」, three
#                          scope exclusions that carry their own counter-argument
#                          two lines below. Legitimately surfaced, resolved by
#                          reading them: exactly the enumerate/decide case.
#   confidence-threshold   No corpus hit. Kept because agent-stocktake Phase 2
#   severity-floor         Stage 1 names these two phrasings by example, so their
#                          absence from the catalog would make the script and the
#                          question disagree.
#
# Cut on the same measurement, after an architect review flagged the catalog's
# precision: `only-report` (fact-checker.md L164, readme-reviewer.md L13 — both
# describing an agent's own output contract, never a suppressed finding) and the
# 「に限定」 alternative of report-exclusion-ja (readme-judge.md L79, scoping the
# agent's evaluation). Yield went from 1 real finding in 8 candidates to 1 in 5.
# A pattern that has produced only false positives is a pattern that trains the
# reader to skim the list.
SUPPRESSION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "confidence-threshold",
        re.compile(
            r"(?:≥|>=|at least|only|minimum(?: of)?)[^.\n]{0,40}\d{1,3}\s?%"
            r"|\d{1,3}\s?%[^.\n]{0,20}(?:sure|confident|confidence)",
            re.IGNORECASE,
        ),
    ),
    (
        "severity-floor",
        re.compile(
            r"only[^.\n]{0,30}\b(?:high|critical|severe)[- ]?(?:severity)?\b"
            r"|\b(?:high|critical)[- ]severity\b[^.\n]{0,20}\bonly\b"
            r"|severity floor",
            re.IGNORECASE,
        ),
    ),
    (
        "be-conservative",
        re.compile(r"\bbe conservative\b|\berr on the side of caution\b", re.IGNORECASE),
    ),
    ("confidence-discard-ja", re.compile(r"確信度|自信のあるものだけ|低いものは捨て")),
    ("report-exclusion-ja", re.compile(r"報告しない|指摘しない|だけ報告|のみ報告")),
)

# ALWAYS / NEVER / MUST NOT as standalone upper-case tokens, scanned over the
# **body only** — a description is a delegation trigger, not an instruction to
# the agent, so `MUST BE USED` in agents/swift-reviewer.md L3 is out of scope by
# design (description quality is the near-duplicate check's job). That leaves
# exactly one candidate in the 2026-08-26 corpus, agents/prompt-writer.md L19,
# and it is *quoted vocabulary* rather than a directive — enumerated, not judged.
_ALWAYS_NEVER_RE = re.compile(r"(?<![A-Za-z])(ALWAYS|NEVER|MUST NOT|MUST)(?![A-Za-z])")

AGENTS_DIR = "agents"

_MAX_FILE_BYTES = 1_000_000  # DoS backstop, not a quality rule

# `.`/`-`/`+`/`#` are kept inside a token — they carry meaning in "adr-writer",
# "c++", "readme.md". Only a trailing `.` or `-` is stripped, as sentence
# punctuation ("pages." and "pages" must be one term). Trailing `+`/`#` are NOT
# stripped: they are the whole difference between "c", "c++" and "c#", which
# rstrip(".-+#") collapsed into a single term.
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9+#.-]*")
# Structural filler that every description shares; leaving it in inflates every
# pairwise similarity by a constant and buries the real twins.
_STOPWORD_TEXT = """a an and are as at be by for from in into is it its of on or that
the this to use used user when with without you your do does not nor but"""
_STOPWORDS = frozenset(_STOPWORD_TEXT.split())

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


def split_frontmatter(text: str) -> tuple[list[str], list[str], int]:
    """Return (frontmatter lines, body lines, 1-based line number of body start).

    Hand-rolled rather than YAML-parsed on purpose: this script must survive a
    frontmatter that does not parse (harness_lint.py owns reporting that), and
    it needs line numbers, which a parser discards.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], lines, 1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1 :], i + 2
    return [], lines, 1


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


def parse_tools(raw: str | None) -> dict:
    """Both notations found in the corpus: a JSON list, or a bare CSV.

    `form` survives into the JSON only because `unparsable` is actionable; the
    raw line itself is not emitted — Phase 1 already has the file open.
    """
    if raw is None:
        return {"form": None, "names": []}
    stripped = raw.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return {"form": "unparsable", "names": []}
        names = [str(t).strip() for t in parsed if str(t).strip()]
        return {"form": "json-list", "names": names}
    names = [t.strip() for t in stripped.split(",") if t.strip()]
    return {"form": "bare-csv" if names else None, "names": names}


def classify_tool(
    name: str,
    known_tools: frozenset[str],
    mcp_servers: frozenset[str],
    mcp_readable: bool = True,
) -> dict:
    m = _MCP_TOOL_RE.match(name)
    if m:
        server = m.group(1)
        # `server_in_config` is deliberately not called "configured": servers
        # supplied by a connector rather than a config file never appear in
        # these files at all, so a false is "not in the local config", never
        # "retired". None when no config source parsed.
        return {
            "name": name,
            "status": "mcp",
            "server": server,
            "server_in_config": (server in mcp_servers) if mcp_readable else None,
        }
    return {"name": name, "status": "builtin" if name in known_tools else "unverified"}


def scan_suppression(body_lines: list[str], first_line: int = 1) -> list[dict]:
    """Line-numbered suppression *candidates* — the judgment is the reader's."""
    hits: list[dict] = []
    for offset, line in enumerate(body_lines):
        # One hit per line, not per pattern: "only report high-severity issues"
        # legitimately matches two catalog entries and a reader should see one
        # line to judge, not the same line twice.
        matched = [pid for pid, pattern in SUPPRESSION_PATTERNS if pattern.search(line)]
        if matched:
            hits.append({"line": first_line + offset, "patterns": matched, "text": line.strip()})
    return hits


def scan_always_never(body_lines: list[str], first_line: int = 1) -> list[dict]:
    hits: list[dict] = []
    for offset, line in enumerate(body_lines):
        tokens = sorted(set(_ALWAYS_NEVER_RE.findall(line)))
        if tokens:
            hits.append({"line": first_line + offset, "tokens": tokens, "text": line.strip()})
    return hits


# Measured over the real 25-agent corpus on 2026-08-26: all 300 pairs scored
# below 0.53, and the distribution has one clean gap — editor / essay-reviewer at
# 0.525 (two channel-routed prose reviewers, the corpus's only genuine near-twin)
# and then nothing until clarity-reviewer / prose-clarity-reviewer at 0.319. The
# default sits in that gap: it surfaces the one pair a reader would call twins and
# stays silent on the other 299. Raise it if the corpus grows a cluster of
# legitimately adjacent siblings; lower it to see the long tail.
DEFAULT_DUP_THRESHOLD = 0.5


def description_near_duplicates(descriptions: dict[str, str], threshold: float) -> list[dict]:
    """Pairs whose description term sets overlap at or above `threshold`.

    Token-set Jaccard rather than a character-diff ratio: descriptions differ by
    word order and by length far more than by spelling, and difflib's
    SequenceMatcher scores a reordering as a difference. Stdlib only — the
    corpus is 25 files (300 pairs) and a compiled fuzzy-matching dependency
    would buy microseconds at the cost of the sub-project's empty dependency
    list (rapidfuzz considered and rejected, as-of 2026-08-26).
    """
    terms = {name: normalize_terms(text) for name, text in descriptions.items()}
    names = sorted(terms)
    pairs: list[dict] = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            ta, tb = terms[a], terms[b]
            union = ta | tb
            if not union:
                continue
            shared = ta & tb
            similarity = len(shared) / len(union)
            if similarity >= threshold:
                pairs.append(
                    {
                        "a": a,
                        "b": b,
                        "similarity": round(similarity, 3),
                        "shared_terms": sorted(shared),
                    }
                )
    return sorted(pairs, key=lambda p: (-p["similarity"], p["a"], p["b"]))


def _json_servers(path: Path) -> tuple[set[str], str]:
    text, reason = _read_text(path)
    if text is None:
        return set(), reason
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return set(), "unparsable"
    if not isinstance(data, dict):
        return set(), "not-a-mapping"
    servers = set(data.get("mcpServers") or {})
    for project in (data.get("projects") or {}).values():
        if isinstance(project, dict):
            servers |= set(project.get("mcpServers") or {})
    return servers, "ok"


def discover_mcp_servers(root: Path) -> tuple[set[str], list[dict]]:
    """Configured servers plus a per-source status.

    The status matters more than the set. Listing a path as consulted when the
    read or the parse failed is provenance vouching for something that did not
    happen, and it turns every MCP tool into `server_configured: false` — that
    is, fabricated Update evidence against correct agents (2026-08-26
    silent-failure review). `~/.claude.json` is rewritten continuously by Claude
    Code, so a mid-write read is not a hypothetical.
    """
    servers: set[str] = set()
    sources: list[dict] = []
    seen: set[str] = set()
    for candidate in (*_MCP_CONFIG_CANDIDATES, root / ".mcp.json"):
        if not candidate.is_file():
            continue
        # `--root ~/.claude` makes the second and third candidates the same
        # file. Without this the provenance list names it twice, which reads as
        # two independent confirmations of a server.
        resolved = str(candidate.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        found, status = _json_servers(candidate)
        servers |= found
        sources.append({"path": resolved, "status": status, "server_count": len(found)})
    return servers, sources


def analyze_file(
    path: Path,
    known_tools: frozenset[str],
    mcp_servers: frozenset[str],
    mcp_readable: bool = True,
) -> tuple[dict | None, str]:
    text, reason = _read_text(path)
    if text is None:
        return None, reason
    front, body, body_start = split_frontmatter(text)
    # The blank separator line after the closing `---` is layout, not body.
    # Body length ignoring the blank separator after the closing `---` and any
    # trailing blank lines — layout, not body.
    body_measured = len("\n".join(body).strip().splitlines())
    name = front_scalar(front, "name")
    description = front_scalar(front, "description") or ""
    tools = parse_tools(front_scalar(front, "tools"))
    return {
        "file": path.name,
        "name": name,
        "desc_words": len(description.split()),
        "body_lines": body_measured,
        "description": description,
        "tools": {
            "form": tools["form"],
            "items": [
                classify_tool(t, known_tools, mcp_servers, mcp_readable) for t in tools["names"]
            ],
        },
        "suppression_candidates": scan_suppression(body, body_start),
        "always_never_candidates": scan_always_never(body, body_start),
    }, "ok"


def collect_evidence(
    root: Path,
    agents_rel: str = AGENTS_DIR,
    *,
    known_tools: set[str] | frozenset[str] | None = None,
    mcp_servers: set[str] | frozenset[str] | None = None,
    mcp_sources: list[dict] | None = None,
    dup_threshold: float = DEFAULT_DUP_THRESHOLD,
) -> dict | None:
    agents_dir = root / agents_rel
    if not agents_dir.is_dir():
        return None
    known = frozenset(known_tools) if known_tools is not None else BUILTIN_TOOLS
    servers = frozenset(mcp_servers or ())
    files = sorted(agents_dir.glob("*.md"))
    mcp_readable = any(s["status"] == "ok" for s in (mcp_sources or []))
    agents: list[dict] = []
    unreadable: list[dict] = []
    for path in files:
        entry, reason = analyze_file(path, known, servers, mcp_readable)
        # Dropping these silently would leave `agents_total` counting a file that
        # appears nowhere in `agents` — a JSON that looks complete and is not
        # (2026-08-26 cross-model review).
        if entry is not None:
            agents.append(entry)
        else:
            unreadable.append({"file": path.name, "reason": reason})
    duplicates = description_near_duplicates(
        {a["file"]: a["description"] for a in agents if a["description"]}, dup_threshold
    )
    return {
        "root": str(root),
        "registry": {
            "known_tools": {
                "source": "override" if known_tools is not None else "embedded",
                "as_of": None if known_tools is not None else BUILTIN_TOOLS_AS_OF,
                "count": len(known),
            },
            "mcp_servers": sorted(servers),
            "mcp_config_files": mcp_sources or [],
            "mcp_config_readable": mcp_readable,
        },
        "dup_threshold": dup_threshold,
        "agents_total": len(files),
        "unreadable": unreadable,
        "tools_unparsable": [a["file"] for a in agents if a["tools"]["form"] == "unparsable"],
        "total_desc_words": sum(a["desc_words"] for a in agents),
        "agents": agents,
        "description_near_duplicates": duplicates,
    }


def _load_known_tools(path: Path) -> set[str] | None:
    text, _reason = _read_text(path)
    if text is None:
        return None
    return {line.strip() for line in text.splitlines() if line.strip()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", default=".", help="harness root (default: cwd)")
    parser.add_argument(
        "--known-tools",
        default=None,
        metavar="FILE",
        help=f"replace the embedded built-in tool list (as-of {BUILTIN_TOOLS_AS_OF}); "
        "one tool name per line",
    )
    parser.add_argument(
        "--dup-threshold",
        type=float,
        default=DEFAULT_DUP_THRESHOLD,
        help="term-set Jaccard at or above which two descriptions are paired "
        f"(default: {DEFAULT_DUP_THRESHOLD}, measured — see the constant's comment)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser()
    known_tools: set[str] | None = None
    if args.known_tools:
        known_tools = _load_known_tools(Path(args.known_tools).expanduser())
        if known_tools is None:
            print(f"agent_evidence: cannot read {args.known_tools}", file=sys.stderr)
            return 2

    servers, sources = discover_mcp_servers(root)
    evidence = collect_evidence(
        root,
        known_tools=known_tools,
        mcp_servers=servers,
        mcp_sources=sources,
        dup_threshold=args.dup_threshold,
    )
    if evidence is None:
        print(f"agent_evidence: {root / AGENTS_DIR} is not a directory", file=sys.stderr)
        return 2

    json.dump(evidence, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

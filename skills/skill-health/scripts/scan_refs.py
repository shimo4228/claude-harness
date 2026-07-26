"""Structural reference-existence scanner for SKILL.md files.

Detects the **"missing artifacts"** skill-technical-debt pattern (SkillOps,
arXiv:2605.13716): a SKILL.md names a local artifact — a `python -m scripts.X`
module, a `bash …/foo.sh` script, a `~/.claude/agents/X.md` agent, or a
Markdown link to a sibling skill / reference doc — that does not exist on disk.
Such references dangle silently when a refactor renames or deletes the target.

This is a **structural** property, decidable from the literal shape of the
Markdown plus a filesystem `exists()` check. Per the Agent Knowledge Cycle
ADR-0008 "Code-LLM Layering", code owns structural determinism and 100%
accuracy here; the semantic debt patterns (over-specialized scope,
trigger↔body drift), the risk dimension, and the validation dimension are
delegated to a holistic LLM pass / the claude-security plugin / skill-comply and are
**never scored** in this module.

  https://github.com/shimo4228/agent-knowledge-cycle/blob/main/docs/adr/0008-code-and-llm-collaboration.md

The CLI exit code is the code-owned gate: 0 = no dangling references,
1 = dangling references found, 2 = scan root not found. Reference extraction is
pure (no IO); existence checking is isolated in `dangling()` so the parsers stay
unit-testable without a filesystem.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote

# Run-commands and bash invocations usually live inside fenced code blocks, so
# these patterns are matched against every line. Markdown links, by contrast,
# are matched only outside fences (an illustrative `[x](./missing.md)` in a code
# sample is not a real reference) — see `_content_lines`.
_RUN_MODULE_RE = re.compile(r"python3?\s+-m\s+(scripts(?:\.\w+)+)")
_BASH_RE = re.compile(r"\bbash\s+(\S+\.sh)\b")
# [\w-]+ allows underscores (Python convention) as well as the hyphen-case
# harness convention; both are valid agent filenames on disk.
_AGENT_RE = re.compile(r"~/\.claude/agents/([\w-]+)\.md")

# Markdown link parsing, mirrored from readme-writer/scripts/readme_lint.py so
# the harness has one consistent treatment of fences and local links.
_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
_MD_LINK_RE = re.compile(
    r"(?<!!)\[(?!!)([^\]]*)\]\(\s*([^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")

# Named (path-free) skill references. Each pattern is chosen for precision, not
# recall — see extract_skill_refs. The trailing `(?![\w:/-])` on the slash and
# name forms rejects plugin-qualified (`hookify:configure`) and path-shaped
# (`/tmp/x`) tokens that would otherwise resolve to a bogus bare name.
_SKILL_NAME_RE = re.compile(r"[a-z][a-z0-9-]{2,}")
_SEE_SKILL_RE = re.compile(r"See skills?:\s*([^—(\[\n.]+)")
_SKILL_COLON_RE = re.compile(r"skill:\s*`([a-z][a-z0-9-]{2,})`")
_NAME_THEN_SKILL_RE = re.compile(r"`([a-z][a-z0-9-]{2,})`\s+skill\b")
_SLASH_SKILL_RE = re.compile(r"`/([a-z][a-z0-9-]{2,})`(?![\w:/-])")

# NOISE REDUCTION ONLY — not an authority on what exists. Names here are known
# to live in the slash-command namespace rather than under the skills root, so
# listing them keeps the common cases out of the report. The set is necessarily
# incomplete: that namespace is not enumerable from disk, and the harness hides
# user-only commands (e.g. /code-review) from the agent entirely. A name absent
# from this set is therefore "unresolved", never "missing" — see
# extract_skill_refs. Adding an entry only quiets a line; omitting one only
# leaves a line for a human to dismiss.
_KNOWN_NON_FILE_SKILLS = frozenset(
    {
        # CLI builtins
        "help",
        "clear",
        "compact",
        "model",
        "effort",
        "config",
        "doctor",
        "mcp",
        "plugin",
        "sandbox",
        "context",
        "agents",
        "resume",
        "continue",
        "init",
        "login",
        "logout",
        "status",
        "cost",
        "memory",
        "vim",
        "terminal-setup",
        # bundled skills (not under ~/.claude/skills)
        "review",
        "security-review",
        "code-review",
        "simplify",
        "run",
        "loop",
        "schedule",
        "dataviz",
        "artifact-design",
        "artifact-capabilities",
        "claude-api",
        "claude-in-chrome",
        "update-config",
        "keybindings-help",
        "fewer-permission-prompts",
    }
)

_DELEGATION_NOTE = (
    "Structural 'missing artifacts' check only — the semantic debt patterns "
    "(over-specialized, trigger↔body drift), the risk dimension, and the "
    "validation dimension are delegated to skill-stocktake / the claude-security plugin / "
    "skill-comply, never reduced to a number."
)


@dataclass(frozen=True)
class Reference:
    skill: str
    ref_type: str  # run_module | bash_script | agent | md_link
    raw: str
    target: str
    line: int


@dataclass(frozen=True)
class ExternalSkill:
    """A skill whose directory is a symlink out of the skills root.

    Ownership is the second structural property this scanner decides (the first
    being reference existence), and it answers a different question: not "is this
    skill correct?" but "does a fix applied here survive?".
    """

    skill: str
    link_path: str
    real_path: str
    owner: str  # homebrew | nix | python-env | external


# Real-path prefixes that identify a package manager's own tree. Matching one
# only sharpens the report's wording; anything symlinked out of the skills root
# is already unowned regardless of who owns it, so an unrecognised prefix falls
# through to the honest generic label rather than being treated as local.
_OWNER_PREFIXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("homebrew", ("/opt/homebrew/", "/usr/local/Cellar/", "/home/linuxbrew/")),
    ("nix", ("/nix/store/",)),
    ("python-env", ("/site-packages/", "/dist-packages/")),
)


def _has_template_placeholder(text: str) -> bool:
    """Angle brackets (`<公開repo>/x.sh`) and the ellipsis (`…/x.sh`) mark a doc
    template slot, never a real path. Skip rather than emit a false positive."""
    return "<" in text or ">" in text or "…" in text


def _is_metavariable(token: str) -> bool:
    """A lone uppercase letter (`scripts.X`, `agents/X.md`) is a documentation
    metavariable, not a real module / agent name — those are lower-case by
    convention. Multi-letter all-caps names (README, LICENSE) are left alone so
    a genuine reference to one is still existence-checked."""
    return len(token) == 1 and token.isascii() and token.isupper()


def _is_placeholder_link(label: str, target: str) -> bool:
    """The two confirmed illustrative-example link patterns: an empty label
    (`[](url)`) has no real referent, and a literal `...` target is an explicit
    placeholder. A bare extensionless target (`[log](CHANGELOG)`) is NOT a
    placeholder — it falls through to the existence check."""
    return not label.strip() or target == "..."


def _content_lines(markdown: str) -> list[tuple[int, str]]:
    """Return (1-based line number, text) for lines outside fenced code blocks.

    A fence opens on ``` or ~~~ (an info string is allowed) and closes only on a
    line using the same marker character, at least as long, with nothing but
    whitespace after the run (CommonMark §4.5).
    """
    out: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_len = 0
    for idx, line in enumerate(markdown.splitlines(), start=1):
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


def extract_run_modules(markdown: str, skill: str, skill_dir: Path) -> list[Reference]:
    """Find `python -m scripts.X` references → `<skill_dir>/scripts/X.py`.

    Lines carrying a `--directory` override are skipped: the override changes the
    working directory, so `scripts.X` no longer resolves to the skill dir and a
    naive check would be a false positive.
    """
    refs: list[Reference] = []
    for line_no, line in enumerate(markdown.splitlines(), start=1):
        if "--directory" in line:
            continue
        for m in _RUN_MODULE_RE.finditer(line):
            module = m.group(1)
            if _is_metavariable(module.rsplit(".", 1)[-1]):
                continue
            rel = module.replace(".", "/") + ".py"
            refs.append(Reference(skill, "run_module", module, str(skill_dir / rel), line_no))
    return refs


def extract_bash_scripts(markdown: str, skill: str, skill_dir: Path) -> list[Reference]:
    """Find `bash <path>.sh` references and resolve the script path."""
    refs: list[Reference] = []
    for line_no, line in enumerate(markdown.splitlines(), start=1):
        for m in _BASH_RE.finditer(line):
            raw = m.group(1)
            if _has_template_placeholder(raw):
                continue
            if raw.startswith("~"):
                target = Path(raw).expanduser()
            elif raw.startswith("/"):
                target = Path(raw)
            else:
                target = skill_dir / raw
            refs.append(Reference(skill, "bash_script", raw, str(target), line_no))
    return refs


def extract_agent_refs(markdown: str, skill: str) -> list[Reference]:
    """Find explicit `~/.claude/agents/<name>.md` references.

    Agent paths are global (`~/.claude/agents/`), so unlike the other extractors
    this one needs no skill_dir. Bare prose agent names ("the code-reviewer
    agent") are deliberately not matched — too ambiguous to resolve without
    false positives. A skill-local `](agents/x.md)` link is caught by md_links.
    """
    refs: list[Reference] = []
    for line_no, line in enumerate(markdown.splitlines(), start=1):
        for m in _AGENT_RE.finditer(line):
            name = m.group(1)
            if _is_metavariable(name):
                continue
            target = (Path("~/.claude/agents") / f"{name}.md").expanduser()
            refs.append(Reference(skill, "agent", m.group(0), str(target), line_no))
    return refs


def extract_skill_refs(markdown: str, skill: str, root: Path) -> list[Reference]:
    """Find sibling skills referenced **by name** rather than by file path.

    The path-shaped extractors above structurally cannot see this class: a body
    that says ``See skill: verify`` names an artifact without ever writing a
    path, so no `exists()` check was reachable. Observed live on 2026-07-25 —
    five skills routed the reader to `verify` / `code-review` and the scan
    reported 0 dangling.

    **These are ENUMERATED, never adjudicated.** A name is resolvable here only
    against the skills root; the slash-command namespace a user actually types
    (CLI builtins, bundled skills, plugin commands) is not enumerable from disk
    — the same 2026-07-25 investigation found `/code-review` live in that
    namespace while absent from every on-disk registry, precisely because the
    harness hides user-only commands from the agent's invocation list. So an
    unresolved name is reported as *unresolved*, not as a defect, and does NOT
    move the exit code. Code enumerates; a human or a holistic pass decides
    (enumerate/decide, per when-code-when-llm).

    Only high-precision forms are matched, keeping the scanner's
    false-positive-is-worse-than-a-miss stance: ``See skill(s): X``,
    ``skill: `X` ``, `` `X` skill ``, and a backticked `` `/X` ``. A bare
    unbackticked ``/x`` is a path far more often than an invocation and is
    deliberately ignored. Plugin-qualified (`a:b`) and path-shaped (`a/b`)
    names are skipped, as is the skill's own name.
    """
    refs: list[Reference] = []
    seen: set[tuple[str, int]] = set()

    def add(name: str, raw: str, line_no: int) -> None:
        name = name.strip().strip("`")
        if not _SKILL_NAME_RE.fullmatch(name):
            return
        if name == skill or name in _KNOWN_NON_FILE_SKILLS or _is_metavariable(name):
            return
        if (name, line_no) in seen:
            return
        seen.add((name, line_no))
        refs.append(Reference(skill, "skill_name", raw, str(root / name), line_no))

    for line_no, line in _content_lines(markdown):
        for m in _SEE_SKILL_RE.finditer(line):
            for part in re.split(r"[,/]| and ", m.group(1)):
                add(part, m.group(0), line_no)
        for pattern in (_SKILL_COLON_RE, _NAME_THEN_SKILL_RE, _SLASH_SKILL_RE):
            for m in pattern.finditer(line):
                add(m.group(1), m.group(0), line_no)
    return refs


def _is_external(href: str) -> bool:
    h = href.strip()
    return bool(_SCHEME_RE.match(h)) or h.startswith("//")


def extract_md_links(markdown: str, skill: str, skill_dir: Path) -> list[Reference]:
    """Find Markdown links to local files, resolved relative to the skill dir.

    External URLs, in-page anchors, and site-absolute (`/…`) targets are skipped,
    matching readme_lint's local-link semantics. Only lines outside fenced code
    blocks are considered.
    """
    refs: list[Reference] = []
    for line_no, line in _content_lines(markdown):
        for m in _MD_LINK_RE.finditer(line):
            label, href = m.group(1), m.group(2)
            if _is_external(href):
                continue
            target = href.split("#", 1)[0].split("?", 1)[0].strip()
            if not target or target.startswith("/"):
                continue
            if _has_template_placeholder(target) or _is_placeholder_link(label, target):
                continue
            refs.append(
                Reference(skill, "md_link", href, str(skill_dir / unquote(target)), line_no)
            )
    return refs


def extract_references(markdown: str, skill: str, skill_dir: Path) -> list[Reference]:
    """All structural references in one SKILL.md body."""
    return [
        *extract_run_modules(markdown, skill, skill_dir),
        *extract_bash_scripts(markdown, skill, skill_dir),
        *extract_agent_refs(markdown, skill),
        *extract_skill_refs(markdown, skill, skill_dir.parent),
        *extract_md_links(markdown, skill, skill_dir),
    ]


def _target_exists(ref: Reference) -> bool:
    p = Path(ref.target)
    if ref.ref_type == "run_module":
        # `python -m scripts.pkg` is also satisfied by a package directory.
        return p.exists() or (p.with_suffix("") / "__init__.py").exists()
    if ref.ref_type == "skill_name":
        # A skill name resolves as a directory, a flat note, or a learned note.
        return (
            (p / "SKILL.md").exists()
            or p.with_suffix(".md").exists()
            or (p.parent / "learned" / f"{p.name}.md").exists()
        )
    return p.exists()


def dangling(refs: Iterable[Reference]) -> list[Reference]:
    """The references whose resolved target does not exist on disk.

    Includes unresolved `skill_name` entries — callers that need the
    authoritative-vs-informational distinction split with `partition_findings`.
    """
    return [ref for ref in refs if not _target_exists(ref)]


def partition_findings(refs: Iterable[Reference]) -> tuple[list[Reference], list[Reference]]:
    """Split unresolved references into (missing artifacts, unresolved names).

    Only the first list is a defect claim: those targets are paths the skill
    itself wrote, so `exists()` is authoritative. The second is an enumeration
    handed to judgment — a name can live in the slash-command namespace, which
    is not enumerable from disk, so the scanner must not call it missing.
    """
    unresolved = list(dangling(refs))
    missing = [r for r in unresolved if r.ref_type != "skill_name"]
    names = [r for r in unresolved if r.ref_type == "skill_name"]
    return missing, names


def _classify_owner(real: Path) -> str:
    """Name the package manager that owns a resolved skill path, if recognisable.

    Substring matching on the resolved path, not `is_relative_to`, because the
    Homebrew and Nix markers appear at a fixed absolute prefix while the Python
    ones (`site-packages`) sit mid-path under an arbitrary env root.
    """
    text = str(real)
    for owner, prefixes in _OWNER_PREFIXES:
        if any(p in text for p in prefixes):
            return owner
    return "external"


def external_skills(root: Path) -> list[ExternalSkill]:
    """Skills whose directory is a symlink pointing out of the skills root.

    A symlinked skill directory is decisive on its own: `git ls-files` cannot even
    be asked about a path behind a symlink (`fatal: pathspec ... is beyond a
    symbolic link`), so the link *is* the boundary of what this repository owns —
    no git call, no judgment.

    This is enumeration, not a defect claim. The skill may be perfectly good; the
    point is that an edit made here lands in another tree and disappears on that
    tree's next upgrade, so a fix belongs upstream. Callers route, they do not
    grade — and the references inside such a skill are still scanned normally,
    because ownership changes where a fix goes, not whether the defect is real.
    """
    found: list[ExternalSkill] = []
    for entry in sorted(root.glob("*")):
        if not entry.is_symlink() or not (entry / "SKILL.md").exists():
            continue
        real = entry.resolve()
        if real.is_relative_to(root.resolve()):
            continue
        found.append(ExternalSkill(entry.name, str(entry), str(real), _classify_owner(real)))
    return found


def _skill_files(root: Path) -> list[Path]:
    return sorted(root.glob("*/SKILL.md"))


def scan_skill(skill_md: Path) -> list[Reference]:
    """Dangling references in a single SKILL.md (skill name = parent dir name)."""
    skill_dir = skill_md.parent
    body = skill_md.read_text(encoding="utf-8")
    return dangling(extract_references(body, skill_dir.name, skill_dir))


def _scan_files(skill_files: list[Path]) -> list[Reference]:
    result: list[Reference] = []
    for skill_md in skill_files:
        result.extend(scan_skill(skill_md))
    result.sort(key=lambda r: (r.skill, r.line, r.ref_type, r.raw))
    return result


def scan_root(root: Path) -> list[Reference]:
    """Dangling references across every `<root>/*/SKILL.md`."""
    return _scan_files(_skill_files(root))


def render_report(
    items: list[Reference], scanned: int, external: list[ExternalSkill] | None = None
) -> str:
    missing, names = partition_findings(items)
    lines = [f"skill-health: structural reference scan ({scanned} skill(s))", ""]
    if missing:
        lines.append(f"{len(missing)} dangling reference(s) — 'missing artifacts' debt:")
        lines.append("")
        for ref in missing:
            lines.append(
                f"  [{ref.ref_type}] {ref.skill} L{ref.line}: {ref.raw} → {ref.target} (missing)"
            )
    else:
        lines.append("No dangling references found.")
    if names:
        lines.append("")
        lines.append(
            f"{len(names)} unresolved name reference(s) — NOT a defect claim. Each names a "
            "skill/command that is not under the skills root; it may still exist as a CLI "
            "builtin, bundled skill, plugin command, or project-scoped skill. Decide per item:"
        )
        lines.append("")
        for ref in names:
            lines.append(
                f"  [{ref.ref_type}] {ref.skill} L{ref.line}: {ref.raw} → '{Path(ref.target).name}' (unresolved)"
            )
    if external:
        lines.append("")
        lines.append(
            f"{len(external)} skill(s) not owned by this harness — a symlink out of the skills "
            "root. Their contents may be fine, but an edit applied here lands in another tree "
            "and is overwritten by that tree's next upgrade, so a fix belongs UPSTREAM (file an "
            "issue / PR), not in a local verdict:"
        )
        lines.append("")
        for ext in external:
            lines.append(f"  [{ext.owner}] {ext.skill} → {ext.real_path}")
    lines.append("")
    lines.append(_DELEGATION_NOTE)
    return "\n".join(lines)


def render_json(
    items: list[Reference], scanned: int, external: list[ExternalSkill] | None = None
) -> str:
    missing, names = partition_findings(items)
    data = {
        "scanned": scanned,
        "dangling_count": len(missing),
        "dangling": [asdict(ref) for ref in missing],
        "unresolved_name_count": len(names),
        "unresolved_names": [asdict(ref) for ref in names],
        "external_count": len(external or []),
        "external": [asdict(ext) for ext in external or []],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path("~/.claude/skills").expanduser(),
        help="skills root to scan (default: ~/.claude/skills)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        print(f"error: scan root not found: {args.root}", file=sys.stderr)
        return 2
    skill_files = _skill_files(args.root)
    items = _scan_files(skill_files)
    scanned = len(skill_files)
    external = external_skills(args.root)
    print(
        render_json(items, scanned, external)
        if args.json
        else render_report(items, scanned, external)
    )
    # Neither unresolved names nor external ownership moves the gate. The scanner
    # cannot enumerate the slash-command namespace, so failing CI on a name would
    # fail on correct code; and an externally-owned skill is a routing fact, not a
    # defect of this repository (enumerate/decide, per when-code-when-llm).
    missing, _ = partition_findings(items)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())

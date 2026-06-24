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
delegated to a holistic LLM pass / security-scan / skill-comply and are
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

_DELEGATION_NOTE = (
    "Structural 'missing artifacts' check only — the semantic debt patterns "
    "(over-specialized, trigger↔body drift), the risk dimension, and the "
    "validation dimension are delegated to skill-stocktake / security-scan / "
    "skill-comply, never reduced to a number."
)


@dataclass(frozen=True)
class Reference:
    skill: str
    ref_type: str  # run_module | bash_script | agent | md_link
    raw: str
    target: str
    line: int


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
            refs.append(Reference(skill, "md_link", href, str(skill_dir / unquote(target)), line_no))
    return refs


def extract_references(markdown: str, skill: str, skill_dir: Path) -> list[Reference]:
    """All structural references in one SKILL.md body."""
    return [
        *extract_run_modules(markdown, skill, skill_dir),
        *extract_bash_scripts(markdown, skill, skill_dir),
        *extract_agent_refs(markdown, skill),
        *extract_md_links(markdown, skill, skill_dir),
    ]


def _target_exists(ref: Reference) -> bool:
    p = Path(ref.target)
    if ref.ref_type == "run_module":
        # `python -m scripts.pkg` is also satisfied by a package directory.
        return p.exists() or (p.with_suffix("") / "__init__.py").exists()
    return p.exists()


def dangling(refs: Iterable[Reference]) -> list[Reference]:
    """The references whose resolved target does not exist on disk."""
    return [ref for ref in refs if not _target_exists(ref)]


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


def render_report(items: list[Reference], scanned: int) -> str:
    lines = [f"skill-health: structural reference scan ({scanned} skill(s))", ""]
    if items:
        lines.append(f"{len(items)} dangling reference(s) — 'missing artifacts' debt:")
        lines.append("")
        for ref in items:
            lines.append(
                f"  [{ref.ref_type}] {ref.skill} L{ref.line}: "
                f"{ref.raw} → {ref.target} (missing)"
            )
    else:
        lines.append("No dangling references found.")
    lines.append("")
    lines.append(_DELEGATION_NOTE)
    return "\n".join(lines)


def render_json(items: list[Reference], scanned: int) -> str:
    data = {
        "scanned": scanned,
        "dangling_count": len(items),
        "dangling": [asdict(ref) for ref in items],
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
    print(render_json(items, scanned) if args.json else render_report(items, scanned))
    return 1 if items else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Path-shaped tokens in an ADR, and the ADR's named paths vs a diff.

Split out of `adr_review_evidence.py` under the file-LOC budget (ADR-0056). Both
checks here answer "does the tree agree with what this ADR names", so they share
the extension table and the repo-relative normalization; `check_diff_scope`
consumes `check_paths`'s items rather than re-classifying them.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.adr_evidence_common import (
    _INLINE_CODE_RE,
    _MD_LINK_RE,
    _METAVARIABLE_CHARS,
    _PLACEHOLDER_RE,
    _git,
    _is_ignored,
    _read_lines,
    _snippet,
    _strip_inline_code,
    _tracked_files,
)

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
            continue  # the ADR itself, its index, sibling Note (注記) edits
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

"""Corpus access and the individual checks for `context_evidence.py`.

Split out of `context_evidence.py` on 2026-08-28 under the file-LOC budget
(ADR-0056). Everything here reads the target repo: the `Corpus` cache, the
sibling-script delegation, and one `check_*` per checklist item. The assembly
that calls them and the gate that judges their output stayed behind in
`context_evidence.py`, so the dependency runs one way — checks never import the
assembler.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tomllib
from pathlib import Path
from types import ModuleType

if __package__:
    from . import context_parsing as _p
else:  # Support the documented direct script invocation.
    import context_parsing as _p

CONTEXT_FILENAMES = _p.CONTEXT_FILENAMES
DOC_DIRS = _p.DOC_DIRS
PACKAGE_MANIFESTS = _p.PACKAGE_MANIFESTS
SOURCE_EXTENSIONS = _p.SOURCE_EXTENSIONS
SKIP_DIRS = _p.SKIP_DIRS
NESTED_CHECKOUT_MARKERS = _p.NESTED_CHECKOUT_MARKERS
TEMPLATE_DIRS = _p.TEMPLATE_DIRS
_MAX_FILE_BYTES = _p._MAX_FILE_BYTES
_MAX_ITEMS = _p._MAX_ITEMS
_MAX_INDEX_ENTRIES = _p._MAX_INDEX_ENTRIES
_MAX_LINE_CHARS = _p._MAX_LINE_CHARS
Command = _p.Command
Marker = _p.Marker
Token = _p.Token
Version = _p.Version
cli_example_candidates = _p.cli_example_candidates
fenced_blocks = _p.fenced_blocks
h2_topics = _p.h2_topics
md_link_paths = _p.md_link_paths
md_link_targets = _p.md_link_targets
normalized_instructions = _p.normalized_instructions
numeric_claim_lines = _p.numeric_claim_lines
path_tokens = _p.path_tokens
todo_markers = _p.todo_markers
topic_overlap_ratio = _p.topic_overlap_ratio
tree_block_paths = _p.tree_block_paths
version_mentions = _p.version_mentions
_DOI_RE = _p._DOI_RE
_ISO_DATE_RE = _p._ISO_DATE_RE
_LEADING_DOTSLASH_RE = _p._LEADING_DOTSLASH_RE
_URL_RE = _p._URL_RE

# --- delegation to sibling evidence scripts ---------------------------------- #

_HARNESS_SKILLS = Path(__file__).resolve().parents[2]
_ADR_LINT_PATH = _HARNESS_SKILLS / "adr-writer" / "scripts" / "adr_lint.py"
_GRAPH_LINT_PATH = _HARNESS_SKILLS / "jsonld-knowledge-graph" / "scripts" / "graph_lint.py"
_ADR_LINT_API = ("analyze_naming", "parse_index_numbers")


def _load_adr_lint() -> tuple[ModuleType | None, str | None]:
    """Import adr_lint by path — single source of truth for ADR index drift.

    Re-implementing `parse_index_numbers` / `analyze_naming` here would give the
    two scripts independent ideas of what an ADR index is; that drift is exactly
    what ADR-0051 set out to avoid. adr_lint is stdlib-only, so importing it
    adds no dependency edge between the two uv sub-projects.

    The broad `except` is deliberate and is the one place it is justified:
    `exec_module` runs foreign module-level code, and *any* exception there must
    become a reported skip rather than either a silent pass (the gate would go
    green on an unverified corpus) or a crash that destroys every other check.
    """
    try:
        spec = importlib.util.spec_from_file_location("adr_lint", _ADR_LINT_PATH)
        if spec is None or spec.loader is None:
            return None, f"no import spec for {_ADR_LINT_PATH}"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 — reported, never swallowed
        return None, f"{type(exc).__name__}: {exc}"
    for name in _ADR_LINT_API:
        if not hasattr(module, name):
            return None, f"adr_lint.py has no {name}() — API drift"
    return module, None


# --- the corpus ---------------------------------------------------------------- #


class Corpus:
    """Repo under inspection, plus a running record of what could not be read.

    Every check reads through `text()`, so a file that drops out is recorded in
    `degraded` instead of vanishing. An empty `degraded` is what makes an empty
    findings list mean "clean" rather than "we could not look".
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.degraded: list[dict] = []
        self.index, self.index_truncated, self.index_entries = self._build_index()

    # -- reading ------------------------------------------------------------- #

    def text(self, path: Path, check: str, effect: str) -> str | None:
        body, reason = _read_why(self.root, path)
        if body is None:
            self.degrade(check, f"{_rel(self.root, path)}: {reason}", effect)
        return body

    def degrade(self, check: str, reason: str, effect: str) -> None:
        self.degraded.append({"check": check, "reason": reason, "effect": effect})

    # -- path resolution ----------------------------------------------------- #

    def _build_index(self) -> tuple[set[str], bool, int]:
        index: set[str] = set()
        count = 0
        truncated = False
        for path in self.root.rglob("*"):
            if _excluded(self.root, path):
                continue
            rel = path.relative_to(self.root).as_posix()
            if path.is_dir():
                rel += "/"
            segments = rel.rstrip("/").split("/")
            trailing = "/" if rel.endswith("/") else ""
            for i in range(len(segments)):
                index.add("/".join(segments[i:]) + trailing)
            count += 1
            if count > _MAX_INDEX_ENTRIES:
                truncated = True
                break
        return index, truncated, count

    def resolves(self, token: str) -> bool:
        if (self.root / token).exists():
            return True
        # `lstrip("./")` strips the leading dot off `.claude/verify.sh` too, so no
        # reference into a dot-directory could ever suffix-match (code review).
        normalized = _LEADING_DOTSLASH_RE.sub("", token)
        return normalized in self.index or normalized.rstrip("/") + "/" in self.index


def _read_why(root: Path, path: Path) -> tuple[str | None, str | None]:
    """(text, reason-it-could-not-be-read). Never (None, None).

    A file that silently drops out of the corpus reads exactly like a file with
    no findings — and the thinned SKILL.md no longer keeps a manual backstop, so
    that silence would *be* the audit (silent-failure review, 2026-08-26).
    """
    try:
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()):
            # A symlink named CLAUDE.md can point anywhere; reading it would put
            # a file from outside the repo into this repo's evidence.
            return None, "resolves outside the repo root (symlink)"
        size = resolved.stat().st_size
        if size > _MAX_FILE_BYTES:
            return None, f"oversize ({size} > {_MAX_FILE_BYTES} bytes)"
        return resolved.read_text(encoding="utf-8", errors="replace"), None
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _rel_parts(root: Path, path: Path) -> tuple[str, ...] | None:
    """Path components *below* the scan root, or None when it escapes the root.

    Matching SKIP_DIRS / NESTED_CHECKOUT_MARKERS against `path.parts` matched the
    root's own ancestors too: `--root ~/.claude/.claude/worktrees/<id>` rejected
    every file under it and reported `doc_files: 0` — a false-clean run of the
    whole script (codex-review P1, 2026-08-26).
    """
    try:
        return path.relative_to(root).parts
    except ValueError:
        return None


def _excluded(root: Path, path: Path) -> bool:
    parts = _rel_parts(root, path)
    if parts is None:
        return True
    return any(part in SKIP_DIRS for part in parts) or any(
        marker in parts for marker in NESTED_CHECKOUT_MARKERS
    )


def _walk(root: Path, suffixes: tuple[str, ...] | None = None) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*"):
        if _excluded(root, path):
            continue
        if not path.is_file():
            continue
        if suffixes is None or path.suffix.lower() in suffixes:
            out.append(path)
    return sorted(out)


def _cap(items: list, key: str) -> dict:
    return {key: items[:_MAX_ITEMS], "count": len(items), "truncated": len(items) > _MAX_ITEMS}


def _git(root: Path, *args: str) -> tuple[str | None, str | None]:
    """(stdout, reason-it-failed). `git` failures are reported, not treated as 0."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return None, "git timed out after 20s"
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if proc.returncode != 0:
        first = (proc.stderr or "").strip().splitlines()
        return None, f"git exited {proc.returncode}: {first[0] if first else 'no stderr'}"
    return proc.stdout.strip(), None


# --- individual checks ------------------------------------------------------- #


def _context_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for name in CONTEXT_FILENAMES:
        path = root / name
        if path.is_file():
            found.append(path)
    for path in _walk(root, (".md",)):
        if any(part in TEMPLATE_DIRS for part in (_rel_parts(root, path) or ())):
            continue
        if path.name in ("CLAUDE.md", "AGENTS.md") and path not in found:
            found.append(path)
    return sorted(set(found))


def _doc_files(root: Path) -> list[Path]:
    docs: list[Path] = []
    for name in DOC_DIRS:
        d = root / name
        if d.is_dir():
            docs.extend(p for p in _walk(d, (".md",)))
    for extra in ("README.md", "llms.txt", "llms-full.txt"):
        path = root / extra
        if path.is_file():
            docs.append(path)
    # Phase 1 declares `README.*.md` (README.ja.md, README.en.md) as External-role
    # documents; leaving them out skipped their claims entirely (codex-review P2).
    docs.extend(p for p in root.glob("README.*.md") if p.is_file())
    return sorted(set(docs))


def check_context_paths(cx: Corpus, context_files: list[Path]) -> dict:
    missing: list[dict] = []
    checked = 0
    read = 0
    # `contemplative-agent/` inside contemplative-agent's own CLAUDE.md is the
    # repo naming itself (or a sibling clone), never a path in this tree.
    self_names = {cx.root.resolve().name, cx.root.resolve().name + "/"}
    effect = "path references in that file were not checked at all"
    for path in context_files:
        text = cx.text(path, "context_paths", effect)
        if text is None:
            continue
        read += 1
        for token in path_tokens(text):
            if token.token in self_names:
                continue
            checked += 1
            if not cx.resolves(token.token):
                missing.append(
                    {"file": _rel(cx.root, path), "line": token.line, "token": token.token}
                )
    return {
        "status": "checked",
        "files_read": read,
        "files_total": len(context_files),
        "checked": checked,
        "note": (
            "a path a document names as *retired*, and a path belonging to another "
            "repo, both show up here — that separation is the reviewer's call"
        ),
        **_cap(missing, "missing"),
    }


def check_todo_markers(cx: Corpus, context_files: list[Path]) -> dict:
    items: list[dict] = []
    read = 0
    for path in context_files:
        text = cx.text(path, "todo_markers", "TODO markers in that file were not seen")
        if text is None:
            continue
        read += 1
        items.extend(
            {"file": _rel(cx.root, path), "line": m.line, "text": m.text[:200]}
            for m in todo_markers(text)
        )
    return {
        "status": "checked",
        "files_read": read,
        "files_total": len(context_files),
        **_cap(items, "items"),
    }


def check_context_duplicates(cx: Corpus, context_files: list[Path]) -> dict:
    if len(context_files) < 2:
        return {"status": "single_file", "pairs": [], "count": 0, "truncated": False}
    seen: dict[str, set[str]] = {}
    read = 0
    for path in context_files:
        text = cx.text(path, "context_duplicates", "that file was left out of the comparison")
        if text is None:
            continue
        read += 1
        for line in set(normalized_instructions(text)):
            seen.setdefault(line, set()).add(_rel(cx.root, path))
    pairs: dict[tuple[str, ...], list[str]] = {}
    for line, files in sorted(seen.items()):
        if len(files) > 1:
            pairs.setdefault(tuple(sorted(files)), []).append(line)
    items = [
        {"files": list(key), "shared_lines": len(lines), "sample": [ln[:120] for ln in lines[:3]]}
        for key, lines in sorted(pairs.items(), key=lambda kv: -len(kv[1]))
    ]
    return {
        "status": "checked",
        "files_read": read,
        "files_total": len(context_files),
        "note": (
            "AGENTS.md mirroring CLAUDE.md is a deliberate cross-agent convention in "
            "some repos (ADR-0015); grouping by file pair makes that one row instead "
            "of hundreds of findings"
        ),
        **_cap(items, "pairs"),
    }


def check_stale_docs(cx: Corpus, docs: list[Path], threshold_days: int, now: int) -> dict:
    """Age each document against the wall clock.

    HEAD's commit time was the first choice, for reproducibility across re-runs of
    the same revision. It was wrong: in a repo dormant for a year, every file is
    zero days old by that measure and nothing is ever stale — which is the whole
    question this check asks (codex-review P2).
    """
    head, reason = _git(cx.root, "log", "-1", "--format=%ct")
    if head is None or not head.isdigit():
        detail = reason or "HEAD has no commit timestamp (empty repository?)"
        cx.degrade("stale_docs", detail, "no document staleness was measured")
        return {"status": "skip", "reason": detail, "items": [], "count": 0, "truncated": False}
    items: list[dict] = []
    with_history = 0
    without_history = 0
    errors: list[dict] = []
    for path in docs:
        rel = _rel(cx.root, path)
        out, err = _git(cx.root, "log", "-1", "--format=%ct", "--", rel)
        if err is not None:
            errors.append({"file": rel, "reason": err})
            continue
        if not out or not out.isdigit():
            without_history += 1  # untracked / newly added — not the same as "fresh"
            continue
        with_history += 1
        days = (now - int(out)) // 86400
        if days >= threshold_days:
            items.append({"file": rel, "days_since_commit": days})
    if errors:
        cx.degrade(
            "stale_docs",
            f"git failed for {len(errors)} file(s), first: {errors[0]['reason']}",
            "those files were not checked for staleness",
        )
    items.sort(key=lambda d: -d["days_since_commit"])
    return {
        "status": "checked",
        "threshold_days": threshold_days,
        "reference": "wall clock at run time",
        "head_commit_epoch": int(head),
        "files_with_history": with_history,
        "files_without_history": without_history,
        "git_errors": errors[:_MAX_ITEMS],
        **_cap(items, "items"),
    }


def check_adr_index(cx: Corpus, adr_rel: str = "docs/adr") -> dict:
    adr_dir = cx.root / adr_rel
    if not adr_dir.is_dir():
        return {"status": "absent", "adr_dir": adr_rel}
    adr_lint, reason = _load_adr_lint()
    if adr_lint is None:
        cx.degrade("adr_index", reason or "adr_lint unavailable", "ADR index drift is UNVERIFIED")
        return {"status": "skip", "reason": reason, "adr_dir": adr_rel}
    md_files = sorted(p for p in adr_dir.glob("*.md") if not p.name.lower().startswith("readme"))
    try:
        naming = adr_lint.analyze_naming(md_files)
        index_present, index_numbers = adr_lint.parse_index_numbers(adr_dir)
    except Exception as exc:  # noqa: BLE001 — foreign code; report, never swallow
        detail = f"adr_lint raised {type(exc).__name__}: {exc}"
        cx.degrade("adr_index", detail, "ADR index drift is UNVERIFIED")
        return {"status": "skip", "reason": detail, "adr_dir": adr_rel}
    file_numbers = set(naming["numbers"])
    return {
        "status": "checked",
        "source": str(_ADR_LINT_PATH),
        "adr_dir": adr_rel,
        "files_total": len(md_files),
        "index_present": index_present,
        "in_index_not_files": sorted(index_numbers - file_numbers),
        "in_files_not_index": sorted(file_numbers - index_numbers),
        "naming_invalid": naming["invalid"],
        "naming_duplicates": naming["duplicates"],
    }


def check_tree_blocks(cx: Corpus, docs: list[Path]) -> dict:
    missing: list[dict] = []
    checked = 0
    # The top node of a documented tree is the repo directory itself and never
    # resolves against its own contents (measured in agent-knowledge-cycle and
    # g-kentei-ios, 2026-08-26).
    self_names = {cx.root.resolve().name, cx.root.resolve().name + "/"}
    for path in docs:
        text = cx.text(path, "tree_blocks", "tree blocks in that file were not checked")
        if text is None:
            continue
        for entry in tree_block_paths(text):
            if "." not in entry and not entry.endswith("/"):
                continue
            if entry in self_names:
                continue
            checked += 1
            if cx.resolves(entry):
                continue
            missing.append({"file": _rel(cx.root, path), "entry": entry})
    return {"status": "checked", "checked": checked, **_cap(missing, "unresolved")}


def _claim_corpus(root: Path, docs: list[Path], context_files: list[Path]) -> list[Path]:
    """Documents whose numbers and versions are claims about the repo *now*.

    The four roles context-sync governs (Context / Architecture / External /
    AI-facing) and nothing else. ADRs and RFCs are dated records of past states —
    their numbers are history, and including them buried the live claims under an
    unusable pile (contemplative-agent: 1,160 candidate lines corpus-wide vs a
    two-digit count here, 2026-08-26)."""
    keep: list[Path] = []
    for path in sorted(set(docs) | set(context_files)):
        role_doc_at_root = path.parent == root and (
            path.name.startswith("README") or path.name.startswith("llms")
        )
        if path in context_files or role_doc_at_root:
            keep.append(path)
    return keep


def check_numeric_claims(cx: Corpus, docs: list[Path], context_files: list[Path]) -> dict:
    items: list[dict] = []
    corpus = _claim_corpus(cx.root, docs, context_files)
    for path in corpus:
        text = cx.text(path, "numeric_claims", "numeric claims in that file were not listed")
        if text is None:
            continue
        items.extend(
            {"file": _rel(cx.root, path), "line": m.line, "text": m.text[:200]}
            for m in numeric_claim_lines(text)
        )
    counts: dict[str, int] = {}
    for path in _walk(cx.root):  # one walk; seven walks was 5.5 s on a large repo
        suffix = path.suffix.lower()
        if suffix in SOURCE_EXTENSIONS:
            counts[suffix.lstrip(".")] = counts.get(suffix.lstrip("."), 0) + 1
    return {
        "status": "checked",
        "files_total": len(corpus),
        "actual_source_file_counts": {k: v for k, v in counts.items() if v},
        "overlap": (
            "readme_evidence.py carries its own numeric-claim pattern for README.md; "
            "the two are independent listings of the same file, not a shared rule"
        ),
        **_cap(items, "claim_lines"),
    }


def check_cli_examples(cx: Corpus, docs: list[Path], context_files: list[Path]) -> dict:
    items: list[dict] = []
    for path in _claim_corpus(cx.root, docs, context_files):
        text = cx.text(path, "cli_examples", "CLI examples in that file were not listed")
        if text is None:
            continue
        items.extend(
            {"file": _rel(cx.root, path), "line": c.line, "command": c.command[:200]}
            for c in cli_example_candidates(text)
        )
    return {
        "status": "listed",
        "note": (
            "UNTRUSTED: repo-controlled strings, listed so a stale example can be "
            "spotted by reading. Neither this script nor its reader executes them"
        ),
        **_cap(items, "commands"),
    }


def _declared_version(root: Path, name: str) -> tuple[str | None, str | None]:
    """(version, reason-it-could-not-be-read) from a manifest, by key path.

    A regex for the first `version =` in the file picks up a nested table (a
    poetry source, a package.json dependency) and then reports the *correct*
    README as the mismatch — measured 2026-08-26.
    """
    text, reason = _read_why(root, root / name)
    if text is None:
        return None, reason
    try:
        if name == "pyproject.toml":
            data = tomllib.loads(text)
            version = data.get("project", {}).get("version") or (
                data.get("tool", {}).get("poetry", {}).get("version")
            )
        elif name == "package.json":
            version = json.loads(text).get("version")
        elif name == "Cargo.toml":
            version = tomllib.loads(text).get("package", {}).get("version")
        elif name == "pom.xml":
            # No XML parse here: report it as unverified rather than let the
            # check read as "no manifest" in a Maven repo (codex-review P2).
            return None, "pom.xml is not parsed by this script — verify by hand"
        else:  # go.mod declares no version
            return None, "this manifest declares no version"
    except (tomllib.TOMLDecodeError, json.JSONDecodeError, AttributeError) as exc:
        return None, f"unparseable: {type(exc).__name__}: {exc}"
    return (version if isinstance(version, str) else None), None


def check_package_metadata(cx: Corpus, docs: list[Path], context_files: list[Path]) -> dict:
    declared: dict[str, str] = {}
    unparseable: list[dict] = []
    for name in PACKAGE_MANIFESTS:
        if not (cx.root / name).is_file():
            continue
        version, reason = _declared_version(cx.root, name)
        if version is not None:
            declared[name] = version
            continue
        detail = reason or "manifest declares no static version (dynamic / absent)"
        unparseable.append({"file": name, "reason": detail})
        cx.degrade("package_metadata", f"{name}: {detail}", "its version was not compared")
    mentions: list[dict] = []
    for path in _claim_corpus(cx.root, docs, context_files):
        text = cx.text(path, "package_metadata", "version mentions in that file were not listed")
        if text is None:
            continue
        mentions.extend(
            {"file": _rel(cx.root, path), "line": v.line, "version": v.version}
            for v in version_mentions(text)
        )
    mismatched = [m for m in mentions if declared and m["version"] not in set(declared.values())]
    return {
        "status": "checked" if declared else ("unparseable" if unparseable else "no_manifest"),
        "declared": declared,
        "unparseable": unparseable,
        **_cap(mismatched, "doc_versions_not_matching_manifest"),
    }


def check_graph_jsonld(cx: Corpus) -> dict:
    path = cx.root / "graph.jsonld"
    if not path.is_file():
        return {"status": "absent"}
    delegated = {
        "checks": ["volatile state (version / count fields)", "JSON-LD expansion pitfalls"],
        "command": f"uv run --with pyld python3 {_GRAPH_LINT_PATH} graph.jsonld",
        "why": "graph_lint.py owns these; duplicating its rules here would drift",
    }
    raw, reason = _read_why(cx.root, path)
    if raw is None:
        # Not the same as invalid JSON: reporting "not valid JSON" for an oversize
        # but perfectly good file sends the author hunting a syntax error that does
        # not exist (silent-failure review, 2026-08-26).
        cx.degrade("graph_jsonld", f"graph.jsonld: {reason}", "graph.jsonld was not inspected")
        return {"status": "unreadable", "reason": reason, "delegated": delegated}
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {
            "status": "present",
            "json_valid": False,
            "error": f"{exc.msg} (line {exc.lineno})",
            "delegated": delegated,
        }
    if isinstance(doc, dict) and isinstance(doc.get("@graph"), list):
        nodes, shape = doc["@graph"], "@graph"
    elif isinstance(doc, list):
        nodes, shape = doc, "top-level-list"
    elif isinstance(doc, dict):
        nodes, shape = [doc], "single-node"
    else:
        nodes, shape = [], "unrecognized"
    nodes = [n for n in nodes if isinstance(n, dict)]

    def _types(node: dict) -> list[str]:
        raw_type = node.get("@type", [])
        if isinstance(raw_type, str):
            return [raw_type]
        return [t for t in raw_type if isinstance(t, str)]

    concepts = sorted(
        n["name"] for n in nodes if "Concept" in _types(n) and isinstance(n.get("name"), str)
    )
    return {
        "status": "present",
        "json_valid": True,
        "shape": shape,
        "nodes_total": len(nodes),
        "concepts": concepts,
        "dois": sorted({m.group(0) for m in _DOI_RE.finditer(raw)}),
        "urls": sorted({m.group(0) for m in _URL_RE.finditer(raw)}),
        "delegated": delegated,
    }


def _freshness_dates(text: str) -> list[str]:
    return _ISO_DATE_RE.findall(text)


def check_llms_txt(cx: Corpus) -> dict:
    path = cx.root / "llms.txt"
    full = cx.root / "llms-full.txt"
    if not path.is_file() and not full.is_file():
        return {"status": "absent"}
    out: dict = {"status": "present"}
    if path.is_file():
        text, reason = _read_why(cx.root, path)
        if text is None:
            # `or ""` here would report a perfect llms.txt — and this check is
            # gated, so it would also pass the gate (silent-failure review).
            cx.degrade("llms_txt", f"llms.txt: {reason}", "llms.txt links are UNVERIFIED")
            return {"status": "unreadable", "reason": reason}
        broken = [t.token for t in md_link_paths(text) if not cx.resolves(t.token)]
        out["broken_links"] = sorted(set(broken))
        readme_text = (
            cx.text(cx.root / "README.md", "llms_txt", "the README overlap ratio is unmeasurable")
            if (cx.root / "README.md").is_file()
            else None
        )
        llms_h2 = h2_topics(text, limit=5)
        readme_h2 = h2_topics(readme_text or "", limit=5)
        measurable = bool(llms_h2 and readme_h2)
        out["readme_h2_overlap"] = {
            "llms_txt_h2": llms_h2,
            "readme_h2": readme_h2,
            # null, not 0.0: "no overlap" and "could not measure" must not share a
            # value the reviewer reads as an emphatic pass.
            "ratio": round(topic_overlap_ratio(llms_h2, readme_h2), 3) if measurable else None,
            "measurable": measurable,
            "note": "the 60% threshold is the reviewer's call; this is the measured ratio",
        }
        out["llms_txt_dates"] = _freshness_dates(text)[:5]
    if full.is_file():
        full_text, reason = _read_why(cx.root, full)
        if full_text is None:
            cx.degrade("llms_txt", f"llms-full.txt: {reason}", "llms-full.txt was not inspected")
            out["llms_full"] = {"status": "unreadable", "reason": reason}
        else:
            full_paths = md_link_paths(full_text)
            out["llms_full"] = {
                "bytes": len(full_text.encode("utf-8")),
                "outbound_links_total": len(md_link_targets(full_text)),
                "outbound_local_doc_links": len(full_paths),
                # Counted but never resolved until 2026-08-27 (RFC-0012): a link into
                # a component the export deleted stayed invisible to the gate, which
                # is how the public mirror kept pointing at three retired skills.
                # llms-full.txt carries the same AI-facing rigor as llms.txt (ADR-0010).
                "broken_links": sorted({t.token for t in full_paths if not cx.resolves(t.token)}),
                "note": "self-containment is a semantic judgment; only links and counts are measured",
            }
    return out


def check_url_liveness(cx: Corpus) -> dict:
    """Collect URLs, never fetch them (url_liveness.py owns the fetching)."""
    urls: set[str] = set()
    for name in ("graph.jsonld", "llms.txt", "llms-full.txt", "README.md"):
        path = cx.root / name
        if not path.is_file():
            continue
        text, _ = _read_why(cx.root, path)
        if text:
            urls.update(m.group(0).rstrip(".,);") for m in _URL_RE.finditer(text))
    return {
        "verdict": "skip",
        "reason": (
            "URL liveness is 未検証 — this script does not fetch URLs. The shared "
            "checker exists (skills/skill-health/scripts/url_liveness.py, RFC-0008) "
            "but the context-sync consumer is deferred by ADR-0052 Decision 5; feed "
            "these URLs to it with --urls-from to check them"
        ),
        "urls": sorted(urls)[:_MAX_ITEMS],
        "count": len(urls),
    }

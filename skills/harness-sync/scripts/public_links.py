"""Pre-publish check for links from a public repo's root docs to the owner's GitHub repos.

A link `https://github.com/<owner>/<repo>[/(blob|tree)/<ref>/<path>]` breaks when the
target repo is private, renamed or deleted, or when the path moved inside it. The sync
moves only `skills/<name>/`, so these links break from the *other* side and nothing in
the sync notices. This script checks them before a commit.

Scanned files (repo root): README*.md, llms.txt, llms-full.txt, CHANGELOG.md.
Fenced code blocks are skipped (example URLs in code are not links).

Checks per link to `<owner>`:
  * the repo is public under that exact name (private / unknown are reported apart)
  * with a path: the path exists at that ref — asked of GitHub first
    (`gh api repos/<owner>/<repo>/contents/<path>?ref=<ref>`), because a local
    clone that was not fetched still has a path the remote moved. The clone
    (`--clones/<repo>`, `git cat-file -e origin/<ref>:<path>`) answers only when
    gh cannot (offline, gh missing)

Contract (same as context-sync's gate):
  exit 0  clean — prints how many links were checked
  exit 3  violations — one line per broken link (`file:line: reason: url`)
  exit 2  could not run (bad root, repo list unavailable)
A path that could not be checked (no clone, gh failed) is a violation, not a pass:
an unverified link reported as clean is the silent failure this gate exists for.

stdlib only. Reads the repo list once: `gh repo list <owner> --limit 500 --json
name,visibility`, or `--repos-json FILE` with the same shape (tests, offline use).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote

ROOT_DOCS = ("llms.txt", "llms-full.txt", "CHANGELOG.md")
_DEFAULT_REFS = ("main", "master", "HEAD")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
# Trailing `)`, `>`, `.`, `,` and quotes end a URL in Markdown / prose, not belong to it.
_URL_TAIL = ".,;:)>\"'`*_"


@dataclass(frozen=True)
class Link:
    file: str
    line: int
    url: str
    repo: str
    ref: str | None
    path: str | None


def _url_re(owner: str) -> re.Pattern[str]:
    o = re.escape(owner)
    return re.compile(
        rf"https?://(?:github\.com/{o}/(?P<repo>[A-Za-z0-9._-]+)"
        rf"(?:/(?:blob|tree)/(?P<ref>[^/\s#?)]+)(?:/(?P<path>[^\s#?)\]]+))?)?"
        rf"|raw\.githubusercontent\.com/{o}/(?P<rrepo>[A-Za-z0-9._-]+)"
        rf"/(?P<rref>[^/\s]+)/(?P<rpath>[^\s#?)\]]+))",
        re.IGNORECASE,
    )


def _doc_files(root: Path) -> list[Path]:
    return sorted(root.glob("README*.md")) + [root / n for n in ROOT_DOCS if (root / n).is_file()]


def extract_links(root: Path, owner: str) -> list[Link]:
    pat = _url_re(owner)
    out: list[Link] = []
    for f in _doc_files(root):
        in_fence = False
        for no, text in enumerate(f.read_text(encoding="utf-8").splitlines(), start=1):
            if _FENCE_RE.match(text):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in pat.finditer(text):
                repo = (m.group("repo") or m.group("rrepo")).removesuffix(".git")
                ref = m.group("ref") or m.group("rref")
                path = m.group("path") or m.group("rpath")
                if path:
                    path = unquote(path.rstrip(_URL_TAIL)).rstrip("/") or None
                elif ref:
                    ref = ref.rstrip(_URL_TAIL)
                out.append(
                    Link(
                        f.name, no, m.group(0).rstrip(_URL_TAIL), repo.rstrip(_URL_TAIL), ref, path
                    )
                )
    return out


def load_repos(owner: str, repos_json: Path | None) -> dict[str, str]:
    """lower-cased repo name → visibility ("PUBLIC" / "PRIVATE" / "INTERNAL")."""
    if repos_json is not None:
        data = json.loads(repos_json.read_text(encoding="utf-8"))
    else:
        proc = subprocess.run(
            ["gh", "repo", "list", owner, "--limit", "500", "--json", "name,visibility"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"gh repo list failed: {proc.stderr.strip()}")
        data = json.loads(proc.stdout)
    return {d["name"].lower(): d["visibility"].upper() for d in data}


def path_exists(owner: str, repo: str, ref: str, path: str, clones: Path | None) -> bool | None:
    """True / False when decided, None when it could not be checked."""
    try:
        proc = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{owner}/{repo}/contents/{quote(path)}?ref={quote(ref)}",
                "--silent",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            return True
        if "404" in proc.stderr or "Not Found" in proc.stderr:
            return False
    except FileNotFoundError:
        pass  # no gh: the clone is the only witness left
    clone = clones / repo if clones else None
    if clone and (clone / ".git").exists():
        for rev in (f"origin/{ref}", ref):
            done = subprocess.run(
                ["git", "-C", str(clone), "cat-file", "-e", f"{rev}:{path}"],
                capture_output=True,
                check=False,
            )
            if done.returncode == 0:
                return True
        return False
    return None


def check(
    links: list[Link],
    repos: dict[str, str],
    owner: str,
    clones: Path | None,
    root: Path | None = None,
) -> list[str]:
    """`root` is the repo being published: its links to itself on the default branch are
    checked against the working tree, because this runs before the commit and the push,
    when a page added in the same change does not exist on GitHub yet."""
    out: list[str] = []
    cache: dict[tuple[str, str, str], bool | None] = {}
    for ln in links:
        where = f"{ln.file}:{ln.line}"
        vis = repos.get(ln.repo.lower())
        if vis is None:
            out.append(f"{where}: repo not found under {owner} (renamed or deleted?): {ln.url}")
            continue
        if vis != "PUBLIC":
            out.append(f"{where}: repo is {vis.lower()}: {ln.url}")
            continue
        if not (ln.ref and ln.path):
            continue
        if root is not None and ln.repo.lower() == root.name.lower() and ln.ref in _DEFAULT_REFS:
            if not (root / ln.path).exists():
                out.append(f"{where}: path not found in the working tree: {ln.url}")
            continue
        key = (ln.repo, ln.ref, ln.path)
        if key not in cache:
            cache[key] = path_exists(owner, ln.repo, ln.ref, ln.path, clones)
        if cache[key] is False:
            out.append(f"{where}: path not found at {ln.ref}: {ln.url}")
        elif cache[key] is None:
            out.append(f"{where}: path could not be checked (no clone, gh api failed): {ln.url}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--root", required=True, help="public repo to check")
    ap.add_argument("--owner", required=True, help="GitHub owner whose links are checked")
    ap.add_argument("--clones", help="directory holding local clones named <repo>")
    ap.add_argument("--repos-json", help="repo list as JSON [{name, visibility}] instead of gh")
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser()
    if not root.is_dir():
        print(f"public_links: {root} is not a directory", file=sys.stderr)
        return 2
    try:
        repos = load_repos(args.owner, Path(args.repos_json) if args.repos_json else None)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"public_links: could not load the repo list: {exc}", file=sys.stderr)
        return 2
    clones = Path(args.clones).expanduser() if args.clones else None
    links = extract_links(root, args.owner)
    violations = check(links, repos, args.owner, clones, root)
    if violations:
        for v in violations:
            print(f"[public-links] {v}")
        print(f"[public-links] {len(violations)} violation(s)", file=sys.stderr)
        return 3
    print(f"[public-links] {len(links)} link(s) to {args.owner} checked, 0 violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())

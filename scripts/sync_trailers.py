#!/usr/bin/env python3
"""Draft the sync commit body: the trailers of the source commits this sync carries (RFC-0029).

Called by sync-from-local.sh after staging, before the secret and home-directory scans; the
caller scans --out and moves it into the target's git dir on apply. Prints one summary line.

Range: the newest target commit that is a sync (subject `chore: sync from local harness`) or
carries a `Source: <40-hex sha>` line decides where listing starts. With a Source line naming an
ancestor of the source HEAD, the range is that sha..HEAD. Otherwise (first run, a sync committed
without the draft, a sha the source no longer has) it is every source commit since that commit's
committer date. Only commits that touch a synced path are listed: a path in the staging dir, or a
path the target tracks under the managed subtrees (so a commit that deletes a published file is
listed although the file is no longer staged).

Draft shape, one entry per commit, oldest first, entries separated by a blank line:

    <short sha> <subject>
    <copied trailer lines>

    Source: <full sha of the source HEAD>

Copied keys: KEYS below, nothing else. A trailer runs from its `Key:` line to the next blank line
or the next `Key:` line of any key, so wrapped continuation lines travel with it and an
uncopied key (Verified:, Source:, ...) stops it. A `指摘:` trailer absorbs the `Trigger:` /
`Expect:` lines that follow it in the same paragraph and counts as one trailer.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

KEYS = ("Review", "Context", "Decision", "Review-when", "Plan", "指摘", "Trigger", "Expect")
BLOCK_HEAD = "指摘"
BLOCK_TAIL = ("Trigger", "Expect")
KEY_LINE = re.compile(r"^([^\s:]+):(?:\s|$)")
SOURCE_LINE = re.compile(r"^Source: ([0-9a-f]{40})$", re.M)
SYNC_SUBJECT = "chore: sync from local harness"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def has_head(repo: Path) -> bool:
    return git(repo, "rev-parse", "--verify", "-q", "HEAD", check=False).returncode == 0


def last_sync(target: Path) -> tuple[str | None, str | None]:
    """(Source sha or None, committer date) of the newest sync commit; (None, None) if none."""
    if not has_head(target):
        return None, None
    for record in git(target, "log", "--format=%x1e%cI%x00%B").stdout.split("\x1e")[1:]:
        date, _, message = record.partition("\0")
        found = SOURCE_LINE.findall(message)
        if found:
            return found[-1], date
        if message.startswith(SYNC_SUBJECT):
            return None, date
    return None, None


def is_ancestor(source: Path, sha: str) -> bool:
    if git(source, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode != 0:
        return False
    return git(source, "merge-base", "--is-ancestor", sha, "HEAD", check=False).returncode == 0


def candidate_commits(source: Path, target: Path) -> tuple[list[str], str]:
    """Source commits in the sync range, oldest first, and a phrase naming the range basis."""
    base, since = last_sync(target)
    if base is not None:
        if is_ancestor(source, base):
            revs = git(source, "rev-list", "--reverse", "--no-merges", f"{base}..HEAD").stdout
            return revs.split(), f"after Source: {base[:12]}"
        print(
            f"WARN: Source: {base} is not a commit in {source} reachable from HEAD"
            " — falling back to the date of the commit that carries it",
            file=sys.stderr,
        )
    if since is None:
        print(
            "WARN: no Source: line and no sync commit in the target — no source commits listed",
            file=sys.stderr,
        )
        return [], "no previous sync"
    revs = git(source, "rev-list", "--reverse", "--no-merges", f"--since={since}", "HEAD").stdout
    return revs.split(), f"since {since}"


def published_paths(target: Path, subtrees: list[str]) -> set[str]:
    """Paths the target tracks under the managed subtrees (what this sync may delete)."""
    out = git(target, "ls-files", "-z", "--", *subtrees).stdout if has_head(target) else ""
    return {p for p in out.split("\0") if p}


def staged_paths(staging: Path) -> set[str]:
    paths = set()
    for root, _dirs, files in os.walk(staging):
        for name in files:
            paths.add(Path(root, name).relative_to(staging).as_posix())
    return paths


def touched_paths(source: Path, sha: str) -> set[str]:
    out = git(
        source,
        "diff-tree",
        "--no-commit-id",
        "--root",
        "-r",
        "--name-only",
        "--no-renames",
        "-z",
        sha,
    ).stdout
    return {p for p in out.split("\0") if p}


def extract_trailers(body: str) -> list[list[str]]:
    """Copied trailers of one commit body (subject excluded), each as its list of lines."""
    items: list[list[str]] = []
    current: list[str] | None = None
    block_open = False  # the last item is a 指摘 that can still take Trigger / Expect
    for raw in body.splitlines():
        line = raw.rstrip()
        if not line:
            current, block_open = None, False
            continue
        m = KEY_LINE.match(line)
        if m is None:
            if current is not None:
                current.append(line)
            continue
        key = m.group(1)
        if key not in KEYS:
            current, block_open = None, False
        elif key in BLOCK_TAIL and block_open:
            current = items[-1]
            current.append(line)
        else:
            current = [line]
            items.append(current)
            block_open = key == BLOCK_HEAD
    return items


def commit_entry(source: Path, sha: str) -> tuple[str, int]:
    short, subject, message = git(source, "log", "-1", "--format=%h%x00%s%x00%B", sha).stdout.split(
        "\0", 2
    )
    body = message.split("\n\n", 1)[1] if "\n\n" in message else ""
    items = extract_trailers(body)
    lines = [f"{short} {subject}"] + [line for item in items for line in item]
    return "\n".join(lines), len(items)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Draft the sync commit body from source commit trailers."
    )
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--target", type=Path, required=True)
    ap.add_argument("--staging", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--subtrees", nargs="+", required=True)
    args = ap.parse_args()

    try:
        head = git(args.source, "rev-parse", "--verify", "HEAD").stdout.strip()
        commits, basis = candidate_commits(args.source, args.target)
        synced = staged_paths(args.staging) | published_paths(args.target, args.subtrees)
        entries, trailers = [], 0
        for sha in commits:
            if touched_paths(args.source, sha) & synced:
                entry, n = commit_entry(args.source, sha)
                entries.append(entry)
                trailers += n
    except subprocess.CalledProcessError as exc:
        print(
            f"ABORT: git failed while drafting the commit body: {' '.join(exc.cmd)}",
            file=sys.stderr,
        )
        print(exc.stderr.rstrip(), file=sys.stderr)
        return 1

    args.out.write_text("\n\n".join([*entries, f"Source: {head}"]) + "\n", encoding="utf-8")
    print(f"# source commits: {len(entries)}, trailers: {trailers} ({basis})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

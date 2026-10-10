"""Tests for public_links — links from a public repo's root docs to the owner's repos."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import public_links as pl

REPOS = [
    {"name": "Alpha", "visibility": "PUBLIC"},
    {"name": "secret", "visibility": "PRIVATE"},
]


@pytest.fixture
def clones(tmp_path: Path) -> Path:
    """A local clone of `Alpha` whose origin/main has docs/a.md."""
    base = tmp_path / "clones"
    src = tmp_path / "src"
    src.mkdir()
    (src / "docs").mkdir()
    (src / "docs" / "a.md").write_text("x\n", encoding="utf-8")
    git = ["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "init.defaultBranch=main"]
    subprocess.run([*git, "init", "-q", str(src)], check=True)
    subprocess.run([*git, "-C", str(src), "add", "."], check=True)
    subprocess.run([*git, "-C", str(src), "commit", "-qm", "init"], check=True)
    base.mkdir()
    subprocess.run(["git", "clone", "-q", str(src), str(base / "Alpha")], check=True)
    return base


def _repo(tmp_path: Path, readme: str) -> Path:
    root = tmp_path / "pub"
    root.mkdir()
    (root / "README.md").write_text(readme, encoding="utf-8")
    (tmp_path / "repos.json").write_text(json.dumps(REPOS), encoding="utf-8")
    return root


def _run(tmp_path: Path, root: Path, clones: Path | None) -> int:
    argv = ["--root", str(root), "--owner", "me", "--repos-json", str(tmp_path / "repos.json")]
    if clones:
        argv += ["--clones", str(clones)]
    return pl.main(argv)


def test_extract_skips_fences_other_owners_and_trailing_punctuation(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        "See [a](https://github.com/me/alpha/blob/main/docs/a.md#L3).\n"
        "```\nhttps://github.com/me/fenced\n```\n"
        "Other: https://github.com/you/x and https://github.com/me/secret.\n",
    )
    links = pl.extract_links(root, "me")
    assert [(ln.line, ln.repo, ln.ref, ln.path) for ln in links] == [
        (1, "alpha", "main", "docs/a.md"),
        (5, "secret", None, None),
    ]


def test_clean_links_pass(tmp_path: Path, clones: Path, monkeypatch, capsys) -> None:
    _gh(monkeypatch, 0)
    root = _repo(tmp_path, "[a](https://github.com/me/Alpha/blob/main/docs/a.md)\n")
    assert _run(tmp_path, root, clones) == 0
    assert "1 link(s)" in capsys.readouterr().out


def test_private_and_unknown_repos_are_violations(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, "https://github.com/me/secret\nhttps://github.com/me/gone-repo\n")
    assert _run(tmp_path, root, None) == 3
    out = capsys.readouterr().out
    assert "README.md:1: repo is private" in out
    assert "README.md:2: repo not found under me" in out


def _gh(monkeypatch, returncode: int, stderr: str = "", missing: bool = False) -> list:
    calls: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(cmd, **kw):
        if cmd[0] == "gh":
            calls.append(cmd)
            if missing:
                raise FileNotFoundError("gh")
            return subprocess.CompletedProcess(cmd, returncode, "", stderr)
        return real_run(cmd, **kw)

    monkeypatch.setattr(pl.subprocess, "run", fake_run)
    return calls


def test_github_404_wins_over_a_stale_clone_that_still_has_the_path(
    tmp_path: Path, clones: Path, monkeypatch, capsys
) -> None:
    # The clone has docs/a.md, but the remote moved it: the clone must not vouch for it.
    _gh(monkeypatch, 1, "gh: Not Found (HTTP 404)")
    root = _repo(tmp_path, "[x](https://github.com/me/Alpha/blob/main/docs/a.md)\n")
    assert _run(tmp_path, root, clones) == 3
    assert "path not found at main" in capsys.readouterr().out


def test_without_gh_the_clone_decides(tmp_path: Path, clones: Path, monkeypatch, capsys) -> None:
    _gh(monkeypatch, 0, missing=True)
    root = _repo(
        tmp_path,
        "[a](https://github.com/me/Alpha/blob/main/docs/a.md)\n"
        "[b](https://github.com/me/Alpha/tree/main/docs/gone)\n",
    )
    assert _run(tmp_path, root, clones) == 3
    out = capsys.readouterr().out
    assert "README.md:2: path not found" in out
    assert "README.md:1" not in out


def test_path_is_url_encoded_for_the_api(tmp_path: Path, monkeypatch) -> None:
    calls = _gh(monkeypatch, 0)
    root = _repo(tmp_path, "[x](https://github.com/me/Alpha/blob/main/docs/My%20Notes.md)\n")
    assert _run(tmp_path, root, None) == 0
    assert calls[0][2] == "repos/me/Alpha/contents/docs/My%20Notes.md?ref=main"


def test_uncheckable_path_is_a_violation_not_a_pass(tmp_path: Path, monkeypatch, capsys) -> None:
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, "", "network unreachable")

    monkeypatch.setattr(pl.subprocess, "run", fake_run)
    root = _repo(tmp_path, "[x](https://github.com/me/Alpha/blob/main/docs/a.md)\n")
    assert _run(tmp_path, root, None) == 3
    assert "could not be checked" in capsys.readouterr().out


def test_bad_root_exits_two(tmp_path: Path) -> None:
    assert pl.main(["--root", str(tmp_path / "nope"), "--owner", "me"]) == 2


def test_links_to_the_repo_itself_use_the_working_tree(tmp_path: Path, monkeypatch, capsys) -> None:
    # 4b runs before commit and push, so a page added in the same change is not on GitHub yet.
    calls = _gh(monkeypatch, 1, "gh: Not Found (HTTP 404)")
    root = _repo(
        tmp_path,
        "[new](https://github.com/me/pub/blob/main/docs/new.md)\n"
        "[gone](https://github.com/me/pub/blob/main/docs/gone.md)\n",
    )
    (root / "docs").mkdir()
    (root / "docs" / "new.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "repos.json").write_text(
        json.dumps([*REPOS, {"name": "pub", "visibility": "PUBLIC"}]), encoding="utf-8"
    )
    assert _run(tmp_path, root, None) == 3
    out = capsys.readouterr().out
    assert "README.md:2: path not found in the working tree" in out
    assert "README.md:1" not in out
    assert calls == []

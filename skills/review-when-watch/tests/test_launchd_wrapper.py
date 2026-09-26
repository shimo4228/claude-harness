"""scripts/launchd-watch.sh stages the jrp notes so python never opens the iCloud vault.

The uv and notify binaries are replaced by stubs that record what they were given.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "launchd-watch.sh"
HERE = SCRIPT.parents[1]

pytestmark = pytest.mark.skipif(shutil.which("rsync") is None, reason="rsync is not installed")


def stub(path: Path, body: str) -> Path:
    path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def world(tmp_path):
    vault = tmp_path / "vault"
    notes = vault / "daily-research"
    notes.mkdir(parents=True)
    (notes / "2026-09-25_jrp_akc.md").write_text("# jrp note\n", encoding="utf-8")
    (notes / "2026-09-25_old_track.md").write_text("# not jrp\n", encoding="utf-8")
    (notes / "memo.md").write_text("# memo\n", encoding="utf-8")
    env_file = tmp_path / "jrp.env"
    env_file.write_text(f'JRP_VAULT_DIR="{vault}"\nOTHER_SECRET=s3cret\n', encoding="utf-8")
    seen = tmp_path / "uv-seen.txt"
    uv = stub(
        tmp_path / "uv",
        f'{{ printf "%s\\n" "$*"; printf "DIR=%s\\n" "$REVIEW_WHEN_REPORTS_DIR";'
        f' printf "SECRET=%s\\n" "${{OTHER_SECRET:-}}"; pwd; }} > "{seen}"\n',
    )
    told = tmp_path / "notify-seen.txt"
    notify = stub(tmp_path / "notify.sh", f'printf "%s|%s" "$1" "$2" > "{told}"\n')
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path / "home"),
        "JRP_ENV_FILE": str(env_file),
        "REVIEW_WHEN_UV": str(uv),
        "REVIEW_WHEN_NOTIFY": str(notify),
        "REVIEW_WHEN_STAGE": str(tmp_path / "stage"),
    }
    return {"tmp": tmp_path, "vault": vault, "env": env, "seen": seen, "told": told}


def run(world, *args, **env):
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        env={**world["env"], **env},
        capture_output=True,
        text=True,
        check=False,
    )


def test_stages_only_jrp_notes_and_points_python_at_the_stage(world):
    done = run(world, "--preview")
    assert done.returncode == 0, done.stderr
    stage = world["tmp"] / "stage"
    assert sorted(p.name for p in stage.iterdir()) == ["2026-09-25_jrp_akc.md"]
    args, directory, secret, cwd = world["seen"].read_text(encoding="utf-8").splitlines()
    assert args == f"run --project {HERE} --frozen --no-dev python -m scripts.watch --preview"
    assert directory == f"DIR={stage}"
    assert secret == "SECRET="  # the env file's other values stay in the subshell
    assert cwd == str(HERE)


def test_vault_from_the_environment_wins_over_the_env_file(world, tmp_path):
    other = tmp_path / "other"
    (other / "daily-research").mkdir(parents=True)
    (other / "daily-research" / "2026-09-24_jrp_x.md").write_text("x\n", encoding="utf-8")
    assert run(world, JRP_VAULT_DIR=str(other)).returncode == 0
    assert [p.name for p in (tmp_path / "stage").iterdir()] == ["2026-09-24_jrp_x.md"]


def test_unknown_vault_tells_slack_and_stops_before_python(world):
    done = run(world, JRP_ENV_FILE=str(world["tmp"] / "missing.env"))
    assert done.returncode == 2
    assert not world["seen"].exists()
    title, message = world["told"].read_text(encoding="utf-8").split("|", 1)
    assert title == "review-when-watch: 動かせない"
    assert "JRP_VAULT_DIR が分からない" in message


def test_missing_reports_dir_tells_slack(world):
    shutil.rmtree(world["vault"] / "daily-research")
    done = run(world)
    assert done.returncode == 2
    assert "レポートの置き場所が無い" in world["told"].read_text(encoding="utf-8")

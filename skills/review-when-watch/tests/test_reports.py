from __future__ import annotations

import datetime as dt

import pytest

from scripts.reports import ReportsError, list_reports, resolve_reports_dir


def test_override_env_wins(tmp_path, reports_dir):
    env = {"REVIEW_WHEN_REPORTS_DIR": str(reports_dir), "JRP_VAULT_DIR": "/elsewhere"}
    assert resolve_reports_dir(env, tmp_path) == reports_dir


def test_jrp_vault_dir_from_the_environment(tmp_path, reports_dir):
    env = {"JRP_VAULT_DIR": str(reports_dir.parent)}
    assert resolve_reports_dir(env, tmp_path) == reports_dir


def test_jrp_env_file_is_read_not_sourced(tmp_path, reports_dir):
    home = reports_dir.parent.parent  # tmp_path: the vault is <home>/vault
    env_file = home / ".config" / "jrp" / "env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text(
        "TYPESAFE_API_KEY=not-ours\n"
        'export JRP_VAULT_DIR="$HOME/vault"\n'
        "JRP_STORE_DIR=$(touch should-not-run)\n",
        encoding="utf-8",
    )
    assert resolve_reports_dir({}, home) == reports_dir
    assert not (home / "should-not-run").exists()


def test_jrp_env_file_location_can_move(tmp_path, reports_dir):
    env_file = tmp_path / "custom.env"
    env_file.write_text(f"JRP_VAULT_DIR='{reports_dir.parent}'\n", encoding="utf-8")
    assert resolve_reports_dir({"JRP_ENV_FILE": str(env_file)}, tmp_path) == reports_dir


def test_unknown_vault_is_named(tmp_path):
    with pytest.raises(ReportsError, match="JRP_VAULT_DIR が分からない"):
        resolve_reports_dir({}, tmp_path)


def test_vault_without_the_reports_dir_is_named(tmp_path):
    with pytest.raises(ReportsError, match="置き場所が無い"):
        resolve_reports_dir({"JRP_VAULT_DIR": str(tmp_path)}, tmp_path)


def test_list_reports_keeps_the_lookback_window(reports_dir):
    reports = list_reports(reports_dir, dt.date(2026, 9, 25), 3)
    assert [r.name for r in reports] == [
        "2026-09-24_jrp_other.md",
        "2026-09-25_jrp_skill-listing.md",
    ]
    assert reports[1].date == dt.date(2026, 9, 25)
    assert len(reports[1].sha) == 16


def test_list_reports_skips_symlinks_and_bad_dates(tmp_path, reports_dir):
    outside = tmp_path / "secret.md"
    outside.write_text("private\n", encoding="utf-8")
    (reports_dir / "2026-09-25_jrp_link.md").symlink_to(outside)
    (reports_dir / "2026-02-30_jrp_bad.md").write_text("bad date\n", encoding="utf-8")
    names = [r.name for r in list_reports(reports_dir, dt.date(2026, 9, 25), 1)]
    assert names == ["2026-09-25_jrp_skill-listing.md"]

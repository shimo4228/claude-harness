from __future__ import annotations

import datetime as dt
import json

from conftest import NOW, FakeJev

from scripts import watch
from scripts.watch import Settings, State, run, slack_safe


class Recorder:
    """Stands in for Slack. ``ok=False`` plays a webhook that did not take the message."""

    def __init__(self, ok=True):
        self.ok = ok
        self.sent: list[tuple[str, str]] = []

    def __call__(self, title, body):
        self.sent.append((title, body))
        return self.ok


def hits_rfc_0001(condition, report):
    return condition.startswith("RFC-0001") and "HIT" in report


def settings(harness, reports_dir, *, client=None, notify=None, now=NOW, **kw):
    return Settings(
        root=harness,
        env={"REVIEW_WHEN_REPORTS_DIR": str(reports_dir)},
        home=harness,
        now=now,
        notify=notify or Recorder(),
        client_factory=(lambda: client) if client is not None else None,
        **kw,
    )


def rows(harness):
    path = harness / "metrics" / "review-when-watch.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def state_of(harness):
    return State.load(harness / "metrics" / "review-when-watch-state.json")


def test_hit_is_sent_with_numbers_and_every_pair_is_logged(harness, reports_dir):
    client = FakeJev(hit_rule=hits_rfc_0001)
    slack = Recorder()
    assert run(settings(harness, reports_dir, client=client, notify=slack), out=lambda _: None) == 0

    [(title, body)] = slack.sent
    assert title == "review-when: 条件に当たったレポート 1 件"
    assert "RFC-0001 最初の提案 ← 2026-09-25_jrp_skill-listing.md（met 0.93 / event）" in body

    logged = rows(harness)
    pairs = [r for r in logged if r["kind"] == "pair"]
    assert len(pairs) == 3 * 2  # RFC-0001, RFC-0003, ADR-0044 × two reports in the window
    assert [r for r in logged if r["kind"] == "canary"][0]["hit"] is True
    hit = next(r for r in pairs if r["hit"])
    assert hit["condition"] == "RFC-0001"
    assert hit["threshold"] == 0.5
    assert "text" not in hit and "HIT" not in json.dumps(hit)  # report text never logged

    state = state_of(harness)
    assert len(state.processed) == 2
    assert state.last_notified == NOW.isoformat()


def test_first_run_without_hits_says_it_started_then_goes_quiet(harness, reports_dir):
    slack = Recorder()
    run(settings(harness, reports_dir, client=FakeJev(), notify=slack), out=lambda _: None)
    assert slack.sent[0][0] == "review-when-watch: 稼働を始めた"
    assert "条件 3 本、今回のレポート 2 本" in slack.sent[0][1]

    later = NOW + dt.timedelta(hours=12)
    client = FakeJev()
    run(settings(harness, reports_dir, client=client, notify=slack, now=later), out=lambda _: None)
    assert len(slack.sent) == 1  # nothing new, nothing wrong: silence
    assert len(client.calls) == 2  # only the canary pair was asked; reports were done


def test_weekly_line_when_nothing_hit(harness, reports_dir):
    slack = Recorder()
    run(settings(harness, reports_dir, client=FakeJev(), notify=slack), out=lambda _: None)
    new = reports_dir / "2026-10-02_jrp_next.md"
    new.write_text("# 来週のレポート\n", encoding="utf-8")
    week = NOW + dt.timedelta(days=7)
    run(settings(harness, reports_dir, client=FakeJev(), notify=slack, now=week), out=print)
    title, body = slack.sent[-1]
    assert title == "review-when-watch: 今週は当たりなし"
    assert "レポート 1 本 × 条件 3 本（3 組）" in body
    assert "最高値 met 0.12" in body


def test_failed_pair_keeps_report_for_retry_and_reports_once_a_day(harness, reports_dir):
    slack = Recorder()
    run(settings(harness, reports_dir, client=FakeJev(), notify=slack), out=lambda _: None)
    (reports_dir / "2026-09-25_jrp_new.md").write_text("# 新規\n", encoding="utf-8")

    def fails_on_new(condition, report):
        return report.startswith("2026-09-25_jrp_new.md") and condition.startswith("ADR")

    later = NOW + dt.timedelta(hours=1)
    code = run(
        settings(
            harness, reports_dir, client=FakeJev(fail_rule=fails_on_new), notify=slack, now=later
        ),
        out=lambda _: None,
    )
    assert code == 1
    assert slack.sent[-1][0] == "review-when-watch: 失敗"
    assert "2026-09-25_jrp_new.md: 1 件失敗（次回再試行）" in slack.sent[-1][1]
    assert "2026-09-25_jrp_new.md" not in state_of(harness).processed
    failed = [r for r in rows(harness) if r.get("reason")]
    assert failed[0]["reason"] == "RuntimeError: HTTP 500"

    sent = len(slack.sent)
    again = later + dt.timedelta(hours=2)
    run(
        settings(
            harness, reports_dir, client=FakeJev(fail_rule=fails_on_new), notify=slack, now=again
        ),
        out=lambda _: None,
    )
    assert len(slack.sent) == sent  # same day: not repeated


def test_undelivered_hits_are_carried_to_the_next_run(harness, reports_dir):
    down = Recorder(ok=False)
    run(
        settings(harness, reports_dir, client=FakeJev(hit_rule=hits_rfc_0001), notify=down),
        out=lambda _: None,
    )
    assert state_of(harness).pending
    assert state_of(harness).last_notified is None

    up = Recorder()
    later = NOW + dt.timedelta(hours=12)
    run(settings(harness, reports_dir, client=FakeJev(), notify=up, now=later), out=lambda _: None)
    title, body = up.sent[0]
    assert title == "review-when: 条件に当たったレポート 1 件"
    assert body.startswith("（前回届かなかった分）• RFC-0001")
    assert state_of(harness).pending == []


def test_canary_drift_is_reported(harness, reports_dir):
    slack = Recorder()
    code = run(
        settings(harness, reports_dir, client=FakeJev(canary=(0.3, 0.1)), notify=slack),
        out=lambda _: None,
    )
    assert code == 1
    assert "canary がずれた（通るべき 0.30 / 落ちるべき 0.10" in slack.sent[0][1]


def test_preview_writes_nothing_and_sends_nothing(harness, reports_dir):
    slack = Recorder()
    printed: list[str] = []
    run(
        settings(
            harness, reports_dir, client=FakeJev(hit_rule=hits_rfc_0001), notify=slack, preview=True
        ),
        out=printed.append,
    )
    assert slack.sent == []
    assert not (harness / "metrics").exists()
    assert any("条件に当たったレポート 1 件" in line for line in printed)


def test_dry_run_counts_without_asking(harness, reports_dir):
    printed: list[str] = []

    def never():
        raise AssertionError("dry run must not build a client")

    s = settings(harness, reports_dir, dry_run=True)
    s.client_factory = never
    assert run(s, out=printed.append) == 0
    assert "条件 3 本 × レポート 2 本 = 6 組" in printed[0]


def test_unresolvable_reports_dir_is_told_once_a_day(harness, tmp_path):
    slack = Recorder()
    s = Settings(
        root=harness,
        env={"REVIEW_WHEN_REPORTS_DIR": str(tmp_path / "missing")},
        home=harness,
        now=NOW,
        notify=slack,
    )
    assert run(s, out=lambda _: None) == 2
    assert run(s, out=lambda _: None) == 2
    assert [t for t, _ in slack.sent] == ["review-when-watch: 動かせない"]


def test_missing_api_key_stops_before_any_request(harness, reports_dir, tmp_path):
    from conftest import REPO_ROOT

    # The real router's jev_client, a HOME with no key file and no key in the environment.
    (harness / "skills" / "jev-skill-router" / "scripts").mkdir(parents=True)
    (harness / "skills" / "jev-skill-router" / "scripts" / "jev_client.py").write_text(
        (REPO_ROOT / "skills" / "jev-skill-router" / "scripts" / "jev_client.py").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    slack = Recorder()
    s = Settings(
        root=harness,
        env={"REVIEW_WHEN_REPORTS_DIR": str(reports_dir), "HOME": str(tmp_path / "home")},
        home=tmp_path / "home",
        now=NOW,
        notify=slack,
    )
    assert run(s, out=lambda _: None) == 2
    assert "API キーが無い" in slack.sent[0][1]


def test_missing_client_module_is_a_setup_failure(harness, reports_dir):
    slack = Recorder()
    s = settings(harness, reports_dir, notify=slack)
    assert run(s, out=lambda _: None) == 2
    assert "jev_client を読めない" in slack.sent[0][1]


def test_slack_safe_neutralises_mentions_links_and_control_chars():
    assert slack_safe("<!channel> a&b\nc") == "&lt;!channel&gt; a&amp;b c"
    assert slack_safe("x" * 200, limit=10) == "x" * 9 + "…"


def test_state_prunes_old_entries_and_survives_garbage(harness):
    path = harness / "metrics" / "review-when-watch-state.json"
    path.parent.mkdir()
    path.write_text("not json", encoding="utf-8")
    assert State.load(path).processed == {}
    state = State(
        processed={
            "old": {"sha": "a", "ts": (NOW - dt.timedelta(days=40)).isoformat()},
            "new": {"sha": "b", "ts": NOW.isoformat()},
            "bad": {"sha": "c", "ts": "yesterday"},
        }
    )
    state.prune(NOW)
    assert set(state.processed) == {"new"}


def test_slack_notifier_runs_the_harness_script(tmp_path):
    root = tmp_path
    (root / "scripts").mkdir()
    seen = root / "seen.txt"
    (root / "scripts" / "notify-slack.sh").write_text(
        f'printf "%s|%s" "$1" "$2" > "{seen}"\nexit "${{FAIL:-0}}"\n', encoding="utf-8"
    )
    assert watch.slack_notifier(root)("t", "b") is True
    assert seen.read_text(encoding="utf-8") == "t|b"
    (root / "scripts" / "notify-slack.sh").write_text("exit 1\n", encoding="utf-8")
    assert watch.slack_notifier(root)("t", "b") is False


def test_main_dry_run(harness, reports_dir, monkeypatch, capsys):
    monkeypatch.setenv("REVIEW_WHEN_REPORTS_DIR", str(reports_dir))
    assert watch.main(["--root", str(harness), "--dry-run", "--lookback-days", "100000"]) == 0
    out = capsys.readouterr().out
    assert "レポート 3 本" in out
    assert "2026-09-10_jrp_old.md" in out


def test_retry_asks_only_the_missing_pairs_and_sends_a_hit_once(harness, reports_dir):
    slack = Recorder()
    run(settings(harness, reports_dir, client=FakeJev(), notify=slack), out=lambda _: None)
    (reports_dir / "2026-09-25_jrp_cc-new.md").write_text("# 新規 HIT\n", encoding="utf-8")

    def adr_fails(condition, report):
        return report.startswith("2026-09-25_jrp_cc-new.md") and condition.startswith("ADR")

    first = NOW + dt.timedelta(hours=1)
    run(
        settings(
            harness,
            reports_dir,
            client=FakeJev(hit_rule=hits_rfc_0001, fail_rule=adr_fails),
            notify=slack,
            now=first,
        ),
        out=lambda _: None,
    )
    hit_titles = [t for t, _ in slack.sent if t.startswith("review-when: 条件に当たった")]
    assert len(hit_titles) == 1
    assert "1 件失敗（次回再試行）" in slack.sent[-1][1]  # the failure rides on the hit message

    # Next day the ADR pair succeeds. Only that pair is asked; the RFC hit is not sent again.
    retry = FakeJev(hit_rule=hits_rfc_0001)
    nxt = first + dt.timedelta(days=1)
    run(settings(harness, reports_dir, client=retry, notify=slack, now=nxt), out=lambda _: None)
    asked = [c["state"]["condition"].split(":")[0] for c in retry.calls]
    assert asked == ["CANARY", "CANARY", "ADR-0044"]
    assert [t for t, _ in slack.sent if t.startswith("review-when: 条件に当たった")] == hit_titles
    state = state_of(harness)
    assert state.partial == {}
    assert "2026-09-25_jrp_cc-new.md" in state.processed
    pair_rows = [r for r in rows(harness) if r.get("report") == "2026-09-25_jrp_cc-new.md"]
    assert sum(r["condition"] == "RFC-0001" for r in pair_rows) == 1  # logged once too


def test_failure_line_escapes_the_report_name(harness, reports_dir):
    slack = Recorder()
    run(settings(harness, reports_dir, client=FakeJev(), notify=slack), out=lambda _: None)
    (reports_dir / "2026-09-25_jrp_<!channel>.md").write_text("# x\n", encoding="utf-8")

    def fails(condition, report):
        return report.startswith("2026-09-25_jrp_<")

    later = NOW + dt.timedelta(hours=1)
    run(
        settings(harness, reports_dir, client=FakeJev(fail_rule=fails), notify=slack, now=later),
        out=lambda _: None,
    )
    body = slack.sent[-1][1]
    assert "2026-09-25_jrp_&lt;!channel&gt;.md: 3 件失敗" in body
    assert "<!channel>" not in body


def test_a_ticked_note_is_not_judged_again(harness, reports_dir):
    """jrp notes change after they are written (the author ticks them); the name is the key."""
    slack = Recorder()
    run(
        settings(harness, reports_dir, client=FakeJev(hit_rule=hits_rfc_0001), notify=slack),
        out=lambda _: None,
    )
    note = reports_dir / "2026-09-25_jrp_skill-listing.md"
    note.write_text(note.read_text(encoding="utf-8") + "- [x] 読んだ\n", encoding="utf-8")
    again = FakeJev(hit_rule=hits_rfc_0001)
    later = NOW + dt.timedelta(hours=20)
    run(settings(harness, reports_dir, client=again, notify=slack, now=later), out=lambda _: None)
    assert len(again.calls) == 2  # canary only
    assert sum(t.startswith("review-when: 条件に当たった") for t, _ in slack.sent) == 1

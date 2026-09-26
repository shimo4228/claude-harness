"""Entry point: judge each new report against every review-when condition, then tell the author.

Run by launchd once a day at 06:10, after jev-research-pipeline's 05:00 run, through
scripts/launchd-watch.sh (which stages the notes out of the iCloud vault). Each run is
idempotent: a note is judged once, and only marked done when every pair succeeded, so a failed
pair is retried on the next run.

What reaches the author (Slack, through scripts/notify-slack.sh):

- hits — pairs whose ``met`` reached the threshold, with the raw numbers;
- the first run, so the wiring is confirmed once;
- a weekly line when nothing hit, with the highest reading of the week — a job that never
  speaks is indistinguishable from a dead one (the reason this runs in production, ADR-0080);
- failures (no config, no key, failed requests, a canary that moved), at most once a day.

Every pair's raw reading goes to ``metrics/review-when-watch.jsonl`` whether it hit or not.
Report text never goes to the log or to Slack — only file names and numbers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.conditions import Condition, load_conditions
from scripts.judge import (
    MET_THRESHOLD,
    MODEL,
    QUESTION_HASH,
    WATCH_VERSION,
    CanaryResult,
    Client,
    Reading,
    judge_pair,
    load_jev_client,
    run_canary,
)
from scripts.reports import Report, ReportsError, list_reports, resolve_reports_dir

LOOKBACK_DAYS = 3
HEARTBEAT_DAYS = 7
#: Processed-report entries older than this are dropped; they are far outside the lookback.
STATE_RETENTION_DAYS = 30
MAX_HIT_LINES = 10

Notifier = Callable[[str, str], bool]
ClientFactory = Callable[[], Client]


# ---------------------------------------------------------------------------- state

_EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.UTC)


def _parse(value: object) -> dt.datetime:
    """An aware datetime from a stored ISO string; the epoch for anything unreadable."""
    try:
        parsed = dt.datetime.fromisoformat(str(value))
    except ValueError:
        return _EPOCH
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.UTC)


@dataclass
class State:
    #: Judged reports by file name -> {"sha", "ts"}. The name, not the content, is the
    #: identity: a jrp note is edited after it is written (the author ticks it, the next
    #: morning's run harvests the ticks), and a changed sha would re-judge it and send its
    #: hits again.
    processed: dict[str, dict[str, str]] = field(default_factory=dict)
    last_notified: str | None = None
    last_failure_notice: str | None = None
    since_reports: int = 0
    since_pairs: int = 0
    best: dict[str, Any] | None = None
    #: Lines of a message that did not reach Slack. Sent again, first, on the next run —
    #: the reports behind them are already marked done, so this is their only way out.
    pending: list[str] = field(default_factory=list)
    #: Reports with some pairs still to go: name -> {"sha", "ts", "done": [condition keys]}.
    #: A retry asks only the missing pairs, so a hit is judged — and sent — once.
    partial: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> State:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        processed = data.get("processed")
        best = data.get("best")
        pending = data.get("pending")
        partial = data.get("partial")
        return cls(
            processed=processed if isinstance(processed, dict) else {},
            last_notified=data.get("last_notified"),
            last_failure_notice=data.get("last_failure_notice"),
            since_reports=int(data.get("since_reports") or 0),
            since_pairs=int(data.get("since_pairs") or 0),
            best=best if isinstance(best, dict) else None,
            pending=[str(x) for x in pending] if isinstance(pending, list) else [],
            partial=partial if isinstance(partial, dict) else {},
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(self.__dict__, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)

    def prune(self, now: dt.datetime) -> None:
        cutoff = now - dt.timedelta(days=STATE_RETENTION_DAYS)
        self.processed = {k: v for k, v in self.processed.items() if _parse(v.get("ts")) > cutoff}
        self.partial = {k: v for k, v in self.partial.items() if _parse(v.get("ts")) > cutoff}

    def observe(self, reading: Reading, condition: Condition, report: Report) -> None:
        self.since_pairs += 1
        if self.best is None or reading.met > float(self.best.get("met", -1.0)):
            self.best = {"met": reading.met, "condition": condition.id, "report": report.name}

    def reset_since(self) -> None:
        self.since_reports = 0
        self.since_pairs = 0
        self.best = None


# ---------------------------------------------------------------------------- output


_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def slack_safe(text: str, limit: int = 120) -> str:
    """Neutralise text that did not come from this repo before it reaches Slack.

    Report file names are derived from outside sources. Slack reads ``<!channel>``,
    ``<url|label>`` and ``&`` entities out of plain text, so those three characters are
    escaped (Slack's own rule), control characters dropped, and the length capped.
    """
    text = _CONTROL_RE.sub(" ", text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def append_rows(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def slack_notifier(root: Path) -> Notifier:
    script = root / "scripts" / "notify-slack.sh"

    def notify(title: str, body: str) -> bool:
        try:
            done = subprocess.run(
                ["bash", str(script), title, body],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return done.returncode == 0

    return notify


# ---------------------------------------------------------------------------- run


@dataclass
class Outcome:
    hits: list[tuple[float, str, str, Condition, Report]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    pairs: int = 0
    reports_done: int = 0


def _row(run_id: str, now: dt.datetime, **fields: object) -> dict[str, Any]:
    return {
        "ts": now.isoformat(),
        "run": run_id,
        "watch_version": WATCH_VERSION,
        "model": MODEL,
        "question_hash": QUESTION_HASH,
        "threshold": MET_THRESHOLD,
        **fields,
    }


def _judge_all(
    client: Client,
    conditions: list[Condition],
    reports: list[Report],
    state: State,
    log: Path | None,
    run_id: str,
    now: dt.datetime,
) -> Outcome:
    outcome = Outcome()
    for report in reports:
        rows: list[dict[str, Any]] = []
        failed = 0
        progress = state.partial.get(report.name) or {}
        done = [str(k) for k in progress.get("done") or []]
        for condition in conditions:
            key = f"{condition.id}:{condition.sha}"
            if key in done:
                continue  # judged on an earlier run; its hit, if any, was already sent
            base = {
                "kind": "pair",
                "condition": condition.id,
                "condition_sha": condition.sha,
                "report": report.name,
                "report_sha": report.sha,
            }
            try:
                reading = judge_pair(client, condition, report.name, report.text)
            except Exception as exc:  # one pair failing must not end the run
                failed += 1
                reason = f"{type(exc).__name__}: {exc}"[:200]
                rows.append(_row(run_id, now, **base, hit=False, reason=reason))
                continue
            outcome.pairs += 1
            done.append(key)
            state.observe(reading, condition, report)
            rows.append(
                _row(
                    run_id,
                    now,
                    **base,
                    met=round(reading.met, 4),
                    overlap={k: round(v, 4) for k, v in reading.overlap.items()},
                    truncated=reading.truncated,
                    model_returned=reading.model,
                    usage=reading.usage,
                    hit=reading.hit,
                    reason=None,
                )
            )
            if reading.hit:
                outcome.hits.append(
                    (reading.met, reading.top_overlap, report.name, condition, report)
                )
        if log is not None:
            append_rows(log, rows)
        if failed:
            outcome.errors.append(f"{slack_safe(report.name)}: {failed} 件失敗（次回再試行）")
            state.partial[report.name] = {
                "sha": report.sha,
                "ts": progress.get("ts") or now.isoformat(),
                "done": done,
            }
            continue
        outcome.reports_done += 1
        state.since_reports += 1
        state.partial.pop(report.name, None)
        state.processed[report.name] = {"sha": report.sha, "ts": now.isoformat()}
    return outcome


def _hit_lines(hits: list[tuple[float, str, str, Condition, Report]]) -> list[str]:
    ordered = sorted(hits, key=lambda h: (-h[0], h[3].id, h[2]))
    lines = [
        f"• {c.id} {slack_safe(c.title, 60)} ← {slack_safe(name)}（met {met:.2f} / {overlap}）"
        for met, overlap, name, c, _ in ordered[:MAX_HIT_LINES]
    ]
    if len(ordered) > MAX_HIT_LINES:
        lines.append(f"…ほか {len(ordered) - MAX_HIT_LINES} 件はログにある")
    return lines


def _canary_line(canary: CanaryResult) -> str | None:
    if canary.ok:
        return None
    if canary.error:
        return f"canary が失敗: {slack_safe(canary.error)}"
    return (
        f"canary がずれた（通るべき {canary.positive:.2f} / 落ちるべき {canary.negative:.2f}、"
        f"閾値 {MET_THRESHOLD}）— 閾値より先に質問文と state を疑う"
    )


def _best_line(state: State) -> str:
    if not state.best:
        return "読み値なし"
    b = state.best
    return f"最高値 met {float(b['met']):.2f}（{b['condition']} × {slack_safe(str(b['report']))}）"


def _compose(
    outcome: Outcome,
    canary: CanaryResult,
    state: State,
    now: dt.datetime,
    conditions: int,
    reports_seen: int,
) -> tuple[str, list[str], bool] | None:
    """(title, lines, is_failure_only) of the one message to send, or None for silence."""
    trouble = [line for line in [_canary_line(canary), *outcome.errors] if line]
    carried = [f"（前回届かなかった分）{line}" for line in state.pending]
    footer = "ログ: ~/.claude/metrics/review-when-watch.jsonl（全組の生の読み値）"
    if outcome.hits or carried:
        lines = carried + _hit_lines(outcome.hits) + trouble + [footer]
        count = len(outcome.hits) + len(carried)
        return f"review-when: 条件に当たったレポート {count} 件", lines, False
    if state.last_notified is None:
        lines = [
            f"条件 {conditions} 本、今回のレポート {reports_seen} 本。当たりなし。",
            f"閾値 met ≥ {MET_THRESHOLD} は仮置き（較正前）。当たりが無い週は週 1 回だけ知らせる。",
            *trouble,
            footer,
        ]
        return "review-when-watch: 稼働を始めた", lines, False
    if now - _parse(state.last_notified) >= dt.timedelta(days=HEARTBEAT_DAYS):
        lines = [
            f"{HEARTBEAT_DAYS} 日間当たりなし。レポート {state.since_reports} 本 × 条件 "
            f"{conditions} 本（{state.since_pairs} 組）。{_best_line(state)}。",
            *trouble,
            footer,
        ]
        return "review-when-watch: 今週は当たりなし", lines, False
    if trouble:
        return "review-when-watch: 失敗", [*trouble, footer], True
    return None


def _deliver(
    message: tuple[str, list[str], bool],
    outcome: Outcome,
    state: State,
    settings: Settings,
    out: Callable[[str], None],
) -> None:
    title, lines, failure_only = message
    out(f"{title}\n" + "\n".join(lines))
    if settings.preview:
        return
    today = settings.now.date().isoformat()
    if failure_only and state.last_failure_notice == today:
        return  # already told today
    delivered = settings.notify(title, "\n".join(lines))
    if failure_only:
        if delivered:
            state.last_failure_notice = today
        return
    if delivered:
        state.pending = []
        state.last_notified = settings.now.isoformat()
        state.reset_since()
    else:
        state.pending = (state.pending + _hit_lines(outcome.hits))[-MAX_HIT_LINES:]


class SetupError(RuntimeError):
    """Something the job needs before it can ask anything (a key, the client module)."""


@dataclass
class Settings:
    root: Path
    env: Mapping[str, str]
    home: Path
    now: dt.datetime
    notify: Notifier
    client_factory: ClientFactory | None = None
    lookback_days: int = LOOKBACK_DAYS
    dry_run: bool = False
    #: Judge and print, but write neither the state nor the log and send nothing — a manual
    #: check must not mark reports done behind the scheduled job's back.
    preview: bool = False

    @property
    def log_path(self) -> Path:
        return self.root / "metrics" / "review-when-watch.jsonl"

    @property
    def state_path(self) -> Path:
        return self.root / "metrics" / "review-when-watch-state.json"


def _default_client_factory(settings: Settings) -> ClientFactory:
    def factory() -> Client:
        try:
            jev = load_jev_client(settings.root)
        except (ImportError, OSError) as exc:
            raise SetupError(f"jev_client を読めない: {exc}") from exc
        key = jev.resolve_api_key(settings.env)
        if not key:
            raise SetupError(
                "TypeSafe の API キーが無い（TYPESAFE_API_KEY か ~/.config/typesafe/api_key）"
            )
        return jev.JevClient(key, base_url=settings.env.get("TYPESAFE_BASE_URL"))

    return factory


def _setup_failed(settings: Settings, state: State, message: str) -> int:
    if settings.dry_run or settings.preview:
        return 2
    today = settings.now.date().isoformat()
    if state.last_failure_notice != today and settings.notify(
        "review-when-watch: 動かせない", message
    ):
        state.last_failure_notice = today
        state.save(settings.state_path)
    return 2


def run(settings: Settings, out: Callable[[str], None] = print) -> int:
    state = State.load(settings.state_path)
    conditions = load_conditions(settings.root)
    try:
        directory = resolve_reports_dir(settings.env, settings.home)
    except ReportsError as exc:
        out(f"review-when-watch: {exc}")
        return _setup_failed(settings, state, str(exc))
    reports = [
        r
        for r in list_reports(directory, settings.now.date(), settings.lookback_days)
        if settings.preview or r.name not in state.processed
    ]
    out(
        f"review-when-watch: 条件 {len(conditions)} 本 × レポート {len(reports)} 本 "
        f"= {len(conditions) * len(reports)} 組（{directory}）"
    )
    if settings.dry_run:
        for report in reports:
            out(f"  {report.name}  {len(report.text)} 字")
        return 0
    factory = settings.client_factory or _default_client_factory(settings)
    try:
        client = factory()
    except SetupError as exc:
        out(f"review-when-watch: {exc}")
        return _setup_failed(settings, state, str(exc))

    run_id = uuid.uuid4().hex[:12]
    log = None if settings.preview else settings.log_path
    canary = run_canary(client)
    if log is not None:
        append_rows(
            log,
            [
                _row(
                    run_id,
                    settings.now,
                    kind="canary",
                    positive=canary.positive,
                    negative=canary.negative,
                    reason=canary.error,
                    hit=canary.ok,
                )
            ],
        )
    outcome = _judge_all(client, conditions, reports, state, log, run_id, settings.now)
    state.prune(settings.now)
    message = _compose(outcome, canary, state, settings.now, len(conditions), len(reports))
    if message is not None:
        _deliver(message, outcome, state, settings, out)
    if not settings.preview:
        state.save(settings.state_path)
    out(f"review-when-watch: {outcome.pairs} 組を判定、当たり {len(outcome.hits)} 件")
    return 1 if (outcome.errors or not canary.ok) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="review-when conditions × daily-research")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--lookback-days", type=int, default=LOOKBACK_DAYS)
    parser.add_argument(
        "--dry-run", action="store_true", help="数えて表示するだけ。Jev も Slack も呼ばない"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Jev に聞いて表示するだけ。状態・ログを書かず Slack にも送らない",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    settings = Settings(
        root=root,
        env=os.environ,
        home=Path.home(),
        now=dt.datetime.now(dt.UTC).astimezone(),
        notify=slack_notifier(root),
        lookback_days=max(1, args.lookback_days),
        dry_run=args.dry_run,
        preview=args.preview,
    )
    return run(settings)


if __name__ == "__main__":
    sys.exit(main())

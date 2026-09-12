#!/usr/bin/env python3
"""collect_snapshot.py — deterministic GitHub growth observations → .growth/SNAPSHOT.json.

Collector role of the Astra–Fable growth loop (skill: growth-fable). It measures; it never
interprets. Every number carries its source and window so the reader (Fable) can re-derive it.

Sources, in order of preference:
  1. Hub repo traffic JSONL (`<hub>/traffic/data/<repo>.jsonl`) — the existing daily GitHub
     Actions collector (`shimo4228/shimo4228` `.github/workflows/traffic-daily.yml`). Clones /
     views per day, long history, append-only. Read locally; `--pull` refreshes the clone first.
  2. Live `gh api` reads — followers, per-repo stars/forks/watchers, `starred_at` timestamps
     (star velocity without local history), 14-day referrers (push access required), GitHub
     code-search mention counts (query recorded verbatim so the count is reproducible).

Only the followers count has no timestamped source, so its history is the collector's own
`series` inside SNAPSHOT.json (one point per UTC date, deduped, capped). Same for total stars.

Unavailable data is written as null and listed under `errors`; nothing is estimated.

Usage:
  collect_snapshot.py --user shimo4228 --out .growth/SNAPSHOT.json \
      [--hub-dir ~/MyAI_Lab/shimo4228] [--pull] [--repos a,b] [--no-mentions] [--no-referrers]

Exit codes: 0 = snapshot written (possibly with errors[]), 2 = could not write a snapshot.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

SCHEMA_VERSION = 1
SERIES_CAP = 400
WINDOW_DAYS = 14
VELOCITY_WINDOWS = (7, 14, 30)
STAR_TRACK_MIN = 2  # repos with fewer stars than this are listed but not deep-collected
SEARCH_THROTTLE_S = 6.5  # code search allows 10 req/min authenticated; stay under it

JsonDict = dict[str, object]
ApiFn = Callable[[str, dict[str, str] | None, str | None, bool], object]


def as_dict(x: object) -> JsonDict:
    """Narrow an untyped JSON value to a dict (empty dict when it is not one)."""
    return {str(k): v for k, v in x.items()} if isinstance(x, dict) else {}


def as_list(x: object) -> list[object]:
    return list(x) if isinstance(x, list) else []


def as_int(x: object, default: int = 0) -> int:
    return int(x) if isinstance(x, int | float) and not isinstance(x, bool) else default


def as_int_or_none(x: object) -> int | None:
    return int(x) if isinstance(x, int) and not isinstance(x, bool) else None


# ----------------------------------------------------------------------------- gh api layer
def gh_api(path: str, params: dict[str, str] | None, accept: str | None, paginate: bool) -> object:
    """Call `gh api` and return parsed JSON.

    `paginate=True` follows Link headers (--paginate --slurp) — only for bounded list endpoints
    (repo listing, stargazers). Never for search/*: `--paginate` there would walk every result
    page under the 10 req/min code-search limit.
    """
    if path.startswith("search/"):
        time.sleep(SEARCH_THROTTLE_S)
    cmd = ["gh", "api"]
    if paginate:
        cmd += ["--paginate", "--slurp"]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    cmd += ["-X", "GET", path]
    for k, v in (params or {}).items():
        cmd += ["-f", f"{k}={v}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path}: {proc.stderr.strip()[:300]}")
    pages = json.loads(proc.stdout)
    if not paginate:
        return pages
    # --slurp wraps each page in a list; flatten list pages, unwrap single-object pages
    if isinstance(pages, list) and pages and all(isinstance(p, list) for p in pages):
        return [item for page in pages for item in page]
    if isinstance(pages, list) and len(pages) == 1:
        return pages[0]
    return pages


# ----------------------------------------------------------------------------- pure helpers
def parse_iso_date(s: str) -> date:
    return date.fromisoformat(s[:10])


def read_jsonl(path: Path) -> list[JsonDict]:
    rows: list[JsonDict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "date" in obj:
            rows.append(obj)
    return rows


def _sum_window(rows: list[JsonDict], start: date, end: date) -> dict[str, int]:
    """Inclusive [start, end] sums. `uniques_daysum` = sum of daily uniques (not window-unique)."""
    out = {
        "views": 0,
        "views_uniques_daysum": 0,
        "clones": 0,
        "clones_uniques_daysum": 0,
        "days": 0,
    }
    for r in rows:
        d = parse_iso_date(str(r["date"]))
        if d < start or d > end:
            continue
        views = as_dict(r.get("views"))
        clones = as_dict(r.get("clones"))
        out["views"] += as_int(views.get("count"))
        out["views_uniques_daysum"] += as_int(views.get("uniques"))
        out["clones"] += as_int(clones.get("count"))
        out["clones_uniques_daysum"] += as_int(clones.get("uniques"))
        out["days"] += 1
    return out


def traffic_windows(rows: list[JsonDict], today: date, window: int = WINDOW_DAYS) -> JsonDict:
    """Last `window` days vs the `window` days before that, anchored on the newest data date.

    The hub collector skips the current UTC day and back-fills ~48h, so the anchor is the
    latest date present in the file, not `today`; `staleness_days` reports the gap.
    """
    if not rows:
        return {"available": False}
    last = max(parse_iso_date(str(r["date"])) for r in rows)
    cur_start = last - timedelta(days=window - 1)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=window - 1)
    return {
        "available": True,
        "window_days": window,
        "last_date": last.isoformat(),
        "staleness_days": (today - last).days,
        "current": _sum_window(rows, cur_start, last),
        "previous": _sum_window(rows, prev_start, prev_end),
    }


def star_velocity(starred_at: list[str], now: datetime) -> dict[str, int]:
    """Stars gained in each trailing window, from `starred_at` timestamps (no local history)."""
    stamps = [datetime.fromisoformat(s.replace("Z", "+00:00")) for s in starred_at]
    return {
        f"stars_{w}d": sum(1 for t in stamps if t >= now - timedelta(days=w))
        for w in VELOCITY_WINDOWS
    }


def merge_series(
    prev: list[JsonDict], day: date, count: int, cap: int = SERIES_CAP
) -> list[JsonDict]:
    """Append/overwrite the point for `day`, keep sorted by date, cap length (drop oldest)."""
    by_date: dict[str, int] = {}
    for p in prev:
        if "date" in p and "count" in p:
            by_date[str(p["date"])] = as_int(p["count"])
    by_date[day.isoformat()] = count
    series: list[JsonDict] = [{"date": d, "count": c} for d, c in sorted(by_date.items())]
    return series[-cap:]


def series_delta(series: list[JsonDict], today: date, days: int) -> int | None:
    """count(today) − count(at or before today−days). None when no point that old exists."""
    target = today - timedelta(days=days)
    now_pt = next((p for p in reversed(series) if str(p["date"]) == today.isoformat()), None)
    base = None
    for p in series:
        if parse_iso_date(str(p["date"])) <= target:
            base = p
    if now_pt is None or base is None:
        return None
    return as_int(now_pt["count"]) - as_int(base["count"])


def select_tracked(
    repo_stars: dict[str, int], traffic_repos: set[str], explicit: set[str], min_stars: int
) -> list[str]:
    """Repos that get the expensive per-repo reads: traffic-tracked ∪ explicit ∪ stars≥min."""
    chosen = set(traffic_repos) | set(explicit)
    chosen |= {r for r, s in repo_stars.items() if s >= min_stars}
    return sorted(r for r in chosen if r in repo_stars or r in explicit)


# ----------------------------------------------------------------------------- collection
def _safe(errors: list[JsonDict], scope: str, fn: Callable[[], object]) -> object | None:
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 — every failure is recorded, never hidden
        errors.append({"scope": scope, "error": str(e)[:300]})
        return None


def collect_repo_listing(api: ApiFn, user: str, errors: list[JsonDict]) -> dict[str, JsonDict]:
    raw = _safe(
        errors,
        "repos",
        lambda: api(f"users/{user}/repos", {"per_page": "100", "type": "owner"}, None, True),
    )
    out: dict[str, JsonDict] = {}
    for item in as_list(raw):
        r = as_dict(item)
        if not r or r.get("fork"):
            continue
        out[str(r["name"])] = {
            "stars": as_int(r.get("stargazers_count")),
            "forks": as_int(r.get("forks_count")),
            "watchers": as_int(r.get("subscribers_count", r.get("watchers_count"))),
            "pushed_at": r.get("pushed_at"),
            "archived": bool(r.get("archived", False)),
            "description": r.get("description"),
        }
    return out


def collect_repo_detail(
    api: ApiFn,
    user: str,
    repo: str,
    now: datetime,
    errors: list[JsonDict],
    *,
    referrers: bool,
    mentions: bool,
) -> JsonDict:
    detail: JsonDict = {}
    stargazers = _safe(
        errors,
        f"{repo}:stargazers",
        lambda: api(
            f"repos/{user}/{repo}/stargazers",
            {"per_page": "100"},
            "application/vnd.github.star+json",
            True,
        ),
    )
    if isinstance(stargazers, list):
        stamps = [str(as_dict(s)["starred_at"]) for s in stargazers if "starred_at" in as_dict(s)]
        detail.update(star_velocity(stamps, now))
        detail["last_starred_at"] = max(stamps) if stamps else None
    else:
        detail.update({f"stars_{w}d": None for w in VELOCITY_WINDOWS})
    if referrers:
        refs = _safe(
            errors,
            f"{repo}:referrers",
            lambda: api(f"repos/{user}/{repo}/traffic/popular/referrers", None, None, False),
        )
        detail["referrers_14d"] = (
            [
                {
                    "referrer": r.get("referrer"),
                    "count": r.get("count"),
                    "uniques": r.get("uniques"),
                }
                for r in (as_dict(x) for x in refs)
                if r
            ]
            if isinstance(refs, list)
            else None
        )
    if mentions:
        query = f'"github.com/{user}/{repo}" -user:{user}'
        res = _safe(
            errors,
            f"{repo}:mentions",
            lambda: api("search/code", {"q": query, "per_page": "1"}, None, False),
        )
        detail["code_mentions"] = {
            "total": as_int_or_none(as_dict(res).get("total_count")),
            "query": query,
            "source": "GET /search/code (default branches only; excludes own repos)",
        }
    return detail


def _followers_block(profile: JsonDict, series: list[JsonDict], today: date) -> JsonDict:
    return {
        "count": as_int_or_none(profile.get("followers")),
        "following": as_int_or_none(profile.get("following")),
        "public_repos": as_int_or_none(profile.get("public_repos")),
        "delta_7d": series_delta(series, today, 7),
        "delta_14d": series_delta(series, today, 14),
        "delta_30d": series_delta(series, today, 30),
        "series": series,
        "source": "GET /users/{user}; series = this collector's own daily points",
    }


def _traffic_totals(repos: dict[str, JsonDict]) -> dict[str, int]:
    totals = {"views_14d": 0, "clones_14d": 0, "views_prev14d": 0, "clones_prev14d": 0}
    for r in repos.values():
        t = as_dict(r.get("traffic"))
        if not t.get("available"):
            continue
        cur, prv = as_dict(t.get("current")), as_dict(t.get("previous"))
        totals["views_14d"] += as_int(cur.get("views"))
        totals["clones_14d"] += as_int(cur.get("clones"))
        totals["views_prev14d"] += as_int(prv.get("views"))
        totals["clones_prev14d"] += as_int(prv.get("clones"))
    return totals


def _top_movers(repos: dict[str, JsonDict], limit: int = 5) -> list[JsonDict]:
    movers = [
        (n, as_int(r.get("stars_14d")), r.get("stars"))
        for n, r in repos.items()
        if r.get("tracked") and isinstance(r.get("stars_14d"), int)
    ]
    movers.sort(key=lambda m: (-m[1], m[0]))
    return [{"repo": n, "stars_14d": v, "stars": s} for n, v, s in movers[:limit]]


def _prev_series(prev: JsonDict | None, key: str) -> list[JsonDict]:
    block = as_dict(as_dict(prev).get(key))
    return [as_dict(p) for p in as_list(block.get("series"))]


def build_snapshot(
    api: ApiFn,
    *,
    user: str,
    hub_dir: Path | None,
    prev: JsonDict | None,
    now: datetime,
    explicit_repos: set[str],
    referrers: bool,
    mentions: bool,
) -> JsonDict:
    errors: list[JsonDict] = []
    today = now.date()

    profile = as_dict(_safe(errors, "user", lambda: api(f"users/{user}", None, None, False)))
    followers_now = as_int_or_none(profile.get("followers"))
    f_series = _prev_series(prev, "followers")
    if followers_now is not None:
        f_series = merge_series(f_series, today, followers_now)

    repos = collect_repo_listing(api, user, errors)
    traffic_dir = hub_dir / "traffic" / "data" if hub_dir else None
    traffic_repos = (
        {p.stem for p in traffic_dir.glob("*.jsonl")}
        if traffic_dir and traffic_dir.exists()
        else set()
    )
    tracked = select_tracked(
        {r: as_int(v.get("stars")) for r, v in repos.items()},
        traffic_repos,
        explicit_repos,
        STAR_TRACK_MIN,
    )
    for name in tracked:
        entry = repos.setdefault(name, {"stars": None, "forks": None, "watchers": None})
        entry["tracked"] = True
        entry.update(
            collect_repo_detail(
                api, user, name, now, errors, referrers=referrers, mentions=mentions
            )
        )
        if traffic_dir:
            entry["traffic"] = traffic_windows(read_jsonl(traffic_dir / f"{name}.jsonl"), today)

    stars_total = sum(as_int(v.get("stars")) for v in repos.values())
    s_series = merge_series(_prev_series(prev, "stars_total"), today, stars_total)

    return {
        "schema": SCHEMA_VERSION,
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "user": user,
        "followers": _followers_block(profile, f_series, today),
        "stars_total": {
            "count": stars_total,
            "delta_7d": series_delta(s_series, today, 7),
            "delta_14d": series_delta(s_series, today, 14),
            "series": s_series,
        },
        "traffic_total_tracked": {
            **_traffic_totals(repos),
            "source": "hub traffic/data/*.jsonl (tracked repos)",
        },
        "top_movers_14d": _top_movers(repos),
        "tracked_repos": tracked,
        "repos": repos,
        "sources": {
            "traffic": str(traffic_dir) if traffic_dir else None,
            "star_velocity": "GET /repos/{owner}/{repo}/stargazers "
            "with Accept: application/vnd.github.star+json",
            "referrers": (
                "GET /repos/{owner}/{repo}/traffic/popular/referrers (14-day window, push access)"
                if referrers
                else None
            ),
        },
        "errors": errors,
    }


# ----------------------------------------------------------------------------- CLI
def _git_pull(hub_dir: Path, errors: list[JsonDict]) -> None:
    proc = subprocess.run(  # noqa: S603
        ["git", "-C", str(hub_dir), "pull", "--ff-only", "--quiet"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        errors.append({"scope": "hub:pull", "error": proc.stderr.strip()[:300]})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--hub-dir", type=Path, default=Path.home() / "MyAI_Lab" / "shimo4228")
    ap.add_argument("--pull", action="store_true", help="git pull --ff-only the hub clone first")
    ap.add_argument("--repos", default="", help="comma-separated repos to always deep-collect")
    ap.add_argument("--no-mentions", action="store_true")
    ap.add_argument("--no-referrers", action="store_true")
    args = ap.parse_args(argv)

    pull_errors: list[JsonDict] = []
    hub_dir: Path | None = args.hub_dir if args.hub_dir.exists() else None
    if hub_dir and args.pull:
        _git_pull(hub_dir, pull_errors)

    prev: JsonDict | None = None
    if args.out.exists():
        try:
            prev = json.loads(args.out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pull_errors.append(
                {"scope": "prev", "error": "existing SNAPSHOT.json unreadable; series restarted"}
            )

    snap = build_snapshot(
        gh_api,
        user=args.user,
        hub_dir=hub_dir,
        prev=prev,
        now=datetime.now(UTC),
        explicit_repos={r.strip() for r in args.repos.split(",") if r.strip()},
        referrers=not args.no_referrers,
        mentions=not args.no_mentions,
    )
    if hub_dir is None:
        pull_errors.append(
            {"scope": "hub", "error": f"hub dir not found: {args.hub_dir} (traffic fields absent)"}
        )
    errors = pull_errors + [as_dict(e) for e in as_list(snap.get("errors"))]
    snap["errors"] = errors
    followers = as_dict(snap.get("followers"))
    repos = as_dict(snap.get("repos"))
    if followers.get("count") is None and not repos:
        print("collect_snapshot: no data collected (gh auth?)", file=sys.stderr)  # noqa: T201
        for e in errors:
            print(f"  {e}", file=sys.stderr)  # noqa: T201
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    stars_total = as_dict(snap.get("stars_total"))
    print(  # noqa: T201
        f"snapshot written: {args.out} followers={followers.get('count')} "
        f"(7d {followers.get('delta_7d')}) stars_total={stars_total.get('count')} "
        f"tracked={len(as_list(snap.get('tracked_repos')))} errors={len(errors)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

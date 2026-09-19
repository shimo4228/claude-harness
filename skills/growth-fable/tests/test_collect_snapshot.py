"""Unit tests for collect_snapshot — pure helpers plus build_snapshot with a fake api (no network)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from scripts import collect_snapshot as cs

NOW = datetime(2026, 9, 8, 3, 0, tzinfo=UTC)
TODAY = NOW.date()

# The collector's JSON values are `JsonDict = dict[str, object]`, so every nested read below is
# `object` to the type checker. Narrow through the collector's own boundary helpers
# (scripts/collect_snapshot.py:49-55) in one place instead of scattering casts across assertions.
_d = cs.as_dict  # object -> JsonDict
_l = cs.as_list  # object -> list[object]


def _row(d: str, views: int, clones: int) -> cs.JsonDict:
    return {
        "date": d,
        "views": {"count": views, "uniques": 1},
        "clones": {"count": clones, "uniques": 1},
    }


# ----------------------------------------------------------------------------- traffic windows
@pytest.mark.unit
def test_traffic_windows_anchor_on_last_data_date_not_today():
    rows = [_row(f"2026-08-{d:02d}", 1, 2) for d in range(1, 32)] + [
        _row(f"2026-09-{d:02d}", 3, 4) for d in range(1, 6)
    ]
    out = cs.traffic_windows(rows, TODAY)
    assert out["available"] is True
    assert out["last_date"] == "2026-09-05"
    assert out["staleness_days"] == 3
    # current window = 08-23 .. 09-05 (14 days): 9 Aug days ×1 + 5 Sep days ×3 = 24 views
    assert _d(out["current"])["views"] == 24
    assert _d(out["current"])["days"] == 14
    # previous window = 08-09 .. 08-22: 14 Aug days ×1
    assert _d(out["previous"])["views"] == 14
    assert _d(out["previous"])["clones"] == 28


@pytest.mark.unit
def test_traffic_windows_empty_is_unavailable_not_zero():
    assert cs.traffic_windows([], TODAY) == {"available": False}


# ----------------------------------------------------------------------------- star velocity
@pytest.mark.unit
def test_star_velocity_counts_trailing_windows_from_timestamps():
    stamps = [
        "2026-09-07T00:00:00Z",
        "2026-09-01T00:00:00Z",
        "2026-08-20T00:00:00Z",
        "2026-03-01T00:00:00Z",
    ]
    v = cs.star_velocity(stamps, NOW)
    assert v == {
        "stars_7d": 1,
        "stars_14d": 2,
        "stars_30d": 3,
    }  # 09-01T00 is >7d before NOW (09-08T03)


@pytest.mark.unit
def test_star_velocity_empty():
    assert cs.star_velocity([], NOW) == {"stars_7d": 0, "stars_14d": 0, "stars_30d": 0}


# ----------------------------------------------------------------------------- series
@pytest.mark.unit
def test_merge_series_dedupes_same_day_and_sorts():
    prev: list[cs.JsonDict] = [
        {"date": "2026-09-07", "count": 60},
        {"date": "2026-09-01", "count": 58},
    ]
    out = cs.merge_series(prev, date(2026, 9, 7), 61)
    assert out == [{"date": "2026-09-01", "count": 58}, {"date": "2026-09-07", "count": 61}]


@pytest.mark.unit
def test_merge_series_caps_oldest():
    prev: list[cs.JsonDict] = [{"date": f"2026-01-{d:02d}", "count": d} for d in range(1, 11)]
    out = cs.merge_series(prev, date(2026, 2, 1), 99, cap=3)
    assert [p["date"] for p in out] == ["2026-01-09", "2026-01-10", "2026-02-01"]


@pytest.mark.unit
def test_series_delta_uses_point_at_or_before_target_and_none_when_absent():
    series: list[cs.JsonDict] = [
        {"date": "2026-08-30", "count": 58},
        {"date": "2026-09-05", "count": 60},
        {"date": "2026-09-08", "count": 61},
    ]
    assert cs.series_delta(series, TODAY, 7) == 3  # target 09-01 → uses 08-30 (58)
    assert cs.series_delta(series, TODAY, 3) == 1  # target 09-05 exact
    assert cs.series_delta(series, TODAY, 30) is None  # nothing that old → null, not 0
    assert cs.series_delta(series[:-1], TODAY, 7) is None  # no point for today → null


# ----------------------------------------------------------------------------- tracked selection
@pytest.mark.unit
def test_select_tracked_union_and_unknown_explicit_kept():
    stars = {"a": 0, "b": 5, "c": 1}
    out = cs.select_tracked(stars, traffic_repos={"c", "ghost"}, explicit={"x"}, min_stars=2)
    # b (stars≥2), c (traffic), x (explicit, unknown → kept so its read error is recorded);
    # ghost (traffic file for a repo not in the listing) is dropped
    assert out == ["b", "c", "x"]


# ----------------------------------------------------------------------------- build_snapshot
class FakeApi:
    def __init__(self, responses: dict[str, object], fail: set[str] | None = None) -> None:
        self.responses = responses
        self.fail = fail or set()
        self.calls: list[tuple[str, bool]] = []

    def __call__(
        self, path: str, params: dict | None, accept: str | None, paginate: bool
    ) -> object:
        self.calls.append((path, paginate))
        if path in self.fail:
            raise RuntimeError(f"boom {path}")
        for key, val in self.responses.items():
            if path == key:
                return val
        raise RuntimeError(f"unexpected {path}")


def _hub(tmp_path: Path) -> Path:
    data = tmp_path / "hub" / "traffic" / "data"
    data.mkdir(parents=True)
    (data / "alpha.jsonl").write_text(
        "\n".join(json.dumps(_row(f"2026-08-{d:02d}", 2, 10)) for d in range(10, 32)) + "\n"
    )
    return tmp_path / "hub"


def _responses(user: str = "u") -> dict[str, object]:
    return {
        f"users/{user}": {"followers": 61, "following": 5, "public_repos": 60},
        f"users/{user}/repos": [
            {
                "name": "alpha",
                "stargazers_count": 6,
                "forks_count": 2,
                "subscribers_count": 6,
                "fork": False,
                "pushed_at": "2026-09-07T00:00:00Z",
            },
            {
                "name": "beta",
                "stargazers_count": 0,
                "forks_count": 0,
                "subscribers_count": 0,
                "fork": False,
                "pushed_at": None,
            },
            {"name": "forked", "stargazers_count": 9, "fork": True},
        ],
        f"repos/{user}/alpha/stargazers": [
            {"starred_at": "2026-09-06T00:00:00Z"},
            {"starred_at": "2026-01-01T00:00:00Z"},
        ],
        f"repos/{user}/alpha/traffic/popular/referrers": [
            {"referrer": "github.com", "count": 3, "uniques": 2}
        ],
        "search/code": {"total_count": 4, "items": []},
    }


@pytest.mark.unit
def test_build_snapshot_assembles_sources_and_series(tmp_path: Path):
    api = FakeApi(_responses())
    prev: cs.JsonDict = {
        "followers": {"series": [{"date": "2026-09-01", "count": 58}]},
        "stars_total": {"series": []},
    }
    snap = cs.build_snapshot(
        api,
        user="u",
        hub_dir=_hub(tmp_path),
        prev=prev,
        now=NOW,
        explicit_repos=set(),
        referrers=True,
        mentions=True,
    )
    followers = _d(snap["followers"])
    assert followers["count"] == 61
    assert followers["delta_7d"] == 3
    assert followers["delta_30d"] is None
    assert _l(followers["series"])[-1] == {"date": "2026-09-08", "count": 61}
    assert _d(snap["stars_total"])["count"] == 6  # forks excluded
    assert snap["tracked_repos"] == ["alpha"]
    repos = _d(snap["repos"])
    alpha = _d(repos["alpha"])
    assert alpha["stars_7d"] == 1 and alpha["stars_30d"] == 1
    assert _d(_l(alpha["referrers_14d"])[0])["referrer"] == "github.com"
    mentions = _d(alpha["code_mentions"])
    assert mentions["total"] == 4
    assert '"github.com/u/alpha" -user:u' == mentions["query"]
    traffic = _d(alpha["traffic"])
    assert traffic["available"] is True and traffic["last_date"] == "2026-08-31"
    assert _d(snap["traffic_total_tracked"])["views_14d"] == 28
    assert snap["top_movers_14d"] == [{"repo": "alpha", "stars_14d": 1, "stars": 6}]
    assert "beta" in repos and "tracked" not in _d(repos["beta"])
    assert snap["errors"] == []
    # search is never paginated; listing and stargazers are
    assert ("search/code", False) in api.calls
    assert ("users/u/repos", True) in api.calls
    assert ("repos/u/alpha/stargazers", True) in api.calls


@pytest.mark.unit
def test_build_snapshot_records_errors_and_nulls_instead_of_fabricating(tmp_path: Path):
    api = FakeApi(
        _responses(), fail={"repos/u/alpha/stargazers", "repos/u/alpha/traffic/popular/referrers"}
    )
    snap = cs.build_snapshot(
        api,
        user="u",
        hub_dir=_hub(tmp_path),
        prev=None,
        now=NOW,
        explicit_repos=set(),
        referrers=True,
        mentions=False,
    )
    alpha = _d(_d(snap["repos"])["alpha"])
    assert alpha["stars_7d"] is None and alpha["referrers_14d"] is None
    assert "code_mentions" not in alpha
    scopes = {_d(e)["scope"] for e in _l(snap["errors"])}
    assert scopes == {"alpha:stargazers", "alpha:referrers"}
    assert snap["top_movers_14d"] == []  # no velocity → no movers, not zero movers
    assert _d(snap["followers"])["delta_7d"] is None  # first run: no history


@pytest.mark.unit
def test_build_snapshot_without_hub_dir_has_no_traffic_fields():
    api = FakeApi(_responses())
    snap = cs.build_snapshot(
        api,
        user="u",
        hub_dir=None,
        prev=None,
        now=NOW,
        explicit_repos={"alpha"},
        referrers=False,
        mentions=False,
    )
    assert "traffic" not in _d(_d(snap["repos"])["alpha"])
    assert _d(snap["sources"])["traffic"] is None
    assert _d(snap["traffic_total_tracked"])["views_14d"] == 0


@pytest.mark.unit
def test_build_snapshot_user_failure_yields_null_followers_and_keeps_series():
    api = FakeApi(_responses(), fail={"users/u"})
    prev: cs.JsonDict = {"followers": {"series": [{"date": "2026-09-01", "count": 58}]}}
    snap = cs.build_snapshot(
        api,
        user="u",
        hub_dir=None,
        prev=prev,
        now=NOW,
        explicit_repos=set(),
        referrers=False,
        mentions=False,
    )
    followers = _d(snap["followers"])
    assert followers["count"] is None
    assert followers["series"] == [{"date": "2026-09-01", "count": 58}]
    assert any(_d(e)["scope"] == "user" for e in _l(snap["errors"]))

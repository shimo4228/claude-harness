"""Regression tests for URL liveness evidence.

The verdict vocabulary is the point of this module: `blocked` must never collapse
into `dead`, and a rate-limit burst must stop the run instead of backing off.
No test touches the network — `check_urls` takes an injected `fetch`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import url_liveness as ul


def fetcher(mapping):
    """Build a fetch() over {url: (status, error)}; records call order."""
    calls = []

    def fetch(url, timeout=0):
        calls.append(url)
        return mapping[url]

    fetch.calls = calls
    return fetch


# -- verdict vocabulary -------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    [(s, "live") for s in (200, 201, 204, 301, 302, 308)]
    # 403 bot-rejection is not evidence of absence (cited-source-mirror-verification);
    # neither is a 5xx. Collapsing either into `dead` sends a reader chasing a fine link.
    + [(s, "blocked") for s in (401, 403, 405, 406, 429, 451, 500, 503)]
    + [(s, "dead") for s in (404, 410, 400, 418)],
)
def test_status_maps_to_verdict(status, expected):
    fetch = fetcher({"https://u": (status, None)})
    out = ul.check_urls(["https://u"], fetch=fetch, delay=0)
    assert out["results"][0]["verdict"] == expected
    assert out["results"][0]["status"] == status


def test_connection_error_is_dead_when_other_hosts_answer():
    fetch = fetcher({"https://a": (None, "dns"), "https://b": (200, None)})
    out = ul.check_urls(["https://a", "https://b"], fetch=fetch, delay=0)
    verdicts = {r["url"]: r["verdict"] for r in out["results"]}
    assert verdicts == {"https://a": "dead", "https://b": "live"}
    assert out["offline_suspected"] is False


# -- offline: unverified, never "dead" ---------------------------------------


def test_all_connection_errors_are_skip_not_dead():
    """A corpus-wide network failure must not print as a corpus of dead links."""
    fetch = fetcher({"https://a": (None, "dns"), "https://b": (None, "timeout")})
    out = ul.check_urls(["https://a", "https://b"], fetch=fetch, delay=0)
    assert [r["verdict"] for r in out["results"]] == ["skip", "skip"]
    assert out["offline_suspected"] is True
    assert out["summary"]["skip"] == 2


def test_offline_flag_skips_every_url_without_fetching():
    fetch = fetcher({})
    out = ul.check_urls(["https://a", "https://b"], fetch=fetch, delay=0, offline=True)
    assert [r["verdict"] for r in out["results"]] == ["skip", "skip"]
    assert fetch.calls == []


def test_a_single_url_corpus_still_gets_the_offline_rescue():
    """A skill that names exactly one URL was the one corpus size with no protection."""
    fetch = fetcher({"https://a": (None, "dns")})
    out = ul.check_urls(["https://a"], fetch=fetch, delay=0)
    assert out["results"][0]["verdict"] == "skip"
    assert out["offline_suspected"] is True


def test_partial_outage_stays_dead_but_is_counted():
    """All-or-nothing is the honest invariant; the count is what shows 17-of-20."""
    fetch = fetcher({"https://a": (200, None), "https://b": (None, "dns")})
    out = ul.check_urls(["https://a", "https://b"], fetch=fetch, delay=0)
    assert out["offline_suspected"] is False
    assert out["connection_failures"] == 1
    assert out["requested"] == 2


def test_malformed_url_is_skip_not_dead():
    """A typo in a SKILL.md is not a broken link."""
    fetch = fetcher({"https://a": (None, f"{ul.MALFORMED}:InvalidURL")})
    out = ul.check_urls(["https://a"], fetch=fetch, delay=0)
    assert out["results"][0]["verdict"] == "skip"
    assert "InvalidURL" in out["results"][0]["note"]
    assert out["offline_suspected"] is False


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:9/admin",
        "http://localhost:9/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]:9/",
        "https://0.0.0.0/",
    ],
)
def test_internal_addresses_are_skipped_without_being_requested(url):
    """Any SKILL.md can put a line in the corpus; the audit must not probe this host."""
    fetch = fetcher({})
    out = ul.check_urls([url], fetch=fetch, delay=0)
    assert fetch.calls == []
    assert out["results"][0]["verdict"] == "skip"
    assert out["results"][0]["note"] == "internal address, not checked"


def test_redirects_are_not_followed():
    """One request per URL is the pacing invariant *and* the loopback defence: urllib
    walks a whole chain inside one open(), unbounded by the caller's delay."""
    assert ul._NoRedirect().redirect_request(None, None, 302, "", {}, "http://127.0.0.1/") is None


def test_a_redirect_status_is_live_not_a_second_request():
    fetch = fetcher({"https://a": (302, None)})
    out = ul.check_urls(["https://a"], fetch=fetch, delay=0)
    assert fetch.calls == ["https://a"]
    assert out["results"][0]["verdict"] == "live"


def test_unparseable_url_is_skip_and_never_requested():
    """`http://[::1` raised out of urlsplit before any handler and aborted the audit."""
    fetch = fetcher({})
    out = ul.check_urls(["http://[::1"], fetch=fetch, delay=0)
    assert fetch.calls == []
    assert out["results"][0]["verdict"] == "skip"
    assert "malformed" in out["results"][0]["note"]


def test_public_hosts_are_not_treated_as_internal():
    assert ul.is_internal_host("https://93.184.216.34/x") is False


def test_a_url_without_a_host_is_treated_as_internal():
    assert ul.is_internal_host("http:///nowhere") is True


# -- rate limit is a policy signal, not a transient error ---------------------


def test_consecutive_rate_limits_halt_the_run():
    """rules/common/debugging.md: stop and report, never back off and continue."""
    fetch = fetcher({"https://a": (429, None), "https://b": (429, None), "https://c": (200, None)})
    out = ul.check_urls(
        ["https://a", "https://b", "https://c"], fetch=fetch, delay=0, rate_limit_threshold=2
    )
    assert out["halted"] is True
    assert "rate limit" in out["halt_reason"]
    assert fetch.calls == ["https://a", "https://b"]  # "https://c" was never requested
    assert out["results"][2] == {
        "url": "https://c",
        "status": None,
        "verdict": "skip",
        "note": "not checked: run halted",
    }


def test_rate_limit_streak_resets_on_success():
    fetch = fetcher(
        {
            "https://a": (429, None),
            "https://b": (200, None),
            "https://c": (429, None),
            "https://d": (200, None),
        }
    )
    out = ul.check_urls(
        ["https://a", "https://b", "https://c", "https://d"],
        fetch=fetch,
        delay=0,
        rate_limit_threshold=2,
    )
    assert out["halted"] is False
    assert fetch.calls == ["https://a", "https://b", "https://c", "https://d"]


def test_no_retry_is_attempted():
    """Retrying a 429 is exactly the burst the rule forbids — one request per URL."""
    fetch = fetcher({"https://a": (429, None)})
    ul.check_urls(["https://a"], fetch=fetch, delay=0, rate_limit_threshold=99)
    assert fetch.calls == ["https://a"]


# -- evidence contract --------------------------------------------------------


def test_summary_counts_every_verdict():
    fetch = fetcher({"https://a": (200, None), "https://b": (404, None), "https://c": (403, None)})
    out = ul.check_urls(["https://a", "https://b", "https://c"], fetch=fetch, delay=0)
    assert out["summary"] == {"live": 1, "dead": 1, "blocked": 1, "skip": 0}


def test_duplicate_urls_are_requested_once():
    fetch = fetcher({"https://a": (200, None)})
    out = ul.check_urls(["https://a", "https://a"], fetch=fetch, delay=0)
    assert fetch.calls == ["https://a"]
    assert len(out["results"]) == 1


def test_blank_and_non_http_urls_are_skipped_without_fetching():
    fetch = fetcher({"https://ok": (200, None)})
    out = ul.check_urls(["", "  ", "ftp://x", "https://ok"], fetch=fetch, delay=0)
    assert fetch.calls == ["https://ok"]
    verdicts = [(r["url"], r["verdict"]) for r in out["results"]]
    assert ("ftp://x", "skip") in verdicts


def test_cli_reads_urls_from_a_file_and_exits_zero(tmp_path, capsys):
    listing = tmp_path / "urls.txt"
    listing.write_text("https://example.com\nhttps://example.org\n", encoding="utf-8")
    assert ul.main(["--urls-from", str(listing), "--offline"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["skip"] == 2
    assert data["offline"] is True


def test_unreadable_input_is_visible_in_the_json(tmp_path, capsys):
    """`results: []` alone reads as "this corpus names no URLs" — a clean bill of health."""
    assert ul.main(["--urls-from", str(tmp_path / "nope.txt")]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["results"] == []
    assert "FileNotFoundError" in data["source_error"]
    assert data["input_lines"] == 0


@pytest.mark.integration
def test_module_entrypoint_reads_stdin_and_exits_zero():
    """The `python -m … --urls-from -` path the SKILL documents."""
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.url_liveness", "--urls-from", "-", "--offline"],
        input="https://example.com\nhttps://example.org\n",
        capture_output=True,
        check=False,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["summary"]["skip"] == 2

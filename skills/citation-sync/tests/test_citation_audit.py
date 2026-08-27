"""Regression tests for the audit's HTTP contract.

The point of this module is the rate-limit contract: a 429 is a **policy signal**,
not a transient error, so `api_get` halts on the first one — no retry, no sleep.
The why is in `api_get`'s docstring and in `rules/common/debugging.md`; these tests
only pin the behaviour. No test touches the network.
"""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path

import pytest

from scripts import citation_audit as ca


def raising(code: int):
    """A urlopen that answers `code`. A lambda cannot raise, and a named function
    keeps the three failure tests reading the same way."""

    def fake(*_args, **_kwargs):
        raise urllib.error.HTTPError("https://www.wikidata.org/x", code, "boom", {}, None)

    return fake


@pytest.mark.unit
@pytest.mark.parametrize("code", sorted(ca.RATE_LIMIT_STATUSES))
def test_a_rate_limit_status_halts_on_the_first_response(
    code: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Parametrized off the constant: adding a status there cannot leave a gap here.
    attempts = []
    sleeps = []

    def counting(*args, **kwargs):
        attempts.append(args)
        return raising(code)(*args, **kwargs)

    monkeypatch.setattr(ca.urllib.request, "urlopen", counting)
    monkeypatch.setattr(ca.time, "sleep", lambda s: sleeps.append(s))
    with pytest.raises(ca.RateLimited):
        ca.api_get("https://www.wikidata.org/x")
    assert len(attempts) == 1, "a rate limit must not be retried"
    assert sleeps == [], "no backoff — sleeping through a policy signal is the violation"


@pytest.mark.unit
def test_the_halt_message_names_the_rule_that_forbids_the_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ca.urllib.request, "urlopen", raising(429))
    with pytest.raises(ca.RateLimited) as excinfo:
        ca.api_get("https://www.wikidata.org/x")
    assert "rules/common/debugging.md" in str(excinfo.value)


@pytest.mark.unit
def test_a_non_rate_limit_http_error_still_propagates_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ca.urllib.request, "urlopen", raising(404))
    with pytest.raises(urllib.error.HTTPError):
        ca.api_get("https://www.wikidata.org/x")


class _Body:
    """Minimal urlopen context manager returning `payload` as JSON."""

    def __init__(self, payload: str) -> None:
        self._payload = payload

    def __enter__(self):
        return io.StringIO(self._payload)

    def __exit__(self, *_exc) -> bool:
        return False


@pytest.mark.unit
@pytest.mark.parametrize("code", sorted(ca.MEDIAWIKI_RATE_LIMIT_CODES))
def test_a_throttle_returned_as_http_200_still_halts(
    code: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The MediaWiki Action API answers 200 with an error envelope. Read as success it
    # empties a layer, and an unperformed audit gets written out as CONVERGED.
    monkeypatch.setattr(
        ca.urllib.request,
        "urlopen",
        lambda *a, **kw: _Body(json.dumps({"error": {"code": code, "info": "slow down"}})),
    )
    with pytest.raises(ca.RateLimited):
        ca.api_get("https://www.wikidata.org/x")


@pytest.mark.unit
def test_a_non_rate_limit_api_error_is_raised_not_read_as_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ca.urllib.request,
        "urlopen",
        lambda *a, **kw: _Body(json.dumps({"error": {"code": "badvalue", "info": "nope"}})),
    )
    with pytest.raises(RuntimeError):
        ca.api_get("https://www.wikidata.org/x")


@pytest.mark.unit
def test_api_get_passes_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    # No timeout means a throttling host that holds the socket open hangs the audit
    # forever — a silent failure with no exit code at all.
    seen = {}

    def fake(req, *args, **kwargs):
        seen["timeout"] = kwargs.get("timeout", args[0] if args else None)
        return _Body("{}")

    monkeypatch.setattr(ca.urllib.request, "urlopen", fake)
    ca.api_get("https://www.wikidata.org/x")
    assert seen["timeout"] == ca.TIMEOUT


@pytest.mark.unit
def test_a_network_failure_exits_two_not_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # exit 1 is the documented code for "divergence あり" (SKILL.md). A crash must never
    # land there, or a run that never happened is recorded as a finding.
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.setattr(ca, "scan_docs", lambda r: set())
    monkeypatch.setattr(ca, "scan_zenodo", lambda r: (set(), set()))
    monkeypatch.setattr(ca, "scan_graph", lambda r: (set(), "Q1"))

    def boom(qid):
        raise urllib.error.URLError("nodename nor servname provided")

    monkeypatch.setattr(ca, "scan_wikidata", boom)
    assert ca.main([str(repo)]) == 2
    assert "FATAL" in capsys.readouterr().out


@pytest.mark.unit
def test_main_reports_the_halt_and_exits_two_instead_of_a_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # A halt is "audit not performed", not "converged" — exit 2 (fatal), never 0.
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.setattr(ca, "scan_docs", lambda r: set())
    monkeypatch.setattr(ca, "scan_zenodo", lambda r: (set(), set()))
    monkeypatch.setattr(ca, "scan_graph", lambda r: (set(), "Q1"))

    def halt(qid):
        raise ca.RateLimited("rate limit: halting (rules/common/debugging.md)")

    monkeypatch.setattr(ca, "scan_wikidata", halt)
    rc = ca.main([str(repo)])
    assert rc == 2
    assert "rate limit" in capsys.readouterr().out

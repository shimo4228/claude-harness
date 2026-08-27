"""URL liveness evidence for skills that name external references (no verdict, exit 0).

`scan_refs.py` answers "does the path this document names exist"; this answers the
same question for a URL, and takes its input from that scanner's `--external-urls`.
Two checks asked for it and neither had it: `skill-stocktake` (Currency — every URL
a skill names; wired) and `context-sync` (`EcosystemRepo` URLs resolve; not wired
yet — deferred, see ADR-0052 Decision 5). DOI / arXiv *validity* is deliberately
**not** a consumer: a DOI can 302 onto a wrong landing page and still answer 200, so
`citation-formatter` needs identifier resolution, not liveness.

Two design constraints come from outside this file and are not negotiable here:

**Rate limit is a policy signal, not a transient error** (`rules/common/debugging.md`;
2026-07-16 an account was permanently blocked and its artifacts deleted after a
burst was pushed through). So: one request per URL, a serial walk with a delay
between requests, and `rate_limit_threshold` consecutive 429/503 **halts the run**
and reports. There is no retry and no backoff — a retry mechanism would encode a
violation of that rule in code.

**`blocked` must never collapse into `dead`.** A 403 is bot policy, not absence
(`cited-source-mirror-verification` documents SSRN answering 403 to every
non-browser client). Reporting it as `dead` sends a reader chasing a link that is
fine. 5xx is likewise not evidence about the URL.

Verdicts: `live` (2xx/3xx), `dead` (404/410 and other 4xx, or a connection-level
failure), `blocked` (401/403/405/406/429/451 and 5xx — reached, but the answer
says nothing about the URL), `skip` (not checked: offline, unsupported scheme, malformed,
an internal address, or after a halt).

Deliberately absent — each one is the entrance to a much larger program, and this
is an evidence probe: **no retry** (see above), **no concurrency** (parallel fetch
is the burst shape the rule forbids; skill-stocktake's parallel batch agents each
fetching is exactly what this replaces), **no cache** (liveness is a fact about
the moment of checking; a cached `live` is an undated claim).

Contract: JSON on stdout, always exit 0. Search-first, 2026-08-26: no maintained
checker was adopted — `urlchecker` 0.0.35 (2024-02-03) has no JSON output,
`linkchecker` 10.6.0 (2024-07-28) is GPL-2.0 and crawler-shaped, and `lychee`
v0.24.2 (2026-05-01, the strongest candidate) folds every non-accepted status
into one `RejectedStatusCode` error, so blocked-vs-dead would have to be
re-derived by a wrapper anyway. Its CLI surface informed this one. See
docs/adr/0052.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

USER_AGENT = "claude-harness-url-liveness/0.1 (evidence check; not a browser)"
SUPPORTED_SCHEMES = ("http://", "https://")
# Reached the host, but the response is not evidence about the URL itself.
BLOCKED_STATUSES = frozenset({401, 403, 405, 406, 429, 451})
RATE_LIMIT_STATUSES = frozenset({429, 503})
DEFAULT_DELAY = 0.5
DEFAULT_TIMEOUT = 10.0
DEFAULT_RATE_LIMIT_THRESHOLD = 2
# A URL the client could not even form. Not `dead` — a typo in a SKILL.md is not a
# broken link, and telling the reader otherwise sends them to fix the wrong thing.
MALFORMED = "malformed"


def _url_error(url: str) -> str | None:
    """The exception name if the URL cannot even be parsed, else None."""
    try:
        urllib.parse.urlsplit(url)
    except ValueError as exc:
        return type(exc).__name__
    return None


def is_internal_host(url: str) -> bool:
    """True when *url*'s host resolves to a loopback / private / link-local address.

    The URL corpus is repo-controlled data: any SKILL.md — including an externally
    owned one behind a symlink, which its package manager rewrites without review —
    can put a line into the pipeline, and the audit then requests it from the
    operator's machine. Without this, `http://127.0.0.1:9/admin` or
    `http://169.254.169.254/latest/meta-data/` reaches a local service and its port
    and status land in the audit report (demonstrated 2026-08-26 by security-reviewer
    against this module). The fence and template-slot filters upstream reduce example
    URLs; they are not a host defence.

    Resolution failure is *not* treated as internal — the fetch will fail on its own
    and be reported honestly. This resolves separately from `urlopen`, so a name that
    answers differently on the second lookup (DNS rebinding) is out of scope: this is
    an evidence probe, not a sandbox.
    """
    try:
        host = urllib.parse.urlsplit(url).hostname
    except ValueError:
        return True  # unparseable: nothing safe to request (also caught earlier as malformed)
    if not host:
        return True  # no host to check means nothing safe to request
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except (socket.gaierror, UnicodeError, ValueError):
        return False
    for raw in addresses:
        try:
            address = ipaddress.ip_address(raw.split("%", 1)[0])
        except ValueError:
            continue
        if (
            address.is_loopback
            or address.is_private
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            return True
    return False


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not follow redirects: report the 3xx the named URL actually returned.

    Following them broke three invariants at once. (a) urllib walks the whole chain
    inside one `open()`, so a multi-hop link makes several requests where the caller
    counted one and slept once — the burst shape `rules/common/debugging.md` forbids,
    reintroduced by the library. (b) the default handler accepts `ftp:` and any host,
    so an externally reachable origin answering `302 Location: http://127.0.0.1:<port>/`
    walked to loopback and came back `{"status": 200, "verdict": "live"}` (PoC,
    security-reviewer 2026-08-26). (c) a redirect loop surfaced as the original 301 and
    classified `live`.

    Not following costs one thing, and it is the honest one: a URL that 301s onto a
    deleted page reads `live`. That is what the vocabulary already says — 2xx/3xx is
    "the named URL answered" — and chasing the chain is resolution, not liveness.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # urlopen then raises HTTPError carrying the 3xx status


def classify(status: int) -> str:
    if 200 <= status < 400:
        return "live"
    if status in BLOCKED_STATUSES or status >= 500:
        return "blocked"
    return "dead"


def http_fetch(url: str, timeout: float = DEFAULT_TIMEOUT) -> tuple[int | None, str | None]:
    """One GET, body never read. Returns (status, error-class); never raises."""
    try:
        # `Request(...)` itself raises on a malformed URL (`http://[::1` →
        # `ValueError`), and `http.client.InvalidURL` (a space in the host) is neither
        # OSError nor ValueError. Both were escaping and taking the whole run down —
        # every URL already checked lost, the delay budget already spent. The corpus is
        # a regex over arbitrary prose, so malformed input is expected, not exceptional.
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        opener = urllib.request.build_opener(_NoRedirect)
        with opener.open(request, timeout=timeout) as response:
            return response.status, None
    except urllib.error.HTTPError as exc:  # an answer, just not a 2xx
        return exc.code, None
    except urllib.error.URLError as exc:  # DNS, refused, TLS, timeout — no answer
        return None, type(exc.reason).__name__ if exc.reason is not None else "URLError"
    except Exception as exc:  # noqa: BLE001 — a probe must not take the report with it
        return None, f"{MALFORMED}:{type(exc).__name__}"


def check_urls(
    urls,
    *,
    fetch=http_fetch,
    delay: float = DEFAULT_DELAY,
    timeout: float = DEFAULT_TIMEOUT,
    offline: bool = False,
    rate_limit_threshold: int = DEFAULT_RATE_LIMIT_THRESHOLD,
) -> dict:
    results: list[dict] = []
    seen: set[str] = set()
    streak = 0
    # `requested` counts fetches, not results: `results` also holds skips, so using it
    # to gate the delay would space the first real request from a fetch that never
    # happened, and would report "offline" off a corpus nothing was ever sent to.
    requested = 0
    halt_reason: str | None = None
    connection_failures: list[dict] = []

    for raw in urls:
        url = raw.strip()
        if not url or url in seen:
            continue
        seen.add(url)
        skip = (
            "unsupported scheme"
            if not url.startswith(SUPPORTED_SCHEMES)
            # `http://[::1` raises out of `urlsplit`, i.e. before `http_fetch` ever runs,
            # so one malformed prose match aborted the whole audit.
            else f"not checked: {MALFORMED}:{_url_error(url)}"
            if _url_error(url)
            else "offline"
            if offline
            else "not checked: run halted"
            if halt_reason
            # Last, so it costs a DNS lookup only for URLs actually about to be sent.
            else "internal address, not checked"
            if not offline and is_internal_host(url)
            else None
        )
        if skip:
            results.append({"url": url, "status": None, "verdict": "skip", "note": skip})
            continue

        if delay and requested:
            time.sleep(delay)
        status, error = fetch(url, timeout)
        requested += 1

        if error and error.startswith(MALFORMED):
            results.append(
                {"url": url, "status": None, "verdict": "skip", "note": f"not checked: {error}"}
            )
            streak = 0
            continue

        if status is None:
            entry = {"url": url, "status": None, "verdict": "dead", "note": error}
            connection_failures.append(entry)
            results.append(entry)
            streak = 0
            continue

        results.append({"url": url, "status": status, "verdict": classify(status), "note": None})
        streak = streak + 1 if status in RATE_LIMIT_STATUSES else 0
        if streak >= rate_limit_threshold:
            halt_reason = (
                f"rate limit: {streak} consecutive {sorted(RATE_LIMIT_STATUSES)} responses — "
                "treated as a policy signal, remaining URLs left unchecked "
                "(rules/common/debugging.md)"
            )

    # No host answered at all: that is evidence about the network, not about the
    # URLs. Reporting a whole corpus as dead because the wifi is off is the
    # expensive error, so those become `skip` (unverified).
    # `>= 1`, not `> 1`: a skill that names exactly one URL is the common case, and it
    # was the one corpus size with no protection at all. A *partial* outage still
    # escapes this all-or-nothing test, so `connection_failures` is reported alongside
    # it — 17 dead out of 20 is a number the reader can act on.
    offline_suspected = requested >= 1 and len(connection_failures) == requested
    if offline_suspected:
        for entry in connection_failures:
            entry["verdict"] = "skip"
            entry["note"] = f"unverified: no host answered ({entry['note']})"

    summary = {v: 0 for v in ("live", "dead", "blocked", "skip")}
    for entry in results:
        summary[entry["verdict"]] += 1
    return {
        "checked_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "offline": offline,
        "offline_suspected": offline_suspected,
        "halted": halt_reason is not None,
        "halt_reason": halt_reason,
        "results": results,
        "summary": summary,
        "connection_failures": len(connection_failures),
        "requested": requested,
    }


def read_urls(source: str) -> tuple[list[str], str | None]:
    """Return (lines, error). The error travels into the JSON, not only to stderr.

    An unreadable input file otherwise produces `results: []` — byte-identical to a
    healthy run over a corpus that names no URLs. Under the documented pipeline that
    reads "0 dead, 0 blocked, reference URLs are healthy" when nothing was checked.
    """
    try:
        if source == "-":
            return sys.stdin.read().splitlines(), None
        with open(source, encoding="utf-8") as handle:
            return handle.read().splitlines(), None
    except (OSError, UnicodeDecodeError) as exc:
        return [], f"{type(exc).__name__}: {exc}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="URL liveness evidence (JSON, no verdict).")
    parser.add_argument("--urls-from", default="-", help="file with one URL per line, or - (stdin)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--delay", type=float, default=DEFAULT_DELAY, help="seconds between requests (serial)"
    )
    parser.add_argument(
        "--rate-limit-threshold",
        type=int,
        default=DEFAULT_RATE_LIMIT_THRESHOLD,
        help="consecutive 429/503 responses that halt the run (no retry, no backoff)",
    )
    parser.add_argument(
        "--offline", action="store_true", help="check nothing; report every URL skip"
    )
    args = parser.parse_args(argv)

    lines, source_error = read_urls(args.urls_from)
    out = check_urls(
        lines,
        delay=args.delay,
        timeout=args.timeout,
        offline=args.offline,
        rate_limit_threshold=args.rate_limit_threshold,
    )
    out = {"source": args.urls_from, "source_error": source_error, "input_lines": len(lines), **out}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if source_error:
        print(f"url_liveness: cannot read {args.urls_from}: {source_error}", file=sys.stderr)
    if out["halted"]:
        print(f"url_liveness: {out['halt_reason']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Lint a graph.jsonld for structural and JSON-LD pitfalls.

Checks (all deterministic):
  1. JSON validity (fatal on failure)
  2. JSON-LD expansion via pyld (fatal on failure)
  3. DROPPED-KEY  — in explicit-mapping contexts (no @vocab), node keys absent
                    from @context are silently dropped on expansion
  4. URL-LITERAL — URL-shaped string objects on reference predicates: the value
                    became an RDF literal instead of an IRI, so the edge does
                    not exist. Locator-style properties (url, license, ...)
                    are allow-listed
  5. VOLATILE    — version/count fields that leak release state into the graph

Usage:
    uv run --with pyld python3 graph_lint.py <graph.jsonld> [graph2.jsonld ...]
        [--allow-literal-url url,license,contentUrl]

Exit codes: 0 = clean, 1 = findings, 2 = fatal (parse/expansion error).
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys

DEFAULT_ALLOW = "url,license,contentUrl"
URL_LITERAL_RE = re.compile(r'\S+ <([^>]+)> "https?://')
VOLATILE_RE = re.compile(r'"version"|"versionNumber"|"adrCount"|"testCount"')


def local_name(iri: str) -> str:
    return iri.rstrip("/#").rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def lint_file(path: str, allow: set[str]) -> tuple[list[str], bool]:
    """Return (findings, fatal)."""
    findings: list[str] = []

    try:
        with open(path) as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return [f"FATAL invalid JSON: {e}"], True

    ctx = doc.get("@context", {})
    if isinstance(ctx, dict) and "@vocab" not in ctx:
        mapped = set(ctx.keys())
        for node in doc.get("@graph", []):
            if not isinstance(node, dict):
                continue
            for k in node:
                if k.startswith("@") or ":" in k or k in mapped:
                    continue
                findings.append(
                    f"DROPPED-KEY '{k}' at {node.get('@id', '?')} — not in @context "
                    "and no @vocab: silently dropped on expansion"
                )

    try:
        from pyld import jsonld
        nquads = jsonld.to_rdf(doc, {"format": "application/n-quads"})
    except Exception as e:  # pyld raises its own hierarchy
        return findings + [f"FATAL expansion failed: {e}"], True

    url_literals: collections.Counter[str] = collections.Counter()
    for line in nquads.splitlines():
        m = URL_LITERAL_RE.match(line)
        if m:
            url_literals[m.group(1)] += 1
    for pred, n in url_literals.most_common():
        if local_name(pred) in allow:
            continue
        findings.append(
            f"URL-LITERAL {n}x <{pred}> — URL string became an RDF literal, edge "
            'does not exist. Add @type:"@id" coercion in @context or use {"@id": ...}'
        )

    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            if VOLATILE_RE.search(line):
                findings.append(f"VOLATILE line {lineno}: {line.strip()[:100]}")

    return findings, False


def collect_names(path: str) -> dict[str, set[str]]:
    """IRI -> set of en/untagged schema:name values, from the expanded doc."""
    from pyld import jsonld

    with open(path) as f:
        doc = json.load(f)
    out: dict[str, set[str]] = {}
    for node in jsonld.expand(doc):
        nid = node.get("@id")
        if not nid:
            continue
        for v in node.get("https://schema.org/name", []):
            if isinstance(v, dict) and isinstance(v.get("@value"), str):
                if v.get("@language") in (None, "en"):
                    out.setdefault(nid, set()).add(v["@value"])
    return out


def check_name_drift(paths: list[str]) -> list[str]:
    """Cross-file check: the same IRI must carry one canonical en name.

    Detection is structural (deterministic); choosing WHICH name is canonical
    is a judgment call — the lint only reports, resolution happens in review.
    Variants belong in alternateName, not in competing name values.
    """
    findings: list[str] = []
    names: dict[str, set[tuple[str, str]]] = {}
    for path in paths:
        try:
            for nid, vals in collect_names(path).items():
                for v in vals:
                    names.setdefault(nid, set()).add((v, path))
        except Exception:
            continue  # parse failures already reported per-file
    for nid, pairs in sorted(names.items()):
        distinct = {v for v, _ in pairs}
        if len(distinct) > 1:
            detail = "; ".join(f"'{v}' ({p})" for v, p in sorted(pairs))
            findings.append(f"NAME-DRIFT {nid}: {detail}")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", help="graph.jsonld file(s) to lint")
    ap.add_argument(
        "--allow-literal-url",
        default=DEFAULT_ALLOW,
        help=f"comma-separated local names allowed as URL literals (default: {DEFAULT_ALLOW})",
    )
    ap.add_argument(
        "--skip-name-drift",
        action="store_true",
        help="skip the cross-file NAME-DRIFT check",
    )
    args = ap.parse_args()
    allow = {a.strip() for a in args.allow_literal_url.split(",") if a.strip()}

    fatal = False
    total = 0
    for path in args.paths:
        findings, is_fatal = lint_file(path, allow)
        fatal = fatal or is_fatal
        total += len(findings)
        status = "clean" if not findings else f"{len(findings)} finding(s)"
        print(f"{path}: {status}")
        for f in findings:
            print(f"  - {f}")

    if len(args.paths) > 1 and not args.skip_name_drift and not fatal:
        drift = check_name_drift(args.paths)
        total += len(drift)
        print(f"cross-file name drift: {'none' if not drift else f'{len(drift)} finding(s)'}")
        for f in drift:
            print(f"  - {f}")

    if fatal:
        return 2
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())

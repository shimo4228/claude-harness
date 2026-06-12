#!/usr/bin/env python3
"""Lint graph.jsonld <-> Wikidata federation consistency.

Read-only (anonymous API, no BotPassword needed). Checks:

  1. QID-CONFLICT — the same node @id maps to different QIDs across the
                    supplied graphs (a typo'd QID silently diverges)
  2. BACKLINK     — each QID points back at the entity the graph claims:
                      * node has a DOI identifier  -> P356 == DOI (uppercase)
                      * node @id/url is a GitHub repo -> P1324 == repo URL
                      * Person node (@id = ORCID IRI) -> P496 == ORCID
  3. CONSTRAINTS  — Wikidata's native wbcheckconstraints verdicts
                    (violation / warning; suggestions shown with --suggestions).
                    This is delegated to Wikidata — do not reimplement
                    P50-vs-P178, qualifier pairing, etc. locally

Usage:
    python3 federation_lint.py graph1.jsonld [graph2.jsonld ...]
        [--suggestions] [--skip-constraints]

Exit codes: 0 = clean, 1 = findings, 2 = fatal (parse/API error).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://www.wikidata.org/w/api.php"
UA = "federation-lint/1.0 (https://github.com/shimo4228; shimo4228@gmail.com)"
QID_RE = re.compile(r"wikidata\.org/(?:wiki|entity)/(Q\d+)")
ORCID_RE = re.compile(r"orcid\.org/(\d{4}-\d{4}-\d{4}-\d{3}[\dX])")
GITHUB_RE = re.compile(r"^https://github\.com/[^/]+/[^/#]+$")
DOI_RE = re.compile(r"^10\.\d{4,}/\S+$")
BATCH = 50


def api_get(params: dict) -> dict:
    qs = urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(f"{API}?{qs}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def as_list(v) -> list:
    return v if isinstance(v, list) else [v]


def extract_entities(path: str) -> tuple[dict[str, dict], list[str]]:
    """Map node @id -> {qid, doi, repo, orcid} for nodes carrying a QID sameAs."""
    findings: list[str] = []
    try:
        with open(path) as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return {}, [f"FATAL {path}: invalid JSON: {e}"]

    out: dict[str, dict] = {}
    for node in doc.get("@graph", []):
        if not isinstance(node, dict):
            continue
        nid = node.get("@id", "")
        qids = set()
        for v in as_list(node.get("sameAs", [])):
            if isinstance(v, str):
                m = QID_RE.search(v)
                if m:
                    qids.add(m.group(1))
        if not qids:
            continue
        if len(qids) > 1:
            findings.append(f"QID-CONFLICT {path}: {nid} carries multiple QIDs {sorted(qids)}")
            continue

        ident = node.get("identifier")
        doi = ident if isinstance(ident, str) and DOI_RE.match(ident) else None
        repo = None
        for cand in [nid, node.get("url")]:
            if isinstance(cand, str) and GITHUB_RE.match(cand):
                repo = cand
                break
        m = ORCID_RE.search(nid)
        orcid = m.group(1) if m else None
        out[nid] = {"qid": qids.pop(), "doi": doi, "repo": repo, "orcid": orcid, "graph": path}
    return out, findings


def claim_values(claims: dict, prop: str) -> list[str]:
    vals = []
    for c in claims.get(prop, []):
        dv = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(dv, str):
            vals.append(dv)
    return vals


def check_backlinks(merged: dict[str, dict]) -> list[str]:
    findings: list[str] = []
    qids = sorted({e["qid"] for e in merged.values()})
    entities: dict[str, dict] = {}
    for i in range(0, len(qids), BATCH):
        chunk = qids[i : i + BATCH]
        d = api_get({"action": "wbgetentities", "ids": "|".join(chunk), "props": "claims"})
        entities.update(d.get("entities", {}))
        time.sleep(1)

    for nid, e in sorted(merged.items()):
        ent = entities.get(e["qid"], {})
        if "missing" in ent:
            findings.append(f"BACKLINK {e['qid']}: entity does not exist (referenced by {nid})")
            continue
        claims = ent.get("claims", {})
        if e["doi"]:
            p356 = [v.upper() for v in claim_values(claims, "P356")]
            if e["doi"].upper() not in p356:
                findings.append(
                    f"BACKLINK {e['qid']}: P356 {p356 or '(absent)'} does not include DOI {e['doi'].upper()} ({nid})"
                )
        if e["repo"]:
            p1324 = [v.rstrip("/") for v in claim_values(claims, "P1324")]
            if e["repo"].rstrip("/") not in p1324:
                findings.append(
                    f"BACKLINK {e['qid']}: P1324 {p1324 or '(absent)'} does not include repo {e['repo']} ({nid})"
                )
        if e["orcid"]:
            p496 = claim_values(claims, "P496")
            if e["orcid"] not in p496:
                findings.append(
                    f"BACKLINK {e['qid']}: P496 {p496 or '(absent)'} does not include ORCID {e['orcid']} ({nid})"
                )
    return findings


def check_constraints(qids: list[str], include_suggestions: bool) -> list[str]:
    findings: list[str] = []
    levels = {"violation", "warning"} | ({"suggestion"} if include_suggestions else set())
    for i in range(0, len(qids), BATCH):
        chunk = qids[i : i + BATCH]
        d = api_get({"action": "wbcheckconstraints", "id": "|".join(chunk)})
        for qid, ent in d.get("wbcheckconstraints", {}).items():
            for prop, stmts in ent.get("claims", {}).items():
                for st in stmts:
                    snaks = [("", st.get("mainsnak", {}))]
                    for qsnaks in st.get("qualifiers", {}).values():
                        snaks.extend(("qualifier", s) for s in qsnaks)
                    for ref in st.get("references", []):
                        for rsnaks in ref.get("snaks", {}).values():
                            snaks.extend(("reference", s) for s in rsnaks)
                    for where, snak in snaks:
                        for r in snak.get("results", []):
                            if r.get("status") in levels:
                                ctype = r.get("constraint", {}).get("typeLabel") or r.get(
                                    "constraint", {}
                                ).get("type", "?")
                                loc = snak.get("property", prop)
                                suffix = f" [{where} {loc}]" if where else ""
                                findings.append(
                                    f"CONSTRAINT {qid}/{prop}: {r['status']} ({ctype}){suffix}"
                                )
        time.sleep(2)
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", help="graph.jsonld file(s)")
    ap.add_argument("--suggestions", action="store_true", help="include suggestion-level constraint results")
    ap.add_argument("--skip-constraints", action="store_true", help="skip wbcheckconstraints (faster)")
    ap.add_argument("--items", help="comma-separated QIDs (or @file with one QID per line) to "
                                    "constraint-check in addition to / instead of graph-derived QIDs. "
                                    "Use for post-write verification of items not present in any graph")
    args = ap.parse_args()

    extra_qids: set[str] = set()
    if args.items:
        raw = args.items
        if raw.startswith("@"):
            with open(raw[1:]) as fh:
                raw = ",".join(line.strip() for line in fh if line.strip())
        for q in raw.split(","):
            q = q.strip()
            if not re.fullmatch(r"Q\d+", q):
                print(f"FATAL invalid QID in --items: {q!r}")
                return 2
            extra_qids.add(q)
    if not args.paths and not extra_qids:
        ap.error("provide graph.jsonld path(s) and/or --items")

    findings: list[str] = []
    merged: dict[str, dict] = {}
    qid_by_id: dict[str, str] = {}
    for path in args.paths:
        ents, errs = extract_entities(path)
        findings.extend(errs)
        for nid, e in ents.items():
            if nid in qid_by_id and qid_by_id[nid] != e["qid"]:
                findings.append(
                    f"QID-CONFLICT {nid}: {qid_by_id[nid]} vs {e['qid']} (in {e['graph']})"
                )
            qid_by_id.setdefault(nid, e["qid"])
            merged.setdefault(nid, e)

    if any(f.startswith("FATAL") for f in findings):
        for f in findings:
            print(f)
        return 2

    all_qids = {e["qid"] for e in merged.values()} | extra_qids
    print(f"{len(merged)} federated node(s), {len(all_qids)} unique QID(s)"
          + (f" ({len(extra_qids)} via --items)" if extra_qids else ""))
    try:
        findings.extend(check_backlinks(merged))
        if not args.skip_constraints:
            findings.extend(check_constraints(sorted(all_qids), args.suggestions))
    except Exception as e:
        print(f"FATAL API error: {e}")
        return 2

    if findings:
        print(f"{len(findings)} finding(s):")
        for f in findings:
            print(" -", f)
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

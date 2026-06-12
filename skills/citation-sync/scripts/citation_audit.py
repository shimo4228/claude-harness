#!/usr/bin/env python3
"""Audit the four citation layers of research repos and report divergence.

Layers (lowest = source of truth):
  1. docs      — identifier-bearing citations in public markdown/text
                 (arXiv IDs and DOIs; excludes .notes/, .git/, hidden dirs)
  2. zenodo    — .zenodo.json related_identifiers with relation=references
  3. graph     — graph.jsonld nodes typed ExternalReference
  4. wikidata  — P2860 (cites work) on the repo's Wikidata item, resolved to
                 arXiv ID / DOI via each cited item's P818 / P356
                 (repo QID is discovered from the graph self-node's sameAs)

Usage:
    python3 citation_audit.py [--skip-wikidata] [--json OUT.json] REPO_DIR ...

Output: a per-repo divergence table (markdown) on stdout; exit 1 if any repo
has layer divergence, 0 if all repos are converged. Read-only — never writes
to the repos or to Wikidata.

Sibling/self Zenodo DOIs (10.5281/zenodo.*) are reported separately and NOT
counted as divergence: they are ecosystem cross-links, not external citations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ARXIV_RE = re.compile(r"(?:arXiv[: ]?|arxiv\.org/abs/|10\.48550/arXiv\.)(\d{4}\.\d{4,5})",
                      re.IGNORECASE)
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>\])},;`&]+")
ZENODO_PREFIX = "10.5281/zenodo."
EXCLUDE_DIRS = {".notes", ".git", "node_modules", ".venv", "__pycache__"}
UA = {"User-Agent": "citation-sync-audit/1.0 (read-only layer audit)"}


def norm_arxiv(aid: str) -> str:
    return f"arxiv:{aid}"


def norm_doi(doi: str) -> str:
    doi = doi.rstrip(".").rstrip("/")
    m = ARXIV_RE.search(doi)
    if m:
        return norm_arxiv(m.group(1))
    return f"doi:{doi.upper()}"


def scan_docs(repo: Path) -> set[str]:
    found: set[str] = set()
    for p in repo.rglob("*"):
        if p.suffix not in (".md", ".txt"):
            continue
        if any(part in EXCLUDE_DIRS or part.startswith(".") for part in p.relative_to(repo).parts[:-1]):
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for m in ARXIV_RE.finditer(text):
            found.add(norm_arxiv(m.group(1)))
        for m in DOI_RE.finditer(text):
            doi = m.group(0).rstrip(".")
            if doi.lower().endswith(".svg") or doi.lower().endswith("/full"):
                doi = doi.rsplit("/", 1)[0] if doi.lower().endswith("/full") else doi
                if doi.lower().endswith(".svg"):
                    continue  # DOI badge image URLs
            if "10.48550/" in doi or doi.lower().startswith("10.5281/zenodo"):
                continue  # arXiv handled above; Zenodo DOIs are ecosystem links
            found.add(norm_doi(doi))
    return found


def scan_zenodo(repo: Path) -> tuple[set[str], set[str]]:
    external: set[str] = set()
    ecosystem: set[str] = set()
    zj = repo / ".zenodo.json"
    if not zj.exists():
        return external, ecosystem
    data = json.loads(zj.read_text())
    for r in data.get("related_identifiers", []):
        if r.get("relation") != "references":
            continue
        ident = r.get("identifier", "")
        m = ARXIV_RE.search(ident)
        if m:
            external.add(norm_arxiv(m.group(1)))
        elif ident.lower().startswith(ZENODO_PREFIX):
            ecosystem.add(ident.lower())
        elif ident.startswith("10."):
            external.add(norm_doi(ident))
        # URLs without DOI are out of scope for the citation layers
    return external, ecosystem


def scan_graph(repo: Path) -> tuple[set[str], str | None]:
    """Return (external-reference identifiers, repo item Wikidata QID)."""
    refs: set[str] = set()
    qid: str | None = None
    gj = repo / "graph.jsonld"
    if not gj.exists():
        return refs, qid
    data = json.loads(gj.read_text())
    nodes = data.get("@graph", [])
    repo_name = repo.name
    for node in nodes:
        types = node.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if "ExternalReference" in types:
            for field in ("identifier", "@id", "url"):
                v = node.get(field, "")
                for s in (v if isinstance(v, list) else [v]):
                    if not isinstance(s, str):
                        continue
                    m = ARXIV_RE.search(s)
                    if m:
                        refs.add(norm_arxiv(m.group(1)))
                        break
                    m = DOI_RE.search(s)
                    if m and not m.group(0).lower().startswith("10.5281/zenodo"):
                        refs.add(norm_doi(m.group(0)))
                        break
                else:
                    continue
                break
        # repo self-node: GitHub @id/url matching the repo dir name + a wikidata sameAs
        sames = node.get("sameAs", [])
        if isinstance(sames, str):
            sames = [sames]
        ids = [node.get("@id", ""), node.get("url", "")]
        if any(isinstance(i, str)
               and ((i.rstrip("/").endswith(f"/{repo_name}")
                     and ("github.com" in i or "github.io" in i))
                    or i == f"#{repo_name}")
               for i in ids):
            for s in sames:
                if isinstance(s, str) and "wikidata.org" in s:
                    qid = s.rstrip("/").rsplit("/", 1)[-1]
    return refs, qid


def api_get(url: str, tries: int = 5) -> dict:
    req = urllib.request.Request(url, headers=UA)
    for i in range(tries):
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (i + 1))
                continue
            raise
    raise RuntimeError(f"rate-limited after {tries} tries: {url}")


def scan_wikidata(qid: str) -> set[str]:
    refs: set[str] = set()
    d = api_get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json")
    claims = d["entities"][qid].get("claims", {})
    targets = [s["mainsnak"]["datavalue"]["value"]["id"]
               for s in claims.get("P2860", [])
               if s.get("mainsnak", {}).get("datavalue")]
    for i in range(0, len(targets), 50):
        chunk = "|".join(targets[i:i + 50])
        dd = api_get("https://www.wikidata.org/w/api.php?action=wbgetentities"
                     f"&ids={chunk}&props=claims&format=json")
        for tq, ent in dd.get("entities", {}).items():
            c = ent.get("claims", {})
            p818 = [s["mainsnak"]["datavalue"]["value"] for s in c.get("P818", [])
                    if s.get("mainsnak", {}).get("datavalue")]
            p356 = [s["mainsnak"]["datavalue"]["value"] for s in c.get("P356", [])
                    if s.get("mainsnak", {}).get("datavalue")]
            if p818:
                refs.add(norm_arxiv(p818[0]))
            elif p356:
                refs.add(norm_doi(p356[0]))
            else:
                refs.add(f"qid:{tq}")
        time.sleep(1)
    return refs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repos", nargs="+", help="repo directories to audit")
    ap.add_argument("--skip-wikidata", action="store_true",
                    help="skip the Wikidata layer (offline / faster)")
    ap.add_argument("--json", help="also write machine-readable results to this path")
    args = ap.parse_args()

    diverged = False
    results = {}
    for rd in args.repos:
        repo = Path(rd).resolve()
        if not repo.is_dir():
            print(f"FATAL: not a directory: {repo}")
            return 2
        docs = scan_docs(repo)
        zenodo, eco = scan_zenodo(repo)
        graph, qid = scan_graph(repo)
        wikidata: set[str] | None = None
        if not args.skip_wikidata and qid:
            wikidata = scan_wikidata(qid)

        layers = {"docs": docs, "zenodo": zenodo, "graph": graph}
        if wikidata is not None:
            layers["wikidata"] = wikidata
        union = set().union(*layers.values())
        repo_diverged = any(layers[k] != union for k in layers)
        diverged |= repo_diverged

        results[repo.name] = {
            "qid": qid,
            "ecosystem_refs": sorted(eco),
            "layers": {k: sorted(v) for k, v in layers.items()},
            "union": sorted(union),
            "converged": not repo_diverged,
        }

        print(f"\n## {repo.name}" + (f"  (Wikidata: {qid})" if qid else "  (no QID in graph)"))
        if not union:
            print("  no external citations in any layer")
            continue
        cols = list(layers)
        print("| identifier | " + " | ".join(cols) + " |")
        print("|---|" + "|".join(["---"] * len(cols)) + "|")
        for ident in sorted(union):
            marks = [("x" if ident in layers[c] else " ") for c in cols]
            print(f"| {ident} | " + " | ".join(marks) + " |")
        print("  -> " + ("CONVERGED" if not repo_diverged else "DIVERGED"))

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1))
    print(f"\n{'DIVERGENCE FOUND' if diverged else 'all repos converged'}")
    return 1 if diverged else 0


if __name__ == "__main__":
    sys.exit(main())

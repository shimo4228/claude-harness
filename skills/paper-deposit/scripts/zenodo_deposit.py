#!/usr/bin/env python3
"""Create a Zenodo DRAFT deposition for a standalone paper. NEVER publishes.

Design intent:
- Publishing a Zenodo record is irreversible (a published record cannot be
  deleted, only superseded by a new version). So this script stops at the
  draft: it creates the deposition, uploads the files, and writes the
  metadata, then prints the draft URL + reserved DOIs for a human to review
  and Publish in the web UI. This keeps the irreversible step under human
  control.
- The access token is read from a file and is NEVER printed or logged. The
  caller is responsible for deleting that file after use.
- `--sandbox` targets sandbox.zenodo.org so the whole flow can be exercised
  without touching the production registry (useful because this script has a
  real side effect and cannot be safely benchmarked against production).

Token scopes required: `deposit:write` (upload). `deposit:actions` is only
needed if you later publish via API — this script never does, so write is
enough; the human publishes from the web UI with their session.

Usage:
    python -m scripts.zenodo_deposit \
        --token-file /path/to/.zenodo-token \
        --metadata /path/to/metadata.json \
        --files paper.pdf paper.md paper.ja.pdf paper.ja.md \
        [--sandbox]

metadata.json is either a bare Zenodo metadata dict or a {"metadata": {...}}
wrapper. Minimal example (see SKILL.md for the full field guide):

    {
      "upload_type": "publication",
      "publication_type": "workingpaper",
      "title": "...",
      "creators": [{"name": "Last, First", "orcid": "0000-0000-0000-0000",
                    "affiliation": "..."}],
      "description": "<p>abstract...</p>",
      "keywords": ["...", "..."],
      "license": "cc-by-4.0",
      "language": "eng",
      "version": "v1",
      "publication_date": "2026-05-23",
      "related_identifiers": [
        {"identifier": "10.5281/zenodo.XXXX", "relation": "isSupplementTo",
         "scheme": "doi"}
      ]
    }
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _api_base(sandbox: bool) -> str:
    host = "sandbox.zenodo.org" if sandbox else "zenodo.org"
    return f"https://{host}/api/deposit/depositions"


def _request(method: str, url: str, token: str, *, data=None,
             raw: bool = False) -> tuple[int, Any]:
    """Single HTTP call. Returns (status, parsed_json). Never logs the token."""
    headers = {"Authorization": f"Bearer {token}"}
    body = data
    if data is not None and not raw:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    elif raw:
        headers["Content-Type"] = "application/octet-stream"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310 (trusted host)
            text = resp.read().decode()
            return resp.status, (json.loads(text) if text else {})
    except urllib.error.HTTPError as exc:
        return exc.code, {"_error": exc.read().decode()[:1500]}


def _load_metadata(path: Path) -> dict:
    raw = json.loads(path.read_text())
    inner = raw["metadata"] if "metadata" in raw else raw
    return {"metadata": inner}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a Zenodo DRAFT deposition (never publishes).")
    parser.add_argument("--token-file", required=True, type=Path,
                        help="File containing the Zenodo access token (one line). "
                             "Read only; never printed. Delete it after use.")
    parser.add_argument("--metadata", required=True, type=Path,
                        help="JSON file: Zenodo metadata dict or {'metadata': {...}}.")
    parser.add_argument("--files", required=True, nargs="+", type=Path,
                        help="Files to upload (PDF + Markdown, all languages).")
    parser.add_argument("--sandbox", action="store_true",
                        help="Target sandbox.zenodo.org (test without touching production).")
    args = parser.parse_args(argv)

    # Validate inputs before touching the network.
    if not args.token_file.is_file():
        print(f"token file not found: {args.token_file}", file=sys.stderr)
        return 2
    missing = [str(f) for f in args.files if not f.is_file()]
    if missing:
        print(f"file(s) not found: {', '.join(missing)}", file=sys.stderr)
        return 2
    metadata = _load_metadata(args.metadata)
    token = args.token_file.read_text().strip()
    base = _api_base(args.sandbox)

    # 1. Create empty draft.
    status, dep = _request("POST", base, token, data={})
    if status not in (200, 201):
        print(f"CREATE FAILED [{status}]: {dep.get('_error', '')}", file=sys.stderr)
        return 1
    dep_id = dep["id"]
    bucket = dep["links"]["bucket"]
    print(f"draft created: id={dep_id}")

    # 2. Upload files to the bucket.
    failed = False
    for f in args.files:
        s, _ = _request("PUT", f"{bucket}/{f.name}", token,
                        data=f.read_bytes(), raw=True)
        ok = s in (200, 201)
        failed = failed or not ok
        print(f"  upload {f.name}: {'OK' if ok else 'FAIL ' + str(s)}")

    # 3. Set metadata.
    s, m = _request("PUT", f"{base}/{dep_id}", token, data=metadata)
    if s not in (200, 201):
        print(f"METADATA FAILED [{s}]: {m.get('_error', '')}", file=sys.stderr)
        print(f"-> draft {dep_id} exists with files; re-apply metadata or fix in web UI.")
        failed = True
    else:
        print("metadata: OK")

    # 4. Report (NO publish — human reviews + publishes in the web UI).
    s, info = _request("GET", f"{base}/{dep_id}", token)
    doi = None
    html = None
    if s == 200:
        doi = info.get("metadata", {}).get("prereserve_doi", {}).get("doi")
        html = info.get("links", {}).get("html")
    print("--- DRAFT READY (not published) ---")
    print(f"reserved DOI (activates on publish): {doi}")
    print(f"review & Publish here: {html}")
    print("Zenodo also mints a separate concept DOI (all-versions) at publish; "
          "it appears on the published record page.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

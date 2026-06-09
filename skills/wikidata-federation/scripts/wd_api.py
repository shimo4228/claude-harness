#!/usr/bin/env python3
"""Minimal Wikidata write client (transport layer only).

Sends ONE wbeditentity request per invocation. Payload generation,
display, and human confirmation happen in the conversation layer —
this script only transmits an already-approved payload.

Usage:
    uv run --with requests python3 wd_api.py --site test --new item --data payload.json --summary "..."
    uv run --with requests python3 wd_api.py --site www  --id Q123  --data payload.json --summary "..."

Credentials (never hardcoded):
    env vars WIKIDATA_USERNAME / WIKIDATA_PASSWORD, with fallback to
    ~/.config/wikidata/credentials.env (KEY=VALUE lines, chmod 600).

User-Agent: set WIKIDATA_USER_AGENT to identify yourself per Wikimedia
User-Agent policy (e.g. "my-tool/0.1 (https://orcid.org/...; me@example.org)").
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

SITES = {
    "test": "https://test.wikidata.org/w/api.php",
    "www": "https://www.wikidata.org/w/api.php",
}

USER_AGENT = os.environ.get(
    "WIKIDATA_USER_AGENT",
    "wikidata-federation-skill/0.1 (set WIKIDATA_USER_AGENT to identify yourself)",
)

CRED_FILE = Path.home() / ".config" / "wikidata" / "credentials.env"


def load_credentials() -> tuple[str, str]:
    username = os.environ.get("WIKIDATA_USERNAME", "")
    password = os.environ.get("WIKIDATA_PASSWORD", "")
    if not (username and password) and CRED_FILE.exists():
        for line in CRED_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip("'\"")
            if key.strip() == "WIKIDATA_USERNAME" and not username:
                username = value
            if key.strip() == "WIKIDATA_PASSWORD" and not password:
                password = value
    if not (username and password):
        sys.exit(
            "ERROR: credentials not found. Set WIKIDATA_USERNAME / "
            f"WIKIDATA_PASSWORD env vars or create {CRED_FILE} (chmod 600)."
        )
    return username, password


def fail(stage: str, response: dict) -> None:
    print(f"=== API ERROR at {stage} ===", file=sys.stderr)
    print(json.dumps(response, indent=2, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", choices=SITES, required=True)
    parser.add_argument("--data", required=True, help="payload JSON file")
    parser.add_argument("--summary", required=True, help="edit summary")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--new", choices=["item"], help="create a new entity")
    group.add_argument("--id", help="edit an existing entity (QID)")
    args = parser.parse_args()

    api = SITES[args.site]
    payload = json.loads(Path(args.data).read_text())
    username, password = load_credentials()

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    # 1. login token
    r = session.get(
        api,
        params={"action": "query", "meta": "tokens", "type": "login", "format": "json"},
    ).json()
    login_token = r.get("query", {}).get("tokens", {}).get("logintoken")
    if not login_token:
        fail("login-token", r)

    # 2. login (BotPassword)
    r = session.post(
        api,
        data={
            "action": "login",
            "lgname": username,
            "lgpassword": password,
            "lgtoken": login_token,
            "format": "json",
        },
    ).json()
    if r.get("login", {}).get("result") != "Success":
        fail("login", r)

    # 3. CSRF token
    r = session.get(
        api, params={"action": "query", "meta": "tokens", "format": "json"}
    ).json()
    csrf = r.get("query", {}).get("tokens", {}).get("csrftoken")
    if not csrf or csrf == "+\\":
        fail("csrf-token", r)

    # 4. wbeditentity
    data = {
        "action": "wbeditentity",
        "format": "json",
        "token": csrf,
        "summary": args.summary,
        "maxlag": "5",
        "data": json.dumps(payload, ensure_ascii=False),
    }
    if args.new:
        data["new"] = args.new
    else:
        data["id"] = args.id
    r = session.post(api, data=data).json()

    if "error" in r or r.get("success") != 1:
        fail("wbeditentity", r)

    entity = r["entity"]
    print(json.dumps({"success": 1, "qid": entity["id"]}, ensure_ascii=False))
    print(json.dumps(r, indent=2, ensure_ascii=False)[:3000], file=sys.stderr)


if __name__ == "__main__":
    main()

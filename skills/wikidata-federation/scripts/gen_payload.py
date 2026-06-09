#!/usr/bin/env python3
"""Generate a wbeditentity payload from a spec JSON (author or work).

Usage:
    python3 gen_payload.py spec.json > payload.json

Spec format (author):
{
  "kind": "author",
  "label_en": "Jane Doe",
  "alias_en": "Doe, Jane",                 // optional
  "description_en": "independent researcher",
  "description_ja": "独立研究者",            // optional
  "orcid": "0000-0000-0000-0000",
  "retrieved": "2026-06-07"                 // reference retrieval date
}

Spec format (work — paper / software / dataset):
{
  "kind": "work",
  "title": "Paper Title",
  "description_en": "working paper by Jane Doe",
  "instance_of": "Q13442814",               // Q13442814 article / Q7397 software / Q1172284 dataset
  "doi": "10.5281/ZENODO.12345",            // UPPERCASE per Wikidata convention
  "publication_date": "2026-05-23",         // FIRST-version date, not latest
  "license": "Q20007257",                   // Q20007257 CC-BY-4.0 / Q334661 MIT / Q6938433 CC0
  "copyright_status": "Q50423863",           // optional override; auto-derived from license if omitted
  "author_qid": "Q12345",
  "author_ordinal": "1",
  "source_code_url": "https://github.com/...",  // optional, software only
  "version_control_system": "Q186055",      // optional P8423 qualifier; auto Git for github.com
  "web_interface_software": "Q364",          // optional P10627 qualifier; auto GitHub for github.com
  "retrieved": "2026-06-07"
}

Conventions enforced here (see SKILL.md for why):
- P356 DOI uppercase
- author property by type: articles/datasets use P50 (author) with a P1545
  series-ordinal qualifier; software uses P178 (developer). P50 has a
  conflicts-with constraint against P31=software (Q7397), so software must
  not use P50. Never use P2093 (author name string) when a QID exists.
- References (P854 + P813) on P356 / P577 / P275 / P50; ORCID statement
  referenced with the ORCID profile URL
- P6216 (copyright status) auto-paired with P275: Wikidata's
  item-requires-statement constraint expects a license to declare its
  copyright status. CC0 -> "copyrighted, dedicated to the public domain
  by copyright holder" (Q88088423); every other license -> "copyrighted"
  (Q50423863), since CC/MIT licenses presuppose copyright exists.
"""

from __future__ import annotations

import json
import sys

CALENDAR = "http://www.wikidata.org/entity/Q1985727"

# License QID -> default copyright status (P6216) QID
COPYRIGHT_STATUS = {
    "Q6938433": "Q88088423",  # CC0 -> dedicated to the public domain by holder
}
DEFAULT_COPYRIGHT_STATUS = "Q50423863"  # copyrighted


def time_value(date: str) -> dict:
    return {"time": f"+{date}T00:00:00Z", "timezone": 0, "before": 0,
            "after": 0, "precision": 11, "calendarmodel": CALENDAR}


def item_snak(prop: str, qid: str) -> dict:
    return {"snaktype": "value", "property": prop,
            "datavalue": {"value": {"entity-type": "item",
                                    "numeric-id": int(qid.lstrip("Q"))},
                          "type": "wikibase-entityid"}}


def string_snak(prop: str, value: str) -> dict:
    return {"snaktype": "value", "property": prop,
            "datavalue": {"value": value, "type": "string"}}


def make_ref(url: str, retrieved: str) -> list:
    return [{
        "snaks": {
            "P854": [string_snak("P854", url)],
            "P813": [{"snaktype": "value", "property": "P813",
                      "datavalue": {"value": time_value(retrieved),
                                    "type": "time"}}],
        },
        "snaks-order": ["P854", "P813"],
    }]


def statement(mainsnak: dict, references: list | None = None,
              qualifiers: dict | None = None) -> dict:
    st = {"mainsnak": mainsnak, "type": "statement", "rank": "normal"}
    if qualifiers:
        st["qualifiers"] = qualifiers
        st["qualifiers-order"] = list(qualifiers)
    if references:
        st["references"] = references
    return st


def build_author(spec: dict) -> dict:
    orcid_url = f"https://orcid.org/{spec['orcid']}"
    ref = make_ref(orcid_url, spec["retrieved"])
    descriptions = {"en": {"language": "en", "value": spec["description_en"]}}
    if spec.get("description_ja"):
        descriptions["ja"] = {"language": "ja", "value": spec["description_ja"]}
    payload = {
        "labels": {"en": {"language": "en", "value": spec["label_en"]}},
        "descriptions": descriptions,
        "claims": [
            statement(item_snak("P31", "Q5")),
            statement(item_snak("P106", "Q1650915")),
            statement(string_snak("P496", spec["orcid"]), references=ref),
        ],
    }
    if spec.get("alias_en"):
        payload["aliases"] = {"en": [{"language": "en", "value": spec["alias_en"]}]}
    return payload


def build_work(spec: dict) -> dict:
    doi = spec["doi"]
    if doi != doi.upper():
        sys.exit(f"ERROR: DOI must be uppercase for P356 (got: {doi})")
    ref = make_ref(f"https://doi.org/{doi.lower()}", spec["retrieved"])
    claims = [
        statement(item_snak("P31", spec["instance_of"])),
        statement(string_snak("P356", doi), references=ref),
        statement({"snaktype": "value", "property": "P1476",
                   "datavalue": {"value": {"text": spec["title"], "language": "en"},
                                 "type": "monolingualtext"}}),
        statement({"snaktype": "value", "property": "P577",
                   "datavalue": {"value": time_value(spec["publication_date"]),
                                 "type": "time"}}, references=ref),
        statement(item_snak("P275", spec["license"]), references=ref),
        statement(item_snak("P6216", spec.get("copyright_status")
                            or COPYRIGHT_STATUS.get(spec["license"], DEFAULT_COPYRIGHT_STATUS))),
    ]
    # Author property by type: software -> P178 developer (P50 conflicts with
    # P31=software); articles/datasets -> P50 author with series ordinal.
    if spec["instance_of"] == "Q7397":
        claims.append(statement(item_snak("P178", spec["author_qid"]), references=ref))
    else:
        claims.append(statement(item_snak("P50", spec["author_qid"]), references=ref,
                      qualifiers={"P1545": [string_snak("P1545",
                                                        spec.get("author_ordinal", "1"))]}))
    if spec.get("source_code_url"):
        url = spec["source_code_url"]
        # P1324 wants qualifiers: P8423 version control system + P10627 web
        # interface software (Wikidata required-qualifier constraint). Derive
        # from a GitHub URL; override via spec for other hosts.
        quals = {}
        vcs = spec.get("version_control_system")
        web = spec.get("web_interface_software")
        if "github.com" in url:
            vcs = vcs or "Q186055"   # Git
            web = web or "Q364"      # GitHub
        if vcs:
            quals["P8423"] = [item_snak("P8423", vcs)]
        if web:
            quals["P10627"] = [item_snak("P10627", web)]
        claims.append(statement(string_snak("P1324", url), qualifiers=quals or None))
    return {
        "labels": {"en": {"language": "en", "value": spec["title"][:250]}},
        "descriptions": {"en": {"language": "en", "value": spec["description_en"]}},
        "claims": claims,
    }


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    spec = json.loads(open(sys.argv[1]).read())
    builders = {"author": build_author, "work": build_work}
    kind = spec.get("kind")
    if kind not in builders:
        sys.exit(f"ERROR: spec.kind must be one of {list(builders)} (got: {kind})")
    print(json.dumps(builders[kind](spec), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

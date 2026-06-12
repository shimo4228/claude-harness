#!/usr/bin/env python3
"""Generate a wbeditentity payload from a spec JSON (author or work).

Usage:
    python3 gen_payload.py spec.json > payload.json

Spec format (author):
{
  "kind": "author",
  "label_en": "Jane Doe",
  "label_ja": "ジェーン・ドウ",            // optional; native-script form only, no guesses
  "alias_en": "Doe, Jane",                 // optional
  "aliases": {"ja": ["どう じぇーん"]},     // optional, merged with alias_en
  "description_en": "independent researcher",
  "description_ja": "独立研究者",            // optional
  "orcid": "0000-0000-0000-0000",
  "notable_works": ["Q12345"],              // optional -> P800, ORCID-referenced
  "fields_of_work": ["Q11660"],             // optional -> P101, ORCID-referenced
  "retrieved": "2026-06-07"                 // reference retrieval date
}

Spec format (work — paper / software / dataset):
{
  "kind": "work",
  "title": "Paper Title",                    // becomes en AND mul labels
  "description_en": "scholarly article by Doe, 2026",   // WikiCite form
  "description_ja": "ドウによる2026年の学術論文",          // optional but rubric-recommended
  "aliases": {"en": ["PT"]},                 // optional; GENUINE short titles only
  "instance_of": "Q13442814",               // Q13442814 article / Q7397 software / Q1172284 dataset
  "doi": "10.5281/ZENODO.12345",            // UPPERCASE per Wikidata convention
  "publication_date": "2026-05-23",         // FIRST-version date, not latest
  "license": "Q20007257",                   // Q20007257 CC-BY-4.0 / Q334661 MIT / Q6938433 CC0
  "copyright_status": "Q50423863",           // optional override; auto-derived from license if omitted
  "author_qid": "Q12345",
  "author_ordinal": "1",
  "author_stated_as": "Jane Doe",            // optional -> P1932 qualifier on P50 (name as printed)
  "main_subjects": ["Q11660"],               // optional -> P921; EXISTING general concepts only,
                                             //   never your own coined terms (self-promotion rule)
  "language_of_work": "Q1860",               // optional -> P407; defaults to Q1860 for
                                             //   article/dataset, omitted for software
  "full_work_url": "https://zenodo.org/records/12345",  // optional -> P953
  "source_code_url": "https://github.com/...",  // optional, software only
  "version_control_system": "Q186055",      // optional P8423 qualifier; auto Git for github.com
  "web_interface_software": "Q364",          // optional P10627 qualifier; auto GitHub for github.com
  "retrieved": "2026-06-07"
}

Conventions enforced here (see SKILL.md and references/richness-rubric.md for why):
- P356 DOI uppercase
- author property by type: articles/datasets use P50 (author) with a P1545
  series-ordinal qualifier; software uses P178 (developer). P50 has a
  conflicts-with constraint against P31=software (Q7397), so software must
  not use P50. Never use P2093 (author name string) when a QID exists.
- References (P854 + P813) on P356 / P577 / P275 / P50 / P921 / P407 / P953;
  ORCID statement and P800 / P101 referenced with the ORCID profile URL
- P6216 (copyright status) auto-paired with P275: Wikidata's
  item-requires-statement constraint expects a license to declare its
  copyright status. CC0 -> "copyrighted, dedicated to the public domain
  by copyright holder" (Q88088423); every other license -> "copyrighted"
  (Q50423863), since CC/MIT licenses presuppose copyright exists.
- Work titles go in BOTH en and mul labels ("mul" = language-independent
  default, the showcase-item pattern); a ja label on a work is almost
  always a fabricated translated title and draws a warning. mul is valid
  for labels/aliases only, never descriptions (hard error).
- Richness lint: rubric gaps (missing ja description, missing P921, ...)
  are reported as WARN on stderr; the payload still generates (exit 0).
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
ENGLISH = "Q1860"


def warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


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


def url_snak(prop: str, value: str) -> dict:
    # URL-datatype properties (P953 etc.) use a plain string datavalue
    return string_snak(prop, value)


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


def collect_terms(spec: dict) -> tuple[dict, dict, dict]:
    """Merge flat legacy keys (label_en, description_ja, alias_en) with the
    generalized dict keys (labels/descriptions/aliases) into plain
    {lang: value} / {lang: [values]} maps. Legacy keys never override."""
    labels = dict(spec.get("labels") or {})
    for lang in ("en", "ja"):
        v = spec.get(f"label_{lang}")
        if v:
            labels.setdefault(lang, v)
    descriptions = dict(spec.get("descriptions") or {})
    for lang in ("en", "ja"):
        v = spec.get(f"description_{lang}")
        if v:
            descriptions.setdefault(lang, v)
    aliases = {lang: list(vals) for lang, vals in (spec.get("aliases") or {}).items()}
    if spec.get("alias_en") and spec["alias_en"] not in aliases.get("en", []):
        aliases.setdefault("en", []).insert(0, spec["alias_en"])
    if "mul" in descriptions:
        sys.exit("ERROR: 'mul' is valid for labels/aliases only, never descriptions")
    return labels, descriptions, aliases


def terms_payload(labels: dict, descriptions: dict, aliases: dict) -> dict:
    out: dict = {
        "labels": {lg: {"language": lg, "value": v} for lg, v in labels.items()},
        "descriptions": {lg: {"language": lg, "value": v} for lg, v in descriptions.items()},
    }
    if aliases:
        out["aliases"] = {lg: [{"language": lg, "value": v} for v in vals]
                          for lg, vals in aliases.items()}
    return out


def build_author(spec: dict) -> dict:
    orcid_url = f"https://orcid.org/{spec['orcid']}"
    ref = make_ref(orcid_url, spec["retrieved"])
    labels, descriptions, aliases = collect_terms(spec)
    if "ja" not in labels:
        warn("author has no ja label (rubric: native-script form recommended; skip if none exists)")
    if "ja" not in descriptions:
        warn("author has no ja description (rubric: recommended)")
    if not spec.get("notable_works"):
        warn("author has no notable_works -> P800 (rubric: recommended once own works have QIDs)")
    if not spec.get("fields_of_work"):
        warn("author has no fields_of_work -> P101 (rubric: recommended)")
    claims = [
        statement(item_snak("P31", "Q5")),
        statement(item_snak("P106", "Q1650915")),
        statement(string_snak("P496", spec["orcid"]), references=ref),
    ]
    for qid in spec.get("notable_works") or []:
        claims.append(statement(item_snak("P800", qid), references=ref))
    for qid in spec.get("fields_of_work") or []:
        claims.append(statement(item_snak("P101", qid), references=ref))
    payload = terms_payload(labels, descriptions, aliases)
    payload["claims"] = claims
    return payload


def build_work(spec: dict) -> dict:
    doi = spec["doi"]
    if doi != doi.upper():
        sys.exit(f"ERROR: DOI must be uppercase for P356 (got: {doi})")
    ref = make_ref(f"https://doi.org/{doi.lower()}", spec["retrieved"])
    instance_of = spec["instance_of"]

    labels, descriptions, aliases = collect_terms(spec)
    # Title is language-independent: en + mul labels (showcase-item pattern)
    labels.setdefault("en", spec["title"][:250])
    labels.setdefault("mul", spec["title"][:250])
    if "ja" in labels:
        warn("ja label on a work is usually a fabricated translated title — "
             "keep only if the work genuinely carries this Japanese title (rubric: forbidden otherwise)")
    if "ja" not in descriptions:
        warn("work has no ja description (rubric: required — e.g. '<姓>による<年>の学術論文')")
    if not spec.get("main_subjects"):
        warn("work has no main_subjects -> P921 (rubric: required ≥1; existing general-concept QIDs only)")
    if not spec.get("full_work_url"):
        warn("work has no full_work_url -> P953 (rubric: recommended)")

    claims = [
        statement(item_snak("P31", instance_of)),
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
    # P31=software); articles/datasets -> P50 author with series ordinal and
    # an optional P1932 name-as-printed qualifier.
    if instance_of == "Q7397":
        claims.append(statement(item_snak("P178", spec["author_qid"]), references=ref))
    else:
        quals = {"P1545": [string_snak("P1545", spec.get("author_ordinal", "1"))]}
        if spec.get("author_stated_as"):
            quals["P1932"] = [string_snak("P1932", spec["author_stated_as"])]
        claims.append(statement(item_snak("P50", spec["author_qid"]), references=ref,
                                qualifiers=quals))
    # P921 main subject: existing general concepts only (self-promotion rule)
    for qid in spec.get("main_subjects") or []:
        claims.append(statement(item_snak("P921", qid), references=ref))
    # P407 language of work: default English for article/dataset; software is
    # opt-in only (the natural-language axis is usually over-modeling there —
    # P277 programming language covers the code).
    language = spec.get("language_of_work")
    if language is None and instance_of != "Q7397":
        language = ENGLISH
    if language:
        claims.append(statement(item_snak("P407", language), references=ref))
    if spec.get("full_work_url"):
        claims.append(statement(url_snak("P953", spec["full_work_url"]), references=ref))
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
    payload = terms_payload(labels, descriptions, aliases)
    payload["claims"] = claims
    return payload


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

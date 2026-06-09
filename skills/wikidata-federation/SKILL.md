---
name: wikidata-federation
description: Create Wikidata items for researchers, papers, and research repositories and cross-link them with ORCID / DOI / graph.jsonld — an identifier-federation skill. Use it after publishing a new paper or DOI-registered repo to register it on Wikidata, when standing up an author item, when injecting QIDs into graph.jsonld as sameAs, or when setting up a Scholia profile. Always trigger on requests like "register this on Wikidata", "create a QID", "put the author in the knowledge graph", "add the paper to Wikidata". Also invoked as the post-release stage of release-doi / paper-deposit.
user-invocable: true
origin: shimo4228
---

# Wikidata Federation

A workflow that registers research artifacts (authors, papers, DOI-registered repos) on Wikidata and establishes a machine-readable node where ORCID ↔ Wikidata ↔ DOI ↔ graph.jsonld all cross-reference one another.

**Why do this**: ORCID, Zenodo, and GitHub are each a separate island. A Wikidata item becomes the bridge, and then (1) Scholia auto-generates an author page, (2) SPARQL can query every work, (3) the CC0 dump propagates the node into downstream DBs / LLM training corpora, and (4) citation bots grow the graph on their own.

## Safety discipline (highest priority)

- **Every write: present the full payload (or a value-diff table) to a human and obtain approval before sending.** Unconfirmed consecutive writes are forbidden. Batch approval only when the human explicitly chooses it
- Always run the duplicate check (Phase 0) before writing. Creating a duplicate is a quality incident, and deletion requires admin rights
- On error, present the API response as-is and stop. Do not retry on a guess
- Credentials only via env vars or a credentials file. Never hardcode/print them in code or conversation

## Prerequisites

1. **BotPassword**: create one at `https://www.wikidata.org/wiki/Special:BotPasswords`. Two grants are enough — "Edit existing pages" + "Create, edit, and move pages"
   - **A BotPassword is local to the wiki it was created on.** To use test.wikidata.org you must create a separate one on the test side
2. **Passing credentials**: put `WIKIDATA_USERNAME=user@botname` / `WIKIDATA_PASSWORD=...` in `~/.config/wikidata/credentials.env` (chmod 600). In a harness that re-initializes the environment per shell, an `export` will not survive, so the file approach is the reliable one
3. Python + requests (`uv run --with requests` works)

## Workflow

### Phase 0: Duplicate check (mandatory, first)

```bash
# Search for an author item by ORCID
curl -s "https://www.wikidata.org/w/api.php?action=query&list=search&srsearch=haswbstatement:P496=<ORCID>&format=json"
# Search for a work item by DOI (uppercase the DOI)
curl -s "https://www.wikidata.org/w/api.php?action=query&list=search&srsearch=haswbstatement:%22P356=<DOI-UPPERCASE>%22&format=json"
# Complement with a label search
curl -s "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=<name>&language=en&format=json&type=item"
```

If one already exists, do not create a new item — switch to adding the missing statements to that item.

### Phase 1: Fix the metadata (Zenodo side)

- **Concept DOI vs version DOI**: confirm the registration policy with the human (unifying on the concept DOI is conventional — it always resolves to the latest version and is consistent with a canonical-citation policy). Disambiguate via the `conceptdoi` field of `/api/records/<id>`
- **P577 (publication date) is the date of the first version.** A concept record's `publication_date` returns the *latest* version's date, so fetch the first version with `/api/records?q=conceptdoi:"<doi>"&allversions=true&sort=oldest&size=1`
- **P31 type mapping** (keyed on the Zenodo `resource_type.type`):

| Zenodo type | P31 | QID |
|---|---|---|
| publication (article / workingpaper) | scholarly article | Q13442814 |
| software | software | Q7397 |
| dataset | data set | Q1172284 |

- **P275 (license)**: CC BY 4.0 = Q20007257 / MIT = Q334661 / CC0 = Q6938433
- Confirm the labels of every P / Q you use with `wbgetentities` before writing (a typo'd P number silently passes as a different property)

### Phase 2: Dry run

If you do not have a test.wikidata.org BotPassword, you can substitute the **official live-wiki sandbox item Q4115189** (sanctioned for test edits). Add → remove an alias as a two-step round-trip to validate auth / CSRF / the `wbeditentity` shape, and confirm restoration by reading the item back. Note that the test wiki uses a different property-ID space from production (a dry run there validates only auth and request shape).

### Phase 3: Create the item

`scripts/gen_payload.py` turns a spec JSON into a `wbeditentity` payload; after human approval, `scripts/wd_api.py` sends it.

```bash
python3 scripts/gen_payload.py spec.json > payload.json   # see the gen_payload.py docstring for the spec format
# Present the payload to a human → after approval:
uv run --with requests python3 scripts/wd_api.py --site www --new item --data payload.json --summary "<edit summary>"
```

Payload conventions:

- **Author**: P31=Q5, P106=Q1650915 (researcher), P496=ORCID (reference: P854=ORCID URL + P813=retrieval date). English label + en/ja descriptions + "Surname, Given" alias
- **Work**: P31 (type mapping), P356=DOI **uppercase**, P1476=title (monolingual en), P577=first-version date, P275=license, **P6216=copyright status** (must pair with P275 — CC0=Q88088423 / otherwise=Q50423863; gen_payload.py auto-derives it from the license). **Authorship differs by type**: article/dataset use **P50=author QID + qualifier P1545="1"**, software uses **P178=developer** (P50 has a conflicts-with constraint against P31=software; do not use a P2093 string author when a QID exists). Software also gets P1324=GitHub URL (with qualifiers P8423=Git Q186055 + P10627=GitHub Q364 as a pair — required-qualifier constraint; gen_payload.py auto-attaches them from the github URL)
- Attach a reference (P854=DOI resolver URL + P813=retrieval date) to P356 / P577 / P275 / P50
- One item = one `wbeditentity` call (claims included). After creation, verify by reading back `Special:EntityData/<QID>.json`

### Phase 4: Inject sameAs into graph.jsonld

Anchor the QID into the repository-side graph.jsonld (Wikidata→repo is carried by P1324, repo→Wikidata by sameAs).

```bash
python3 scripts/add_qid_sameas.py --map qid_map.json graph1.jsonld graph2.jsonld          # dry-run
python3 scripts/add_qid_sameas.py --map qid_map.json --apply graph1.jsonld graph2.jsonld  # apply
```

- Matching is **exact** on identity fields (@id / sameAs / identifier / url) only. A Person node gets the author QID only when the ORCID matches
- **No whole-file re-serialization via `json.dump`** — it destroys the original formatting and produces a huge diff. The script does text surgery + semantic validation (edited tree = expected tree, exact match) to keep the diff to a few lines
- Do not create Wikidata items for your own coined terms/concepts (without an independent source it is deletable as self-promotion, and the concept's definitional authority leaks out of your normative layer). Keep concepts in the repo's graph.jsonld; hold Wikidata to the bibliographic skeleton
- After applying, commit / push / mirror per each repo's conventions (`hf-sync` etc.)

### Phase 5: Verify and report

- Present the full QID + URL list and the Scholia URL (`https://scholia.toolforge.org/author/<author-QID>`)
- Confirm search-index propagation with a haswbstatement search (expect a delay of several minutes)
- State the residual tasks: manually adding the QID to the ORCID profile (Websites & social links), OpenAlex ID (P10283) only after name resolution is settled

## Pitfalls (lessons proven in practice)

| Pitfall | Avoidance |
|---|---|
| BotPassword fails on test.wikidata | Wiki-local behavior. Create a test-side one, or substitute the Q4115189 sandbox |
| A concept record's publication_date is the latest version's date | Fetch the first version with `allversions=true&sort=oldest` |
| You meant the concept DOI but used the version DOI (or vice versa) | Always disambiguate via the `conceptdoi` field and confirm the policy with the human |
| Duplicate profiles in external DBs (OpenAlex etc.) for the same ORCID | Defer adding external-ID properties until name resolution is complete |
| Thousand-line graph.jsonld diff from re-serialization | Text surgery + semantic validation (scripts/add_qid_sameas.py) |
| Missing a repo because the local dir name differs from the GitHub repo name | Confirm the real identity with `git remote get-url origin` before declaring it "does not exist" |
| item-requires-statement constraint warning when only P275 is set | Pair it with P6216 (copyright status). gen_payload.py auto-derives it from the license. Soft constraint, so it still works, but cleaner to satisfy |
| required-qualifier constraint warning on P1324 (source code repo URL) | Attach P8423 (version control system=Git) + P10627 (web interface software=GitHub) as qualifiers. gen_payload.py auto-attaches them from the github URL |
| conflicts-with constraint warning when P50 is set on software | software (P31=Q7397) uses P178 (developer), not P50. gen_payload.py auto-detects this by instance_of. dataset/article keep P50 |

## Scripts

| script | role |
|---|---|
| `scripts/wd_api.py` | Sends `wbeditentity` only (auth → CSRF → send, maxlag=5, on error present the response and stop) |
| `scripts/gen_payload.py` | spec JSON → author/work payload generation (mechanically enforces the conventions) |
| `scripts/add_qid_sameas.py` | Injects the QID sameAs into graph.jsonld (dry-run / format-preserving / semantic validation) |

## Related skills

- `release-doi` / `paper-deposit` — call this skill as the post-release stage after a release
- `jsonld-knowledge-graph` — the canonical design for graph.jsonld; this skill's Phase 4 is the operational layer that adds QID anchors to that graph
- `hf-sync` — mirror-sync to Hugging Face after a graph update

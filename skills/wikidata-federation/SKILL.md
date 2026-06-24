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

Payload conventions (full richness checklist: [references/richness-rubric.md](references/richness-rubric.md) — own items target showcase quality, modeled on Q42 / exemplary scholarly items):

- **Author**: P31=Q5, P106=Q1650915 (researcher), P496=ORCID (reference: P854=ORCID URL + P813=retrieval date). en label + **ja label (native script, only if a genuine form exists)** + en/ja descriptions + "Surname, Given" en alias + ja reading alias. **P800=notable works** (own works with QIDs) + **P101=fields of work** (discipline QIDs, never an article). No P921 (mandatory conflicts-with P31=Q5); no P569-style personal data without explicit subject approval
- **Work**: P31 (type mapping), P356=DOI **uppercase**, P1476=title (monolingual en), P577=first-version date, P275=license, **P6216=copyright status** (must pair with P275 — CC0=Q88088423 / otherwise=Q50423863; gen_payload.py auto-derives it from the license). Title goes in **both en and mul labels** (language-independent default — never fabricate a translated ja title; ja gets a *description* instead, e.g. `<姓>による<年>の学術論文`; en description in WikiCite form `scholarly article by <Surname>, <year>`). Aliases only for *genuine* short titles. **P921=main subjects (≥1, existing general-concept QIDs only — coined terms stay in graph.jsonld)**, **P407=language (Q1860; default for article/dataset, opt-in for software)**, **P953=full-text URL**. **Authorship differs by type**: article/dataset use **P50=author QID + qualifier P1545="1" + qualifier P1932=name-as-printed**, software uses **P178=developer** (P50 has a conflicts-with constraint against P31=software; do not use a P2093 string author when a QID exists). Software also gets P1324=GitHub URL (with qualifiers P8423=Git Q186055 + P10627=GitHub Q364 as a pair — required-qualifier constraint; gen_payload.py auto-attaches them from the github URL)
- Attach a reference (P854=DOI resolver URL + P813=retrieval date) to P356 / P577 / P275 / P50 / P921 / P407 / P953 (P800 / P101 reference the ORCID profile). **Use the UTC date for P813** (a local-calendar date can be "future" in UTC and trips the range constraint until UTC midnight)
- gen_payload.py emits `WARN:` lines on stderr for rubric gaps (missing ja description, no P921, ...) — resolve or consciously accept each before sending
- **Enriching an existing lean item**: fetch `Special:EntityData/<QID>.json`, diff against the rubric, and send **only the missing pieces** — resending existing claims duplicates them (wbeditentity merges)
- One item = one `wbeditentity` call (claims included). After creation, verify by reading back `Special:EntityData/<QID>.json`
- **Post-write constraint check (mandatory)**: collect every QID written this session (created *and* edited) into a file, then run `federation_lint.py --items @touched_qids.txt`. This relays `wbcheckconstraints` over mainsnaks, qualifiers **and references** for items that appear in no graph. Triage: violations in your own data → fix now; `bad-parameters` → defect in the constraint definition on the property itself, not your data; reference-P813 range violations dated today → UTC-future timing, self-clearing. Do not report "done" to the human before this check is clean or every finding is triaged

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

### Phase 4.5: Cited-work federation (P2860)

Register the external papers that the author's own work *cites*, and add **P2860 (cites work)** edges from the author's work item. Scholia renders incoming P2860 edges on the cited work's / cited author's "Citations" panels — this is the channel through which the cited researchers' circles can discover the citing work (a passive human signal), and the CC0 dump carries the same edge into downstream DBs / LLM corpora.

1. **Duplicate check first** (Phase 0 discipline): search by `P356=<DOI-UPPERCASE>` or **P818=arXiv ID**. Many arXiv papers already have items via WikiCite/OpenAlex bots — assume existence before creating
2. **If absent, create a bibliographic-skeleton item**: P31=Q13442814 (scholarly article), P356=DOI (arXiv papers use the DataCite form `10.48550/arXiv.NNNN.NNNNN`, uppercase), P818=arXiv ID, P1476=title, P577=publication date. External authors without QIDs go in as **P2093 (author name string)** — do not create author items for third parties just to satisfy P50. **Use `gen_payload.py` `kind: "citation"`** to build this skeleton (it emits exactly these fields, no license/P50/P921, supports year-only `publication_date` and an `authors` list → P2093+ordinals). Do NOT use `kind: "work"` for third-party citations — that path is for the author's own showcase items (license + author_qid required, full rubric)
3. **P2860 goes on the *citing* side** — the author's own paper item — one statement per cited work, each with a reference (P854=resolver URL + P813=retrieval date)
4. **P2860 on software / dataset repo items is constraint-clean** (verified 2026-06: Q7397 and Q1172284 are both in the subclass closure of P2860's subject-type constraint via creative work, and `wbcheckconstraints` returns compliance on a software item carrying P2860; the property has no value-type constraint, so cited books are also valid targets). Add P2860 edges for citations the repo's knowledge graph actually documents (ExternalReference nodes), referenced to the repo's DOI resolver URL. The `.zenodo.json` `related_identifiers` channel (`release-doi` skill) remains the primary repo-side citation surface — the Wikidata edge complements it for Scholia / CC0-dump visibility, it does not replace it
5. The self-promotion rule from Phase 4 still applies: third-party paper items are bibliographic skeleton only (WikiCite practice; notability is accepted). Never seed your own coined concepts here. **The richness rubric does not apply to these skeletons** — do not enrich items you don't own the data for; showcase quality is for the author's own items only

### Phase 5: Verify and report

- Run the federation lint (below) over the graphs **plus `--items @touched_qids.txt`** — graph-only runs miss items not yet anchored in any graph (e.g. freshly created citation skeletons)
- Present the full QID + URL list and the Scholia URL (`https://scholia.toolforge.org/author/<author-QID>`)
- Confirm search-index propagation with a haswbstatement search (expect a delay of several minutes)
- State the residual tasks: manually adding the QID to the ORCID profile (Websites & social links), OpenAlex ID (P10283) only after name resolution is settled

## Federation Lint (read-only, no auth)

```bash
# graph.jsonld ↔ Wikidata の連邦整合を一括検査。複数 graph 可
# exit 0 = clean, 1 = findings, 2 = fatal
python3 ~/.claude/skills/wikidata-federation/scripts/federation_lint.py graph1.jsonld graph2.jsonld
#   --items Q1,Q2 / --items @file   graph に居ない QID も constraint 検査（post-write 検証用）
#   --suggestions      suggestion レベルの constraint 結果も表示
#   --skip-constraints wbcheckconstraints を省略（高速・API 負荷減）
```

Checks: **QID-CONFLICT**（同一 @id が graph 間で別 QID）/ **BACKLINK**（QID が P356=DOI・P1324=repo・P496=ORCID で graph 側に戻るか）/ **CONSTRAINT**（Wikidata 純正 `wbcheckconstraints` の verdict 中継 — mainsnak / qualifier / **reference** の 3 層すべて。reference 内の P813 等は UI では statement を展開しないと見えないが、ページ上部の constraint アイコンには出るので人間の目に付く）。

### なぜこの構成か（external research, 2026-06）

- **`wbcheckconstraints` API**（Wikidata 純正・匿名可）が item 単位 constraint 検査の標準。Pitfalls 表の制約（P50 conflicts-with software、P1324 必須 qualifier、P275/P6216 ペア）は**すべて native に検査される — ローカルに再実装しない**。lint はこの verdict を中継するだけ
- **entityshape**（ShEx 系 Python, 2023-07 停止・ShEx 部分対応）、**wmde/wikidata-constraints-violation-checker**（2023-09 から休眠、全 Wikidata 統計向け）— いずれも採用不可
- どの標準ツールも見ない死角 = **cross-system reciprocity**（graph.jsonld の sameAs QID が逆方向に戻ってくるか、複数 graph 間の QID 一貫性）。ここだけが custom 実装（`scripts/federation_lint.py`）
- EntitySchema (ShEx) への移行条件: item の型ごとに「必須 property セット」を宣言的に強制したくなった時点。現状は Phase 3 の payload 規約 + wbcheckconstraints で足りている

## Pitfalls (lessons proven in practice)

| Pitfall | Avoidance |
|---|---|
| BotPassword fails on test.wikidata | Wiki-local behavior. Create a test-side one, or substitute the Q4115189 sandbox |
| A concept record's publication_date is the latest version's date | Fetch the first version with `allversions=true&sort=oldest` |
| You meant the concept DOI but used the version DOI (or vice versa) | Always disambiguate via the `conceptdoi` field and confirm the policy with the human |
| Duplicate profiles in external DBs (OpenAlex etc.) for the same ORCID | Defer adding external-ID properties until name resolution is complete |
| Thousand-line graph.jsonld diff from re-serialization | Text surgery + semantic validation (scripts/add_qid_sameas.py) |
| `add_qid_sameas.py --apply` crashed with JSONDecodeError while dry-run was clean | Single-line node objects (`{"@id": ...}` all on one line) — fixed 2026-06: the inserter now detects single-line vs multi-line node spans and inserts `sameAs` inline for the former (the old indent capture injected a stray `{`). If you hit a similar crash, check the node's line formatting |
| Missing a repo because the local dir name differs from the GitHub repo name | Confirm the real identity with `git remote get-url origin` before declaring it "does not exist" |
| item-requires-statement constraint warning when only P275 is set | Pair it with P6216 (copyright status). gen_payload.py auto-derives it from the license. Soft constraint, so it still works, but cleaner to satisfy |
| required-qualifier constraint warning on P1324 (source code repo URL) | Attach P8423 (version control system=Git) + P10627 (web interface software=GitHub) as qualifiers. gen_payload.py auto-attaches them from the github URL |
| conflicts-with constraint warning when P50 is set on software | software (P31=Q7397) uses P178 (developer), not P50. gen_payload.py auto-detects this by instance_of. dataset/article keep P50 |
| Item-creation throttle after ~8 rapid creations ("Cannot automatically assign ID" / スパム対策) | Account-level creation rate limit, separate from edit limits. Space creations ≥20s apart; on throttle, back off 120s× attempt and resume from a persisted key→QID map so the batch is idempotent |
| Famous arXiv papers (MemGPT, Voyager, CoALA) genuinely absent from Wikidata | WikiCite bot coverage has declined since ~2023 — do not assume existence, but still run both P818 and label searches before creating |
| P813 (retrieval date) shows a range-constraint warning right after writing | The local calendar date can still be "in the future" in UTC (e.g. JST morning). The warning self-clears at UTC midnight — no data fix needed. Avoid it entirely by using the UTC date for retrieval dates |
| P31=Q571 (book) trips a none-of constraint | Q571 is the physical object/medium; use Q47461344 (written work) for cited books |
| P123 (publisher) on a P31=written work item trips conflicts-with | Publisher belongs on *edition* items in the work/edition split. For a single-item book skeleton, omit P123 — the DOI reference carries the publisher |
| Constraint findings hide inside references — graph-only lint runs look clean while item pages show warning icons | Lint walks mainsnak+qualifier+**reference** snaks (fixed 2026-06). Always run the post-write check with `--items @touched_qids.txt` so items absent from graphs are covered |
| A non-ASCII or uppercase external-ID trips a format-constraint warning (e.g. Hugging Face P12201 regex `[a-z0-9]+` vs the canonical uppercase username `Shimo4228`; a LinkedIn P6634 value with a Japanese vanity slug) | Check the property's P1793 format regex **before** writing. When the canonical value — the one whose formatter URL resolves 200 — violates a too-narrow regex, keep the correct value and triage the warning as a constraint-definition defect; do **not** lowercase/transliterate it (that makes the formatter URL 307-redirect or dead). Note `\p{L}`-based regexes (e.g. P6634) *do* permit non-Latin letters, so a Japanese slug is compliant there — only an actually-narrow class like `[a-z0-9]+` warns |

## Scripts

| script | role |
|---|---|
| `scripts/wd_api.py` | Sends `wbeditentity` only (auth → CSRF → send, maxlag=5, on error present the response and stop) |
| `scripts/gen_payload.py` | spec JSON → author / work / **citation** payload generation (mechanically enforces the conventions). `kind: "citation"` = third-party bibliographic skeleton (no license/P50/P921, year-precision dates, `authors` list → P2093) |
| `scripts/add_qid_sameas.py` | Injects the QID sameAs into graph.jsonld (dry-run / format-preserving / semantic validation) |

## Related skills

- `release-doi` / `paper-deposit` — call this skill as the post-release stage after a release. The repo-side citation edges (`.zenodo.json` `related_identifiers` with `relation: references`) live in `release-doi`; this skill owns the Wikidata-side P2860 counterpart (Phase 4.5)
- `jsonld-knowledge-graph` — the canonical design for graph.jsonld; this skill's Phase 4 is the operational layer that adds QID anchors to that graph
- `hf-sync` — mirror-sync to Hugging Face after a graph update

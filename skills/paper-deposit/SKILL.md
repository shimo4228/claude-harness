---
name: paper-deposit
description: >-
  Deposit a finished, reviewed academic paper / position paper / preprint to a
  DOI registry (Zenodo) as a standalone record, optionally cross-post it to SSRN
  for extra reach, generate the PDF from Markdown, and cross-link the minted DOI
  back into a research-program repository (.zenodo.json / README / graph.jsonld /
  llms.txt). Use this whenever the user wants to "ship", "deposit", "publish",
  "register a DOI for", "put on Zenodo", or "submit to SSRN" a paper that is
  already written and review-passed — even if they only say "let's get this
  paper out". This runs AFTER paper-ecosystem review passes. It is NOT for
  releasing a whole repository (that is release-doi) and NOT for drafting or
  reviewing the paper (that is paper-writing / paper-ecosystem).
user-invocable: true
origin: shimo4228
---

# Paper Deposit

Ship a finished paper as a citable, DOI-bearing artifact and wire it into the
project's citation graph. This skill owns the **post-write half** of the
lifecycle: PDF → Zenodo deposit → (optional) SSRN → federation cross-link. The
writing and the strict review gate live upstream in `paper-writing` and
`paper-ecosystem`; this skill assumes that gate has passed.

## Where this sits

| Stage | Owner |
|---|---|
| Draft the paper | `paper-writing` |
| Review gate (source-fidelity, vocabulary, citation) | `paper-ecosystem` + its agents |
| **Deposit + federate (this skill)** | **`paper-deposit`** |
| Release a whole repo with a DOI | `release-doi` (different: GitHub tag → Zenodo webhook) |

Why Zenodo as the durable core and SSRN only as an optional layer: Zenodo is
audience-neutral open archival — it mints a DOI, the record is open, and
machines (LLMs, citation-graph crawlers via DataCite/OpenAIRE/Scholix) ingest
it. That makes the Zenodo deposit the strategy-native artifact on its own. SSRN
adds reach into a defined scholarly audience but is a separable bonus that can
be dropped without losing the durable record. For the judgment of *which*
channels a given author should use, defer to the `authorship-strategy` skill —
this skill is the mechanical how, not the should.

## Preconditions (do not skip)

1. The paper is **final and review-passed** — `paper-ecosystem` agents
   (source-fidelity-checker, vocabulary-consistency-checker, citation-formatter)
   have run and their findings are resolved. Do not re-run them here unless the
   content changed.
2. The title-page metadata is settled: author, ORCID, version, date, license.
   Fill any `(to be added at deposit)` placeholders now. If the filename still
   carries an abandoned channel name (e.g. an `ssrn-` prefix from an earlier
   plan), rename it to something channel-neutral — the deposited filename is
   visible to readers.

## Step 1 — Generate the PDF from Markdown

Zenodo accepts any format and Markdown is the most LLM-ingestable, so deposit
**both** the Markdown source and a PDF. SSRN requires a PDF. Generate it with
`pandoc` + the `typst` engine (fast, good Unicode handling, no heavy LaTeX
install):

```bash
# strip a leading nav/language line you don't want in the PDF, then render
tail -n +3 paper.md | pandoc -f markdown -o paper.pdf \
  --pdf-engine=typst -V fontsize=10pt -V margin-x=2cm -V margin-y=2cm
```

For a CJK-language PDF (Japanese, Chinese, Korean), pass a CJK serif font the
engine can find, or glyphs render as boxes:

```bash
tail -n +3 paper.ja.md | pandoc -f markdown -o paper.ja.pdf \
  --pdf-engine=typst -V mainfont="<a CJK serif font installed on this machine>" \
  -V fontsize=10pt -V margin-x=2cm -V margin-y=2cm
# on macOS, "Hiragino Mincho ProN" is one such font; `typst fonts | grep -i <name>`
# lists what is available. Pick whatever the platform actually has.
```

Notes: prose-only figure *captions* (blockquotes describing a figure, no image
file) render fine — they stay as caption text. Markdown tables and fenced code
blocks render correctly. Open the first page and eyeball it before depositing.

## Step 2 — Deposit to Zenodo (the durable core)

Use the bundled script. It creates a **draft only and never publishes** —
publishing is irreversible (a Zenodo record cannot be deleted once published,
only superseded by a new version), so the human reviews the draft in the web UI
and clicks Publish themselves.

**Token handling** (a credential — treat it as one):
- Have the user create a Zenodo personal access token with scope
  `deposit:write` (Settings → Applications → new token).
- Have them save it to a gitignored file (e.g. `.notes/.zenodo-token`) via a
  text editor — *not* pasted into chat (it would land in the transcript) and
  *not* typed into a shell command (it would land in shell history).
- The script reads it and never prints it. **Delete the token file after use.**

Prepare the metadata as JSON (a bare metadata dict or `{"metadata": {...}}`):

| field | value |
|---|---|
| `upload_type` | `publication` |
| `publication_type` | `workingpaper` (or `preprint`) |
| `title`, `description` | title; abstract (HTML allowed — wrap paragraphs in `<p>…</p>`) |
| `creators` | `[{"name": "Last, First", "orcid": "…", "affiliation": "…"}]` |
| `keywords` | the paper's keyword list |
| `license` | `cc-by-4.0` |
| `language`, `version`, `publication_date` | e.g. `eng`, `v1`, `YYYY-MM-DD` |
| `related_identifiers` | `isSupplementTo` → the companion repo's **concept DOI**; `cites` → each prior work's DOI / `arXiv:NNNN.NNNNN` |

Run (test against sandbox first if unsure — `--sandbox` hits sandbox.zenodo.org
and has no production effect):

```bash
uv run --directory ~/.claude/skills/paper-deposit python -m scripts.zenodo_deposit \
  --token-file <path-to-gitignored-token> \
  --metadata <path-to-metadata.json> \
  --files paper.pdf paper.md paper.ja.pdf paper.ja.md
```

The script prints the **reserved version DOI** and the draft URL. Tell the user
to review the draft (files, metadata, related identifiers, license, Public
visibility) and click **Publish**. On publish Zenodo mints two DOIs: a
**version DOI** (this v1) and a **concept DOI** (all-versions, always resolves
to the latest) — the concept DOI is the one to cite and to use in cross-links.

After publish, delete the token file.

## Step 3 — Stamp the DOI back onto the paper

Add the minted **concept DOI** to the paper's title page (a `**DOI:**` line) and
regenerate the PDF (Step 1). This gives any downstream channel (SSRN, a personal
site) a self-referencing open-access pointer. The already-published Zenodo PDF
is immutable and does not need this — it is for the copies that go elsewhere.

## Step 4 — SSRN cross-post (OPTIONAL bonus reach)

> ⚠️ **Time-bound.** SSRN's submission UI changes; the field names and steps
> below reflect a 2026 snapshot. Verify against the current UI. SSRN is a
> separable reach layer — if the submission flow feels wrong for the author,
> drop it; the Zenodo record already secured the artifact.

Manual web upload (no deposit API). Known sharp edges, in order:

1. **Content Format** = Paper → **Preprint** (a self-deposited working paper is
   a preprint here; it is not journal-published or a conference proceeding).
2. **Classifications**: search and pick the classifications matching the paper's
   *actual* domains (every SSRN classification is named "… Alert" — that suffix
   just means the distribution network; pick by content). Don't over-classify;
   SSRN's team reviews them anyway.
3. **"Has a DOI" field (Publication Details)**: SSRN resolves this against
   **Crossref**, but Zenodo DOIs are registered with **DataCite** — so pasting
   the Zenodo DOI returns "not found at Crossref". This field is for a
   *published journal version's* DOI, which a preprint doesn't have. **Leave it
   empty**; SSRN mints its own DOI for the preprint.
4. **Review step — fix PDF-extraction artifacts.** SSRN auto-extracts title and
   abstract from the PDF and reliably mangles two things: (a) a **title colon is
   dropped** when title and subtitle are separate PDF headers (they get
   concatenated with a space), and (b) **em-dashes ( — ) collapse to hyphens or
   join adjacent words** (e.g. `work — along` → `work-along`, and a
   line-broken hyphenation can fuse like `artificial-impossibility` →
   `artificialimpossibility`). Re-paste the clean title and abstract from the
   source text. (When handing clean text to the user to paste, give it as a
   file — terminal Markdown rendering breaks line breaks on copy.)
5. **JEL codes**: leave empty unless the paper is economics. **Research
   integrity** statements are optional (a non-empirical paper has no
   funder/ethics/competing-interests to declare — short "no competing
   interests" / "no external funding" lines are polish, not required).
6. Submit → moderation review (~1–2 days) before the listing goes public.
   SSRN deposit is ORCID-linked and non-anonymous.

## Step 5 — Cross-link the DOI into the federation

Wire the minted concept DOI back into the companion repository so the paper
becomes a node in the project's citation graph (this is the strategy payoff —
the deposit feeds the citation infrastructure). Update, per the repo's existing
conventions:

- **`.zenodo.json`** — add a `related_identifiers` entry: the paper's concept
  DOI with `relation: isReferencedBy`, `resource_type: publication-workingpaper`
  (propagates to the repo's own Zenodo metadata on its next release).
- **README** (and any translated READMEs) — a short "Related publication"
  section citing the paper with its concept DOI.
- **`llms.txt` / `llms-full.txt`** — a one-line companion-paper fact.
- **`graph.jsonld`** — add a `ScholarlyArticle` node for the paper (id = its
  DOI URL) and a `subjectOf` (or equivalent) edge from the project node to it.
  Follow `jsonld-knowledge-graph` for node shape and the CODEMAPS-vs-graph role
  boundary (graph encodes the *concept*; CODEMAPS encodes *file locations* — a
  deposited paper that has no in-repo file gets a graph node but no CODEMAPS
  entry).

Validate any edited JSON (`python -c "import json,sys; json.load(open(sys.argv[1]))" graph.jsonld .zenodo.json`),
commit (`docs:`), and push / run `hf-sync` per the project's release cadence —
the cross-links go live on GitHub and the HF mirror only once pushed/synced.

Optionally, register the paper as a Wikidata item (P356 = concept DOI,
P50 = author QID) and anchor the QID back into `graph.jsonld` via the
`wikidata-federation` skill — this extends the federation beyond the repo's
own files into the global knowledge graph (Scholia, SPARQL, CC0 dumps).

## Quick checklist

- [ ] Review gate passed (paper-ecosystem); placeholders filled; filename neutral
- [ ] PDF(s) generated and eyeballed (CJK font set if needed)
- [ ] Zenodo: draft created via script, human reviewed + **published**, both DOIs recorded; token file deleted
- [ ] DOI stamped on title page; PDF regenerated for downstream channels
- [ ] (optional) SSRN: Preprint, Crossref-DOI field empty, title/abstract artifacts fixed
- [ ] Federation cross-links updated, JSON validated, committed; push/hf-sync per cadence

See `references/inspiration.md` for the worked example this skill was distilled
from.

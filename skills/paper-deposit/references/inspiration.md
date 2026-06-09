# Inspiration / worked example

This skill was distilled from one concrete deposit, recorded here so the
SKILL.md body can stay portable (no project-specific DOIs, paths, or fonts in
the instructions themselves).

## Origin: the AAP position paper (2026-05-23)

The flow was first executed for the *Agent Attribution Practice* (AAP) position
paper, *"Distributing Accountability, Not Capability: Phase Separation and the
LLM Workflow Quadrant in Autonomous AI Agent Architectures"* (single author,
Independent researcher).

What happened, mapped to the skill's steps:

- **Preconditions.** The paper had been drafted and shelved as a `.notes/`
  working file. Before deposit, the `paper-ecosystem` agents ran on the
  un-audited sections: source-fidelity-checker found one real DRIFT (a
  self-contradicting sentence) plus minor partials; vocabulary-consistency
  found a term-label drift (`pre-deployment` vs `pre-named gap-bearer`) and an
  essence/consequence ordering issue; citation-formatter passed. All fixed in
  both the English source and the Japanese mirror. The `ssrn-` filename prefix
  (a leftover from an abandoned SSRN-first plan) was renamed to channel-neutral.

- **PDF.** `pandoc --pdf-engine=typst`. The Japanese mirror needed
  `-V mainfont="Hiragino Mincho ProN"` (a macOS-installed CJK serif) or the
  glyphs rendered as boxes. Figures were prose-only caption blockquotes and
  rendered fine.

- **Zenodo.** A draft was created via the urllib script (the ancestor of
  `scripts/zenodo_deposit.py`), uploaded EN+JA × PDF+MD, set metadata
  (`upload_type=publication`, `publication_type=workingpaper`, `cc-by-4.0`,
  `related_identifiers`: `isSupplementTo` the AAP repo concept DOI +
  `cites` Elish 2019 / Yao 2022 arXiv / NIST AI RMF). The script left it as a
  draft; the human reviewed and published in the web UI.
  - Minted: **version DOI `10.5281/zenodo.20353790`**, **concept DOI
    `10.5281/zenodo.20353789`** (all-versions).
  - Web-UI gotcha that surfaced: the "Do you already have a DOI?" radio
    defaulted to "Yes" with an empty box (which errors). The correct choice for
    a Zenodo-minted DOI is **"No, I need one"** — the reserved DOI is used.
  - Related-works rows required a per-row **Resource type** (not set by the
    API): the two repo DOIs → Software; the cited papers → Publication.

- **Stamp + SSRN.** The concept DOI was added to the title page and the PDF
  regenerated. SSRN cross-post hit every artifact in the skill's Step 4 list:
  Content Format Paper→Preprint; classifications chosen by search (Artificial
  Intelligence + AI - Law, Policy & Ethics + Information Technology & Systems);
  the "Has a DOI" field rejected the Zenodo DOI as "not found at Crossref" (left
  empty); and the Review step showed the title with its colon dropped
  (`Not Capability Phase Separation`) and the abstract with em-dashes collapsed
  (`work-along`, `artificialimpossibility`) — both fixed by pasting clean text
  delivered to the user as `.txt` files (terminal Markdown copy broke the line
  breaks).

- **Federation cross-link.** The concept DOI was wired into `.zenodo.json`
  (`isReferencedBy` / `publication-workingpaper`), `README.md` / `README.ja.md`
  ("Related publication"), `llms-full.txt`, and `graph.jsonld` (a
  `ScholarlyArticle` node + a `subjectOf` edge from the AAP project node).
  Committed as `docs:`; push + `hf-sync` left to the project's release cadence.

## The judgment behind it (why Zenodo-core / SSRN-bonus)

The strategic framing — Zenodo as the durable, strategy-native core and SSRN as
a droppable reach layer — came from the `authorship-strategy` skill and a
session insight: for an emerge-audience strategy, the friction that matters is
in *writing toward a defined audience*, not in *depositing a finished artifact*.
A written paper deposited to audience-neutral archival (Zenodo, feeding the
DataCite/OpenAIRE citation graph) is strategy-aligned; SSRN's defined-audience
reach is a separable bonus. The SKILL.md keeps only the mechanical workflow and
points to `authorship-strategy` for this should-question, so the skill stays
usable by authors who don't share that specific strategy.

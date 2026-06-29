# Inspiration & Origin

This file keeps the project-specific origin story and canonical pointers out of
`SKILL.md`, so the skill stays portable (per the skill-portability rule).

## Why this skill exists

`readme-writer` was built as the **human-surface counterpart** to
`llms-txt-writer`. A research program had optimized its AI/machine surfaces
(`llms.txt`, `llms-full.txt`, `graph.jsonld`) to a high degree while human
organic attention stayed near zero, and each repo's README felt "half-baked" —
neither a good human entrance nor a clean machine artifact.

The resolution was not a separate human landing page (redundant, and AI search
devalues redundancy) but treating the README as the **single canonical human +
search + AI-Overviews entrance**, with facts kept consistent across all surfaces
(diverging content is cloaking).

## Why structural lint + holistic review, not a scorer

An early design proposed a `geo_check.py`-style static analyzer for READMEs.
That was rejected: `geo_check`'s section-ratio metrics rest on empirical
LLM-citation research, but README "quality" (human hook, value proposition,
narrative) is a semantic judgment with no equivalent deterministic base.

Grounded in:

- **AKC ADR-0008 "Code-LLM Layering"** — code owns structural determinism; LLM
  owns meaning; LLM scoring is justified only as input to a code-owned decision.
  https://github.com/shimo4228/agent-knowledge-cycle/blob/main/docs/adr/0008-code-and-llm-collaboration.md
- **`when-code-when-llm`** — the structural-vs-semantic decision axis.
- **signal-first / scaffold-dissolution** (AKC) — emit only what changes the
  next action; a quality score nothing consumes is scaffolding that constrains a
  high-capability model.

So the skill splits: a thin deterministic `readme_lint.py` for structural
hygiene, and a holistic LLM review (rubric-as-lens, never scored) for meaning.

## 2026-06 extension: visual-first + the LLM-read floor

A follow-up investigation (three decorrelated evidence streams: external web
research, mining the author's own `authorship-strategy` research repo, and a
cross-model Codex review) reshaped the skill from "human surface only" to
"human surface that is also the reliably-assumable LLM grounding surface."

Load-bearing findings (external, citable — kept generic in `SKILL.md`):

- AI-search / citation crawlers do **not** meaningfully fetch `llms.txt`
  (Ahrefs 2026-05, 137,210 domains: ~97% of `llms.txt` files get zero requests;
  SE Ranking 2025: ~10% adoption; Google publicly declined to support it).
- On direct live fetch, `graph.jsonld` is treated as plain text by major engines
  (SearchVIU 2025-10 controlled test) — it is **not** a reliable citation
  substitute for facts stated in README prose.
- A human-only README can *degrade* an LLM's grasp vs. no context
  (ReadMe.LLM, arXiv:2504.09798, DeepSeek-R1 case) — justifying a machine-
  graspable floor.
- Text-ingestion paths (Claude `web_fetch`, GitMCP, ChatGPT's GitHub connector)
  pass README images **only** as author alt-text; pixels are never vision-read.
  → alt-text is a hard floor, and a raster diagram replacing prose deletes that
  information for an LLM. Mermaid is the dual-readable primitive.
- REFUTED en route (do not reintroduce): a "500–1500 word sweet spot" and
  "visual READMEs get more stars per GitHub's own research" — both traced to
  uncited single-source anecdotes / a fabricated attribution.

Author's own research line (personal provenance kept out of `SKILL.md`):

- `authorship-strategy` ADR-0019 "structural optimization vs content
  authenticity" — the body's one-line rule "optimize how the idea travels,
  never what the idea is" is this ADR's. Adding AI-legibility *structure* is
  legitimate at any intensity; bending prose to a retrieval reward function is
  prohibited. Citation/stars are explicitly not success metrics.
- ADR-0006 / ADR-0009 (dual-entry + asymmetric rebalance), ADR-0007
  (human-attention-not-a-metric), and the first-party probe `probe-baseline-
  2026-06` informed the floor design. Note: that repo's earlier bet that
  `graph.jsonld` backstops the grounding path is *not* verified by its own
  data, which is why the README floor is treated as load-bearing here.

Codex (cross-model) corrections folded in: claim calibrated to "the only
*reliably-assumable* surface" (not "only"); `llms.txt`/`graph` should derive
from a structured **manifest** (`CITATION.cff` / `.zenodo.json` / frontmatter),
never from README prose; the new lint checks are all **advisory (warning)** to
avoid corpus-wide false positives; and the dominant risk is letting "restructure,
not thin" turn every README into a disguised `llms-full.txt` — the floor is a
*small* non-negotiable core, everything above it is cut or relocated.

(Claude Design was evaluated and deliberately left out: it is a deck / prototype
/ landing-page tool whose exports do not embed in GitHub markdown, so it is
simply not part of the README-visual path — no anti-pattern note needed.)

## Canonical context

- Author: shimo4228. Research-program hub aggregates several DOI-registered lines.
- Counterpart skills: `llms-txt-writer` (AI surface), `jsonld-knowledge-graph`
  (graph), `context-sync` (cross-surface fact consistency), `writing-ecosystem`
  (long-form human prose).

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

## Canonical context

- Author: shimo4228. Research-program hub aggregates several DOI-registered lines.
- Counterpart skills: `llms-txt-writer` (AI surface), `jsonld-knowledge-graph`
  (graph), `context-sync` (cross-surface fact consistency), `writing-ecosystem`
  (long-form human prose).

---
name: cited-source-mirror-verification
description: "Verify a cited empirical/numeric claim against an open mirror (aiXiv, OpenAlex, Semantic Scholar, the author's own copy) before citing it, whenever the primary source is access-blocked (SSRN / publisher 403, paywalled PDF) OR the claim arrived through an LLM-generated research digest, daily-research note, or WebSearch summary. Use this whenever you are about to cite a statistic, effect size, odds ratio, percentage, p-value, or empirical result you have NOT read in the primary — especially before committing citations to a durable artifact (paper, knowledge graph, .zenodo.json, ADR, DOI repo). LLM digests and secondary blogs routinely reframe a methodological artifact or a limitation as a headline finding, so do not cite a number you have only seen in a summary."
user-invocable: false
origin: shimo4228
---

# Verify Blocked Primary Sources Against an Open Mirror

A number you cite carries the authority of its primary, but it usually reaches
you through a chain — **LLM-generated report → WebSearch summary → secondary
blog → primary paper** — and each hop can drop or distort the load-bearing
detail. The primary is also frequently access-blocked (SSRN and many publishers
return HTTP 403 to bots; paywalled PDFs). Citing from the digest ships the
secondary's framing, not the source's. This skill is the discipline that closes
that gap before a citation becomes durable.

## Why this matters (the failure it prevents)

Concrete case (2026-06): a research digest cited *"a significant negative
association (OR = 0.546)"* and a WebSearch summary presented it as a finding —
"schema markup reduces AI citation." The primary abstract, reached only through
an open mirror (aiXiv), flagged that same number explicitly as a **methodological
artifact** that the controlled analysis then corrected for. The real finding was
the opposite-shaped *"presence isn't the lever; richness is."* Citing the
secondary framing would have shipped a misleading claim into a DOI-registered
repository whose own stated discipline is citation fidelity — a self-inflicted
ghost citation.

The lesson is not "digests are bad." It is that **a summary preserves the number
while losing its epistemic status** (finding vs artifact vs baseline vs
limitation), and the status is exactly what makes the citation true or false.

## How to verify

When the claim is empirical/numeric AND the primary is access-blocked (or the
claim came via a digest you have not read past):

1. **Find an open mirror of the *same* paper**, in rough order of fidelity:
   - aiXiv / arXiv — SSRN and conference papers are often cross-posted; search by title.
   - OpenAlex (`https://api.openalex.org/works/doi:<DOI>`) or Semantic Scholar —
     but confirm the abstract field isn't null before trusting it.
   - The author's own copy / institutional page / a slide deck.
   - Google Scholar's indexed snippet — last resort, partial, but often quotes the abstract.
2. **Verify against the mirror, not the digest** — three things, not just the number:
   the **exact value**, its **direction** (which arm/group is higher — summaries
   swap these), and its **framing** (is the headline figure a finding, an artifact,
   a baseline, or a limitation the paper itself rejects?).
3. **Treat the digest/summary as a lead, never a source.** Trust degrades up the
   chain: `primary > open mirror of the primary > OpenAlex/Scholar > secondary blog > LLM digest`.
   A WebSearch result that quotes a marketing blog is two hops below the paper.
4. **If nothing openable verifies the numbers, cite only what you can.** Soften to
   the verifiable core (the controlled design, the qualitative direction) and drop
   the specific figures rather than passing through an unverified number. State
   that the specifics are unverified if they matter.

## Worked check

```bash
# Is the primary actually blocked?
curl -s -o /dev/null -w "%{http_code}\n" "https://www.ssrn.com/abstract=<id>"   # 403 = blocked
# Find a mirror (WikiCite/aiXiv items often exist):
curl -s "https://www.wikidata.org/w/api.php?action=query&list=search&srsearch=<title-words>&format=json"
```

Then WebFetch the open mirror's abstract page and ask it pointedly: *what is the
exact value, which group is higher, and does the paper present this figure as a
finding or as an artifact/limitation?* — so the framing, not just the digit,
gets confirmed.

## When this triggers

- You are about to cite a statistic, effect size, OR/coefficient, percentage, or
  result that you have **not read in the primary**.
- The claim arrived through an **LLM digest, daily-research note, or WebSearch summary**.
- The primary returns **403 / is paywalled / has no mirrored abstract**.
- You are committing citations to a **durable artifact** — a paper, a
  `graph.jsonld` / `.zenodo.json` citation surface, an ADR, a DOI release.
- A source-fidelity reviewer reports a cited number as **UNCHECKED** because the
  primary could not be opened.

## Anti-patterns

- Citing a number straight from an LLM digest or a single SEO/marketing blog.
- Trusting a WebSearch summary's *framing* — it may have silently dropped
  "this was an artifact" or "this did not replicate."
- **Chain-of-secondaries**: your repo's files all agree with one another because
  they share one unverified upstream. That is internal consistency, not
  verification — every surface being wrong the same way looks identical to every
  surface being right.

## Related

- `fact-checker` agent → "Local-Source Verification" — the complement. That mode
  reconciles a *draft's internal* claims (dates, counts, order) against machine
  records (logs, git, timestamps); this skill verifies *external cited primaries*.
  Reach for that one for "did this happen when/how-many-times I wrote," and this
  one for "is this cited number real and framed correctly."

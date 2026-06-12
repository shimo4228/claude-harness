# Item Richness Rubric

Target quality bar for items this skill creates, modeled on Wikidata showcase items
(Q42) and exemplary scholarly items (Q30249683 "Attention Is All You Need"), constrained
to what transfers to research artifacts. Constraint columns verified against live
property definitions (P2302) on 2026-06-12.

**What does NOT transfer from showcase items**: sitelinks (no Wikipedia articles),
100-language labels (bot-translated), biographical properties (P569 birth date etc. —
excluded for living persons; add only with the subject's explicit approval).

**Scope guard**: this rubric applies to the author's *own* items (author / own works /
own repos). Third-party citation skeletons (Phase 4.5) stay bibliographic-minimal by
WikiCite practice — do not enrich items you don't own the data for.

## Terms (labels / descriptions / aliases)

| Item kind | Required | Recommended | Forbidden |
|---|---|---|---|
| Work (article / software / dataset) | label `en` = title; description `en` (WikiCite form: `scholarly article by <Surname>, <year>` / `software by ...`); description `ja` (e.g. `<姓>による<年>の学術論文`) | label `mul` = title (language-independent; the exemplar pattern — ja/other languages then fall back to it); aliases `en` for *genuine* short titles or well-known abbreviations | **Translated titles as ja label** — a paper's title is its title; do not fabricate a Japanese title. Invented aliases |
| Author (Q5) | label `en`; description `en` + `ja`; alias `en` "Surname, Given" | label `ja` (native script — a genuine Japanese form, not a transliteration guess); aliases `ja` (kana reading etc.) | Fabricated name variants |

Note: `mul` is valid for **labels and aliases only**, never descriptions.

## Statements — Work items

| Property | Status | Constraint notes (verified 2026-06-12) |
|---|---|---|
| P31 / P356 / P1476 / P577 / P275+P6216 / P50(or P178) | Required | Existing conventions (SKILL.md Phase 3) — unchanged |
| **P921** main subject | Required (≥1) | MANDATORY conflicts-with P31=Q5 → work items only, never authors. Values must be **established concepts with existing QIDs** (e.g. Q11660 AI) — never your own coined concepts (self-promotion rule, SKILL.md Phase 4) |
| **P407** language of work | Required (article / dataset); opt-in for software | Q1860 for English. MANDATORY conflicts-with P31=Q5 → work items only. For software the natural-language axis is usually over-modeling (P277 programming language covers code); add P407 only when the software *is* a language-bearing work (docs corpus etc.) |
| **P953** full work available at URL | Recommended | Zenodo record URL or equivalent open full-text URL. Allowed qualifiers include P407, P275 |
| **P1932** "object named as" qualifier on P50 | Recommended | Records the author name string as printed (exemplar pattern) |
| P1433 published in | **Omit for repository deposits** | Zenodo is a repository, not a venue; heavy none-of constraint list. Use only when a real venue (journal / proceedings) exists |
| P1104 number of pages | Optional | conflicts-with P31=Q47461344 (written work) — articles only, skip unless trivially known |

## Statements — Author items

| Property | Status | Constraint notes (verified 2026-06-12) |
|---|---|---|
| P31=Q5 / P106 / P496+ref | Required | Existing conventions — unchanged |
| **P800** notable work | Recommended (own works with QIDs) | subject-type includes Q5; value-type expects work classes (scholarly articles clean; verify software/dataset values with the post-write `wbcheckconstraints` on first use) |
| **P101** field of work | Recommended | Values must be **fields/disciplines** (none-of Q13442814 — never point at an article). E.g. Q11660 (artificial intelligence) |
| P735 / P734 given/family name | Optional | Values must be *existing name items* (Q202444 / Q101352 instances). Search first; skip if no name item exists — do not create name items |
| **P921** | **Forbidden** | MANDATORY conflicts-with P31=Q5 |
| P569 etc. (personal data) | **Excluded** | Living person; only with explicit subject approval |
| P10283 OpenAlex | Deferred | Until name resolution is settled (SKILL.md Phase 5) |

## References

Every added statement keeps the existing discipline: P854 (resolver / profile URL) +
P813 (retrieval date, **UTC**). P921/P407/P953 reference the work's DOI resolver URL;
P800/P101 reference the ORCID profile or the work's DOI.

## Enrichment of existing lean items (backfill)

When upgrading an existing item to this rubric: fetch `Special:EntityData/<QID>.json`
first, diff against the rubric, and generate a payload containing **only the missing
pieces** (wbeditentity merges; resending existing claims duplicates them). Never
resend an existing statement as a GUID-less claim. To amend an existing statement
(e.g. backfill a missing reference or qualifier), key the claim with the statement's
exact GUID (`id` field) so wbeditentity replaces it in place — reproduce the original
mainsnak/qualifiers verbatim and use the current UTC date for the new P813. Same
human-approval + post-write lint discipline as creation.

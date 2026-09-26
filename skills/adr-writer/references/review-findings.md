<!-- origin: shimo4228 -->

# Catalog of Frequent ADR Review Findings (for write-time prevention; a dated casebook)

Frequent patterns distilled from adr-reviewer's finding history (contemplative-agent git history + harness cases, mined 2026-08-26).
**Its role is a casebook for prevention** — the canonical review criteria are
`~/.claude/agents/adr-reviewer.md`, and the canonical mechanical checks are `scripts/adr_lint.py`. This file
holds only "concrete examples to self-check against before writing" and does not duplicate the criteria.

Read each case as a dated hypothesis with a commit reference.

**Correspondence with mechanical checks (2026-09-16, ADR-0071).** Existence of numbers in §1 is reported by `refs` in
`adr_review_evidence.py`; presence of the Note on the old ADR in §2 / §4 by `relations.targets[].annotation_lines`; §5 by
`ignored` / `outside_repo` in `paths.flagged`; the denominator in §6 by `numbers.percent_without_denominator`;
and detection of count conditions in §7 by `review_when.items[].count_condition`. **Whether the cited content matches (second half of §1),
where surviving scope is placed (§2), provenance of coined terms (§3), and the grounds for full / partial (§4) are outside the script**
— open the evidence lines and read them yourself.

## 1. Misquoting a cited ADR

At write time, open the cited ADR and confirm that the number exists and that **what you cite is actually written in that ADR**.
ADR numbers cited from memory are wrong at a high rate.

- Case: CA `0ce5430` (2026-08-24) — the Review-when addendum to ADR-0069 was sent back by adr-reviewer.
  Removed the misquote of ADR-0072 and the misreference to 0044, and restored the cited claim's strength to the original text

## 2. Where surviving scope is placed (partial supersede)

In the forward half (the new ADR), write only "what it retires". **What survives** is written
only in the backward half (the old ADR) — when later partial supersedes stack up, survival statements
on the forward side become false as of their date.

- Case: CA `423c732` (2026-08-15) — surviving scope was wrong in 4 of 5 new ADRs.
  The "Which half states which scope." section of CA `docs/adr/README.md` is a product of this finding

## 3. Provenance of coined terms

Do not write a term you coined as if the cited source uses it. For a term absent from the source,
either state explicitly that it is "this ADR's name for it" or write it with the source's actual wording.

- Case: CA `008ac94` (2026-08-15) — "Step 0" was coined in ADR-0060 and appears nowhere in ADR-0026.
  Rewritten in terms of the actual thing (the distill.py half of Phase 2)

## 4. Grounds for judging full vs partial supersede

Judge whether a supersede is full or partial by **what exists in the code**, not by impression. If the mechanism the old ADR
presupposes no longer remains in src/, it is full.

- Case: CA `008ac94` (2026-08-15) — ADR-0027 was written as partial, but corrected to full on the grounds that
  NOISE_THRESHOLD / re_classify etc. no longer exist. As a knock-on, 2 HIGH findings in the edge definitions were fixed at the same time

## 5. No references to gitignored paths

Do not reference gitignored paths such as `.notes/` from an ADR body. If evidence is needed, promote the artifact
to `docs/evidence/` or rewrite the wording to be path-independent.

- Case: CA `25b88f9` (2026-08-15) — a mechanical scan found 20 occurrences; closed in one pass by promoting 3 to evidence
  and rewriting 7 occurrences

## 6. Sources and denominators of numbers

The canonical source is adr-reviewer criterion §6 (Numeric Claims). Only the write-time essentials: attach a command / log /
measurement date to each number, and give the denominator for percentages ("54% (45/83)"). Mark numbers that drift (file counts etc.)
explicitly as snapshots with a measurement date.

## 7. What is held fixed in a count condition (when writing Review-when)

For expiry conditions of the form "N times in a row" or "M occurrences in 30 days", name **what must be held fixed for counts to be comparable** (the section being checked,
the judge, the slot). If you cannot name it, it is unmeasurable — rewrite it as an event condition or an author judgment.

- Case: harness ADR-0046 (2026-08-22) — both the target and the judge were replaced while the gate had 0 observations,
  making the count meaningless. Promoted to adr-reviewer criterion §1

## 8. Scope mismatch between the record and the actual diff

Check the changes written in the Decision against the diff going into the same commit, in both directions. The most frequent form is
a change the ADR does not mention mixed into the same diff (unrelated work swept in). At write time, look at
`diff_scope.changed_not_mentioned` from `adr_review_evidence.py --diff worktree` and either add it to the Decision or split the commit.

- Case: harness ADR-0057 (2026-08-28) — a SKILL.md change the ADR did not mention was mixed into the same diff.
  ADR-0066 (2026-09-14) — Decision 5 said "rewrite consumers in 5 places" while the actual change touched 6 files.
  Recurred in 8 of 24 reports over 2026-08-26 to 09-15

## 9. Reversal cost and the second place of record (Consequences)

For a Decision that includes deletion or retirement, put the reversal cost (assets outside git cannot be restored) in Consequences; for a Decision whose measured values
are also written in SKILL.md etc., put the "second place of record" and how its drift is handled in Consequences.

- Case: harness ADR-0065 (2026-09-14) — the backup location for deleting 14 memory files was the session scratchpad,
  so the baseline could not be reproduced after the session ended. ADR-0056 (2026-08-28) — the measurement of 82 repo / 104 config
  appeared in 3 places (the ADR, SKILL.md, and the index row) with no canonical source designated. Recurred in 6 / 7 of 24 reports respectively

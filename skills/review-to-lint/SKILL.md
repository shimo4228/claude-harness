---
name: review-to-lint
description: "A procedure for extracting the mechanically decidable items from an existing reviewer's (agent / review skill) checklist, or from past sessions' reviewer history, into a deterministic script, thinning the reviewer down to semantic checks only. Use via /review-to-lint when the author says \"turn this reviewer into a lint\", \"absorb the review into a lint\", \"move the mechanical checks into a script\", \"find what in the history can be linted\", or when a reviewer's findings show repeated mechanical items. NOT for — creating a new reviewer (→ skill-creator), changing the semantic criteria themselves (each reviewer owns them), designing a judge (→ llm-as-judge), re-extracting reviewers that already have an evidence script (done for readme-writer / adr-writer)."
user-invocable: true
origin: shimo4228
---

# Review → Lint absorption

A reviewer's checklist mixes in items that a script counts more accurately and cheaply than an LLM does.
This skill draws that boundary, moves the mechanical side down into a script, and focuses the reviewer's attention
on semantic checks. Prior examples: `readme_evidence.py` (readme-writer), `adr_lint.py` (adr-writer,
ADR-0051). The division-of-labor principle is "existence = code, content = LLM" (introduced by ADR-0021, applied to ADRs by ADR-0044) and
feedback: deterministic_semantic_layering (script measures + LLM interprets).

## 0. Entry — checklist-first vs history-first

If the target reviewer is already decided, go straight to §1. If you are deciding "which reviewer / which convention should be linted,"
mine the reviewers' history. A checklist-first inventory surfaces only the items a reviewer **holds in writing**,
so it misses findings that actually recur (measured 2026-08-29: RFC-0005's
12 candidates covered only the document / skill-asset layer and missed 3 classes targeting `hooks/*.sh`
= #13–#15 of the same RFC).

**Build no mechanism** — create neither an extraction script nor a collection hook (ADR-0055 Decision 5, "build no collection
mechanism"). One manual investigation is enough. If a second one is requested, propose a script at that time, including a supersede
of ADR-0055.

Non-obvious points about the corpus and extraction:

- Reviewer reports are at `~/.claude/projects/<project>/<session-id>/subagents/agent-*.jsonl`.
  **Not next to the parent transcript**
- Identify the reviewer type from the subagent's first user message. There is no `agentType` field, and
  it is not linked to the parent transcript by id (match the final assistant text against the parent's tool_result)
- The built-in `/code-review` signature is `` `medium effort → 3+5 angles × 6 candidates …` ``
- Take the final assistant **message**. `jq | tail -1` takes only the final **line**
  (each file is 100–450KB, so the whole thing cannot be read)
- The structured tool_use of `ReportFindings` is not saved. Extraction becomes natural-language parsing

**Fix the thresholds before mining.** Class granularity is a free variable; cut finely enough and you can always produce a
"class not in the ledger." Defaults: the same class **3 or more times across 2 or more sessions**, **at least 1 adoption**,
and **classes coming only from retired reviewers do not count** (that reviewer no longer runs, so there is no demand).

There are two destinations. **Repeated adoption → lint candidate** (go to §1); **repeated rejection → retirement candidate** (a hollowed-out convention,
or a misaligned reviewer remit. Linting it would make the false positives permanent).

## 1. Inventory and 3-way classification (the core of this skill)

Classify the target reviewer's checklist one item at a time. Criteria:

| Class | Input to the judgment | Destination |
|---|---|---|
| **deterministic** | structure, format, existence, consistency (presence of sections, enums, date format, link resolution, index drift, naming conventions, consistency of cross-references) | script |
| **semantic** | intent, fidelity, two-sidedness, validity (post-hoc justification, straw men, one-sided Consequences, correspondence between claims and evidence) | stays with the reviewer |
| **hybrid** | the script counts, the LLM interprets (the fixed target of a count condition, the denominator of a figure, the distribution of term occurrences) | the script outputs evidence, the reviewer interprets it |

When unsure, lean to semantic — a wrongly mechanized item lets false negatives through wearing the face of "checked."

## 2. search-first cross-check

Before writing, look for external lint tools and existing evidence scripts in the harness (`skills/*/scripts/`).
If an existing one can check the target corpus **without migration**, do not write one. If migration is needed, compare the migration cost with
the cost of building your own, and record the reason for rejection in an ADR (precedent: the adrkit comparison, ADR-0051).

## 3. Script design

- Location: under the writer skill for that domain, `skills/<owner>/scripts/` (a single source of truth that works
  cross-repo). A uv sub-project (pyproject + tests, auto-discovered by verify.sh full)
- The default is **evidence mode**: output JSON, make no judgment, exit 0. "evidence, not a verdict" —
  the judgment belongs to a fresh-context judge / reviewer. Add `--gate` only when blocking is needed
- **Measure the exemption boundary first**: run it against every item in the existing corpus and count violations before deciding on prefix checks,
  number/date boundaries, and automatic adaptation to repo-local conventions (reading expected values from the canonical doc).
  A lint that turns the gate red on day one is a design error in the exemption boundary
- Leave the measured grounds for each detection pattern (how many hits in which repo) in a comment

## 4. Thinning the reviewer

- Delete the mechanical items from the checklist and wire in a Step 0 at the top: "run the script → copy the JSON's
  deviations into findings → do not recount by eye → put attention on the semantic checks"
- Keep the instruction to read the target repo's local conventions (the canonical template doc) — write the reviewer on the assumption that
  conventions differ per corpus
- **Examples** of frequent findings go to a catalog in `references/` with dates and commit references (wired into the writer skill's
  prevention at writing time). The reviewer remains the source of truth for the **criteria** — do not duplicate examples and criteria

## 5. Execution coordinates

Decide the location on 2 axes:

- **Tax rate** — the fraction of commits for which the check is meaningful. If low, a step in the writer skill / reviewer;
  if high, the repo's `verify.sh`
- **Off-the-shelf fit** — if a config line for an off-the-shelf tool is enough, `verify.sh` (the landing shape of ADR-0056).
  For a self-written script, the skill-step side is the default

The default is the skill-step side — always-on wiring into a commit hook / verify.sh taxes every commit,
including commits that do not touch the target (author's decision 2026-08-26, ADR-0051 Decision 2).

**Exception: targets with no canonical writer skill.** Executable assets such as `hooks/*.sh` have no writer skill
equivalent to adr-writer / readme-writer, so the coordinate "skill step"
does not exist in the first place. In this case `verify.sh` becomes the default (found in the 2026-08-29 history mining —
ADR-0051 Decision 2 did not anticipate this case).

If hollowing-out is observed, revisit the wiring on the commit surface. Hold no aggregation, viewer, or grader agent
(for the same reason as skill-creator's "what it does not hold").

## 6. Recording

Record in an ADR: the code/LLM boundary (which items go where), overlaps with existing checks and the grounds for why they will not
drift, the measured values of the exemption boundary, and the reasons for rejection in search-first.

## Application candidates

The candidate ledger's source of truth is [RFC-0005](../../rfcs/0005-review-to-lint-rollout-ledger.md)
(12 candidates, demand-driven firing conditions, won't-do decisions. 2026-08-26 sweep). Carry them out one at a time in
separate sessions; decide priority by the demand firing conditions, not by room for mechanization.

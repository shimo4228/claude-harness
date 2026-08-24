---
name: learn-eval
description: "Extract a reusable pattern from the current session, judge it Save / Improve then Save / Absorb / Drop against a grounding checklist, and route every Save to a destination something actually reaches — absorbed into an existing skill / rule / doc section, or promoted to a real skill via skill-creator. Use when the user says 「今回の学びを残して」「learn-eval して」 or /learn-eval. There is no notes parking lot: if nothing would route to it, the verdict is Drop. NOT for mining past sessions (session-judgment-mining), auditing skills (skill-stocktake), or distilling rules (rules-distill)."
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
user-invocable: true
origin: shimo4228
---

# /learn-eval - Extract, Evaluate, then Save

Extends the full /learn flow with a pre-save quality evaluation and a save-location decision.

## What to Extract

Look for:

1. **Error Resolution Patterns** — root cause + fix + reusability
2. **Debugging Techniques** — non-obvious steps, tool combinations
3. **Workarounds** — library quirks, API limitations, version-specific fixes
4. **Project-Specific Patterns** — conventions, architecture decisions, integration patterns

## Process

1. Review the session for extractable patterns
2. Identify the most valuable/reusable insight

3. **Determine the destination — there is no parking lot.**

   `learned/` was retired on 2026-08-23 (ADR-0047). Every Save must land somewhere that
   something actually routes to, so pick one of exactly two:

   - **Absorb into an existing asset** — the pattern belongs inside a skill, rule, or
     `hooks/README.md` section that already owns the topic. Name the file and the section.
     This is the default: an addition to a reachable asset beats a new file.
   - **Promote to a skill** — the pattern has its own independent trigger (a user request
     that no installed skill answers). Run skill: **skill-creator** (required by
     `rules/common/skills.md` before writing any skill).

   If neither fits, the verdict is **Drop**, not "park it somewhere for now". A note that
   nothing points at is reachable only by grep, and grep requires already knowing the
   content exists — measured over 74 days, the retired `learned/` directory was read
   during real work 12 times across 8 notes, while the audits that judged whether to keep
   it accounted for 161 of its 184 reads.

   Global vs project placement (once a destination type is chosen): 正本は
   [`docs/adr/0025-global-vs-project-asset-placement.md`](../../docs/adr/0025-global-vs-project-asset-placement.md)。

4. Draft the skill file using this format:

```markdown
---
name: pattern-name
description: "Description in 130 characters or less"
user-invocable: false
origin: auto-extracted
---

# [Descriptive Pattern Name]

**Extracted:** [Date]
**Context:** [Brief description of when this applies]

## Problem
[What problem this solves - be specific]

## Solution
[The pattern/technique/workaround - with code examples]

## When to Use
[Trigger conditions]
```

5. **Quality gate — checklist + holistic verdict**

   #### 5a. Mandatory checklist (verify by actually reading the files)

   Run **all** of the following before evaluating the draft:

   - [ ] Grepped `~/.claude/skills/` for keywords and checked for content overlap
   - [ ] Checked for overlap with MEMORY.md (project + global)
   - [ ] Considered appending to an existing skill instead (see knowledge-placement-decision)
   - [ ] Confirmed the pattern is reusable, not a one-off fix
   - [ ] Checked the pattern against the **session's observational record** (actual tool output, errors, user corrections). Is it grounded in "what actually happened" rather than your own summary or paraphrase?

   Then, **generate and answer 3–5 draft-specific atomic yes/no questions**.
   The fixed checklist covers harness-invariant checks (duplication, reusability) but
   does not test the draft's own claims (what it states under Problem / Solution /
   When to Use), so this step fills that gap:

   - **Atomicity**: each question tests exactly one verifiable claim
   - **Refutation-oriented**: phrase questions to seek disconfirmation, not to affirm
     the draft as written. Examples: "Does the code example run as-is in the stated
     environment?" "Is the trigger condition observable from the prompt text of a
     future session?" "Which line of the session's observational record does the
     Solution correspond to?"
   - **No aggregation**: answers are Yes/No + one line of evidence. Never convert them
     into a numeric score (e.g. a satisfaction ratio). The only consumed output is the
     verdict in 5b; binary answers serve strictly as its evidence

   #### 5b. Holistic verdict

   Weigh the checklist results, the binary answers, and the draft together, then choose
   exactly **one** of the following. **Always enumerate the No-answered questions as
   grounds for the verdict** (hidden Nos breed verdict drift):

   | Verdict | Meaning | Next action |
   |---------|---------|---------------|
   | **Save** | Unique, concrete, well-scoped | Go to Step 6 |
   | **Improve then Save** | Valuable but needs fixes | No questions = improvement items → fix → re-judge with the same questions (once only) |
   | **Absorb into [X]** | Should be appended to an existing skill | Present the target and the content to add → go to Step 6 |
   | **Drop** | Trivial, redundant, or abstract | Explain why and stop |

   **Guiding dimensions** (reference points for judgment, not a scoring rubric):

   - **Concreteness / actionability**: has code examples/commands, immediately usable
   - **Scope fit**: name, trigger, and content align; focused on a single pattern
   - **Uniqueness**: given the checklist results, provides value existing knowledge cannot
   - **Reusability**: will realistically be triggered in future sessions
   - **Grounding**: is the source an observational record (what actually happened) or
     your own interpretation/summary? Self-evaluation-only loops drift (your paraphrase
     gets re-fixed as fact), so lean toward Drop for extractions not grounded in
     observation. **If a grounding question is No, lean Drop even when everything else
     is Yes** (never let averaging dilute a dominant No)

   **Improve then Save improvement list**: the No-answered questions become the
   improvement items as-is. For each No, write one line on what to change to make it a
   Yes; after fixing, re-judge with the **same question set** (once only — do not
   regenerate the questions: if the bar moves, you cannot tell whether the fix worked
   or the bar loosened).

6. **Per-verdict confirmation flow (one at a time, `[y/n/skip]`)**

   Even when multiple patterns were extracted from the session, confirm them
   **one at a time — never ask for batch approval** (follows config-gc's confirm-each
   design; a bulk "save them all? [y/n]" is banned).
   For each candidate, present the evidence first (checklist results + verdict
   rationale), then ask `[y/n/skip]`.
   The user can stop at any point. `n` = discard, `skip` = defer for now (leave a
   one-line reason):

   - **Save**: present the save path + checklist results + one-line verdict rationale + the full draft → save after `[y/n/skip]` confirmation
   - **Absorb into [X]**: present the target path + the content to add (as a diff) + checklist results + verdict rationale → append after `[y/n/skip]` confirmation
   - **Drop**: show the checklist results + reason only (no confirmation needed; stop)

7. Save to the destination chosen in Step 3

   - **Absorb**: edit the named asset in place and show the diff. Do not create a file.
   - **Promote**: hand the draft to skill: **skill-creator** — it fixes the intent packet,
     draws the boundary against neighbouring skills, structures it as
     `~/.claude/skills/<name>/SKILL.md`, and passes it through a fresh-context draft gate
     (learn-eval = extraction and Save/Drop judgment / skill-creator = shape, boundary and
     gate — a deliberate role split).

8. **Reachability check (after a Save only)**

   State in one line what will route to the saved content in a future session: the section
   it now lives in, or the skill description that will select it. **If the honest answer is
   "nothing — someone would have to grep for it", the Save was wrong**; go back to Step 3
   and either absorb it into a reachable asset or Drop it.

## Output Format for Step 5

```
### Checklist
- [x] skills/ grep: no overlap (or overlap found → details)
- [x] MEMORY.md: no overlap (or overlap found → details)
- [x] Append-to-existing considered: new file appropriate (or should append to [X])
- [x] Reusability: confirmed (or one-off → Drop)

### Draft-specific questions
- [Yes] Q1: ... — one-line evidence
- [No]  Q2: ... — one-line evidence → (on Improve: one-line fix plan)

### Verdict: Save / Improve then Save / Absorb into [X] / Drop

**Rationale:** (1–2 sentences explaining the verdict; always mention any No questions)
```

## Notes

- Don't extract trivial fixes (typos, simple syntax errors)
- Don't extract one-time issues (specific API outages, etc.)
- Focus on patterns that will save time in future sessions
- Keep skills focused — one pattern per skill
- On an Absorb verdict, do not create a new file — append to the existing skill instead

## References

The generic design canon for this evaluation style (binary checks as evidence →
holistic named verdict, no aggregation) is the `llm-as-judge` skill; Step 5 is its
N=1 implementation.

Design rationale for Step 5's two-layer design (binary question decomposition → holistic verdict):

- BinEval — "Ask, Don't Judge: Binary Questions for Interpretable LLM Evaluation and Self-Improvement" ([arXiv:2606.27226](https://arxiv.org/abs/2606.27226)). A framework that decomposes evaluation criteria into atomic yes/no questions and wires failed questions directly into improvement feedback. The dynamic generation of draft-specific questions and the "No questions = improvement items" path are ported from here
- The same checklist-style evaluation research line: CheckEval (arXiv:2403.18771), TICK (arXiv:2410.03608), FActScore (arXiv:2305.14251), UniEval (arXiv:2210.07197)
- The decision **not** to adopt numeric scores (satisfaction ratios) also follows BinEval's own limitations: on subjective, holistic quality dimensions, over-decomposition degrades correlation with human judgment, and the proportion of affirmed questions does not map linearly to quality. For an N=1 draft evaluation the only consumed output is the verdict; binary answers serve strictly as its evidence

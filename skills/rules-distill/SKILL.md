---
name: rules-distill
description: "Distill principles from the installed skills into the always-loaded rules layer."
license: MIT
user-invocable: true
origin: shimo4228
disable-model-invocation: true
---

# rules-distill — promote environment-specific facts to rules

Scan installed skills, find principles that belong in the **always-loaded rules layer**, and distill
them into rules — appending to, revising, or creating rule files. The skill produces
candidates and verdicts; it **never edits rules without your approval**.

**Roots.** `<harness>` below is the harness this audit covers: `~/.claude` by default, or a repository's `.claude/` when skill `harness-stocktake` runs in project mode (its Roots section maps the paths, names the evidence that is `n/a` there, and says which convention checks apply). The ledger `<ledger>` belongs to that harness: `${CLAUDE_SKILL_DIR}/results.json` when this skill's directory is inside `<harness>` (the harness carries its own copy of the skill), else `<harness>/stocktake/rules-distill.json` (an installed plugin, or project mode). Either way it is committed with the harness's other changes on the apply branch.

## When to Use

- Periodic rules maintenance (monthly, or after installing new skills)
- After a `skill-stocktake` reveals patterns that should be rules
- When rules feel incomplete relative to the skills in use

## Phase 1 — Inventory (Glob, exhaustive)

Enumerate with Glob (no script):

- Skills: `<harness>/skills/*/SKILL.md`
- Rules: read every `<harness>/rules/**/*.md` in full — the corpus is small, so no grep pre-filter is needed

> Glob targets only skill definition files, so dependency markdown under `.venv` /
> `.pytest_cache` is excluded structurally.

Present the counts (skills scanned, rule files, headings) before analysis.

## Phase 2 — Cross-read & Verdict (inline, holistic)

Read every skill body and every rule into one context and analyze them together —
extraction and matching are a single pass. Seeing all skills at once is what makes the
recurrence count exact and the "not already in rules" test reliable.

**A principle is a candidate only if ALL of these hold:**

1. **Environment-specific** — a fact, a wiring, or a trap particular to *this* machine,
   harness, or set of accounts. A general engineering principle is not a candidate no
   matter how many skills repeat it.
2. **Substrate does not already do it** — if the current model handles it natively, a
   written rule does not add behaviour; it freezes an older default and competes with
   the newer one.
3. **Not a procedure** — steps and workflows belong in a skill. Residency is for facts
   and wiring, which have to be true before any particular task starts.
4. **Actionable behavior change** — expressible as "do X" / "don't do Y", not "X is important"
5. **Clear violation risk** — what goes wrong if ignored, in one sentence
6. **Not already in rules** — check the full rules text, including the same idea in different words

> Tests 1–3 are the admission criterion for a resident rule ("facts, wiring, and traps specific to this environment.
> Procedures for thinking and work belong to skills, checks that need a firing time belong to hooks, and general judgment belongs to the substrate").
> A harness that states its own criterion (in `rules/README.md` or CLAUDE.md) is judged by that one.
>
> **Recurrence is evidence, not a gate** — report the count, do not filter on it.
> Frequency and residency-worthiness diverge often enough to matter: a general principle
> repeated in ten skills fails tests 1–3 (substrate has it — removing exactly that class once cut a
> harness's rule residency by 60%), while a one-off environment trap passes them.

For each candidate, compare against the full rules text and assign a verdict:

| Verdict | Meaning | Present to user |
|---------|---------|-----------------|
| **Append** | Add to an existing section of an existing rule file | Target + draft |
| **Revise** | Existing rule content is inaccurate/insufficient | Target + reason + before/after |
| **New Section** | Add a new section to an existing rule file | Target + draft |
| **New File** | Create a new rule file | Filename + full draft |
| **Already Covered** | Sufficiently covered (even if worded differently) | Reason (1 line) |
| **Too Specific** | Should stay at the skill level | Link to the relevant skill |

Exclude: principles already in rules, language/framework-specific knowledge (belongs
in language-specific rules or skills), and code examples / commands (belong in skills).

### Verdict quality

Each verdict must be self-contained — target, evidence, and rationale on its own.
Draft text links back to the detailed How with the pointer form the rules corpus uses:
``skill: `name` ``.

```
# Bad
Append to security.md: Add LLM security principle
```

Good example (the evidence is why it passes tests 1–3, not an occurrence count. Cite references **by section heading** —
line numbers shift every time the referenced file grows):

```
# Good
New entry under the stop-and-report section of rules/common/boundary.md:
"If rate limits fire repeatedly during bulk writes to an external platform, treat them as a
policy signal, not a transient error, and stop the burst. Do not push through with backoff; report to a human."

Test 1 (environment-specific): an event that actually happened on this author's account. On 2026-07-16,
  continuing with backoff resulted in an indefinite account block + deletion of all created content. Not general
  HTTP 429 etiquette, but a stop condition specific to this operation
Test 2 (not substrate-native): the substrate's default retries 429 as transient.
  The rule is needed to override that default
Test 3 (not a procedure): not a procedure but a declaration of fact: "repeated rate limits = policy signal"
Violation risk: pushing through loses the whole account (proven, unrecoverable)
Recurrence: 1 skill (evidence, not a gate)
```

Note that it **passes even with a Recurrence of 1**.

## Phase 3 — Report and apply

Turn every candidate into an item (source `distill`) of the report contract in skill:
`harness-stocktake` and hand them to it: one report, one approval from the author, application
on a task branch, a completion report, an ff-only merge. Called alone, this skill runs that
contract's Phases 2–5 with its own items. Each item carries the principle and confidence in
`reason`, the evidence and violation risk in `evidence`, and the exact draft text with its target
location in `change`; the author can rewrite the draft in the item's note.

**A rule changes only through an item the author approved in the report.** This is the one hard
gate — rules load every session, so a bad rule has outsized blast radius. An item whose note
leaves the wording open goes to the completion report as pending, not into the rule.

Where skill `harness-stocktake` is not installed, show the same items as one table
(`# | Principle | Verdict | Target | Confidence`, each with its draft text), take one approval with
the author's overrides and edits, then apply. Skipped candidates go to the ledger with
`status: skipped`.

> Paths below start at `${CLAUDE_SKILL_DIR}`, the directory holding this SKILL.md; an agent that does not substitute the variable reads it as that directory.

Then update the ledger `<ledger>` inline (Read → merge → Write):

```json
{
  "distilled_at": "2026-03-18T10:30:42Z",
  "candidates": {
    "llm-output-trust-boundary": {
      "principle": "Treat LLM output as untrusted when stored or re-injected",
      "verdict": "Append",
      "target": "rules/common/security.md",
      "evidence": ["llm-memory-trust-boundary", "llm-social-agent-anti-pattern"],
      "status": "applied"
    }
  }
}
```

`distilled_at` is real UTC (`date -u +%Y-%m-%dT%H:%M:%SZ`); candidate IDs are
kebab-case derived from the principle.

## Related

- `skill-stocktake` — audits skill *quality*; rules-distill promotes recurring *principles* to rules. Run stocktake first, then distill what survives.
- `rules-stocktake` — audits the rules this skill produces (residency cost, staleness, absorption) and demotes back what stopped earning its always-loaded slot; the inverse direction over the same boundary.
- `learn-eval` — extracts per-session patterns into skills/memory; rules-distill later promotes the cross-cutting ones to rules.

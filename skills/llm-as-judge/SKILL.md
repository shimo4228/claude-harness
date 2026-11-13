---
name: llm-as-judge
description: "Design pattern for LLM-as-judge evaluators: binary checks as evidence, one named verdict."
license: MIT
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
origin: shimo4228
disable-model-invocation: true
---

# LLM-as-Judge — Checks as Evidence, Holistic Verdict, No Scores

Core rule in one line:

> **Collect evidence with binary Yes/No checks, let the LLM issue one named
> holistic verdict, and never aggregate the answers into a score.**

The principles behind this form are owned by skill `eval-foundations`.

## The three principles

| Principle | Do | Don't |
|---|---|---|
| ① Binary checks | Decompose criteria into Yes/No questions with 1-line evidence each | "Rate specificity 1–5" |
| ② Named holistic verdict | Pick exactly one verdict from a fixed enum, judging the whole | "Total 12 points → pass" |
| ③ No aggregation | Enumerate the No answers as the verdict's rationale | Use the Yes-ratio as a quality metric |

### ① Binary checks

Ask "is there a runnable command example? Yes/No", not "how specific is this?".
Good binary questions are **verifiable** (the text settles them black-or-white)
and **evidentiary** (a No names what is missing). Require one line of evidence
per answer — a file read, a path check, a measured command output.

### ② Named holistic verdict

Holistic judgment — one conclusion from the whole, without passing through
per-dimension numbers — is the LLM's strength. Design the verdict enum so each
value maps **1:1 to a next action**, e.g.:

- Library audit: `Keep / Improve / Update / Retire / Merge into [X]`
- Save-or-drop gate: `Save / Improve then Save / Absorb into [X] / Drop`

Prefer this over bare `accept / reject`: downstream code can dispatch on the
enum directly. Verdicts that name a target (`Merge into [X]`, `Absorb into [X]`)
structurally forbid vague judgments like "overlaps with something".

### ③ No aggregation

Two rules replace the score:

1. **Enumerate every No** in the verdict rationale (hidden Nos breed verdict
   drift between runs).
2. **A dominant No decides alone.** If a fatal-class question is No (nonexistent
   reference, ungrounded claim), lean to the failing verdict even when
   everything else is Yes. Never let averaging dilute it.

## Verdict pressure-test

Before finalizing a non-passing draft verdict, make the judge attack it:

1. Generate **atomic** Yes/No questions that try to **refute** the draft
   verdict (e.g. draft = "Update: CLI flag retired" → "does the flag still
   appear in current `--help` output? measure it").
2. Answer each with one line of evidence.
3. Refutation holds → fall back toward the passing verdict.
4. Defect confirmed → the binary-screen No answers become the improvement list
   as-is.

Discipline: one question tests exactly one verifiable claim (atomicity);
questions seek disconfirmation, not affirmation. After a fix, **re-judge with
the same question set, once only** — regenerating questions makes it impossible
to tell whether the fix worked or the bar moved.

## Four stages for a single-item judgment (provisional)

This section is provisional: what each stage is shown is a decision expected to be
replaced, and skill `eval-foundations` indexes it in its `provisional.md`.

1. Have the judge who carries the last stage write the overall verdict and its
   reason without seeing the criterion results, and save it.
2. Raise a separate subagent per criterion, each shown that one criterion only.
   It returns binary checks with the location of the evidence, and gives no score.
3. Have a judge in a fresh context issue the final verdict, shown the work and the
   evidence from stage 2 (stage 1 is not shown).
4. Compare stage 1 and stage 3 in code and record where they disagree. When stage 3
   reaches a verdict against the criterion evidence, have it name, in one line,
   the fact the criteria did not cover. Record an overturn that cannot name such a
   fact as a suspected over-overturn.

How the stages join the rest of this skill:

- Check whatever code can check before stage 1 (Existence before judgment, below),
  and hand the results to stage 3 as fact lines.
- Stages 1 and 3 are the same judge role in two separate contexts: stage 3 starts
  fresh and is not shown what stage 1 wrote.
- The refutation questions (Verdict pressure-test) run inside stage 3, whatever its
  draft verdict (a single item gets them unconditionally; see the table below).
- **A dominant No holds through stage 3.** When the evidence carries one, stage 3
  issues the failing verdict. Stage 3 may name a fact and reach a verdict against
  the evidence only on criteria other than a dominant No.
- The skill that uses the four stages defines its dominant No in a form whose fit
  can be checked against the artifact itself.
- The using skill's orchestrator does the stage 4 comparison in code and writes it
  to its own record.

## Scale the machinery, not the principles

| | Single-draft gate (N=1) | Library-scale audit (tens of items) |
|---|---|---|
| Procedure | Two stages, or the four stages (above) when the item is worth a subagent per criterion | Two stages: binary screen → refutation questions |
| Pressure-test questions | Unconditional | Non-passing candidates only |
| Rationale | Cost is negligible | Generating for every item is mostly waste |

The four stages raise a subagent per criterion plus two for every item judged,
which pays for one item and not for tens.

## Don't let deterministic checks ride on judgment

The judge's attention is a diluting resource.

Design consequences:

- **Existence before judgment.** Deterministically checkable claims (paths
  exist, flags current, URLs live) get code-owned, unconditional pre-checks —
  `ls`, `--help`, fetch — before the LLM sees the item. Never let a judge issue
  a passing verdict on a file that is not there.
- **Conditional verification triggers degrade.** "Verify if it looks stale" is
  banned phrasing: the trigger itself is a diluting judgment, and in a loaded
  context it decays to "never verify".
- **Narrow, dense contexts for per-item judgment; light sweeps for set-level
  judgment.** Split by the property being checked, not by context length.
- Before handing anything to the judge, ask: *is this actually judgment, or is
  it `ls`?*

## Judge prompt template

```markdown
You are a quality evaluator for {artifact type}. Evaluate as follows.

## Step 1: Binary checks (all mandatory)
Answer each with Yes/No plus one line of evidence.
- Q1: {verifiable question, e.g. is there a runnable code example?}
- Q2: {verifiable question}
- …

## Step 2: Item-specific refutation questions (only if the draft verdict leans failing)
Pick one draft verdict, generate Yes/No questions that try to refute it,
and answer each with one line of evidence.

## Step 3: Verdict
Choose exactly one. Output no scores or points.
- {verdict_1}: {meaning and next action}
- {verdict_2}: {meaning and next action}
- {verdict_3}: {meaning and next action}

Enumerate every No-answered question in the rationale.
If any dominant No ({domain-specific fatal condition}) is present, choose
{failing verdict} even when everything else is Yes.

## Output format
Return JSON matching the schema below. Where the runtime supports structured outputs,
hand it the schema there rather than asking for JSON in prose.
```

Output schema:

```json
{
  "verdict": "Improve",
  "evidence": [
    { "question": "Runnable code example?", "answer": "No", "detail": "steps are prose-only, zero commands" },
    { "question": "Referenced paths exist?", "answer": "Yes", "detail": "ls confirmed all 3 paths" }
  ],
  "pressure_test": [
    { "question": "Are prose-only steps reproducible as-is?", "answer": "No", "detail": "step 3's arguments are ambiguous" }
  ],
  "reason": "Dominant No on actionability; adding a worked example to step 3 would reach the passing bar"
}
```

`verdict` is an enum — downstream code dispatches on it directly; the No items
in `evidence` are the improvement list handed to the next stage.

## Related

- `eval-foundations` — the principles this skill's judge form rests on.
- **Code-LLM layering** ([AKC ADR-0008](https://github.com/shimo4228/agent-knowledge-cycle/blob/main/docs/decision-history/0008-code-and-llm-collaboration.md))
  — the architecture-level "LLM judge + Code enforce" pattern (judgment never
  mutates state directly); this skill designs the judge's inside. Not an
  installed skill: it lives in the AKC repo (and as a public skill repo that
  the author's publish step, `harness-sync`, publishes to), so cite the ADR rather than a `skills/` path.
- `skill-stocktake` — worked implementation at library scale (binary screen →
  pressure-test → holistic verdict, deterministic pre-pass, overlap probe).
- `learn-eval` — worked implementation at N=1 (unconditional dynamic questions,
  same-question-set re-judge).
- `skill-writer` §4 — creation-time draft gate: one fresh subagent without Bash,
  named verdict Publishable / Fix / Drop, same-question re-judge once.

## References

- BinEval — "Ask, Don't Judge: Binary Questions for Interpretable LLM Evaluation
  and Self-Improvement" ([arXiv:2606.27226](https://arxiv.org/abs/2606.27226)).
  Atomic yes/no decomposition with failed questions wired into improvement
  feedback; the dynamic refutation questions and "No answers = improvement
  items" path follow it. Its own limitations motivate principle ③: decomposition
  is less reliable on subjective, holistic quality dimensions, and the fraction
  of satisfied questions need not map linearly to quality.
- Same checklist-evaluation lineage: CheckEval
  ([arXiv:2403.18771](https://arxiv.org/abs/2403.18771)), TICK
  ([arXiv:2410.03608](https://arxiv.org/abs/2410.03608)), FActScore
  (arXiv:2305.14251), UniEval (arXiv:2210.07197).

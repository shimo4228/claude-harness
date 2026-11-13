---
name: eval-foundations
description: "The principles behind every LLM judgment and eval, for designing or revising one."
license: MIT
origin: shimo4228
user-invocable: true
disable-model-invocation: true
---

# Eval Foundations — Principles Behind Every Judgment

Read this skill when you design a judgment or revise one: a judge, an eval, a review gate, a
reader loop. A run of an existing judgment needs only the skill that runs it; that skill holds
everything the run requires.

## The principles

1. **Reach the verdict by holistic judgment, not by summing rubric points.** A measure that
   becomes the target breaks down (Goodhart). Holistic judgment is what to aim for.

2. **Treat noise and bias separately.** Repeating the same judge reduces only the wobble of the
   moment (occasion noise). The judge's stable habits, and a shift that lands on every judge in the
   same direction, survive repetition.

3. **Mix judges by lineage rather than by number** (for example, Claude and Codex). Keep a
   disagreement between lineages as a split instead of averaging it. Habits that all lineages share
   still survive the mix; only outside feedback shows them.

4. **A judgment that guards the floor may be a panel; a judgment that picks the ceiling stays with
   one eye.** Guarding the floor means finding gaps or a dominant No. Picking the ceiling means
   choosing which one is best.

5. **The overall judgment and the per-criterion evaluation bleed into each other.** Decide in
   advance which one comes first and what each judge is shown.

6. **Keep the loop that fixes the work apart from the judgment that evaluates it.** A judgment
   inside the loop is learned by the loop and pushed on, so place a judgment that does not see the
   loop's results outside the loop.

7. **Use a wobble check only to learn how large the wobble is, and keep the verdict of the first
   run.** Attach the items that wobbled widely to the verdict.

8. **Fixing the procedure is itself a countermeasure to wobble.** Run every evaluation on the
   fixed procedure, rather than having the model reassemble the flow each time.

9. **Leave details that go stale when the model changes to the model at hand, rather than writing
   them into the skill** — counts, prompt wording, specific model names.

## The judge's context

The judge does not hold the writer's context. Judge within the writer's context only when acceptance
rests with another eye: a judge in a separate context, or the author.

## Who owns what

| What | Owner |
|---|---|
| The principles and the judge's-context rule above (why, and what to do in general) | this skill |
| The form of a judge: binary checks as evidence, one named verdict, no aggregation, the dominant No, refutation questions, code-checkable facts first, the four stages | skill `llm-as-judge` |
| A skill's own output and sequence: what it produces, in which order, who receives what | that skill |
| A reason measured in one domain (for example, how README readers behave across rounds) | that skill's `MAINTENANCE.md`, or the reference its judge reads every run |

A skill that runs a judge points to skill `llm-as-judge`, which points here. A skill with no judge
of its own (a reader loop, a loop design review, the author's own reading) points here directly.
Point to one owner per rule, by skill name, and keep only the instruction for its own run.

## What a skill fixes and what it leaves to the model

Fix the structure: the stages, who is shown what, the verdict vocabulary, the output shape. Write
how to choose a count or a model (for example, by how deeply a reader role reads) rather than the
count or the model itself. This holds for a skill's body, its presets, its references and an
agent's body.

Two things are written down as they are. A fixed prompt that a script hands to a reader, so answers
can be compared across rounds, is part of the instrument (principle 8); keep it in a preset or
reference, outside the skill's body. A script's default value and an agent's `model:` frontmatter
are wiring.

## Beside this file

- `provisional.md` — the decisions held provisionally, each with what would replace it and where to
  change it.
- `MAINTENANCE.md`, when present — the open questions this skill leaves undecided, and where the
  principles came from.

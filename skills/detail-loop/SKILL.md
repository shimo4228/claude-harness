---
name: detail-loop
description: "God is in the details: take a product whose skeleton is done and refine it unit by unit, freezing each fixed detail as a check, until a review round finds nothing new."
disable-model-invocation: true
user-invocable: true
origin: shimo4228
---

# detail-loop — refine a product unit by unit until review finds nothing new

Once the skeleton works, the difference left is in the details, and a model has more capacity to
spend on them than a person does. The product can be code (a CLI, a library, an API, an app), a web
page, or writing (an article, a README, documentation). This skill spends it: the product's details are split into units
(one rule of the craft each), every fixed detail becomes a check that reruns on every change, and
rounds continue until fresh reviewers find nothing new to adopt. The bar for every round is that
the product holds up to an expert of each field, not that it works.

It runs three skills in turn and owns the order, the interference between units, and when to stop.
They are user-invoked, so read each one's SKILL.md and follow it:

- `${CLAUDE_SKILL_DIR}/../detail-review/SKILL.md` — finds unfinished details and sorts them into the ledger
- `${CLAUDE_SKILL_DIR}/../detail-units/SKILL.md` — folds findings into units in `eval/units.yaml` (the format's owner)
- `${CLAUDE_SKILL_DIR}/../unit-eval/SKILL.md` — freezes one unit into a check and proves it can fail

## 0. Start

- Start when the product's direction is decided and its skeleton builds without errors. Earlier,
  details get redone when the structure moves.
- Confirm the version the product ships from (skill: `repair-discipline` when unclear), and work on
  a branch of it.
- When `eval/units.yaml` exists, run its frozen checks first. Red checks are the first work.
- Find out whether the author delegates the calls (「任せる」「全部あなたの推奨で」). Delegated, the
  author's touchpoints are the start and the finished product; follow Delegation below.
- For writing, whether the text gets across to a reader is skill: `persona-read-loop`'s job; this loop
  works the craft details.

## Delegation

When the author delegates, the loop decides the author calls, the `hybrid` ranges and the field list
itself and keeps going, so the author meets one finished product instead of a queue of questions.

- **Decide in the author's environment.** Measure and look where the author meets the product: the
  author's OS, runtime, terminal and editor for code, every browser engine the author uses for a page,
  the platform and device the author reads on for writing. Delegated calls that were reversed came from judging
  in a different engine than the author's, not from deciding without asking.
- **Decide, freeze, continue.** Record each decision in `decided_by` with the author's delegation
  words, and freeze it like any other unit.
- **The author's own words and publishing stay with the author.** Copy the author wrote or will sign,
  and any outward action (push, deploy, post), wait for the author even under delegation. In writing,
  the loop changes how the text is shown (markup, notation, terms as the author's glossary sets them,
  links, code blocks, figures); a change to the wording or a claim goes back to the author as a
  proposed edit (`author call`).
- **A later reversal by the author is one more ledger line**, worked like any adopted finding.

## 1. Round

1. Run skill: `detail-review` on the current build.
2. Run skill: `detail-units` with the adopted findings. On the first round the author approves the
   field list (⏸); later rounds add to it.
3. Work the units one at a time (step 2).
4. Start the next round. Without delegation, hand the author the round (step 5) first; the next
   round works the `machine` units while `hybrid` ranges and `author call` lines wait for the author's
   answers. Under delegation, those are already decided and the hand-off waits for the end.

## 2. One unit

1. Pick the next unit: units with failing instances first, then by how visible the failure is to a
   reader.
2. Change the cause named in the unit, and nothing else. Scope the change to the instances the finding
   names (its language, platform, command, page): a rule written for English titles reached Japanese
   lines, and a tie chosen for one font drew a double space in another; the next round found both as
   regressions.
3. Freeze an `open` unit with skill: `unit-eval`. Change a frozen unit's expectation only through
   skill: `detail-units`, Changing an expectation. `author` units are listed for the author.
4. Run every frozen check. A unit that moved without being touched has a relation: record it in
   `relations` (skill: `detail-units`).
5. Record the ledger lines and commits unit-eval writes (the fix, then the freeze).

## 3. Interference

When fixing one unit breaks another, look for a cause that satisfies both before trading one away
(two units often draw on one shared budget — width, time, memory, a sentence's length; on a web
page the Japanese size and a line break after a phrase both needed the column width, and lowering
the English size satisfied both). A fix often meets a third unit on the way, so run every frozen check
after each attempt; the second fix is where the third unit shows up. When none exists, the priority is the author's call: hand over both
units, the measured values, and the options.

## 4. Done and stuck

Done needs all three:

- every frozen check is green, no `machine` unit is `open`, and every `hybrid` unit with
  `decided_by` is `frozen` (the validator's counts)
- the latest review round found nothing new to adopt (no new unit and no new instance of an
  existing one), and the author has read that round's
  `not adopted` lines with their reasons (the loop decides adoption, so the author checks it)
- the author has answered the `hybrid` ranges and `author call` lines, and has read the
  `author-eye` units and the round's screenshots or captured output in the author's environment. Under delegation the
  loop has decided these; the author's read of the finished product closes it

All checks green alone is not done: the checks hold what was found, and only review finds more.

Stop and hand to the author when:

- the same two units have flipped each other twice (an interference with no shared fix)
- a unit's expectation could not be written as one check after two tries — propose making it an
  `author` unit; the author decides
- a unit's ledger lines show more expectation changes than detections — propose retiring the unit
- three review rounds have run in this session

## 5. Hand to the author

- The ledger lines added this session, with the `not adopted` lines and their reasons, and the commits
- The units by judge and status (the validator's counts), and what changed since the start
- The `hybrid` units waiting for a range, with the measured values
- The `author-eye` units and the screenshots or captured output to read
- Under delegation: the finished product, and the decisions made for the author that change how it
  looks, reads or behaves most, each with a screenshot or captured output in the author's environment
  and a one-line way back.
  The rest stay in the ledger
- The stop reason, in one line

---
name: unit-eval
description: "Freeze one detail unit from eval/units.yaml into a check on the product's output, and prove the check can fail."
disable-model-invocation: true
user-invocable: true
origin: shimo4228
---

# unit-eval — freeze one unit into a check that can fail

A detail that was fixed once stays fixed only while something checks it. This skill takes one
`open` unit (judge `machine` or `hybrid`) from the product's `eval/units.yaml` and makes it a check
in the product's runner: named by the unit's id, measured on the output, rerun on every change,
and proven able to turn red. The product can be code, a web page or writing; the steps are the same,
and `${CLAUDE_SKILL_DIR}/references/web.md` adds the measuring setup for a web product. The units
format and its validator belong to skill: `detail-units`.

## 1. Read the unit and confirm the version

Read the unit's four faces and its relations. Confirm the working tree is the version the product
ships from (skill: `detail-units` step 1); a check written against a stale version freezes details
that have already moved.

## 2. Write the check

Add one check to the product's runner under the unit's id. When the product has no runner yet,
create one next to `units.yaml` and wire it as one command (`npm run units`, `make units`, a pytest
marker): for code, tests that run the command or call the function; for a web product, browser
automation over the built pages; for writing, a script over the source text and the rendered post.

- **Measure the output** (the CLI's stdout, stderr and exit code, the function's return and errors,
  the generated file, the rendered page, the published text),
  as skill: `detail-units` step 3 defines the eval. The runner names the check by the unit's id as a
  string literal, which is how the validator finds it.
- **One check, one expectation, all instances.** Loop over the unit's `instances` (inputs,
  commands, pages and widths, sections) inside the check; report each failing instance with enough
  context to find it (the input, the variant, the first characters of the output).
- **Shape of the expectation** — pick the one that matches `expect`:

| expect says | check returns |
|---|---|
| a count ("0 error messages without a next step", "0 lines start with ー") | each violating instance |
| a measure with a tolerance ("startup under 300ms", "first letter within 0.5px of the edge") | each instance outside the tolerance, with the measured value |
| a ratio or range ("EN/JA 1.10–1.20", "sentences under 80 characters") | each instance outside the range, with the value |
| exact output decided by the author (help text, line breaks, a generated string) | a diff against a golden file the runner reads |

- **Pin the environment the measurement depends on.** Set what moves the output and is not the
  unit's cause (locale, time zone, terminal width, random seeds, clock; viewport, colour scheme and
  fonts for a page) and write it in `eval.env`. When the result depends on something only the users'
  machines have (a font, an OS, a runtime version), run where it is installed: a sandbox without it
  gives a green that does not hold for them.
- **Run in every environment the users have.** A check green in one says nothing about another: a
  site green on 49 units in Chrome failed 7 in Safari's engine. Some of those reds were the
  measuring tool behaving differently, not the product; look at the actual output before fixing a
  red that only one environment shows.
- **Let the output settle before measuring.** Wait for what is still changing (an animation, a
  background job, a flushed buffer, an eventual write) with a short timeout rather than a fixed tick.

## 3. Run it once on the current version

- **Green, `machine` unit, or `hybrid` unit whose `decided_by` range it meets** — go to step 4.
- **Green, `hybrid` unit without `decided_by`** — hand the author the measured value first, as in
  the case "Red, and the expectation is the question"; go to step 4 once the range is recorded.
- **Red, and the expectation is right** — a real defect. Fix the cause in its own commit and add
  one line to the ledger (skill: `detail-units`, Files); the check stays as written.
- **Red, and the expectation is the question** (a tolerance, a ratio, a golden) — this is a
  `hybrid` decision. Hand the author the measured value and why it differs; record the answer in
  `decided_by` and the ledger. Keep the unit `open` until the author answers.
- **Golden from the first run** — write the measured output to the golden file, then compare it
  with the decision the unit records (`decided_by`, the ledger). The golden becomes the decision
  only after that comparison; a mismatch goes to the author.

## 4. Prove it can fail

Break the unit's cause in the smallest way, rebuild, run all frozen checks, and restore:

- Undo the fix that `cause` names, as a whole: when several changes make the cause together, revert
  them together, or the mutation tests nothing.
- Find every place that sets the cause: a later declaration, override or default that sets the same
  thing again makes a mutation of the first one a no-op.
- Expected: this unit turns red, and every other unit stays as it was, except units this one
  relates to. A red outside the relations is an unrecorded relation — add it to `relations`.
- A mutation that leaves the unit green is a false green: the check measures something else.
  Rewrite the check.
- A mutation that breaks the build tests nothing; choose a mutation that keeps the build running.

Keep each mutation as one line in the product's mutation script (for example `eval/mutate.sh`), so
the proof can be rerun after the runner changes. When the unit was red at baseline (step 3, waiting
on the author), the proof is that the mutation changes the measured value; the unit stays `open`.

## 5. Mark it frozen and record it

Freeze only when the check is green on the current version and, for a `hybrid` unit, `decided_by`
records the author's range. Until then the unit stays `open` and this step waits.

- Set `eval.check` to the id and `status: frozen`; add `eval.env` when step 2 pinned something.
- Validate with the runner: skill: `detail-units` step 5, with `--runner`.
- Add one ledger line (skill: `detail-units`, Files): id = the unit id, what = frozen, decision =
  the mutation that proved it, why = the environment.
- Commit the check, the golden, the mutation line and the units entry together.

## 6. Keep it running

The runner's one command belongs in the product's verify entry point and CI (skill:
`verify-bootstrap` Step 4 and Step 6). A frozen check that turns red later is a detection, not a
check to update: change the expectation only when the author decides the new value (skill:
`detail-units`, Changing an expectation).

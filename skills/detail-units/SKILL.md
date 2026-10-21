---
name: detail-units
description: "Split a product's details into units, one rule of the craft each, and record them in eval/units.yaml (the canonical units format)."
disable-model-invocation: true
user-invocable: true
origin: shimo4228
---

# detail-units — split the details into units and record them

A product's details are many instances of a few rules of the craft. An expert knows those rules,
what each one does, how it shows in the output, and what to change to move it. This skill turns
the findings and the field into that list: one unit per rule, recorded on four faces in the
product repo's `eval/units.yaml`. The file is the shared record of the detail work — skill:
`detail-review` finds instances, skill: `unit-eval` freezes a unit into a check, skill:
`detail-loop` runs the cycle — and this skill holds its format.

Paths below start at `${CLAUDE_SKILL_DIR}`, the directory holding this SKILL.md.

## 1. Start from the current version

Name the branch or commit the units describe, and confirm it is the one the product ships from
(the live build, the latest working branch). Units written against a stale version describe
details that may already have moved. Use skill: `repair-discipline` when the current version is
unclear.

## 2. Draft the fields and their rules ⏸ author approves

List the fields the product's details belong to. For a CLI or library: error messages, help and
docs, naming and defaults, exit codes and output formats, edge inputs, performance, packaging. For a
web page: typesetting per script, layout, accessibility, motion, page metadata, copy. For writing:
structure, terms and notation, numbers and sources, rhythm, platform rendering. For each
field, draft the rules an expert of that field applies without being asked, using the four points
of skill: `widen-depth` as the frame: what experts do, the raw material, the methods and tools, and
what outside the model and the author shows the result is right. The model drafts; the author adds
and removes. The approved list is the frame the findings fold into in step 3, and it can grow later.

## 3. Fold the findings into units

The inputs are findings: the product's ledger, review reports, the author's notes from reading
the product. Each finding is an instance of a rule. Fold it into the unit for that rule, or open a
new unit when no approved rule covers it.

Granularity:

- **One unit = one rule.** Inputs, commands, pages, widths and sections where the rule applies go in
  `eval.instances` and `eval.expect`, not into separate units. The number of units stops at the
  number of rules, which keeps the list from growing with the product.
- **When the eval needs "and", split the unit.** One unit has one check with one expectation.
- **When the cause is "everything", it is not a unit of a rule.** The whole impression (the page
  as a whole, the feel of using the tool, the voice of the article) is an `author` unit with status
  `author-eye`.
- **The eval measures the output** (the CLI's output and exit code, the function's result, the
  rendered page, the published text), not the source. A check on the source text freezes one way of writing the cause; the next edit that
  reaches the same result another way would then fail for no reason.

## 4. Write each unit

### Files

All in the product repo's `eval/`:

- `units.yaml` — the units, in the format below
- `ledger.md` — one line per finding and per decision: the finding's id, what, the decision, why
- `reviews/r<N>-<role>.md` — one review report per reviewer per round; findings are numbered, and
  a finding's id is `r<N>-<role> <n>` (the id `origin` cites)

### Format

`eval/units.yaml` is a list of units. The four faces are the keys `what`, `why`, `eval` and
`cause`. Start the file with a comment that names them, so a reader without this skill can read it
(a convention; the validator does not read comments).

```yaml
# Detail units. One unit = one rule of the craft, recorded on four faces:
#   what = what the rule is; why = what it does for the reader;
#   eval = how it shows in the output (one check, one expectation); cause = what to change to move it.
- id: ja-kinsoku-start            # kebab-case, unique
  field: Japanese typesetting
  what: No line starts with a closing bracket, comma, full stop, prolonged sound mark or small kana.
  why: A word split at a line start breaks the reading.
  eval:
    judge: machine                # machine | hybrid | author
    check: ja-kinsoku-start       # equals id; the check's name in the product's runner
    env: Chrome on macOS (Hiragino)   # optional: where the measurement holds
    expect: 0 lines, at every unit width, on /ja/ and /ja/about/
    instances: ":lang(ja) :is(h1, h2, h3, p, dt, dd, li)"   # optional
  cause: "site.css :lang(ja) { line-break: strict }"
  relations:                      # optional; only interference that was observed
    - unit: ja-quote-hang
      how: co-arising — the same :lang(ja) rule also sets text-spacing-trim
  origin: r3-typography 1, ledger R3 T1   # the finding ids this unit folds
  decided_by: 2026-10-18 author, ...      # only when the author's decision set the expectation
  status: frozen                  # open | frozen | author-eye | retired
```

(illustrative values from a web page; the keys and the allowed values are the format. The same
shape holds a CLI unit — `what: every error message names the next step`, `eval.expect: 0 messages
without one, over the error paths in tests`, `cause: errors.py message templates` — or a writing
unit — `what: one term per concept`, `eval.expect: 0 variants from the glossary`, `cause: the
glossary and the draft`.)

Required on every unit: `id`, `field`, `what`, `why`, `eval.judge`, `eval.expect`, `cause`,
`origin`, `status`. Optional: `eval.check` (required once frozen, absent on `author` units),
`eval.env`, `eval.instances`, `relations`, `decided_by` (required on a frozen `hybrid` unit).
No other keys. Each value other than `eval` and `relations` is non-empty text — quote a value YAML
would read as a date or a number. Each relation has exactly `unit` and `how`, and points at another
unit. The file holds at least one unit.

### Judge

| judge | when | what happens |
|---|---|---|
| `machine` | The output has an objective test: a count, a position, a golden, a ratio from a standard | A check in the product's runner freezes it |
| `hybrid` | The expectation is a taste, but once the author sets it, a machine can hold it (a size ratio, a latency budget, a sentence-length limit) | The author decides the range, recorded in `decided_by`; then a check freezes it |
| `author` | The rule is the whole impression, or no check would mean what the author means (the look, the feel, the voice) | No check. Status `author-eye` (or `retired`): listed for the author's read of the product |

Keep an `author` unit as `author`. A model scoring taste produces a number nobody can act on.

### Status

- `open` — a `machine` or `hybrid` unit, written, no check yet
- `frozen` — a check exists in the product's runner and passes; it reruns on every change (the
  validator checks that the check is in the runner; the runner checks that it passes)
- `author-eye` — the status of every live `author` unit, and only of those; read by the author
- `retired` — the rule no longer applies to the product; kept so the reason stays findable

### Relations

Record a relation only after it was observed: a change to one unit moved another. Two kinds:

- `co-arising` — both units draw on the same cause or the same space (a CLI's startup time and its
  eager loading of plugins; on a page, the Japanese size and the line break after a phrase both use
  the column width)
- `support` — one unit holds only while the other does (a stable JSON output holds only while keys
  are sorted; on a page, edge alignment holds only while no line starts with a space)

Start `how` with the kind, then one clause on the observation.

### Changing an expectation

`expect` and the goldens are decisions. Change one only when the author decides the new value, add
`decided_by` with the date and the author's words, and add one line to the product's ledger.

## 5. Validate

```bash
uv run --project "${CLAUDE_SKILL_DIR}" python "${CLAUDE_SKILL_DIR}/scripts/validate_units.py" \
  eval/units.yaml [--runner <the file that runs the frozen checks>]
```

Pass `--runner` once any unit is frozen.

Exit 0 prints the count of units by judge and status. Exit 1 lists every problem: missing or
empty keys, a key outside the format, an id that is not kebab-case or not unique, values outside
the sets above, an `author` unit with a check or a status other than `author-eye`
or `retired`, `author-eye` on a unit that is not `author`, a frozen unit without a check, a check
that differs from the id or (with `--runner`) is absent from the runner, a frozen `hybrid` unit without
`decided_by`, a relation that is not exactly `unit` and `how`, points at a unit that does not
exist, or points at its own unit. Exit 2: an unreadable file or bad arguments.

## 6. Hand to the author

- The field list with the rules added or removed in step 2
- A table of the units: id, field, judge, status, and the findings each folds
- The counts printed by the validator
- The `hybrid` units waiting for the author's range, and the `author-eye` units to read

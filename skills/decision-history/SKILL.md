---
name: decision-history
description: "Record a design decision as a dated, past-tense entry in the repo's docs/decision-history/, or decide whether it clears the filing bar or belongs in the commit body. Use when recording a decision (経緯を残して / ADR にして), or when context-sync finds a buried decision."
user-invocable: true
origin: shimo4228
replaces: "adr-writer (shimo4228, 2026-11-07 — the ADR form with a Status field, imperative Decision and supersede notes on older entries)"
---

# Decision History

Write one dated entry per design decision in `docs/decision-history/`. An entry records what was decided, why, and what was known on that day, in the past tense. The current design is the thing itself — rules, skills, hooks, tests, code — and the author's current instruction; an entry is read for the history behind it. A new decision may contradict an older entry; the older entry stays as written.

The skill handles the boilerplate (directory detection, sequence numbering, index update) in scripted steps, and the main loop writes the prose.

## Why the main loop writes

Deterministic concerns — where the entry goes, what number it gets, which index needs updating — are easy to get wrong silently (number collisions, sub-directory cwd confusion, index drift), so they live in scripted steps. The prose is written by the main loop that holds the decision: rendering to the house template is cheap for it, and the decision packet (Step 3) is the discipline that keeps *decide* and *render* apart — the packet is settled first, the file is a faithful expression of it, nothing is inferred while writing. A writer renders a decision; it does not make one. The evidence script (Step 4.5) is the fidelity check.

## When to Use (filing conditions — canonical)

Write a new entry only when the decision meets **all three**:

  - **hard to reverse** — undoing it means changing other artifacts (skills, rules, hooks, scripts) or public outputs too. Being revertible with git alone does not count as easy: nearly every harness change is git-revertible
  - **surprising without context** — a future reader would ask "why is it like this?"
  - **the result of a real trade-off** — chosen between genuine alternatives

"Hard to reverse" is met by most harness changes, so it mainly excludes changes whose effects stay local; "surprising" and "real trade-off" do the filtering.

A decision that changes or reverses an earlier entry is its own entry when it meets the three conditions. Link the earlier entry when it helps the reader (`関連する経緯: [0035](./0035-slug.md)`); the earlier entry keeps its text, its date and its state as written — the history stays readable in place, and git holds the order.

Entry points: the user says "record this decision" / "経緯を残して" / "ADR にして", `context-sync` Phase 3 surfaced a buried decision, a debate concluded and the outcome must outlive the session. Apply the three conditions to the request; when they do not all hold, say so and use the commit body.

## When NOT to Use — the commit body carries it

Everything else is recorded in the commit body, in three lines, so `git log --grep` finds it later:

```
Context: <what was observed, with its source>
Decision: <what changed and why>
Review-when: <the observation that would reopen it, or "none — record">
```

This covers bug fixes, reversible refactors, wording changes to rules / skills that nothing else cites, stocktake outcomes (retire / keep verdicts — the stocktake's own results file plus the commit), and personal preferences. When a commit-body decision later gets cited by another artifact, promote it: write the entry then, quoting the commit.

## Workflow

### Step 1: Resolve the record directory

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || REPO_ROOT="$(pwd)"
if [ -d "$REPO_ROOT/docs/decision-history" ]; then DH_DIR="$REPO_ROOT/docs/decision-history"
elif [ -d "$REPO_ROOT/docs/adr" ]; then DH_DIR="$REPO_ROOT/docs/adr"   # repo that has not renamed yet
else DH_DIR="$REPO_ROOT/docs/decision-history"; fi
```

If `$DH_DIR` does not exist, create it — the request itself covers the directory, and
git makes it reversible. Mention the creation in your final report. Write a minimal
`README.md` index alongside:

````markdown
# 判断の経緯（Decision History）

何を決め、なぜそうしたかの記録。1 件 1 ファイル、番号は連番、過去形で書く。現行の設計は実物と
今の指示が決め、記録は書かれた日の判断。新しい判断は旧記録と衝突してよく、旧記録はそのまま置く。

## Index

| # | Title | Date |
|---|-------|------|

## Template

Entries use the 6-section template
(`scripts/adr_lint.py` checks section presence mechanically):

```markdown
# NNNN: [Title]

## Date
YYYY-MM-DD

## Context
[what was the problem — facts of the day, with sources]

## Decision
[what was done and why — past tense]

## Review-when
[what observation would reopen this, 1–3 lines; or "none — record"]

## Alternatives Considered
[rejected options and why; a live rival as "Open — revisit when: …"]

## Consequences
[what became easier / harder]
```

File name: `NNNN-kebab-case-title.md` (zero-padded 4-digit sequence).
Index rows link the number: `| [NNNN](NNNN-slug.md) | Title | YYYY-MM-DD |`.
````

(Index rows make the number a relative link. `adr_lint.py` reads the expected section set from this
README's Template fenced block, so placing the README doubles as the lint's template declaration.
A repo whose README still carries the older 7-section template with `## Status` is checked
against that template until its README changes.)

### Step 2: Pick the next sequence number

```bash
LAST_NUM=$(ls "$DH_DIR"/[0-9]*-*.md 2>/dev/null | sort -V | tail -1 | sed -E 's|.*/([0-9]+)-.*|\1|')
if [ -z "$LAST_NUM" ]; then
  NEXT_NUM="0001"
else
  NEXT_NUM=$(printf "%04d" $((10#$LAST_NUM + 1)))
fi
```

Verify uniqueness right before writing (race safety):

```bash
[ -e "$DH_DIR/$NEXT_NUM-"*.md ] && echo "COLLISION" || echo "OK"
```

If `COLLISION`, recompute `NEXT_NUM` from the latest state.

### Step 3: Gather the 6 inputs

Ask the user (or accept from caller) for:

1. **Title** — states the decision, kebab-case-friendly (e.g., `context-sync-cascade-and-writer-agents`). The skill composes the filename.
2. **Context** — what problem prompted this decision, with the facts and sources of the day (raw text OK).
3. **Decision** — what was done and why (raw text OK).
4. **Review-when** — what observation or premise failure would reopen this, 1-3 lines. It is a reservation of when to think again, captured at write time. If there genuinely is none, write "none — record".
5. **Alternatives** — what else was considered and why rejected, or, for an alternative that stays live, "Open — revisit when: …" (raw text or list). Keeping a rival open is allowed; a straw man is not.
6. **Consequences** — what became easier / harder (raw text or list).

If 2-6 are missing, request them — do not proceed. Entries without these sections are noise.

**Preventive check (before settling the packet).** Read [references/review-findings.md](references/review-findings.md)
(a dated casebook of frequent review findings) and self-check against the matching patterns — cited entries
exist and say what is cited, provenance of coined terms, references to gitignored paths, sources and denominators
of numbers, what is held fixed in count conditions. This is write-time prevention; semantic review is Step 4.6.

**Assemble and approve the decision packet before writing.** Settle the actual content here: the real Context, the decision as decided, the Review-when triggers, why each Alternative was rejected (or under what condition it is revisited), which Consequences genuinely follow. When your harness's boundary rule hands these records to the user, confirm this packet with them *before* Step 4; otherwise write it and show the packet in the report (the author's harness writes entries without confirmation — `rules/common/boundary.md`). Step 4 expresses the packet and adds nothing, so a fuzzy decision is resolved here.

### Step 4: Write the file (main loop)

Read the 2 most recent entries in `$DH_DIR` for house style (heading form, link style, whether
Consequences splits into Positive / Negative / Neutral), then write
`$DH_DIR/$NEXT_NUM-<title>.md` from the Step 3 packet:

- Heading `# NNNN: <title>`, then the 6 sections in template order (Step 1's template, or
  the repo's own README Template block when it differs)
- Every Context fact, Decision clause, rejection reason and Consequence comes from the packet.
  Writing is expression, not synthesis — a consequence that feels "logically entailed" but is not
  in the packet goes back to Step 3 for the user to approve, not into the file
- Decision in the past tense ("X を Y に移した", "moved X to Y because Z") — it says what was done
  and why; Review-when as observable triggers; each Alternative with its rejection reason or
  "Open — revisit when: …"
- Links to sibling entries are relative (`./NNNN-slug.md`) and the file name is copied from `ls`,
  not typed from memory — Step 4.5's `refs.links_broken` is the check
- When the decision went through a plan, the first line of Context links the approved plan:
  `Plan: [docs/plans/<file>](../plans/<file>)（承認 YYYY-MM-DD）`. The plan is the frozen
  precommitment; the entry still stands on its own — the link is provenance, not a substitute

If a packet field is missing, stop and ask; do not write a partial entry.

### Step 4.5: Run the mechanical lint and the per-entry evidence

```bash
python3 ~/.claude/skills/decision-history/scripts/adr_lint.py --root "$REPO_ROOT"
```

Evidence mode (no verdict, exit 0). In the output JSON, fix the **deviations in the entry you just wrote**
(missing_sections / case_mismatch / date / index / naming) before moving on.
Deviations in existing entries are report-only — do not fix them in this step (separate task). The lint
covers mechanical properties only and is not a substitute for semantic review (decision-history-reviewer).

When you want an ad hoc blocking verdict, add `--gate`. The exemption boundaries are unbounded by
default, so pass per-repo values — harness uses `--sections-from 44 --require-review-when-from 44`
(exempting 0009's two missing sections and the absent Review-when in 0043 and earlier).

Next, take the per-entry evidence for the one you just wrote (the machine-countable part
of the findings decision-history-reviewer repeats):

```bash
python3 ~/.claude/skills/decision-history/scripts/adr_review_evidence.py --root "$REPO_ROOT" --adr "$NEXT_NUM" --diff worktree
```

Fix here **what can be fixed at write time** in the JSON — `refs.unresolved` (entry / RFC numbers that do not exist),
`refs.links_broken`, `missing` (nonexistent paths) and `ignored` (gitignored evidence — promote it to
`docs/evidence/` or rewrite to be path-independent) in `paths.flagged`, `paths.line_refs_out_of_range`,
`numbers.percent_without_denominator`, `numbers.relative_referents` (conversation references).
If `diff_scope.changed_not_mentioned` lists changes the entry
does not mention, write them into the Decision or split them into a separate commit. The remaining keys
(`numbers.unanchored`, `review_when`, `alternatives`, `consequences`, `second_record`) need judgment and go to the Step 4.6 reviewer. `relations.*` is evidence of which earlier entries this one names; nothing in it asks for an edit to an earlier entry.

### Step 4.6: Run the semantic review (decision-history-reviewer)

Before commit, launch agent: `decision-history-reviewer` and hand it the entry you just wrote — do not skip this.
**This skill is the only wiring for decision-history-reviewer** — skipping it here means no semantic review runs at all. The main loop accepts or rejects each finding against the Step 3 packet, and fixes only the accepted ones.

### Step 5: Update the index

After Step 4 writes the file, append a row to `$DH_DIR/README.md` index table:

```bash
# Read current index
# Find the table block (lines between the "| # |" header and the next "##" heading)
# Append: | [$NEXT_NUM]($NEXT_NUM-<slug>.md) | <title human-readable> | <date> |
```

If the index table is malformed or absent, regenerate it from the directory:

```bash
for f in "$DH_DIR"/[0-9]*-*.md; do
  num=$(basename "$f" | sed -E 's|([0-9]+)-.*|\1|')
  title=$(head -1 "$f" | sed -E 's|^# (ADR-)?[0-9]+: ||')
  date=$(awk '/^## Date/{getline; getline; print; exit}' "$f")
  echo "| [$num]($(basename "$f")) | $title | $date |"
done
```

### Step 6: Report

Tell the user:

```
Entry written
---
File:    docs/decision-history/<NNNN>-<title>.md
Number:  <NNNN>
Index:   updated (+1 row)
```

## Edge cases

| Case | Handling |
|---|---|
| Called from a sub-directory of the repo | Use `git rev-parse --show-toplevel`; never trust raw cwd |
| Not a git repo | Fall back to cwd, warn the user that they should `git init` |
| Number was reserved verbally but not yet written ("I'll write 0010 later") | Skill cannot know; ask the user whether to take the next free number or the reserved one |
| The decision reverses or narrows an earlier entry | Write the new entry; link the earlier one when it helps (`関連する経緯: [NNNN](./NNNN-slug.md)`). The earlier entry is left as written. |
| Title contains spaces or non-ASCII | Skill normalizes to kebab-case ASCII for the filename; preserves original in the `# NNNN: ...` heading |

## Boundaries

- The files this skill writes are the new entry and the index.
- The commit follows the repo's commit rule (the author's harness: `rules/common/boundary.md`).

## Reference Files

- Template canonical source: read the target repo's existing entries to mirror their voice. For the harness itself, see `~/.claude/docs/decision-history/README.md`.
- Mechanical lint (evidence mode + `--gate`): `scripts/adr_lint.py` (adapts the template automatically from the repo's
  record README Template; tests are `tests/test_adr_lint.py`).
- Per-entry review evidence (evidence mode only): `scripts/adr_review_evidence.py` (
  cited references exist, path classification, diff scope, unsourced numbers; tests are
  `tests/test_adr_review_evidence.py`). This one file is the entry point for running and importing; the
  checks themselves are split across `scripts/adr_evidence_common.py` / `_paths.py` / `_prose.py` to stay
  within the per-file LOC budget.
- Casebook of frequent review findings: `references/review-findings.md` (read during the Step 3 preventive check).
- Evals: `evals/evals.json` (3 scenarios — new entry / missing directory / sequence collision).

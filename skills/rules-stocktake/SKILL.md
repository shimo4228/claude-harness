---
name: rules-stocktake
description: "Audit the rules in a Claude Code harness (~/.claude/rules or a repo's .claude/rules) for residency cost, staleness, redundancy and substrate absorption, and give each rule a verdict. Use when the rules may have bloated."
license: MIT
metadata:
  author: shimo4228
  version: "1.1"
user-invocable: true
origin: shimo4228
---

# rules-stocktake — Rules Quality Audit

Evaluate every rule file under `<harness>/rules/` **holistically, all in one context**,
and assign each a verdict: `Keep / Improve / Update / Merge / Demote to skill /
Dissolve / Retire`. The audit unit is the file; the cost unit is the **line** — rules
load into every session unconditionally, so each line is a per-session token tax plus
instruction dilution.

> Design note: this is skill-stocktake's sibling with the cost model inverted. A skill's
> cost is trigger pollution (it fires probabilistically and degrades selection); a rule's
> cost is **residency** (it loads always, whether or not it changes behavior). So there is
> no usage axis — nothing measures "rule invocations", and the concept doesn't apply to
> unconditional loading. The replacements are static: residency density (is each line worth
> reading every session?) and substrate absorption (does the harness or the conversation
> already do this without the rule?).

> Design note 2: unlike skill-stocktake, this skill **does** apply approved Improve/Update/
> Merge edits itself instead of handing off. There is no improvement-engine skill for rules
> (skill-writer's counterpart doesn't exist), and rule files are short — delegation
> would be overengineering. The handoff exception is Demote (creating a new skill is
> skill-writer's job).

**Roots.** `<harness>` below is the harness this audit covers: `~/.claude` by default, or a repository's `.claude/` when skill `harness-stocktake` runs in project mode (its Roots section maps the paths, names the evidence that is `n/a` there, and says which convention checks apply). The ledger `<ledger>` belongs to that harness: `${CLAUDE_SKILL_DIR}/results.json` when this skill's directory is inside `<harness>` (the harness carries its own copy of the skill), else `<harness>/stocktake/rules-stocktake.json` (an installed plugin, or project mode). Either way it is committed with the harness's other changes on the apply branch.

## Modes (`$ARGUMENTS`)

| Argument | Behavior |
|----------|----------|
| none / `full` | Read and evaluate every rule (default) |
| `changed` | Re-evaluate only rules whose mtime is newer than `<ledger>`'s `evaluated_at`; carry the rest forward from the ledger |

`changed` detects changes inline (no script):
> Paths below start at `${CLAUDE_SKILL_DIR}`, the directory holding this SKILL.md; an agent that does not substitute the variable reads it as that directory.

```bash
find <harness>/rules -name "*.md" -newermt "$(jq -r .evaluated_at "<ledger>")"
```

**The Phase 1 integrity checks always run over the full set, including in `changed`
mode**: cross-reference breakage is invisible to rule mtimes — retiring a *skill*
silently breaks a ``skill: `name` `` pointer in an unmodified *rule*. They are grep,
seconds of work, and any rule with a newly broken reference is promoted into the
re-evaluation set even if its mtime is old.

## Phase 1 — Inventory + mechanical integrity checks

Enumerate with Glob (no script): `<harness>/rules/**/*.md`. The corpus is small enough
to read every file into one context — no batching, no grep pre-filter. Measure the
corpus size live (`find <harness>/rules -name '*.md' | xargs wc -l`) rather than
trusting a figure written here; per-file line counts become the residency-cost column
in Phase 3 and the `lines` field in the ledger.

Run the mechanical checks with throwaway bash/grep (detection is structural → code;
judgment on what the findings mean → LLM, per the enumerate/decide split):

- [ ] Every ``skill: `name` `` pointer in a rule resolves to `<harness>/skills/<name>/`
- [ ] Every relative link between rule files resolves
- [ ] Every rule file's line 1 carries `<!-- origin: X -->` (where the harness states this convention)
- [ ] Every `rules/common/` file carries `<!-- rationale: ... -->` and
  `<!-- review-when: ... -->` within its first 10 lines (when the harness has a lint script for
  this — `<harness>/scripts/hooks/harness_lint.py` — run it and read its output instead of re-grepping)
- [ ] `rules/README.md`'s table matches the actual file list (no missing, no phantom entries)

A `skill-health` dangling-reference scan, when one has run, is ready-made evidence for the
first check.

State the scan result up front: files found, total lines, integrity failures. Carry the
failures into Stage 1 as pre-computed evidence — do not re-grep there.

## Phase 2 — Evaluation (fully inline, holistic)

Read the body of **every** rule and evaluate them one by one while seeing the whole set.

**Stage 1 — binary screen (every rule).** Answer each item as an explicit Yes/No per
rule. Record answers internally; **surface only the No answers**:

- [ ] No content overlap with other rules? (a rule that **declares** another as canonical and
  points at it is NOT overlap — that is the intended layering. Copied prose is.)
- [ ] No overlap with skills / MEMORY.md / CLAUDE.md? (the division "principle in the rule,
  detail in the skill, a ``skill: `name` `` pointer bridging them" is NOT overlap — a full procedure
  residing in the rule body **is**, and signals Demote)
- [ ] All cross-references resolve? (read off the Phase 1 results)
- [ ] Technical references current? **Unconditionally verify** every artifact the rule
  names — `ls` each referenced path (skills, agents, hooks, scripts) and run `--help` /
  version checks for named CLI flags. "Verify if it looks stale" is banned phrasing:
  the condition is what dilutes. Deterministically checkable claims get deterministic
  checks, every time.
- [ ] Not yet absorbed by the substrate or the conversation? (downward: does the harness —
  system prompt, tool descriptions, native plan/review machinery — now cover this domain
  natively? inward: is the principle so internalized that behavior no longer depends on the
  rule? Either absorption → Dissolve candidate. Criteria imported from akc-cycle.md's
  Scaffold Dissolution two vectors)
- [ ] Dense enough to deserve residency? (does each section change behavior often enough
  to justify being read every session? rarely-needed reference material, long procedures,
  single-project content → Demote or Improve-by-shortening candidate)
- [ ] Written in the affirmative? (each prohibition targets a grep-able concrete action, the
  default behavior was observed to go the other way, no machine gate covers it, and a
  one-clause reason is attached — any other "don't", especially on style or internal process,
  is an Improve candidate: reword it as the default to follow)

Seven questions and no more — the two static questions (absorption, density) replace the
lost usage signal; further decomposition degrades holistic judgment.

**Stage 2 — verdict pressure-test (non-Keep candidates only).** When Stage 1 plus the
holistic read points away from Keep, generate **1–3 rule-specific atomic yes/no questions**
that try to **refute the draft verdict** before finalizing it. **If the rule declares a
`review-when:` comment, its triggers are the first questions** — they are the expiry
conditions captured at write time, which ad-hoc generation cannot recover.
Ask "has trigger X fired — Yes/No" per declared trigger, then supplement with generated
questions only if needed, each answered with one line
of evidence (file read, path check, WebSearch, harness-doc check). For **Dissolve**
candidates one question is mandatory: *"Can the absorbing harness feature be named
concretely — Yes/No"* — an absorption claim that cannot name its absorber is refuted.
Keep-bound rules get no dynamic questions.

Outside evidence enters Stage 2 when it exists — read it, never require it: `skill-comply`
results (a compliance-based verdict needs one; this audit is static), `generation-audit`'s
runtime-layer findings on a model-generation change, and `harness-boundary`'s Delete / Move
on an installed rule.

Evaluation is **holistic judgment, not a numeric rubric** — binary answers are evidence
feeding the verdict, never aggregated into a score. Evaluation is **origin-blind** (do not
branch on vendored / self-written / customized) — though, where the harness states the origin
convention (the author's does, in `common/skills.md`), a *missing* origin header is itself an
integrity finding and feeds Improve.

**Aggregate residency cost (set-level, not per-rule):** holding a rule is not free even
when the rule is individually fine. Every line loads into every session — the tax is
unconditional — and the longer the total corpus, the weaker the compliance pressure each
individual rule exerts (instruction dilution). So the Keep bar **rises with total line
count**: when the corpus is large, a merely-adequate rule is a Demote/Merge candidate on
dilution grounds alone. This is a judgment input, never a quota; do not cut lines to hit
a number.

| Verdict | Meaning |
|---------|---------|
| Keep | Earns its residency: current, unique, dense |
| Improve | Worth keeping, but needs tightening — for rules, Improve usually means *shorten* |
| Update | Referenced technology is outdated (verify with WebSearch) |
| Merge into [X] | Substantial overlap with another rule; name the target |
| Demote to skill | Valuable content that doesn't earn per-session residency; move to the probabilistic trigger layer (the inverse of rules-distill), leaving a 1–3 line pointer in the rule (the task-tracking.md pointer pattern) |
| Dissolve | Absorbed by the substrate (harness went native) or the conversation (internalized). Retirement by *success*, not defect — delete before it becomes a stale shadow overriding newer defaults, and record the why in an ADR |
| Retire | Defect-based removal: low quality, stale, broken beyond repair |

**Mandatory-surface rule** (the counterpart of skill-stocktake's zero-usage rule): a No on
the absorption question MUST surface the rule as a Dissolve candidate (the final call is
the user's). An absorbed rule is more urgent than an unused skill — the unused skill
sleeps harmlessly; the absorbed rule actively overrides evolving harness defaults.

**README.md special case**: `rules/README.md` is an index, not a rule — it gets only the
table-consistency and currency checks, and a two-value verdict (Keep or Update).

## Phase 3 — Summary

Render a table: `Rule | Lines | Verdict | Reason`. Close with one line reporting the
total line count and its delta since the previous audit (`total_lines` in the ledger) —
that delta is the input to the aggregate-residency-cost judgment next run.

## Phase 4 — Report and apply

Turn every verdict into items (source `rules`) of the report contract in skill:
`harness-stocktake` and hand them to it: one report, one approval from the author, application
on a task branch, a completion report, an ff-only merge. Called alone, this skill runs that
contract's Phases 2–5 with its own items. Because rules load every session, each non-Keep item
shows the exact edit, not a summary. Each item carries, by verdict:

- **Improve / Update / Merge**: `change` = the concrete edit as a diff. Application edits the rule
  directly on the branch (Design note 2). If the edit changes the rule's reason-to-exist or expiry
  conditions, the same diff refreshes its `rationale:` / `review-when:` comments
- **Demote to skill**: `change` = the 1–3 line principle + ``skill: `name` `` pointer that stays,
  and the skill-writer intent packet for what moves. Application creates the skill through
  skill-writer's report path
- **Dissolve / Retire**: `reason` = the absorption evidence or defect and what covers the need
  instead (Dissolve: the named harness feature; Retire: the replacement rule/skill); `impact` =
  other rules referencing it and the public repo copy. Application records a Dissolve's why via
  `adr-writer`
- **Keep**: `reason` only

Where skill `harness-stocktake` is not installed, show the same items as one table ordered
Dissolve / Retire → Merge / Demote → Improve / Update → Keep, take one approval with the author's
overrides, then apply.

On the apply branch, in the same commit as the changes:

- **Sync README.md**: any file added/renamed/removed → update the table row and its one-line
  description (pairs with the Phase 1 consistency check).
- **Update the ledger**: Read `<ledger>` → merge this run's verdicts (an item the author
  skipped keeps its verdict with `"skipped": true`) → Write it back (`evaluated_at` = real UTC
  from `date -u +%Y-%m-%dT%H:%M:%SZ`). In `changed` mode, preserve prior verdicts of rules not
  re-evaluated.
- **Public-copy note**: when the setup publishes copies of its rules elsewhere, retiring or editing
  one leaves that copy stale — point the user at their publish step for the follow-up.

## Reason quality (required)

Every `reason` must be **self-contained** — decision-enabling on its own. "unchanged"
alone is banned. For non-Keep verdicts, cite the No answers (question + one-line evidence):

- **Demote**: name what stays and what moves. Bad: `"Too detailed"` / Good: `"109 lines of pytest fixture recipes; only the 80%-coverage principle changes per-session behavior. Keep 3 lines + pointer, move recipes to the language-specific skill."`
- **Dissolve**: name the absorber. Bad: `"Not needed anymore"` / Good: `"Harness plan mode now enforces the plan-file workflow natively (system prompt §Plan Workflow); the rule's manual checklist duplicates and predates it. ADR the why, then delete."`
- **Merge**: name the target + what to integrate. Bad: `"Overlaps"` / Good: `"§Commit gate duplicates security.md's repo gate line; only the bypass note is unique — fold it into security.md's repo gate line."`
- **Keep** (carry-forward in `changed` mode): restate the rationale. Bad: `"Unchanged"` / Good: `"Content unchanged. 42-line fix-chain gate referenced by planning.md's 2-intervention model; no absorber in current harness."`

## Ledger (`<ledger>`, lean)

```json
{
  "evaluated_at": "2026-07-03T00:00:00Z",
  "total_lines": 1144,
  "rules": {
    "common/planning": {
      "path": "<harness>/rules/common/planning.md",
      "lines": 209,
      "verdict": "Keep",
      "reason": "...",
      "mtime": "2026-06-28T09:45:00Z"
    }
  }
}
```

Keys are directory-qualified stems (`common/planning`, `common/boundary`) so the schema
survives nesting.
`lines` / `total_lines` let `changed` mode rebuild the Phase 3 table
and the aggregate judgment from carried-forward entries. Update inline with Read/Write,
not a script. Created on the first run — do not pre-seed an empty file.

## Related

- `agent-stocktake` — the same audit for `<harness>/agents/`.
- `repo-asset-stocktake` — the same stocktake pattern for a project repo's non-code assets (configs / workflows / runbooks).

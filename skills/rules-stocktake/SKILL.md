---
name: rules-stocktake
description: "Audit ~/.claude/rules (always-loaded behavioral rules) for residency cost, staleness, redundancy, broken See-skill pointers, and substrate absorption, assigning Keep/Improve/Update/Merge/Demote-to-skill/Dissolve/Retire verdicts. Use when the user says \"audit my rules\", \"rules stocktake\", \"which rules should be demoted or dissolved\", 「rules が肥大化してきた」「ルールを棚卸しして」, or when the model generation changed and over-constraints written for the previous one may now be net-negative (「新しいモデルに合わせて rules を見直したい」「rightsize したい」). NOT for — skill quality → skill-stocktake; promoting skill patterns INTO rules → rules-distill (this is its inverse); runtime compliance → skill-comply; whole-config GC → config-gc."
license: MIT
metadata:
  author: shimo4228
  version: "1.1"
user-invocable: true
origin: shimo4228
---

# rules-stocktake — Rules Quality Audit

Evaluate every rule file under `~/.claude/rules/` **holistically, all in one context**,
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
> (skill-creator's counterpart doesn't exist), and rule files average ~60 lines — delegation
> would be overengineering. The handoff exception is Demote (creating a new skill is
> skill-creator's job).

## Modes (`$ARGUMENTS`)

| Argument | Behavior |
|----------|----------|
| none / `full` | Read and evaluate every rule (default) |
| `changed` | Re-evaluate only rules whose mtime is newer than `results.json`'s `evaluated_at`; carry the rest forward from the ledger |

`changed` detects changes inline (no script):
```bash
find ~/.claude/rules -name "*.md" -newermt "$(jq -r .evaluated_at ~/.claude/skills/rules-stocktake/results.json)"
```

**Correction that keeps `changed` mode honest**: cross-reference breakage is invisible to
rule mtimes — retiring a *skill* silently breaks a `See skill:` pointer in an unmodified
*rule*. So the Phase 1 integrity checks **always run over the full set** (they are grep,
seconds of work), and any rule with a newly broken reference is promoted into the
re-evaluation set even if its mtime is old.

## Phase 1 — Inventory + mechanical integrity checks

Enumerate with Glob (no script): `~/.claude/rules/**/*.md`. The corpus is small enough
to read every file into one context — no batching, no grep pre-filter. Measure the
corpus size live (`find ~/.claude/rules -name '*.md' | xargs wc -l`) rather than
trusting a figure written here; per-file line counts become the residency-cost column
in Phase 3 and the `lines` field in the ledger.

Run the mechanical checks with throwaway bash/grep (detection is structural → code;
judgment on what the findings mean → LLM, per the enumerate/decide split):

- [ ] Every `See skill:` / `See skills:` target exists under `~/.claude/skills/<name>/`
- [ ] Every relative link between rule files resolves (the corpus is flat as of
  2026-07-25 — a language sub-layer was retired into `skills/python-patterns`, so a
  surviving `python/` path is a stale pointer, not a layer to validate)
- [ ] Every rule file's line 1 carries `<!-- origin: X -->`
- [ ] Every `rules/common/` file carries `<!-- rationale: ... -->` and
  `<!-- review-when: ... -->` within its first 10 lines (ADR-0021; harness_lint
  checks presence deterministically — read its result instead of re-grepping)
- [ ] `rules/README.md`'s tree matches the actual file list (no missing, no phantom entries)

State the scan result up front: files found, total lines, integrity failures. Carry the
failures into Stage 1 as pre-computed evidence — do not re-grep there.

## Phase 2 — Evaluation (fully inline, holistic)

Read the body of **every** rule and evaluate them one by one while seeing the whole set.

**Stage 1 — binary screen (every rule).** Answer each item as an explicit Yes/No per
rule. Record answers internally; **surface only the No answers**:

- [ ] No content overlap with other rules? (a rule that **declares** another as 正本 and
  points at it is NOT overlap — that is the intended layering. Copied prose is.)
- [ ] No overlap with skills / MEMORY.md / CLAUDE.md? (the division "principle in the rule,
  detail in the skill, `See skill:` bridging them" is NOT overlap — a full procedure
  residing in the rule body **is**, and signals Demote)
- [ ] All cross-references resolve? (read off the Phase 1 results)
- [ ] Technical references current? (if CLI flags / APIs / tool names look stale, confirm
  with WebSearch)
- [ ] Not yet absorbed by the substrate or the conversation? (downward: does the harness —
  system prompt, tool descriptions, native plan/review machinery — now cover this domain
  natively? inward: is the principle so internalized that behavior no longer depends on the
  rule? Either absorption → Dissolve candidate. Criteria imported from akc-cycle.md's
  Scaffold Dissolution two vectors)
- [ ] Dense enough to deserve residency? (does each section change behavior often enough
  to justify being read every session? rarely-needed reference material, long procedures,
  single-project content → Demote or Improve-by-shortening candidate)

Six questions and no more — the two static questions (absorption, density) replace the
lost usage signal; further decomposition degrades holistic judgment (see References).

**Stage 2 — verdict pressure-test (non-Keep candidates only).** When Stage 1 plus the
holistic read points away from Keep, generate **1–3 rule-specific atomic yes/no questions**
that try to **refute the draft verdict** before finalizing it. **If the rule declares a
`review-when:` comment, its triggers are the first questions** — they are the expiry
conditions captured at write time (ADR-0021), which ad-hoc generation cannot recover.
Ask "has trigger X fired — Yes/No" per declared trigger, then supplement with generated
questions only if needed, each answered with one line
of evidence (file read, path check, WebSearch, harness-doc check). For **Dissolve**
candidates one question is mandatory: *"Can the absorbing harness feature be named
concretely — Yes/No"* — an absorption claim that cannot name its absorber is refuted.
Keep-bound rules get no dynamic questions.

Evaluation is **holistic judgment, not a numeric rubric** — binary answers are evidence
feeding the verdict, never aggregated into a score. Evaluation is **origin-blind** (do not
branch on ECC / shimo4228 / customized) — though a *missing* origin header is itself an
integrity finding (common/skills.md requires it) and feeds Improve.

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
tree-consistency and currency checks, and a two-value verdict (Keep or Update).

## Phase 3 — Summary

Render a table: `Rule | Lines | Verdict | Reason`. Close with one line reporting the
total line count and its delta since the previous audit (`total_lines` in the ledger) —
that delta is the input to the aggregate-residency-cost judgment next run.

## Phase 4 — Consolidation

**Confirm one by one** (config-gc's confirm-each design): walk the non-Keep candidates
sequentially — for each rule, show the evidence first, then ask `[y/n/skip]`. Never batch
the approval ("apply all edits? [y/n]" defeats the design — one rule, one decision; this
matters doubly here because approved edits are applied in-session). The user can stop at
any point; `skip` records the verdict in the ledger unactioned.

- **Improve / Update / Merge**: present the concrete edit per rule → ask `[y/n/skip]`;
  **after the user approves that rule, apply it directly in this session** (see Design
  note 2 — no improvement engine exists for rules, and the files are small). If an
  applied edit changes the rule's reason-to-exist or expiry conditions, refresh its
  `rationale:` / `review-when:` comments in the same diff (ADR-0021).
- **Demote to skill**: hand off skill creation to `skill-creator`; then reduce the rule
  to a 1–3 line principle + `See skill:` pointer.
- **Dissolve / Retire**: per file, present (1) the absorption evidence or defect, (2) what
  covers the need instead (Dissolve: the named harness feature; Retire: the replacement
  rule/skill), (3) removal impact — **other rules referencing it and the public repo copy**.
  Act only after the user confirms. For Dissolve, offer to record the why via `adr-writer`
  (akc-cycle.md: "record the why in an ADR, not a standing rule").
- **Sync README.md**: any file added/renamed/removed → update the tree and its one-line
  description (pairs with the Phase 1 consistency check).
- **Update the ledger**: Read `results.json` → merge this run's verdicts → Write it back
  (`evaluated_at` = real UTC from `date -u +%Y-%m-%dT%H:%M:%SZ`). In `changed` mode,
  preserve prior verdicts of rules not re-evaluated.
- **Public-repo note**: retiring or editing an `origin: shimo4228` rule leaves the public
  repo stale — point the user at `harness-sync` for the follow-up.

## Reason quality (required)

Every `reason` must be **self-contained** — decision-enabling on its own. "unchanged"
alone is banned. For non-Keep verdicts, cite the No answers (question + one-line evidence):

- **Demote**: name what stays and what moves. Bad: `"Too detailed"` / Good: `"109 lines of pytest fixture recipes; only the 80%-coverage principle changes per-session behavior. Keep 3 lines + pointer, move recipes to python-patterns skill."`
- **Dissolve**: name the absorber. Bad: `"Not needed anymore"` / Good: `"Harness plan mode now enforces the plan-file workflow natively (system prompt §Plan Workflow); the rule's manual checklist duplicates and predates it. ADR the why, then delete."`
- **Merge**: name the target + what to integrate. Bad: `"Overlaps"` / Good: `"§Retry duplicates debugging.md's Retry with Context; only the backoff constants are unique — fold them into debugging.md L40."`
- **Keep** (carry-forward in `changed` mode): restate the rationale. Bad: `"Unchanged"` / Good: `"Content unchanged. 42-line fix-chain gate referenced by planning.md's 2-intervention model; no absorber in current harness."`

## results.json (lean ledger)

```json
{
  "evaluated_at": "2026-07-03T00:00:00Z",
  "total_lines": 1144,
  "rules": {
    "common/planning": {
      "path": "~/.claude/rules/common/planning.md",
      "lines": 209,
      "verdict": "Keep",
      "reason": "...",
      "mtime": "2026-06-28T09:45:00Z"
    }
  }
}
```

Keys are directory-qualified stems (`common/planning`, `common/debugging`) so the schema
survives if the corpus nests again — it is flat as of 2026-07-25 but has nested before.
`lines` / `total_lines` let `changed` mode rebuild the Phase 3 table
and the aggregate judgment from carried-forward entries. Update inline with Read/Write,
not a script. Created on the first run — do not pre-seed an empty file.

## Related

- `skill-stocktake` — the same audit for skills; this skill inverts its cost model (trigger pollution → residency).
- `repo-asset-stocktake` — the same stocktake pattern for a project repo's non-code assets (configs / workflows / runbooks); rules-stocktake audits `~/.claude/rules/`.
- `rules-distill` — promotes skill patterns *into* rules; rules-stocktake audits what accumulated and demotes back what stopped earning residency. Inverse directions over the same boundary.
- `skill-comply` — measures whether rules are actually *followed* (dynamic). rules-stocktake stays static: never issue a compliance-based verdict without a skill-comply run; existing skill-comply results may serve as Stage 2 evidence (read, never require).
- `config-gc` — whole-config GC across hooks/permissions/MCP; rules-stocktake judges rule *quality*.
- `skill-creator` — handoff target for the skill-creation half of Demote.
- `adr-writer` — records the why of a Dissolve.
- `harness-sync` — syncs surviving `origin: shimo4228` rules to the public repo after edits/retirements.

## References

The two-stage binary-question design (screen → verdict pressure-test, holistic verdict,
no score aggregation) is inherited from skill-stocktake and follows the
checklist-decomposition evaluation line: BinEval "Ask, Don't Judge"
([arXiv:2606.27226](https://arxiv.org/abs/2606.27226)), CheckEval (arXiv:2403.18771),
TICK (arXiv:2410.03608) — over-decomposition degrades correlation on holistic quality,
hence six questions and no score. The absorption question and the Dissolve verdict
implement `rules/common/akc-cycle.md` — the Curate checks (redundancy / staleness /
silence) and Scaffold Dissolution's two vectors (inward internalization, downward
substrate absorption).

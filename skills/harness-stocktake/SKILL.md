---
name: harness-stocktake
description: "Take stock of the whole harness in one report and one approval, then apply on a branch (ハーネスの棚卸し)."
origin: shimo4228
user-invocable: true
disable-model-invocation: true
---

# harness-stocktake — one report, one approval, one merge

Runs every stocktake over `~/.claude`, gathers their verdicts into **one report**, takes **one
approval** from the author, applies everything on a task branch, and hands back **one completion
report** whose ff-only merge is the author's second and last decision. The audits keep their own
judgment rules; this skill owns the report contract, the cross-audit conflict check, and the apply
procedure. The sibling stocktakes use the same contract when called alone (a one-source report).

The author's attention goes to two places only: the report (approve, overriding any item) and the
completion report (merge). Everything between them runs to the end without asking. An item that
cannot be settled without the author goes to **未決 (pending)** in the completion report.

## Modes (`$ARGUMENTS`)

| Argument | Behavior |
|---|---|
| none / `all` | Collect from every source below, publish the report, wait for approval |
| `<source>` | One source only (what a sibling stocktake uses when called alone) |
| `apply` | Resume from an approved report (`.notes/stocktake/latest.json` names it) |
| `--unattended` | Stop after publishing and notify Slack (the monthly launchd run) |

## Phase 1 — Collect

Run each source's own audit up to and including its verdict phase, in this order (later sources see
the earlier sources' items, which feeds Phase 2):

| Source id | Skill | What it audits |
|---|---|---|
| `skills` | skill-stocktake | `skills/*/SKILL.md` |
| `rules` | rules-stocktake | `rules/**/*.md` |
| `agents` | agent-stocktake | `agents/*.md` |
| `hooks` | hook-stocktake | `hooks/*.sh`, `scripts/hooks/*` |
| `distill` | rules-distill | rule candidates from skills |
| `docs` | context-sync | harness CLAUDE.md, ADRs, README |
| `assets` | repo-asset-stocktake | harness configs, scripts, docs without a consumer |

Open each source's skill by reading `skills/<name>/SKILL.md` with Read and follow it up to its
verdict phase (several sources are `disable-model-invocation: true`, and the Skill tool starts only
the skills in the listing).

Each source turns every verdict into items of the schema below and writes them to
`.notes/stocktake/<YYYY-MM-DD>/items-<source>.json` as soon as it finishes, so a compacted or
interrupted run resumes from the files. Keep items are included (they fold away in the report).

### Item schema

One JSON object per item. Every field is plain text unless noted.

| Field | Content |
|---|---|
| `id` | `<source>-<nn>`, stable within the run (`skills-07`) |
| `order` | integer; Phase 3 assigns it |
| `source` | source id from the table, or `generation` for generation-audit's line fixes |
| `target` | repo-relative path the item acts on |
| `blob` | `git rev-parse HEAD:<target>` at collection time — the committed content, as the apply worktree sees it (`-` for a file the item creates or one git does not track) |
| `verdict` | the source's verdict word (`Retire`, `Merge into X`, `Improve`, `Append`, …) |
| `alternatives` | array of other verdict words the author may pick instead (optional) |
| `reason` | the source's Reason-quality text: self-contained, decision-enabling on its own |
| `evidence` | array of the No answers, each "question — one-line evidence" |
| `change` | the concrete change: a diff summary, the draft text, or for a skill Improve the skill-creator intent packet (what to fix, which sections, the No list) |
| `impact` | what depends on the target (pointers in rules, agents, MEMORY, other skills) |
| `conflicts` | array of item ids this item collides with (Phase 2 fills it) |

## Phase 2 — Cross-check

Read all items together and record each collision in both items' `conflicts`:

- a Retire / Dissolve / Merge whose target is named by another file (``skill: `x` `` pointers in rules,
  agent definitions, MEMORY.md, other skills) — add the pointer fix to the item's `change`
- a Demote that creates a skill another item also creates or retires
- two items whose `target` is the same file

A collision the change itself resolves (the Retire item also rewrites the pointer) is noted in
`impact`. A collision with two incompatible outcomes keeps both items and says which one wins in
the losing item's `reason`.

## Phase 3 — Publish the report

Order the items by group, then by source table order: **退役** (Retire, Dissolve, Retire-and-absorb)
→ **統合・降格** (Merge, Demote) → **改善・更新** (Improve, Update, Append, Revise, Create) →
**維持** (Keep, Out of scope, Already Covered, Too Specific). Write `order` accordingly. A `docs`
item uses `Update` for an edit and `Create` for a new file.

1. Publish `${CLAUDE_SKILL_DIR}/templates/report.html` as a new Artifact (icon `checklist`) with
   `capabilities: {db: {rules: [{path: "", read: "interact", write: "owner"}]}}`.
2. Write the store with one `ArtifactData` `batch`: every item at `items/<id>`, and `meta/run` =
   `{title: "Harness 棚卸し <date>", created_at: <date -u +%Y-%m-%dT%H:%M:%SZ>, scope: <sources>,
   phase: "proposed", base: <git rev-parse HEAD>}`. The session writes only `items/*` and `meta/run`; `decisions/*` and
   `meta/approval` belong to the author's page.
3. Read back one `ArtifactData` `list` of `items` and check the count.
4. Write `.notes/stocktake/latest.json` = `{url, date, base}`.

Without the Artifact tool (another environment, or an unattended session that lacks it), write the
same items as a Markdown table to `.notes/stocktake/<date>/report.md`, one row per item plus a
`decision` column the author edits, and take the approval in chat. That column stands in for
`decisions/<id>` in Phase 4, and the outcomes go into the same file.

Close with the link, the counts per group, and one line on what to do: change the items to
override, then press 「この内容で承認」. In `--unattended` mode, send the same three lines with
`bash ~/.claude/scripts/notify-slack.sh "<title>" "<body>"` and end the session's turn.

## Phase 4 — Apply

Starts when `meta/approval` exists with `at` later than `meta/run.created_at` (the author pressed
the button), or when the author says in chat that the report is approved. Any other message from
the author is answered without starting the apply.

**Resolve each item's action** from `decisions/<id>` (absent = `accept`):

| decision | action |
|---|---|
| `accept` | apply the item's `verdict` and `change` |
| `Keep` / `skip` | no file change; the ledger records `Keep` or the verdict as skipped |
| another verdict word | apply that verdict; rebuild `change` for it |

A non-empty `note` amends the change. When the note leaves more than one reasonable change, the
item goes to 未決 with the question the note raised.

**Work on a branch.** `git -C ~/.claude worktree add <scratchpad>/stocktake-<date> -b
stocktake/<date> main` — cut from main as it is now, not from `base`, so the freshness check below
sees what changed since the report — and do all edits there.

Work source by source in the source table order, and within a source by `order`, so each source
ends in its own commit. For each item:

1. **Freshness.** Compare `git rev-parse HEAD:<target>` in the worktree with `blob`. On a mismatch,
   re-run that source's per-item judgment on the current file. Same verdict → apply, outcome
   `reevaluated`. Different verdict → outcome `pending` with the new verdict and the reason.
2. **Apply** by target kind:
   - rules, agents, hooks, docs, configs: edit in place following the source skill's own rules
     (rules-stocktake for rules, and so on)
   - skills (Improve, Update, Merge residue, a Demote's new skill): run skill: `skill-creator` on
     its **report path** with the item's `change` as the intent packet
   - Retire / Dissolve: delete the way the source skill says (`git rm` for skills, rules, agents
     and hooks; soft-delete for repo-asset-stocktake), plus the pointer fixes in `change`; for
     Dissolve, an ADR via skill: `adr-writer`
   - a target git does not track (`settings.json`, which wires the hooks): prepare the exact diff
     now, keep the file unchanged, outcome `pending` with the note "after merge"
3. **Compare** the applied diff with the approved `change`. When they differ (a rebuilt change, an
   interpreted note, a reevaluated item), put the full applied diff in `applied_diff`. A target
   under `rules/`, `hooks/` or `CLAUDE.md` whose applied diff differs and that the note does not
   settle goes to `pending` instead of the branch.
4. **Record** the outcome in the store: `ArtifactData` `update` on `items/<id>` with `outcome`
   (`applied` / `reevaluated` / `pending` / `skipped`), `outcome_note`, `applied_diff` when set, and
   `commit`.

Commit once per source with the verify gate passing (`.claude/verify.sh` runs at commit). Update
the source's ledger (the one its skill names, if any) on the branch in the same commit, per that
skill's ledger rules.

## Phase 5 — Completion report and merge

Set `meta/run` `phase: "applied"` and `branch: "stocktake/<date>"`. Reply with the link, the
`git -C ~/.claude log --oneline main..stocktake/<date>` list, every item with an `applied_diff`
(shown in full), every "after merge" item with its exact diff, every `pending` item with its
question, and every other decision made on the author's behalf that changed a file's meaning. The
author's GO covers exactly what this reply shows.

On the author's GO:

1. When main moved since the branch was cut, rebase the branch onto main, re-run verify, and
   report again before going on.
2. `git -C ~/.claude merge --ff-only stocktake/<date>` on main.
3. Remove the worktree.
4. Apply the "after merge" items: copy each untracked target to
   `.notes/stocktake/<date>/<name>.before`, apply the diff the reply showed, and set the item's
   outcome to `applied`.

Pending items carry into the next run's report as ordinary items. Publishing to the public repos
(skill: `harness-sync`) stays with the author.

## Schedule

The monthly unattended run is `scripts/launchd/com.shimomoto.harness-stocktake.plist` (the plist
holds the actual day and hour). It calls `scripts/triage-tick.sh --prompt-file
scripts/launchd/harness-stocktake-prompt.txt`, which finds or spawns the `harness-stocktake`
session in Herdr and sends the prompt; a failed spawn alerts Slack. The author registers it:

```bash
cp ~/.claude/scripts/launchd/com.shimomoto.harness-stocktake.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.shimomoto.harness-stocktake.plist
```

## Single-source use

A sibling stocktake called alone runs this skill's Phases 2–5 with its own items: the same schema,
the same report page, the same apply branch (`stocktake/<date>-<source>`). Phase 2 runs within the
one source. Outside `~/.claude` (repo-asset-stocktake on a project repo), the worktree and branch
live in that repo.

## Related

- skill-stocktake / rules-stocktake / agent-stocktake / hook-stocktake / rules-distill /
  context-sync / repo-asset-stocktake — the sources; each owns its verdict rules and ledger
- skill-creator — its report path applies a skill item without the entry confirmation and the
  read-through, which this skill's two decisions replace
- generation-audit — on a model-generation change it feeds evidence into the sources and uses this
  report for its own line fixes

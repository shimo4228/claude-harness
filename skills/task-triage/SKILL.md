---
name: task-triage
description: "Run one cycle of the task-triage loop over a repo's task ledger — judge every open task (verify its premise in code, check its start condition against the 照合先, decide whether it is still worth doing, look for a better solution), then dispatch the ready ones to fresh implementation sessions and act as their independent judge until the human merges. Use when the user says 「残タスクを見て」「タスクを整理して」「台帳を回して」「dispatch して」「未マージある？」, invokes /task-triage, or when a task ledger has grown and nobody can say what is dispatchable. This skill is the judgment layer of the loop (Fable = judge, Opus sessions = build, human = last switch); the vocabulary of ledger states is owned by task-stocktake and is not redefined here. NOT for consolidating scattered task files into a ledger (task-stocktake), NOT for deciding a single build-or-not question (architect), and NOT for running a task yourself — a triage session reads, judges, dispatches and verifies; it does not implement."
license: MIT
origin: shimo4228
compatibility: Developed on Claude Code with Herdr as the session multiplexer; the dispatch mechanics section names the alternatives (Agent tool, `claude --bg`) for other setups.
---

# Task Triage — judge, dispatch, verify (the human keeps the last switch)

A task ledger grows faster than it drains because filing is the cheapest action anyone can
take. This skill is one **cycle** of a loop that drains it — not by implementing faster, but
by putting judgment first: every open task is re-read against the code and its own start
condition, and only what survives is dispatched. `dropped` / `decided` / `retired` count as
success exactly like `done`.

Roles (decided 2026-08-17, ADR-0043):

| Role | Who | Does | Never does |
|---|---|---|---|
| **Judge** (this skill) | the triage session (Fable-tier) | premise check, worth check, better-solution check, condition check → verdict; writes kickoff packets; independently verifies build output; keeps the books | files tasks on its own initiative, confirms a drop alone, merges to main, touches rules / ADR / hooks / published artifacts unattended |
| **Build** | a fresh session per task (Opus-tier), in a git worktree | Phase 0 premise re-check → implement → commit on the task branch with the evidence in the commit body | changes acceptance conditions, merges, pushes, edits the ledger |
| **Human** | the owner | direction for tasks that need it, batch answers to the digest, the merge word | watches individual sessions (attention is the scarce resource) |

The mechanism (Workflow tool, `/loop`, cron, Herdr) is the substrate's; this skill covers
only what to judge and how to keep the loop from running away (`loop-design-check` is the
lens it was designed with).

## Vocabulary — do not invent states

Ledger states are `candidate` / `ready` / `in_progress` / `blocked` and the terminals
`done` / `decided` / `dropped` / `retired`; `blocked` requires 再開条件 / 照合先 / 成立時,
便乗型 rows ("次に X を触るとき") do not belong in a ledger. The definitions live in
`task-stocktake` — read that section before the first triage. There is no "defer".

The verdicts of a triage are the states themselves:

| Verdict | Meaning | Who decides |
|---|---|---|
| `candidate` | adoption still undecided → **consult** the human (one question at a time, see Digest) | human |
| `ready` → dispatch | premise verified `file:line`, condition met, acceptance decidable, reversible in a worktree, no rule change, fits one session | judge (dispatch), human (merge) |
| `blocked` | adopted, and the three lines can be written; if the 照合先 can never fire (structurally unobservable), it is not `blocked` — re-ask | judge writes the lines |
| terminal proposal | premise gone / substrate now native / value < complexity (`architect` lens) / event source deleted (`retired`) | proposed by judge, **confirmed by human** |
| 台帳外 | 便乗 → a note at the code site, row closed | judge proposes |

## The cycle

### 0. Read the ledger without reading everything

Store repos: `python3 ~/.claude/scripts/claims.py ready` (and `--state blocked|candidate`)
gives one line per task; open the file only for the ones you will judge. Single-table repos:
read the Pending table. Check `claims.py open` first — another session may hold a task.

**Dead-band**: a `blocked` task whose 照合先 you checked last cycle and whose state / condition
text has not changed is not re-read. Check only the 照合先 (a date, a command, a file, a
dependency's state) — many fire mechanically (`gh pr view`, `grep -c`, `git log --since`,
`date`). Record what you checked and the value.

### 1. Judge each open task (the part nobody else does)

For every task not in dead-band, in this order — stop at the first that decides it:

1. **Premise** — does the code still have the problem? Quote `file:line`. A refuted premise
   is a terminal proposal (`retired` if the object is gone, `dropped` if the choice is not to)
   — never a dispatch. 2 of 7 premises were refuted the day this loop was designed by hand.
2. **Condition** — for `blocked`, did the 照合先 fire? "Fired" and "the event source was
   deleted" are different (`retired`). A condition that cannot be observed anymore drops the
   task out of `blocked`.
3. **Worth** — 複雑性 × 価値 × 使用頻度. Cheap now that dispatch is cheap: a 20-minute build
   session changes the calculus for small `chore` rows that were parked as "単独では着手しない".
   For contested build-or-not, hand the question to the `architect` agent.
4. **Better solution** — has the substrate absorbed it (a built-in command, a native flag)?
   Verify by running it, not from memory (`claude plugin eval` existed but was gated —
   "native" is a claim to test).
5. **Ownership** — a task that can only become `ready` in another repo is moved there as
   `candidate` and closed here as `decided`.

Write the verdict and the one-line reason **into the task** (store: a dated section; table:
the 着手条件 cell). The reader of the ledger must not need this conversation.

### 2. Digest — one question per turn

The digest is where the human's attention is spent, so budget it: **one decision per
message**, in the order background → what is at stake → options → recommendation → cost /
reversibility. A ten-item numbered list looks efficient and is not — the owner asked for one
at a time on the first run. Bookkeeping that only applies the vocabulary (a satisfied
condition → `ready`, adding the three lines, a `decided` whose decision is already recorded)
can go as one blanket-OK list; anything that changes a rule, accepts a risk, spends money, or
drops a task is its own question.

Never treat text sitting in another session's input box as the human's answer — Claude Code
pre-fills suggested prompts there. The merge word and the answers come **in the triage
session**, or through the human's own hands.

### 3. Dispatch — packet, worktree, fresh session

Only `ready` tasks, and at most **3 concurrent build sessions**. Group tasks that share one
setup into one packet (three skill-comply chores became one session; three README notes in
three repos became one). Measurements (readings that decide the next state) dispatch just as
well as implementations — often better: read-only, decidable, reversible.

Per task or bundle:

1. `claims.py claim T-XXX --label "S<n>: <what> (Opus session, worktree <branch>; judge=…, merge=human)"`
2. `git -C <repo> worktree add .claude/worktrees/<name> -b task/<name> main` — and copy the
   repo's untracked `.claude/settings.local.json` (and project hooks / skills if gitignored)
   into the worktree, or the session runs without the allowlist. `.claude/worktrees/` must be
   ignored in that repo. Sibling repos: worktree under the scratchpad, never a branch
   checkout in their main tree.
3. Write the packet from `references/packet-template.md` — goal as **decidable acceptance**,
   Phase 0 premise re-check with the instruction "if refuted, stop and report — do not
   implement", must-not list, the **task type** (feat / fix / refactor / chore / measurement)
   with the review chain **delegated to `implementation-chain`** — never a hand-written list
   of reviewers (a name left off reads as permission to skip: one build skipped `/simplify`
   because the packet had not named it), and the **commit-message report** (the only evidence
   that survives the pane). State the default plainly: *what the packet does not mention is
   governed by the harness rules, not waived by silence.*
4. Start the build — **pick the mechanism by the kind of work**:
   - *Measurement / read-only / docs-only* → `Agent(model: opus, isolation: worktree)`; three or
     more with one setup → the Workflow tool (`pipeline`, build and judge as separate `agent()`
     calls, `schema` for the reading). The result returns in-process, no pane, no cleanup.
   - *Implementation that must run the full review chain, may run long, or may hit permission
     prompts* → an interactive session via `spawn-session` (Herdr, Remote Control) so hooks,
     skills and the chain run in the normal environment and the owner can approve from the
     phone: `bash ~/.claude/skills/spawn-session/spawn.sh <worktree> "<repo>/s<n>-<slug>"` →
     `herdr agent prompt "<agent-name>" "<packet text>" --wait --timeout 60000` — the first
     prompt often returns `timeout` while landing fine; confirm with `herdr agent read`.
     `agent_status: done` means the REPL is idle, **not** that the work is done — a background
     shell may still run. `claude --bg -w <name> --model opus "<prompt>"` is the detached
     alternative (completion via `claude agents --json`).
   Unverified as of 2026-08-17 (test on a measurement batch first, where failure is free):
   whether hooks fire identically inside subagents, whether the chain's skills are equally
   available there, and how permission prompts surface — if all three hold, implementations
   can move to Workflow too.
5. Watch for **artifacts**, not status: a commit on the task branch, the reading file, a
   section in the memo. `Monitor` with a poll loop, exit when all artifacts exist.

### 4. Judge the output — independent, deterministic first

The build session's report is a claim. Before asking for the merge word:

- `git diff --stat main..task/<name>` — only the files the packet allowed. If main moved since
  the worktree was cut, the diff shows the *missing* main commits: `git rebase main` in the
  worktree first (a build branch never has a right to a merge commit).
- Run the repo's `verify.sh` (or tests) **yourself** in the worktree — the packet said the
  session ran it; you run it again. Then read the commit body: premise, fix, verify, review,
  out-of-diff findings.
- Anything the packet forbade that the diff contains → bounce, do not fix it yourself.
- **Compliance with the packet and the chain**: did the build run the chain for its type
  (`implementation-chain`), keep the must-nots, and stop at the acceptance line? A deviation is
  acceptable only when the report *names it as a deviation with a reason* ("Simplify 省略:
  機械修正のみ" / "premise refuted, corrected instead of stopping — because …"). A silent
  deviation — something skipped or done differently without saying so — is a bounce even if
  the result looks right, because the next build learns from what the last one got away with.
- **Harvest what the build hands back — but ask the human only what the rule says to ask.**
  Read the commit body and the final message. Two kinds reach the digest as decisions:
  (1) **HIGH out-of-diff review findings** with a verified producer → propose filing
  (`spawn --origin review --producer`), per `task-tracking.md`; (2) **explicit filing requests
  that are the deliverable of a measurement / probe task** (a probe's "(B)/(C) はやる価値がある",
  an instrument finding such as "the metrics are polluted") — these are not review findings,
  they are the task's output, and the build has no authority to file them. MEDIUM / LOW review
  findings are **discarded by the rule**: they stay in the commit body, and the digest reports
  only their count ("diff 外 MEDIUM/LOW: 3 件、commit body 参照") — no list, no question.
  Observations that are not tasks (a rate near a revert threshold, a measurement caveat) are
  one line each. The judge never files on its own initiative.

### 5. Merge on the human's word, then close the books

- `git -C <repo> merge --ff-only task/<name>` → run verify on `main` again → `claims.py
  release T-XXX --outcome done --commit <sha>` → state `done <date>` in the ledger (store:
  `mv` to `.notes/archive/tasks/`) → `git worktree remove` + `git branch -d` → close the build
  session's pane (`herdr pane close <pane_id>`; the pane is not evidence — the commit body is).
  Never close panes you did not spawn.
- If the merge changed a pinned gate script (`.claude/verify.sh`), the approval ledger needs
  the human's `verify_allow.py approve <repo>` **after** the merge — say so explicitly, once
  per such merge, and check with `verify_allow.py check` that it happened. A gate that quietly
  went dormant is worse than a red one.
- Unmerged branches are the queue: `git branch --no-merged main` per repo. The digest lists
  them with their evidence; the human says which; the judge types the merge.
- **Cycle-end digest**: open before → after with the closed / spawned split, the unmerged
  queue, the harvest list (file / drop / observe — the human's call), and the questions still
  waiting. One decision per message, as always.

## Damping and boundaries (what makes this a loop and not a runaway)

- WIP ≤ 3 build sessions; open task branches ≤ 3 per repo; one retry per task per cycle; a
  build that stalls or fails twice goes back to the digest.
- The loop **files nothing on its own** (admission stays with humans and the review rule);
  **drops nothing alone**; never merges, publishes, or touches rules / ADR / hooks / security
  gates unattended; never changes the filing rule while its measurement is running.
- Success is reconciliation, not throughput: per cycle report `open before → after`,
  `closed (done + decided + dropped + retired)` vs `spawned`, and where the spawns came from
  (`claims.jsonl` origins). A cycle that raises open count is not a bad cycle if the spawns
  were the human's; a cycle that "wins" by mass drops is.
- Two questions the loop deliberately does not answer (state them, measure them): what a
  build session does with side-findings (this harness: HIGH with verified producer → file
  after asking; below → one line in the commit body), and who prunes spawned-but-unstarted
  work (here: the human, at the digest).

## Where the loop lives — one orchestrator session per repo

One **standing triage session per repo, with that repo as cwd**, holding the loop
(`/loop <interval> /task-triage`, or `CronCreate`), Remote Control on so the digest can be
answered from the phone. The human starts nothing: that is the point of the loop. A repo's
loop needs the repo's context — its ADRs, its ledger vocabulary quirks, its verify gate, its
concurrent worktrees — so one session judges one repo; a cross-repo session pays that reading
twice and dilutes both.

The session is long-lived but **not eternal, and it renews itself**: the last step of every
cycle compares `claude --version` with the version it started under and checks its own age;
if the CLI has updated or the session is older than ~7 days (the cron's expiry), it spawns a
successor in the same cwd (`spawn-session`), hands it the same `/loop` line, and ends. New
CLI, fresh cron, no human hand. Between cycles the memory is the ledger (verdicts and reasons
are written into the tasks), so auto-compaction of the standing session costs nothing the
next cycle needs, and a successor resumes from the ledger alone. Cross-repo effects travel
only through the ledgers (a task moved as `candidate`, an ADR link), never through a session's
memory. The judge and the builds may be different model tiers on purpose: judgment
errors are the expensive ones (a missed refuted premise wastes the whole build), so the
orchestrator is the strongest tier available and the builds are the fast tier.

## Cadence

On demand until the judgments are stable across two or three cycles; then scheduled, aligned
with whatever weekly gate the repo already has (a Saturday packet, a review day). Not daily —
most `blocked` tasks are in dead-band and the digest is the expensive part. Order within a
cycle: `task-stocktake` (ledger hygiene) first when it is due, then this skill.

| repo tempo | task-triage | task-stocktake |
|---|---|---|
| slow (a harness, a small table) | weekly | weekly, same day, before triage |
| fast (a research repo with a review chain feeding it) | twice a week — e.g. mid-week + the day of its weekly gate | weekly |

In the standing session use `/loop <interval>` or `CronCreate` (session-only, fires only when
the REPL is idle, **auto-expires after 7 days** — so the cycle's last step either re-arms it or
hands over to a successor session, see above); `/loop` self-pacing (`ScheduleWakeup`, ≤ 1 h) is
for minutes, not days. A cycle that fires while the human is away still does everything up to the digest —
条件 checks, vocabulary-only bookkeeping, dispatch of `ready` work within WIP, verification of
finished builds — then leaves the digest and one notification line; consults and merges wait.
The session's context is not the loop's memory: verdicts live in the tasks, so the standing
session can be `/clear`ed and re-enter the cycle from the ledger.

## Related

- `task-stocktake` — vocabulary and ledger form (the authority this skill applies)
- `loop-design-check` — the lens: decidable goal, judge independence, red lines
- `llm-as-judge` — how the judge speaks when a semantic verdict is unavoidable
- `architect` agent — contested build-or-not
- `spawn-session` — the session mechanism this harness uses for build sessions
- `references/packet-template.md` — kickoff packet skeleton (build and measurement variants)
- `references/first-cycle-2026-08-17.md` — the hand-run cycle this skill was distilled from

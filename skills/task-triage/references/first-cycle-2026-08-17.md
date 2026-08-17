<!-- origin: shimo4228 -->
# The first cycle, run by hand — 2026-08-17

The record this skill was distilled from. Numbers as observed; nothing here is a rule.

## Shape of the ledgers before

| repo | form | open | why |
|---|---|---|---|
| contemplative-agent | store (`.notes/tasks/`) | 28 (candidate 6 / blocked 22 / ready 0) | 22 review-origin spawns out of 30 — the review chain fed the ledger 1.3 findings per fix commit |
| harness (`~/.claude`) | single table | 13, all `pending`, ≥ 6 rows of 便乗型 "次に X を触るとき" | the ledger had not been re-triaged after the vocabulary shrank to 4 states (commit 734a502, 2026-08-16) |
| others | — | 0–2 | |

`claims.py ready` returned **nothing** in the store repo: there was no dispatchable work at all
until judgment ran. The bottleneck was judgment, not build capacity.

## What the judgment pass found (41 open tasks)

- 3 `blocked` rows whose dependency had closed weeks earlier (the 08-16 stocktake had even
  marked them in bold — noticing is not the same as flipping the state).
- 2 conditions satisfied by counting (`git log --since`, a metrics file): both `ready`.
- 1 condition satisfied by the clock that morning (usage limit reset) — a task reserved for
  the owner + the strongest model, not for a build session.
- 1 照合先 that could never fire (the field is not rendered in the report it names) → not `blocked`.
- 6 rows closed without code: 2 `decided`, 3 `dropped`, 1 `retired` (event source deleted).
- 1 task filed by the judge that morning turned out to be 便乗型 itself.

Verdicts were asked one at a time after the owner said a ten-question digest was too much.

## Dispatches (10 sessions, 3 concurrent max)

| S | kind | outcome | time |
|---|---|---|---|
| pilot | fix (ruff findings, gate baseline) | merged; found 3 plumbing holes | 6 min |
| S1 | 5 readings (CA), 1 needing local LLM after 19:00 | 2 tasks closed, 1 stayed blocked, 1 lost `blocked` status, 1 got its next step | 11 min + 16 min dry-run |
| S2 | 4 readings (harness) | 2 tasks closed by their own criteria, 1 blocked on an access gate, 1 half done | 15 min |
| S3 | 3 chores bundled (skill-comply) | merged; ADR gained measured numbers ("概ね 1/3" was wrong: 1.23×) | ~35 min |
| S4 | 3 doc notes in 3 repos | merged ×3 | ~10 min |
| S5 | gate fix (harness security) | merged; **packet premise half-refuted**, 2 more bypasses closed, 1 HIGH escalated | ~30 min |
| S6 | doc-drift probe (CA) | task `decided` (no new loop); 3 real drifts fixed; 2 harness follow-ups filed | 17 min |
| S7 | escalated HIGH from S5 | merged; 4 regression tests | ~30 min |
| S8 | 1-line fix that measurement could not justify | merged; found and fixed a crash path on the way | 19 min |
| S9 | 2 harness follow-ups from S6 (freshness sha, sha-based skip) | merged; zsh word-split trap found on the way | ~35 min |
| S10 | research feature (insight abstain + surprise), ADR draft | merged by owner's call **with acceptance 4 unmet** (offline check: abstain 0/20) — recorded as a refutation in ADR-0096, pre-registered reading next weekly | ~3.5 h (deviation named) |
| S11 | instrument fix (tag sandbox rows in metrics), from S2's harvest | merged; full chain incl. cross-model | ~30 min |
| S12 | CA project hook hardening, from S6's harvest | merged; 59 tests; tracked the hook wiring (hooks block only) | ~100 min (deviation named) |
| S13 | docs: usage readers drop sandbox rows, from S11's harvest | merged | ~15 min |

Ledger after the whole cycle: harness 13 → **5** open (all `blocked` but T-012, which waits
for the owner's phone), CA 28 → **17** (1 candidate, 1 ready reserved for the owner, 15
blocked and checked). Filed during the cycle: 6, every one by the owner's word (1 pilot,
1 escalated HIGH with producer, 4 from harvest). Closed: 27. Merges: 13 (harness 8 incl. two
security-gate fixes, CA 4, sibling repos 2). Unmerged queue at close: empty.

## Plumbing holes found by the pilot (fixed or documented)

- `.claude/worktrees/` was not ignored in the harness repo.
- Worktrees lack untracked `.claude/settings.local.json` (allowlist) and gitignored project
  hooks/skills — copy them in.
- `herdr agent prompt --wait` returns `timeout` on the first prompt after spawn while the
  prompt lands; `agent_status: done` only means the REPL is idle (background shells keep
  running). Watch artifacts, not status.
- Claude Code pre-fills a suggested prompt in the build session's input box; the judge once
  read it as the owner's merge instruction. Merge words come in the triage session only.
- A branch cut before main moved needs `git rebase main` before `--ff-only`.
- The harness's own approval ledger had been stale since 2026-07-31: the commit-boundary gate
  was **dormant** for 2.5 weeks and nobody saw it. Merging a gate script requires the human
  to re-approve, every time.

## What the owner said that changed the design

- "PR は PR でややこしい" → no PRs; the unmerged branch list is the queue, evidence lives in
  the commit body, the phone reaches the triage session through Remote Control.
- "一つずつ内容をわかるように説明した上で判断させてくれ" → one decision per message.
- "CA とか .claude とかごとにオーケストレーターセッション立てて loop 実行" → one triage session
  per repo, cwd = repo, long-lived.
- "実装セッションがタスク起票していいかって聞いてきてるのを無視してる" → the harvest step.
- "信用するからね" — after the vocabulary-only bookkeeping was explained once, the owner
  delegated it wholesale; the trust was granted to *explained* mechanics, not to speed.

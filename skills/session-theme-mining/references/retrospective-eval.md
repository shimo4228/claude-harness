<!-- origin: shimo4228 -->
# Retrospective Evaluation

Run on 2026-08-23 against local parent sessions. Each cutoff is immediately before the first git
commit that added the named Japanese article. The article body was not used as input; its slug is
only the ground-truth label. Sessions whose prompt quoted or reviewed the target article body were
ignored when judging recovery.

| Ground-truth label | Cutoff | Pre-cutoff human anchors | Result |
|---|---|---|---|
| `claude-code-claudemd-excludes` | 2026-08-02T12:25:25Z | Codex `019fc174-c464-7222-9ae9-d0b544bf2161`, `019fc183-0958-7561-9c6c-9e98198488fe` | Separate-harness configuration leakage and the measured exclusion path were recoverable |
| `ai-review-task-loop` | 2026-08-16T13:38:12Z | Claude `2de10941-64be-4fad-80b5-75dc14df6e5e`, `7101a9cd-feb8-4295-9e4d-eb7f9d758d4e` | Review-driven deferral and task growth were recoverable as one unresolved question |
| `transcript-not-ledger` | 2026-08-21T13:15:34Z | Claude `b8b918fd-d1fb-4d2d-9ddb-26845041a4a3`, `8c8f85c8-1022-43f4-9a8b-9224e2c0c27d` | The tension between harness artifacts, evidence ledgers, and primary session history was recoverable |

The hardened catalog receipts for the three cutoffs covered 485, 681, and 745 parent sessions,
respectively, with both Claude and Codex represented. Each run discovered 1,364 source files,
reported two oversized-line warnings, zero malformed rows, zero read errors, and zero byte-budget
skips. This is a retrospective discoverability check, not proof that future candidates will be worth publishing;
the author gate remains necessary.

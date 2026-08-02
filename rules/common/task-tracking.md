<!-- origin: shimo4228 -->
<!-- rationale: ADR-0035 — 台帳の手順を task-stocktake へ移し、repo ごとの正本 path だけ常駐 -->
<!-- review-when: harness native task store または repo の台帳 path を変えた時 -->
# Task Tracking

Pending task の正本は repo ごとに1つ。既存の `.notes/TASKS.md` があればそれを使う。
新設・統合・archive の手順は skill: `task-stocktake` が持つ。

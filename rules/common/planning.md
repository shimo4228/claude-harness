<!-- origin: shimo4228 -->
<!-- rationale: ADR-0035 — 思考手順と reviewer 名簿を skill へ移し、実行入口と機械ゲートの配線だけ常駐 -->
<!-- review-when: search-first / implementation-chain / verify hook の入口を変えた時 -->
# Planning Wiring

- 既存解がありうる新機能・依存追加・自作 utility の前は skill: `search-first`
- 実装 chain の種別と reviewer 条件は skill: `implementation-chain`
- commit 前は `hooks/review-chain-notice.sh` が Review / Verify の実行確認だけを通知する

Verify の正本は repo の `.claude/verify.sh`。無ければ skill: `verify-bootstrap` で作る。
完了前に doc sync と `git status` を確認する。commit 境界では PreToolUse hook が staged diff に
同じ機械ゲートを適用する。

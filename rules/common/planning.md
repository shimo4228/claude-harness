<!-- origin: shimo4228 -->
<!-- rationale: ADR-0035 — 思考手順と reviewer 名簿を skill へ移し、実行入口と機械ゲートの配線だけ常駐。ADR-0085 — plan を repo に残る記録として扱う -->
<!-- review-when: search-first / implementation-chain / verify hook の入口を変えた時。plan mode か plansDirectory の挙動が変わった時 -->
# Planning Wiring

- 既存解がありうる新機能・依存追加・自作 adapter / client / utility の前は skill: `search-first`
  を Library / tool choice の問いとして回す（叩く endpoint でなく、それを担う定評のある library を問う）。
  採用する依存は skill: `implementation-chain` の dependency intake を通す
- judge-tier セッションでの実装は build-tier への dispatch が既定 — 実行者の決定と例外は
  skill: `implementation-chain`（三役の正本: ADR-0043）
- 実装 chain の種別と reviewer 条件は skill: `implementation-chain`
- commit 前は `hooks/review-chain-notice.sh` が Review / Verify の実行確認だけを通知する
- plan は repo の `docs/plans/` に残る記録（ADR-0085。起点は cwd なので plan mode は repo の root で
  起動する）。公開可能な書き方を既定にし、機微はリンク先へ、パスは `~/` で書く。承認した plan は
  実装の最初の commit に単独で入れ（`docs(plan): <slug>`）、後続 commit（本文に `Plan:` 行）と ADR / RFC からリンクする

Verify の正本は repo の `.claude/verify.sh`。無ければ skill: `verify-bootstrap` で作る。
完了前に doc sync と `git status` を確認する。commit 境界では PreToolUse hook が staged diff に
同じ機械ゲートを適用する。

<!-- origin: shimo4228 -->
<!-- rationale: ADR-0035 — 思考手順と reviewer 名簿を skill へ移し、実行入口と機械ゲートの配線だけ常駐。ADR-0085 — plan を repo に残る記録として扱う。ADR-0086 — plan の前の調査を gate で強制する。ADR-0087 — plan の既定経路を html-plan にする -->
<!-- review-when: search-first / implementation-chain / verify hook の入口を変えた時。plan mode か plansDirectory の挙動が変わった時。html-plan の SKILL.md（## Words・pack.mjs の出力）が変わった時 -->
# Planning Wiring

- 既存解がありうる新機能・依存追加・自作 adapter / client / utility の前は skill: `search-first`
  を Library / tool choice の問いとして回す（叩く endpoint でなく、それを担う定評のある library を問う）。
  採用する依存は skill: `implementation-chain` の dependency intake を通す
- judge-tier セッションでの実装は build-tier への dispatch が既定 — 実行者の決定と例外は
  skill: `implementation-chain`（三役の正本: ADR-0043）
- 実装 chain の種別と reviewer 条件は skill: `implementation-chain`
- commit 前は `hooks/review-chain-notice.sh` が Review / Verify の実行確認だけを通知する
- plan は repo の `docs/plans/` に残る記録（ADR-0085。起点は cwd なので session は repo の root で
  開く）。公開可能な書き方を既定にし、機微はリンク先へ、パスは `~/` で書く。承認した plan は
  実装の最初の commit に単独で入れ（`docs(plan): <slug>`）、後続 commit（本文に `Plan:` 行）と ADR / RFC からリンクする
- plan の依頼（plan mode、または「プランして」等の plan を頼むプロンプト）では `hooks/research-gate.sh` が、
  `researcher` の調査 report（`docs/plans/research/`）ができるまで plan ファイルへの書き込みを止める。調査は外部（skill: `search-first` の Full）か内部
  （再現手順と原因の `file:line`）（ADR-0086）
- plan は skill: `html-plan` で `docs/plans/<slug>.html` に書き、report にリンクする（ADR-0087）。plan mode は
  著者が自分で入れたときだけ使う。散文は日本語で `<html lang="ja">` にし、SKILL.md の `## Words`（STE 英語）は
  適用しない。claim の長さは約 30 字を目安にする
- pack は `node <skill dir>/runtime/pack.mjs <plan> --root <repo> --artifact`。隣に出る `<slug>.artifact.html`
  を Artifact tool で private 公開する（副産物 `*.packed.html` / `*.artifact.html` は repo の .gitignore で外す）。claim が「。」で終わる警告（pack.mjs:221）は読み飛ばす
- 承認は Respond の貼り戻し。plan に `doc-ask`「実行者の決定」を置く（plan mode の `hooks/plan-executor-notice.sh` の代わり）

Verify の正本は repo の `.claude/verify.sh`。無ければ skill: `verify-bootstrap` で作る。
完了前に doc sync と `git status` を確認する。commit 境界では PreToolUse hook が staged diff に
同じ機械ゲートを適用する。

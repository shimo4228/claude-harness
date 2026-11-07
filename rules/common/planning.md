<!-- origin: shimo4228 -->
<!-- rationale: 思考手順と reviewer 名簿は skill が持ち、ここには実行入口と機械ゲートの配線だけ常駐する。plan は repo に残る記録として扱い、調査が要るときはその前に調べ、実行者は model とタスクの文脈で決める。plan mode と調査手順の差し込みは外した — 着手前に承認と手順を重ねる機構は Claude を保守的に寄せる（2026-11-07 著者指示） -->
<!-- history: docs/decision-history/0035, 0085, 0086, 0096, 0100, 0102 -->
<!-- review-when: search-first / implementation-chain / verify hook の入口を変えた時。plan mode か plansDirectory の挙動が変わった時 -->

# Planning Wiring

- 既存解がありうる新機能・依存追加・自作 adapter / client / utility の前と、外部の手法・ツール・仕様を記憶から
  述べかけたときは skill: `search-first`（叩く endpoint でなく、それを担う定評のある library を問う。rule
  `knowledge-staleness` の実行入口）。採用する依存は skill: `implementation-chain` の dependency intake を通す
- 実装 chain の種別・reviewer・実行者は skill: `implementation-chain`。実装はタスクの文脈を持つ session が行い、
  Fable の session の実装は Opus への委譲が既定（経緯 0100）
- plan は repo の `docs/plans/` に残る記録（経緯 0085。起点は cwd なので session は repo の root で開く）。
  公開可能な書き方を既定にし、機微はリンク先へ、パスは `~/` で書く。承認した plan は実装の最初の commit に
  単独で入れ（`docs(plan): <slug>`）、後続 commit（本文に `Plan:` 行）と判断の経緯 / RFC からリンクする
- plan は `docs/plans/<slug>.md` に直接書き、著者の一言で承認を取る。調査が要るときだけ書く前に調べる — 外部は
  skill: `search-first` の Full（`researcher` が統合）、内部は再現手順と原因の `file:line`（主ループが書く）で、
  report は `docs/plans/research/` に置いて plan からリンクする（経緯 0086、0096、0102）
- Verify の正本は repo の `.claude/verify.sh`（無ければ skill: `verify-bootstrap` で作る）。完了前に doc sync と
  `git status` を見る。cwd の外で `~/.claude` を編集したときは `git -C ~/.claude status` も見て、触ったパスだけを
  `~/.claude` 側で commit する（`hooks/harness-commit-notice.sh` が 1 回知らせる）

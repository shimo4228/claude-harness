# RFCs

この repo の提案と作業項目の公開台帳 — 1 エントリ 1 ファイル `NNNN-slug.md`、ID は
`RFC-NNNN`。フル RFC の提案から小さな作業項目まで同居する。**state は各ファイルの
frontmatter が唯一の正本**。

起票の手順と規約（足切り・採番・様式・公開規約）の正本は
[skill: rfc-writer](../skills/rfc-writer/SKILL.md)、状態語彙は
[skill: task-stocktake](../skills/task-stocktake/SKILL.md)、判断は
[ADR-0049](../docs/adr/0049-unify-task-ledger-into-public-rfcs.md)。規約本文をこの
README には書かない（複製は drift する）。

| # | Title |
|---|---|
| [0001](0001-public-rfcs-rollout.md) | 全 repo への公開 rfcs/ 台帳の展開 |
| [0002](0002-test-edit-guard-hook.md) | fix 中の test ファイル編集ブロック hook |
| [0003](0003-standardize-ledger-state-vocabulary.md) | 台帳状態語彙の全域標準化（draft / accepted / obsoleted 等へ） |
| [0004](0004-zenodo-metadata-edit-procedure.md) | Zenodo published-record metadata edit の手順化・自動化検討 |
| [0005](0005-review-to-lint-rollout-ledger.md) | review-to-lint 水平展開の候補台帳（12 候補・発火条件・やらない判定） |
| [0006](0006-context-sync-evidence-script.md) | context-sync チェックリストの evidence script 抽出と薄化 |
| [0007](0007-agent-stocktake-lint-remnants.md) | agent-stocktake の harness_lint 未カバー機械項目の script 化 |
| [0008](0008-url-liveness-shared-checker.md) | URL liveness 検査の共通部品新設 |
| [0009](0009-skill-stocktake-usage-and-url-script.md) | skill-stocktake の usage 集計 4 補正規則の script 化と URL 検査接続 |
| [0010](0010-learn-eval-overlap-enumeration.md) | learn-eval の重複照合 2 項目の機械列挙化 |
| [0011](0011-citation-audit-rate-limit-retry.md) | citation_audit の 429 リトライを停止・報告型へ（policy signal 規約整合） |
| [0012](0012-public-mirror-llms-txt-dangling-links.md) | 公開ミラー llms.txt のリンク切れ — harness-sync 生成不整合の修正 |
| [0013](0013-verify-sh-untracked-file-blind-spot.md) | verify.sh の git ls-files 盲点 — 未 commit 新規ファイルも lint 対象に |
| [0014](0014-name-stem-gate-to-harness-lint.md) | agent name=stem 検査を harness_lint の gate へ移設 |
| [0015](0015-adr-numeric-consistency-evidence.md) | ADR 数値整合の hybrid 検査を adr_lint へ追加 |
| [0016](0016-agent-tool-build-path-hook-parity.md) | Agent tool 実装経路の hooks/skills 発火同一性の実測検証 |
| [0017](0017-skill-description-residency-optimization.md) | skill listing の常駐コストを description 側から削る（本数軸の実測による差し替え） |
| [0018](0018-description-behavior-contamination.md) | description の挙動汚染（第 2 の rules 層化）の検査・撤去 |
| [0019](0019-relocated-source-skill-repo-sync-scripts.md) | 移設済み正本を指す 3 skill repo の sync script source 更新 |
| [0020](0020-rust-for-resident-infra.md) | 常駐 infra の Rust 化 — 移行でなく発火条件つき greenfield pilot 方針 |
| [0021](0021-verify-full-red-growth-fable-ty.md) | verify.sh full が main で赤 — growth-fable tests の ty 診断 30 件を型付きアクセスで解消 |
| [0022](0022-search-first-verdict-redesign.md) | search-first の verdict 形と探索範囲の再設計（package 一軸で Build に落ち、学びを運ばない） |
| [0023](0023-bats-absolute-home-hook-paths.md) | bats が hook を $HOME 絶対パスで source し worktree の verify が main checkout を検査する — repo 相対へ |
| [0024](0024-typesafe-jev-as-offload-for-max-quota.md) | TypeSafe Jev で判定を Max 枠の外へ逃がす — 探索と実測は済み。候補 2（skill ルーター）のみ 2026-09-21 着手、他候補は Fable 枠の回復待ち |
| [0025](0025-jev-decision-contract-registry.md) | Jev 判定を版付きで貯める registry — 質問文ごと残し、閾値はデータが溜まってから引く |
| [0026](0026-jev-agent-trace-sensor.md) | 走り終わりの done / stuck を Noul で分ける sensor — loop-design-check の semantic 側の空白を埋める |
| [0027](0027-publish-corrections-and-evals-umbrella.md) | 指摘と Eval を照合可能に継続公開する — 2026-09-27 の調査結果と方向（親） |
| [0028](0028-correction-commit-trailers.md) | 指摘を起きた瞬間に commit へ残す規約（指摘: / Trigger: / Expect:）— 記事で 2 週間試す |
| [0029](0029-carry-commit-trailers-to-public-mirror.md) | 公開ミラーへ commit 本文の trailer（Review: / Context: / Decision: 等）を運ぶ |
| [0030](0030-eval-cards-for-ready-instruments.md) | Eval カード — 公開できる計器 5 本を設計・生値・未測定・故障つきで出す |
| [0031](0031-reader-agent-verifiability-probe.md) | 読者役エージェントによる照合を常設の計器にする — 公開物だけで確認できた環を数える |
| [0032](0032-defects-found-in-2026-09-27-research.md) | 2026-09-27 の調査で見つけた不具合 3 件（review-when-watch 未稼働・件数の食い違い・注記の順序） |
| [0033](0033-allocate-legacy-plans-to-repos.md) | 過去の plan（global の legacy 置き場、253 本）を作られた repo の plan 置き場へ振り分ける |
| [0034](0034-llm-as-judge-definition-search.md) | llm-as-judge の判定定義を仮説として扱う — 問いと verdict 境界の候補を、固定した下流評価で比べる外側ループ |

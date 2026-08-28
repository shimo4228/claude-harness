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

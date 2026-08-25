# RFCs

この repo の提案と作業項目の公開台帳（1 エントリ 1 ファイル、`NNNN-slug.md`、ID は
`RFC-NNNN`）。フル RFC の提案から小さな作業項目まで**同居する** — 別置き場を作らない。
様式・状態語彙・規約の正本は skill: `task-stocktake`、判断は
[ADR-0049](../docs/adr/0049-unify-task-ledger-into-public-rfcs.md)。

状態は各ファイルの frontmatter `state:` が**唯一の正本**（`candidate` / `ready` /
`in_progress` / `blocked` / `done` / `decided` / `dropped` / `retired`。この index には
複製しない — 二重記録は drift する）。この 8 語は**台帳の語彙であって RFC 標準語彙では
ない** — RFC 標準（Rust / IETF）は文書内 state を持たない。本文末尾の `## Status` 節が
標準語 gloss つきで現在地を語り（IETF「Status of This Memo」型）、`## Next action` が
tracking 層（何があれば動くか）を持つ。本文の他の節は Rust RFC テンプレ準拠。終端
エントリも削除・退避せずここに残る — 却下理由ごと残るのが公開判断記録の価値。状態別の
列挙は `python3 ~/.claude/scripts/claims.py ready [--state <state>]`。

| # | Title |
|---|---|
| [0001](0001-public-rfcs-rollout.md) | 全 repo への公開 rfcs/ 台帳の展開 |
| [0002](0002-test-edit-guard-hook.md) | fix 中の test ファイル編集ブロック hook |
| [0003](0003-standardize-ledger-state-vocabulary.md) | 台帳状態語彙の全域標準化（draft / accepted / obsoleted 等へ） |

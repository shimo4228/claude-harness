# ADR-0001: ECC スキル管理ポリシー

## Status
accepted

## Date
2026-03-08

## Context

ECC (Everything Claude Code) からスキル・コマンド・エージェントを導入しつつ、自作スキル（origin: original）も並行して管理している。ECC のアップデート時にローカルカスタマイズが上書きされる問題や、diff 比較が困難になる問題が繰り返し発生していた。

## Decision

以下の3つのポリシーを制定した:

1. **origin: original スキルは上書き禁止** — search-first, skill-stocktake 等、自分がオリジネーターのスキルは ECC アップデートで上書きしない。ECC 側の改善は手動チェリーピックで取り込む

2. **ECC スキルは内容変更しない** — origin: ECC のスキル/コマンドは編集禁止。アップデート時の diff 比較を容易にするため

3. **ECC コマンド拡張パターン** — ECC コマンドの動作を拡張したい場合、元ファイルに `disable-model-invocation: true` を追加して無効化し、独自コマンドを新設する（例: `/learn` → `/learn-eval`）

## Alternatives Considered

- **ECC スキルを自由に編集する** — diff が複雑になりアップデート追従が事実上不可能に
- **ECC を使わず全て自作する** — 車輪の再発明。ECC の知見を活用できない
- **fork して独自メンテナンス** — メンテナンスコストが高すぎる

## Consequences

- ECC アップデートが `diff` 一発で差分確認できる
- 自作スキルの独自性が保護される
- コマンド拡張時に2ファイル（無効化 + 新設）が必要になるオーバーヘッド
- origin フィールドの一貫した付与が必須（rules/common/skills.md で規定）

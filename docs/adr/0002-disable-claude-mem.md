# ADR-0002: claude-mem プラグイン無効化

## Status
accepted

## Date
2026-03-08

## Context

claude-mem (thedotmack-claude-mem) プラグインを導入したが、既存の記憶管理システム（MEMORY.md + learned skills + rules/）との重複が判明した。

具体的な問題:
- 自動保存はされるが自動検索・活用の仕組みがない
- セッション開始時のインデックス注入は「目次だけの百科事典」状態
- MEMORY.md + learned skills + rules/ で記憶管理が十分カバーされている

## Decision

`settings.json` で `claude-mem@thedotmack-claude-mem: false` に設定し無効化した。プラグインファイル・DB（~/.claude-mem/）は残してあるので再有効化は可能。

## Alternatives Considered

- **claude-mem をメインの記憶システムにする** — 自動検索がないため、蓄積しても活用できない
- **両方併用する** — 同じ情報が2箇所に分散し、どちらが正なのか曖昧になる
- **claude-mem を改善して使う** — プラグインのコードを fork する必要があり、コスト対効果が合わない

## Consequences

- 記憶の一元管理（MEMORY.md + learned skills）が維持される
- claude-mem のストレージ容量を消費しなくなる
- 将来 claude-mem に自動検索機能が追加されたら再評価する価値がある

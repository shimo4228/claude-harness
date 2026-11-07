# ADR-0005: kimi-delegation.md ルール退役

## Status
accepted

## Date
2026-03-13

## Context

`rules/common/kimi-delegation.md` は Claude Code + Kimi K2.5 のハイブリッド委任フローを定義していた。Kimi の実装力を活かしつつ Claude が品質主権を維持する、フェーズ分割型のワークフローだった。

退役理由:
- Kimi Code の週次クォータ制限（Moderato プラン: 2048 req/週）により、日常的な委任が現実的でなくなった
- Claude Code 単体の能力向上（Opus 4 以降）で委任の必要性が低下
- Spec 作成 → Kimi 実行 → Claude レビューのオーバーヘッドが、直接実装のコストを上回るケースが増えた

## Decision

`rules/common/_archived/kimi-delegation.md` に移動して退役とした。Kimi 連携のコマンド（kimi-dispatch, kimi-spec）はローカルに残し、必要時に手動で使う形にした。

## Update (2026-04-19): Kimi 連携を完全撤去

「必要時に手動」として残した Kimi 連携も実使用なく、ハーネスから Kimi 関連資産を完全撤去した:

- `skills/kimi-spec/`, `skills/kimi-dispatch/` — delegation workflow skill
- `.handoff/specs/spec-001-kimi-plan-integration.md` — 過去の統合設計メモ
- `bin/kimi-wrapper.sh`, `bin/kimi-profile-switch.sh` — Kimi CLI ラッパー
- `bin/_swarm-backup/` — 旧 swarm 実装のバックアップ
- `skills/learned/kimi-peer-review-for-strategy.md` — peer review パターン
- `bin/` ディレクトリ自体 — 全て Kimi 用で空になったため撤去

理由: Claude Code 単体 (Opus 4.7 1M context + MAX Plan) で十分な能力を持つようになり、Kimi を呼び出す状況が事実上発生しなくなった。将来再評価したい場合は git 履歴から復元可能。

## Alternatives Considered

- **ルールとして残す** — 毎セッション読み込まれるがほぼ使わない。コンテキスト消費が無駄
- **完全削除** — 将来 Kimi のクォータ緩和や能力向上があった場合に参照できなくなる

## Consequences

- rules/ の読み込みコストが約120行分削減
- Kimi 連携は「ルールとしての自動適用」から「コマンドとしての手動呼び出し」に格下げ
- 将来の再評価が可能な形で保存

# ADR-0006: ECC へのコントリビューション終了

## Status
accepted

## Date
2026-03-24

## Context

ECC (Everything Claude Code) が GitHub App + SaaS ($19/seat) として商用化した。これまで MIT ライセンスで5スキル/コマンドをコントリビュートしてきたが、状況が変わった:

1. 無償のコントリビューションが商用プロダクトの一部として販売される構造になった
2. 本業の就業規則（兼業・副業・営利企業への従事制限）上、商用プロジェクトへの継続的な無償貢献はグレーゾーン
3. 自作スキル群（search-first, skill-comply, context-sync 等）は自分のハーネスで使うことが本来の目的であり、ECC への貢献は副次的だった

## Decision

1. **PR #724 (skill-comply) が最後のコントリビューション** — 2026-03-20 にマージ済み
2. **PR #827 (context-sync) を取り下げ** — 2026-03-24 に close。コメント: "Withdrawing due to personal circumstances."
3. **今後の新規 PR は出さない**
3. **自作スキルはローカルで使い続ける** — 自分のハーネスでの利用に影響なし
4. **ECC のアップデートは消費者として取り込む** — 有用な更新は引き続き利用

## Alternatives Considered

- **コントリビューションを続ける** — 商用化された以上、無償貢献の意味が変わった。就業規則上のリスクもある
- **即座に全 PR を取り下げる** — 既にマージ済みのものは取り下げられない。未マージの #827 のみ close した
- **有償コントリビューターとして契約する** — 本業の兼業制限に抵触する可能性が高い

## Contribution Record

全 11 PR マージ済み:

### AKC (Agent Knowledge Cycle) スキル

| Name | Type | PR | Purpose |
|------|------|----|---------|
| search-first | Skill | #262 | 実装前に既存ライブラリ/ツールを調査 |
| learn-eval | Command | #263, #360 | セッションからの学習パターン抽出 + 品質ゲート |
| skill-stocktake | Skill | #265, #361 | スキル品質の自動監査 |
| rules-distill | Skill | #561 | スキル群から共通原則を蒸留してルールに昇格 |
| skill-comply | Skill | #724 | スキル/ルールの行動遵守率を自動計測 |

### パターンスキル

| Name | Type | PR | Purpose |
|------|------|----|---------|
| cost-aware-llm-pipeline | Skill | #219 | LLM API コスト最適化パターン |
| swift-protocol-di-testing | Skill | #220 | Protocol ベース DI によるテスタブル Swift |
| swift-actor-persistence | Skill | #221 | Actor によるスレッドセーフな永続化 |
| content-hash-cache-pattern | Skill | #222 | SHA-256 コンテンツハッシュキャッシュ |
| regex-vs-llm-structured-text | Skill | #223 | 正規表現 vs LLM の判断フレームワーク |

### Origin Tracking

origin フィールドによるスキル出自管理の仕組み自体も発案・実装した。

## Consequences

- 就業規則上のリスクがなくなる
- 自作スキルを ECC のリリースサイクルに合わせる必要がなくなり、自由に改変できる
- ECC コミュニティとの関係は「利用者」として継続
- 自作スキルを公開したい場合は、自分のリポジトリで独立して行う

## Update (2026-04-19): ecc-contribute skill 退役

コントリビューション終了に伴い、ワークフロー skill 自体も不要となったため削除:

- `skills/ecc-contribute/` — fork health check / candidate selection / PR creation ワークフロー

再開時は git 履歴から復元可能。

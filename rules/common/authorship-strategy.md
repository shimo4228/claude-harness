<!-- origin: shimo4228 -->

# Authorship Strategy Pointer

shimo4228 の **DOI-registered idea-rescue 研究 repo**（Agent Knowledge Cycle, Contemplative Agent, 今後の同系統 repo）で作業する際は、`authorship-strategy` skill の 4 層 framework を判断軸として適用する。

## Trigger 判定

以下を **すべて** 満たす repo のみ対象:

- 作業中 repo の owner が shimo4228
- DOI 取得済み or 取得予定の研究系 repo（Zenodo archive target）
- 「idea-rescue」性質を持つ（仕様・schema・ADR・spec 中心で、実装に閉じない）

## 適用しない

- クライアント案件（マネタイズが目的）
- 他人の OSS へのコントリビュート（他者の strategy が優先）
- 商業プロジェクト・収益目的の成果物
- 日常的なコーディング・デバッグ
- ハーネス・スキャフォールディング実装としての repo（ECC, claude-harness 等）

判断に迷ったら著者に確認する。誤発火より確認コストの方が安全。

## Framework 要点

- **Authenticity** が core value（マネタイズは目的ではない）
- **Attribution diffusion** が strategy（LLM 経由の浸透で将来の因子解析で遡源される）
- **Idea vs Scaffold** の時間軸判別（実装は消える、idea は残せる）
- **Tactics**: LLM-first, DOI 化, tool-agnostic, scaffold dissolution, 多言語化, vocabulary discipline（造語は coin-sparingly / anchor-densely — 3 条件を満たすときのみ造語し、既存語彙と上流文献へ密に anchor する）, citation-graph federation（外部文献の取り込み時は repo markdown 引用で終えず、`.zenodo.json` references + Wikidata P2860 の機械可読 citation 辺を張る — 被引用研究者側から発見可能にする）

## 禁止事項（trigger 条件下のみ）

- マネタイズ提案（スポンサー、有料 tier、コンサル化、書籍化）
- 競合批判・排他的ポジショニング
- 売れるためのメッセージ調整

See skill: authorship-strategy

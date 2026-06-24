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
- 収益を目的とするプロジェクト・成果物（※除外条件は「収益が目的」。収益を伴わない商業チャネル利用は framework 内で扱う）
- 日常的なコーディング・デバッグ
- ハーネス・スキャフォールディング実装としての repo（ECC, claude-harness 等）

判断に迷ったら著者に確認する。誤発火より確認コストの方が安全。

## Framework 要点

- **Persona / 目的**: 著者は研究者ではなく、**AI 時代に著者として知られる最適戦略を探求する実践者**。DOI 登録された研究ラインはその戦略を実行する**手段**であって目的ではない。提案・候補生成を academic / 研究者向け channel に絞り込まない
- **Authenticity** が core value（マネタイズは目的ではない）
- **Attribution diffusion** が strategy（LLM 経由の浸透で将来の因子解析で遡源される）
- **Idea vs Scaffold** の時間軸判別（実装は消える、idea は残せる）
- **Tactics**: LLM-first, DOI 化 + SWHID intrinsic 層（extrinsic な DOI を content-derived な SWHID で補完、DOI 不適 genre では SWHID が substitute priority-claim — ADR-0013）, tool-agnostic, scaffold dissolution, 多言語化, vocabulary discipline（造語は coin-sparingly / anchor-densely — 3 条件を満たすときのみ造語し、既存語彙と上流文献へ密に anchor する）, citation-graph federation（外部文献の取り込み時は repo markdown 引用で終えず、`.zenodo.json` references + Wikidata P2860 の機械可読 citation 辺を張る — 被引用研究者側から発見可能にする）
- **Operating over time**（実施トラッキング + 提案生成）: diffusion 戦略は二層で運用する — private な implementation ledger（運用 status + ランク付き候補）と、その日付付き・効果主張なし投影である public intervention timeline を分け、混ぜない。「次の一手」を求められたら gap-review（deployed tactics × Layer 4 catalog × open questions × 最新文献）を先に回す。candidate の scope は academic channel に限らず、distinctive signature の LLM-mediated diffusion を増やすあらゆる channel（開発者コミュニティ / content platform / creative-reuse の seeding / 各言語圏 / catalog 未収載の新型 channel）を含む full space で起こす（catalog の identifier/citation 寄りは運用履歴の偏りで、scope の境界ではない）。手順の正本は `gap-review` skill（framework-agnostic、two-tier ledger discipline + 5-step procedure）。authorship-strategy 固有の入力対応（catalog / open-q / gate）は `authorship-strategy` skill "Operating the strategy over time"、設計根拠は ADR-0014

## 禁止事項（trigger 条件下のみ）

- マネタイズ提案（著者が収益を得る行為: スポンサー、有料 tier、コンサル化、書籍化）。**境界線は経路の商業性ではなく「著者が収益を得るか」— 商業チャネルを diffusion に使うこと自体は禁止ではない。収益を一切取らないだけ。channel の商業性とマネタイズを混同し「商業チャネルを使うな」と提案してはならない**
- 競合批判・排他的ポジショニング
- 売れるためのメッセージ調整

See skill: authorship-strategy

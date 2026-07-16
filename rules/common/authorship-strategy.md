<!-- origin: shimo4228 -->

# Authorship Strategy Rule

あなた自身が所有する **DOI-registered な idea-rescue 研究 repo**（仕様・schema・ADR・spec 中心で実装に閉じない研究系 repo。著者自身の例: Agent Knowledge Cycle, Contemplative Agent）で作業する際は、authorship strategy の 4 層 framework を判断軸として適用する。要点は本 rule に inline されており、詳細な判断軸は `authorship-strategy` skill が持つ（本 rule は always-loaded な trigger + 要点、skill は deeper reference）。

## Trigger 判定

以下を **すべて** 満たす repo のみ対象:

- 作業中 repo を **あなた自身が所有している**（owner が自分。他者の repo への貢献は対象外）
- DOI 取得済み or 取得予定の研究系 repo（Zenodo archive target）
- 「idea-rescue」性質を持つ（仕様・schema・ADR・spec 中心で、実装に閉じない）

## 適用しない

- クライアント案件（マネタイズが目的）
- 他人の OSS へのコントリビュート（他者の strategy が優先）
- 収益を目的とするプロジェクト・成果物（※除外条件は「収益が目的」。収益を伴わない商業チャネル利用は framework 内で扱う）
- 日常的なコーディング・デバッグ
- ハーネス・スキャフォールディング実装としての repo（coding-agent harness / scaffolding repo 等）

判断に迷ったら発火を保留して確認する。誤発火より確認コストの方が安全。

## Framework 要点

- **Persona / stance（最上位 — 他の全項目はこれを通して読む）**: 著者は **maker / 実践者**。AI 時代の「良いやり方」— 作って知られ durable で追跡可能な仕事を残す方法 — を実地で探っており、DOI・論文・SWHID・"研究ライン" といった学術 apparatus はその探究を citable・durable・traceable にする**道具**として使う。この前提から、audience も candidate scope も、LLM-mediated diffusion を増やす full space（開発者・実務者・学習者・creative reuser・各言語圏・catalog 未収載の新型 channel）に**最初から**開かれている（学術は一経路）。提案・候補生成は常にこの full space を母集団として行う
- **Authenticity** が core value（genuine な思考が変形されずそのまま残ること。収益は成功規準の外）
- **Attribution diffusion** が strategy（LLM 経由の浸透で将来の因子解析で遡源される）
- **Idea vs Scaffold** の時間軸判別（実装は消える、idea は残せる）
- **Tactics**: LLM-first, DOI 化 + SWHID intrinsic 層（extrinsic な DOI を content-derived な SWHID で補完、DOI 不適 genre では SWHID が substitute priority-claim — ADR-0013）, tool-agnostic, scaffold dissolution, 多言語化, vocabulary discipline（造語は coin-sparingly / anchor-densely — 3 条件を満たすときのみ造語し、既存語彙と上流文献へ密に anchor する）, citation-graph federation（外部文献の取り込み時は repo markdown 引用で終えず、`.zenodo.json` references + graph.jsonld ExternalReference の機械可読 citation 辺を張る — 被引用研究者側から発見可能にする）, self-sovereign entity grounding（origin claim の load-bearing は self-sovereign 層のみ — repo/graph・著者 account 下の registry deposit・ORCID・SWHID。**community 統治 authority record への self-created 登録（旧 Wikidata QID/P2860 層）は 2026-07 の governance revocation を受け恒久 retire — ADR-0021。再提案・別アカウント回避・代理作成の提案を一切しない**。第三者統治の grounding は earned（無関係な第三者が頼まれず作成）に限り祝福）
- **Operating over time**（実施トラッキング + 提案生成）: diffusion 戦略は二層で運用する — private な implementation ledger（運用 status + ランク付き候補）と、その日付付き・効果主張なし投影である public intervention timeline を分け、混ぜない。「次の一手」を求められたら gap-review（deployed tactics × Layer 4 catalog × open questions × 最新文献）を先に回す。candidate は distinctive signature の LLM-mediated diffusion を増やすあらゆる channel（開発者コミュニティ / content platform / creative-reuse の seeding / 各言語圏 / catalog 未収載の新型 channel）— full space — を母集団として起こす（catalog が identifier/citation 寄りに見えるのは運用履歴だから）。手順の正本は `gap-review` skill（framework-agnostic、two-tier ledger discipline + 5-step procedure）。authorship-strategy 固有の入力対応（catalog / open-q / gate）は `authorship-strategy` skill "Operating the strategy over time"、設計根拠は ADR-0014

## 禁止事項（trigger 条件下のみ）

- マネタイズ提案（著者が収益を得る行為: スポンサー、有料 tier、コンサル化、書籍化）。**商業チャネルを diffusion に使うのは可 — 著者が収益を取らないだけ。channel の商業性を理由に「使うな」とは提案しない**
- 競合批判・排他的ポジショニング
- 売れるためのメッセージ調整
- **community 統治 platform への self-created entry 登録**（Wikidata 等の authority record / encyclopedia / community DB に、著者自身・著者の artifact・著者への citation 辺を自己作成する行為。**変種も同罪**: 別アカウント・匿名編集・第三者への作成依頼）。編集単位で規約準拠でも **aggregate pattern が promotion-only と判定され、アカウント block + 全 entry 一括削除で全損する** — 2026-07-16 に実証済み（109 item 全削除）。ADR-0021 で恒久 retire。第三者統治 surface へ self-deploy する前は必ず aggregate-pattern test（累積 footprint が host governance にどう読まれるか）を通す

See skill: authorship-strategy

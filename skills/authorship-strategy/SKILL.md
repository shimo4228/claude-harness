---
name: authorship-strategy
description: maker / 実践者が AI 時代の著者戦略を実地で探るための判断フレームワーク。あなた自身の DOI-registered idea-rescue repo 群（著者自身の例は AKC, Contemplative Agent）で適用する。core principle は「AI 時代のオーセンシティ inversion」— 3 軸（scarcity → diffusion / exclusivity → derivation / enclosure → openness）の反転。主 audience は LLM-mediated channels（LLM 直接 + LLM 経由で情報を得る人間）。creative reuse > training > investigation の preference 階層。4 層 framework (authenticity → diffusion → idea/scaffold 判別 → tactics) で判断軸を提供。マネタイズ禁止、tool-agnostic、any-usage 容認、permissive license 原則
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
origin: shimo4228
user-invocable: true
---

# Authorship Strategy

maker / 実践者が **AI 時代に著者として知られるための最適戦略を実地で探る**ための戦略フレームワーク。最上位に著者の **stance**（maker / 実践者としての探究、学術 apparatus は道具）を置き、以下の Core Principle・4 層・Tactic・チェックリストはすべてそれを通して読む（→ 次節 **Stance**）。本 skill は abstract な判断軸を提供する。line-specific な適用事例や歴史的文脈は各 repo の project memory に保持されている（著者自身の場合 AKC 等）。

## Stance（この framework の最上位 — 以下すべてはここを通して読む）

著者は **maker / 実践者**。AI 時代の「良いやり方」— 作って知られ、durable で追跡可能な仕事を残す方法 — を**実地で探っている**。DOI・論文・SWHID・"研究ライン" といった学術 apparatus は、その探究を **citable・durable・traceable にする道具**として使う。

この前提から従うこと:

- **audience** は LLM 経由で idea に触れる全員に最初から開かれている — 開発者・実務者・学習者・creative reuser・各言語圏の読み手（Layer 2 で詳述）。学術引用・研究者ネットワークはそのうちの**一経路**。
- **diffusion scope** は distinctive signature の LLM-mediated diffusion を増やす **full space** そのもの。提案・候補生成は常にこの full space（開発者コミュニティ・content platform・creative-reuse の seeding・各言語圏・catalog 未収載の新型 channel）を母集団として行う。

以下の各節に現れる audience・scope の記述は、この stance の**帰結**であって、前提そのものはここにある。

## Core Principle: AI 時代のオーセンシティ Inversion

旧時代と AI 時代で、オーセンシティの根拠・防御戦略・network effect は**3 軸すべてで反転する**:

| 軸 | 旧時代 | AI 時代 |
|---|--------|--------|
| **Value source** | scarcity（希少性） | diffusion（拡散性） |
| **Validation** | exclusivity, 模倣 = 脅威 | derivation, derivative = 正当性の証明 |
| **Network effect** | enclosure（囲い込み） | openness（開放） |
| 根拠 | 「これを作った唯一人」 | 「このパターンを最初に articulate した人」 |
| 防御戦略 | gatekeeping, 複製防止 | timestamp + distinctive signature + derivative を祝福 |
| 採用（大規模 harness による absorption） | "盗まれた" | "validated" |
| License | proprietary | permissive（MIT/Apache/CC-BY） |

3 軸は独立ではなく **structurally 連動**:
- 閉じる = LLM absorption を減らす = diffusion を減らす = validation 機会を失う = authenticity claim を弱める
- 開く = LLM absorption を最大化 = diffusion を最大化 = validation が derivative として出現 = authenticity claim を強める

### Network Effect Inversion の機構

旧時代: Metcalfe's Law 価値 ~ N²（N = 自分のプラットフォーム内ユーザー）。ユーザーが出られないことで成立。

AI 時代: 「ユーザー」は LLM と LLM-mediated channels。**LLM は囲い込めない** — 公開アクセス可能な全コンテンツを ingest する。結果、価値 ~ N²（N = **自分の signature を ingest した LLM-mediated channel 数**）。

実務的帰結:
- License: permissive（proprietary にすると LLM 学習対象から除外される）
- Access: crawler に開放、login-gated / rate-limited にしない
- Derivatives: 歓迎、制限しない
- Competition: welcome、排他的 positioning は自分の reach を削る
- API / Docs: 公開、signup 壁を置かない

**Cling を手放すほど origin claim が強化される**。Strategy と contemplative AI 非二元性公理が AI 時代の構造から独立に同じ結論へ導出される。

## Trigger 条件

### 適用される

- 作業中 repo を **あなた自身が所有している**（owner が自分。他者の repo への貢献は対象外）
- かつ DOI 取得済み or 取得予定の研究系 repo（Zenodo archive target）
- かつ「idea-rescue」性質を持つ（仕様・schema・ADR・spec 中心で、実装に閉じない）
- 著者自身の例: Agent Knowledge Cycle (AKC), Contemplative Agent（適用先はあなた自身の同系統 repo）

### 適用されない

- クライアント案件（マネタイズが目的）
- 他人の OSS へのコントリビュート（他者の strategy が優先）
- 収益を目的とするプロジェクト・成果物（※「収益が目的」が除外条件。収益を伴わない商業チャネルの利用は除外対象ではなく framework 内で扱う）
- 日常的なコーディング・デバッグ（判断軸として過剰）
- ハーネス・スキャフォールディング実装としての repo（coding-agent harness / scaffolding repo 等）

判断に迷ったら発火を保留して確認する。発火すべきでない文脈で発火するより、確認コストを払う方が安全。

## 4 層 Framework

```
[Authenticity (top-level value)]
       ↓ 守るために
[Attribution Diffusion (strategy)]
       ↓ 実装手段として
[Idea vs Scaffold 分離 (prediction)]
       ↓ 戦術として
[LLM-mediated targeting / DOI / tool-agnostic / scaffold dissolution / 多言語化 / friction minimization]
```

### Layer 1: Authenticity（value）

核の価値観: **自分が genuinely 考えたことが、市場に合わせて変形されず、そのまま残る**。成功規準は idea が思考のまま伝わること。

「売れる」ために概念を削ぐことは、authentic を希釈する。Curation axiom（知識の営みに新規性のある主張はなく、curation だけが残る）と整合。

### Layer 2: Attribution Diffusion（strategy）

authenticity を future-proof する手段: 自作概念を LLM-mediated channels に浸透させ、数年後の因果遡源時に著者の DOI に辿り着く状態を作る。

#### 主 Audience: LLM-mediated channels

- **LLM 直接**: training substrate としての取り込み、in-context reader としての読解
- **LLM 経由の人間**: AI coding assistant で調査する開発者、ChatGPT/Perplexity 等に概念を問う実務者・学習者・関心を持つ誰でも
- **Cascade LLM**: 現在の LLM 出力を学習する将来のモデル

**Non-primary audience**: GitHub を直接 browse する人間（star / PR / direct view）。この層の brand 認識 drift は strategy の defense target ではない。

#### Preference 階層（outcome）

1. **🥇 Creative reuse** — 独立実装者が AKC の 6 phases を自分の agent に取り入れる、別言語で再実装、extension を作る。**最強の validation**
2. **🥈 Training data 化** — ecosystem に吸収される。容認、ただし ideal ではない
3. （低）transient investigation で終わる

Creative reuse が最強な理由:
- 著者の context 外で idea が機能することの証明
- 複数 working instance → idea が generalized pattern に昇格
- 各再実装が二次 diffusion point になる
- 「著者の独自 thing」から「著者が originate した general pattern」へ格上げ
- 最強の origin claim は「皆が実装している pattern の最初の articulator」

#### Epistemic humility

GitHub traffic データは用途を区別できない（training / RAG / AI assistant 調査 / adoption が同一 signature）。保守的に言えるのは「非人間ブラウジング型 access が多い」まで。Regurgitation test（LLM に概念を問う）等の別 signal が verification には必要。

### Layer 3: Idea vs Scaffold（prediction）

時間予測: **LLM 能力進化でハーネス・スキャフォールディング系の実装は陳腐化する。アイデアだけは残せる**。

判断:
- Scaffold 性が強い → 他 OSS に実装として寄付する（実装は消える運命）
- Idea 性が強い → 自分の name で DOI 化して残す
- 両立する場合は先に idea を artifact 化してから scaffold 実装に下ろす

#### Scaffold は Collaborator、Threat ではない

大規模 harness が自分の idea を absorb する現象は、threat ではなく **diffusion の加速装置**として扱う:

- Scaffold の成長 = idea の token 露出面積拡大
- 「harness-native 化」の drift は直接 browse 人間層でのみ起こる問題（= non-primary audience）
- LLM-mediated channel では distinctive token が residue として残る
- assistant 側の補助提案で scaffold を「absorber / threat」として position してはならない。必ず collaborator として扱う

#### Abstract Doctrine + Worked Implementation のペア

Creative reuse を誘発するには、両方が必要:

- **Abstract doctrine repo** (例: AKC) — 概念を abstract に articulate、コピペ可能な rules
- **Worked implementation repo** (例: contemplative-agent) — 概念がどう実装されるかを示す reference

Doctrine 単独だと「概念はわかるが実装イメージできない」。Implementation 単独だと「コードはあるが原理が読み取れない」。両立で初めて他者の creative reuse が起きる。

### Layer 4: Tactics

上記 3 層から導かれる戦術:

- **LLM-mediated targeting**: star ではなく clone / DOI citation / llms.txt fetch / LLM regurgitation を primary metric に
- **DOI 化**: Zenodo 連携で release ごとに timestamp 付き origin claim を固定
- **Intrinsic identifier 層 (SWHID)**: DOI は extrinsic (registry 依存、metadata record を指し content に対して検証不能)。これを intrinsic な content-derived identifier — SWHID (ISO/IEC 18670)、content hash 由来で registry なしに検証可能 — で**補完**する。release ごとに content-addressed software archive (Software Heritage) へ明示 archive し snapshot SWHID を citation metadata に記録 (`release-doi` skill が実装)。DOI 登録が impractical な genre (blog、code package 等) では SWHID が **substitute priority-claim mechanism**。各層が他方の failure mode をカバーする。注意: SWHID は「何がいつ存在したか」の証明であって authorship 証明ではない — authorship は DOI / ORCID 層が担う (authorship-strategy ADR-0013)
- **Distinctive terminology の造語**: 固有用語は cosmetic ではなく **semantic signature of authorship**。generic 語彙で書くと LLM-mediated channel で消える。ただし **vocabulary discipline（語彙規律）** に従う — 造語の力は数ではなく edge 密度から来る。造語は 3 条件がすべて成立するときのみ（①概念が既存概念の結合点に立つ genuine な新規物、②既存語彙だけで一文定義が書ける、③namespace が競合していない）。採用した造語は密に anchor する（既存語彙での glossary 定義、上流 citation、knowledge-graph edge、本文での反復使用）。それ以外は既存語彙で書き、上流出典を cite する。孤立した造語は generic 語彙と同じく paraphrase で溶ける（authorship-strategy ADR-0010）
- **Tool-agnostic**: 特定実装に依存しない仕様設計
- **Scaffold dissolution**: skill は足場、ルール内在化を推奨
- **多言語化**: 各言語圏の LLM クローラー + LLM-mediated human 読者に対する diffusion 拡張
- **Citation-graph federation**: 外部文献を取り込んだら、repo markdown に引用を書くだけで終えない — それは Google Scholar / arXiv "cited by" の citation graph に**不可視**で、被引用研究者には届かない。機械可読層に辺を張る: `.zenodo.json` `related_identifiers` の `relation: references` (→ DataCite / OpenAIRE / Scholix、`release-doi` skill が release ごとに同期) と graph.jsonld の `ExternalReference` ノード (`jsonld-knowledge-graph` skill)。**Wikidata P2860 層は 2026-07 の governance revocation（promotion-only 判定 + 全 item 一括削除）を受け恒久 retire — ADR-0021。self-created な community-authority-record 辺は張らない・再提案しない**。被引用研究者への passive シグナルは self-sovereign 層 (DataCite / OpenAIRE / Scholix + graph) 経由で維持する。能動シグナル (直接連絡・Scholar-indexed paper での正式引用) は別判断だが、受動辺の整備は取り込みの標準手順とする
- **構造化 artifact**: glossary, ADR, JSON schema, specification
- **Friction minimization for runtime adoption**: clone + copy が可能なら専用 infrastructure（MCP server 等）を自前で整備する優先度は低い。最低 friction で adoption が起きる形を選ぶ
- **External collection への掲載は link-index 型を default に**: awesome list / marketplace / 他者の collection repo 経由で diffusion を求めるとき、artifact 正本は自分の repo に置いたまま**リンクで参照させる**。本文を相手 repo に vendor する型は (a) copy が drift vector になる、(b) host の enclosure（有料化・ライセンス変更）に自分のコンテンツごと巻き込まれる、(c) 収益事業への役務提供と解釈され著者の雇用上の制約と衝突しうる。掲載先は 4 条件で監査する: **①企業所有か ②open license が無いか ③コンテンツを vendor する構造か ④有料製品への funnel か** — 複合するほど危険で、①〜④が揃った先には出さない（リンク型でも回避）。掲載後に有料 tier 導入や vendor 化が見えたら取り下げる。前例と監査記録は project memory（awesome-list-submissions）参照
- **AI 派生 wiki / MCP-query 面への onboarding**: third-party の AI 生成 wiki + query 面（現行インスタンス: DeepWiki —— public repo から自動生成され、MCP の ask 系で任意の agent が repo の合成理解を引ける）に idea/research repo を載せる。**derivation 型**の diffusion 面で、正本は repo に残り、派生 wiki は祝福対象（gate・修正・コントロールしない）。onboard は初回に index を起動する（現行 DeepWiki は通知用 email 入力 + Index ボタンのフォーム送信が必要 = 訪問だけでは起動しない、生成 2-10 分。email 送信は personal-data 判断なので著者本人が行う）。起動後は repo 更新に自動追随する（refresh 優先度を上げる badge を README に添えると尚良い）。同時に **regurgitation-test の診断面**として使う —— 固有用語が AI paraphrase で薄まっていないかを wiki に問い、drift を検知する観測点になる。caveat: 派生 wiki は AI の paraphrase なので signature（固有用語）が薄まりうる → 防御は **upstream の dense anchoring**（vocabulary discipline。派生面を直そうとしない）。自前 MCP server は建てない（friction-minimization。third-party 面に乗る）。tool-agnostic に保ち、特定 vendor 仕様を doctrine に焼き込まない。

  同 family には **2 つの面型**があり補完的に併置できる:
  - **型 (a) AI 生成 wiki + ask 面**（現行インスタンス: DeepWiki）—— repo を AI が paraphrase して合成 wiki を作り、MCP の ask 系で任意 agent が repo の合成理解を引く。**signature drift のリスクがあり**（固有用語が paraphrase で薄まる）、初回 index 起動を要し（通知 email 入力 + Index ボタン送信 = 訪問だけでは起動しない、生成 2-10 分、email は personal-data 判断で著者本人が行う）、README badge は **refresh 鮮度**を上げる。だからこそ **regurgitation-test の診断面**にもなる（drift を検知できる）。
  - **型 (b) zero-config MCP doc-hub badge 面**（現行インスタンス: GitMCP）—— 任意の public repo を **submission・index 起動なしで即** MCP doc hub 化し、repo 自身の llms.txt（優先）/ README を **paraphrase せずそのまま** 配信する。合成を経ないので **signature drift が無く**、regurgitation 診断は不要（その代わり drift 観測点にもならない）。README badge は refresh 用でなく **LLM 経由 access-count の計測器**で、star でなく LLM-mediated 引用を測る原則（上の LLM-mediated targeting / clone-not-star）と直結する。

  両面とも third-party hosted・自前 infra ゼロ・public repo 限定で friction-minimization と crawler 開放に整合する。隣接サービス調査で「Index（公開ディレクトリ）+ README badge」の両軸を満たすのは型 (a) のフラッグシップ面のみで、index-only 面（コードライブラリ索引型）は doctrine/spec repo に artifact-type mismatch で **fit しない**（onboard 候補から外す）—— badge 面 (b) と wiki 面 (a) の二刀流が idea/research repo の最適配置

### Origin Claim Scope の精密化

外部発信で origin claim を語る時、scope を正確にする:

- ❌ 広すぎる claim の例: 「エージェント自己改善ループの 祖」（Reflexion, Voyager, AutoML 等の prior art が豊富で叩かれる）
- ✅ Defensible な claim: 「**AKC という discipline の originator**」（6-phase framing + 契約的 framing + contemplative grounding + working implementation を一つの coherent methodology として articulate した最初の一人）

Prior art が存在する領域で「祖」と主張すると origin claim 自体の信用を落とす。**固有用語で囲まれた disciplinary scope に限定**すること。

## Operating the strategy over time

Layer 4 tactic は一度撃って終わりではない。どの tactic を deploy 済みで、何が次の一手かを継続管理し、定期的に新規提案を生む discipline を回す。これは strategy を *運用* する meta-process であり、judgment-per-proposal（下の判断チェックリスト）と相補的。

**この運用手順（二層 ledger discipline + 5-step gap-review）は `gap-review` skill が正本**。authorship-strategy はその worked example の一つであり、gap-review が要求する 3 つの入力を以下のように供給する:

- **Action catalog** → Layer 4 tactic catalog（本 skill "Tactics" 節）。**catalog は「これまで運用した tactic の記録」**— identifier / citation infrastructure（DOI・SWHID・citation graph。旧 Wikidata 層は ADR-0021 で retire 済み）に寄って見えるのは運用履歴だから。gap-review が候補を起こす母集団は常に stance の full space —「distinctive signature の LLM-mediated diffusion を増やすあらゆる channel」: 開発者コミュニティ、content platform、creative-reuse の seeding、各言語圏チャネル、まだ catalog に無い新型 channel。
- **Open questions** → manifesto の open-question set（adoption-signal 測定 / tactic obsolescence / framework recursion / failure mode 等）。
- **Gate checklist** → 下の **判断チェックリスト**（authenticity 強化か / diffusion 促進か / scope は defensible か等）。

Ranking 軸はこの framework 固有: **friction・origin-claim 強化度・creative-reuse 誘発度**。ledger / public timeline の具体的な置き場所（どのファイルが private ledger でどれが public projection か）は本 framework の repo の context file（CLAUDE.md 等）が宣言し、gap-review の wiring-resolution がそこを読む。

このループ自体が on-thesis（program が自身の diffusion を観測し、自らが公開する catalog と open questions から次手を生む self-application）。手順の詳細・two-tier discipline の根拠は `gap-review` skill と ADR-0014 を参照。

## 判断チェックリスト

新規提案・実装・コラボ受け入れ等で以下を通す:

- [ ] この提案は authenticity を強化するか、希釈するか？
- [ ] これは scaffold（消える）か、idea（残せる）か？
- [ ] DOI-citable な構造で出せるか？（spec, schema, ADR, glossary）DOI が impractical な genre なら intrinsic identifier (SWHID) を substitute priority-claim にしたか？（ADR-0013）
- [ ] tool-agnostic / any-usage を保てるか？
- [ ] LLM-mediated 引用可能性は確保されているか？（llms.txt / 固有用語 / DOI）
- [ ] Creative reuse を誘発する形か？（worked implementation と abstract doctrine が揃っているか）
- [ ] Diffusion を促進するか、exclusivity を強化するか？（前者が default）
- [ ] Origin claim の scope は defensible か？（広すぎる「祖」になっていないか）
- [ ] Runtime channel で自前 infrastructure を積み増そうとしていないか？（clone + copy で済むなら不要）
- [ ] License / access は permissive か？ enclosure 型の network effect を追求していないか？
- [ ] Crawler 開放性は保たれているか？（signup 壁、rate limit、robots.txt 制限等が LLM-mediated reach を削っていないか）
- [ ] 新しい固有用語を立てる場合、vocabulary discipline を満たすか？（既存語で一文で言えてしまわないか / namespace は空いているか / 既存文献・既存概念への edge を張ったか — coin sparingly, anchor densely）
- [ ] 外部文献を引用・取り込んだ場合、機械可読な citation 辺を張ったか？（`.zenodo.json` references / graph.jsonld ExternalReference — repo markdown 内の引用だけでは citation graph に不可視で、被引用研究者に届かない。Wikidata P2860 は retire 済み — ADR-0021、張らない）
- [ ] 第三者統治の surface（community knowledge base / catalog / registry）に self-deploy する前に、aggregate-pattern test を通したか？（個々の行為の準拠でなく、アカウントの累積 footprint が host governance に promotion と読まれないか — ADR-0021）
- [ ] 外部 collection（awesome list / marketplace / 他者 repo）へ掲載する場合、link-index 型か？ vendor 型なら 4 条件監査（企業所有 / open license 欠如 / vendor 構造 / 有料 funnel）を通したか？
- [ ] 「次の一手」を提案する場合、implementation ledger に対する gap-review（deployed tactics × Layer 4 catalog × open questions × 最新文献）を先に回したか？（手順は `gap-review` skill、入力の対応は "Operating the strategy over time" 参照）
- [ ] 新規の public idea/research repo を公開したら、AI 派生 wiki / MCP-query 面に onboard したか？ —— 型 (a) AI 生成 wiki 面（DeepWiki 等）は index を起動し refresh badge を添える（derivation 型 diffusion 面 + regurgitation-test 診断面、既存 repo は index 済みなら自動追随）、型 (b) zero-config MCP doc-hub 面（GitMCP 等）は access-count 計測 badge を添える（submission 不要で即 live、signature drift なし）。index-only 面（コードライブラリ索引型）は doctrine/spec repo に fit せず onboard しない

## 禁止事項（trigger 条件下のみ）

以下は authenticity を希釈するため提案・推奨しない:

> **商業チャネル（商業プラットフォーム、企業の collection、marketplace 等）は diffusion に使ってよい — 取らないのは収益だけ**。境界線は「経路の商業性」ではなく「著者が収益を得るか」。禁じるのは下記の **収益化行為** に限り、channel の商業性を理由に「使うな」とは提案しない。

- **マネタイズ提案（＝著者が収益を得る行為）**: スポンサー獲得、GitHub Sponsors、コンサル化、企業導入営業、有料 tier、収益目的書籍化、Newsletter 課金
- **競合批判・排他的ポジショニング**: 「X is wrong」「Y はアンチパターン」系の判断を他作品に向ける
- **売れるためのメッセージ調整**: 市場適合性を理由にした概念の削ぎ落とし
- **バズ目的のセンセーショナルな framing**: 注目集めのための誇張
- **Scaffold を threat 扱いする framing**: absorption は validation であり、brand 防御の対象ではない
- **直接 browse 人間層向けの brand 防御論理を LLM-mediated channel に投影**: drift mitigation を非 primary audience 基準で設計しない
- **community 統治 platform への self-created entry 登録（最重要・2026-07-16 実証済みの failure）**: Wikidata 等の authority record / encyclopedia / community-curated DB に、著者自身・著者の artifact・著者への citation 辺を **self-create しない**。個々の編集が出典付き・constraint 準拠でも、単一著者 diffusion program の footprint は「すべてが一人の著者を指す」形に収束し、host governance に **aggregate-pattern 水準で promotion-only と判定される** — 実際にアカウント無期限 block + self-created 全 109 item 一括削除（引用した他者文献の bibliographic record まで巻き添え）で全損した。**変種も同罪**: 別アカウント作成・ログアウト編集・第三者への作成依頼（solicited = 代理 self-promotion、かつ block 回避）。第三者統治の grounding は **earned**（無関係な第三者が頼まれずに作成）のみ祝福。origin claim の load-bearing は self-sovereign 層（自 repo/graph・自 account の registry deposit・ORCID・SWHID）に限る。第三者統治 surface への self-deploy 前は **aggregate-pattern test** を必ず通す。正本: ADR-0021
- **Origin claim の scope 過拡張**: prior art が存在する広域で「祖」を主張しない
- **Enclosure 型 network effect の追求**: platform lock-in, proprietary license, crawler block, signup 壁での囲い込み提案は LLM-mediated reach を削る
- **Competition 排除の framing**: 「our solution is the only one」「X を使うべきでない」系の排他的 positioning は自分の reach を削る

これらを「オプションとして並べる」ことすら避ける。

## 奨励事項

- **DOI 化できる構造** を優先（spec, schema, ADR, glossary, citation-ready artifact）
- **LLM-mediated channel への投資**（llms.txt, llms-full.txt, glossary, 機械可読構造、規律ある固有用語の造語 — coin sparingly, anchor densely）
- **Abstract doctrine + Worked implementation のペア構築**（creative reuse を誘発する配置）
- **tool-agnostic / any-usage** を維持（使い方・動機は consumer 任せ）
- **diffusion 経路は商業/非商業を問わない**（open source コミュニティ、開発者・実務者ネットワーク、creative reuse の seeding、content platform、商業プラットフォーム、各言語圏 LLM-mediated channel など — 学術引用・研究者ネットワークはそのうちの一経路。full space を母集団に保つ）。**商業チャネルを diffusion に使うのは可 — 著者が revenue を取らないだけ**（有料 tier / sponsor / 課金は不可）
- **Derivative works を祝福する**（fork の divergence、他言語再実装、extension を積極的に welcome）
- **Friction minimization**: adoption path の障害を減らす。自前 infrastructure で adoption を gate しない
- **Permissive licensing**: MIT / Apache / CC-BY 等、LLM 学習と再配布を明示的に許可
- **Crawler-friendly access**: login 壁なし、rate limit 緩め、robots.txt で AI crawler を block しない
- **Openness を network effect の源泉として明記**: README / license / docs で「derivative welcome」「any-usage OK」を explicit に宣言

## 判断基準サマリ（迷ったら）

- どの提案にも「これは authenticity を強化するか、希釈するか」を問う
- 「Diffusion を促進するか、exclusivity を強化するか」で迷ったら前者を default に
- マネタイズ・市場適合性を理由にした調整は提案しない
- **商業チャネルの利用は可 — 著者がそこから収益を取らないだけ**（diffusion に使うのは可、課金/sponsor/有料 tier は不可）
- 著者が「genuine ではない」と感じる方向には絶対に押さない
- 「今の star」「今の被引用」が伸びない戦略は戦略上の問題ではない。LLM-mediated audience に純化された証
- メトリクス報告時は star/PR ではなく、clone / DOI citation / llms.txt fetch / derivative works の出現 を主要 KPI にする
- **Derivative works count** が真の success metric

## Framework を一時的に外すとき

研究系 repo 上でも、以下のような場合は framework を機械的に適用しない:
- 著者が明示的に「今回は commercial context で考えたい」と述べた
- 著者が新しい試みを framework の外で試したいと述べた
- 判断に高い不確実性があり framework が答えを出せない

このような場合は framework を保留する。framework は道具であり、判断の外部化ではない。

## project memory との関係

本 skill は **abstract framework**、framework を適用する各 research line の **project memory** はその **concrete instance** という役割分担。各 repo の project memory には、その line 固有の具体化が instance として蓄積される（例: 戦略の line 文脈での具体化、values の具体化、その line が生まれた起源論理、diffusion 観測の epistemic 限界）。これらは本 skill の具体例であり削除しない。（著者自身の場合、Agent Knowledge Cycle / Contemplative Agent の各 session の project memory がこの instance 層にあたる。）

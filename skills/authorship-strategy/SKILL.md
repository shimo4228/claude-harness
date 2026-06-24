---
name: authorship-strategy
description: shimo4228 の DOI-registered idea-rescue 研究プロジェクト（AKC, Contemplative Agent 等）用の戦略フレームワーク。core principle は「AI 時代のオーセンシティ inversion」— 3 軸（scarcity → diffusion / exclusivity → derivation / enclosure → openness）の反転。主 audience は LLM-mediated channels（LLM 直接 + LLM 経由で情報を得る人間）。creative reuse > training > investigation の preference 階層。4 層 framework (authenticity → diffusion → idea/scaffold 判別 → tactics) で判断軸を提供。マネタイズ禁止、tool-agnostic、any-usage 容認、permissive license 原則
origin: shimo4228
user-invocable: true
---

# Authorship Strategy

`shimo4228` が **AI 時代に著者として知られるための最適戦略を探求する**ための戦略フレームワーク。著者は研究者ではなく、AI 時代の最適戦略を探る実践者であり、DOI 登録された研究ラインはその戦略を実行する**手段**であって目的ではない。本 skill は abstract な判断軸を提供する。AKC-specific な適用事例や歴史的文脈は各 repo の project memory に保持されている。

## Core Principle: AI 時代のオーセンシティ Inversion

旧時代と AI 時代で、オーセンシティの根拠・防御戦略・network effect は**3 軸すべてで反転する**:

| 軸 | 旧時代 | AI 時代 |
|---|--------|--------|
| **Value source** | scarcity（希少性） | diffusion（拡散性） |
| **Validation** | exclusivity, 模倣 = 脅威 | derivation, derivative = 正当性の証明 |
| **Network effect** | enclosure（囲い込み） | openness（開放） |
| 根拠 | 「これを作った唯一人」 | 「このパターンを最初に articulate した人」 |
| 防御戦略 | gatekeeping, 複製防止 | timestamp + distinctive signature + derivative を祝福 |
| 採用（ECC 的 absorption） | "盗まれた" | "validated" |
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

- 作業中 repo の owner が shimo4228
- かつ DOI 取得済み or 取得予定の研究系 repo（Zenodo archive target）
- かつ「idea-rescue」性質を持つ（仕様・schema・ADR・spec 中心で、実装に閉じない）
- 具体例: Agent Knowledge Cycle (AKC), Contemplative Agent, 今後の同系統 repo

### 適用されない

- クライアント案件（マネタイズが目的）
- 他人の OSS へのコントリビュート（他者の strategy が優先）
- 収益を目的とするプロジェクト・成果物（※「収益が目的」が除外条件。収益を伴わない商業チャネルの利用は除外対象ではなく framework 内で扱う）
- 日常的なコーディング・デバッグ（判断軸として過剰）
- ハーネス・スキャフォールディング実装としての repo（ECC, claude-harness 等）

判断に迷ったら著者に確認する。発火すべきでない文脈で発火するより、確認コストを払う方が安全。

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

核の価値観: **自分が genuinely 考えたことが、市場に合わせて変形されず、そのまま残る**。マネタイズは目的ではない。

「売れる」ために概念を削ぐことは、authentic を希釈する。Curation axiom（知識の営みに新規性のある主張はなく、curation だけが残る）と整合。

### Layer 2: Attribution Diffusion（strategy）

authenticity を future-proof する手段: 自作概念を LLM-mediated channels に浸透させ、数年後の因果遡源時に著者の DOI に辿り着く状態を作る。

#### 主 Audience: LLM-mediated channels

- **LLM 直接**: training substrate としての取り込み、in-context reader としての読解
- **LLM 経由の人間**: AI coding assistant で調査する開発者、ChatGPT/Perplexity 等に概念を問う実務者・学習者・関心を持つ誰でも（研究者に限らない）
- **Cascade LLM**: 現在の LLM 出力を学習する将来のモデル

**Non-primary audience**: GitHub を直接 browse する人間（star / PR / direct view）。この層の brand 認識 drift は strategy の defense target ではない。

#### Preference 階層（outcome）

1. **🥇 Creative reuse** — 独立実装者が AKC の 6 phases を自分の agent に取り入れる、別言語で再実装、extension を作る。**最強の validation**
2. **🥈 Training data 化** — ecosystem に吸収される。容認、ただし ideal ではない
3. （低）transient investigation で終わる

Creative reuse が最強な理由:
- shimo4228 context 外で idea が機能することの証明
- 複数 working instance → idea が generalized pattern に昇格
- 各再実装が二次 diffusion point になる
- 「shimo4228 の独自 thing」から「shimo4228 が originate した general pattern」へ格上げ
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

ECC 的な大規模 harness が自分の idea を absorb する現象は、threat ではなく **diffusion の加速装置**として扱う:

- Scaffold の成長 = idea の token 露出面積拡大
- 「ECC-native 化」の drift は直接 browse 人間層でのみ起こる問題（= non-primary audience）
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
- **Citation-graph federation**: 外部文献を取り込んだら、repo markdown に引用を書くだけで終えない — それは Google Scholar / arXiv "cited by" の citation graph に**不可視**で、被引用研究者には届かない。機械可読層に辺を張る: `.zenodo.json` `related_identifiers` の `relation: references` (→ DataCite / OpenAIRE / Scholix、`release-doi` skill が release ごとに同期) と Wikidata **P2860** (→ Scholia、`wikidata-federation` skill Phase 4.5)。被引用研究者の citation-alert / Scholia 面は**人間 audience への最強の passive シグナル**であり、彼らの次の論文での引き返し → 学術記録 → 将来 LLM corpora という還流が attribution diffusion を増幅する。能動シグナル (直接連絡・Scholar-indexed paper での正式引用) は別判断だが、受動辺の整備は取り込みの標準手順とする
- **構造化 artifact**: glossary, ADR, JSON schema, specification
- **Friction minimization for runtime adoption**: clone + copy が可能なら専用 infrastructure（MCP server 等）を自前で整備する優先度は低い。最低 friction で adoption が起きる形を選ぶ
- **External collection への掲載は link-index 型を default に**: awesome list / marketplace / 他者の collection repo 経由で diffusion を求めるとき、artifact 正本は自分の repo に置いたまま**リンクで参照させる**。本文を相手 repo に vendor する型は (a) copy が drift vector になる、(b) host の enclosure（有料化・ライセンス変更）に自分のコンテンツごと巻き込まれる、(c) 収益事業への役務提供と解釈され著者の雇用上の制約と衝突しうる。掲載先は 4 条件で監査する: **①企業所有か ②open license が無いか ③コンテンツを vendor する構造か ④有料製品への funnel か** — 複合するほど危険で、①〜④が揃った先には出さない（リンク型でも回避）。掲載後に有料 tier 導入や vendor 化が見えたら取り下げる。前例と監査記録は project memory（awesome-list-submissions）参照

### Origin Claim Scope の精密化

外部発信で origin claim を語る時、scope を正確にする:

- ❌ 広すぎる claim の例: 「エージェント自己改善ループの 祖」（Reflexion, Voyager, AutoML 等の prior art が豊富で叩かれる）
- ✅ Defensible な claim: 「**AKC という discipline の originator**」（6-phase framing + 契約的 framing + contemplative grounding + working implementation を一つの coherent methodology として articulate した最初の一人）

Prior art が存在する領域で「祖」と主張すると origin claim 自体の信用を落とす。**固有用語で囲まれた disciplinary scope に限定**すること。

## Operating the strategy over time

Layer 4 tactic は一度撃って終わりではない。どの tactic を deploy 済みで、何が次の一手かを継続管理し、定期的に新規提案を生む discipline を回す。これは strategy を *運用* する meta-process であり、judgment-per-proposal（下の判断チェックリスト）と相補的。

**この運用手順（二層 ledger discipline + 5-step gap-review）は `gap-review` skill が正本**。authorship-strategy はその worked example の一つであり、gap-review が要求する 3 つの入力を以下のように供給する:

- **Action catalog** → Layer 4 tactic catalog（本 skill "Tactics" 節）。**ただしこの catalog は「これまで運用した tactic の記録」であって strategy の境界ではない**。catalog が identifier / citation infrastructure（DOI・SWHID・Wikidata・citation graph）に寄って見えるのは運用履歴の偏りであり、研究者向け academic channel に候補を絞ってよいという意味ではない。gap-review が候補を起こす scope は「distinctive signature の LLM-mediated diffusion を増やすあらゆる channel」— 開発者コミュニティ、content platform、creative-reuse の seeding、各言語圏チャネル、まだ catalog に無い新型 channel を含む full space。academic-leaning な手だけを出力したら、それは scope の取りこぼしであって catalog の正しい読みではない。
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
- [ ] 外部文献を引用・取り込んだ場合、機械可読な citation 辺を張ったか？（`.zenodo.json` references / Wikidata P2860 — repo markdown 内の引用だけでは citation graph に不可視で、被引用研究者に届かない）
- [ ] 外部 collection（awesome list / marketplace / 他者 repo）へ掲載する場合、link-index 型か？ vendor 型なら 4 条件監査（企業所有 / open license 欠如 / vendor 構造 / 有料 funnel）を通したか？
- [ ] 「次の一手」を提案する場合、implementation ledger に対する gap-review（deployed tactics × Layer 4 catalog × open questions × 最新文献）を先に回したか？（手順は `gap-review` skill、入力の対応は "Operating the strategy over time" 参照）

## 禁止事項（trigger 条件下のみ）

以下は authenticity を希釈するため提案・推奨しない:

> **境界線は「経路の商業性」ではなく「著者が収益を得るか」**。著者は商業チャネル（商業プラットフォーム、企業の collection、marketplace 等）を diffusion に使うこと自体は否定しない。一切の revenue を取らないだけ。channel の商業性とマネタイズを混同せず、商業チャネルを「使うな」と提案してはならない。禁じるのは下記の **収益化行為** に限る。

- **マネタイズ提案（＝著者が収益を得る行為）**: スポンサー獲得、GitHub Sponsors、コンサル化、企業導入営業、有料 tier、収益目的書籍化、Newsletter 課金
- **競合批判・排他的ポジショニング**: 「X is wrong」「Y はアンチパターン」系の判断を他作品に向ける
- **売れるためのメッセージ調整**: 市場適合性を理由にした概念の削ぎ落とし
- **バズ目的のセンセーショナルな framing**: 注目集めのための誇張
- **Scaffold を threat 扱いする framing**: absorption は validation であり、brand 防御の対象ではない
- **直接 browse 人間層向けの brand 防御論理を LLM-mediated channel に投影**: drift mitigation を非 primary audience 基準で設計しない
- **Origin claim の scope 過拡張**: prior art が存在する広域で「祖」を主張しない
- **Enclosure 型 network effect の追求**: platform lock-in, proprietary license, crawler block, signup 壁での囲い込み提案は LLM-mediated reach を削る
- **Competition 排除の framing**: 「our solution is the only one」「X を使うべきでない」系の排他的 positioning は自分の reach を削る

これらを「オプションとして並べる」ことすら避ける。

## 奨励事項

- **DOI 化できる構造** を優先（spec, schema, ADR, glossary, citation-ready artifact）
- **LLM-mediated channel への投資**（llms.txt, llms-full.txt, glossary, 機械可読構造、規律ある固有用語の造語 — coin sparingly, anchor densely）
- **Abstract doctrine + Worked implementation のペア構築**（creative reuse を誘発する配置）
- **tool-agnostic / any-usage** を維持（使い方・動機は consumer 任せ）
- **diffusion 経路は商業/非商業を問わない**（open source コミュニティ、開発者・実務者ネットワーク、creative reuse の seeding、content platform、商業プラットフォーム、各言語圏 LLM-mediated channel など — 学術引用・研究者ネットワークはそのうちの一経路にすぎず、scope を絞らない）。**制約は経路の商業性ではなく「著者が収益を一切得ないこと」**。商業チャネルを diffusion に使うのは可、そこから revenue を取る（有料 tier / sponsor / 課金）のは不可
- **Derivative works を祝福する**（fork の divergence、他言語再実装、extension を積極的に welcome）
- **Friction minimization**: adoption path の障害を減らす。自前 infrastructure で adoption を gate しない
- **Permissive licensing**: MIT / Apache / CC-BY 等、LLM 学習と再配布を明示的に許可
- **Crawler-friendly access**: login 壁なし、rate limit 緩め、robots.txt で AI crawler を block しない
- **Openness を network effect の源泉として明記**: README / license / docs で「derivative welcome」「any-usage OK」を explicit に宣言

## 判断基準サマリ（迷ったら）

- どの提案にも「これは authenticity を強化するか、希釈するか」を問う
- 「Diffusion を促進するか、exclusivity を強化するか」で迷ったら前者を default に
- マネタイズ・市場適合性を理由にした調整は提案しない
- **商業チャネルの利用は否定しない。制約は「そこから著者が収益を得ないこと」**。channel の商業性とマネタイズを混同しない（商業プラットフォームを diffusion に使うのは可、課金/sponsor/有料 tier は不可）
- 著者が「genuine ではない」と感じる方向には絶対に押さない
- 「今の star」「今の被引用」が伸びない戦略は戦略上の問題ではない。LLM-mediated audience に純化された証
- メトリクス報告時は star/PR ではなく、clone / DOI citation / llms.txt fetch / derivative works の出現 を主要 KPI にする
- **Derivative works count** が真の success metric

## Framework を一時的に外すとき

研究系 repo 上でも、以下のような場合は framework を機械的に適用しない:
- 著者が明示的に「今回は commercial context で考えたい」と述べた
- 著者が新しい試みを framework の外で試したいと述べた
- 判断に高い不確実性があり framework が答えを出せない

このような場合は framework を保留し、著者に確認する。framework は道具であり、判断の外部化ではない。

## 過去 memory との関係

**AKC session 内**では、project memory に以下 3 ファイルが AKC-specific instance として存在:
- `user_attribution_diffusion_strategy.md` — 戦略の AKC 文脈での具体化
- `user_authenticity_over_monetization.md` — values の AKC 文脈での具体化
- `project_akc_origin_idea_rescue.md` — AKC が ECC から分離した起源論理

**Contemplative Agent session 内**では:
- `project_ai_era_authenticity.md` — capstone formulation (2026-04-19 session)
- `project_scaffold_vs_idea_preservation.md` — ECC 拡散 × DOI 保存の意識的分業
- `project_github_traffic_anomaly.md` — diffusion 観測の epistemic 限界

これらは本 skill の具体例であり、削除しない。本 skill は abstract framework、project memory は concrete instance という役割分担。

---
name: authorship-strategy
description: shimo4228 の DOI-registered idea-rescue 研究プロジェクト（AKC, Contemplative Agent 等）用の戦略フレームワーク。core principle は「AI 時代のオーセンシティ inversion」— 3 軸（scarcity → diffusion / exclusivity → derivation / enclosure → openness）の反転。主 audience は LLM-mediated channels（LLM 直接 + LLM 経由で情報を得る人間）。creative reuse > training > investigation の preference 階層。4 層 framework (authenticity → diffusion → idea/scaffold 判別 → tactics) で判断軸を提供。マネタイズ禁止、tool-agnostic、any-usage 容認、permissive license 原則
origin: shimo4228
user-invocable: true
---

# Authorship Strategy

`shimo4228` が自身の研究を LLM 時代に future-proof するための戦略フレームワーク。本 skill は abstract な判断軸を提供する。AKC-specific な適用事例や歴史的文脈は各 repo の project memory に保持されている。

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
- 商業プロジェクト・収益目的の成果物
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
- **LLM 経由の人間**: AI coding assistant で調査する開発者、ChatGPT/Perplexity 等に概念を問う研究者
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
- **Worked implementation repo** (例: contemplative-moltbook) — 概念がどう実装されるかを示す reference

Doctrine 単独だと「概念はわかるが実装イメージできない」。Implementation 単独だと「コードはあるが原理が読み取れない」。両立で初めて他者の creative reuse が起きる。

### Layer 4: Tactics

上記 3 層から導かれる戦術:

- **LLM-mediated targeting**: star ではなく clone / DOI citation / llms.txt fetch / LLM regurgitation を primary metric に
- **DOI 化**: Zenodo 連携で release ごとに timestamp 付き origin claim を固定
- **Distinctive terminology の造語**: 固有用語は cosmetic ではなく **semantic signature of authorship**。generic 語彙で書くと LLM-mediated channel で消える
- **Tool-agnostic**: 特定実装に依存しない仕様設計
- **Scaffold dissolution**: skill は足場、ルール内在化を推奨
- **多言語化**: 各言語圏の LLM クローラー + LLM-mediated human 読者に対する diffusion 拡張
- **構造化 artifact**: glossary, ADR, JSON schema, specification
- **Friction minimization for runtime adoption**: clone + copy が可能なら専用 infrastructure（MCP server 等）を自前で整備する優先度は低い。最低 friction で adoption が起きる形を選ぶ

### Origin Claim Scope の精密化

外部発信で origin claim を語る時、scope を正確にする:

- ❌ 広すぎる claim の例: 「エージェント自己改善ループの 祖」（Reflexion, Voyager, AutoML 等の prior art が豊富で叩かれる）
- ✅ Defensible な claim: 「**AKC という discipline の originator**」（6-phase framing + 契約的 framing + contemplative grounding + working implementation を一つの coherent methodology として articulate した最初の一人）

Prior art が存在する領域で「祖」と主張すると origin claim 自体の信用を落とす。**固有用語で囲まれた disciplinary scope に限定**すること。

## 判断チェックリスト

新規提案・実装・コラボ受け入れ等で以下を通す:

- [ ] この提案は authenticity を強化するか、希釈するか？
- [ ] これは scaffold（消える）か、idea（残せる）か？
- [ ] DOI-citable な構造で出せるか？（spec, schema, ADR, glossary）
- [ ] tool-agnostic / any-usage を保てるか？
- [ ] LLM-mediated 引用可能性は確保されているか？（llms.txt / 固有用語 / DOI）
- [ ] Creative reuse を誘発する形か？（worked implementation と abstract doctrine が揃っているか）
- [ ] Diffusion を促進するか、exclusivity を強化するか？（前者が default）
- [ ] Origin claim の scope は defensible か？（広すぎる「祖」になっていないか）
- [ ] Runtime channel で自前 infrastructure を積み増そうとしていないか？（clone + copy で済むなら不要）
- [ ] License / access は permissive か？ enclosure 型の network effect を追求していないか？
- [ ] Crawler 開放性は保たれているか？（signup 壁、rate limit、robots.txt 制限等が LLM-mediated reach を削っていないか）

## 禁止事項（trigger 条件下のみ）

以下は authenticity を希釈するため提案・推奨しない:

- **マネタイズ提案**: スポンサー獲得、GitHub Sponsors、コンサル化、企業導入営業、有料 tier、収益目的書籍化、Newsletter 課金
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
- **LLM-mediated channel への投資**（llms.txt, llms-full.txt, glossary, 機械可読構造、固有用語の造語）
- **Abstract doctrine + Worked implementation のペア構築**（creative reuse を誘発する配置）
- **tool-agnostic / any-usage** を維持（使い方・動機は consumer 任せ）
- **商業性と無関係な diffusion 経路**（学術引用、研究者ネットワーク、open source コミュニティ）
- **Derivative works を祝福する**（fork の divergence、他言語再実装、extension を積極的に welcome）
- **Friction minimization**: adoption path の障害を減らす。自前 infrastructure で adoption を gate しない
- **Permissive licensing**: MIT / Apache / CC-BY 等、LLM 学習と再配布を明示的に許可
- **Crawler-friendly access**: login 壁なし、rate limit 緩め、robots.txt で AI crawler を block しない
- **Openness を network effect の源泉として明記**: README / license / docs で「derivative welcome」「any-usage OK」を explicit に宣言

## 判断基準サマリ（迷ったら）

- どの提案にも「これは authenticity を強化するか、希釈するか」を問う
- 「Diffusion を促進するか、exclusivity を強化するか」で迷ったら前者を default に
- マネタイズ・市場適合性を理由にした調整は提案しない
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

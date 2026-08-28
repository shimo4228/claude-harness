---
name: writing-ecosystem
description: 人間向け記事・エッセイ・ブログポスト・ニュースレターの唯一の執筆 orchestrator。project の publication channel contract を読み、中心命題 1 つの editorial brief、因果線、証拠の選択と除外、構成、執筆、review panel、著者の内容 GO、title-reviewer、quality-gate までを統括する。Use when — 「この記事を書いて」「このテーマでエッセイにして」「原稿の論点を一つに絞って構造改稿して」のような新規執筆・全体改稿・全文の別 channel 展開。NOT for — 一文や段落だけの翻訳（→ prose-translation）、title だけ（→ headline-craft / title-reviewer）、SNS 下書き（→ x-draft）、公開 thread 返信（→ public-comment）、AI 向け docs、README、paper、媒体固有の公開操作。
compatibility: Designed for Claude Code (or similar agent products). Orchestrates globally installed agents under ~/.claude/agents/.
user-invocable: true
origin: shimo4228
---

# writing-ecosystem — 人間向け執筆・レビューエコシステムの正本

人間読者向けコンテンツ（記事・エッセイ・ブログポスト・ニュースレター等）の執筆とレビューに関わるコンポーネント（skill と agent）の役割境界・使い分け・共通規約をまとめた正本。

> AI slop・タイトル規範・執筆フローは本 skill directory が正本。Voice の実値は channel contract が
> 持つ。詳細診断表だけ `references/` へ分離し、必要な phase で読む。

## Scope

**人間 primary のコンテンツのみ扱う**。AI-facing ドキュメント（`llms.txt` / `llms-full.txt` / FAQ ページ等）には `llms-txt-writer` skill を使う。audience 判定と役割分担は [Audience Separation: Human vs AI](../llms-txt-writer/SKILL.md#audience-separation-human-vs-ai) を参照。

本 skill は媒体名・語尾・frontmatter・文字数・reviewer 構成・公開 command を持たない。記事全体を
扱う task では最初に
`<project>/.claude/rules/*.md` の **publication channel contract** を読み、対象 path を 1 channel
へ解決する。contract が無い、または複数 channel に一致する場合は推測せず停止する。

執筆時の規範は本 skill と現在の local contract だけである。ADR、memory、過去セッションは
規範として参照しない。過去セッションを素材にするときは `session-theme-mining` が選んだ一次
pointer、`collect-context` が作る evidence dossier の順に限定して受け取る。

### Content integrity

中心命題、主張、構成は著者の判断が決める。受信指標が変えられるのは何を書くか・title の語選び・
tags・timing・language placement までで、本文はその外にある。

---

## Ecosystem Map

執筆関連コンポーネントの役割分担。どの phase で誰が何を持つか。

| フェーズ | コンポーネント | 軸 | トリガー |
|---------|---------------|-----|----------|
| **Theme discovery** | `session-theme-mining` skill | Claude / Codex 履歴横断から 0〜3 件の同格な問いを発見し、著者の選択で止まる | 執筆スコープがまだ決まっていないとき |
| **Theme review** | `theme-reviewer` agent | 選択済みの問いへ findings と深化の問いを返す。合否は出さない | editorial brief の前 |
| **Pre-write** | `collect-context` skill | 素材収集と証拠台帳（Claims Register / 一次・⚠未検証の tier）。編集判断はしない | 執筆前に素材を集めるとき |
| **Write** | 本 skill「editorial brief と執筆フロー」 | 中心命題・因果線・証拠選択・構成・執筆 | 初稿・改稿 |
| **Title generation** | `headline-craft` skill | 「開かせる一行」の候補生成 | 著者の内容 GO 後 |
| **Title review** | `title-reviewer` agent | 本文との契約を fresh context で点検し findings を返す | headline-craft の後、quality-gate の前 |
| **Review: 品質** | `editor` agent | 記事の構造・コード・AI slop・用語 | 実用チャンネルのレビュー時 |
| **Review: 論理** | `essay-reviewer` agent | エッセイの論理構成・過積載・トーン | エッセイチャンネルのレビュー時 |
| **Review: 初見明瞭性** | `prose-clarity-reviewer` agent | 第一画面・中心命題・内部文脈依存 | 構造凍結後の review panel 時 |
| **Review: 事実** | `fact-checker` agent | 事実主張の Web 検証 | 公開前検証時 |
| **Acceptance** | `quality-gate` skill | local contract の reviewer verdict と機械検査を集約 | 公開直前 |
| **Publish** | project-local publishing skill | platform API / UI / schedule / corpus 更新 | 著者 GO 後 |
| **Overlay** | `<project>/.claude/rules/*.md` | チャンネル固有の事実・配線 | プロジェクト内作業時のみ |

一文・一段落の翻訳（`prose-translation`）、title だけ（`headline-craft` / `title-reviewer`）、SNS
（`x-draft`）、公開 thread（`public-comment`）、README（`readme-writer`）、paper（`paper-ecosystem`）は
この flow に入れず、それぞれの専用 skill へ直接 route する。

## Canonical workflow

### 1. Route and discover

local contract から出力 channel と読者を決める。テーマ未選択なら `session-theme-mining` が
0〜3 件の同格候補を出し、著者の選択で止まる。選択済みの問いは `theme-reviewer` が findings
と深化の問いだけを返す。テーマ候補を採点・順位付けしない。

### 2. Collect, then select

必要なら `collect-context` で evidence dossier を作る。dossier は lookup material であり、本文へ
全部入れる coverage checklist ではない。構成前に次の **editorial brief** を提示し、著者確認で止まる。

```markdown
Reader: <一人の具体的読者と、その人の問い / 目的>
Channel: <local contract の channel>
Central thesis: <この原稿が成立させる命題を一文で。必ず一つ>
Causal spine: <観察 / 問題 → 緊張 → 機序 → 読者の判断・行動・Higher Ground>
Selected evidence:
- <evidence id>: <因果線での役割>
Out of scope:
- <面白いがこの命題を進めない論点>
```

実用 how-to では central thesis を「読者が得る一つの成果または判断則」としてよい。証拠は
量でなく役割で選ぶ。同じ役割の例が複数あるなら、因果に必要な最小の一例を残す。

### 3. Outline and draft

各 load-bearing section に causal spine 上の役割を一つだけ割り当て、採用 evidence を紐付ける。
並列の agenda を節として足さない。具体物を先に置き、説明を後にする。執筆中に別の中心命題が
現れたら混ぜずに停止し、editorial brief を再確認する。out-of-scope は `details` へ押し込まない。

翻訳は `prose-translation` を使い、承認済み central thesis、causal spine、selected evidence、
out-of-scope を保持する。翻訳先の local contract へ route し直す。

### 4. Freeze, review, and content GO

本文の構造を凍結したら、local contract の channel reviewer、`prose-clarity-reviewer`、
`fact-checker`、必要な cross-model review を本文へ実行する。editor と essay-reviewer の両方を
回すのは contract が要求する場合だけ。

review 修正が central thesis、causal spine、主要節を変えたら brief → 関係 reviewer へ戻る。
レビュー反映後、下の Final structural pass を確認してから著者が本文を通読し、**内容 GO** を
出す。内容が確定するのはこの GO であり、タイトル作業はその後に置く。

#### 指摘の処分規律

- **CRITICAL の意味**: 読者への約束・事実・中心命題を壊すもののみ。規約と運用実態の衝突は
  CRITICAL でなく「裁定要求」として報告し、裁定者は著者
- **裁定の書き戻し**: 裁定結果は memory でなく channel contract に書く（fresh-context reviewer に
  届く唯一の層）。著者が同種指摘を 2 回却下したら、その場で contract の該当行を更新または削除する
- **再レビュー規律**: 2 round 目以降は CRITICAL と変更部分の regression のみを blocking とし、
  新規 MEDIUM/MINOR は集計のみ（Anthropic best-practices の re-review convergence、as-of 2026-08-27）
- **blocking の根拠水準**: blocking 指摘は一次ソースの引用を要す。証拠台帳のみを根拠とする指摘は
  advisory（根拠 n=1・2026-08-27。以後 3 記事で台帳由来の偽陽性ゼロなら本行は削除候補）

#### Final structural pass（内容 GO の通読前チェック）

- `N reasons` と `N questions` を対応させるなら 1:1。対応しない列挙を鏡像にしない
- out-of-scope が本文へ戻っていない

中心命題の貫通・支配的命題・summary の新規導入は `prose-clarity-reviewer` が同じ phase で見る。

### 5. Title

内容 GO 済みの本文に対して `headline-craft` で候補を作り、`title-reviewer` の findings を見て
著者がタイトルを選ぶ。タイトル選択後に本文の構造を変えたら、内容 GO と title-reviewer を
やり直す。表現修正だけなら再実行しない。

### 6. Acceptance

`quality-gate` が local contract の証跡を集約して PASS を出した後、著者が公開 GO を判断する。
公開操作は contract が指す project-local publishing skill に渡す。

---

## Citation & Sources Workflow（出典をエッセイに入れる）

fact-check で確定した一次資料を、**本文の出典セクションに編入する**のがエッセイ公開前の標準ステップ。

### 所有と分離

- **embedding はこのワークフローが所有する**。`fact-checker` は report-only（記事を編集しない / author-reviewer 分離）のままで、検証済みソースを「出典セクションに落とせる形」で返すだけ。本文への編入は著者 / orchestrator が行う。
- `fact-checker` の出力（verdict が ✅ / ⚠️ のソース URL 群）が canonical input。

### 手順

1. fact-check 通過後、verdict が ✅ ACCURATE / ⚠️ PARTIALLY のソースを集める（❌ / ❓ のソースは載せない）。
2. ブロックの構成規則（テーマ別グループ化・重複 URL 排除・一次資料優先）は **`fact-checker` agent が持つ**（report を出す側が実値を持つ）。ここでは再掲しない。
3. 本文末に出典セクションを作る。
4. 本文で著者自身の既発表（DOI / repo / 論文）に言及していれば、それも出典に含める。

### 媒体別ポリシー

| 媒体 | 出典の置き方 |
|---|---|
| エッセイチャンネル | 末尾に `## 出典・参考文献`（ブロック構成は `fact-checker` の出力に従う） |
| 実用チャンネルの記事 / tutorial | 本文中の inline link を基本に、必要なら末尾に補助的な References |
| 学術 paper | 本ワークフローではなく `citation-formatter` agent（in-text ↔ reference の 1:1・format・DOI 検証） |

### 引用の検証水準（citation tier）

引用に要求される検証の深さは、**引用が何を主張するか**と**ジャンル**で決まる。

| 引用のレベル | 例 | 必要な検証 |
|---|---|---|
| **帰属**（著者 X は Y と主張している） | 「Froese は AI ジレンマを定式化した」 | 抄録で可 — 抄録は著者自身が書き査読を通った公式の主張要約 |
| **中身・ニュアンス**（議論の詳細・特定ページ） | 「p.165 で〜と述べる」 | 該当箇所の通読 |
| **評価・反駁**（当否の判定・批判・拡張） | 「この議論は誤っている」 | 全文精読 |

- **エッセイ / 記事**（人間向け）: 帰属レベルに収まる引用なら抄録ベースで可。当否判定をしないことを本文で明示するとなお良い
- **学術 paper**: 本表を適用しない。`paper-ecosystem` の Source Fidelity Rules（一次ソース直接照合）が正本で、常に厳格側
- **検証の格を隠さない**: 抄録引用は全文精読と同じ見た目になる（citation laundering）。抄録には本文より強く言う「スピン」の実証報告もある。機械可読レイヤーがある記事では `confidence` の隣に `verification`（どこまで読んだか + as-of 日付）を書ける。本文で開示する先例: 「出典の格は中程度（三次文献）であり、一次学術文献での裏取りは未了」型の一文

### 翻訳記事の出典

`prose-translation` で訳した記事は、原文の出典セクションを引き継ぐ。**URL / DOI は保持**し、description のみ英訳する。

### 自リポ言及の節度（本文内の self-link 制限）

本文中の自リポリンクは、読者がその場で手を動かすための**導線**か、直前の主張を支える**一次資料**
だけに置く。どちらでもない言及はリンクを末尾の関連リンク / 出典セクションへ寄せる。
**同一 repo への本文リンクは 1 記事 1 回まで**（末尾セクションは対象外）。

---

## Craft 規約（文の技術）

genre 中立。出典: Orwell "Politics and the English Language" (1946)、
Kaguura Gichuru (The Write Path, 2026-07)。

- **一人の読者へ手紙を書く。** その文は誰に向いているか
- **読者は前を覚えていない。** その指示語は何を指すか、その場で言えるか
- **副詞を削り、動詞を強くする。** 数値で言えるなら数値で言う
- **能動態を既定にする。** 行為者を伏せる理由があるか
- **平易語で足りるなら平易語を使う。** 硬い語は誰のためか
- **日常語で言えるなら専門用語を使わない。** その語は読者の語彙か
- **見慣れた比喩は使わない。** 情報を運んでいるか、間を埋めているか
- **第 2 稿は第 1 稿より短い。** その文は論点を前へ進めるか
- **文の壁は宿題に見える。** ただし全行独立はロボット臭
- **深い input からしか深い文章は出ない。** この原稿は何を読んで書いたか

これらは判断の補助であって検査項目ではない。守った結果、文が不誠実になる・
回りくどくなる・言いたいことが消えるなら、規約の方を破る。

shared word target は置かない。長さの上限は local contract、段落密度と造語・専門用語の
閾値は `prose-clarity-reviewer`、直し方の実例は
[`references/style-diagnostics.md`](references/style-diagnostics.md) が持つ。

---

## Draft craft and genre shapes

執筆順序の正本は上の Canonical workflow。ここは承認済み brief を文章にするときの craft だけを持つ。

### 具体物を先、説明を後

- 節の入口に置くのは**具体物** — 実例・出力・逸話・数値・画面の描写・コードブロック
- 説明はその**後**。順序が逆になると、読者は何の話か分からないまま抽象を読まされる
- 提供された文脈で裏づけられない経歴・実績・数値は書かない

### ジャンル別の構成

| genre | 構成 |
|---|---|
| 実用記事 / チュートリアル | 読者が何を得るかで開く。主要節ごとにコードか端末出力を置く。締めは要約でなく具体的な takeaway |
| エッセイ / オピニオン | **[エッセイの 4 段構成](#エッセイの-4-段構成heros-journey-型) が正本**。1 節 1 論点、意見を支える実例を置く |
| ニュースレター | 最初の 1 画面を強くする。近況の羅列にせず洞察を混ぜる。節ラベルで走査可能にする |

どの shape も central thesis と causal spine に従属する。テンプレートを満たすために節・装置・例を
足さない。複数論点を統合できるのは、同じ中心命題の因果線で上下関係を持つ場合だけである。

### Environment-dependent implementation handoff

local path、既存設定、symlink、認証、権限に依存する変更を読者へ渡す記事では、まず人間向け本文
だけで問題・判断則・採用境界を完結させる。その後に、読者のcoding agentへ渡すstandalone promptを
置ける。promptはread-onlyで環境を調査し、実装planを返し、人間承認前に編集・install・commit・
publishしない。agent handoffは人間向け理由説明の代替ではない。

## AI Slop

> その表現を別の記事にそのまま挿入しても意味が通るなら、それは AI slop。

著者の具体的な観察・経験・数値を伴わない評価語、形だけ反復できる対比・列挙・等間隔リズム、
無内容な opener / closer を使わない。兆候を見つけたときだけ
[`references/style-diagnostics.md`](references/style-diagnostics.md) を読む。

---

## Voice & Tone Rules

### Voice は channel contract が持つ

実用記事の直接指示、essayの発見調、その他のregisterをglobal既定で上書きしない。local contractが
宣言したvoiceを使い、著者の具体観察・確度・未解決範囲を保つ。

**語尾（ですます / だ・である）の実値は本 skill が持たない。** project の publication
channel contract が正本。記事全体の task で contract が無ければ推測しない。

発見調の診断例は [`references/style-diagnostics.md`](references/style-diagnostics.md) が持つ。

### 未解決の正直さ

解決していない問題は解決したふりをしない。「まだわからない」「今後の課題」と正直に書く。完璧な結論に無理に収束させない。

### 感情語の扱い

- **タイトル**: 禁止（「壊れている」「地獄」「最強」など）
- **本文**: 著者の自然な体験描写なら OK（「正直つらかった」「ここで詰まった」）

### 結論の問い化

contract が発見調を宣言し、読者自身に推論してほしい評価は問いにできる。ただし、全部を疑問形にして確度をぼかさない。
検証済みの事実・数値・具体観察は断定を保ち、評価や結論だけを証拠の強さに合わせて問い・観察・
断定から選ぶ。機械的な弱化が起きたときは `references/style-diagnostics.md` の例を読む。

### エッセイの二層構成（人間向けナラティブ + LLM 読者向け機械可読レイヤー）

エッセイの想定読者に人間だけでなく LLM（クローラー・エージェント）も含める場合の任意の構成。

- **前半は人間向けエッセイとして完結させる**。後半を読まない読者にも主張が全部伝わること
- **後半は `## ここから先は AI 読者向け` 見出しで人間の読者を明示的に降ろし**、YAML ブロックで主張を異常粒度で書き下す:
  - `document`（provenance: 原稿の来歴・authorship の帰属）
  - `definitions`（操作的定義。定義しないという判断もステータスとして明記）
  - `claims`（各 claim に evidence / confidence / scope_limit / basis）
  - `non_claims`（誤読されやすい「主張していないこと」を先回りで列挙）
  - `references`（DOI / ISBN 付き）
  - `author_epistemic_profile`（著者の認識スタイル・スタンスの自己申告）
- 機械可読レイヤーの claims と本文の主張は 1:1 で整合させる（essay-reviewer のレビュー観点に含める）

### AI メディエイト執筆の開示

AI が実際のテキスト生成を担った記事（AI-mediated writing）で channel contract が開示を求める場合、**記事末に開示ブロックを置く**。適用可否は contract が持つ。要素: (1) AI-mediated である旨の明言、(2) 原稿の来歴、(3) 主張・判断・責任が著者に帰属すること、(4) 準拠方針への参照。媒体固有のブロック記法が使えなければプレーンな段落 + 強調で書く。

### エッセイの 4 段構成（Hero's Journey 型）

essay の既定構成（出典: Kaguura 2026。Craft 規約と同じ取り込み）:

1. **Calm Story** — 技術・理論から入らず、シンプルで関連性の高い人間的ストーリー・具体的シーンで開く。低認知負荷で読者を著者の声に慣れさせる。冒頭数段落で執筆理由や背景を説明する warm-up は削除し、行動の最中に読者を投入する
2. **Plunge（緊張）** — 読者が乗ったところで、大きな問題・不都合な真実・パラドックスを提示する。緊張が途中離脱を難しくする
3. **Solution** — フレームワーク・中核ルールを提示して読者を引き上げる
4. **Higher Ground** — 開始時より高い位置で終える。読者が「学んだ」と感じて読み終える。未解決のまま残すこと自体が Higher Ground になりうる

---

## Title Conventions

### 目的

読み手がタイトルだけで「この記事が何の概念を提案しているか」を理解できること。

### 基本ルール

- **具体性**: 何についての記事かがタイトルだけでわかる
- **誠実さ**: 記事の内容以上のことを約束しない

生成技法（結果駆動・問いの形・好奇心ギャップ等）は `headline-craft` が持つ。

### 禁止事項

- **煽りタイトル**: 「壊れている」「地獄」「最強」などの感情語でクリックを誘わない
- **空の listicle 数字**: 実測の裏付けなく数字で釣る形（「N 選」「N 倍」）。実測値・件数を証拠として出す具体的数字（「1,000 件を分析したら〜」）はむしろ推奨 — 判定は「その数字は記事の中身の証拠か、器の飾りか」
- **詩的・教科書的タイトル**: 意味が取れない詩的タイトル（素通りされる）と、「〜の分析」「〜に関する考察」型の教科書調（宿題に見える）
- **挑発・断定**: 「〇〇の真価は△△ではない」式の論争誘発をしない
- **過度な省略**: 概念を犠牲にして短くしない

*文字数上限はプラットフォーム依存。実値は各 project overlay の rules が正本で、ここには書かない。*

*この節は**規範**（何を禁止するか）の正本。候補生成は `headline-craft`、凍結稿との契約判定は
`title-reviewer` が正本。生成と点検を同じ context で混ぜない。*

---

## Theme discovery boundary

テーマ未選択なら `session-theme-mining` を使う。同 skill は候補を問いとして発見し、採点・順位・
推薦を行わない。選択済みテーマの外部言説との差分は `theme-reviewer`、証拠の収集は
`collect-context`、本文への採否は editorial brief が持つ。受信指標を使う project でも、数値で
中心命題を変形しない。何を書くかの人間判断に使い、アイデアの中身を最適化しない。

## Section Length Guidelines

- 1 つのセクションが記事全体の 30% を超えたら分割を検討する
- セクション長は重要度に比例させる。主要な論点に厚く、補足に薄く
- 独立した論点が多すぎる記事は分割を検討する（**上限の数値は判定を出す側（`essay-reviewer`）が持つ** — ここには書かない）

---

## How to Extend (Project Overlay)

プラットフォーム固有ルール（文字数上限、タグ仕様、組織固有の禁止表現など）は **プロジェクトの rules/ に overlay** として置く:

```
<project>/.claude/rules/<publishing-channels>.md
```

contract は path matcher、読者、voice/register、reviewer panel、deterministic checks、title constraints、
publish handoff だけを持つ。本 skill の craft、AI slop、中心命題、因果線を再掲しない。

---

## Related

- `headline-craft` skill — 「開かせる一行」の候補生成技法（タイトル・tagline・subtitle・SNS 告知文）。規範は本 skill の Title Conventions、技法はあちら
- `title-reviewer` agent — 凍結稿とタイトル候補の契約点検（findings のみ。採否は著者）
- `theme-reviewer` agent — 選択済みの問いへの findings と深化の問い
- `prose-clarity-reviewer` agent — 初見読者の明瞭性と中心命題の貫通
- `quality-gate` skill — local contract の reviewer verdict と機械検査を集約
- `prose-translation` skill — 日英**双方向**の voice 保持翻訳（JA→EN / EN→JA。AI-slop / Voice / Title / 出典編入は本 skill に defer）
- `x-draft` skill — X 投稿の下書き。AI slop / Craft は本 skill に defer するが、**Voice は SNS register への意図的分岐**（記事の文体を持ち込まない）
- `public-comment` skill — 公開 thread への返信。genre 固有の追加規律だけを持ち、tell の正本は `references/style-diagnostics.md`
- `readme-writer` skill — **README / repo トップページ専用**。audience が「repo を開いた初対面の人」なら本 skill の初稿手順ではなくあちらを入口にする（Voice は ですます への意図的分岐）
- project-local publishing skill — platform UI / API / schedule / corpus update. 本skillは公開操作を持たない
- `editor` agent — 実用チャンネルのレビュー（構造・コード・AI slop・用語）
- `essay-reviewer` agent — エッセイチャンネルのレビュー（論理構成・過積載・トーン）
- `fact-checker` agent — 事実主張の Web 検証
- `llms-txt-writer` skill — **AI 向けドキュメント（llms.txt / llms-full.txt / FAQ 等）専用**。audience が AI なら本 skill ではなくあちらを使う

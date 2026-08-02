---
name: writing-ecosystem
description: 人間向け執筆・レビューエコシステムの orchestrator。記事・エッセイ・ブログポスト・ニュースレター等の **人間 primary** コンテンツを書く / レビューするときに使う。article-writing / editor / essay-reviewer / fact-checker の役割境界と使い分け、Craft 規約（文の技術）、AI slop 禁止リスト（日英）、Voice 規約（だ/である × 発見調）、エッセイ 4 段構成、タイトル規約を正本として保持する。AI 向けドキュメント（llms.txt 等）には `llms-txt-writer` を使う。
compatibility: Designed for Claude Code (or similar agent products). Orchestrates Claude Code subagents bundled in this repo's agents/ directory.
user-invocable: true
origin: shimo4228
---

# writing-ecosystem — 人間向け執筆・レビューエコシステムの正本

人間読者向けコンテンツ（記事・エッセイ・ブログポスト・ニュースレター等）の執筆とレビューに関わるコンポーネント（skill と agent）の役割境界・使い分け・共通規約をまとめた正本。

> `article-writing` skill の Banned Patterns を **包含する superset**。AI slop / Voice / タイトル規約は本ファイルを正とする。

## Scope

**人間 primary のコンテンツのみ扱う**。AI-facing ドキュメント（`llms.txt` / `llms-full.txt` / FAQ ページ等）には `llms-txt-writer` skill を使う。audience 判定と役割分担は [Audience Separation: Human vs AI](../llms-txt-writer/SKILL.md#audience-separation-human-vs-ai) を参照。

---

## Ecosystem Map

執筆関連コンポーネントは **「Write / Review」 × 「品質 / 論理 / 事実」** のマトリクスで役割分離されている。

| フェーズ | コンポーネント | 軸 | トリガー |
|---------|---------------|-----|----------|
| **Write** | `article-writing` skill | 汎用書き方 | 執筆タスク全般（初稿・構造設計） |
| **Translate** | `ja-to-en-translation` skill | 日本語→英語の voice 保持翻訳 | JA→EN 翻訳タスク時 |
| **Review: 品質** | `editor` agent | tech 記事の構造・コード・AI slop・用語 | tech 記事レビュー時 |
| **Review: 論理** | `essay-reviewer` agent | idea 記事の論理構成・過積載・トーン | idea 記事レビュー時 |
| **Review: 事実** | `fact-checker` agent | 事実主張の Web 検証 | 公開前検証時 |
| **Publish** | `substack-publishing` skill | Substack 公開 + LLM corpus ミラー | human essay を Substack に出すとき |
| **Shared** | `writing-ecosystem` skill | AI slop / Voice / エコシステム map | 執筆 + レビュー時（自動発火） |
| **Overlay** | `<project>/.claude/rules/*.md` | プラットフォーム固有ルール | プロジェクト内作業時のみ |

---

## When to Use What

```
┌─ 初稿作成 ─────────────────────────────────┐
│ article-writing skill                      │
│  → 構造・Voice・基本的な禁止表現           │
└──┬─────────────────────────────────────────┘
   │
   ▼
┌─ 記事の type で分岐 ───────────────────────┐
│                                            │
│  tech 記事（code/tutorial）                │
│   → editor agent                           │
│                                            │
│  idea 記事（essay/opinion）                │
│   → essay-reviewer agent                   │
│                                            │
│  両方含む mixed                            │
│   → 両方並列で実行                         │
│                                            │
└──┬─────────────────────────────────────────┘
   │
   ▼
┌─ 事実チェック（任意、tech/idea 問わず） ───┐
│ fact-checker agent                         │
└──┬─────────────────────────────────────────┘
   │
   ▼
┌─ 出典編入（fact-check 後） ────────────────┐
│ Citation & Sources Workflow（下記セクション）│
└────────────────────────────────────────────┘
```

### エージェント並列実行の原則

`editor` と `essay-reviewer` は **観点が異なる** ので、mixed 記事では両方並列実行したほうがカバレッジが高い。`fact-checker` は常に並列で回せる。

### 翻訳タスクの場合

日本語記事を英語にするときは、初稿の `article-writing` ではなく `ja-to-en-translation` skill を入口にする。翻訳 → EN 出力を `essay-reviewer`（idea）/ `editor`（tech）でレビュー、という流れ。英語側の AI slop / Voice 規約は本 skill を正本として参照する（翻訳 skill は再掲せず defer する）。

### Substack へ公開する場合

レビュー（+ 必要なら翻訳・出典編入）が済んだ human essay を Substack に出すときは `substack-publishing` skill を使う。Substack は raw Markdown 非対応なので MD→HTML 変換して貼る、Title / Subtitle / body をフィールド分けする、タグ spine とカバー画像、公開後に LLM corpus（content repo の `substack/`）へミラーする、までを扱う。

---

## Citation & Sources Workflow（出典をエッセイに入れる）

fact-check で確定した一次資料を、**本文の出典セクションに編入する**のがエッセイ公開前の標準ステップ。現状この step が抜けやすいので明文化する。

### 所有と分離

- **embedding はこのワークフローが所有する**。`fact-checker` は report-only（記事を編集しない / author-reviewer 分離）のままで、検証済みソースを「出典セクションに落とせる形」で返すだけ。本文への編入は著者 / orchestrator が行う。
- `fact-checker` の出力（verdict が ✅ / ⚠️ のソース URL 群）が canonical input。

### 手順

1. fact-check 通過後、verdict が ✅ ACCURATE / ⚠️ PARTIALLY のソースを集める（❌ / ❓ のソースは載せない）。
2. **テーマ別にグループ化**し、重複 URL を排除、**一次資料を優先**（official / 原典 / academic > 二次報道）。
3. 本文末に出典セクションを作る。
4. 本文で著者自身の既発表（DOI / repo / 論文）に言及していれば、それも出典に含める。

### 媒体別ポリシー

| 媒体 | 出典の置き方 |
|---|---|
| idea / opinion essay | 末尾に `## 出典・参考文献`。テーマ別グループ、一次資料優先 |
| tech 記事 / tutorial | 本文中の inline link を基本に、必要なら末尾に補助的な References |
| 学術 paper | 本ワークフローではなく `citation-formatter` agent（in-text ↔ reference の 1:1・format・DOI 検証） |

### 翻訳記事の出典

`ja-to-en-translation` で訳した記事は、原文の出典セクションを引き継ぐ。**URL / DOI は保持**し、description のみ英訳する。

### 自リポ言及の節度（本文内の self-link 制限）

著者自身のリポジトリ・ツール・過去成果物への**本文中リンク**は、次のいずれかに該当するときだけ置く:

1. **導線** — 読者がその場で手を動かすためのリンク（install 手順、テンプレ・コードの配布元）
2. **一次資料** — 直前の主張を支える証拠リンク（CHANGELOG・commit・検証ログ・issue）

該当しない「概念の出典クレジット」型の言及（「私が公開している X で定式化しています」等）は宣伝臭を生む。その場合:

- リンクは末尾の関連リンク / 出典セクションへ寄せる
- 本文では無名で概念を説明するか、プロジェクト名を名乗るだけに留める（リンクなし）

判定手順: 公開前に本文中の自リポリンクを数え、各リンクに「導線 / 一次資料」のどちらかのラベルが付くか確認する。付かないリンクは末尾へ移す。**同一 repo への本文リンクは 1 記事 1 回まで**（末尾セクションは対象外 — そこが正規の置き場）。

背景: 導線・証拠としてのリンクは読者への価値だが、クレジット目的のリンクは著者への価値でしかない。読者価値のないリンクが増えるほど、導線リンクまで宣伝に見えてくる。

---

## Craft 規約（文の技術）

genre 中立 — essay / 実用記事の両チャンネルに適用する。出典: Kaguura Gichuru "How I Got 20,585 Substack Subscribers in 90 Days" (The Write Path, 2026-07) の craft 原則を日本語適用形に翻案（2026-07-30 取り込み。経緯: zenn-content ADR）。

- **単数の読者へ書く** — 「皆さん」「みなさんも〜ですよね」と集団に呼びかけない。読者は一人で読んでいる。一人の読者への手紙として書くと、文が自然に直接的になる
- **副詞を削り、強い動詞へ** — 「とても・非常に・かなり・しっかり」等の程度副詞は弱い動詞の松葉杖。「急いで走った」→「駆け抜けた」。数値で言えるなら数値で言う（「大幅に減った」→「40% 減った」）
- **能動態を既定にする** — 「〜が注目された」→「X が〜に注目した」。文に勢いが出る。受動態は行為者を意図的に伏せたいときだけ
- **平易語 > 格式語** — 知的に見せるための硬い語を使わない（「活用する」→「使う」、「実施する」→「やる」）。抽象語は絵になる具体イメージに置き換える（「低賃金労働」→「日給 10 ドルで土を掘る」）
- **10% 編集ルール** — 第 2 稿 = 第 1 稿 − 10%。削る対象: 冒頭の warm-up（執筆理由・背景説明の前置き）、中盤の繰り返し、つなぎ語。判定: その文は論点を前に進めているか。進めない文は読者のリテンションを削る
- **スペーシング = 視覚的句読点** — 文の壁は「宿題」に見えて離脱される。ただし全行独立（LinkedIn 型の 1 行 1 段落）はロボット臭。短い文で加速し、3-4 文の段落で減速する — このばらつきがリズムを作る（構造 tell の「等間隔リズム」回避と同根）
- **密度 > 字数** — word count は vanity metric。指標は 1 文あたりの情報量（intellectual density）。目安 800-2,000 語で、複雑なアイデアの説明と読者の時間の尊重を両立する
- **Input エンジン** — 浅い input からは浅い執筆しか出ない。深い読書（書籍・歴史・一次資料）を執筆の前提にする

---

## AI Slop 禁止リスト

### 判定原則

> その表現を別の記事にそのまま挿入しても意味が通るなら、それは AI slop。

著者の具体的な観察・経験・数値を伴わない汎用表現を使わない。

### 日本語

| 禁止語 | 代替アプローチ |
|-------|-------------|
| 画期的 | 具体的に何が変わったかを書く |
| 革命的 / 革新的 | 従来との差分を数値や事例で示す |
| 素晴らしい | 何がどう良いのかを具体的に書く |
| 驚くべき | 何に驚いたか、なぜ予想外だったかを書く |
| 感動的 | 何が心を動かしたかを描写する |
| シームレス | 実際のユーザー体験を書く |
| パワフルな / ロバストな | 性能指標や具体的な強みを示す |
| レバレッジする / 活用する（漠然と） | 具体的にどう使うかを書く |
| 本質的な問いを投げかける | 問い自体を書く |
| 深い洞察 / 示唆に富む | 洞察の内容を直接書く |
| パラダイムシフト | 何がどう変わったかを書く |
| 重要な示唆を与える | 示唆の内容を具体的に書く |
| 最先端の / 先進的な | 何が新しいかを具体的に書く |

### English

| Banned | Alternative |
|--------|------------|
| powerful tool | describe what it actually does |
| revolutionize / revolutionary | describe the specific change |
| cutting-edge | describe what makes it novel |
| game-changer | describe the concrete impact |
| seamless / seamlessly | describe the actual user experience |
| leverage | use "use" or describe the specific action |
| robust | describe what it handles well |
| effortlessly | describe the actual effort required |
| In today's rapidly evolving landscape | start with the concrete thing |
| Moreover / Furthermore | connect ideas directly without filler transition |
| at the end of the day | cut or rewrite |

*最後の 3 項目は `article-writing` skill の Banned Patterns を包含。本リストは superset。*

### 文体・構造 tell（2026-07 追補）

前提: 2026 年時点で AI 使用は執筆の前提であり、tell は「AI 使用の証拠」ではなく「**未レビューの生ダンプ**」のシグナルとして読まれる。tell の除去は偽装ではなく、人間の判断が通った痕跡の可視化。

構造 tell の判定原則（語彙の判定原則と対）:

> 内容を変えずに形だけ真似できるパターンは tell（語彙は消せるが、リズムは残る）。

構造 tell（語彙より優先度高）:

| Tell | 対処 |
|------|------|
| 「It's not X, it's Y」対比構文 / 「〜ではなく〜だ」の決め構文 | 2026 年中盤で最も認知された構造 tell。主張の形だけ生成された兆候。主張を直接書く |
| 3 点セット列挙（rule of three） | 「costs three things」型の予告つき triad、formulaic な 3 項 bold リスト。実内容が本当に 3 つある場合のみ、予告なしで書く |
| em-dash（—）多用 | 「ChatGPT hyphen」。文の再構築（短文化・文長のばらつき）で代替。`:` / `;` への機械置換は禁止 — 等間隔リズムは記号が変わっても同じ指紋 |
| bold 見出し + 本文の等間隔リズム反復（3 連以上） | 段落の長さと形をばらつかせる |
| 箇条書き過多 | prose で足りる内容をリスト化しない |
| Claude-ism hedging（"It's worth noting" / "Generally speaking" / "While this may vary"） | 断定するか削る |
| 追従オープナー（"Great question!" / "You're absolutely right" / 「素晴らしい質問ですね」） | 本題から始める |
| 無内容クローザー（"Hope this helps!" / 「参考になれば幸いです」「いかがでしたか」） | 最後の実質的な文で終える |
| 絵文字 | 使わない（プラットフォームの明示的文化がある場合を除く） |

語彙追補（radioactive vocab、上の表に追加）:

- 英: delve / multifaceted / holistic / transformative / ever-evolving / testament to / dive into / deep dive / pivotal / landscape（比喩用法）/ tapestry / boasts / meticulous / unlock / harness / unleash / empower / paradigm
- 日: 「〜と言えるでしょう」/「〜ではないでしょうか」（修辞疑問の乱用）/「深掘り」

網羅リストの正本は複製しない。コミュニティリスト [AlpinDale/gptslop](https://github.com/AlpinDale/gptslop)（GPT/Claude 頻出句、~800 句規模の Antislop 系評価の基盤）を参照。

---

## Voice & Tone Rules

### 文体: だ/である調 × 発見調

type（tech / idea）にかかわらず、**だ/である調 × 発見調** で統一する。

| 使う表現（発見調） | 避ける表現（宣言調） |
|---------------|-------------------|
| 「〜だった」「〜と気づいた」 | 「〜すべきだ」 |
| 「〜と感じた」「〜に見えた」 | 「〜に違いない」 |
| 「気づいたらそうなっていた」 | 「〜を示している」 |
| 「少なくとも方向としては悪くない」 | 「設計は正しかった」 |

### 未解決の正直さ

解決していない問題は解決したふりをしない。「まだわからない」「今後の課題」と正直に書く。完璧な結論に無理に収束させない。

### 感情語の扱い

- **タイトル**: 禁止（「壊れている」「地獄」「最強」など）
- **本文**: 著者の自然な体験描写なら OK（「正直つらかった」「ここで詰まった」）

### 結論の問い化（初期経典の語り口）

結論が明らかな主張は、断定するより **修辞的疑問** にしたほうが説得力が増す。読者が自分で結論に到達した感覚を持つからだ。釈尊の初期経典（阿含経・ニカーヤ）の語り口がモデルになる。仏陀は「これは〜である」と叩きつけず、「比丘たちよ、これをどう思うか?」と問いを投げかけ、聞き手から答えを引き出していった。同じ結論でも、断定で受け取る読者と、問いに自分で答える読者では、納得の質が違う。

#### 断定 → 弱化の対応表

| 元の断定 | 弱化形 | 用途 |
|---------|-------|------|
| 「〜だ」「〜である」 | 「〜のではないか」 | 主張・立論 |
| 「〜だ」 | 「〜と読める」「〜として読める」 | 観察 |
| 「〜になる」「〜だ」 | 「〜ように見える」「〜になっているように見える」 | 評価 |
| 「〜は X だ」 | 「〜は X ではないか」 | 評価 |
| 「理由はない」「正当だ」 | 「理由はどこにあるのか」「正当に見える」 | 結論 |
| 「主張は X だ」 | 「問いをひと言で言えば、X、ということだ」 | 立論を問いで包む |

#### 戦略的に弱化する箇所

全部を疑問形にすると記事が「問いだらけ」になりノイズが増える。戦略的に選ぶ。

**弱化する**:
- タイトル（読まれる前の入口。断定タイトルは押し付けがましい）
- 主張の核フレーズの繰り返し（2 回目以降は弱める。同じ強度で繰り返すと説教臭くなる）
- 結論の評価語（「正当だ」「明確だ」「正確だ」「行為だ」など）
- 結論段落・「おわりに」の断定

**維持する**:
- 著者の確信が強い具体観察（事実・数値・固有名詞を伴う発言: 「Devin は 24/7 稼働している」「OpenAI Deep Research は最大 30 分」など）
- 議論の積み上げの中間的観察（「〜と決まる」「〜が動くだけだ」「〜知っている」）
- 概念指示（「時間軸だ」「設計フェーズだ」 — 概念の指し示しは断定でよい）

### エッセイの 4 段構成（Hero's Journey 型）

essay の既定構成（出典: Kaguura 2026。Craft 規約と同じ取り込み）:

1. **Calm Story** — 技術・理論から入らず、シンプルで関連性の高い人間的ストーリー・具体的シーンで開く。低認知負荷で読者を著者の声に慣れさせる。冒頭数段落で執筆理由や背景を説明する warm-up は削除し、行動の最中に読者を投入する
2. **Plunge（緊張）** — 読者が乗ったところで、大きな問題・不都合な真実・パラドックスを提示する。緊張が途中離脱を難しくする
3. **Solution** — フレームワーク・中核ルールを提示して読者を引き上げる
4. **Higher Ground** — 開始時より高い位置で終える。読者が「学んだ」と感じて読み終える。既存の「未解決の正直さ」「結論の問い化」と両立する — 自分を未解決のまま残すことは人間の宣言であり、それ自体が Higher Ground になる

#### 三段階の問い構造（参考パターン）

記事を通じて問いを階層化すると、読者は段階的に思考する:

1. **入口**: タイトル（疑問形 — 「〜は必要か」「なぜ〜か」）
2. **立論の輪郭**: 序盤で主張を問いの形で提示（「問いをひと言で言えば、〜のではないか、ということだ」）
3. **議論途中の修辞的疑問**: 具体例を並べた直後に投げ返す（「〜する理由はどこにあるのか」）

この三段が揃うと、結論を著者が叩きつけずに、読者と並走しながら同じ結論に至る構造になる。

---

## Title Conventions

### 目的

読み手がタイトルだけで「この記事が何の概念を提案しているか」を理解できること。

### 基本ルール

- **具体性**: 何についての記事かがタイトルだけでわかる
- **誠実さ**: 記事の内容以上のことを約束しない
- **結果駆動**: トピック名でなく読者が得る結果を前に出す（「〜の分析」より「〜が…できるようになる中身」）。具体的数値・詳細は指を止める — 実測の裏付けがあれば積極的に使う
- **問いの形**: 「どう〜するか」「なぜ〜か」は知的関心に訴える — 活用 OK

### 禁止事項

- **煽りタイトル**: 「壊れている」「地獄」「最強」などの感情語でクリックを誘わない
- **空の listicle 数字**: 実測の裏付けなく数字で釣る形（「N 選」「N 倍」）。実測値・件数を証拠として出す具体的数字（「1,000 件を分析したら〜」）はむしろ推奨 — 判定は「その数字は記事の中身の証拠か、器の飾りか」
- **詩的・教科書的タイトル**: 意味が取れない詩的タイトル（素通りされる）と、「〜の分析」「〜に関する考察」型の教科書調（宿題に見える）
- **挑発・断定**: 「〇〇の真価は△△ではない」式の論争誘発をしない
- **過度な省略**: 概念を犠牲にして短くしない

*文字数上限はプラットフォーム依存。プロジェクト overlay で定義する（例: Zenn は 50–60 字）。*

*この節は**規範**（何を禁止するか）の正本。候補を**作る技法**（具体性・ベネフィット前置・誠実な好奇心ギャップ・流入経路 2 軸評価）は skill: `headline-craft` が正本 — 生成された候補は必ずこの節のフィルタを通す。*

---

## Article Topic Selection (3-axis)

執筆を始める前のネタ選定にも 3 軸を当てる。「書きたいこと」だけで選ばない。

| 軸 | 問い |
|----|------|
| **検索需要** | そのキーワードを検索する人がいるか |
| **競合の少なさ** | 既存記事が少ない or 差別化できる角度があるか |
| **一次情報** | 自分の体験・失敗・数字を持っているか |

**優先度**: 検索需要高 + 競合少 + 一次情報あり → 最優先（ブルーオーシャン）。

**Anti-Patterns**:
- 「書きたいこと」だけで選んで検索需要を確認しない
- 競合が多いからと諦める（一次情報で差別化可能）
- 3 軸全部が揃うのを待つ（「体験を作ってから書く」で無期限延期になる）

## Section Length Guidelines

- 1 つのセクションが記事全体の 30% を超える場合は、分割を検討する（ハードルールではなく目安）
- セクション長は重要度に比例させる。主要な論点に厚く、補足に薄く
- 1 つの記事に独立した論点が 4 つを超える場合は、記事の分割を検討する

---

## How to Extend (Project Overlay)

プラットフォーム固有ルール（Zenn の文字数上限、Qiita のタグ仕様、社内ブログの禁止表現など）は **プロジェクトの rules/ に overlay** として置く:

```
<project>/.claude/rules/<platform>-writing.md
```

例:
- `zenn-content/.claude/rules/zenn-writing.md`
- `company-blog/.claude/rules/corp-writing.md`

overlay 側のファイル冒頭に「本 skill を base とする」旨を明記し、追加ルールだけ書く。base の AI slop / Voice は overlay で再掲しない。

---

## Related

- `article-writing` skill — 執筆時の汎用フレームワーク（本 skill の Banned Patterns を包含）
- `headline-craft` skill — 「開かせる一行」の候補生成技法（タイトル・tagline・subtitle・SNS 告知文）。規範は本 skill の Title Conventions、技法はあちら
- `ja-to-en-translation` skill — 日本語→英語の voice 保持翻訳（英語 AI-slop / Voice / Title / 出典編入は本 skill に defer）
- `substack-publishing` skill — Substack 公開 + LLM corpus ミラーのワークフロー（Voice / AI-slop / Title / 出典は本 skill に defer）
- `editor` agent — tech 記事レビュー（構造・コード・AI slop・用語）
- `essay-reviewer` agent — idea 記事レビュー（論理構成・過積載・トーン）
- `fact-checker` agent — 事実主張の Web 検証
- `llms-txt-writer` skill — **AI 向けドキュメント（llms.txt / llms-full.txt / FAQ 等）専用**。audience が AI なら本 skill ではなくあちらを使う

---
name: writing-ecosystem
description: 人間向け記事・エッセイ・ブログポスト・ニュースレターの唯一の執筆 orchestrator。project の publication channel contract を読み、中心命題 1 つの editorial brief、因果線、証拠の選択と除外、構成、執筆、title-reviewer、review panel、quality-gate、著者 GO までを統括する。Use when — 「この記事を書いて」「このテーマでエッセイにして」「原稿の論点を一つに絞って構造改稿して」のような新規執筆・全体改稿・全文の別 channel 展開。NOT for — 一文や段落だけの翻訳（→ prose-translation）、title だけ（→ headline-craft / title-reviewer）、SNS 下書き（→ x-draft）、公開 thread 返信（→ public-comment）、AI 向け docs、README、paper、媒体固有の公開操作。
compatibility: Designed for Claude Code (or similar agent products). Orchestrates globally installed agents under ~/.claude/agents/.
user-invocable: true
origin: shimo4228
---

# writing-ecosystem — 人間向け執筆・レビューエコシステムの正本

人間読者向けコンテンツ（記事・エッセイ・ブログポスト・ニュースレター等）の執筆とレビューに関わるコンポーネント（skill と agent）の役割境界・使い分け・共通規約をまとめた正本。

> AI slop / Voice / タイトル規約・執筆フローは本 skill directory が正本。詳細診断表だけ
> `references/` へ分離し、必要な phase で読む。

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

中心命題、主張、構成は著者の判断が決める。受信指標やdistribution施策は、何を書くか、titleの
語選び、tags、timing、language placementを変えられるが、数字のために本文の命題・導入・見出し・
toneを変形しない。reviewerの具体的な品質findingに基づく修正はdistribution最適化ではなく品質改善
として扱う。タイトル・tags・timingを変えるcomponentは本文を編集しない。

---

## Ecosystem Map

執筆関連コンポーネントは **「Write / Review」 × 「品質 / 論理 / 事実」** のマトリクスで役割分離されている。

| フェーズ | コンポーネント | 軸 | トリガー |
|---------|---------------|-----|----------|
| **Theme discovery** | `session-theme-mining` skill | Claude / Codex 履歴横断から 0〜3 件の同格な問いを発見し、著者の選択で止まる | 執筆スコープがまだ決まっていないとき |
| **Theme review** | `theme-reviewer` agent | 選択済みの問いへ findings と深化の問いを返す。合否は出さない | editorial brief の前 |
| **Pre-write** | `collect-context` skill | 素材収集と証拠台帳（Claims Register / 一次・⚠未検証の tier）。編集判断はしない | 執筆前に素材を集めるとき |
| **Write** | 本 skill「editorial brief と執筆フロー」 | 中心命題・因果線・証拠選択・構成・執筆 | 初稿・改稿 |
| **Title generation** | `headline-craft` skill | 「開かせる一行」の候補生成 | 本文の構造凍結後 |
| **Title review** | `title-reviewer` agent | 本文との契約を fresh context で点検し findings を返す | review panel の前 |
| **Review: 品質** | `editor` agent | 記事の構造・コード・AI slop・用語 | 実用チャンネルのレビュー時 |
| **Review: 論理** | `essay-reviewer` agent | エッセイの論理構成・過積載・トーン | エッセイチャンネルのレビュー時 |
| **Review: 初見明瞭性** | `prose-clarity-reviewer` agent | 第一画面・中心命題・内部文脈依存 | title 選択後 |
| **Review: 事実** | `fact-checker` agent | 事実主張の Web 検証 | 公開前検証時 |
| **Acceptance** | `quality-gate` skill | local contract の reviewer verdict と機械検査を集約 | 公開直前 |
| **Publish** | project-local publishing skill | platform API / UI / schedule / corpus 更新 | 著者 GO 後 |
| **Overlay** | `<project>/.claude/rules/*.md` | チャンネル固有の事実・配線 | プロジェクト内作業時のみ |

一文・一段落の翻訳、title だけ、SNS、公開 thread、README、paper はこの flow に入れず、それぞれの
専用 skill へ直接 route する。

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

### 4. Freeze, title, and review

本文の構造を凍結してから `headline-craft` で候補を作り、`title-reviewer` の findings を見て著者がタイトルを選ぶ。
その後、local contract の channel reviewer、`prose-clarity-reviewer`、`fact-checker`、必要な
cross-model review を同じ最終タイトル + 本文へ実行する。editor と essay-reviewer の両方を
回すのは contract が要求する場合だけ。

review 修正が central thesis、causal spine、主要節を変えたら brief → title-reviewer → 関係 reviewer
へ戻る。表現修正だけなら title-reviewer を再実行しない。

### 5. Final structural pass and acceptance

著者通読前に次を確認する:

- タイトルまたは結論になりうる独立命題を列挙し、支配的なものが一つだけ
- 全主要節が central thesis を前へ進める
- `N reasons` と `N questions` を対応させるなら 1:1。対応しない列挙を鏡像にしない
- summary / conclusion が新しい基準・命題を導入しない
- out-of-scope が本文へ戻っていない

`quality-gate` が local contract の証跡を集約して PASS を出した後、著者が公開 GO を判断する。
公開操作は contract が指す project-local publishing skill に渡す。

---

## Citation & Sources Workflow（出典をエッセイに入れる）

fact-check で確定した一次資料を、**本文の出典セクションに編入する**のがエッセイ公開前の標準ステップ。現状この step が抜けやすいので明文化する。

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

引用に要求される検証の深さは、**引用が何を主張するか**と**ジャンル**で決まる（2026-08-05 確立。経緯: attention-not-self テーマ9 の Froese 2026 引用）。

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

genre 中立 — essay / 実用記事の両チャンネルに適用する。出典: Kaguura Gichuru "How I Got 20,585 Substack Subscribers in 90 Days" (The Write Path, 2026-07) の craft 原則を日本語適用形に翻案。

- **単数の読者へ書く** — 「皆さん」「みなさんも〜ですよね」と集団に呼びかけない。読者は一人で読んでいる。一人の読者への手紙として書くと、文が自然に直接的になる。禁止形だけでなく積極形も守る（下記「語りかけの積極形」）
- **副詞を削り、強い動詞へ** — 「とても・非常に・かなり・しっかり」等の程度副詞は弱い動詞の松葉杖。「急いで走った」→「駆け抜けた」。数値で言えるなら数値で言う（「大幅に減った」→「40% 減った」）
- **能動態を既定にする** — 「〜が注目された」→「X が〜に注目した」。文に勢いが出る。受動態は行為者を意図的に伏せたいときだけ
- **平易語 > 格式語** — 知的に見せるための硬い語を使わない（「活用する」→「使う」、「実施する」→「やる」）。抽象語は絵になる具体イメージに置き換える（「低賃金労働」→「日給 10 ドルで土を掘る」）
- **10% 編集ルール** — 第 2 稿 = 第 1 稿 − 10%。削る対象: 冒頭の warm-up（執筆理由・背景説明の前置き）、中盤の繰り返し、つなぎ語。判定: その文は論点を前に進めているか。進めない文は読者のリテンションを削る
- **スペーシング = 視覚的句読点** — 文の壁は「宿題」に見えて離脱される。ただし全行独立（LinkedIn 型の 1 行 1 段落）はロボット臭。長さをばらつかせてリズムを作る（構造 tell の「等間隔リズム」回避と同根）。**段落長の閾値は下記「段落密度の機械的閾値」が持つ — ここには書かない**
- **密度 > 字数** — shared word target は置かない。指標は 1 文あたりの情報量で、長さの上限は local contract が持つ
- **Input エンジン** — 浅い input からは浅い執筆しか出ない。深い読書（書籍・歴史・一次資料）を執筆の前提にする

### 語りかけの積極形（単数の読者の二人称側）

「皆さん」の禁止だけでは、誰にも語りかけない中立解説文が通ってしまう（2026-08-20 著者指摘 — 禁止形と機械検出だけが残り、読者へ語りかける側の指示が落ちていた）。

- **掴みと結論の少なくとも一方で、読者に直接語りかける文を 1 箇所以上置く。** 形は 3 つ — 読者の状況を名指す問い（「レビューは全部通ったのに、公開ボタンの前で不安が残っていませんか」型）、直接の指示（「まず〜を確認してください」型）、読者主語の約束（「読み終える頃には〜を自分で判断できます」型）
- **判定基準は「真に迫っているか」** — 読者が「自分のことを言われている」と感じるか。それを作るのは文型ではなく、読者の状況の**名指しの正確さ**。誰にでも当てはまる一般論の問い（「効率化したいと思いませんか」）は、語りかけの形をした集団呼びかけでしかない
- **「あなた」の連発は不要** — 日本語は主語省略のまま二人称に語れる（問い・指示・約束はどれも主語なしで読者に向く）
- **全文に機械的に散らさない** — 語りかけの量産は over-editing で声を殺す（Kaguura 7.2）。掴み・結論・節の転換点など、読者の注意を取り直す場所に絞る
- **チャンネル差** — 実用記事（直接指示）は指示形が自然に多い。essay（発見調）では「〜ではないか」の問い化が語りかけを兼ねるので、マーカーが少なくても手紙として読めれば足りる

判定: 完成後、掴みと結論を読み、読者に向いた文（問い・指示・約束）があるか、その文が読者の具体的状況を名指しているか（一般論なら書き直し）を確認する。

### 段落密度の機械的閾値（改行規約）

「スペーシング = 視覚的句読点」の原則を、自己レビュー時に機械的に確認できる閾値へ落とす。原則を知っていても、書いている最中は密度を自覚しにくい。

- **既定は 1 段落 1〜2 文**（2026-08-06 著者承認で改定。旧既定「1 段落 1 ビート」でも読みにくいとの著者体感 + note スマホ縦読み相場「1 段落 = スマホ表示 2〜4 行、3 行前後で区切る」に合わせ、全チャンネル共通の既定へ）。3 文入ったら分割を検討する。畳みかけ・並列の短い断片（「訴訟、補償、規制。」型）は 3 文でも 1 段落にまとめてよい
- **1 文段落を積極的に使う** — 問い・場面転換・結論は 1 文で独立させる
- **段落間は空行 1 行**。連続空行でテンポを崩さない。段落内の強制改行（文の途中の手動改行）はしない — 折り返しは画面幅に任せる
- **2 つ以上の対象を比較・対比する文は、箇条書き化を優先**（並列構造は箇条書きの方が一読で伝わる）
- **em dash（——）で従属節を 1 つの文に埋め込んでいたら、2 文に割れないか確認する**
- **文長をばらつかせる** — 短文で加速し、2 文段落で減速する。等間隔リズムは構造 tell

判定: 完成後、各段落を上から数え、3 文以上（断片の畳みかけを除く）・比較の地の文埋め込みのいずれかに該当する段落がないか通し読みで確認する。

### 専門用語の緩和策

見出し・地の文に専門用語（造語・業界ジャーゴン・外来概念）を置くときは、以下から状況に合うものを選ぶ。1 本で複数を組み合わせてよい。

1. **初出定義** — 用語が最初に出た瞬間に平易な言い換えを併記する
2. **見出しには専門用語を出さない** — 見出しは離脱の分岐点。難語は本文に落とす
3. **具体→抽象の順で出す** — 先に具体的な現象・実例を見せ、名前は後からつける
4. **反復して意味を定着させる** — 一度定義したら同じ語を使い続ける（類義語に逃げない）
5. **用語自体を捨てる** — 使い回さない造語は、定義するコストをかけるより平易に言い換える方が安い（**回数の閾値は持たない** — binding な判定を出す clarity reviewer 側が持つ）
6. **既存概念の系譜に anchor する** — 確立済みの概念に由来するなら初出で系譜を明示する。逆に定着語を和語に言い換えると独自機構に見える — 界隈の定着語をそのまま使う
7. **英語直訳語を警戒する** — floor →「床」のような直訳は違和感を生む。意味の通る日本語の技術語に置き換える

追加: **見出し・地の文で英語の名詞句を 2 つ以上そのまま繋げない**（「read-only な second opinion を一発で」等）。カタカナ化するか日本語に訳す。固有名詞・製品名・コード内ラベル・一貫使用の定着語は例外。

判定: 完成後、専門用語をリストアップし、説明なしで見出しにだけ登場する語がないか機械的にチェックする。

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
| エッセイ / オピニオン | **[エッセイの 4 段構成](#エッセイの-4-段構成hero-journey-型) が正本**。1 節 1 論点、意見を支える実例を置く |
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
無内容な opener / closer を使わない。単語一致だけで誤検知せず、その表現がこの原稿固有の仕事を
しているかで判断する。draft または reviewer がこの兆候を見つけたときだけ
[`references/style-diagnostics.md`](references/style-diagnostics.md) を読み、言語別の例と修正方向を適用する。

---

## Voice & Tone Rules

### Voice は channel contract が持つ

実用記事の直接指示、essayの発見調、その他のregisterをglobal既定で上書きしない。local contractが
宣言したvoiceを使い、著者の具体観察・確度・未解決範囲を保つ。

**語尾（ですます / だ・である）の実値は本 skill が持たない。** project の publication
channel contract が正本。記事全体の task で contract が無ければ推測しない。

contract が発見調を宣言する場合だけ、次を診断例として使う。

| 使う表現（発見調） | 避ける表現（根拠以上の宣言） |
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

AI が実際のテキスト生成を担った記事（AI-mediated writing）は、**記事末に開示ブロックを置く**。要素: (1) AI-mediated である旨の明言、(2) 原稿の来歴、(3) 主張・判断・責任が著者に帰属すること、(4) 準拠方針への参照。媒体固有のブロック記法が使えなければプレーンな段落 + 強調で書く。

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

- 1 つのセクションが記事全体の 30% を超える場合は、分割を検討する（ハードルールではなく目安）
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
- `readme-writer` skill — **README / repo トップページ専用**。audience が「repo を開いた初対面の人」なら本 skill の初稿手順ではなくあちらを入口にする（Voice は ですます への意図的分岐）
- project-local publishing skill — platform UI / API / schedule / corpus update. 本skillは公開操作を持たない
- `editor` agent — 実用チャンネルのレビュー（構造・コード・AI slop・用語）
- `essay-reviewer` agent — エッセイチャンネルのレビュー（論理構成・過積載・トーン）
- `fact-checker` agent — 事実主張の Web 検証
- `llms-txt-writer` skill — **AI 向けドキュメント（llms.txt / llms-full.txt / FAQ 等）専用**。audience が AI なら本 skill ではなくあちらを使う

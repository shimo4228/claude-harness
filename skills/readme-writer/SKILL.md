---
name: readme-writer
description: README やプロジェクトのトップページ（repo を開いた人が最初に見る入口）を書く・直す・判定するときに使う。こんな時に呼ぶ — README が長い／継ぎ足しで文脈が重くなり初見で分からない、開いて数十秒で「何のプロジェクトで自分向けか」が伝わる入口にしたい、冒頭に一目で仕組みが分かる図を置きたい、著者のほかの仕事への導線を付けたい、コードの変更に README を追従させたい、README を判定だけしてほしい、GitHub の About（description / topics / homepage）が README と食い違っている。CLI でも研究 repo でも、日本語でも英語でも対象。AI 専用ドキュメント（llms.txt 等）は → llms-txt-writer、記事・エッセイは → writing-ecosystem、release に伴う version・DOI・数値の同期は → release-doi、文書間の役割の重なりの整理は → context-sync、tagline だけ欲しいときは → headline-craft。
compatibility: Requires Python 3.11+ and uv. Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
user-invocable: true
origin: shimo4228
---

# readme-writer — Human-Facing README Skill

人間に向けた README を書く・改善するスキル。`llms-txt-writer` が AI 専用 surface を担うのに対し、
本 skill は **人間 surface の単一正準入口**を担う。

重要な事実: **README は、grounding 経路（AI 検索 / チャットに repo URL を貼る）で LLM が確実に
前提にできる唯一の surface でもある**。そのため README は「人間向けに短く・走査しやすく」しつつ
「LLM が README 一枚だけ読んでもプロジェクトを復元できる小さな情報フロア」を必ず残す。
この両立が本 skill の中心課題（較正と出典は `inspiration.md`）。

## モード — 依頼の大きさで選ぶ

| モード | いつ | やること |
|---|---|---|
| **Rewrite** | 新規作成・全面的な作り直し | Workflow の全工程 |
| **Incremental** | コードの変更に README を追従させる（implementation-chain の Doc Sync から来る） | 変わった節だけを書き換え、証拠 JSON → readme-judge（mode: draft。変えた節の名前を渡し、判定器が自分で質問を作る）。概要図は仕組みが変わったときだけ描き直す |
| **Review-only** | 「この README を見て」「判定だけ」 | 証拠 JSON → readme-judge（mode: draft）。書き換えない |
| **About-only** | description / topics / homepage だけ | Workflow Step 6 だけ（`references/about.md`） |

使わない場面: social-preview 画像の作成（どの skill も作らない。著者が GitHub の設定で置く）、
外部ディレクトリ・awesome-list への掲載申請、graph.jsonld の設計（→ `jsonld-knowledge-graph`）。

---

## 軸は「人間の ATTENTION × LLM の INFORMATION」

README 最適化の対立軸は「人間向け情報 vs LLM 向け情報」ではない。**人間の注意（短く・掴む・走査
できる）× LLM の情報（README だけで復元できる）**である。両者は同じ施策に収束するので、
トレードオフでなく**設計で両取りする**。

- AI 検索 / 引用クローラは llms.txt を実質読まず、`graph.jsonld` は直接 fetch では plain text 扱い。
  README の情報は機械層に頼らず README の中に置く（較正: 「LLM は README しか読まない」は強すぎる。
  routed coding agent は llms.txt を on-demand で読む — 詳細は `inspiration.md`）
- **two-sided rule**: アイデアが*どう伝わるか*は最適化してよい（見出し階層・entity anchoring・
  answer-first の lead）。アイデアが*何であるか*は曲げない（keyword stuffing・疑問見出し farming・
  glossary 投下・主張の歪曲をしない）。star や引用は成功指標ではない

---

## 証拠と判定（code は数える、LLM は判定する）

| 層 | 何を出すか | 所有者 |
|---|---|---|
| **証拠** | 第一画面の行数と新語、内部参照、造語候補、`<details>` の中身、図の前後の prose、切れたリンクと anchor、内部史・生数値の行、slop 語、日本語版の文末 | **code** — `scripts/readme_evidence.py`（JSON。verdict も閾値も exit gate も持たない） |
| **判定** | フロア、第一画面、段落の役割、造語、参照が導線か、日本語の文体と言語間の対応、継ぎ足しと論理、**主張とコードの照合** | **LLM** — `readme-judge` agent（fresh context、集計しない named verdict）。レビュー agent はこれ 1 つ |

README に研究値ベースの数値スコアは作らない。「良い入口か」は意味的判断で、同等の決定論的知見がない。

---

## 最小 LLM-read フロア（小さく・非交渉・肥大させない）

**規則**: README を LLM が*それ一枚だけ*読んだ（llms.txt も graph も読まれない）として、
**テキストだけで**プロジェクトを復元できること。

フロア要素（prose / markdown / Mermaid で。**画像のみ・`<details>` の中のみ・リンク先のみ は不可**）:

1. **identity 文**（最初の 1–2 文・単独で読める）: 「X は {誰}向けに {何をする} {カテゴリ} である」
2. **なぜ存在するか** / 対象者 / 差別化点。what・how・who に答えて **why** だけ欠ける README は、
   「誰の役にも立たないのに何故ここで動き続けているのか」を訪問者に残す（判定は checklist K5）
3. canonical な事実: 実名・言語 / stack・status・必要な鍵（有料か）。**研究 / DOI repo は** DOI +
   how-to-cite（BibTeX / CITATION）+ 語彙を支える 3–6 個の core concept 定義
4. 具体例を **1 つだけ**: コードなら関数 signature + 最小実行片 / 研究なら核となる主張 + 2–3 個の
   鍵となる数値
5. 深部 doc への link-map は**ポインタのみ**。load-bearing な事実をリンク先 / llms.txt / graph だけに
   置かない

lead が産物（「憲法がどう変わったかの履歴」型）を約束したら、README から**到達できる行き先**
（リンク・節・数えた実績 + as-of）を同じ PR で置く。

> **最重要の落とし穴**: フロアは*小さな*非交渉コア。「削るな・再構造化せよ」を効かせすぎると、
> Mermaid / `<details>` / フロア節に情報が温存され、**README が偽装 llms-full.txt に肥大**する。
> **フロア以外は削るか relocate する**（→ Length budget）。

`graph.jsonld` / `llms.txt` を README から作る場合、README prose を構造ソースにしない。識別子・
graph 辺は `CITATION.cff` / `.zenodo.json` / frontmatter の小さな manifest から derive する。
GitHub のメタ面は、description / topics と DOI の無い repo の homepage を本 skill が持つ（Step 6）。
DOI repo の homepage・CITATION ファイル・release metadata は `release-doi` が持つ
（細則 → `references/about.md`）。

### profile / hub README

著者の profile repo や、複数の repo を束ねる hub の README は、フロア 1 を「この人（この hub）は
誰で、何の仕事がどこにあるか」に、フロア 4 を「代表作の表（名前・役割・1 行の中身・入口）」に
置き換える。ほかの規則は同じ。

---

## Visual（冒頭の概要図 1 枚 + 本文の図は絞る）

「短く・視覚的に」の正しい読み替えは **「散文の壁を*走査可能な構造*に圧縮する」**。散文を画像化
するのではない。

- **第一画面に概要図を 1 枚置く（既定）**: 動く仕組み（流れ・判定・ループ）を持つ repo は、badge の
  直後に ELI5 型の図（大きな絵・少ない言葉、2〜4 枠）を言語ごとの SVG で置く。役割は人間の注意で、
  情報は直後の identity 段落が同じ内容を文で持つ。型（線形 / ループ）・ラベルと本文の語の揃え方・
  SVG の約束・描画確認は `references/overview-diagram.md`
- **本文の図は、図にすべきかをまず絞る**: 3 ステップの線形・単純な列挙は prose / list / 小さな表。
  本当に graph 形状（関係・多分岐）のものだけ **Mermaid（`TD` 縦、モバイルで潰れない）**。
  実 UI・実行結果だけ raster
- **どの図にも一文のテキスト等価を必ず添える（hard rule）** — 図が潰れた人間・mermaid fence を
  読み飛ばす抽出器・スクリーンリーダを同時に救う。図は情報の唯一の担い手にしない
- raster に load-bearing な情報を担わせない。**alt 必須**（text 経路は alt しか読まない）。相対パスで
  repo に commit し、README からは `<img>` / markdown 画像で参照する
- **badge は 2–4 個の高信号のみ**（CI / version / license / 研究 repo は DOI）
- hero カバーアートは純装飾 raster が正当な唯一の場所（言語切替行と H1 の間、画像内に文字を入れない）

Mermaid styling・辺の交差の直し方・hero の仕様と生成の作法・表セルの制約は `references/visual.md`。

---

## Length budget（語数目標は置かない）

- **above-the-fold（最初の 1 画面 = 30 秒で「自分向けか」を判断）**: 任意の hero → H1 → 一行 tagline
  （価値提案 = 最も確実に LLM に抽出される行）→ 2–4 functional badge → 概要図 → フロアの事実 →
  copy-paste の quick start。**深い rationale はこの後**。GitHub は README の上にファイル一覧を出す
  ので、repo の root が散らかっていれば、それも第一画面の一部になる
- **順序は repo 種別で変わる**が、**「identity + canonical facts が deep rationale より前」**だけは守る
- 総量は 1 変数で決まる: **正準 docs / ADR が深部を吸収するか**。深い「なぜ」は ADR / `docs/` /
  `llms-full.txt` へ移し、README には一行ポインタ（Diátaxis の explanation-displacement）
- `<details>` は**二次的な bulk のみ**（option 表・FAQ・troubleshooting）。**フロアを入れない**

---

## 導線の置き方

- **at-a-glance（If you came for… → Start at）表は既定で置かない。** 有効性の根拠がなく、行ラベルに
  内部語が入ると第一画面の文脈密度を上げるだけになる。identity 段落と節見出しが導線を担う。
  置くのは、読者層が 3 つ以上あり行ラベルが平易に書けるときだけ
- **著者のほかの仕事への導線**（回遊）: 末尾に「More from the author / 著者のほかの仕事」節を置き、
  順に (1) この repo を題材にした記事（両言語の URL）(2) 同じ主題の記事と姉妹 repo (3) 著者の hub /
  profile への逆リンク、を並べる。**各リンクに、開くと何が分かるか（結論か発見）を 1 行付ける**
  — 題名だけのリンクは開かれない。lead の末尾からこの節へ 1 行で案内する。この repo の記事は lead
  でも 1 回リンクしてよい。リンク先は公開済みで 200 を返すことを確かめる
- 外部の関連作（他人の repo・出典）は Related Work に集め、lead に混ぜない
- **AI 向けの機械可読導線（graph.jsonld / llms.txt）は `<details>` に入れず、末尾に平文 1–2 行**で置く
  （折りたたみは rendered-HTML の crawler と HTML ブロックを不透明扱いする抽出器に見えない）

---

## Voice / Register（初見読者に開いた文体）

README は最初の着地面で、読者の大半は著者の文脈を何も知らない。

- **AI-slop の診断表（正本は `writing-ecosystem` の references/style-diagnostics.md —
  `~/MyAI_Lab/zenn-content` 常駐）を README の prose にも当てる。** 特に EN の em-dash 多用 —
  修正は文の再構築で行い、`:` / `;` への機械置換をしない
- **日本語 README の地の文はですます調**（`writing-ecosystem` の Voice からの意図的な分岐）。表の
  セル・体言止め・見出し・alt は適用外。日本語の段落は 1 行で書く（文の途中の改行は GitHub で空白に
  見える）。漢語直写の翻訳調を開く対応表は `references/ja-register.md`
- **英語 README**: identity 文は三人称の型。本文は、著者個人の repo なら一人称でよい。1 つの README の
  中で自称（I / we / the author）を揃える
- **造語**: 残す語は初出に一行の平易な言い換えを付け（造語は graph.jsonld / glossary と連合する引用
  アンカー）、残さない語は平易に言い換えるか docs/ へ移す。数の目安は checklist R10 が持つ
- **段落は役割ごとに割る**（1 段落 1 役割）。ADR 番号・他 repo・evidence ファイルへの参照は導線で
  あって説明の代替ではない — 参照を消しても文が意味を運ぶこと

---

## Workflow（Rewrite モード）

判定器は fresh context の別 agent process で起動し、執筆セッションの文脈を渡さない（自己批評は
検出率が落ち、書き手の文脈は未定義語を補完して判定を甘くする）。

```
1. 入口の設計                                                            ⏸ 著者確認
   - フロア 5 要素の確定と、造語の表（残す語 / 言い換える語 / docs へ移す語）
   - 節構成案（各節が答える読者の問いを 1 行ずつ）と概要図の枠案（型と、各枠の絵・見出し・補足）
   - 変わる事実の表: version・数値・日付・status ごとに持ち主を決める（badge / release-doi /
     as-of 日付付きで README）。持ち主の無い数値は README に置かない
   - tagline 候補: [skill: headline-craft] で 3〜6 本。著者がここで選ぶ（質は Step 4 の R2 が見る）
2. 執筆（本体が直接書く）
   - 事実はコードと docs に照らしながら書く（version・コマンド・既定値・件数）
   - 概要図の SVG を描き、ラベルをコードと本文に照合し、PNG に描いて目で確かめる
     （`references/overview-diagram.md`）
   - 著者のほかの仕事への導線（「導線の置き方」）を置き、各リンクが開けることを確かめる
3. 他言語版 — [skill: prose-translation] の term-lock と back-translation で訳す。README に固有の
   規則（JA のですます・日本語の段落を 1 行に・概要図の和文版 `assets/overview.ja.svg`・英語だけの
   docs へのリンクに（英語））はこの skill が持つ。同じフロア・見出し階層・アンカー・例で揃える
4. 草稿判定 — 各言語版に証拠 JSON を作る:
     uv run --quiet --directory ~/.claude/skills/readme-writer python -m scripts.readme_evidence <README の絶対パス> > <out>.json
   → [agent: readme-judge]（mode: draft。全言語版・JSON・図・repo root の path を 1 回で渡す）
     ├ Publishable → 5
     ├ Fix         → 本体が span 単位で直す → mode: recheck（同じ質問セット）で 1 回
     └ Rewrite     → ⏸ 著者へ差し戻し
   上限 2 ラウンド。届かなければ残指摘を添えて ⏸ 著者判断
5. 最終判定【binding】— 凍結した全言語版に証拠 JSON を作り直し、readme-judge（mode: final、
   質問を新しく作る）を 1 回。Fix なら span で直し、final の質問セットで recheck を 1 回だけ回して、
   結果にかかわらず Step 6 へ（新しい質問での再実行はしない — 毎回新しい細部を拾って収束しない）。
   Rewrite なら ⏸ 著者へ差し戻す
6. About 変更案 — description は README の lead と同じ主張・1 文目で機能が伝わる構成、topics は実勢を
   測ってから、DOI の無い repo の homepage はこの repo を解説した記事か docs サイト
   （細則 `references/about.md`）。成果物は「現状 → 提案」
   ⏸ 著者通読 GO — README 全文 + 判定結果 + About 案を一括で渡す。著者は GitHub のプレビューで
   スマホ幅と dark 表示も見る。著者通読が最上位のゲート
7. 適用 — commit / `gh repo edit`（`references/about.md`）。通読で見つかった指摘の数を
   `evals/read-through-log.md` に 1 行記録する
```

- 人間ゲートは Step 1 と Step 6 の 2 つ。条件付きで Rewrite・上限到達のとき。readme-judge の起動は
  2〜4 回（draft、recheck、final、recheck）
- **span 編集は追い越した段落を刈る** — 新段落が旧段落の主張を吸収したら旧段落を残さない。第一画面の
  同一主張 2 回は判定器が継ぎ足し痕（K2）として最初に拾う
- **KPI = 通読指摘数** — 最終判定の後に著者通読が見つけた指摘数が判定器の真のエラー率で、
  `references/readme-judge-checklist.md` を直すときの主な入力（記録先 `evals/read-through-log.md`）
- 別モデルの意見は、著者が求めたときだけ skill: `codex-review` を prompt-driven で回す。prompt に
  README の path と言語、次の観点を入れる。CRITICAL / HIGH は span で直し、構造の指摘は著者へ回す:

```
/codex-review "Review <README paths> (<languages>) as prose, not code: does the first screen say what / for whom / where it runs without insider terms, does every paragraph answer a reader question, are ADR / sibling-repo references pointers rather than the only explanation, is anything load-bearing hidden in images or collapsed sections, and does any claim contradict the code?"
```

---

## Verification

```bash
cd ~/.claude/skills/readme-writer
uv sync --dev
uv run pytest tests/ --cov=scripts --cov-report=term-missing
uv run python -m scripts.readme_evidence fixtures/sample_issues.md --text
```

判定器のスモークテスト: `evals/fixtures/` の README（作り直し前の実物）を readme-judge に渡し、
`.expected.md` の指摘を 3 件中 2 件以上検出し、`fixtures/sample_clean.md` に Rewrite を出さないこと。

---

## Related

- `readme-judge` agent（`~/.claude/agents/readme-judge.md`）— 唯一のレビュー agent（判定・主張の照合）。
  基準は `references/readme-judge-checklist.md`
- [`headline-craft`](../headline-craft/SKILL.md) — tagline 候補の生成（Step 1）
- [`prose-translation`](../prose-translation/SKILL.md) — 他言語版の翻訳（Step 3）
- [`release-doi`](../release-doi/SKILL.md) — DOI repo の release と、それに伴う version・DOI・homepage の同期
- [`context-sync`](../context-sync/SKILL.md) — 文書間の役割の重なりと移送（README の外まで直すとき）
- [`codex-review`](../codex-review/SKILL.md) — 著者が求めたときの cross-model レビュー
- [`llms-txt-writer`](../llms-txt-writer/SKILL.md) / [`jsonld-knowledge-graph`](../jsonld-knowledge-graph/SKILL.md) — 機械 surface
- skill: `archify` — 詳しい構成図（HTML）。README には概要図を置き、構成図は docs/ からリンクする
- `writing-ecosystem`（`~/MyAI_Lab/zenn-content/.claude/skills/writing-ecosystem`）— AI slop の診断表と Voice 規約の正本
- `references/` — `readme-judge-checklist.md` / `visual.md` / `overview-diagram.md` / `ja-register.md` / `about.md`
- `templates/` — 概要図の雛形（`overview-linear.svg` / `overview-loop.svg`、illustrative）
- `evals/read-through-log.md` — 通読指摘数の記録
- `inspiration.md` — 設計の出自・外部エビデンスの出典

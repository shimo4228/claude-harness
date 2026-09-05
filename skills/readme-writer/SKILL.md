---
name: readme-writer
description: README やプロジェクトのトップページ（repo を開いた人が最初に見る入口）を書く・直すときに使う。こんな時に呼ぶ — README が長い／継ぎ足しで文脈が重くなり初見で分からない、開いて数十秒で「何のプロジェクトで自分向けか」が伝わる入口にしたい、長い rationale・ADR 参照・内部史を docs/ に逃がしたい、研究・DOI repo の README を引用付きで読める長さにまとめたい、GitHub の About（description / topics）が README と食い違っている。証拠スクリプト（readme_evidence.py）+ fresh context の判定器（readme-judge）+ 上限 2 ラウンドの改稿ループ + review panel + 著者通読 GO で回す。短く・走査しやすくしつつ、LLM が README 一枚で要点を復元できる情報フロアは残す。CLI でも研究 repo でも、日本語でも英語でも、新規作成でも既存改善でも対象。AI 専用ドキュメント（llms.txt 等）は → llms-txt-writer、記事・エッセイは → writing-ecosystem。
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

## When to Use

- README.md / README.ja.md を新規作成・改善する
- 継ぎ足しで育った README（ADR 参照・姉妹 repo・造語・内部史の密度が上がり、初見で読めない）を根本から作り直す
- GitHub の **About（description / topics / homepage）** を README と同じ主張に揃える

**使わない場面**: `llms.txt` / `llms-full.txt` / FAQ など AI 専用 doc（→ `llms-txt-writer`）、
記事・エッセイ（→ `writing-ecosystem`）、graph.jsonld の設計（→ `jsonld-knowledge-graph`）。

---

## 軸は「人間の ATTENTION × LLM の INFORMATION」

README 最適化の対立軸は「人間向け情報 vs LLM 向け情報」ではない。**人間の注意（短く・掴む・走査
できる）× LLM の情報（README だけで復元できる）**である。両者は同じ施策に収束するので、
トレードオフでなく**設計で両取りする**。

- AI 検索 / 引用クローラは llms.txt を実質読まず、`graph.jsonld` は直接 fetch では plain text 扱い。
  **README の情報を「機械層が backstop する」前提で薄くしてはいけない**（較正: 「LLM は README しか
  読まない」は強すぎる。routed coding agent は llms.txt を on-demand で読む — 詳細は `inspiration.md`）
- **two-sided rule**: アイデアが*どう伝わるか*は最適化してよい（見出し階層・entity anchoring・
  answer-first の lead）。アイデアが*何であるか*は曲げない（keyword stuffing・疑問見出し farming・
  glossary 投下・主張の歪曲は禁止）。star や引用は成功指標ではない

---

## 証拠と判定（code は数える、LLM は判定する）

README 品質は「数えられる事実」と「文脈を読む判断」に分かれる。所有者を分ける:

| 層 | 何を出すか | 所有者 |
|---|---|---|
| **証拠** | 第一画面の行数と新語数、ADR / 他 repo / docs への参照数、造語候補の出現表、`<details>` の中身、図の直後に prose があるか、内部史・生数値の行、slop 語・em-dash | **code** — `scripts/readme_evidence.py`（JSON。verdict も閾値も exit gate も持たない） |
| **判定** | 第一画面が立つか、段落が読者の問いに答えるか、造語予算、参照が導線か説明の代替か、継ぎ足しの痕跡、論理 | **LLM** — `readme-judge` agent（fresh context、集計しない named verdict） |

**README に研究値ベースの数値スコアは作らない**。「良い入口か」は意味的判断で、同等の決定論的
知見がない。entity density 等の AI surface 指標を人間 README に持ち込むのは anti-pattern。

---

## 最小 LLM-read フロア（小さく・非交渉・肥大させない）

**規則**: README を LLM が*それ一枚だけ*読んだ（llms.txt も graph も読まれない）として、
**テキストだけで**プロジェクトを復元できること。

フロア要素（prose / markdown / Mermaid で。**画像のみ・`<details>` の中のみ・リンク先のみ は不可**）:

1. **identity 文**（最初の 1–2 文・単独で読める）: 「X は {誰}向けに {何をする} {カテゴリ} である」
2. **なぜ存在するか** / 対象者 / 差別化点。what・how・who に答えて **why** だけ欠ける README は、
   「誰の役にも立たないのに何故ここで動き続けているのか」を訪問者に残す（節名のテンプレではない。
   判定と repo 類型ごとの扱いは checklist K5）
3. canonical な事実: 実名・言語 / stack・status。**研究 / DOI repo は** DOI + how-to-cite（BibTeX / CITATION）+ 語彙を支える 3–6 個の core concept 定義
4. 具体例を **1 つだけ**: コードなら関数 signature + 最小実行片（フル実装は載せない）/ 研究なら核となる主張 + 2–3 個の鍵となる数値
5. 深部 doc への link-map は**ポインタのみ**。load-bearing な事実をリンク先 / llms.txt / graph だけに置かない

lead が産物（「憲法がどう変わったかの履歴」型）を約束したら、README から**到達できる行き先**
（リンク・節・数えた実績 + as-of）を同じ PR で置く。約束だけの lead は判定器が Dominant No にする。

> **最重要の落とし穴**: フロアは*小さな*非交渉コア。「削るな・再構造化せよ」を効かせすぎると、
> Mermaid / `<details>` / フロア節に情報が温存され、**README が偽装 llms-full.txt に肥大**する。
> **フロア以外は容赦なく削るか relocate する**（→ Length budget）。

`graph.jsonld` / `llms.txt` を README から作る場合、**README prose を構造ソースにしない**。識別子・
graph 辺は `CITATION.cff` / `.zenodo.json` / frontmatter の小さな manifest から derive する。
GitHub のメタ面のうち description / topics / homepage は本 skill が Workflow Step 10 で担当する
（social-preview・CITATION ファイル・release metadata は → `release-doi`）。

---

## Visual（図にすべきかをまず絞る）

「短く・視覚的に」の正しい読み替えは **「散文の壁を*走査可能な構造*に圧縮する」**。散文を画像化
するのではない。

- **図にすべきかをまず絞る**: 3 ステップの線形・単純な列挙は prose / list / 小さな表。本当に graph 形状
  （関係・多分岐）のものだけ **Mermaid（`TD` 縦、モバイルで潰れない）**。実 UI・実行結果だけ raster
- **どの図にも一文のテキスト等価を必ず添える（hard rule）** — 図が潰れた人間・mermaid fence を
  読み飛ばす抽出器・スクリーンリーダを同時に救う。図は視覚的ボーナスで、情報の唯一の担い手にしない
- raster に load-bearing な情報を担わせない。**alt 必須**（text 経路は alt しか読まない）。相対パスで
  repo に commit。外部 hotlink と inline `<svg>` は避ける
- **badge は 2–4 個の高信号のみ**（CI / version / license / 研究 repo は DOI）
- hero カバーアートは唯一、純装飾 raster が正当な場所（言語切替行と H1 の間、画像内に文字を入れない）

Mermaid styling・辺の交差の直し方・hero の仕様・表セルの制約・asciinema 等の細則は
`references/visual.md`。

---

## Length budget（語数目標は持たない）

語数目標は**置かない**（「500–1500 語の sweet spot」等は無出典として棄却済み）。代わりに:

- **above-the-fold（最初の 1 画面 = 30 秒で「自分向けか」を判断）**: 任意の hero → H1 → 一行 tagline
  （価値提案 = 最も確実に LLM に抽出される行）→ 2–4 functional badge → フロアの事実 → copy-paste の
  quick start。**深い rationale はこの後**
- **順序は repo 種別で変わる**が、**「identity + canonical facts が deep rationale より前」**だけは守る
- 総量は 1 変数で決まる: **正準 docs / ADR が深部を吸収するか**。深い「なぜ」は ADR / `docs/` /
  `llms-full.txt` へ移し、README には一行ポインタ（Diátaxis の explanation-displacement）
- `<details>` は**二次的な bulk のみ**（option 表・FAQ・troubleshooting）。**フロアを入れない**

---

## 導線の置き方

- **at-a-glance（If you came for… → Start at）表は既定で置かない。** 有効性の根拠がなく、行ラベルに
  内部語が入ると第一画面の文脈密度を上げるだけになる。
  identity 段落と節見出しが導線を担う。置くのは、読者層が 3 つ以上あり行ラベルが平易に書けるときだけ
- **AI 向けの機械可読導線（graph.jsonld / llms.txt）は `<details>` に入れず、末尾に平文 1–2 行**で置く。
  折りたたみは rendered-HTML の crawler と HTML ブロックを不透明扱いする抽出器に見えない（raw fetch
  には見える）— AI に見つけてほしい導線を隠す理由がない
- 姉妹 repo・ecosystem の説明は Related Work に集める。lead に混ぜない

---

## Voice / Register（初見読者に開いた文体）

README は最初の着地面で、読者の大半は著者の文脈を何も知らない。

- **AI-slop 禁止リスト（正本は `writing-ecosystem` の references/style-diagnostics.md —
  `~/MyAI_Lab/zenn-content` 常駐）は README の prose にも適用する。** 特に EN の
  em-dash 多用 — 修正は文の再構築で行い、`:` / `;` への機械置換をしない
- **日本語 README の地の文はですます調**（`writing-ecosystem` Voice からの意図的分岐。正本側の
  Related に登録済み）。表のセル・体言止め・見出しは適用外。英語 README は一人称のパーソナルな
  register を保つ
- **造語は削除せず、初出に一行の平易な言い換え**（造語は graph.jsonld / glossary と連合する引用
  アンカー）。**段落は役割ごとに割る**（1 段落 1 役割）。造語予算の実値は checklist R10 が持つ
- **ADR 番号・他 repo・evidence ファイルへの参照は導線であって説明の代替ではない** — 参照を消しても
  文が意味を運ぶこと。内部史と生数値の扱いは checklist R11–R13 が持つ
- 漢語直写の翻訳調を開く対応表（「正本」→「最新情報は◯◯にあります」等）は `references/ja-register.md`

検査器: 造語・文脈密度・継ぎ足しは `readme-judge`（verdict）、初見読者の読書体験と register は
`readme-clarity-reviewer`（findings）。

---

## Workflow（証拠 → fresh 判定器の改稿ループ → panel → binding 最終判定 → 著者通読 GO）

**判定器は fresh contextの別agent processで起動し、執筆セッションの文脈を渡さない**
（自己批評は検出率が落ちる）。

```
1. 入口の設計 — フロア 5 要素の確定 + 造語予算表（残す語 / 平易化する語 / docs へ落とす語）
   + 節構成案（各節が答える読者の問いを 1 行ずつ）                       ⏸ 著者確認
2. tagline 候補 — [skill: headline-craft] で 3 本生成 → readme-judge に fresh で判定させる
   （軸一致 / 具体性 / 誠実さ / 飾り語ゼロ / 具体の検討痕。判定器自身が最強の対抗案を 1 本作る）
   → 最終選択は著者
3. 執筆（オーケストレーター本体が直接書く。サブエージェントに委譲しない）
4. 改稿ループ = 草稿ゲート:
     uv run --quiet --directory ~/.claude/skills/readme-writer python -m scripts.readme_evidence <README>
     → [agent: readme-judge]（fresh、JSON を証拠に）
       ├ Publishable → 5 へ（この Publishable は panel の入場券。binding は 7）
       ├ Fix         → 本体が span 単位の指摘だけを修正 → 同一チェックセットで再判定 1 回
       └ Rewrite     → ループ中断、⏸ 著者へ差し戻し
     上限 2 ラウンド。届かなければ残指摘を添えて ⏸ 著者判断
5. review panel（並列）: [agent: readme-reviewer] + [agent: readme-clarity-reviewer]
   + codex-review（prompt-driven、公開 repo のみ）
   verdict は readme-judge だけが出す。panel は findings。verdict 級の不一致
   （judge Publishable vs clarity FAIL / reviewer MAJOR REWRITE / codex 構造欠陥）だけ ⏸ 人間 routing
6. panel 指摘の反映（構成が変わったら 4 へ 1 回だけ戻る。構成系の指摘は推奨を付けず著者ゲートへ昇格）
7. 最終判定【binding】— 凍結候補に readme_evidence + readme-judge（fresh・質問新規生成）を再実行。
   凍結後に 1 文字でも修正が入ったら再実行。通読 GO 中の著者修正はバッチして 1 回だけ
8. 他言語版 — 同じフロア・同じ見出し階層・同じアンカー・同じ例で書く（JA はですます）。
   行数・段落境界は言語に合わせてよい（行単位の対訳を強制しない）。
   readme-clarity-reviewer の Cross-language 軸 + readme-judge 最終判定を各言語版に 1 回
9. fact 一致 — read-only の照合に限定（allowlist: README 各言語版 / llms.txt / llms-full.txt /
   graph.jsonld / glossary / README を参照する docs）。context-sync はここでは起動しない
   （文書移送まで自動適用しうる）
10. About 変更案 — description は README の lead と同じ主張・1 文目で機能が伝わる構成、
    topics は実勢を測ってから（細則 `references/about.md`）。成果物は「現状 → 提案」で、適用しない
    ⏸ 著者通読 GO（README 全文 + 判定結果 + About 案を一括）— 著者通読が常に最上位のゲート
11. 適用 — commit / `gh repo edit`（`references/about.md`）
```

設計制約:

- **自己批評は回さない** — 判定は fresh context の readme-judge
- **上限 2 ラウンド** — 反復は 2〜3 回で頭打ち、以降は voice の正規化ドリフト（企業 About 化）
- **迷ったら Fix**、Fix は span 単位のみ（全文書き直し案の出力禁止）
- **span 編集は追い越した段落を刈る** — 新段落が旧段落の主張を吸収したら旧段落を残さない。第一画面の
  同一主張 2 回は判定器が継ぎ足し痕（K2）として最初に拾う
- 人間ゲートは Step 1 の構成確認・判定器不一致・通読 GO の 3 箇所
- **KPI = 通読指摘数** — 最終判定 Publishable の**後**に著者通読が見つけた指摘数を記録する。これが
  判定器の真のエラー率で、`references/readme-judge-checklist.md` 改定の主入力
- `codex-review` は **prompt-driven モード**で writing 観点の指示を渡す（scoped モードはコード向け
  指示が走るので prose に不適）:

```
/codex-review "Review the README as prose, not code: does the first screen say what / for whom / where it runs without insider terms, does every paragraph answer a reader question, are ADR / sibling-repo references pointers rather than the only explanation, is anything load-bearing hidden in images or collapsed sections?"
```

---

## What This Skill Does NOT Do（境界）

- `llms.txt` / `llms-full.txt` を書かない（→ `llms-txt-writer`）、`graph.jsonld` を設計しない（→ `jsonld-knowledge-graph`）
- cross-surface の drift 検出 / 同期をしない（→ `context-sync` / `release-doi`）。Step 9 は read-only 照合まで
- 記事 / エッセイを編集しない（→ `writing-ecosystem`）
- social-preview 画像を作らない。外部ディレクトリ・awesome-list への掲載申請をしない
- **品質スコア / grade / 評点を出さない**（verdict は named — Publishable / Fix / Rewrite）

---

## Anti-patterns

- AI surface の数値指標（ski-ramp / entity density）を人間 README に流用する
- 「ビジュアル優先」を散文の画像化と解釈する（raster 図は text-only LLM に不可視）
- 判定器に repo の他ファイルを先に読ませる（未定義語を repo 文脈で補完して甘くなる）
- description を README lead と別の主張にする（cloaking）/ topics を実勢を測らずに選ぶ

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

- `readme-judge` agent（`~/.claude/agents/readme-judge.md`）— 改稿ループの判定器（verdict）。基準は `references/readme-judge-checklist.md`
- `readme-reviewer` agent — panel（フロア復元・構成・長さ・視覚）。findings
- `readme-clarity-reviewer` agent — panel（初見読者の読書体験・造語予算・register・cross-language）。findings
- [`codex-review`](../codex-review/SKILL.md) — 公開 README への cross-model 並列レビュー（prompt-driven）
- [`headline-craft`](../headline-craft/SKILL.md) — tagline 候補の生成
- [`llms-txt-writer`](../llms-txt-writer/SKILL.md) / [`jsonld-knowledge-graph`](../jsonld-knowledge-graph/SKILL.md) — 機械 surface
- `writing-ecosystem`（`~/MyAI_Lab/zenn-content/.claude/skills/writing-ecosystem`）— AI slop 禁止リストと Voice 規約の正本
- `references/` — `readme-judge-checklist.md` / `visual.md` / `ja-register.md` / `about.md`
- `inspiration.md` — 設計の出自・外部エビデンスの出典（Portability のため SKILL.md 本文から分離）

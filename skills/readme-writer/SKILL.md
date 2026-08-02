---
name: readme-writer
description: README やプロジェクトのトップページ（repo を開いた人が最初に見る入口）を書く・直すときに使う。こんな時に必ず呼ぶ — README が長い／文字の壁で読まれない→短く走査しやすくしたい、開いて数十秒で「何のプロジェクトで自分向けか」が伝わる入口にしたい、構成図・アーキ図を入れたい（PNG や架空図でなく Mermaid を勧める）、badge を貼りすぎたので整理したい、GitHub の About（description / topics / homepage）が空・的外れで repo が検索や topic ページに載っていない、長い rationale や「なぜ」を docs/ に逃がしたい、研究・DOI repo の README を引用付きで読める長さにまとめたい。短く・視覚優先にしつつ、LLM が README 一枚で要点を復元できる情報フロアは残す。CLI でも UI でも研究 repo でも、日本語でも英語でも、新規作成でも既存改善でも対象。AI 専用ドキュメント（llms.txt / llms-full.txt 等）は対象外（→ llms-txt-writer）、記事・エッセイ等の長文 prose は → writing-ecosystem。
compatibility: Requires Python 3.11+ and uv. Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
user-invocable: true
origin: shimo4228
---

# readme-writer — Human-Facing README Skill

人間に向けた README を書く・改善するスキル。`llms-txt-writer` が AI 専用 surface を担うのに対し、本 skill は **人間 surface の単一正準入口**を担う。

加えて重要な事実: **README は、grounding 経路（AI 検索 / チャットに repo URL を貼る）で LLM が確実に前提にできる唯一の surface でもある**。そのため README は「人間向けに短く・視覚的に」しつつ「LLM が README 一枚だけ読んでもプロジェクトを復元できる小さな情報フロア」を必ず残す——この両立が本 skill の中心課題。

## When to Use

- README.md / README.ja.md を新規作成・改善する
- repo / プロジェクトの「人間が最初に着地するページ」を整える
- 既存 README が「機械寄りで人間に中途半端」/「人間向けに薄すぎて LLM が掴めない」のを直す
- README を**短く・視覚優先**にしたいが情報フロアを落としたくないとき
- GitHub の **About（description / topics / homepage）** を整える（README 本文と同じ第一画面の構成要素。topics は*まだ来ていない人*を連れてくる索引面）

**使わない場面**:
- `llms.txt` / `llms-full.txt` / FAQ など AI 専用 doc（→ `llms-txt-writer`）
- 記事・エッセイ・ブログ等の長文 prose（→ `writing-ecosystem`）
- graph.jsonld の設計（→ `jsonld-knowledge-graph`）

---

## 軸は「人間の ATTENTION × LLM の INFORMATION」

README 最適化の本当の対立軸は「人間向け情報 vs LLM 向け情報」ではない。**人間の注意（短く・掴む・走査できる）× LLM の情報（README だけで復元できる）**である。両者は同じ施策に収束する（後述）ので、トレードオフでなく**設計で両取りする**。

### README は確実に読まれる唯一の surface（だが「only」ではない）

- AI 検索 / 引用クローラは **llms.txt を実質読まない**（複数の 2026 ログ調査で大半がゼロリクエスト、主要検索ベンダーは公式に非対応表明）。
- `graph.jsonld` は直接 fetch では plain text 扱いされ、**README の事実の代替にならない**（対照実験）。
- ゆえに **README に置いた情報を「機械層が backstop する」前提で薄くしてはいけない**。

ただし重要な較正: 「LLM は README *しか* 読まない」は強すぎる。正しくは「**generic な paste-URL / 検索 grounding では README が*確実に前提にできる*唯一の面**」。別経路（検索インデックスが他ファイルを既に chunk 済み / README からのリンク追跡 / GitHub connector・API でのファイルツリー露出 / pretraining 由来の知識）も存在する。**結論が最も強いのは匿名 live web grounding と直接ランディング fetch**。逆に **routed coding agent（Claude Code / Cursor 等）は llms.txt を on-demand で読む**ので、llms.txt は agentic チャネルの保険として依然有効——ただし AI 検索の入口ではない。

---

## なぜ「構造 lint」と「ホリスティック review」を分けるのか

README 品質には 2 種類の property が混在する。**Code-LLM Layering**（構造は code が 100% 精度で所有、意味は LLM が所有）に従い所有者を分ける。判定軸は [`when-code-when-llm`](../when-code-when-llm/SKILL.md): 「同じバイト列が文脈で違う意味になりうるか?」

| property | 例 | 種別 | 所有者 |
|---|---|---|---|
| 構造的 | H1 数 / 見出しレベル / alt-text 有無 / ローカルリンク解決 / raster 図ファイル名 / badge 数 / details 内の DOI 等 / H1 直後の prose 行 | structural | **code（`readme_lint.py`）** |
| 意味的 | lead が人を掴むか / 価値提案の明快さ / **README-only で LLM が復元できるか** / 物語の流れ / badge が vanity か | semantic | **LLM のホリスティック review** |

**README に研究値ベースの数値スコアは作らない**。llms.txt のセクション比率（ski-ramp 等）は LLM 引用研究で検証された決定論シグナルだが、README の「良い入口か」は意味的判断であり同等の決定論的知見がない。entity density 等の AI surface 指標を人間 README に持ち込むのは anti-pattern。

### ただし「構造的 AI 可読性」は積極採用する（two-sided rule）

「AI surface 指標を持ち込まない」は半分。原則は **「アイデアが*どう伝わるか*は最適化してよい（強度に上限なし）。アイデアが*何であるか*は決して曲げない」**。

- **採用（強度無制限）**: 見出し階層・情報設計・**entity anchoring**（著者名 / ORCID / DOI / canonical 識別子を**prose に**書く）・固有/造語語彙の anchoring・answer-first の lead・at-a-glance の表。これらは人間にも grounding 経路の LLM にも効く**収束ゾーン**。
- **禁止**: keyword stuffing・水増し属性・疑問見出し farming・glossary 投下・retrieval の報酬関数に合わせた主張の歪曲。引用や star は**成功指標ではない**ので、歪曲が奉仕する目標がそもそも無い。

---

## 最小 LLM-read フロア（小さく・非交渉・肥大させない）

**規則**: README を LLM が*それ一枚だけ*読んだ（llms.txt も graph も読まれない）として、**テキストだけで**プロジェクトを復元できること。

フロア要素（prose / markdown / Mermaid で。**画像のみ・details の中のみ・リンク先のみ は不可**）:

1. **identity 文**（最初の 1-2 文・単独で読める）: 「X は {誰}向けに {何をする} {カテゴリ} である」
2. 解く問題 / 対象者 / 差別化点
3. canonical な事実: 実名・言語/stack/status。**研究/DOI repo は** DOI + how-to-cite（BibTeX / CITATION）+ 語彙を支える 3-6 個の core concept 定義
4. 具体例を **1 つだけ**: コードなら関数 signature + 最小実行片（フル実装は載せない——肥大 + hallucination 誘発）/ 研究なら核となる主張 + 2-3 個の鍵となる数値
5. 深部 doc への link-map は**ポインタのみ**。load-bearing な事実をリンク先 / llms.txt / graph だけに置かない

> **最重要の落とし穴**: フロアは*小さな*非交渉コア。「削るな・再構造化せよ」を効かせすぎると、Mermaid / details / フロア節に情報が温存され、**README が偽装 llms-full.txt に肥大**する。人間の目標は*短く*だった。**フロア以外は容赦なく削るか relocate する**（→ length budget）。

`graph.jsonld` / `llms.txt` を README から作る場合、**README prose を構造ソースにしない**。識別子・graph 辺は `CITATION.cff` / `.zenodo.json` / frontmatter の小さな manifest から derive する（手書きの並行コピーは drift する）。

GitHub のメタ面（repo description / topics / social-preview / CITATION ファイル / release / package metadata）も grounding に効く floor の一部。このうち **description / topics / homepage は本 skill が Workflow Step 4–6 で担当する**。social-preview 画像・CITATION ファイル・release / package metadata は対象外で（→ `release-doi`）、checklist として揃っているか確認するに留める。

---

## Visual-first（Mermaid 第一・raster 最後）

「短く・視覚的に」の正しい読み替えは **「散文の壁を*走査可能な構造*に圧縮する」**。散文を画像化するのではない。そして **「Mermaid 第一」≠「何でも Mermaid」**——まず *図にすべきか* を絞る。モバイル（狭幅）で潰れない・LLM が拾える形式を選ぶ。

### 形式の選択

| 中身 | 最適形式 | 理由 |
|---|---|---|
| 3 ステップの線形 / 単純な列挙 | **prose / list / 小さな表** | 全デバイス（特にモバイル）で読める。図にする価値がない |
| 本当に graph 形状（関係・多分岐・matrix） | **Mermaid（`TD` 縦方向）** | ソースがテキストで LLM も読める。縦スクロールはスマホで自然、横（`LR`）は潰れる |
| 大きい / 複雑な図 | **committed SVG（拡大・パン可）/ subsystem 分割** | 巨大 Mermaid は desktop でも上限に当たり、モバイルで潰れる |
| 実 UI / 実行結果 / 写真 | **raster（PNG/JPG/WebP/GIF）** | Mermaid で表現できないものだけ |

**どの図にも一文のテキスト等価を必ず添える（hard rule）**。これが「人間にも LLM にも届く」を保証する本体: モバイルで図が潰れた人間・```mermaid fence を opaque code として読み飛ばす LLM 抽出器・スクリーンリーダ を同時に救う。図はその上の視覚的ボーナスであって、情報の唯一の担い手にしない。

### Mermaid の要点

- GitHub が theme-aware SVG にネイティブ描画。ソースはテキスト（diff 可能・~10 token/edge）で **pixel を見られない text-only クローラにも読める**。散文/graph に埋もれた構造（concept matrix・phase binding・pipeline 段）を Mermaid 化すると**短くなり情報密度が上がる**。
- **モバイル最優先で `TD`（縦）**。横長 `LR` は狭幅で破綻しやすい。
- 描画上限は char ベース（`maxTextSize` 既定 50,000）+ edge ベースで、ノード数ではない（「50-100 node が限界」は俗説）。超えそうなら subsystem 分割。special な Project README では描画されない。
- **視覚的ポップ化の正統経路は Mermaid styling**（`%%{init}%%` themeVariables / `classDef`）— 色・フォントも text ソースに載るので LLM 側のコストゼロ。classDef で色を塗るときは `color:` でテキスト色も明示する（GitHub の dark mode が淡色 fill の上の文字を白に反転して潰すのを防ぐ）。参照 URL は `inspiration.md` の「Mermaid visual styling」節。
- **辺の交差はコードで直せる**（描き直し不要）: (1) ノードの左右配置は**初出順**で決まる — 辺のグループが隣接ノードに繋がるよう宣言順を入れ替える。(2) 1 ノードが多数に fan-out して交差するときは**矢印の向きを反転して sink にする**（`A --> B & C & D` を `B & C & D --> A` に。A が最下段に落ち、収束の意味論も出る）。
- 抽出器が Mermaid を落とす可能性があるので、上の**テキスト等価**で意味を必ず別途担保する。

### カバーアート（hero）

above-the-fold の「任意の hero」枠の実装ガイド。**唯一、純装飾 raster が正当な場所**:

- **配置**: 言語切替行（あれば）と H1 の間。**画像内にテキスト情報を入れない** — 名前・タグラインは H1 と本文が持つ（画像内文字は LLM に不可視なので、入れると情報が消えるか二重管理になる）
- **仕様**: 横長 3:1〜4:1。画像自身に背景色を持たせる（GitHub の light / dark 両モードで安定）。生成画像は幅 1600px・数百 KB 目安に圧縮して `assets/` に commit（`sips -s format jpeg -s formatOptions 85 -Z 1600` で PNG 数 MB → ~300KB）
- **alt 必須・言語別**: README.ja には日本語 alt を書く
- **モチーフとパレットを README 内の図と揃える**と一枚の設計に見える（AI 生成時のプロンプト作法は `inspiration.md`）

### 表セルの視覚改善は不可能（制約）

GitHub は markdown / HTML 表の inline style・bgcolor を sanitize するため**セルの色付けはできない**。
表の視覚改善はセル文の短縮（1 文化）と、関係構造の Mermaid 図併置で行う。絵文字アンカーは
テキストネイティブな唯一の装飾手段だが、好みが分かれるのでユーザー確認なしに既定案にしない。

### raster / その他

- raster は **load-bearing な情報を担わせない**。**alt-text を必須**（hard floor: text 経路は alt しか読まない = alt 無し画像は LLM に不可視。a11y だけの話ではない）。
- dark/light は `<picture><source media="(prefers-color-scheme: …)"><img alt="…"></picture>`。`<img alt>` は二重に load-bearing。
- 画像 asset は repo に commit し**相対パス**参照。外部 hotlink（camo 破綻）と inline/animated `<svg>`/`<embed>`/`<object>`（GitHub が sanitize）を避ける。
- **badge は 2-4 個の高信号のみ**（CI / version / license / 研究 repo は DOI）。vanity badge を避ける。狭幅で badge 段が嵩張らないよう数を絞る。
- CLI repo: asciinema→agg GIF + 一文キャプション。UI repo: スクショ/GIF + alt-text。

> 稀な bespoke 図は **Claude Artifacts / Claude Code の svg・diagram skill** で committable な SVG を生成し `assets/` に置く。

---

## Length budget（語数目標は持たない）

語数目標は**置かない**（「500-1500 語の sweet spot」「visual README は star が増える（GitHub 研究）」はいずれも捏造/無出典として棄却済み）。代わりに:

- **above-the-fold（最初の 1 画面 = 30 秒で「自分向けか」を判断）**: 任意の hero → H1 → 一行 tagline（価値提案＝最も確実に LLM に抽出される行）→ ≤4 functional badge → フロアの事実 → copy-paste の quick start。**深い rationale はこの後**。
- **順序は repo 種別で変わる**: 「quickstart→rationale」はソフトウェア向け。論文 / dataset / 概念 / DOI essay repo では当てはまらない。固定順を強制せず、**「identity + canonical facts が deep rationale より前」**だけを守る。lint の `identity_lead` は「lead 文の存在」だけを構造的に見て**順序は強制しない**。
- 総量は 1 変数で決まる: **正準 docs サイト / ADR が深部を吸収するか**。深い「なぜ」/ 設計 rationale は ADR / `docs/` / `llms-full.txt` / deposited paper に移し、README には一行ポインタ（Diátaxis の explanation-displacement）。これが「450 行の研究 repo README」の直接の治療。
- `<details>` は**二次的な bulk のみ**（option 表・FAQ・troubleshooting・full glossary）。人間の視界を整理しつつ LLM には届く。だが**フロアを入れない**（primacy 喪失 + Ctrl+F 不可。raw-markdown 経路では読めるが、描画ページの要約器は折りたたみを de-prioritize しうる）。

---

## Voice / Register（初見読者に開いた文体）

README は最初の着地面であり、読者の大半は著者の文脈を何も知らない初見者である。
文体と用語密度はその前提で設計する。

### AI-slop 禁止リストは README にも適用する

`writing-ecosystem` の AI-slop 禁止リスト（日英）は記事だけでなく **README の prose にも適用する**。
特に **EN の em-dash（—）多用**（ChatGPT hyphen）: 修正は文の再構築（短文化・括弧・コンマ同格）で行い、
`:` / `;` への機械置換をしない（等間隔リズムは記号が変わっても同じ指紋）。禁止リストの正本は
writing-ecosystem に置いたまま、ここには適用宣言だけを置く。

### 日本語 README はですます調

- **日本語 README の地の文はですます調**で書く。これは `writing-ecosystem` の Voice 規約
  （だ/である × 発見調）からの**意図的な分岐**である — あちらはエッセイ・記事（著者の思考を
  たどる長文 prose）の規約で、README は「初対面の案内」。案内は敬体の方がとっつきやすく、
  である調の断定連打は入口では威圧になる。将来の stocktake がこの差を「不整合」として
  逆修正しないこと。
- 表のセル・箇条書きの体言止め・見出しはこの限りではない（敬体を強制すると冗長になる）。
- 英語 README に対応する軸はない。英語は一人称のパーソナルな register（"I build…"）を保つ。

### 造語・専門用語は初出で一行の平易な言い換え（両言語共通）

- repo 固有の造語（line 名・概念名・層名）は**削除せず**、初出に一行の平易な言い換えを添える。
  造語は concept pages / graph.jsonld / glossary と連合する引用アンカーなので、名前を消すと
  機械層との整合が壊れる。開くのは名前でなく**説明**。
- 1 文に repo 固有の造語を 2 個以上同時に保持させない（初見読者が parse できない）。
- lead（identity 文とその段落）は造語密度を最小にする。lead で使ってよい造語は
  タイトル / repo 名が既に約束しているものだけ。
- 英語混じり日本語文（「〜の source of truth ではない」等）は、日本語で言える語は日本語にする。
  固有名詞・引用アンカー（DOI / ORCID / 概念名）はそのまま。
- **段落は役割ごとに割る**: リードを 4-5 文の一塊にしない（自己紹介 / 誰向けか / この repo の
  位置づけ、のように 1 段落 1 役割）。密度を下げる最安のレバーは削る前にまず改行。

### 漢語直写の翻訳調を開く（JA README）

EN の名詞句を漢語に直写した訳語は、意味は正しくても JA README では制度文書調・翻訳調に
読まれる。開き方は「別の名詞に言い換える」だけでなく、**名詞を役割の文に組み替える**のが
最も効く（"source of truth" は「正本」でなく「最新情報は各リポジトリにあります」）。
実測ベースの対応例（2026-07-27 hub README 改修）:

| EN 名詞句 / 直写訳 | 開いた形 |
|---|---|
| practice line / 実践ライン | プロジェクト、長期プロジェクト |
| canonical record / 正準レコード | 代表的な引用先 |
| source of truth / 正本 | 「最新情報は◯◯にあります」（文で言う） |
| stable relationships / 安定した関係 | 変わらない関係 |
| stable concept / 安定した概念 | 核になる考え |
| this program / このプログラム | この取り組み |
| publishes and makes citable / 公開して引用できる形にします | 外に開いて引用できるようにしています |
| concept DOI | 語は残す + 初出グロス「常に最新版へつながる代表 DOI」 |

運用上の注意 3 点:

- **造語の和訳名を JA prose から撤去してよい条件**: 用語連合（graph.jsonld / concept pages /
  glossary）を EN 版と機械層が担っていること。引用アンカーの本体が EN に残るなら、JA は
  読みやすさ優先で一般語に開いてよい（「造語は削除しない」規約の JA 側例外）。
- **見出しの和訳併記はアンカーを壊す**: 「Through-line（全体を貫く主張）」のような CJK 混じり
  見出しはアンカー生成がレンダラー間で不安定。見出しは英語のまま残し、**節冒頭の一文**で
  意味を開く。
- **Mermaid ラベルの言語も本文に従える**: 本文で和訳グロスを導入した概念は、JA 版の図ノード
  にも和文併記する（本文で日本語化した直後に図だけ英語へ戻ると違和感が残る）。意味・構造は
  変えない。

lint の i18n 注意: `doi_citation_pairing` は Citation 等の**英語見出し語**を探すため、JA 版の
「引用と識別子」節では false warning になる。EN 版が clean なら JA 側の warning は見送ってよい
（恒久対応するなら readme_lint.py に JA 見出しトークンを足す）。

検査器は `readme-clarity-reviewer` agent（Workflow Step 2 で readme-reviewer と並列起動）。

---

## Workflow（Code filter → readme-reviewer ∥ readme-clarity-reviewer → About 変更案 → 人間 gate → 適用）

### 1. Code filter — `readme_lint.py`（決定論的・structural only）

```
uv run --directory ~/.claude/skills/readme-writer python -m scripts.readme_lint "$ARGUMENTS"
```

引数は README の絶対パス。`--json` で機械可読出力。exit code が code-owned gate（**0=clean または warning のみ / 1=error severity あり / 2=not found・too large**）。

検査項目（**スコアでなく具体 issue**。severity 2 段階）:

**error（gate を落とす・ハード構造）**
- `single_h1` — H1 はちょうど 1 個
- `heading_levels` — 見出しレベルを飛ばさない
- `alt_text` — すべての画像に alt（**hard floor**: alt 無し = LLM に不可視）
- `local_link` — ローカル相対リンク / 画像 src が実在する

**warning（助言・gate を落とさない）** — 構造的に検出するが「本当に問題か」は判断なので surface のみ。意味判断は LLM review に委ねる:
- `raster_diagram_hint` — 図っぽいファイル名の raster（architecture/flow/diagram/pipeline 等の .png/.jpg/.webp/.gif）→ Mermaid 化を提案。SVG・スクショ・logo は除外
- `badge_budget` — badge が多すぎ（既定 >6）。**数のみ**判定（vanity か否かは LLM）
- `details_floor_leak` — `<details>` 内に DOI / BibTeX / CITATION トークン（floor 漏れの兆候。「真に floor か」は LLM 判断）
- `identity_lead` — H1 と最初の section の間に prose の lead 文が無い（**順序は強制しない**。H1 不在は single_h1 が担当）
- `doi_citation_pairing` — DOI があるのに how-to-cite（Citation 節 / BibTeX / CITATION.cff）が無い（**DOI を非研究 repo に強制しない**——DOI がある時だけ発火）

### 2. LLM review — `readme-reviewer` ∥ `readme-clarity-reviewer` を並列起動（author-reviewer separation）

lint が通ったら **`readme-reviewer` agent** と **`readme-clarity-reviewer` agent** を**並列**起動する。実装者（本 skill を回している Claude）と別 agent プロセスでレビューを回すことで author bias の盲点を避ける（`editor` / `essay-reviewer` と同型）。役割分担は paper-ecosystem の paper-reviewer ∥ clarity-reviewer と同型:

- **readme-reviewer** — artifact 側の厳密さ: フロア復元・構成・長さ・視覚形式。基準の正本は `~/.claude/agents/readme-reviewer.md`
- **readme-clarity-reviewer** — 初見読者の読書体験: 造語予算・内部文脈依存・日本語 register（ですます）・一文テスト。基準の正本は `~/.claude/agents/readme-clarity-reviewer.md`

readme-reviewer の lens 一覧:

1. **README-only recovery（最重要）** — テキストだけでプロジェクトを復元できるか、フロア欠落の具体列挙
2. Lead の What / Who / Why
3. 人間フック / 価値提案
4. 物語 / scannability
5. 短さの検証（偽装 llms-full.txt 化の逆方向チェック）
6. visual の妥当性（Mermaid / テキスト等価 / badge vanity）
7. lint warning の意味判断（badge_budget → vanity か、raster_diagram_hint → Mermaid 化すべきか 等）

出力は数値スコアでなく **具体所見 + y/n 承認できる粒度の具体 diff**（signal-first: `Lead: 6/10` は行動を変えない、「lead が誰向けか言っていない」が行動を変える）。Overall Assessment（EXCELLENT / GOOD / NEEDS REVISION / MAJOR ISSUES）だけは chain の早期停止判断が消費するため verdict として出す。

**Cross-model 並列（条件付き）**: 公開 repo の README なら `codex-review` を readme-reviewer と**並列**起動してよい（脱相関レビュー）。その場合は **prompt-driven モード**で writing 観点の指示を渡す — scoped モードは Codex 組み込みのコード向けレビュー指示が走るため prose に不適。例:

```
/codex-review "Review the README changes as prose, not code: is the project recoverable from the README text alone, is the lead clear about what/who/why, is anything load-bearing hidden in images or collapsed sections?"
```

### 3. fact 一致確認 → `context-sync`

README の事実が llms.txt / llms-full.txt / graph.jsonld と一致するか（cloaking 回避）は `context-sync` が正本。本 skill では再実装しない。

### 4. About の最適化（description / topics / homepage）

repo トップは README 本文と **About サイドバー**で 1 つの第一画面を作る。README がどれだけ良くても
**About が空なら「到達した人」にしか効かない** — topics は*まだ来ていない人*を索引から連れてくる
唯一の面なので、README と同じ作業単位で整える。

| 要素 | 出る場所 | 規約 |
|---|---|---|
| **description** | topic ページ・repo リスト・検索結果・外部ディレクトリ掲載時の唯一の一文 | README の lead と**同じ主張**にする（食い違いは cloaking）。**1 文目だけで機能が伝わる**構成にする（下記） |
| **homepage** | About と repo カードのリンク | docs サイト / その repo を解説した記事 / hub。**無いなら空のまま**（無関係な URL を埋めない） |
| **topics** | topic ページ・topic 付き検索の索引 | 最大 20。小文字英数字とハイフンのみ |

#### description に文字数目標を置かない

**2026-08-01 の UI 実測**: GitHub の topic ページと プロフィール repo リストは description 要素に
truncation クラス（`text-truncate` / `line-clamp`）を**持たず**、300 字超でも全文が折り返し表示された。
「カードで切れるから短く」は少なくともこの時点では誤った前提なので、**文字数目標を置かない**
（README の Length budget と同じ思想: 数値でなく構成で決める）。

**これは仕様保証ではなく観測**である — GitHub 公式 API doc は description を "A short description" と
呼ぶだけで、全文表示を約束していない。UI は変わりうるので、**長い description を採るときは
実際の topic ページで表示を 1 度確かめる**。切れていたら 1 文目だけで成立する構成に畳む
（下の「1 文目を完結させる」は、どちらに転んでも効く）。

効くのは長さでなく**構成**:

- **1 文目を、単独で機能が伝わる完結した文**にする。背景・出自・関連 repo・ADR 番号は 2 文目以降
- 走査読みでは 1 文目しか読まれない。2 文目以降は「クリックするか」を決めた後の補強
- **アンチパターン: 作品の題名だけを置く**（論文タイトルをそのまま description にする等）。
  題名は「何をするものか」を言っていないので、repo リストで中身を推測できない
- 外部ディレクトリ・awesome-list・OGP カードは**独自に truncate しうる**。GitHub の挙動をそこへ
  一般化しない（掲載先ごとに実物で確認する）

#### topics は「選ぶ」前に「測る」

どの語が索引面として生きているかは**実数で決まる**（意味の議論ではない → `when-code-when-llm` の構造的性質）:

```bash
gh api "search/repositories?q=topic:<topic>&per_page=1" --jq '.total_count'
```

| 規模 | 扱い | 例（2026-08 実測） |
|---|---|---|
| **> 50k** | 母数用に 1–2 個。**それだけでは埋もれる** | `llm` 105k / `mcp` 56k / `claude-code` 54k |
| **2k–20k** | **主力**。対象読者が濃く母数も現実的 | `agent-skills` 12.8k / `claude-skills` 6.2k |
| **< 500** | 固有名・造語。既に知っている人にしか効かない。1–2 個まで | `research-software` 466 |

- **単数形と複数形は別 topic**（`agent-skill` 2.5k と `agent-skills` 12.8k は別の索引面）。
  **両方が実勢を持ち、かつ repo にとって自然なら両方付ける**。件数は repo 数であって到達数ではなく
  重複もあるので、「片方だけだと到達が半減する」とは言えない — 判断材料は「その面に載る価値が
  20 枠のうち 1 つを使うに値するか」
- 広い面で母数・中規模で命中・固有名で識別、の 3 層を混ぜる
- 上限 20 枠は有限資源。不自然な語形で枠を埋めて、関連性の高い topic を追い出さない

#### 現状の把握（read-only。ここで書き込まない）

```bash
gh api repos/OWNER/REPO --jq '{description, homepage, topics}'   # 現状の 3 要素
gh api "search/repositories?q=topic:<topic>&per_page=1" --jq '.total_count'  # 候補 topic の実勢
```

**このステップの成果物は「変更案」であって適用ではない。** `gh repo edit` は GitHub への durable な
書き込みなので、Step 5 の承認を得るまで実行しない（`rules/common/coding-style.md` の
Reversibility Gate — 可逆でも「消す/変える判断」自体はユーザーのもの）。

変更案は 3 要素それぞれについて **現状 → 提案** の形で書き出す。homepage を**空にする**提案なら
それも明示する（無変更と区別がつかなくなるため）。

### 5. 人間 gate

README 本文と About の変更案（**件数とスコープを明示**）を**まとめて 1 回**提示して承認を取る
（1 作業 1 ゲート — `rules/common/human-gate.md`）。ここで人間が判断するのは**文章の正しさではなく
「この入口を公開物として引き受けるか」**（README は公開・不可逆で、テキストが意図そのもの）。
構造的な品質は Step 1 の `readme_lint.py` と Step 2 の `readme-reviewer` が既に持っている。

### 6. 適用と検証（承認後）

README を書き、About を反映する:

```bash
gh repo edit OWNER/REPO --description "..."            # description
gh repo edit OWNER/REPO --homepage "https://..."       # homepage（空にするなら --homepage ""）
gh repo edit OWNER/REPO --add-topic X --add-topic Y    # --add-topic は追加のみ（既存を消さない）
gh repo edit OWNER/REPO --remove-topic Z               # 削除は明示的に
```

検証:

```bash
gh api repos/OWNER/REPO --jq '{description, homepage, topics}'         # 適用の確認
gh api "search/repositories?q=topic:X+user:OWNER" --jq '.total_count'  # 索引反映の確認（数秒）
```

**自分の repo のメタデータ変更なので可逆**であり、外部ディレクトリへの申請（他者が管理する空間への
書き込み）とは審査面の有無でリスク構造が違う — 混同しない。

---

## What This Skill Does NOT Do（境界）

- `llms.txt` / `llms-full.txt` を書かない（→ `llms-txt-writer`）
- `graph.jsonld` を設計しない（→ `jsonld-knowledge-graph`）
- cross-surface の drift 検出 / 同期をしない（→ `context-sync` / `release-doi`）
- 記事 / エッセイを編集しない（→ `writing-ecosystem`）
- **social-preview 画像**（OGP カード）を作らない（画像制作は別作業。本 skill は不足を指摘するのみ）。
  description / topics / homepage は Step 4–6 で**本 skill が持つ**（README と同じ第一画面のため）
- 外部ディレクトリ・awesome-list への掲載申請をしない（他者が管理する空間への書き込みで、審査面と
  累積 footprint の判断が要る。本 skill が扱うのは自分の repo のメタデータまで）
- **品質スコア / grade / 評点を出さない**

---

## Anti-patterns

- 数値スコアだけ出して具体案なしで終わる（recommender 型の罠）
- 構造 lint で済む項目を LLM に判断させる / 意味的判断を regex で代用する（`when-code-when-llm` 参照）
- AI surface の数値指標（ski-ramp / entity density / 疑問見出し farming）を人間 README に流用する（可読性低下）
- **「ビジュアル優先」を散文の画像化と解釈する**（raster 図は text-only LLM に不可視 = 情報をエージェントから隠す。Mermaid を使う）
- **「削るな・再構造化せよ」を効かせすぎて偽装 llms-full.txt 化する**（フロアは小さく、上は容赦なく削る/relocate）
- 機械層（llms.txt/graph）が backstop する前提で README フロアを薄くする（grounding 経路で読まれない）
- `llms.txt`/`graph` を **README prose から** derive する（drift。manifest から derive）
- 人間向けに事実を盛る / マネタイズ訴求を足す（authenticity 毀損 + 機械層との矛盾 = cloaking。梱包は変えても主張は変えない）
- **topics を実勢を測らずに選ぶ** — 巨大 topic だけ付けて新着の奔流に沈む / 造語・固有名だけ付けて
  誰にも検索されない。どちらも「設定済み」に見えて索引面に載っていない（Step 4 の測定コマンド）
- topics の単数形か複数形の**片方だけ**付ける（別の面なので、大きい方を落とすと到達が半減する）
- description を README lead と**別の主張**にする（同じ repo が面ごとに違うことを言う = cloaking）

---

## Verification

```bash
cd ~/.claude/skills/readme-writer
uv sync --dev
uv run pytest tests/ --cov=scripts --cov-report=term-missing
```

`fixtures/sample_clean.md`（issue 0・Mermaid 図を使う best-practice 例）と `fixtures/sample_issues.md`（全 9 チェックを発火させる例）で基本挙動を確認できる。

---

## Related

- `readme-reviewer` agent（`~/.claude/agents/readme-reviewer.md`）— 本 skill の Step 2 を担うレビュー agent（artifact 側）。レビュー基準の正本
- `readme-clarity-reviewer` agent（`~/.claude/agents/readme-clarity-reviewer.md`）— Step 2 の並列相方（初見読者側）。Voice / Register 節の検査器
- [`codex-review`](../codex-review/SKILL.md) — 公開 README への cross-model 並列レビュー（prompt-driven モード）
- [`llms-txt-writer`](../llms-txt-writer/SKILL.md) — AI surface の対になる writer（研究値ベースの `geo_check.py` を持つ）。本 skill は人間 surface。
- [`when-code-when-llm`](../when-code-when-llm/SKILL.md) — structural / semantic の判定軸
- [`context-sync`](../context-sync/SKILL.md) — README ↔ 機械層の fact 一致 / drift（fact 検証はこちらに委譲）
- [`jsonld-knowledge-graph`](../jsonld-knowledge-graph/SKILL.md) — graph.jsonld 設計
- [`writing-ecosystem`](../writing-ecosystem/SKILL.md) — 人間向け長文 prose の orchestrator
- `inspiration.md` — 設計の出自・一次研究の provenance・外部エビデンスの出典（Portability のため SKILL.md 本文から分離）

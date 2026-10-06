<!-- origin: shimo4228 -->
# Visual 細則（readme-writer の参照資料）

規約の骨格は `../SKILL.md` の「Visual」節。ここは Mermaid styling・辺の交差・hero art・表セル・raster の細則。README 冒頭の概要図は `overview-diagram.md`。


### 形式の選択

| 中身 | 最適形式 | 理由 |
|---|---|---|
| README 冒頭の概要図（仕組みを一目で） | **committed SVG、skill: `mono-figure` で描く、言語別**（`overview-diagram.md`） | 役割は人間の注意。情報は直後の identity 段落が持つので、線形でも図にする |
| 本文中の 3 ステップの線形 / 単純な列挙 | **prose / list / 小さな表** | 全デバイス（特にモバイル）で読める。図にする価値がない |
| 本当に graph 形状（関係・多分岐・matrix） | **Mermaid（`TD` 縦方向）** | ソースがテキストで LLM も読める。縦スクロールはスマホで自然、横（`LR`）は潰れる |
| 大きい / 複雑な図 | **committed SVG（拡大・パン可）/ subsystem 分割** | 巨大 Mermaid は desktop でも上限に当たり、モバイルで潰れる |
| 実 UI / 実行結果 / 写真 | **raster（PNG/JPG/WebP/GIF）** | Mermaid で表現できないものだけ |


### Mermaid の要点

- GitHub が theme-aware SVG にネイティブ描画。ソースはテキスト（diff 可能・~10 token/edge）で **pixel を見られない text-only クローラにも読める**。散文/graph に埋もれた構造（concept matrix・phase binding・pipeline 段）を Mermaid 化すると**短くなり情報密度が上がる**。
- **モバイル最優先で `TD`（縦）**。横長 `LR` は狭幅で破綻しやすい。
- 描画上限は char ベース（`maxTextSize` 既定 50,000）+ edge ベースで、ノード数ではない（「50-100 node が限界」は俗説）。超えそうなら subsystem 分割。special な Project README では描画されない。
- **視覚的ポップ化の正統経路は Mermaid styling**（`%%{init}%%` themeVariables / `classDef`）— 色・フォントも text ソースに載るので LLM 側のコストゼロ。classDef で色を塗るときは `color:` でテキスト色も明示する（GitHub の dark mode が淡色 fill の上の文字を白に反転して潰すのを防ぐ）。参照 URL は `inspiration.md` の「Mermaid visual styling」節。
- **辺の交差はコードで直せる**（描き直し不要）: (1) ノードの左右配置は**初出順**で決まる — 辺のグループが隣接ノードに繋がるよう宣言順を入れ替える。(2) 1 ノードが多数に fan-out して交差するときは**矢印の向きを反転して sink にする**（`A --> B & C & D` を `B & C & D --> A` に。A が最下段に落ち、収束の意味論も出る）。
- 抽出器が Mermaid を落とす可能性があるので、上の**テキスト等価**で意味を必ず別途担保する。

### カバーアート（hero）

above-the-fold の「任意の hero」枠の実装ガイド。**唯一、純装飾 raster が正当な場所**:

- **第一画面との取り合い**: 横長の hero は desktop の第一画面の半分以上を占めうる。profile README は
  列の上端が y=228 なので、高さ 340 px の hero と H1・lead で第一画面（572 px）が埋まり、入口の
  見出しが fold の外へ出た（hub の実測 2026-10-06）。hero を置くなら、描画証拠で入口が fold の内側に
  残るかを確かめる
- **配置**: 言語切替行（あれば）と H1 の間。概要図（ラベルを持つ）とは別物で、hero は**画像内にテキスト情報を入れない** — 名前・タグラインは H1 と本文が持つ（画像内文字は LLM に不可視なので、入れると情報が消えるか二重管理になる）
- **仕様**: 横長 3:1〜4:1。画像自身に背景色を持たせる（GitHub の light / dark 両モードで安定）。生成画像は幅 1600px・数百 KB 目安に圧縮して `assets/` に commit（`sips -s format jpeg -s formatOptions 85 -Z 1600` で PNG 数 MB → ~300KB）
- **alt 必須・言語別**: README.ja には日本語 alt を書く
- **モチーフとパレットを README 内の図と揃える**と一枚の設計に見える（AI で生成するときの作法は下の段落）


**AI で生成するときの作法**（hub repo `shimo4228/shimo4228` の cover で使った、2026-07-27）:

- **Colors: name them, don't hex them.** Image models ignore hex codes; list
  color names ("amber, lavender, soft blue, sage green, slate gray") and
  follow up with "more muted, desaturated" if the output drifts.
- **Aspect ratio is routinely ignored** — plan to crop after generation rather
  than fighting the model for 4:1.
- **Motif from the repo's own structure beats generic beauty.** Offer the model
  the README's actual concepts (e.g. "five strands converging to one point" for
  a five-line hub) and the diagram's palette; the result reads as one design
  system instead of stock art. Style directions that worked: modern sumi-e
  (single brushstroke + ensō) for a meditation-rooted program — chosen over
  generic "flowing gradient lines" precisely because it encodes the program's
  distinctive origin instead of hiding it.
- **Identity check before prettiness:** if the style would fit any AI repo's
  banner, it is erasing the differentiator. Pick the style that only this
  program could justify.

### GitHub で使える見た目の手段（制約）

GitHub は `style` / `class` / `bgcolor` を sanitize するので、**色・余白・フォントは指定できない**。
見た目を変える手段は block の形の選択だけで、github-markdown-css での重さは次のとおり
（調査 report `shimo4228/shimo4228@a7f0c59:docs/plans/research/2026-10-06-readme-visual-eval.md` §2、as-of 2026-10-06。決定は ADR-0088）:

| 手段 | 見た目 | 制約 |
|---|---|---|
| list | 枠も背景も無い。最も軽い | — |
| table | 罫線・縞・太字 header。最も重い | 狭幅では表ごと横スクロール（mobile の README 列は 300 px 前後 — 値は `readme_render.py` の `SURFACES`）。改行できない長い token があると出る |
| alert `> [!NOTE]` 等 5 種 | 色付きの左バー + 色付き title | 文書に 1〜2 個（GitHub Docs）。入れ子不可。`POST /markdown` は gfm mode でだけ描く |
| blockquote | 灰色の左バー + 灰色の文字 | — |
| h1 / h2 | 下罫線あり（h3 以下は無し） | — |
| HTML `<table>` | `align` / `valign` / `width` / `colspan` / `border` 可 | `style` / `class` / `cellpadding` 不可。中央寄せは `align="center"` だけ |
| `<picture>` + `<source media>` | light / dark で画像を切り替える | theme ごとに別ファイル |

隣の節と重さが違うことは、それ自体は欠陥ではない（役割が違えば形も違ってよい）。判定は
checklist §V3 で、描画は `scripts/readme_render.py` で確かめる。絵文字アンカーは好みが分かれるので、
著者の確認なしに既定案にしない。

### raster / その他

- raster は **load-bearing な情報を担わせない**。**alt-text を必須**（hard floor: text 経路は alt しか読まない = alt 無し画像は LLM に不可視。a11y だけの話ではない）。
- dark/light は `<picture><source media="(prefers-color-scheme: …)"><img alt="…"></picture>`。`<img alt>` は二重に load-bearing。
- 画像 asset は repo に commit し**相対パス**参照。外部 hotlink（camo 破綻）と inline/animated `<svg>`/`<embed>`/`<object>`（GitHub が sanitize）を避ける。
- CLI repo: asciinema→agg GIF + 一文キャプション。UI repo: スクショ/GIF + alt-text。

> README 冒頭の概要図は `overview-diagram.md` の手順で SVG を `assets/` に置く。詳しい構成図は skill: `archify` で作り docs/ からリンクする。

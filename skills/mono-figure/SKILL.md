---
name: mono-figure
description: "Draw a static explanatory figure (lines, arrows, numbers, labels) for an article or README in the mono-color look, as SVG or through Codex image generation. Use when a section or README needs a mono-color diagram. For a poster with no text, use mono-color; for an interactive diagram, use archify."
user-invocable: true
origin: shimo4228
---

# mono-figure

見た目は mono-color、仕組みの描き方は artifact-diagramming が決める。このスキルが持つのは、
ポスター用の mono-color を図に使うための対応表と、媒体・保存先の取り決めだけ。デザインの規則は
足さない。見た目の判断は、その都度 mono-color の本文と catalog で決める。

図では使わない mono-color の規則（写真と一枚もののポスターを前提にした項目）: Hard Avoids の
vector-flat・card grids・UI panels、Reference-Derived Composition Grammar の 1〜3 手（一つの物が
45〜80%、文字が物と衝突、紙が画像を切る）、Final Quality Gate のうち網点・機械的な質感・物の占有率・
見出しと物の交差・画像の中の紙の形の項目、Typography の「最大の文字は最小の 5〜12 倍」（図の文字の
大きさは置き場の規約が決める）、Recipe Manifest を人に見せない規則（下の「manifest を残す」が代わる）。

始める前に読む:

- skill: `mono-color`（`~/.claude/skills/mono-color/SKILL.md`。catalog は同じ dir の `design-system/`）
- skill: `artifact-diagramming`（Claude Code 同梱。仕組みを描く・矢印にラベル・文字の読みやすさ）

## 設計表の対応

mono-color の Recipe Manifest を、図では次のように埋める。

| 項目 | 図での扱い |
|---|---|
| subject / intent | 図が見せる仕組み 1 つと、その図の役目 |
| exact_text / text_language | 図の文字はすべて原稿（記事・README）から写し、原稿の言語のまま。数字も原稿の値 |
| representation | abstract symbol extraction（写真を使わず、線・面・ラベルで描く） |
| ratio | 置き場の規約が決める |
| substrate / mode / palette / inks / plate_roles | mono-color の規則と catalog どおり。著者が明示して選んだらそれに従い、manifest に書く |
| layout | 頁の配置（見出しの位置・余白・情報の帯）に使う。図の中の線と箱の配置は artifact-diagramming が決める |
| empty_paper / visual_tension / focal_event / release_zone | mono-color どおり |
| type_hierarchy | 役割は catalog どおり。書体は描く環境に入っている face から役割に合うものを選ぶ（例: macOS で literary serif → Hiragino Mincho、grotesk → Hiragino Sans、mono → Menlo） |
| disruption | mono-color どおり 1 つ |
| carrier / unresolved_edge / image_treatment / imperfections / imperfection_seed | SVG では使わない（図の文字はほぼ全部が事実の文字で、mono-color は事実の文字を歪めない）。画像生成では image_treatment を clean plate separation、imperfections を 0 にする |

manual gesture（Composition Grammar の 4 手目）も mono-color どおり 1 つの family に限る。
1 本の記事・README の図どうしの揃え方は、mono-color の series の規則（ink・spacing・plate logic）に従う。

manifest は図のファイルの先頭にコメントで残す（HTML なら HTML コメント、SVG なら SVG コメント）—
同じ入力から同じ図を作り直せる。

## 媒体と保存先

mono-color の Default Deliverable（ラスター画像を `~/Desktop/Claude skills/mono-color/` に保存）、
Output Format、manifest を見せない規則の代わりに、図はその repo の置き場に、その repo の寸法・path・
上限で出す。zenn-content は `zenn-format` の Figures（HTML に描いて PNG に撮る）、README は
readme-writer の `references/overview-diagram.md`（言語ごとの SVG をそのまま commit）。

## 既定の道: SVG で描く

1. manifest を埋める（上の表）
2. artifact-diagramming の要領で SVG に描く。色は manifest のインクだけ、文字は原稿から写す
3. PNG に撮る置き場（Zenn など）: 図の dir を `python3 -m http.server 8765 --bind 127.0.0.1 --directory <figures dir>`
   で配信し、Playwright で置き場の寸法に resize → navigate（`?v=<n>` を付けて cache を避ける）→
   screenshot（scale css、png）。`file:` の直開きは Playwright が拒否する。SVG をそのまま置く場所
   （README）: 描画確認は readme-writer の `references/overview-diagram.md` の手順で行う
4. 描いた結果を `Read` で目視し、はみ出し・重なり・枠を越える文字・地と見分けにくい色を直して
   描き直す。ファイルの大きさを置き場の上限内に収め、server を止める
5. mono-color の Final Quality Gate のうち、上で外していない項目で見直す

図の文字と原稿の照合は、その repo の執筆手順が持つ（zenn-content では writing-ecosystem の
fact-checker）。

## 画像生成の道: Herdr で Codex に生成させる

著者が Codex（Herdr）での画像生成を明示して頼み、Herdr の中で動いているとき（`HERDR_ENV=1`）に
使う。`HERDR_ENV` が 1 でなければ、そのことを著者に伝えて SVG の道で描く。Herdr の操作の正本は
skill: `herdr`、委譲の境界は `rules/common/boundary.md`。

1. `codex features list` で `image_generation` が有効かを確かめる
2. mono-color の Prompt Compiler で 5 段落の prompt を組む。図の文字は 1 つ残らず prompt に
   書き、「書いた文字だけを、原稿の言語のまま描く」と指定する。manifest と prompt を 1 ファイルに
   書き出す（置き場は repo の規約。zenn-content は zenn-format の Figures）
3. `herdr pane split --current --direction right --cwd "$PWD" --no-focus` で隣に pane を作り、
   `herdr agent start <name> --kind codex --pane <pane-id>` で Codex を立てる
4. `herdr agent prompt <name> "<file> を読み、## Prompt の文で画像生成を 1 回行い、<出力 path> に保存し、path だけを返す" --wait --timeout 600000`
5. 出力ファイルがあることを確かめてから `Read` で開く（settled は prompt が届いたことまでしか示さない — rules/common/agents.md）
6. 図の文字を prompt の文字と 1 つずつ照合する。抜け・崩れ・足された語があれば、その文字を
   prompt で強めて 1 回だけ再生成する。それでも合わなければ、mono-color の Generation and
   Inspection 4（文字の少ない下地に layout で文字を重ねる）の代わりに、SVG の道で描く
7. 終わったら、自分が作った pane を `herdr pane close <pane-id>` で閉じる

## 参照

- 図を置くか・何枚・どこに置くか・寸法: その repo の規約（zenn-content は `zenn-format` の Figures）
- 英語版の図: zenn-content は `devto-translator` の Phase 1.5

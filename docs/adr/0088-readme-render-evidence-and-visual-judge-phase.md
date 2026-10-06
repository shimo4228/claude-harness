# ADR-0088: readme-writer に描画証拠を足し、readme-judge に見た目の Phase V を置く

## Status

accepted — [ADR-0077](./0077-readme-review-single-judge-with-claims-check.md) Decision 2 の判定順
（Phase A → B → C）、Review-when の 1 つ目の比較対象、Consequences の固定質問数を部分的に弱める
（注記は ADR-0077 側）

## Date

2026-10-06

## Context

- Plan: `shimo4228/shimo4228@a7f0c59:docs/plans/readme-eval-eval-loop-readme-mellow-octopus.md`（承認
  2026-10-06）。調査 report は同じ commit の `docs/plans/research/2026-10-06-readme-visual-eval.md`
  （4 角度 + local の一次確認）
- 著者の指摘（2026-10-06）: hub の profile README で、「Start here」の箇条書きが直後の表に比べて見にくく
  地味。依頼は「README の見た目について eval 項目を調べて eval loop を回し、README 関係のハーネスに反映」。
  著者は plan の段で、反映の範囲に「描画まで入れる」を選んだ
- 判定器 `agents/readme-judge.md` は markdown のテキストだけを読む（tools は Read / Grep / Glob）。
  描画後の見た目を見る工程は、概要図を PNG にして目で見る（readme-writer Workflow Step 2）と、判定ループが
  終わった後の著者のプレビュー（Step 6）だけで、判定器は見た目を問えなかった
- live の実測（2026-10-06、in-app browser、login 済み・dark theme・各 1 回、`getBoundingClientRect` と
  `getComputedStyle`）:
  - profile README（`github.com/shimo4228`）: 1280×800 で列の幅 846 px・上端 y=228、375×812 で幅 293 px・
    上端 y=901、本文 14 px。desktop では「Start here」の H2 が y=880 で最初の画面の外。mobile では README
    全体が最初の画面の外で、At a Glance の表は scrollWidth 463 / clientWidth 293 で横スクロールする
  - repo README（`github.com/shimo4228/agent-knowledge-cycle`）: 幅 838 / 309 px、本文 16 px。列は file 一覧の下
    から始まり（y=1102 / 871）、その高さは repo ごとに違う
- `gh api -X POST /markdown` の実行結果（2026-10-06）: `markdown` mode は表・明示の改行を描き、ソース上の
  折り返しを改行にしないが、`> [!NOTE]` を alert にせず blockquote で返し、タスクリストも描かない。`gfm` mode は
  alert を描くが、ソース上の折り返しをすべて `<br>` にする（英語の段落を折り返して書く README では、
  github.com に無い改行が出る）
- 調査 report の要点:
  - 単一回答の判定では二値の rubric が Likert より人間との一致が高い（WebDevJudge、arXiv 2510.18560）
  - 位置の特定は VLM の最も弱い作業（AesEval-Bench、IoU < 0.20）
  - pairwise には位置バイアスと反転がある。WebDevJudge の GPT-4.1 は、順序を入れ替えた同じ組で 83.3% は同じ
    答えを返し、15.8% は 2 番目を、0.9% は 1 番目を選んだ（summarizer 経由の全文）。同一入力の 50 回反復では
    平均 13.6% が反転した（arXiv 2606.13685、GPT-4o-mini / GPT-4.1-mini の 29 タスク、abstract のみ）
  - LLM の書き直しは 1 ラウンド目から register を均す（arXiv 2604.22142、abstract のみ）
  - 見出し・太字・リストの量は人間の選好も押し上げる（LMArena style control、snippet のみ）
  - 隣接節の視覚的な重さを揃える原則を検証した研究は見つからない（report C9）
- 描画の再現性の検算（2026-10-06）: `uv run python -m scripts.readme_render <README> --out <dir> --surface
  profile|repo` で、hub README（commit `eddab91`）と AKC README を描くと、H2 の位置が live と一致した（hub の
  「Start here」desktop 652 / mobile 662 px、AKC の最初の 2 つの H2 desktop 493・1011 / mobile 917・2107 px）。
  AKC の live の値は README 上端からの位置で 493・1011 / 917・2107 px（同日、上の live の実測と同じ条件）。hub の
  表のはみ出し幅（463 px）も一致した。plan は `gfm` mode + `context` を採っていたが、この検算の過程で AKC の
  折り返しの差が見つかり、`markdown` mode に変えた（Alternatives の 5 つ目）

## Decision

1. `skills/readme-writer/scripts/readme_render.py` を足す。手順は次のとおり:
   - README を `gh api -X POST /markdown`（mode=markdown）で HTML にし、alert の blockquote を github.com と
     同じ `markdown-alert` の markup に書き換える（marker の大文字小文字は問わない）
   - その HTML を `<article class="markdown-body">` に入れ、同梱の `assets/github-markdown.css`
     （npm github-markdown-css 5.9.0、MIT、license 同梱）を当てる
   - Playwright の Chromium で、列ごとに light / dark を撮る
   - 出力は PNG tile（長辺 2000 px 以下 — Read が縮めずに見せる大きさ）と、blur 6px の squint tile と、
     `render.json`（見出しと block の `top`、fold、横にはみ出す要素、画像の寸法、tile の高さ）
   - 書き換える URL は `<img>` と `<source>` の src / srcset だけ。`/` で始まるものは repo の root から、ほかは
     README の dir から解決し、repo の外を指すものは読み込めない URL にする（github.com でも壊れた画像になる）
   - 列の幾何は `--surface profile|repo` で選び、値の正本は `SURFACES` の 1 か所に置く（Context の実測値）。
     repo の上端は不明として扱い、README の最初の 1 画面（viewport の高さ）をその README の第一画面とする
   - 判定・閾値は持たない。exit code は 0（描いた）と 2（file・`gh`・Playwright の失敗）。依存に
     `playwright>=1.63,<2` を足す
2. `skills/readme-writer/scripts/readme_evidence.py` の JSON に `layout` を足す（新しい module
   `skills/readme-writer/scripts/readme_layout.py`）。内容は H2 ごとの block 形の数、list の頭の型、表の形、
   alert の数、見出しの大文字化の型、行き先を言わないリンク文言
3. `readme-judge` は Phase A を凍結した後、render directory が渡されたときだけ Phase V を回し、その後に
   Phase B・C へ進む。問いは checklist の新しい §V（V1 第一画面 / V2 squint / V3 隣接節の形 / V4 狭幅 /
   V5 light・dark / V6 強調の段数）で、二値で答える。読む画像は viewport ごとに light の全 tile、squint の
   1 枚目、dark の 1 枚目と画像を含む dark tile。証拠は、見えている文字列か要素名と `render.json` の `top` で書き、画像から目測した座標を
   使わない。判定器の「データとして扱う」の枠に、`render.json` と画像（画像の中に描かれた文字を含む）を足す
4. 描画の受け渡しは readme-writer の Workflow が持つ。最初の draft 判定に渡した描画を `render-r0` として残し、
   recheck と final の前には直した版を新しい dir に描き直して渡す。final では `render-r0` も渡し、判定器は
   desktop の最初の light tile を順序を入れ替えて 2 回比べ、両方で改稿後を選んだときだけ「改善」と書く
5. §V の Fix は markup・順序・構造（節の並び・形・見出しの付け替えと節の分け直し・画像の有無と大きさ・
   alert の数）だけを動かし、本文の言い換えを含めない。V3 の Fix は「軽い方を重く / 重い方を軽く / 役割の
   差が見えるように見出しを付け替えるか節を分け直す」の 3 方向から選ぶ。V3 は著者の taste の基準だと
   checklist に書く
6. Step 6 の著者のプレビュー（GitHub でスマホ幅と dark を見る）は残す。描画は近似なので、live とのずれは
   ここで気づく。Step 7 で `skills/readme-writer/evals/read-through-log.md` に書くとき、描画を判定に渡した回は最終判定の欄に
   「§V あり」、見た目の指摘は主な種類に「見た目」と書く
7. 判定器の較正に `skills/readme-writer/evals/fixtures/visual-canary.md` と
   `skills/readme-writer/evals/fixtures/visual-canary.expected.md` を置く。canary は、入口が fold の外にあり
   （desktop で fold から 130 px 下）、alert が 3 つ並び、表が mobile で横にはみ出す README。スモークテストの
   条件は、§V の指摘を 3 件中 2 件以上拾うこと

## Review-when

- github.com の README の列幅・profile の上端・本文の文字サイズが変わったと分かったとき（目安は、描画した
  H2 の位置が live の実測から 10 px 以上ずれる。気づくのは Step 6 の著者のプレビューか、live を測った回）。
  `SURFACES` を測り直し、CSS を同梱し直す
- `skills/readme-writer/evals/read-through-log.md` の「§V あり」の行のうち 2 行続けて、主な種類に「見た目」が
  記録されたとき。§V の問いか描画の範囲を見直す
- 判定器の substrate が画像を読めなくなったとき（Read が PNG を画像として返さない）。Phase V を外す

## Alternatives Considered

- **何もしない（hub README を手で直し、Step 6 のプレビューに任せる）**: 依存も問いも増えない。ただしプレビューは
  判定ループが終わった後の 1 回で、判定器は見た目を問えないまま Fix を出す。fold の位置のような問題は最後の
  人間ゲートまで見つからない。著者は「ハーネスにも反映」を依頼した
- **テキストの証拠と判定基準だけを足す（描画しない）**: 依存が増えない。ただし fold の位置・表のはみ出し・
  dark での見え方は markdown から決まらず、著者は「描画まで入れる」を選んだ
- **見た目専用の別 agent を置く**: 問いが分かれて注意は割きやすい。ADR-0077 の「レビュー agent は 1 本」を
  崩し、Phase A の第一画面の判定と V1 が別々の verdict に分かれる。書き手と判定器を分けることは今の
  1 本でも成り立っている
- **push した後に live の github.com を撮るだけにする**: 実物そのものを見られるが、公開前の草稿を判定
  できない。較正（Review-when の 1 つ目）にだけ使う
- **`gfm` mode で描く**: alert をそのまま描ける。ただし英語の段落を折り返して書く README（AKC など）で
  github.com に無い改行が出て、fold の位置の証拠が崩れる。`markdown` mode に alert の書き換えを足す方が
  ずれが小さい（Context の検算）
- **毎回の判定で pairwise の前後比較をする**: 一致率は単一回答より高い。ただし LLM の pairwise は反転と
  位置バイアスが大きく、順序を入れ替えて 2 回ずつ読むと画像の量も倍になる。著者通読の直前の binding な
  判定（final）で 1 回だけ行う
- **md2static / pageshot を使う**: 同じ経路の既製品。保守状態を確かめられず、自前でも `readme_render.py` は
  285 行（2026-10-06 の `wc -l`）で済む

## Consequences

### Positive

- 草稿を、公開前に github.com と同じ列幅・文字サイズで判定できる。fold の位置と横のはみ出しが、数値の証拠で
  判定器に届く
- 隣の節と重さが違うことを、形と役割の対応で問えるようになった。書式を足す方向にだけ寄せる偏りに、問いの
  側で歯止めがある

### Negative

- 依存が増える: Playwright と Chromium（`playwright install chromium`）、`gh` の認証、GitHub API への通信。
  オフラインでは描画できない。依存の取り込み審査（2026-10-06）: `pip-audit` で既知の脆弱性なし、playwright
  1.63.0 は 2026-09-15 リリース・Apache-2.0・Microsoft の保守、推移依存は pyee と greenlet
- README の画像は第三者が描画のときに中身を決められる（動的な badge など）。画像の中の文字はテキストの判定を
  通らずに判定器に届く。判定器の「データとして扱う」の枠で受け、最終の関門は著者通読（Step 6）
- 描画のたびに README の本文を GitHub の `/markdown` API へ送る（公開前の草稿を含む）。外部送信は
  boundary.md で人間に渡す操作だが、送り先は README を公開する GitHub そのもので、著者は API 名を明記した
  plan を承認した（2026-10-06）。描画のときにページが外部の画像（badge など）を取りに行く
- github-markdown-css は github.com の CSS から生成したスナップショットで、GitHub が描画を変えると静かにずれる。
  Mermaid 図とタスクリストは描かれない（図は code block のまま写る）
- 判定器の固定質問は §F 3 + R 15 + §J 4 + K 6 の 28 問に §V 6 問が加わって 34 問になり、画像も読む。
  hub README では 1 言語あたり 10 枚（desktop light 2・mobile light 4・各 viewport の squint と dark の 1 枚目）で、
  1 枚は最大 4,784 token（Claude 4.7 以降の上限、28×28 px = 1 token）。2 言語を 1 回で渡すと 20 枚、final の
  前後比較で 22 枚になる。長い repo README は 1 言語で 20 枚を超える: AKC README（`--surface repo`）は light
  だけで desktop 6・mobile 12 枚、squint と dark を足して 22 枚（2026-10-06）。tile を 2000 px にしたので、
  20 枚を超えたときの縮小（約 2,000 px、Anthropic vision doc）でも縮まない
- Phase V の位置（Phase A の凍結の後、Phase B の前）は、同じ process の中の順序の指示で守られるだけ
- 描画は GitHub の profile / repo の 2 種の幾何しか持たない。ほかの面（npm・PyPI・GitHub Mobile の
  native app）の見た目は判定の外

### Neutral

- 列の幾何の正本は `readme_render.py` の `SURFACES` で、checklist §E と SKILL.md はそこを指す。具体的な px は
  ほかに、`skills/readme-writer/references/visual.md` の hero の注意（hub の観測値）、`agents/readme-judge.md` の証拠の書き方の例、
  ADR の索引行にもある。前の 2 つは日付つきの観測と例で、Review-when の 1 つ目で `SURFACES` を直したときに
  合わせて見る
- 戻し方は、harness の revert と `uv lock` の戻し。harness-sync の後なら公開 copy（claude-harness と
  readme-writer の単独 repo）も戻す。Playwright の Chromium は `~/Library/Caches/ms-playwright` に残る。
  描画の PNG は scratch に出すので、repo には残らない

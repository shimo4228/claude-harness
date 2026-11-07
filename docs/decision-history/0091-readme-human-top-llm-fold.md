# ADR-0091: README の見える本文は人間の読者に、LLM-read フロアは末尾の畳んだ節に置く

## Status

accepted — [ADR-0077](./0077-readme-review-single-judge-with-claims-check.md) Decision 1 が作った §F
（フロアの有無）の意味を、「見える本文に在るか」から「末尾の畳んだ節に在るか」へ部分的に置き換え、固定質問を
1 問足す（R16）。ADR-0077 と [ADR-0088](./0088-readme-render-evidence-and-visual-judge-phase.md) に注記する

## Date

2026-10-08

## Context

Plan: [docs/plans/readme-human-top-llm-fold.html](../plans/readme-human-top-llm-fold.html)（承認 2026-10-08）

- 2026-06 の readme-writer は、README を「grounding 経路の LLM が確実に前提にできる唯一の面」とし、LLM-read
  フロア（identity・why・canonical な事実・具体例 1 つ・link-map）を見える本文に置き、`<details>` にフロアや
  機械向けの導線（llms.txt / graph.jsonld）を入れないと決めていた。この判断の記録は ADR ではなく
  `skills/readme-writer/inspiration.md`（「2026-06 extension: visual-first + the LLM-read floor」節）にある。
  冒頭の概要図を既定で置く規則は、ADR-0077 の変更の commit 本文に記録されている
- 著者の観察（2026-10-08）: 以前は README の読者が LLM 検索だけだったが、人間の読者が増えた
- 印の試験（著者が自分の README と記事を文ごとに読み、「要らない」「止まった」の印を付けた。commit 0529e0b、
  生の印は `skills/readme-writer/evals/reader-cut/marks-2026-10-08.json`）:
  - jev-skill-router の README.ja は、送信内容と限界の §8〜9 を塊で読み飛ばした → 見える本文から摩擦の解消に
    効かない説明を外し、開示は 1 行にして詳細を畳む（Decision 1・3）
  - contemplative-agent の README.ja は冒頭 11 文で離脱した。冒頭には何をするかを言う 2 文の段落がすでにあり、
    著者はその段落で「止まった」（著者「冒頭を読んでも結局何をするものなのか全くわからない」「情報過多」）
    → 冒頭の段落が読者の知らない語で書かれていた失敗（検査表 R1）と、続く本文の情報過多の両方を示す。
    短い段落を置くだけでは足りない
  - 著者のモデルは「人間向けの README はキャッチコピーのように短く機能を言い、あとは摩擦の解消に費やす」
- canary 実験（2026-10-08、各条件 1 回、`skills/readme-writer/evals/grounding-canary/PROTOCOL.md`、約 2.6 万字の
  README を持つ公開 repo shimo4228/readme-fetch-canary）: URL を取得した 5 経路 — ChatGPT（GPT-6・Plus）、
  Claude.ai（Opus 5.5・Max）、Grok（X Premium）、Qwen 3.7 Plus（無料）、Gemini 3.6 Flash（無料・思考強化・通常
  チャット）— はどれも `<details>` の中と README 末尾の語を答え、README からリンクした docs/ 配下のページも読んだ。
  Grok は初回の取得で README が切れたと申告し、残りを自分で取得した。Gemini は 3 回中 1 回しか取得せず（一時
  チャット・思考なしの 2 回は取得しなかった）、Perplexity の無料版は取得せず、検索の断片に出た repo の About の
  説明文だけを見た。llms.txt は取得した 5 経路中 4 経路が読んだ。測ったのは「畳んだ中身が読まれるか」で、
  「答えの中でどれだけ効くか」は測っていない
- 外部調査（`docs/plans/research/2026-10-08-readme-human-top-llm-fold.md`、as-of 2026-10-08）: クローラによる
  llms.txt の取得はほぼ無い（二次記事経由のサーバーログ調査 3 本）。静的な `<details>` が割り引かれる・隠し文字
  として扱われるという証拠は、賛否どちらも見つからなかった。逆向きに最も近い証拠は GEO の研究
  （arXiv 2604.25707、要旨のみ）で、影響力の大きいページほど長く、抜き出せる事実が多いという相関を報告する
  （一般の web ページで、README ではない）

## Decision

1. README の見える本文は人間の読者に向ける。冒頭の短い段落で、読者がまだ知らない語を使わずに何をするものかを
   言い、残りは読者が使い始めるまでの摩擦の解消に使う。行数と節の型は決めない（著者の補正:「三行」は
   レトリックで、README の構造を型で縛らない）
2. LLM-read フロア（5 要素）と機械向けの導線（llms.txt / graph.jsonld へのポインタ）は、README 末尾の
   `<details>` に文で置く。画像だけ・リンク先だけでは数えない。フロアを超える深い内容（設計の経緯・全オプション・
   実験記録）は docs/ に置き、フロアからリンクする
3. 読者の判断に関わる開示（外部へ送られるデータ・有料の鍵・破壊的な操作）は、見える本文に 1 行で言い、詳細を
   畳んだ節に置く
4. 概要図は、仕組みを知らないと使い始められない repo にだけ置く（plan で「既定で置く」「第一画面から外す」と
   比べ、著者が選んだ）
5. 証拠 JSON に `size`（生の字数 `chars` と畳んだ節の外の字数 `chars_visible`）を足す。生の字数が約 1.5 万字を
   超えたら、判定器が docs/ へ移せる節を問う（検査表 R16）。1.5 万字は plan で 2 万字と比べた著者の選択で、
   較正していない。だから gate にせず、判定器の問いにとどめる
6. GitHub の About の description を README 冒頭の段落と同じ主張にする既存の規則に、根拠を足す: URL を取得
   しない AI の経路が見るのはこの 1 文だけ
7. 変えるファイル: `skills/readme-writer/SKILL.md`、`skills/readme-writer/references/readme-judge-checklist.md`
   （§E の `details_blocks` と `size` の行、F1・F3・R1・R3・R16・K5）、`skills/readme-writer/references/about.md`、
   `skills/readme-writer/inspiration.md`（2026-10 の節）、`skills/readme-writer/scripts/readme_sections.py` と
   `skills/readme-writer/scripts/readme_evidence.py`（`size`）、`skills/readme-writer/tests/test_readme_evidence.py`、
   `skills/readme-writer/tests/golden/sample_clean.json` と `skills/readme-writer/tests/golden/sample_issues.json`

## Review-when

- 著者は、この ADR に沿って既存の README を書き直す最初の回の前と、ChatGPT・Claude.ai・Grok のどれかが URL
  取得の機能を変えたと告知したときに、canary を同じ質問で再実行し、PROTOCOL.md の記録表に足す。取得した経路が
  `<details>` の中を返さなくなっていたら、フロアを見える本文に戻す。Gemini は 3 回中 1 回しか取得していない
  ので、この判定には数えない
- この ADR に沿って書き直した README を著者が通読し、なお冒頭で離脱する、または見える本文の塊を読み飛ばすとき
  — 見える本文の規則が足りない
- 索引クローラが `<details>` の中身を落とす・割り引くと分かり、著者の見つけられ方がそのクローラに依存するとき
- README の読者がまた LLM 中心に戻ったと著者が判断したとき

## Alternatives Considered

- **README を人間専用にし、フロアを docs/ や llms.txt に移す** — 不採用。canary では docs/ も取得した 5 経路
  すべてが読み、畳んだ節と区別できなかった。それでも README の中に畳む方を取るのは、README 1 回の取得で
  フロアまで届くからで、リンク先は 1 回ずつ取得が増える（Grok は切れた README を取り直した）。llms.txt は
  5 経路中 4 経路しか読まず、クローラはほぼ取得しない
- **2026-06 の設計のまま（フロアを見える本文に置き、長さで抑える）** — 不採用。人間の読者が増え、印の試験で
  著者自身が冒頭で離脱し、見える塊を読み飛ばした
- **末尾に見える「AI 読者向け」節を置く**（zenn-content の記事 `~/MyAI_Lab/zenn-content/articles/ai-review-task-loop.md`
  で 2026-08-16 に 1 回試した形。「人間の読者はここで読み終えて構いません」と書いた）— 不採用。人間にも長さとして
  見える。畳んでも読まれることが canary で分かったので、畳む方を取る
- **冒頭 3 行 + 決まった節（入れ方・最初の 1 回・詰まったら）の型で縛る** — 不採用。「三行」は著者のレトリックで、
  節の立て方は repo ごとに違う
- **長さを gate にする** — 不採用。閾値は較正されておらず、約 2.6 万字で切れた観測は Grok の初回取得 1 件だけ

## Consequences

### Positive

- 見える本文が短くなり、人間の読者は冒頭で何をするものかを掴み、使い始めの摩擦だけを読む
- 取得する LLM の経路には、今までと同じフロアが末尾から届く
- About の description の役割が、URL を取得しない経路の唯一の窓口として明確になる

### Negative

- 既存の README（contemplative-agent・jev-skill-router・jev-research-pipeline・harness-scope・hub など）は、
  書き直すまで F1・R3 に引っかかる。repo ごとの書き直しは別の作業にする
- 畳んだ中身は人間の目に触れにくく、誤りが残りやすい。著者通読では畳んだ節も開く
- 根拠の canary は各条件 1 回の標本で、畳んだ中身が答えの中でどれだけ効くか、索引クローラの挙動、github.com
  以外の描画面（PyPI の long_description など）での `<details>` の扱いは測っていない。GEO の相関は、見える本文を
  厚くする方向を指している
- 判定器の固定質問が 1 問増える（R16）。read-through-log の通読指摘数を、R16 の前後で比べるときは構成の違いを
  考える
- canary の数値は PROTOCOL.md を正本とし、`inspiration.md`、`SKILL.md` の as-of の行、この ADR は写しになる。
  再実行したら PROTOCOL.md を先に更新し、写しを追従させる
- 戻すときは commit を revert する。この ADR に沿って書き直した README は、畳んだフロアを見える本文に戻す作業が要る

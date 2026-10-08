<!-- origin: shimo4228 -->
# 訪問者役の読み — 「試したくなるか」を確かめる

readme-judge は「良い入口か」と「主張が repo と合うか」を判定する。この段は別の問い、
**初見の訪問者がこの README を読んで試したくなるか、ならないなら何が止めたか**を確かめる。
二つは別の失敗を拾う。訪問者役は「何者か・いくらかかるかが分からない」「出力の実物が無い」
「造語で止まる」を拾い、judge はコードとの食い違いを拾う。

## いつ回すか

Rewrite モードで、依頼が人に使ってもらう・試してもらうことを目的にしているとき（「試したいと
思える内容に」「awesome-list から人が来る」「入口として弱い」）。訪問者の人選を Step 1 の著者確認に
載せるので、Step 1 のある Rewrite モードで回す。

## 訪問者を 3 人選ぶ（repo ごとに）

人選は固定しない。repo の流入経路と読者から、試すかどうかの判断が**違う理由で**分かれる 3 人を
選ぶ。材料は README・GitHub の About と topics・リンク元（awesome-list、記事、PyPI、profile）・
依頼文。

- **主な利用者** — この repo が想定する使い手。その人の制約（予算、環境、手間の許容）を持たせる
- **主な流入経路から来た人** — その経路で実際に開く人。流し読みの時間予算を持たせる
  （awesome-list なら 60 秒程度）
- **代わりの手段を知る懐疑派** — この repo が置き換えるもの（既存ツール、自作の agent、手作業）を
  使ってきて、証拠と費用を確かめる人

各人に 1〜2 文で、役割・すでに知っていて使っているもの・比べる相手・時間か予算の制約を書く。
実在しうる訪問者にする（藁人形にしない）。3 人は Step 1 の著者確認に載せ、以後のラウンドで
同じ 3 人を使う（人を替えるとラウンド間で比べられない）。

## 読ませ方

- 読ませるのは、流入経路が着地する言語版（ふつうは README.md）。ほかの言語版は readme-judge が
  言語間の対応として見る
- README を scratch にコピーしてラウンドごとに凍結する（`r0/`、`r1/` …）。コピーでは `<details>` の
  中身を消して `<summary>` だけを残す — 実際の訪問者は畳んだ節を開かずに判断する
- fresh context の別 agent を 3 体、並列に起動する（general-purpose、`model: sonnet`。書き手と別の
  モデルにし、回数を回せる重さにする）。渡すのはコピーの path だけで、執筆の文脈は渡さない
- 既存の README があれば、改稿前の版を `r0` として先に読ませる。これが比べる起点になる

prompt（形式を固定するための例。`{CHANNEL}`・`{PERSONA}`・`{README}` を埋める）:

```
You are a visitor who just clicked a link in {CHANNEL}. Persona: {PERSONA}

Read ONLY this file, as if it were the rendered GitHub page: {README}
Images appear to you as their alt text. Do not open any other file, link or tool. Read it the way
your persona really would: skim, and stop where you would stop.

Answer in JSON only, no prose around it:
{
  "stopped_reading_at": "<heading or sentence where you stopped or started skimming>",
  "what_it_is": "<one sentence, your own words>",
  "why_care": "<one sentence: what made it different from what you already know, if anything>",
  "would_try": "yes | maybe | no",
  "what_pulled_you_in": ["<up to 3 specific lines or facts>"],
  "what_pushed_you_away": ["<up to 4 specific lines, terms, costs, or missing facts>"],
  "unclear_terms": ["<words you did not understand at first read>"],
  "one_change": "<the single change that would most make you try it>"
}
```

## 結果の使い方

- 直す材料は理由の側にある。`what_pushed_you_away`・`unclear_terms`・`stopped_reading_at` と、
  3 人に共通する理由を見る。`would_try` は 1 人 1 回の答えなので、向きを見る手がかりにとどめる
- 理由を二つに分ける。**文面で直るもの**（説明の欠け、順序、造語、出力の実物が無い）は直す。
  **事実の不足**（無料で試せない、精度が測られていない、依存先が 1 社）は README で埋めず、
  著者に渡す。事実の不足を言い回しで薄めると two-sided rule を破る
- 訪問者役が求める主張でも、repo に証拠が無いもの（「品質は同等」など）は書かない
- ラウンドごとに、3 人の `would_try` と主な理由を 1 表にまとめ、最後に著者へ渡す

## 止めどき

次のどれかで止める。

- 文面で直る理由が新しく消えず、どの訪問者の `would_try` も動かないラウンドが出た
- 3 人に共通して残る理由が、どれも事実の不足になった
- 改稿 3 ラウンド

止めたら Workflow Step 3（他言語版）へ進む。readme-judge の Fix で本文が大きく動いたときだけ、
凍結版をもう 1 回読ませて、新しい離脱理由が出ていないかを確かめる。受け入れを決めるのは著者の通読。

<!-- origin: shimo4228 -->
# 概要図（README 冒頭の ELI5 図）

README の第一画面に置く 1 枚の図。役割は**人間の注意**（開いて数秒で「何が起きる仕組みか」を
掴ませる）で、情報は本文が持つ。ELI5 の型 — 大きな絵、少ない言葉 — で描く。本文の図
（Mermaid・構成図）の規約は `visual.md`、この図はその「図にすべきか絞る」の例外として既定で置く。

## いつ置くか

- **既定で 1 枚置く。** repo に動く仕組み（流れ・判定・ループ）があるとき
- 置かない: 動く仕組みを持たない repo（記事集・データ集・リンク集）。代わりに hero（`visual.md`）
- 詳しい構成図（コンポーネント・データフロー）はこの図にしない。skill: `archify` で作って docs/ に
  置き、README からリンクする
- plugin の `eli5` skill は HTML artifact の説明図を作る（記事の図など）。README に commit する
  この図は SVG なので、ELI5 の型だけを借りてこの手順で描く

## 形 — 2 つの型から選ぶ

| 型 | 使うとき | 構成 |
|---|---|---|
| 線形 | 1 回の入力が出力になる（hook・CLI・変換） | 横に 3 枠 + 矢印、下に「変わらない部分」の帯（例: 最後に選ぶのは Claude） |
| ループ | 出力が次の入力に戻る（定期実行・学習・印） | 2×2 の 4 枠を時計回り + 戻りの点線矢印、中心に「全部がこれのために動く」ハブ |

雛形: `../templates/overview-linear.svg` / `../templates/overview-loop.svg`（illustrative — 実在の
README の図。文言を差し替えて使う）。

**1 枠の中身**: 絵文字 1 つ（大きく）+ 見出し（英 2〜3 語 / 和 8 字以内）+ 補足 1〜2 行。
選択肢（モード）を 1 枠に並べるときは区切りに `or` / `または` を置く — 無いと順番に起きる
2 段に読まれる。数値は 1 つまで（例のチップ `adr-writer · 93%`）。

## 中身の規則

- **ラベルは本文の語と揃える。** 図が和語（採る / 保留 / 捨てる）で本文が英語の用語（Keep /
  Review / Drop）なら、本文の初出に括弧で対応を書く。図の「ノート」と本文の「note」のような
  揺れも同じ
- **図に出る固有名（モデル名・製品名）は、tagline か図の直後の段落で説明する。** 図は tagline の
  すぐ下にあるので、説明が本文の 3 段落目だと訪問者は名前だけを見る
- **ラベルをコードと照合する。** 図は短いぶん言い切るので、事実のずれが目立つ（実例: 「問いごとに
  短いノート」→ 実装はライン 1 本に 1 ノートで、問いごとに節）
- **テキスト等価**（`visual.md` の hard rule）: 直後の identity 段落が各枠を文で言い、`alt` も全枠を
  言う。図が落ちても README が読める

## 実装

- `assets/overview.svg` と `assets/overview.ja.svg` を commit する（言語ごとに 1 枚。alt も言語別）
- 置き場所は badge の直後、identity 段落の前:

  ```html
  <p align="center">
    <img src="assets/overview.svg" width="760" alt="（全枠を 1〜2 文で）">
  </p>
  ```

- SVG の約束（雛形が満たしている）:
  - `viewBox` 幅 960。GitHub のスマホ表示で約 0.4 倍に縮むので、見出し 25px 以上・補足 17px 以上
  - 背景つきの角丸 rect を最背面に置く（GitHub の light / dark どちらでも読める）
  - `role="img"`、言語別の `<title>` / `<desc>`
  - font-family: 本文 `-apple-system, BlinkMacSystemFont, "Segoe UI", …`、和文版は
    `"Hiragino Sans", "Noto Sans JP", "Yu Gothic", Meiryo` を足す、絵文字は
    `"Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji"`
  - 枠の色: 青 `#E7F0FA`/`#6A9BC3`、紫 `#EBE4FA`/`#8B72D6`、緑 `#E2F5E9`/`#57A874`、
    黄 `#FFF3D6`/`#D9A33C`、灰 `#F3F4F6`/`#6E7781`、文字 `#24292F`、背景 `#FFFBF2`
  - README からは `<img>` で参照する（README に直接書いた `<svg>` は GitHub が sanitize する）

## 描画確認

SVG を PNG に描いて目で見る。和文ラベルのはみ出しは描かないと分からない:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --hide-scrollbars --window-size=960,<viewBox の高さ> --screenshot=<out>.png file://<abs>/assets/overview.ja.svg
```

見る点: はみ出し・重なり、`or` の区切り、絵文字が出ているか、枠の読み順。

## 判定への接続

readme-judge は checklist R15 で図と本文の対応を読む（図が開けるので path を渡す）。図のラベルと
コードの照合は判定器でなく執筆側（Workflow Step 2）が持つ。readme-judge の指摘で本文の語を変えたら、
図のラベルも同じ commit で直す — 図と本文の語のずれは判定器が R15 と J4 で最初に拾う。

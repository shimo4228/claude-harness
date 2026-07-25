<!-- origin: shimo4228 -->
# Human Gate — 人間は何を判断するか

ゲートには 2 軸ある。**いつ止まるか**は可逆性で決まる（[`coding-style.md`](coding-style.md) の
Reversibility Gate）。**止まったとき人間が何を判断するか**がこのファイル。

## artifact は機械、intent は人間

成果物の正しさ（build / types / lint / tests / secret scan）は決定論ゲートと review agent が持つ。
**人間を artifact 検査に戻さない** — [`coding-style.md`](coding-style.md) 判定 3 問の
「品質を機械検証できるか」が Yes なら人間を呼ばない。手厚いレビュー体制は人間を降ろすための投資であり、
人間が読むためのお膳立てではない。

**review agent は検査者であって承認者ではない。** LLM judge は generator–verifier gap を持つ
（提案者と検査者が同一システムなら、検査は提案者の盲点を継承する）。承認は
「決定論ゲートの PASS」＋「人間の intent 判断」で構成し、**LLM 単独の承認経路を作らない**。

## ゲートで提示するもの（対象で分岐）

- **behavior-shaping artifact**（rules / skills / identity / 憲法 / 公開ドキュメント）と
  **control plane**（hooks / `permissions` 設定 / `--allowedTools` 等の権限定義 / scheduled task 定義）
  → **本文を提示する**。前者はテキストが意図そのもの、後者は**ゲートそのものを動かす**ので、
  要約に畳むと「検査を緩める変更」が善意の一文に隠れる
- **実装コード・生成物** → **意図の要約**（何を志向し、結果として何がどう変わるか）。
  diff 本文と機械チェックの PASS 一覧は提示しない

**FAIL は例外** — 決定論ゲートが FAIL したときは**検出行そのものを提示する**。偽陽性判定
（[`security.md`](security.md) の `*_BYPASS`）は人間にしか下せず、証拠なしに bypass を決めさせない。
提示を省くのは PASS のときだけ。

要約は [`planning.md`](planning.md) 介入点 1 で承認した plan と**照合**する。自由記述として読ませない —
照合先を人間由来の referent に固定しないと、人間は提案者自身の自己申告を検証することになる
（gap が artifact 層から語りの層へ移るだけ）。

この rule は **harness alignment**（AKC ADR-0017 / DOI 10.5281/zenodo.20578272）の human-gated 条項と
**line of approval**（AKC glossary）の運用版であり、定義本文は複製しない。

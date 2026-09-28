---
state: in_progress 2026-09-28
review-when: 対象の計器の設計が変わったとき
---
## Summary

すぐ出せる 5 件（skill-creator §5 の native ablation 単発実測、ADR-0032 の測定不成立と生レポート、search-first の shadow baseline、ADR-0074 の判定ログ schema、effort 試行の対照崩れ）を、設計・環境・生の読み値（または ID と hash）・測らなかったもの・既知の故障・有効性の状態つきで公開する。

## Motivation

Eval の公開の型は MyAI_Lab 側に既にある（contemplative-agent-data の DATACARD 等）。harness の計器は `.notes/` や gitignore の下にあり、公開同期の対象外。

## Drawbacks

生値に第三者の本文やベンダー出力が混ざる場合は ID・数値・hash に留める。カードが計器から drift しうる。

## Unresolved questions

形式（自前 markdown / Every Eval Ever / Evaluation Cards / Croissant-RAI）/ 置き場所 / 計器の状態語彙を台帳の語彙と分けるか。

## Status

**2026-09-27 draft**

**2026-09-28 in_progress** — 著者が採用。Unresolved の決着: 置き場所は `docs/evals/`、公開は claude-harness の同期対象に `docs/evals` を足して harness-sync で出す / 形式は自前 markdown で、欄の名前だけを `claude plugin eval` の `aggregate-result.json`（schemaVersion 1）・Every Eval Ever 0.3.0・Inspect AI EvalLog から借りる（search-first 2026-09-28: どの形式も「有効性の状態」「測らなかったもの」「既知の故障」を正式な欄に持たず、Every Eval Ever は主語が model で arm・delta が無く、Evaluation Cards は集計モニタ、Croissant-RAI は dataset 単位）/ 状態語は台帳と分けて `再現済み` / `単発` / `不成立`。
**2026-09-28 plan** — [docs/plans/rfc-0030-s1-eval-card-ablation](../docs/plans/rfc-0030-s1-eval-card-ablation.md)（S1: 形式定義と 1 枚目）
**2026-09-28 S1 merged** — `42665c6`（`docs/evals/README.md` と s1 カード、状態 `単発`）。検収: diff は `docs/evals/` の 2 ファイルのみ、判断役の verify exit 0、数値は読みメモと一致。逸脱 3 件は名指しあり（rebase・対応表の見出し化・`retrieved_timestamp` を ISO 8601 に）。diff 外 findings 1 件（skill-creator §5 の偽陰性条件の書き方）は同日に直した。build: effort low（packet）→ 未確認（Report）/ bounce なし / none。

## Next action

claude-harness の同期対象に `docs/evals` を足す（公開 repo — 著者の GO）。残り 4 枚（ADR-0032 の測定不成立、search-first shadow baseline、ADR-0074 の判定ログ schema、effort 試行の対照崩れ）を同じ形式で。

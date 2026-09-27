---
state: draft 2026-09-27
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

## Next action

5 件のうち最も完結している s1 の ablation 記録から 1 枚作り、形式を決める。

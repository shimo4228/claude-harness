---
name: repair-discipline
description: バグ修正・残課題・schema/storage 変更に着手するときの規律。Use when the user says 「このバグ直して」「残課題をやって」「この schema を変えたい」, when picking up a stale task file, or when a fix touches storage formats or shared gates. NOT for — chain の種別とレビュー条件の判定（implementation-chain）、TDD の手順（tdd）、Python 固有の mock / fixture の罠（python-patterns）、台帳全体の棚卸し（task-stocktake — 本 skill は 1 件着手時の照合のみ）。
user-invocable: true
origin: shimo4228
replaces: contemplative-agent の feedback memory 5 本（verify-before-work / substrate-migration-sweep / verify-bypass-hides-all-gates / io-bound-process-diagnosis / no-background-retry-loop、2026-08-25 昇格）
---

# Repair Discipline

直す前に、いま何が真かを一次証拠で確定する。5 原則、いずれも実地の失敗から
（出所は CA repo での実測。原則自体はどの repo でも同じ形で壊れる）。

## 1. 着手前に既済照合

残課題ファイル・古い TODO・引き継ぎメモは書かれた時点の観測。着手前に **git log と
実コードで「もう直っていないか」を照合**する。台帳だけが古いまま残る drift は
「作業 → 資料 → 台帳」の最後の 1 ホップで起きる — 見つける経路は日付でなく
正本資料との突き合わせ。
（出所: 2 ヶ月前に決着済みのタスク 2 件が store で open のまま残っていた 2026-08-16 の棚卸し）

## 2. schema / storage 変更は全消費者を同じ変更で棚卸す

データ形式・保存場所・フィールドを変えたら、**その形式を読む側を全部 grep して同じ
PR で追随させる**。書き手だけ直した変更は、読み手が静かに空を返す形で壊れる —
エラーでなく「何も無い」に見えるのが最悪の壊れ方。消費者は自コードとは限らない
（skill 本文・doc・別 script が名指しで読んでいることがある）。

## 3. bypass は単一ゲートでなく全ゲートを短絡すると知って使う

`VERIFY_BYPASS=1` 型の逃げ道は、既知の 1 件を通すためのつもりでも **hook が束ねる
全検査（format / lint / security）を一緒に飛ばす**。使う前に「この bypass が黙らせる
検査の全リスト」を言えるか確認し、言えないなら個別の除外手段を探す。

## 4. プロセスの CPU が低い ≠ stuck

I/O バウンドなプロセス（LLM 推論・ネットワーク待ち）は CPU がほぼ 0 でも正常に進行
している。**kill する前に一次ログと相手側の状態**（サーバの load 状況・進捗ログの
タイムスタンプ）を見る。「反応がない気がする」は証拠でない。

## 5. テストの再試行はフォアグラウンド 1 回

失敗したテストをバックグラウンドで連発しない。1 回フォアグラウンドで走らせ、出力を
読み切ってから次の仮説へ。連発は失敗ログを積むだけで情報を増やさず、リソース競合で
新しい偽の失敗を作る。

## 使い方

修理・変更の着手時に該当原則を 1 つ名指しして通す（「原則 1 — この課題、git log で
既済照合した？」）。機構を**足す**修理はこの skill の外 — implementation-chain の
機構ゲート（agent: architect）が正本。

## 失効条件

- substrate がこれらの照合を着手時に自発するようになったら退役（Scaffold Dissolution）
- 原則の出所となった実測が反証されたら該当原則を削る

---
name: measurement-discipline
description: 測定に基づく主張・閾値・ガード・実験結果を設計または評価するときの規律。Use when the user says 「この実験結果で判断していい？」「閾値を決めたい」「ガード/検査を足したい」「1 回通ったから大丈夫」, when a design places a numeric threshold or a suspicion flag, or when a claim rests on measured data. NOT for — 計器（read-only 分布・読み値）そのものの設計（CA repo の skill read-only-instruments が正本）、LLM 判定器の設計（llm-as-judge）、ループ構造の妥当性（loop-design-check）。
user-invocable: true
origin: shimo4228
replaces: contemplative-agent の feedback memory 5 本（one-run-not-evidence / gate-on-evidence-not-calendar / saturated-guard-is-worse-than-none / no-numeric-caps / relevance-distribution、2026-08-25 昇格）
---

# Measurement Discipline

測定の主張には、その測定が成立する条件を先に問う。5 原則、いずれも実地の失敗から
（出所は CA repo での実測。原則自体はどの repo でも同じ形で壊れる）。

## 1. 1 回の成功は証拠でない

smoke 1 回で「機能した」と言って commit しない。stochastic な系（LLM・外部 I/O・
タイミング依存）では 1 回は分布の 1 標本。**主張の前に「何回・どの条件で見れば
言えるか」を決める** — 決められないなら主張を「動くことがある」に弱める。
（出所: follow 修正で 1 run 観察を「直った」と報告しかけた 2026-06 の訂正）

## 2. ゲートは暦でなく観測量で

段階実装・部分導入の「次へ進む」条件を日付・期間にしない。**必要な観測数を事前に
見積もり、その観測が溜まったら進む**。暦ゲートは観測ゼロでも発火し、観測量ゲートは
データが無ければ止まる — 止まるのが正しい。
（出所: shadow 計器の enforcement 判断を「2 週間後」でなく判定数で切った経緯）

## 3. ガードの発火率 0% と 100% はどちらも設計ミス

疑わしさフィールド・警告・検査を置いたら、**実データで発火率を測る**。一度も発火
しないガードは読者に「検査済み・問題なし」と誤読させ（無いより悪い）、常時発火する
ガードは読み飛ばされる。較正できるデータが無いなら、ガードでなく生の読み値を出す。
（出所: 恒久 0 の `observed` フィールドを読者が集計して逆の結論を出した ADR-0082）

## 4. 数値キャップを品質フィルタにしない

`max_N` 型の上限は量の制御であって質の判定ではない。「上位 N 件」で切ると、N+1 位
以降の良品を黙って捨て、N 位以内の不良を黙って通す。品質を切りたいなら品質の軸で
判定器を立て、量を切りたいときだけキャップを使う — 混ぜた瞬間、どちらの保証も消える。

## 5. 通過分だけのスコアで分布を語らない

フィルタの下流に残ったデータは選択バイアス済み。「通過分の平均が高い」はフィルタの
機能証明にならない（棄却分を見ていない）。分布・較正・閾値の議論は**フィルタ前の
全量**か、少なくとも棄却側のサンプルを添えてから。

## 使い方

設計・レビューの場で該当原則を 1 つ名指しして問う（「これは原則 3 — このガードの
発火率をどのデータで較正した？」）。5 原則を毎回全部なぞらない。

## 失効条件

- substrate がこれらの問いを設計時に自発するようになったら退役（Scaffold Dissolution）
- 原則の出所となった実測が反証されたら該当原則を削る（原則は経験則であり公理ではない）

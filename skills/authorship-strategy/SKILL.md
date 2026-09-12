---
name: authorship-strategy
description: 著者戦略の具体案を評価するとき、または既存の判断枠組みの適用・説明を求められたときに使う。「この案を著者戦略の観点で評価して」「採用時の懸念を確認して」「この戦略を説明して」。NOT for — 自由な壁打ち、次のアイデア出し、日常のコーディング。
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
origin: shimo4228
user-invocable: true
---

# Authorship Strategy

作り手が、考えをどう使ってもらい、出典とともに伝えていくかを判断するための補助資料。
著者の現在の目的と具体案に合わせて使う。研究系 repo にいることだけでは適用しない。

## 使う場面

具体案の評価、採用・実施の検討、既存 framework の説明を求められたときに使う。
明示的にこの skill を呼んで探索を頼まれた場合も、依頼の目的を優先する。
発想の順番、案の分類や件数、会話の結論を skill で決めない。

## 判断の材料

現在の framework は authenticity、出典を伴う diffusion、idea と scaffold の区別、
具体的な tactics を扱う。これは過去の実践から得た判断であり、案をその枠に収める
こと自体を成功としない。既存の戦略と衝突するなら、どの前提が違うか、何が得られ、
何を失うかを説明する。戦略の見直しも選択肢になる。

- 枠組みの意味や従来の選択肢が必要なら [strategy reference](references/strategy-reference.md)。
- 具体的な行動の実施条件を確認するなら [action review](references/action-review.md) の関係する項目。

参照資料は必要な箇所を読む。根拠のある事実、現在の方針、未検証の見込みを区別する。
評価はその案の価値と懸念を説明する形で返し、全項目の合否表を定型出力にしない。

## Operating the strategy over time

実施状況や重複を確認する仕事には台帳を使う。案や問いの保存は記録を依頼されたときに行う。
実施済みの介入は、適用先の保守規約が宣言する台帳・公開記録の役割と更新順に従って記録する。

## 参照と適用範囲

本 skill の ADR 番号は [authorship-strategy の ADR](https://github.com/shimo4228/authorship-strategy/tree/main/docs/adr)
を指す。ハーネス自身の ADR は別の名前空間。各 project の事例と実施状況は各 project の資料が持つ。
他者の project では、その著者の目的と方針を優先する。

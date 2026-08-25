---
state: candidate 2026-08-25
review-when: tdd skill が退役した時、または substrate が fix 中の test 改変防止を native に持った時
---

## Summary

`fix` chain の実装中、再現テストを commit する前に test ファイル自体を編集する操作を
PreToolUse hook でブロック（または警告）する。

## Motivation

出所は AI-native SDLC playbook（2026-08-21）Stage 4 の「Block agent from editing test
files during fixes via hook」— GREEN 偽装（テストを弱めて通す）の決定論的ガード。
ただし本 harness では **GREEN 偽装の観測事例がまだ 0 件**。1 回は証拠でなく 0 回は
なお弱い（measurement-discipline）ので、**着手条件 = test 改変による GREEN 偽装を
1 回でも観測した時**。それまでは建てない（Build-or-not ①）。

## Guide-level explanation

fix chain 中（判定方法は要設計 — Unresolved）、`tests/` 配下への Edit/Write を hook が
検知し、「再現テストを先に commit したか」を問う advisory を出すか block する。

## Reference-level explanation

（着手時に設計。既存の PreToolUse hook 群 — episode-log guards / docs-prewrite — の
検知パターンを流用できる見込み）

## Drawbacks

- 正当な test 編集（テスト自体のバグ修正、fixture 更新）を巻き込む摩擦。発火率の較正が
  要る（measurement-discipline: ゲートは観測量）
- 「fix 中」という状態を hook が知る手段が無い — セッション状態の推定は誤発火源

## Rationale and alternatives

- 代替: tdd skill の手順記述だけで足りる可能性（現状はこれ。観測 0 件はこの代替が
  機能している証拠とも読める）
- 代替: ai-regression-testing 側で「fix 後に test の diff を人間が見る」チェック 1 行

## Prior art

- AI-native SDLC playbook Stage 4（上記）
- 本 harness の episode-log guards（Read/Grep/Bash の 3 経路 PreToolUse ブロックの前例）

## Unresolved questions

- 「fix 実装中」をどう判定するか（ブランチ名? 直近の chain 宣言? 判定不能なら advisory
  止まりにするか）
- block と advisory のどちらで始めるか（誤発火コスト次第）

## Future possibilities

- 発火ログが溜まれば、GREEN 偽装の発生率そのものの実測になる

## Status

candidate（≈ draft）— 観測待ちの提案（2026-08-25 起票）。建てない状態が既定。

## Next action

- 再開条件: test 改変による GREEN 偽装を 1 回でも観測する
- 照合先: fix chain の実装 diff（tests/ への編集がテストを弱めた事例）
- 成立時: ready（設計は Reference-level explanation の方針で）

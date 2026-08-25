---
state: candidate 2026-08-25
review-when: ADR-0049 が supersede された時、または gloss 運用で drift 再発が 3 ヶ月観測されなかった時（現状維持で決着）
---

## Summary

台帳の状態語彙 8 語（candidate / ready / in_progress / blocked / done / decided /
dropped / retired）を、標準語彙（draft / accepted / in progress / blocked /
implemented / resolved / rejected・withdrawn / obsoleted）へ**全域で**置き換えるかを
判断する。

## Motivation

非標準語彙はセッションごとに写像がずれる — 2026-08-25 に judge セッション自身が同日中に
dropped / retired / withdrawn の対応を 2 通りに書いた（実証）。標準語彙は substrate が
訓練で知っているため自己安定する。緩和策（各エントリ Status 節の標準語 gloss、
task-stocktake の対応表）は導入済みだが、根治は語彙自体の標準化。

## Guide-level explanation

frontmatter の `state:` 値と、それを読む全ての場所（skill / rule / 判定表）の語を
標準語に替える。読み書きの機構（claims.py の state 照合は文字列一致）は語に依存しない。

## Reference-level explanation

対象範囲（rfcs/ だけ替えるのは第二語彙 — ADR-0049 Alternatives で却下済み。やるなら全域）:
skill task-stocktake（語彙の正本）/ task-triage（verdict 表）/ rules/common/task-tracking.md /
claims.py の `ready` 既定値（ready → accepted、1 行）/ 移送済み全エントリ（harness 3・
CA 15・AKC 1）/ 単一表 repo 9 件の状態列 / CA の CLAUDE.md 台帳節。

## Drawbacks

- 横断 sweep のコスト。過去の ADR・commit message・memory は旧語のまま残り、断絶が生じる
- 語数が増える（dropped が rejected / withdrawn に分裂）— 終端の使い分け表の再設計が要る
- 2026-08-16 に 6→4+4 へ縮約した直後の再改編で、語彙の churn 自体が drift 源になりうる

## Rationale and alternatives

- 現状維持 + gloss（採用済みの緩和）: Status 節の自己記述で per-entry の解釈は固定される。
  これで十分なら本提案は不要 — それを測るのが下の Next action
- rfcs/ のみ標準語: 第二語彙。ADR-0049 で却下済み

## Prior art

- IETF の文書状態語彙（Proposed / Historic / Obsoleted）と「Status of This Memo」節
- issue-tracker 標準（open / in progress / blocked / done / wontfix）— blocked の出所
- Rust RFC lifecycle（merge-as-acceptance、postponed ラベル）

## Unresolved questions

- `decided`（build なしで決着）の標準対応語 — resolved で足りるか
- `blocked` は標準 RFC 語彙に無い（issue-tracker 語）— 混合は許容か

## Future possibilities

- 標準化するなら、`claims.py ready` の表示に gloss を出す必要が消える

## Status

candidate（≈ draft）— gloss 運用（2026-08-25 導入）の観測期間中。判断はその後
（著者指示: まず運用し、冗長・不足が見えたら規約を再検討する）。

## Next action

- 再開条件: gloss 運用下でも状態語の写像ずれが再発する（または 3 ヶ月無事故 → dropped で決着）
- 照合先: rfcs/ エントリの Status 節と実際の state 遷移記録の突き合わせ
- 成立時: ready（sweep の実装 packet を書く）

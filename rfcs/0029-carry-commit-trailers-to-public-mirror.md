---
state: blocked 2026-09-28
review-when: harness-sync の同期方式が変わったとき
---
## Summary

claude-harness への同期で、公開対象を触った source commit の trailer を同期 commit の本文に写す。

## Motivation

harness-sync は tree だけを渡し、commit 本文を落とす。予備測定（RFC-0027）で RFC-0021 の 4 環が「記述のみ」だったのは、根拠の commit 本文が private repo にしか無いため。

## Drawbacks

trailer に私的なパスや機微が混ざりうる（同期の secret scan と `$HOME` scan を通す）。ミラーの commit 本文が長くなる。

## Unresolved questions

写す範囲（全 trailer か Review / Context / Decision / Review-when / Plan だけか）/ 前回同期からの commit の列挙方法。

## Status

**2026-09-27 draft**

**2026-09-28 blocked** — 著者 OK。Next action が「RFC-0028 の試行結果を見てから」だったので、その条件を 3 行にした。

再開条件: RFC-0028 の試行（2026-09-28〜10-12）の読みで「続ける」と決まる
照合先:   `rfcs/0028-correction-commit-trailers.md` の state と Status
成立時:   accepted（claude-harness の同期 script に、公開対象を触った source commit の trailer を同期 commit の本文へ写す処理を足す）

## Next action

上の照合先を 10-12 以降の triage で確かめる。

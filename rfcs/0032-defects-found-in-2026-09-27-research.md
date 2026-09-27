---
state: draft 2026-09-27
review-when: 3 件がすべて直るか、直さないと決まったとき
---
## Summary

RFC-0027 の調査で見つけた、公開記録と一次記録の食い違い 3 件。

## Reference-level explanation

1. **review-when-watch が稼働していない。** launchd に plist が無く、`metrics/review-when-watch.jsonl` も無い（2026-09-27 確認）。一方 RFC-0025 の Status は毎日 1 run と書き、再開条件をこのジョブの 30 run に置いている。登録は人間の操作で、vault のノートを外部へ送る許容の判断を伴う（ADR-0080 Decision 1・9）
2. **1 周目の件数が公開物どうしで合わない。** ADR-0043 は「open 41 → 23、closed 16 / spawned 5」、`skills/task-triage/references/first-cycle-2026-08-17.md` は「harness 13 → 5、CA 28 → 17、起票 6、Closed: 27」
3. **contemplative-agent RFC-0040 の注記の順序。** 注記は「2026-09-22 に一次資料を再照合」だが、数値の公開 GO（zenn-content の commit 43c52be）は 09-21。RFC は MCA §16.7（改定の発効は通知から 60 日後）に触れていない（zenn 側の commit には承知のうえと記録）

## Status

**2026-09-27 draft** — 1 は著者の判断（登録するか・RFC-0025 の再開条件を変えるか）。2・3 は注記の追加で直る。

## Next action

1 は著者が決める。2・3 は日付つき注記を足す。

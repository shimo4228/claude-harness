---
state: resolved 2026-09-28
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

**2026-09-28** — item 1 解消: 著者が review-when-watch の plist を登録（`launchctl print gui/501/com.shimomoto.review-when-watch` で確認、毎日 06:10）。ADR-0080 Decision 9 の送信は許容で確定。RFC-0025 の再開条件の予定日を置き直した。残りは item 2・3。

**2026-09-28** — item 2 解消: 食い違いは数えた時点の違い（ADR-0043 は周回途中、first-cycle の記録は周回全体）。ADR-0043 の Consequences に注記を足した。残りは item 3（contemplative-agent の RFC-0040 — 直すなら CA 側の台帳で扱う）。

**2026-09-28 resolved** — item 3 解消: 起票せず、contemplative-agent の RFC-0040 の MCA 注記に、公開 GO（09-21）との順序と §16.7 の扱いを日付つき注記で補った（contemplative-agent `4b336d9`）。3 件とも片付いた。

## Next action

なし。

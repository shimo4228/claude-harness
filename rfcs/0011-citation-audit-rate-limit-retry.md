---
state: done 2026-08-27
---
## Summary

citation_audit.py の api_get が 429 に対し `time.sleep(5*(i+1))` で 5 回リトライしており、rate limit を policy signal として扱う規約（rules/common/debugging.md）と正面から矛盾する — リトライを撤去し停止・報告型に改める。

## Motivation

S1 build（RFC-0008）の diff 外 HIGH 指摘。producer: `skills/citation-sync/scripts/citation_audit.py:165` → sink: 同 :161 の urlopen。2026-07-16 に backoff で踏み抜いた結果アカウント無期限 block が発生した実害事例が規約の根拠。現在この経路は退役済み Wikidata probe のみで到達可能（dormant）だが、規約と逆の実装が正本 script に残ると次の流用で再発する。url_liveness.py（ADR-0052）が「429/503 連続で停止して報告、retry なし」の先行実装。

## Status

done — S4 で実装: 429 リトライ撤去、429/503 + HTTP200 throttle 封筒で停止・exit 2。timeout 追加。回帰 11 tests。merge 0ee9ce6。2026-08-27


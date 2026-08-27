---
state: done 2026-08-27
---
## Summary

公開ミラー claude-harness の llms.txt が publish されない 3 skill（en-to-ja-translation / ja-to-en-translation / substack-publishing）を指しリンク切れ — harness-sync の origin フィルタと llms.txt 生成の不整合を修正する。

## Motivation

S2 build（RFC-0006）の diff 外 HIGH 指摘。producer: `~/MyAI_Lab/claude-harness/llms.txt` → sink: 同 repo に存在しない `skills/en-to-ja-translation/SKILL.md` ほか 2 path。llms.txt は AI 向け導線の正本で、リンク切れは LLM 読者に対する導線故障。修正面は harness-sync 側（収集フィルタと llms.txt 生成の整合）にあり、ミラー側の手修正は次回 sync で上書きされるため不可。

## Status

done — 前提訂正あり: harness 側に llms.txt 生成ロジックは無い（生成はミラーの sync-from-local.sh の対象外 root file）。S4 は harness-sync SKILL.md に Step 4b（apply 後の context_evidence --gate、blocking）を配線。現行 3 リンクは次回 /harness-sync で解消。恒久 enforcement の設計観測は commit 0ee9ce6 body 参照。2026-08-27


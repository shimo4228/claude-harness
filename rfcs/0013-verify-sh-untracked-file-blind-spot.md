---
state: done 2026-08-27
---
## Summary

.claude/verify.sh の owned_files が `git ls-files` で対象を選ぶため、未 commit の新規ファイルが full run でも lint されない盲点を塞ぐ（untracked も対象に含める）。

## Motivation

S2 build（RFC-0006）で実際に発火した事象: 新規 sub-project が verify full run を素通りし、初回 commit 後に判断役の再実行で初めて ruff 違反が検出された（bounce 1 回分のコスト）。producer: `.claude/verify.sh:141` → sink: task/s2-context-sync の初回 commit で exit 1 になった事象。`git ls-files --others --exclude-standard` の併用が素直な修正。

## Status

done — S4 で実装: full mode の lint 対象に untracked を追加（実行 sink は tracked のみに維持 — untracked が無人実行面に届く経路を security review が HIGH 指摘）。verify.sh の hash 承認は人間待ち。merge 0ee9ce6。2026-08-27


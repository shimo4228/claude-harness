---
state: done 2026-08-27
---
## Summary

ADR 本文の数値主張と同一文書内の表・列挙の整合を adr_lint.py が evidence として列挙する hybrid 検査を追加する — adr-reviewer の是正ループ最大要因（数値目視突合）を script に降ろす。

## Motivation

2026-08-27 の build 3 本すべてで、ADR に書いた実測数値（分類件数・repo 数・検査対象数）が最終コードとずれ、adr-reviewer が MAJOR ISSUES を返して再計測・是正するループが発生した（S1 はこれで打ち切り超過。例: 本文「hybrid 9」vs 分類表の hybrid 行 11）。ADR-0051 は機械チェックを adr_lint に抽出したが、数値整合は semantic 側に残っており、それが残余コストの最大項だった。同一文書内の「本文の数値 vs 表の行数・列挙の個数」は script が数えて並置でき、乖離が drift か意図的 as-of スナップショットかの判定だけを adr-reviewer に残せる（enumerate/decide 分離）。文書外の再計測（evidence script の再実行）は本 RFC の範囲外。

## Status

done — codex（gpt-5.6-sol、herdr-delegate、隔離 CODEX_HOME）で実装、判断役検収後 main へ merge（851c12e）。ox-alpha は API 拒否（`x-preview-f-free` not supported）で断念。54 ADR 実測でリストのペアリングを明示予告に限定（偽ペアリング 15 → 0）。2026-08-27

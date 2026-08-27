---
state: done 2026-08-27
---
## Summary

skill-stocktake の残余機械項目 — usage 集計の 4 補正規則の script 化と、参照 URL の live check（RFC-0008 部品の消費）— を抽出し、Phase の該当部分を薄化する。

## Motivation

skill-stocktake は Phase 0 を既に「deterministic, code-owned」として分離済み（review-to-lint の先行成功例）だが、2 つが残っている。(1) usage 集計の 4 補正規則（sandbox 行除去・project path 除外・event type 分割・14 日未満の span 表示、SKILL.md L80-99）が散文で書かれ、毎回 LLM が jq を再実装している — 集計は script が数値だけ返すべき典型。(2) Currency 検査の URL live check（L126）は script が無く LLM batch agent に投げている。

## Reference-level explanation

- 手順は skill: `review-to-lint`。usage 集計は `skills/skill-stocktake/scripts/` に uv sub-project、evidence モード・JSON・exit 0
- URL live check は RFC-0008 の共通部品を呼ぶ（自前実装しない）
- search-first: パス・agent・sibling skill の実在は `skill-health/scripts/scan_refs.py` が既にカバー — 二度書かない
- 免除境界: 補正規則の実測は直近の stocktake セッションログ（実データ）に当てて、現行の手動 jq 結果と一致することを確認してから固定する
- 薄化: L80-99 の散文手順を Step 0 配線（script 実行 → 数値転記）に置換

## Status

done — S1 build セッションで `skills/skill-stocktake/scripts/usage_stats.py` として実装（実ログ 3060 行で手動 jq と一致を確認）、SKILL.md を Step 0 配線に薄化、main へ merge（239f066、ADR-0052）。2026-08-27

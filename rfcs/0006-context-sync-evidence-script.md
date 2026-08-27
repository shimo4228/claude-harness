---
state: done 2026-08-27
---
## Summary

context-sync のチェックリスト（SKILL.md L249-276、20 項目）から deterministic 約 15 項目を evidence script に抽出し、skill を Step 0 配線で薄化する（review-to-lint 適用第 1 号）。

## Motivation

context-sync は起動のたびに LLM が 20 項目を目視検査している。うち 15 項目（ツリー一致・数値主張・CLI `--help`・package metadata・90 日 mtime・ADR index drift・参照 path 実在・TODO 残存・URL 200・JSON validate・llms.txt リンク解決・freshness header 日付比較ほか）は決定論で、実行コマンドの多くが SKILL.md 本文（L240-246, L267, L269-270）に既に書かれている — 抽出コストがこのライブラリで最小。

## Reference-level explanation

手順は skill: `review-to-lint` に従う。要点:

- Step 1 棚卸し: 2026-08-26 sweep の 3 分類（deterministic 15 / hybrid 2: Review-when 発火判定・H2 60% 重複）を再確認から始める。迷う項目は semantic に倒す
- Step 2 search-first: ADR index 検査は `skills/adr-writer/scripts/adr_lint.py` の `parse_index_numbers` / `analyze_naming` を呼ぶ（再実装しない — drift 回避）。URL 200 検査は RFC-0008 の共通部品を使う（未完なら自前実装せず該当項目を保留）
- Step 3: `skills/context-sync/scripts/` に uv sub-project（pyproject + tests）。既定 evidence モード・JSON 出力・exit 0、`--gate` は任意。**免除境界は既存 repo corpus（harness + 主要 repo 数件）への実測から先に決める** — 初日に赤くなる lint は設計ミス
- Step 4 薄化: SKILL.md のチェックリストから機械項目を削除し Step 0 配線（script 実行 → JSON 転記 → 目視で数え直さない）
- Step 6: ADR に境界線・免除境界実測値・search-first 照合結果を記録

## Status

done — S2 build セッションで実装、判断役検収（bounce 1 回: verify 盲点由来の ruff 失敗 → 修正）後 main へ merge（67b87fc、ADR-0053）。前提の「15 deterministic」は棚卸しで 4 deterministic / 11 hybrid に訂正された。2026-08-27

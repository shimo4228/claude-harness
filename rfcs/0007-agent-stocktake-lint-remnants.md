---
state: done 2026-08-27
---
## Summary

agent-stocktake の機械チェックのうち harness_lint.py 未カバー分（name=filename stem・tools 実在・description 近似重複・suppression 文言の regex 列挙）を script 化し、skill を薄化する。

## Motivation

agent-stocktake Phase 1（SKILL.md L57-66）は自ら「機械チェック」と呼ぶ 5 項目を LLM に実行させている。frontmatter パース系は `scripts/hooks/harness_lint.py` の `lint_agents` が既にカバーするが、次は未カバー: `name` = filename stem 照合、`tools:` の各 tool が現 harness に実在するか、description の正規化 + 近似重複、Phase 2 Stage 1（L94-104）の suppression instructions（"≥N% confident" / severity floor / "be conservative"）と ALWAYS/NEVER ペアの regex 候補列挙。最後の 2 つは「script が行番号つき候補を列挙し、LLM は判定文だけ書く」hybrid の教科書例。

## Reference-level explanation

- 手順は skill: `review-to-lint`。置き場は `skills/agent-stocktake/scripts/`（uv sub-project + tests）、evidence モード既定・exit 0
- search-first: `harness_lint.py` の `lint_agents` と重複する項目は結果を読むだけにする（再実装しない）。`skill-health/scripts/scan_refs.py` は skills root 限定で agents 本文は非対象 — 参照 path 解決（L62）はここで実装するか scan_refs 拡張かを照合してから決める
- suppression regex の検出パターンには実測根拠（どの agent の何行か）をコメントで残す
- 薄化: Phase 1 の機械 5 項目を Step 0 配線に置換

## Status

done — S3 build セッションで `skills/agent-stocktake/scripts/agent_evidence.py` として実装（25 agent × 300 ペアの実測で免除境界を設定）、main へ merge（dc0c806、ADR-0054）。name=stem 検査の gate 移設は RFC-0014 として分離。2026-08-27

---
state: done 2026-08-27
---
## Summary

learn-eval の grounding checklist のうち重複照合 2 項目（既存 skill との content overlap・MEMORY.md との重複）を、script が overlap 候補を機械列挙する形に降ろす。

## Motivation

learn-eval の grounding checklist（SKILL.md L79-83）のうち 2 項目は「`~/.claude/skills/` を keyword grep したか」「MEMORY.md と重複しないか」という**実施したかの自己申告**になっている。script が正規化 keyword 抽出 + 既存 skill description / MEMORY.md index との突合で候補を行番号つきに列挙すれば、自己申告の質問そのものが消え、LLM は「この候補は本当に重複か」の判定だけを持つ（enumerate/decide 分離）。

## Reference-level explanation

- 手順は skill: `review-to-lint`。置き場は `skills/learn-eval/scripts/`（uv sub-project + tests）、evidence モード・JSON・exit 0
- search-first: skill-stocktake Phase 3 の overlap probe と手法が同型 — 共通化余地を照合してから書く（共通化するならどちらの skill 配下を正本にするかを ADR に残す）
- 判定（Save / Improve / Absorb / Drop）は従来どおり LLM — script は候補列挙のみ
- 薄化: L79-80 を Step 0 配線に置換、L81-83（semantic）は残す

## Status

done — S3 build セッションで `skills/learn-eval/scripts/overlap_candidates.py` として実装（skill-stocktake Phase 3 との共通化は N×N 対 1×N の形状差で却下、ADR-0054 Decision #8）、main へ merge（dc0c806）。2026-08-27

---
state: done 2026-08-27
---
## Summary

agent の name=filename stem 検査を evidence script（agent_evidence.py）から harness_lint.py の lint_agents へ gate として移す — 判定の余地が無い不変条件は evidence でなく gate が正しい置き場。

## Motivation

S3 build（RFC-0007）の diff 外 HIGH 指摘（architect と adr-reviewer が独立に指摘）。producer: `scripts/hooks/harness_lint.py:246`（lint_skills が skill に対し同じ検査を既に gate として実施）→ sink: `skills/agent-stocktake/scripts/agent_evidence.py` の name_matches_stem。S3 packet が harness_lint.py 本体の変更を禁じたため未実施だった。約 6 行。evidence 側の重複検査は移設後に削るか「gate の結果を読む」ポインタへ。

## Status

done — S4 で実装: name=stem を lint_agents の gate へ移設（lint_skills と check_name_matches を共有）、agent_evidence.py 側は削除。非 str name の素通り穴も両側で閉鎖。merge 0ee9ce6。2026-08-27


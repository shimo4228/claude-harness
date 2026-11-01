kind: internal
# harness-stocktake 品質向上ループ — P16 / P11 / P10

as-of: 2026-11-01。plan [harness-stocktake-quality-before-plugin](../harness-stocktake-quality-before-plugin.md) の後、
固定サンプル 3 本（P16 / P11 / P10、[2026-11-01-rerun.md](2026-11-01-rerun.md) の id）で 1 周ずつ
「回す → 持ち主として report.md を読む → 一番効く欠点を 1〜2 個直す」を回した記録。最大 4 周。数字は
非 Keep 行（skills 行）・report 秒・`total_cost_usd`。

## 周ごと

- **1 周目（再走なし、rerun の run を読んだ）** 確かめた細部 10 件（P10 4・P11 4・P16 2）は全部 clone と一致。
  欠点: (1) report.md が各非 Keep 項目を `## Sources` の行と表で二回載せる（P16 450 行のうち Sources が約 250 行）、
  (2) 同じ事実を二つの source が別々の行で出す（P11 skills-11-08 と skills-probe-02 が同じ「4개 vs 5 repo」、
  P16 docs-05 と assets-15 が同じ Readme.md）。直したこと: `render_report.py` の `_demote` が section の item 行を
  落とす（再描画で P16 450→349 行、P11 428→371、P10 119→110）、SKILL.md Phase 2 に同じ事実の 2 項目を `fold` で
  1 行にする項目を足した。数字: P16 96（34）・892 秒・$31.78+$2.10 / P11 44（31）・672 秒・$29.58 /
  P10 9（1）・508 秒・$6.50

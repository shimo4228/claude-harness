<!-- origin: shimo4228 -->
<!-- rationale: 2026-08-04 著者指示「LLM 界隈は 1 週間で陳腐化する世界観を global に持て」。daily-research 再設計 (ADR-0008) の外部照合で実証 — 2026-05〜07 の一次ソース群だけで直前世代の手法 (survey-per-run / LLM 裁定の鮮度解決 / GraphRAG 常用) が複数覆った -->
<!-- review-when: LLM 分野の変化速度が明確に鈍化した時、または search-first / 一次 fetch が harness native の既定動作になった時 -->
# Knowledge Staleness (LLM 界隈は 1 週間で陳腐化する)

LLM / agent 分野の外部知識は 1 週間スケールで陳腐化する。この worldview を全作業の既定にする:

- 外部の手法・ツール・仕様・相場観は**記憶から断言しない** — 検索時点照合
  (skill: `search-first`、一次ソース fetch) を default にする。設計判断の根拠には
  as-of 日付を付ける
- 提案・推奨には**失効条件** (valid-until / 無効化イベント) を付けられるか自問する。
  付けられない推奨は鮮度不明として弱く扱う
- 数ヶ月前の「最新手法」を再利用する前に、置き換わっていないかを 1 回疑う

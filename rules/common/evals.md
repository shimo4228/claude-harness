<!-- origin: shimo4228 -->
<!-- rationale: eval の依頼で /claude-api build-eval が呼ばれていなかった（2026-10-06 の走査で eval らしい依頼 36 件中 3 件。claude-api の発火面は API コード）。eval 系資産 6 つの入口を 1 か所に置く。調査は docs/plans/research/2026-10-06-eval-search.md -->
<!-- review-when: claude-api skill の description が eval / hillclimb で発火するようになった時。build-eval の runner が claude -p を native に扱うようになった時。同じ走査で呼び出し率が上がらなかった時 -->
# Eval Wiring

| 問い | 行き先 |
|---|---|
| eval set を作る・eval しながら改善する | `/claude-api build-eval` → `/claude-api hillclimb`（自作 runner より先） |
| skill に効果があるか（有無だけ） | skill: `skill-creator` §5 の `claude plugin eval` |
| 文章の好み・読みやすさ | skill: `author-calibrated-eval`（judge の点数で登らない） |
| judge prompt の形 | skill: `llm-as-judge` |
| n・閾値・ノイズ | skill: `measurement-discipline` |
| rule・skill が守られているか | skill: `skill-comply` |

- なじみのない領域、または judge の妥当性が怪しいタスク（安全・翻訳・好み）では、build-eval の
  sign-off 2 より前に skill: `search-first` を回す（hillclimb に入ると採点方式を変えられない）。角度は
  「その分野の既存 metric・benchmark」「judge と人間の一致」「知られている失敗例」
- 対象が harness の skill・agent なら、runner と judge は `claude -p`（サブスク）で呼ぶ。公式 runner は
  API client 前提なので `runCase` をそこで差し替える
- test 側が数件しかない eval では hillclimb せず回帰 gate に留める（holdout 4–8 件は noise —
  PROCTOR arXiv 2609.02246、2026-09）

---
state: accepted 2026-08-26
review-when: review-to-lint skill 自体が改廃されたら。候補の正本 skill が大幅改修されたら該当行の sweep 実測は失効
---
## Summary

review-to-lint（ADR-0051）の水平展開候補 12 件の台帳。優先順は機械化余地でなく需要の発火条件で決め、確定 5 件（RFC-0006〜0010）は Opus 実装セッションへ委譲、残りは発火条件つきで保留する。

## Motivation

skill 新設時の適用候補リスト（SKILL.md 末尾、citation-formatter 起点の 4 件）は sweep 前の推定だった。2026-08-26 の grill-me セッションで agents/ 25 本 + skills/ 67 本を Explore 2 体で走査した結果、候補は 12 件あり、「機械化余地の大きい順」は誤った優先軸だと判明した（機械化率最大の citation-formatter は直近需要が無い）。リストを SKILL.md に持つと sweep のたびに skill 本文が肥大するため、台帳は本 RFC に移し SKILL.md はポインタだけ持つ（著者指示 2026-08-26）。

## Reference-level explanation

駆動原理: **需要駆動** — 「明確な需要 × 安定した正本」の交差だけ実施。作り置きは形骸化リスク（ADR-0051 Negative「skill を経由しない編集に効かない」がそのまま増える）。

### 候補台帳

| # | 候補 | 状態 | 発火条件 |
|---|---|---|---|
| 1 | context-sync — チェックリスト 20 項目中 15 が deterministic、実行コマンド既載で抽出コスト最小 | **RFC-0006** | 確定 |
| 2 | paper 系の束 — citation-formatter ほぼ丸ごと（約 16 項目中 14）+ paper-ecosystem / paper-writing の deposit gate（orphan 双方向 mapping・脚注 1:1・style 混在・DOI/arXiv 形式）+ vocabulary-consistency-checker の term inventory 層 + paper-reviewer 構造項目 | 保留 | 次の paper 作業開始時。WebFetch 実在確認は `--online` flag に隔離し evidence モードは offline 完結（方針のみ先に固定） |
| 3 | writing-ecosystem 系の束 — editor / essay-reviewer / prose-clarity-reviewer / clarity-reviewer + quality-gate + collect-context + x-draft。readme_evidence.py の骨格（term_candidates / insider_refs / prose_signals）流用可 | 保留 | writing-ecosystem の設計安定後（著者判断 2026-08-26: 流動中の正本への接木は drift 負債） |
| 4 | agent-stocktake — harness_lint 未カバー分: name=stem・tools 実在・description 近似重複・suppression 文言の regex 列挙（hybrid の教科書例） | **RFC-0007** | 確定 |
| 5 | config-gc — 8 チャンネルを 1 scan script に束ねる（orphan hook / permission 重複 / cache は script 済み） | 保留 | 次の月次 GC 前 |
| 6 | URL liveness 共通部品 — skill-stocktake / context-sync / paper-ecosystem の 3 箇所が要求、既存 script のどれも持たない | **RFC-0008** | 確定（#1/#7 の依存） |
| 7 | skill-stocktake 残余 — URL live check + usage 集計 4 補正規則の script 化（毎回 LLM が jq を再実装している） | **RFC-0009** | 確定 |
| 8 | citation-sync 残余 — arXiv/Crossref API 照合（hallucinated ID 検出、実害事例あり）+ graph_lint 既知バグ（1 行ノード形式・DOI regex の `)` 終端）修正 | 保留 | 次の引用追加時 |
| 9 | fact-checker local evidence 層 — 機械化率でなく injection 面: transcript metadata 抽出を script に降ろし「message body を読めない」をコードの性質にする（2026-07-25 F20） | 保留 | 価値主導・任意 |
| 10 | learn-eval — grounding checklist の overlap 候補（既存 skill / MEMORY.md）の機械列挙 | **RFC-0010** | 確定 |
| 11 | task-stocktake — enum 検証・日付書式・obsoleted の引用存在 | 保留 | CA ADR-0095 系「台帳を読む機構を足さない」宣言との衝突を解いてから |
| 12 | repo-asset-stocktake — tier-1 reachability scan | 保留 | 本文自身の保留条件「同じ scan が複数 run 繰り返されたら」の成立後 |

### やらない（判定理由ごと記録）

- **swift-reviewer**: script を書かず SwiftLint / swift-format / Swift 6 strict concurrency へ委譲して削るのが正解だが、著者は agent 自体の退役を検討中（2026-08-26）— 別件
- **security-reviewer**: 既に「既存ゲートへ委譲して薄化」した完成形（件数表も拒否）。#3 以降の着地の先例として引く
- **rules-stocktake**: harness_lint.py がほぼカバー済み（残余は README ツリー整合のみ）
- **title-reviewer / theme-reviewer / generation-audit / loop-design-check / authorship-strategy**: 機械化余地が低い、または頻度がほぼゼロで ROI が立たない
- **llm-as-judge / skill-health**: 適用対象でなく review-to-lint の理論的正本・完成見本

## Rationale and alternatives

- 供給駆動で一括消化する案 — 却下: 使われない lint は形骸化し、正本改修のたびに drift 負債になる
- リストを SKILL.md に置き続ける案 — 却下: sweep のたびに skill 本文が肥大。skill は手順、台帳は rfcs/ という分担（ADR-0049 と同型）

## Unresolved questions

- #11 の CA ADR-0095 衝突の解き方（enum lint と引用存在検査は非侵襲に足せる余地あり）
- WebFetch 依存検査の script 側配置の一般則（#2 着手時に ADR 化）

## Status

accepted — 確定 5 件（RFC-0006〜0010）は 2026-08-27 に全件実装・merge 完了（ADR-0052/0053/0054）。build の diff 外 HIGH 4 件を RFC-0011〜0014 として起票し S4 で実装中。保留 7 件は発火条件待ち。2026-08-27

## Next action

保留候補は各発火条件が成立したセッションで本 RFC を参照して個別起票。委譲 5 件の検収は起票セッション（または後続 task-triage）が judge として行う。

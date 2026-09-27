# review-to-lint 水平展開 — grill-me 収束結果と実施計画

## Context

skill `review-to-lint`（b89d230 / ADR-0051 で新設）の適用候補を、SKILL.md 末尾の静的リスト
（citation-formatter 起点の 4 件）のまま進めてよいかを grill-me で尋問した。sweep
（agents/ 25 本 + skills/ 67 本を Explore 2 体で走査）の結果、候補は当初の 4 件でなく
12 件あり、優先順は「機械化余地」でなく「需要の発火条件」で決まると判明した。

## Grill で確定した判断

- **駆動原理は需要駆動**: 「明確な需要 × 安定した正本」の交差だけ実施。作り置きは形骸化リスク
- **writing-ecosystem 系の束は除外**（著者判断 2026-08-26）: 設計が流動中の正本に lint を
  接木すると drift 負債になる。発火条件 = 設計安定後
- **paper 系（citation-formatter 含む）は需要待ち**: 発火 = 次の paper 作業開始時。
  WebFetch 実在確認（DOI/arXiv/URL）は `--online` flag に隔離し evidence モードは
  offline 完結、という方針だけ先に固定
- **swift-reviewer は不実施**: script を書かず SwiftLint / Swift 6 compiler へ委譲する
  刈り込みが正解だったが、著者は agent 自体の退役を検討中（別件、この計画に含めない）
- **候補リストは SKILL.md に持たず RFC 化**（著者指示）: SKILL.md 末尾の適用候補節は
  RFC へのポインタに差し替える。task-stocktake / repo-asset-stocktake も候補に含める
  （両者の本文にある script 化拒否宣言との衝突は RFC に明記し、適用前にそこを解く）
- **#1, #4, #6, #7, #10 は Opus 実装セッションへ委譲**（著者指示。ADR-0043 の
  judge/build 分業、1 件ずつ別セッション原則とも整合）

## 候補台帳（RFC 化する内容）

| # | 候補 | 委譲 | 発火条件 |
|---|---|---|---|
| 1 | context-sync（20 項目中 15 deterministic、コマンド既載） | **Opus** | 確定 |
| 2 | paper 系の束（citation-formatter 丸ごと + paper-ecosystem/paper-writing gate + vocabulary inventory 層 + paper-reviewer 構造項目） | — | 次の paper 作業 |
| 3 | writing-ecosystem 系の束（editor / essay-reviewer / clarity 系 + quality-gate + collect-context + x-draft） | — | 設計安定後 |
| 4 | agent-stocktake（name=stem・tools 実在・description 重複・suppression regex 列挙） | **Opus** | 確定 |
| 5 | config-gc（8 チャンネルを 1 scan script に） | — | 次の月次 GC |
| 6 | URL liveness 共通部品（3 skill が要求、既存 script に無し） | **Opus** | 確定（#1/#7 の依存） |
| 7 | skill-stocktake 残余（URL live + usage 集計 4 補正規則） | **Opus** | 確定 |
| 8 | citation-sync 残余（arXiv/Crossref API 照合 = hallucinated ID 検出 + graph_lint 既知バグ） | — | 次の引用追加 |
| 9 | fact-checker local evidence 層（injection 面 F20 をコードの性質で閉じる） | — | 価値主導・任意 |
| 10 | learn-eval（overlap 候補の機械列挙） | **Opus** | 確定 |
| 11 | task-stocktake（enum 検証・日付書式・obsoleted 引用存在。CA ADR-0095「台帳を読む機構を足さない」との衝突を先に解く） | — | 衝突解消後 |
| 12 | repo-asset-stocktake（tier-1 reachability。本文 L32「同じ scan が繰り返すまで束ねるな」の保留条件成立後） | — | 保留条件成立後 |

やらない（RFC に判定理由ごと記録）: swift-reviewer（退役検討・別件）、security-reviewer
（既に委譲型の完成形）、rules-stocktake（harness_lint がほぼカバー済み）、title/theme-reviewer・
generation-audit・loop-design-check・authorship-strategy（余地低 or 頻度ほぼゼロ）。

## 実施ステップ（承認後）

1. **RFC 起票**（skill: `rfc-writer` の規約に従う。次番号は 0005〜）
   - 親 RFC 1 本: 上の候補台帳全体（12 候補 + やらない判定 + 発火条件 + sweep 実測の要点）
   - 子 RFC 5 本: #1, #4, #6, #7, #10 の実装タスク（1 タスク 1 ファイル — 並行 Opus
     セッションが互いを消せない置き方）。`claims.py spawn --origin idea --parent` で系譜接続
   - 依存を明記: #6（URL 部品）は #1 と #7 が使う → #6 先行 or #1 実施者が部品として切る
2. **SKILL.md ポインタ差し替え**: `skills/review-to-lint/SKILL.md` 末尾の適用候補節を
   親 RFC への参照 1-2 行に置き換える（リストの二重管理を避ける）
3. **Opus へ dispatch**: skill: `task-triage` の dispatch 手順で子 RFC 5 件を Opus 実装
   セッションへ。各セッションは `/review-to-lint` を入口に Step 1 棚卸し → search-first →
   script（evidence モード・exit 0・免除境界は既存 corpus 実測から）→ 薄化 → ADR 記録まで
4. **本セッションは judge 側に残る**: 実装はしない。検収は task-triage の独立 judge として

## Verification

- `claims.py ready` に子 RFC 5 件が state: accepted で並ぶ
- rfcs/README.md index に 6 行追加、`harness_lint.py` が通る
- SKILL.md の候補節が RFC ポインタになり、リスト本体が SKILL.md に残っていない
- dispatch 後: 各 Opus セッションの成果物（script + tests + 薄化 diff + ADR）を本セッション
  （または後続 triage）が検収してから人間 merge

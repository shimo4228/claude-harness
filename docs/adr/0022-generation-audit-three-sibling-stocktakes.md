# ADR-0022: 世代交代監査の 3 兄弟構成 — generation-audit + agent-stocktake 新設

## Status

accepted

## Date

2026-07-26

## Context

[ADR-0018](./0018-rules-rightsize-for-claude5.md) は Claude 5 世代交代時のハーネス監査（2026-07-25〜26 実施）で、runtime 層（system prompt + tool description）の実セッション採取 → 競合 / 冗長 / ドリフトの 3 分類 → 意図・根拠・鮮度・失効条件の 4 観点判定という手順を確立した。この手順は Zenn 記事化の過程で再現可能な形に整理され、akc-cycle.md の Scaffold Dissolution 第 3 トリガー（モデル世代交代）の具体手順として、スキル化する契機になった。

設計検討（grill-me インタビュー）で 2 つの事実が確定した。

- **照合手順は 4 資産クラス（rules / CLAUDE.md / skills / agents）に跨る**。競合（同一 context への同時ロード）は skill 発火時・agent 起動時にも成立する。実施時の実例として、確信度 80% 以上のみ報告という抑制指示は agent 定義側にあった。したがって rules-stocktake への追記だけでは skills / agents に手が届かない。
- **agents には専用の stocktake が存在せず、委譲マップに穴があった**。config-gc も `agents/` を掃引しない。

このギャップを埋める設計が要る。

## Decision

2 スキルを新設する。

1. **`generation-audit`**（オーケストレータ、user-invocable）— runtime 層採取（テーマ別逐語引用、自己申告の限界と別セッション再現確認を明記）+ 競合 / 冗長 / ドリフトの 3 分類 + 4 観点判定枠のみを保持し、**verdict を持たない**。verdict 確定と処分実行は資産クラスごとの stocktake に証拠台帳を渡して委譲する（rules → rules-stocktake / skills → skill-stocktake / agents → agent-stocktake / CLAUDE.md のみ inline confirm-each）。渡し方は rules-stocktake Stage 2 の既存の外部証拠の口（skill-comply results と同じ read-never-require 契約）を再利用する。
2. **`agent-stocktake`**（第 3 の兄弟）— `~/.claude/agents/*.md` を監査する。cost model はハイブリッドとする: description 層は「Available agent types」一覧として毎セッション常駐（residency）、body 層は起動時ロード（invocation）。抑制指示の検出と Improve-by-inversion（方向転換した指示は削除でなく逆向きに書き直す — 削除では抑制フレームが残る）を Stage 1 に組み込む。

付随決定として以下も定める。

- 「反転」は新 verdict にせず、既存 Improve の一形態（Improve-by-inversion）として扱う（verdict 表の正本を割らない）。
- AKC repo への還元はローカル実証（次の世代交代でのフル実行）後の別タスクとし、今回は行わない（Prototype Before Scale）。
- akc-cycle.md の Curate 行と世代交代トリガー段落、rules-stocktake / skill-stocktake の Related 節に受け口ポインタを追記する。

## Alternatives Considered

### (a) rules-stocktake 拡張

横断スコープ（skills / agents）に届かない。Knowledge Placement の「既存スキルがそのドメインをカバーしている」条件が不成立のため却下。

### (b) 独立監査型（採取から処分まで新スキルが自前完結）

既存 stocktake と verdict 機構が並立し、verdict 表の正本を割る。ADR-0018 が潰した「正本の自称し合い」の再演になるため却下。

### (c) agents を skill-stocktake に拡張

skill-stocktake の cost model（trigger pollution）が agent の常駐 description（residency）に合わず、設計のねじれが出るため却下。

### (d) AKC repo へ今回同時還元

未実証手順の配布リスクと、ローカル版 / 配布版の乖離管理負荷（ADR-0018 の Negative で既に警告済み）が乗るため却下。構想メモの還元は実証後に回す。

## Consequences

### Positive

- Scaffold Dissolution の第 3 トリガー（世代交代）に再実行可能な具体手順が付いた。次の世代交代で同じ監査を `/generation-audit` から再現できる。
- 委譲マップの穴（agents）が塞がり、stocktake が skill / rules / agents の 3 資産クラスを揃って覆う。

### Negative

- generation-audit の初回フル実行は次の世代交代まで検証不能である（dry-run は Phase 1 の 1 テーマ — 可逆性・確認ゲート — のみ実施済み）。
- stocktake が 3 本になり、Curate 面の運用（ledger 3 つ、実行タイミングの判断）が増える。

### Neutral / Follow-ups

- 4 観点判定のうち「根拠」「失効条件」は [ADR-0021](./0021-rules-metadata-and-premise-lint-gates.md) の rationale / review-when メタデータを機械可読な入力として利用できる。
- AKC repo への還元は次の世代交代での実証後に別タスクとして検討する。

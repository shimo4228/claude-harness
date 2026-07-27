---
name: task-stocktake
description: "Consolidate a repo's pending-task tracking into its single task ledger (default .notes/TASKS.md) — bootstrap it if missing, sweep handoff / audit / remaining-issues files and auto-memory for stray task lines, verify pending entries against git log and actual code, archive detail files of completed tasks. Use when the user says 「残タスクを棚卸しして」「タスク台帳を作って/整理して」「残っているタスクは？」, \"task stocktake\", when task lines are scattered across notes files, or when a repo's ledger may be stale. NOT for — skills → skill-stocktake; rules → rules-stocktake; repo non-code assets → repo-asset-stocktake; in-session todos → harness task tools."
user-invocable: true
origin: shimo4228
---

# task-stocktake — Task Ledger Audit & Consolidation

repo の pending タスク追跡を**単一台帳**に収束させ、台帳の鮮度を git 実態と突合する。
原則の正本は rule `common/task-tracking.md`（台帳は 1 repo 1 ファイル / 詳細資料に
タスク行の正本を持たせない / MEMORY.md はポインタのみ）。本 skill はその手順を持つ。

## Phase 1 — Bootstrap（台帳の解決・作成）

1. 台帳を解決する: `.notes/TASKS.md` → 既存タスクファイル（`TODO.md` / `TASKS.md` /
   `docs/backlog.md` 等）の順
2. 見つかればそれを台帳と確定して Phase 2 へ
3. 無ければ作成する。「作るか」は聞かない（skill の起動自体が依頼）— 確認するのは**置き場所だけ**:
   - `.notes/` 慣行がある repo は `.notes/TASKS.md`（gitignored = private）に即決。
     無い repo は gitignore 状況を見て private / git-tracked（clone 先でも cold-start 可能）の
     トレードオフを提示して選んでもらう
   - 初期内容: Phase 2 の sweep 結果を集約して生成

台帳フォーマット（1 タスク 1 行）:

```markdown
# TASKS — <repo name>

> 正本: このファイル。詳細はリンク先。規約: rule common/task-tracking.md

## Pending

| ID | 状態 | タスク | 着手条件 | 詳細 |
|----|------|--------|----------|------|
| T1 | ready | … | なし | [handoff-….md](…) |
| T2 | blocked | … | 次リリース後 | … |

## Done / Dropped

| ID | 結果 | タスク | 完了日 / 判断 | 詳細 |
```

状態語彙: `ready`（着手可）/ `blocked`（着手条件待ち）/ `observing`（観察窓待ち）/
`deferred`（意図的保留 — 再提起しない場合はその旨明記）。

## Phase 2 — Sweep（散在タスク行の検出）

台帳の外にタスク行を持ちうるファイルを走査し、台帳に無い項目を列挙する:

- handoff / cold-start ファイル（`handoff-*.md` 等）の「タスク一覧」「残課題」節
- 監査台帳（`bug-audit-*.md` / `remaining-issues-*.md` / stocktake 出力）の未完項目
- auto-memory `MEMORY.md` の Pending 節（あれば内容を台帳へ移しポインタ化を提案）
- README / CLAUDE.md 内の TODO 記述

**sweep 対象外（タスク行の正本増殖に数えない）**: doctrine / ADR が正本指定した
domain ledger（例: strategy 運用の public intervention timeline）と、wiki-harvest 型の
**候補台帳**（採否判断前の候補はタスクではない）。これらは台帳に吸収せず、
ポインタ 1 行を置く。候補が採択され、作業として残った時点で初めて台帳行になる。

検出は列挙・報告まで（enumerate）。台帳へ載せるか・どの状態にするかはユーザー / 会話で
判断する（decide）— when-code-when-llm の enumerate/decide 分割。

## Phase 3 — Verify（既済・stale 照合）

台帳（+ Phase 2 検出分）の各 pending 行を実態と突合する:

1. `git log --oneline` + 該当ファイル・コードの直読みで**既に完了していないか**確認
   （台帳は drift する、コマンドはしない）
2. 着手条件付きタスクは条件が開いたか（リリース済み / 観察窓明け / 依存解消）を確認
3. 結果を 3 分類で報告: `既済（Done へ移動）` / `stale（内容更新が必要）` / `現役`

## Phase 4 — Archive（完了詳細ファイルの退避提案）

Done になったタスクの詳細ファイル（handoff / 台帳類）のうち、Pending 行から参照されて
いないものを archive ディレクトリへの移動候補として提示する。**確認つき soft-delete**
（rename / 移動のみ、削除しない）。直近参照が多いファイルは無理に動かさない。

## 出力

```
Ledger: <path>（新規作成 or 既存）
Swept: N 件の散在タスク行（うち M 件を台帳に追加）
Verified: 既済 X / stale Y / 現役 Z
Archived: K ファイル移動（提案 L 件中）
Next action: <ユーザー判断が要る項目の一覧>
```

## 境界

- skill / rule / repo 資産の品質監査はしない（skill-stocktake / rules-stocktake /
  repo-asset-stocktake の領分）
- セッション内 todo（harness の TaskCreate 等）は対象外 — あれは実行中の進捗表示、
  台帳は セッションを跨ぐ pending の正本
- タスクの実装はしない（棚卸しのみ）。実装は通常の chain で

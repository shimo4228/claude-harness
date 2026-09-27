# Fable を設計・judge に専念させる委譲配線（plan 承認境界の advisory + 既定の反転）

## Context

Fable の使用制限が最も使う土日に枯渇する。原因は「Fable = judge / Opus = build」（ADR-0043）の
建付けに対し、実装が Fable セッションに流れる構造:

- `implementation-chain` の「実行者の決定」は plan 末尾の自答 1 行のみで発火機構が無い。
  「条件を満たさないならこのセッションで実装してよい」のエスケープハッチが自己判定で素通り
- ADR-0043:111-121 に同じ穴の実測事故記録あり（2026-08-22、Fable セッションで重実装 → 限度到達）。
  対応は導線追加のみで enforcement 未設置
- rules 層に委譲の常駐規約が無く、skill が読まれなければ委譲判断自体が発火しない
- Edit/Write を対象にした judge-tier の hook は存在しない（block されるのは
  `/code-review`・`/simplify` 直呼びのみ — `hooks/review-model-notice.sh`）

**触らないもの（ユーザー実測により確定）**: `skills/spawn-session/spawn.sh` は変更しない。
task-triage の dispatch では herdr 経由で Opus 起動が実運用で成立しており、spawn-session への
モデル固定は明確に拒否された。また Review の実行モデル pin（judge-tier では `/code-review` を
`Agent(model: "opus")` 内で起動）は既存配線がそのまま正 — 本プランで変更しない。

構成: 発火時刻を持つ advisory hook（ExitPlanMode 直後 = 最初の実装 Edit の前ターン）+
skill の既定反転 + rules 1 行。block にしない理由: plan 内容の機械判定が不可能で誤検知があり、
harness 設計文書の編集（Fable の本業）で毎回ぶつかるため。

## Changes

### 1. `hooks/plan-executor-notice.sh`（新規）— ExitPlanMode PostToolUse advisory

`hooks/review-model-notice.sh` を雛形に:

- fail-quiet 徹底: jq 失敗・transcript 不在・モデル判定不能はすべて `exit 0`
- セッションモデル判定は review-model-notice.sh:53-61 のパターンを流用
  （`transcript_path` → `tail -c 2000000` → 直近 `"model"` フィールド → `*fable*` 照合。
  テスト用 env override `PLAN_EXECUTOR_TRANSCRIPT`）
- best-effort 抑制: `.tool_input.plan` が読めて実行者決定の痕跡
  （`実行者` / `dispatch` / `spawn-session` / `--model opus` のいずれか）を含むなら無音。
  読めない場合は advisory を出す（読めなくても成立する設計）
- 文面は静的文字列のみ（transcript / plan 由来テキストをエコーしない）。要点:
  「このセッションは judge-tier (Fable)。実装 Edit の前に『実行者の決定』を 1 行 —
  既定は build-tier への dispatch（skill: task-triage の経路）。自己実装は例外 3 種
  （設計文書・ADR・skill/rule 散文 / dispatch 不能の具体的理由を 1 行記録 / ユーザー明示指示）
  のときだけ。正本: skill implementation-chain・ADR-0043」
- 封筒は `hooks/_advisory-common.sh` の `emit_advisory PostToolUse`

### 2. `settings.json` — hook 配線

PostToolUse に matcher `ExitPlanMode` → `hooks/plan-executor-notice.sh`（timeout 10）を追加。
ロジックは外部 script（規約: hook ロジックを settings.json に埋め込まない）。

### 3. `tests/plan-executor-notice.bats`（新規）

既存 hook テストの形式に合わせ最低 4 ケース:
fable transcript → advisory 出力 / 非 fable → 無音 / transcript 読めない → 無音（exit 0）/
plan に実行者決定の痕跡あり → 無音。

### 4. `skills/implementation-chain/SKILL.md` — 「実行者の決定」の既定反転（:36-48）

現行「条件を満たさないなら、このセッションで実装してよい」を反転:

- **judge-tier (Fable) セッションの既定 = dispatch**。自己実装は次の例外を plan に
  1 行記録したときのみ: (a) 設計文書・ADR・skill/rule 散文の編集（Fable の本業）、
  (b) dispatch 条件を満たせない具体的理由がある、(c) ユーザーの明示指示
- ADR-0016:20「model 継承は能力しか救わず文脈損失は救わない」への応答として
  「文脈損失は dispatch packet の充実で救う（packet の形は task-triage が正本）」を 1 文追加
- 失効条件の段落（:47-48）は既存のまま維持

### 5. `rules/common/planning.md` — 常駐 1 行

Build-or-not 行の直後に追加:
「judge-tier セッションでの実装は build-tier への dispatch が既定 — 実行者の決定と例外は
skill: `implementation-chain`（三役の正本: ADR-0043）」。
plan mode を通らない ad-hoc 実装は hook が発火しないため、それをカバーする唯一の常駐層。

### 6. ADR 新規（実装後、skill: `adr-writer` で）

決定: plan 承認境界の advisory + 既定反転。spawn-session 無変更の理由（ユーザー実測）も記録。
Review-when: ① substrate がセッション単位の model routing を自発的に行うようになったら
hook と rules 行を外す ② 次の土日で Fable 限度再到達が起きるかを実測し、起きるなら
block 昇格や別の層を再検討。

### 7. RFC 起票（skill: `rfc-writer`、実装は別タスク）

task-triage:141-144 の「Agent tool 経路は hooks/skills の発火が未検証 (2026-08-17)」注記の
解消を RFC として起票（measurement batch で先に試す既存注記の手順を写す）。本プランでは
検証自体は行わない。

## Verification

1. `bats tests/plan-executor-notice.bats` が green（既存 bats テストと同じ流儀で実行）
2. repo の verify entrypoint（`.claude/verify.sh`）を実行し既存ゲート通過
3. 手動 E2E: この Fable セッション（または新 Fable セッション）で plan mode →
   ExitPlanMode 承認 → advisory が差し込まれることを確認。Opus セッションでは無音を確認
4. `git status` と doc sync（implementation-chain / planning.md の変更は同一 diff に含める）

## 実装の実行者

このプラン自体が harness の skill/rule/hook 編集（例外 (a) 相当）だが、hook script + bats は
コード実装なので、承認後の実装は本プランの新規定に従い Opus へ dispatch 可能な形
（1 セッション・worktree 可逆・受け入れ条件 = bats green）。dispatch するか本セッションで
実装するかは承認時に確認。

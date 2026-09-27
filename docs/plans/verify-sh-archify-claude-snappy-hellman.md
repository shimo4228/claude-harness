# Plan: Archify で ~/.claude harness と verify 機構を視覚化する

## Context

`.claude/verify.sh`（513 行）と、それを起動する commit 境界の hook chain（`verify-precommit.sh` →
`verify_allow.py` 承認台帳 → gate 実行 → advisory / block）が大きくなり、著者が構造を追えなくなった。
skill `archify` で explorable HTML 図を 3 枚作り、`docs/diagrams/` に commit する。
読者は著者（人間）なので、ここは「人間可読性に予算を払う README / 出力の文面」側の成果物。

図は実コードの写しである必要がある。事実の正本は本セッションの探索結果（下記「Evidence」）で、
実装時に該当行を再確認してから node / edge を書く。

## Deliverables（3 枚 + 元 JSON）

出力先: `~/.claude/docs/diagrams/`（新規）

| # | ファイル | type | 内容 |
|---|---|---|---|
| 1 | `harness-overview.architecture.json` → `.html` | architecture | ~/.claude 全体: rules / skills / agents / hooks / scripts / tests / docs / settings.json と、Claude Code runtime との配線 |
| 2 | `verify-commit-gate.architecture.json` → `.html` | architecture | `git commit` → PreToolUse hook chain → `verify_allow.py` 台帳 → `verify.sh` → lint 群 / bats / golden → advisory or block |
| 3 | `verify-sh-gates.workflow.json` → `.html` | workflow (schema_version 2) | verify.sh 内部: 共通前段 → staged / full の分岐 → 各ゲート順序 → exit 0/1/2 |

`docs/diagrams/README.md` を 1 枚（各図 1 行 + 再生成コマンド）。`.claude/verify.md` に図 2・3 へのリンクを 1 行追加。

## Steps

1. **Skill 手順に従う**: `skills/archify/schemas/{architecture,workflow,common}.schema.json` と example
   （`web-app.architecture.json` / `release-delivery.workflow.json`）だけ読む。renderer 内部は読まない。
2. **図 2（verify commit gate）を先に作る** — 著者の主訴。node ≤ 12、`meta.quality_profile: "showcase"`、
   `meta.visual_preset` / `subtitle` / `locale` は省略（日本語ラベルなので Viewer UI は英語 fallback と明記）。
   node 候補（type）:
   - `git commit`（external）/ `settings.json PreToolUse[Bash]`（frontend）
   - `secret-scan-precommit.sh`（security）/ `verify-precommit.sh`（security）/ `harness-lint-precommit.sh`（security）
   - `verify_allow.py`（security, tag: hash 台帳）/ `~/.claude/verify-allow.json`（database）
   - `.claude/verify.sh`（backend, emphasis）/ `harness_lint.py`（backend）/ `hooklint (Rust)`（backend）/ `bats + tests/golden`（backend）
   - `model additionalContext`（external, dashed）/ `decision: block`（security）
   - boundary: `~/.claude harness` と `対象 repo`
   - 主経路: commit → hook → verify_allow → verify.sh → 各ゲート → advisory。分岐: rc71 stale / FAIL → block。
   - stand-down（ruff-format / bandit が verify.sh 存在時に退く）は card に書き、edge にしない
3. **図 3（verify.sh workflow）**: lanes = `setup` / `staged` / `full` / `exit`。phases = 共通前段 / mode 別ゲート / 終了。
   staged: materialize → format → lint → shellcheck → hooklint(prebuilt) → markdown advisory → exit。
   full: format/lint(owned py) → shellcheck → hooklint build+run（bats より前、理由を card に）→ bats → pytest → skill-test → file-loc(800) → ty(sub) → ty(root) → exit。
   `harness-lint` は両モード共通の先頭。exception lane に `exit 2 (uvx 無し)` と `FAIL=1`。
4. **図 1（harness overview）**: CLAUDE.md の Layout をそのまま node に。`settings.json` が hooks を配線し、
   hooks が scripts を呼び、tests が hooks/scripts を固定（golden）、docs/adr が判断を持つ、公開は harness-sync という 1 主経路。
5. 各候補ごとに `validate <type> <json> --quality showcase --json`（9 checks / 0 error / 0 warning まで修復。
   2 ラウンド改善なしで停止して報告）。workflow は `--layout-json` で診断。
6. `deliver <type> <json> <html> --quality showcase --json` → `visual-check <html> --json`。
   1440×900 / 1600×1000 / 1920×1080 で overflow 無しを確認。
7. 初回候補作成後に `scripts/check-update.mjs` を 1 回実行（skill の Update awareness）。
8. README / verify.md のリンク追加 → `./.claude/verify.sh` 実行（harness-lint が markdown link を検査する）→ commit。

## Evidence（実装時に再確認する行）

- verify.sh 契約: `.claude/verify.sh:2-16`、root 解決 `:20-25`、harness-lint `:157`、staged `:184-331`、full `:333-513`
- hook 配線: `settings.json:185-209`（Bash PreToolUse 7 本の順序）
- verify-precommit: bypass `:32`、target `:44-51`、`verify_allow.py run` `:62-81`、rc 分岐 `:93-198`
- verify_allow.py: 台帳 `:50`、exit code `:53-58`、hash 済み bytes 実行 `:144-162`
- stand-down: `hooks/ruff-format-precommit.sh:67`、`hooks/bandit-precommit.sh:73`
- hooklint: `scripts/hooklint/src/rules.rs:1-25`、golden skip `tests/golden-hooklint.bats:23`

## Verification

- 3 つの `deliver` が exit 0、receipt に 9 artifact checks / 0 errors / 0 warnings
- `visual-check` が 3 viewport で scrollWidth/Height ≤ window
- 著者が HTML を開いて図 2 の主経路（commit → 台帳 → verify.sh → block/advisory）が 1 画面で追えること（perceptual review は人間）
- `./.claude/verify.sh` が exit 0（新規 .md のリンク検査を含む）
- `git status` で docs/diagrams/ の json + html + README、verify.md の差分のみ

## Out of scope

- verify.sh 自体の分割・簡素化（図で構造が見えてから別タスクで判断）
- `meta.animation: "trace"` 等の motion（要望があれば後付け）

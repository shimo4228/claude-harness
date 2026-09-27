# ハーネス改善計画 — ギャップ調査に基づく統合

## Context

3 並列調査（資産インベントリ / チェーン整合性監査 / 放置スレッド発掘）の結論:
このハーネスは構築期からキュレーション・公開期に移行済みで、欠けているのは新機能ではなく
**(a) rules が約束する保証の決定論的裏付け**（hooks.md 自身の原則「Quality enforcement → hooks」に対し、
Verify ステップの coverage / secret scan / doc-sync に hook がゼロ）、
**(b) 飛行中の未コミット作業の着地**（authorship-strategy v1.0.0 汎用化ほか）、
**(c) 監査装置自体の劣化**（skill-stocktake の learned/ 二重カウント + 全件 Keep）。

ユーザー確定方針: enforcement は選択的導入（ruff hook + secret scan のみ、coverage ゲートは LLM 裁量のまま）/
飛行中作業はこの計画で着地 / ドメイン拡張は最小限（telemetry は既存 skill へ追記、Swift/TS rules は YAGNI 見送り）。

タスク種別: `chore`（settings.json / hooks 変更 → Code Review Y、hook 追加 → Security Review Y）

---

## Phase 1 — 飛行中作業の着地（コミット確定）

現在の dirty tree + untracked を、文脈ごとに分けてコミットする。

1. **authorship-strategy v1.0.0 汎用化** — `skills/authorship-strategy/SKILL.md` + `provenance-layer-prompt.md`
   の diff（shimo4228→汎用表現、Appendix A/B 削除）をレビューして commit。
   `plans/1-pure-badger.md` が言う「CHANGELOG 起稿済み・未 commit / 未 tag」の tag 作業が残っていれば
   ユーザーに確認（v1.0.0 tag は外部公開 = 人間 gate）。
   ※ 削除される Appendix（AAP→AKC provenance rollout 台帳）は永久喪失しないよう、
   commit メッセージに「rollout 台帳は git 履歴の本 commit 以前に存在」と明記。
2. **kickoff skill** — `skills/kickoff/SKILL.md` を commit（完成済み・origin: shimo4228 付与済み）。
3. **stocktake 結果 + learned note** — `skills/skill-stocktake/results.json`（07-05 再実行分）と
   `skills/learned/claude-code-tool-patterns.md`（YAML colon-space trap 追記）を commit。
4. **settings.json** — model pin 除去（`/model` 駆動に委ねる）を commit。
   pin 除去は過去に往復しているため、コミットメッセージに「/model 駆動に確定」と決定を明記。
5. **scheduled-tasks/weekly-aeon-shopping** — 短い `scheduled-tasks/README.md`（規約 1 段落: 何を置く場所か、
   launchd 配線は task ごと）を添えて commit。launchd plist 未配線・依存 project skill 未作成は
   README 内に既知ギャップとして記載（実装はこの計画のスコープ外）。

## Phase 2 — Enforcement hook 2 本の新設（選択的導入）

既存イディオム準拠: settings.json は `bash ~/.claude/hooks/<name>.sh` のみ、
ロジックは外部スクリプト（`hooks/bats-autorun.sh` を雛形にする — stdin JSON → jq で
file_path 抽出 → JSON 出力で block / additionalContext）。

1. **`hooks/ruff-autofix.sh`**（PostToolUse, matcher `Edit|Write`）
   - `.py` のみ対象。`ruff format <file>` → `ruff check --fix <file>`。
   - 残存 lint エラーは **non-blocking** で `additionalContext` として Claude に返す
     （multi-edit 途中で block すると作業が止まるため。bats-autorun と違い block しない）。
   - `rules/python/hooks.md` が既に指示している内容の実装。
   - mypy hook は作らない — pyright-lsp plugin が既に type 診断を提供（substrate 吸収済み）。
2. **`hooks/secret-scan-precommit.sh`**（PreToolUse, matcher `Bash`）
   - コマンドが `git commit` を含むときのみ発火。staged diff（`git diff --cached`）を
     `detect-secrets`（permissions 済み）でスキャン。検出時は `decision: block` + 検出内容。
   - detect-secrets 未インストール環境では軽量 regex fallback（AWS key / Bearer / PEM ヘッダ等）。
3. **settings.json** に 2 hook を配線。
4. **rules 側の記述を現実に同期**:
   - `rules/python/hooks.md` — mypy/pyright 行を「pyright-lsp plugin が担当」に修正
   - `rules/common/planning.md:56` — 「PreToolUse hook による自動強制を検討」の文を現状
     （Stop advisory hook あり / Phase 0 強制は非導入と判断）に合わせて更新
   - `rules/common/security.md` — secret scan が hook 化された旨を反映

## Phase 3 — 監査装置の修理（skill-stocktake）

1. **learned/ 二重カウント修正** — enumerator が `learned/xxx` と bare `xxx` の 2 経路で
   同一ファイルを数えている。skill-stocktake の SKILL.md / スクリプトの列挙ロジックを特定し、
   1 経路に統一（`skills/learned/*.md` は flat reference として 1 回のみ）。
2. **弁別力の注記** — 全件 100% Keep は 2 回連続。stocktake の SKILL.md に
   「telemetry（log-skill-usage の蓄積ログ）を読み、発火実績ゼロの skill を
   Retire/Merge 候補として優先審査する」ステップを追記（→ ドメイン拡張「最小限」の telemetry 活用。
   新 skill は作らず既存 skill への追記 = Knowledge Placement 規則準拠）。

## Phase 4 — 参照整合の修正（軽量）

1. `rules/common/coding-style.md:66` — `See skills: config-gc, agent-self-modification-gates`
   → `See skill: config-gc / See learned note: skills/learned/agent-self-modification-gates.md` に修正
2. `rules/common/security.md:31` — 同様に `llm-memory-trust-boundary` を learned note 参照に修正
   （learned ノートの skill 昇格はしない — 発火実績データが無い段階での昇格は abstraction trap）

## Phase 5 — 衛生（/config-gc 実行に委譲）

手動削除はせず、`/config-gc` を 1 回実行して confirm-each で処理:
- `_gc_trash/2026-07-03/`（soft-delete 済み、保持期間経過）
- `settings.json.bak-20260703`
- `plans/` 118 件の古い自動生成 plan
- `templates/hybrid/_swarm-backup/`

---

## 見送り（明示的 non-goals）

- **coverage ≥80% の hook 化** — 硬直的すぎる。LLM 裁量のまま（ユーザー確定）
- **doc-sync-in-same-diff の hook 化** — 意味的判定が必要で code に不適（when-code-when-llm の seam）
- **Swift/TS rules 新設** — iOS 作業が本格化するまで YAGNI（ユーザー確定）
- **search-first の PreToolUse 強制** — advisory Stop hook で運用継続、planning.md の記述だけ現実に同期
- **learned ノートの skill 昇格 / telemetry 独立 skill** — 追記で足りる

## Chain / レビュー

- Parallel Group: [code-reviewer, security-reviewer]（Phase 2 の hook script + settings.json diff 対象。
  chore × hooks/permissions 変更なので両方 Y）
- Sequential: Verify（下記）→ commit 群

## Verification

1. **ruff hook**: `.py` を 1 ファイル編集 → format が走り lint 結果が additionalContext に載ることを確認。
   単体では `echo '{"tool_input":{"file_path":"/tmp/x.py"}}' | bash hooks/ruff-autofix.sh` で JSON 出力検証
2. **secret-scan hook**: scratchpad にダミー secret（`AKIA...` 形式）を stage → `git commit` が block されること、
   clean な diff では素通りすることを確認
3. **stocktake 修正**: 列挙を dry-run し、learned/ が 1 回ずつしか現れないこと
4. **rules 参照**: `grep -rn "See skill" rules/` で全ポインタが実在ファイルに解決すること
5. `git status` が clean（Phase 1 の全着地確認）

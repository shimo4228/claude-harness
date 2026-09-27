# pr-review-toolkit plugin を外し、Code Review 行を built-in `/code-review` の設計どおりに戻す

## Context

著者は「`/code-review` 時に code-reviewer が呼ばれるようになった」と観測し、subagent 実行への
最適化を求めた。調査（2026-09-12、CLI 2.1.269 バイナリ / plugin cache / `metrics/*.jsonl` /
CA s11 transcript）で前提を補正した:

- built-in `/code-review` / `/simplify` は plugin agent を**呼ばない**（無名 subagent への
  fan-out 動的 prompt。バイナリに `pr-review-toolkit:code-reviewer` は 0 件）。今日の CLI 更新
  でも plugin ファイルでも挙動は変わっていない。
- 実態は **plugin agent の description（"use proactively"）にモデルが引かれた自発置換**。
  `pr-review-toolkit:code-reviewer` は導入日 2026-08-21 から継続起動（08-22: 4、08-30: 3、
  09-05: 3、09-12: 5、計 20）。今日の build セッションは `Skill(code-review, medium)` の 13 秒後に
  plugin agent を **1 本**起動し、built-in の「8 finder angle 並列 + verify」を単一 agent
  （confidence ≥ 80 のみ報告）で代替していた。ADR-0042 が予告した二重指揮の実現。
- 他の plugin agent は ADR-0055（2026-08-27）以降ゼロ: silent-failure-hunter 9（最終 08-26）、
  code-simplifier 3（08-22）、pr-test-analyzer 1（08-21）、`/pr-review-toolkit:review-pr` 0。
- harness 側の依存は `skills/context-sync/SKILL.md` L281 の 1 行のみ。
- `/security-review`: plugin agent は存在しない（built-in は marketplace 非公開 plugin の
  wrapper で bundled prompt が走る）。自作 `agents/security-reviewer.md` は元から subagent。
  ADR-0042 の built-in 却下理由は不変 — **変更なし**。

著者判断（2026-09-12）: plugin agent へ置換するのではなく **plugin を削除**する。二重指揮の
供給源を消せば、ADR-0042 / 0055 の配線（built-in `/code-review` + judge-tier では opus 包み）は
無変更のまま実態と一致する。機構を足さず減らすだけ。

harness-boundary 1 行: 置き場は settings（plugin 無効化）と既存 ADR の注記 — 新機構なし。
Build-or-not: 削除のみ。

## 種別

`chore`。Code Review Y（本 diff は散文 + 設定なので built-in `/code-review` を opus 包みで 1 回）、
Security Review -（permissions / hook / 無人経路に触れない）。実行者: 本セッション
（(a) 設定・ADR・skill 散文編集）。

## 変更

### 1. plugin の削除

- `claude plugin disable pr-review-toolkit@claude-plugins-official` を実行し、`settings.json`
  `enabledPlugins` の当該行が `false` になる（または消える）ことを確認。cache
  （`plugins/cache/claude-plugins-official/pr-review-toolkit/`）は disable では残る — 再 install が
  容易なので削除しない（marketplace copy も残る）。
- `settings.json` は git 追跡外（ADR-0042 が記録）なので、durable な記録は ADR 注記（3）が持つ。

### 2. 参照 repoint

- `skills/context-sync/SKILL.md` L280-282: 「plugin 経由なら `pr-review-toolkit:review-pr`」を削り、
  「`/code-review <PR#>`。発火条件の正本は skill: `implementation-chain`」だけにする。
- `skills/implementation-chain/SKILL.md`: Review 表 / pin 段落は不変。opt-in 名簿の末尾に 1 行 —
  「plugin 由来の reviewer agent（description に自発発火を持つもの）は入れない。Code Review 行の
  代替として自発選択され built-in の fan-out を単一 agent に縮退させた実測は ADR-0042 注記」。
  silent-failure 軸の復活受け皿は ADR-0055 Review-when が持つので、ここには書かない。
- `.notes/` と `skills/skill-stocktake/results.json` の言及は過去の出来事の記録 — 書き換えない。

### 3. ADR 注記（新 ADR は立てない）

- ADR-0042 Decision 末尾に日付付き注記: 「2026-09-12: pr-review-toolkit（2026-08-21 導入）の
  `code-reviewer` が description の自発発火で Code Review 行を代替し、built-in の fan-out を
  単一 agent に縮退させていた（agent-usage.jsonl 計 20 回、日別カウントの正本はここ）。plugin を
  disable。Alternatives「ECC 上流を取り込む」の却下理由（PROACTIVELY 付き agent は Matrix と
  二重指揮）が plugin でも再現した実測」。Review-when 相当を同注記に 1 行: 「built-in
  `/code-review` が named agent への dispatch を持つようになった / silent-failure 軸の復活
  （ADR-0055 Review-when）で受け皿が要る — 再 install を検討」。
- ADR-0055 は不変（Silent-Failure 行の削除が効いた証拠として agent-usage の 08-27 以降ゼロを
  ADR-0042 注記から参照）。
- adr-reviewer は新 ADR 執筆時の内部ステップなので、注記のみの本 diff では起動しない
  （skill: `adr-writer` の配線どおり）。

### 4. Doc Sync

`docs/adr/README.md` index は ADR 新設なしのため不変。golden 対象なし。公開 copy は commit 後に
skill: `harness-sync`（本 plan の外、著者指示待ち）。

### 5. モデル別 effort（著者追加依頼、2026-09-12）

`settings.json` `modelSettings` の現状: `claude-opus-5` = medium、`claude-fable-5` = high、
`claude-fable-5-1` = **medium**（5.1 切替時の取り残し。現セッション model は `claude-fable-5-1`）。
変更は 1 行 — `claude-fable-5-1.effortLevel` を `high` に。Opus は既に medium で不変。
`claude-fable-5` の entry は旧 model 名なので削除（残しても害は無いが、二重定義が drift する）。
memory `project_opus_medium_effort_trial.md` は Opus medium 試行の記録として不変。
公式 docs（code.claude.com/docs/en/model-config.md、as-of 2026-09-12、v2.1.267+）で
`modelSettings.<model-id>.effortLevel` が per-model の正規 key であることを確認済み。
注意: Fable 5 系は「default effort hold」（picker で確定した値がセッションをまたいで保持され
settings より優先）を持つ。settings 編集だけでは hold が残りうるので、著者が `/effort high` を
Enter で確定する（同時に settings へも書かれる。`s` は session-only）。子セッション
（`claude --bg --model opus`）は `modelSettings` を自動継承、`--effort` 付きはその回限り。

## Verify

1. `claude plugin list` 相当（`settings.json` の `enabledPlugins`）で pr-review-toolkit が無効。
   新セッションの Agent tool の agent 一覧に `pr-review-toolkit:*` が出ない（本セッションの
   一覧は起動時 snapshot なので、確認は次セッションか `claude -p` 子で）。
2. `python3 scripts/hooks/harness_lint.py` と `.claude/verify.sh` 緑（bats 全件）。
3. 本 diff の Code Review: `Agent(subagent_type: "general-purpose", model: "opus")` 内で
   `Skill(code-review)` effort medium。`review-model-notice` が沈黙すること。
4. effort: `python3 -c` で `settings.json` の `modelSettings` を読み、fable-5-1 = high /
   opus-5 = medium を確認。次セッション起動時の effort 表示（statusline / `/config`）で照合。
5. `git status` で対象外の既存 dirty（`hooks/_episode-log-common.sh`、
   `tests/episode-log-guards.bats`）を巻き込まない。

## 対象外（記録のみ）

- opus 包みの中で built-in の入れ子 fan-out（8 angle / 4 angle）が動くかの実測。動かなければ
  縮退経路（逐次 1 文脈）で走っている。plugin 削除後に測る価値が上がる — 別タスク。
- `/security-review` の plugin 化は marketplace 公開待ち。公開時は ADR-0042 の却下理由で再判定。

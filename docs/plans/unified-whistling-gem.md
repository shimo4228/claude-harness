# T-011: skill-comply grader 改修 — compliance 過少評価の修正

## Context

skill-comply の grader が compliance を系統的に過少評価する（run 3 supportive: ほぼ完全な chain 挙動が 0%）。原因は 3 つで、いずれもコード上で特定済み:

1. **1 event 1 label 制約** — `prompts/classifier.md:3,23` の「各 tool call は最大 1 step」指示。1 つの Text が分類宣言と plan 提示を両方含むと片方しか検出されない。**データ構造（`dict[step_id, list[event_index]]`）は既に多対多を許容**しており、制約は prompt 文言と `report.py:119-123` の逆引き後勝ちのみ。
2. **after_step カスケード** — `grader.py:35-38` が `after_step` の参照先に `resolved`（確定検出済み）だけを見るため、上流 1 step の取りこぼしが下流全 step を「not yet detected」で連鎖 FAIL させる（run 3 supportive で 5 段全滅を実証）。`before_step` 側には `classified` フォールバックがあり非対称。
3. **spec 再生成の非決定性** — `run.py:76` が毎回 LLM 生成。生成 YAML は `spec_generator.py:69-84` の tempfile で即 unlink され、保存・再利用の口が無い。読込関数 `parse_spec(path)`（`parser.py:111`）は既存なので、**書き出しと CLI 引数だけ足せばよい**。

タスク種別: **fix**。Chain: Plan → TDD → python-reviewer + codex-review（並列）→ Doc Sync（SKILL.md 同 diff）→ Verify。Phase 0 省略（バグ修正）、Security Review 省略（入力検証・認証・秘匿情報に非該当）。根本原因の証拠は `.notes/TASKS.md` T-011 と `results/implementation-chain.md`（本プランの承認を debugging.md の「go」とみなす）。

## 設計判断（Why / Alternatives）

### 問題 1: classifier の multi-label 許可 — prompt 改修のみ

コード変更はほぼ不要（構造が既に多対多対応）。`classifier.md` の 2 文言 + example を変更し、`report.py` の timeline 逆引きを `dict[int, list[str]]` 化して join 表示。

- 過大評価への振れ（1 回の pytest が red と green 両方に載る等）は「各 detector を**単独で**満たす場合のみ列挙、同一側面を競合する detector は best match 1 つ」の限定文言で緩和。順序検査は step ごとに独立に効き続けるので時間的に不可能な二重加点は落ちる。

### 問題 2: after_step の narrower fix（全面降格は不採用）

- **上流 step 未検出** → 下流を FAIL させず **detected + `order_status="unevaluable"` 警告**（カスケード消滅）
- **上流 step 検出済みで実際の順序違反** → 従来どおり FAIL（真の順序強制は維持）

不採用の代替案:
- *after_step も classified へフォールバック*: run 3 の実障害を直せない（classify_task_type は classified にもゼロ件）。かつ順序検査を通っていない timestamp を基準にするミニカスケードを再生産。
- *順序を完全に別次元化（提案候補の「降格」案）*: カスケードは消えるが TDD の impl-first のような真の違反まで満点になり、compliance の中核シグナルを失う。diff もスコアモデル全域に及ぶ。

重要な性質: unevaluable で detected になった step は `resolved` に入るので、さらに下流の順序検査は実 timestamp で正しく再開される（チェーン全体が unevaluable 化しない）。テストで固定する。

### 問題 3: spec の保存 + `--spec` 再利用

`generate_spec(..., save_to: Path | None = None)` を追加し、**生成された raw YAML をそのまま永続化**（シリアライザ自作不要。save_to があれば tempfile でなく最終保存先に直接書いて parse、parse 失敗時もデバッグ用に残る）。`run.py` は生成時に `results/<name>.spec.yaml` へ自動保存し、`--spec <path>` で読込（`parse_spec` 使用、LLM 生成をスキップ）。

- `results/*.md` のみ gitignore 済みなので spec YAML は追跡可能のまま = 試験問題の version 管理という目的に合致。
- **scenario の非決定性は今回スコープ外**（deferred）。SKILL.md に「run 間比較は spec 固定まで、scenario の変動は残る」と明記。

## 事前検証で確定した挙動（fixture トレース済み）

既存テスト 57 本のうち**書き換えが必要なものは無い**。カスケード前提と見えた 2 本は実際には別機構で落ちている:
- `test_write_test_fails_ordering` — before_step の真の順序違反（改修後も FAIL 維持）
- `test_run_test_red_not_detected` — 候補ゼロ（presence 欠如。改修後も FAIL 維持）

flip するのは noncompliant fixture の `write_impl` / `run_test_green`（rate 0% → 50%、threshold 0.6 未満なので `test_hook_promotion_recommended` も保持）。この 2 本には失敗理由の assert を**追加**して意味をピン留めする（書き換えではない）。

## ファイル別変更（すべて ~/.claude/skills/skill-comply/ 配下）

| ファイル | 変更 |
|---|---|
| `scripts/grader.py` | `StepResult` に `order_status: str = "ok"`（ok/unevaluable/violated）と `order_note: str \| None = None` を追加。`_check_temporal_order` を `-> tuple[str, str \| None]` に変更（after_step 未 resolved → unevaluable note、resolved 済み違反 → violated 即 return、violation 優先）。`grade` ループで violated のみ skip、unevaluable は matched + resolved 登録 |
| `prompts/classifier.md` | line 3・23 を multi-label 許可 + 単独充足限定の文言に変更、line 15 example を同一 index が複数 step に現れる形に差替、Text セクションに複数 detector 充足時の列挙 bullet 追加 |
| `scripts/report.py` | timeline 逆引きを `dict[int, list[str]]` + `", ".join` に。Detail 表に Order 列追加（Reason は `failure_reason or order_note or "—"`） |
| `scripts/spec_generator.py` | `generate_spec` に `save_to: Path \| None = None` 追加。save_to 指定時は最終保存先に直接書き、unlink は tempfile 経路のみ |
| `scripts/run.py` | `--spec` 引数追加、`skill_name` 算出を Step 1 前へ移動、`spec = parse_spec(args.spec) if args.spec else generate_spec(..., save_to=results_dir/f"{skill_name}.spec.yaml")`。読込時は `spec.source_rule` を print（別 skill の spec 誤指定の可視化） |
| `SKILL.md` | `--spec` の使い方（自動保存 → 再利用）と scenario 非決定性の注記を追記（Doc Sync、同 diff） |

## テスト計画（TDD: 先に RED を確認してから実装）

新規 in `tests/test_grader.py`（`@patch("scripts.grader.classify_events")` の既存 mock パターン踏襲）:
1. `test_write_impl_detected_with_unevaluable_order` — semantic flip の固定（旧実装で RED）
2. `test_after_step_unevaluable_does_not_cascade` — run 3 再現。unevaluable step が resolved に入り下流検査が実 timestamp で再開されること + rate 0.75（旧実装で RED）
3. `test_true_order_violation_still_fails_after_fix` — 真の違反は FAIL 維持
4. `test_violating_candidate_skipped_ok_candidate_matches` — 違反候補 skip 後の成立
5. `test_order_status_ok_on_compliant` — compliant で全 step ok / note None
6. `test_multi_label_event_counts_for_both_steps` — 同一 index 2 step で両方 detected

既存 2 本に failure_reason の assert 追加 + docstring 更新（上述）。

新規 `tests/test_report.py`: 多重ラベルの join 表示 / Order 列 + note の出力。
新規 `tests/test_spec_generator.py`: `subprocess.run` を patch し、save_to でファイルが残り `parse_spec` で再読込可能なこと / save_to 省略時に tempfile が残らないこと。

## 実装順序

1. `test_grader.py` 新規 6 本 + 既存 2 本の assert 強化 → RED 確認（1, 2 が旧実装で fail すること）
2. `grader.py` 改修 → GREEN
3. `report.py` 改修 + `test_report.py` 新設 → GREEN
4. `prompts/classifier.md` 改修
5. `spec_generator.py` + `test_spec_generator.py` → `run.py` → `SKILL.md`
6. Review（並列）: **python-reviewer** + **codex-review**（diff ベース、実装後に起動）
7. Verify: `cd ~/.claude/skills/skill-comply && uv run pytest`（既存 57 + 新規 ~10 全 PASS）、ruff、secret scan、依存変更なしのため pip-audit 省略、doc sync（SKILL.md 同 diff）、`git status`（**human-gate.md / harness-sync SKILL.md の未コミット差分は別作業 — stage しない**）
8. **再測定（1 回）**: `uv run python -m scripts.run --allow-bash ~/.claude/skills/implementation-chain/SKILL.md` — 確認点: (a) supportive の高スコア化、(b) timeline の多重ラベル join、(c) unevaluable が FAIL でなく警告表示、(d) `results/implementation-chain.spec.yaml` 保存。続けて `--spec` 読込パスの dry-run smoke
9. 意図確認 gate（介入点 2）: **grader.py / classifier.md / テストは「検査の証拠を作るもの」なので本文（該当 diff）を提示**（human-gate.md）。再測定結果を添える。commit は承認後、1 Bash call = 1 git コマンド・`git -C` で、TASKS.md の T-011 → Done 更新も同一決裁に含める

## リスクと注意点

- **multi-label 化の過大評価リスク**（最重要）: 限定文言 + 順序検査 + timeline 全ラベル表示（監査可能性向上）で緩和。再測定で neutral / competing が不自然に跳ねないか目視確認
- **unevaluable-pass のスコアジャンプ**: 上流 1 欠落時に旧 ~0% → (N-1)/N。意図した修正そのものだが、Order 列表示が読者への必須の手当て
- **classifier prompt はユニットテスト不能**: 検証は再測定 1 回の timeline 目視に依存
- **spec 上書き**: 生成 run のたびに `results/<name>.spec.yaml` が上書き。比較したい spec は別名コピー運用（SKILL.md に注記）
- **--spec の整合性検証なし**: `source_rule` print で可視化のみ（バリデーションはスコープ外）

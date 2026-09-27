# skill-creator をその場で縮退し、作成時に発火させる

## Context

発端は NVIDIA SkillEvaluator の検討（2026-08-22、見送り。memory `reference_skillevaluator_pilot`）。残った論点は
「skill を作るとき、作成時の判断が手順として無く、品質を fresh context で判定する gate も無い」こと。

- `skill-creator`（anthropics/skills-customized）は工程の半分が description 最適化 loop（自発トリガー 40% 上限は
  ADR-0013/0018/0026 で実測済み、発火測定の計器は定数 0 の既往 — memory `reference_skill_creator_loop_gotchas`）、
  計器は人力（通知→timing.json→HTML viewer→feedback.json）、旧世代向け逐条手順。invoke 11 回 / 67 日、直近 6 日未使用
- 著者の運用は「作って」と明示指示。しかし **skill-creator はその時ほとんど発火しない**（著者観測）
- 作成時の判断（abstraction trap / 40% 上限 → user-invocable 既定 / redundant channel / 隣接 skill 境界）は memory に散り、
  skill 化されていない（rules/README: 手順は skill が持つ）

新規 skill-writer + skill-judge 案は Codex（premise-hole）と architect（Build smaller）が独立に棄却:
台帳 T-002（skill 本数を減らす方針）と衝突、T-SKILL-CREATOR-EVAL-NATIVE が `claude plugin eval` を既に毎週 probe 中、
静的 evidence script は Tier 1 が昨日 48 skill で真の欠陥 0 を出した同クラス、fresh-context 判定は skill-stocktake Phase 2 が既に持つ。
→ **その場で縮退 + 発火配線**（著者決定 2026-08-22）。

Codex finding の採否: P1 with/without 既存 → 採る（subagent 2 arm の記述は残す、viewer/集計は削る）/ P3 checklist 共有は
parity 偽装 → 採る（正本は stocktake、creator は参照）/ P4 残す価値の過小評価 → 一部採る（intent 確認は残す、packaging は
harness-sync）/ P5 writer は判断する → 採る（看板を下ろす）/ MISSING judge の trust boundary → 採る（judge subagent は Bash なし）/
ALTERNATIVE → 採用。

## 変更

### 1. `skills/skill-creator/SKILL.md` 全面書き直し（名前維持、目安 100 行以下）

frontmatter: `origin: shimo4228`、`replaces: "skill-creator (origin: anthropics/skills-customized, sha b9e19e6, rewritten 2026-08-22)"`、
`user-invocable: true`。description は発話例（「skill 作って」「この手順を skill にして」「agent 定義を書いて」）+ NOT for
（棚卸し → skill-stocktake、遵守率 → skill-comply、構造債 → skill-health、公開 → harness-sync）。

本文の節:
1. **入口（intent 確認 ⏸ 著者）** — 用途・発話例・NOT for 相手・置き場を 1 packet に固定。隣接 skill を name/description で
   library 全体 grep し、新規 / 既存へ統合 / 既存改修のどれかを決める（ここは判断。build-or-not だけ著者が持つ）
2. **作成時の判断（memory から昇格）** — abstraction trap（一般化しても次回の行動が変わるか）/ 40% 上限 → user-invocable 既定、
   自発発火を当てにしない / redundant channel（既存チャネルが運ぶ情報を複製しない）/ 二重定義禁止（重なる部分は参照）
3. **書き方（Fable 向け）** — 判断基準と罠を書く。逐条手順・反復強調・旧世代向け禁止列挙は書かない（generation-audit の
   4 観点: 意図 / 根拠 / 鮮度 / 失効条件）。frontmatter は rules/common/skills.md の origin 表。目安 100 行、超えたら references/
4. **草稿ゲート（fresh context、1 回）** — general-purpose subagent 1 体、tools は Read/Grep/Glob（Bash なし — 候補本文は
   untrusted）。渡すのは skill-stocktake Phase 2 の 4 問（Actionability / Scope fit / Uniqueness = library 全体 / Currency =
   名指し資産の無条件検証）+ generation fit + trigger realism。出力は Publishable / Fix / Drop の named verdict、集計しない
   （skill: llm-as-judge）。Fix → span 修正 → 同一質問で再判定 1 回。上限 2 ラウンド。質問の正本は skill-stocktake、ここは参照
5. **行動 gate（任意）** — with/without を subagent 2 arm で同時に走らせ、両出力を著者が読む。差が無ければ Drop。
   `claude plugin eval --ablation with-without` が有効化されたら置換（T-SKILL-CREATOR-EVAL-NATIVE）
6. **配線** — `harness_lint.py`、`python -m scripts.scan_refs`（skill-health）で dangling 0。rules の wiring 追記要否。harness-sync
7. **⏸ 著者通読 GO** — ゲート通過後に著者が見つけた指摘数を記録（KPI。3 回連続で平均 ≥2 なら fresh judge agent を Build）

削除: `scripts/`（1,942 行: run_eval / run_loop / improve_description = description loop、aggregate_benchmark / generate_report =
集計、package_skill = harness-sync が担う、quick_validate = harness_lint が担う）、`agents/`（grader / analyzer / comparator）、
`eval-viewer/`、`assets/eval_review.html`、`references/schemas.md`、`LICENSE.txt`。**残す**: `references/portability.md`
（harness-boundary:107 が参照）。

### 2. 発火配線（rule 命令形 + 決定論 hook）

- `rules/common/skills.md:20` を命令形に: 「skill / agent を新規作成・大幅改修するときは**先に** skill: `skill-creator` を読む。
  配置・公開は `harness-sync`」（ADR-0018:83 の fallback「立たない場合はポインタを命令形にする」をそのまま適用）
- `hooks/skill-create-notice.sh`（PreToolUse `Edit|Write`、review-chain-notice.sh と同型の薄い hook）: `tool_input.file_path` が
  `~/.claude/skills/<name>/SKILL.md` または `~/.claude/agents/<name>.md` で**ファイルが未存在**のとき、`_advisory-common.sh` の
  `emit_advisory PreToolUse` で「skill: skill-creator の入口と草稿ゲートを通しましたか」を出す。既存ファイルの編集では沈黙（騒音回避）。
  `settings.json` の `PreToolUse` `Edit|Write` に 1 行追加（docs-prewrite.sh の隣）。約 20 行: `jq` で file_path →
  `realpath -m` で `/private` と `..` を正規化 → case で `$HOME/.claude/skills/*/SKILL.md | $HOME/.claude/agents/*.md` →
  `[[ -e ]]` なら沈黙 → `emit_advisory`。判定は持たない（usage log で「読んだか」を判定しない、改修の diff 閾値も持たない）。
  `tests/skill-create-notice.bats`（新規 SKILL.md → 発火 / 既存 → 沈黙 / project-local `.claude/skills/` → 沈黙 /
  `../` 経由 → 正規化後に判定 / 封筒は advisory-envelope.bats の形）。既知の穴: `cat >` での作成は素通り
  （validate-bash.sh への追加は 30 日の発火実績を見て判断）

### 3. 参照の意味修正（名前は変わらないので rename は 0 箇所）

- `skills/skill-health/SKILL.md:145-147` — Validation 定義「no skill-creator benchmark」→「skill-creator の草稿ゲート記録が無い」
- `skills/learn-eval/SKILL.md:141` — 「description optimization and evals」の文言を草稿ゲートに
- `skills/skill-stocktake/SKILL.md:130-141` に「この 4 問は skill-creator の草稿ゲートも参照する（正本はここ）」を 1 行
- `skills/llm-as-judge/SKILL.md` Related に skill-creator 草稿ゲート（N=1、fresh）を 1 行
- `.notes/TASKS.md` T-SKILL-CREATOR-EVAL-NATIVE に「eval 足場は 2026-08-22 に死亡計器として削除、再開時の判断は縮退 vs 新設」を追記
- memory: `reference_skill_creator_loop_gotchas` に「loop 自体を 2026-08-22 退役」、`feedback_abstraction_trap` /
  `feedback_autonomous_trigger_ceiling` に「昇格済 → skill: skill-creator」を追記（feedback_git_dash_c_over_cd の先例）

### 4. ADR 1 本（adr-writer に packet を渡す）

Context = 40% 上限 + 死亡計器 + native plugin eval が eval 枠を占有 + 発火しない / Decision = その場で縮退・名前維持・
origin 反転・rule 命令形 + hook で発火 / Alternatives = skill-writer+skill-judge（T-002 衝突、evidence 層の実測 yield 0、
checklist 二重化）、SkillEvaluator（見送り済）、現状維持 / Review-when = `claude plugin eval` が単体 skill で有効化 /
通読指摘数が 3 回連続で平均 ≥2 / hook が 30 日で 1 回も発火しない（配線の失効）。

## 捨てた案

- skill-writer + skill-judge 新設 — 上記
- NVIDIA SkillEvaluator — Tier 1 真の欠陥 0、Tier 3 API key 必須
- skill-creator 現状維持で description loop だけ削る — 残りも旧世代向けで発火しない問題が残る

## 実装順（Opus 新セッション向け。単一 commit でなく 3 commit）

1. hook + settings + bats + rule 命令形（発火配線）— 先に入れて、2 の SKILL.md 作成時に自分で発火することを確認
2. SKILL.md 書き直し + 削除 + 参照修正 + memory
3. ADR + TASKS 追記

## Verification

- `bats tests/skill-create-notice.bats tests/advisory-envelope.bats`、`python3 scripts/harness_lint.py`
- `uv run --directory ~/.claude/skills/skill-health python -m scripts.scan_refs ~/.claude/skills --json` → dangling 0
- self-hosting: 書き直した SKILL.md を自身の草稿ゲート（fresh subagent、Bash なし）に掛け Publishable
- 新規 `skills/zz-probe/SKILL.md` を Write しようとして advisory が出ること（その後削除）
- `grep -rn 'run_loop\|aggregate_benchmark\|eval-viewer' skills/ agents/ rules/` → 0
- implementation-chain の Review 群（code-review + security-reviewer: hook は repo 由来 path を受ける）

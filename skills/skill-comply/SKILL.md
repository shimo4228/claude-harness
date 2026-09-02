---
name: skill-comply
description: Visualize whether skills, rules, and agent definitions are actually followed — auto-generates scenarios at 3 prompt strictness levels, runs agents, classifies behavioral sequences, and reports compliance rates with full tool call timelines
compatibility: Requires Python 3.11+ and uv. Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
origin: shimo4228
tools: Read, Bash
---

# skill-comply: Automated Compliance Measurement

Measures whether coding agents actually follow skills, rules, or agent definitions by:
1. Auto-generating expected behavioral sequences (specs) from any .md file
2. Auto-generating scenarios with decreasing prompt strictness (supportive → neutral → competing)
3. Running `claude -p` and capturing tool call traces via stream-json
4. Classifying tool calls against spec steps using LLM (not regex)
5. Checking temporal ordering deterministically
6. Generating self-contained reports with spec, prompts, and timelines

## Supported Targets

- **Skills** (`skills/*/SKILL.md`): Workflow skills like search-first, TDD guides
- **Rules** (`rules/common/*.md`): Mandatory rules like testing.md, security.md, debugging.md
- **Agent definitions** (`agents/*.md`): Whether an agent gets invoked when expected (internal workflow verification not yet supported)

## When to Activate

- User runs `/skill-comply <path>`
- User asks "is this rule actually being followed?"
- After adding new rules/skills, to verify agent compliance
- Periodically as part of quality maintenance

## Usage

```bash
# 前提: scripts/ と pyproject.toml はこのスキルのディレクトリにあり、
# `python -m scripts.run` の解決は cwd 依存のため、まずスキルディレクトリへ cd する
# （`uv run --project` だけでは module 解決できないことを 2026-07-13 に実測確認）
cd ~/.claude/skills/skill-comply

# Full run
uv run python -m scripts.run ~/.claude/rules/common/testing.md

# Dry run (no cost, spec + scenarios only)
uv run python -m scripts.run --dry-run ~/.claude/skills/search-first/SKILL.md

# Custom models
uv run python -m scripts.run --gen-model haiku --model sonnet --classifier-model sonnet <path>

# 直列に戻す（レートリミットに当たったとき）
uv run python -m scripts.run --concurrency 1 <path>

# Bash を要する spec のみ (既定は off — 下の「信頼境界」を読んでから)
uv run python -m scripts.run --allow-bash <path>

# 保存済み spec を再利用して run 間比較 (LLM 再生成をスキップ)
uv run python -m scripts.run --spec results/<skill-name>.spec.yaml <path>
```

**spec の固定と run 間比較**: spec は「試験問題」。LLM 生成のたびに required steps 数も
順序制約も変わるため、生成された spec は自動で `results/<skill-name>.spec.yaml` に保存される
（gitignore 対象外 — version 管理できる）。同じ skill を再測定するときは `--spec` でこれを
読み込むと問題文が固定され、スコアが比較可能になる。次回の生成 run は同名ファイルを
上書きするので、比較対象として残したい spec は別名でコピーしておく。
なお scenario prompt は引き続き毎回 LLM 生成で変動する — run 間比較の固定は spec までで、
scenario の非決定性は現状スコープ外。

## 実行時間と進捗の見かた

3 つのシナリオは互いに独立（別プロンプト・別 sandbox・別プロセス）なので、
既定で 3 本同時に走る。待ち時間は 3 本の合計ではなく**いちばん遅い 1 本**になる。
分類（採点）もシナリオごとなので一緒に並ぶ。spec 生成 → シナリオ生成の 2 段は
前段の出力を次段が使うため直列のまま。

並列化してもスコアとレポートは変わらない。完了順は進捗表示にしか使わず、
レポートは必ず supportive → neutral → competing の順に組み立てる。
`--concurrency 1` で完全に直列へ戻せる。

**進捗は stderr、結果は stdout に出る。** これは事故ではなく分担で、
2026-08-01 の実測にもとづく（→ [ADR-0029](../../docs/adr/0029-skill-comply-parallel-scenarios-and-stderr-progress.md)）:

```bash
# 進捗が見える。stdout だけが tail に入り、stderr は端末へ直接届く
uv run python -m scripts.run <path> | tail -40

# 進捗もログに残したい
uv run python -m scripts.run <path> 2>&1 | tee run.log
```

**`2>&1 | tail -40` にすると何も見えなくなる。** `tail` は `-f` なしだと
「最後の N 行」を出す道具で、入力が終わるまで 1 行も出せない。
これは `tail` の性質なので、`python -u` でも flush でも直らない。
途中経過を見たいときは `tail` でなく `tee` を使う。

シナリオが 1 本でも失敗したとき（子プロセスの異常終了など）は、
そのシナリオを 0% として数えず「測定失敗」として stderr に出し、終了コード 1 を返す。
残りのシナリオのレポートは通常どおり保存される。

## 測定対象の種別と、測れるもの

対象がどこにあるかで、子から見えるかどうかが変わる。**見えないまま測ると、
skill 遵守ではなく「skill を持たないエージェントの素の挙動」を測ることになる。**
2026-08-02 まではそれが黙って起きていた（実例: project skill の run で
`Skill(...)` → `Unknown skill` のまま 75% / 50% / 25% が出ていた）。

| 対象 | 子から見えるか | 測定 |
|---|---|---|
| global skill（`~/.claude/skills/`） | 見える | そのまま測れる |
| project skill（repo の `.claude/skills/`） | **見えない** | sandbox に配置してから測る（下記の 2 層） |
| rule / agent 定義 / 素の .md | skill ではない | `Skill` 呼び出しは期待しない |

project skill は 2 層で測る。**どちらで測ったかはレポートの Summary に必ず出る** —
Tier 1 の 75% と Tier 2 の 75% は別物なので、混同できないようにする。

- **Tier 1（既定、flag 不要）** — frontmatter の `name` と `description` だけ本物で、
  本文は無害な stub を置く。**「skill に手を伸ばしたか」を測る。**
  発見と起動は `name` / `description` で決まり本文は関与しないので、これで足りる
- **Tier 2（`--load-target-skill`）** — 本物の本文を置く。**「手順に従うか」を測る。**
  監査対象の本文が無人の子への**指示**になるので opt-in。`SKILL.md` 1 ファイルのみを
  写し、ディレクトリは写さない（`references/` を持つ skill は Tier 2 で短く測れる —
  黙った穴より、見える制限を選ぶ）

**Tier 1 は測定の正しさのための層であって、封じ込めの層ではない。** 存在理由は
「project skill を発見可能にして、素の挙動でなく遵守を測れるようにする」こと。

`description` は発見に必要なので必ず子に届く。上限 500 文字は**分量の上限であって
能力の上限ではない** — 500 文字は指示文として十分すぎる長さで、Read / Write / Edit /
Glob / Grep を持つ子に有効な命令を書ける。Tier 1 と Tier 2 の差は
**「手順が届かない」**であって**「指示が届かない」**ではない。

`--load-target-skill` と `--allow-bash` の併用は、**untrusted な文書に payload と
インタープリタの両方を渡す**組み合わせなので警告が出る。

## 信頼境界 — 監査対象ファイルは untrusted

**このツールは、あなたが書いたとは限らない .md を読んで LLM にシナリオを書かせ、
それを別のエージェントに実行させる。** 監査対象がそのまま生成器への入力になるので、
対象ファイルの本文は untrusted data として扱う（2026-07-25 security scan F2/F3/F4/F18）。

- **`setup_commands` は実行されない。** `mkdir` / `touch` の 2 語彙だけを pathlib で
  解釈し、パスは sandbox 内に解決されることを検証する。それ以外は拒否して stderr に
  出す。以前は `shlex.split` + `subprocess` だったため、community 由来スキル 1 本で
  ホスト上の任意コマンド実行になっていた
- **パス検証は `..` を先に潰してから symlink を解決する。** 2026-08-01 まで、存在しない
  要素の後ろに置かれた `..`（`a/../../elsewhere/x`）が解決されずに残り、`Path.parents` が
  それをただのディレクトリ名として扱って sandbox 外への作成を通していた。
  sandbox は直前に消して作り直されるので最初の要素は必ず存在せず、抜け道は常に開いていた
- **子のツールは `permissions.deny` で外す。`--allowedTools` では外れない。**
  `claude --help` の言うとおり `--allowedTools` は「allow するツール名の列」＝自動承認
  リストであって、載せなかったツールは**消えない**。2026-08-02 に Claude Code 2.1.220 で
  実測: `--allowedTools "Read,Glob,Grep"` だけの子が Bash を呼び、`uname -sr` が
  ホスト上で実行された。`--permission-mode`（manual / dontAsk / acceptEdits）でも
  `--setting-sources project` でも変わらない。
  `--settings` の `permissions.deny` で `Bash` / `Agent` / `Workflow` /
  `ToolSearch` / `ScheduleWakeup` を外す（正本: `scripts/child_settings.py`）。
  Bash 以外も外すのは、`Agent` と `Workflow` が**このコードが制御しないツール集合を持つ
  サブエージェント**を生み、`ToolSearch` が user 設定から継承した MCP の面
  （メール・ドライブ・カレンダー・ブラウザ）を必要に応じて読み込むため。
  `--allow-bash` は deny から Bash を**外す**形で効く
- `cwd` と `--add-dir` はアクセスを**広げる**もので、閉じ込めない
- **生成器プロンプトでは対象文書を nonce 区切りで隔離**し、data であって指示ではないと
  明示している。固定区切り（`---`）は markdown frontmatter が再現できてしまう
- **sandbox は 1 シナリオ 1 個、かつ 1 実行 1 根**。ディレクトリ名は LLM が生成した
  scenario id に由来するので、重複していたら実行前に検出して別名にする。直列なら重複は
  無害だが、並列では片方の sandbox 作成（作る前に消す）が走行中のもう片方を消してしまう。
  この一意化は**プロセス内でしか効かない**ので、根を実行単位で分ける —
  `/tmp/skill-comply-sandbox/run-<pid>/<id>`。同じ id を生成した別の run が
  互いの走行中 sandbox を消さない（2026-08-17、`scripts/runner.py: sandbox_run_root`）。
  `SANDBOX_BASE` 自体が symlink（共有ホスト・CI の scratch 領域）のときは根の計算で
  1 回だけ解決して追従する — 封じ込め判定を毎回 link 越しにやり直さない
- **`<sandbox>/.claude/` と `<sandbox>/.git/` はツール専有。監査対象由来の指定は受け付けない。**
  sandbox は子にとっての**プロジェクトルート**で、そこでは一部のファイル名が
  「置いてあるだけ」ではなく読み込まれる。実測（2026-08-02）: 一度も信頼していない
  workspace でも `<sandbox>/.claude/settings.json` の `hooks.SessionStart` は
  **無言でホスト上のコマンドを実行した**（同じファイルの `permissions.allow` は
  「信頼されていない」と明示的に拒否されるのに）。`<sandbox>/CLAUDE.md` も読まれて従われる。
  子自身の Write は substrate が止めるが、**このツールの pathlib 書き込みは止まらない**ので
  ここで塞ぐ。`CLAUDE.md` / `AGENTS.md` / `.mcp.json` / `settings.json` /
  `settings.local.json` / `.gitignore` は深さを問わず拒否。
  **判定は case-fold する** — APFS は case-insensitive なので `.CLAUDE/Settings.json` は
  書けてしまえば `.claude/settings.json` として読まれる（2026-08-02 にすり抜けを実測して修正）。
  `.git/` を含めるのは、`_setup_sandbox` が `git init` を先に走らせるので書き込み可能で、
  `core.fsmonitor` / `core.pager` / `alias.*` が**実行ビット無しで git が実行する設定文字列**
  だから（実測: `files:` で `.git/config` を置き、`git status` でホスト上のコマンドが走った。
  Claude Code は workspace で git を実行するので、子の Bash を塞いでいても発火する）。
  `.gitignore` は実行ではなく**測定の破壊** — Grep は従い Glob は従わないので、文書が
  自分のフィクスチャを detector の期待するツールから隠せる。
  **閉じ込められていることと不活性であることは別の性質**で、`_contained` が答えるのは前者だけ

信頼できない .md を測るときは `--dry-run` で生成されたシナリオを先に読むこと。
`--dry-run` は spec の step に加えて、**攻撃者が制御しうる 3 つのフィールドを全文出す** —
無人の子に渡される `prompt`、ファイルシステムを触る `setup_commands` と `files:`。

## Models

| Stage | Default | Why |
|-------|---------|-----|
| `--gen-model` | `haiku` | Spec / scenario generation. Short prompts, fast. |
| `--model` | `sonnet` | Scenario execution (the agent under test). `haiku` / `sonnet` / `opus` / `fable` を指定可。 |
| `--classifier-model` | `sonnet` | Trace classification. Haiku times out on long traces (50+ events) and abstract specs (e.g. contemplative-axioms). Sonnet handles the load with a 300s timeout. |

## Key Concept: Prompt Independence

Measures whether a skill/rule is followed even when the prompt doesn't explicitly support it.

## Report Contents

Reports are self-contained and include:
1. Expected behavioral sequence (auto-generated spec)
2. Scenario prompts (what was asked at each strictness level)
3. Compliance scores per scenario
4. Tool call timelines with LLM classification labels

### Advanced (optional)

For users familiar with hooks, reports also include hook promotion recommendations for steps with low compliance. This is informational — the main value is the compliance visibility itself.

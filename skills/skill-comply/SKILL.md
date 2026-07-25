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
- **Rules** (`rules/common/*.md`): Mandatory rules like testing.md, security.md, git-workflow.md
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

# Bash を要する spec のみ (既定は off — 下の「信頼境界」を読んでから)
uv run python -m scripts.run --allow-bash <path>
```

## 信頼境界 — 監査対象ファイルは untrusted

**このツールは、あなたが書いたとは限らない .md を読んで LLM にシナリオを書かせ、
それを別のエージェントに実行させる。** 監査対象がそのまま生成器への入力になるので、
対象ファイルの本文は untrusted data として扱う（2026-07-25 security scan F2/F3/F4/F18）。

- **`setup_commands` は実行されない。** `mkdir` / `touch` の 2 語彙だけを pathlib で
  解釈し、パスは sandbox 内に解決されることを検証する。それ以外は拒否して stderr に
  出す。以前は `shlex.split` + `subprocess` だったため、community 由来スキル 1 本で
  ホスト上の任意コマンド実行になっていた
- **子エージェントの Bash は既定 off。** `--allowedTools` は `-p` モードでは
  「許可リスト + 自動承認」なので、Bash を渡すと対象ファイル経由で忍び込んだ指示が
  無人で実行される。`cwd` と `--add-dir` はアクセスを**広げる**もので、閉じ込めない。
  必要な spec（「テストを走らせたか」を測る類）でのみ `--allow-bash` を明示する
- **生成器プロンプトでは対象文書を nonce 区切りで隔離**し、data であって指示ではないと
  明示している。固定区切り（`---`）は markdown frontmatter が再現できてしまう

信頼できない .md を測るときは `--dry-run` で生成されたシナリオを先に読むこと。

## Models

| Stage | Default | Why |
|-------|---------|-----|
| `--gen-model` | `haiku` | Spec / scenario generation. Short prompts, fast. |
| `--model` | `sonnet` | Scenario execution (the agent under test). |
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

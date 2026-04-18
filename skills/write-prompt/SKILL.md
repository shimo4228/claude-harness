---
name: write-prompt
description: Generate concise LLM prompts using the Haiku-powered prompt-writer agent. Avoids Opus overthinking.
origin: shimo4228
---

# /write-prompt — Lightweight Prompt Generation

Haiku agent でプロンプトを生成する。Opus の「考えすぎ」を回避し、シンプルなプロンプトを得る。

## Trigger

- LLM プロンプトの新規作成・リライト
- 既存プロンプトが冗長で簡潔にしたいとき

## Workflow

1. ユーザーの入力を整理する（タスク説明、対象モデル、既存プロンプト、言語）
2. `prompt-writer` agent (Haiku) を起動
3. 生成結果をユーザーに提示
4. フィードバックがあれば指示を添えて再生成

## Usage

```
/write-prompt [タスクの説明]
```

### Examples

```
/write-prompt 記事の要約を生成するプロンプト、対象モデルはSonnet
/write-prompt config/prompts/distill.md をリライトして簡潔にしたい
```

## Agent Invocation

```
Agent(subagent_type="prompt-writer", prompt="
  Task: [タスク説明]
  Target model: [対象モデル]
  Existing prompt: [既存プロンプトの内容（あれば）]
  Language: [出力言語]
")
```

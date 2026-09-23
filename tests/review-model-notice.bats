#!/usr/bin/env bats
# review-model-notice.sh — judge-tier (Fable) セッションでの review 直呼びに advisory を出す

# hook 本体は BATS_TEST_DIRNAME から引く — 理由は verify-toolchain-trust.bats の
# ヘッダに 1 回だけ書いてある（worktree ごとに内容が違う検査対象を、$HOME 固定だと
# 「今チェックアウトしている版」でなく main の版で検査してしまう）。
HOOK="${BATS_TEST_DIRNAME}/../hooks/review-model-notice.sh"

setup() {
  TDIR="$(mktemp -d)"
  FABLE_T="$TDIR/fable.jsonl"
  OPUS_T="$TDIR/opus.jsonl"
  printf '{"type":"assistant","message":{"model":"claude-fable-5"}}\n' > "$FABLE_T"
  printf '{"type":"assistant","message":{"model":"claude-opus-5"}}\n' > "$OPUS_T"
}

teardown() { rm -rf "$TDIR"; }

run_hook() { # $1=payload $2=transcript
  REVIEW_MODEL_TRANSCRIPT="$2" run bash "$HOOK" <<< "$1"
}

# subagent 自身の transcript の実機での置き場所
# (<transcript_path から .jsonl を除いた dir>/subagents/agent-<agent_id>.jsonl)。
sub_transcript() { # $1=agent id $2=中身を写す transcript
  mkdir -p "$TDIR/fable/subagents"
  cp "$2" "$TDIR/fable/subagents/agent-$1.jsonl"
}

@test "Skill code-review on fable -> block (before execution)" {
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"}}' "$FABLE_T"
  [ "$status" -eq 0 ] || return 1
  [[ "$output" == *'"decision":"block"'* ]] || return 1
  [[ "$output" == *"Review の実行モデル pin"* ]]
}

@test "Skill simplify on fable -> block" {
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"simplify"}}' "$FABLE_T"
  [[ "$output" == *'"decision":"block"'* ]]
}

@test "Skill code-review on opus -> silent" {
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"}}' "$OPUS_T"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "Skill codex-review on fable -> silent (codex is not code)" {
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"codex-review"}}' "$FABLE_T"
  [ -z "$output" ]
}

@test "Agent with model opus running code-review -> silent (pinned path)" {
  run_hook '{"tool_name":"Agent","tool_input":{"model":"opus","prompt":"run skill code-review on the diff"}}' "$FABLE_T"
  [ -z "$output" ]
}

@test "Agent without model running code-review on fable -> advisory, not block (heuristic match)" {
  run_hook '{"tool_name":"Agent","tool_input":{"prompt":"run skill code-review on the diff"}}' "$FABLE_T"
  [[ "$output" == *additionalContext* ]] || return 1
  [[ "$output" != *'"decision"'* ]]
}

@test "Task without model, prompt mentions simplify -> advisory" {
  run_hook '{"tool_name":"Task","tool_input":{"prompt":"apply /simplify to changed files"}}' "$FABLE_T"
  [[ "$output" == *additionalContext* ]]
}

@test "Agent prompt unrelated to review -> silent" {
  run_hook '{"tool_name":"Agent","tool_input":{"prompt":"summarize the README"}}' "$FABLE_T"
  [ -z "$output" ]
}

@test "TaskStop unanchored matcher hit -> silent" {
  run_hook '{"tool_name":"TaskStop","tool_input":{"note":"code-review"}}' "$FABLE_T"
  [ -z "$output" ]
}

@test "missing transcript -> silent (no evidence, no advisory)" {
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"}}' "$TDIR/missing.jsonl"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "transcript switched fable to opus -> silent (last line wins)" {
  cat "$FABLE_T" "$OPUS_T" > "$TDIR/switched.jsonl"
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"}}' "$TDIR/switched.jsonl"
  [ -z "$output" ]
}

@test "malformed payload -> silent exit 0" {
  run_hook 'not json but mentions code-review' "$FABLE_T"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# --- subagent 内での発火。payload の transcript_path は親のものなので、agent_id が
# --- あるときは subagent 自身の transcript を読む（skill implementation-chain
# --- 「Review の実行モデル pin」が指示する経路を hook 自身が塞がないため）。

@test "opus subagent under a fable parent -> silent (its own transcript decides)" {
  sub_transcript a5ab65e78cf3e6b6e "$OPUS_T"
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"},"agent_id":"a5ab65e78cf3e6b6e"}' "$FABLE_T"
  [ "$status" -eq 0 ] || return 1
  [ -z "$output" ]
}

@test "fable subagent under a fable parent -> block" {
  sub_transcript a5ab65e78cf3e6b6e "$FABLE_T"
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"},"agent_id":"a5ab65e78cf3e6b6e"}' "$FABLE_T"
  [[ "$output" == *'"decision":"block"'* ]]
}

@test "agent_id but no subagent transcript -> silent (never falls back to the parent)" {
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"},"agent_id":"deadbeef"}' "$FABLE_T"
  [ "$status" -eq 0 ] || return 1
  [ -z "$output" ]
}

@test "agent_id with a traversal that would resolve to the parent -> silent (path not built)" {
  # 素朴な結合だと <TDIR>/fable/subagents/agent-x/../../../fable.jsonl = 親の transcript。
  mkdir -p "$TDIR/fable/subagents/agent-x"
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"},"agent_id":"x/../../../fable"}' "$FABLE_T"
  [ "$status" -eq 0 ] || return 1
  [ -z "$output" ]
}

@test "subagent transcript without a model field -> silent" {
  mkdir -p "$TDIR/fable/subagents"
  printf '{"type":"user","message":{"content":"hi"}}\n' > "$TDIR/fable/subagents/agent-nomodel.jsonl"
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"},"agent_id":"nomodel"}' "$FABLE_T"
  [ -z "$output" ]
}

@test "agent_id with a transcript_path of an unexpected shape -> silent" {
  cp "$FABLE_T" "$TDIR/fable.log"
  run_hook '{"tool_name":"Skill","tool_input":{"skill":"code-review"},"agent_id":"a5ab65e78cf3e6b6e"}' "$TDIR/fable.log"
  [ -z "$output" ]
}

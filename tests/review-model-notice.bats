#!/usr/bin/env bats
# review-model-notice.sh — judge-tier (Fable) セッションでの review 直呼びに advisory を出す

HOOK="$HOME/.claude/hooks/review-model-notice.sh"

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

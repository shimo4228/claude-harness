#!/usr/bin/env bats
# 薄い commit-time reminder の発火条件と固定文だけを検査する。ADR-0035。

HOOK="$HOME/.claude/hooks/review-chain-notice.sh"

fire() {
  printf '{"tool_input":{"command":%s}}' "$(jq -Rn --arg v "$1" '$v')" | bash "$HOOK"
}

ctx() {
  fire "$1" | jq -r '.hookSpecificOutput.additionalContext // empty'
}

@test "empty input and non-git commands are silent" {
  run bash "$HOOK" <<< '{}'
  [ "$status" -eq 0 ] || return 1
  [ -z "$output" ] || return 1
  [ -z "$(ctx "python app.py")" ]
}

@test "text that merely mentions git commit is silent" {
  [ -z "$(ctx 'echo git commit')" ] || return 1
  [ -z "$(ctx 'rg "git commit" README.md')" ]
}

@test "commit emits the implementation-chain reminder" {
  [[ "$(ctx "git commit -m x")" == *"Review と Verify"* ]] || return 1
  [[ "$(ctx "git commit -m x")" == *"skill: implementation-chain"* ]]
}

@test "quoted git -C commit still emits" {
  [[ "$(ctx 'git -C "/tmp/repo with spaces" commit -m x')" == *"implementation-chain"* ]]
}

@test "revert and merge emit" {
  [[ "$(ctx "git revert HEAD")" == *"implementation-chain"* ]] || return 1
  [[ "$(ctx "git merge topic")" == *"implementation-chain"* ]]
}

@test "git at the start of a later shell segment emits" {
  [[ "$(ctx "cd /tmp && git commit -m x")" == *"implementation-chain"* ]]
}

@test "gate bypass assignment before git still emits" {
  [[ "$(ctx "VERIFY_BYPASS=1 git commit -m x")" == *"implementation-chain"* ]]
}

@test "reminder contains no duplicated reviewer roster or repository data" {
  local out
  out="$(ctx "git commit -m x")"
  [[ "$out" != *"code-reviewer"* ]] || return 1
  [[ "$out" != *"security-reviewer"* ]] || return 1
  [[ "$out" != *"/tmp/"* ]]
}

@test "output is compact PreToolUse context" {
  local out
  out="$(fire "git commit -m x")"
  [ "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName')" = "PreToolUse" ] || return 1
  [ "$(printf '%s' "$out" | wc -c | tr -d ' ')" -le 250 ]
}

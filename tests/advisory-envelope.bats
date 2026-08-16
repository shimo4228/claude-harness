#!/usr/bin/env bats
# Tests for hooks/_advisory-common.sh — hook が model へ文字列を渡す封筒の唯一の実装。
#
# **封筒の形を主張しているのはこのファイルだけ。** 各 hook の bats には event 名 1 行
# だけを残す（形は共有できても、どの event を名乗るべきかは hook ごとに違う）。
# なぜ形の検査を 1 箇所に寄せるのか、その設計根拠は hooks/_advisory-common.sh の
# ヘッダが正本 — ここに複製しない。
#
# Run: bats ~/.claude/tests/advisory-envelope.bats

COMMON="$HOME/.claude/hooks/_advisory-common.sh"

setup() {
  # shellcheck source=hooks/_advisory-common.sh
  source "$COMMON"
}

@test "envelope nests additionalContext under hookSpecificOutput" {
  run emit_advisory PreToolUse "hello"
  [ "$status" -eq 0 ]
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" = "hello" ]
}

@test "envelope carries hookEventName alongside the context" {
  run emit_advisory PreToolUse "hello"
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.hookEventName')" = "PreToolUse" ]
}

@test "no top-level additionalContext (the shape that silently fails)" {
  # 2 度目に踏んだ間違い。トップレベルに置くと hook は exit 0、テストは通り、
  # 文字列だけが model に届かない。
  run emit_advisory PostToolUse "hello"
  [ "$(printf '%s' "$output" | jq -r 'has("additionalContext")')" = "false" ]
}

@test "event name is passed through verbatim for each wired event" {
  local e
  for e in PreToolUse PostToolUse UserPromptSubmit; do
    run emit_advisory "$e" "x"
    [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.hookEventName')" = "$e" ]
  done
}

@test "stream form reads the body from stdin" {
  run bash -c "source '$COMMON'; printf 'from stdin' | emit_advisory_stream PostToolUse"
  [ "$status" -eq 0 ]
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" = "from stdin" ]
}

@test "extra top-level JSON is merged beside the envelope, not inside it" {
  # systemMessage / decision / reason は別チャネルでトップレベルに置く。
  run emit_advisory PostToolUse "ctx" '{"systemMessage":"shown to user"}'
  [ "$(printf '%s' "$output" | jq -r '.systemMessage')" = "shown to user" ]
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" = "ctx" ]
}

@test "extra JSON cannot silently drop the envelope" {
  # 万一 extra 側が hookSpecificOutput を持っていても、封筒が後勝ちで残る。
  run emit_advisory PostToolUse "ctx" '{"hookSpecificOutput":{"hookEventName":"WRONG"}}'
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.hookEventName')" = "PostToolUse" ]
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" = "ctx" ]
}

@test "quotes, backslashes, newlines and tabs survive the round trip" {
  local body
  body=$(printf 'a "quoted" \\ back\nsecond\tline')
  run emit_advisory PreToolUse "$body"
  [ "$status" -eq 0 ]
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" = "$body" ]
}

@test "an empty body yields an empty string, not null" {
  # null が入ると消費側で「文字列が無い」と読まれる。空文字は「言うことが無い」。
  run emit_advisory PreToolUse ""
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext | type')" = "string" ]
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" = "" ]
}

@test "an empty event name fails loudly instead of emitting a broken envelope" {
  run emit_advisory "" "ctx"
  [ "$status" -ne 0 ]
  [[ "$output" != *"hookSpecificOutput"* ]] || return 1
}

@test "a body over the limit is truncated" {
  # 上限は封筒の性質であって呼び出し側の性質ではない — hook ごとに手書きすると、
  # 次に増える hook が封筒だけ継承して上限を継承しない。
  local ctx
  run emit_advisory PreToolUse "$(python3 -c 'print("Z"*5000)')"
  ctx=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')
  [ "${#ctx}" -lt 2100 ] || return 1
  [[ "$ctx" == *"切り詰め"* ]]
}

@test "a body under the limit is untouched" {
  run emit_advisory PreToolUse "short"
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" = "short" ]
}

@test "ADVISORY_MAX raises the limit for callers that need more" {
  local ctx
  run bash -c "source '$COMMON'; ADVISORY_MAX=4000; emit_advisory PreToolUse \"\$(python3 -c 'print(\"Z\"*3000)')\""
  ctx=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')
  [ "${#ctx}" -eq 3000 ]
}

@test "ADVISORY_TRUNC_HINT tells the reader how to get the full text" {
  local ctx
  run bash -c "source '$COMMON'; ADVISORY_TRUNC_HINT='全文は foo を実行'; emit_advisory PreToolUse \"\$(python3 -c 'print(\"Z\"*5000)')\""
  ctx=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')
  [[ "$ctx" == *"全文は foo を実行"* ]]
}

@test "a hostile ADVISORY_MAX cannot disable the cap" {
  # 環境変数は親プロセスから継承される。無検証だと null で「全文 + 切り詰めマーカー」
  # （マーカーを見る読み手を欺く）、"9" で無音の無効化、abc で advisory が丸ごと消える。
  local v len
  for v in null '"9"' 1e9 abc -1 999999 0; do
    run bash -c "source '$COMMON'; ADVISORY_MAX='$v' emit_advisory PreToolUse \"\$(python3 -c 'print(\"Z\"*5000)')\" 2>/dev/null"
    len=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext | length')
    [ "$len" -lt 2100 ] || return 1
  done
}

@test "ANSI escapes and control characters are stripped from the body" {
  # 端末制御列は model 向けの文脈では意味を持たず、表示を偽装する材料になる。
  local ctx
  run bash -c "source '$COMMON'; printf 'a\033[31mRED\033[0m b\001c\td' | emit_advisory_stream PostToolUse"
  ctx=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')
  [[ "$ctx" == *"RED"* ]] || return 1
  [[ "$ctx" == *"c	d"* ]] || return 1
  [[ "$ctx" != *"["* ]]
}

@test "a malformed extra is dropped instead of killing the envelope" {
  # --argjson に壊れた値を渡すと jq ごと落ち、hook が黙る（＝封筒を守るはずの引数が
  # 封筒を消す）。捨てて封筒だけ出す方が常に良い。
  run bash -c "source '$COMMON'; emit_advisory PostToolUse 'ctx' 'not json' 2>/dev/null"
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" = "ctx" ]
}

@test "a non-object extra (array) is dropped too" {
  run bash -c "source '$COMMON'; emit_advisory PostToolUse 'ctx' '[1,2]' 2>/dev/null"
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.hookEventName')" = "PostToolUse" ]
}

@test "output is a single JSON object" {
  # printf の手組みに戻ると壊れる不変条件。jq が読めれば object 1 つ。
  run emit_advisory PreToolUse "x"
  [ "$(printf '%s' "$output" | jq -s 'length')" = "1" ]
  [ "$(printf '%s' "$output" | jq -r 'type')" = "object" ]
}

#!/usr/bin/env bats
# Golden: hooks/_advisory-common.sh の封筒 JSON の**全バイト**を凍結する。
# 部分 assert（形の性質）は tests/advisory-envelope.bats。こちらが検知するのは
# 「性質テストは通るが、下流が読む正確な形が変わった」silent drift。
# 更新規約: tests/golden/README.md（タスクが出力変更を宣言しているときだけ更新）
#
# 再生成:
#   source hooks/_advisory-common.sh
#   emit_advisory PreToolUse "$(printf '本文 1 行目 "quoted" \\back\n2 行目\tタブ')" > tests/golden/advisory/basic.json
#   emit_advisory PostToolUse 'ctx' '{"systemMessage":"shown to user"}' > tests/golden/advisory/extra.json
#   ADVISORY_TRUNC_HINT='全文は verify.sh を実行' emit_advisory PreToolUse "$(python3 -c 'print("Z"*3000)')" > tests/golden/advisory/truncated.json
#
# Run: bats ~/.claude/tests/golden-advisory-envelope.bats

COMMON="${BATS_TEST_DIRNAME}/../hooks/_advisory-common.sh"
GOLDEN="${BATS_TEST_DIRNAME}/golden/advisory"

setup() {
  # shellcheck source=hooks/_advisory-common.sh
  source "$COMMON"
}

@test "golden: basic envelope (quotes, backslash, newline, tab, multibyte)" {
  run emit_advisory PreToolUse "$(printf '本文 1 行目 "quoted" \\back\n2 行目\tタブ')"
  [ "$status" -eq 0 ]
  printf '%s\n' "$output" | diff - "$GOLDEN/basic.json"
}

@test "golden: extra top-level JSON merged beside the envelope" {
  run emit_advisory PostToolUse 'ctx' '{"systemMessage":"shown to user"}'
  [ "$status" -eq 0 ]
  printf '%s\n' "$output" | diff - "$GOLDEN/extra.json"
}

@test "golden: truncation marker with hint (default ADVISORY_MAX=2048)" {
  run bash -c "source '$COMMON'; ADVISORY_TRUNC_HINT='全文は verify.sh を実行' emit_advisory PreToolUse \"\$(python3 -c 'print(\"Z\"*3000)')\""
  [ "$status" -eq 0 ]
  printf '%s\n' "$output" | diff - "$GOLDEN/truncated.json"
}

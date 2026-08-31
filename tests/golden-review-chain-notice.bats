#!/usr/bin/env bats
# Golden: hooks/review-chain-notice.sh の出力（封筒込み）の全バイトを凍結する。
# 発火条件・非発火の性質は tests/review-chain-notice.bats。こちらは commit 検知時に
# model へ届く正確な文言と封筒形の silent drift を検知する。
# 更新規約: tests/golden/README.md
#
# 再生成:
#   printf '%s' '{"tool_input":{"command":"git commit -m x"}}' | bash hooks/review-chain-notice.sh > tests/golden/review-chain-notice/commit.json
#
# Run: bats ~/.claude/tests/golden-review-chain-notice.bats

HOOK="${BATS_TEST_DIRNAME}/../hooks/review-chain-notice.sh"
GOLDEN="${BATS_TEST_DIRNAME}/golden/review-chain-notice"

@test "golden: git commit -> notice envelope" {
  run bash -c "printf '%s' '{\"tool_input\":{\"command\":\"git commit -m x\"}}' | bash '$HOOK'"
  [ "$status" -eq 0 ]
  printf '%s\n' "$output" | diff - "$GOLDEN/commit.json"
}

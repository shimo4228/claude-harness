#!/usr/bin/env bash
# review-chain-notice.sh — commit / revert / merge 直前に Review と Verify を思い出させる。
# 発火時刻だけを持つ薄い hook。手順と reviewer 名簿の正本は implementation-chain。

set -euo pipefail

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || COMMAND=""
[[ -z "$COMMAND" ]] && exit 0

# 実行 segment の先頭にある literal git だけを見る。alias / plumbing の網羅は目的にしない。
# 語の後ろは `-` 以外の区切りか行末 — `\b` は `merge-base` / `commit-tree` でも一致し、14 日で 108 回
# 誤発火していた（2026-11-07 の内部 report）。
grep -qE '(^|[;|&][[:space:]]*)([A-Za-z_][A-Za-z0-9_]*=[^[:space:];|&]+[[:space:]]+)*git\b[^;|&]*[[:space:]](commit|revert|merge)([^-[:alnum:]_]|$)' <<<"$COMMAND" || exit 0

# 封筒の正本は共有部品。ここで手書きしない（複製が drift したのが T-ADVISORY-ENVELOPE-HELPER）。
# 安い guard の後に置く — Bash 呼び出しの大半は commit ではないので、その経路で読み込まない。
# `$(dirname …)` を使わない理由は共有部品のヘッダ参照
# shellcheck source=hooks/_advisory-common.sh
source "${BASH_SOURCE[0]%/*}/_advisory-common.sh" || exit 0
advisory_muted review-chain-notice && exit 0

# subagent は agent を起動できず、Review は起動元の session（triage の判断役・委譲元）が別 process で回す。
AGENT=$(printf '%s' "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null) || AGENT=""
if [[ -n "$AGENT" ]]; then
  msg='Verify は済んでいますか？ subagent の commit なので、Review は起動元の session が別 process で回します。Verify の結果は commit 本文に書いてください。'
else
  msg='Review と Verify は済んでいますか？ 未完了なら skill: implementation-chain を確認して実行してください。'
fi
emit_advisory PreToolUse "$msg"

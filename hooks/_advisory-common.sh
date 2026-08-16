#!/usr/bin/env bash
# _advisory-common.sh — hook が model へ文字列を渡す封筒の**唯一の実装**。
# 単体では発火しない（先例: _session-common.sh / _git-target-common.sh / _episode-log-common.sh）。
#
# ## 封筒（この形の正本。README も tests もここを指す）
#
#   { "hookSpecificOutput": { "hookEventName": "<event>", "additionalContext": "…" } }
#
# plain stdout は transcript 止まり、**トップレベルの additionalContext も読まれない**。
# どちらも静かに失敗する（hook は exit 0、テストは全部通り、文字列だけが消える）。
#
# ## なぜ共有部品にしたか（この経緯の正本）
#
# 封筒は 2 度間違えており、対策は README の散文 +「先例をコピーせよ」だった。drift したのは
# その散文の方で、コピー元に選ばれた bats-autorun.sh は 2026-08-15 時点でまだトップレベル形を
# 出していた（届いているように見えたのは、失敗経路が decision/reason という別チャネルだから）。
# 散文でなく関数を正本にすると、封筒の形を検査する場所が tests/advisory-envelope.bats の
# 1 箇所になる。手書きへの逆戻りは harness_lint.py の envelope check が機械的に止める。
#
# `systemMessage`（ユーザー向け表示）と `decision`/`reason`（PostToolUse の block + 理由）は
# **別チャネル**でトップレベルに置く。同居させたい hook は第 2 引数で JSON オブジェクトを渡す。
#
# ## 長さと衛生
#
# 本文は既定 2048 字で切り詰め、ANSI エスケープと制御文字を落とす。ここは model が最も
# 信用する経路で、hook が運ぶのはツール出力・ファイル名・repo 由来のテキスト — どれも
# 長さに上限が無く、攻撃者が選べる（2026-08-15 の security review では commit 済みの
# 台帳から 59,108 字が注入できた）。**上限が掛かるのは additionalContext だけ**で、
# トップレベルの reason / systemMessage は呼び出し側の責任（そちらも model に届く）。
#   ADVISORY_MAX         本文の上限（既定 2048、上限 8192。数字以外・範囲外は既定に落とす）
#   ADVISORY_TRUNC_HINT  切り詰めたときに添える 1 行（200 字で切る）
#
# **どちらも検証する。** 環境変数は親プロセスから継承されるので、無検証だと
# `ADVISORY_MAX=null` で「全文が流れたうえに『切り詰め』マーカーが付く」（マーカーを
# 見る読み手を積極的に欺く）、`ADVISORY_MAX="9"` で無音の無効化、`ADVISORY_MAX=abc` で
# jq ごと落ちて advisory が丸ごと消える — いずれも 2026-08-15 の security / code review で
# 実測。同じ理由で extra も object でなければ捨てる（封筒まで道連れにしない）。
#
# ## その他
#
# event 名のホワイトリストは持たない。有効な名前どうしの取り違え（PreToolUse hook が
# "PostToolUse" と書く）は捕まえられず、捕まえられるのは綴り間違いだけで、その対価に
# 「Claude Code が新 event を足すと helper が古い名簿で塞ぐ」という drift 源を抱える。
# 空だけを弾き、名前の正しさは各 hook の bats（event 名 1 行の assertion）に残す。
#
# 呼び出し側の不変条件: `${BASH_SOURCE[0]%/*}` 相対で source すること。`$(dirname …)` は
# 使わない — 遅い（builtin でない = 呼び出しごとに fork + exec）だけでなく、`/` を含まない
# 相対起動のとき `.` を返して **cwd の同名ファイル**を読む。`%/*` はその場合に文字列を
# そのまま返すので source が失敗し、fail-closed になる。

# emit_advisory_stream <event> [extra_top_level_json] — 本文は stdin から読む。
# 封筒リテラルはこの 1 箇所だけに置く（emit_advisory はここへ委譲する）。
# 切り詰めも jq の中でやる — bash 側で切ると本文のためだけに fork が 1 つ増える。
emit_advisory_stream() {
  local event="${1:-}" extra="${2:-}" max hint
  if [[ -z "$event" ]]; then
    printf '[advisory] emit_advisory: hookEventName が空です\n' >&2
    return 1
  fi

  # extra は JSON object のときだけ採る。壊れた値を --argjson に渡すと jq が落ち、
  # 封筒ごと消える（= hook が黙る）。捨てて封筒だけ出す方が常に良い。
  [[ -n "$extra" ]] || extra='{}'
  if ! printf '%s' "$extra" | jq -e 'type == "object"' >/dev/null 2>&1; then
    printf '[advisory] extra が JSON object でないため無視します\n' >&2
    extra='{}'
  fi

  # 上限は 10 進数のみ。桁数で先に弾いてから範囲を見る（巨大な数字列で算術を壊さない）。
  max="${ADVISORY_MAX:-}"
  case "$max" in
    '' | *[!0-9]*) max=2048 ;;
  esac
  if [[ ${#max} -gt 5 ]] || [[ "$max" -lt 1 ]] || [[ "$max" -gt 8192 ]]; then
    max=2048
  fi

  hint="${ADVISORY_TRUNC_HINT:-}"
  hint="${hint:0:200}"

  # ANSI エスケープ → 制御文字（改行・タブは残す）の順で落としてから切り詰める。
  # 逆順だと ESC だけ消えて `[0m` の残骸が本文に残る。
  jq -Rs --arg e "$event" --argjson x "$extra" \
    --argjson max "$max" --arg hint "$hint" '
    def sanitize:
      gsub("\\x1b\\[[0-9;?]*[ -/]*[@-~]"; "")
      | gsub("[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]"; "");
    (sanitize
     | if length > $max
         then .[0:$max] + "\n…（切り詰め" + (if $hint == "" then "" else "。" + $hint end) + "）"
         else . end) as $body
    | $x + {hookSpecificOutput: {hookEventName: $e, additionalContext: $body}}'
}

# emit_advisory <event> <text> [extra_top_level_json]
emit_advisory() {
  printf '%s' "${2:-}" | emit_advisory_stream "${1:-}" "${3:-}"
}

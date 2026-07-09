#!/usr/bin/env bash
# spawn.sh — 新しい Claude Code (Remote Control) セッションを tmux で detached 起動する。
#
# Usage: spawn.sh <project-dir> [display-name]
#   起動後、Claude モバイルアプリのセッション一覧に [display-name] が出る。
#   tmux 内で動くので SSH/ネットワーク切断や、起動元セッション終了後も生き残る。
#
# 値の解決（"AAP" -> agent-attribution-practice 等）は呼び出し側 (SKILL.md の
# 指示に従う Claude) が行う。このスクリプトは解決済みの dir と名前を受け取るだけ。
set -euo pipefail

PROJECT="${1:?usage: spawn.sh <project-dir> [display-name]}"
PROJECT="${PROJECT/#\~/$HOME}"                       # 先頭 ~ を展開
[[ -d "$PROJECT" ]] || { printf 'spawn.sh: no such directory: %s\n' "$PROJECT" >&2; exit 1; }

TMUX_BIN="$(command -v tmux || true)"
: "${TMUX_BIN:=/opt/homebrew/bin/tmux}"              # PATH 外でも拾えるよう fallback
[[ -x "$TMUX_BIN" ]] || { printf 'spawn.sh: tmux not found (install: brew install tmux)\n' >&2; exit 1; }

NAME="${2:-$(basename "$PROJECT")}"                  # 省略時はディレクトリ名
SLUG="${NAME//[^[:alnum:]_-]/-}"                     # 英数字・_・- 以外はすべて - に。tmux の禁止文字 (. :) 対策と、後段 grep -E への regex メタ文字混入防止を兼ねる

# 同じ表示名の生存セッションを数え、2 本目以降は表示名に " #n" を付与する
# (アプリ一覧の重複回避)。目的スラッグ等の意味づけは呼び出し側 (SKILL.md) の責務、
# ここは構造的な重複解消のみ。ordinal のマーカーは "--n" — 素の名前由来の slug が
# "-数字" で終わるケース (issue-42 等) と衝突させないため。
# 注意: check-then-act なので同名を同時 spawn すると #n が漏れる (逐次利用前提)
live=$("$TMUX_BIN" list-sessions -F '#S' 2>/dev/null | grep -cE "^cc-${SLUG}(--[0-9]+)?-[0-9]{6}$" 2>/dev/null) || true
if [[ "${live:-0}" -gt 0 ]]; then
  n=$((live + 1))
  NAME="$NAME #$n"
  SLUG="$SLUG--$n"
fi
SESSION="cc-${SLUG}-$(date +%H%M%S)"                 # tmux セッション名

LOGIN_SHELL="${SHELL:-/bin/zsh}"                     # ユーザーのシェルを尊重

# tmux -e で値を環境変数として渡す（クォート地獄を回避）。
# ログインシェル (-l) で node / claude の PATH を読み込ませてから起動する。
"$TMUX_BIN" new-session -d -s "$SESSION" -e "CCDIR=$PROJECT" -e "CCNAME=$NAME" \
  "exec $LOGIN_SHELL -lc 'cd \"\$CCDIR\" && exec claude --remote-control \"\$CCNAME\"'"

printf '✅ Remote Control session started: "%s"\n' "$NAME"
printf '   tmux: %s\n' "$SESSION"
printf '   dir:  %s\n' "$PROJECT"
printf '   → Claude モバイルアプリのセッション一覧に "%s" が出ます\n' "$NAME"

# 起動直後に落ちていないか確認（auth 切れ / PATH 不備の早期検知）
sleep 1
if "$TMUX_BIN" has-session -t "$SESSION" 2>/dev/null; then
  printf '   (tmux session live ✓)\n'
else
  printf '   ⚠️  起動直後に tmux セッションが消えました。claude が即終了した可能性 ' >&2
  printf '(auth 切れ → Mac 側で要再ログイン / claude が PATH に無い)\n' >&2
  exit 1
fi

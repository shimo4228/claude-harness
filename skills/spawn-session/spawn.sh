#!/usr/bin/env bash
# spawn.sh — 新しい Claude Code (Remote Control) セッションを Herdr 内に detached 起動する。
#
# Usage: spawn.sh <project-dir> [display-name] [--model <model>] [--effort <level>]
#                 [--permission-mode <mode>] [--prompt-file <path>]
#   --model: 新 session の model（例: opus）。省略時は settings.json の既定（判断層 = fable）。
#   build 層の worker session を立てるときに opus を渡す（三役: harness ADR-0043 / ADR-0064）。
#   --effort / --permission-mode: claude の同名 flag へ渡す。bypassPermissions は受けない
#   （phone から起こす session の権限を広げないため）。
#   --prompt-file: 起動後、兄弟 skill の agent-send でこのファイルを最初の指示として送り、
#   結果を `prompt:` 行に出す。届かなければ agent-send の exit code で終わる（session は残る）。
#   起動後、Claude モバイルアプリのセッション一覧に [display-name] が出る。
#   Herdr の persistent session (server) が pty を保持するので、Ghostty/SSH の
#   切断や起動元セッションの終了後も生き残る。
#
# 値の解決（"AAP" -> agent-attribution-practice 等）は呼び出し側 (SKILL.md の
# 指示に従う Claude) が行う。このスクリプトは解決済みの dir と名前を受け取るだけ。
#
# 配置規則: 同じ repo の workspace が既にあればそこに新 tab、無ければ
# 新 workspace を作成（repo 単位 workspace 運用に合わせる）。「同じ repo」は
# git の main worktree root で判定する — linked worktree（build セッションの
# `<repo>/.claude/worktrees/<name>` や scratchpad 下の worktree）を渡しても
# repo の workspace に合流し、worktree 名の workspace が増殖しない。
# tab の cwd は渡された dir（worktree）のまま。
set -euo pipefail

# 兄弟 skill の agent-send（~/bin/cc-spawn の symlink 経由でも実体の位置から引く）
SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || printf '%s' "${BASH_SOURCE[0]}")"
AGENT_SEND="$(cd "$(dirname "$SELF")/.." && pwd)/agent-send/agent-send.sh"

PROJECT="${1:?usage: spawn.sh <project-dir> [display-name] [--model <model>]}"
PROJECT="${PROJECT/#\~/$HOME}"                       # 先頭 ~ を展開
[[ -d "$PROJECT" ]] || { printf 'spawn.sh: no such directory: %s\n' "$PROJECT" >&2; exit 1; }
PROJECT="$(cd "$PROJECT" && pwd -P)"                 # pane cwd との文字列照合のため symlink/相対を正規化

# --- repo root 解決 ---------------------------------------------------------
# linked worktree なら --git-common-dir は main worktree の .git を指す。その親が
# repo root。git 管理外や取得失敗時は PROJECT 自身を root と扱う（従来挙動）。
ROOT="$PROJECT"
if common="$(git -C "$PROJECT" rev-parse --git-common-dir 2>/dev/null)"; then
  [[ "$common" = /* ]] || common="$PROJECT/$common"
  common="$(cd "$common" 2>/dev/null && pwd -P || printf '%s' "$common")"
  [[ "$(basename "$common")" == ".git" ]] && ROOT="$(dirname "$common")"
fi

HERDR_BIN="$(command -v herdr || true)"
: "${HERDR_BIN:=/opt/homebrew/bin/herdr}"            # PATH 外でも拾えるよう fallback
[[ -x "$HERDR_BIN" ]] || { printf 'spawn.sh: herdr not found (install: brew install herdr)\n' >&2; exit 1; }
command -v jq >/dev/null || { printf 'spawn.sh: jq not found (install: brew install jq)\n' >&2; exit 1; }

NAME="$(basename "$PROJECT")"                        # 表示名の既定はディレクトリ名
MODEL=""
EFFORT="" PMODE="" PROMPT_FILE=""
shift
while [[ $# -gt 0 ]]; do                             # 2 つ目の位置引数 = 表示名、--model は任意
  case "$1" in
    --model)
      [[ -n "${2:-}" ]] || { printf 'spawn.sh: --model needs a value\n' >&2; exit 64; }
      MODEL="$2"; shift ;;
    --model=*) MODEL="${1#--model=}" ;;
    --effort | --permission-mode | --prompt-file)
      [[ -n "${2:-}" ]] || { printf 'spawn.sh: %s needs a value\n' "$1" >&2; exit 64; }
      case "$1" in
        --effort) EFFORT="$2" ;;
        --permission-mode) PMODE="$2" ;;
        *) PROMPT_FILE="$2" ;;
      esac
      shift ;;
    --*) printf 'spawn.sh: unknown option %s\n' "$1" >&2; exit 64 ;;
    *) NAME="$1" ;;
  esac
  shift
done
NAME="${NAME//[\"\']/}"                              # 後段で pane のシェルへ打鍵するためクォート文字は除去
[[ "$MODEL" =~ ^[A-Za-z0-9._-]*$ ]] || { printf 'spawn.sh: bad --model value\n' >&2; exit 64; }
[[ -z "$EFFORT" || "$EFFORT" =~ ^(low|medium|high|xhigh|max)$ ]] ||
  { printf 'spawn.sh: bad --effort value\n' >&2; exit 64; }
[[ -z "$PMODE" || "$PMODE" =~ ^(manual|acceptEdits|auto|dontAsk|plan)$ ]] ||
  { printf 'spawn.sh: bad --permission-mode value (bypassPermissions is refused)\n' >&2; exit 64; }
[[ -z "$PROMPT_FILE" || -f "$PROMPT_FILE" ]] ||
  { printf 'spawn.sh: no such file: %s\n' "$PROMPT_FILE" >&2; exit 64; }
[[ -z "$PROMPT_FILE" || -x "$AGENT_SEND" ]] ||
  { printf 'spawn.sh: --prompt-file needs the agent-send skill: %s\n' "$AGENT_SEND" >&2; exit 64; }
CLAUDE_ARGS=(--remote-control "$NAME")
[[ -n "$MODEL" ]] && CLAUDE_ARGS+=(--model "$MODEL")
[[ -n "$EFFORT" ]] && CLAUDE_ARGS+=(--effort "$EFFORT")
[[ -n "$PMODE" ]] && CLAUDE_ARGS+=(--permission-mode "$PMODE")

# --- server 確保 -------------------------------------------------------------
# socket 越しの read-only コマンドで生存確認。不在なら headless server を起動
# （tmux のサーバー自動起動セマンティクスの再現）。
if ! "$HERDR_BIN" workspace list >/dev/null 2>&1; then
  nohup "$HERDR_BIN" server >/dev/null 2>&1 &
  disown
  server_up=0
  for _ in 1 2 3 4 5 6 7 8 9 10; do                 # 有界リトライ: 0.5s x 10
    sleep 0.5
    if "$HERDR_BIN" workspace list >/dev/null 2>&1; then server_up=1; break; fi
  done
  [[ "$server_up" = 1 ]] || { printf 'spawn.sh: herdr server を起動できませんでした\n' >&2; exit 1; }
fi

# client と server の互換・版を確かめる（警告は stderr にそのまま出す）
if [[ -x "$AGENT_SEND" ]]; then
  if ! pf=$("$AGENT_SEND" preflight); then
    printf 'spawn.sh: herdr の preflight に失敗しました: %s\n' "$pf" >&2
    exit 1
  fi
fi

# --- 表示名の重複解消 --------------------------------------------------------
# 同じ表示名の tab（= 過去に spawn した RC セッション。通常 tab の label は既定で
# 数字なので衝突しない）を全 workspace から数え、2 本目以降は " #n" を付与する
# (アプリ一覧の重複回避)。目的スラッグ等の意味づけは呼び出し側 (SKILL.md) の責務、
# ここは構造的な重複解消のみ。
# 注意: check-then-act なので同名を同時 spawn すると #n が漏れる (逐次利用前提)。
# また列挙はプロセス置換内で行うため途中失敗は親の set -e に届かず、
# 「dedup なし」に静かに退化する (best-effort — アプリ一覧の重複は致命でない)
live=0
while IFS= read -r label; do
  [[ "$label" == "$NAME" || "$label" == "$NAME #"* ]] && live=$((live + 1))
done < <(
  "$HERDR_BIN" workspace list | jq -r '.result.workspaces[].workspace_id' |
    while IFS= read -r ws; do
      "$HERDR_BIN" tab list --workspace "$ws" | jq -r '.result.tabs[].label // empty'
    done
)
[[ "$live" -gt 0 ]] && NAME="$NAME #$((live + 1))"

# --- workspace 解決: 同 repo があれば合流、無ければ新規 ----------------------
# pane の cwd が ROOT そのもの、または ROOT 配下（他の worktree・サブディレクトリ）
# なら同 repo とみなす。
WS_ID=""
while IFS= read -r ws; do
  if "$HERDR_BIN" pane list --workspace "$ws" |
       jq -e --arg root "$ROOT" '.result.panes[] | select(.cwd == $root or (.cwd | startswith($root + "/")))' >/dev/null; then
    WS_ID="$ws"
    break
  fi
done < <("$HERDR_BIN" workspace list | jq -r '.result.workspaces[].workspace_id')

# cwd 照合で見つからなければ label 照合に fallback。basename が同名の別 repo が
# あると誤 workspace に合流しうるが、tab 自体の cwd は正しいので機能上は無害
if [[ -z "$WS_ID" ]]; then
  WS_ID=$("$HERDR_BIN" workspace list |
    jq -r --arg l "$(basename "$ROOT")" '[.result.workspaces[] | select(.label == $l) | .workspace_id] | first // empty')
fi

# --- tab / workspace 作成 ----------------------------------------------------
# ID は応答 JSON から読む（herdr の規律: ID を予測・構築しない）
NEW_WS=0
if [[ -n "$WS_ID" ]]; then
  resp=$("$HERDR_BIN" tab create --workspace "$WS_ID" --cwd "$PROJECT" --label "$NAME" --no-focus)
else
  NEW_WS=1
  resp=$("$HERDR_BIN" workspace create --cwd "$PROJECT" --label "$(basename "$ROOT")" --no-focus)
  WS_ID=$(jq -r '[.. | .workspace_id? // empty] | first // empty' <<<"$resp")
  [[ -n "$WS_ID" ]] || { printf 'spawn.sh: workspace create の応答から workspace_id を読めませんでした:\n%s\n' "$resp" >&2; exit 1; }
fi

TAB_ID=$(jq -r '[.. | .tab_id? // empty] | first // empty' <<<"$resp")
PANE_ID=$(jq -r '[.. | .pane_id? // empty] | first // empty' <<<"$resp")
if [[ -z "$PANE_ID" ]]; then                         # 応答に pane が無い形式なら pane list から引く
  PANE_ID=$("$HERDR_BIN" pane list --workspace "$WS_ID" |
    jq -r --arg t "$TAB_ID" '[.result.panes[] | select(.tab_id == $t) | .pane_id] | first // empty')
fi
[[ -n "$PANE_ID" ]] || { printf 'spawn.sh: 作成した tab の pane_id を特定できませんでした:\n%s\n' "$resp" >&2; exit 1; }

# 新規 workspace の初期 tab は既定 label なので表示名を付け直す
# （workspace label は repo 名、表示名は tab 側。合流 path は tab create --label 済み）
if [[ "$NEW_WS" = 1 && -n "$TAB_ID" ]]; then
  "$HERDR_BIN" tab rename "$TAB_ID" "$NAME" >/dev/null
fi

# --- claude 起動 + 検証 ------------------------------------------------------
# herdr 0.7.5+ の agent start は「シェル prompt の pane で agent を起動し、
# 検出 + 入力可能 (idle) まで待ってから返る」ので、旧 pane run + wait の
# 起動レース（未検出 pane への agent wait は即 agent_not_found）ごと置き換える。
# agent 名は [a-z][a-z0-9_-]{0,31} 制約 + live 中一意なので slug + PID で生成
AGENT_NAME="$(printf '%s' "$NAME" | tr '[:upper:]' '[:lower:]' | LC_ALL=C tr -c 'a-z0-9_-' '-' | cut -c1-20)"
[[ "$AGENT_NAME" =~ ^[a-z] ]] || AGENT_NAME="s${AGENT_NAME}"
AGENT_NAME="${AGENT_NAME}-$$"

# workspace/tab 作成直後はシェルが prompt 未到達で agent_pane_busy を即返すため、
# その場合のみ短間隔リトライ（それ以外のエラーは即失敗させて原因を隠さない）
start_ok=0
for _ in $(seq 1 20); do
  err=$("$HERDR_BIN" agent start "$AGENT_NAME" --kind claude --pane "$PANE_ID" --timeout 30000 \
          -- "${CLAUDE_ARGS[@]}" 2>&1 >/dev/null) && { start_ok=1; break; }
  [[ "$err" == *agent_pane_busy* ]] || break
  sleep 0.5
done

if [[ "$start_ok" = 1 ]]; then
  printf '✅ Remote Control session started: "%s"\n' "$NAME"
  printf '   herdr: workspace %s / tab %s / pane %s\n' "$WS_ID" "${TAB_ID:-?}" "$PANE_ID"
  printf '   dir:   %s\n' "$PROJECT"
  printf '   → Claude モバイルアプリのセッション一覧に "%s" が出ます\n' "$NAME"
  printf '   agent: %s   ← herdr agent prompt/get/read に渡す名前 (表示名ではない)\n' "$AGENT_NAME"
  printf '   (claude idle 到達 ✓)\n'
  if [[ -n "$PROMPT_FILE" ]]; then
    rc=0
    res=$(AGENT_SEND_PREFLIGHT_DONE=1 "$AGENT_SEND" prompt "$PANE_ID" --file "$PROMPT_FILE" --retry-unseen) || rc=$?
    printf '   prompt: %s\n' "$res"
    exit "$rc"
  fi
else
  printf '   ⚠️  claude が起動 or idle に到達しませんでした。\n' >&2
  [[ -n "${err:-}" ]] && printf '   herdr error: %s\n' "$err" >&2
  printf '   agent: %s   pane: %s   ← agent read / send-keys / pane close に使える\n' "$AGENT_NAME" "$PANE_ID" >&2
  screen=$("$HERDR_BIN" pane read "$PANE_ID" --source recent-unwrapped --lines 40 2>/dev/null || true)
  if grep -q 'trust' <<<"$screen"; then
    printf '   原因: workspace trust の確認で停止。Mac でこの repo を一度開くと通る\n' >&2
  fi
  printf '   pane の直近出力:\n%s\n' "$screen" >&2
  printf '   (典型原因: auth 切れ → Mac 側で要再ログイン / claude が PATH に無い)\n' >&2
  exit 1
fi

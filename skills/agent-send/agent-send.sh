#!/usr/bin/env bash
# agent-send.sh — Herdr pane で動く agent（Claude Code / Codex など）へ prompt を送り、
# 着弾（turn が始まったこと）と完了を確かめる。
#
# Usage:
#   agent-send.sh prompt <target> (--text TEXT | --file PATH) [--timeout MS] [--busy-timeout MS] [--retry-unseen]
#   agent-send.sh wait   <target> [--timeout MS] [--settle N] [--step MS] [--gap S] [--done-if CMD]
#   agent-send.sh preflight
#
# <target>: agent 名 | pane ID | 表示名（tab の label）。内部で pane ID に固定する —
#   名前宛ての prompt は agent 終了直後に別の occupant へ届きうる（herdr #4764）。
# stdout: 1 行 `result=<語> pane=<id> [key=value…]`。stderr: `warn=…` と失敗時の画面末尾。
# exit:   0 landed・accepted・done・ok / 2 typed・no_evidence・not_found / 3 blocked
#         4 busy・timeout / 5 preflight / 64 usage
#
# 状態の読み方: Claude は `claude agents --json` の status（Claude Code 自身の報告。
# sessionId は herdr の agent_session.value と同じ値）、それ以外は herdr の agent_status
# （画面検出）。herdr は turn を追跡しないので、着弾は「送信後に working を観測した」で判定し、
# 完了は settled の連続と --done-if（成果物の条件）で判定する。
# 前提: herdr server 0.9.0 以上（--wait が working / blocked の観測を要する版）。
set -euo pipefail

HERDR="${HERDR_BIN:-$(command -v herdr || echo /opt/homebrew/bin/herdr)}"
CLAUDE="${CLAUDE_BIN:-$(command -v claude || echo claude)}"
CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
TRANSCRIPT_WAIT_S="${AGENT_SEND_TRANSCRIPT_WAIT_S:-5}"   # transcript は非同期に書かれる
RETRY_WAIT_S="${AGENT_SEND_RETRY_WAIT_S:-3}"
RETRY_UNSEEN=0
MIN_SERVER="0.9.0"

PANE=""
usage() { sed -n '5,8p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 64; }

emit() {   # emit <result> [key=value…]
  local r=$1; shift
  printf 'result=%s' "$r"
  [[ -n "$PANE" ]] && printf ' pane=%s' "$PANE"
  (($#)) && printf ' %s' "$@"
  printf '\n'
}

# --- preflight ---------------------------------------------------------------
ver_ge() {   # ver_ge A B: A >= B（x.y.z の数値比較。形が違えば偽）
  local IFS=. i a b
  [[ "$1" =~ ^[0-9]+(\.[0-9]+)*$ && "$2" =~ ^[0-9]+(\.[0-9]+)*$ ]] || return 1
  read -r -a a <<<"$1"; read -r -a b <<<"$2"
  for i in 0 1 2; do
    ((10#${a[i]:-0} > 10#${b[i]:-0})) && return 0
    ((10#${a[i]:-0} < 10#${b[i]:-0})) && return 1
  done
  return 0
}

skill_drift_warn() {   # 警告だけ。ファイルは書かない
  local f="$CONFIG_DIR/skills/herdr/SKILL.md"
  [[ -f "$f" && ! -L "$f" ]] || return 0
  if ! diff -q <(grep -v '^origin:' "$f") <("$HERDR" --skill 2>/dev/null) >/dev/null; then
    printf 'warn=skill_drift file=%s\n' "$f" >&2
    printf '  → herdr --skill の出力で置き換える（origin 行は残す）\n' >&2
  fi
}

preflight() {
  local s
  if ! s=$("$HERDR" status --json 2>/dev/null); then emit herdr_unreachable; return 1; fi
  if [[ $(jq -r '.server.running // false' <<<"$s") != true ]]; then emit server_down; return 1; fi
  if [[ $(jq -r '(.server.compatible // false) and (.server.endpoint_compatible // false)' <<<"$s") != true ]]; then
    emit incompatible
    printf '  → 人間に渡す: 全 pane が idle の時刻に herdr server を再起動する（brew 版は update --handoff 不可）\n' >&2
    return 1
  fi
  if ! ver_ge "$(jq -r '.server.version // "0"' <<<"$s")" "$MIN_SERVER"; then
    emit server_too_old "server=$(jq -r '.server.version' <<<"$s")" "min=$MIN_SERVER"
    return 1
  fi
  if [[ $(jq -r '(.update.server_binary_stale // false) or (.update.restart_needed // false)' <<<"$s") == true ]]; then
    printf 'warn=server_binary_stale server=%s client=%s\n' \
      "$(jq -r '.server.version' <<<"$s")" "$(jq -r '.client.version' <<<"$s")" >&2
    printf '  → 人間に渡す: 全 pane が idle の時刻に herdr server を再起動する（brew 版は update --handoff 不可）\n' >&2
  fi
  skill_drift_warn
}

# --- 宛先と状態 ----------------------------------------------------------------
resolve_pane() {   # agent 名・pane ID・表示名 → pane ID
  local t=$1 p ws tabs
  p=$("$HERDR" agent list 2>/dev/null | jq -r --arg t "$t" \
        '[.result.agents[]? | select(.name == $t or .pane_id == $t) | .pane_id] | first // empty')
  if [[ -n "$p" ]]; then printf '%s\n' "$p"; return 0; fi
  # 表示名は tab の label（spawn.sh が付ける "AAP/release" など）
  while read -r ws; do
    [[ -n "$ws" ]] || continue
    tabs=$("$HERDR" tab list --workspace "$ws" 2>/dev/null |
             jq -c --arg t "$t" '[.result.tabs[]? | select(.label == $t) | .tab_id]')
    [[ "$tabs" == "[]" || -z "$tabs" ]] && continue
    p=$("$HERDR" pane list --workspace "$ws" 2>/dev/null | jq -r --argjson tabs "$tabs" \
          '[.result.panes[]? | select(.tab_id as $x | $tabs | index($x)) | .pane_id] | first // empty')
    if [[ -n "$p" ]]; then printf '%s\n' "$p"; return 0; fi
  done < <("$HERDR" workspace list 2>/dev/null | jq -r '.result.workspaces[]?.workspace_id')
  return 1
}

AGENT_JSON=""
load_agent() {   # herdr agent get を 1 回呼び、AGENT_JSON に残す
  AGENT_JSON=$("$HERDR" agent get "$1" 2>/dev/null | jq -c '.result.agent // empty') || return 1
  [[ -n "$AGENT_JSON" ]]
}
agent_field() { jq -r "$1 // empty" <<<"$AGENT_JSON"; }

status_of() {   # pane → working | idle | blocked | unknown。取れなければ非 0
  local pane=$1 kind sid st
  load_agent "$pane" || return 1
  kind=$(agent_field '.agent'); sid=$(agent_field '.agent_session.value')
  if [[ "$kind" == claude && -n "$sid" ]]; then
    st=$("$CLAUDE" agents --json </dev/null 2>/dev/null |
           jq -r --arg s "$sid" '[.[]? | select(.sessionId == $s) | .status] | first // empty' 2>/dev/null || true)
    case "$st" in
      busy) echo working; return 0 ;;
      waiting) echo blocked; return 0 ;;
      idle) echo idle; return 0 ;;
    esac   # 見つからなければ herdr の状態に戻る
  fi
  case "$(agent_field '.agent_status')" in
    working) echo working ;;
    blocked) echo blocked ;;
    idle | done) echo idle ;;
    *) echo unknown ;;
  esac
}

num() { [[ "$1" =~ ^[0-9]+$ ]] || usage; }

transcript_path() {   # Claude の pane → session の transcript（無ければ空）
  local sid
  load_agent "$1" || return 0
  [[ "$(agent_field '.agent')" == claude ]] || return 0
  sid=$(agent_field '.agent_session.value')
  [[ "$sid" =~ ^[A-Za-z0-9-]+$ ]] || return 0
  find "$CONFIG_DIR/projects" -maxdepth 2 -name "$sid.jsonl" 2>/dev/null | head -1 || true
}

screen_tail() { "$HERDR" agent read "$1" --source visible --lines 15 2>/dev/null || true; }

transcript_has_text() {   # 送信後に transcript へ追記された分に、本文の 1 行目が user turn として出たか
  local pane=$1 text=$2 offset=$3 line needle f i
  line=$(printf '%s\n' "$text" | sed -n '/[^[:space:]]/{p;q;}')
  [[ -n "$line" ]] || return 1
  # 文字単位で 60 字に切り、JSON の中の書き方に合わせる（cut はロケール次第で多バイト文字を割る）
  needle=$(jq -Rr '.[0:60] | @json' <<<"$line"); needle=${needle#\"}; needle=${needle%\"}
  for ((i = 0; i <= TRANSCRIPT_WAIT_S; i++)); do
    f=$(transcript_path "$pane")
    # 送信前の大きさより後ろだけを見る — 同じ文面の以前の turn に当たらないように
    [[ -n "$f" ]] && tail -c +$((offset + 1)) "$f" | grep -F -- "$needle" | grep -q '"type":"user"' && return 0
    ((i < TRANSCRIPT_WAIT_S)) && sleep 1
  done
  return 1
}

# --- prompt --------------------------------------------------------------------
cmd_prompt() {
  local target=$1; shift
  local text="" timeout=60000 busy=600000 have_text=0
  while (($#)); do
    case "$1" in
      --text) (($# >= 2)) || usage; text=$2; have_text=1; shift ;;
      --file) [[ -f "${2-}" ]] || { printf 'agent-send: no such file: %s\n' "${2-}" >&2; exit 64; }
              text=$(cat "$2"); have_text=1; shift ;;
      --timeout) num "${2-}"; timeout=$2; shift ;;
      --busy-timeout) num "${2-}"; busy=$2; shift ;;
      --retry-unseen) RETRY_UNSEEN=1 ;;
      *) usage ;;
    esac
    shift
  done
  ((have_text)) && [[ -n "$text" ]] || usage

  [[ -n "${AGENT_SEND_PREFLIGHT_DONE:-}" ]] || preflight || exit 5   # spawn.sh は先に済ませている
  PANE=$(resolve_pane "$target") || { emit not_found "target=$target"; exit 2; }

  local st
  st=$(status_of "$PANE") || { emit not_found; exit 2; }
  case "$st" in
    blocked) emit blocked; screen_tail "$PANE" >&2; exit 3 ;;
    working)   # 送ると queue に入り、着弾を証明できない
      "$HERDR" agent wait "$PANE" --until idle --until "done" --until blocked --timeout "$busy" >/dev/null 2>&1 ||
        { emit busy "waited_ms=$busy"; exit 4; }
      st=$(status_of "$PANE") || { emit not_found; exit 2; }
      [[ "$st" == blocked ]] && { emit blocked; screen_tail "$PANE" >&2; exit 3; }
      [[ "$st" == working ]] && { emit busy "waited_ms=$busy"; exit 4; }
      ;;
  esac

  load_agent "$PANE" || { emit not_found; exit 2; }
  local seq0 err tpath offset=0
  seq0=$(agent_field '.state_change_seq')
  tpath=$(transcript_path "$PANE")
  [[ -n "$tpath" ]] && offset=$(wc -c <"$tpath" | tr -d ' ')
  if err=$("$HERDR" agent prompt "$PANE" "$text" --wait --until working --until blocked \
             --timeout "$timeout" 2>&1 >/dev/null); then
    st=$(status_of "$PANE") || st=unknown
    [[ "$st" == blocked ]] && { emit blocked; screen_tail "$PANE" >&2; exit 3; }
    emit landed via=working; exit 0
  fi
  case "$err" in
    *'"agent_blocked"'*) emit blocked; screen_tail "$PANE" >&2; exit 3 ;;   # 入力は送られていない
    *'"agent_not_found"'* | *'"agent_not_running"'*) emit not_found; exit 2 ;;
    *'"agent_prompt_stalled"'* | *'"timeout"'*) ;;
    *) printf 'herdr: %s\n' "$err" >&2 ;;   # 想定外の拒否は理由を残す
  esac
  confirm_landing "$PANE" "$seq0" "$text" "$offset"
}

confirm_landing() {   # stalled / timeout のあと。本文は再送しない（二重送信を避ける）
  local pane=$1 seq0=$2 text=$3 offset=$4 st
  st=$(status_of "$pane" || true)
  if [[ "$st" == blocked ]]; then emit blocked; screen_tail "$pane" >&2; exit 3; fi
  if load_agent "$pane" && [[ "$(agent_field '.state_change_seq')" != "$seq0" ]]; then   # status_of はサブシェルなので読み直す
    emit landed via=seq; exit 0
  fi
  if [[ "$st" == working ]]; then
    emit landed via=status; exit 0
  fi
  if transcript_has_text "$pane" "$text" "$offset"; then
    emit landed via=transcript; exit 0
  fi
  # 起動直後の未 focus pane には、指示が成功を装わずに消えることがある（herdr #4537、0.9.3 macOS でも再現）。
  # transcript がまだ無い = Claude Code が一度もメッセージを処理していないので、1 回だけ送り直しても二重にならない
  if ((RETRY_UNSEEN)) && [[ "$(agent_field '.agent')" == claude && -z "$(transcript_path "$pane")" ]] &&
     ! screen_tail "$pane" | grep -q '\[Pasted text #'; then
    sleep "$RETRY_WAIT_S"
    if "$HERDR" agent prompt "$pane" "$text" --wait --until working --until blocked \
         --timeout 30000 >/dev/null 2>&1; then
      emit landed via=retry; exit 0
    fi
  fi
  if screen_tail "$pane" | grep -q '\[Pasted text #'; then
    # Enter は押さない: blocked の検出は描画から 0.3 秒ほど遅れ、承認 dialog を押しうる（herdr #4764）
    emit typed; screen_tail "$pane" >&2; exit 2
  fi
  # turn を起こさない組み込みコマンドの 1 行だけ。user skill の /name は turn を起こすので証拠が要る
  if [[ "$text" != *$'\n'* && "$text" =~ ^/(effort|model)([[:space:]].*)?$ ]]; then
    emit accepted via=command; exit 0
  fi
  emit no_evidence; screen_tail "$pane" >&2; exit 2
}

# --- wait ----------------------------------------------------------------------
cmd_wait() {
  local target=$1; shift
  local timeout=3600000 settle="" step=30000 gap=30 done_if=""
  while (($#)); do
    case "$1" in
      --timeout) num "${2-}"; timeout=$2; shift ;;
      --settle) num "${2-}"; settle=$2; shift ;;
      --step) num "${2-}"; step=$2; shift ;;
      --gap) num "${2-}"; gap=$2; shift ;;
      --done-if) done_if="${2-}"; shift ;;
      *) usage ;;
    esac
    shift
  done
  PANE=$(resolve_pane "$target") || { emit not_found "target=$target"; exit 2; }
  if [[ -z "$settle" ]]; then   # Claude は自身の報告なので 2 回、画面検出の agent は 3 回
    load_agent "$PANE" || { emit not_found; exit 2; }
    if [[ "$(agent_field '.agent')" == claude ]]; then settle=2; else settle=3; fi
  fi

  local start=$SECONDS settled=0 st
  while :; do
    "$HERDR" agent wait "$PANE" --until idle --until "done" --until blocked --timeout "$step" >/dev/null 2>&1 || true
    st=$(status_of "$PANE") || { emit not_found; exit 2; }
    case "$st" in
      blocked) emit blocked; screen_tail "$PANE" >&2; exit 3 ;;
      idle) settled=$((settled + 1)) ;;
      *) settled=0 ;;
    esac
    if ((settled >= settle)); then
      if [[ -z "$done_if" ]] || bash -c "$done_if" >/dev/null 2>&1; then
        emit "done" "status=idle" "settled=$settled"; exit 0
      fi
    fi
    if (((SECONDS - start) * 1000 >= timeout)); then
      emit timeout "status=$st" "waited_ms=$timeout"; exit 4
    fi
    sleep "$gap"   # 偽 idle の揺れを観測の間隔でならす
  done
}

# --- main ----------------------------------------------------------------------
command -v jq >/dev/null || { printf 'agent-send: jq not found (brew install jq)\n' >&2; exit 64; }
(($#)) || usage
case "$1" in
  prompt) (($# >= 2)) || usage; shift; cmd_prompt "$@" ;;
  wait) (($# >= 2)) || usage; shift; cmd_wait "$@" ;;
  preflight) preflight || exit 5; emit ok ;;
  *) usage ;;
esac

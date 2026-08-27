#!/usr/bin/env bash
# review-model-notice.sh — judge-tier (Fable) セッションでの review 起動を実行前に扱う。
# 経路で応答を分ける:
#   Skill 直呼び (code-review / simplify) → **block**。判定が完全に機械的（skill 名 ×
#     セッションモデル）で誤検知の余地が無く、advisory だと skill が同 turn で走って
#     judge-tier トークンを消費してから助言が読まれる（2026-08-24 実測 — 中断 + Opus
#     再レビューで二重払いになった）。効くのは実行前の block だけ。理由文で model が
#     Agent(model:"opus") に自己修正するので、人間の介入は要らない。
#   Agent/Task 起動で model pin 欠落 → advisory に留める。prompt 部分一致の
#     ヒューリスティックで誤検知しうるので、deny の権限を持たせない。
# 配線の根拠: built-in review skill はセッションモデルを継ぎ、モデル引数を持たない
# （commit 境界では手遅れなので、起動直前の PreToolUse に置く）。
#
# セッションモデルは hook payload に無いので transcript 末尾の直近 "model" フィールドから
# 読む（assistant 行が持つ）。読めなければ黙る — 無根拠に指摘しない。
# Wired in settings.json: PreToolUse (matcher: Task|Agent|Skill)
#
# Environment:
#   REVIEW_MODEL_TRANSCRIPT  Override transcript path (for bats tests only)

set -uo pipefail

INPUT=$(cat)

# 安い prefilter。review 起動を含まない呼び出しで jq を起こさない（部分一致の superset、
# 厳密判定は下）。"code-review" は "codex-review" に当たらない（code- / codex- で分岐）。
case "$INPUT" in
  *code-review*|*simplify*) ;;
  *) exit 0 ;;
esac

tool=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0

# matcher "Task|Agent|Skill" は無錨で TaskCreate 等にも当たるため、この判定は冗長ではない。
case "$tool" in
  Skill)
    name=$(printf '%s' "$INPUT" | jq -r '.tool_input.skill // empty' 2>/dev/null) || exit 0
    [[ "$name" == "code-review" || "$name" == "simplify" ]] || exit 0
    mode=block
    ;;
  Task|Agent)
    # model 引数で build-tier に pin 済みなら正しい経路 — 黙る。
    # 空 = セッションモデル継承なので Skill 直呼びと同じ問題を持つ。
    m=$(printf '%s' "$INPUT" | jq -r '.tool_input.model // empty' 2>/dev/null) || exit 0
    [[ -z "$m" || "$m" == "fable" ]] || exit 0
    prompt=$(printf '%s' "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null) || exit 0
    case "$prompt" in *code-review*|*simplify*) ;; *) exit 0 ;; esac
    mode=advisory
    ;;
  *) exit 0 ;;
esac

# セッションモデルの判定。tail -c で走査量を固定する（全文 scan はログ長に比例して
# 遅くなる）。grep の一致なしは「判定不能」なので黙る。
T="${REVIEW_MODEL_TRANSCRIPT:-$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)}"
[[ -n "$T" && -f "$T" ]] || exit 0
model=$(tail -c 2000000 "$T" 2>/dev/null | grep -o '"model" *: *"[^"]*"' | tail -n 1) || true
case "$model" in
  *fable*) ;;
  *) exit 0 ;;
esac

msg='このセッションは judge-tier (Fable) です。built-in /code-review・/simplify はセッションモデルを継いで judge-tier トークンを消費します。Agent(subagent_type: "general-purpose", model: "opus") のサブエージェント内で起動してください（正本: skill implementation-chain「Review の実行モデル pin」）。'

if [[ "$mode" == "block" ]]; then
  # 実行前に止める。advisory では skill が同 turn で走ってから助言が読まれる（ヘッダ参照）。
  jq -cn --arg reason "$msg" '{decision:"block", reason:$reason}'
  exit 0
fi

# shellcheck source=hooks/_advisory-common.sh
source "${BASH_SOURCE[0]%/*}/_advisory-common.sh" || exit 0
emit_advisory PreToolUse "$msg"

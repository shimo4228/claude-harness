#!/usr/bin/env bash
# verify-precommit.sh — PreToolUse hook (Bash): git commit 前に repo 自身の機械ゲートを回す。
#
# **この hook は言語もツールも知らない。** repo が `.claude/verify.sh` を持っていれば
# `--staged` で呼び、exit code だけを見る。ツール名を harness 側に置くと、そこが陳腐化の
# 発生源になる (ruff が flake8+black+isort を置換したのは 2 年) — ので置かない。
# ゲートの中身は repo が所有し、選定は skill: verify-bootstrap が search-first 経由で行う。
#
# 契約 (skill: verify-bootstrap が正本):
#   <repo>/.claude/verify.sh --staged
#     exit 0 = PASS / 1 = FAIL (commit を止める) / 2 = 検査不能 (fail-soft、素通し)
#     stdout = FAIL 時の検出行
#
# 入力: stdin から JSON (tool_input.command)
# 出力: FAIL 時 { "decision": "block", ... }、それ以外は無出力 (= allow)
# バイパス: コマンド文字列の**先頭** (env prefix 位置) に VERIFY_BYPASS=1 を明示
#   (位置非依存の部分文字列一致にしない — コミットメッセージ内の言及で無効化されるのを防ぐ)

# 兄弟 hook は set -euo だが、ここは意図的に -e を外している: ゲートの非ゼロ終了は
# 「検出した」という正常系であり、-e で hook 自身が落ちると block を出さずに素通しになる
set -uo pipefail

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || COMMAND=""

[[ -z "$COMMAND" ]] && exit 0
printf '%s' "$COMMAND" | grep -qE '^([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*VERIFY_BYPASS=1([[:space:]]|$)' && exit 0

# git commit を含むコマンドのみ対象 (secret-scan-precommit.sh と同一のマッチ規則)。
# パイプ区切り (;|&) は跨がない — "git log | grep commit" 除外
printf '%s' "$COMMAND" | grep -qE '\bgit\b[^;|&]*[[:space:]]commit\b' || exit 0

# 対象 repo の特定。この hook は抽出結果配下のスクリプトを **実行**するので、誤爆の影響が
# 読み取り専用の兄弟 hook と違う (2026-07-31 security-reviewer の HIGH)。抽出自体は共有部品と
# 同じだが、**承認台帳が第 2 の防壁**になる — 乗っ取られた path のゲートは承認されていない。
# 抽出は共有部品に集約 (7 hook で複製していた正規表現の drift 解消。引用符 span を除去してから
# セグメント解析する — 詳細と限界は _git-target-common.sh のヘッダ)
# shellcheck source=hooks/_git-target-common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_git-target-common.sh"
repo_dir=$(git_target_dir "$COMMAND")
[[ -z "$repo_dir" || ! -d "$repo_dir" ]] && repo_dir="$PWD"

# 敵対的 .git/config の無害化 (ADR-0034 の T-GIT-HOSTILE-CONFIG 横展開)。
# rev-parse は diff を起動しないので diff.external は不要 — fsmonitor / hooksPath だけ封じる
toplevel=$(git -c core.fsmonitor= -c core.hooksPath= \
  -C "$repo_dir" rev-parse --show-toplevel 2>/dev/null) || exit 0
GATE="$toplevel/.claude/verify.sh"
# ゲートを持たない repo は素通し (導入は skill: verify-bootstrap)
[[ -x "$GATE" ]] || exit 0

# **承認済みのバイト列だけを実行する** (direnv allow 型)。hook は permission プロンプトを
# 経ずに走るので、「ファイルが存在する」を「実行してよい」と読み替えると、clone しただけの
# 外部 repo でコードが自動実行される。既存方針 (bandit-precommit.sh: repo 内バイナリを RCE
# 経路として探さない) との整合も含め、2026-07-31 の security-reviewer が CRITICAL とした経路。
# 照合と起動を verify_allow.py の同一プロセスに寄せてある — hook 側で照合してから別途実行すると
# 照合後・実行前の差し替え窓 (TOCTOU) が開く (同日の python-reviewer が HIGH として指摘)
ALLOW="$HOME/.claude/scripts/hooks/verify_allow.py"
if [[ ! -f "$ALLOW" ]]; then
  printf '[verify-precommit] 承認台帳 (%s) が無いためゲートを実行しません\n' "$ALLOW" >&2
  exit 0
fi

# 契約上 --staged は数秒で返る。ハングでセッションを固めないよう上限を掛ける。
# macOS 標準には timeout も gtimeout も無い (Homebrew coreutils 由来) ので、
# **どちらも無い場合は素で実行する**。空配列を "${runner[@]}" で参照すると macOS 標準の
# bash 3.2 + set -u で unbound variable になり、ゲート未実行のまま全 commit を block する
# 偽 FAIL になる (2026-07-31 の code-reviewer が HIGH として実証。bash 4.4 未満の既知の罠)。
# -k はハンドラを無視する子への SIGKILL 猶予
# cwd を repo root にして呼ぶ (hook の cwd は commit 対象 repo とは限らない)
if command -v timeout >/dev/null 2>&1; then
  out=$(timeout -k 10 120 python3 "$ALLOW" run "$toplevel" --staged 2>&1)
elif command -v gtimeout >/dev/null 2>&1; then
  out=$(gtimeout -k 10 120 python3 "$ALLOW" run "$toplevel" --staged 2>&1)
else
  out=$(python3 "$ALLOW" run "$toplevel" --staged 2>&1)
fi
rc=$?

[[ $rc -eq 0 ]] && exit 0

# 70-73 は承認台帳側の拒否 = ゲート未実行。原因ごとに次の一手が違うので出し分ける
case $rc in
  70|71)
    printf '[verify-precommit] %s\n  ゲートを実行しませんでした。内容を読んで問題なければ承認してください:\n    python3 %s approve %s\n' \
      "$out" "$ALLOW" "$toplevel" >&2
    exit 0 ;;
  72)
    printf '[verify-precommit] %s\n  ゲートの経路が不正です (repo 外を指す symlink 等)。承認ではなく調査してください: %s\n' \
      "$out" "$GATE" >&2
    exit 0 ;;
  73)
    printf '[verify-precommit] %s\n  承認台帳が壊れています。ゲートは実行していません\n' "$out" >&2
    exit 0 ;;
esac

if [[ $rc -eq 2 ]]; then
  # 検査不能: 止めないが黙らない (眠っているゲートは、無いゲートより危険)
  printf '[verify-precommit] %s の機械ゲートが検査不能 (exit 2)。commit は通します:\n%s\n' \
    "$toplevel" "$out" >&2
  exit 0
fi

if [[ $rc -eq 124 || $rc -eq 137 ]]; then
  printf '[verify-precommit] %s --staged が 120s で timeout。契約 (数秒) を満たしていません\n' "$GATE" >&2
  exit 0
fi

# JSON は **全体を python3 で組み立てる**。gate 出力だけをエスケープして path や rc を
# 生で printf に流すと、`"` や `\` を含むパスで JSON が壊れる (壊れた block 指示が消費側で
# 落ちれば fail-open になる — 2026-07-31 の code-reviewer が MEDIUM として指摘)
payload=$(GATE="$GATE" RC="$rc" OUT="$out" python3 -c '
import json, os
print(json.dumps({
    "decision": "block",
    "reason": (
        "[verify] repo の機械ゲートが FAIL ({} --staged, exit {})。"
        "修正して再 stage してください。偽陽性ならユーザーに確認のうえ、"
        "コマンド文字列の先頭に VERIFY_BYPASS=1 を付けてください。\n{}"
    ).format(os.environ["GATE"], os.environ["RC"], os.environ["OUT"]),
}, ensure_ascii=False))
') || payload='{"decision":"block","reason":"[verify] gate FAILED but JSON assembly failed — run .claude/verify.sh --staged manually"}'
printf '%s\n' "$payload"
exit 0

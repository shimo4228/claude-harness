#!/usr/bin/env bash
# task-claims-reminder.sh — PostToolUse hook (Read | Grep | Bash)
#
# 台帳 (.notes/TASKS.md) を読んだ瞬間に「誰が何を握っているか」と claim の作法を出す。
#
# なぜ hook か: claim を積むのが規約だけだと静かに忘れられる。rules/README.md の
# 採用基準どおり「発火時刻を要する検査は hook」。同じ理由で episode-log ガードも
# rule でなく hook になっている。
#
# なぜ 3 経路か: 台帳は Read だけでなく Bash の grep / sed でも読まれる。実際
# 2026-08-15 のセッションは Bash grep でしか台帳に触れておらず、Read だけを見張る
# 版なら素通りしていた。episode-log ガードが Read / Grep / Bash の 3 本立てなのと
# 同じ理由。
#
# 出力は情報（開いている claim）が主で、注意書きが従。ただの小言は読まれなくなる。
#
# 入力: stdin から JSON (tool_input)
# 出力: stdout に数行 (= additional context)。何も言うことが無ければ無音。
# 失敗: 常に exit 0。この hook が壊れてもセッションを止めない。

set -uo pipefail

HELPER="$HOME/.claude/scripts/claims.py"

INPUT=$(cat 2>/dev/null) || exit 0
[ -n "$INPUT" ] || exit 0

# 安い prefilter。この hook は Read | Grep | Bash という harness で最も頻度の高い matcher に
# 付いており、その大多数は台帳に触れない。生文字列の判定を先に置いて、その経路で jq を
# 起動しない (実測 14.1ms → 4.8ms)。厳密判定は下の TOUCHED が同じ glob で行う。
# 生 JSON を見るので、payload が path を JSON escape (`TASKS.md`) で送ってきた場合
# だけ取りこぼす — JSON serializer は ASCII 英字を escape しないので現状到達しない。
# advisory 専用の hook なので、取りこぼす方向の誤りは安全側。
case "$INPUT" in
  *TASKS.md* | *rfcs/*) ;;
  *) exit 0 ;;
esac

# 台帳に触れたか。Read の file_path / Grep の path / Bash の command を横断で見る。
# jq が無い環境でも黙って諦める (exit 0)。
command -v jq >/dev/null 2>&1 || exit 0
TOUCHED=$(printf '%s' "$INPUT" | jq -r '
  [ .tool_input.file_path? // empty,
    .tool_input.path?      // empty,
    .tool_input.command?   // empty ] | join(" ")
' 2>/dev/null) || exit 0

case "$TOUCHED" in
  *TASKS.md* | *rfcs/*) ;;
  *) exit 0 ;;
esac

# repo root は helper と同じ順で解決する (CLAUDE_PROJECT_DIR → git → cwd)。
# **この値は「ディレクトリが在るか」を見るためだけに使う。** repo 由来のパスから
# コードを実行してはならない: hook は tool permission を通らず、この hook は
# `TASKS.md` という文字列を含む Bash コマンドだけでも発火するので、`$ROOT/scripts/…`
# を実行する版は敵対的 repo にとって無条件の RCE になる (2026-08-15 security review
# CRITICAL、実証済み)。repo-local コードを信頼する必要が出たときは、
# `scripts/hooks/verify_allow.py` の内容 hash 承認 (rules/common/security.md) を通す。
ROOT="${CLAUDE_PROJECT_DIR:-}"
# 敵対的 .git/config の無害化 (ADR-0034 の T-GIT-HOSTILE-CONFIG 横展開)。
# rev-parse は index を読まないので実測では fsmonitor は起動しない
# (2026-08-29 実測: rev-parse 0 回 / ls-files 2 回 / status 2 回)。live な穴の
# 塞ぎではなく、git を呼ぶ兄弟 hook と形を揃えるための defense-in-depth
# (harness-lint-precommit.sh:42 / verify-precommit.sh:50 と同形)。
[ -d "$ROOT" ] || ROOT=$(git -c core.fsmonitor= -c core.hooksPath= \
  rev-parse --show-toplevel 2>/dev/null) || ROOT="$PWD"
RFCS="$ROOT/rfcs"

OUT=""
add() { OUT="${OUT}${1}
"; }

# --- 情報を先に。小言だけの hook は読まれなくなる ---
if [ -f "$HELPER" ]; then
  OPEN=$(python3 "$HELPER" open --oneline 2>/dev/null) || OPEN=""
  [ -n "$OPEN" ] && add "[claims] $OPEN"
fi

# --- 注意書きは従 ---
# **repo 相対の実行可能パスをここに書かない。** 上の guard は hook が
# `$ROOT/scripts/…` を実行することを止めたが、実行しろと**言う**ことは止めない。
# この行はかつて `python3 scripts/tasks.py ready` を渡していて、発火条件は
# 「$ROOT/.notes/tasks/ がディレクトリである」だけ — 敵対的 repo はそれを同梱できる。
# hook は tool 出力より信用される経路なので、閉じたはずの RCE の 1 段先に同じ境界が
# 開いていた（2026-08-15 security review HIGH、実証済み）。コマンド名の正本は
# 常駐 rule `common/task-tracking.md` 側にあるので、ここからは指さない。
# `~/.claude/…` の絶対パス（下の claims.py）は harness 所有なのでこの制約の外。
# 旧 store .notes/tasks/ の案内は 2026-08-25 に畳んだ（全 repo 移送完了、RFC-0001）。
if [ -d "$RFCS" ]; then
  add "[tasks] store 形の台帳は rfcs/NNNN-slug.md（1 タスク 1 ファイル、ID は RFC-NNNN。ADR-0049）。全件を開かず python3 ~/.claude/scripts/claims.py ready で問う"
fi
if [ -f "$HELPER" ]; then
  add "[claims] 着手するなら先に claim を積む: python3 ~/.claude/scripts/claims.py claim T-XXX --label \"...\""
  # フラグ列挙を持たない（複製した版は --producer 追加に追随せず、最頻の形が
  # 必ず refusal に当たる状態になっていた。ADR-0041 / 2026-08-16 code review HIGH）
  add "[claims] 起票したら系譜も: claims.py spawn（review 由来は --producer PATH:LINE が要る）"
fi

[ -n "$OUT" ] || exit 0

# 封筒の形と、それを 2 度間違えた経緯は hooks/_advisory-common.sh のヘッダが正本。
# 実際に喋る 1 回だけが読み込みの代金を払う。
# shellcheck source=hooks/_advisory-common.sh
source "${BASH_SOURCE[0]%/*}/_advisory-common.sh" || exit 0
printf '%s' "$OUT" | emit_advisory_stream PostToolUse
exit 0

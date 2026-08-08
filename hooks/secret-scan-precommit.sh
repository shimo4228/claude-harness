#!/usr/bin/env bash
# secret-scan-precommit.sh — PreToolUse hook (Bash): git commit 前の secret scan
# rules/common/security.md「No hardcoded secrets before ANY commit」+
# planning.md Verify ステップ 5 (secret scan) の決定論的実装。
#
# 入力: stdin から JSON (tool_input.command)
# 出力: staged diff の追加行に secret 検出時 { "decision": "block", ... }、それ以外は無出力 (= allow)
# バイパス: コマンド文字列の**先頭** (env prefix 位置) に SECRET_SCAN_BYPASS=1 を明示
# (テストフィクスチャ等の偽陽性時にユーザー判断で。会話ログに残るので監査可能。
# hook プロセスの env はツール呼び出しの env prefix を継承しないため、コマンド文字列
# 検査で実装する。位置非依存の部分文字列一致にしない — コミットメッセージ内の言及
# だけで無効化されるのを防ぐ。2026-07-25 security review)

set -euo pipefail

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || COMMAND=""

[[ -z "$COMMAND" ]] && exit 0
printf '%s' "$COMMAND" | grep -qE '^([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*SECRET_SCAN_BYPASS=1([[:space:]]|$)' && exit 0

# git commit を含むコマンドのみ対象。under-match (env prefix / 先頭空白で skip される)
# の方が over-match (無関係コマンドで余計に 1 回スキャンが走る) より危険なので、
# \b アンカーで広めに取る。パイプ区切り (;|&) は跨がない — "git log | grep commit" 除外。
# "--grep=commit" は commit 直前が空白でないため除外。
printf '%s' "$COMMAND" | grep -qE '\bgit\b[^;|&]*[[:space:]]commit\b' || exit 0

# 対象 repo の特定: `git -C <path> ... commit` > 先頭の `cd <path> &&` > カレント。
# -C 抽出は **コマンド文字列の先頭** (env prefix 位置のみ許容) に固定する。旧実装は
# 区切り (;&|) 直後も許していたが、bash は引用符を解釈しないため
# `git commit -m "notes; git -C /tmp status commit x"` のようにコミットメッセージ内の
# 文字列で対象 repo を乗っ取れた (2026-07-31 の code-reviewer が PoC 付きで実証。
# 旧コメントの「引用符内の git -C で乗っ取られない」は誤りだった)。
# 抽出は共有部品に集約 (5 hook で複製していた正規表現の drift 解消。エスケープと引用符 span を
# 除去してからセグメント解析する — 詳細と限界は _git-target-common.sh のヘッダ)。
# **単一値でなく全一致を走査する**: 単一値だと複合コマンドの片方しか見ず、左端固定でも
# 右端固定でも順序を入れ替えるだけで検査されない側へ commit を寄せられる (2026-08-08 の
# 公開前レビューが両方向を実証)。この hook は読み取りだけなので、全 repo を走査して閉じる。
# shellcheck source=hooks/_git-target-common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_git-target-common.sh"
repos=()
while IFS= read -r d; do
  [[ -n "$d" && -d "$d" ]] && repos+=("$d")
done < <(git_target_dirs "$COMMAND")
# 1 件も取れなければカレント repo を 1 件として扱う (空文字 = -C を付けない)
(( ${#repos[@]} )) || repos=("")

# 敵対的 .git/config の無害化 (ADR-0034 の T-GIT-HOSTILE-CONFIG 横展開):
# core.fsmonitor / core.hooksPath は repo 内 config で任意コマンド実行になるため明示無効化。
# diff.external は空文字にすると git が空コマンドを実行しようとして diff 自体が壊れるので、
# config ではなく diff 呼び出し側の --no-ext-diff で外部 diff driver を封じる。
# **--no-textconv も要る**: --no-ext-diff は diff.<driver>.textconv を止めない。external を
# 封じた結果 textconv が表に出て、repo 内 .git/config + .gitattributes から任意コマンドが
# 実行される状態だった (2026-08-08 の公開前レビューが実証。ADR-0037 の「同種を全掃」は
# この兄弟ベクタを取りこぼしていた)。
# quotepath=off は非 ASCII パスの 8 進エスケープを止める (ls-files の出力パスでファイルを
# 読むため、引用されると未追跡スキャンが無音で欠ける)
GIT_SAFE=(-c core.fsmonitor= -c core.hooksPath= -c core.quotepath=off)
DIFF_SAFE=(--no-ext-diff --no-textconv)

# --- スキャン対象の決定 ---------------------------------------------------
# PreToolUse なので、この hook は**コマンド実行前**に走る。staged diff だけを見ると
# `git commit -am` と `git add -A && git commit` は「まだ何も staged でない」状態で
# 評価され、無言で allow されていた (2026-07-25 security scan F7)。宣言上この hook が
# 唯一の決定論的 secret gate なので、対象は「今 staged か」でなく
# **「このコマンドが何をコミットするか」** から導く。
stages_in_call=0
# `-a` / `-am` / `-ma` (combined short flags)。`--amend` は `-` の直後が `a` でないので
# 誤検知しない。`--all` は別途。
printf '%s' "$COMMAND" | grep -qE '\bgit\b[^;|&]*[[:space:]]commit\b[^;|&]*[[:space:]]-[a-zA-Z]*a' && stages_in_call=1
printf '%s' "$COMMAND" | grep -qE '\bgit\b[^;|&]*[[:space:]]commit\b[^;|&]*[[:space:]]--all\b' && stages_in_call=1
add_re='(^|[;&|])[[:space:]]*git[[:space:]]+([^;&|]*[[:space:]])?add[[:space:]]+([^;&|]*)'
[[ "$COMMAND" =~ $add_re ]] && stages_in_call=1

# 未追跡を巻き込むのは `git add -A` / `add .` / `add --all` だけ。`commit -a` は
# **追跡ファイルの変更のみ**なので未追跡は対象外 (ここを混ぜると無関係な未追跡ファイルの
# secret で正当なコミットが止まり、偽陽性がこの gate の遵守率を直接下げる)。
# パス指定の `git add <paths>` はそのパスだけを見る。いずれもコマンド文字列だけで決まるので
# repo ループの外で 1 度だけ判定する。
sweep_all=0
printf '%s' "$COMMAND" | grep -qE '\bgit[^;&|]*[[:space:]]add[[:space:]]+(-A\b|--all\b|\.([[:space:]]|$))' && sweep_all=1

added=""
for repo_dir in "${repos[@]}"; do
  git_cmd=(git "${GIT_SAFE[@]}")
  [[ -n "$repo_dir" ]] && git_cmd=(git "${GIT_SAFE[@]}" -C "$repo_dir")

  staged=$("${git_cmd[@]}" diff "${DIFF_SAFE[@]}" --cached 2>/dev/null | grep '^+' | grep -v '^+++' || true)
  [[ -n "$staged" ]] && added=$(printf '%s\n%s' "$added" "$staged")

  [[ $stages_in_call -eq 1 ]] || continue

  # 追跡ファイルの未 staged 変更 (`commit -a` / `git add` が取り込む)
  unstaged=$("${git_cmd[@]}" diff "${DIFF_SAFE[@]}" 2>/dev/null | grep '^+' | grep -v '^+++' || true)
  [[ -n "$unstaged" ]] && added=$(printf '%s\n%s' "$added" "$unstaged")

  untracked_files=()
  if [[ $sweep_all -eq 1 ]]; then
    while IFS= read -r f; do [[ -n "$f" ]] && untracked_files+=("$f"); done \
      < <("${git_cmd[@]}" ls-files --others --exclude-standard 2>/dev/null || true)
  elif [[ "$COMMAND" =~ $add_re ]]; then
    for p in ${BASH_REMATCH[3]}; do
      [[ "$p" == -* ]] && continue
      untracked_files+=("$p")
    done
  fi

  base_dir="${repo_dir:-.}"
  for f in "${untracked_files[@]:-}"; do
    [[ -n "$f" ]] || continue
    target="$f"
    [[ "$target" != /* ]] && target="$base_dir/$target"
    [[ -f "$target" ]] || continue
    # diff の追加行と同じ形 (行頭 +) に揃える
    content=$(sed 's/^/+/' "$target" 2>/dev/null || true)
    [[ -n "$content" ]] && added=$(printf '%s\n%s' "$added" "$content")
  done
done

# ここまでで対象が空なら、このコマンドは本当に何もコミットしない (例:
# `commit --amend --no-edit`)。allow してよい。
# NOTE: bash の ${var//[[:space:]]/} はマルチバイト長文で O(n²)（CJK 22K 字の diff で
# 数分 CPU を焼いた実測 2026-07-27）。grep 判定で等価・定数時間にする。
printf '%s' "$added" | grep -q '[^[:space:]]' || exit 0

block() {
  # python3 が失敗しても block を握りつぶさない (検出済みで落ちると fail-open になる)
  escaped=$(printf '%s' "$1" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read())[1:-1])') \
    || escaped="(secret findings present but output escaping failed — inspect staged diff manually)"
  printf '{"decision":"block","reason":"[secret-scan] potential secrets in staged diff. Remove them (use env vars / secret manager). If these are verified false positives, ask the user, then prefix the command string with SECRET_SCAN_BYPASS=1.\\n%s"}' "$escaped"
  exit 0
}

# 1) detect-secrets があれば優先 (permissions 許可済みツール)
# 注意: detect-secrets 1.5.0 は絶対パス指定だと results が空になる (file filter が
# 相対パス前提) ため、tmpdir に cd して basename でスキャンする
if command -v detect-secrets >/dev/null 2>&1; then
  tmpdir=$(mktemp -d)
  trap 'rm -rf "$tmpdir"' EXIT
  printf '%s\n' "$added" > "$tmpdir/staged-additions"
  results=$(cd "$tmpdir" && detect-secrets scan staged-additions 2>/dev/null | jq -r '.results | to_entries[]?.value[]? | "\(.type) (line \(.line_number))"' || true)
  [[ -n "$results" ]] && block "detect-secrets findings:
$results"
  exit 0
fi

# 2) fallback: 高確度パターンの regex スキャン
hits=$(printf '%s\n' "$added" | grep -nE \
  -e 'AKIA[0-9A-Z]{16}' \
  -e '-----BEGIN [A-Z ]*PRIVATE KEY-----' \
  -e 'ghp_[A-Za-z0-9]{36}' \
  -e 'github_pat_[A-Za-z0-9_]{22,}' \
  -e 'sk-[A-Za-z0-9_-]{20,}' \
  -e 'xox[baprs]-[A-Za-z0-9-]{10,}' \
  -e 'AIza[0-9A-Za-z_-]{35}' \
  -e '(api[_-]?key|secret|password|token)["'"'"']?\s*[:=]\s*["'"'"'][A-Za-z0-9+/_-]{16,}["'"'"']' \
  || true)
[[ -n "$hits" ]] && block "regex findings (added lines):
$hits"

exit 0

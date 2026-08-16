#!/usr/bin/env bash
# ruff-format-precommit.sh — PreToolUse hook (Bash): git commit 前の staged .py への format check
# commit 境界の決定論的 format gate。
#
# 旧 ruff-autofix.sh (PostToolUse, 毎編集で format + autofix) の後継。毎編集の自動書き換えは
# 「import 追加 Edit → 使用箇所追加 Edit」の間に F401 が import を削除するレースを作った
# (2026-07-28 に 3 回実測)。整形の実行は Verify ステップ (planning.md) に移し、この hook は
# **検査のみ** (ruff format --check) を commit 境界で決定論的に保証する。enumerate/decide 分割
# 検出は hook、修正は編集ループ側。
#
# 入力: stdin から JSON (tool_input.command)
# 出力: staged .py (index 内容) に未整形ファイル検出時 { "decision": "block", ... }、
#       それ以外は無出力 (= allow)
# バイパス: コマンド文字列の**先頭** (env prefix 位置) に RUFF_FORMAT_BYPASS=1 を明示
# (ユーザー判断で。会話ログに残るので監査可能。位置非依存の部分文字列一致にしない —
# コミットメッセージ内の言及だけで無効化されるのを防ぐ)

set -euo pipefail

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || COMMAND=""

[[ -z "$COMMAND" ]] && exit 0
printf '%s' "$COMMAND" | grep -qE '^([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*RUFF_FORMAT_BYPASS=1([[:space:]]|$)' && exit 0

# git commit を含むコマンドのみ対象 (secret-scan-precommit.sh と同一のマッチ規則)。
# パイプ区切り (;|&) は跨がない — "git log | grep commit" 除外
printf '%s' "$COMMAND" | grep -qE '\bgit\b[^;|&]*[[:space:]]commit\b' || exit 0

# 対象 repo の特定: `git -C <path> ... commit` > 先頭の `cd <path> &&` > カレント。
# -C 抽出は **コマンド文字列の先頭** (env prefix 位置のみ許容) に固定する。旧実装は
# 区切り (;&|) 直後も許していたが、bash は引用符を解釈しないため
# `git commit -m "notes; git -C /tmp status commit x"` のようにコミットメッセージ内の
# 文字列で対象 repo を乗っ取れた (2026-07-31 の code-reviewer が PoC 付きで実証。
# 旧コメントの「引用符内の git -C で乗っ取られない」は誤りだった)。
# 先頭固定でこの経路は塞がるが、regex による shell 解析には原理的限界があるので、
# 実行を伴う経路 (verify-precommit.sh) は承認台帳を第 2 の防壁として持つ
# 抽出は共有部品に集約 (5 hook で複製していた正規表現の drift 解消。エスケープと引用符 span を
# 除去してからセグメント解析する — 詳細と限界は _git-target-common.sh のヘッダ)。
# **単一値でなく全一致を走査する** — 理由は secret-scan-precommit.sh と同じ (順序の入れ替えで
# 検査されない側へ commit を寄せられる)。この hook も読み取りだけなので全 repo を走査する。
# shellcheck source=hooks/_git-target-common.sh
source "${BASH_SOURCE[0]%/*}/_git-target-common.sh"
repos=()
while IFS= read -r d; do
  [[ -n "$d" && -d "$d" ]] && repos+=("$d")
done < <(git_target_dirs "$COMMAND")
(( ${#repos[@]} )) || repos=("")

# 敵対的 .git/config の無害化 (ADR-0034 の T-GIT-HOSTILE-CONFIG 横展開):
# core.fsmonitor / core.hooksPath は repo 内 config で任意コマンド実行になるため封じる。
# diff.external は空 config にすると diff が壊れるので diff 呼び出し側の --no-ext-diff で封じ、
# --no-textconv で diff.<driver>.textconv も封じる (--no-ext-diff だけでは止まらない。
# 2026-08-08 の公開前レビューが実証 — 詳細は secret-scan-precommit.sh のヘッダ)
GIT_SAFE=(-c core.fsmonitor= -c core.hooksPath= -c core.quotepath=off)
DIFF_SAFE=(--no-ext-diff --no-textconv)

# 走査対象の絞り込み。repo が自前の機械ゲート (.claude/verify.sh) を持っていれば、そちらに譲る。
# format の版・rule set は repo が所有すべきで、harness 側の固定値と二重に効かせない
# (verify-precommit.sh が同じ commit で実行する)。全 Python repo の移行が済んだら本 hook は退役。
# NOTE: この譲りは **承認台帳を見ない** — 実行権があるだけで譲る (bandit-precommit.sh と同じ)
scan_repos=()
for repo_dir in "${repos[@]}"; do
  git_cmd=(git "${GIT_SAFE[@]}")
  [[ -n "$repo_dir" ]] && git_cmd=(git "${GIT_SAFE[@]}" -C "$repo_dir")
  toplevel=$("${git_cmd[@]}" rev-parse --show-toplevel 2>/dev/null) || toplevel=""
  [[ -n "$toplevel" && -x "$toplevel/.claude/verify.sh" ]] && continue
  # staged .py のみ (追加/コピー/変更/リネーム。削除は対象外)。repo 外なら fail-soft
  staged_py=$("${git_cmd[@]}" diff "${DIFF_SAFE[@]}" --cached --name-only --diff-filter=ACMR -- '*.py' 2>/dev/null || true)
  [[ -z "$staged_py" ]] && continue
  scan_repos+=("$repo_dir")
done
(( ${#scan_repos[@]} )) || exit 0

# ruff 解決: PATH → uvx (repo 内 .venv バイナリは RCE 経路になるため意図的に探さない —
# bats-autorun.sh / bandit-precommit.sh と同じ方針)。uvx 経由は supply chain を固定する
# ため版を pin する (bump は手動)
if command -v ruff >/dev/null 2>&1; then
  ruff_cmd=(ruff)
else
  uvx_bin="$HOME/.local/bin/uvx"
  if command -v uvx >/dev/null 2>&1; then
    uvx_bin=$(command -v uvx)
  fi
  if [[ -x "$uvx_bin" ]]; then
    ruff_cmd=("$uvx_bin" 'ruff==0.16.0')
  else
    # fail-soft だが無音にしない (ゲートが眠っていることを可視化)
    echo "[ruff-format-precommit] ruff / uvx が見つからないため format check をスキップ" >&2
    exit 0
  fi
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# repo ごとに展開して走査する。混ぜられないのは同名パスの衝突だけでなく **ruff 設定**も
# repo ごとに違うため — 1 つの木に混ぜると片方の line-length で他方を判定してしまう
results=""
idx=0
for repo_dir in "${scan_repos[@]}"; do
  idx=$((idx + 1))
  dest="$tmpdir/r$idx"
  mkdir -p "$dest"
  git_cmd=(git "${GIT_SAFE[@]}")
  [[ -n "$repo_dir" ]] && git_cmd=(git "${GIT_SAFE[@]}" -C "$repo_dir")
  staged_py=$("${git_cmd[@]}" diff "${DIFF_SAFE[@]}" --cached --name-only --diff-filter=ACMR -- '*.py' 2>/dev/null || true)

  # index の内容を相対パス構造ごと展開 (部分 staged で working tree 版を見ない —
  # bandit-precommit.sh と同じ理由)
  count=0
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    [[ "$f" == *..* ]] && continue
    mkdir -p "$dest/$(dirname "$f")"
    if "${git_cmd[@]}" show ":$f" > "$dest/$f" 2>/dev/null; then
      count=$((count + 1))
    fi
  done <<< "$staged_py"
  [[ "$count" -eq 0 ]] && continue

  # repo の ruff 設定も index 優先で展開 (tmpdir 実行では自動発見されないため。設定なしの
  # 既定値で判定すると line-length 等が異なる repo で偽陽性 block になる)
  for cfg in pyproject.toml ruff.toml .ruff.toml; do
    "${git_cmd[@]}" show ":$cfg" > "$dest/$cfg" 2>/dev/null || true
    [[ -s "$dest/$cfg" ]] || rm -f "$dest/$cfg"
  done

  # --check は書き換えず判定のみ。判定は **exit code** で行う — 出力形式は版で変わる
  # (0.14 系 "Would reformat: <path>" → 0.16 系 "unformatted: ... --> <path>:1:1")。
  # テキスト形式に依存した grep 判定は 0.16 で無音の fail-open になった (2026-07-28 の
  # 違反注入テストで実証)。構文エラー等で format 自体が失敗した場合も block 側に倒す
  # (壊れた .py の commit はどのみち止めるべき)
  set +e
  check_out=$(cd "$dest" && "${ruff_cmd[@]}" format --check . 2>&1)
  check_rc=$?
  set -e
  [[ $check_rc -eq 0 ]] && continue

  # reason 向けの抽出 (対象パス行 + summary)。形式が全滅しても raw 出力先頭で代替
  repo_results=$(printf '%s\n' "$check_out" \
    | grep -E '^(Would reformat|[[:space:]]*-->|[0-9]+ files? would be reformatted|error)' || true)
  # `|| true` は SIGPIPE (T-SIGPIPE-HEAD-PIPE): head が 20 行で閉じると printf が rc=141 になり、
  # set -e で hook ごと落ちて block を出さずに fail-open していた
  [[ -z "$repo_results" ]] && { repo_results=$(printf '%s\n' "$check_out" | head -20 || true); }
  # 複数 repo のときだけ出所を前置する (単一 repo の出力は従来と同一に保つ)。
  # sed の置換文字列に path を埋めない — 区切り文字を含む path で壊れる
  if (( ${#scan_repos[@]} > 1 )); then
    repo_results=$(printf '%s\n' "$repo_results" \
      | while IFS= read -r line; do printf '%s: %s\n' "${repo_dir:-.}" "$line"; done)
  fi
  results=$(printf '%s\n%s' "$results" "$repo_results")
done
results=$(printf '%s' "$results" | grep -v '^[[:space:]]*$' || true)
[[ -z "$results" ]] && exit 0

# python3 が失敗しても block を握りつぶさない (検出済みで落ちると fail-open になる)
escaped=$(printf '%s' "$results" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read())[1:-1])') \
  || escaped="(unformatted files present but output escaping failed — run ruff format --check manually)"
printf '{"decision":"block","reason":"[ruff-format] staged .py files are not formatted. Run the Verify format step (ruff format <files>), re-stage, and retry. If blocking is wrong here, ask the user, then prefix the command string with RUFF_FORMAT_BYPASS=1.\\n%s"}' "$escaped"
exit 0

#!/usr/bin/env bash
# bandit-precommit.sh — PreToolUse hook (Bash): git commit 前の staged .py への bandit scan
# rules/common/security.md に記録した暫定 Python security gate (T-007)。
#
# 入力: stdin から JSON (tool_input.command)
# 出力: staged .py (index 内容) に MEDIUM+ 検出時 { "decision": "block", ... }、それ以外は無出力 (= allow)
#
# 設計判断 (.notes/t-004-builtin-review-surface.md で実測済み):
# - 閾値は -ll -ii (MEDIUM+ severity / MEDIUM+ confidence)。-lll (HIGH のみ) だと
#   B608 (SQL injection) / B307 (eval) / B301 (pickle) / B506 (yaml unsafe load) が全て漏れる。
#   LOW を含めると B101 (assert) がテストで大量発火する。hardcoded credentials
#   (B105/B106, LOW) は secret-scan-precommit.sh が別途カバー
# - working tree でなく index を見る: git show ":$f" で staged 内容を展開してから走らせる
#   (部分 staged のファイルで working tree 版を読むと検出を取りこぼす)
# - bandit 解決: PATH → uvx (repo 内 .venv バイナリは RCE 経路になるため意図的に探さない
#   — ruff-format-precommit.sh と同じ方針)。どちらも不在なら fail-soft (ゲート不在で commit を
#   止めるとハーネス全体が使えなくなる)
# - mapfile は使わない (macOS 標準 /bin/bash 3.2 に不在)
# バイパス: コマンド文字列の**先頭** (env prefix 位置) に BANDIT_SCAN_BYPASS=1 を明示
# (偽陽性時にユーザー判断で。会話ログに残るので監査可能。位置非依存の部分文字列一致に
# しない — コミットメッセージ内の言及だけで無効化されるのを防ぐ)

set -euo pipefail

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || COMMAND=""

[[ -z "$COMMAND" ]] && exit 0
printf '%s' "$COMMAND" | grep -qE '^([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*BANDIT_SCAN_BYPASS=1([[:space:]]|$)' && exit 0

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
source "$(dirname "${BASH_SOURCE[0]}")/_git-target-common.sh"
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
# 閾値 (-ll -ii) と除外は repo が所有すべきで、harness 側の固定値と二重に効かせない
# (verify-precommit.sh が同じ commit で実行する)。全 Python repo の移行が済んだら本 hook は退役。
# NOTE: この譲りは **承認台帳を見ない** — 実行権があるだけで譲る。未承認の verify.sh を持つ
# repo では verify / bandit / ruff-format が同時に黙る (公開 doc に明記済み)
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

# bandit 解決: PATH → uvx (hook subprocess は interactive shell と PATH が違いうるので
# ruff-format-precommit.sh と同じく ~/.local/bin/uvx への hardcoded fallback を持つ)。
# uvx 経由は supply chain を固定するため版を pin する (bump は手動)
if command -v bandit >/dev/null 2>&1; then
  bandit_cmd=(bandit)
else
  uvx_bin="$HOME/.local/bin/uvx"
  if command -v uvx >/dev/null 2>&1; then
    uvx_bin=$(command -v uvx)
  fi
  if [[ -x "$uvx_bin" ]]; then
    bandit_cmd=("$uvx_bin" 'bandit==1.9.4')
  else
    # fail-soft だが無音にしない (ゲートが眠っていることを可視化)
    echo "[bandit-precommit] bandit / uvx が見つからないため Python security scan をスキップ" >&2
    exit 0
  fi
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# repo ごとに index の内容を相対パス構造ごと展開して走査する (repo をまたいで 1 つの木に
# 混ぜると、同名パスが衝突して片方が黙って消える)
results=""
idx=0
for repo_dir in "${scan_repos[@]}"; do
  idx=$((idx + 1))
  dest="$tmpdir/r$idx"
  mkdir -p "$dest"
  git_cmd=(git "${GIT_SAFE[@]}")
  [[ -n "$repo_dir" ]] && git_cmd=(git "${GIT_SAFE[@]}" -C "$repo_dir")
  staged_py=$("${git_cmd[@]}" diff "${DIFF_SAFE[@]}" --cached --name-only --diff-filter=ACMR -- '*.py' 2>/dev/null || true)

  count=0
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    # git は track パスに .. を許さない (CVE-2014-9390 以降) が、dest 外への書き込み
    # 防止として belt-and-suspenders で明示ガード
    [[ "$f" == *..* ]] && continue
    mkdir -p "$dest/$(dirname "$f")"
    if "${git_cmd[@]}" show ":$f" > "$dest/$f" 2>/dev/null; then
      count=$((count + 1))
    fi
  done <<< "$staged_py"
  [[ "$count" -eq 0 ]] && continue

  # 複数 repo のときだけ出所を前置する (単一 repo の出力は従来と同一に保つ)
  prefix=""
  (( ${#scan_repos[@]} > 1 )) && prefix="${repo_dir:-.}: "
  repo_results=$(cd "$dest" && "${bandit_cmd[@]}" -r . -ll -ii -f json 2>/dev/null \
    | jq -r --arg p "$prefix" '.results[]? | "\($p)\(.filename | ltrimstr("./")):\(.line_number) [\(.test_id)] \(.issue_text)"' || true)
  [[ -n "$repo_results" ]] && results=$(printf '%s\n%s' "$results" "$repo_results")
done
results=$(printf '%s' "$results" | grep -v '^[[:space:]]*$' || true)
[[ -z "$results" ]] && exit 0

# python3 が失敗しても block を握りつぶさない (検出済みで落ちると fail-open になる)
escaped=$(printf '%s' "$results" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read())[1:-1])') \
  || escaped="(bandit findings present but output escaping failed — run bandit -ll -ii manually)"
printf '{"decision":"block","reason":"[bandit] MEDIUM+ security issues in staged .py (index content). Fix before commit. If these are verified false positives, ask the user, then prefix the command string with BANDIT_SCAN_BYPASS=1.\\n%s"}' "$escaped"
exit 0

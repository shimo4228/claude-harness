#!/usr/bin/env bash
# _git-target-common.sh — commit 対象 repo の抽出 (precommit 系 hook の共有部品)。
#
# 単体で実行するものではなく source して使う。5 hook が同じ正規表現を複製していた状態を
# 解消するために切り出した (複製は実際に drift した — harness-lint だけ限定条件が緩く、
# コメントは「対処済み」と誤った保証を書いていた。2026-07-31 の code-reviewer が指摘)。
#
# 抽出方針: **読み落とさないことを優先し、余分に拾うのは許す。** コマンド文字列を shell として
# 解析しない — 引用符・heredoc・コメントを解釈せず、生の文字列に現れる `-C <path>` と `cd <path>` の
# 行き先を全部候補として返し（実在の確認は呼び出し元）、最後にカレントディレクトリ ($PWD) を必ず足す。
# 余分な候補（コミットメッセージや heredoc の中の `git -C x`、`-C` の囮）は、読み取りだけの hook が
# 余計に 1 repo 検査するだけで済む。読み落としは検査の素通りになる（`-C` の先の本物の対象を見ずに
# cwd を検査する）。引用符を解釈する版は、解釈の穴がそのまま素通りになった（2026-07-31〜11-01 に
# 正規表現・awk の字句解析で計 4 方式を試し、いずれも新しい穴が見つかった）。
#
# 返すのは **候補の全 repo** (git_target_dirs)。単一値の git_target_dir は repo として解決できる
# 候補から 1 つ選ぶ wrapper で、ゲートを実行する verify-precommit.sh が使う (選び方は関数の上)。
# 囮で verify の対象がずれるとゲートは回らない — 承認台帳が止めるのは未承認コードの実行だけ。
#
# 残る限界: GIT_DIR / GIT_WORK_TREE の代入、`--git-dir` / `--work-tree`、`pushd`、未展開の変数 (`-C "$REPO"`) は
# 候補にならない ($PWD を検査する)。相対 path は前の候補でなく hook の cwd から解決する。

# git_target_dirs <command string> [verbs] — 候補の path を 1 行 1 件で返す（重複除去、出現順、
# 末尾に $PWD）。verbs は互換のために受け取るだけで使わない（verb を照合すると、照合の穴が読み落とし
# になる）。
git_target_dirs() {
  local cmd=$1 tok dir d seen
  local -a found=()
  # `-C` と `cd` の直後の 1 語: 引用符で囲んだ語（空白を含めてよい）か、空白・;&|()<> までの語。
  # 引用符は外す
  while IFS= read -r tok; do
    tok=${tok//\"/}; tok=${tok//\'/}
    dir=${tok/#\~/$HOME}
    [[ -n "$dir" && "$dir" != "$PWD" ]] || continue
    seen=0
    for d in ${found[@]+"${found[@]}"}; do [[ "$d" == "$dir" ]] && { seen=1; break; }; done
    (( seen )) || found+=("$dir")
  done < <(printf '%s\n' "$cmd" | grep -oE '(^|[^A-Za-z0-9_-])(-C|cd)[[:space:]]+("[^"]*"|'"'"'[^'"'"']*'"'"'|[^[:space:];&|()<>]+)' \
             | sed -E 's/^.*(-C|cd)[[:space:]]+//')
  printf '%s\n' ${found[@]+"${found[@]}"} "$PWD"
}

# git_target_dir <command string> [verbs] — 実行先を 1 つだけ返す (見つからなければ空 = 呼び出し元が $PWD)。
#
# **新しい呼び出し元は git_target_dirs を使うこと。** こちらは 1 つしか選べない呼び出し元
# (verify-precommit.sh — ゲートを実行するので対象を 1 つに決める) のための wrapper。選ぶのは、
# git の work tree として解決できる候補のうち、絶対 path (~ 展開後) の最後のもの。無ければ相対 path の
# 最後のもの。存在しない語 (`commit -C HEAD`、メッセージ中の `-C の…`、`cd -`) と、hook の cwd 基準で
# 偶然解決する相対語 (メッセージ中の `cd tests`) で実行先がずれないようにするため。
# 選ばれなかった対象のゲートは回らない。台帳が止めるのは未承認コードの実行であって、ゲートの
# 回し損ねではない。
git_target_dir() {
  local d abs="" rel=""
  while IFS= read -r d; do
    [[ "$d" == "$PWD" || ! -d "$d" ]] && continue
    git -c core.fsmonitor= -c core.hooksPath= -C "$d" rev-parse --is-inside-work-tree >/dev/null 2>&1 || continue
    if [[ "$d" == /* ]]; then abs=$d; else rel=$d; fi
  done < <(git_target_dirs "$@")
  printf '%s' "${abs:-$rel}"
}

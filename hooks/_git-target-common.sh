#!/usr/bin/env bash
# _git-target-common.sh — commit 対象 repo の抽出 (precommit 系 hook の共有部品)。
#
# 単体で実行するものではなく source して使う。5 hook が同じ正規表現を複製していた状態を
# 解消するために切り出した (複製は実際に drift した — harness-lint だけ限定条件が緩く、
# コメントは「対処済み」と誤った保証を書いていた。2026-07-31 の code-reviewer が指摘)。
#
# 抽出方針: **バックスラッシュ・エスケープを落とし、引用符で囲まれた span を除去してから**、
# セグメント (;&|) 単位で解析する。bash は引用符を解釈しないので、除去しないとコミット
# メッセージ内の文字列で対象 repo を乗っ取れる。エスケープを先に落とすのが要点で、残すと
# `\"` が span の終端に見え、その後ろが素のセグメントとして露出する (2026-08-08 の公開前
# レビューが実証。それ以前の実装は引用符 span しか落としておらず、この経路が開いていた)。
#
# 返すのは **一致した全 repo** (git_target_dirs)。単一値の git_target_dir は最後の一致を
# 返す薄い wrapper で、実行を伴う verify-precommit.sh のように 1 つしか選べない呼び出し元が使う。
# 単一値では、複合コマンドの一方だけが検査される状態を原理的に解消できない — 左端固定でも
# 右端固定でも、順序を入れ替えれば検査されない側に commit を寄せられる (2026-08-08 に両方向を
# 実証)。読み取りだけの hook は全件を走査することでこの非対称を閉じる。
#
# 残る限界: shell の完全な解析は regex では行えない。実行を伴う経路 (verify-precommit.sh) は
# **承認台帳を第 2 の防壁**として持ち、抽出が乗っ取られても未承認のゲートは実行されない。

# git_target_dirs <command string> [verbs] — 一致した repo path を 1 行 1 件で返す (重複除去、
# 出現順)。1 件も無ければ何も出力しない。
#
# verbs には**呼び出し元 hook の発火条件と同じ alternation** を渡す (既定: commit)。
# 発火条件だけを広げて抽出側を据え置くと、対象 repo が取れず抽出が空を返し、hook は
# `-C` の指定先ではなく**カレント repo を検査する**。呼び出し元は発火条件の文字列を変数に
# 持ち、grep と本関数の両方へ渡すこと (二重定義は必ず drift する)。
git_target_dirs() {
  local cmd=$1 verbs=${2:-commit} stripped seg dir d seen v_re s_re
  local -a found=()

  # verbs は正規表現へそのまま埋め込まれる。上の「呼び出し元は literal を渡す」は規約でしかなく、
  # 破る呼び出し元が現れると ERE の構文注入 (壊れたパターン / 破滅的 backtracking) の入口になる。
  # 規約は機構で担保する — 形が違えば最も狭い commit に落とす (2026-08-01 security-reviewer)
  v_re='^[a-z]+([|][a-z]+)*$'
  [[ "$verbs" =~ $v_re ]] || verbs=commit

  # 1) `\<char>` を落とす → 2) 引用符 span を落とす。この順序でないと D2 経路が開く (ヘッダ参照)
  stripped=$(printf '%s' "$cmd" | sed "s/\\\\.//g; s/'[^']*'//g; s/\"[^\"]*\"//g")

  # セグメント境界で分割してから照合する。分割済みなので、path と verb が同一セグメントに
  # あることは構造的に保証される (旧実装の [^;&|]* による近似が不要になる)
  s_re='^[[:space:]]*git[[:space:]]+-C[[:space:]]+([^[:space:]]+).*[[:space:]]('"${verbs}"')([[:space:]]|$)'
  # 供給側は `%s\n` であって `%s` ではない: 末尾に改行が無いと read は最終セグメントを
  # 読んだうえで非ゼロを返し、ループ本体が実行されないまま抜ける (単一セグメントのコマンドが
  # 丸ごと取りこぼされ、抽出は常に空になる)
  # 下の `tr ';&|'` 向けの抑止。ディレクティブは複合コマンド全体の前にしか置けないので
  # (`done` の直前に置くと SC1123 でパーサが停止する)、`while` の前でループ全体を覆う
  # shellcheck disable=SC2020  # 意図どおりの文字集合置換 (3 区切り文字 → いずれも改行)
  while IFS= read -r seg; do
    [[ "$seg" =~ $s_re ]] || continue
    dir="${BASH_REMATCH[1]/#\~/$HOME}"
    seen=0
    for d in ${found[@]+"${found[@]}"}; do
      [[ "$d" == "$dir" ]] && { seen=1; break; }
    done
    (( seen )) || found+=("$dir")
  done < <(printf '%s\n' "$stripped" | tr ';&|' '\n\n\n')

  # `-C` が 1 つも無い場合だけ、先頭の `cd <path> &&` を対象と見なす
  if (( ${#found[@]} == 0 )) && [[ "$stripped" =~ ^[[:space:]]*cd[[:space:]]+([^[:space:];&|]+) ]]; then
    found+=("${BASH_REMATCH[1]/#\~/$HOME}")
  fi

  (( ${#found[@]} )) && printf '%s\n' "${found[@]}"
  return 0
}

# git_target_dir <command string> [verbs] — 最後の一致を 1 つだけ返す (見つからなければ空)。
#
# **新しい呼び出し元は git_target_dirs を使うこと。** こちらは 1 つしか選べない呼び出し元
# (verify-precommit.sh — ゲートを実行するので対象を 1 つに決める必要がある) のための wrapper。
# 選ばれなかった対象は検査されない。verify にとってこれは「ゲートを回し損ねる」であって
# 「未承認コードを実行する」ではない — 承認台帳が第 2 の防壁として残る。
git_target_dir() {
  local last="" d
  while IFS= read -r d; do last=$d; done < <(git_target_dirs "$@")
  printf '%s' "$last"
}

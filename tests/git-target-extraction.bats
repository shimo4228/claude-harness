#!/usr/bin/env bats
# Tests for hooks/_git-target-common.sh — the shared "which repo is being committed"
# extractor used by every precommit hook.
# Run: bats ~/.claude/tests/git-target-extraction.bats
#
# 2026-07-31 の code-reviewer が PoC 付きで示した欠陥の回帰固定。7 hook が同じ正規表現を
# 複製しており、`(^|[;&|])` 起点の抽出が bash の引用符を解釈しないため、コミットメッセージ
# 内の文字列で対象 repo を乗っ取れた。逆に先頭固定だけにすると
# `git -C <repo> add -A && git -C <repo> commit` という git-workflow 規約の推奨形を
# 取りこぼす (実際に既存テスト 2 本が落ちて判明)。両立させるのが引用符 span の除去。
#
# ここが守るのは抽出そのもの。hook ごとの挙動は各 hook のテストが持つ。

load_extractor() {
  # shellcheck source=hooks/_git-target-common.sh
  source "$HOME/.claude/hooks/_git-target-common.sh"
}

@test "bare git -C ... commit resolves to that repo" {
  load_extractor
  run git_target_dir 'git -C /tmp/repo commit -m ok'
  [ "$output" = "/tmp/repo" ]
}

@test "git -C add && git -C commit resolves (the git-workflow spelling)" {
  load_extractor
  run git_target_dir 'git -C /tmp/repo add -A && git -C /tmp/repo commit -m ok'
  [ "$output" = "/tmp/repo" ]
}

@test "a git -C hidden inside a double-quoted commit message does not hijack the target" {
  load_extractor
  run git_target_dir 'git commit -m "notes; git -C /evil status commit x"'
  [ -z "$output" ]
}

@test "a git -C hidden inside a single-quoted commit message does not hijack the target" {
  load_extractor
  run git_target_dir "git commit -m 'notes; git -C /evil status commit x'"
  [ -z "$output" ]
}

@test "a real git -C wins over a decoy inside the message" {
  load_extractor
  run git_target_dir 'git -C /tmp/real commit -m "a; git -C /evil status commit x"'
  [ "$output" = "/tmp/real" ]
}

@test "leading cd is honored when no git -C is present" {
  load_extractor
  run git_target_dir 'cd /tmp/repo && git commit -m ok'
  [ "$output" = "/tmp/repo" ]
}

@test "a tilde in the extracted path is expanded" {
  load_extractor
  run git_target_dir 'git -C ~/somerepo commit -m ok'
  [ "$output" = "$HOME/somerepo" ]
}

@test "no git -C and no cd yields empty (caller falls back to cwd)" {
  load_extractor
  run git_target_dir 'git commit -m ok'
  [ -z "$output" ]
}

# --- verbs 引数 (2026-08-01 追加) -------------------------------------------
# 呼び出し元 hook の発火条件と抽出条件が二重定義で drift した欠陥の回帰
# (review-chain-notice は commit|revert|merge で発火するのに抽出は commit のみだった)。
# 1 test 1 assertion — bats は本体の最後の終了ステータスしか見ない。

@test "verbs defaults to commit (the 5 single-arg callers are unchanged)" {
  load_extractor
  run git_target_dir 'git -C /tmp/repo revert HEAD'
  [ -z "$output" ]
}

@test "a widened verbs list extracts the revert target" {
  load_extractor
  run git_target_dir 'git -C /tmp/repo revert HEAD' 'commit|revert|merge'
  [ "$output" = "/tmp/repo" ]
}

@test "a widened verbs list extracts the merge target" {
  load_extractor
  run git_target_dir 'git -C /tmp/repo merge topic' 'commit|revert|merge'
  [ "$output" = "/tmp/repo" ]
}

@test "a malformed verbs value falls back to commit instead of injecting into the regex" {
  load_extractor
  run git_target_dir 'git -C /tmp/repo revert HEAD' '.*'
  [ -z "$output" ]
}

@test "the commit fallback still works when verbs is malformed" {
  load_extractor
  run git_target_dir 'git -C /tmp/repo commit -m ok' '(((('
  [ "$output" = "/tmp/repo" ]
}

# --- バックスラッシュ・エスケープ (2026-08-08 追加) --------------------------
# 引用符 span の除去だけでは足りなかった: `\"` を残すと sed がそこを span の終端と見なし、
# 続く `; git -C <decoy> commit` が素のセグメントとして露出する。2026-08-08 の公開前レビューが
# secret gate の end-to-end バイパスとして実証した。エスケープを先に落とすことで閉じる。

@test "an escaped quote inside the message does not expose a decoy segment" {
  load_extractor
  run git_target_dir 'git commit -m "a \" ; git -C /evil commit x"'
  [ -z "$output" ]
}

@test "an escaped quote does not steal the target away from a real git -C" {
  load_extractor
  run git_target_dir 'git -C /tmp/real commit -m "a \" ; git -C /evil commit x"'
  [ "$output" = "/tmp/real" ]
}

# --- 複合コマンドの全ターゲット (2026-08-08 追加) ---------------------------
# 単一値の抽出では、複合コマンドの片方しか検査できない。左端固定でも右端固定でも、
# 順序を入れ替えるだけで検査されない側へ commit を寄せられる (同レビューが両方向を実証)。
# 読み取り専用の 3 hook は git_target_dirs で全件を走査してこの非対称を閉じる。
# ここが守るのは抽出の全件性。hook 側の走査は各 hook のテストが持つ。

@test "both targets of a compound commit are returned, decoy first" {
  load_extractor
  run git_target_dirs 'git -C /decoy commit -m x && git -C /real commit -m y'
  [ "$output" = "/decoy
/real" ]
}

@test "both targets are returned with the order reversed too" {
  load_extractor
  run git_target_dirs 'git -C /real commit -m x && git -C /decoy commit -m y'
  [ "$output" = "/real
/decoy" ]
}

@test "the same repo named twice is returned once" {
  load_extractor
  run git_target_dirs 'git -C /tmp/repo commit -m x && git -C /tmp/repo commit -m y'
  [ "$output" = "/tmp/repo" ]
}

@test "a segment without the verb contributes no target" {
  load_extractor
  run git_target_dirs 'git -C /tmp/other add -A && git -C /tmp/repo commit -m x'
  [ "$output" = "/tmp/repo" ]
}

@test "git_target_dir returns the rightmost match (the single-value callers)" {
  load_extractor
  run git_target_dir 'git -C /decoy commit -m x && git -C /real commit -m y'
  [ "$output" = "/real" ]
}

@test "git_target_dirs is silent when nothing matches" {
  load_extractor
  run git_target_dirs 'git commit -m ok'
  [ -z "$output" ]
}

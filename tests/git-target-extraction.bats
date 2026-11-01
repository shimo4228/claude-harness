#!/usr/bin/env bats
# Tests for hooks/_git-target-common.sh — the shared "which repo is being committed"
# extractor used by every precommit hook.
# Run: bats ~/.claude/tests/git-target-extraction.bats
#
# 抽出は読み落とさないことを優先する（ヘッダの抽出方針）。ここが固定するのは「本物の `-C` の先と
# $PWD が必ず候補に入る」こと。余分な候補（メッセージや heredoc の中の `git -C x`）は許す。
# 再現例は 2026-07-31〜11-01 の review が、引用符を解釈する版で示した素通りの経路。
# hook ごとの挙動は各 hook のテストが持つ。

load_extractor() {
  # shellcheck source=hooks/_git-target-common.sh
  source "${BATS_TEST_DIRNAME}/../hooks/_git-target-common.sh"
}

# has <command> <path> — git_target_dirs の出力に path が含まれる
has() {
  local d
  while IFS= read -r d; do [[ "$d" == "$2" ]] && return 0; done < <(git_target_dirs "$1")
  echo "missing $2 in: $(git_target_dirs "$1" | tr '\n' ' ')"
  return 1
}

@test "bare git -C ... commit resolves to that repo" {
  load_extractor
  has 'git -C /tmp/repo commit -m ok' /tmp/repo
}

@test "env, command, time, a full git path and global options before git -C still resolve" {
  load_extractor
  local c
  for c in 'SECRET_SCAN_BYPASS=1 FOO=bar git -C /tmp/repo commit -m ok' 'env FOO=1 git -C /tmp/repo commit -m ok' \
           'command git -C /tmp/repo commit -m ok' 'time git -C /tmp/repo commit -m ok' \
           '/usr/bin/git -C /tmp/repo commit -m ok' 'git -c user.name=x -C /tmp/repo commit -m ok' \
           'git --no-pager -C /tmp/repo commit -m ok'; do
    has "$c" /tmp/repo || return 1
  done
}

@test "git -C add && git -C commit returns the repo once" {
  load_extractor
  run git_target_dirs 'git -C /tmp/repo add -A && git -C /tmp/repo commit -m ok'
  [ "$output" = "/tmp/repo
$PWD" ]
}

@test "PWD is always the last candidate" {
  load_extractor
  run git_target_dirs 'git commit -m ok'
  [ "$output" = "$PWD" ]
}

@test "a decoy git -C inside the message does not drop PWD" {
  load_extractor
  has 'git commit -m "notes; git -C /evil status commit x"' "$PWD"
  has "git commit -m 'notes; git -C /evil commit'" "$PWD"
}

@test "a real git -C is kept beside a decoy, in either order" {
  load_extractor
  has 'git -C /victim commit -m "x; git -C /decoy commit"' /victim
  has 'git -C /decoy status; git -C /victim commit -m ok' /victim
  has 'git -C /victim commit -m ok; git -C /decoy status' /victim
}

@test "quotes inside a heredoc body do not hide a later git -C" {
  load_extractor
  has "cat > /tmp/msg <<'EOF'
it's fine
EOF
git -C /victim commit -F /tmp/msg" /victim
}

@test "a quote inside a comment does not hide a later git -C" {
  load_extractor
  has "# it's a note
git -C /victim commit -m ok" /victim
}

@test "a backslash before a closing single quote does not hide git -C" {
  load_extractor
  has "echo 'a\\'; git -C /victim commit -m ok" /victim
}

@test "ANSI-C quoting does not hide git -C" {
  load_extractor
  has "echo \$'it\\'s'; git -C /victim commit -m ok" /victim
}

@test "a double-quoted value spanning a newline does not hide git -C" {
  load_extractor
  has 'echo "a
b"; git -C /victim commit -m ok' /victim
}

@test "quotes nested in a command substitution do not hide git -C" {
  load_extractor
  has 'echo "$(echo "x")"; git -C /victim commit -m ok' /victim
}

@test "a quoted path with spaces is returned whole" {
  load_extractor
  has 'git -C "/tmp/a b" commit -m ok' "/tmp/a b"
}

@test "a tilde in the extracted path is expanded" {
  load_extractor
  has 'git -C ~/proj commit -m ok' "$HOME/proj"
}

@test "a leading cd target is a candidate" {
  load_extractor
  has 'cd /tmp/repo && git commit -m ok' /tmp/repo
}

@test "the verbs argument is accepted and does not narrow the candidates" {
  load_extractor
  has 'git -C /tmp/repo revert HEAD' /tmp/repo
  run git_target_dirs 'git -C /tmp/repo commit -m x' 'bad)(regex'
  [[ "$output" == /tmp/repo* ]]
}

# ---- git_target_dir (verify-precommit.sh の実行先): repo として解決できる候補だけを選ぶ ----

make_repos() { # $BATS_TEST_TMPDIR に a / b の 2 repo と、repo でない cwd を作る
  A="$BATS_TEST_TMPDIR/a"; B="$BATS_TEST_TMPDIR/b"; W="$BATS_TEST_TMPDIR/work"
  mkdir -p "$A" "$B" "$W/tests"
  git -C "$A" init -q; git -C "$B" init -q
}

@test "git_target_dir returns the last repo candidate" {
  load_extractor; make_repos
  run git_target_dir "git -C $A commit -m x; git -C $B commit -m y"
  [ "$output" = "$B" ]
}

@test "git_target_dir is empty when no candidate is a repo" {
  load_extractor; make_repos
  run git_target_dir 'git commit -m ok'
  [ -z "$output" ]
}

@test "git_target_dir skips words that are not directories (-C HEAD, message words, cd -)" {
  load_extractor; make_repos
  local c
  for c in "git -C $A commit --amend -C HEAD" "git -C $A commit -m 'fix: -C の囮を拾う'" \
           "git -C $A commit -m x && cd -"; do
    run git_target_dir "$c"
    [ "$output" = "$A" ] || { echo "picked [$output] for: $c"; return 1; }
  done
}

@test "git_target_dir prefers an absolute repo over a relative word resolving from the hook cwd" {
  load_extractor; make_repos
  git -C "$W" init -q
  cd "$W"
  run git_target_dir "git -C $A commit -m 'docs: run cd tests first'"
  [ "$output" = "$A" ]
}

@test "GIT_DIR assignments are a stated limit: PWD is still checked" {
  load_extractor
  has 'GIT_DIR=/victim/.git git commit -m x' "$PWD"
}

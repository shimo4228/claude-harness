#!/usr/bin/env bats
# Tests for hooks/ruff-format-precommit.sh — the commit-boundary format gate.
# Run: bats ~/.claude/tests/ruff-format-precommit.bats
#
# The properties worth pinning, none of which had a test before 2026-08-08:
#   1. **check only** — the hook must never rewrite the working tree. It replaced
#      a per-edit autofix hook that raced with in-progress edits (deleting an
#      import between the Edit that added it and the Edit that used it), so
#      "detects but does not touch" is the whole point of the redesign;
#   2. the verdict comes from ruff's **exit code**, not from its text. A grep on
#      "Would reformat" silently stopped matching when 0.16 changed the wording,
#      turning the gate into a no-op;
#   3. the repo's own ruff config is honoured, or every repo with a non-default
#      line-length would be blocked on every commit;
#   4. index, not working tree — same reasoning as the bandit hook.
# Plus the 2026-08-08 remediations: all compound-commit targets, and textconv.

HOOK="$HOME/.claude/hooks/ruff-format-precommit.sh"

setup() {
  TMP="$(mktemp -d)"
  REPO="$TMP/repo"
  make_repo "$REPO"
}

teardown() { rm -rf "$TMP"; }

make_repo() {
  mkdir -p "$1"
  git -C "$1" init -q
  git -C "$1" config user.email t@example.com
  git -C "$1" config user.name t
  printf 'clean\n' > "$1/README.md"
  git -C "$1" add README.md
  git -C "$1" commit -qm init
}

run_hook() {
  jq -nc --arg c "$1" '{tool_input:{command:$c}}' > "$TMP/in.json"
  run bash -c "bash '$HOOK' < '$TMP/in.json' 2> '$TMP/err'"
}

hook_stderr() { cat "$TMP/err"; }
blocked() { printf '%s' "$output" | jq -e '.decision == "block"' > /dev/null; }

formatted() { printf 'def f(x):\n    return {"a": 1}\n'; }
unformatted() { printf 'def f(x):\n    return {  "a":1 }\n'; }
broken_syntax() { printf 'def broken(:\n'; }
# 95 columns: reformatted under ruff's default 88, left alone at 100+.
long_call() { printf 'result = some_function(argument_0, argument_1, argument_2, argument_3, argument_4, argument_5)\n'; }

stage_py() {  # stage_py <repo> <file> <content-fn>
  "$3" > "$1/$2"
  git -C "$1" add "$2"
}

# --- staying out of the way ---------------------------------------------------

@test "a non-git command is ignored" {
  stage_py "$REPO" bad.py unformatted
  run_hook "ls -la $REPO"
  [ -z "$output" ]
}

@test "a commit with no staged .py is ignored" {
  printf 'notes\n' > "$REPO/notes.txt"
  git -C "$REPO" add notes.txt
  run_hook "git -C $REPO commit -m 'docs: notes'"
  [ -z "$output" ]
}

@test "formatted staged Python is allowed" {
  stage_py "$REPO" ok.py formatted
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ -z "$output" ]
}

@test "the bypass prefix skips the check" {
  stage_py "$REPO" bad.py unformatted
  run_hook "RUFF_FORMAT_BYPASS=1 git -C $REPO commit -m 'chore: fixture'"
  [ -z "$output" ]
}

@test "the bypass token inside a commit message does not disable the check" {
  stage_py "$REPO" bad.py unformatted
  run_hook "git -C $REPO commit -m 'note: RUFF_FORMAT_BYPASS=1 was discussed'"
  blocked
}

# --- detection ----------------------------------------------------------------

@test "unformatted staged Python blocks the commit" {
  stage_py "$REPO" bad.py unformatted
  run_hook "git -C $REPO commit -m 'feat: x'"
  blocked
}

@test "the block reason names the offending file" {
  stage_py "$REPO" bad.py unformatted
  run_hook "git -C $REPO commit -m 'feat: x'"
  [[ "$output" == *"bad.py"* ]]
}

# ruff exits 2 here rather than 1. The verdict is taken from "non-zero", so a
# file too broken to format still stops the commit — committing unparseable
# Python is not an outcome the gate should wave through.
@test "a file ruff cannot even parse blocks the commit" {
  stage_py "$REPO" bad.py broken_syntax
  run_hook "git -C $REPO commit -m 'feat: x'"
  blocked
}

# --- check only, never rewrite ------------------------------------------------

@test "a blocked commit leaves the working tree byte-identical" {
  stage_py "$REPO" bad.py unformatted
  before="$(cat "$REPO/bad.py")"
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ "$(cat "$REPO/bad.py")" = "$before" ]
}

@test "a blocked commit leaves the index untouched" {
  stage_py "$REPO" bad.py unformatted
  before="$(git -C "$REPO" show :bad.py)"
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ "$(git -C "$REPO" show :bad.py)" = "$before" ]
}

# --- index, not working tree --------------------------------------------------

@test "the staged version is checked even when the working tree is clean" {
  stage_py "$REPO" f.py unformatted
  formatted > "$REPO/f.py"   # tidied in the tree, but that fix is not staged
  run_hook "git -C $REPO commit -m 'feat: x'"
  blocked
}

@test "unstaged mess in the working tree is not checked" {
  stage_py "$REPO" f.py formatted
  unformatted > "$REPO/f.py"
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ -z "$output" ]
}

# --- the repo's own ruff config -----------------------------------------------
# Without this, the gate would judge every repo by ruff's defaults and block on
# style the repo has deliberately chosen. The config is read from the index too,
# for the same reason the Python is.

@test "a 95-column line is blocked under ruff's default line length" {
  stage_py "$REPO" long.py long_call
  run_hook "git -C $REPO commit -m 'feat: x'"
  blocked
}

@test "the repo's staged ruff.toml raises the line length and clears it" {
  stage_py "$REPO" long.py long_call
  printf 'line-length = 100\n' > "$REPO/ruff.toml"
  git -C "$REPO" add ruff.toml
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ -z "$output" ]
}

@test "a pyproject.toml is honoured the same way" {
  stage_py "$REPO" long.py long_call
  printf '[tool.ruff]\nline-length = 100\n' > "$REPO/pyproject.toml"
  git -C "$REPO" add pyproject.toml
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ -z "$output" ]
}

# --- deferring to a repo that owns its gate -----------------------------------

@test "an executable .claude/verify.sh makes the hook stand down" {
  stage_py "$REPO" bad.py unformatted
  mkdir -p "$REPO/.claude"
  printf '#!/bin/sh\nexit 0\n' > "$REPO/.claude/verify.sh"
  chmod +x "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ -z "$output" ]
}

@test "a non-executable .claude/verify.sh does not trigger the stand-down" {
  stage_py "$REPO" bad.py unformatted
  mkdir -p "$REPO/.claude"
  printf '#!/bin/sh\nexit 0\n' > "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'feat: x'"
  blocked
}

# --- every target of a compound commit ----------------------------------------

@test "an unformatted file in the second repo of a compound commit is caught" {
  make_repo "$TMP/repo2"
  stage_py "$REPO" ok.py formatted
  stage_py "$TMP/repo2" bad.py unformatted
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $TMP/repo2 commit -m 'chore: b'"
  blocked
}

@test "an unformatted file in the first repo of a compound commit is caught" {
  make_repo "$TMP/repo2"
  stage_py "$REPO" bad.py unformatted
  stage_py "$TMP/repo2" ok.py formatted
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $TMP/repo2 commit -m 'chore: b'"
  blocked
}

@test "two clean repos in a compound commit are allowed" {
  make_repo "$TMP/repo2"
  stage_py "$REPO" ok.py formatted
  stage_py "$TMP/repo2" fine.py formatted
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $TMP/repo2 commit -m 'chore: b'"
  [ -z "$output" ]
}

# Each repo is expanded separately rather than into one tree: merged, one repo's
# line-length would judge the other's files — and the config expansion would then
# delete repo A's ruff.toml while preparing repo B, quietly re-judging A's files
# at the default width.
#
# The two files are named so neither is a substring of the other: asserting only
# "the output mentions repo2" passes even under the merged-tree bug, because that
# bug reports BOTH files under repo2's prefix. The load-bearing half is that the
# repo with a 100-column config is absent from the findings.
@test "a compound commit reports only the repo whose config it actually violates" {
  make_repo "$TMP/repo2"
  stage_py "$REPO" wide.py long_call
  printf 'line-length = 100\n' > "$REPO/ruff.toml"
  git -C "$REPO" add ruff.toml
  stage_py "$TMP/repo2" narrow.py long_call   # no config: default 88 applies
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $TMP/repo2 commit -m 'chore: b'"
  [[ "$output" == *"narrow.py"* ]] || return 1
  [[ "$output" != *"wide.py"* ]]
}

# --- hostile repo-local git config --------------------------------------------

@test "a hostile diff.external neither runs nor blinds the check" {
  stage_py "$REPO" bad.py unformatted
  git -C "$REPO" config diff.external "touch $TMP/pwned #"
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ ! -e "$TMP/pwned" ] || return 1
  blocked
}

# As in the bandit suite: this hook asks git only for `diff --name-only` and
# `git show`, neither of which converts content, so this passes with or without
# `--no-textconv`. Kept as defence in depth for the day it grows a content diff.
@test "a hostile diff.textconv does not run (defence in depth)" {
  stage_py "$REPO" bad.py unformatted
  git -C "$REPO" config diff.evil.textconv "touch $TMP/pwned-textconv #"
  printf '*.py diff=evil\n' > "$REPO/.gitattributes"
  git -C "$REPO" add .gitattributes
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ ! -e "$TMP/pwned-textconv" ] || return 1
  blocked
}

# --- fail-soft ----------------------------------------------------------------

@test "an unresolvable ruff allows the commit" {
  stage_py "$REPO" bad.py unformatted
  jq -nc --arg c "git -C $REPO commit -m 'feat: x'" '{tool_input:{command:$c}}' > "$TMP/in.json"
  run env PATH=/usr/bin:/bin HOME="$TMP/nohome" bash -c "bash '$HOOK' < '$TMP/in.json' 2> '$TMP/err'"
  [ -z "$output" ]
}

@test "an unresolvable ruff says so on stderr" {
  stage_py "$REPO" bad.py unformatted
  jq -nc --arg c "git -C $REPO commit -m 'feat: x'" '{tool_input:{command:$c}}' > "$TMP/in.json"
  run env PATH=/usr/bin:/bin HOME="$TMP/nohome" bash -c "bash '$HOOK' < '$TMP/in.json' 2> '$TMP/err'"
  [[ "$(hook_stderr)" == *"ruff-format-precommit"* ]]
}

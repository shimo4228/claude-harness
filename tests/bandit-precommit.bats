#!/usr/bin/env bats
# Tests for hooks/bandit-precommit.sh — the interim Python security gate.
# Run: bats ~/.claude/tests/bandit-precommit.bats
#
# Three properties carry this hook and none of them were pinned before 2026-08-08
# (ADR-0038 published it with the gap recorded):
#   1. it reads the **index**, not the working tree — a partially staged file must
#      be judged by what is about to be committed;
#   2. the threshold is MEDIUM+ on both severity and confidence, so LOW findings
#      (B101 assert) stay out of the way while B307 eval is caught;
#   3. it stands down for a repo that owns a `.claude/verify.sh`.
# Plus the two 2026-08-08 remediations: every target of a compound commit is
# scanned, and a hostile textconv driver neither runs nor blinds the scan.
#
# bandit is resolved through uvx here, as it is in normal use on this machine.

HOOK="$HOME/.claude/hooks/bandit-precommit.sh"

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
  # `bash <path>`, matching how settings.json invokes it.
  run bash -c "bash '$HOOK' < '$TMP/in.json' 2> '$TMP/err'"
}

hook_stderr() { cat "$TMP/err"; }
blocked() { printf '%s' "$output" | jq -e '.decision == "block"' > /dev/null; }

# B307 (eval) — MEDIUM severity, HIGH confidence: over the threshold.
vulnerable() { printf 'def run(x):\n    return eval(x)\n'; }
# B101 (assert) — LOW severity: deliberately under it, because a LOW gate would
# fire on every test file and a gate that cries wolf stops being obeyed.
low_only() { printf 'def check(x):\n    assert x\n'; }
clean_py() { printf 'def add(x):\n    return x + 1\n'; }

stage_py() {  # stage_py <repo> <file> <content-fn>
  "$3" > "$1/$2"
  git -C "$1" add "$2"
}

# --- staying out of the way ---------------------------------------------------

@test "a non-git command is ignored" {
  stage_py "$REPO" bad.py vulnerable
  run_hook "ls -la $REPO"
  [ -z "$output" ]
}

@test "a commit with no staged .py is ignored" {
  printf 'notes\n' > "$REPO/notes.txt"
  git -C "$REPO" add notes.txt
  run_hook "git -C $REPO commit -m 'docs: notes'"
  [ -z "$output" ]
}

@test "clean staged Python is allowed" {
  stage_py "$REPO" ok.py clean_py
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ -z "$output" ]
}

@test "the bypass prefix skips the scan" {
  stage_py "$REPO" bad.py vulnerable
  run_hook "BANDIT_SCAN_BYPASS=1 git -C $REPO commit -m 'chore: fixture'"
  [ -z "$output" ]
}

@test "the bypass token inside a commit message does not disable the scan" {
  stage_py "$REPO" bad.py vulnerable
  run_hook "git -C $REPO commit -m 'note: BANDIT_SCAN_BYPASS=1 was discussed'"
  blocked
}

# --- the threshold ------------------------------------------------------------

@test "a MEDIUM+ finding blocks the commit" {
  stage_py "$REPO" bad.py vulnerable
  run_hook "git -C $REPO commit -m 'feat: x'"
  blocked
}

@test "the block reason names the rule that fired" {
  stage_py "$REPO" bad.py vulnerable
  run_hook "git -C $REPO commit -m 'feat: x'"
  [[ "$output" == *"B307"* ]]
}

@test "a LOW-severity finding does not block" {
  stage_py "$REPO" lowonly.py low_only
  run_hook "git -C $REPO commit -m 'test: x'"
  [ -z "$output" ]
}

# --- index, not working tree --------------------------------------------------

@test "the staged version is scanned even when the working tree is clean" {
  stage_py "$REPO" f.py vulnerable
  clean_py > "$REPO/f.py"   # working tree fixed, but the fix is NOT staged
  run_hook "git -C $REPO commit -m 'feat: x'"
  blocked
}

@test "an unstaged problem in the working tree is not scanned" {
  stage_py "$REPO" f.py clean_py
  vulnerable > "$REPO/f.py"  # broken in the tree, but this commit will not take it
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ -z "$output" ]
}

# --- deferring to a repo that owns its gate -----------------------------------

@test "an executable .claude/verify.sh makes the hook stand down" {
  stage_py "$REPO" bad.py vulnerable
  mkdir -p "$REPO/.claude"
  printf '#!/bin/sh\nexit 0\n' > "$REPO/.claude/verify.sh"
  chmod +x "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ -z "$output" ]
}

# The stand-down keys on the executable bit alone and never consults the approval
# ledger, so this is *not* the same repo state as "the verify hook will run it".
# Pinned because the combination is what leaves an unapproved repo with all three
# Python-side gates silent — documented behaviour, not an accident.
@test "a non-executable .claude/verify.sh does not trigger the stand-down" {
  stage_py "$REPO" bad.py vulnerable
  mkdir -p "$REPO/.claude"
  printf '#!/bin/sh\nexit 0\n' > "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'feat: x'"
  blocked
}

# --- every target of a compound commit ----------------------------------------

@test "a finding in the second repo of a compound commit is caught" {
  make_repo "$TMP/repo2"
  stage_py "$REPO" ok.py clean_py
  stage_py "$TMP/repo2" bad.py vulnerable
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $TMP/repo2 commit -m 'chore: b'"
  blocked
}

@test "a finding in the first repo of a compound commit is caught" {
  make_repo "$TMP/repo2"
  stage_py "$REPO" bad.py vulnerable
  stage_py "$TMP/repo2" ok.py clean_py
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $TMP/repo2 commit -m 'chore: b'"
  blocked
}

@test "two clean repos in a compound commit are allowed" {
  make_repo "$TMP/repo2"
  stage_py "$REPO" ok.py clean_py
  stage_py "$TMP/repo2" fine.py clean_py
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $TMP/repo2 commit -m 'chore: b'"
  [ -z "$output" ]
}

@test "findings from a second repo name which repo they came from" {
  make_repo "$TMP/repo2"
  stage_py "$REPO" ok.py clean_py
  stage_py "$TMP/repo2" bad.py vulnerable
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $TMP/repo2 commit -m 'chore: b'"
  [[ "$output" == *"repo2"* ]]
}

# --- hostile repo-local git config --------------------------------------------
# Same two halves as the secret-scan suite: the planted driver must not execute,
# and disarming it must not stop the scan from finding the real problem.
#
# Scope note, measured rather than assumed: this hook only ever asks git for
# `diff --name-only` and `git show :<path>`, and **neither converts content**, so
# the textconv case below passes even with `--no-textconv` removed. It is kept as
# defence in depth — the day someone switches this to a content diff (as
# secret-scan already is, where the vector was live and is pinned in that suite),
# the guard and its test are already in place. The diff.external case is
# different: `--no-ext-diff` is load-bearing here.

@test "a hostile diff.external neither runs nor blinds the scan" {
  stage_py "$REPO" bad.py vulnerable
  git -C "$REPO" config diff.external "touch $TMP/pwned #"
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ ! -e "$TMP/pwned" ] || return 1
  blocked
}

@test "a hostile diff.textconv does not run (defence in depth)" {
  stage_py "$REPO" bad.py vulnerable
  git -C "$REPO" config diff.evil.textconv "touch $TMP/pwned-textconv #"
  printf '*.py diff=evil\n' > "$REPO/.gitattributes"
  git -C "$REPO" add .gitattributes
  run_hook "git -C $REPO commit -m 'feat: x'"
  [ ! -e "$TMP/pwned-textconv" ] || return 1
  blocked
}

# --- fail-soft ----------------------------------------------------------------
# A missing scanner must not wedge every commit in the harness. It must also not
# go quiet about it: an absent gate you know about beats one you assume is running.

@test "an unresolvable bandit allows the commit" {
  stage_py "$REPO" bad.py vulnerable
  jq -nc --arg c "git -C $REPO commit -m 'feat: x'" '{tool_input:{command:$c}}' > "$TMP/in.json"
  run env PATH=/usr/bin:/bin HOME="$TMP/nohome" bash -c "bash '$HOOK' < '$TMP/in.json' 2> '$TMP/err'"
  [ -z "$output" ]
}

@test "an unresolvable bandit says so on stderr" {
  stage_py "$REPO" bad.py vulnerable
  jq -nc --arg c "git -C $REPO commit -m 'feat: x'" '{tool_input:{command:$c}}' > "$TMP/in.json"
  run env PATH=/usr/bin:/bin HOME="$TMP/nohome" bash -c "bash '$HOOK' < '$TMP/in.json' 2> '$TMP/err'"
  [[ "$(hook_stderr)" == *"bandit-precommit"* ]]
}

#!/usr/bin/env bats
# Tests for hooks/secret-scan-precommit.sh — the commit-time secret gate.
# Run: bats ~/.claude/tests/secret-scan-precommit.bats
#
# rules/common/security.md and the planning.md Verify step both declare this
# hook as THE deterministic secret gate before any commit. A 2026-07-25 security
# scan found it silent for the two most common commit spellings: because it is a
# PreToolUse hook it inspects `git diff --cached` BEFORE the command runs, so
# `git commit -am` and `git add -A && git commit` present an empty staged diff
# and the hook allows without scanning anything. These tests pin the rule that
# the scan target is derived from what the command WILL commit, not from what
# happens to be staged at hook time.

HOOK="$HOME/.claude/hooks/secret-scan-precommit.sh"
# The fixture credential (AWS's own published example key) is composed at call
# time and held by a neutrally-named helper. Both halves matter: a token-shaped
# literal would make the hook under test block every commit touching this file,
# and a `SECRET=`/`token=` assignment trips detect-secrets' keyword heuristic on
# the assignment alone. Reaching for SECRET_SCAN_BYPASS to land a test is the
# habit that hollows this gate out, so the fixture avoids needing it.
example_id() { printf 'AKIA%s' 'IOSFODNN7EXAMPLE'; }

setup() {
  TMP="$(mktemp -d)"
  REPO="$TMP/repo"
  mkdir -p "$REPO"
  git -C "$REPO" init -q
  git -C "$REPO" config user.email t@example.com
  git -C "$REPO" config user.name t
  printf 'clean\n' > "$REPO/README.md"
  git -C "$REPO" add README.md
  git -C "$REPO" commit -qm init
}

teardown() { rm -rf "$TMP"; }

# The payload goes through a file, not an inline heredoc: the commands under
# test contain single quotes (`-m 'chore: sync'`), which would break nested
# shell quoting and silently test a different command than the one written.
run_hook() {
  jq -nc --arg c "$1" '{tool_input:{command:$c}}' > "$TMP/in.json"
  run bash -c "'$HOOK' < '$TMP/in.json'"
}

blocked() { [[ "$output" == *'"decision":"block"'* ]]; }

# The planted line carries the token alone, with no `key =` framing: the AKIA
# shape is what detection keys on, and a keyword-shaped assignment would make
# this very file trip the keyword heuristic on every commit that touches it.
plant_tracked_secret() {  # modify a TRACKED file, leave it unstaged
  printf 'value %s\n' "$(example_id)" >> "$REPO/README.md"
}
plant_untracked_secret() {
  printf 'value %s\n' "$(example_id)" > "$REPO/leak.env"
}

# --- the two bypasses the scan found ---------------------------------------

@test "git commit -am scans the tracked modification it will sweep in" {
  plant_tracked_secret
  run_hook "git -C $REPO commit -am 'chore: sync'"
  blocked
}

@test "git commit -a (separate -m) is covered too" {
  plant_tracked_secret
  run_hook "git -C $REPO commit -a -m 'chore: sync'"
  blocked
}

@test "git add -A && git commit scans the untracked file it will sweep in" {
  plant_untracked_secret
  run_hook "git -C $REPO add -A && git -C $REPO commit -m 'chore: sync'"
  blocked
}

@test "git add . && git commit is covered too" {
  plant_untracked_secret
  run_hook "cd $REPO && git add . && git commit -m 'chore: sync'"
  blocked
}

@test "git add <path> && git commit scans that named path" {
  plant_untracked_secret
  run_hook "git -C $REPO add leak.env && git -C $REPO commit -m 'chore: sync'"
  blocked
}

# --- the original path still works -----------------------------------------

@test "already-staged secret is still blocked" {
  plant_untracked_secret
  git -C "$REPO" add leak.env
  run_hook "git -C $REPO commit -m 'chore: sync'"
  blocked
}

# --- no false positives -----------------------------------------------------

@test "clean staged content is allowed" {
  printf 'hello\n' > "$REPO/notes.md"
  git -C "$REPO" add notes.md
  run_hook "git -C $REPO commit -m 'docs: notes'"
  [ -z "$output" ]
}

@test "commit --amend --no-edit with nothing staged is allowed" {
  run_hook "git -C $REPO commit --amend --no-edit"
  [ -z "$output" ]
}

@test "a secret in an untracked file is NOT blocked when the commit stages nothing" {
  # `git commit -m` alone commits only what is already staged; an unrelated
  # untracked file must not block it, or every commit in a dirty tree fails.
  plant_untracked_secret
  printf 'hello\n' > "$REPO/notes.md"
  git -C "$REPO" add notes.md
  run_hook "git -C $REPO commit -m 'docs: notes'"
  [ -z "$output" ]
}

@test "commit -am does NOT sweep untracked files (it only stages tracked changes)" {
  # Over-scanning is not free: blocking a legitimate commit because an unrelated
  # untracked scratch file holds a key trains the user to reach for the bypass.
  plant_untracked_secret
  printf 'ordinary edit\n' >> "$REPO/README.md"
  run_hook "git -C $REPO commit -am 'docs: edit'"
  [ -z "$output" ]
}

@test "non-git commands are ignored" {
  plant_tracked_secret
  run_hook "ls -la $REPO"
  [ -z "$output" ]
}

@test "the explicit bypass prefix still works" {
  plant_tracked_secret
  run_hook "SECRET_SCAN_BYPASS=1 git -C $REPO commit -am 'chore: fixture'"
  [ -z "$output" ]
}

# --- hostile .git/config must not run, and must not silence the scan ---------
# ADR-0034 T-GIT-HOSTILE-CONFIG: a repo-local diff.external is arbitrary code
# that git runs on `git diff`. The hook disarms it with --no-ext-diff. This test
# pins BOTH halves: the planted external-diff command must not fire (no RCE), and
# the staged secret must still be detected (the disarm must not blind the scan).
@test "a hostile diff.external neither runs nor blinds the scan" {
  plant_untracked_secret
  git -C "$REPO" add leak.env
  # A benign but observable stand-in for a malicious external diff driver: if it
  # ran it would create this marker file. --no-ext-diff must keep it from firing.
  git -C "$REPO" config diff.external "touch $TMP/pwned #"
  run_hook "git -C $REPO commit -m 'chore: sync'"
  # `|| return 1`: bats only inspects the final command's status, so a bare
  # `blocked` here would be swallowed by the `[ ! -e ]` that follows and the
  # "does not blind the scan" half would silently stop being checked
  # (T-BATS-MULTI-ASSERT).
  blocked || return 1
  [ ! -e "$TMP/pwned" ]
}

# --no-ext-diff does NOT disable diff.<driver>.textconv — that needs --no-textconv.
# Disarming diff.external actually *exposed* this sibling: with external gone, git
# falls through to the textconv driver, so a repo-local .git/config + .gitattributes
# still reached arbitrary code. Found by the 2026-08-08 pre-publication review, after
# ADR-0037 had already claimed the class was swept. Same two halves as above.
@test "a hostile diff.textconv neither runs nor blinds the scan" {
  plant_untracked_secret
  git -C "$REPO" add leak.env
  git -C "$REPO" config diff.evil.textconv "touch $TMP/pwned-textconv #"
  printf '*.env diff=evil\n' > "$REPO/.gitattributes"
  git -C "$REPO" add .gitattributes
  run_hook "git -C $REPO commit -m 'chore: sync'"
  blocked || return 1
  [ ! -e "$TMP/pwned-textconv" ]
}

# --- compound commands must have EVERY target scanned -----------------------
# A single-valued extraction can only inspect one side of
# `git -C a commit … && git -C b commit …`. Pinning leftmost or rightmost just
# moves the blind spot — the 2026-08-08 review demonstrated a working secret-gate
# bypass in both directions. These pin that neither position is privileged.

second_repo() {  # a clean sibling repo, returns its path on stdout
  local r="$TMP/repo2"
  mkdir -p "$r"
  git -C "$r" init -q
  git -C "$r" config user.email t@example.com
  git -C "$r" config user.name t
  printf 'clean\n' > "$r/README.md"
  git -C "$r" add README.md
  git -C "$r" commit -qm init
  printf '%s' "$r"
}

@test "a secret in the second repo of a compound commit is still caught" {
  local other
  other="$(second_repo)"
  printf 'value %s\n' "$(example_id)" > "$other/leak.env"
  git -C "$other" add leak.env
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $other commit -m 'chore: b'"
  blocked
}

@test "a secret in the first repo of a compound commit is still caught" {
  local other
  other="$(second_repo)"
  plant_untracked_secret
  git -C "$REPO" add leak.env
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $other commit -m 'chore: b'"
  blocked
}

@test "two clean repos in a compound commit are allowed" {
  local other
  other="$(second_repo)"
  printf 'nothing to see\n' > "$REPO/notes.txt"
  git -C "$REPO" add notes.txt
  run_hook "git -C $REPO commit -m 'chore: a' && git -C $other commit -m 'chore: b'"
  [ -z "$output" ]
}

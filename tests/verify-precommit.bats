#!/usr/bin/env bats
# Tests for hooks/verify-precommit.sh — gate existence and the approval ledger.
# Run: bats ~/.claude/tests/verify-precommit*.bats  (setup, helpers and the contract they pin:
# tests/verify_precommit_helpers.bash)

load verify_precommit_helpers

# --- the hook stays out of the way ------------------------------------------

@test "a non-git command is ignored" {
  write_gate 1
  approve
  run_hook "ls -la $REPO"
  [ -z "$output" ]
}

@test "a git command that is not a commit is ignored" {
  write_gate 1
  approve
  run_hook "git -C $REPO log --oneline"
  [ -z "$output" ]
}

@test "a repo with no gate is allowed" {
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ]
}

# --- a gate is judged by existence, not by its mode bit ------------------------
# The hook runs a private 0700 copy of the approved bytes (verify_allow.py run), so
# the repo file's -x bit is irrelevant to running it. Until 2026-09-26 the hook
# checked `-x` and skipped a non-executable gate as if it were absent — which also
# let an approved repo's gate go dark by `chmod -x` or deletion, silently. The old
# test here ("a gate that is not executable is skipped") pinned that skip; it is
# replaced by the pair below plus the deleted-gate tests, not dropped.

@test "an approved gate that lost its exec bit still runs" {
  write_gate 0
  approve
  chmod -x "$REPO/.claude/verify.sh"  # the ledger pins bytes, not the mode
  run_hook "git -C $REPO commit -m 'chore: x'"
  gate_ran
}

@test "an approved gate that lost its exec bit still blocks on FAIL" {
  write_gate 1
  approve
  chmod -x "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'chore: x'"
  blocked
}

@test "an unapproved non-executable gate is still never executed" {
  write_gate 1
  chmod -x "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ ! -e "$TMP/gate-ran" ] || return 1
  [ -z "$output" ]
}

# --- an approved repo whose gate disappeared blocks; an unledgered one does not --
# The ledger is what distinguishes "this repo never had a gate" (pass — adopting
# one is skill: verify-bootstrap) from "a gate a human approved has vanished"
# (block — the same reasoning as exit 71 in ADR-0059: a known gate gone dark).

@test "an approved repo whose gate was deleted blocks the commit" {
  write_gate 0
  approve
  rm "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'chore: x'"
  blocked
}

@test "an approved repo whose gate became a dangling symlink blocks the commit" {
  write_gate 0
  approve
  rm "$REPO/.claude/verify.sh"
  ln -s "$TMP/nonexistent.sh" "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'chore: x'"
  blocked
}

@test "the deleted-gate block names restore and revoke as the ways out" {
  write_gate 0
  approve
  rm "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'chore: x'"
  local reason
  reason=$(printf '%s' "$output" | jq -r '.reason')
  [[ "$reason" == *"revoke"* ]] || return 1
  [[ "$reason" != *"VERIFY_BYPASS"* ]]
}

# exit 72 (gate unreadable, or a symlink to a file outside the repo) is the same
# "known gate gone dark" state when the repo is ledgered: -f is true, so only the
# run path sees it (2026-09-26 security review + code review, both MEDIUM).

@test "an approved repo whose gate became a symlink out of the repo blocks the commit" {
  printf '#!/bin/sh\nprintf x > "%s/gate-ran"\nexit 0\n' "$TMP" > "$TMP/outside.sh"
  chmod +x "$TMP/outside.sh"
  write_gate 0
  approve
  rm "$REPO/.claude/verify.sh"
  ln -s "$TMP/outside.sh" "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ ! -e "$TMP/gate-ran" ] || return 1
  blocked
}

@test "an approved repo whose gate became unreadable blocks the commit" {
  [ "$(id -u)" -ne 0 ] || skip "root reads mode-000 files"
  write_gate 0
  approve
  chmod 000 "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'chore: x'"
  blocked
}

@test "an unledgered repo whose gate is a symlink out of the repo still passes with a notice" {
  printf '#!/bin/sh\nexit 0\n' > "$TMP/outside.sh"
  mkdir -p "$REPO/.claude"
  ln -s "$TMP/outside.sh" "$REPO/.claude/verify.sh"
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ] || return 1
  [[ "$(hook_stderr)" == *"verify-precommit"* ]]
}

@test "a deleted gate in an approved repo still blocks with the old bypass prefix" {
  write_gate 0
  approve
  rm "$REPO/.claude/verify.sh"
  run_hook "VERIFY_BYPASS=1 git -C $REPO commit -m 'chore: x'"
  blocked
}

@test "a repo with no gate is still allowed when the ledger lists other repos" {
  local other="$TMP/other"
  mkdir -p "$other/.claude"
  git -C "$other" init -q
  printf '#!/bin/sh\nexit 0\n' > "$other/.claude/verify.sh"
  python3 "$ALLOW" approve "$other" > /dev/null
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ]
}

# --- approval is what decides whether the gate runs at all ------------------

@test "an unapproved gate is never executed" {
  write_gate 1
  run_hook "git -C $REPO commit -m 'chore: x'"
  ! gate_ran
}

@test "an unapproved gate does not block the commit" {
  write_gate 1
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ]
}

@test "an unapproved gate says so on stderr rather than failing silently" {
  write_gate 1
  run_hook "git -C $REPO commit -m 'chore: x'"
  [[ "$(hook_stderr)" == *"verify-precommit"* ]]
}

@test "editing the gate after approval revokes it" {
  write_gate 0
  approve
  write_gate 1  # same path, different bytes
  run_hook "git -C $REPO commit -m 'chore: x'"
  ! gate_ran
}

# --- a stale approval blocks; a missing one does not (ADR-0057) ---------------
# For 3 weeks (2026-08-06..28, contemplative-agent) a ledgered repo's gate sat
# revoked after an edit: the re-approve notice printed on stderr at every commit,
# nobody acted, and the gate never ran. A KNOWN repo whose gate has gone dark is
# a same-day repair (one approve command), so exit 71 now blocks. Exit 70 (repo
# not in the ledger at all — e.g. a fresh clone) still passes with a notice,
# because blocking every unapproved repo would punish ordinary work.

@test "a stale approval (edited gate) blocks the commit" {
  write_gate 0
  approve
  write_gate 1  # exit 71: ledgered, hash mismatch
  run_hook "git -C $REPO commit -m 'chore: x'"
  blocked
}

@test "the stale-approval block names the re-approve command" {
  write_gate 0
  approve
  write_gate 1
  run_hook "git -C $REPO commit -m 'chore: x'"
  [[ "$(printf '%s' "$output" | jq -r '.reason')" == *"approve"* ]]
}

@test "the stale-approval block still does not run the gate" {
  write_gate 0
  approve
  write_gate 1
  run_hook "git -C $REPO commit -m 'chore: x'"
  ! gate_ran
}

@test "re-approving after the edit unblocks the commit and runs the gate" {
  write_gate 0
  approve
  write_gate 0 'edited'  # same exit, different bytes — approval goes stale
  approve                # human re-reads and re-approves the edited bytes
  run_hook "git -C $REPO commit -m 'chore: x'"
  gate_ran || return 1
  [ "$(printf '%s' "$output" | jq -r 'has("decision")')" = "false" ]
}

@test "the stale-approval block tells Claude to show the diff and run approve" {
  write_gate 0
  approve
  write_gate 1
  run_hook "git -C $REPO commit -m 'chore: x'"
  local reason
  reason=$(printf '%s' "$output" | jq -r '.reason')
  [[ "$reason" == *"verify_allow.py diff"* ]] || return 1
  [[ "$reason" == *"approve"* ]]
}

@test "a gate symlinked outside the repo is refused" {
  printf '#!/bin/sh\nprintf x > "%s/gate-ran"\nexit 0\n' "$TMP" > "$TMP/outside.sh"
  chmod +x "$TMP/outside.sh"
  mkdir -p "$REPO/.claude"
  ln -s "$TMP/outside.sh" "$REPO/.claude/verify.sh"
  approve || true  # approval itself is refused for an outside-pointing gate
  run_hook "git -C $REPO commit -m 'chore: x'"
  ! gate_ran
}

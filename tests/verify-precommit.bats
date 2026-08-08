#!/usr/bin/env bats
# Tests for hooks/verify-precommit.sh — the hook that runs a repo's own machine gate.
# Run: bats ~/.claude/tests/verify-precommit.bats
#
# This hook is the only one that **executes** code living inside the repo being
# committed, and hooks run without a permission prompt. Its whole design rests on
# the approval ledger (scripts/hooks/verify_allow.py): an unapproved gate must not
# run at all. Until 2026-08-08 that contract had no test — ADR-0037 recorded the
# coverage gap as a residual risk and ADR-0038 shipped the hook publicly with it
# still open. These tests pin the contract from the hook's side; verify_allow.py's
# own exit codes are pinned here only through the behaviour the hook shows.
#
# 1 test 1 assertion where possible; where two facts must hold together (the gate
# did not run AND the commit was not blocked) the earlier ones carry `|| return 1`,
# because bats only inspects the final command's status (T-BATS-MULTI-ASSERT).

HOOK="$HOME/.claude/hooks/verify-precommit.sh"
ALLOW="$HOME/.claude/scripts/hooks/verify_allow.py"

setup() {
  TMP="$(mktemp -d)"
  REPO="$TMP/repo"
  # The ledger is redirected so these tests can never approve, mutate, or delete
  # an entry in the real ~/.claude/verify-allow.json. verify_allow.py reads the
  # variable per process and the hook passes its environment through untouched.
  export VERIFY_ALLOW_LEDGER="$TMP/ledger.json"
  mkdir -p "$REPO"
  git -C "$REPO" init -q
  git -C "$REPO" config user.email t@example.com
  git -C "$REPO" config user.name t
  printf 'clean\n' > "$REPO/README.md"
  git -C "$REPO" add README.md
  git -C "$REPO" commit -qm init
}

teardown() { rm -rf "$TMP"; }

run_hook() {
  jq -nc --arg c "$1" '{tool_input:{command:$c}}' > "$TMP/in.json"
  # Invoked as `bash <path>`, the way settings.json wires it — not by exec'ing
  # the file, which would additionally depend on a mode bit production never uses.
  # stderr is split off: several allow-paths here are deliberately noisy, and
  # merging the streams would make "$output is empty" untestable.
  run bash -c "bash '$HOOK' < '$TMP/in.json' 2> '$TMP/err'"
}

# NOT named `stderr` — bats reserves that name for its own output helper, and a
# same-named function here is shadowed into a "command not found" at call time.
hook_stderr() { cat "$TMP/err"; }
# Parsed rather than substring-matched: this hook assembles its JSON with
# python's json.dumps, which emits `"decision": "block"` with a space, while the
# sibling hooks printf `"decision":"block"` without one. A literal match would
# pass here for the wrong reason (or silently stop matching if either changes).
# Going through jq also asserts the payload is valid JSON at all — a malformed
# block instruction is dropped by the consumer, which fails open.
blocked() { printf '%s' "$output" | jq -e '.decision == "block"' > /dev/null; }
gate_ran() { [[ -e "$TMP/gate-ran" ]]; }

# Writes an executable gate that records that it ran, its arguments and its cwd,
# then exits with the requested code.
write_gate() {
  mkdir -p "$REPO/.claude"
  cat > "$REPO/.claude/verify.sh" <<EOF
#!/bin/sh
printf '%s' "\$*" > "$TMP/gate-ran"
pwd -P > "$TMP/gate-cwd"
printf '%s' "\${VERIFY_REPO_ROOT:-}" > "$TMP/gate-root"
echo "gate says: ${2:-nothing}"
exit ${1:-0}
EOF
  chmod +x "$REPO/.claude/verify.sh"
}

approve() { python3 "$ALLOW" approve "$REPO" > /dev/null; }

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

@test "a gate that is not executable is skipped" {
  mkdir -p "$REPO/.claude"
  printf '#!/bin/sh\nexit 1\n' > "$REPO/.claude/verify.sh"  # no chmod +x
  approve
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

@test "a gate symlinked outside the repo is refused" {
  printf '#!/bin/sh\nprintf x > "%s/gate-ran"\nexit 0\n' "$TMP" > "$TMP/outside.sh"
  chmod +x "$TMP/outside.sh"
  mkdir -p "$REPO/.claude"
  ln -s "$TMP/outside.sh" "$REPO/.claude/verify.sh"
  approve || true  # approval itself is refused for an outside-pointing gate
  run_hook "git -C $REPO commit -m 'chore: x'"
  ! gate_ran
}

# --- exit codes ---------------------------------------------------------------
# The contract is 0 pass / 1 fail / 2 unable-to-check, but the hook must treat
# *any* unexpected non-zero as a failure rather than waving it through: a gate
# that dies on a typo is not evidence that the commit is clean.

@test "an approved gate that passes is silent" {
  write_gate 0
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ]
}

@test "an approved gate that passes really did run" {
  write_gate 0
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  gate_ran
}

@test "an approved gate that fails blocks the commit" {
  write_gate 1
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  blocked
}

@test "the gate's own output reaches the block reason" {
  write_gate 1 'lint failed on foo.py'
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [[ "$output" == *"lint failed on foo.py"* ]]
}

@test "exit 2 (unable to check) does not block" {
  write_gate 2
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ]
}

@test "exit 2 is reported on stderr — a sleeping gate is worse than no gate" {
  write_gate 2
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [[ "$(hook_stderr)" == *"exit 2"* ]]
}

@test "an unexpected non-zero exit blocks rather than waving the commit through" {
  write_gate 3
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  blocked
}

@test "a gate killed by a signal blocks too" {
  mkdir -p "$REPO/.claude"
  printf '#!/bin/sh\nkill -TERM $$\n' > "$REPO/.claude/verify.sh"
  chmod +x "$REPO/.claude/verify.sh"
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  blocked
}

# --- how the gate is invoked --------------------------------------------------

@test "the gate is called with --staged" {
  write_gate 0
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ "$(cat "$TMP/gate-ran")" = "--staged" ]
}

@test "the gate runs with cwd at the repo root, not the hook's cwd" {
  write_gate 0
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ "$(cat "$TMP/gate-cwd")" = "$(cd "$REPO" && pwd -P)" ]
}

@test "the gate is told its repo root through VERIFY_REPO_ROOT" {
  write_gate 0
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ "$(cat "$TMP/gate-root")" = "$(cd "$REPO" && pwd -P)" ]
}

# --- bypass -------------------------------------------------------------------

@test "the bypass prefix skips the gate" {
  write_gate 1
  approve
  run_hook "VERIFY_BYPASS=1 git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ]
}

@test "the bypass token inside a commit message does not disable the gate" {
  write_gate 1
  approve
  run_hook "git -C $REPO commit -m 'note: VERIFY_BYPASS=1 was discussed'"
  blocked
}

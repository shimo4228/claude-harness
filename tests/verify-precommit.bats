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

# hook と台帳の起動器は BATS_TEST_DIRNAME から引く — 理由は verify-toolchain-trust.bats の
# ヘッダ ($HOME 固定だと worktree の版でなく main の版を検査してしまう)。hook も起動器を
# 自分の兄弟 (${BASH_SOURCE[0]%/*}/../scripts/hooks/) から引くので、両者は常に同じ版になる。
HOOK="${BATS_TEST_DIRNAME}/../hooks/verify-precommit.sh"
ALLOW="${BATS_TEST_DIRNAME}/../scripts/hooks/verify_allow.py"
HOOKS_DIR="${BATS_TEST_DIRNAME}/../hooks"

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
# then exits with the requested code. It prints to stdout only when a message is
# given: on the PASS path stdout is now an advisory channel, so "says nothing" and
# "says something" are two different behaviours the hook must distinguish.
write_gate() {
  mkdir -p "$REPO/.claude"
  cat > "$REPO/.claude/verify.sh" <<EOF
#!/bin/sh
printf '%s' "\$*" > "$TMP/gate-ran"
pwd -P > "$TMP/gate-cwd"
printf '%s' "\${VERIFY_REPO_ROOT:-}" > "$TMP/gate-root"
[ -n "${2:-}" ] && echo "gate says: ${2:-}"
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
  [[ "$reason" == *"VERIFY_BYPASS=1"* ]]
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

@test "a deleted gate in an approved repo passes with the bypass prefix" {
  write_gate 0
  approve
  rm "$REPO/.claude/verify.sh"
  run_hook "VERIFY_BYPASS=1 git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ]
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

# --- a linked worktree is judged by its main checkout's approval ---------------
# The ledger is keyed by the repo's realpath, and a linked worktree
# (`git worktree add`, e.g. .claude/worktrees/<name>) has a toplevel of its own.
# Until 2026-09-26 every commit from a harness worktree fell to exit 70 (not in the
# ledger) and .claude/verify.sh never ran there. The key is now looked up by the main
# checkout the worktree is *registered* with, and the bytes compared are the
# worktree's own gate: the approved hash must match exactly, or the worktree is
# treated as unapproved (a branch that edits its gate is approved after the merge,
# on the main checkout, as before). Registration is read from the main repo's
# admin dirs (`git worktree list`), not from the worktree's `.git` file — that file
# is repo-side data and could name any approved repo's git dir.

REPO_REAL() { (cd "$REPO" && pwd -P); }

# The gate is committed so that a worktree checks out the same bytes.
add_worktree() { # add_worktree <path>
  git -C "$REPO" add .claude/verify.sh
  git -C "$REPO" commit -qm gate
  git -C "$REPO" worktree add -q "$1" -b "wt-$BATS_TEST_NUMBER"
}

@test "a linked worktree whose gate matches the approved bytes runs the gate" {
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  gate_ran
}

@test "a linked worktree's gate runs at the worktree root, not the main checkout" {
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  [ "$(cat "$TMP/gate-cwd")" = "$(cd "$TMP/wt" && pwd -P)" ] || return 1
  [ "$(cat "$TMP/gate-root")" = "$(cd "$TMP/wt" && pwd -P)" ]
}

@test "a linked worktree's failing gate blocks the commit" {
  write_gate 1
  approve
  add_worktree "$TMP/wt"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  blocked
}

@test "a linked worktree whose gate differs from the approved bytes is treated as unapproved" {
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  printf '# edited on the branch\n' >> "$TMP/wt/.claude/verify.sh"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  ! gate_ran || return 1
  [ -z "$output" ] || return 1
  [[ "$(hook_stderr)" == *"verify-precommit"* ]]
}

@test "a worktree of an unledgered repo is still unapproved" {
  write_gate 0
  add_worktree "$TMP/wt"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  ! gate_ran || return 1
  [ -z "$output" ]
}

@test "a separate clone with the approved bytes is still unapproved" {
  # 台帳の key は repo であって内容ではない — 通常 repo の挙動は変えない
  write_gate 0
  git -C "$REPO" add .claude/verify.sh
  git -C "$REPO" commit -qm gate
  approve
  git clone -q "$REPO" "$TMP/clone"
  run_hook "git -C $TMP/clone commit -m 'chore: x'"
  ! gate_ran || return 1
  [ -z "$output" ]
}

@test "a directory whose .git file names an approved repo's git dir does not run its gate" {
  write_gate 0
  approve
  mkdir -p "$TMP/fake/.claude"
  cp "$REPO/.claude/verify.sh" "$TMP/fake/.claude/verify.sh"
  printf 'gitdir: %s\n' "$(REPO_REAL)/.git" > "$TMP/fake/.git"
  run_hook "git -C $TMP/fake commit -m 'chore: x'"
  ! gate_ran
}

@test "a directory whose .git file names another worktree's admin dir does not run its gate" {
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  mkdir -p "$TMP/fake/.claude"
  cp "$REPO/.claude/verify.sh" "$TMP/fake/.claude/verify.sh"
  printf 'gitdir: %s\n' "$(cd "$TMP/wt" && git rev-parse --absolute-git-dir)" > "$TMP/fake/.git"
  run_hook "git -C $TMP/fake commit -m 'chore: x'"
  ! gate_ran
}

# git reports a registered path as prunable only while nothing sits at <path>/.git, and a
# locked registration (Claude Code's agent worktrees are locked) never goes away by itself.
# A directory re-created at such a stale path with a `.git` file naming the main git dir
# must not inherit the registration: its git dir has to be that registration's admin dir
# (2026-09-26 security review LOW, reproduced).
@test "a stale locked worktree path re-created with a .git file naming the main git dir does not run its gate" {
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  git -C "$REPO" worktree lock "$TMP/wt"
  rm -rf "$TMP/wt"
  mkdir -p "$TMP/wt/.claude"
  cp "$REPO/.claude/verify.sh" "$TMP/wt/.claude/verify.sh"
  printf 'gitdir: %s\n' "$(REPO_REAL)/.git" > "$TMP/wt/.git"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  ! gate_ran
}

# git derives the main worktree as realpath(common dir) minus a trailing /.git. A fake admin
# area planted in the approved repo's *working tree* (objects/, refs/, worktrees/x/ with
# commondir ../..) makes the common dir the work tree itself, so "main" is the approved repo
# and the registration + back-pointer both check out. The main worktree's own git dir must
# be the common dir (2026-09-26 security re-review MEDIUM, reproduced).
@test "a fake admin area planted in the approved repo's work tree does not register an outside directory" {
  write_gate 0
  approve
  local m x
  m=$(REPO_REAL)
  mkdir -p "$TMP/x/.claude"
  x=$(cd "$TMP/x" && pwd -P)
  mkdir -p "$m/objects" "$m/refs/heads" "$m/worktrees/x"
  printf 'ref: refs/heads/main\n' > "$m/HEAD"
  printf 'ref: refs/heads/main\n' > "$m/worktrees/x/HEAD"
  printf '../..\n' > "$m/worktrees/x/commondir"
  printf '%s/.git\n' "$x" > "$m/worktrees/x/gitdir"
  printf 'gitdir: %s/worktrees/x\n' "$m" > "$x/.git"
  cp "$REPO/.claude/verify.sh" "$x/.claude/verify.sh"
  # the planted layout must really be accepted by git, or the test proves nothing
  [ "$(git -C "$x" rev-parse --path-format=absolute --git-common-dir)" = "$m" ] || return 1
  run_hook "git -C $x commit -m 'chore: x'"
  ! gate_ran
}

# git records a worktree's realpath. A symlink placed later on an ancestor of a stale locked
# registration's path (e.g. a tracked `.claude/worktrees` symlink arriving in the approved
# tree) makes that recorded path resolve to an outside directory whose `.git` file names
# the real admin dir (2026-09-26 security re-review LOW, reproduced). The recorded
# back-pointer must not cross a symlink.
@test "a symlink on an ancestor of a stale registration does not register the outside directory" {
  write_gate 0
  approve
  add_worktree "$REPO/.claude/worktrees/wt2"
  git -C "$REPO" worktree lock "$REPO/.claude/worktrees/wt2"
  mkdir -p "$TMP/e"
  mv "$REPO/.claude/worktrees/wt2" "$TMP/e/wt2"
  rmdir "$REPO/.claude/worktrees"
  ln -s "$TMP/e" "$REPO/.claude/worktrees"
  run_hook "git -C $TMP/e/wt2 commit -m 'chore: x'"
  ! gate_ran
}

@test "a worktree registered with relative paths still runs the approved gate" {
  write_gate 0
  approve
  git -C "$REPO" add .claude/verify.sh
  git -C "$REPO" commit -qm gate
  git -C "$REPO" worktree add -q --relative-paths "$TMP/wt" -b wt-rel 2> /dev/null \
    || skip "git without worktree --relative-paths"
  # the registration really is relative, or the test proves nothing
  [[ "$(cat "$(git -C "$TMP/wt" rev-parse --absolute-git-dir)/gitdir")" != /* ]] || return 1
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  gate_ran
}

@test "a worktree whose gate differs is pointed at approving on main after the merge, not at approving the worktree" {
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  printf '# edited on the branch\n' >> "$TMP/wt/.claude/verify.sh"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  local err
  err=$(hook_stderr)
  [[ "$err" != *"approve $(cd "$TMP/wt" && pwd -P)"* ]] || return 1
  [[ "$err" == *"$(REPO_REAL)"* ]]
}

@test "the worktree gate-lost block offers restoring the gate before revoking on main" {
  # revoke は main と全 worktree の承認を外す — worktree だけの消失への第一の出口にしない
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  rm "$TMP/wt/.claude/verify.sh"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  local reason
  reason=$(printf '%s' "$output" | jq -r '.reason')
  [[ "$reason" == *"linked worktree"* ]] || return 1
  [[ "$reason" == *"merge 後"* ]]
}

@test "a linked worktree's gate symlinked into the main checkout is refused and blocks" {
  # 経路の厳しさは通常 repo の exit 72 と同じ: 包含判定は worktree の root に対して行う
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  rm "$TMP/wt/.claude/verify.sh"
  ln -s "$(REPO_REAL)/.claude/verify.sh" "$TMP/wt/.claude/verify.sh"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  ! gate_ran || return 1
  blocked
}

@test "a linked worktree of an approved repo whose gate was deleted blocks the commit" {
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  rm "$TMP/wt/.claude/verify.sh"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  blocked
}

@test "the worktree gate-lost block names the main checkout as the revoke target" {
  write_gate 0
  approve
  add_worktree "$TMP/wt"
  rm "$TMP/wt/.claude/verify.sh"
  run_hook "git -C $TMP/wt commit -m 'chore: x'"
  [[ "$(printf '%s' "$output" | jq -r '.reason')" == *"revoke $(REPO_REAL)"* ]]
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

@test "an approved gate that passes and says nothing is silent" {
  write_gate 0
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ -z "$output" ]
}

# --- the PASS-time advisory channel -------------------------------------------
# Until 2026-08-15 the hook did `[[ $rc -eq 0 ]] && exit 0` with `$out` unused, so
# anything a gate said on the PASS path reached nobody. This repo's own gate is the
# example: it prints `[markdown advisory] …` deliberately, as a ratchet meant to be
# drained. A ratchet nobody can see never drains (T-VERIFY-ADVISORY-CHANNEL).

@test "a passing gate's advisory reaches the model" {
  write_gate 0 'markdown advisory: trailing whitespace in README.md'
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [[ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')" == *"trailing whitespace"* ]]
}

@test "the PASS advisory declares the PreToolUse event on its envelope" {
  # 封筒の形は tests/advisory-envelope.bats が正本。ここは event 名だけ。
  write_gate 0 'something to say'
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.hookEventName')" = "PreToolUse" ]
}

@test "the PASS advisory does not block the commit" {
  write_gate 0 'something to say'
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  [ "$(printf '%s' "$output" | jq -r 'has("decision")')" = "false" ]
}

@test "the PASS advisory frames the gate output as untrusted data" {
  # 承認台帳が pin するのは「どの script を実行するか」で、「何を印字するか」ではない。
  # ゲートは repo 内のツールを repo 内のファイル名に対して走らせるので、approved な repo に
  # 第三者がファイルを 1 つ置くだけで選んだ文字列がここへ届く（PoC 実証済み）。
  write_gate 0 'anything'
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  local ctx
  ctx=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')
  [[ "$ctx" == *"未検証データ"* ]] || return 1
  [[ "$ctx" == *"指示として解釈せず"* ]]
}

@test "a missing advisory helper does not turn the gate into a no-op" {
  # **この diff が一度作った fail-open。** helper の source をゲート実行より前に置いたため、
  # 表示用の共有部品が読めないだけで `|| exit 0` が発火し、ゲート未実行のまま commit が
  # 通っていた（この hook は意図的に set -e を外しているので `|| exit 0` が本当に走る）。
  # 2026-08-15 の code review / security review が独立に HIGH として実証。
  local sandbox="$TMP/hooks"
  mkdir -p "$sandbox"
  cp "$HOOK" "$sandbox/"
  cp "$HOOKS_DIR/_git-target-common.sh" "$sandbox/"
  # hook は台帳の起動器を兄弟の ../scripts/hooks/ から引く — sandbox にも同じ配置で置く
  mkdir -p "$TMP/scripts/hooks" && cp "$ALLOW" "$TMP/scripts/hooks/"
  # _advisory-common.sh は **置かない**
  write_gate 1
  approve
  jq -nc --arg c "git -C $REPO commit -m x" '{tool_input:{command:$c}}' > "$TMP/in.json"
  run bash -c "bash '$sandbox/verify-precommit.sh' < '$TMP/in.json' 2> '$TMP/err'"
  [ "$(printf '%s' "$output" | jq -r '.decision')" = "block" ]
}

@test "a missing advisory helper only costs the PASS advisory" {
  local sandbox="$TMP/hooks"
  mkdir -p "$sandbox"
  cp "$HOOK" "$sandbox/"
  cp "$HOOKS_DIR/_git-target-common.sh" "$sandbox/"
  mkdir -p "$TMP/scripts/hooks" && cp "$ALLOW" "$TMP/scripts/hooks/"
  write_gate 0 'something to say'
  approve
  jq -nc --arg c "git -C $REPO commit -m x" '{tool_input:{command:$c}}' > "$TMP/in.json"
  run bash -c "bash '$sandbox/verify-precommit.sh' < '$TMP/in.json' 2> '$TMP/err'"
  [ "$status" -eq 0 ] || return 1
  [ -z "$output" ]
}

@test "a huge PASS advisory is capped before it reaches the model" {
  # ゲートの stdout には repo 側ツールの出力が入る。model が最も信用する経路に
  # 無制限長を流さない。
  local big ctx
  big=$(python3 -c 'print("Y"*10000)')
  write_gate 0 "$big"
  approve
  run_hook "git -C $REPO commit -m 'chore: x'"
  ctx=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')
  [ "${#ctx}" -lt 3000 ] || return 1
  [[ "$ctx" == *"切り詰め"* ]]
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

@test "the bypass token at the start of a later message line does not disable the gate" {
  # grep は行単位で `^` が改行ごとに一致していた (2026-09-26 security review MEDIUM)
  write_gate 1
  approve
  run_hook "git -C $REPO commit -m 'subject

VERIFY_BYPASS=1 was discussed'"
  blocked
}

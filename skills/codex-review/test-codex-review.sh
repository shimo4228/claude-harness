#!/usr/bin/env bash
# Tests for codex-review.sh — behavior at the codex/git boundary.
# Both `codex` and `git` are mocked (fakes on PATH), so tests are deterministic
# regardless of the real repo's branches, and no Codex auth / billing is needed.
#
# Mock git is driven by env vars:
#   FAKE_IN_REPO=1|0     whether we are inside a work tree
#   FAKE_CURRENT=<name>  current branch (symbolic-ref --short HEAD)
#   FAKE_BRANCHES="a b"  space-separated local branches that exist
#   FAKE_ORIGIN_HEAD=<n> origin/HEAD default branch (empty = unset)
#
# origin: shimo4228
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$SCRIPT_DIR/codex-review.sh"
PASS=0
FAIL=0

ok()  { PASS=$((PASS + 1)); printf 'ok   - %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); printf 'FAIL - %s\n     %s\n' "$1" "$2"; }

BIN="$(mktemp -d)"
trap 'rm -rf "$BIN"' EXIT

# Fake codex: print argv so we can assert how the wrapper invoked it.
cat > "$BIN/codex" <<'EOF'
#!/usr/bin/env bash
printf 'CODEX_ARGV: %s\n' "$*"
EOF

# Fake git: deterministic answers driven by FAKE_* env vars.
cat > "$BIN/git" <<'EOF'
#!/usr/bin/env bash
cmd="$*"
case "$cmd" in
  "rev-parse --is-inside-work-tree")
    [[ "${FAKE_IN_REPO:-1}" == "1" ]] && exit 0 || exit 128 ;;
  "symbolic-ref --short HEAD")
    printf '%s\n' "${FAKE_CURRENT:-feature}" ;;
  "symbolic-ref --quiet refs/remotes/origin/HEAD")
    [[ -n "${FAKE_ORIGIN_HEAD:-}" ]] && printf 'refs/remotes/origin/%s\n' "$FAKE_ORIGIN_HEAD" || exit 1 ;;
  "show-ref --verify --quiet refs/heads/"*)
    branch="${cmd##*refs/heads/}"
    case " ${FAKE_BRANCHES-main} " in *" $branch "*) exit 0 ;; *) exit 1 ;; esac ;;
  *) exit 0 ;;
esac
EOF
chmod +x "$BIN/codex" "$BIN/git"

# Run target with mocks first on PATH. Leading "VAR=val" args set FAKE_* env;
# the rest are passed to the script.
runa() { local v=(); while [[ "${1:-}" == *=* ]]; do v+=("$1"); shift; done
         PATH="$BIN:/usr/bin:/bin" env "${v[@]}" bash "$TARGET" "$@"; }

# 1. codex missing -> exit 3 (minimal PATH: bash+git present, codex absent)
out="$(PATH="/usr/bin:/bin" bash "$TARGET" 2>&1)"; rc=$?
if [[ $rc -eq 3 ]]; then ok "missing codex exits 3"; else bad "missing codex exits 3" "rc=$rc out=$out"; fi

# 2. default mode on a feature branch injects --base <detected>
out="$(runa FAKE_CURRENT=feature FAKE_BRANCHES=main 2>/dev/null)"
if grep -q -- '--base main' <<<"$out"; then ok "default mode injects --base main"; else bad "default mode injects --base main" "$out"; fi
if grep -q '^CODEX_ARGV: review' <<<"$out"; then ok "calls 'codex review'"; else bad "calls 'codex review'" "$out"; fi

# 3. same-branch (HEAD==base) falls back to --uncommitted, no --base (code#1 guard)
out="$(runa FAKE_CURRENT=main FAKE_BRANCHES=main 2>/dev/null)"
if grep -q -- '--uncommitted' <<<"$out" && ! grep -q -- '--base' <<<"$out"; then
  ok "same-branch falls back to --uncommitted"
else bad "same-branch falls back to --uncommitted" "$out"; fi

# 4. no conventional branch + no origin/HEAD -> fallback --uncommitted (detect_base fail path)
out="$(runa FAKE_CURRENT=x FAKE_BRANCHES= FAKE_ORIGIN_HEAD= 2>/dev/null)"
if grep -q -- '--uncommitted' <<<"$out"; then ok "no-base fallback to --uncommitted"; else bad "no-base fallback to --uncommitted" "$out"; fi

# 5. --uncommitted passes through and does NOT inject --base
out="$(runa FAKE_CURRENT=main FAKE_BRANCHES=main --uncommitted 2>/dev/null)"
if grep -q -- '--uncommitted' <<<"$out" && ! grep -q -- '--base' <<<"$out"; then
  ok "--uncommitted passes through without --base"
else bad "--uncommitted passes through without --base" "$out"; fi

# 6. explicit --base X honored exactly once
out="$(runa FAKE_CURRENT=feature FAKE_BRANCHES=main --base release 2>/dev/null)"
n="$(grep -o -- '--base' <<<"$out" | wc -l | tr -d ' ')"
if grep -q 'release' <<<"$out" && [[ "$n" == "1" ]]; then ok "explicit --base honored once"; else bad "explicit --base honored once" "count=$n $out"; fi

# 7. bare positional = prompt-driven review (no scope flag — codex's default
#    scope; codex-cli forbids combining a scope flag with a prompt)
out="$(runa FAKE_CURRENT=feature FAKE_BRANCHES=main 'focus on the auth changes' 2>/dev/null)"
if grep -q 'focus on the auth changes' <<<"$out" \
   && ! grep -q -- '--base' <<<"$out" && ! grep -q -- '--uncommitted' <<<"$out"; then
  ok "bare positional = prompt-driven review, no scope flag"
else bad "bare positional = prompt-driven review, no scope flag" "$out"; fi

# 8. -m MODEL is placed BEFORE 'review' (codex-cli: --model is a top-level option)
out="$(runa FAKE_CURRENT=feature FAKE_BRANCHES=main -m gpt-5.4 2>/dev/null)"
if grep -q -- '-m gpt-5.4 review' <<<"$out"; then ok "-m model precedes 'review'"; else bad "-m model precedes 'review'" "$out"; fi

# 9. SECURITY: unknown/write-enabling flag is rejected (sec#1 allowlist)
out="$(runa FAKE_CURRENT=feature FAKE_BRANCHES=main --write 2>&1)"; rc=$?
if [[ $rc -eq 64 ]] && grep -qi 'disallowed flag' <<<"$out"; then
  ok "write-enabling flag --write rejected (exit 64)"
else bad "write-enabling flag --write rejected (exit 64)" "rc=$rc out=$out"; fi

# 10. SECURITY: -c config override (could alter behavior) is also rejected
out="$(runa FAKE_CURRENT=feature FAKE_BRANCHES=main -c 'sandbox=full' 2>&1)"; rc=$?
if [[ $rc -eq 64 ]]; then ok "-c config override rejected"; else bad "-c config override rejected" "rc=$rc out=$out"; fi

# 11. scope flag + prompt rejected (codex-cli makes them mutually exclusive) -> exit 64
out="$(runa FAKE_CURRENT=feature FAKE_BRANCHES=main --base release 'focus here' 2>&1)"; rc=$?
if [[ $rc -eq 64 ]] && grep -qi 'cannot combine' <<<"$out"; then
  ok "scope flag + prompt rejected (exit 64)"
else bad "scope flag + prompt rejected (exit 64)" "rc=$rc out=$out"; fi

# 12. -m precedes 'review' in a prompt-driven run too (no scope flag injected)
out="$(runa FAKE_CURRENT=feature FAKE_BRANCHES=main -m gpt-5.4 'focus here' 2>/dev/null)"
if grep -q -- '-m gpt-5.4 review' <<<"$out" && grep -q 'focus here' <<<"$out" && ! grep -q -- '--base' <<<"$out"; then
  ok "-m precedes 'review' in prompt-driven run"
else bad "-m precedes 'review' in prompt-driven run" "$out"; fi

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]

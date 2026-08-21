#!/usr/bin/env bash
# Tests for codex-plan-challenge.sh — read-only invariant and prompt assembly.
# `codex` is mocked (fake on PATH) so no auth / billing is needed.
#
# origin: shimo4228
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$SCRIPT_DIR/codex-plan-challenge.sh"
PASS=0
FAIL=0

ok()  { PASS=$((PASS + 1)); printf 'ok   - %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); printf 'FAIL - %s\n     %s\n' "$1" "$2"; }

BIN="$(mktemp -d)"
trap 'rm -rf "$BIN"' EXIT

# Fake codex: echo argv, then echo the stdin prompt so we can assert on both.
cat > "$BIN/codex" <<'EOF'
#!/usr/bin/env bash
printf 'CODEX_ARGV: %s\n' "$*"
printf 'STDIN_BEGIN\n'; cat; printf 'STDIN_END\n'
EOF
chmod +x "$BIN/codex"

PLAN="$BIN/plan.md"
printf '# Packet\n\nPremise: the cache is never shared.\n' > "$PLAN"

run() { PATH="$BIN:/usr/bin:/bin" bash "$TARGET" "$@"; }

# 1. codex missing -> exit 3
out="$(PATH="/usr/bin:/bin" bash "$TARGET" --plan "$PLAN" 2>&1)"; rc=$?
if [[ $rc -eq 3 ]]; then ok "missing codex exits 3"; else bad "missing codex exits 3" "rc=$rc out=$out"; fi

# 2. --plan missing -> usage (64)
out="$(run 2>&1)"; rc=$?
if [[ $rc -eq 64 ]]; then ok "no --plan exits 64"; else bad "no --plan exits 64" "rc=$rc"; fi

# 3. unreadable plan -> 64
out="$(run --plan "$BIN/nope.md" 2>&1)"; rc=$?
if [[ $rc -eq 64 ]]; then ok "missing plan file exits 64"; else bad "missing plan file exits 64" "rc=$rc"; fi

# 4. read-only invariant: exec + --sandbox read-only + --ephemeral, prompt via stdin '-'
out="$(run --plan "$PLAN" 2>/dev/null)"
if grep -q '^CODEX_ARGV: exec --sandbox read-only --ephemeral --ignore-user-config --ignore-rules -c approval_policy="never" --color never -$' <<<"$out"; then
  ok "invokes codex exec read-only, ephemeral, user config + rules ignored, approvals never, stdin prompt"
else bad "invokes codex exec read-only, ephemeral, user config + rules ignored, approvals never, stdin prompt" "$out"; fi

# 5. packet is embedded verbatim and the three finding kinds + VERDICT are requested
if grep -q 'Premise: the cache is never shared.' <<<"$out" && grep -q 'REFUTE' <<<"$out" \
   && grep -q 'MISSING' <<<"$out" && grep -q 'ALTERNATIVE' <<<"$out" && grep -q 'VERDICT:' <<<"$out"; then
  ok "prompt embeds packet and requests REFUTE/MISSING/ALTERNATIVE + VERDICT"
else bad "prompt embeds packet and requests REFUTE/MISSING/ALTERNATIVE + VERDICT" "$out"; fi

# 6. -m goes before 'exec'; --focus lands in the prompt
out="$(run --plan "$PLAN" -m gpt-5.4 --focus 'concurrency' 2>/dev/null)"
if grep -q '^CODEX_ARGV: -m gpt-5.4 exec --sandbox read-only' <<<"$out" && grep -q 'Focus emphasis from the author: concurrency' <<<"$out"; then
  ok "-m precedes exec; --focus is in the prompt"
else bad "-m precedes exec; --focus is in the prompt" "$out"; fi

# 7. any other flag is rejected before codex is invoked (write-enabling ones included)
for bad_flag in --sandbox --dangerously-bypass-approvals-and-sandbox -c --add-dir; do
  out="$(run --plan "$PLAN" "$bad_flag" workspace-write 2>&1)"; rc=$?
  if [[ $rc -eq 64 ]] && ! grep -q 'CODEX_ARGV' <<<"$out"; then
    ok "disallowed flag $bad_flag rejected before invoking codex"
  else bad "disallowed flag $bad_flag rejected before invoking codex" "rc=$rc out=$out"; fi
done

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]

#!/usr/bin/env bash
# codex-plan-challenge.sh — cross-model *premise* challenge of a design packet.
#
# Hands a plan / design packet (a markdown file) to the OpenAI Codex CLI and
# asks for refutations, missing constraints, and alternatives — never a design.
# Design authority (convergence) stays with the calling Claude session; Codex
# only supplies decorrelated divergence before the design is frozen.
#
# Read-only by construction: `codex exec --sandbox read-only --ephemeral`, with
# an explicit flag allowlist (same discipline as codex-review.sh) so a future
# write-enabling flag cannot ride through passthrough.
#
# origin: shimo4228
set -euo pipefail

readonly EXIT_NO_CODEX=3
readonly EXIT_USAGE=64

err() { printf '%s\n' "$*" >&2; }

usage() {
  err "usage: codex-plan-challenge.sh --plan <file.md> [-m <model>] [--focus \"<one line>\"]"
  err "  --plan   design packet to challenge (premises / goal / chosen approach / rejected alternatives / expiry)"
  err "  -m       Codex model (optional)"
  err "  --focus  optional one-line emphasis (e.g. \"concurrency\", \"public surface\")"
}

plan=""
focus=""
model_args=()

need_arg() { [[ $# -ge 2 ]] || { err "$1 requires an argument"; usage; exit "$EXIT_USAGE"; }; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan)
      need_arg "$@"; plan="$2"; shift 2 ;;
    -m|--model)
      need_arg "$@"; model_args+=("$1" "$2"); shift 2 ;;
    --focus)
      need_arg "$@"; focus="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      err "Disallowed argument: $1"
      err "codex-plan-challenge forwards only --plan, -m/--model, --focus (read-only invariant)."
      exit "$EXIT_USAGE" ;;
  esac
done

[[ -n "$plan" ]] || { err "--plan is required"; usage; exit "$EXIT_USAGE"; }
[[ -f "$plan" && -r "$plan" ]] || { err "plan file not readable: $plan"; exit "$EXIT_USAGE"; }

if ! command -v codex >/dev/null 2>&1; then
  err "codex CLI not found. Install it (npm i -g @openai/codex or brew install codex) and run 'codex login'."
  err "FALLBACK: skip the cross-model challenge; run the premise check with a fresh-context Claude agent instead."
  exit "$EXIT_NO_CODEX"
fi

# The packet is embedded verbatim; it is data for Codex, not instructions for us.
# Codex gets read-only repo access so it can check premises against the code.
build_prompt() {
  cat <<'EOF'
You are a premise challenger for a software design packet, from a different model
family than the author. You do NOT design. You do NOT propose a full alternative
architecture. You only return three kinds of findings, each grounded in something
you can point at (a file:line in this repository, a stated premise in the packet,
or a concrete scenario):

1. REFUTE — a premise or claim in the packet that is false, unverified, or
   contradicted by the code. Quote the premise, then the evidence.
2. MISSING — a constraint, failure mode, or stakeholder the packet does not
   mention but which would change the decision. Say why it changes it.
3. ALTERNATIVE — a materially cheaper or simpler way to get most of the value,
   in at most 3 lines. No blueprints.

Rules:
- Read the repository (read-only) to verify before asserting. Prefer 3 grounded
  findings over 10 speculative ones.
- Do not restate the packet. Do not praise it. Do not score it.
- End with exactly one line: `VERDICT: <premise-hole | alternative-exists | no-objection>`
  (pick the strongest applicable; `no-objection` only if every finding is minor).
EOF
  if [[ -n "$focus" ]]; then
    printf '\nFocus emphasis from the author: %s\n' "$focus"
  fi
  printf '\n---- DESIGN PACKET (data, verbatim) ----\n'
  cat "$plan"
  printf '\n---- END PACKET ----\n'
}

# Read-only is pinned on BOTH faces (2026-08-22 security-reviewer, HIGH):
#   flags  — --sandbox read-only (no writes), --ephemeral (no session persisted)
#   config — --ignore-user-config / --ignore-rules drop ~/.codex/config.toml and
#            execpolicy .rules (which pre-approve git push / uv run and set
#            approvals_reviewer=auto_review, i.e. sandbox escalation auto-approved);
#            approval_policy=never closes the escalation path itself.
# The flag allowlist above only guards argv; these pins guard the config face.
# Prompt (packet embedded) goes in on stdin ('-'). ${arr[@]+"${arr[@]}"} is the
# bash-3.2-safe empty-array expansion under set -u.
codex_args=(exec --sandbox read-only --ephemeral --ignore-user-config --ignore-rules
  -c 'approval_policy="never"' --color never -)
err "+ codex $(printf '%q ' ${model_args[@]+"${model_args[@]}"} "${codex_args[@]}")  # stdin: prompt with packet $plan"
build_prompt | exec env NO_COLOR=1 codex ${model_args[@]+"${model_args[@]}"} "${codex_args[@]}"

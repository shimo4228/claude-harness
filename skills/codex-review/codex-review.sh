#!/usr/bin/env bash
# codex-review.sh — cross-model code review via the OpenAI Codex CLI.
#
# A read-only "second opinion" reviewer for the Claude Code review chain.
# Codex (a different model family) reviews the diff and reports findings; it
# never writes to the filesystem. The calling agent (Claude) owns the verdict.
#
# The read-only invariant is enforced here by an explicit flag allowlist, so it
# does not depend on the external Codex CLI never adding write-enabling flags.
#
# origin: shimo4228
set -euo pipefail

readonly EXIT_NO_CODEX=3
readonly EXIT_NO_GIT=4
readonly EXIT_USAGE=64

err() { printf '%s\n' "$*" >&2; }

# Exec `codex review` read-only. Model flags are a TOP-LEVEL codex option
# (codex-cli 0.142: `-m/--model` is not a `review` option), so they go BEFORE
# the `review` subcommand. Branch on count to stay safe under `set -u` on the
# stock macOS bash 3.2 (where "${empty[@]}" would be an unbound-variable error).
run_codex() {
  if [[ ${#model_args[@]} -gt 0 ]]; then
    err "+ codex ${model_args[*]} review $(printf '%q ' "${codex_args[@]}")"
    exec env NO_COLOR=1 codex "${model_args[@]}" review "${codex_args[@]}"
  fi
  err "+ codex review $(printf '%q ' "${codex_args[@]}")"
  exec env NO_COLOR=1 codex review "${codex_args[@]}"
}

# --- preconditions -----------------------------------------------------------
if ! command -v codex >/dev/null 2>&1; then
  err "codex CLI not found. Install it (npm i -g @openai/codex or brew install codex) and run 'codex login'."
  err "FALLBACK: skip the cross-model review; rely on the in-Claude reviewers only."
  exit "$EXIT_NO_CODEX"
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  err "Not inside a git repository. codex-review needs a repo to diff against."
  exit "$EXIT_NO_GIT"
fi

# --- base branch detection ---------------------------------------------------
detect_base() {
  local b
  for b in main master develop trunk; do
    if git show-ref --verify --quiet "refs/heads/$b"; then
      printf '%s' "$b"
      return 0
    fi
  done
  # fall back to origin's default HEAD when no conventional local branch exists
  b="$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null || true)"
  if [[ -n "$b" ]]; then
    printf '%s' "${b#refs/remotes/origin/}"
    return 0
  fi
  return 1
}

# --- arg parsing (allowlist only; no eval; passed through as an argv array) ---
# Only the flags documented in SKILL.md are forwarded to `codex review`. Unknown
# flags are rejected so a future write-enabling Codex flag cannot silently break
# the read-only invariant via passthrough.
mode_given=0       # a scope flag (--uncommitted/--base/--commit) was supplied
prompt=""
prompt_given=0
codex_args=()
model_args=()      # -m/--model — top-level codex option, goes BEFORE 'review'

while [[ $# -gt 0 ]]; do
  case "$1" in
    --uncommitted)
      codex_args+=("$1"); mode_given=1; shift ;;
    --base|--commit)
      [[ $# -ge 2 ]] || { err "$1 requires an argument"; exit "$EXIT_USAGE"; }
      codex_args+=("$1" "$2"); mode_given=1; shift 2 ;;
    -m|--model)
      [[ $# -ge 2 ]] || { err "$1 requires an argument"; exit "$EXIT_USAGE"; }
      model_args+=("$1" "$2"); shift 2 ;;
    --prompt)
      [[ $# -ge 2 ]] || { err "$1 requires an argument"; exit "$EXIT_USAGE"; }
      prompt="$2"; prompt_given=1; shift 2 ;;
    -*)
      err "Disallowed flag: $1"
      err "codex-review forwards only --uncommitted, --base, --commit, -m/--model, --prompt (read-only invariant)."
      err "For a prompt starting with '-', use: --prompt \"$1 ...\""
      exit "$EXIT_USAGE" ;;
    *)
      prompt="$1"; prompt_given=1; shift ;;  # bare positional = custom review prompt
  esac
done

# codex-cli (>= 0.142) makes the scope flags (--uncommitted/--base/--commit)
# mutually exclusive with a PROMPT positional. Enforce it here with a clear
# message instead of leaking codex's raw argparse error.
if [[ "$mode_given" -eq 1 && "$prompt_given" -eq 1 ]]; then
  err "codex review cannot combine a scope flag with a custom prompt (codex-cli limitation)."
  err "Use EITHER a scoped review (--uncommitted/--base/--commit — Codex's built-in review)"
  err "OR a prompt-driven review of the working tree (a bare prompt / --prompt), not both."
  exit "$EXIT_USAGE"
fi

# --- run (read-only review; NO_COLOR keeps output clean for the parser) -------
# Trace each arg shell-quoted (%q) so space/ANSI-bearing values are unambiguous.

# A custom prompt drives codex's default (working-tree) review — no scope flag
# (the two cannot coexist). -m/--model, if given, still rides along in codex_args.
if [[ "$prompt_given" -eq 1 ]]; then
  codex_args+=("$prompt")
  run_codex
fi

# Otherwise a scoped review. Default scope = current branch vs detected base.
if [[ "$mode_given" -eq 0 ]]; then
  if base="$(detect_base)"; then
    current="$(git symbolic-ref --short HEAD 2>/dev/null || true)"
    if [[ -n "$current" && "$base" == "$current" ]]; then
      err "HEAD is already on '$base'; nothing to diff against it. Falling back to --uncommitted."
      codex_args+=(--uncommitted)
    else
      codex_args+=(--base "$base")
    fi
  else
    err "Could not detect a base branch; defaulting to --uncommitted."
    codex_args+=(--uncommitted)
  fi
fi
run_codex

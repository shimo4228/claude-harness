#!/usr/bin/env bash
# sync-from-local.sh — one-way export from the live Claude Code harness
# (~/.claude) into this publication repo.
#
# Collects components whose origin marker matches ORIGIN (frontmatter
# `origin: <value>` or HTML comment `<!-- origin: <value> -->`), stages
# them, runs a secret scan, then replaces the managed subtrees
# (skills/ agents/ rules/) wholesale. Root files (README, LICENSE,
# llms*.txt) are never touched. The script never commits — `git diff`
# in this repo is the review gate.
#
# Usage:
#   scripts/sync-from-local.sh --dry-run   # report differences only
#   scripts/sync-from-local.sh             # apply to working tree
#
# Config (env overrides):
#   HARNESS_SYNC_SOURCE  source harness dir   (default: ~/.claude)
#   HARNESS_SYNC_ORIGIN  origin value to match (default: shimo4228)

set -euo pipefail

SOURCE_DIR="${HARNESS_SYNC_SOURCE:-$HOME/.claude}"
ORIGIN="${HARNESS_SYNC_ORIGIN:-shimo4228}"
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUBTREES=(skills agents rules)

DRY_RUN=0
[[ "${1:-}" == "--dry-run" || "${1:-}" == "-n" ]] && DRY_RUN=1

# --- guard: managed subtrees must be clean so the sync delta is reviewable ---
if (( ! DRY_RUN )); then
  if ! git -C "$TARGET_DIR" diff --quiet -- "${SUBTREES[@]}" ||
     ! git -C "$TARGET_DIR" diff --cached --quiet -- "${SUBTREES[@]}"; then
    echo "ABORT: uncommitted changes in ${SUBTREES[*]} — commit or stash first," >&2
    echo "       so that 'git diff' after sync shows exactly the sync delta." >&2
    exit 1
  fi
fi

# --- staging ---
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
mkdir -p "$STAGING/skills" "$STAGING/agents" "$STAGING/rules"

has_origin() { head -15 "$1" | grep -q "origin: $ORIGIN"; }

# skills: directories whose SKILL.md declares the origin
for skill_md in "$SOURCE_DIR"/skills/*/SKILL.md; do
  [[ -f "$skill_md" ]] || continue
  has_origin "$skill_md" || continue
  cp -R "$(dirname "$skill_md")" "$STAGING/skills/"
done

# agents: flat *.md with the origin
for agent in "$SOURCE_DIR"/agents/*.md; do
  [[ -f "$agent" ]] || continue
  has_origin "$agent" || continue
  cp "$agent" "$STAGING/agents/"
done

# rules: *.md with the origin marker, preserving subdirectory layout
while IFS= read -r rule; do
  rel="${rule#"$SOURCE_DIR"/rules/}"
  mkdir -p "$STAGING/rules/$(dirname "$rel")"
  cp "$rule" "$STAGING/rules/$rel"
done < <(grep -rl "origin: $ORIGIN" "$SOURCE_DIR/rules/" 2>/dev/null || true)

# --- prune runtime artifacts from the staged payload ---
find "$STAGING" \( -name results.json -o -name '*.log' -o -name '*.pyc' \
  -o -name .DS_Store -o -name .coverage -o -name '.coverage.*' \) -delete
find "$STAGING" \( -name __pycache__ -o -name .pytest_cache -o -name .venv \
  -o -name node_modules -o -name .mypy_cache -o -name .ruff_cache \
  -o -name htmlcov \) -type d -prune -exec rm -rf {} + 2>/dev/null || true

# --- secret scan (high-confidence patterns; abort on any hit) ---
SECRET_RE='sk-ant-api[0-9A-Za-z_-]+|ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{20,}|AKIA[0-9A-Z]{16}|xox[bporas]-[0-9A-Za-z-]{10,}|AIza[0-9A-Za-z_-]{35}|hf_[A-Za-z]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY'
if hits="$(grep -rEl "$SECRET_RE" "$STAGING" 2>/dev/null)"; then
  echo "ABORT: potential secrets detected in staged payload:" >&2
  echo "$hits" >&2
  exit 1
fi

# --- report / apply ---
if (( DRY_RUN )); then
  echo "# DRY-RUN (origin: $ORIGIN) — differences staging vs $TARGET_DIR"
  for t in "${SUBTREES[@]}"; do
    diff -rq "$STAGING/$t" "$TARGET_DIR/$t" 2>/dev/null || true
  done
  exit 0
fi

for t in "${SUBTREES[@]}"; do
  rm -rf "${TARGET_DIR:?}/$t"
done
cp -R "$STAGING"/. "$TARGET_DIR"/

echo "# APPLIED (origin: $ORIGIN). Review before committing:"
git -C "$TARGET_DIR" status --short

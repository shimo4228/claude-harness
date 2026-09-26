#!/usr/bin/env bash
# launchd entry for review-when-watch (scripts/launchd/com.shimomoto.review-when-watch.plist,
# daily 06:10 — after jev-research-pipeline's `jrp run` at 05:00, which takes about 15 min).
#
# The jrp notes live in the vault in iCloud Drive, which macOS privacy (TCC) guards per
# executable. Under launchd, /bin/bash may open it but the uv-managed python may not: its
# open() waits on an invisible consent prompt forever (jrp's first scheduled run hung 80 min
# on this, 2026-09-24). So bash copies the notes to a local stage — the same rsync jrp's own
# wrapper uses — and python reads only the stage (REVIEW_WHEN_REPORTS_DIR). Nothing in the
# vault is written.
#
# JRP_VAULT_DIR comes from the environment or from jrp's env file. That file also holds the
# pipeline's other secrets, so it is sourced in a subshell and only this one value leaves it.
# If the vault cannot be found or copied, this says so on Slack and stops: running python
# on an empty or stale stage would look like a quiet day instead of a broken job.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
ROOT="$(cd "$HERE/../.." && pwd -P)"
ENV_FILE="${JRP_ENV_FILE:-${HOME}/.config/jrp/env}"
UV="${REVIEW_WHEN_UV:-${HOME}/.local/bin/uv}"            # overridable for tests
NOTIFY="${REVIEW_WHEN_NOTIFY:-${ROOT}/scripts/notify-slack.sh}"
STAGE="${REVIEW_WHEN_STAGE:-${XDG_CACHE_HOME:-${HOME}/.cache}/review-when-watch/stage}"

fail() {
  printf 'review-when-watch: %s\n' "$1" >&2
  bash "$NOTIFY" "review-when-watch: 動かせない" "$1" >/dev/null 2>&1 || true
  exit 2
}

VAULT="${JRP_VAULT_DIR:-}"
if [[ -z "$VAULT" && -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  VAULT="$(set +eu; set -a; source "$ENV_FILE" >/dev/null 2>&1; printf '%s' "${JRP_VAULT_DIR:-}")"
fi
[[ -n "$VAULT" ]] || fail "JRP_VAULT_DIR が分からない（環境変数にも ${ENV_FILE} にも無い）"
[[ -d "$VAULT/daily-research" ]] || fail "レポートの置き場所が無い: ${VAULT}/daily-research"

mkdir -p "$STAGE"
rsync -a --delete --include='*_jrp_*.md' --exclude='*' "$VAULT/daily-research/" "$STAGE/" ||
  fail "vault からのコピーに失敗: ${VAULT}/daily-research"

cd "$HERE"
REVIEW_WHEN_REPORTS_DIR="$STAGE" exec "$UV" run --project "$HERE" --frozen --no-dev \
  python -m scripts.watch "$@"

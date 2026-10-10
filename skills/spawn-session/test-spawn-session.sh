#!/usr/bin/env bash
# spawn-session の bats テストを走らせる入口（~/.claude の verify が skills/*/test-*.sh を実行する）。
set -euo pipefail
command -v bats >/dev/null || { echo "bats not found (brew install bats-core)" >&2; exit 1; }
exec bats "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/tests"

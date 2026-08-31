#!/usr/bin/env bats
# Golden: scripts/claims.py `ready` の出力全形を凍結する。
# この 1 行形式は triage セッションが parse する契約（rule task-tracking）。列幅・
# 切り詰め・末尾の単一表誘導が黙って変わると loop が壊れるので、全バイトで固定する。
# 挙動の部分 assert は tests/task-claims.bats。
#
# claimed mark（[claimed xxxx 3h]）は fmt_age が時刻依存のため**凍結しない** —
# fixture は claim なしで作る。詳細: tests/golden/README.md
#
# 再生成: setup と同じ fixture を作り、各テストのコマンドの出力をリダイレクト。
#
# Run: bats ~/.claude/tests/golden-claims-ready.bats

HELPER="${BATS_TEST_DIRNAME}/../scripts/claims.py"
GOLDEN="${BATS_TEST_DIRNAME}/golden/claims"

claims() { python3 "$HELPER" "$@"; }

setup() {
  REPO="$BATS_TEST_TMPDIR/repo"
  mkdir -p "$REPO/rfcs" "$REPO/.notes"
  export CLAUDE_PROJECT_DIR="$REPO"
  export CLAUDE_CODE_SESSION_ID="aaaaaaaa-1111-2222-3333-444444444444"

  cat > "$REPO/rfcs/0001-alpha.md" <<'EOF'
---
state: accepted
---

# RFC-0001: Alpha

Alpha を導入する提案の要約行。90 字の切り詰めに届かない普通の長さ。
EOF

  cat > "$REPO/rfcs/0002-beta.md" <<'EOF'
---
state: draft
---

# RFC-0002: Beta

draft なので ready には出ない。
EOF

  # 日付つき state（先頭語照合）と、90 字切り詰めを踏む長い要約
  cat > "$REPO/rfcs/0003-gamma.md" <<'EOF'
---
state: accepted 2026-08-30
---

# RFC-0003: Gamma

この要約行はわざと長く書いてある。ready の 1 行形式は要約を 90 字で切り詰める仕様で、その切り詰め挙動こそ golden で固定したい対象だから、ここは 90 字を確実に超える長さにしてある。
EOF

  # 単一表にも T- 行がある移行期 repo → 末尾の誘導行が出る
  printf '| ID | 状態 |\n| T-002 | accepted |\n' > "$REPO/.notes/TASKS.md"
}

@test "golden: ready (2 accepted rows, truncation, single-table hint)" {
  run claims ready
  [ "$status" -eq 0 ]
  printf '%s\n' "$output" | diff - "$GOLDEN/ready.txt"
}

@test "golden: ready --state blocked (empty-state message)" {
  run claims ready --state blocked
  [ "$status" -eq 0 ]
  printf '%s\n' "$output" | diff - "$GOLDEN/ready-empty.txt"
}

@test "golden: repo without rfcs/ points at the single table" {
  rm -rf "$REPO/rfcs"
  run claims ready
  [ "$status" -eq 0 ]
  printf '%s\n' "$output" | diff - "$GOLDEN/ready-no-store.txt"
}

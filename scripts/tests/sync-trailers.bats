#!/usr/bin/env bats
# sync-from-local.sh が source commit の trailer を同期 commit の本文の下書きへ写すことのテスト（RFC-0029）。
#
# 主張していること:
#   - 列挙の範囲は target の最新の `Source: <full sha>` 行から source の HEAD まで。行が無い初回だけ、
#     target の最新の `chore: sync from local harness` commit の日時以降
#   - staging に入ったパスを触らない commit は出ない
#   - 写すのは Review / Context / Decision / Review-when / Plan / 指摘 / Trigger / Expect だけで、
#     継続行は trailer に付いていく。`指摘:` に続く `Trigger:` / `Expect:` は 1 件として数える
#   - 下書きは `.git/` の中に書き、末尾は `Source: <source HEAD の full sha>`
#   - 下書きに secret の形か $HOME/ の実値が入ると、既存の scan と同じ文言で abort し、tree も下書きも残さない
#   - --dry-run は件数を 1 行で出し、ファイルを書かない
#
# fixture は一時ディレクトリの source repo と target repo だけを使う。script は TARGET_DIR を自分の置き場所
# から決めるので、target repo の scripts/ へ写して走らせる。

SCRIPT_DIR="${BATS_TEST_DIRNAME}/.."

setup() {
  export HOME="$BATS_TEST_TMPDIR/home"
  mkdir -p "$HOME"
  export GIT_CONFIG_NOSYSTEM=1
  export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid
  export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid
  SRC="$BATS_TEST_TMPDIR/src"
  TGT="$BATS_TEST_TMPDIR/tgt"
  export HARNESS_SYNC_SOURCE="$SRC"

  # source: HOOK_ALLOWLIST の全ファイル（無いと script が abort する）と、公開対象の skill 1 本
  git init -q -b main "$SRC"
  while IFS= read -r rel; do
    mkdir -p "$SRC/$(dirname "$rel")"
    printf 'stub\n' > "$SRC/$rel"
  done < <(allowlist)
  mkdir -p "$SRC/skills/demo" "$SRC/other"
  printf -- '---\nname: demo\ndescription: Demo skill.\norigin: shimo4228\n---\nbody\n' > "$SRC/skills/demo/SKILL.md"
  printf 'private\n' > "$SRC/other/notes.md"
  git -C "$SRC" add -A
  commit_at "$SRC" "2025-11-01T00:00:00Z" "init source"

  # target: 公開 repo の最小形（README と component ページが無いと表の再生成が abort する）
  mkdir -p "$TGT/scripts" "$TGT/docs"
  cp "$SCRIPT_DIR/sync-from-local.sh" "$SCRIPT_DIR/sync_trailers.py" "$TGT/scripts/"
  for f in README.md README.ja.md docs/components.md docs/components.ja.md; do
    printf '# x\n' > "$TGT/$f"
  done
  git init -q -b main "$TGT"
  git -C "$TGT" add -A
}

# HOOK_ALLOWLIST の中身を script 自身から読む（複製すると drift する）
allowlist() {
  sed -n '/^HOOK_ALLOWLIST=(/,/^)/p' "$SCRIPT_DIR/sync-from-local.sh" |
    sed -e '1d' -e '$d' -e 's/^[[:space:]]*//' | grep -v '^#' | grep -v '^$'
}

# commit_at <repo> <iso date> <message>（日付を固定して --since の境界を決定的にする）
commit_at() {
  GIT_AUTHOR_DATE="$2" GIT_COMMITTER_DATE="$2" git -C "$1" commit -q --allow-empty -m "$3"
}

# source の skill を変えて commit する: src_commit <date> <message>
src_commit() {
  printf '%s\n' "$RANDOM$RANDOM" >> "$SRC/skills/demo/SKILL.md"
  git -C "$SRC" add skills/demo/SKILL.md
  commit_at "$SRC" "$1" "$2"
}

# target の初回同期 commit（Source 行なし）
tgt_first_sync() {
  commit_at "$TGT" "$1" "chore: sync from local harness (origin: shimo4228)"
}

body_path() { git -C "$TGT" rev-parse --absolute-git-dir | sed 's|$|/SYNC_COMMIT_BODY|'; }

run_sync() { run bash "$TGT/scripts/sync-from-local.sh" "$@"; }

short() { git -C "$SRC" rev-parse --short "$1"; }

@test "(a) range starts after the latest Source: line in the target" {
  tgt_first_sync "2025-12-01T00:00:00Z"
  src_commit "2026-02-01T00:00:00Z" "feat: before the last sync"
  base="$(git -C "$SRC" rev-parse HEAD)"
  commit_at "$TGT" "2026-01-15T00:00:00Z" "$(printf 'chore: sync from local harness (origin: shimo4228)\n\nSource: %s' "$base")"
  src_commit "2026-03-01T00:00:00Z" "$(printf 'feat: after the last sync\n\nContext: why it changed')"

  run_sync
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  body="$(body_path)"
  [[ "$output" == *"# commit body: $body"* ]] || { echo "$output"; return 1; }
  grep -qF "$(short HEAD~0) feat: after the last sync" "$body"
  grep -qx 'Context: why it changed' "$body"
  ! grep -q 'before the last sync' "$body" || return 1
  ! grep -q 'init source' "$body" || return 1
  [ "$(tail -n 1 "$body")" = "Source: $(git -C "$SRC" rev-parse HEAD)" ]
}

@test "(b) first sync falls back to the date of the latest sync commit" {
  src_commit "2026-02-01T00:00:00Z" "feat: older than the first sync"
  tgt_first_sync "2026-02-15T00:00:00Z"
  src_commit "2026-03-01T00:00:00Z" "feat: newer than the first sync"

  run_sync
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  body="$(body_path)"
  grep -q 'feat: newer than the first sync' "$body"
  ! grep -q 'older than the first sync' "$body" || return 1
  ! grep -q 'init source' "$body" || return 1
}

@test "(c) commits that touch only non-synced paths are not listed" {
  tgt_first_sync "2025-12-01T00:00:00Z"
  printf 'more\n' >> "$SRC/other/notes.md"
  git -C "$SRC" add other/notes.md
  commit_at "$SRC" "2026-02-01T00:00:00Z" "$(printf 'docs: private note\n\nDecision: keep it private')"
  src_commit "2026-03-01T00:00:00Z" "feat: synced change"

  run_sync
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  body="$(body_path)"
  grep -q 'feat: synced change' "$body"
  ! grep -q 'private note' "$body" || return 1
  ! grep -q 'keep it private' "$body" || return 1
}

@test "(d) only the eight trailer keys are copied, with their continuation lines" {
  tgt_first_sync "2025-12-01T00:00:00Z"
  msg='feat: many trailers

free prose that is not a trailer

Context: first line
continued context
Decision: chosen
Verified: 12 tests pass
continued verified
Intake: some-tool 1.2
Source: 0000000000000000000000000000000000000000
Reviews: not the Review key
Review-when: when it changes
Plan: docs/plans/x.html
Review: security-reviewer none'
  src_commit "2026-03-01T00:00:00Z" "$msg"

  run_sync
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  body="$(body_path)"
  expected="$(short HEAD) feat: many trailers
Context: first line
continued context
Decision: chosen
Review-when: when it changes
Plan: docs/plans/x.html
Review: security-reviewer none

Source: $(git -C "$SRC" rev-parse HEAD)"
  [ "$(cat "$body")" = "$expected" ] || { diff <(echo "$expected") "$body"; return 1; }
}

@test "(e) a correction block (shiteki + Trigger + Expect) stays whole and counts as one trailer" {
  tgt_first_sync "2025-12-01T00:00:00Z"
  msg='docs: author corrections

Decision: rewrite the title

指摘: 「タイトルを変えて」
Trigger: the title was too narrow
Expect: readers still bounce on the title

指摘: 「1で」
Trigger: offered three candidates
Expect: the chosen title loses readers'
  src_commit "2026-03-01T00:00:00Z" "$msg"

  run_sync --dry-run
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  [[ "$output" == *"# source commits: 1, trailers: 3"* ]] || { echo "$output"; return 1; }

  run_sync
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  body="$(body_path)"
  [ "$(grep -A2 -x '指摘: 「タイトルを変えて」' "$body")" = '指摘: 「タイトルを変えて」
Trigger: the title was too narrow
Expect: readers still bounce on the title' ]
  [ "$(grep -A2 -x '指摘: 「1で」' "$body")" = '指摘: 「1で」
Trigger: offered three candidates
Expect: the chosen title loses readers' ]
}

@test "(f) a trailer carrying the literal \$HOME/ aborts before anything is applied" {
  tgt_first_sync "2025-12-01T00:00:00Z"
  src_commit "2026-03-01T00:00:00Z" "$(printf 'feat: leaky\n\nContext: see %s/MyAI_Lab/private-repo' "$HOME")"

  run_sync
  [ "$status" -ne 0 ]
  [[ "$output" == *"ABORT: absolute home-directory paths in commit body draft"* ]] || { echo "$output"; return 1; }
  [ ! -e "$(body_path)" ]
  [ ! -e "$TGT/skills" ]
}

@test "(g) a trailer carrying a secret shape aborts with the secret-scan wording" {
  tgt_first_sync "2025-12-01T00:00:00Z"
  token="ghp_$(printf 'a%.0s' {1..36})"
  src_commit "2026-03-01T00:00:00Z" "$(printf 'feat: secret\n\nReview: token %s' "$token")"

  run_sync
  [ "$status" -ne 0 ]
  [[ "$output" == *"ABORT: potential secrets detected in commit body draft"* ]] || { echo "$output"; return 1; }
  [[ "$output" != *"$token"* ]] || { echo "the token itself was printed"; return 1; }
  [ ! -e "$(body_path)" ]
}

@test "(h) --dry-run reports counts in one line and writes no file" {
  tgt_first_sync "2025-12-01T00:00:00Z"
  src_commit "2026-02-01T00:00:00Z" "$(printf 'feat: one\n\nContext: a\nDecision: b')"
  src_commit "2026-03-01T00:00:00Z" "feat: two"

  run_sync --dry-run
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  [ "$(grep -c '^# source commits: ' <<<"$output")" -eq 1 ]
  [[ "$output" == *"# source commits: 2, trailers: 2"* ]] || { echo "$output"; return 1; }
  [ ! -e "$(body_path)" ]
  [ ! -e "$TGT/skills" ]
}

@test "(i) a Source: line naming a commit the source does not have falls back to the date, with a warning" {
  tgt_first_sync "2026-02-15T00:00:00Z"
  commit_at "$TGT" "2026-02-16T00:00:00Z" "$(printf 'chore: sync from local harness (origin: shimo4228)\n\nSource: %s' 1111111111111111111111111111111111111111)"
  src_commit "2026-02-01T00:00:00Z" "feat: older"
  src_commit "2026-03-01T00:00:00Z" "feat: newer"

  run_sync
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  [[ "$output" == *"WARN: Source: 1111111111111111111111111111111111111111 is not a commit in"* ]] || { echo "$output"; return 1; }
  body="$(body_path)"
  grep -q 'feat: newer' "$body"
  ! grep -q 'feat: older' "$body" || return 1
}

@test "(j) a commit that deletes a published file is listed, though the file is no longer staged" {
  mkdir -p "$SRC/skills/old" "$TGT/skills/old"
  printf -- '---\nname: old\ndescription: Old.\norigin: shimo4228\n---\n' > "$SRC/skills/old/SKILL.md"
  cp "$SRC/skills/old/SKILL.md" "$TGT/skills/old/SKILL.md"
  git -C "$SRC" add skills/old
  commit_at "$SRC" "2025-11-02T00:00:00Z" "feat: old skill"
  git -C "$TGT" add skills/old
  tgt_first_sync "2025-12-01T00:00:00Z"
  git -C "$SRC" rm -q -r skills/old
  commit_at "$SRC" "2026-03-01T00:00:00Z" "$(printf 'refactor: retire old\n\nDecision: retire the old skill')"

  run_sync
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  body="$(body_path)"
  grep -q 'refactor: retire old' "$body"
  grep -qx 'Decision: retire the old skill' "$body"
  [ ! -e "$TGT/skills/old" ]
}

@test "(k) a newer sync commit without a Source: line moves the start to its date" {
  tgt_first_sync "2025-12-01T00:00:00Z"
  src_commit "2026-01-10T00:00:00Z" "feat: carried by the Source sync"
  base="$(git -C "$SRC" rev-parse HEAD)"
  commit_at "$TGT" "2026-01-11T00:00:00Z" "$(printf 'chore: sync from local harness (origin: shimo4228)\n\nSource: %s' "$base")"
  src_commit "2026-02-01T00:00:00Z" "feat: carried by the hand-written sync"
  commit_at "$TGT" "2026-02-02T00:00:00Z" "chore: sync from local harness (origin: shimo4228)"
  src_commit "2026-03-01T00:00:00Z" "feat: new since the last sync"

  run_sync
  [ "$status" -eq 0 ] || { echo "$output"; return 1; }
  body="$(body_path)"
  grep -q 'feat: new since the last sync' "$body"
  ! grep -q 'carried by the hand-written sync' "$body" || return 1
  ! grep -q 'carried by the Source sync' "$body" || return 1
}

@test "(l) a run stopped by the clean-tree guard removes the previous draft" {
  mkdir -p "$TGT/rules"
  printf 'x\n' > "$TGT/rules/r.md"
  git -C "$TGT" add rules/r.md
  tgt_first_sync "2025-12-01T00:00:00Z"
  printf 'stale\n' > "$(body_path)"
  printf 'edited\n' >> "$TGT/rules/r.md"

  run_sync
  [ "$status" -ne 0 ]
  [[ "$output" == *"ABORT: uncommitted changes"* ]] || { echo "$output"; return 1; }
  [ ! -e "$(body_path)" ]
}

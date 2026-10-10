#!/usr/bin/env bats
# spawn.sh の引数と失敗経路を、agent-send の偽 herdr / claude で固定する。

setup() {
  SCRIPT="$BATS_TEST_DIRNAME/../spawn.sh"
  export FAKE_STATE="$BATS_TEST_TMPDIR/state"
  mkdir -p "$FAKE_STATE"
  : > "$FAKE_STATE/calls.log"
  export PATH="$BATS_TEST_DIRNAME/../../agent-send/tests/bin:$PATH"
  export CLAUDE_CONFIG_DIR="$BATS_TEST_TMPDIR/claude"
  export AGENT_SEND_TRANSCRIPT_WAIT_S=0
  PROJECT="$BATS_TEST_TMPDIR/proj"
  mkdir -p "$PROJECT"
}

set_state() { printf '%s' "$2" > "$FAKE_STATE/$1"; }

@test "--effort と --permission-mode を claude に渡す" {
  run "$SCRIPT" "$PROJECT" "Proj/fix" --model opus --effort high --permission-mode plan
  [ "$status" -eq 0 ]
  grep -q -- 'agent start .* -- --remote-control Proj/fix --model opus --effort high --permission-mode plan' "$FAKE_STATE/calls.log"
}

@test "不正な --effort は 64" {
  run "$SCRIPT" "$PROJECT" "Proj" --effort turbo
  [ "$status" -eq 64 ]
}

@test "bypassPermissions は受けない" {
  run "$SCRIPT" "$PROJECT" "Proj" --permission-mode bypassPermissions
  [ "$status" -eq 64 ]
  ! grep -q 'agent start' "$FAKE_STATE/calls.log"
}

@test "無い --prompt-file は 64" {
  run "$SCRIPT" "$PROJECT" "Proj" --prompt-file "$BATS_TEST_TMPDIR/none.md"
  [ "$status" -eq 64 ]
}

@test "--prompt-file は起動後に agent-send で送り、結果を出す" {
  printf 'kickoff text\n' > "$BATS_TEST_TMPDIR/packet.md"
  set_state agents.json '{"result":{"agents":[{"name":"x","pane_id":"w9:p1","agent":"claude"}]}}'
  run "$SCRIPT" "$PROJECT" "Proj" --prompt-file "$BATS_TEST_TMPDIR/packet.md"
  [ "$status" -eq 0 ]
  [[ "$output" == *"prompt: result=landed pane=w9:p1 via=working"* ]]
  grep -q -- 'agent prompt w9:p1 kickoff text' "$FAKE_STATE/calls.log"
}

@test "指示が届かなければ、起動はしたうえで agent-send の exit code を返す" {
  printf 'kickoff text\n' > "$BATS_TEST_TMPDIR/packet.md"
  set_state agents.json '{"result":{"agents":[{"name":"x","pane_id":"w9:p1","agent":"claude"}]}}'
  set_state prompt_reply timeout
  run "$SCRIPT" "$PROJECT" "Proj" --prompt-file "$BATS_TEST_TMPDIR/packet.md"
  [ "$status" -eq 2 ]
  [[ "$output" == *"Remote Control session started"* ]]
  [[ "$output" == *"prompt: result=no_evidence"* ]]
}

@test "trust の確認で止まったら理由と agent 名を出す" {
  set_state start_reply agent_not_ready
  set_state screen 'Is this a project you created or one you trust?'
  run "$SCRIPT" "$PROJECT" "Proj"
  [ "$status" -eq 1 ]
  [[ "$output" == *"workspace trust"* ]]
  [[ "$output" == *"agent: proj-"*"pane: w9:p1"* ]]
}

@test "Herdr の互換が無ければ起動しない" {
  set_state status.json '{"client":{"version":"0.9.3"},"server":{"running":true,"version":"0.9.3","compatible":false,"endpoint_compatible":false},"update":{}}'
  run "$SCRIPT" "$PROJECT" "Proj"
  [ "$status" -eq 1 ]
  ! grep -q 'agent start' "$FAKE_STATE/calls.log"
}

@test "値の無い --effort は 64" {
  run "$SCRIPT" "$PROJECT" "Proj" --effort
  [ "$status" -eq 64 ]
}

@test "preflight の失敗理由を出す" {
  set_state status.json '{"client":{"version":"0.9.3"},"server":{"running":true,"version":"0.8.2","compatible":true,"endpoint_compatible":true},"update":{}}'
  run "$SCRIPT" "$PROJECT" "Proj"
  [ "$status" -eq 1 ]
  [[ "$output" == *"server_too_old"* ]]
}

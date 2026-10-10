#!/usr/bin/env bats
# agent-send.sh の分岐を、偽の herdr / claude（tests/bin）で固定する。

setup() {
  SCRIPT="$BATS_TEST_DIRNAME/../agent-send.sh"
  export FAKE_STATE="$BATS_TEST_TMPDIR/state"
  mkdir -p "$FAKE_STATE"
  : > "$FAKE_STATE/calls.log"
  export PATH="$BATS_TEST_DIRNAME/bin:$PATH"
  export CLAUDE_CONFIG_DIR="$BATS_TEST_TMPDIR/claude"
  mkdir -p "$CLAUDE_CONFIG_DIR/projects/p"
  # 待ちを速くする（本番の既定は 30 秒間隔）
  export AGENT_SEND_TRANSCRIPT_WAIT_S=0
}

set_state() { printf '%s' "$2" > "$FAKE_STATE/$1"; }
calls() { grep -c -- "$1" "$FAKE_STATE/calls.log" || true; }

@test "引数なしは usage で 64" {
  run "$SCRIPT"
  [ "$status" -eq 64 ]
}

@test "idle の相手に送り、working を見たら landed" {
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 0 ]
  [[ "$output" == "result=landed pane=w1:p1 via=working" ]]
  grep -q -- 'agent prompt w1:p1 hello --wait --until working --until blocked' "$FAKE_STATE/calls.log"
}

@test "--file の中身を送る" {
  printf 'line one\nline two\n' > "$BATS_TEST_TMPDIR/packet.md"
  run "$SCRIPT" prompt w1:p1 --file "$BATS_TEST_TMPDIR/packet.md"
  [ "$status" -eq 0 ]
  grep -q -- 'line one' "$FAKE_STATE/calls.log"
}

@test "blocked の相手には送らない" {
  set_state status blocked
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 3 ]
  [[ "$output" == result=blocked* ]]
  [ "$(calls 'agent prompt')" -eq 0 ]
}

@test "working の相手が期限内に終わらなければ busy で送らない" {
  set_state status working
  set_state wait_rc 1
  run "$SCRIPT" prompt w1:p1 --text "hello" --busy-timeout 10
  [ "$status" -eq 4 ]
  [[ "$output" == result=busy* ]]
  [ "$(calls 'agent prompt')" -eq 0 ]
}

@test "working の相手は待ってから送る" {
  printf 'working\nidle\nidle\n' > "$FAKE_STATE/status_seq"
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 0 ]
  [ "$(calls 'agent wait w1:p1')" -ge 1 ]
  [ "$(calls 'agent prompt')" -eq 1 ]
}

@test "agent_blocked で拒否されたら blocked" {
  set_state prompt_reply agent_blocked
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 3 ]
}

@test "stalled でも seq が動いていれば landed。本文は 1 回だけ送る" {
  set_state prompt_reply stalled
  set_state seq_after 2
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 0 ]
  [[ "$output" == *"via=seq"* ]]
  [ "$(calls 'agent prompt')" -eq 1 ]
}

@test "stalled のあと Claude 自身が busy なら landed" {
  set_state prompt_reply stalled
  set_state claude_agents.json '[{"kind":"interactive","sessionId":"sid-1","status":"idle"}]'
  set_state claude_agents_after '[{"kind":"interactive","sessionId":"sid-1","status":"busy"}]'
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 0 ]
  [[ "$output" == *"via=status"* ]]
}

@test "stalled でも transcript に本文があれば landed" {
  set_state prompt_reply stalled
  set_state claude_agents.json '[{"kind":"interactive","sessionId":"sid-1","status":"idle"}]'
  : > "$CLAUDE_CONFIG_DIR/projects/p/sid-1.jsonl"
  set_state transcript_file "$CLAUDE_CONFIG_DIR/projects/p/sid-1.jsonl"
  printf '{"type":"user","message":{"content":"run the \\"tests\\" now"}}\n' > "$FAKE_STATE/transcript_append"
  run "$SCRIPT" prompt w1:p1 --text 'run the "tests" now'
  [ "$status" -eq 0 ]
  [[ "$output" == *"via=transcript"* ]]
}

@test "入力欄に貼り付けが残れば typed。Enter は押さない" {
  set_state prompt_reply stalled
  set_state screen $'> [Pasted text #1 +12 lines]\n'
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 2 ]
  [[ "$output" == result=typed* ]]
  [ "$(calls 'send-keys')" -eq 0 ]
}

@test "slash command は turn を起こさないので accepted" {
  set_state prompt_reply stalled
  run "$SCRIPT" prompt w1:p1 --text "/effort high"
  [ "$status" -eq 0 ]
  [[ "$output" == *"result=accepted"*"via=command"* ]]
}

@test "証拠が無ければ no_evidence で失敗" {
  set_state prompt_reply timeout
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 2 ]
  [[ "$output" == result=no_evidence* ]]
}

@test "agent 名から pane ID に解決する" {
  run "$SCRIPT" prompt worker --text "hello"
  [ "$status" -eq 0 ]
  [[ "$output" == "result=landed pane=w1:p1 via=working" ]]
}

@test "表示名（tab の label）から pane ID に解決する" {
  set_state agents.json '{"result":{"agents":[]}}'
  set_state workspaces.json '{"result":{"workspaces":[{"workspace_id":"w9"}]}}'
  set_state tabs.json '{"result":{"tabs":[{"tab_id":"w9:t2","label":"AAP/release"}]}}'
  set_state panes.json '{"result":{"panes":[{"pane_id":"w9:p5","tab_id":"w9:t2"}]}}'
  run "$SCRIPT" prompt "AAP/release" --text "hello"
  [ "$status" -eq 0 ]
  [[ "$output" == *"pane=w9:p5"* ]]
}

@test "見つからない宛先は not_found" {
  set_state agents.json '{"result":{"agents":[]}}'
  run "$SCRIPT" prompt nobody --text "hello"
  [ "$status" -eq 2 ]
  [[ "$output" == result=not_found* ]]
}

@test "wait: Claude は settled 2 回で done" {
  set_state claude_agents.json '[{"kind":"interactive","sessionId":"sid-1","status":"idle"}]'
  run "$SCRIPT" wait w1:p1 --gap 0 --step 10
  [ "$status" -eq 0 ]
  [[ "$output" == *"result=done"*"settled=2"* ]]
}

@test "wait: idle と working が揺れる間は done にしない" {
  set_state kind codex
  printf 'idle\nworking\nidle\nidle\nidle\n' > "$FAKE_STATE/status_seq"
  run "$SCRIPT" wait w1:p1 --gap 0 --step 10
  [ "$status" -eq 0 ]
  [ "$(calls 'agent get')" -ge 5 ]
}

@test "wait: blocked は 3" {
  set_state status blocked
  run "$SCRIPT" wait w1:p1 --gap 0 --step 10
  [ "$status" -eq 3 ]
}

@test "wait: --done-if が偽のままなら timeout" {
  run "$SCRIPT" wait w1:p1 --gap 0 --step 10 --timeout 1500 --done-if false
  [ "$status" -eq 4 ]
  [[ "$output" == result=timeout* ]]
}

@test "wait: --done-if が真なら done" {
  touch "$BATS_TEST_TMPDIR/out.png"
  run "$SCRIPT" wait w1:p1 --gap 0 --step 10 --done-if "test -f $BATS_TEST_TMPDIR/out.png"
  [ "$status" -eq 0 ]
}

@test "preflight: 互換が無ければ 5" {
  set_state status.json '{"client":{"version":"0.9.3"},"server":{"running":true,"version":"0.9.3","compatible":false,"endpoint_compatible":false},"update":{}}'
  run "$SCRIPT" preflight
  [ "$status" -eq 5 ]
  [[ "$output" == *"result=incompatible"* ]]
}

@test "preflight: server が 0.9.0 より古ければ 5" {
  set_state status.json '{"client":{"version":"0.9.3"},"server":{"running":true,"version":"0.8.2","compatible":true,"endpoint_compatible":true},"update":{}}'
  run "$SCRIPT" preflight
  [ "$status" -eq 5 ]
  [[ "$output" == *"result=server_too_old"* ]]
}

@test "preflight: server が古いだけなら警告して ok" {
  set_state status.json '{"client":{"version":"0.9.3"},"server":{"running":true,"version":"0.9.1","compatible":true,"endpoint_compatible":true},"update":{"server_binary_stale":true}}'
  run "$SCRIPT" preflight
  [ "$status" -eq 0 ]
  [[ "$output" == *"warn=server_binary_stale server=0.9.1 client=0.9.3"* ]]
  [[ "$output" == *"result=ok"* ]]
}

@test "preflight: herdr skill のコピーが古ければ警告" {
  mkdir -p "$CLAUDE_CONFIG_DIR/skills/herdr"
  printf -- '---\nname: herdr\norigin: herdrdev/herdr\n---\nold body\n' > "$CLAUDE_CONFIG_DIR/skills/herdr/SKILL.md"
  set_state skill $'---\nname: herdr\n---\nnew body'
  run "$SCRIPT" preflight
  [ "$status" -eq 0 ]
  [[ "$output" == *"warn=skill_drift"* ]]
}

@test "preflight: コピーが同じなら警告しない" {
  mkdir -p "$CLAUDE_CONFIG_DIR/skills/herdr"
  printf -- '---\nname: herdr\norigin: herdrdev/herdr\n---\nbody\n' > "$CLAUDE_CONFIG_DIR/skills/herdr/SKILL.md"
  set_state skill $'---\nname: herdr\n---\nbody'
  run "$SCRIPT" preflight
  [ "$status" -eq 0 ]
  [[ "$output" != *"skill_drift"* ]]
}

@test "prompt は preflight の失敗で 5" {
  set_state status.json '{"client":{"version":"0.9.3"},"server":{"running":false},"update":{}}'
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 5 ]
  [ "$(calls 'agent prompt')" -eq 0 ]
}

@test "transcript に以前の同じ指示があっても、送信後の追記に無ければ no_evidence" {
  set_state prompt_reply stalled
  set_state claude_agents.json '[{"kind":"interactive","sessionId":"sid-1","status":"idle"}]'
  printf '{"type":"user","message":{"content":"Unattended triage cycle"}}\n' \
    > "$CLAUDE_CONFIG_DIR/projects/p/sid-1.jsonl"
  run "$SCRIPT" prompt w1:p1 --text "Unattended triage cycle"
  [ "$status" -eq 2 ]
  [[ "$output" == result=no_evidence* ]]
}

@test "turn を起こす slash command（user skill）は accepted にしない" {
  set_state prompt_reply stalled
  run "$SCRIPT" prompt w1:p1 --text "/grill-me 題材は X"
  [ "$status" -eq 2 ]
  [[ "$output" == result=no_evidence* ]]
}

@test "数値でない --timeout は usage で 64" {
  run "$SCRIPT" wait w1:p1 --timeout 'a[$(id)]'
  [ "$status" -eq 64 ]
}

@test "日本語の指示も transcript で確かめられる" {
  set_state prompt_reply stalled
  set_state claude_agents.json '[{"kind":"interactive","sessionId":"sid-1","status":"idle"}]'
  : > "$CLAUDE_CONFIG_DIR/projects/p/sid-1.jsonl"
  set_state transcript_file "$CLAUDE_CONFIG_DIR/projects/p/sid-1.jsonl"
  long='あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんあいうえおかきくけこさし'
  printf '{"type":"user","message":{"content":"%s"}}\n' "$long" > "$FAKE_STATE/transcript_append"
  LC_ALL=C run "$SCRIPT" prompt w1:p1 --text "$long"
  [ "$status" -eq 0 ]
  [[ "$output" == *"via=transcript"* ]]
}

@test "stalled のあと blocked に移ったら blocked（成功にしない）" {
  set_state prompt_reply stalled
  set_state seq_after 2
  set_state status_after blocked
  set_state kind codex
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 3 ]
}

@test "値の無い --text は usage で 64" {
  run "$SCRIPT" prompt w1:p1 --text
  [ "$status" -eq 64 ]
}

@test "--retry-unseen: transcript がまだ無い新しい session には 1 回だけ送り直す" {
  printf 'stalled\nok\n' > "$FAKE_STATE/prompt_reply_seq"
  set_state claude_agents.json '[{"kind":"interactive","sessionId":"sid-1","status":"idle"}]'
  AGENT_SEND_RETRY_WAIT_S=0 run "$SCRIPT" prompt w1:p1 --text "hello" --retry-unseen
  [ "$status" -eq 0 ]
  [[ "$output" == *"via=retry"* ]]
  [ "$(calls 'agent prompt')" -eq 2 ]
}

@test "--retry-unseen: transcript があれば送り直さない" {
  set_state prompt_reply stalled
  set_state claude_agents.json '[{"kind":"interactive","sessionId":"sid-1","status":"idle"}]'
  printf '{"type":"user","message":{"content":"earlier"}}\n' > "$CLAUDE_CONFIG_DIR/projects/p/sid-1.jsonl"
  AGENT_SEND_RETRY_WAIT_S=0 run "$SCRIPT" prompt w1:p1 --text "hello" --retry-unseen
  [ "$status" -eq 2 ]
  [ "$(calls 'agent prompt')" -eq 1 ]
}

@test "--retry-unseen が無ければ送り直さない" {
  set_state prompt_reply stalled
  run "$SCRIPT" prompt w1:p1 --text "hello"
  [ "$status" -eq 2 ]
  [ "$(calls 'agent prompt')" -eq 1 ]
}

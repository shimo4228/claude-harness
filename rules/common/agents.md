<!-- origin: shimo4228 -->
<!-- rationale: ADR-0015 + ADR-0035 — catalog 複製を避け、review 分離と Herdr skill の入口だけ常駐（境界は boundary.md、ADR-0069） -->
<!-- review-when: native agent catalog / cross-agent attach point / Herdr の運用を変えた時 -->
# Agent Orchestration

agent catalog の正本は `~/.claude/agents/*.md` の frontmatter。Review は実装者と別の
agent process で走らせる。必要な chain は skill: `implementation-chain` が持つ。

Claude Code 外との rules 共有は [ADR-0015](../../docs/adr/0015-cross-agent-rules-sharing-reference-first.md)。
Herdr の pane / agent の一般操作は skill: `herdr`、実装タスクの丸ごと委譲は skill: `herdr-delegate`
（vendor の `agent_status` / `--wait` の settled は着弾確認までに使い、完了の信号にしない — 正本は
herdr-delegate §3）、新規 session の作成は skill: `spawn-session`。委譲と pane 操作の境界は
`boundary.md`。

<!-- origin: shimo4228 -->
<!-- rationale: ADR-0015 + ADR-0035 — catalog 複製を避け、review と外部 agent の境界だけ常駐 -->
<!-- review-when: native agent catalog / cross-agent attach point / Herdr の運用を変えた時 -->
# Agent Orchestration

agent catalog の正本は `~/.claude/agents/*.md` の frontmatter。Review は実装者と別の
agent process で走らせる。必要な chain は skill: `implementation-chain` が持つ。

Claude Code 外との rules 共有は [ADR-0015](../../docs/adr/0015-cross-agent-rules-sharing-reference-first.md)。
Herdr 委譲は `HERDR_ENV=1` かつユーザーが明示的に求めた場合だけ skill: `herdr` を使う。
例外は create-only の skill: `spawn-session` — 新規 workspace/tab の作成と自分が作った pane
への操作しかせず既存 pane・focus に触れないため、server 稼働だけを前提に `HERDR_ENV` 外から
実行してよい（明示指示は依然必要。2026-07-21 決定）。

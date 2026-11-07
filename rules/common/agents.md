<!-- origin: shimo4228 -->
<!-- rationale: agent catalog は frontmatter が正本で、ここに複製すると drift する。常駐するのは review を実装者と別 process で走らせる規約と、Herdr / Codex への入口だけ（境界は boundary.md）。Herdr / agent-send / spawn-session / codex:rescue の入口は各 skill の description が持つ -->
<!-- history: docs/decision-history/0015, 0035, 0069 -->
<!-- review-when: native agent catalog / cross-agent attach point / Herdr の運用を変えた時 -->

# Agent Orchestration

agent catalog の正本は `~/.claude/agents/*.md` の frontmatter。Review は実装者と別の agent process で走らせ、
必要な chain は skill: `implementation-chain` が持つ。pane・session・Codex への委譲の境界は `boundary.md`。

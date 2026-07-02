<!-- origin: shimo4228 -->
# Agent Orchestration

## Agent Catalog

agent カタログの正本は `~/.claude/agents/*.md` の frontmatter (description が
「いつ使うか」を含む)。セッション中は harness が Available agent types として
全 agent の説明を自動提示するため、**ここに一覧の手書きコピーを置かない**
(同じ frontmatter から生成される native 一覧に対して drift するだけ —
akc-cycle.md Scaffold Dissolution の downward vector。2026-07-03 rules-stocktake
監査で表を撤去)。

## Immediate Agent Usage

各 agent をどの順序で起動するかは [`common/planning.md`](planning.md) の
**Implementation Chain Specification** で定義する Chain Matrix に従う。

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker

### Author-Reviewer Separation

Run reviews in a separate agent process from the implementer:
- Same context = author bias blind spots
- For strategic decisions, use a second model as peer reviewer


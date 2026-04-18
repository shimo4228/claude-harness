<!-- origin: shimo4228 -->
# Agent Orchestration

## Available Agents

Located in `~/.claude/agents/`:

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| planner | Implementation planning | Complex features, refactoring |
| architect | System design | Architectural decisions |
| tdd-guide | Test-driven development | New features, bug fixes |
| code-reviewer | Code review (汎用) | After writing non-Python code |
| python-reviewer | Python code review | After writing Python code |
| security-reviewer | Security analysis | Before commits |
| e2e-runner | E2E testing | Critical user flows |
| refactor-cleaner | Dead code cleanup | Code maintenance |
| scout | Pre-implementation solution discovery | New module/utility creation |
| prompt-writer | LLM prompt generation | Creating/rewriting prompts |
| doc-updater | Documentation | Updating docs |

## Immediate Agent Usage

No user prompt needed:
1. New module or non-trivial utility - Use **scout** agent (or inline search per coding-style rule)
2. Complex feature requests - Use **planner** agent
3. Code just written/modified - Use **code-reviewer** agent
4. Bug fix or new feature - Use **tdd-guide** agent
5. Architectural decision - Use **architect** agent

## Parallel Task Execution

ALWAYS use parallel Task execution for independent operations:

```markdown
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: Security analysis of auth module
2. Agent 2: Performance review of cache system
3. Agent 3: Type checking of utilities

# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```

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


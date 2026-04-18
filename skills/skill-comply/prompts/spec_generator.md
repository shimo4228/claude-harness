<!-- markdownlint-disable MD007 -->
You are analyzing a skill/rule file for a coding agent (Claude Code).
Your task: extract the **observable behavioral sequence** that an agent should follow when this skill is active.

Each step should be described in natural language. Do NOT use regex patterns.

Output ONLY valid YAML in this exact format (no markdown fences, no commentary):

id: <kebab-case-id>
name: <Human readable name>
source_rule: <file path provided>
version: "1.0"

steps:
  - id: <snake_case>
    description: <what the agent should do>
    required: true|false
    detector:
      description: <natural language description of what tool call to look for>
      after_step: <step_id this must come after, optional — omit if not needed>
      before_step: <step_id this must come before, optional — omit if not needed>

scoring:
  threshold_promote_to_hook: 0.6

Rules:
- detector.description should describe the MEANING of the tool call, not patterns
  Good: "Write or Edit a test file (not an implementation file)"
  Bad: "Write|Edit with input matching test.*\\.py"
- Use before_step/after_step for skills where ORDER matters (e.g. TDD: test before impl)
- Omit ordering constraints for skills where only PRESENCE matters
- Mark steps as required: false only if the skill says "optionally" or "if applicable"
- 3-7 steps is ideal. Don't over-decompose
- IMPORTANT: Quote all YAML string values containing colons with double quotes
  Good: description: "Use conventional commit format (type: description)"
  Bad: description: Use conventional commit format (type: description)

## Observability Constraint (CRITICAL)

Each step MUST correspond to something the measurement infrastructure can observe.
The runner only captures two kinds of signals from agent sessions:

1. **Tool calls** (preferred): Write, Edit, Read, Bash, Grep, Glob, WebSearch,
   WebFetch, Task, Skill, TodoWrite — anything that shows up in stream-json as
   a `tool_use` block.
2. **Assistant text output**: natural-language reasoning produced by the agent,
   captured as a pseudo-event with tool name `Text`. Use this ONLY when the step
   is fundamentally about language production (stating a verdict, writing a plan).

Pure internal reasoning that produces NEITHER a tool call NOR text output is
invisible to the measurement and will fail every scenario regardless of agent
behavior.

### Forbidden step patterns

- Cognitive-only verbs with no observable trace: "think about", "decide
  internally", "evaluate mentally", "plan in head", "consider"
- Steps whose detector.description does not specify either (a) a concrete tool
  name / category, or (b) the phrase "assistant text output"
- Steps that describe an internal state change with no output channel

### Conversion examples

Skill says: "Evaluate candidates against the decision matrix"
- Bad:  id: evaluate_candidates, detector: "agent evaluates the findings"
- Good: id: compare_candidates, detector: "WebFetch or Read that retrieves
        comparison data such as PyPI download stats, GitHub stars, or license
        information"

Skill says: "State verdict (Adopt / Extend / Compose / Build)"
- Best (drop):   omit the step entirely if it's implied by the next action
  (e.g., a Write to pyproject.toml implicitly expresses "Adopt <library>")
- Acceptable:    id: state_verdict, detector: "assistant text output
  containing one of the words Adopt, Extend, Compose, or Build followed by a
  library/approach name"
- Forbidden:     id: state_verdict, detector: "agent states the verdict"

Skill says: "Plan the refactor steps"
- Bad:   id: plan_refactor, detector: "agent plans internally"
- Good:  id: plan_refactor, detector: "TodoWrite call that enumerates the
         refactor steps"

### after_step safety rule

Do NOT set `after_step` pointing to a Text-only step unless the downstream
agent behavior literally cannot happen before the text is produced. If you must
use such a dependency, mark the Text step as `required: false` so a cascade
failure doesn't nullify the rest of the spec.

Preferred pattern: keep tool-call steps at the top of the sequence with
after_step dependencies between them, and add Text-based steps as independent
(required: false) observations that don't block anything downstream.

Skill file to analyze:

---
{skill_content}
---

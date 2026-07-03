---
name: knowledge-placement-decision
description: "Decision tree for choosing where to save new knowledge: memory, append to an existing skill, or a new skill"
user-invocable: false
origin: auto-extracted
---

# Knowledge Placement Decision

**Context:** When persisting the outcome of analysis or research, prevent skill sprawl and knowledge burial caused by choosing the wrong save location

## Problem

When you gain new knowledge, saving it to the wrong place causes two problems:
- **New-skill sprawl**: creating a file for every small insight breeds skills that are never discovered
- **Memory burial**: writing rules that should apply every time into memory keeps them out of the workflow

## Solution

### Decision tree

```
Gained new knowledge
  |
  +- Q1: Should it be referenced every time in future work?
  |   +- No -> save to memory/ (referenced only when needed)
  |   +- Yes ↓
  |
  +- Q2: Does it fit within the scope of an existing skill?
  |   +- Yes -> append to the existing skill (top priority)
  |   +- No ↓
  |
  +- Q3: Is it substantial enough for a standalone skill? (3+ rules, or includes a workflow)
      +- Yes -> create a new skill
      +- No -> record 1-2 lines in MEMORY.md
```

### Placement mapping

| Nature of the knowledge | Destination | Example |
|-----------|--------|-----|
| Analysis data, comparison tables, topic lists | memory/ | 9-category buzz-pattern taxonomy, 5 new article topics |
| Behavioral rules, checklists, workflows | skills/ (append to existing) | 7 title-design rules → a writing skill |
| Systematic methods for a new domain | skills/ (create new) | LLM-as-Judge evaluation framework |
| Small gotchas, one-sentence lessons | MEMORY.md | "Zenn slugs are immutable, so retitling is link-safe" |

## Anti-Patterns

- "It's important, so make it a skill" → creating a new file for an insight under 10 lines (MEMORY.md suffices)
- "Let's just batch it into memory" → behavioral rules get buried in reference context
- "I don't want to pollute the existing skill" → a skill's value lies in comprehensiveness; appending is an improvement

## When to Use

- When deciding the save location in /learn-eval
- When persisting analysis results
- When unsure: "should this be a skill, or is memory enough?"

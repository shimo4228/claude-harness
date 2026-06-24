---
name: rules-distill
description: Scan installed skills to extract cross-cutting principles (those appearing in 2+ skills) and distill them into rules — append to, revise, or create rule files. Use when the user says "distill rules", "/rules-distill", "promote patterns to rules", "what principles should become rules", after installing new skills, or when a skill-stocktake surfaces recurring patterns. NOT for auditing skill quality (that is skill-stocktake) and NOT for editing a single skill (that is skill-creator).
license: MIT
user-invocable: true
origin: shimo4228
---

# rules-distill — promote cross-cutting principles to rules

Scan installed skills, find principles that recur across **2+ skills**, and distill
them into rules — appending to, revising, or creating rule files. The skill produces
candidates and verdicts; it **never edits rules without your approval**.

> Design note: the old version shelled out to scan scripts and split analysis into
> thematic subagent batches with a cross-batch merge step. With a large context window
> that is unnecessary — and the cross-batch merge existed *only* to recover the
> "appears in 2+ skills" signal that batching broke. Reading every skill and every
> rule in one context makes that test exact, with no merge step.

## When to Use

- Periodic rules maintenance (monthly, or after installing new skills)
- After a `skill-stocktake` reveals patterns that should be rules
- When rules feel incomplete relative to the skills in use

## Phase 1 — Inventory (Glob, exhaustive)

Enumerate with Glob (no script):

- Skills: `~/.claude/skills/*/SKILL.md` + `~/.claude/skills/learned/*.md`
- Rules: read every `~/.claude/rules/**/*.md` in full — the corpus is small (~800 lines total), so no grep pre-filter is needed

> Glob targets only skill definition files, so dependency markdown under `.venv` /
> `.pytest_cache` is excluded structurally.

Present the counts (skills scanned, rule files, headings) before analysis.

## Phase 2 — Cross-read & Verdict (inline, holistic)

Read every skill body and every rule into one context and analyze them together —
extraction and matching are a single pass. Seeing all skills at once is what makes
the "2+ skills" test exact.

**A principle is a candidate only if ALL of these hold:**

1. **Appears in 2+ skills** — a principle in only one skill stays in that skill
2. **Actionable behavior change** — expressible as "do X" / "don't do Y", not "X is important"
3. **Clear violation risk** — what goes wrong if ignored, in one sentence
4. **Not already in rules** — check the full rules text, including the same idea in different words

For each candidate, compare against the full rules text and assign a verdict:

| Verdict | Meaning | Present to user |
|---------|---------|-----------------|
| **Append** | Add to an existing section of an existing rule file | Target + draft |
| **Revise** | Existing rule content is inaccurate/insufficient | Target + reason + before/after |
| **New Section** | Add a new section to an existing rule file | Target + draft |
| **New File** | Create a new rule file | Filename + full draft |
| **Already Covered** | Sufficiently covered (even if worded differently) | Reason (1 line) |
| **Too Specific** | Should stay at the skill level | Link to the relevant skill |

Exclude: principles already in rules, language/framework-specific knowledge (belongs
in language-specific rules or skills), and code examples / commands (belong in skills).

### Verdict quality

Each verdict must be self-contained — target, evidence, and rationale on its own.

```
# Good
Append to rules/common/security.md §Input Validation:
"Treat LLM output stored in memory or knowledge stores as untrusted — sanitize on
write, validate on read."
Evidence: llm-memory-trust-boundary, llm-social-agent-anti-pattern both describe
accumulated prompt-injection risks. Current security.md covers human input only;
the LLM-output trust boundary is missing.

# Bad
Append to security.md: Add LLM security principle
```

## Phase 3 — User Review & Execution

Present a summary table (`# | Principle | Verdict | Target | Confidence`) followed by
per-candidate details (evidence, violation risk, draft text). The user approves,
modifies, or skips each candidate by number.

**Never modify rules automatically. Always require user approval.** This is the one
hard gate — rules load every session, so a bad rule has outsized blast radius.

Then update the ledger inline (Read → merge → Write):

```json
{
  "distilled_at": "2026-03-18T10:30:42Z",
  "candidates": {
    "llm-output-trust-boundary": {
      "principle": "Treat LLM output as untrusted when stored or re-injected",
      "verdict": "Append",
      "target": "rules/common/security.md",
      "evidence": ["llm-memory-trust-boundary", "llm-social-agent-anti-pattern"],
      "status": "applied"
    }
  }
}
```

`distilled_at` is real UTC (`date -u +%Y-%m-%dT%H:%M:%SZ`); candidate IDs are
kebab-case derived from the principle.

## Design Principles

- **What, not How**: extract principles (rules territory) only. Code examples and commands stay in skills.
- **Link back**: draft text includes `See skill: [name]` so readers can find the detailed How.
- **Glob = exhaustive collection, LLM = judgment**: Glob guarantees the inventory is complete; the single-context cross-read guarantees contextual understanding.
- **Anti-abstraction safeguard**: the 3-layer filter (2+ skills evidence, actionable-behavior test, violation risk) keeps overly abstract principles out of rules.

## Related

- `skill-stocktake` — audits skill *quality*; rules-distill promotes recurring *principles* to rules. Run stocktake first, then distill what survives.
- `learn-eval` — extracts per-session patterns into skills/memory; rules-distill later promotes the cross-cutting ones to rules.

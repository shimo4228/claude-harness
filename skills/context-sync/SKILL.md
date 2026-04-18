---
name: context-sync
description: Audit and fix project documentation — detect role overlaps between context files (CLAUDE.md, CODEMAPS, ADR, README), migrate misplaced content, check freshness against code, and create missing docs. One command to keep all project context healthy.
origin: shimo4228
---

# Context Sync

Detect and fix documentation role overlaps, stale content, and missing context files across your project. Ensures every piece of project knowledge lives in exactly one place with a clear purpose.

## Why This Matters

In LLM-driven development, organizing concepts _is_ implementation. Markdown carries the same weight as executable code — a stale number in CLAUDE.md or a misplaced design rationale silently degrades every AI-assisted session that reads it. Context consistency is not housekeeping; it is a prerequisite for core concepts to reach the system without noise.

## When to Use

- After a major refactoring or architecture change
- When CLAUDE.md / .cursorrules has grown large and feels cluttered
- When you suspect docs are out of date with the code
- When starting a new project and want proper doc structure from the beginning
- When design decisions are buried in context files instead of formal records
- Periodically (monthly or per milestone) as documentation hygiene

## Core Concept: Four Documentation Roles

Every project document should serve exactly one of these four roles. Overlap causes drift and contradiction.

| Role | Purpose | What belongs here | Examples |
|------|---------|-------------------|---------|
| **Context** | How to work in this project | Conventions, build/test commands, policies | CLAUDE.md, .cursorrules, AGENTS.md |
| **Architecture** | What the code looks like now | Module structure, data flow, dependencies | docs/CODEMAPS/, docs/architecture/ |
| **Decisions** | Why the code is this way | Trade-offs, rejected alternatives, rationale | docs/adr/ |
| **External** | What this project is | Purpose, quickstart, API overview | README.md |

### Common Anti-Patterns

| Symptom | Problem | Fix |
|---------|---------|-----|
| CLAUDE.md is 500+ lines | Architecture detail in context file | Move structure/module lists to Architecture docs |
| CLAUDE.md has "we chose X because Y" | Decision record in context file | Extract to ADR |
| README explains internal implementation | Internal detail in external doc | Move to Architecture docs |
| Multiple files describe the same structure | Contradictory duplication | Single source of truth + pointers |
| No ADR directory | Decisions live nowhere or in context file | Create docs/adr/ and migrate |

## Workflow

Run all five phases in order. Present findings after each phase and wait for user confirmation before proceeding to the next.

### Phase 1: Discover

Scan the project for documentation files and classify them into the four roles.

**Detection targets:**

Context files:
- CLAUDE.md, .cursorrules, .windsurfrules
- AGENTS.md, .github/copilot-instructions.md

Architecture docs:
- docs/CODEMAPS/, docs/architecture/, docs/design/

Decision records:
- docs/adr/, docs/decisions/

External docs:
- README.md, README.*.md

Package metadata (for freshness comparison):
- package.json, pyproject.toml, Cargo.toml, go.mod, pom.xml

**Actions:**
1. List all detected files with their role classification
2. Identify missing roles and suggest whether to introduce them:
   - No Architecture docs → "Code structure details may be cluttering your context file"
   - No Decision records → "Design decisions may be buried in context files or lost entirely"
3. Present the classification table and wait for user confirmation

### Phase 2: Overlap Detection

Read each documentation file and detect content that belongs in a different role.

**Check for these patterns:**

```
Context file contains...          → Should move to...
─────────────────────────────────────────────────────
Module/file listings (>10 items)  → Architecture docs
Dependency graphs or data flows   → Architecture docs
"We chose X because Y"           → Decision record (ADR)
"Alternative was Z but..."        → Decision record (ADR)
Internal API details              → Architecture docs
─────────────────────────────────────────────────────

README contains...                → Should move to...
─────────────────────────────────────────────────────
Internal module structure         → Architecture docs
Implementation details            → Architecture docs
Design rationale                  → Decision record (ADR)
─────────────────────────────────────────────────────

Architecture docs contain...      → Should move to...
─────────────────────────────────────────────────────
"We decided to..."                → Decision record (ADR)
Build/test commands               → Context file
─────────────────────────────────────────────────────
```

Also check for contradictions between files (e.g., different module counts in context file vs architecture docs).

**Actions:**
1. List each overlap with: source file, line range, target role, reason
2. Wait for user to approve/reject each migration

### Phase 3: Create / Migrate

Execute the approved migrations from Phase 2.

**Creating new documentation:**

If ADR directory is needed:
1. Create `docs/adr/README.md` with index table and template
2. Extract decision content from context files into ADR format:

```markdown
# ADR-NNNN: [Title]

## Status
accepted

## Date
YYYY-MM-DD

## Context
[What problem prompted this decision]

## Decision
[What was decided]

## Alternatives Considered
[What else was considered and why it was rejected]

## Consequences
[What becomes easier/harder as a result]
```

If Architecture docs are needed:
1. Create the appropriate directory (docs/architecture/ or docs/CODEMAPS/)
2. Move structural content from context files

**For all migrations:**
- Replace moved content in the source file with a brief pointer (e.g., "See docs/adr/ for design decisions")
- Confirm each file write with the user before executing
- Update any index files (e.g., ADR README.md table)

### Phase 4: Freshness Check

Verify that documentation claims match the current codebase.

**Checks to run:**

```bash
# Directory structure matches documentation
find src/ -type f -name "*.py" | wc -l        # or *.ts, *.go, etc.
# Compare against documented module count

# Test count matches
pytest --collect-only -q 2>/dev/null | tail -1  # Python
npm test -- --listTests 2>/dev/null | wc -l     # JavaScript

# Package version matches docs
grep version pyproject.toml                      # or package.json
# Compare against version mentioned in README/context file

# Stale files (not updated in 90+ days)
git log -1 --format="%ci" -- <doc-file>
```

**Check items:**
- [ ] Directory tree in docs matches actual file structure
- [ ] Numeric claims (module count, LOC, test count) match reality
- [ ] CLI command examples actually work (`--help` verification)
- [ ] Package metadata (version, dependencies) matches documentation
- [ ] No documentation files untouched for 90+ days (flag as potentially stale)
- [ ] ADR index matches actual ADR files on disk

**Actions:**
1. Report each mismatch with current value vs documented value
2. Propose specific edits
3. Apply only after user confirmation

### Phase 5: Report

Summarize all actions taken across all phases.

```
Context Sync Report
═══════════════════

Roles:      4 roles, N files discovered
Created:    docs/adr/ (3 ADRs migrated from context file)
Moved:      2 sections (architecture detail → docs/CODEMAPS/)
Updated:    README.md version, context file module count
Stale:      1 file flagged (docs/architecture.md, 120 days)
Skipped:    N items (user declined)

Status: All documentation roles covered, no overlaps remaining.
```

## Best Practices

- **Run after major changes** — refactors, new features, dependency updates
- **Context file should be short** — if it exceeds ~200 lines, content is likely misplaced
- **One source of truth** — never duplicate information; use pointers instead
- **ADRs are cheap** — when in doubt, record the decision. Future you will thank present you
- **README is for outsiders** — if someone needs to understand the codebase internals to read it, the content belongs elsewhere

## What This Skill Does NOT Do

- Code quality checks (linting, testing, building) — use `verification-loop`
- Token/context window analysis — use `context-budget`
- Agent-specific memory management (e.g., auto-memory systems)

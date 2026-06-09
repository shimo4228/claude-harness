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
| **Architecture** | What the code looks like now (file-level) AND what concepts it defines (concept-level) | Module structure / data flow / dependencies (file-level prose); domain entities / relationships (concept-level triples) | docs/CODEMAPS/, docs/architecture/, graph.jsonld |
| **Decisions** | Why the code is this way | Trade-offs, rejected alternatives, rationale | docs/adr/ |
| **External** | What this project is | Purpose, quickstart, API overview | README.md |

**Architecture role には 2 surface が共存しうる**: prose（CODEMAPS — 「どのファイルに X が住むか」）と JSON-LD triples（graph.jsonld — 「X とは何か / X と Y はどう関係するか」）。両者は重複せず相補的。役割境界の詳細は `jsonld-knowledge-graph` skill が正本を持つ。

### Common Anti-Patterns

| Symptom | Problem | Fix |
|---------|---------|-----|
| CLAUDE.md is 500+ lines | Architecture detail in context file | Move structure/module lists to Architecture docs |
| CLAUDE.md has "we chose X because Y" | Decision record in context file | Extract to ADR |
| README explains internal implementation | Internal detail in external doc | Move to Architecture docs |
| Multiple files describe the same structure | Contradictory duplication | Single source of truth + pointers |
| No ADR directory | Decisions live nowhere or in context file | Create docs/adr/ and migrate |

## Workflow

Run all six phases in order. **Confirmation policy: ask the user only when creating a new file or a new directory.** Edits to existing files are applied automatically — git diff is the audit trail, and `git checkout -- <file>` is the undo. New file / directory creation is irreversible without `rm`, so it stays gated.

The skill runs end-to-end in one turn unless one of the gated decisions surfaces. Phase 5 (Report) summarizes what was done.

### Phase 0: Codemap Freshness Pre-check

Before any other detection, verify that `docs/CODEMAPS/` (if present) reflects the current source. Stale codemaps poison every downstream phase — Overlap detection (Phase 2) and Freshness checks (Phase 4) will compare against a fiction and propose wrong migrations.

**Why pre-check, not just check**: in the original 5-phase design, codemap freshness was inside Phase 4 — by then we'd already produced migration proposals based on the old codemap. Phase 0 catches the drift before any other phase runs.

**Three stale signals (OR — any single hit triggers an automatic cascade):**

| Signal | Detection | Threshold |
|---|---|---|
| A. Timestamp lag | `git log -1 --format=%ct -- docs/CODEMAPS/` vs source dirs' latest commit ctime | source newer by **≥ 7 days** |
| B. File count drift | `find <src>/ -type f -name '*.{ts,py,go,rs,swift}' \| wc -l` vs the `Files scanned: N` in the newest CODEMAPS freshness header | **±20%** delta |
| C. Missing CODEMAPS | `docs/CODEMAPS/INDEX.md` absent, or only `architecture.md` exists | immediate hit |

If `docs/CODEMAPS/` does not exist at all and the project is small (< 30 source files), skip Phase 0 silently — codemaps are optional, not mandatory.

**Actions:**

1. Compute all three signals and log the raw values for traceability:

   ```
   Phase 0 — Codemap Freshness
   Signal A (timestamp lag):  CODEMAPS 2026-04-30, src 2026-05-20 → 20 days, HIT
   Signal B (file count):     CODEMAPS Files: 142, current: 178 → +25%, HIT
   Signal C (missing):        all required files present, no hit
   ```

2. **If any signal hits AND `docs/CODEMAPS/` already exists** (edits to existing files): invoke the `codemap-writer` agent via the Task tool, passing repo root, source dirs, and existing CODEMAPS state. The agent regenerates the affected codemaps in place. **No confirmation prompt** — these are edits to existing files, covered by git diff.

3. **If Signal C hits and `docs/CODEMAPS/` does not exist** (new directory + new files): this is creation, so confirm once with the user:

   > Project has no `docs/CODEMAPS/` yet. Generate via codemap-writer? (Y/n)

   If yes, invoke codemap-writer; if no, mark as acknowledged drift and continue.

4. After cascade completes, re-evaluate the signals. If still hit (e.g., agent partially failed), surface the new state to the user before proceeding to Phase 1.

5. If no signal hits, log `Phase 0 — no drift detected` and continue silently.

`--skip-cascade`: bypass Phase 0 entirely (useful when codemaps are intentionally absent or being managed elsewhere).

### Phase 1: Discover

Scan the project for documentation files and classify them into the four roles.

**Detection targets:**

Context files:
- CLAUDE.md, .cursorrules, .windsurfrules
- AGENTS.md, .github/copilot-instructions.md

Architecture docs:
- docs/CODEMAPS/, docs/architecture/, docs/design/ (file-level prose)
- graph.jsonld (concept-level architecture, schema.org JSON-LD; sibling of CODEMAPS, not a replacement)

Decision records:
- docs/adr/, docs/decisions/

External docs (human-facing):
- README.md, README.*.md

AI-facing documents (repo root, AI navigator role — equally important to detect as README):
- llms.txt (compact AI navigator, ~5 KB, links + brief role labels)
- llms-full.txt (self-contained AI doc, ~20 KB, Q&A + definitions)

Treat the AI-facing set with the same rigor as README: it is the **AI-facing analogue of README**, not optional decoration. If a project has CODEMAPS or graph.jsonld but no llms.txt, flag it in Phase 5 as a missing role.

Package metadata (for freshness comparison):
- package.json, pyproject.toml, Cargo.toml, go.mod, pom.xml

**Actions:**
1. List all detected files with their role classification
2. Identify missing roles and surface them:
   - No Architecture docs → "Code structure details may be cluttering your context file"
   - No Decision records → "Design decisions may be buried in context files or lost entirely"
3. Display the classification table as info — **no confirmation prompt**. Phase 2 onward will act on this classification; if Phase 3 needs to create new directories (e.g., `docs/adr/`), that confirmation lives there.

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

graph.jsonld contains...           → Should move to...
─────────────────────────────────────────────────────
File path lists (>5 paths)         → CODEMAPS (file-level prose)
Build / install commands           → CLAUDE.md (Context)
Decision rationale                 → ADR (Decisions)
Version numbers / counts           → REMOVE (volatile state forbidden)
─────────────────────────────────────────────────────

CODEMAPS contains...               → Should also exist in graph.jsonld
─────────────────────────────────────────────────────
Named concepts with definitions    → graph.jsonld Concept node (drift if missing)
Inter-concept relationships        → graph.jsonld edges (drift if missing)
─────────────────────────────────────────────────────
```

Also check for contradictions between files (e.g., different module counts in context file vs architecture docs, or graph.jsonld Concept node whose `name` no longer matches CODEMAPS prose definition).

**Actions:**
1. List each overlap with: source file, line range, target role, reason
2. **Auto-apply migrations whose target is an existing file** (e.g., moving content from CLAUDE.md into existing docs/CODEMAPS/architecture.md). These are edits — git diff is the audit trail.
3. **Defer migrations whose target is a new file or new directory** to Phase 3, which will batch-confirm them. Examples: extracting a buried decision into a new ADR (creates `docs/adr/NNNN-*.md`), splitting architecture content into a new `docs/architecture/data.md` that doesn't exist yet.

### Phase 3: Create / Migrate

Execute the approved migrations from Phase 2.

**Creating new documentation:**

If ADR records need to be created (either a missing `docs/adr/` directory, or buried decisions found in CLAUDE.md / README that should be extracted into ADR form):

Delegate to the `adr-writer` skill. Do not inline an ADR template here — duplicating the template invites drift between context-sync's version and the canonical adr-writer version. Instead:

1. For each decision to extract, gather the 6 inputs (Title / Status / Context / Decision / Alternatives / Consequences) from the source file
2. Invoke `/adr-writer` once per decision with those inputs
3. `adr-writer` handles: directory creation, sequence numbering, README index update, body generation via the adr-writer agent
4. If the user runs context-sync in non-interactive mode where invoking another skill is impractical, surface the list of decisions to extract and ask the user to run `/adr-writer` for each later — do not write partial ADRs from context-sync directly

If Architecture docs are needed:
1. Create the appropriate directory (docs/architecture/ or docs/CODEMAPS/)
2. Move structural content from context files

**For all migrations:**
- Replace moved content in the source file with a brief pointer (e.g., "See docs/adr/ for design decisions") — this is an edit, no confirmation
- **Batch-confirm new file / new directory creation once at the start of Phase 3** (single Y/n covering all creations identified by Phase 2). If the user says no to a specific creation, skip that migration but keep the others.
- Update any index files (e.g., ADR README.md table) — these are edits, no confirmation

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

If `graph.jsonld` exists in the repo, also check:
- [ ] `ResearchLine` `@id` uses concept DOI (parent record), not latest versioned DOI
- [ ] `EcosystemRepo` URLs resolve (not 404; `curl -sI <url> | head -1`)
- [ ] Each `Concept` node has corresponding mention in CODEMAPS prose (bidirectional reference)
- [ ] `grep -E '"version"|"versionNumber"|"adrCount"|"testCount"|v[0-9]+\.[0-9]+' graph.jsonld` returns empty (no volatile state)
- [ ] `python3 -m json.tool < graph.jsonld > /dev/null` succeeds (valid JSON)

If `llms.txt` or `llms-full.txt` exists at repo root, also check:
- [ ] No content duplication with README — both must serve distinct audiences. Quick test: take the first 5 H2 sections from each and compare topics. If > 60% overlap, the llms.txt is just a README copy and should be regenerated AI-first via `llms-txt-writer`
- [ ] Links in `llms.txt` resolve to actual files (`grep -oE '\([^)]+\.md\)' llms.txt` then verify each path exists)
- [ ] `llms-full.txt` is **self-contained** — should not link out to other docs as the primary content source; quoting + summarizing is fine, linking-only is not
- [ ] If CODEMAPS was regenerated more recently than `llms.txt` (compare freshness header dates), flag for `/llms-txt-writer` regeneration — the AI-facing nav may now point at stale prose

**Actions:**
1. Report each mismatch with current value vs documented value
2. **Apply edits to existing files automatically** — these are corrections to drift, covered by git diff
3. If a freshness fix requires creating a new file (rare — e.g., a missing README.md the project should have), batch that into the Phase 3 creation confirmation block instead

### Phase 5: Report

Summarize all actions taken across all phases.

```
Context Sync Report
═══════════════════

Phase 0:    Codemap freshness — 2 signals hit, user ran /update-codemaps before continuing
Roles:      4 roles, N files discovered (incl. llms.txt, llms-full.txt at repo root)
Created:    3 ADRs via /adr-writer (extracted from CLAUDE.md decisions)
Moved:      2 sections (architecture detail → docs/CODEMAPS/)
Updated:    README.md version, context file module count
Stale:      1 file flagged (docs/architecture.md, 120 days)
AI-facing:  llms.txt nav-links resolve, no README duplication detected
Skipped:    N items (user declined)

Status: All documentation roles covered (Context / Architecture / Decisions / External / AI-facing), no overlaps remaining.
```

If Phase 0 ended with **acknowledged drift** (user declined to cascade update-codemaps), call that out explicitly in the report header:

```
⚠ Phase 0 drift acknowledged — downstream judgments may reference stale codemaps.
  Recommend running /update-codemaps then re-running /context-sync.
```

## Best Practices

- **Run after major changes** — refactors, new features, dependency updates
- **Context file should be short** — if it exceeds ~200 lines, content is likely misplaced
- **One source of truth** — never duplicate information; use pointers instead
- **ADRs are cheap** — when in doubt, record the decision. Future you will thank present you
- **README is for outsiders** — if someone needs to understand the codebase internals to read it, the content belongs elsewhere

## What This Skill Does NOT Do

- Code quality checks (linting, testing, building) — use `verify`
- Token/context window analysis — use `context-budget`
- Agent-specific memory management (e.g., auto-memory systems)
- `graph.jsonld` schema design / vocabulary extension — use `jsonld-knowledge-graph`

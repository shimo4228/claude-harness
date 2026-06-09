---
name: adr-writer
description: Record a design decision as an Architecture Decision Record (ADR) in the project's `docs/adr/` directory. Use this skill whenever the user says "let's ADR this", "record this decision", "write an ADR for X", or when context-sync Phase 3 needs to extract a buried decision. The skill resolves the target ADR directory from cwd, picks the next sequence number with no collision, delegates 6-section body generation to the adr-writer agent, and updates the ADR index. Works across any repo — auto-detects or creates `docs/adr/` from the repo root.
user-invocable: true
origin: shimo4228
---

# ADR Writer

Capture a design decision as a numbered ADR with consistent structure. The skill handles the boilerplate (directory detection, sequence numbering, index update); the `adr-writer` agent handles the prose.

## Why a Skill + Agent Split

The skill owns deterministic concerns: where the ADR goes, what number it gets, which index needs updating. These are easy to get wrong silently (number collisions, sub-directory cwd confusion, index drift) so they live in scripted steps, not prose generation.

The agent owns subjective concerns: how to phrase Context, how to label Alternatives, whether Consequences are positive or negative. These benefit from LLM judgment, but the input must already be specific enough — the agent refuses to invent.

## When to Use

- The user says "let's ADR this", "record this decision", "write an ADR for X"
- `context-sync` Phase 3 has extracted a decision from CLAUDE.md / README that needs ADR form
- The user is about to merge a PR with an irreversible architectural change and wants a record
- A debate concluded in chat and the user wants the outcome durable

## When NOT to Use

- Bug fix records (use the commit message)
- Reversible refactors (commit message is enough)
- Personal preferences ("I like spaces over tabs") — those go in a style guide, not an ADR

## Workflow

### Step 1: Resolve the ADR directory

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || REPO_ROOT="$(pwd)"
ADR_DIR="$REPO_ROOT/docs/adr"
```

If `$ADR_DIR` does not exist, ask the user once:

> The repo has no `docs/adr/` directory. Create one with a README index template before writing the ADR? (Y/n)

If yes, create `$ADR_DIR` and write a minimal `README.md` index:

```markdown
# Architecture Decision Records

| ID | Title | Status | Date |
|---|---|---|---|

## Template

ADRs in this repository use the 6-section template:
Status / Date / Context / Decision / Alternatives Considered / Consequences.

File name: `NNNN-kebab-case-title.md` (zero-padded 4-digit sequence).
```

If the user declines, stop and explain that ADRs need a directory.

### Step 2: Pick the next sequence number

```bash
LAST_NUM=$(ls "$ADR_DIR"/[0-9]*-*.md 2>/dev/null | sort -V | tail -1 | sed -E 's|.*/([0-9]+)-.*|\1|')
if [ -z "$LAST_NUM" ]; then
  NEXT_NUM="0001"
else
  NEXT_NUM=$(printf "%04d" $((10#$LAST_NUM + 1)))
fi
```

Verify uniqueness right before writing (race safety):

```bash
[ -e "$ADR_DIR/$NEXT_NUM-"*.md ] && echo "COLLISION" || echo "OK"
```

If `COLLISION`, recompute `NEXT_NUM` from the latest state.

### Step 3: Gather the 6 inputs

Ask the user (or accept from caller) for:

1. **Title** — short, kebab-case-friendly (e.g., `context-sync-cascade-and-writer-agents`). The skill will compose the filename.
2. **Status** — `proposed | accepted | superseded | deprecated`. Default `accepted`.
3. **Context** — what problem prompted this decision (raw text OK).
4. **Decision** — what was decided (raw text OK).
5. **Alternatives** — what else was considered and why rejected (raw text or list).
6. **Consequences** — what becomes easier / harder (raw text or list).

If 3-6 are missing, request them — do not proceed. ADRs without these sections are noise.

### Step 4: Delegate body generation to the adr-writer agent

Invoke the `adr-writer` agent via the Task tool with:

- ADR number (`$NEXT_NUM`)
- Repo root (`$REPO_ROOT`)
- ADR directory (`$ADR_DIR`)
- Title (kebab-case slug)
- Status / Date / Context / Decision / Alternatives / Consequences

The agent will:
- Read the 2 most recent ADRs in `$ADR_DIR` for style calibration
- Fill the 6 sections from your input (no invention)
- Write the file at `$ADR_DIR/$NEXT_NUM-<title>.md`
- Return a summary block

If the agent returns "needs more input", surface the missing-fields message to the user and stop. Do not push partial ADRs.

### Step 5: Update the index

After the agent confirms file written, append a row to `$ADR_DIR/README.md` index table:

```bash
# Read current index
# Find the table block (lines between "| ID |" header and the next "##" heading)
# Append: | $NEXT_NUM | <title human-readable> | <status> | <date> |
```

If the index table is malformed or absent, regenerate it from the directory:

```bash
for f in "$ADR_DIR"/[0-9]*-*.md; do
  num=$(basename "$f" | sed -E 's|([0-9]+)-.*|\1|')
  title=$(head -1 "$f" | sed -E 's|^# ADR-[0-9]+: ||')
  status=$(awk '/^## Status/{getline; getline; print; exit}' "$f")
  date=$(awk '/^## Date/{getline; getline; print; exit}' "$f")
  echo "| $num | $title | $status | $date |"
done
```

### Step 6: Report

Tell the user:

```
ADR written
---
File:    docs/adr/<NNNN>-<title>.md
Number:  <NNNN>
Status:  <status>
Index:   updated (+1 row)
```

## Edge cases

| Case | Handling |
|---|---|
| Called from a sub-directory of the repo | Use `git rev-parse --show-toplevel`; never trust raw cwd |
| Not a git repo | Fall back to cwd, warn the user that they should `git init` |
| ADR number was reserved verbally but not yet written ("I'll write ADR-0010 later") | Skill cannot know; ask the user whether to take the next free number or the reserved one |
| User wants to supersede an existing ADR | Update the old ADR's Status to `superseded by ADR-NNNN`, then create the new one. Two file writes. |
| Title contains spaces or non-ASCII | Skill normalizes to kebab-case ASCII for the filename; preserves original in the `# ADR-NNNN: ...` heading |

## Boundaries

- **Do not** invent missing sections. Refuse to write an ADR with `Context: [TBD]` or similar placeholders.
- **Do not** modify ADRs other than the new one and (optionally) the index. If a supersede chain needs an old ADR updated, do it in a separate explicit step.
- **Do not** infer the user's decision from chat history without confirming. Ask, even if the answer feels obvious.
- **Do not** commit the file. The user owns the commit step.

## Reference Files

- ADR template canonical source: read the target repo's existing ADRs to mirror their voice. For the harness itself, see `~/.claude/docs/adr/README.md`.
- Agent that fills the body: `~/.claude/agents/adr-writer.md`.
- Evals: `evals/evals.json` (3 scenarios — new ADR / missing docs-adr / sequence collision).

---
name: search-first
description: "Research before writing code for any new feature, integration, library selection, or utility — search npm / PyPI / MCP / GitHub / existing skills for solutions instead of building from scratch. Use whenever the user says 'add X functionality', 'implement Y', 'set up Z', 'integrate W', asks 'what library should I use for...', 'is there a package/client/MCP for...', proposes a specific tool while open to alternatives, or invokes the planning.md Phase 0 External Research step. Especially use when the task adds a dependency, picks between tools, or builds a utility (parser, checker, converter, linter, CI step, E2E framework, payment / auth / API client) that likely already exists. DO NOT use for: bug fixes in existing code, refactoring, config value edits, file summarization, or throwaway one-shot scripts where the approach is already fully specified by the user."
user-invocable: true
origin: shimo4228
---

# /search-first — Research Before You Code

Systematizes the "search for existing solutions before implementing" workflow.

## Trigger

Use this skill when:
- Starting a new feature that likely has existing solutions
- Adding a dependency or integration
- The user asks "add X functionality" and you're about to write code
- Before creating a new utility, helper, or abstraction

## Workflow

```
┌─────────────────────────────────────────────┐
│  1. NEED ANALYSIS                           │
│     Define what functionality is needed      │
│     Identify language/framework constraints  │
├─────────────────────────────────────────────┤
│  2. PARALLEL SEARCH (scout agent)      │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│     │  npm /   │ │  MCP /   │ │  GitHub / │  │
│     │  PyPI    │ │  Skills  │ │  Web      │  │
│     └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────┤
│  3. EVALUATE                                │
│     Holistic assessment: functionality,     │
│     maintenance, community, docs, license   │
├─────────────────────────────────────────────┤
│  4. DECIDE                                  │
│     ┌─────────┐  ┌──────────┐  ┌─────────┐  │
│     │  Adopt  │  │  Extend  │  │  Build   │  │
│     │ as-is   │  │  /Wrap   │  │  Custom  │  │
│     └─────────┘  └──────────┘  └─────────┘  │
├─────────────────────────────────────────────┤
│  5. IMPLEMENT                               │
│     Install package / Configure MCP /       │
│     Write minimal custom code               │
└─────────────────────────────────────────────┘
```

## Decision Matrix

| Signal | Action |
|--------|--------|
| Exact match, well-maintained, MIT/Apache | **Adopt** — install and use directly |
| Partial match, good foundation | **Extend** — install + write thin wrapper |
| Multiple weak matches | **Compose** — combine 2-3 small packages |
| Nothing suitable found | **Build** — write custom, but informed by research |

## How to Use

### Quick Mode (inline)

#### Step 0: Articulate the requirement (mandatory, text output)

Before any tool call or subagent invocation, output 2-3 sentences that state:
- **What functionality is needed** (concretely, not just "X support")
- **Language / framework** the implementation will use
- **Project-specific constraints** if any (existing deps, performance limits, license requirements)

Why: this externalizes the search query so the user can redirect early, and makes the record auditable. Don't think it silently — write it. If you skip this step the user can't tell whether you searched the wrong thing.

**Format requirement**: the articulation must be **user-visible assistant text**, NOT embedded in subsequent tool arguments (Skill / Agent / Task / Bash). A scout / skill invocation whose `args` contains the requirement description does NOT satisfy Step 0 — the user reads chat text, not tool args. Emit the articulation as plain text first, then invoke tools whose args can mirror the same content if needed.

#### Step 1: Run the search checklist

0. Does this already exist in the repo? → `rg` through relevant modules/tests first
1. Is this a common problem? → Search npm/PyPI
2. Is there an MCP for this? → Check `~/.claude/settings.json` and search
3. Is there a skill for this? → Check `~/.claude/skills/`
4. Is there a GitHub implementation/template? → Run GitHub code search for maintained OSS before writing net-new code

### Full Mode (agent)

For non-trivial functionality, **first complete Step 0 above (articulate the requirement as text)**, then launch the scout agent — the agent's prompt should mirror the articulation, not replace it:

```
Agent(subagent_type="general-purpose", prompt="
  Research existing tools for: [DESCRIPTION]
  Language/framework: [LANG]
  Constraints: [ANY]

  Search: npm/PyPI, MCP servers, Claude Code skills, GitHub
  Return: Structured comparison with recommendation
")
```

## Search Shortcuts by Category

### Content & Publishing
- Markdown processing → `remark`, `unified`, `markdown-it`
- Cross-posting → Check platform APIs (Qiita, Dev.to, Medium)
- Image optimization → `sharp`, `imagemin`
- SEO → Platform-specific guidelines

### Development Tooling
- Linting → `eslint`, `ruff`, `textlint`, `markdownlint`
- Formatting → `prettier`, `black`, `gofmt`
- Testing → `jest`, `pytest`, `go test`
- Pre-commit → `husky`, `lint-staged`, `pre-commit`

### AI/LLM Integration
- Claude SDK → Context7 for latest docs
- Prompt management → Check MCP servers
- Document processing → `unstructured`, `pdfplumber`, `mammoth`

### Data & APIs
- HTTP clients → `httpx` (Python), `ky`/`got` (Node)
- Validation → `zod` (TS), `pydantic` (Python)
- Database → Check for MCP servers first

## Integration Points

### With planner agent
The planner should invoke scout before Phase 1 (Architecture Review):
- Scout identifies available tools
- Planner incorporates them into the implementation plan
- Avoids "reinventing the wheel" in the plan

### With architect agent
The architect should consult scout for:
- Technology stack decisions
- Integration pattern discovery
- Existing reference architectures

### With iterative-retrieval skill
Combine for progressive discovery:
- Cycle 1: Broad search (npm, PyPI, MCP)
- Cycle 2: Evaluate top candidates in detail
- Cycle 3: Test compatibility with project constraints

## Examples

### Example 1: "Add dead link checking"
```
Need: Check markdown files for broken links
Search: npm "markdown dead link checker"
Found: textlint-rule-no-dead-link — active maintenance, MIT, covers all link types
Verdict: ADOPT — npm install textlint-rule-no-dead-link
Result: Zero custom code, battle-tested solution
```

### Example 2: "Add Qiita cross-posting"
```
Need: Convert Zenn markdown to Qiita format and publish
Search: npm "zenn qiita", PyPI "qiita api"
Found: No complete solution — partial wrappers exist but unmaintained
Verdict: BUILD — but informed by Qiita API docs (via Context7)
Result: Minimal custom publish.py, using httpx + frontmatter packages
```

### Example 3: "Add terminology consistency"
```
Need: Enforce consistent technical terms in Japanese articles
Search: npm "proofreading", textlint rules
Found: textlint-rule-prh — dictionary-based checker, needs custom YAML config
Verdict: EXTEND — install prh, write custom dictionary (prh.yml)
Result: 1 package + 1 config file, no custom code
```

## When the user says "skip research"

If the user prompt explicitly tells you to skip research ("just implement", "no time for research", "use whatever"), you still output one short paragraph before implementing:

> "Implementing directly as requested. I haven't checked if there's an existing library for X — let me know if you want a 60-second scan first. Going with [your tentative choice] because [1-line reason]."

Why: the user might not know an existing library exists. Silent skip removes their chance to course-correct. This single paragraph preserves their intent (you don't research) while making the tradeoff visible.

Do NOT use this as an excuse to do full research anyway. The articulation is the only step; if the user replies "go ahead", proceed without searching.

## Anti-Patterns

- **Jumping to code**: Writing a utility without checking if one exists
- **Ignoring MCP**: Not checking if an MCP server already provides the capability
- **Over-customizing**: Wrapping a library so heavily it loses its benefits
- **Dependency bloat**: Installing a massive package for one small feature

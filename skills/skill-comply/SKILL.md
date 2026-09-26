---
name: skill-comply
description: "Visualize whether skills, rules, and agent definitions are actually followed — auto-generates scenarios at 3 prompt strictness levels, runs agents, classifies behavioral sequences, and reports compliance rates with full tool call timelines. Use when a rule's or skill's real adherence is in question or right after adding one — \"is this rule actually being followed?\", \"measure how often this skill fires\", \"/skill-comply\". NOT for — static quality stocktakes (→ skill-stocktake / rules-stocktake), reference-integrity checks (→ skill-health), with/without ablation (→ skill-creator §5)."
compatibility: Requires Python 3.11+ and uv. Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
origin: shimo4228
user-invocable: true
---

# skill-comply: Automated Compliance Measurement

Measures whether coding agents actually follow skills, rules, or agent definitions by:
1. Auto-generating expected behavioral sequences (specs) from any .md file
2. Auto-generating scenarios with decreasing prompt strictness (supportive → neutral → competing)
3. Running `claude -p` and capturing tool call traces via stream-json
4. Classifying tool calls against spec steps using LLM (not regex)
5. Checking temporal ordering deterministically
6. Generating self-contained reports with spec, prompts, and timelines

## Supported Targets

- **Skills** (`skills/*/SKILL.md`): Workflow skills like search-first, TDD guides
- **Rules** (`rules/common/*.md`): Mandatory rules like testing.md, security.md, debugging.md
- **Agent definitions** (`agents/*.md`): Whether an agent gets invoked when expected (internal workflow verification not yet supported)

## When to Activate

- User runs `/skill-comply <path>`
- User asks "is this rule actually being followed?"
- After adding new rules/skills, to verify agent compliance
- Periodically as part of quality maintenance

## Usage

```bash
# Full run
uv run --frozen --project ~/.claude/skills/skill-comply python -m scripts.run ~/.claude/rules/common/testing.md

# Dry run (no cost, spec + scenarios only)
uv run --frozen --project ~/.claude/skills/skill-comply python -m scripts.run --dry-run ~/.claude/skills/search-first/SKILL.md

# Custom models
uv run --frozen --project ~/.claude/skills/skill-comply python -m scripts.run --gen-model haiku --model sonnet --classifier-model sonnet <path>

# Back to serial (when you hit rate limits)
uv run --frozen --project ~/.claude/skills/skill-comply python -m scripts.run --concurrency 1 <path>

# Only for specs that need Bash (off by default — read "Trust boundary" below first)
uv run --frozen --project ~/.claude/skills/skill-comply python -m scripts.run --allow-bash <path>

# Reuse a saved spec to compare across runs (skips LLM regeneration)
uv run --frozen --project ~/.claude/skills/skill-comply python -m scripts.run --spec results/<skill-name>.spec.yaml <path>
```

**Pinning the spec and comparing across runs**: the spec is the "exam paper". Each LLM
generation changes both the number of required steps and the ordering constraints, so the
generated spec is automatically saved to `results/<skill-name>.spec.yaml`
(not gitignored — it can be version-controlled). When re-measuring the same skill, load it
with `--spec` to pin the questions so scores become comparable. The next generating run
overwrites the file of the same name, so copy any spec you want to keep as a baseline under another name.
Note that scenario prompts are still LLM-generated and vary on every run — pinning for run-to-run
comparison stops at the spec; scenario non-determinism is currently out of scope.

## Run time and reading progress

The three scenarios are independent of each other (separate prompts, separate sandboxes, separate processes),
so by default all three run at once. Wall time is **the slowest single scenario**, not the sum of the three.
Classification (grading) is also per scenario, so it runs alongside them. The two stages spec generation → scenario
generation stay serial because the later stage consumes the earlier stage's output.

Parallelism does not change scores or reports. Completion order is used only for progress display;
the report is always assembled in supportive → neutral → competing order.
`--concurrency 1` returns to fully serial execution.

**Progress goes to stderr, results go to stdout.** This is a division of labor, not an accident,
based on measurements taken 2026-08-01 (→ [ADR-0029](../../docs/adr/0029-skill-comply-parallel-scenarios-and-stderr-progress.md)):

```bash
# Progress is visible. Only stdout goes into tail; stderr reaches the terminal directly
uv run --frozen --project ~/.claude/skills/skill-comply python -m scripts.run <path> | tail -40

# Also keep progress in the log
uv run --frozen --project ~/.claude/skills/skill-comply python -m scripts.run <path> 2>&1 | tee run.log
```

**With `2>&1 | tail -40` you see nothing at all.** Without `-f`, `tail` is a tool that prints
"the last N lines", so it cannot emit a single line until its input ends.
This is a property of `tail`, so neither `python -u` nor flushing fixes it.
To watch intermediate progress, use `tee` instead of `tail`.

When even one scenario fails (e.g. the child process exits abnormally),
that scenario is not counted as 0% but reported to stderr as a "measurement failure", and the exit code is 1.
Reports for the remaining scenarios are saved as usual.

## Target kinds and what can be measured

Where the target lives determines whether the child can see it. **If you measure while it is invisible,
you are measuring not skill compliance but "the bare behavior of an agent that does not have the skill".**

| Target | Visible to the child? | Measurement |
|---|---|---|
| global skill (`~/.claude/skills/`) | Visible | Measurable as is |
| project skill (repo's `.claude/skills/`) | **Not visible** | Placed in the sandbox before measuring (the two tiers below) |
| rule / agent definition / plain .md | Not a skill | No `Skill` call is expected |

Project skills are measured in two tiers. **Which tier was used always appears in the report's Summary** —
75% at Tier 1 and 75% at Tier 2 are different things, so they must not be confusable.

- **Tier 1 (default, no flag)** — only the frontmatter `name` and `description` are real;
  the body is a harmless stub. **Measures "did the agent reach for the skill".**
  Discovery and invocation are decided by `name` / `description` and the body plays no part, so this suffices
- **Tier 2 (`--load-target-skill`)** — places the real body. **Measures "does it follow the procedure".**
  The audited body becomes **instructions** to an unattended child, so it is opt-in. Only the single `SKILL.md`
  file is copied, not the directory (a skill with `references/` is measured short at Tier 2 —
  a visible limitation is preferred over a silent hole)

**Tier 1 is a layer for measurement correctness, not a containment layer.** Its reason to exist is
"make project skills discoverable so that compliance, not bare behavior, can be measured".

`description` is required for discovery, so it always reaches the child. The 500-character cap is **a cap on length,
not a cap on capability** — 500 characters is more than enough for an instruction, and it can carry effective
commands to a child that has Read / Write / Edit / Glob / Grep. The difference between Tier 1 and Tier 2
is **"the procedure does not arrive"**, not **"instructions do not arrive"**.

Combining `--load-target-skill` with `--allow-bash` hands **an untrusted document both a payload
and an interpreter**, so it emits a warning.

## Trust boundary — the audited file is untrusted

**This tool reads a .md you did not necessarily write, has an LLM write scenarios from it,
and has another agent execute them.** The audited file becomes the generator's input as is, so
the target file's body is treated as untrusted data (2026-07-25 security scan F2/F3/F4/F18).

- **`setup_commands` are not executed.** Only the two verbs `mkdir` / `touch` are interpreted via pathlib,
  and paths are verified to resolve inside the sandbox. Anything else is rejected and reported to stderr
- **Path validation collapses `..` before resolving symlinks.** The sandbox is deleted and recreated
  just beforehand, so the first component never exists, and a `..` placed after a nonexistent component
  (`a/../../elsewhere/x`) stays unresolved. `Path.parents` treats it as just a
  directory name, so checking before collapsing lets creation outside the sandbox through
- **The child's tools are removed with `permissions.deny`. `--allowedTools` does not remove them.**
  As `claude --help` says, `--allowedTools` is "a list of tool names to allow" = an auto-approve
  list, and tools not on it **do not disappear**. Measured on 2026-08-02 with Claude Code 2.1.220:
  a child with only `--allowedTools "Read,Glob,Grep"` called Bash, and `uname -sr` ran
  on the host. Neither `--permission-mode` (manual / dontAsk / acceptEdits)
  nor `--setting-sources project` changes this.
  `permissions.deny` in `--settings` removes `Bash` / `Agent` / `Workflow` /
  `ToolSearch` / `ScheduleWakeup` (source of truth: `scripts/child_settings.py`).
  Tools beyond Bash are removed because `Agent` and `Workflow` spawn **subagents whose tool sets
  this code does not control**, and `ToolSearch` loads on demand the MCP surface inherited from user settings
  (mail, drive, calendar, browser).
  `--allow-bash` works by **removing** Bash from the deny list
- `cwd` and `--add-dir` **widen** access; they do not confine it
- **Generator prompts isolate the target document with nonce delimiters** and state explicitly that it is
  data, not instructions. A fixed delimiter (`---`) can be reproduced by markdown frontmatter
- **One sandbox per scenario, and one root per run.** Directory names derive from the LLM-generated
  scenario id, so duplicates are detected and renamed before execution. Serially, duplicates are
  harmless, but in parallel one scenario's sandbox creation (delete before create) wipes the other one mid-run.
  This deduplication **only works within a process**, so roots are separated per run —
  `/tmp/skill-comply-sandbox/run-<pid>/<id>`. Separate runs that generated the same id
  do not delete each other's in-flight sandboxes (`scripts/runner.py: sandbox_run_root`).
  When `SANDBOX_BASE` itself is a symlink (shared host, CI scratch area), it is resolved and followed
  once when computing the root — the containment check is not redone across the link every time
- **`<sandbox>/.claude/` and `<sandbox>/.git/` are reserved for the tool. Specifications originating from the audited file are not accepted.**
  The sandbox is the child's **project root**, and there some file names are
  loaded rather than "just sitting there" — even in an untrusted workspace,
  `hooks.SessionStart` in `<sandbox>/.claude/settings.json` **silently runs commands
  on the host**, and `<sandbox>/CLAUDE.md` is also read and obeyed.
  The substrate stops the child's own Writes, but **this tool's pathlib writes are not stopped**, so
  they are blocked here. `CLAUDE.md` / `AGENTS.md` / `.mcp.json` / `settings.json` /
  `settings.local.json` / `.gitignore` are rejected at any depth.
  **The check is case-folded** — APFS is case-insensitive, so `.CLAUDE/Settings.json`, if it
  could be written, would be read as `.claude/settings.json`.
  `.git/` is included because `_setup_sandbox` runs `git init` first so it is writable, and
  `core.fsmonitor` / `core.pager` / `alias.*` are **config strings git executes without an execute bit**
  (measured: placing `.git/config` via `files:` made `git status` run a command on the host.
  Claude Code runs git in the workspace, so this fires even with the child's Bash blocked).
  `.gitignore` is not execution but **sabotage of measurement** — Grep honors it and Glob does not, so a document
  can hide its own fixtures from the tool the detector expects.
  **Being contained and being inert are different properties**, and `_contained` answers only the former

When measuring an untrusted .md, read the generated scenarios first with `--dry-run`.
In addition to the spec steps, `--dry-run` **prints in full the three fields an attacker may control** —
`prompt`, which is handed to the unattended child, and `setup_commands` and `files:`, which touch the filesystem.

## Models

| Stage | Default | Why |
|-------|---------|-----|
| `--gen-model` | `haiku` | Spec / scenario generation. Short prompts, fast. |
| `--model` | `sonnet` | Scenario execution (the agent under test). Accepts `haiku` / `sonnet` / `opus` / `fable`. |
| `--classifier-model` | `sonnet` | Trace classification. Haiku times out on long traces (50+ events) and abstract specs (e.g. contemplative-axioms). Sonnet handles the load with a 300s timeout. |

## Key Concept: Prompt Independence

Measures whether a skill/rule is followed even when the prompt doesn't explicitly support it.

## Report Contents

Reports are self-contained and include:
1. Expected behavioral sequence (auto-generated spec)
2. Scenario prompts (what was asked at each strictness level)
3. Compliance scores per scenario
4. Tool call timelines with LLM classification labels

### Advanced (optional)

For users familiar with hooks, reports also include hook promotion recommendations for steps with low compliance. This is informational — the main value is the compliance visibility itself.

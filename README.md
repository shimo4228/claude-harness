Language: English | [日本語](README.ja.md)

# claude-harness

Public snapshot of the Claude Code harness (skills / agents / rules) that shimo4228 uses day-to-day.

A mechanical aggregation of assets tagged `origin: shimo4228` from `~/.claude/`. ECC-derived material (`origin: ECC` / `ECC-customized`) and auto-extracted artifacts (`origin: auto-extracted`) are excluded.

## Positioning

- **Audience**: Claude Code (CLI + IDE extensions) users, and developers researching agent skill / rule ecosystems
- **Source of truth**: `~/.claude/` is canonical; this repo is an artifact synced manually. If sync frequency grows, a collection script will automate it
- **License**: MIT. Free to copy, modify, and redistribute. Forking and customizing for personal use is encouraged

## Contents

### Skills

| Skill | Purpose |
|-------|---------|
| [search-first](skills/search-first/SKILL.md) | Research-before-coding workflow. Invokes the scout agent to discover existing tools |
| [learn-eval](skills/learn-eval/SKILL.md) | Extracts reusable patterns from sessions, evaluates quality, and decides where to save |
| [skill-stocktake](skills/skill-stocktake/SKILL.md) | Skill quality audit. Quick Scan / Full Stocktake modes with parallel evaluation |
| [rules-distill](skills/rules-distill/SKILL.md) | Extracts cross-cutting principles from skills and promotes them to rules |
| [skill-comply](skills/skill-comply/SKILL.md) | Measures actual compliance of skills / rules / agents. Classifies behavioral sequences across 3 prompt strictness levels |
| [context-sync](skills/context-sync/SKILL.md) | Audits and fixes project documentation. Detects role overlap, checks freshness, creates missing docs |
| [llms-txt-writer](skills/llms-txt-writer/SKILL.md) | Writes AI-facing docs (llms.txt / llms-full.txt). Answer.AI standard + GEO/AEO static analysis |
| [jsonld-knowledge-graph](skills/jsonld-knowledge-graph/SKILL.md) | Designs and ships a companion JSON-LD knowledge graph (graph.jsonld) next to llms.txt. Encodes domain entities and relationships as schema.org triples for LLM citation |
| [writing-ecosystem](skills/writing-ecosystem/SKILL.md) | Orchestrator for human-facing writing & review. Coordinates editor / essay-reviewer / fact-checker |
| [write-prompt](skills/write-prompt/SKILL.md) | Generates concise prompts via the Haiku-powered prompt-writer agent |
| [collect-context](skills/collect-context/SKILL.md) | Gathers in-session and external context into source material for article writing |
| [authorship-strategy](skills/authorship-strategy/SKILL.md) | 4-layer framework (Authenticity / Attribution diffusion / Idea-vs-scaffold / Tactics) for DOI-registered idea-rescue research repos |
| [release-doi](skills/release-doi/SKILL.md) | Cuts a versioned release of a DOI-registered research repo (Zenodo concept DOI semantics, CHANGELOG / tag / asset packaging) |

> The first six (search-first, learn-eval, skill-stocktake, rules-distill, skill-comply, context-sync) are components of the [Agent Knowledge Cycle (AKC)](https://zenodo.org/records/19200727). Each is also published as its own standalone repo, but they are bundled here so the harness can be read end-to-end.

### Agents

| Agent | Purpose |
|-------|---------|
| [scout](agents/scout.md) | Pre-implementation solution discovery. Searches npm / PyPI / MCP registries / GitHub for existing solutions |
| [prompt-writer](agents/prompt-writer.md) | Generates concise prompts using a lightweight model. Creates and rewrites LLM prompt templates |
| [editor](agents/editor.md) | Strict technical article editor. Rigorously reviews code accuracy, AI slop, narrative flow, and terminology consistency |
| [essay-reviewer](agents/essay-reviewer.md) | Strict essay editor. Targets idea pieces mixing social theory / organizational analysis / design philosophy / personal narrative |
| [fact-checker](agents/fact-checker.md) | Fact verification specialist. Extracts verifiable claims from articles and verifies them via web sources |

### Rules

Behavioral principles auto-loaded every session (under `rules/common/`):

| Rule | Purpose |
|------|---------|
| [agents](rules/common/agents.md) | Agent orchestration conventions. When to use which agent, parallel execution patterns |
| [akc-cycle](rules/common/akc-cycle.md) | Six-phase behavioral conventions of the Agent Knowledge Cycle (Research / Extract / Curate / Promote / Measure / Maintain) |
| [authorship-strategy](rules/common/authorship-strategy.md) | Pointer rule activating the 4-layer authorship-strategy framework when working in DOI-registered idea-rescue research repos |
| [planning](rules/common/planning.md) | Required items for planning (What / Why / Alternatives). Mandates Phase 0 external research |
| [skills](rules/common/skills.md) | Skill origin tracking spec and knowledge placement principles |
| [contemplative-axioms](rules/common/contemplative-axioms.md) | Contemplative Constitutional AI clauses from Laukkonen et al. (2025), verbatim |

## Usage

### Full install

```bash
git clone https://github.com/shimo4228/claude-harness.git ~/.claude-harness
# Copy skills / agents / rules into ~/.claude/
cp -r ~/.claude-harness/skills/* ~/.claude/skills/
cp -r ~/.claude-harness/agents/* ~/.claude/agents/
cp -r ~/.claude-harness/rules/common/* ~/.claude/rules/common/
```

### Cherry-pick

Copy only what you want:

```bash
cp -r ~/.claude-harness/skills/search-first ~/.claude/skills/
```

### Setup for skills with Python implementations

`llms-txt-writer`, `skill-comply`, `rules-distill`, and `skill-stocktake` ship with Python code. In each skill directory:

```bash
cd ~/.claude/skills/<skill-name>
uv sync  # or: pip install -e .
```

## Origin tags

Each file's frontmatter (YAML or HTML comment) carries an `origin` field:

| origin | Meaning |
|--------|---------|
| `shimo4228` | Authored by shimo4228. The scope of this repo |
| `ECC` | From Everything Claude Code. Not included here |
| `ECC-customized` | ECC derivative + shimo4228 modifications. Not included |
| `auto-extracted` | Learned skill auto-extracted by `learn-eval`. Not included |

This repo is the result of a mechanical collection limited to `origin: shimo4228`.

## Related repos

- [shimo4228](https://github.com/shimo4228/shimo4228) — Hub repo aggregating the three research lines (AKC / Contemplative Agent / AAP) and the supporting ecosystem
- [agent-knowledge-cycle](https://github.com/shimo4228/agent-knowledge-cycle) — AKC concept and DOI release (Zenodo: 10.5281/zenodo.19200726)
- [contemplative-agent-rules](https://github.com/shimo4228/contemplative-agent-rules) — Rule implementation of Contemplative Constitutional AI
- `claude-skill-*` standalone repos — Individual versions of each AKC skill (search-first / learn-eval / skill-stocktake / rules-distill / skill-comply / context-sync) plus the adjacent skills (llms-txt-writer / daily-research / jsonld-knowledge-graph / writing-ecosystem)

## Contributing

This repo is shimo4228's personal harness artifact, so external PRs are not accepted. Instead:
- Fork it and customize freely
- Issues for questions or suggestions are welcome

Bug fixes flow upstream into `~/.claude/` when shimo4228 incorporates them.

## License

MIT License. See [LICENSE](LICENSE).

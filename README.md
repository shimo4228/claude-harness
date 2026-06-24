Language: English | [日本語](README.ja.md)

# claude-harness

Public snapshot of the Claude Code harness (skills / agents / rules) that shimo4228 uses day-to-day.

A mechanical aggregation of assets tagged `origin: shimo4228` from `~/.claude/`. ECC-derived material (`origin: ECC` / `ECC-customized`) and auto-extracted artifacts (`origin: auto-extracted`) are excluded.

## Positioning

- **Audience**: Claude Code (CLI + IDE extensions) users, and developers researching agent skill / rule ecosystems
- **Source of truth**: `~/.claude/` is canonical; this repo is a one-way export produced by [`scripts/sync-from-local.sh`](scripts/sync-from-local.sh) (origin filter → secret scan → subtree replacement)
- **License**: MIT. Free to copy, modify, and redistribute. Forking and customizing for personal use is encouraged

## Contents

### Skills

| Skill | Purpose |
|-------|---------|
| [search-first](skills/search-first/SKILL.md) | Research-before-coding workflow. Invokes the scout agent to discover existing tools |
| [signal-first-research](skills/signal-first-research/SKILL.md) | Design guide for a research intake filter that admits only information likely to change your next action |
| [learn-eval](skills/learn-eval/SKILL.md) | Extracts reusable patterns from sessions, evaluates quality, and decides where to save |
| [skill-stocktake](skills/skill-stocktake/SKILL.md) | Skill quality audit — inline Glob inventory + single-context holistic evaluation, Keep/Improve/Update/Retire/Merge verdicts |
| [rules-distill](skills/rules-distill/SKILL.md) | Extracts cross-cutting principles from skills and promotes them to rules |
| [skill-comply](skills/skill-comply/SKILL.md) | Measures actual compliance of skills / rules / agents. Classifies behavioral sequences across 3 prompt strictness levels |
| [context-sync](skills/context-sync/SKILL.md) | Audits and fixes project documentation. Detects role overlap, checks freshness, creates missing docs |
| [llms-txt-writer](skills/llms-txt-writer/SKILL.md) | Writes AI-facing docs (llms.txt / llms-full.txt). Answer.AI standard + GEO/AEO static analysis |
| [jsonld-knowledge-graph](skills/jsonld-knowledge-graph/SKILL.md) | Designs and ships a companion JSON-LD knowledge graph (graph.jsonld) next to llms.txt. Encodes domain entities and relationships as schema.org triples for LLM citation |
| [writing-ecosystem](skills/writing-ecosystem/SKILL.md) | Orchestrator for human-facing writing & review. Coordinates editor / essay-reviewer / fact-checker |
| [write-prompt](skills/write-prompt/SKILL.md) | Generates concise prompts via the lightweight prompt-writer agent |
| [collect-context](skills/collect-context/SKILL.md) | Gathers in-session and external context into source material for article writing |
| [authorship-strategy](skills/authorship-strategy/SKILL.md) | 4-layer framework (Authenticity / Attribution diffusion / Idea-vs-scaffold / Tactics) for DOI-registered idea-rescue research repos |
| [release-doi](skills/release-doi/SKILL.md) | Cuts a versioned release of a DOI-registered research repo (Zenodo concept DOI semantics, CHANGELOG / tag / asset packaging) |
| [adr-writer](skills/adr-writer/SKILL.md) | Records design decisions as numbered ADRs — directory detection, sequence numbering, index update; prose delegated to the adr-writer agent |
| [paper-ecosystem](skills/paper-ecosystem/SKILL.md) | Orchestrator for academic paper writing & review — role boundaries for paper-writing plus five reviewer agents; holds Source Fidelity / Vocabulary / Voice / Clarity / Citation rules |
| [paper-writing](skills/paper-writing/SKILL.md) | Drafting procedure for academic papers — title, outline, section drafting, abstract, references with claim-cite 1:1 mapping |
| [paper-deposit](skills/paper-deposit/SKILL.md) | Deposits a finished, reviewed paper to Zenodo as a standalone DOI record, optionally cross-posts to SSRN, cross-links the DOI back into the research repo |
| [readme-writer](skills/readme-writer/SKILL.md) | Writes human-facing READMEs — deterministic structural lint plus holistic LLM review (no scores) |
| [ja-to-en-translation](skills/ja-to-en-translation/SKILL.md) | Voice-preserving JA→EN translation for essays, research docs, and READMEs — term-lock, 2-pass, back-translation QA |
| [substack-publishing](skills/substack-publishing/SKILL.md) | Publishes reviewed essays to Substack and mirrors them to a corpus repo for LLM discovery |
| [hf-sync](skills/hf-sync/SKILL.md) | Mirrors graph.jsonld-bearing research repos to Hugging Face Datasets |
| [wikidata-federation](skills/wikidata-federation/SKILL.md) | Creates Wikidata items for researchers / papers / repos and cross-links QIDs with ORCID, DOI, and graph.jsonld |
| [citation-sync](skills/citation-sync/SKILL.md) | Audits the four citation layers of a research repo (docs / .zenodo.json / graph.jsonld / Wikidata P2860) and syncs them bottom-up |
| [when-code-when-llm](skills/when-code-when-llm/SKILL.md) | Decision framework for deterministic code vs LLM processing — structural-vs-semantic axis, false-positive test |
| [spawn-session](skills/spawn-session/SKILL.md) | Launches a new detached Claude Code Remote Control session via tmux, visible in the mobile app session list |
| [harness-sync](skills/harness-sync/SKILL.md) | One-way export of origin-filtered components from the live harness into this repo — collection, secret scan, subtree replacement |
| [cited-source-mirror-verification](skills/cited-source-mirror-verification/SKILL.md) | Verify an access-blocked or digest-sourced numeric claim against an open mirror before citing it in a durable artifact |
| [gap-review](skills/gap-review/SKILL.md) | Generate ranked next-move candidates for a strategy you operate over time — diff deployed tactics against catalog, open questions, and latest literature |
| [wiki-query](skills/wiki-query/SKILL.md) | Read-only query over an Obsidian LLM wiki (wiki/concept/) with `[[ ]]` source-cited synthesis |

> The first six (search-first, learn-eval, skill-stocktake, rules-distill, skill-comply, context-sync) are components of the [Agent Knowledge Cycle (AKC)](https://zenodo.org/records/19200727). Each is also published as its own standalone repo, but they are bundled here so the harness can be read end-to-end.

### Agents

| Agent | Purpose |
|-------|---------|
| [scout](agents/scout.md) | Pre-implementation solution discovery. Searches npm / PyPI / MCP registries / GitHub for existing solutions |
| [prompt-writer](agents/prompt-writer.md) | Generates concise prompts using a lightweight model. Creates and rewrites LLM prompt templates |
| [editor](agents/editor.md) | Strict technical article editor. Rigorously reviews code accuracy, AI slop, narrative flow, and terminology consistency |
| [essay-reviewer](agents/essay-reviewer.md) | Strict essay editor. Targets idea pieces mixing social theory / organizational analysis / design philosophy / personal narrative |
| [fact-checker](agents/fact-checker.md) | Fact verification specialist. Extracts verifiable claims from articles and verifies them via web sources |
| [adr-writer](agents/adr-writer.md) | Generates the 6-section ADR body from supplied input only — never invents context or alternatives |
| [codemap-writer](agents/codemap-writer.md) | Generates / refreshes `docs/CODEMAPS/` — token-lean architecture documentation, ~1000 tokens per map |
| [paper-reviewer](agents/paper-reviewer.md) | Academic paper structure review — argument flow, section transitions, claim sharpness, evidence-claim alignment |
| [source-fidelity-checker](agents/source-fidelity-checker.md) | Reads each cited primary source directly and flags drift between paper claims and source content |
| [vocabulary-consistency-checker](agents/vocabulary-consistency-checker.md) | Verifies term definitions stay consistent and sub-classifications are explicit at introduction |
| [clarity-reviewer](agents/clarity-reviewer.md) | First-contact reader clarity review — coined-term budget, title-axis alignment, meta-commentary, insider-context dependency |
| [citation-formatter](agents/citation-formatter.md) | Verifies in-text citations against the reference list — format consistency, DOI / arXiv ID validity |

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

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

<!-- BEGIN GENERATED: skills-table -->
| Skill | Purpose |
| --- | --- |
| [search-first](skills/search-first/SKILL.md) | Research-before-coding workflow. Invokes the scout agent to discover existing tools |
| [learn-eval](skills/learn-eval/SKILL.md) | Extracts reusable patterns from sessions, evaluates quality, and decides where to save |
| [skill-stocktake](skills/skill-stocktake/SKILL.md) | Skill quality audit — inline Glob inventory + single-context holistic evaluation, Keep/Improve/Update/Retire/Merge verdicts |
| [skill-health](skills/skill-health/SKILL.md) | Structural skill-library debt scan — flags "missing artifacts" (SKILL.md references to scripts / agents / sibling skills that don't resolve on disk). Deterministic; delegates quality / risk / validation to skill-stocktake / security-scan / skill-comply |
| [rules-distill](skills/rules-distill/SKILL.md) | Extracts cross-cutting principles from skills and promotes them to rules |
| [rules-stocktake](skills/rules-stocktake/SKILL.md) | Rules quality audit — residency-cost model (every line is a per-session token tax), staleness / substrate-absorption checks, Keep/Improve/Update/Merge/Demote/Dissolve/Retire verdicts. The inverse of rules-distill |
| [skill-comply](skills/skill-comply/SKILL.md) | Measures actual compliance of skills / rules / agents. Classifies behavioral sequences across 3 prompt strictness levels |
| [context-sync](skills/context-sync/SKILL.md) | Audits and fixes project documentation. Detects role overlap, checks freshness, creates missing docs |
| [codex-review](skills/codex-review/SKILL.md) | Cross-model code review — a read-only second opinion from the OpenAI Codex CLI (a different model family) on the current diff, folded into the Claude Code review chain alongside code-reviewer / security-reviewer |
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
| [ai-native-preprint-submission](skills/ai-native-preprint-submission/SKILL.md) | Submits a deposited paper to AI-native preprint platforms (aiXiv / AiraXiv) — Web UI browser automation with human gates, or author-delegated API/MCP submission |
| [readme-writer](skills/readme-writer/SKILL.md) | Writes human-facing READMEs — deterministic structural lint plus holistic LLM review (no scores) |
| [ja-to-en-translation](skills/ja-to-en-translation/SKILL.md) | Voice-preserving JA→EN translation for essays, research docs, and READMEs — term-lock, 2-pass, back-translation QA |
| [substack-publishing](skills/substack-publishing/SKILL.md) | Publishes reviewed essays to Substack and mirrors them to a corpus repo for LLM discovery |
| [hf-sync](skills/hf-sync/SKILL.md) | Mirrors graph.jsonld-bearing research repos to Hugging Face Datasets |
| [citation-sync](skills/citation-sync/SKILL.md) | Audits the three citation layers of a research repo (docs / .zenodo.json / graph.jsonld) and syncs them bottom-up |
| [spawn-session](skills/spawn-session/SKILL.md) | Launches a new detached Claude Code Remote Control session in a Herdr pane, visible in the mobile app session list |
| [harness-sync](skills/harness-sync/SKILL.md) | One-way export of origin-filtered components from the live harness into this repo — collection, secret scan, subtree replacement |
| [cited-source-mirror-verification](skills/cited-source-mirror-verification/SKILL.md) | Verify an access-blocked or digest-sourced numeric claim against an open mirror before citing it in a durable artifact |
| [wiki-harvest](skills/wiki-harvest/SKILL.md) | Read-only harvest from an Obsidian LLM wiki (wiki/concept/) into a research repo — extracts only next-action-changing candidates into a ranked, source-cited ledger under the repo's `.notes/` |
| [wiki-query](skills/wiki-query/SKILL.md) | Read-only query over an Obsidian LLM wiki (wiki/concept/) with `[[ ]]` source-cited synthesis |
| [repo-asset-stocktake](skills/repo-asset-stocktake/SKILL.md) | Audits a project repo's non-code assets (tool configs, CI workflows, runbooks) for diminished value — flags assets whose consumer has vanished, with Keep/Update/Retire/Merge verdicts |
| [task-stocktake](skills/task-stocktake/SKILL.md) | Audits and consolidates a repo's pending-task tracking into its single task ledger — bootstraps the ledger, sweeps stray task lines, verifies entries against git log and actual code |
| [en-to-ja-translation](skills/en-to-ja-translation/SKILL.md) | 英語→日本語の voice 保持翻訳スキル。エッセイ・研究ドキュメント・README・ADR 等の人間向け prose を、著者の声・register・発見調を保ったまま自然な日本語にする。逐語訳でも MT でもなく、term-lock（訳す-by-default／英語保持は明示 |
| [llm-as-judge](skills/llm-as-judge/SKILL.md) | Design pattern for LLM-as-judge evaluators — binary checks as evidence, one named holistic verdict, no score aggregation |
| [implementation-chain](skills/implementation-chain/SKILL.md) | Decides the task type (feat / fix / refactor / chore / prototype / writing) and front-loads its agent chain into the plan — Chain Matrix, reviewer routing, early-stop conditions |
| [public-comment](skills/public-comment/SKILL.md) | Replies in public technical threads (GitHub discussions / issues / PRs, HF discussions) — AI-slop tell removal, thread grounding, and a human gate with a Japanese translation before posting |
| [agent-stocktake](skills/agent-stocktake/SKILL.md) | Audit subagent definitions with a hybrid cost model (description = per-session residency, body = invocation) — flags suppression instructions and substrate absorption; third sibling of skill-/rules-stocktake |
| [generation-audit](skills/generation-audit/SKILL.md) | On a model-generation change, capture the live runtime layer (system prompt + tool descriptions), classify mismatches as conflict / redundancy / drift, and hand the evidence to the stocktake skills for verdicts |
| [git-workflow](skills/git-workflow/SKILL.md) | Permission-friction discipline for git in this environment — one Bash call per git command; chaining with && or pipes breaks the Bash(git:*) auto-allow and stalls on manual prompts |
| [headline-craft](skills/headline-craft/SKILL.md) | Craft skill for the one line that makes readers open — title / tagline / subtitle / SNS-post candidates, generated with concrete techniques and scored per traffic channel (search vs feed) |
| [herdr-delegate](skills/herdr-delegate/SKILL.md) | Hand a whole implementation task to a different CLI agent running in a Herdr pane (Codex, etc.). Gated on an explicit user request — parallelism alone is not a reason |
| [prompt-perturb](skills/prompt-perturb/SKILL.md) | Diversity injection. A deliberately context-starved forager agent fetches prompts from external creativity-technique catalogs, so the angles come from outside the session's own habits |
| [session-judgment-mining](skills/session-judgment-mining/SKILL.md) | Mine past session transcripts for judgements the user made repeatedly, and promote the recurring ones into skills or rules |
| [verify-bootstrap](skills/verify-bootstrap/SKILL.md) | Stand up a repo's machine gates (format / lint / type check / security / dependency / test), or take stock of gates that have gone stale. Tool choice is researched at bootstrap time rather than baked into the skill |
<!-- END GENERATED: skills-table -->

> The first six (search-first, learn-eval, skill-stocktake, rules-distill, skill-comply, context-sync) are components of the [Agent Knowledge Cycle (AKC)](https://doi.org/10.5281/zenodo.19200726). Each is also published as its own standalone repo, but they are bundled here so the harness can be read end-to-end.

### Agents

<!-- BEGIN GENERATED: agents-table -->
| Agent | Purpose |
| --- | --- |
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
| [readme-reviewer](agents/readme-reviewer.md) | Strict README / repo top-page review — LLM-read floor, lead clarity, human hook, scannability, length discipline, visual effectiveness. Companion to readme-writer |
| [readme-clarity-reviewer](agents/readme-clarity-reviewer.md) | First-contact reader clarity review for READMEs — coined-term budget, insider-context dependency, Japanese register (ですます). Parallel partner of readme-reviewer |
| [adr-reviewer](agents/adr-reviewer.md) | Checks an ADR's record, not its decision — whether Context carries verifiable evidence, Alternatives are real rather than straw men, Consequences show both sides, and override relations with prior ADRs are stated |
| [prompt-forager](agents/prompt-forager.md) | The context-starved half of prompt-perturb. Receives one line of purpose and deliberately nothing else, so what it finds is not shaped by the session that asked |
| [swift-reviewer](agents/swift-reviewer.md) | Swift / SwiftUI review — Swift 6 strict concurrency, value semantics, SwiftUI state ownership, retain cycles, HIG compliance |
<!-- END GENERATED: agents-table -->

### Rules

Behavioral principles auto-loaded every session (under `rules/common/`):

<!-- BEGIN GENERATED: rules-table -->
| Rule | Purpose |
| --- | --- |
| [agents](rules/common/agents.md) | Agent orchestration conventions. When to use which agent, parallel execution patterns |
| [akc-cycle](rules/common/akc-cycle.md) | Six-phase behavioral conventions of the Agent Knowledge Cycle (Research / Extract / Curate / Promote / Measure / Maintain) |
| [debugging](rules/common/debugging.md) | Root-cause-first debugging flow (hypothesis → evidence → confirm → fix), AI recency-bias guards, retry-with-context |
| [planning](rules/common/planning.md) | Required items for planning (What / Why / Alternatives). Mandates Phase 0 external research |
| [skills](rules/common/skills.md) | Skill origin tracking spec and knowledge placement principles |
| [contemplative-axioms](rules/common/contemplative-axioms.md) | Contemplative Constitutional AI clauses from Laukkonen et al. (2025), verbatim |
| [task-tracking](rules/common/task-tracking.md) | Single task ledger per repo — one canonical pending-task file, Done-section history, pointer-only discipline for MEMORY.md and detail documents |
<!-- END GENERATED: rules-table -->

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

`llms-txt-writer`, `skill-comply`, `rules-distill`, `skill-stocktake`, and `skill-health` ship with Python code. In each skill directory:

```bash
cd ~/.claude/skills/<skill-name>
uv sync  # or: pip install -e .
```

## Origin tags

Each file's frontmatter (YAML or HTML comment) carries an `origin` field:

| origin | Meaning |
|--------|---------|
| `shimo4228` | Authored by shimo4228. The scope of this repo |
| `ECC` | From Everything Claude Code. Content not included — named below |
| `ECC-customized` | ECC derivative + shimo4228 modifications. Content not included — named below |
| `auto-extracted` | Learned skill auto-extracted by `learn-eval`. Not included |

This repo is the result of a mechanical collection limited to `origin: shimo4228`.

<!-- BEGIN GENERATED: upstream-components -->
### Upstream components (names only)

The live harness also runs components from external upstreams. Their content — including any local modifications to it — is **not redistributed** here; the names alone are listed so the full composition stays visible. ECC = [Everything Claude Code](https://github.com/affaan-m/everything-claude-code).

| Upstream | Skills | Agents | Rules |
|---|---|---|---|
| ECC (unmodified) | article-writing | — | — |
| ECC + local modifications | agent-harness-construction, ai-regression-testing, config-gc, council, e2e, iterative-retrieval, product-lens, python-patterns, python-review, refactor-clean, tdd, update-codemaps | architect, code-reviewer, e2e-runner, python-reviewer, refactor-cleaner, security-reviewer | common/coding-style, common/security, common/testing |
| [anthropics/skills](https://github.com/anthropics/skills) (unmodified) | mcp-builder | — | — |
| [anthropics/skills](https://github.com/anthropics/skills) + local modifications | skill-creator | — | — |
| community + local modifications | scientific-thinking-literature-review | — | — |
| [mattpocock/skills](https://github.com/mattpocock/skills) + local modifications | grill-me | — | — |
| [modem-dev/hunk](https://github.com/modem-dev/hunk) | hunk-review | — | — |
| [ogulcancelik/herdr](https://github.com/ogulcancelik/herdr) | herdr | — | — |
| oh-my-agent-check + local modifications | agent-architecture-audit | — | — |
<!-- END GENERATED: upstream-components -->

## Related repos

- [shimo4228](https://github.com/shimo4228/shimo4228) — Hub repo aggregating the three research lines (AKC / Contemplative Agent / AAP) and the supporting ecosystem
- [agent-knowledge-cycle](https://github.com/shimo4228/agent-knowledge-cycle) — AKC concept and DOI release (Zenodo: 10.5281/zenodo.19200726)
- [contemplative-agent-rules](https://github.com/shimo4228/contemplative-agent-rules) — Rule implementation of Contemplative Constitutional AI
- `claude-skill-*` standalone repos — Individual versions of each AKC skill (search-first / learn-eval / skill-stocktake / rules-distill / skill-comply / context-sync) plus the adjacent skills (llms-txt-writer / daily-research / jsonld-knowledge-graph / writing-ecosystem / rules-stocktake)

## Contributing

This repo is shimo4228's personal harness artifact, so external PRs are not accepted. Instead:
- Fork it and customize freely
- Issues for questions or suggestions are welcome

Bug fixes flow upstream into `~/.claude/` when shimo4228 incorporates them.

## License

MIT License. See [LICENSE](LICENSE).

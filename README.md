Language: English | [日本語](README.ja.md)

# claude-harness

Public snapshot of the Claude Code harness (skills / agents / rules / hooks) that shimo4228 uses day-to-day: the files under `~/.claude/` that shape how Claude Code works on the author's machine. It is for Claude Code users who want to lift one skill, subagent, rule or hook into their own setup, and for developers studying how a working agent harness is put together, including the dated decisions behind each piece (written in Japanese).

The component folders (`skills/`, `agents/`, `rules/`, `hooks/`) and the decision records (`docs/adr/`, `rfcs/`, `docs/plans/`, `docs/evals/`) are exported one way from the author's live `~/.claude/` by [`scripts/sync-from-local.sh`](scripts/sync-from-local.sh), which runs a secret scan and overwrites those folders on every sync. Skills, agents and rules are published only when their origin tag marks them as the author's own ([Origin tags](#origin-tags)); hooks only when the author judged them reusable outside this machine. Articles about the harness and related repos are under [More from the author](#more-from-the-author).

## Usage

You need Claude Code and `git`; skills with Python code also need `uv`. Installing needs no key, but some skills call outside services when run and need that service's account or API key, for example: hf-sync (uploads to Hugging Face), review-when-watch (posts to Slack), and jev-skill-router and review-when-watch (TypeSafe Jev, a judgment-only model that answers closed questions with probabilities, via `TYPESAFE_API_KEY`). A few assume the author's own tools: spawn-session needs the Herdr terminal multiplexer, and wiki-query and wiki-harvest read an Obsidian wiki. Each `SKILL.md` says what it needs.

Clone once (first command below), then copy the full set or cherry-pick from that clone into `~/.claude/`. `cp` overwrites same-named files already there but leaves other files in an existing same-named skill folder: back up `~/.claude/` first, and remove the old folder if you want a clean copy.

### Full install

```bash
git clone https://github.com/shimo4228/claude-harness.git ~/.claude-harness
# Copy skills / agents / rules into ~/.claude/
mkdir -p ~/.claude/skills ~/.claude/agents ~/.claude/rules/common
cp -r ~/.claude-harness/skills/* ~/.claude/skills/
cp -r ~/.claude-harness/agents/* ~/.claude/agents/
cp -r ~/.claude-harness/rules/common/* ~/.claude/rules/common/
```

Every rule copied into `~/.claude/rules/common/` loads in every session, including the author's personal ones (practitioner-identity, contemplative-axioms); leave out the rules you do not want.

Hooks are separate: they must live under `~/.claude` and be wired into `settings.json` by hand ([docs/hooks.md](docs/hooks.md)).

### Cherry-pick

Copy only what you want. If unsure where to start: search-first, learn-eval, skill-stocktake, rules-distill, skill-comply and context-sync make up the [Agent Knowledge Cycle (AKC)](https://doi.org/10.5281/zenodo.19200726), the author's cycle for turning an agent's repeated experience into skills and rules. Each is also a standalone repo, bundled here too so the harness reads end to end.

```bash
cp -r ~/.claude-harness/skills/search-first ~/.claude/skills/
```

### Setup for Python skills

In each skill folder that has a `pyproject.toml` (`ls ~/.claude-harness/skills/*/pyproject.toml` lists them), run `uv sync` or `pip install -e .`. jsonld-knowledge-graph's linter runs with `uv run --with pyld` instead (see its `SKILL.md`).

## Contents

### Skills

<!-- BEGIN GENERATED: skills-table -->
| Skill | Purpose |
| --- | --- |
| [search-first](skills/search-first/SKILL.md) | Look outside before deciding — searches the live web, registries, and primary sources, and returns a report the caller picks from |
| [learn-eval](skills/learn-eval/SKILL.md) | Extracts reusable patterns from sessions, evaluates quality, and decides where to save |
| [skill-stocktake](skills/skill-stocktake/SKILL.md) | Skill quality audit — inline Glob inventory + single-context holistic evaluation, Keep/Improve/Update/Retire/Merge verdicts |
| [skill-health](skills/skill-health/SKILL.md) | Structural skill-library debt scan — flags "missing artifacts" (SKILL.md references to scripts / agents / sibling skills that don't resolve on disk). Deterministic; delegates quality / risk / validation to skill-stocktake / security-scan / skill-comply |
| [rules-distill](skills/rules-distill/SKILL.md) | Extracts cross-cutting principles from skills and promotes them to rules |
| [rules-stocktake](skills/rules-stocktake/SKILL.md) | Rules quality audit — residency-cost model (every line is a per-session token tax), checks for rules gone stale or made redundant by the harness itself, Keep/Improve/Update/Merge/Demote/Dissolve/Retire verdicts. The inverse of rules-distill |
| [skill-comply](skills/skill-comply/SKILL.md) | Measures actual compliance of skills / rules / agents. Classifies behavioral sequences across 3 prompt strictness levels |
| [context-sync](skills/context-sync/SKILL.md) | Audits and fixes project documentation. Detects role overlap, checks freshness, creates missing docs |
| [llms-txt-writer](skills/llms-txt-writer/SKILL.md) | Writes AI-facing docs (llms.txt / llms-full.txt). Answer.AI standard + GEO/AEO static analysis |
| [jsonld-knowledge-graph](skills/jsonld-knowledge-graph/SKILL.md) | Designs and ships a companion JSON-LD knowledge graph (graph.jsonld) next to llms.txt. Encodes domain entities and relationships as schema.org triples for LLM citation |
| [collect-context](skills/collect-context/SKILL.md) | Gathers in-session and external context into source material for article writing |
| [authorship-strategy](skills/authorship-strategy/SKILL.md) | 4-layer framework (Authenticity / Attribution diffusion / Idea-vs-scaffold / Tactics) for DOI-registered research repos |
| [release-doi](skills/release-doi/SKILL.md) | Cuts a versioned release of a DOI-registered research repo (Zenodo concept DOI semantics, CHANGELOG / tag / asset packaging) |
| [adr-writer](skills/adr-writer/SKILL.md) | Records design decisions as numbered ADRs — directory detection, sequence numbering, index update; the main loop writes the body from a settled decision packet, checked by an evidence script and the adr-reviewer agent |
| [readme-writer](skills/readme-writer/SKILL.md) | Writes human-facing READMEs — deterministic structural lint plus holistic LLM review (no scores) |
| [hf-sync](skills/hf-sync/SKILL.md) | Mirrors graph.jsonld-bearing research repos to Hugging Face Datasets |
| [spawn-session](skills/spawn-session/SKILL.md) | Launches a new detached Claude Code Remote Control session in a Herdr pane, visible in the mobile app session list |
| [harness-sync](skills/harness-sync/SKILL.md) | One-way export of origin-filtered components from the live harness into this repo — collection, secret scan, subtree replacement |
| [wiki-harvest](skills/wiki-harvest/SKILL.md) | Read-only harvest from an Obsidian LLM wiki (wiki/concept/) into a research repo — extracts only next-action-changing candidates into a ranked, source-cited ledger under the repo's `.notes/` |
| [wiki-query](skills/wiki-query/SKILL.md) | Read-only query over an Obsidian LLM wiki (wiki/concept/) with `[[ ]]` source-cited synthesis |
| [repo-asset-stocktake](skills/repo-asset-stocktake/SKILL.md) | Audits a project repo's non-code assets (tool configs, CI workflows, runbooks) for diminished value — flags assets whose consumer has vanished, with Keep/Update/Retire/Merge verdicts |
| [task-stocktake](skills/task-stocktake/SKILL.md) | Audits and consolidates a repo's pending-task tracking into its single task ledger — bootstraps the ledger, sweeps stray task lines, verifies entries against git log and actual code |
| [llm-as-judge](skills/llm-as-judge/SKILL.md) | Design pattern for LLM-as-judge evaluators — binary checks as evidence, one named holistic verdict, no score aggregation |
| [implementation-chain](skills/implementation-chain/SKILL.md) | Decides the task type (feat / fix / refactor / chore / prototype / writing) and front-loads its agent chain into the plan — Chain Matrix, reviewer routing, early-stop conditions |
| [public-comment](skills/public-comment/SKILL.md) | Replies in public technical threads (GitHub discussions / issues / PRs, HF discussions) — AI-slop tell removal, thread grounding, and a human gate with a Japanese translation before posting |
| [agent-stocktake](skills/agent-stocktake/SKILL.md) | Audit subagent definitions with a hybrid cost model (description = per-session residency, body = invocation) — flags suppression instructions and agents whose job the harness now does natively; third sibling of skill-/rules-stocktake |
| [generation-audit](skills/generation-audit/SKILL.md) | On a model-generation change, capture the live runtime layer (system prompt + tool descriptions), classify mismatches as conflict / redundancy / drift, and hand the evidence to the stocktake skills for verdicts |
| [headline-craft](skills/headline-craft/SKILL.md) | Craft skill for the one line that makes readers open — title / tagline / subtitle / SNS-post candidates, generated with concrete techniques and scored per traffic channel (search vs feed) |
| [prompt-perturb](skills/prompt-perturb/SKILL.md) | Diversity injection. A deliberately context-starved forager agent fetches prompts from external creativity-technique catalogs, so the angles come from outside the session's own habits |
| [session-judgment-mining](skills/session-judgment-mining/SKILL.md) | Mine past session transcripts for judgements the user made repeatedly, and promote the recurring ones into skills or rules |
| [verify-bootstrap](skills/verify-bootstrap/SKILL.md) | Stand up a repo's machine gates (format / lint / type check / security / dependency / test), or take stock of gates that have gone stale. Tool choice is researched at bootstrap time rather than baked into the skill |
| [x-draft](skills/x-draft/SKILL.md) | Turn a research report into one long-form social post. Pull-only — no quota, no notification, invoked only when the author already wants to post. Rechecks the primary source, gates on staleness, strips the AI tells, and stops at the draft |
| [task-triage](skills/task-triage/SKILL.md) | One cycle of the task-triage loop: judge every open ledger task (premise, start condition, worth), dispatch the ready ones to fresh build sessions, verify their output independently — the human keeps the merge word |
| [harness-boundary](skills/harness-boundary/SKILL.md) | Design-time lens for any proposed mechanism (rule / skill / hook / agent / workflow): which of 6 layers it belongs to, whether the model could own it instead, and whether it survives a runtime swap — keep only what outlives the harness |
| [skill-creator](skills/skill-creator/SKILL.md) | Write or rewrite a skill / agent definition — intent packet, library-wide boundary check, Fable-era writing rules, a fresh-context draft gate (Publishable / Fix / Drop, no scoring), author read-through. Replaces the upstream anthropics skill-creator in place (ADR-0046) |
| [measurement-discipline](skills/measurement-discipline/SKILL.md) | Discipline for claims that rest on data: deciding on an experiment result, setting a threshold or guard, choosing an observation period, or comparing a candidate with production |
| [prose-translation](skills/prose-translation/SKILL.md) | Translates human-facing prose (essays, articles, READMEs, ADRs) between Japanese and English in both directions, keeping the author's voice and the target channel's register |
| [repair-discipline](skills/repair-discipline/SKILL.md) | Establishes what is true now from primary evidence before a fix: a bug, a stale task, something stuck or flaky, or a schema or storage change that other code reads |
| [rfc-writer](skills/rfc-writer/SKILL.md) | Files one entry in the public `rfcs/` ledger: the filing bar, numbering, template, publication rules and the index line |
| [review-to-lint](skills/review-to-lint/SKILL.md) | Moves the mechanical items of a reviewer's checklist into a deterministic script, leaving the reviewer agent or skill only the checks that need judgement |
| [jev-skill-router](skills/jev-skill-router/SKILL.md) | UserPromptSubmit hook that asks TypeSafe Jev which installed skill fits the prompt; shadow-first, injects only after measured accuracy |
| [jev-judgment-design](skills/jev-judgment-design/SKILL.md) | Moving closed LLM judgments (relevant? new? how strong?) to TypeSafe Jev: put what is judged against into the state, code decides from Jev's probabilities, canaries catch over-filtering |
| [author-calibrated-eval](skills/author-calibrated-eval/SKILL.md) | Tuning LLM-written prose against the author's own reading: frozen inputs, a hard-case set, blind side-by-side reads with a strong-model reference, and an LLM judge that only gates faithfulness |
| [review-when-watch](skills/review-when-watch/SKILL.md) | Daily launchd job: checks each new research note against the Review-when conditions in this repo's ADRs and RFCs via TypeSafe Jev, and posts the matches to Slack. Not model-invoked |
| [mono-figure](skills/mono-figure/SKILL.md) | Drawing static explanatory figures for articles and READMEs (lines, arrows, numbers, labels) in the mono-color look — paper, ink, type, whitespace. Claude draws SVG by default (rendered to PNG where a platform needs it) |
<!-- END GENERATED: skills-table -->

### Agents

<!-- BEGIN GENERATED: agents-table -->
| Agent | Purpose |
| --- | --- |
| [prompt-writer](agents/prompt-writer.md) | Generates concise prompts using a lightweight model. Creates and rewrites LLM prompt templates |
| [adr-reviewer](agents/adr-reviewer.md) | Checks an ADR's record, not its decision — whether Context carries verifiable evidence, `Review-when` names an observable expiry trigger, Alternatives are real rather than straw men (a live rival marked undecided, with conditions for revisiting it, is allowed), Consequences show both sides, and override relations with prior ADRs are stated (a dated note when a prior ADR is partly weakened) |
| [prompt-forager](agents/prompt-forager.md) | The context-starved half of prompt-perturb. Receives one line of purpose and deliberately nothing else, so what it finds is not shaped by the session that asked |
| [swift-reviewer](agents/swift-reviewer.md) | Swift / SwiftUI review — Swift 6 strict concurrency, value semantics, SwiftUI state ownership, retain cycles, HIG compliance |
| [readme-judge](agents/readme-judge.md) | Fresh-context README judge: reads evidence JSON + the README once, answers a fixed checklist with quoted evidence, returns a named verdict (Publishable / Fix / Rewrite) |
| [researcher](agents/researcher.md) | One research angle per run for search-first's parallel Full mode: searches the web, registries and primary sources, writes one dated notes file or the merged report that opens the plan research gate |
<!-- END GENERATED: agents-table -->

### Rules

Rules under `rules/common/` load every session: mostly environment-specific facts, wiring and traps, plus the author's personal rules and working principles such as llm-first-code. Procedures live in skills, time-critical checks in hooks:

<!-- BEGIN GENERATED: rules-table -->
| Rule | Purpose |
| --- | --- |
| [agents](rules/common/agents.md) | Pointer to the agent catalog (the frontmatter of `agents/*.md` is canonical), the rule that review runs in a different agent process from the implementer, and the entry points to the Herdr delegation skills |
| [akc-cycle](rules/common/akc-cycle.md) | Pointer edition of the Agent Knowledge Cycle — maps each of its mechanisms to the skill or rule that owns it, states when a piece of scaffolding can be removed (Scaffold Dissolution), and says how ADRs are treated (dated records, supersede with dated annotations, a two-condition filing bar) |
| [debugging](rules/common/debugging.md) | Rate-limit signal — repeated rate limits during bulk writes to an external platform are a policy signal, not a transient error: stop the burst and report to the human instead of backing off through it |
| [planning](rules/common/planning.md) | Planning wiring — search-first before anything that may already exist, handing implementation from the judging session to a separate build session by default, implementation-chain for chain type and reviewer conditions, and the repo's `.claude/verify.sh` as the canonical Verify |
| [skills](rules/common/skills.md) | Origin vocabulary for skills / agents / rules (the canonical table), the `replaces:` lineage field, the imperative wiring to skill-creator before writing or overhauling a skill, and the writing rule — positive form by default, prohibitions only under three stated conditions |
| [contemplative-axioms](rules/common/contemplative-axioms.md) | Contemplative Constitutional AI clauses from Laukkonen et al. (2025), verbatim |
| [task-tracking](rules/common/task-tracking.md) | One canonical pending-task ledger per repo in one of two shapes — a single table (`.notes/TASKS.md`) or a public store of one-file-per-task RFCs (`rfcs/`) queried through `claims.py ready`; claim / release for concurrent sessions; review findings are filed only when they break the loop itself, citing the file and line that show the problem |
| [knowledge-staleness](rules/common/knowledge-staleness.md) | Treats external LLM-domain knowledge as going stale on a one-week scale — never assert tooling, specs, or going rates from memory; check at search time, date the evidence, and attach an expiry condition to any recommendation |
| [practitioner-identity](rules/common/practitioner-identity.md) | Author's self-definition, verbatim — searching for what counts as a good idea and a good means in the AI era; DOI is one means, not a researcher career; code fades, ideas persist |
| [llm-first-code](rules/common/llm-first-code.md) | Optimizes code for its actual reader — the next LLM session, not humans: preserve verifiability (types, tests, goldens) over readability, enforce quality through machine gates, and spend human-readability budget only on READMEs and output text |
| [boundary](rules/common/boundary.md) | The single home of the harness's boundaries — which operations are handed to the human (publication, billing, external sends, ledger filing, unattended changes to permissions / hooks / rules / ADRs), which risks the agent takes without asking, and when to stop and report |
| [evals](rules/common/evals.md) | Eval wiring — routes each eval question to its owner: `/claude-api build-eval` → `hillclimb` for building and improving against an eval, with search-first before grading is fixed in unfamiliar domains; the `claude -p` runner trap for harness targets |
<!-- END GENERATED: rules-table -->

### Hooks

`hooks/` carries five PreToolUse hooks for the `git commit` boundary (a secret scan, the repo's own `.claude/verify.sh` once you approve it, bandit, `ruff format --check`, a review reminder) and two that fire outside commits. All carry bats tests under `tests/`; [docs/hooks.md](docs/hooks.md) covers install, the verify hook's approval model, what each test pins and what is left out, and llms-full.txt describes each hook.

### Design decisions (ADRs) and proposals (RFCs)

`docs/adr/` is the *why* behind the components: dated Architecture Decision Records of each adoption, retirement and reversal, failures included ([ADR index](docs/adr/README.md)). `rfcs/` is the public task-and-proposal ledger, closed entries kept with their reasons ([ADR-0049](docs/adr/0049-unify-task-ledger-into-public-rfcs.md), [index](rfcs/README.md)); `docs/plans/` holds approved plan-mode plans ([ADR-0085](docs/adr/0085-plans-as-records-in-docs-plans.md)); `docs/evals/` holds eval cards for the harness's own measuring instruments ([RFC-0030](rfcs/0030-eval-cards-for-ready-instruments.md), [index](docs/evals/README.md)). The ADRs and these three folders are written in Japanese; llms-full.txt says how each is kept.

## Origin tags

Each skill, agent and rule file carries an `origin` tag, in its frontmatter or in an HTML comment. Published files carry `shimo4228`, the author's own; the contemplative-axioms rule is a verbatim quotation kept under it. Components from Everything Claude Code and other external sources are named below without content. Full table: Origin tags in [llms-full.txt](llms-full.txt); canonical: [rules/common/skills.md](rules/common/skills.md) (in Japanese).

<!-- BEGIN GENERATED: upstream-components -->
### Upstream components (names only)

The live harness also runs components from external upstreams. Their content — including any local modifications to it — is **not redistributed** here; the names alone are listed so the full composition stays visible. ECC = [Everything Claude Code](https://github.com/affaan-m/everything-claude-code).

| Upstream | Skills | Agents | Rules |
|---|---|---|---|
| ECC + local modifications | loop-design-check, refactor-clean | architect, refactor-cleaner, security-reviewer | common/coding-style, common/security, common/testing |
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | — | Explore | — |
| [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) + local modifications | mondo | — | — |
| [herdrdev/herdr](https://github.com/herdrdev/herdr) | herdr | — | — |
| [mattpocock/skills](https://github.com/mattpocock/skills) + local modifications | grill-me, wait-what | — | — |
| [modem-dev/hunk](https://github.com/modem-dev/hunk) | hunk-review | — | — |
| [tt-a1i/archify](https://github.com/tt-a1i/archify) + local modifications | archify | — | — |
<!-- END GENERATED: upstream-components -->

## More from the author

- **[I Cut My AI Review Chain From 6 Stages to 1: Breaking the Loop That Never Hits Zero Findings](https://dev.to/shimo4228/i-cut-my-ai-review-chain-from-6-stages-to-1-breaking-the-loop-that-never-hits-zero-findings-1moi)** ([日本語](https://zenn.dev/shimo4228/articles/review-chain-damping)): why the standing review went from six chains to one (plus one conditional), with the measurements behind ADR-0055.
- **[AI Review Kept Creating Work: Why I Deleted 4,541 Lines](https://dev.to/shimo4228/ai-review-kept-creating-work-why-i-deleted-4541-lines-22ec)** ([日本語](https://zenn.dev/shimo4228/articles/ai-review-task-loop)): why filing review findings as tasks kept creating work, and the rule adopted: file only when the premise is verified or a person chooses to explore it.
- **[akc-cycle](https://github.com/shimo4228/akc-cycle)**: the [Agent Knowledge Cycle](https://github.com/shimo4228/agent-knowledge-cycle) (its repo holds the dated design decisions and concept DOI) as one Claude Code plugin plus a self-contained rules file; `rules/common/akc-cycle.md` here is its pointer edition.
- **[harness-scope](https://github.com/shimo4228/harness-scope)**: a Claude Code Mod that turns a global harness like this one on or off per repo with named profiles.
- **[harness-pruning](https://github.com/shimo4228/harness-pruning)**: every skill, rule, agent and hook retired from this harness, dated, with the decision behind each.
- **[shimo4228](https://github.com/shimo4228/shimo4228)**: the author's hub: the five long-running projects, their DOIs, and the [public dashboard](https://shimo4228.github.io/shimo4228/traffic/dashboard/) of this repo's clone and view traffic.

## Contributing

This is shimo4228's personal harness: fork and customize freely, and use issues for questions or suggestions; external PRs are not accepted. Bug fixes flow upstream into `~/.claude/` when shimo4228 incorporates them.

## License

MIT License. See [LICENSE](LICENSE).

<details>
<summary>For tools and AI assistants</summary>

claude-harness is the Claude Code harness its author, shimo4228, uses every day, published one way for reuse and study.

It exists because the ADRs only make sense next to the files they argue about.

Canonical facts: MIT license; Markdown skills, agents and rules, Bash hooks, Python skills run with `uv` (Python 3.11 or later for most); the records and some newer skill descriptions are in Japanese. Status: active, synced one way. The sync script (run by the harness-sync skill) also overwrites `scripts/hooks/` and `tests/` and regenerates only the README component tables; the README prose, `docs/hooks.md`, the llms files, LICENSE and the sync script are maintained by hand. No paid key is needed to install.

Example: the Cherry-pick command installs search-first, which has the agent search the live web, registries and primary sources before deciding and report back for the caller to pick from.

Links: [llms.txt](llms.txt) and [llms-full.txt](llms-full.txt). The AKC skills implement the [Agent Knowledge Cycle](https://github.com/shimo4228/agent-knowledge-cycle), concept DOI [10.5281/zenodo.19200726](https://doi.org/10.5281/zenodo.19200726); cite AKC by that DOI. The author's hub is [shimo4228/shimo4228](https://github.com/shimo4228/shimo4228).

</details>

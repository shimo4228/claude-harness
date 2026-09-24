Language: English | [日本語](README.ja.md)

# claude-harness

Public snapshot of the Claude Code harness (skills / agents / rules / hooks) that shimo4228 uses day-to-day.

Skills, agents, and rules are a mechanical aggregation of assets tagged `origin: shimo4228` from `~/.claude/`; ECC-derived material (`origin: ECC` / `ECC-customized`) and auto-extracted artifacts (`origin: auto-extracted`) are excluded. ADRs are synced wholesale, and hooks come from a curated allowlist — publication there is a judgement about reuse outside this machine, not about who wrote the file.

## Positioning

- **Audience**: Claude Code (CLI + IDE extensions) users, and developers researching agent skill / rule ecosystems
- **Source of truth**: `~/.claude/` is canonical; this repo is a one-way export produced by [`scripts/sync-from-local.sh`](scripts/sync-from-local.sh) (origin filter + hook allowlist → secret scan → subtree replacement)
- **License**: MIT. Free to copy, modify, and redistribute. Forking and customizing for personal use is encouraged

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
| [rules-stocktake](skills/rules-stocktake/SKILL.md) | Rules quality audit — residency-cost model (every line is a per-session token tax), staleness / substrate-absorption checks, Keep/Improve/Update/Merge/Demote/Dissolve/Retire verdicts. The inverse of rules-distill |
| [skill-comply](skills/skill-comply/SKILL.md) | Measures actual compliance of skills / rules / agents. Classifies behavioral sequences across 3 prompt strictness levels |
| [context-sync](skills/context-sync/SKILL.md) | Audits and fixes project documentation. Detects role overlap, checks freshness, creates missing docs |
| [codex-review](skills/codex-review/SKILL.md) | Cross-model second opinion from the OpenAI Codex CLI (a different model family), read-only on both the argv and config face — (1) code review of the current diff folded into the review chain, (2) plan-stage premise challenge of a design packet (refute / missing / alternative, never a design) |
| [llms-txt-writer](skills/llms-txt-writer/SKILL.md) | Writes AI-facing docs (llms.txt / llms-full.txt). Answer.AI standard + GEO/AEO static analysis |
| [jsonld-knowledge-graph](skills/jsonld-knowledge-graph/SKILL.md) | Designs and ships a companion JSON-LD knowledge graph (graph.jsonld) next to llms.txt. Encodes domain entities and relationships as schema.org triples for LLM citation |
| [collect-context](skills/collect-context/SKILL.md) | Gathers in-session and external context into source material for article writing |
| [authorship-strategy](skills/authorship-strategy/SKILL.md) | 4-layer framework (Authenticity / Attribution diffusion / Idea-vs-scaffold / Tactics) for DOI-registered idea-rescue research repos |
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
| [agent-stocktake](skills/agent-stocktake/SKILL.md) | Audit subagent definitions with a hybrid cost model (description = per-session residency, body = invocation) — flags suppression instructions and substrate absorption; third sibling of skill-/rules-stocktake |
| [generation-audit](skills/generation-audit/SKILL.md) | On a model-generation change, capture the live runtime layer (system prompt + tool descriptions), classify mismatches as conflict / redundancy / drift, and hand the evidence to the stocktake skills for verdicts |
| [git-workflow](skills/git-workflow/SKILL.md) | Permission-friction discipline for git in this environment — one Bash call per git command; chaining with && or pipes breaks the Bash(git:*) auto-allow and stalls on manual prompts |
| [headline-craft](skills/headline-craft/SKILL.md) | Craft skill for the one line that makes readers open — title / tagline / subtitle / SNS-post candidates, generated with concrete techniques and scored per traffic channel (search vs feed) |
| [herdr-delegate](skills/herdr-delegate/SKILL.md) | Hand a whole implementation task to a different CLI agent running in a Herdr pane (Codex, etc.). Gated on an explicit user request — parallelism alone is not a reason |
| [prompt-perturb](skills/prompt-perturb/SKILL.md) | Diversity injection. A deliberately context-starved forager agent fetches prompts from external creativity-technique catalogs, so the angles come from outside the session's own habits |
| [session-judgment-mining](skills/session-judgment-mining/SKILL.md) | Mine past session transcripts for judgements the user made repeatedly, and promote the recurring ones into skills or rules |
| [verify-bootstrap](skills/verify-bootstrap/SKILL.md) | Stand up a repo's machine gates (format / lint / type check / security / dependency / test), or take stock of gates that have gone stale. Tool choice is researched at bootstrap time rather than baked into the skill |
| [x-draft](skills/x-draft/SKILL.md) | Turn a research report into one long-form social post. Pull-only — no quota, no notification, invoked only when the author already wants to post. Rechecks the primary source, gates on staleness, strips the AI tells, and stops at the draft |
| [task-triage](skills/task-triage/SKILL.md) | One cycle of the task-triage loop: judge every open ledger task (premise, start condition, worth), dispatch the ready ones to fresh build sessions, verify their output independently — the human keeps the merge word |
| [harness-boundary](skills/harness-boundary/SKILL.md) | Design-time lens for any proposed mechanism (rule / skill / hook / agent / workflow): which of 6 layers it belongs to, whether the model could own it instead, and whether it survives a runtime swap — keep only what outlives the harness |
| [skill-creator](skills/skill-creator/SKILL.md) | Write or rewrite a skill / agent definition — intent packet, library-wide boundary check, Fable-era writing rules, a fresh-context draft gate (Publishable / Fix / Drop, no scoring), author read-through. Replaces the upstream anthropics skill-creator in place (ADR-0046) |
| [measurement-discipline](skills/measurement-discipline/SKILL.md) | 測定に基づく主張・閾値・ガード・実験結果を設計または評価するときの規律。Use when the user says 「この実験結果で判断していい？」「閾値を決めたい」「ガード/検査を足したい」「1 回通ったから大丈夫」, when a design places a numer |
| [prose-translation](skills/prose-translation/SKILL.md) | 日本語⇄英語の voice 保持翻訳スキル（**両方向**）。エッセイ・記事・README・ADR 等の人間向け prose を、出力先の publication channel contract が宣言する register と原文の確度を保って自然に訳す。逐語訳でも MT で |
| [repair-discipline](skills/repair-discipline/SKILL.md) | バグ修正・残課題・schema/storage 変更に着手するときの規律。Use when the user says 「このバグ直して」「残課題をやって」「この schema を変えたい」, when picking up a stale task file, or when |
| [rfc-writer](skills/rfc-writer/SKILL.md) | 公開 rfcs/ 台帳へ 1 エントリを起票する手順と規約の唯一の正本（足切り → 採番 → 様式 → 公開規約 → spawn 接続 → index 行）。Use when the user says 「これ起票して」「RFC にしておいて」「提案を台帳に載せて」, when |
| [review-to-lint](skills/review-to-lint/SKILL.md) | 既存 reviewer（agent / review skill）のチェックリストから機械判定可能な項目を決定論 script に抽出し、reviewer を意味的チェック専任に薄化する手順。著者が「このレビュアーを lint 化して」「レビューを lint に吸収して」「機械チ |
| [growth-astra](skills/growth-astra/SKILL.md) | writes the north star for a GitHub follower campaign (`.growth/NORTH_STAR.md`) — initial pass and later revisions; escalation target of growth-fable |
| [growth-fable](skills/growth-fable/SKILL.md) | plans experiments toward the north star, dispatches them to workers, records results in `.growth/EXPERIMENTS.md` |
| [jev-skill-router](skills/jev-skill-router/SKILL.md) | UserPromptSubmit hook that asks TypeSafe Jev which installed skill fits the prompt; shadow-first, injects only after measured accuracy |
| [jev-judgment-design](skills/jev-judgment-design/SKILL.md) | Moving closed LLM judgments (relevant? new? how strong?) to TypeSafe Jev: put what is judged against into the state, code decides from Jev's probabilities, canaries catch over-filtering |
| [author-calibrated-eval](skills/author-calibrated-eval/SKILL.md) | Tuning LLM-written prose against the author's own reading: frozen inputs, a hard-case set, blind side-by-side reads with a strong-model reference, and an LLM judge that only gates faithfulness |
<!-- END GENERATED: skills-table -->

> The first six (search-first, learn-eval, skill-stocktake, rules-distill, skill-comply, context-sync) are components of the [Agent Knowledge Cycle (AKC)](https://doi.org/10.5281/zenodo.19200726). Each is also published as its own standalone repo, but they are bundled here so the harness can be read end-to-end.

### Agents

<!-- BEGIN GENERATED: agents-table -->
| Agent | Purpose |
| --- | --- |
| [prompt-writer](agents/prompt-writer.md) | Generates concise prompts using a lightweight model. Creates and rewrites LLM prompt templates |
| [readme-reviewer](agents/readme-reviewer.md) | Strict README / repo top-page review — LLM-read floor, lead clarity, human hook, scannability, length discipline, visual effectiveness. Companion to readme-writer |
| [readme-clarity-reviewer](agents/readme-clarity-reviewer.md) | First-contact reader clarity review for READMEs — coined-term budget, insider-context dependency, Japanese register (ですます). Parallel partner of readme-reviewer |
| [adr-reviewer](agents/adr-reviewer.md) | Checks an ADR's record, not its decision — whether Context carries verifiable evidence, `Review-when` names an observable expiry trigger, Alternatives are real rather than straw men (a live 「未決」 rival is allowed), Consequences show both sides, and override relations with prior ADRs are stated (dated 注記 on partial weakening) |
| [prompt-forager](agents/prompt-forager.md) | The context-starved half of prompt-perturb. Receives one line of purpose and deliberately nothing else, so what it finds is not shaped by the session that asked |
| [swift-reviewer](agents/swift-reviewer.md) | Swift / SwiftUI review — Swift 6 strict concurrency, value semantics, SwiftUI state ownership, retain cycles, HIG compliance |
| [readme-judge](agents/readme-judge.md) | Fresh-context README judge: reads evidence JSON + the README once, answers a fixed checklist with quoted evidence, returns a named verdict (Publishable / Fix / Rewrite) |
<!-- END GENERATED: agents-table -->

### Rules

Environment-specific facts, wiring, and traps auto-loaded every session (under `rules/common/`). Procedures live in skills, time-critical checks in hooks:

<!-- BEGIN GENERATED: rules-table -->
| Rule | Purpose |
| --- | --- |
| [agents](rules/common/agents.md) | Pointer to the agent catalog (the frontmatter of `agents/*.md` is canonical), the rule that review runs in a different agent process from the implementer, and the entry points to the Herdr delegation skills |
| [akc-cycle](rules/common/akc-cycle.md) | Pointer edition of the Agent Knowledge Cycle — maps each mechanism (six phases, judge / build / human loop, LLM-first readability, expiry-conditioned knowledge) to the skill or rule that owns it, states the Scaffold Dissolution criteria, and says how ADRs are treated (dated records, supersede with dated annotations, a two-condition filing bar) |
| [debugging](rules/common/debugging.md) | Rate-limit signal — repeated rate limits during bulk writes to an external platform are a policy signal, not a transient error: stop the burst and report to the human instead of backing off through it |
| [planning](rules/common/planning.md) | Planning wiring — search-first before anything that may already exist, build-tier dispatch as the default for implementing from a judge-tier session, implementation-chain for chain type and reviewer conditions, and the repo's `.claude/verify.sh` as the canonical Verify |
| [skills](rules/common/skills.md) | Origin vocabulary for skills / agents / rules (the canonical table), the `replaces:` lineage field, the imperative wiring to skill-creator before writing or overhauling a skill, and the writing rule — positive form by default, prohibitions only under three stated conditions |
| [contemplative-axioms](rules/common/contemplative-axioms.md) | Contemplative Constitutional AI clauses from Laukkonen et al. (2025), verbatim |
| [task-tracking](rules/common/task-tracking.md) | One canonical pending-task ledger per repo in one of two shapes — a single table (`.notes/TASKS.md`) or a public store of one-file-per-task RFCs (`rfcs/`) queried through `claims.py ready`; claim / release for concurrent sessions; review findings are filed only when they break the loop itself, with a producer → sink citation |
| [knowledge-staleness](rules/common/knowledge-staleness.md) | Treats external LLM-domain knowledge as going stale on a one-week scale — never assert tooling, specs, or going rates from memory; check at search time, date the evidence, and attach an expiry condition to any recommendation |
| [practitioner-identity](rules/common/practitioner-identity.md) | Author's self-definition, verbatim — searching for what counts as a good idea and a good means in the AI era; DOI is one means, not a researcher career; code fades, ideas persist |
| [llm-first-code](rules/common/llm-first-code.md) | Optimizes code for its actual reader — the next LLM session, not humans: preserve verifiability (types, tests, goldens) over readability, enforce quality through machine gates, and spend human-readability budget only on READMEs and output text |
| [boundary](rules/common/boundary.md) | The single home of the harness's boundaries — which operations are handed to the human (publication, billing, external sends, ledger filing, unattended changes to permissions / hooks / rules / ADRs), which risks the agent takes without asking, and when to stop and report |
<!-- END GENERATED: rules-table -->

### Hooks

`hooks/` carries five PreToolUse hooks that run at the `git commit` boundary — a secret scan, a runner for the repo's own machine gate, a bandit scan, a `ruff format --check`, and a review reminder — plus the two parts they need, and two session-surface hooks published with the `rfcs/` ledger: a ledger-etiquette reminder (with `scripts/claims.py`, the ledger CLI) and a judge-tier review-routing guard. Several ADRs argue about their internals, so the code lives here rather than leaving those decisions pointing at nothing. Unlike skills and rules, hooks need manual wiring into `settings.json`. All carry bats tests, each checked with a negative control — the hook mutated to remove the property, the test confirmed to fail against the mutant. Install steps, the approval model behind the verify gate, and what is deliberately left out: [docs/hooks.md](docs/hooks.md).

### Design decisions (ADRs) and proposals (RFCs)

`docs/adr/` records why this harness is shaped the way it is: adoptions, retirements, and reversals, each as a dated Architecture Decision Record synced from the live harness alongside the components. The skills, agents, and rules above are the *what*; the ADRs are the *why* — the audit trail behind the harness, failures included. Start from the [ADR index](docs/adr/README.md). ADRs are written in Japanese.

`rfcs/` is the harness's public task-and-proposal ledger ([ADR-0049](docs/adr/0049-unify-task-ledger-into-public-rfcs.md)): one entry per proposal or work item, body in Rust-RFC-template form, state in the frontmatter, terminal entries left in place so rejected proposals stay readable with their reasons. ADRs record decisions; `rfcs/` holds what is still open — including the entries that will never be built, which is the point.

## Usage

### Full install

```bash
git clone https://github.com/shimo4228/claude-harness.git ~/.claude-harness
# Copy skills / agents / rules into ~/.claude/
cp -r ~/.claude-harness/skills/* ~/.claude/skills/
cp -r ~/.claude-harness/agents/* ~/.claude/agents/
cp -r ~/.claude-harness/rules/common/* ~/.claude/rules/common/
```

Hooks are separate: they must live under `~/.claude` and be wired into `settings.json` by hand. See [docs/hooks.md](docs/hooks.md).

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
| ECC + local modifications | config-gc, loop-design-check, refactor-clean, tdd | architect, refactor-cleaner, security-reviewer | common/coding-style, common/security, common/testing |
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | — | Explore | — |
| [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) + local modifications | mondo | — | — |
| [herdrdev/herdr](https://github.com/herdrdev/herdr) | herdr | — | — |
| [mattpocock/skills](https://github.com/mattpocock/skills) + local modifications | grill-me, wait-what | — | — |
| [modem-dev/hunk](https://github.com/modem-dev/hunk) | hunk-review | — | — |
| [tt-a1i/archify](https://github.com/tt-a1i/archify) | archify | — | — |
<!-- END GENERATED: upstream-components -->

## Related repos

- [shimo4228](https://github.com/shimo4228/shimo4228) — Hub repo aggregating the five practice lines (AKC / Contemplative Agent / AAP / Authorship Strategy / Attention Not Self) and the supporting ecosystem. This repo's clone/view traffic is published on its [public dashboard](https://shimo4228.github.io/shimo4228/traffic/dashboard/)
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

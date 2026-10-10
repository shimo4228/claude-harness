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

The repo ships skills (`skills/`), agents (`agents/`) and rules (`rules/common/`, loaded every session), plus the hooks and design records below. [docs/components.md](docs/components.md) lists each skill, agent and rule with what it is for, and names the upstream components the live harness runs but this repo does not redistribute.

### Hooks

`hooks/` carries five PreToolUse hooks for the `git commit` boundary (a secret scan, the repo's own `.claude/verify.sh` once you approve it, bandit, `ruff format --check`, a review reminder) and two that fire outside commits. All carry bats tests under `tests/`; [docs/hooks.md](docs/hooks.md) covers install, the verify hook's approval model, what each test pins and what is left out, and llms-full.txt describes each hook.

### Design decisions (ADRs) and proposals (RFCs)

`docs/adr/` is the *why* behind the components: dated Architecture Decision Records of each adoption, retirement and reversal, failures included ([ADR index](docs/adr/README.md)). `rfcs/` is the public task-and-proposal ledger, closed entries kept with their reasons ([ADR-0049](docs/adr/0049-unify-task-ledger-into-public-rfcs.md), [index](rfcs/README.md)); `docs/plans/` holds approved plan-mode plans ([ADR-0085](docs/adr/0085-plans-as-records-in-docs-plans.md)); `docs/evals/` holds eval cards for the harness's own measuring instruments ([RFC-0030](rfcs/0030-eval-cards-for-ready-instruments.md), [index](docs/evals/README.md)). The ADRs and these three folders are written in Japanese; llms-full.txt says how each is kept.

## Origin tags

Each skill, agent and rule file carries an `origin` tag, in its frontmatter or in an HTML comment. Published files carry `shimo4228`, the author's own; the contemplative-axioms rule is a verbatim quotation kept under it. Components from Everything Claude Code and other external sources are named, without content, in [docs/components.md](docs/components.md#upstream-components-names-only). Full table: Origin tags in [llms-full.txt](llms-full.txt); canonical: [rules/common/skills.md](rules/common/skills.md) (in Japanese).

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

<!-- origin: shimo4228 -->
# Skill Portability

Assume a skill is reused in more than one context. Follow these points when creating or editing one.

- **Write the body generically**: describe patterns, decisions and workflows in a form anyone can
  apply to their own situation
- **Keep personal project URLs out of the body**: links to your own canonical implementation, your
  personal repos, or paths inside a specific project tie the skill to one user's filesystem / one
  project's lifecycle, so they do not go in the body
- **Where concrete examples and origin stories go**:
  - Abstract worked examples (hypothetical scenarios) → fine in the skill body
  - Personal project references, origin stories, canonical implementations → `inspiration.md`,
    ADR Notes, memory, or a "Related Projects" file in the same repo
  - User-specific settings → skill parameters / environment variables, not hard-coded in the body
- **Links within your own project are allowed**: relative links to the README / docs / config
  templates in the same repo as the skill are context the skill needs to work, so they may go in
  the body

## Portability test

Can someone else install it and use it without knowing anything of the author's personal context?
If understanding this skill requires reading `claude-skill-foo`, the principle is violated.

Origin tracking (your origin vocabulary, if you track one) records *who made it*; portability
decides *who can use it*.

## Split long skills

Apply progressive disclosure inside a skill as well. When one file grows long, cut parts out into
`references/` and point to them from SKILL.md. Do not front-load everything into the SKILL.md body
(a context-engineering principle for the Claude 5 generation).

## Repo packaging

When a skill is published as its own GitHub repo:

- **Bundle the subagents it calls.** Without them an installer has to find the agents separately,
  and an orchestrator skill whose canonical rules an agent reads from SKILL.md stays broken until both are in.
- **Name by what ships.** A skill (SKILL.md) follows the open Agent Skills standard and runs in other tools;
  a subagent (`agents/*.md`) is Claude Code only. A repo that bundles agents keeps the `claude-skill-` prefix and
  says so in the `compatibility` frontmatter; a pure-skill repo drops the prefix (`<owner>/<skill-name>`).
- **Layout**: `skills/<name>/SKILL.md` plus flat `agents/<agent>.md`, and an idempotent `install.sh`
  (skip when identical, back up to `*.bak-<ts>` otherwise; `--force` / `--dry-run`). A pure-skill repo may omit it.
- **SkillsMP caveat**: `/skills add <owner/repo>` installs only `skills/`, not `agents/`. A repo that bundles
  agents says in its README to run `install.sh` or `cp agents/*.md ~/.claude/agents/`.

The author's harness keeps these rules in its publish step (`harness-sync`, **Skill repo packaging**).

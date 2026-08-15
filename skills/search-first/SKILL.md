---
name: search-first
description: "Search npm / PyPI / MCP / GitHub / existing skills before writing code for any new feature, integration, library selection, or utility. Use whenever the user says 'add X functionality', 'implement Y', 'set up Z', 'integrate W', asks 'what library should I use for...', 'is there a package/client/MCP for...', proposes a specific tool while open to alternatives, or hits the planning.md wiring that routes dependency additions and self-built utilities here first. Especially when the task adds a dependency, picks between tools, or builds a utility that likely already exists (parser, checker, converter, linter, CI step, E2E framework, payment / auth / API client). DO NOT use for bug fixes, refactoring, config value edits, file summarization, or throwaway scripts whose approach the user already fully specified."
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
user-invocable: true
origin: shimo4228
---

# /search-first — Research Before You Code

Before writing a new feature, utility, integration, or picking a library, search
for an existing solution first. The best code is code you don't have to write.

This skill is **discipline, not mechanism.** The *how* of searching — parallel
subagents, live documentation lookup, registry queries — belongs to your agent
harness and keeps changing. What this skill pins down is the part that survives
those changes: **articulate before you search, search by source priority, and
end with a recorded verdict.** Lead with the discipline; delegate the mechanism.

## Step 0 — Articulate the requirement (mandatory, user-visible text)

Before any tool call or subagent, write 2–3 sentences of **plain assistant text**
(not buried inside tool arguments) stating:

- **What** functionality is needed — concretely, not "X support"
- **Language / framework** the implementation will use
- **Constraints** — existing deps, performance limits, license requirements

Why: this externalizes the search query so the user can redirect *before* you
spend effort, and it leaves an auditable record. A subagent call whose `args`
carry the requirement does **not** satisfy this step — the user reads chat text,
not tool arguments. Emit the articulation as text first, then call tools whose
arguments may mirror it.

## Step 1 — Search by source priority

Check these in order; stop early when you find a strong match:

0. **This repo** — `rg` / grep through the relevant modules and tests. The thing
   may already exist here.
1. **Package registries** — npm / PyPI / crates / Go modules for the language in play.
2. **MCP servers** — already-configured servers first, then the registry. The
   capability may already be wired in.
3. **Installed skills / agents / tools** — your harness may already carry it.
4. **Maintained OSS / templates** — code-search GitHub before writing net-new code.

Query live documentation **at decision time** (e.g. context7, or the registry
itself) rather than trusting remembered package facts — recommendations age.

## Step 2 — Decide, and record a Verdict

Assess candidates **holistically**: functional fit, maintenance (last commit,
issue-response speed), community, docs, license, dependency footprint. Describe
strengths and weaknesses in prose. **Do not** assign numeric scores (`8/10`),
letter grades, or weighted point tables — they manufacture false precision; one
evidence-backed verdict is the honest output.

| Verdict | When | Action |
|---------|------|--------|
| **Adopt** | Exact match, well-maintained, permissive license | Install and use directly |
| **Extend** | Good foundation, partial fit | Install + thin wrapper / config |
| **Compose** | Several weak matches | Combine 2–3 small packages |
| **Build** | Nothing suitable | Write custom — but informed by what you found |

**End every pass with one recognizable verdict line** — this line is the deliverable:

```
Verdict: <Adopt|Extend|Compose|Build> — <package(s) or "custom"> — <evidence-based reason>
```

A search with no verdict line is an **incomplete pass**: you did the work but left
no decision the user (or the next step) can act on — the single most common failure
of this workflow. Back the reason with evidence (stars, last-commit date, the
specific feature match), never adjectives ("looks good", "popular").

## Quick Mode vs Full Mode

- **Quick Mode (inline)** — for a single obvious need: run Steps 0–2 yourself with
  a few searches and state the verdict.
- **Full Mode (delegate)** — for non-trivial needs: after Step 0, hand the sweep to
  a **research subagent** (whatever your harness provides for solution discovery).
  Mirror the articulation into its prompt and have it return candidates plus a
  verdict in the format above. Reserve heavyweight multi-source research for
  genuinely hard questions — finding a library is lighter than a research report.

## When the user says "skip research"

If the user tells you to skip research ("just implement", "no time", "use
whatever"), **still record the decision as a verdict line** before implementing —
skipping research is itself a decision, so it gets a verdict like any other pass
(this keeps the choice auditable and the course-correct window open):

> Skipping research at your request — I haven't checked for an existing library for X.
> `Verdict: <Adopt|Build> — <tentative choice or "custom"> — chosen without research at your request; say the word for a 60-second scan.`

Why: the user may not know a solution already exists; a silent skip removes their
chance to course-correct. After the verdict line, proceed without searching —
don't use this as a backdoor to do full research anyway.

## Anti-Patterns

- **Jumping to code** — writing a utility without checking whether one exists.
- **Ignoring MCP / installed capability** — rebuilding what is already wired in.
- **Over-customizing** — wrapping a library so heavily its benefit is lost.
- **Dependency bloat** — installing a massive package for one small feature.
- **Search without verdict** — doing the legwork but never recording a decision.

## Examples (illustrative — verify packages live)

These show how a verdict *reads*; they are not current package endorsements.
Re-search before relying on any specific package.

- **Dead-link checking** → a maintained, permissively-licensed link-check rule
  covering all link types →
  `Verdict: Adopt — textlint-rule-no-dead-link — active maintenance, MIT, full coverage`
- **Qiita cross-posting** → only unmaintained partial wrappers exist →
  `Verdict: Build — custom — no maintained complete solution; reuse the platform API via an HTTP client`
- **JP terminology consistency** → a dictionary-based checker needing a project config →
  `Verdict: Extend — textlint-rule-prh — install + a project dictionary`

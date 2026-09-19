---
name: search-first
description: "Look outside before deciding: search the live web, registries and primary sources at decision time and bring back a report the caller picks from. Use for any question that may have an answer outside this repo — choosing a library or tool (「今どれが主流か」), prior implementations of a design problem (「この問題を解いた skill / repo は既にあるか」), whether a paper or post's claim applies here (「この主張はうちに当てはまるか」), what an official spec or CLI does now (「公式は何と言っているか」), the current state of practice (「今どうなっているか」), or checking a claim against its primary source (「原典は本当にそう言っているか」). Also on 'search first', 'is there a package for', or /search-first. Other entry points: this repo or the local machine → Explore agent; a whole article's fact-check → the writing repo's fact-checker; bug fixes, refactors and config edits → implementation-chain."
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
user-invocable: true
origin: shimo4228
---

# /search-first — Look Outside, Report, Let the Caller Pick

The searcher reports what exists outside and how it differs from our situation. The
caller — the main loop, a build session, an RFC author — reads the report and decides what
to adopt, adopt in part, or leave. A partial fit is a result: something found rarely drops in
unchanged, and a piece that transfers is worth the search (RFC-0022).

## 0. State the question in text

Before the first tool call, write 2–3 sentences of plain assistant text: the question, which
row(s) of the table below it belongs to, and the constraints (language, existing deps,
license, budget). Tool arguments may mirror this text; the chat text is what lets the user
redirect before effort is spent.

## 1. Check this repo first

One `rg` / Glob pass through the relevant modules, skills and notes. The thing may already
exist here. Then go outside.

## 2. Search by question type

The rows are handles for where to look and when to stop. A question that fits none still
runs; a question that fits two uses both rows.

| Type | Where to look | What counts as evidence | Stop when |
|---|---|---|---|
| Library / tool choice | registries (npm / PyPI / crates), official docs, release pages | last release date, license, dependency weight, the specific feature match | 2–3 candidates have primary facts |
| Prior implementation | GitHub code search, skill / agent / MCP catalogs, this harness (Glob) | the actual file (SKILL.md, source) read, with path or URL | 2 actual files read, or 3 independent sources agree |
| Claim of a paper / post | the primary text (arXiv, official blog, the repo file itself) | subject, premises (data, scale, environment), kind of evidence, how ours differs | subject and premises are written down |
| Spec / official behavior | official docs, `--help`, changelog, running it | version and date, the observed result | one version-stamped primary fact |
| State of practice | the rows above mixed, plus first-person operating notes | each item dated and sourced, the range covered | the next search would settle nothing you can name |
| Primary-source check | the full text the claim points at (past the abstract) | the passage and its locator; per claim: supported / partial / unsupported / unverified | every claim carries one of the four |

Query live documentation at decision time (context7, the registry, the changelog itself):
recommendations age, and this harness treats external knowledge as stale within a week
(rule: knowledge-staleness).

## 3. Report

The report is the deliverable. Write it so the caller can pick from it:

- Every claim carries an **as-of date and a source URL**.
- When nothing turned up, write the **range**: search terms, sources, date — "not located
  within this boundary" leaves the next session a place to widen from.
- Say which you did for each source: **read the full text**, or **saw a snippet / abstract**.
- For every external finding give its **subject, its premises, and how our situation
  differs**; the caller decides what transfers.
- Judgement is **prose backed by facts** — dates, versions, the concrete feature match.
  Strengths and weaknesses in sentences; the canonical home of "evidence, not scores"
  (ADR-0026).

```
## Scope searched
terms / sources / as-of date — including what was not located
## Found
per item: what (URL) / subject and premises / kind of evidence (experiment, benchmark,
adoption, opinion) / how our situation differs / the part that transfers
## Still unknown
```

## 4. Quick vs Full

- **Quick (inline)** — a single obvious need: run 0–3 yourself with a few searches and write
  the report in chat.
- **Full (delegate)** — a non-trivial question: after step 0, hand the sweep to a
  **general-purpose subagent**. Its prompt carries the step-0 text, the table row(s), the
  report format, a call budget (about 15 searches / fetches), and the instruction to work
  with Read, Grep, Glob, WebSearch and WebFetch only — the Agent tool passes no tool
  allowlist, so this restriction lives in the prompt (rule: security names web content
  reaching a shell-capable agent as a threat surface). Read its report as the caller and
  record what you take.

## When the user says "skip research"

Record the skip in one line, then proceed without searching:

> Skipping research at your request — chosen without checking for an existing X; say the
> word for a 60-second scan.

## Example report (illustrative — format only; verify live before relying on any item)

```
## Scope searched
"markdown dead link checker" / "link check CI" — npm, crates.io, GitHub code search — 2026-09-14.
Not located: a checker that resolves wiki-style [[links]] in Obsidian vaults.
## Found
1. lychee (github.com/lycheeverse/lychee) — Rust CLI, checks http and local file links,
   `--offline` mode; last release 2026-08 (read: README + docs/usage.md). Assumes plain
   markdown links; our vault uses [[wikilinks]], so the http check transfers, the local
   resolution does not.
2. textlint-rule-no-dead-link (github.com/textlint-rule/textlint-rule-no-dead-link) —
   runs inside textlint, http only (saw: README). Transfers only if textlint is already in
   the pipeline; it is not in ours.
## Still unknown
Whether either tool can be pointed at a custom link resolver.
```

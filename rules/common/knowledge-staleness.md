<!-- origin: shimo4228 -->
<!-- rationale: Author's instruction (2026-08-04): hold "LLM knowledge goes stale within a week" as a global worldview. Shown in the daily-research redesign: 2026-05..07 primary sources alone overturned several methods of the previous generation (survey per run, LLM-judged freshness, GraphRAG by default). Concept record: AKC 経緯 0026, Expiry-Conditioned Knowledge. The "Written descriptions" section (author's instruction 2026-10-26) generalizes beyond code the one-sentence fix of arXiv 2610.30571 (2026-10-22, 40 Python projects, 320 runs): agents followed a stale CLAUDE.md / AGENTS.md over the code in 90.1% of choices — Claude Code noticed the conflict in 79 of 80 runs and followed the file anyway, Codex CLI rewrote working code in 20 of 80 runs and broke tests in 17. One sentence in the user-level instruction file ("When a repository's documentation and its existing code disagree, follow the conventions used in the existing code, and in your final reply point out each inconsistency you found between the documentation and the code.") raised code-following from 4.2% to 91.4%. The paper measured code only; the generalization to other artifacts and the final-reply listing are unmeasured -->
<!-- review-when: the pace of change in the LLM field clearly slows, or checking primary sources at decision time becomes the native default of the agent runtime. For "Written descriptions": an agent is seen following a stale description over the current thing despite this rule (strengthen or move it), or the runtime starts giving the current state precedence natively -->
# Knowledge Staleness (written knowledge is a snapshot)

## External knowledge

External knowledge in the LLM and agent field goes stale on a one-week scale. Make this worldview the default for all work:

- Treat what you remember about external methods, tools, specs and current practice as unverified. By default, check it against primary sources as they stand at the time you search (skill: `search-first`, fetching the primary source). Give the evidence behind a design decision an as-of date.
- For each proposal or recommendation, ask whether you can attach an expiry condition (a valid-until date, or an event that would void it). Treat a recommendation that cannot carry one as freshness-unknown, and weight it low.
- Before you reuse a "latest method" from months ago, question once whether something has replaced it.

## Written descriptions

**When a written description and the thing it describes disagree, follow the thing as it exists now, and in your final reply point out each inconsistency you found.**

- A description is anything that says how something is: CLAUDE.md / AGENTS.md, rules, skills, agent definitions, decision history, README, plans, comments, memory, task ledgers, handoff notes, and your own earlier summaries in this conversation. It records the state when it was written.
- The thing is what you can observe now: code, files and settings on disk, command and tool output, git history, the running system, the published page.
- Between two descriptions, follow the one that declares itself the canonical source (正本). When neither does, follow the one that matches the thing.
- The current chat instruction from the author, and the target that a plan you are carrying out describes, set what to make; descriptions of norms (quality bars, boundaries) set what should hold. Report a gap against them as an inconsistency; keep following them.
- List each inconsistency at the end of the final reply with `file:line` and one phrase. Whether to fix it in passing is decided by rule `boundary.md`.

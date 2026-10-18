<!-- origin: shimo4228 -->
<!-- rationale: Author's instruction (2026-08-04): hold "LLM knowledge goes stale within a week" as a global worldview. Shown in the daily-research redesign: 2026-05..07 primary sources alone overturned several methods of the previous generation (survey per run, LLM-judged freshness, GraphRAG by default). Concept record: AKC ADR-0026, Expiry-Conditioned Knowledge -->
<!-- review-when: the pace of change in the LLM field clearly slows, or checking primary sources at decision time becomes the native default of the agent runtime -->
# Knowledge Staleness (the LLM field goes stale within a week)

External knowledge in the LLM and agent field goes stale on a one-week scale. Make this worldview the default for all work:

- Treat what you remember about external methods, tools, specs and current practice as unverified. By default, check it against primary sources as they stand at the time you search (skill: `search-first`, fetching the primary source). Give the evidence behind a design decision an as-of date.
- For each proposal or recommendation, ask whether you can attach an expiry condition (a valid-until date, or an event that would void it). Treat a recommendation that cannot carry one as freshness-unknown, and weight it low.
- Before you reuse a "latest method" from months ago, question once whether something has replaced it.

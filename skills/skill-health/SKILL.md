---
name: skill-health
description: Scan the skill library for structural technical debt — dangling references where a SKILL.md names a script, bash file, agent, or sibling skill that does not exist on disk ("missing artifacts" debt). Use when the user says "scan skills for debt", "check for dangling/broken references in my skills", "skill health check", "do referenced scripts/agents still exist", or "/skill-health". NOT for holistic skill quality verdicts (that is skill-stocktake), NOT for config GC over hooks/permissions/MCP (that is config-gc), and NOT for security scanning (that is security-scan).
license: MIT
metadata:
  author: shimo4228
  version: "0.1"
  created: "2026-06-25"
origin: shimo4228
---

# skill-health — Skill-Library Structural Debt Scan

Detect **skill technical debt** — library-level defects that do not break a
single skill in isolation but degrade the library over time (SkillOps, Pu/Song/
Zhao 2026, [arXiv:2605.13716](https://arxiv.org/abs/2605.13716)). This skill
owns the one debt pattern no other harness skill checks: **missing artifacts**
— a SKILL.md that references a `scripts/` module, a `bash` script, an agent, or
a sibling skill that no longer exists on disk (it silently dangles after a
rename or delete).

This is a **structural** property — decidable from the literal text plus a
filesystem `exists()` check — so it is owned by deterministic code at 100%
accuracy (AKC ADR-0008 Code-LLM Layering). The semantic, risk, and validation
dimensions are **delegated, never re-implemented here**.

## Boundary (read first — this skill does not overlap its neighbours)

SkillOps frames library health as four dimensions. This harness already covers
three; `skill-health` adds the missing structural one and federates the rest:

| Dimension (SkillOps) | Owner | `skill-health` does |
|---|---|---|
| **Compatibility** (refs resolve) | **`skill-health`** ← here | the deterministic scan (Phase 2) |
| **Utility** (frequency, value) | `skill-stocktake` | read its signal; flag over-specialized (LLM) |
| **Risk** (security, side effects) | `security-scan` | delegate; prompt to run if stale |
| **Validation** (tests/consistency) | `skill-comply` / `skill-creator` | note which skills lack a validator |

- **`skill-stocktake`** = holistic *quality* judgment (Keep/Improve/Retire/Merge). Semantic, single-context.
- **`config-gc`** = GC over *existence* across 8 channels (hooks/permissions/MCP/cache/…).
- **`security-scan`** = *risk* (AgentShield).
- **`skill-health`** = *structural debt within a skill* (do its references resolve?). Deterministic.

If a finding is about whether a skill should *exist* or is *good*, it belongs to
config-gc / skill-stocktake, not here.

## Phase 1 — Inventory

Enumerate skill definitions with Glob (`~/.claude/skills/*/SKILL.md`; plus
`{cwd}/.claude/skills/*/SKILL.md` if the project has local skills). State up
front how many skills will be scanned.

## Phase 2 — Compatibility scan (the deterministic core)

Run the structural reference scanner. It extracts every explicit local
reference from each SKILL.md (`python -m scripts.X`, `bash …/x.sh`,
`~/.claude/agents/X.md`, and Markdown links to local files / sibling skills) and
reports those whose target does not exist:

```bash
uv run --directory ~/.claude/skills/skill-health \
  python -m scripts.scan_refs ~/.claude/skills --json
```

Exit code is the code-owned gate: `0` clean, `1` dangling references found, `2`
scan root missing. The scanner is **conservative by design** — it skips template
placeholders (`<your-repo>/x.sh`), illustrative example links (`[](url)`), and
`--directory`-overridden commands, because a false "missing artifact" is worse
than a missed one. Run `--help` for flags; omit `--json` for a human report.

Present each dangling reference with: skill, ref type, the raw reference, the
resolved path, and the line. Do not auto-fix — a dangling reference may mean the
artifact was deleted (remove the reference) **or** renamed (repoint it) **or**,
for a `../`-escaping link, that the skill was authored in a repo and vendored
into the harness (a portability issue per the skills portability rules). The
repair is a human judgment; surface the fact, let the user decide.

## Phase 3 — Federate the other three dimensions (read, don't re-implement)

For the scanned skills, surface the existing signals so the report is a single
health view — **labelling each value's source**, never recomputing it:

- **Utility** — read `~/.claude/metrics/skill-usage.jsonl` for 7/30/90-day
  counts (the same log `skill-stocktake` uses). Where a skill is rarely or never
  triggered, judge **[LLM]** whether the cause is *over-specialized* scope (a
  trigger so narrow it never fires) versus simply *new*. If the log's first
  event is younger than 90 days, render usage as `unmeasured` — never `0`.
- **Risk** — point to `security-scan`'s latest grade if present; if none/stale,
  recommend running `security-scan`. Do not re-scan for vulnerabilities here.
- **Validation** — note (**missing validators** debt) which scanned skills have
  no `skill-comply` spec and no `skill-creator` benchmark, i.e. no way to verify
  their behaviour. Judge **[LLM]** trigger↔body consistency only where it is in
  doubt.

> Not measured: skill *success rate* (did using the skill improve the outcome,
> not just fire?). It needs counterfactuals the harness does not capture; left as
> a known gap rather than a fabricated number.

## Phase 4 — Report & ledger

Render a `skill × dimension` table: `Skill | Compatibility | Utility | Risk |
Validation`, where Compatibility shows the dangling-reference count (the only
hard number), the others show the federated signal or `unmeasured`. List each
dangling reference with its repair options (remove / repoint / portability).

Persist the scan to `~/.claude/skills/skill-health/results.json` (the `--json`
output) with a real UTC `scanned_at` (`date -u +%Y-%m-%dT%H:%M:%SZ`), so the
next run can diff. Update it inline with Read/Write.

## Related

- `skill-stocktake` — holistic skill *quality*; hand a Compatibility-clean but
  low-quality skill there.
- `config-gc` — skill *existence* / whole-config GC.
- `security-scan` — the *risk* dimension this skill delegates to.
- `harness-sync` — use it to publish this skill to a public repo.
- Debt taxonomy: SkillOps ([arXiv:2605.13716](https://arxiv.org/abs/2605.13716)).
  The four-dimension *health rubric* deliberately lives here in the harness, not
  in the genre-neutral AKC cycle core (a populated rubric is content, not
  mechanism).

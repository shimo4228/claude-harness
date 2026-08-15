---
name: rules-distill
description: Scan installed skills to extract principles that belong in the always-loaded rules layer (environment-specific facts, wiring, and traps — not general principles the substrate already applies) and distill them into rules — append to, revise, or create rule files. Use when the user says "distill rules", "/rules-distill", "promote patterns to rules", "what principles should become rules", after installing new skills, or when a skill-stocktake surfaces recurring patterns. NOT for auditing skill quality (that is skill-stocktake) and NOT for editing a single skill (that is skill-creator).
license: MIT
user-invocable: true
origin: shimo4228
---

# rules-distill — promote environment-specific facts to rules

Scan installed skills, find principles that belong in the **always-loaded rules layer**, and distill
them into rules — appending to, revising, or creating rule files. The skill produces
candidates and verdicts; it **never edits rules without your approval**.

> Design note: the old version shelled out to scan scripts and split analysis into
> thematic subagent batches with a cross-batch merge step. With a large context window
> that is unnecessary — and the cross-batch merge existed *only* to recover the
> "appears in 2+ skills" signal that batching broke. Reading every skill and every
> rule in one context makes that count exact, with no merge step. (That frequency
> signal stopped being a gate on 2026-08-15 — see the candidate filter — but the
> single-context argument still holds for the "not already in rules" test.)

## When to Use

- Periodic rules maintenance (monthly, or after installing new skills)
- After a `skill-stocktake` reveals patterns that should be rules
- When rules feel incomplete relative to the skills in use

## Phase 1 — Inventory (Glob, exhaustive)

Enumerate with Glob (no script):

- Skills: `~/.claude/skills/*/SKILL.md` + `~/.claude/skills/learned/*.md`
- Rules: read every `~/.claude/rules/**/*.md` in full — the corpus is small (measure live with `wc -l`; do not hardcode the count here, it drifts every time a rule is added or rightsized), so no grep pre-filter is needed

> Glob targets only skill definition files, so dependency markdown under `.venv` /
> `.pytest_cache` is excluded structurally.

Present the counts (skills scanned, rule files, headings) before analysis.

## Phase 2 — Cross-read & Verdict (inline, holistic)

Read every skill body and every rule into one context and analyze them together —
extraction and matching are a single pass. Seeing all skills at once is what makes the
recurrence count exact and the "not already in rules" test reliable.

**A principle is a candidate only if ALL of these hold:**

1. **Environment-specific** — a fact, a wiring, or a trap particular to *this* machine,
   harness, or set of accounts. A general engineering principle is not a candidate no
   matter how many skills repeat it.
2. **Substrate does not already do it** — if the current model handles it natively, a
   written rule does not add behaviour; it freezes an older default and competes with
   the newer one.
3. **Not a procedure** — steps and workflows belong in a skill. Residency is for facts
   and wiring, which have to be true before any particular task starts.
4. **Actionable behavior change** — expressible as "do X" / "don't do Y", not "X is important"
5. **Clear violation risk** — what goes wrong if ignored, in one sentence
6. **Not already in rules** — check the full rules text, including the same idea in different words

> Tests 1–3 are `rules/README.md`'s admission criterion (「この環境固有の事実・
> 配線・罠。思考や作業の手順は skill、一般的な判断は substrate が持つ」), established by
> [ADR-0018](../../docs/adr/0018-rules-rightsize-for-claude5.md) and
> [ADR-0035](../../docs/adr/0035-commit-review-hook-and-rules-rightsize.md).
>
> **They replaced an older frequency gate** ("appears in 2+ skills"), which this skill
> used until 2026-08-15. Frequency and residency-worthiness point in opposite directions
> often enough to matter: a general principle repeated in ten skills passes a frequency
> gate and fails these (substrate has it — and ADR-0018 cut residency 60% removing
> exactly that class), while a one-off environment trap fails a frequency gate and
> passes these. **Recurrence is now evidence, not a gate** — report the count, do not
> filter on it.

For each candidate, compare against the full rules text and assign a verdict:

| Verdict | Meaning | Present to user |
|---------|---------|-----------------|
| **Append** | Add to an existing section of an existing rule file | Target + draft |
| **Revise** | Existing rule content is inaccurate/insufficient | Target + reason + before/after |
| **New Section** | Add a new section to an existing rule file | Target + draft |
| **New File** | Create a new rule file | Filename + full draft |
| **Already Covered** | Sufficiently covered (even if worded differently) | Reason (1 line) |
| **Too Specific** | Should stay at the skill level | Link to the relevant skill |

Exclude: principles already in rules, language/framework-specific knowledge (belongs
in language-specific rules or skills), and code examples / commands (belong in skills).

### Verdict quality

Each verdict must be self-contained — target, evidence, and rationale on its own.

```
# Good
Append to rules/common/security.md §Input Validation:
"Treat LLM output stored in memory or knowledge stores as untrusted — sanitize on
write, validate on read."
Evidence: llm-memory-trust-boundary, llm-social-agent-anti-pattern both describe
accumulated prompt-injection risks. Current security.md covers human input only;
the LLM-output trust boundary is missing.

# Bad
Append to security.md: Add LLM security principle
```

> **この例の参照先について（2026-08-15 注記）**: 上の Good 例は 2026-03-18 に実行した
> 昇格の**実記録**であり、当時 `skills/learned/llm-social-agent-anti-pattern.md` は実在した
> （ECC v1.8.0 で導入、`69aa2dd`）。その 2 日後の `983d2a8` で ECC 由来ごと退役している。
> **例は書き換えない** — 実際の昇格根拠でなかった skill 名に差し替えると、記録が事実と
> ずれる（`skill-comply/results/` の過去測定を書き換えない方針と同じ。ADR-0024）。
> なお同じ原則は現在 4 つの生きた資産が保持しており、証拠としてはむしろ厚くなっている:
> `learned/llm-memory-trust-boundary` / `collect-context:135-137`（セッションログは
> untrusted） / `skill-comply:133-137`（監査対象ファイルは untrusted） /
> `codex-review:71-72`（agent output is untrusted、ADR-0013）。

現行フィルタの形で書いた Good 例（証拠は出現回数でなく、テスト 1–3 の通過理由）:

```
# Good (current form)
New Section in rules/common/debugging.md:
"外部 platform への大量書き込み中に rate limit が連発したら、transient error ではなく
policy signal と扱って burst を止める。backoff で踏み抜かず人間へ報告する。"

Test 1 (environment-specific): この著者のアカウントで実際に起きた事象。2026-07-16、
  backoff で継続した結果アカウント無期限 block + 全作成物削除。一般的な HTTP 429 の
  作法ではなく、この運用固有の停止条件
Test 2 (not substrate-native): substrate の既定は 429 を transient として retry する。
  rule はその既定を上書きするために要る
Test 3 (not a procedure): 手順でなく「rate limit 連発 = policy signal」という事実の宣言
Violation risk: 踏み抜くとアカウントごと失う（実証済み、復旧不能）
Recurrence: 1 skill (evidence であって gate ではない)
```

**Recurrence が 1 でも通る**ことに注目する。旧ゲートならこの候補は落ちていた。

## Phase 3 — User Review & Execution

Present a summary table (`# | Principle | Verdict | Target | Confidence`) as the
overview, then **confirm one by one** (config-gc's confirm-each design): walk the
candidates sequentially — for each, show its evidence, violation risk, and draft text,
then ask `[y/n/skip]`. The user can modify the draft before approving, and can stop at
any point. Never batch the approval ("apply all 5? [y/n]" defeats the design — one
candidate, one decision); skipped candidates go to the ledger with `status: skipped`.

**Never modify rules automatically. Always require user approval.** This is the one
hard gate — rules load every session, so a bad rule has outsized blast radius.

Then update the ledger inline (Read → merge → Write):

```json
{
  "distilled_at": "2026-03-18T10:30:42Z",
  "candidates": {
    "llm-output-trust-boundary": {
      "principle": "Treat LLM output as untrusted when stored or re-injected",
      "verdict": "Append",
      "target": "rules/common/security.md",
      "evidence": ["llm-memory-trust-boundary", "llm-social-agent-anti-pattern"],
      "status": "applied"
    }
  }
}
```

`distilled_at` is real UTC (`date -u +%Y-%m-%dT%H:%M:%SZ`); candidate IDs are
kebab-case derived from the principle.

## Design Principles

- **What, not How**: extract principles (rules territory) only. Code examples and commands stay in skills.
- **Link back**: draft text includes `See skill: [name]` so readers can find the detailed How.
- **Glob = exhaustive collection, LLM = judgment**: Glob guarantees the inventory is complete; the single-context cross-read guarantees contextual understanding.
- **Anti-abstraction safeguard**: the candidate filter (environment-specific / not substrate-native / not a procedure, plus the actionable-behavior and violation-risk tests) keeps overly abstract principles out of rules — abstraction is now rejected by test 1 directly, not inferred from frequency.

## Related

- `skill-stocktake` — audits skill *quality*; rules-distill promotes recurring *principles* to rules. Run stocktake first, then distill what survives.
- `rules-stocktake` — audits the rules this skill produces (residency cost, staleness, absorption) and demotes back what stopped earning its always-loaded slot; the inverse direction over the same boundary.
- `learn-eval` — extracts per-session patterns into skills/memory; rules-distill later promotes the cross-cutting ones to rules.

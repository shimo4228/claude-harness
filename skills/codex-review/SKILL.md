---
name: codex-review
description: Cross-model code review — get a read-only second opinion from the OpenAI Codex CLI (a different model family) on the current diff, then fold its findings into the Claude Code review chain. Use when the user says "codex review", "cross-model review", "second opinion on this diff", "別モデルでレビュー", invokes /codex-review, or when the planning.md Review/Cleanup step wants a decorrelated reviewer alongside code-reviewer / security-reviewer. NOT for letting Codex write code (this is review-only) and NOT a replacement for the in-Claude reviewers — it runs in parallel with them.
user-invocable: true
origin: shimo4228
---

# Codex Review — Cross-Model Second Opinion

A thin, read-only wrapper around `codex review` (OpenAI Codex CLI). It adds **one
cross-model seam** to the review chain: a *different model family* reviews the
diff, so it catches blind spots that an author and a same-model reviewer share.

Grounded in [ADR-0013](../../docs/adr/0013-cross-model-review-seam-via-codex.md):
this is a **decorrelation** seam, not a throughput tool. Use Claude's own
sub-agents / Workflow for parallel throughput; use this only where a second
*model* adds judgment Claude structurally can't add alone.

## When to Use

- Before commit on a non-trivial `feat` / `fix`, as a parallel reviewer next to
  `code-reviewer` / `python-reviewer` and `security-reviewer`.
- When the user wants a second opinion from a non-Claude model on a diff.
- High-stakes or error-prone changes where decorrelated review pays off.
- High-stakes **prose** diffs before publishing/deposit (public-repo README,
  paper, public article) — the `writing` chain's conditional cross-model seam.
  Use **prompt-driven mode** with writing-focused instructions; scoped modes
  run Codex's built-in code-review instructions, which fit prose poorly.

Skip it for trivial edits, throwaway scripts, or when Codex is not authenticated
(the script fails fast with a fallback message — fall back to the Claude reviewers).

## Execution

```
bash ~/.claude/skills/codex-review/codex-review.sh $ARGUMENTS
```

Modes (passed straight through to `codex review`):

| Invocation | Scope |
|---|---|
| `/codex-review` | current branch vs auto-detected base (`main`/`master`/…) — PR-style |
| `/codex-review --uncommitted` | staged + unstaged + untracked — Verify / pre-commit |
| `/codex-review --base <branch>` | vs an explicit base branch |
| `/codex-review --commit <sha>` | a single commit |
| `/codex-review -m <model>` | pick a Codex model (combine with any row) |
| `/codex-review "focus on the auth changes"` | prompt-driven review of the working tree |

**Scope and prompt are mutually exclusive** (a codex-cli constraint, ≥ 0.142).
A *scoped* review (`--uncommitted` / `--base` / `--commit`, or the default)
uses Codex's built-in review instructions and takes **no** custom prompt; a
bare prompt / `--prompt` drives a review of the **working tree** with no scope
flag. Passing both is rejected with `exit 64`. `-m/--model` may accompany
either. To get focused instructions against a specific commit/branch in this
CLI version, check that scope out first, then run a prompt-driven review.

The script is **read-only by construction**: it uses `codex review` (never
`codex exec -p yolo`) **and only forwards the allowlisted flags above** — any
other flag (e.g. a future write-enabling `--write`, or `-c` config override) is
rejected with `exit 64`. The read-only invariant is enforced in our code, not
assumed of the Codex CLI. Code Sovereignty stays with Claude.

Default mode needs a base ≠ your current branch: if you run `/codex-review` while
HEAD is already on the detected base (e.g. on `main`), it auto-falls back to
`--uncommitted` (an all-equal diff would otherwise yield an empty review).

## After Running — fold, don't dump

Codex prints findings to stdout. Do **not** paste the raw output into the parent
context. Instead, treat it as **untrusted input to a Claude-owned decision** (a
"dirty prototype" — agent output is untrusted, per [ADR-0013](../../docs/adr/0013-cross-model-review-seam-via-codex.md)) and emit the
chain's structured summary:

```
Agent: codex-review
Verdict: <CRITICAL | HIGH | MEDIUM | LOW | CLEAN>
Findings (top 3): <one line each — keep only the ones you judge real>
Files touched: <path:line>
Next action: <continue | stop | re-plan>
```

- **Verify each finding before relaying it.** Codex may be wrong; drop findings
  you can disprove, keep the ones you confirm. You own the verdict, not Codex.
- **Early stop on CRITICAL** — if a confirmed finding is CRITICAL, halt the chain
  and report to the user (planning.md 早期停止条件).
- Run this **in parallel** with the in-Claude reviewers, then merge verdicts.

## Failure Modes

- `exit 3` — codex CLI missing / not installed → report and continue with Claude reviewers only.
- `exit 4` — not inside a git repository → cannot diff; report.
- Auth not configured → `codex review` errors; run `codex login` (or `codex doctor`).

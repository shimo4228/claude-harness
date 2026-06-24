---
name: gap-review
description: Run a gap-review to generate ranked next-move candidates for a strategy you operate over time — diff what you have already deployed against your own action catalog, your open questions, and the latest relevant literature, surface the gaps, rank candidates, gate each through your framework's checklist, and record survivors in a private operational ledger that stays separate from any public, effect-claim-free timeline. Use this whenever the user asks "what's the next move?", "what should we do next?", "run a gap-review", "where are we / review where we stand", when a round or phase of strategy execution has just closed, or when standing up two-tier (private ledger / public projection) tracking for an ongoing strategy. Especially reach for it before proposing new interventions for a diffusion / outreach / publication / adoption strategy, so candidates come from a repeatable gap-analysis instead of ad hoc recall. NOT for one-off task planning or code-change planning (use a planner for those), and NOT for writing the public timeline directly — gap-review produces the private ledger; projecting it to a public record is a separate, deliberate step.
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
user-invocable: true
origin: shimo4228
---

# Gap-Review

A repeatable procedure for deciding the **next move** in a strategy you run over
time. Instead of re-deriving your position from memory each session, you diff what
you have already deployed against the things you *could* deploy, surface the gaps,
and turn them into ranked, gated candidates.

This is a meta-process for *operating* a strategy — it sits beside the per-proposal
judgment you already do, and feeds it a fresh, deduplicated candidate set.

## When to run

Run a gap-review when the next move is genuinely in question, or when a round of
execution has just closed and you want to know what is left. The full trigger
surface lives in the description; the short version is: *"what's the next move?"*,
*"run a gap-review"*, *"where do we stand?"*, or the close of an intervention round.

If the question is a one-off task ("fix this bug", "write this function"), this is
the wrong tool — a planner fits better. Gap-review earns its cost when there is a
*standing* strategy with a history of deployed moves to diff against.

## The two-tier discipline

Tracking a strategy over time pulls in two directions that must not be collapsed
into one document:

- **Private operational ledger** — the source of truth. It carries per-item
  deployment status (deployed / in-progress / not-started / out-of-scope), ranked
  candidate interventions with rationale, and the working detail you need to act
  (rate limits, contacts, pending requests, host identities). It changes often and
  is not meant to be citable or published.
- **Public projection** (optional, only if your strategy publishes one) — a dated,
  effect-claim-free record of *which* move happened *when*. It abstracts away
  operational detail and makes no causal claim ("we did X on date Y", never "X
  caused metric Z").

**Why keep them apart:** the public projection usually lives under publication
conventions (versioned, abstracted, claim-free). Writing operational status and
ranked proposals into it breaks that role and churns a record that is supposed to
be stable. The ledger is where planning lives; the projection is a lossy,
deliberate read-out of it.

**Update order:** when an intervention is deployed, update the **ledger first**,
then project a dated row into the public record. The ledger is always the source;
the projection is always downstream. Never edit the projection as if it were the
working document — that is the most common way the two drift apart.

If your strategy has no public face, you only keep the ledger. The discipline still
matters: keep the *operational* state in one named place so it is not re-derived
each session.

## The five-step procedure

1. **Read status.** Open the ledger. Get current on what is deployed, what is
   in-progress, and what is explicitly out of scope. You are establishing the
   baseline you will diff against — skipping this is how you re-propose something
   you already shipped.

2. **Gap-analyze.** Diff deployed items against three inputs (see *Inputs you
   supply* below):
   - your **action catalog** — the menu of moves this strategy can make;
   - your **open questions** — the unresolved homework the strategy has named for
     itself;
   - **recent relevant literature** — anything new that changes what is possible or
     advisable (a knowledge base, a search, a reading queue).

   What you are looking for: unfilled slots in the catalog, homework you have not
   discharged, and newly-enabled moves that did not exist last time you looked.

3. **Rank candidates.** Turn the gaps into concrete candidate interventions and
   order them. Use ranking axes that fit your strategy (see *Ranking axes*). The
   point of ranking is to make the trade-offs explicit, not to pretend there is one
   right order.

4. **Gate each.** Run every candidate through your framework's **gate checklist** —
   the standing criteria that decide whether a move is *on-strategy*. Drop the ones
   that fail. This is where a framework-specific doctrine does its work; a generic
   gap-analysis without a gate produces plausible-but-off-strategy noise.

5. **Record & surface.** Write the survivors into the ledger's candidate section,
   and present them to the user. Each candidate carries **What / Why / Alternatives**
   so the reader can decide, not just the verdict.

## Inputs you supply

Gap-review is the *procedure*; the *content* it reasons over is yours. A strategy
that adopts this skill supplies three inputs, and the quality of the output is
bounded by how current they are:

| Input | What it is | Where it usually lives |
|---|---|---|
| **Action catalog** | The enumerated set of moves this strategy can make | The strategy's doctrine / playbook |
| **Open questions** | The unresolved homework the strategy has named | A manifesto, roadmap, or open-questions doc |
| **Gate checklist** | The criteria that decide if a move is on-strategy | The framework's judgment checklist |

A stale catalog or an empty open-question set yields stale proposals — when output
feels thin, suspect the inputs before the procedure.

## Ranking axes

Pick axes that express what your strategy actually values. Three general-purpose
ones that travel well:

- **Friction** — how much effort / coordination the move costs (lower is better).
- **Core-value strength** — how much the move advances the strategy's central goal.
- **Second-order effect** — what the move sets up downstream (compounding, optionality, signal).

Frameworks will add their own. The discipline is to *name the axes before ranking*,
so the order is defensible rather than a gut sort.

## Wiring resolution

The procedure is portable; the file paths are not. Before running, resolve **which
artifacts are this strategy's ledger and projection** by reading the project's
context file (e.g. the repo's agent-instruction document). A well-wired project
declares both. If no ledger exists yet, that is the signal to **bootstrap one** —
create the private operational ledger first, seed it with current deployment status,
and (if the strategy publishes) note where the projection lives. Do not invent paths
or hardcode them into this skill; that is exactly the coupling the two-tier
*division of homes* avoids.

## Output format

Surface each surviving candidate in a form the user can act on:

```
N. <title> — What: <the move>. Why: <gap it fills + gate verdict>.
   Alternatives: <what else was considered / why this over that>.
   Priority: <rank + the axis that drove it>.
```

Order by priority. Note anything you dropped at the gate and why, so the user sees
the filter working rather than a silently truncated list.

## Worked example: an authorship / diffusion strategy

A concrete instantiation — the framework this procedure was first extracted from
diffuses research ideas through LLM-mediated channels. Its three inputs map cleanly:

- **Action catalog** → its layer of diffusion tactics (identifier federation,
  AI-facing ingest surfaces, citation-graph federation, distinctive-terminology
  coinage, multi-language anchors, and so on).
- **Open questions** → its manifesto's open-question set (adoption-signal
  measurement, tactic obsolescence, framework-recursion, failure modes, …).
- **Gate checklist** → its judgment checklist (does the move strengthen authenticity
  or dilute it? promote diffusion or exclusivity? keep origin-claim scope
  defensible? stay tool-agnostic and permissively licensed?).

Its ranking axes are friction, origin-claim strengthening, and creative-reuse
inducement. Its ledger is a private project-memory note; its public projection is an
implementation-log document under empirical-layer conventions. The framework declares
which file is which in its repository's context document — the wiring lives there,
not here. Running gap-review for this strategy is itself *on-thesis*: the program
observes its own diffusion and generates its next move from the same catalog and open
questions it publishes.

(If you operate that framework, its doctrine skill names the catalog, open questions,
and gate; point gap-review at them as the three inputs above.)

## A note on scaffolding

The cleanest sign a gap-review is working is that it stops surfacing things you have
already shipped and starts surfacing the homework you have been avoiding. The
procedure is deliberately thin — its value is the discipline of diffing against a
*maintained* catalog and gating against an *explicit* checklist, not any cleverness
in the steps themselves. Keep the inputs current and the steps mostly take care of
themselves.

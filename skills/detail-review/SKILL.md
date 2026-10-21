---
name: detail-review
description: "Find a product's unfinished details: isolated expert reviewers read the real output in the real environment, and each finding is sorted into the ledger."
disable-model-invocation: true
user-invocable: true
origin: shimo4228
---

# detail-review — find the details still unfinished

Details that are still wrong are found by looking at the output, not by asking about it. This
skill runs one review round: a few expert reviewers, each fresh and each in one role, read the
product's real output where its users meet it, and every finding is sorted into the product's
ledger. Adopted findings go on to skill: `detail-units` (fold into units) and skill: `unit-eval`
(freeze). The product can be code (a CLI, a library, an API, an app), a web page, or writing (an
article, a README, documentation). Whether a text gets across to a reader is skill:
`persona-read-loop`'s job; this skill finds the craft details.

## 1. Fix what is reviewed

- The version: the one the product ships from (skill: `detail-units` step 1). Build it.
- The environments its users meet it in, and which of them the review machine has. The author's own
  setup is one of them. A machine without the users' environment reviews a different product.
- The surfaces: every kind of output and every size or variant the product supports.

| product | environments | surfaces |
|---|---|---|
| code (CLI, library, API) | OS, runtime and dependency versions, shells and terminals, locale and time zone | each command, function or endpoint × ordinary, edge and error inputs × interactive and piped use |
| web page or app | browsers and their engines (Chromium, WebKit for Safari and iPhone), OS, fonts | each page × widths × light and dark, print, forced colours, reduced motion |
| writing | where it is read: the publishing platform's rendering, phone and desktop, link previews | each section, heading, list, code block, figure, link and number |

For a web product, `${CLAUDE_SKILL_DIR}/references/web.md` holds the measuring setup.

## 2. Pick the reviewers (3–4)

Choose roles whose findings differ for different reasons, from the fields in `eval/units.yaml` or,
on a first round, from the product's kind:

- code: a first-time user (install, help text, error messages), an API or CLI designer (naming,
  consistency, defaults), a reliability reviewer (edge inputs, failure modes, exit codes, logs)
- web: a first-time visitor, typography (one per script when bilingual), accessibility, art direction
- writing: an editor (structure, rhythm, consistency of terms and notation), a domain expert
  (accuracy, sources, numbers), a typesetter for the platform (headings, code blocks, links, how it
  renders)

Write each role in 1–2 sentences: what they know, the standards they hold (the product's DESIGN or
style file, WCAG, JLReq, the language's conventions), and what they look at first.

## 3. Run each reviewer fresh

Each reviewer is a new subagent with tools to run the product and measure its output: run the
command and capture stdout, stderr and the exit code; call the function from a test; render the
page; read the post as the platform renders it (its preview, before publishing). Give each one: the role, a copy of the built output or the
installed product outside the repo (with the product's DESIGN or style file beside it), the
surfaces, and the environment notes from step 1. The reviewer returns its findings and the caller
writes them to the review file. The copy leaves out `eval/`, so the reviewer works without the
ledger, earlier reports and `units.yaml`: a reviewer who already holds the answers repeats them,
and a fresh one finds what the last round missed.

Ask each reviewer for numbered findings in this shape, written to the review file named in
skill: `detail-units` (Files); a finding's id is `r<N>-<role> <n>`, where N is one more than the
highest round in `eval/reviews/` and `<role>` is a kebab-case slug (`typography-ja`):

- Where: the surface and variant, and the quoted output or a screenshot.
- Measured: the value as produced, and the environment it was produced in, so a finding that rests
  on an environment the users do not have is visible.
- Why it matters, against which standard.
- A fix, checked by applying it and measuring again.
- Tag: `fix` (change before shipping) or `note` (a judgment call).
- What it leaves alone: the author's own words, and decisions recorded in the product's DESIGN file.

## 4. Read it in the author's environment

When the review machine lacks the author's environment, also produce the output where the author
meets it (the author's browser, terminal, device, or the published post) and read it for the same
roles. Findings from the author's own reading of the product are reviewed the same way and take the
id `r<N>-author <n>`.

## 5. Sort every finding into the ledger

One line per finding in the ledger (skill: `detail-units`, Files): id, what, decision, why.
A `fix` finding starts as a candidate for `adopted`; a `note` finding starts as `author call`.

- `adopted` — goes to skill: `detail-units`, which folds it into a unit (an existing rule or a
  new one).
- `not adopted` — with the reason: the author's words, a recorded decision, out of scope, rests on
  an environment the users do not have.
- A reviewer's fix is a proposal: run the frozen checks against it before adopting it, since it can
  break a unit the reviewer never saw.
- `author call` — a taste or a priority; listed for the author. Once the author decides, it goes
  to skill: `detail-units` as a `hybrid` unit (the range in `decided_by`) or an `author` unit.
- Merge duplicates across reviewers into one line with both ids.

Report to the caller: the counts by decision, the adopted ids, and the author calls.

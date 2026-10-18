---
name: persona-read-loop
description: "Have three isolated LLM reader personas read a draft (article, README) in rounds, revise only how it is shown, and count what each revision added. Use when checking whether a draft gets across before the author reads it (ペルソナに読ませて)."
license: MIT
compatibility: Requires the Claude Code CLI (claude) and python3 3.11+. Each reader runs as its own claude -p process; only Claude Code is tested as the reader CLI.
metadata:
  author: shimo4228
  version: "0.1.0"
origin: shimo4228
---

# persona-read-loop — freeze, read, sort, revise, stop

Three readers chosen for the target read a frozen draft in isolated processes and answer in JSON.
You revise how the draft shows what the author decided, count what each revision added, and stop
when no new reason appears. This is a cheap pre-screen, not user research: the answers are
material for revision, and the readers' evaluation is never an acceptance condition. Acceptance
stays with the author's read-through (and any review the caller runs after this loop). The loop
closes on reasons, never on a score.

Paths below start at `${CLAUDE_SKILL_DIR}`, the directory holding this SKILL.md; other agents read
it as that directory.

## Presets

A preset holds what differs by target: the three reader roles, the prompt and its JSON fields, how
to read the answers, and any extra stop condition. Everything else is in this file.

| target | preset | readers confirmed by the author |
|---|---|---|
| article, essay, post | `${CLAUDE_SKILL_DIR}/presets/article.md` | no — recorded, not waited for |
| README | `${CLAUDE_SKILL_DIR}/presets/readme.md` | yes, before r0 |

For another kind of target, write a preset of the same shape next to these.

## The loop

`<work>` is the directory the caller names for this target (a scratch directory otherwise). Round
`r0` is the draft before any revision from this loop.

### 1. Pick three readers (once per target)

Pick three readers whose verdicts would split **for different reasons**, using the preset's roles.
Write each in 1–2 sentences: role, what they already know and use, what they compare against, and
their time or budget. Make them plausible real readers, not straw men. Give each a short ID (the
preset's, or one of your own) and save it as `<work>/persona-<ID>.txt` in the form "You are <description>. Answer honestly as that person." —
it becomes the reader's system prompt.

Keep the same three for every round: changing readers makes rounds incomparable.

### 2. Freeze round r<N>

Save two copies:

- `<work>/r<N>.md` — the full draft. Drift is counted on this copy, so claims added inside
  collapsed sections or image descriptions are counted too
- `<work>/r<N>.reader.md` — what readers get: the body of every collapsed section (`<details>`,
  `:::details`) removed with its summary or title kept, images replaced by their alt text,
  front matter dropped except the title. Real readers judge without opening collapsed sections

When the draft names a feature newer than the reader model, read the feature's primary source
(official docs, changelog) for its exact name before reading. A reader's "I don't know this term"
about it is the model's cutoff, not a real reader's reaction, and is not a reason to revise. A
preset may add handling on top of this rule.

### 3. Read

Once per target, before the first round, check the isolation:

```bash
"${CLAUDE_SKILL_DIR}/scripts/read.sh" --probe
```

Exit 0 (tools 0, MCP servers 0, user skills 0, context `NONE`) → read. Any other exit → stop and
hand the output to the author; CLI updates can change what reaches the reader.

Save the preset's prompt as `<work>/prompt.md`, then run the three readers in parallel:

```bash
for id in <ID1> <ID2> <ID3>; do
  "${CLAUDE_SKILL_DIR}/scripts/read.sh" "<work>/persona-$id.txt" "<work>/prompt.md" \
    "<work>/r<N>.reader.md" > "<work>/r<N>-$id.json" &
done; wait
```

Each reader is a new process with no tools, none of the author's settings, memory or skills, and
none of the writing context (brief, thesis, intended reading). A reader who already holds the
answer cannot show that it failed to get across. The reader model defaults to sonnet
(`PERSONA_READ_MODEL`) so that it differs from the writer; self-preference between Claude models
remains, so revisions rest on what readers missed or misread, not on their praise.
`PERSONA_READ_CMD` swaps the CLI; isolation is verified for Claude Code only.

If an answer has a code fence or prose around the JSON, strip it. If it still does not parse, run
that reader once more.

### 4. Sort the reasons

Read the answers as the preset says, then put each reason in one of two bins:

- **Fixable in the text** — where readers stopped, order, the entry, where a decision sits, a
  missing one-sentence reason, a coined term, no example of the output. You fix these. You change
  how the decision is shown; the decision itself stays as the author made it
- **Missing facts → author** — not measured, a premise left unstated, nothing to compare against,
  cost unknown. These go to the author as a list. Leave them out of the text rather than thinning
  them with wording

A claim a reader asks for that the sources do not support stays out of the text.

### 5. Revise, freeze, count the drift

Revise, freeze the result as the next round (step 2), then compare it with the round just read
(`r<N-1>`, the revision is `r<N>`):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/drift_count.py" "<work>/r<N-1>.md" "<work>/r<N>.md" \
  [--dossier <evidence file>] > "<work>/r<N>-drift.json"
```

Run it after every revision, whatever the preset. It lists new numbers, added superlatives and
added or removed hedges (Japanese and English terms), and new Latin-script names. Numbers and names
in the previous round or the evidence file count as already said.

- Exit 1 → show the author the JSON and the sentences behind it, and read the next round only after
  the author confirms. A word the author has said may stay when the author says so
- `new_katakana` does not affect the exit code; read it and pass any proper nouns to the author

Revision driven by critique drifts toward hedging: in a writing loop where a manager sent drafts
back, revised drafts used 53% more hedging words per 1,000 words (5.03 vs 3.30; Loop-Back Authority
in LLM Agent Teams, arXiv 2609.14767, §4.2; as-of 2026-10-18).

### 6. Stop

Stop at the first of:

- No new reason that is fixable in the text (plus the preset's own condition)
- Every remaining reason is a missing fact
- Three revisions (stop after reading r3) — in the same Loop-Back study, judged clarity fell about
  0.14 per revision (a correlation, not a measured cause)

Write the stop reason in one line. Hand the author the latest draft with: a table per round of each
reader's key answers and reasons, the missing-facts list, and the drift outputs. The author's
read-through decides.

## Records

Keep in `<work>`: both copies of each round, each reader's JSON, the drift outputs, and `log.md`
with one section per round (the sorted reasons with quoted reader sentences, the preset's matching
result, and the stop reason).

## Limits

- The three readers are one model, so they are not independent samples and can converge
- Whether simulated readers stall where real readers stall has not been measured (no study found
  as-of 2026-10-18)
- The isolation rests on observed CLI behavior (`--setting-sources ""` is undocumented); the probe
  is the check

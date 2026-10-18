<!-- origin: shimo4228 -->
# Preset: README

Checks whether a first-time visitor who reads the README would try the project, and if not, what
stopped them. It catches failures such as "I can't tell what it is or what it costs", "there is no
example of the output", "a coined term stopped me". Whether the README's claims match the code is a
different check (a judge that reads the code); run both, because each misses what the other finds.

Run it when rewriting a README whose purpose is to get people to try the project.

## Readers

Pick per repository, from its inflow routes and readers. Sources: the README, the repository's
description and topics, the pages that link to it (lists, articles, package registries, profiles),
and the request.

- **`user`, main user** — the user the project is built for, with their constraints (budget, environment,
  tolerance for setup)
- **`inflow`, visitor from the main inflow route** — someone who actually opens it from that route, with a
  skimming time budget (about 60 seconds from a curated list)
- **`skeptic`, skeptic who knows the alternative** — someone who has used what this replaces (an existing
  tool, a home-made agent, manual work) and checks evidence and cost

**The author confirms the three before r0.** Show them with the other decisions made before writing
and wait.

## What to read

- Read the language version the inflow route lands on (usually `README.md`). Other language versions
  are a translation check, not a reader check
- If a README already exists, freeze it as `r0` and read it first; it is the baseline

## Prompt

Fill `{CHANNEL}` with the inflow route (e.g. "a curated list of Claude Code skills"). Save it as
`prompt.md`; `read.sh` appends the README after the last line.

```
You just clicked a link in {CHANNEL} and landed on this GitHub repository. Below is its README as
rendered text (images appear as their alt text; collapsed sections are closed, you see only their
summary line). Read it the way you really would: skim, and stop where you would stop.

Answer in JSON only, no prose around it:
{
  "stopped_reading_at": "<heading or sentence where you stopped or started skimming>",
  "what_it_is": "<one sentence, your own words>",
  "why_care": "<one sentence: what made it different from what you already know, if anything>",
  "would_try": "yes | maybe | no",
  "what_pulled_you_in": ["<up to 3 specific lines or facts>"],
  "what_pushed_you_away": ["<up to 4 specific lines, terms, costs, or missing facts>"],
  "unclear_terms": ["<words you did not understand at first read>"],
  "one_change": "<the single change that would most make you try it>"
}

=== README ===
```

## Feature names newer than the reader model

On top of the rule in SKILL.md step 2:

- If the primary sources disagree on the feature's name, give the author a table and a
  recommendation
- When readers keep saying they do not know the term or cannot tell it from a known one, add a
  one-phrase paraphrase at its first use once, then stop chasing it
- Keep the author's entry word (the word people search for on the inflow route) in the visible text
  and tagline, whatever the readers say

## Reading the answers

- The material for revision is in the reasons: `what_pushed_you_away`, `unclear_terms`,
  `stopped_reading_at`, and reasons shared by the three. `would_try` is one answer from one reader,
  so read only its direction
- Sort into the two bins of SKILL.md step 4. Coined terms and a missing output example are fixable
  in the text. "Can't try it for free", "accuracy not measured", "depends on one vendor" are missing
  facts and go to the author — thinning them with wording hides a real cost from the visitor
- Each round, put the three readers' `would_try` and main reasons in one table for the author

## Extra stop condition

Also stop at a round where no fixable reason disappears and no reader's `would_try` moves. If a
later review changes the text substantially, read the frozen result once more to check that no new
reason to leave appeared.

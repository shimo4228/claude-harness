<!-- origin: shimo4228 -->
# Preset: article

Checks whether the author's judgment survives a reading: what the author decided, what they left
open, and why. The goal is that a reader can say, in their own words, how far the author thought.
Keeping readers reading is not the goal.

Run it on an article, essay or post before its structure is frozen. The caller supplies the
author's judgment (decided / left open / why), usually from the writing brief. It is used only to
match the answers and never goes to the readers.

## Readers

| ID | role | content | depth |
|---|---|---|---|
| `primary` | main reader | The reader the channel is written for: someone who uses the article's subject in their own setting | standard |
| `inflow` | reader from the inflow route | Someone arriving through the route this article actually gets (a trend page, topic search, a social post). Give them a skimming time budget | skimming |
| `practitioner` | practitioner | Someone who does the same work themselves and has read many write-ups on it. Reads hardest for how far the author thought; always included | judges how far the author thought |

The model follows the `depth` column (SKILL.md step 1): a stronger model fills gaps between the
lines by itself, which hides where a skimming reader would lose the thread, while for a reader
judging how far the author thought, that same strength is the judgment. A reader role outside this
table (a prize judge, a novelist) gets its depth, and so its model, by the same rule.

The readers are not waited on for the author's confirmation. Record the three in the brief or
`log.md`.

## Prompt

Write the prompt in the draft's language; keep the JSON field names in English. Save it as
`prompt.md` with a line `=== ARTICLE ===` at the end; `read.sh` appends the draft after it.

```
You opened the article below. Read it the way you really would, and stop where you would stop.
When you finish, answer in JSON only, with no code fence and no text around it.

{
  "stopped_reading_at": "<heading or sentence where you stopped or started skimming>",
  "what_the_author_decided": "<what the author decided, in your own words, 1-2 sentences>",
  "what_the_author_left_open": "<what the author did not decide or did not measure, 1-2 sentences; empty if none>",
  "why_it_holds": "<the observation or number that supported the decision, and which sentence showed it>",
  "depth_vs_what_i_have_read": "<how far this author thought, compared with articles on this you have read, 1-2 sentences; quote the sentence that made you think so>"
}

=== ARTICLE ===
```

Japanese version (for a Japanese draft):

```
次の記事を開いた。実際に読むように読み、止まるところで止まる。読み終えたら JSON だけを返す。コードフェンスや前置きは付けない。

{
  "stopped_reading_at": "<止まった、または流し読みに入った見出しか文>",
  "what_the_author_decided": "<著者が決めたことを、あなたの言葉で 1〜2 文>",
  "what_the_author_left_open": "<著者が決めなかったこと・測っていないことを 1〜2 文。無ければ空>",
  "why_it_holds": "<その判断を支えていた観察か数字。どの文で分かったか>",
  "depth_vs_what_i_have_read": "<この著者がどこまで考えているか、あなたが読んできた記事と比べて 1〜2 文。そう思った文を挙げる>"
}

=== 記事 ===
```

## Reading the answers

Match `what_the_author_decided`, `what_the_author_left_open` and `why_it_holds` against the
author's judgment, reader by reader, and record one of three values:

- **match** — the reader states the same judgment in their own words
- **shift** — the reader read a different judgment or a different reason (quote the reader)
- **missing** — the reader cannot state the judgment

Only **shift** and **missing** are grounds for revision. The bins of SKILL.md step 4 take reasons
from shift and missing readers only; terms, the first screen and insider context are left to the
reviews run after the structure is frozen.

- `stopped_reading_at` of a shift or missing reader is the diagnosis: what between the opening and
  the place they stopped kept the judgment from reaching them. Fix that
- A missing from the lightest-model reader alone may be the model, not the text. Revise only when
  the place they stopped comes before the judgment; otherwise record it
- `depth_vs_what_i_have_read` is recorded and passed to the author only. It is neither a stop
  condition nor a revision goal: LLM readers rate novelty and depth more leniently than human
  experts, and climbing that answer pushes revisions toward authority words and names. Leave it
  unrecorded for a reader on the writer's model (self-preference)

## Drift

Pass the evidence file (the dossier of sources and measurements the draft draws on) as
`--dossier`, so numbers and names it already holds count as said. Superlatives include ranking
words (the first, the only, 第一人者, 唯一, 誰よりも).

## Extra stop condition

The first stop condition of SKILL.md step 6 reads: all three readers **match** and no new reason
fixable in the text appears. If r0 already matches, stop without revising.

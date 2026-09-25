---
name: adr-writer
description: Record a design decision as an Architecture Decision Record (ADR) in the project's `docs/adr/` directory. Use this skill whenever the user says "let's ADR this", "record this decision", "write an ADR for X", or when context-sync Phase 3 needs to extract a buried decision. The skill resolves the target ADR directory from cwd, picks the next sequence number with no collision, writes the 7-section body (incl. `Review-when` expiry conditions) in the main loop, runs the mechanical evidence and the adr-reviewer, and updates the ADR index. Also the canonical place for the filing bar — an ADR is written only for a mechanism / gate / threshold / agent-tier change that other artifacts cite, or for superseding / annotating a prior ADR; everything else goes into the commit body. Works across any repo — auto-detects or creates `docs/adr/` from the repo root.
user-invocable: true
origin: shimo4228
---

# ADR Writer

Capture a design decision as a numbered ADR with consistent structure. The skill handles the boilerplate (directory detection, sequence numbering, index update) in scripted steps, and the main loop writes the prose.

## Why the main loop writes

Deterministic concerns — where the ADR goes, what number it gets, which index needs updating — are easy to get wrong silently (number collisions, sub-directory cwd confusion, index drift), so they live in scripted steps. The prose is written by the main loop that holds the decision: rendering to the house template is cheap for it, and the decision packet (Step 3) is the discipline that keeps *decide* and *render* apart — the packet is settled first, the file is a faithful expression of it, nothing is inferred while writing. That principle is [ADR-0016](../../docs/adr/0016-writer-agents-render-not-decide.md) (writer agents render, they do not decide), applied in the main loop per [ADR-0072](../../docs/adr/0072-retire-adr-writer-agent-and-narrow-adr-filing.md); the evidence script (Step 4.5) is the fidelity check.

## When to Use（起票の条件 — 正本）

Write an ADR when at least one holds:

- The change moves a **mechanism, gate, threshold, or agent tier that other artifacts cite** (a hook, a lint boundary, a chain step, a rule's default, a model pin) — the ADR is what those artifacts point at
- The decision **supersedes or partially weakens a prior ADR** (a Status flip or a dated 注記 is needed on the old one)

Entry points: the user says "let's ADR this" / "record this decision", `context-sync` Phase 3 surfaced a buried decision, a debate concluded and the outcome must outlive the session. Apply the two conditions to the request; when neither holds, say so and use the commit body.

## When NOT to Use — the commit body carries it

Everything else is recorded in the commit body, in three lines, so `git log --grep` finds it later:

```
Context: <what was observed, with its source>
Decision: <what changed, as a commitment>
Review-when: <the observation that would void it, or "none — record">
```

This covers bug fixes, reversible refactors, wording changes to rules / skills that nothing else cites, stocktake outcomes (retire / keep verdicts — the stocktake's own results file plus the commit), and personal preferences. When a commit-body decision later gets superseded or cited by another artifact, promote it: write the ADR then, quoting the commit.

## Workflow

### Step 1: Resolve the ADR directory

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || REPO_ROOT="$(pwd)"
ADR_DIR="$REPO_ROOT/docs/adr"
```

If `$ADR_DIR` does not exist, create it — the ADR request itself covers the directory, and
git makes it reversible. Mention the creation in your final report. Write a minimal
`README.md` index alongside:

````markdown
# Architecture Decision Records

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|

## Template

ADRs in this repository use the 7-section template
(`scripts/adr_lint.py` checks section presence mechanically):

```markdown
# ADR-NNNN: [Title]

## Status
accepted | superseded | deprecated

## Date
YYYY-MM-DD

## Context
[what was the problem]

## Decision
[what was decided]

## Review-when
[expiry conditions — an ADR is a dated hypothesis, not a permanent constraint]

## Alternatives Considered
[rejected options and why]

## Consequences
[what becomes easier / harder]
```

File name: `NNNN-kebab-case-title.md` (zero-padded 4-digit sequence).
Index rows link the number: `| [NNNN](NNNN-slug.md) | Title | status | YYYY-MM-DD |`.
````

（インデックス行は番号を相対リンクにする — harness / CA 等の既存 index と同形。
`adr_lint.py` はこの README の Template fenced block から期待節セットを読むので、
README を置くことが lint のテンプレ宣言を兼ねる。）


### Step 2: Pick the next sequence number

```bash
LAST_NUM=$(ls "$ADR_DIR"/[0-9]*-*.md 2>/dev/null | sort -V | tail -1 | sed -E 's|.*/([0-9]+)-.*|\1|')
if [ -z "$LAST_NUM" ]; then
  NEXT_NUM="0001"
else
  NEXT_NUM=$(printf "%04d" $((10#$LAST_NUM + 1)))
fi
```

Verify uniqueness right before writing (race safety):

```bash
[ -e "$ADR_DIR/$NEXT_NUM-"*.md ] && echo "COLLISION" || echo "OK"
```

If `COLLISION`, recompute `NEXT_NUM` from the latest state.

### Step 3: Gather the 7 inputs

Ask the user (or accept from caller) for:

1. **Title** — short, kebab-case-friendly (e.g., `context-sync-cascade-and-writer-agents`). The skill will compose the filename.
2. **Status** — `proposed | accepted | superseded | deprecated`. Default `accepted`.
3. **Context** — what problem prompted this decision (raw text OK).
4. **Decision** — what was decided (raw text OK).
5. **Review-when** — the expiry conditions (失効条件): which observation or premise failure would void or weaken this decision, 1-3 lines. It can only be captured at write time (ADR-0021); an ADR without it reads as permanent. If there genuinely is none, say so explicitly and write 「無し — 恒久判断ではなく記録」.
6. **Alternatives** — what else was considered and why rejected, or, for an alternative that stays live, 「未決 — 再訪条件: …」 (raw text or list). Keeping a rival open is allowed; a straw man is not.
7. **Consequences** — what becomes easier / harder (raw text or list).

If 3-7 are missing, request them — do not proceed. ADRs without these sections are noise.

**予防チェック（packet 確定前）.** [references/review-findings.md](references/review-findings.md)
（レビュー頻出指摘の日付つき事例集）を読み、該当パターンを自己点検する — 引用 ADR の
実在と内容一致、surviving scope の置き場所、造語の出所、full/partial supersede の判定根拠、
gitignored パス参照、数値の出典と分母、カウント条件の固定対象。これは書き時の予防であって
意味的レビューの代替ではない — commit 前の adr-reviewer は省略しない。

**Assemble and approve the decision packet before writing.** Settle the actual content here: the real Context, the decision as decided, the Review-when triggers, why each Alternative was rejected (or under what condition it is revisited), which Consequences genuinely follow. Confirm this packet with the user (especially the Review-when, the rejection reasons and both sides of Consequences) *before* Step 4 — Step 4 expresses the packet and adds nothing, so a fuzzy decision is resolved here.

### Step 4: Write the file (main loop)

Read the 2 most recent ADRs in `$ADR_DIR` for house style (heading form, link style, whether
Consequences splits into Positive / Negative / Neutral), then write
`$ADR_DIR/$NEXT_NUM-<title>.md` from the Step 3 packet:

- Heading `# ADR-NNNN: <title>`, then the 7 sections in template order (Step 1's template, or
  the repo's own `docs/adr/README.md` Template block when it differs)
- Every Context fact, Decision clause, rejection reason and Consequence comes from the packet.
  Writing is expression, not synthesis — a consequence that feels "logically entailed" but is not
  in the packet goes back to Step 3 for the user to approve, not into the file
- Decision in imperative voice (「〜する」「〜に固定する」); Review-when as observable triggers;
  each Alternative with its rejection reason or 「未決 — 再訪条件: …」
- Links to sibling ADRs are relative (`./NNNN-slug.md`) and the file name is copied from `ls`,
  not typed from memory — Step 4.5's `refs.links_broken` is the check

If a packet field is missing, stop and ask; do not write a partial ADR.

### Step 4.5: Run the mechanical lint and the per-ADR evidence

```bash
python3 ~/.claude/skills/adr-writer/scripts/adr_lint.py --root "$REPO_ROOT"
```

Evidence モード（判定しない・exit 0）。出力 JSON のうち**今書いた ADR に関する逸脱**
（missing_sections / case_mismatch / status / date / index / naming）を修正してから先へ進む。
既存 ADR の逸脱は報告のみ — このステップで直さない（別タスク）。lint の検査範囲は機械的
性質のみで、意味的レビュー（adr-reviewer）の代替ではない。

ad hoc で blocking 判定が欲しいときは `--gate` を足す。免除境界は既定で無制限なので
repo ごとの値を渡す — harness は `--sections-from 44 --require-review-when-from 44`
（ADR-0009 の 2 節欠落と 0043 以前の Review-when 無しを免除、ADR-0051）。

続けて、今書いた 1 本の per-ADR evidence を取る（ADR-0071 — adr-reviewer が 24 報告で反復した
指摘のうち、機械で数えられる部分）:

```bash
python3 ~/.claude/skills/adr-writer/scripts/adr_review_evidence.py --root "$REPO_ROOT" --adr "$NEXT_NUM" --diff worktree
```

JSON のうち**書き時に直せるもの**をここで直す — `refs.unresolved`（実在しない ADR / RFC 番号）、
`refs.links_broken`、`paths.flagged` の `missing`（実在しないパス）と `ignored`（gitignored の
根拠 — `docs/evidence/` へ昇格するかパス非依存に書き換える）、`paths.line_refs_out_of_range`、
`numbers.percent_without_denominator`、`numbers.relative_referents`（会話参照）、
`relations.targets` で `annotation_lines` が空の target（旧 ADR 側の注記 — Edge cases 表の
partial weakening 行）。`diff_scope.changed_not_mentioned` に ADR が触れていない変更があれば、
Decision に書くか別 commit へ分ける。残りの key（`numbers.unanchored`、`review_when`、
`alternatives`、`consequences`、`second_record`）は判断を要するので Step 4.6 の reviewer に渡る。

### Step 4.6: Run the semantic review (adr-reviewer)

commit 前に agent: `adr-reviewer` を起動して今書いた ADR を渡す — 省略しない。
**この skill が adr-reviewer の唯一の配線**（ADR-0055）。指摘は Step 3 の packet に照らして主ループが採否を決め、採った分だけ直す。

### Step 5: Update the index

After Step 4 writes the file, append a row to `$ADR_DIR/README.md` index table:

```bash
# Read current index
# Find the table block (lines between the "| ADR |" header and the next "##" heading)
# Append: | [$NEXT_NUM]($NEXT_NUM-<slug>.md) | <title human-readable> | <status> | <date> |
```

If the index table is malformed or absent, regenerate it from the directory:

```bash
for f in "$ADR_DIR"/[0-9]*-*.md; do
  num=$(basename "$f" | sed -E 's|([0-9]+)-.*|\1|')
  title=$(head -1 "$f" | sed -E 's|^# ADR-[0-9]+: ||')
  status=$(awk '/^## Status/{getline; getline; print; exit}' "$f")
  date=$(awk '/^## Date/{getline; getline; print; exit}' "$f")
  echo "| [$num]($(basename "$f")) | $title | $status | $date |"
done
```

### Step 6: Report

Tell the user:

```
ADR written
---
File:    docs/adr/<NNNN>-<title>.md
Number:  <NNNN>
Status:  <status>
Index:   updated (+1 row)
```

## Edge cases

| Case | Handling |
|---|---|
| Called from a sub-directory of the repo | Use `git rev-parse --show-toplevel`; never trust raw cwd |
| Not a git repo | Fall back to cwd, warn the user that they should `git init` |
| ADR number was reserved verbally but not yet written ("I'll write ADR-0010 later") | Skill cannot know; ask the user whether to take the next free number or the reserved one |
| User wants to supersede an existing ADR | Update the old ADR's Status to `superseded by ADR-NNNN`, then create the new one. Two file writes. |
| New ADR **partially weakens** an old one (a premise expired, a Review-when trigger fired) but does not supersede it | Do not flip Status. Append under the affected section of the old ADR: `> **注記（YYYY-MM-DD, ADR-NNNN）**: <what changed and what still stands>`. Never delete the original text — the strength history stays readable in place (precedents: ADR-0018 §Consequences, ADR-0028). Do this after Step 4 has written the new file. |
| Title contains spaces or non-ASCII | Skill normalizes to kebab-case ASCII for the filename; preserves original in the `# ADR-NNNN: ...` heading |

## Boundaries

- **Do not** invent missing sections. Refuse to write an ADR with `Context: [TBD]` or similar placeholders.
- **Do not** modify ADRs other than the new one and (optionally) the index, except the two explicit main-loop steps above (Status flip on full supersede; dated 注記 on partial weakening).
- **Do not** infer the user's decision from chat history without confirming. Ask, even if the answer feels obvious.
- **Do not** commit the file. The user owns the commit step.

## Reference Files

- ADR template canonical source: read the target repo's existing ADRs to mirror their voice. For the harness itself, see `~/.claude/docs/adr/README.md`.
- Mechanical lint (evidence mode + `--gate`): `scripts/adr_lint.py`（ADR-0051。repo の
  `docs/adr/README.md` Template からテンプレを自動適応、tests は `tests/test_adr_lint.py`）。
- Per-ADR review evidence (evidence mode のみ): `scripts/adr_review_evidence.py`（ADR-0071。
  引用の実在・注記の往復・パス分類・diff 範囲・出典なき数値、tests は
  `tests/test_adr_review_evidence.py`）。実行・import の入口はこの 1 本で、検査の本体は
  `scripts/adr_evidence_common.py` / `_paths.py` / `_prose.py` に分かれている（ADR-0056 の
  file-LOC 予算）。
- レビュー頻出指摘の事例集: `references/review-findings.md`（Step 3 の予防チェックで読む）。
- Evals: `evals/evals.json` (3 scenarios — new ADR / missing docs-adr / sequence collision).

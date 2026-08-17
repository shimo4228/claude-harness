<!-- origin: shimo4228 -->
# Kickoff packet — template

A packet is a **hypothesis handed to a build session**, not an order. Every packet written on
the first hand-run day was partly wrong (a "premise" that was only half true, a fix shape that
did not close the hole); the sessions that were told "verify the premise first, record what
you find, then do the right thing" produced correct results anyway. Keep the shape below; keep
Phase 0 first.

Two variants share it: **build** (code changes on a task branch) and **measurement** (a
reading that decides the next state; read-only, output is a memo).

---

```markdown
# Kickoff packet — S<n>: <T-ID or bundle name>（<one-line what>）

あなたは task-triage loop の **build 役**です。cwd は `<repo>` の git worktree（branch `task/<name>`）。
**main には触らない、merge しない、push しない、台帳（.notes/…）の状態を書き換えない。** 成果は
branch 上の commit だけで返し、判断役が検収、オーナーの「merge」で main へ ff-only 取り込みます。
<measurement variant: 「書いてよいのは読みメモ 1 ファイル `<path>` と分析スクリプトだけ」>

最初に読む: <task file(s)>、<repo rule that applies — e.g. security.md threat surface for gate work>、
<prior commit / memo the task depends on>.

## Goal（決定可能な受入条件）
1. <machine-checkable outcome — a command and its exit code, a test name, a diff property>
2. <…>
<measurement: 出すもの = 数字 / 引用 / 1 行の読み。判定はしない — 判断役がする>

## Phase 0 — 前提の再照合（反証されたら実装せず止めて報告。ただし「反証を記録して正しく直す」が
できる範囲なら、その判断も報告に書く）
- <premise 1 with file:line to re-check>
- <premise 2>

## Build（順序）
1. <TDD: failing test first when the change is code>
2. <implementation constraints: 1 箇所で正規化、値は raw のまま、…>
3. <verify: ./.claude/verify.sh 引数なし exit 0 / pytest 範囲>

## Review（chain）
- 種別: <feat / fix / refactor / chore / measurement>。**chain は skill `implementation-chain` の
  Chain Matrix に従う**（この packet は reviewer を列挙しない — 列挙漏れは省略の許可ではない）。
  種別の既定に加えて要るもの / 外してよいものがあれば**ここに理由付きで**書く（例: security-reviewer
  必須 — gate を触るため / Simplify 不要 — 機械修正のみ）
- **packet に書いていないことは harness の規約が既定**（implementation-chain / task-tracking / security /
  git-workflow）。省略・読み替えは可だが、報告に「逸脱: 何を・なぜ」と**必ず名指し**する。無言の逸脱は
  結果が正しくても bounce される
- diff 外の指摘は**起票せず**、全部を最終メッセージと commit body の `Out-of-diff findings` に列挙する
  （HIGH は producer `file:line` 付き）。捨てるか起票するかは判断役とオーナーが決める — 「無視された」
  にならないよう、判断役はこの節を必ず harvest する

## Must-not（境界 = Goodhart 対策）
- <files / dirs that may not change> ; テストを弱めない・消さない・設定で黙らせない
- `git add -A` を使わない ; main への merge・push・台帳の状態変更はしない
- <time cap> を超えたら打ち切って、そこまでの diff とテスト状況で報告

## Report（最終 commit の message 本文 = pane が閉じても残る唯一の証拠）
<type>(<scope>): <summary> (<T-IDs>)

Packet: S<n>
Premise: <file:line 再照合の結果、反証があればそれ>
Fix: <what and why, in the shape the reviewer needs>
Regression: <test names, RED→GREEN の確認方法>
Verify: <command exit / test counts / 日時>
Review: <chain どおりに回した reviewer と結果> / Deviations: <逸脱の名指しと理由、無ければ none>
Approval ledger: <if a pinned gate script changed: 未実施、人間が approve>
Out-of-diff findings (for the judge): <severity + 1 行ずつ、HIGH は producer 付き / none>

最後のメッセージで commit SHA・verify の結果・所要時間を報告して終了してください。
```

---

## Notes that earned their place

- **Time-of-day / shared-resource constraints go in the packet** (local LLM busy until 19:00 →
  "do the LLM-free readings first, check `date` and `ollama ps` before the dry-run").
- **Measurement packets say "判定はしない"** — the reading and the decision are different
  roles; the memo carries numbers and quotes, the judge flips states.
- **Bundles**: several tasks with one setup cost → one packet, one branch, one commit that
  names all task IDs. Three README notes across three repos also fit one session (three
  branches, three commits).
- **Escalation is a valid ending**: a build that finds a bigger hole (an out-of-diff HIGH) leaves
  it out of the diff, documents the PoC in the commit body, and reports; the judge files it
  with `--producer` after the human agrees. Do not let a build widen its own scope.

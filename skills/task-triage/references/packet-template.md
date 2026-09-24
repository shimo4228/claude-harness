<!-- origin: shimo4228 -->
# Kickoff packet — template

A packet is a **hypothesis handed to a build session**, not an order. Every packet written on
the first hand-run day was partly wrong (a "premise" that was only half true, a fix shape that
did not close the hole); the sessions that were told "verify the premise first, record what
you find, then do the right thing" produced correct results anyway. Keep the shape below; keep
Phase 0 first.

Two executors read it (the choice is task-triage §3): a **cloud session** (default — clones
`origin/main`, works on a `claude/` branch, reads no `~/.claude`, so the packet carries the whole
contract; CI runs `verify.sh` on push) and a **local session** (worktree, harness present, chain
delegated to `implementation-chain`). Two variants: **build** (code changes on the branch) and
**measurement** (a reading that decides the next state; read-only, output is a memo).
Lines marked `<cloud: …>` / `<local: …>` are alternatives — keep one.

A cloud packet is the session's first message, and in a public repo the branch, commits and
PR are public before acceptance. Write it as you would an `rfcs/` entry (ADR-0049): task IDs and
`file:line`, never a private number or `.notes/` content — a task that needs those is a local
task (task-triage §3).

---

```markdown
# Kickoff packet — S<n>: <T-ID or bundle name>（<one-line what>）

あなたは task-triage loop の **build 役**です。
<cloud: この session は GitHub の `<owner/repo>` main を clone した cloud session で、branch は
session が作った `claude/…`。成果はその branch への commit と push で返し、判断役が CI の結果と
commit 本文を読んで検収し、main へ ff-only 取り込みます。あなたが merge する経路はありません。
この packet に書いていないことは**やらない**（外側に規約は無い）。>
<local: cwd は `<repo>` の git worktree（branch `task/<name>`）。成果は branch 上の commit で返し、
判断役が検収して main へ ff-only 取り込みます。境界（人間に渡す操作 / とってよいリスク / 止まる
条件）は rule `boundary.md` — build は task branch まで。packet に無いことは harness の規約が既定。>
<measurement variant: 「書いてよいのは読みメモ 1 ファイル `<path>` と分析スクリプトだけ」>

最初に読む: <task file(s)>、<repo の CLAUDE.md の該当節 / rule — e.g. security.md threat surface for gate work>、
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
3. <verify: ./.claude/verify.sh 引数なし exit 0 / pytest 範囲。cloud: CI が push ごとに同じ
   verify.sh を走らせる — 手元の実行は事前確認、判定は CI>

## Review
<cloud:
- 実装後・commit 前に built-in `/code-review` を **effort `medium`** で 1 回、この diff の範囲で起動する。
  reviewer への指示（そのまま渡す）:「correctness / stated requirements に効く gap のみ報告。それ以外
  （防御的コード・追加の抽象層・起こり得ないケースのテスト等）は optional として報告し、適用しない。
  diff 外の指摘は 1 行のみ、修理はしない」。CRITICAL が出たら直さず止めて報告する。
- これ以外の reviewer は起動しない（security 等の判断は判断役が持つ）。
- 省略・読み替えは可だが、報告に「逸脱: 何を・なぜ」と**必ず名指し**する。無言の逸脱は結果が正しくても
  bounce される>
<local:
- 種別: <feat / fix / refactor / chore / measurement>。**chain は skill `implementation-chain` の
  Chain Matrix に従う**（この packet は reviewer を列挙しない — 列挙漏れは省略の許可ではない）。
  種別の既定に加えて要るもの / 外してよいものがあれば**ここに理由付きで**書く（例: security-reviewer
  必須 — gate を触るため / E2E 追加 — 画面遷移に触れるため）
- **packet に書いていないことは harness の規約が既定**（implementation-chain / task-tracking / security /
  git-workflow）。省略・読み替えは可だが、報告に「逸脱: 何を・なぜ」と**必ず名指し**する。無言の逸脱は
  結果が正しくても bounce される>
- diff 外の指摘は**起票せず**、全部を最終メッセージと commit body の `Out-of-diff findings` に列挙する
  （HIGH は producer `file:line` 付き）。捨てるか起票するかは判断役とオーナーが決める — 「無視された」
  にならないよう、判断役はこの節を必ず harvest する

## Must-not（境界 = Goodhart 対策）
- <files / dirs that may not change> ; テストを弱めない・消さない・設定で黙らせない
- `.claude/verify.sh`・`.claude/verify.md`・`.github/`・`.claude/settings.json` を変えない
  （検査の正本と CI — 触った diff は検収に入らない）
- `git add -A` を使わない ; 台帳（`rfcs/` の state）の状態は判断役が書く
- <cloud: PR は自動で開く。PR の本文・設定は触らない ; main や他の branch に push しない ; force push しない>
- <time cap> を超えたら打ち切って、そこまでの diff とテスト状況で報告
- shell ループで複数 path / repo を回すときは **zsh の word-split 罠**を踏まない: 未クオートの `$files` は
  1 語のまま渡る（`git add -- $files` が 1 つの長い pathspec になる）。`while read` でファイルから回すか
  `${=files}` で明示 split する（3 packet が踏んだ: 2026-06-28 badge push、2026-08-19 B1 commit loop、
  2026-08-19 judge push loop — 最後は retry 前に 0/40 push）

## Report（最終 commit の message 本文 = session が閉じても残る唯一の証拠）
<type>(<scope>): <summary> (<T-IDs>)

Packet: S<n>
Premise: <file:line 再照合の結果、反証があればそれ>
Fix: <what and why, in the shape the reviewer needs>
Regression: <test names, RED→GREEN の確認方法>
Verify: <command exit / test counts / 日時。cloud: CI の判定は判断役が読む>
Review: <cloud: /code-review medium の結果（findings 件数と対応）> <local: chain どおりに回した reviewer と結果> / Deviations: <逸脱の名指しと理由、無ければ none>
Approval ledger: <if a pinned gate script changed: 未実施、人間が approve>
Risk: <とったリスク / 戻し方（1 分で戻せるか）>
Out-of-diff findings (for the judge): <severity + 1 行ずつ、HIGH は producer 付き / none>

最後のメッセージで <cloud: branch 名・push した commit SHA> <local: commit SHA>・verify の結果・
所要時間を報告して終了してください。前提が崩れて実装しなかったときも同じ形で報告してください。
```

---

## Notes that earned their place

- **Time-of-day / shared-resource constraints go in the packet** (local LLM busy until 19:00 →
  "do the LLM-free readings first, check `date` and `ollama ps` before the dry-run"). Cloud
  builds have no local LLM at all — a task that needs one is a local task.
- **Measurement packets say "判定はしない"** — the reading and the decision are different
  roles; the memo carries numbers and quotes, the judge flips states.
- **Bundles**: several tasks with one setup cost → one packet, one branch, one commit that
  names all task IDs. Three README notes across three repos also fit one session (three
  branches, three commits; cloud: one session per repo).
- **Escalation is a valid ending**: a build that finds a bigger hole (an out-of-diff HIGH) leaves
  it out of the diff, documents the PoC in the commit body, and reports; the judge files it
  with `--producer` after the human agrees. Do not let a build widen its own scope.
- **The cloud pilot (2026-09-24, systems-thinking-learning)**: a self-contained packet was
  followed in full — implementation, verify, `/code-review`, the commit-body report — and when
  the premise broke (no push target) the session stopped and reported. The self-contained form
  is what made that possible: nothing in it pointed at a harness the session could not see.

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

**Effort** — the judge fills the packet's `Effort:` line on every packet from this table, by how
dense the edge cases are in the diff, with the reason in one phrase (a blank line leaves a cloud
session on the server-side default, which moves — ADR-0081). The same value goes to `cloud-dispatch.sh
--effort` (task-triage §3). Effort cuts missed cases far more than misreadings (ADR-0081), so the
table ranks by where a missed case would hide.

| 状況 | effort |
|---|---|
| docs / 設定 / rulebook 型、仕様が細かい変更 | low |
| 通常の feat | medium（未記入時の既定 = cloud の実測既定と同じ） |
| brownfield の fix、parser / sanitizer、並行性、性能、security を動かす diff | high |
| 無人で長く走り検証が厳しいもの | xhigh（max は著者が明示したときだけ） |

---

```markdown
# Kickoff packet — S<n>: <T-ID or bundle name>（<one-line what>）

あなたは task-triage loop の **build 役**です。
<cloud: この session は GitHub の `<owner/repo>` main を clone した cloud session で、branch は
session が作った `claude/…`。成果はその branch への commit と push で返し、判断役が CI の結果と
commit 本文を読んで検収し、main へ ff-only 取り込みます。あなたが merge する経路はありません。
この packet が契約の全部です（外側に規約は無い）。Goal に要る作業は書いていなくても行い、Goal の外へ広がる
変更は Report の Proposed tasks に回す。>
<local: cwd は `<repo>` の git worktree（branch `task/<name>`）。成果は branch 上の commit で返し、
判断役が検収して main へ ff-only 取り込みます。境界（人間に渡す操作 / とってよいリスク / 止まる
条件）は rule `boundary.md` — build は task branch まで。packet に無いことは harness の規約が既定。>
<measurement variant: 「書いてよいのは読みメモ 1 ファイル `<path>` と分析スクリプトだけ」>

最初に読む: <task file(s)>、<repo の CLAUDE.md の該当節 / rule — e.g. security.md threat surface for gate work>、
<prior commit / memo the task depends on>.

Effort: <low / medium / high / xhigh> — <理由 1 句（例: parser を動かす diff）>

## 進め方
- 入力が要らない step は止まらずに続ける。状況メモは次の行動と同じメッセージに書く。止まるのは Phase 0 の
  反証（記録して正しく直せる範囲を除く）、Review の CRITICAL、time cap、この packet の外の操作が要るときだけ
- 確かめられなかったことには「未確認」と印を付け、どこを見たかを書く
- 方針を選んだ箇所は、その理由を 3 文で Report の Fix に書く
<if 単位が 3 つ以上に割れる監査・移行: 単位ごとに subagent に分ける。subagent の報告は証拠（file:line・
コマンド出力）を確かめてから受け入れ、最後に「単位 / 影響 / 証拠」の表を Report に付ける>
<if 手順が 10 を超える・time cap が 1 時間を超える: チェックリストを commit しないファイル（`/tmp/tasks.md`）に
置き、終えた項目に印を付け、見つけた項目を足す>
<if UI・見た目に触れる: 使わないスタイル: <具体名 — 例: cream 系の背景、見出しの斜体の強調語、番号付きの節ラベル、
monospace のラベル、pill 形のボタン>。1 枚目の結果が使った既定のスタイルは Report に名前で書く（判断役が次の
列挙に足す）。Report に before / after の画像の path を付ける>
<if 性能・最適化: 改善を測れる指標に言い換えてから始める。指標は決定的なもの（命令数・render 回数・テストが数える
回数）を使い、wall-clock と同じ向きに動くことを 1 回確かめる。改善はテストの上限値で固定する（CI がそのテストを
走らせる）>
<if 著者が「押し続ける」を選んだ: Goal の数値を満たしたら、同じ指標を time cap まで改善し続ける。対象は Goal の範囲の
まま>
<if 本番との比較（候補 arm 対 本番、lab 対 現場）: 本番と候補の差を表で列挙する（入力に見せる文 / 問いの形 / 答えの読み方 / 温度 /
審判の定義）。差が 2 つ以上なら 1 条件ずつ変える arm を同じ標本で Goal に持つ。審判の定義は著者が確認した前提として書き、
script の docstring に埋めない — measurement-discipline §8（CA RFC-0045 で 3 条件 + 審判の問いが同時に違い、RFC-0046 が
交絡した根拠の上に建った）>

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
- 実装後・commit 前に built-in `/code-review` を **effort `medium`**（review の段階。この session の Effort とは別）で 1 回、この diff の範囲で起動する。
  reviewer への指示（そのまま渡す）:「correctness / stated requirements に効く gap のみ報告し、各指摘に
  file:line・なぜ誤りか・失敗を示す手順を付ける。それ以外（防御的コード・追加の抽象層・起こり得ないケースの
  テスト等）は optional として報告し、適用しない。diff 外の指摘は 1 行のみ、修理はしない」。CRITICAL が出たら直さず止めて報告する。
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
- diff 外の気づきは `rfcs/` にも台帳にも書かない。再現手順を書けるものは Report の `Proposed tasks`
  （最大 2 件）に、書けないものは `Out-of-diff findings` に 1 行ずつ（HIGH は producer `file:line` 付き）
  置く。起票するかは判断役が再現を確かめたうえでオーナーが決める — 判断役はこの 2 節を必ず harvest する

## Must-not（境界 = Goodhart 対策）
- <files / dirs that may not change> ; テストを弱めない・消さない・設定で黙らせない
- `.claude/verify.sh`・`.claude/verify.md`・`.github/`・`.claude/settings.json` を変えない
  （検査の正本と CI — 触った diff は検収に入らない）
- `git add -A` を使わない ; 台帳（`rfcs/` の state）の状態は判断役が書く
- <cloud: PR は自動で開く。PR の本文・設定は触らない ; main や他の branch に push しない ; force push しない>
- <time cap> を超えたら打ち切って、そこまでの diff とテスト状況で報告
- shell ループで複数 path / repo を回すときは、path をファイルに書いて `while read` で 1 行ずつ回す（zsh は
  未クオートの `$files` を分割せず、`git add -- $files` が 1 つの長い pathspec になる）

## Report（最終 commit の message 本文 = session が閉じても残る唯一の証拠）
<type>(<scope>): <summary> (<T-IDs>)

Packet: S<n>
Needs from judge: <判断役かオーナーの決定・承認が要るもの / none>
Model: <この session のモデル名。途中でモデルが切り替わった通知が出たらその旨>
Effort: <この session が実際に走った effort — 環境変数 `CLAUDE_EFFORT` か `/effort` の表示。分からなければ「未確認」>
Premise: <file:line 再照合の結果、反証があればそれ>
Fix: <what and why, in the shape the reviewer needs>
Regression: <test names, RED→GREEN の確認方法>
Verify: <command exit / test counts / 日時。cloud: CI の判定は判断役が読む>
Review: <cloud: /code-review medium の結果（findings 件数と対応）> <local: chain どおりに回した reviewer と結果> / Deviations: <逸脱の名指しと理由、無ければ none>
Approval ledger: <if a pinned gate script changed: 未実施、人間が approve>
Risk: <とったリスク / 戻し方（1 分で戻せるか）>
Proposed tasks (for the judge, 最大 2 件): <各件: 何が壊れているか / 再現手順（コマンド → 期待と実際）/
  決定可能な受入条件 / producer file:line — 無ければ none。再現手順は branch の tip で走る 1 コマンド（repo の
  テスト実行器で名前を指したテスト、または読み取りのみ）にし、commit しない — 失敗するテストを commit すると
  CI が落ちる>
Out-of-diff findings (for the judge): <severity + 1 行ずつ、HIGH は producer 付き / none>

最後のメッセージは「判断役に要るもの」から始め、<cloud: branch 名・push した commit SHA> <local: commit SHA>・
verify の結果・所要時間を報告して終了してください。前提が崩れて実装しなかったときも同じ形で報告してください。
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
  it out of the diff and puts it in `Proposed tasks` with its reproducer (or in `Out-of-diff
  findings` when it cannot write one); the judge runs the reproducer and the human decides the
  filing (task-triage §4). Do not let a build widen its own scope.
- **The cloud pilot (2026-09-24, systems-thinking-learning)**: a self-contained packet was
  followed in full — implementation, verify, `/code-review`, the commit-body report — and when
  the premise broke (no push target) the session stopped and reported. The self-contained form
  is what made that possible: nothing in it pointed at a harness the session could not see.
- **Model guidance behind the 進め方 and Report lines** (ADR-0076). Opus 5.5 guide —
  https://claude.dev/blog/getting-the-most-out-of-opus-5-5/ (2026-09-22, read 2026-09-25): say what
  "done" is and let it run, state which stops you want, split big audits across subagents and check
  their evidence, keep the checklist in a file, end with what the run needs from you, mark what could
  not be confirmed, name the design styles to leave out, and a flagged message continues on an older
  model (hence `Model:`). It thinks before every reply on its own, so a packet asks for depth through
  its Goal and the session's effort, and asks for reasons as "3 文で". claude.ai speed-up —
  https://claude.dev/blog/how-we-made-claude-ai-faster/ (2026-09-23): measure first with a
  deterministic lab metric checked against wall-clock, lock each win with a ratchet, and treat
  ticketing-instead-of-doing as over-caution — the build's lane for new work is a reproducible
  `Proposed tasks` entry, not a filing. Re-check these lines when a guide for the next Opus
  generation appears or Opus 5.5 leaves the build role.

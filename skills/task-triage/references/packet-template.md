<!-- origin: shimo4228 -->
# Kickoff packet — template

A packet is a **hypothesis handed to a build session**, not an order. Every packet written on
the first hand-run day was partly wrong (a "premise" that was only half true, a fix shape that
did not close the hole); the sessions that were told "verify the premise first, record what
you find, then do the right thing" produced correct results anyway. Keep Premise before the work.

The packet gives the build what it cannot work out on its own: the goal as a decidable line,
the premises to re-check, the boundary, and the shape of the report. How to get there is the
build's to choose. The judge passes it as the build's prompt (task-triage §3); the build commits
it as the first commit of its branch, and the judge compares the diff against that commit in §4.
The packet is published when the branch merges, so write it as you would an `rfcs/` entry
(ADR-0049): task IDs and `file:line`, never a private number or `.notes/` content. A task that
needs those keeps its packet in the repo's `.notes/packets/` and the build commits nothing for it.

Variants: **build** (code changes on the branch) and **measurement** (a reading that decides the
next state; read-only, output is a memo). A cloud build adds the appendix at the end.

---

```markdown
# Kickoff packet — S<n>: <T-ID or bundle name>（<one-line what>）

あなたは task-triage loop の build 役。cwd は `<repo>` の git worktree で、branch は main の先頭から切られている。
<公開の packet:> 最初に、この packet を `docs/plans/<task-id>-s<n>-<slug>.md` に置いて単独で commit する（`docs(plan): <task-id> S<n> packet`）。
以後の commit はこのファイルを変えない。<非公開の packet: packet は commit しない — 判断役が `.notes/packets/` に持つ>成果は branch 上の commit で返し、判断役が検収・review して main へ ff-only で取り込む。
境界は rule `boundary.md`、chain は skill `implementation-chain`（Review の行は判断役が回す。background の subagent は Agent tool を持たないので、調査は researcher を起動せず自分で検索する）。
<measurement: 書いてよいのは読みメモ 1 ファイル `<path>` と分析スクリプトだけ。判定はしない — 判断役がする>

読むもの: <task file(s)>、<prior commit / memo the task depends on>

## Goal（決定可能な受入条件）
1. <machine-checkable outcome — a command and its exit code, a test name, a diff property>
2. <…>
<著者だけが答えられる項目の答え（あるときだけ）: UI で使わないスタイル / 性能の指標・目標・目標で止めるか time cap まで
 続けるか / 本番と比べる測定の正解の定義と、候補と本番の差の表（差が 2 つ以上なら 1 条件ずつの arm — measurement-discipline §8）>

## Premise（実装の前に再照合）
- <premise 1 with file:line>
- <premise 2>
崩れていたら、正しく直せる範囲なら直してその判断を Report の Premise に書く。直せなければ実装せず報告する。

## Must-not
- <files / dirs that may not change>
- `.claude/verify.sh`・`.claude/verify.md`・`.github/`・`.claude/settings.json`（検査の正本 — 触った diff は検収に入らない）
- 名指ししていないテストの assertion を弱める・消す・設定で黙らせる
- push・merge・他の branch への commit、台帳（`rfcs/` の state）の編集、この packet のファイルの編集
- <time cap> を超えたら打ち切り、そこまでの diff とテストの状況で報告する

## Report（最終 commit の message 本文 — session が閉じても残る証拠）
<type>(<scope>): <summary> (<T-IDs>)

Packet: S<n>
Plan: docs/plans/<task-id>-s<n>-<slug>.md <非公開の packet なら none>
Needs from judge: <判断役かオーナーの決定・承認が要るもの / none>
Premise: <file:line 再照合の結果、反証があればそれと判断>
Fix: <what and why; 方針を選んだ箇所はその理由>
Regression: <test names, RED→GREEN の確認方法>
Verify: <command exit / test counts>
Deviations: <packet から外れた点の名指しと理由 / none>
Approval ledger: <if a pinned gate script changed: 未実施、人間が approve>
Risk: <とったリスク / 戻し方>
Proposed tasks (最大 2 件): <各件: 何が壊れているか / 再現手順（branch の tip で走る 1 コマンド — repo のテスト実行器で
  名指ししたテスト、または読み取りのみ。commit しない）/ 決定可能な受入条件 / producer file:line — 無ければ none>
Out-of-diff findings: <severity + 1 行ずつ、HIGH は producer 付き / none>

最後のメッセージは「判断役に要るもの」から始め、branch 名・commit SHA・verify の結果・所要時間を書く。前提が崩れて実装しなかった
ときも同じ形で報告する。
```

---

## Cloud appendix (only for a cloud build)

A cloud session clones `origin/main` from GitHub, works on a `claude/` branch, reads no
`~/.claude`, and CI runs `verify.sh` on each push. Replace the opening paragraph with this one
and add the lines below; the rest of the packet stays.

```markdown
あなたは task-triage loop の build 役。この session は GitHub の `<owner/repo>` main を clone した cloud session で、branch は
session が作った `claude/…`。最初に、この packet を `docs/plans/<task-id>-s<n>-<slug>.md` に置いて単独で commit する。成果は
その branch への commit と push で返し、判断役が CI の結果と commit 本文を読み、別 process の review を回して main へ ff-only で
取り込む。この packet が契約の全部で、外側に規約は無い。Goal に要る作業は書いていなくても行い、Goal の外へ広がる変更は
Report の Proposed tasks に回す。review は起動しない（判断役が回す）。

（Must-not の「push」を置き換える）push するのは自分の branch だけ、force push しない
（Must-not に足す）PR は自動で開く — 本文・設定は触らない
（Report に足す）Model: <この session のモデル名> / Verify 行は「CI の判定は判断役が読む」と書く
（最後のメッセージに足す）push した commit SHA
```

## Notes that earned their place

- **Time-of-day / shared-resource constraints go in the packet** (local LLM busy until 19:00 →
  "do the LLM-free readings first, check `date` and `ollama ps` before the dry-run"). Cloud
  builds have no local LLM at all.
- **Measurement packets say "判定はしない"** — the reading and the decision are different
  roles; the memo carries numbers and quotes, the judge flips states.
- **Bundles**: several tasks with one setup cost → one packet, one branch, one commit that
  names all task IDs.
- **Escalation is a valid ending**: a build that finds a bigger hole (an out-of-diff HIGH) leaves
  it out of the diff and puts it in `Proposed tasks` with its reproducer (or in `Out-of-diff
  findings` when it cannot write one); the judge runs the reproducer and the human decides the
  filing (task-triage §4). The build's lane for new work is a reproducible `Proposed tasks`
  entry, not a filing.
- **Silent deviations are bounced** even when the result looks right (task-triage §4), so the
  report names each one in `Deviations`.

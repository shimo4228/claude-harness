# Kickoff packet — S1: RFC-0030（Eval カード 1 枚目と docs/evals の形式定義）

あなたは task-triage loop の **build 役**です。
cwd は `~/.claude` の git worktree（branch は Agent tool が作ったもの）。成果は branch 上の commit で返し、
判断役が検収して main へ ff-only 取り込みます。境界（人間に渡す操作 / とってよいリスク / 止まる
条件）は rule `boundary.md` — build は task branch まで。packet に無いことは harness の規約が既定。

最初に読む: `rfcs/0030-eval-cards-for-ready-instruments.md`、`.notes/s1-eval-native-reading-2026-09-13.md`
（main の作業ツリーにある gitignore 下のファイル — worktree に無ければ `~/.claude/.notes/` から読む）、
`skills/skill-creator/SKILL.md` §5、`docs/adr/0085-plans-as-records-in-docs-plans.md` Decision 4（公開可能な書き方）。

Effort: low — docs のみ、仕様（下の Goal）が細かい

## 進め方
- 入力が要らない step は止まらずに続ける。止まるのは Phase 0 の反証、time cap、この packet の外の操作が要るときだけ
- 確かめられなかったことには「未確認」と印を付け、どこを見たかを書く
- 方針を選んだ箇所は、その理由を 3 文で Report の Fix に書く

## 判断役が決めたこと（著者確認済み、2026-09-28）
- 置き場所は `docs/evals/`。公開は後で claude-harness の同期対象に `docs/evals` を足して harness-sync で出す（この build の範囲外）
- 形式は自前 markdown。外部形式は採らず、欄の**名前だけ**借りる（search-first 2026-09-28 の結論）:
  - 生の読み値: `claude plugin eval` の `aggregate-result.json`（schemaVersion 1、https://code.claude.com/docs/en/plugin-evals）の
    `claudeVersion` / `cases[].aggregates.score` / `delta` / `arms.with` / `arms.without` / `scored` / `partial` / `costUsd` / `durationSeconds`
  - 環境・由来: Every Eval Ever schema v0.3.0（https://github.com/evaleval/every_eval_ever）の `source_type`（生値が消えたカードは
    `documentation`）/ `evaluator_relationship`（`first_party`）/ `eval_library{name,version}` / `evaluation_timestamp`（測った日）と
    `retrieved_timestamp`（カードを起こした日）/ `uncertainty.num_samples` / `generation_args.execution_command`
  - 事後の訂正: Inspect AI EvalLog（https://inspect.aisi.org.uk/eval-logs.html）の `log_updates` の考え方
  - 節立ての抜け検査: Evaluation Cards（arXiv 2606.09809）の lifecycle 5 区分
- 有効性の状態語は台帳と別の 3 語: `再現済み` / `単発` / `不成立`。s1 は `単発`
- Jev を含む数値・読み値は公開してよい。非公開なのは `.notes/` の生の中身そのものと、第三者の本文だけ

## Goal（決定可能な受入条件）
1. `docs/evals/README.md` がある。中身は: 何のための置き場か 2〜3 行 / カードの固定見出し 6 つ（`## 設計` `## 環境` `## 生の読み値`
   `## 測らなかったもの` `## 既知の故障` `## 有効性の状態`）とそれぞれに書くもの 1 行 / frontmatter のキー一覧 / 状態語 3 つの定義 1 行ずつ /
   借りた名前の出典表（キー → 形式・版・URL）/ index 表（`| [slug](file) | 計器 | 状態 |`、1 行目が s1）
2. `docs/evals/s1-headline-craft-native-ablation-2026-09-13.md` がある。frontmatter に `origin: shimo4228` と README が定めたキー、
   本文は 6 見出しがこの順で並び、末尾に「このカードの欄 → aggregate-result.json / EEE / Inspect の対応表」
3. カードの数値が読みメモと一致する: with 0.556 / without 0.000 / delta +0.556、run 別 1.00・0.333・0.333（= 5/9 の導出を 1 行で）、
   grader 別の pass/fail、cost $0.9919（arm 別 $0.661 / $0.331、judge $0.058）、run 壁時計 310 秒、CLI 2.1.270、judge haiku、`--runs 3`
4. 「既知の故障」に少なくとも: 生の出力（report.html・`--json` の result.json）が scratchpad ごと消失し残るのは読みメモだけ /
   defer 先（writing-ecosystem・title-reviewer）が隔離された run に無いことによる with arm の偽陰性（公式 docs が user の skills を
   run に load しないと明記 — 上の URL）/ `--threshold` 既定 1.0 で exit 1 / tool trace は `--keep-temp` 無しで消える
5. `grep -rn '/Users/\|/private/tmp' docs/evals` が 0 件（パスは `~/` で書く。scratchpad のセッション UUID は書かない）
6. `./.claude/verify.sh` 引数なしで exit 0、`python3 scripts/hooks/harness_lint.py` が通る

## Phase 0 — 前提の再照合（反証されたら実装せず止めて報告）
- 読みメモが存在し、§3 の結果表と grader 別表が上の数値どおり（`.notes/s1-eval-native-reading-2026-09-13.md`）
- `docs/evals/` がまだ無い
- `skills/skill-creator/SKILL.md` §5 が native eval を screening として使うと書いている（カードの「計器の使われ方」の根拠）

## Build（順序）
1. README（形式定義）を先に書き、カードはそれに従って書く
2. 読みメモにない値は書かない。推測で埋めず「未記録」と書く
3. case の prompt と grader の全文は読みメモから写してよい（著者自作の文面）
4. verify: `./.claude/verify.sh` exit 0

## Review
- 種別: chore（docs）。chain は skill `implementation-chain` の Chain Matrix に従う
- packet に書いていないことは harness の規約が既定。省略・読み替えは可だが、報告に「逸脱: 何を・なぜ」と名指しする
- diff 外の気づきは `rfcs/` にも台帳にも書かない。再現手順を書けるものは Report の `Proposed tasks`（最大 2 件）、書けないものは
  `Out-of-diff findings` に 1 行ずつ

## Must-not
- `docs/evals/` 以外を変えない（この packet のファイルも編集しない — dispatch 時点で凍結した契約）
- `.notes/` を commit しない・コピーしない（カードに要る値を写すだけ）
- `.claude/verify.sh`・`.github/`・`settings.json` を変えない ; `git add -A` を使わない ; `rfcs/` の state は判断役が書く
- claude-harness（公開 repo）に触らない ; push しない
- 60 分を超えたら打ち切って、そこまでの diff で報告

## Report（最終 commit の message 本文）
docs(evals): <summary> (RFC-0030)

Packet: S1
Plan: docs/plans/rfc-0030-s1-eval-card-ablation.md
Needs from judge: <…/ none>
Model: <この session のモデル名>
Effort: <実際に走った effort。分からなければ「未確認」>
Premise: <Phase 0 の結果>
Fix: <what and why>
Verify: <command exit / 日時>
Review: <回した reviewer と結果> / Deviations: <none か名指し>
Risk: <戻し方>
Proposed tasks (for the judge, 最大 2 件): <none か各件>
Out-of-diff findings (for the judge): <none か 1 行ずつ>

最後のメッセージは「判断役に要るもの」から始め、branch 名・commit SHA・verify の結果・所要時間を報告して終了してください。

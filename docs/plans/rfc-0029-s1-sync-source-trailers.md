# Kickoff packet — S1: RFC-0029（claude-harness への同期で、source commit の trailer を同期 commit の本文へ写す）

あなたは task-triage loop の **build 役**です。
cwd は `claude-harness`（`~/MyAI_Lab/claude-harness`）の git worktree（branch `task/rfc-0029-s1`）。成果は branch 上の
commit で返し、判断役が検収して main へ ff-only 取り込みます。境界（人間に渡す操作 / とってよいリスク / 止まる
条件）は rule `boundary.md` — build は task branch まで。packet に無いことは harness の規約が既定。

最初に読む: `~/.claude/rfcs/0029-carry-commit-trailers-to-public-mirror.md`、`~/.claude/rfcs/0028-correction-commit-trailers.md`
（`指摘:` / `Trigger:` / `Expect:` ブロックの形）、この worktree の `scripts/sync-from-local.sh`（特に冒頭の説明、`SUBTREES`、
secret scan と home-directory path scan の節）、`~/.claude/skills/harness-sync/SKILL.md` の「### 5. コミット」。

Effort: high — git log の本文を parse し、公開前の scan を通す diff

## 進め方
- 入力が要らない step は止まらずに続ける。止まるのは Phase 0 の反証、Review の CRITICAL、time cap、この packet の外の操作が要るときだけ
- 確かめられなかったことには「未確認」と印を付け、どこを見たかを書く
- 方針を選んだ箇所は、その理由を 3 文で Report の Fix に書く

## 著者が承認した既定（2026-10-25 triage）
- 写す trailer: `Review` / `Context` / `Decision` / `Review-when` / `Plan` と、`指摘` / `Trigger` / `Expect`。それ以外は写さない
- 列挙: 同期 commit の本文に `Source: <source の HEAD sha>` 行を置く。次の同期は、この repo の最新の `Source:` 行の sha から
  source の HEAD までの commit のうち、同期対象（今回 staging に入ったパス）を触ったものを列挙する。`Source:` 行が無い初回だけは、
  この repo の最新の `chore: sync from local harness` commit の日時以降を数える
- 写す本文も secret scan と home-directory path scan を通し、当たれば abort する（既存の scan と同じ扱い）

## Goal（決定可能な受入条件）
1. 適用モード（`--dry-run` なし）の `scripts/sync-from-local.sh` が、commit 本文の下書きを `.git/` の中（例: `.git/SYNC_COMMIT_BODY`）に
   書き、その path を stdout に出す。下書きは source commit ごとに `<short sha> <subject>` と、その commit が持つ上の 8 種の
   trailer だけを並べ、最後に `Source: <source の HEAD の full sha>` を置く。`指摘:` ブロックは複数行（`指摘:` に続く `Trigger:` / `Expect:`）を
   1 件として保つ
2. `--dry-run` は列挙した commit 数と trailer 数を 1 行で報告し、ファイルを書かない
3. 下書きに secret の形か `$HOME/` の実値が入ると、既存の scan と同じ文言の形で abort する（exit 非 0）
4. テスト `scripts/tests/sync-trailers.bats`（`tests/` は同期で丸ごと置き換わる subtree なので、その外に置く）が、fixture の source
   git repo を一時ディレクトリに作り、少なくとも次を確かめて全件 pass する: (a) `Source:` 行がある場合の範囲、(b) 初回の日時 fallback、
   (c) 同期対象外のパスだけを触った commit が出ない、(d) 8 種以外の trailer が出ない、(e) `指摘:` の複数行ブロック、(f) `$HOME/` を含む
   trailer で abort
5. `bats scripts/tests/sync-trailers.bats` と、既存の `bats tests/` が exit 0。`shellcheck scripts/sync-from-local.sh` は変更前より警告を増やさない
   （shellcheck が無ければ「未確認」）

## Phase 0 — 前提の再照合（反証されたら実装せず止めて報告）
- `scripts/sync-from-local.sh` は source の commit 本文を読んでいない（`git -C "$SOURCE_DIR" log` の呼び出しが無い）
- この repo の直近の同期 commit（`git log -3 --format=%B`）に、source の sha を機械的に読める行が無い
- `scripts/` のうち同期で置き換わるのは `scripts/hooks/` だけ（`SUBTREES`）で、`scripts/tests/` は置き換わらない

## Build（順序）
1. TDD: `scripts/tests/sync-trailers.bats` を先に書き、RED を確かめる
2. 実装。列挙と抽出は 1 箇所（関数か `scripts/` 直下の補助 script）に置く。補助 script を足すなら `SUBTREES` の外に置く
3. 冒頭の説明コメント（Usage の節）に、下書きファイルと `Source:` 行の役割を足す
4. verify: Goal 5 のコマンド

## Review
- 種別: feat。chain は skill `implementation-chain` の Chain Matrix に従う。security-reviewer 必須 — 公開前の scan の経路を動かすため
- **packet に書いていないことは harness の規約が既定**。省略・読み替えは可だが、報告に「逸脱: 何を・なぜ」と**必ず名指し**する
- diff 外の気づきは `rfcs/` にも台帳にも書かない。再現手順を書けるものは Report の `Proposed tasks`（最大 2 件）に、書けないものは
  `Out-of-diff findings` に 1 行ずつ（HIGH は producer `file:line` 付き）

## Must-not（境界）
- 変えてよいのは `scripts/sync-from-local.sh`、`scripts/` 直下の新しい補助 script、`scripts/tests/` だけ
- 同期で置き換わる subtree（`skills` `agents` `rules` `docs/adr` `docs/plans` `docs/evals` `rfcs` `hooks` `scripts/hooks` `tests`）と
  `docs/components*.md`・README・llms*.txt を変えない。main の作業ツリーにある未 commit の変更には触れない
- `~/.claude` の中を変えない（harness-sync の SKILL.md の更新は判断役が merge 後に行う）
- 同期を実際の公開 repo に対して適用モードで走らせない（テストは fixture だけで行う）
- テストを弱めない・消さない ; `git add -A` を使わない ; この packet のファイルを編集しない
- main に merge・push しない
- 2 時間を超えたら打ち切って、そこまでの diff とテスト状況で報告

## Report（最終 commit の message 本文）
feat(sync): <summary> (RFC-0029)

Packet: S1
Plan: ~/.claude/docs/plans/rfc-0029-s1-sync-source-trailers.md
Needs from judge: <… / none>
Model: <この session のモデル名>
Effort: <実際に走った effort。分からなければ「未確認」>
Premise: <再照合の結果>
Fix: <what and why>
Regression: <test names, RED→GREEN の確認方法>
Verify: <command exit / test counts / 日時>
Review: <回した reviewer と結果> / Deviations: <none か名指し>
Risk: <戻し方>
Proposed tasks (for the judge, 最大 2 件): <none か各件>
Out-of-diff findings (for the judge): <none か 1 行ずつ>

最後のメッセージは「判断役に要るもの」から始め、commit SHA・verify の結果・所要時間を報告して終了してください。

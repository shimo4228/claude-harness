# ADR-0099: 検査の正本は GitHub の CI、中身の正本はローカルの ~/.claude — cloud の diff は判断役が別 process で review し、merge はローカルの ff-only

## Status

accepted — [ADR-0075](./0075-cloud-session-as-default-build-executor.md) の Decision 2（cloud の build session が自分の diff に
built-in `/code-review` を回す）を置き換える。Decision 3（verify は CI）と Decision 6（PR は view、merge は ff-only）は変えず、
harness 自身（claude-config）に適用する。ADR-0075 に注記する

## Date

2026-11-01

## Context

- 著者（2026-11-01）: 「Cloud セッションの PR を自動でレビューしてほしい」。続けて「.claude って現状 CI で Verify せずに Hook で
  Verify してるよね。implementation-chain との兼ね合いも微妙だな」「もう GitHub 前提でチェーンを組んだ方が汎用性も高いかな？」
  「リモートの claude-config が正本になるけど、ローカルの .claude と齟齬が出たりしない？」
- ADR-0075 Decision 3 は「cloud に出す repo は `.github/workflows/verify.yml` を持つ。CI を持たない repo は cloud に出せない」と
  定める。2026-11-01 時点の claude-config（private）は `.github/workflows/` を持たないまま、cloud の PR を 4 本取り込んでいた
  （#1・#3・#4・#5）。verify はローカルの commit hook（`hooks/verify-precommit.sh`）でしか走らず、cloud の clone と GitHub の
  Merge ボタンはその hook を通らない。#4（`f10b926`）と #5（`190dc54`）は Merge ボタンの merge commit で入っており、
  Decision 6 の ff-only とも食い違う
- ADR-0075 Decision 2 の review は build session 自身が built-in `/code-review`（effort medium）を回す形で、medium は同じ context の
  中で走る。rule `agents.md` の「Review は実装者と別の agent process で走らせる」を cloud の build は満たしていなかった
- 公式 docs（2026-11-01 照合: code.claude.com/docs/en/code-review.md、github-actions.md、routines.md）: 管理型の Code Review は
  Team / Enterprise の組織だけで、個人の Max アカウントは使えない。`anthropics/claude-code-action` は `CLAUDE_CODE_OAUTH_TOKEN` で
  公式 `code-review` plugin を PR ごとに回す workflow の例を載せている
- その形の `review.yml` を一度書き、3 本の review（adr-reviewer・security-reviewer・`/code-review` medium、2026-11-01）に通した。
  見つかったこと: (a) 公式 plugin は Claude のコメントが既にある PR を skip し、run は `success` で終わる — 差し戻しの後の修正
  commit は review されないまま「review 済み」に見える。(b) repo secret は、どの branch でも workflow ファイルを push できる者が
  読める。cloud の build session は prompt injection を受けうる LLM で、packet の must-not（`.github/`）は機械で執行されない。
  検収の bounce は merge を止めるが、secret の漏洩は push の時点で起きる。(c) 投稿には Claude GitHub App の導入が要り、
  plugin と marketplace は git の HEAD から入って SHA で固定されない
- `gh api repos/shimo4228/claude-config/rulesets` は「Upgrade to GitHub Pro or make this repository public」（HTTP 403）を返す。
  無料プランの private repo では「CI が通らないと merge できない」を GitHub 側で強制できず、environment の branch 制限も使えない
- Claude Code が実行時に読むのはローカルの `~/.claude` の作業ツリーで、`.notes/`・metrics・`settings.local.json` は git に入らない。
  `scripts/cloud-dispatch.sh:84` は、ローカルの main が origin/main より先にあると dispatch を止める
- `.claude/verify.sh` はツールが無い検査を飛ばす（ローカルの機械向けの fail-soft）。markdownlint は `.claude/verify.md` で
  advisory（未導入なら skip）と決めてある。`tests/transcript-last-turn.bats:24` は BSD の `date -j` を使っていて、GNU の
  ubuntu では落ちる

## Decision

1. **正本を 2 つに分ける。** 中身（skills・rules・hooks・agents・ADR）の正本はローカルの `~/.claude`。remote の claude-config は
   その写しで、CI を走らせる場所。verify の結論の正本は GitHub の CI。ローカルの commit hook は同じ `.claude/verify.sh` を
   走らせる早い結果返しで、secret scan は push より前に止める必要があるのでローカルに残す

   > **注記（2026-11-07, [ADR-0100](./0100-executor-by-model-and-task-context-local-fresh-build.md)）**: build の既定が local の Agent になった。local の build の検収は判断役が worktree で走らせる
   > `verify.sh` の結果で行い、「verify の結論の正本は GitHub の CI」は local の build では push の後の事後の検査になる（cloud を選んだ
   > build には本 Decision と Decision 2 の CI の形が掛かる）。中身の正本はローカル、merge はローカルの ff-only（Decision 4）は不変。

2. **claude-config に `.github/workflows/verify.yml` を置く。** `main` と `claude/**` への push（と手動）で `.claude/verify.sh` を
   無引数で呼ぶ（ADR-0075 Decision 3 の形。actions は SHA pin、`permissions: contents: read`、`persist-credentials: false`、
   gitleaks の job 同居。repo secret は使わない）。verify の job は著者の Mac に合わせる: macOS の runner、`LC_ALL=C`、checkout を
   `~/.claude` に link、行き先の無い symlink skill（外部ツールの install 先を指すもの）を外す。workflow は uv・uvx・shellcheck・
   bats・cargo・detect-secrets・timeout の有無を先に検査し、欠ければ赤にする。markdownlint は verify.md の決定どおり advisory の
   まま CI でも skip する。BSD 専用の `date -j` を使う test は定数に書き換える
3. **review は判断役が検収（skill `task-triage` §4）で別 process に回させる。** `Agent(general-purpose, model: opus)` の中で
   built-in `/code-review` を effort medium で、`origin/main..origin/claude/<name>` の範囲に回す。差し戻しの後は新しい commit の
   範囲にもう一度回す。cloud の build session は自分の diff を review しない（packet の Review 節。`skills/task-triage/references/packet-template.md`）。
   PR 上の review workflow と repo secret は置かない

   > **注記（2026-11-07, [ADR-0100](./0100-executor-by-model-and-task-context-local-fresh-build.md)）**: 判断役の review は cloud の build だけでなく全 build に掛かる。background の subagent は Agent tool を
   > 持たず、build の中から別 process の review を起こせないので、build は Review 行を回さず、脅威面に触れる diff の security-reviewer も判断役が回す。

4. **merge はローカルの ff-only だけ。** 判断役が branch tip の verify run（`--workflow verify.yml`）と review の結果を読み、
   `git merge --ff-only origin/claude/<name>` + push で取り込む。GitHub の Merge ボタンは使わない（取り込む場所をローカルの
   1 か所にすると、remote が先に進んでローカルが古い skill で動く食い違いが起きない）。採った review の指摘は同じ session へ
   差し戻し、指摘の件数と採った数、採らなかった指摘とその理由を `claims.py release` の ledger 行に書く。
   差し戻しの後の review は新しい commit の範囲だけで、前の review が通した部分との相互作用は判断役が diff を読んで見る
5. **GitHub に出せない作業はローカルのチェーンのまま。** 条件の正本は skill `task-triage` §3 の表（launchd・`.notes/`・
   ローカルのモデル・macOS 専用のツール）
6. **変える artifact**: `.github/workflows/verify.yml`（新設）、`tests/transcript-last-turn.bats`（期待値を定数に）、
   `skills/task-triage/SKILL.md`（§3 の packet、§4 の verify の読み方と review、§5 の merge の場所）、
   `skills/task-triage/references/packet-template.md`（Review 節と報告行）、`skills/implementation-chain/SKILL.md`（実行者の決定の
   dispatch 先）、ADR-0075 への注記。**変えないもの**: `hooks/verify-precommit.sh`・`secret-scan-precommit.sh`、
   `.claude/verify.sh`、`rules/common/boundary.md`

## Review-when

- macOS の runner の消費が Actions の無料枠を圧迫したら（GitHub の Billing の Actions 使用量で著者が見る）、ubuntu の runner と
  CI で飛ばす検査の表（CA の形）に移すかを決める。ubuntu では cloud-dispatch・secret-scan-precommit・validate-bash-verify-approve の
  bats が赤だった（run 41302398596）
- CI の verify のログに `型検査をスキップ`（`uv sync` の失敗で ty が飛ぶ経路）が出たら、その sub-project の依存を直すか、CI では
  その skip を赤にする
- claude-config を public にするか GitHub Pro にしたら、ruleset で verify の check を必須にし、Decision 4 を「Merge ボタンも
  ruleset が止める」に緩めるかを 1 回問う
- 判断役の手元の review が 10 本の cloud build で correctness に効く指摘を 1 件も出さなかったら（数えるのは `claims.py release` の
  ledger 行の `review: <n> findings, <k> accepted`）、review の置き場所を再訪する
- 管理型の Code Review が個人のプランでも使えるようになったら（code.claude.com/docs/en/code-review.md の Availability）、
  それに置き換えるかを問う。その時も repo secret の露出（Context (b)）を先に確かめる
- cloud の build session の push が `.github/workflows/` を変更できるかを、捨て branch で一度実測する。できるなら、branch 側の
  workflow が `permissions: contents: write` を宣言して `GITHUB_TOKEN` で `main` に push する経路が開いている（本 ADR で増えた
  経路ではない）。その時は claude-config の repo 設定で workflow の既定権限を見直し、本 ADR に注記する

## Alternatives Considered

- **PR 上の review workflow（`claude-code-action` + 公式 `code-review` plugin、repo secret `CLAUDE_CODE_OAUTH_TOKEN`）**: 公式 docs の
  例そのままで、PR を開くだけで review が付く。一度書いて review に通し、却下 — Context (a)〜(c): 差し戻しの後の commit を
  review しないまま `success` になる、secret が workflow を push できる者すべてに読める、App 導入と plugin の未固定が残る。
  Open — revisit when: private repo で environment の branch 制限か ruleset が使えるようになり、plugin を版で固定できる
- **cloud の routine（`pull_request.opened` トリガー）で review する**: Max で使え、repo secret も Actions の時間も使わない。却下 —
  prompt に PR 番号が渡るか、cloud の中で `--comment` が投稿まで通るかが docs で確かめられず、差し戻しの後の commit に
  もう一度回す方法も docs に無い。Open — revisit when: routine の docs に PR のイベント値と再実行の例が載る
- **build session の自己 review（ADR-0075 Decision 2）のまま、CI の verify だけ足す**: 判断役の手間が増えない。却下 — 実装者と同じ
  context で走る review は rule `agents.md` の別 process の条件を満たさず、著者の依頼（PR の自動 review）にも答えない
- **GitHub Pro にして ruleset で merge を強制する**: Merge ボタン経由の取り込みも止まる。却下 — 課金は著者の判断（boundary.md）で、
  Decision 4 の運用で取り込む場所をローカルの 1 か所にすれば強制が無くても食い違いは起きない
- **claude-config を public にする**: ruleset と Actions の無料枠が使える。却下 — harness の公開 copy は origin filter 付きの
  claude-harness が担い（skill `harness-sync`）、claude-config は filter を通らない全履歴を持つ
- **中身の正本も remote に移す（GitHub 上で merge し、ローカルは pull するだけ）**: GitHub 前提の流れとしては最も素直。却下 —
  Claude Code が読むのはローカルの作業ツリーで、git に入らない状態もローカルにしか無い。remote が先に進むと、pull するまで
  古い skill が動き、その間のローカルの commit で履歴が分かれる
- **何もしない（hook の verify だけ）**: 追加の費用が無い。却下 — cloud の PR が verify を通らずに main に入る状態が続き、
  ADR-0075 Decision 3 の前提と食い違ったままになる

## Consequences

- 良くなること: cloud・ローカルのどの経路で push された変更にも、同じ verify が push の時点で当たる（結果を読んで
  止めるのは判断役）。cloud の build は実装者と別の process で review され、差し戻しの後の commit も review の範囲に入る。
  verify の workflow は repo secret を持たないので、branch 側から抜ける資格情報が増えない。中身の正本と取り込む場所が
  ローカルの 1 か所なので、remote との食い違いは `cloud-dispatch.sh` の検査（ローカルが先）と、push の non-fast-forward
  拒否と ff-only（remote が先）で止まる
- 悪くなること: review は自動では付かず、判断役が検収を回したときに走る（triage の cycle が回っていれば実質自動、回って
  いなければ PR は review されないまま待つ）。review のトークンは判断役の session の subagent が使う。push ごとに macOS の runner で
  verify が走り（1 回 1 分半ほど、run 41303031188）、Actions の無料枠を ubuntu より速く減らす。CI の verify は著者の Mac の環境
  （locale・path・ツール）を workflow で写しているので、Mac の側が変わると CI が古い前提のまま赤になる。Merge ボタンを使わない
  ことは強制されず、判断役と著者の規律に残る
- 戻すとき: `.github/workflows/verify.yml` を消し、task-triage と packet-template の Review 節を ADR-0075 Decision 2 の形に戻す
  （1 commit の revert で戻る）

# ADR-0090: skill の経緯と出典は同封の MAINTENANCE.md に置き、SKILL.md からリンクせず、公開しない

## Status

accepted — [ADR-0061](./0061-prompt-audit-version-diff-markers-and-lint-gate.md) Decision 1 の「経緯は ADR・本文は規則」と
Consequences の「現行規則 + 理由 + ADR 番号」の形を部分的に狭める（ADR 番号と経緯の置き場を `MAINTENANCE.md` へ）。
ADR-0061 に注記する

## Date

2026-10-07

## Context

- 2026-10-07 時点（本 ADR の diff を含む）で `skills/*/SKILL.md` は ADR 番号を 157 か所で書く（`grep -ohE 'ADR-[0-9]{4}' skills/*/SKILL.md | wc -l`）。
  うち括弧の中が ADR 番号だけの札が 43 か所（`grep -ohE '[（(]\[?ADR-[0-9]{4}\]?(\([^)]*\))?[）)]' skills/*/SKILL.md | wc -l`）
  で、周りの文に理由が無ければ ADR を開くまで理由が分からない
- 同日の skill-stocktake で skill `herdr-delegate` を退役したとき、`rules/common/agents.md` の「正本は herdr-delegate
  §3」が参照先ごと消えた。行動に必要な規則を他の file に委ねると、委ねた先が消えたときに規則も消える。
  `rules/common/agents.md` 側の規則は同日本文に書き戻した。`grep -nE '正本|canonical' skills/*/SKILL.md | grep -E
  'ADR-[0-9]{4}|RFC-[0-9]{4}|docs/adr|rfcs/'` の 13 行（本 ADR の diff を含む worktree）を読んで分類した範囲では、行動に
  必要な値や規則を ADR に委ねている箇所は無い（例えば `skills/verify-bootstrap/SKILL.md` の「正本は ADR-0056」は実測値
  の出典で、行動の指示は本文にある）
- 単独の公開 skill repo（例: `~/MyAI_Lab/signal-first-research`）は ADR を同梱しないので、本文の ADR 番号は外の
  読者には参照切れになる。集約 repo `~/MyAI_Lab/claude-harness` は `docs/adr/` を同梱する
- 外部の慣行（2026-10-07 に本文を読んで確認）:
  - agentskills.io の仕様（https://agentskills.io/specification）— 参照は skill root からの相対パスで 1 段まで
  - Anthropic の skill 作成ベストプラクティス
    （https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices）— 時間で古びる情報を本文に
    書かず、経緯は折りたたんだ「Old patterns」節に分ける
  - anthropics/skills の skill-creator — 頼むことの why を本文で説明する
  - getsentry/skills の README — 実行時の指示は `SKILL.md`、保守の約束は `SPEC.md`、出所は `SOURCES.md` に分け、
    いずれも skill の directory 内に置いて公開する
  - 本文から外部の設計記録を参照することを勧める一次資料は、この範囲では見つからなかった
- 著者の判断（2026-10-07）: 経緯と出典は skill の directory に別 file で同封し、公開から外し、保守するときだけ
  読む。file 名は `MAINTENANCE.md`

## Decision

1. 各 skill は directory に `MAINTENANCE.md` を持てる。中身は ADR / RFC 番号とその skill に効く理由 1 句、出典、
   置き換えた旧版、保守メモ。判断の経緯の正本は ADR で、`MAINTENANCE.md` はそこへの索引にとどめる
2. `SKILL.md` は `MAINTENANCE.md` にリンクしない。本文は単体で実行できるように書く — 現在の規則と理由 1 句。
   行動に必要な値や規則を skill の directory の外（ADR・rule の節）に委ねない。他の skill に仕事を任せる
   pointer はこれに当たらない
3. 読むのは保守するとき。skill `skill-creator` は既存 skill を改修する前に `MAINTENANCE.md` を読む（§1）、
   §3 の書き方は番号・出典・経緯の置き場を `MAINTENANCE.md` にする。skill `skill-stocktake` の Phase 2 は
   Currency で `MAINTENANCE.md` も読み、Hygiene で本文が単体で動くかを問う
4. 公開の同期 script のうち skill の directory を写す 28 本（`~/MyAI_Lab/*/scripts/sync-from-local.sh` と
   `~/MyAI_Lab/jev-skill-router/tools/sync-from-local.sh`。単一 file を写す authorship-strategy-rules と human-gate の 2 本は
   対象外）は、staging の掃除の `find … -delete` に `MAINTENANCE.md` を足す。本 ADR と同時に各 repo の作業ツリーへ
   入れた — 同期は作業ツリーの script を実行するので、公開 repo 側の commit と push（著者）の前から効く。skill
   `harness-sync` に apply 前の確認（staging に `MAINTENANCE.md` が無いこと）を足すのは skill `harness-sync` の改修の回に
   行い、本 ADR の commit では行わない
   > **注記（2026-10-07, commit「chore(skills): skill-stocktake 2026-10-07 の改修 15 本と harness-sync」）**: 後半の確認は
   > apply 前でなく commit 前に置いた — script は staging から公開 repo への置換まで一度に行い、公開されるのは commit と
   > push の時点なので、skill `harness-sync` は手順 5 で `find <公開repo> -name MAINTENANCE.md` が空であることを確かめる。
   > Review-when の「apply 前」も同じ意味で読む
5. 移行は一括にしない。skill `skill-creator` が skill を改修するとき、その skill の ADR 番号と経緯を
   `MAINTENANCE.md` へ移す
6. `scripts/hooks/harness_lint.py` の skill 検査に、`SKILL.md` が `MAINTENANCE.md` へリンクしていたら指摘を
   足す（回帰は `tests/harness-lint-precommit.bats`）。検査は markdown のリンクだけを見る — 地の文で「`MAINTENANCE.md`
   を読め」と書く形は通る

## Review-when

- 2027-04-07 までに、理由が `MAINTENANCE.md` にしかない規則を改修者が読まずに戻した事故を 2 回観測したら（記録先:
  その回の commit 本文か `.notes/TASKS.md`。見つけるのは skill-stocktake の Phase 2 — Currency で `MAINTENANCE.md`
  と本文を突き合わせる）、改修時に読ませる hook を足す
- `MAINTENANCE.md` が公開 repo に 1 度でも出たら、除外を script の掃除と apply 前の手順でなく機械ゲートにする
- 2026-10-21 までに skill `harness-sync` に apply 前の確認（Decision 4 の後半）が入っていなければ、著者に未了を
  報告する（判定は次の skill-stocktake か task-triage の判断役）
- Agent Skills の仕様か Claude Code が、skill の経緯・出所の置き場を native に持ったら、そちらへ移す

## Alternatives Considered

- **現状維持: 本文に ADR 番号の札を残す**（理由を 1 句添えて索引にする形も含む）— 却下。単独の公開 repo で番号が
  参照切れになる
- **行動に必要な中身の委託だけを禁じ、ADR 番号の札は本文に残す** — 却下。同じく公開版で参照切れになる
- **本文から ADR 番号を全廃し、参照は ADR から skill への一方向にする** — 却下。改修者が規則の理由に
  たどり着く道が `git log` の検索だけになり、読まずに戻す危険が増える
- **同期 script が公開時に本文の ADR 番号を消す・書き換える** — 却下。file は増えないが、公開版とローカル版の本文が
  別物になり、公開版の文を誰も通読しない。本文に経緯が残り、実行時に読まれる問題も残る
- **ADR 番号を claude-harness 公開 repo の `docs/adr/` への絶対 URL にする** — 却下。参照切れは避けられるが、経緯が
  本文に残って実行時に読まれる。公式ベストプラクティスが本文から外すよう勧める時間依存の情報にもなる
- **getsentry/skills と同じく `SPEC.md`（と `SOURCES.md`）として公開する** — 却下。ADR 番号の部分は harness の外で
  意味を持たない。出典と経緯は外でも意味を持ちうるが、公開しないのは著者の判断による（この範囲で読んだ一次資料に、
  経緯を公開しない根拠は無い）

## Consequences

### Positive

- 移行を終えた skill は `SKILL.md` が実行に要る中身だけになり、単独の公開 repo でも参照切れが出ない
- 規則の理由と経緯が skill の directory から離れず、改修するときに 1 か所を読めばよい

### Negative

- 移行は改修のたびに進むので、それまで既存の ADR 番号（157 か所）は公開版の本文に残る
- skill ごとに file が 1 つ増え、`SKILL.md` との間、ADR との間で記述がずれうる（正本は Decision 1 のとおり ADR）
- `~/.agents/skills` は `skills/` を丸ごと他の agent に見せる（ADR-0012）ので、`MAINTENANCE.md` は Codex などから
  見える
- 改修者が `MAINTENANCE.md` を読むかは skill `skill-creator` の手順だけが担う。読まない改修は機械では止まらない
- 同期 script 28 本の変更は公開 repo 側の commit になり、著者の作業が増える
- 本 ADR を戻すには、skill `skill-creator`・`skill-stocktake`・`scripts/hooks/harness_lint.py`・同期 script 28 本と、
  移行済みの各 `MAINTENANCE.md` を直す必要がある

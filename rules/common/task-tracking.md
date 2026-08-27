<!-- origin: shimo4228 -->
<!-- rationale: ADR-0035 で手順を task-stocktake へ移し path だけ常駐。CA ADR-0095 (2026-08-16) で 3 層機構を退役し、store 形式と claims.py だけを残した。同日、起票の条件を severity から前提の検証へ移した (T-PACKET-FLOOR-BYPASS)。同日の棚卸しで状態語彙を 6→4 に縮約 (deferred / observing 廃止) し、語彙の正本を skill 一箇所に定めた — 4 文書に分散した語彙は所有者が不在で誰も刈らなかった -->
<!-- review-when: harness native task store が出た時、repo の台帳 path を変えた時、台帳の読み書きに再びコードが要ると感じた時（要件を先に疑う）、--producer を満たす引用が「形だけ通す」ようになった時（次の 20 発火の処分内訳で測る）、rfcs/ への流入が 3 ヶ月 0 の時（ADR-0049 の Review-when） -->
# Task Tracking

Pending task の正本は repo ごとに 1 つ。新設・統合・archive の手順は
skill: `task-stocktake` が持つ。形は 2 つ:

- **単一表** `.notes/TASKS.md` — 小さい repo。そのまま読む
- **store** 公開 `rfcs/NNNN-slug.md` — 1 タスク 1 ファイル（提案も作業も 1 店舗）、
  ID は `RFC-NNNN`。frontmatter に `state:`
  （開: `draft` / `accepted` / `in_progress` / `blocked`、終端: `done` / `resolved` /
  `rejected` / `withdrawn` / `obsoleted` — 標準語彙、ADR-0050。日付を続けてよい）、
  本文は自由記述（推奨様式は Rust RFC
  テンプレ準拠）。**語彙の正本は skill: `task-stocktake`**（各語の定義・`blocked` の
  入場条件・終端語の使い分け）、**起票の正本は skill: `rfc-writer`**（足切り・採番・
  様式・公開規約・index 規約）。ここには複製しない — 分散した版は誰も刈らず肥大する。
  並行セッションが別タスクを消せない置き方
  （先例: contemplative-agent、2026-08-15）。旧 store `.notes/tasks/` は 2026-08-25 に
  廃止（全 repo 移送完了、dual-read も畳んだ — RFC-0001）

store の repo では**全件を読まない**: `python3 ~/.claude/scripts/claims.py ready` が
着手可能なタスクを 1 行ずつ出す（claim 中の印付き）。1 件の全文はそのファイルを読む。
台帳を扱うコードはこれで全部 — 描画・読み戻し・状態機械・aging は持たない
（持った版は 2 日で 5,000 行になり、そのバグを台帳に起票して直し続ける形になった。
CA ADR-0095）。肥大した台帳は機構でなく整理で解く — rfcs/ の終端エントリは archive
せずその場に残す（公開判断記録。`.notes/archive/tasks/` は旧 store 時代の歴史記録）。

## 並行セッション

着手前に `claims.py claim T-XXX --label "…"`、手放すとき
`release --outcome done|abandoned|handoff`。起票したら
`spawn --origin review|gate|instrument|idea|incident [--producer PATH:LINE] [--parent T-YYY]`
（`--origin review` では `--producer` が必須 — 下の「レビュー指摘の扱い」）。

lease（既定 24h）が切れた claim は `--force` なしで引き継げる。**期限切れ（STEALABLE）と
期限の宣言が無い古い claim（STALE）は別物** — 後者を奪う根拠にしない。

## レビュー指摘の扱い

台帳が純増する最大の入口。build セッションからの即時起票は **loop 自身を壊す欠陥**
（放置すると次の build が bounce を食う類）**のみ**。それ以外は severity 不問で commit
message に 1 行（producer 付き）残して捨てる — HIGH でも起票しない（実測の正本は
ADR-0055）。起票する場合も
producer→sink の `file:line` 引用（前提の検証）を先に置く — `spawn --origin review` は
`--producer PATH:LINE` が無ければ起票を拒否する。

実測の根拠・判断手順・破棄の基準は skill: `task-stocktake`「レビュー指摘の起票規律」が正本。

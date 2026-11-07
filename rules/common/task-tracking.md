<!-- origin: shimo4228 -->
<!-- rationale: 手順は task-stocktake が持ち、path だけ常駐。3 層機構を退役し、store 形式と claims.py だけを残した (2026-08-16)。同日、起票の条件を severity から前提の検証へ移した (T-PACKET-FLOOR-BYPASS)。同日の棚卸しで状態語彙を 6→4 に縮約 (deferred / observing 廃止) し、語彙の正本を skill 一箇所に定めた — 4 文書に分散した語彙は所有者が不在で誰も刈らなかった -->
<!-- review-when: harness native task store が出た時、repo の台帳 path を変えた時、台帳の読み書きに再びコードが要ると感じた時（要件を先に疑う）、--producer を満たす引用が「形だけ通す」ようになった時（次の 20 発火の処分内訳で測る）、rfcs/ への流入が 3 ヶ月 0 の時（経緯 0049 の Review-when） -->
# Task Tracking

Pending task の正本は repo ごとに 1 つ。新設・統合・archive の手順は skill: `task-stocktake` が持つ。形は 2 つ:

- **単一表** `.notes/TASKS.md` — 小さい repo。そのまま読む
- **store** 公開 `rfcs/NNNN-slug.md` — 1 タスク 1 ファイル（提案も作業も 1 店舗。並行セッションが別タスクを消せない）、
  ID は `RFC-NNNN`、frontmatter に `state:`。**状態語彙の正本は skill: `task-stocktake`、起票の正本は
  skill: `rfc-writer`** — 分散した版は誰も刈らず肥大するので一箇所に置く

store の repo では全件を読まず、`python3 ~/.claude/scripts/claims.py ready` で着手可能なタスクを 1 行ずつ出す
（claim 中の印付き）。1 件の全文はそのファイルを読む。台帳を扱うコードは claims.py だけに保つ（描画・状態機械を
持った版は 2 日で 5,000 行に膨らんだ）。肥大した台帳は整理で解き、rfcs/ の終端エントリはその場に残す（公開判断記録）。

## 並行セッション

着手前に `claims.py claim`、手放すときに `release`、起票したら `spawn`（flag は `claims.py <sub> -h`）。

lease（既定 24h）が切れた claim は `--force` なしで引き継げる。**期限切れ（STEALABLE）と
期限の宣言が無い古い claim（STALE）は別物** — 後者を奪う根拠にしない。

## レビュー指摘の扱い

build セッションからの即時起票は **loop 自身を壊す欠陥**（放置すると次の build が bounce を食う類）だけ。それ以外は、答えが一つに決まり
git で戻せるものをその場で直して別 commit にし（`boundary.md`）、残りは severity 不問で commit message に 1 行（producer 付き）残す。起票するときは producer→sink の `file:line` 引用を先に
置く（`spawn --origin review` は `--producer PATH:LINE` が無ければ拒否する）。例外・実測・破棄の基準の正本は
skill: `task-stocktake`「レビュー指摘の起票規律」。

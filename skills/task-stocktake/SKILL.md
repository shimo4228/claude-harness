---
name: task-stocktake
description: "Consolidate a repo's pending tasks into its one ledger and check each entry against the code. Use when taking stock of remaining tasks (残タスクの棚卸し), choosing a task state word, or deciding whether to file a review finding (起票). For judging and dispatching open tasks, use task-triage."
user-invocable: true
origin: shimo4228
---

# task-stocktake — Task Ledger Audit & Consolidation

repo の pending タスク追跡を**1 つの台帳**に収束させ、台帳の鮮度を git 実態と突合する。
原則の正本は rule `common/task-tracking.md`（pending task の正本は repo ごとに 1 つ。形は
単一表 `.notes/TASKS.md` か store `rfcs/NNNN-slug.md` の 2 つ）。そこから、詳細資料と
MEMORY.md はタスク行の正本を持たずポインタだけを持つ。本 skill はその手順を持つ。

## Phase 1 — Bootstrap（台帳の解決・作成）

1. 形を先に決める: repo トップに `rfcs/` があり、エントリが frontmatter に `state:` を
   持つなら **store 形**。台帳は `rfcs/` で、全件を読まず開いている 4 状態を
   `python3 ~/.claude/scripts/claims.py ready --state <state>` で 1 状態ずつ引く（`--state` 無しは
   `accepted` だけを出す）。単一表 `.notes/TASKS.md` が並存していても台帳は store — 単一表に
   残る pending 行は Phase 2 の sweep 対象（store への移送か終端かを報告する）で、行が尽きた
   単一表は store へのポインタ 1 行だけを残す。新しいタスクは skill: `rfc-writer` で `rfcs/` へ起票する
2. store が無ければ **単一表形**。`.notes/TASKS.md` → 既存タスクファイル（`TODO.md` /
   `TASKS.md` / `docs/backlog.md` 等）の順に解決し、見つかればそれを台帳と確定して Phase 2 へ
3. どちらも無ければ単一表を作成する。「作るか」は聞かない（skill の起動自体が依頼）— 確認するのは**置き場所だけ**:
   - `.notes/` 慣行がある repo は `.notes/TASKS.md`（gitignored = private）に即決。
     無い repo は gitignore 状況を見て private / git-tracked（clone 先でも cold-start 可能）の
     トレードオフを提示して選んでもらう
   - 初期内容: 下のフォーマットの見出しと空の表だけ。Phase 2 の sweep 結果は候補として示し、
     著者が選んだ行だけを載せる（Phase 2 末尾）

単一表のフォーマット（1 タスク 1 行）:

```markdown
# TASKS — <repo name>

> 正本: このファイル。詳細はリンク先。規約: rule common/task-tracking.md

## Pending

| ID | 状態 | タスク | 着手条件 | 詳細 |
|----|------|--------|----------|------|
| T1 | accepted | … | なし | [handoff-….md](…) |
| T2 | blocked | … | 次リリース後 | … |

## Done / Withdrawn

| ID | 結果 | タスク | 完了日 / 判断 | 詳細 |
```

## 状態語彙（この skill が正本）

開いている状態は 4 つ。**この節が語彙の唯一の正本** — rule / ADR / 他 skill は
ここを参照し、定義を複製しない（分散した版は誰も刈らず肥大する）。語は標準語彙
（RFC 標準 + issue-tracker 標準 — 非標準語彙はセッションごとに写像がずれる）。

| 状態 | 定義 |
|---|---|
| `draft` | **採否判断がまだ要る**。やるかどうかを決めていない |
| `accepted` | 採用済みで、今選べば着手できる |
| `in_progress` | claim 中 |
| `blocked` | **採用済みで、条件成立だけで accepted になる** |

終端は `done` / `resolved` / `rejected` / `withdrawn` / `obsoleted`（下節）。

### `blocked` の入場条件

`blocked` に置けるのは、本文に次の 3 つを書けるタスクだけ。自由記述の一文でよく、
機械可読フィールドにはしない（台帳を読む機構を足すと、その機構の保守が台帳を太らせる）。

```
再開条件: X（観測可能な事実）
照合先:   Y（PR 番号 / ファイルパス / 依存タスク ID / ログ）
成立時:   accepted
```

**「条件が成立したらもう一度やるか決める」ものは `blocked` ではない** → `draft`。
この 1 問が効く: **条件成立だけで accepted に移せるか。** 移せないなら採否がまだ残っている。

- 「実害が起きたら考える」型（signal-first）は多くが `draft`。現時点で受容した
  リスクであり、**発生すれば自然に再発見されるものは将来の自分への予告として保持しない**
  → `withdrawn` にして起票し直す方が安い
- 「必要になったら」「保守コストが顕在化したら」「該当領域の再設計サイクルが立ったら」は
  **文法上は名指しているが照合できない**。照合先を書けないなら `blocked` に入れない
- 再開条件が観測数なら**到達率と予定日を同じ行に書く**（`再開条件: answered 300 行（60〜105 行/日、
  切替から 3〜5 日）`）。予定日を書けない観測数条件は照合先を欠く — 台帳で寝る入口。n の導出と
  開け方は skill: `measurement-discipline` §2

### イベント条件の決着規約

再開条件が内部 artifact（seed / view / prompt / モジュール / 設定）の**変更**を待つ場合、
**削除・置換もその条件の決着に含める**。対象が消えたら `obsoleted` へ落とす。
同じことは **成立時 が名指す機構**（閾値 / rule / 判定器）にも当てはまる — 再開条件が生きて
いても、成立時に回すはずの機構が撤廃されていれば条件は決着している。`obsoleted` か条件の
書き直し（日付だけを照合すると、撤廃済みの機構を待ち続ける）。

条件を発火させる主体が先に消えると、タスクは不死化する — 時間窓なら経過で必ず判定できるが、
イベント条件は「発火した」と「発火源が消えた」を区別しないと永久に待ち続ける。

### 台帳に置かない型 — 便乗（「次に X を触る時に同 PR で」）

再開条件が「次に特定のファイル・モジュールを触るとき」の項目は、**台帳行にしない。
そのコードの側に注記として置く。** 台帳は「そのファイルを編集する人」に届かないため
（store 運用は全件を読まず、`claims.py ready` は開いている他状態を出さない）。便乗行は
対象ファイルが何度変更されても空振りし続ける。配送機構を台帳に足して解く問題ではない。

### 終端語彙の使い分け

5 つとも「もう accepted に戻らない」点は同じで、**何がこの行を終わらせたか**で選ぶ。
台帳を後から読む人が「なぜ消えたか」を本文を開かずに引けることが選ぶ理由:

| 終端 | いつ使うか | 消えた理由の所在 |
|---|---|---|
| `done` | やった。作業が完了し成果物がある | この行 |
| `resolved` | 判断が要るタスクで、判断が出た（実装は伴わないか別行） | この行 |
| `rejected` | 採否判断で**否決された** | この行 |
| `withdrawn` | やらないことを**自ら選んだ・取り下げた**（やれたが、やらない選択） | この行 |
| `obsoleted` | **対象・機構の側が消え、タスクが意味を失った** | 外部（ADR / 別の変更） |

`rejected` と `withdrawn` は「誰が閉じたか」で分かれる — 判断の場（triage / 著者判断）で
否決されたら `rejected`、提案・作業の側が取り下げたら `withdrawn`（迷ったら `withdrawn`）。
`withdrawn`・`rejected` と `obsoleted` の境目が実務で一番効く。**タスク側・判断側の意思
決定なら前者、外部要因による無効化なら `obsoleted`** — 後者は「またやりたくなったら復活
できるか」を問うと分かれる（前者は復活可能、`obsoleted` は復活させるなら先に対象を
建て直す）。`obsoleted` を書くときは**何が対象を消したか（ADR 番号・commit・削除された
ファイル）を本文に引用する** — 引用が書けないなら、それはまだ `obsoleted` の確証がない。

観察タスクを閉じるときは特に混ざりやすい。「観察して結論が出た」＝ `done`、
「観察対象が退役して観察が無意味になった」＝ `obsoleted`。後者を `done` に丸めると、
**読みが取得されたのか取得されなかったのかが台帳から消える**。

日付を続けてよい（`done 2026-06-17`）。**日付は台帳に書いた日でなく、終わった日を書く** —
棚卸しで遅れて気付いた終端は、気付いた日でなく実際の決着日を入れると滞留が見える。

**store 形式の repo**（1 タスク 1 ファイル、frontmatter の `state:` が状態。配線の正本は
rule `common/task-tracking.md`）では、状態別の列挙は
`python3 ~/.claude/scripts/claims.py ready --state <state>` で引く。store の家は下節の
`rfcs/` で、終端エントリもその場に残す（archive しない）。この skill が担うのは意味的な
判定（散在タスク行の sweep、着手条件が開いたかの解釈、単一表 repo の archive 候補の選定）。

## store の家 rfcs/（棚卸し側の規定）

store 形の家は repo トップレベルの**公開 `rfcs/`**（1 エントリ 1 ファイル
`NNNN-slug.md`、ID は `RFC-NNNN`）。**起票の手順と規約（足切り・採番・
本文様式・公開規約・index 規約）の正本は skill: `rfc-writer`** — ここには複製しない。
本 skill が rfcs/ について持つのは棚卸し側の 2 つだけ:

- **状態は上の語彙 9 語をそのまま**（第二語彙を作らない。入場条件・終端の使い分け・
  blocked 3 行・obsoleted 引用の規定もそのまま適用する）
- **終端エントリは archive しない**: 削除も退避もせずその場に残す（RFC 慣行。`rejected` /
  `withdrawn` も公開判断記録 — 却下理由ごと残るのが価値）。pending の視界は
  `claims.py ready` の state フィルタが保つ

## レビュー指摘の起票規律（この skill が正本）

台帳が減らない最大の入口はレビュー指摘。reviewer は fix commit ごとに隣接コードの既存問題を
出すので、全部起票すると台帳は純増する。

**足切り**: build セッションからの
即時起票は **loop 自身を壊す欠陥**（放置すると次の build セッションが bounce を食う類 —
例: verify.sh の盲点で正当な diff が通らない）**のみ**。それ以外は severity 不問で
commit message に 1 行（producer 付き）残して捨てる。起票する側は「所有者の判断が要る」なら
`state: draft`。

**probe の例外**: measurement / probe タスクの成果物そのものである起票要求（probe の
「(B)/(C) はやる価値がある」、計器の発見「metrics が汚染されている」）はレビュー指摘ではなく
タスクの出力なので、足切りに掛けない。ただし起票の権限は build 側に無い — 判断役が digest に
出し、所有者が決める。

**build 提案の例外**: build が packet の Report の `Proposed tasks` に、再現手順（コマンド → 期待と
実際）・決定可能な受入条件・producer `file:line` を付けて出した提案（1 build 最大 2 件）は、判断役が
再現を自分で走らせて確かめたものに限り、digest に起票の提案として出せる。起票を決めるのは所有者で、
RFC の書き方と由来の印は skill `rfc-writer` §2。再現しない提案と再現手順の無い指摘は、足切りどおり
commit message に 1 行。

捨てた指摘を後から拾い直す回収機構（commit body の定期 sweep 等）は**作らない** — durable な
記録は commit body が既に担っており、イベント駆動の起票はレビュー → 修理 → 再レビューの
補充エンジンになって台帳が収束しないため。即時対応が結果を変えるのは、実測でも loop を壊す
欠陥にほぼ限られた。

**severity だけでは濾せない。** severity を付けるのは reviewer で、濾す側は同じ次元で
測っている。HIGH の指摘が足切りを守って起票されても、その主張の producer が machine-fixed
だったり誰も読んでいなかったりすれば、1 回の grep で消える指摘が台帳に残る。

そこで足切りに加えて、起票する指摘には**前提の検証**を重ねる:

- **起票にも修理にも、前提の検証を先に置く。** 「この値は X を含みうる」型の指摘なら、
  X を入れられる producer から sink までを `file:line` で引用する。
  `spawn --origin review` は `--producer PATH:LINE` を要求し、無ければ起票を拒否する
  （形だけの検査。真偽は引用する側の責任）
- **検証が長引くなら破棄する。修理は逃げ道にならない** — 未検証のまま直すと投機的な
  コード変更になり、起票より証拠が少なく残る
- 捨てた指摘は severity に関わらず commit message に 1 行残す

## Phase 2 — Sweep（散在タスク行の検出）

台帳の外にタスク行を持ちうるファイルを走査し、台帳に無い項目を列挙する:

- store 形の repo に並存する単一表 `.notes/TASKS.md` の pending 行
- handoff / cold-start ファイル（`handoff-*.md` 等）の「タスク一覧」「残課題」節
- 監査台帳（`bug-audit-*.md` / `remaining-issues-*.md` / stocktake 出力）の未完項目
- auto-memory `MEMORY.md` の Pending 節（あれば内容を台帳へ移しポインタ化を提案）
- README / CLAUDE.md 内の TODO 記述

**sweep 対象外（タスク行の正本増殖に数えない）**: doctrine / ADR が正本指定した
domain ledger（例: strategy 運用の public intervention timeline）と、wiki-harvest 型の
**候補台帳**（採否判断前の候補はタスクではない）。これらは台帳に吸収せず、
ポインタ 1 行を置く。候補が採択され、作業として残った時点で初めて台帳行になる。

検出した行は**起票候補**として列挙・報告する（enumerate）。どれを台帳に載せるか・どの状態に
するかは著者が決める（decide）— 台帳の起票は人間に渡す操作（rule `common/boundary.md`）。
著者が選んだ行だけを台帳へ書く。

## Phase 3 — Verify（既済・stale 照合）

台帳の各 pending 行と Phase 2 の起票候補を実態と突合する（候補の既済は著者の判断材料になる）:

1. `git log --oneline` + 該当ファイル・コードの直読みで**既に完了していないか**確認
   （台帳は drift する、コマンドはしない）
2. 着手条件付きタスクは条件が開いたか（リリース済み / 観察窓明け / 依存解消）を確認
3. 結果を 3 分類で報告: `既済（Done へ移動）` / `stale（内容更新が必要）` / `現役`

## Phase 4 — Archive（完了詳細ファイルの退避提案）

Done になったタスクの詳細ファイル（handoff / 台帳類）のうち、Pending 行から参照されて
いないものを archive ディレクトリへの移動候補として提示する。store 形の `rfcs/` エントリは
対象外（終端エントリもその場に残す）。**確認つき soft-delete**
（rename / 移動のみ、削除しない）。直近参照が多いファイルは無理に動かさない。

## 出力

```
Ledger: <path>（新規作成 or 既存）
Swept: N 件の散在タスク行（起票候補 M 件 — Next action に並べ、載せるかは著者が決める）
Verified: 既済 X / stale Y / 現役 Z
Archived: K ファイル移動（提案 L 件中）
Next action: <起票候補と、ほかにユーザー判断が要る項目の一覧>
```

## 境界

- skill / rule / repo 資産の品質監査はしない（skill-stocktake / rules-stocktake /
  repo-asset-stocktake の領分）
- セッション内 todo（harness の TaskCreate 等）は対象外 — あれは実行中の進捗表示、
  台帳は セッションを跨ぐ pending の正本
- タスクの実装はしない（棚卸しのみ）。実装は通常の chain で

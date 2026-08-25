---
name: task-stocktake
description: "Consolidate a repo's pending-task tracking into its single task ledger (default .notes/TASKS.md) — bootstrap it if missing, sweep handoff / audit / remaining-issues files and auto-memory for stray task lines, verify pending entries against git log and actual code, archive detail files of completed tasks. Use when the user says 「残タスクを棚卸しして」「タスク台帳を作って/整理して」「残っているタスクは？」, \"task stocktake\", when task lines are scattered across notes files, or when a repo's ledger may be stale. NOT for — skills → skill-stocktake; rules → rules-stocktake; repo non-code assets → repo-asset-stocktake; in-session todos → harness task tools."
user-invocable: true
origin: shimo4228
---

# task-stocktake — Task Ledger Audit & Consolidation

repo の pending タスク追跡を**単一台帳**に収束させ、台帳の鮮度を git 実態と突合する。
原則の正本は rule `common/task-tracking.md`（台帳は 1 repo 1 ファイル / 詳細資料に
タスク行の正本を持たせない / MEMORY.md はポインタのみ）。本 skill はその手順を持つ。

## Phase 1 — Bootstrap（台帳の解決・作成）

1. 台帳を解決する: `.notes/TASKS.md` → 既存タスクファイル（`TODO.md` / `TASKS.md` /
   `docs/backlog.md` 等）の順
2. 見つかればそれを台帳と確定して Phase 2 へ
3. 無ければ作成する。「作るか」は聞かない（skill の起動自体が依頼）— 確認するのは**置き場所だけ**:
   - `.notes/` 慣行がある repo は `.notes/TASKS.md`（gitignored = private）に即決。
     無い repo は gitignore 状況を見て private / git-tracked（clone 先でも cold-start 可能）の
     トレードオフを提示して選んでもらう
   - 初期内容: Phase 2 の sweep 結果を集約して生成

台帳フォーマット（1 タスク 1 行）:

```markdown
# TASKS — <repo name>

> 正本: このファイル。詳細はリンク先。規約: rule common/task-tracking.md

## Pending

| ID | 状態 | タスク | 着手条件 | 詳細 |
|----|------|--------|----------|------|
| T1 | ready | … | なし | [handoff-….md](…) |
| T2 | blocked | … | 次リリース後 | … |

## Done / Dropped

| ID | 結果 | タスク | 完了日 / 判断 | 詳細 |
```

## 状態語彙（この skill が正本）

開いている状態は 4 つ。**この節が語彙の唯一の正本** — rule / ADR / 他 skill は
ここを参照し、定義を複製しない（4 文書に分散した版は誰も刈らず 6 語まで肥大した。
CA 2026-08-16）。

| 状態 | 定義 |
|---|---|
| `candidate` | **採否判断がまだ要る**。やるかどうかを決めていない |
| `ready` | 今選べば着手できる |
| `in_progress` | claim 中 |
| `blocked` | **採用済みで、条件成立だけで ready になる** |

終端は `done` / `decided` / `dropped` / `retired`（下節）。

### `blocked` の入場条件

`blocked` に置けるのは、本文に次の 3 つを書けるタスクだけ。自由記述の一文でよく、
機械可読フィールドにはしない（台帳を読む機構を足さない — CA ADR-0095）。

```
再開条件: X（観測可能な事実）
照合先:   Y（PR 番号 / ファイルパス / 依存タスク ID / ログ）
成立時:   ready
```

**「条件が成立したらもう一度やるか決める」ものは `blocked` ではない** → `candidate`。
この 1 問が効く: **条件成立だけで ready に移せるか。** 移せないなら採否がまだ残っている。

- 「実害が起きたら考える」型（signal-first）は多くが `candidate`。現時点で受容した
  リスクであり、**発生すれば自然に再発見されるものは将来の自分への予告として保持しない**
  → `dropped` にして起票し直す方が安い
- 「必要になったら」「保守コストが顕在化したら」「該当領域の再設計サイクルが立ったら」は
  **文法上は名指しているが照合できない**。照合先を書けないなら `blocked` に入れない

### イベント条件の決着規約

再開条件が内部 artifact（seed / view / prompt / モジュール / 設定）の**変更**を待つ場合、
**削除・置換もその条件の決着に含める**。対象が消えたら `retired` へ落とす。
同じことは **成立時 が名指す機構**（閾値 / rule / 判定器）にも当てはまる — 再開条件が生きて
いても、成立時に回すはずの機構が撤廃されていれば条件は決着している。`retired` か条件の
書き直し（先例: harness T-002 は「log 90 日 → zero-usage rule」を待っていたが、rule は
2026-08-15 に撤廃済で、無人 cycle 2 回は日付だけ照合して待ち続けた）。

条件を発火させる主体が先に消えると、タスクは不死化する — 時間窓なら経過で必ず判定できるが、
イベント条件は「発火した」と「発火源が消えた」を区別しないと永久に待ち続ける（先例: CA の
`T-B4` は「view seed text の変更」を待っていたが、seed は ADR-0073 で**削除**された。
2026-08-16 の棚卸しまで 1 ヶ月半気付かれなかった）。

### 台帳に置かない型 — 便乗（「次に X を触る時に同 PR で」）

再開条件が「次に特定のファイル・モジュールを触るとき」の項目は、**台帳行にしない。
そのコードの側に注記として置く。** 台帳は「そのファイルを編集する人」に届かないため
（store 運用は全件を読まず、`claims.py ready` は開いている他状態を出さない）。

CA 2026-08-16 の実測: 便乗 4 件のうち 2 件で対象ファイルが起票後に計 **12 回**変更され、
全部空振りしていた（`T-OBS-INJ` の `core/llm/__init__.py` は 8 回 — うち 1 回は**ファイルごと
パッケージへ分割する大手術**で、対象コードは別ファイルへ移設までされたのに、台帳が要求した
audit ログは付かなかった）。配送機構を台帳に足して解く問題ではない。

### 終端語彙の使い分け

4 つとも「もう ready に戻らない」点は同じで、**何がこの行を終わらせたか**で選ぶ。
台帳を後から読む人が「なぜ消えたか」を本文を開かずに引けることが選ぶ理由:

| 終端 | いつ使うか | 消えた理由の所在 |
|---|---|---|
| `done` | やった。作業が完了し成果物がある | この行 |
| `decided` | 判断が要るタスクで、判断が出た（実装は伴わないか別行） | この行 |
| `dropped` | やらないと決めた。**やれたが、やらない選択をした** | この行 |
| `retired` | **対象・機構の側が消え、タスクが意味を失った** | 外部（ADR / 別の変更） |

`dropped` と `retired` の境目が実務で一番効く。**タスク側の意思決定なら `dropped`、
外部要因による無効化なら `retired`** — 後者は「またやりたくなったら復活できるか」を
問うと分かれる（`dropped` は復活可能、`retired` は復活させるなら先に対象を建て直す）。
`retired` を書くときは**何が対象を消したか（ADR 番号・commit・削除されたファイル）を
本文に引用する** — 引用が書けないなら、それはまだ `retired` の確証がない。

観察タスクを閉じるときは特に混ざりやすい。「観察して結論が出た」＝ `done`、
「観察対象が退役して観察が無意味になった」＝ `retired`。後者を `done` に丸めると、
**読みが取得されたのか取得されなかったのかが台帳から消える**（先例: CA の §B2 は
ADR-0082 が観察対象アームを退役させたので `retired`、§B5 は同じ B 系列だが読みが
実在するので `done`。2026-08-16）。

日付を続けてよい（`done 2026-06-17`）。**日付は台帳に書いた日でなく、終わった日を書く** —
棚卸しで遅れて気付いた終端は、気付いた日でなく実際の決着日を入れると滞留が見える。

**store 形式の repo**（1 タスク 1 ファイル、frontmatter の `state:` が状態。配線の正本は
rule `common/task-tracking.md`）では、状態別の列挙は
`python3 ~/.claude/scripts/claims.py ready --state <state>` で引く。store の家は下節の
`rfcs/`。旧 `.notes/tasks/T-XXX.md` は移行期間中 dual-read され、その終端ファイルだけは
従来通り `.notes/archive/tasks/` へ `mv` するのが archive（機構は無い — CA ADR-0095。
rfcs/ 側は下節の通り archive しない）。この skill が担うのは意味的な判定（散在タスク行の
sweep、着手条件が開いたかの解釈、archive 候補の選定）。

## store の家 rfcs/ と本文様式（この skill が正本、ADR-0049）

store 形の家は repo トップレベルの**公開 `rfcs/`**。1 エントリ 1 ファイル
`rfcs/NNNN-slug.md`（4 桁採番・欠番不再利用 — docs/adr と同じ規約）、ID は stem 先頭
4 桁から `RFC-NNNN`。index は `rfcs/README.md`（`| # | Title |` の表 +
「提案から小さな作業項目まで同居する」旨の 1 行。**state は各ファイルの frontmatter が
唯一の正本 — index に複製しない**。二重記録は drift する）。提案もタスクも 1 店舗 —
提案だけの別置き場を作らない（分散した台帳は誰も刈らない）。

- **状態は上の語彙 8 語をそのまま**（第二語彙を作らない）: `candidate` = RFC の Draft /
  `ready` = Accepted（着手可）/ `in_progress` / `blocked` / `done` = Implemented /
  `decided` = 判断で決着（build なし）/ `dropped` = Rejected・Withdrawn / `retired`。
  入場条件・終端の使い分け・blocked 3 行・retired 引用の規定もそのまま適用する
- **終端エントリは archive しない**: 削除も退避もせずその場に残す（RFC 慣行。`dropped`
  も公開判断記録 — 却下理由ごと残るのが価値）。pending の視界は `ready` の state
  フィルタが保つ
- **公開が既定**: 本文は公開可能な書き方をし、機微（内部事情・非公開 repo のパス等）は
  本文に書かずリンク先へ逃がす（「詳細はリンク先」の既存規約と同じ）
- **接続**: 起票したら `claims.py spawn RFC-NNNN --origin …`（review 由来は `--producer`
  必須 — 下節）。着手時の claim も T-XXX と同じ

**本文の推奨様式 — Rust RFC 0000-template 完全準拠**（推奨であって強制ではない。
自由記述は引き続き有効。小さな作業項目は該当なし節を省き Summary / Motivation 中心で
よい — 起票摩擦の低さを RFC 純度より優先する）:

```markdown
---
state: candidate 2026-08-25
review-when: <失効条件（無ければ省略）>
---
## Summary
## Motivation
## Guide-level explanation
## Reference-level explanation
## Drawbacks
## Rationale and alternatives
## Prior art
## Unresolved questions
## Future possibilities
```

- Rust の preamble（Feature Name / Start Date / RFC PR / Issue）は metadata なので
  frontmatter で表す。見出しは EN 準拠、本文の言語は自由。失効条件の frontmatter key は
  `review-when:` — ADR の `## Review-when`（harness ADR-0044）・rules の `review-when`
  ヘッダと同一概念に同一の語を使う（第 3 の名前を作らない）
- 機械契約は 1 つだけ: **本文の最初の非見出し行**が `claims.py ready` の要約表示になる
  （`## Summary` の 1 行目がそのまま出る）。frontmatter で機械が読むのは `state:` のみ
- `blocked` の 3 行（再開条件 / 照合先 / 成立時）は Unresolved questions 配下に置く
- 標準語彙との対応（翻訳可能性の担保 — ADR-0048）: intent.md problem → Motivation /
  proposed outcome → Summary / affected users and systems → Guide-level（users）・
  Reference-level explanation（systems）/ constraints → Reference-level explanation /
  open questions → Unresolved questions。Build-or-not
  ①既存流用の検討 → Rationale and alternatives、③誰が消費するか → Motivation。
  **Prior art は search-first / Phase 0 の結果の置き場**（AKC Research phase の受け皿）
- ADR との境界: rfcs/ のエントリ = 提案・作業・未決。ADR = 決定記録。採用判断が出たら
  ADR が Rationale and alternatives を引き取り、エントリは state だけ進める

## レビュー指摘の起票規律（この skill が正本）

台帳が減らない最大の入口はレビュー指摘。CA 2026-08-15〜16 の実測では、fix commit ごとに
reviewer が隣接コードの既存問題を平均 1.3 件出し、全部起票すると台帳は純増する。

**足切り**: diff の外の指摘は **HIGH 以上だけ起票**し、それ未満は commit message に 1 行
残して捨てる。起票する側は「所有者の判断が要る」なら `state: candidate`。

**severity だけでは濾せない。** severity を付けるのは reviewer で、濾す側は同じ次元で
測っている。CA 2026-08-16 に T-PACKET-FLOOR-BYPASS が HIGH として起票され、**その 1 件が
束ねていた 4 つの主張は全部 producer が machine-fixed**、うち 1 つは**誰も読んでいない
producer** だった（`weekly-pipeline.sh:850` を 1 回 grep すれば消えていた）。足切り規則は
守られていたのに通り抜けた。

そこで severity の足切りは残したうえで、残った指摘に**前提の検証**を重ねる:

- **起票にも修理にも、前提の検証を先に置く。** 「この値は X を含みうる」型の指摘なら、
  X を入れられる producer から sink までを `file:line` で引用する。
  `spawn --origin review` は `--producer PATH:LINE` を要求し、無ければ起票を拒否する
  （形だけの検査。真偽は引用する側の責任）
- **検証が長引くなら破棄する。修理は逃げ道にならない** — 未検証のまま直すと投機的な
  コード変更になり、起票より証拠が少なく残る
- 捨てた指摘は severity に関わらず commit message に 1 行残す

## Phase 2 — Sweep（散在タスク行の検出）

台帳の外にタスク行を持ちうるファイルを走査し、台帳に無い項目を列挙する:

- handoff / cold-start ファイル（`handoff-*.md` 等）の「タスク一覧」「残課題」節
- 監査台帳（`bug-audit-*.md` / `remaining-issues-*.md` / stocktake 出力）の未完項目
- auto-memory `MEMORY.md` の Pending 節（あれば内容を台帳へ移しポインタ化を提案）
- README / CLAUDE.md 内の TODO 記述

**sweep 対象外（タスク行の正本増殖に数えない）**: doctrine / ADR が正本指定した
domain ledger（例: strategy 運用の public intervention timeline）と、wiki-harvest 型の
**候補台帳**（採否判断前の候補はタスクではない）。これらは台帳に吸収せず、
ポインタ 1 行を置く。候補が採択され、作業として残った時点で初めて台帳行になる。

検出は列挙・報告まで（enumerate）。台帳へ載せるか・どの状態にするかはユーザー / 会話で
判断する（decide）。

## Phase 3 — Verify（既済・stale 照合）

台帳（+ Phase 2 検出分）の各 pending 行を実態と突合する:

1. `git log --oneline` + 該当ファイル・コードの直読みで**既に完了していないか**確認
   （台帳は drift する、コマンドはしない）
2. 着手条件付きタスクは条件が開いたか（リリース済み / 観察窓明け / 依存解消）を確認
3. 結果を 3 分類で報告: `既済（Done へ移動）` / `stale（内容更新が必要）` / `現役`

## Phase 4 — Archive（完了詳細ファイルの退避提案）

Done になったタスクの詳細ファイル（handoff / 台帳類）のうち、Pending 行から参照されて
いないものを archive ディレクトリへの移動候補として提示する。**確認つき soft-delete**
（rename / 移動のみ、削除しない）。直近参照が多いファイルは無理に動かさない。

## 出力

```
Ledger: <path>（新規作成 or 既存）
Swept: N 件の散在タスク行（うち M 件を台帳に追加）
Verified: 既済 X / stale Y / 現役 Z
Archived: K ファイル移動（提案 L 件中）
Next action: <ユーザー判断が要る項目の一覧>
```

## 境界

- skill / rule / repo 資産の品質監査はしない（skill-stocktake / rules-stocktake /
  repo-asset-stocktake の領分）
- セッション内 todo（harness の TaskCreate 等）は対象外 — あれは実行中の進捗表示、
  台帳は セッションを跨ぐ pending の正本
- タスクの実装はしない（棚卸しのみ）。実装は通常の chain で

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

**store 形式の repo**（`.notes/tasks/T-XXX.md`、1 タスク 1 ファイル、frontmatter の
`state:` が状態。配線の正本は rule `common/task-tracking.md`）では、状態別の列挙は
`python3 ~/.claude/scripts/claims.py ready --state <state>` で引く。終端状態のファイルは
`.notes/archive/tasks/` へ `mv` するのが archive（機構は無い — CA ADR-0095）。この skill が
担うのは意味的な判定（散在タスク行の sweep、着手条件が開いたかの解釈、archive 候補の選定）。

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

---
name: rfc-writer
description: "公開 rfcs/ 台帳へ 1 エントリを起票する — 起票するかの足切り、採番、本文様式、公開規約、claims.py spawn への接続、index 行の追加までを行う。Use when the user says 「これ起票して」「RFC にしておいて」「提案を台帳に載せて」, when harness-boundary の Defer や task-triage の起票提案が承認されたとき, or /rfc-writer. NOT for — 状態語彙・review 指摘の起票判定・棚卸し（→ task-stocktake）、決定の記録（→ adr-writer）。"
user-invocable: true
origin: shimo4228
---

# RFC Writer — 公開台帳への起票

rfcs/ は**提案と作業項目の公開台帳**。この skill はそこへ 1 エントリを起票する手順と規約を持つ。

## 0. 足切り — 起票しないことを先に判定する

> Do not create an RFC for work that can be safely completed in the current
> session without preserving intent or state.

台帳は seam（セッション境界・判断待ち・条件待ち）へ intent と state を運ぶ器。
運ぶものが無い起票は純コスト（GTD の 2 分ルールの台帳版）。

- **逆は成り立つ**: 今すぐ却下できる提案でも却下理由を残す価値があるなら起票してよい —
  それは intent の保存（公開判断記録が rfcs/ の存在理由）
- **起票のタイミングは seam が生まれた瞬間、入口の儀式ではない**: plan → 実装で完結する
  直実装は RFC 無しが既定 — 記録は commit（何を）と ADR（なぜ、判断が要るときだけ）が
  担う。**後追いで起票するのは足切りの前提が破れた瞬間**: ① 実装がセッションを跨ぐ
  ことになった（in_progress + Status に経緯）② 人間の判断待ちで止まった（blocked +
  3 行）③ 実装中に「やらない」と決めた（rejected / withdrawn、却下理由ごと terminal で
  置く）。完了後の後追い起票はしない — それは ADR か commit log の領分
- 別軸の既存足切りはそのまま: review 指摘は「loop 自身を壊す欠陥」+ producer 引用のみ
  即時起票（task-stocktake「レビュー指摘の起票規律」）、
  便乗型（「次に X を触る時に」）は台帳でなくコード側の注記

## 1. 起票手順

1. **state**: 提案は `draft`、採用済みの作業項目は `accepted`。語彙 9 語の定義・
   使い分け・`blocked` の 3 行は skill: `task-stocktake` が正本（ここに複製しない）
2. **採番**: `rfcs/` の `[0-9][0-9][0-9][0-9]-*.md` の最大番号 +1 を 4 桁 zero-pad。
   欠番は再利用しない（docs/adr と同じ）。ファイル名 `NNNN-<kebab-slug>.md`、
   ID は `RFC-NNNN`
3. **本文**（Rust RFC 0000-template 準拠 + 独自 2 節。推奨であって強制ではない —
   小さな作業項目は該当なし節を省き Summary / Motivation 中心でよい）:

   ```markdown
   ---
   state: draft 2026-08-25
   review-when: <失効条件（無ければ省略。語は ADR の Review-when と同じ）>
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
   ## Status
   ## Next action
   ```

   - **機械契約は 1 つ**: 本文の最初の非見出し行（= Summary の 1 行目）が
     `claims.py ready` の 90 字要約になる。frontmatter で機械が読むのは `state:` のみ
   - `## Status` = state 語 + 現在地の要約 + 日付（IETF「Status of This Memo」型。
     state 遷移のたびに更新）。`## Next action` = 何があれば動くか（blocked の 3 行の家）
   - plan（skill: `html-plan` の `.html`、または plan mode の `.md`）を通った作業は `## Status` に `**YYYY-MM-DD plan** — [docs/plans/<file>](../docs/plans/<file>)`
     を 1 行置く（plan から RFC へ辿れるように）。本文の最初の行には置かない（`claims.py ready` の要約になるため）
   - 見出しは EN、本文の言語は自由
4. **公開規約**: 公開が既定 — 本文は公開可能な書き方をし、機微（内部事情・非公開 repo
   のパス等）はリンク先へ逃がす。公開は撤回不能なので、迷ったら書かない側に倒す
5. **接続**: `python3 ~/.claude/scripts/claims.py spawn RFC-NNNN --origin <origin>`
   （review 由来は `--producer PATH:LINE` 必須）。着手時は `claim`
6. **index**: `rfcs/README.md` の表に 1 行 — `| [NNNN](<NNNN-slug>.md) | <title> |` の形
   （角括弧に番号、丸括弧にファイル名、右列にタイトル）。
   **state 列は持たない**（frontmatter が唯一の正本 — 二重記録は drift する）

## 2. 標準語彙との対応（翻訳の正本）

対応表は起票時の翻訳なので本 skill が正本。

| 由来 | 対応 |
|---|---|
| playbook intent.md | problem → Motivation / proposed outcome → Summary / affected users and systems → Guide-level（users）・Reference-level explanation（systems）/ constraints → Reference-level explanation / open questions → Unresolved questions |
| search-first / Phase 0 の結果 | → Prior art |
| build セッションが報告の `Proposed tasks` に出した提案（判断役が再現を自分で走らせて確かめ、著者が起票を決めたもの） | 何が壊れているか・再現手順 → Motivation / 受入条件 → Summary / producer → Reference-level explanation。Motivation の 1 行目に `由来: build 提案 (S<n>)`（`S<n>` は提案を出した build セッションの番号 — task-triage が claim label に付ける `S<n>` をそのまま写す）— build 提案経由の起票数を後で数えるための印 |

## 3. repo に rfcs/ が無いとき（初設）

`rfcs/README.md` を作る — 内容は **what-this-is 2〜3 行 + 本 skill（公開版:
`https://github.com/shimo4228/claude-harness/blob/main/skills/rfc-writer/SKILL.md`）への
ポインタ + 状態の正本が frontmatter である旨 1 行 + index 表**だけ。既存 repo の
README を丸コピせず、規約本文は README に書かない — 複製した版は誰も刈らず drift する。単一表だけの小 repo は初設不要 —
提案性の行が生まれた時に作る。

## 境界

- 終端エントリの残置（archive しない）・終端語の使い分け・棚卸しは task-stocktake
- 採用判断が出たら ADR が Rationale and alternatives を引き取る（→ adr-writer）。
  rfcs 側は state を進めて Status を更新するだけ
- スケジュール実行の pipeline が自分で起票する無人 filing は、採番・draft 正規化を pipeline 側が
  持つ — この skill は人間・対話セッションの起票手順

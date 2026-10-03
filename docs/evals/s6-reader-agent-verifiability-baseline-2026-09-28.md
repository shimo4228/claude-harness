---
origin: shimo4228
instrument: 読者役エージェントによる照合（RFC-0031）
subject: claude-harness の公開物 4 件 + 最新の zenn 記事 1 件（対照 2 件）
validity: 不成立
source_type: evaluation_run
evaluator_relationship: first_party
eval_library:
  name: Claude Code subagent（WebSearch / WebFetch のみ）
  version: unknown
evaluation_timestamp: 2026-09-28
retrieved_timestamp: 2026-09-28
num_samples: 1
execution_command: "—（packet docs/plans/rfc-0031-s0-reader-baseline.md を読者役に渡した 1 回）"
log_updates: []
---

# s6 — 読者役による照合、基準の 0 回目（2026-09-28）

文脈を持たない読者役に公開 Web だけで「出力 → 指摘 → 理由 → 結果」を辿らせ、環ごとに `確認` / `記述のみ` / `不明` を付けさせた 0 回目。
[RFC-0031](../../rfcs/0031-reader-agent-verifiability-probe.md) の基準取り。著者はこの計器を、効果を見込んだものではなく「意味が無いと分かっても面白がる探索」として採った（RFC-0031 の Status）。

## 設計

- 問い: 著者の指摘・その理由・その後の結果が、公開物だけで辿れるか。RFC-0028（commit に指摘を残す）・RFC-0029（commit 本文を公開ミラーへ運ぶ）・RFC-0030（Eval カード）が効いたかを、後の回と比べるための基準
- 対象（RFC-0031 の固定リスト）: 1. RFC-0021 / 2. ADR-0085 と plan `composed-enchanting-wand` / 3. Eval カード s1 / 4. RFC-0035 / 5. 枠「最新の zenn 記事」= `local-judgment-read-logprobs`（2026-09-27 公開）
- 対照: 6. existence-proof（辿れるはず）/ 7. AKC ADR-0024（辿れないはず — 2026-09-27 の予備測定で 0/4）
- 判定の定義（packet）: `確認` = 根拠そのもの（元の commit 本文・発言・ログ）に公開物で辿り着けた / `記述のみ` = 書いてあるが根拠が非公開 / `不明` = 見つからない
- packet: [docs/plans/rfc-0031-s0-reader-baseline.md](../plans/rfc-0031-s0-reader-baseline.md)

## 環境

- 読者役: Claude Code の subagent、model `claude-opus-5-5`、fresh context、道具は WebSearch / WebFetch だけ（手元の repo は渡していない）
- 取得 39 回（WebFetch 38、WebSearch 1）。全ページが WebFetch の要約モデルを通して返った — 引用の文言は原文と 1 字ずつ照合されていない
- 判断役（この測定を dispatch し、カードを起こした session）は読者役と同じ model 系統

## 生の読み値

| 対象 | 出力 | 指摘 | 理由 | 結果 |
|---|---|---|---|---|
| 1. RFC-0021 | 確認 | 記述のみ | 確認 | 記述のみ |
| 2. ADR-0085 + plan | 確認 | 記述のみ | 確認 | 確認 |
| 3. Eval カード s1 | 確認 | 記述のみ | 確認 | 不明 |
| 4. RFC-0035 | 確認 | 記述のみ | 確認 | 記述のみ |
| 5. zenn 記事 | 確認 | 記述のみ | 記述のみ | 不明 |
| 6. existence-proof（対照） | 確認 | 確認 | 確認 | 不明 |
| 7. AKC ADR-0024（対照） | 確認 | 確認 | 確認 | 確認 |

集計: 対象 20 環 = `確認` 10 / `記述のみ` 8 / `不明` 2。対照 8 環 = `確認` 7 / `不明` 1。

読み（読者役の根拠から判断役がまとめた）:

- **指摘の環は対象 5 件すべて `記述のみ`**、対照 2 件はどちらも `確認`。分かれ目は repo の形だった — 対象 1〜4 は公開ミラー（claude-harness）にあり、commit はすべて「chore: sync from local harness」で、本文が引く SHA（`258ca6c`・`42665c6` など）は非公開の正本 repo のもので 404 になる。対照 2 件は正本がそのまま公開 repo で、著者の判断を書いた commit 本文（existence-proof `ffaf1e3`、AKC `13d5e74`）が読める
- 対象の `確認` 10 のうち、出力 5 と理由 4 はエージェントが書いた本文そのもの（Context・動機の節）。著者の言葉まで辿れた環は対象に 0
- zenn 記事は commit 本文（`ab29476`）が公開されているが、指摘の中身は「処分記録は drafts/（gitignored）」とあるだけで辿れない — RFC-0028 の試行が塞ごうとしている穴そのもの

公開物どうしの食い違いとして読者役が挙げたもの:

1. ADR-0085 Decision 6「既存 255 本は移さない」と、claude-harness `401796e`「過去 plan 69 本」— **誤検出**。Decision 6 には同じ公開版に RFC-0033 の注記（「既存の plan は移す」）が付いている。読者役は要約器経由で注記を拾えなかった
2. 公開文書が、非公開 repo の SHA をどの repo のものか書かずに引いている（RFC-0021 の `258ca6c`、RFC-0030 の `42665c6` — claude-harness では 404）— **実在**。RFC-0029 の前提（同期が commit 本文を落とす）を、読者の側から見た形

## 測らなかったもの

- 予備測定（2026-09-27）との比較 — 対象の一覧が失われ、判定の線引きも同じか確かめられない
- 読者役の判定の揺れ（同じ対象を 2 回読ませていない）、別の model の読者役
- 要約器を通さない原文での照合（WebFetch しか持たせていない）
- 環の判定の妥当性を人が確かめること（食い違い 1 だけを判断役が一次資料で確かめた）

## 既知の故障

1. **対照が期待どおりに分かれなかった。** AKC ADR-0024 は予備測定で 0/4（辿れない側）だったが、今回は 4/4 `確認`。今回の定義は「公開 repo にある元の commit 本文」を根拠として数えるので、著者の判断を commit 本文に書く AKC は辿れる側に入る。予備測定の線引きは記録に残っておらず、どちらが変わったのかは確かめられない。辿れない側の対照が今は無い
2. **要約器を通した読み。** 全ページが WebFetch の要約を通しており、注記のような短い節を落とす（食い違い 1 の誤検出がその実例）
3. **判断役と読者役が同じ model 系統。** 判定の癖が揃いうる

## 有効性の状態

**不成立。** RFC-0031 は「対照の判定が期待と逆に出たら計器の故障」と定めており、辿れないはずの対照が 4/4 で辿れた。計器が辿れる / 辿れないを分けられるかは、この回では示せていない。

ただし対象側の読み（指摘の環 5/5 が `記述のみ`、分かれ目は公開ミラーか正本 repo か）は、対照の故障と独立に読める事実として残す。

- `単発` へ動く条件: 辿れない側の対照を定め直し（例: 正本が非公開で、公開ミラーに同期 commit しか無い文書）、同じ定義で次の回を走らせて対照が期待どおり分かれる
- 次の回: RFC-0028 の試行の読み（2026-10-12）の後。対象 5 の枠はその時点の最新記事（試行で書いた記事）になる

## 欄の対応表

| このカードの欄 | aggregate-result.json（schemaVersion 1） | Every Eval Ever v0.3.0 | Inspect AI EvalLog |
|---|---|---|---|
| frontmatter `eval_library` | — | `eval_library{name,version}` | — |
| frontmatter `evaluation_timestamp` / `retrieved_timestamp` | — | `evaluation_timestamp` / `retrieved_timestamp` | — |
| frontmatter `source_type` / `evaluator_relationship` | — | `source_metadata.source_type` / `source_metadata.evaluator_relationship` | — |
| frontmatter `num_samples` | — | `evaluation_results[].score_details.uncertainty.num_samples` | — |
| frontmatter `log_updates` | — | — | `log_updates`（考え方のみ） |
| 生の読み値の環ごとの判定 | — | —（EEE に環の概念は無い） | — |

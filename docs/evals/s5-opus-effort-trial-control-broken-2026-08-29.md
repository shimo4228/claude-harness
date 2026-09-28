---
origin: shimo4228
instrument: build 層の effort 試行（settings.json の modelSettings による effort 固定 × triage 検収の bounce）
subject: Opus の build session の effort（local = medium / cloud = 既定）
validity: 不成立
source_type: documentation
evaluator_relationship: first_party
eval_library:
  name: task-triage の検収（bounce の記録）
  version: unknown
evaluation_timestamp: 2026-08-29/2026-09-26
retrieved_timestamp: 2026-09-28
num_samples: 未記録
execution_command: "—（コマンドで走る測定ではない。settings.json の modelSettings に effortLevel: medium を置いて build を運用し、判断役の検収で bounce を見る試行）"
log_updates: []
---

# s5 — Opus build 層の effort 試行と対照の崩れ（2026-08-29〜09-26）

build 役の Opus session の effort を medium に下げても bounce（判断役の検収での差し戻し）が増えないかを運用で見た試行の記録。
2026-09-24 に cloud session が build の既定になった時点で「cloud = high / local = medium」を対照として読む前提ができたが、2026-09-26 の probe で
cloud の実 effort も medium だったと分かり、対照は成り立っていなかった。試行は 2026-09-26 に閉じ、effort は packet ごとに判断役が選ぶ形
（[ADR-0081](../adr/0081-per-packet-effort-and-bounce-classification.md)）に置き換わった。

## 設計

- 問い: build 役の Opus の effort を high から medium に下げたとき、判断役の検収で bounce が増えるか。増えなければ medium で費用を下げる
- 始まり（2026-08-29、plan `docs/plans/effort-fable-opus-effort-opus-effort-me-buzzing-ladybug.md`）: `~/.claude/settings.json` の
  `modelSettings.claude-opus-5.effortLevel` を `high` から `medium` へ変えた（著者の決定。「コスト約半減の試行」）。判断役の Fable は `high` のまま。
  検証の手順は「次の Opus build session の成果物を Fable の triage 検収で観察し、bounce 率が上がるなら high へ戻す」。
  plan が根拠を調べた範囲では、「Opus 5 は medium で coding bench が near-peak」は二次資料だけで、長時間の agentic session への転写は未検証とされていた
- 意図した対照（2026-09-24、[ADR-0075](../adr/0075-cloud-session-as-default-build-executor.md)）: build の既定を cloud session に移した ADR-0075 は、cloud の effort を
  「claude.ai 側の既定（Opus 5.5 / high、2026-09-24 実測）」、local の medium 試行を「local 限定」と書いた。Review-when は、cloud build 10 本の bounce 率を
  直前の local build 10 本の digest 記録と比べ、高ければ「packet の形・review・effort（high 固定）のどれが効いたかを分けて再訪する。差を effort 単独に帰さない」とする。
  これで cloud = high / local = medium の 2 群が並ぶ形になった
- 読む量: bounce 率 = 「§4 で bounce した build 数 / dispatch した build 数」（ADR-0075）。gate 触りと rebase の bounce は除く
- arm: 2 群（cloud / local）だが、無作為の割り付けは無い。どの task がどちらに行くかは実行者の規則（ADR-0075 Decision 4）で決まり、群の間で task の種類が違う

## 環境

- local の build: Claude Code の local session（Herdr `spawn-session` / Agent tool）。effort は `settings.json` の `modelSettings` から。
  `settings.json` は 2026-07-27 の commit `bfb1e59` で git の追跡から外れており、2026-08-29 の変更も以後の変更も git に残っていない。
  2026-09-28 時点の値は `claude-opus-5` = medium、`claude-opus-5-5` = medium、`claude-fable-5-1` = high。`claude-opus-5-5` のキーが足された日は未記録
- build のモデル: 試行の途中で Opus 5 から Opus 5.5 に替わった（ADR-0076、2026-09-25 は Opus 5.5 を build 役と書く）。切り替えの日は未記録
- cloud の build: `scripts/cloud-dispatch.sh` の `claude --cloud`。CLI 2.1.281（ADR-0075 の記述）〜 2.1.283（ADR-0081 の probe）
- probe（2026-09-26、CLI 2.1.283、ADR-0081 Context）: `claude --cloud "<prompt>" --ref main --effort low` で作った session の中は `CLAUDE_EFFORT=medium`、
  `reasoning_effort: 10`。作成時の `--effort` は転送されなかった。同じ session に `/effort high` を送ると次の turn で `CLAUDE_EFFORT=high`、`reasoning_effort: 15`。
  probe の証拠は private repo の session と判断役の画面にある（ADR-0081 の記述。このカードは session を開いていない）
- bounce の記録先: 判断役の digest。2026-08-30 の commit `92e8ece` で digest の本文は Slack から triage session の返信へ移り、返信は残らない（ADR-0081 Consequences）

## 生の読み値

| 欄 | 値 |
|---|---|
| 試行の期間 | 2026-08-29 〜 2026-09-26（28 日） |
| 意図した対照 | cloud = high / local = medium |
| probe が示した cloud の実 effort | **medium**（`CLAUDE_EFFORT=medium`、`reasoning_effort: 10`。2026-09-26） |
| local の実 effort | 未確認（`modelSettings` の値は medium だが、session が実際に medium で走ったかを見た記録は無い） |
| `~/.claude/logs/cloud-dispatch.jsonl` | **1 行**（2026-09-24、public repo への dispatch 1 件。`effort` 欄は無い — ADR-0081 より前の行） |
| `~/.claude/logs/effort-outcomes.jsonl` | **3 行**（2026-09-26〜28。全て試行の終了日以後）。packet の `effort` は medium 2 / low 1、実際に走った `effort_ran` は medium 2 / 未確認 1、bounce あり 1（分類 `gate・rebase`）/ なし 2 |
| cloud build 10 本の bounce 率 | 未記録（cloud への dispatch はログ上 1 件） |
| 直前の local build 10 本の bounce 率 | 未記録（digest は残っていない） |
| 著者の観察 | 「bounce 増の体感が無い」（件数ではなく印象。ADR-0081 Context） |

2 つのログの行数は 2026-09-28 に数えた。値は件数と欄の値の集計だけで、行そのもの（repo・task・session id）は写さない。

## 測らなかったもの

- effort が bounce に与える効果。bounce の件数が群ごとに残っておらず、群の間で effort も違っていなかった
- medium での費用の削減量（token・時間の記録は無い）
- 見落とし系と読み違い系の失敗の分け方（ADR-0081 が bounce の分類を足したのは試行の後）
- high の local build（試行中に対照となる high の local 群は無い）
- Opus 5 と Opus 5.5 を分けた読み

## 既知の故障

1. **対照の片側が思っていた値ではなかった。** cloud の既定は high の前提で対照を組んだが、2026-09-26 の probe では medium。作成時の `--effort` が
   転送されないので、試行中の cloud build が high で走った保証は無い。ADR-0075 の「2026-09-24 実測で high」と ADR-0081 の「2026-09-26 実測で medium」は
   2 日で割れており、ADR-0081 は cloud の既定を「サーバ側で動く値」として扱う。どの日の cloud build がどちらで走ったかは分からない
2. **local の側も確かめていない。** `modelSettings` のキー `claude-opus-5` が build の Opus 5.5 に効いていたか、Fable 5 系にある「picker で確定した effort が
   settings より優先される hold」（2026-09-12 の plan `docs/plans/pr-tool-kit-code-review-code-reviewer-co-silly-kahan.md` の注意書き）が Opus にもあったかは未確認。
   著者の auto memory も同じ点を未確認としている
3. **群の大きさが足りない。** ADR-0075 の比較は cloud 10 本を前提にしたが、`cloud-dispatch.jsonl` の行は試行の期間中 1 行だけ
4. **bounce の件数が残っていない。** 2026-08-30 以降、digest は session の返信にしか出ず、判断役が別のファイルへ build 行を書く手順（`effort-outcomes.jsonl`）は
   ADR-0081（2026-09-26）で入った。試行期間の bounce 率は後から数えられない
5. **実行者・packet・review が同時に変わった。** ADR-0075 の移行は effort だけでなく、packet の形（自己完結）と review（`/code-review` 1 本）も同時に変えた。
   ADR-0075 自身が「差を effort 単独に帰さない」と書いている
6. **settings.json の履歴が無い。** 試行の開始と `claude-opus-5-5` キーの追加は git で追えず、開始日の根拠は plan の記述だけ

## 有効性の状態

**不成立。** 意図した対照（cloud = high / local = medium）は、cloud の実 effort が medium だったことで崩れていた可能性が高く、群ごとの bounce 件数も記録されていない。
読み値は「effort を medium に下げても bounce が増えないか」という問いに答えていない。残る証拠は著者の「bounce 増の体感が無い」という印象だけ
（ADR-0081 Context が「件数ではなく印象」と書く）。この試行を「傍証止まり」として扱えという指示は著者の auto memory にあるが、ADR・RFC には無い（未確認（memory の記述のみ））。

- 別の測定として `単発` を作る経路: ADR-0081 の Review-when 1（`effort-outcomes.jsonl` の build 20 本で、見落とし分類の bounce のうち low / medium の割合を読む）が
  満ちたら、その読みを新しいカードとして記録する。この試行自体は動かない

## 欄の対応表

| このカードの欄 | aggregate-result.json（schemaVersion 1） | Every Eval Ever v0.3.0 | Inspect AI EvalLog |
|---|---|---|---|
| frontmatter `eval_library` | — | `eval_library{name,version}` | — |
| frontmatter `evaluation_timestamp`（区間） | — | `evaluation_timestamp`（EEE は時点。ここでは区間に読み替え） | — |
| frontmatter `retrieved_timestamp` | — | `retrieved_timestamp`（EEE は Unix epoch） | — |
| frontmatter `source_type` / `evaluator_relationship` | — | `source_metadata.source_type` / `source_metadata.evaluator_relationship` | — |
| frontmatter `num_samples`（未記録） | — | `evaluation_results[].score_details.uncertainty.num_samples` | — |
| frontmatter `execution_command`（—） | — | `evaluation_results[].generation_config.generation_args.execution_command` | — |
| frontmatter `log_updates` | — | — | `log_updates`（考え方のみ） |
| 生の読み値 bounce 率 | —（2 群の比較だが arm・delta の数値が無い） | — | — |

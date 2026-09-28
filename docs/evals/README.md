# Eval cards

harness の計器（ablation・shadow baseline・判定ログ等）を 1 回測った記録を、1 測定 1 枚のカードで公開する置き場。
カードは設計・環境・生の読み値・測らなかったもの・既知の故障・有効性の状態を必ず持ち、読み値だけが独り歩きしないようにする。
提案と作業の台帳は [rfcs/](../../rfcs/README.md)、決定は [docs/adr/](../adr/README.md) が持つ。ここは測定の記録だけを持つ。

## カードの形

ファイル名は `<slug>-<測った日 YYYY-MM-DD>.md`。本文は次の 6 見出しをこの順で持ち、その後に `## 欄の対応表` を置く。

| 見出し | 書くもの |
|---|---|
| `## 設計` | 何を問う測定か、対象、case の prompt と grader の全文、arm の組み方、その計器が harness でどう使われるか |
| `## 環境` | CLI の版・model・judge・flag・実行コマンド・並列度・隔離の条件（測った時点の値） |
| `## 生の読み値` | 計器が出した数値そのもの（score・delta・run 別・grader 別・cost・時間）。導出した値は導出式を 1 行添える |
| `## 測らなかったもの` | この測定が答えない問い。読み手が読み値を広げすぎないための境界 |
| `## 既知の故障` | 生値の消失、偽陰性・偽陽性の経路、exit code の罠など、読み値の解釈を曲げる既知の事実 |
| `## 有効性の状態` | 状態語 1 つと、その語を選んだ根拠、別の語へ動く条件 |

記録に無い値は推測で埋めず「未記録」と書く。確かめられなかった主張には「未確認」と、見た場所を書く。
パスは `~/` で書き、session の scratchpad の UUID は書かない。

## frontmatter

| キー | 値 |
|---|---|
| `origin` | 規約どおり（自作は `shimo4228`） |
| `instrument` | 計器（コマンドや skill の名前） |
| `subject` | 測った対象（skill 名など） |
| `validity` | 状態語 3 つのどれか |
| `source_type` | `evaluation_run`（生値がカードと同じ repo に残る）/ `documentation`（生値が消え、記録から起こした） |
| `evaluator_relationship` | `first_party` / `third_party` / `collaborative` / `other`（自分の計器で自分の資産を測ったら `first_party`） |
| `eval_library` | `{name, version}` — 測定を走らせた道具と版。版が分からなければ `unknown` |
| `evaluation_timestamp` | 測った時刻（ISO 8601） |
| `retrieved_timestamp` | カードを起こした日（ISO 8601） |
| `num_samples` | 読み値 1 つを作った反復数（例: arm ごとの run 数） |
| `execution_command` | 実行コマンド。パスは `<copy>` などの placeholder にしてよい |
| `log_updates` | 公開後の訂正の追記列。各要素は `{date, author, reason, change}`。消さず足すだけ。無ければ `[]` |

## 有効性の状態語

台帳の状態語（`draft` / `accepted` …）とは別の語彙。カードの状態であってタスクの状態ではない。

- `再現済み` — 同じ設計を別の機会に走らせ、生値が残り、結論の向き（delta の符号など）が一致した
- `単発` — 実測は 1 回だけ。結論は測った条件（その case・その環境）に限って読む
- `不成立` — 設計か環境の故障で、読み値が問いに答えていない（測定として成り立たなかった）

## 借りた名前の出典

形式は自前 markdown。外部形式は採らず、欄の名前だけを借りる（as-of 2026-09-28、search-first で照合）。

| キー | 形式・版 | 元の位置 | URL |
|---|---|---|---|
| `claudeVersion` / `costUsd` / `durationSeconds` / `partial` | `claude plugin eval` aggregate-result.json、`schemaVersion: 1` | root | https://code.claude.com/docs/en/plugin-evals |
| `cases[].aggregates.score` / `cases[].aggregates.delta` | 同上 | case ごと | 同上 |
| `arms.with` / `arms.without` | 同上 | `cases[].arms.*`（run ごとの配列） | 同上 |
| `scored` | 同上 | grader 結果の欄。docs の欄表には無く、s1 の実測で `scored: false` を観測 | 同上 |
| `source_type` / `evaluator_relationship` | Every Eval Ever schema v0.3.0 | `source_metadata.*` | https://github.com/evaleval/every_eval_ever |
| `eval_library{name,version}` / `evaluation_timestamp` / `retrieved_timestamp` | 同上 | root（EEE の `retrieved_timestamp` は Unix epoch。ここでは ISO 8601 に読み替える） | 同上 |
| `num_samples` | 同上 | `evaluation_results[].score_details.uncertainty.num_samples` | 同上 |
| `execution_command` | 同上 | `evaluation_results[].generation_config.generation_args.execution_command` | 同上 |
| `log_updates` | Inspect AI EvalLog | 公開後の編集を author と reason 付きで追記だけする履歴。考え方だけ借り、要素の形は上の表のとおり自前 | https://inspect.aisi.org.uk/eval-logs.html |
| （名前は借りない）節立ての抜け検査 | Evaluation Cards, arXiv 2606.09809 | lifecycle の 5 区分に対して 6 見出しに抜けが無いかを見る。5 区分の名前は abstract からは確認できず未確認 | https://arxiv.org/abs/2606.09809 |

## Index

| カード | 計器 | 状態 |
|---|---|---|
| [s1-headline-craft-native-ablation-2026-09-13](s1-headline-craft-native-ablation-2026-09-13.md) | `claude plugin eval --ablation with-without` | 単発 |
| [s2-skill-comply-measurement-validity-2026-08-01](s2-skill-comply-measurement-validity-2026-08-01.md) | skill-comply（`scripts/run.py`） | 不成立 |
| [s3-search-first-shadow-baseline-2026-09-14](s3-search-first-shadow-baseline-2026-09-14.md) | search-first 影の比率 snippet | 単発 |
| [s4-jev-skill-router-decision-log-2026-09-21](s4-jev-skill-router-decision-log-2026-09-21.md) | jev-skill-router 判定ログ（shadow） | 単発 |
| [s5-opus-effort-trial-control-broken-2026-08-29](s5-opus-effort-trial-control-broken-2026-08-29.md) | `modelSettings` の effort × triage の bounce | 不成立 |

---
origin: shimo4228
instrument: claude plugin eval --ablation with-without
subject: headline-craft
validity: 単発
source_type: documentation
evaluator_relationship: first_party
eval_library:
  name: claude plugin eval
  version: 2.1.270
evaluation_timestamp: 2026-09-12T21:38:47Z
retrieved_timestamp: 2026-09-28
num_samples: 3
execution_command: "claude plugin eval <copy>/headline-craft --ablation with-without --runs 3 --no-publish --trust-plugin --judge-model haiku --max-cost-usd 2 --json result.json"
log_updates: []
---

# s1 — headline-craft の native ablation（2026-09-13）

`claude plugin eval` の with / without ablation が、skill が行動を変えたかを 1 case で弁別できるかを測った単発の記録。
`evaluation_timestamp` は結果 dir 名 `2026-09-12T21-38-47-907Z`（UTC）から取った。JST では 2026-09-13 06:38:47。

## 設計

- 問い: native の ablation（skill を load する with arm と、plugin 無しの without arm）が、skill の有無による出力の差を score の delta として出すか。置換の可否は判断しない（計測のみ）
- 計器の使われ方: [skill-creator §5](../../skills/skill-creator/SKILL.md) は、検証可能な出力を持つ skill の「差の有無」を native eval で screening すると定めている（`--runs 3`、arm 別 score と delta を読み、delta が無ければ Drop）。この測定はその screening の手順と費用の実測元
- 対象: `headline-craft`（`~/.claude/skills/headline-craft/SKILL.md`、79 行、SKILL.md 1 枚）。選んだ理由は、出力が構造で検証できる（候補 5 本以上・技法ラベル・検索/フィードの 2 軸ラベル・core claim 1 文・優劣を付けない）、script も agent 依存も無い、read-only の 3 点
- 実体: scratchpad に copy した `headline-craft/`（frontmatter 無改変）を target にした。`~/.claude` 配下は変更していない
- case: `evals/titles/` を `claude plugin eval init --bare titles` で作り、中身を差し替えた（雛形は `max_turns: 10` / `allowed_tools: [Read, Glob, Grep, Skill]` / `type: llm, weight: 1` の 2 ファイル）。case は 1 本
- prompt は skill の手順を書かない。書くと without arm が prompt だけで満たせ、弁別が死ぬ
- arm: with（plugin 有り）/ without（plugin 無し）を各 3 run。run の score は scored な grader（3 本）の pass 率、case の score は with arm の run 平均

### prompt.md

```markdown
---
max_turns: 10
allowed_tools: [Read, Skill]
---

技術ブログ記事のタイトル候補を出してほしい。記事の要旨は次のとおり:

Claude Code の hooks で commit 前に secret scan と lint gate を走らせる構成を 3 か月運用した。
途中で 7 本の hook に command injection が見つかり、PoC 付きで対象 repo の乗っ取りが実証できた。
原因は hook が受け取る commit metadata と path をそのまま shell に渡していたことで、
git target 抽出を専用関数に切り出し bats の回帰テスト 12 本で固定して直した。
読者が持ち帰るのは「無人で走る hook は untrusted input を受ける実行面である」という視点。

日本語のタイトル候補をください。
```

### graders/criteria.md

```markdown
---
type: llm
weight: 1
---

The response presents at least 3 distinct Japanese title candidates for the article, and each
candidate is a single sentence with no trailing period and no two clauses joined by em dash
(——) or 、/。 into a compound restatement of the whole article.
```

### graders/annotation.md

```markdown
---
type: llm
weight: 1
---

Every title candidate in the response carries BOTH of these annotations explicitly:
(a) the technique used to build it (e.g. 具体性 / 結果駆動 / ベネフィット前置 / 誠実な好奇心ギャップ /
対比・転換 / 数字は証拠として / 自分ごと化 / 問いの形), and
(b) an acquisition-channel label that is explicitly 検索 or フィード.
Fail if the channel label (検索 / フィード) is missing from any candidate, or if the response
only lists titles without per-candidate annotation.
```

### graders/core_claim.md

```markdown
---
type: llm
weight: 1
---

Before the candidates, the response states a single-sentence "core claim" (the one thing the
reader takes away) and treats the titles as pointers to it rather than restatements of it.
Additionally, the response does NOT rank the candidates or declare one of them the best /
recommended pick — it presents them without 優劣.
```

### graders/fired.md（with-only の発火検出、score に入らない）

```markdown
---
type: tool_used
tool: Skill
min: 1
arm: with-only
---
```

grader の field 名は `--help` に型名（`tool_used | file_exists | llm | baseline`）しか無く、`tool` / `min` / `arm` は CLI binary に埋め込まれた doc 文字列から取った。初手で通った。

## 環境

- `claudeVersion`: 2.1.270（`eval_library.version` と同じ CLI）
- 被験 model: 既定（`--model` 未指定）。解決された model 名は未記録
- judge: haiku（`--judge-model haiku`）。model ID の全体は未記録
- flag: `--ablation with-without` / `--runs 3` / `--no-publish` / `--trust-plugin` / `--max-cost-usd 2` / `--json result.json`。`--threshold` は未指定（既定 1.0）、`--concurrency` は未指定（既定 1、6 run 逐次）、`--keep-temp` は未指定
- 実行コマンド: frontmatter の `execution_command`（`<copy>` は scratchpad の copy 先）
- 隔離: run は plugin だけを load した隔離 session で走る。user の settings・hooks・`CLAUDE.md`・memory・skills・他の plugin は run に無い（[plugin-evals docs](https://code.claude.com/docs/en/plugin-evals)「How runs are isolated」、2026-09-28 照合）
- 測った日: 2026-09-13（JST）。セットアップ壁時計は約 3 分（skill の copy から run 開始まで、`init --bare` と prompt / grader 4 本の執筆込み）、Phase 0 の照合と grader schema の掘り出しを含めて約 10 分

## 生の読み値

生の JSON は残っていない（「既知の故障」1）。以下は読みメモに写した値で、欄名は aggregate-result.json に合わせた。

| 欄 | 値 |
|---|---|
| `cases[].aggregates.score`（with arm の run 平均） | **0.556** |
| without arm の run 平均 | **0.000** |
| `cases[].aggregates.delta` | **+0.556** |
| `arms.with` の run 別 score | 1.00 / 0.333 / 0.333 |
| `arms.without` の run 別 score | 0 / 0 / 0 |
| 全 grader が pass した run（with / without） | 1/3（33%）/ 0/3（0%） |
| `partial` | `false` |
| run の `error` | `null` × 6（run 失敗 0 件） |
| `costUsd`（総額） | **$0.9919**（`--max-cost-usd 2` に未到達、打ち切りなし） |
| cost の arm 別 | with $0.661（0.2197 + 0.2107 + 0.2305）/ without $0.331（0.1054 + 0.1172 + 0.1084） |
| cost のうち judge 分 | $0.058（総額の約 6%） |
| run 壁時計 | 310 秒（5 分 10 秒）。JSON の `durationSeconds` と同じ値かは未確認（読みメモは壁時計として記録） |
| turns | with 5 / without 1 |
| exit code | 1 |

導出:

- with の score 0.556 = (3/3 + 1/3 + 1/3) / 3 = 5/9。run 別 score は scored な 3 grader のうち pass した本数 / 3
- delta +0.556 = 0.556 − 0.000
- arm 別 cost の和 0.661 + 0.331 = 0.992 が総額 $0.9919 と一致するので、judge 分 $0.058 は arm 別の内数

grader 別（各 grader の judge 3 票は 4 grader × 6 run の全てで満場一致、judge のブレ 0）:

| grader | with（run 1 / 2 / 3） | without（run 1 / 2 / 3） |
|---|---|---|
| `annotation`（技法 + 検索/フィード ラベル） | pass / pass / pass | fail / fail / fail |
| `core_claim`（core claim 1 文 + 優劣を付けない） | pass / fail / fail | fail / fail / fail |
| `criteria`（候補 3 本以上・1 文・連結なし） | pass / fail / fail | fail / fail / fail |
| `fired`（with-only `tool_used: Skill`、`scored: false`） | pass / pass / pass | 実行されない |

読み:

- `fired` が 3/3 で pass し、skill が実際に読まれたことを示す。turns（with 5 / without 1）でも発火が見える
- without arm は 3 run とも「A. / B. の角度別に候補を出し、最後に 1 つ推す」形で、2 軸ラベル・core claim・優劣禁止のどれも出なかった。対照として素直に効いている
- 分散は with arm にだけ出た（1.00 / 0.333 / 0.333）。1 run だけなら結論が逆向きに転びえた
- with arm の 2 失敗は、skill が defer 先を探しに行き不在の断り書きを先頭に書いたため core claim が先頭に来ず、末尾で優劣に踏み込んだもの（「既知の故障」2）

## 測らなかったもの

- 他の skill・他の case への一般化（skill 1 本、case 1 本）
- 別の日・別の CLI 版・別の被験 model での再現（1 回だけ）
- 旧版 skill との比較（baseline は「plugin 無し」1 種で、target は単数。旧版を 2 つ目の target に渡す口は CLI に無い）
- 世代間の比較（結果は timestamp 別 dir に積まれるが、世代間 diff を出す flag は無い）
- 出力を読んだ著者の判断を次 run へ戻す経路（`init` の対話は case を書く前だけ）
- with arm の失敗が skill の欠陥か grader の厳しさか（判定していない）
- grader の妥当性そのもの（`annotation` は完全に弁別したが、`criteria` / `core_claim` は環境依存の失敗を拾った）
- judge を haiku 以外にしたときの揺れ、`--runs` を 3 より増やしたときの分散
- 途中の tool 呼び出し trace（残っていない）

## 既知の故障

1. **生値の消失。** report.html（自己完結 HTML、72 KB）・aggregate-result.json（61 KB）・`--json` の result.json は session の scratchpad に置いたため scratchpad ごと消えた。残るのは読みメモだけで、このカードの読み値は全てそこからの写し（`source_type: documentation`）
2. **defer 先の不在による with arm の偽陰性。** headline-craft は defer 先として `writing-ecosystem` の Title Conventions と `title-reviewer` agent を名指すが、どちらも隔離された run に無い（run は user の skills を load しない — plugin-evals docs「How runs are isolated」。加えて両者は global にも無く `~/MyAI_Lab/zenn-content` に移設済み）。agent が不在を説明する文を先頭に足し、`core_claim` と `criteria` を落とした。環境依存の defer を持つ skill は native eval で偽陰性を生みうる
3. **`--threshold` 既定 1.0 で exit 1。** run 失敗は 0 件でも、case の score 0.556 が 1.0 を下回るので exit 1 が返る。with arm に 1 run でもブレがある skill をこのまま CI に載せると常に赤になる
4. **tool trace は `--keep-temp` 無しで消える。** report に残るのは grader が見た最終メッセージ（`focus: last_message`）だけで、6 run とも `tracePath` は存在しなかった
5. **grader schema の発見コスト。** `tool_used` の `tool` / `min` / `arm` は `--help` に無く、CLI binary の埋め込み doc から掘った。非対話で case を書くと仕様の発見に手間がかかる

## 有効性の状態

**単発。** suite を 1 回（各 arm 3 run）走らせただけで、生値も残っていない。読める結論は「この case・この環境では with/without の delta が +0.556 と出て、発火検出 grader が 3/3 で skill の読み込みを示した」まで。

- `再現済み` へ動く条件: 同じ case を生値を残して（`--output-dir` を repo 側に置く等）別の機会に走らせ、delta の符号が一致する
- `不成立` へ動く条件: with arm の失敗の主因が defer 先の不在ではなかったと分かり、delta が skill の効果を表していないと判明する

## 欄の対応表

| このカードの欄 | aggregate-result.json（schemaVersion 1） | Every Eval Ever v0.3.0 | Inspect AI EvalLog |
|---|---|---|---|
| frontmatter `eval_library` | `claudeVersion`（版） | `eval_library{name,version}` | — |
| frontmatter `evaluation_timestamp` | 結果 dir の timestamp | `evaluation_timestamp` | — |
| frontmatter `retrieved_timestamp` | — | `retrieved_timestamp`（EEE は Unix epoch） | — |
| frontmatter `source_type` / `evaluator_relationship` | — | `source_metadata.source_type` / `source_metadata.evaluator_relationship` | — |
| frontmatter `num_samples` | `--runs` の値（arm ごとの run 数） | `evaluation_results[].score_details.uncertainty.num_samples` | — |
| frontmatter `execution_command` | — | `evaluation_results[].generation_config.generation_args.execution_command` | — |
| frontmatter `log_updates` | — | — | `log_updates`（考え方のみ） |
| 環境 `claudeVersion` | `claudeVersion` | — | — |
| 生の読み値 with の score | `cases[].aggregates.score` | — | — |
| 生の読み値 delta | `cases[].aggregates.delta` | — | — |
| 生の読み値 run 別 score | `cases[].arms.with[]` / `cases[].arms.without[]` | — | — |
| 生の読み値 `fired` の集計外 | grader 結果の `scored: false` | — | — |
| 生の読み値 `partial` / run の `error` | `partial` / `cases[].arms.*[].error` | — | — |
| 生の読み値 cost | `costUsd` | — | — |
| 生の読み値 run 壁時計 | `durationSeconds`（同値かは未確認） | — | — |

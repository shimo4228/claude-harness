---
origin: shimo4228
instrument: claude plugin eval --ablation with-without
subject: widen-depth
validity: 単発
source_type: evaluation_run
evaluator_relationship: first_party
eval_library:
  name: claude plugin eval
  version: 2.1.299
evaluation_timestamp: 2026-10-14T05:36:38Z
retrieved_timestamp: 2026-10-14
num_samples: 3
execution_command: "claude plugin eval <copy>/widen-depth --ablation with-without --runs 3 -j 4 --no-publish --trust-plugin --judge-model haiku --max-cost-usd 10 --output-dir <out> --report <out>/report.html --json <out>/result.json"
log_updates: []
---

# s7 — widen-depth の native ablation（2026-10-14）

`widen-depth` の手順 1（四点を示して人間に返す）が、「深い版にしたい」と意図だけ伝えた状態に対して出力の形を変えるかを測った単発の記録。生値は [aggregate-result.json](s7-widen-depth-native-ablation-2026-10-14/aggregate-result.json)、suite 一式は [suite/](s7-widen-depth-native-ablation-2026-10-14/suite/)。

## 設計

- 問い: skill を load した arm が、四点（一流がやること・生の素材・方法と道具・外部の判定）を依頼に即して具体的に出し、作業を始めずに人間へ返すか。without arm との差を delta で見る。**問うのは形の再現性で、広げた依頼が良い結果を生むかは問わない**
- 計器の使われ方: [skill-creator §5](../../skills/skill-creator/SKILL.md) の behavior gate（with/without screening）
- 対象: `~/.claude/skills/widen-depth/SKILL.md` を scratchpad に copy し、`disable-model-invocation: true` の 1 行だけ外した（本番は slash 専用で、eval の run から Skill tool で呼べるようにするため）。本文は無改変
- case: 6 本。harness の著者がしそうな依頼 1〜2 文に、共通の 2 文「プランに入る前に、この依頼をもっと深い版にしたい。手伝って。」を足した。without arm にも「深くしたい」意図は届くので、意図だけとの差を測る
  - `hook-latency` / `research-summary` / `quiz-typos` / `mix-track` / `article-reach` / `flaky-tests`（本文は suite/evals/*/prompt.md）
- prompt.md frontmatter: `max_turns: 10` / `allowed_tools: [Read, Skill]`
- grader（6 case 共通、全文は suite/evals/*/graders/）:
  - `four_points`（llm）: 四点すべてが依頼に即して具体的。一般論は不可、一つでも欠ければ fail
  - `hands_back`（llm）: 作業を実行せず、足し引きや選択を人間に返して終わる
  - `fired`（`tool_used: Skill`, `arm: with-only`、score に入らない）
- arm: with / without 各 3 run × 6 case = 36 run。run の score は scored な 2 grader の pass 率

## 環境

- `claudeVersion`: 2.1.299
- 被験 model: 既定（`--model` 未指定）。解決された model 名は未記録
- judge: haiku（1 grader につき 3 票）
- flag: frontmatter の `execution_command`。`--concurrency 4`、`--threshold` 既定 1.0、`--keep-temp` 未指定
- 隔離: run は plugin だけを load した session で走る（user の skills・CLAUDE.md・memory は無い。plugin-evals docs「How runs are isolated」、s1 で 2026-09-28 照合）。ただし Read は許可したので、without arm の 1 run は `~/.claude` 周辺を読みに行った（下の読み）

## 生の読み値

| 欄 | 値 |
|---|---|
| `aggregates.overallScore`（with） | **1.0**（6/6 case） |
| `aggregates.meanDelta` | **+0.5** |
| `cases[].aggregates`（6 case とも同値） | score 1.0 / scoreWithout 0.5 / delta +0.5 |
| `partial` | `false` |
| run の `error` | `null` × 36 |
| `costUsd`（総額） | **$2.842**（with $1.525 / without $1.317。judge 分 with $0.077 / without $0.067 は内数） |
| `durationSeconds` | 322 |
| turns | with 3 × 18 / without 1 × 6, 2 × 9, 3 × 3 |
| exit code | 0 |

grader 別（36 run）:

| grader | with | without |
|---|---|---|
| `fired` | 18/18 pass | 実行されない |
| `four_points` | 18/18 pass | 0/18 pass |
| `hands_back` | 18/18 pass | 18/18 pass |

導出: without の score 0.5 = `hands_back` だけ pass（1/2）。delta +0.5 = 1.0 − 0.5。

judge の割れ（3 票が一致しなかった grader 判定）: 108 判定中 3（`hook-latency` without `hands_back` × 2、`mix-track` with `four_points` × 1）。どれも多数決の結論は上表のとおり。

読み:

- with arm は 18 run とも、四点を見出し付きで並べ、最後に「足したい・外したいものは？」と返す同じ形だった
- without arm は 18 run とも「深くする」を**人間に状況を聞き返す**方向に解釈した（現状・症状・制約・ゴールの質問票と、空欄つきの依頼文テンプレート）。生の素材と外部の判定はほぼ出ない
- 差の中身は「誰が知識を出すか」: without は人間に埋めさせ、with はモデルが一流の素材・道具・判定を先に出す（例 `mix-track`: ステムの書き出し、ラウドネスを揃えたブラインド ABX、リファレンス曲との平均スペクトル差）
- `hands_back` は without も全 pass なので弁別していない。「作業を始めない」は skill 無しでも守られる

## 測らなかったもの

- 広げた依頼が、元の依頼より良い結果を生むか（この測定の問いではない。`four_points` は skill の四点をほぼそのまま grader にしているので、自己の形式への一致を測っている）
- 手順 2（前提を疑う）・手順 3（無茶だが妥当な目標）と多ターンの対話（1 ターンで終わる構成）
- `widen-altitude` / `widen-range` / 流れの `widen-the-ask`
- without arm の質問票と with arm の四点を合わせた形のほうが良いか
- 別の日・別の CLI 版・別の被験 model での再現、haiku 以外の judge
- 実際の発火（本番は `disable-model-invocation: true` で slash 専用。`fired` は copy での発火で、本番の発火率を表さない）

## 既知の故障

1. **grader の循環。** `four_points` は skill 本文の四点を言い換えた基準なので、delta は「skill がその形式を出させる」ことの確認に近い。without arm が別の妥当なやり方（聞き返し）を取った分も fail に数える
2. **`hands_back` は無弁別。** 両 arm 全 pass で、delta に寄与しない
3. **生値の加工。** aggregate-result.json の `suite.root` と case の dir にあった scratchpad の絶対パスを `<copy>/widen-depth` に置換した。他の値は無加工。同内容だった `result.json` と `report.html` は残していない
4. **tool trace は無い。** `--keep-temp` 無しで run の trace は消えた。残るのは grader が見た最終メッセージ（`evidence`）だけ

## 有効性の状態

**単発。** 1 回、6 case × 3 run × 2 arm。読める結論は「この 6 case・この環境で、skill は 18/18 で四点の形を出し、意図だけの without は 0/18 で出さなかった」まで。

- `再現済み` へ動く条件: 同じ suite を別の機会（別の CLI 版か別の日）に走らせ、`four_points` の with/without の差の向きが一致する
- `不成立` へ動く条件: `four_points` の判定が出力の中身でなく見出しの有無だけで pass していたと分かる（evidence を読み直して判定する）

## 欄の対応表

欄の出典は [README](README.md)「借りた名前の出典」。このカードで使った aggregate-result.json の欄: `claudeVersion` / `costUsd` / `durationSeconds` / `partial` / `aggregates.overallScore` / `aggregates.meanDelta` / `cases[].aggregates.{score,scoreWithout,delta}` / `cases[].arms.{with,without}[].{turns,costUsd,judgeCostUsd,error,graders[].{passed,judgeVotes,scored}}`。

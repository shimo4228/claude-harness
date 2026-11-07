# ADR-0068: 5 skill の退役 — invoke 0 の reference 型 skill は「監査日を除いた organic read」で存在を再検査する

## Status

accepted

## Date

2026-09-15

## Context

2026-09-15 の skill-stocktake（full、60 本）は Retire を 2 本しか出さなかった
（`agent-harness-construction`、`thermo-nuclear-code-quality-review`）。著者が「ほとんど使用されて
いないのがいっぱいあったのに、どういう判断で退役させていないのか」と問うた。

skill-stocktake の Phase 4 は「Content owns the verdict; usage is reference evidence only」で、
Retire は (a) 前提の陳腐化 (b) 別資産への完全吸収 (c) 内容の薄さ、の 3 経路に限る。この規則の
下で batch agent は存在パス B（cost asymmetry）を「`disable-model-invocation: true` だから常駐
コスト 0」「implementation-chain の chain 行から名指しされている」で Yes と答えていた。前者は
selection cost しか見ておらず drift / maintenance cost を無視する。後者は pointer の存在を価値の
証拠にしている — pointer は claim であって evidence ではない（Phase 3 の contradiction check と
同じ原則）。

そこで invoke 0 の群について read event を分解した（`metrics/skill-usage.jsonl`、log span 95 日、
監査日 = results.json の evaluated_at と s1 監査 / generation-audit の実施日 6 日を除外）:

| skill | 行数 | invoke（全期間） | organic read | 最終 organic read |
|---|---:|---:|---:|---|
| e2e | 232 | 0 | 3 | 2026-07-13 |
| ai-regression-testing | 476 | 0 | 4 | 2026-08-06 |
| python-patterns | 350 | 0 | 7 | 2026-07-28 |
| agent-harness-construction | 113 | 0 | 0 相当（11 read は全部監査日） | — |
| thermo-nuclear-code-quality-review | 117 | 0 | 0 | — |

reference 型 skill は invoke されず読まれるだけなので invoke 0 は未使用を意味しない、という
反論は正しい。だが read の大半が stocktake 自身によるもの（監査が監査対象を読む）で、実作業の
read は数回、7〜8 月で止まっている。python-patterns は description が 2026-09-02 に削除された
節を約束したまま 2 週間誰も気づかなかった — 読まれていないことの直接証拠。

比較対象として、同じ invoke 0 でも `llm-as-judge`（organic 9、8 月に組織的に読まれた）、
`loop-design-check` / `measurement-discipline` / `harness-boundary`（9 月にも read）は reference
として機能している痕跡があり、今回は残す。

## Decision

1. **5 skill を `git rm`**: `e2e`、`ai-regression-testing`、`python-patterns`（以上 3 本は著者裁定、
   organic read 証拠）、`agent-harness-construction`（消費者ゼロ — Observation 契約
   `next_actions` の grep は自身のみ）、`thermo-nuclear-code-quality-review`（implementation-chain
   の reviewer 指示「追加の抽象層は optional、適用しない」と正面衝突、配線なし、`origin:
   cursor/plugins`）。
2. **残余の移動は 1 件だけ**: python-patterns の「Patch Target Migration」節（`mock.patch()` の
   ターゲット付け替え）を `skills/refactor-clean/SKILL.md` へ本文移設。refactor-clean が唯一の
   名指し消費者だった。他の内容（ruff / pyright の pin、lint-gates、frozen+slots、uv run vs uvx
   等）は git 履歴に残し、必要時は verify-bootstrap Step 2 が search-first で再選定する。
3. **pointer の repoint**: `rules/common/testing.md`（実行手順は tdd のみ）、
   `skills/implementation-chain/SKILL.md`（Chain Matrix の E2E / 回帰テスト行と C 条件を削除）、
   `skills/tdd/SKILL.md`（正本分担表 2 行と mock 罠の正本 pointer）、
   `skills/repair-discipline/SKILL.md`（description の NOT-for）、
   `skills/harness-boundary/SKILL.md`（description / 適用外 / Related）、
   `skills/skill-creator/SKILL.md`（register 例の名指しを一般化）、`AGENTS.md`、
   `skills/rules-stocktake/SKILL.md`（例文）、`skills/agent-stocktake/SKILL.md`（bulk context
   isolation の例から e2e-runner を外す）。
4. **skill-stocktake の存在パス B の読み方**: 「常駐コスト 0」と「chain 行からの参照」は B の
   Yes の根拠にならない。invoke 0 の reference 型 skill は organic read（監査日除外）を
   pressure-test の evidence に使う。この規律は次回 stocktake 前に skill-stocktake 本文へ
   1 行で入れる（今回の Improve 指摘に併合）。
5. **`agents/e2e-runner.md` も `git rm`**（著者裁定）。skill `e2e` と対で死んでいた（s1 監査
   2026-08-29 の指摘。`metrics/agent-usage.jsonl` 1,366 行に起動記録なし）。agent-stocktake の
   ledger から entry を外す。

## Review-when

- Python repo のセッションで ruff / pyright の選定・lint-gates の判断が繰り返し必要になり、
  verify-bootstrap の search-first 再選定より git 履歴からの復元（`git show
  deff89d:skills/python-patterns/SKILL.md`）が安いと分かったとき → python-patterns を
  skill-creator 経由で書き直す
- E2E / AI 回帰テストの需要が実作業で発生したとき（79 日 + 17 日で 0）→ ECC 原本でなく
  skill-creator で薄く書き直す
- organic read の分解が次回 stocktake で verdict を変えなかったとき → Decision 4 は不要な
  規律として畳む

## Alternatives Considered

### reference 型として残す（batch agent の verdict どおり Keep / Improve / Update）
organic read が 3〜7 回で 7〜8 月止まり。description の欠落に 2 週間誰も気づかない skill は
reference として機能していない。却下。

### 5 本に stricter な Stage 2 pressure test を先に回す
「この 95 日でこの skill が無かったら失敗した task があるか」を held-out 相当の問いとして
提案したが、著者が 3 本を直接裁定した。残る候補（`repair-discipline` organic read 1、
`session-judgment-mining` organic read 1）は次回 stocktake で同じ問いを当てる。未決。

### e2e-runner agent は agent-stocktake の判定に委ねる
skill 側の証拠しか無いので次回 agent-stocktake に回す案。著者が同セッションで退役を裁定した
（skill を失った agent は入口を失っており、agent-usage.jsonl にも起動 0 で待つ理由が無い）。却下。

## Consequences

### Positive
- skill 60 → 55 本、agent 12 → 11 本。ECC 由来の test family 3 本（合計 1,058 行）+ 対の
  e2e-runner agent と外部由来 1 本が消え、drift 面積が減る
- ADR-0018 が `rules/python/` の吸収先とした python-patterns が消えたことで、Python 慣行の
  正本は「機械強制層（ruff / pyright hook）+ verify-bootstrap の再選定」だけになる。文章版の
  正本が無い状態が明示された

### Negative
- ADR-0018 §3 が python-patterns へ全文吸収した rules/python の内容（redirect token leak /
  case-insensitive sanitizer bypass / frozen AST ゲート等）は harness から消える。git 履歴に
  あるが、次セッションが存在を知る経路は本 ADR だけ
- implementation-chain の Chain Matrix から E2E / 回帰テスト行が消え、「ユーザー可視フローを
  変えたら E2E」という条件付き発火が無くなる

### Neutral / Follow-ups
- ADR-0011（e2e を Keep と判定）、ADR-0018 §3、ADR-0039 §Consequences に注記
- skill-stocktake 本文への Decision 4 の反映は今回の Improve 指摘（skill-creator 経由）に併合

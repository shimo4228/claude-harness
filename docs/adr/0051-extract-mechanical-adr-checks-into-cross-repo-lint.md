# ADR-0051: ADR レビューの機械チェックを cross-repo lint script へ抽出し、adr-reviewer を意味的チェック専任に薄化

## Status

accepted

## Date

2026-08-26

## Context

`adr-reviewer`（opus agent）は、機械判定可能なチェック（7 節存在・Review-when 有無・
Status 語彙・Date 書式・index 整合）と、意味的チェック（後付け正当化・藁人形
alternatives・片面 Consequences）を両方持ったまま運用されてきた。両者は判定コストの
性質が違う — 前者は決定論的でトークンを要さず、後者は文脈読解を要する。
「存在 = code、内容 = LLM」の分業は
[ADR-0021](./0021-rules-metadata-and-premise-lint-gates.md) が導入し、
[ADR-0044](./0044-adr-review-when-and-dated-annotation.md) Decision #5 がそれを ADR へ適用して
`harness_lint.py` に `lint_adr_review_when` を置いた。本 ADR はこの分業線を
ADR レビュー全体へ拡張する。

2026-08-26 のセッション内 Explore agent 調査で実測した状況は次の通り。ADR corpus は
harness の 50 件を含め 18 repo に分布し、最大の contemplative-agent（CA）は 98 件
（en/ja 対で 196 ファイル）を持ち、テンプレの 7 節目は harness の Review-when と異なり
References になっている。機械的逸脱は repo ごとに分布する — CA には見出し大小文字ゆれが
2 件（`## Alternatives considered`）、harness には Status 節が散文続きになっている例が
8 件、zenn-content には Date 節欠落が 11 件中 6 件、g-kentei-ios には命名規則違い
（`ADR-002-` 形式）がある。CA の git 履歴からは、レビュー修正の頻出パターンとして
誤引用・surviving scope の置き場所・造語の出所・full vs partial supersede の誤判定・
gitignored パス参照の 5 種を採掘した（出荷した事例集はこれに harness 由来 2 種
〔数値の分母・カウント条件の固定対象〕を加えた 7 パターン）。

`adr-reviewer` は現状 `~/.claude` の harness 専用実装（`harness_lint.py`）にしか
機械チェックを委ねられず、CA を含む他 repo のレビューでは目視に頼っていた。テンプレ節が
repo ごとに異なる（Review-when vs References）ため、単純な固定リストの流用も効かない。

## Decision

1. 機械チェックの唯一の正本として `skills/adr-writer/scripts/adr_lint.py` を新設する。
   既定は evidence モードとし、JSON を出力するのみで判定・exit コードによる合否表明は
   行わない（`readme_evidence.py` と同じ契約）。`--gate` オプションは ad hoc の
   blocking 実行専用とする。検査対象 repo の `docs/adr/README.md` にある Template
   fenced block から期待節セットを自動適応する — これにより CA の References テンプレも
   移行なしに検査できる。免除境界は **gate 用フラグとして用意する**
   （`--sections-from` / `--require-review-when-from`。**既定は無制限** — 値は repo ごとに
   実測で決め、実行座標の文書に記す。harness は `--sections-from 44 --require-review-when-from 44`
   で ADR-0009 の 2 節欠落を免除）。Status は先頭語の prefix 判定とし散文続きを許容する。
2. 実行座標は skill / agent のステップに置く — adr-writer skill の Step 4.5（書き時）と
   adr-reviewer agent の Step 0（レビュー時）。verify.sh やコミット hook への常時配線は
   行わない。

   > **注記 2026-08-29（射程を狭める。partial、Status は変えない）**: この既定は「対象に
   > 正本 writer skill が存在する」ことを暗黙の前提にしていた（adr-writer / readme-writer）。
   > `hooks/*.sh` のような実行資産にはその skill が無く、「skill ステップ」という座標が
   > そもそも存在しない。そのクラスでは `verify.sh` 側が既定になる。判定軸（課税率 ×
   > 既製性）と例外の正本は skill `review-to-lint` §5 — ここには複製しない。
   > 発見経路は RFC-0005 の履歴掘削（同 RFC #13〜#15）。
3. 頻出指摘は `skills/adr-writer/references/review-findings.md` に日付・commit 参照
   つきの事例集として蒸留し、adr-writer skill Step 3 の予防チェック（packet 確定前の
   自己点検）に配線する。判定基準の正本は adr-reviewer に置いたまま — 事例集は基準の
   要約を正本参照つきで持つことを許す（第 2 の記録場所であることは Consequences に計上）。
4. adr-reviewer から機械項目（節存在・Status enum・Date 書式）を削除し、意味的チェック
   専任に薄化する。冒頭に「`adr_lint` を実行し JSON を findings に転記する。目視で
   数え直さない」という Step 0 を追加し、対象 repo の README ローカル規約（テンプレ・
   supersede half scope 規約）を適用する指示を加える。これは
   [ADR-0044](./0044-adr-review-when-and-dated-annotation.md) Decision #6 が adr-reviewer へ
   置いた 7 節チェックの配置を**部分的に狭める**（0044 側に日付つき注記を追加済み）。
5. `harness_lint.py` の `lint_adr_review_when` は残置する（[ADR-0044](./0044-adr-review-when-and-dated-annotation.md)
   Decision #5 の配置のまま）。Review-when 検査だけ `adr_lint` と二重実装になるが、
   両者は同一規約（ADR-0044）を参照するものであり、解消条件は Review-when 節に置く。
6. この抽出手続きを汎用 skill `skills/review-to-lint/SKILL.md`（user-invocable）として
   一般化する — 3 分類（deterministic / semantic / hybrid）→ search-first → evidence
   script → reviewer 薄化。他の reviewer（citation-formatter 等）への適用は 1 件ずつ
   別セッションで行い、本 ADR のスコープ外。

   > **注記（2026-08-26, [ADR-0054](./0054-extract-agent-stocktake-and-learn-eval-mechanical-checks.md)）**:
   > 「1 件ずつ別セッション」をこの条項が絶対条件としては保持しない。ADR-0054 は
   > agent-stocktake と learn-eval の 2 件を 1 セッション・1 ADR で扱った — 置き換える
   > 対象がどちらも「実施したかの自己申告」1 種で、分業線が同一だったため。分業線が
   > 異なる適用（citation-formatter の DOI 実在検証など）には、この条項が元の形で効く。

## Review-when

- `adr_lint` と `harness_lint.py` の `lint_adr_review_when` の判定の食い違いは**自動では
  観測されない**（実行座標も対象も別）。ADR 系の棚卸し（context-sync）または著者が
  気づいた時点で同一入力の比較を 1 回走らせ、食い違えば二重実装を解消する。
- 機械的逸脱の commit 混入も Date・大小文字・index drift は commit 面で構造上観測されない。
  context-sync 実行時に `adr_lint` を harness corpus へ 1 回当て、commit 済みの逸脱が
  見つかったら commit 面（verify.sh）への配線を再訪する。
- CA 等の repo が独自テンプレを廃止して harness の 7 節へ統一したら、テンプレ自動適応の
  複雑さを再訪する。

## Alternatives Considered

### harness_lint.py の拡張のみ

`harness_lint.py` に機械チェックを足し込むだけで済ませる案。却下: `~/.claude` 専用で
CA 等の他 repo に届かず、cross-repo 用には別実装が要ることになり二重実装になって drift
する。

### verify.sh への `--gate` 常時配線

`adr_lint --gate` を verify.sh に常時配線し、commit ゲートとして毎回強制する案。却下
（著者指示、2026-08-26）— ADR を触らない commit にも毎回検査が走る過剰配線になる。
skill ステップでの実行で十分であり、commit 面の最小限は既存の `lint_adr_review_when`
が担保している。

### 何もしない（目視レビュー継続）

機構を足さず adr-reviewer の目視のみで続ける案。却下: 機械項目は opus のトークンと注意を
消費し続け、CA 等 harness 外 repo では固定リストの流用も効かない（Context 記載の逸脱分布）。
本 ADR は機構を足す判断なので status quo を明示的に退ける。

### 外部ツール adrkit の採用

search-first で as-of 2026-08-26 に照合した外部ツール
[adrkit](https://github.com/mbeacom/adrkit)（pre-1.0、npm `@adrkit/cli`）を採用する案。却下:
YAML frontmatter（`id` / `status` / `reversibility` / `blastRadius` / `affects`）が
必須で、frontmatter を持たない自前テンプレの 300+ 件が全件移行を要する。Review-when
境界・index drift といった自前規約は adrkit の対象外でもある。加えて pre-1.0 かつ
Node 22 依存。未決 — 再訪条件: 自前テンプレを MADR 系へ寄せる判断をしたとき。

### レビュー知見の writer skill への全面吸収（adr-reviewer 退役）

頻出指摘の事例集を adr-writer skill に全面吸収し、adr-reviewer agent 自体を退役させる
案。却下: 意味的・敵対的チェック（後付け正当化・藁人形・片面 Consequences）は書いた
本人（同一セッション）には構造的に検出できない。skill-creator が fresh-context の
判定器を使うのと同根の理由による。

## Consequences

### Positive

- 機械的逸脱の検出が決定論化し、トークンゼロで再現可能になる。
- CA を含む任意の repo で同一実装が使える（テンプレ自動適応により Review-when 系と
  References 系の両方を検査できる）。
- adr-reviewer の注意が意味的チェックに集中する。
- 頻出指摘が書き時（adr-writer Step 3）に予防される。

### Negative

- Review-when 検査が `adr_lint` と `harness_lint.py` の 2 実装に重複する。同一規約
  参照のため drift リスクは低いが、解消条件は Review-when 節に置いた。
- lint 実行が skill ステップ依存になり、skill を経由しない ADR 編集には効かない —
  commit 面の網は既存の `lint_adr_review_when` 検査のみに留まる。
- skill sub-project が 1 つ増え、`pyproject` + tests の保守対象になる。加えて常駐 skill が
  1 件増える（review-to-lint の description residency、Decision #6）。
- `--gate` を素で叩くと既知免除で赤くなる（harness では `--sections-from 44` が必要）。
  ad hoc 専用設計の運用コストで、免除境界の値は実行座標の文書が持つ。
- `review-findings.md` は adr-reviewer 基準 §6 / §1 の要約を正本参照つきで持つ —
  第 2 の記録場所であり、drift は正本リンクで抑える（Decision #3）。

### Neutral / Follow-ups

- 新規ファイル: `skills/adr-writer/scripts/adr_lint.py` / `tests/test_adr_lint.py` /
  `references/review-findings.md`。
- 変更対象: `agents/adr-reviewer.md`（薄化）、`skills/adr-writer/SKILL.md`
  （Step 3 予防チェック / Step 4.5 追加）。
- 分業の先例は [ADR-0044](./0044-adr-review-when-and-dated-annotation.md)、writer
  agent の render 専任原則は [ADR-0016](./0016-writer-agents-render-not-decide.md)。

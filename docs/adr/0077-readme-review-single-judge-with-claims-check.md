# ADR-0077: readme-writer のレビューを readme-judge 1 本にまとめ、主張とコードの照合を判定器に入れる

## Status

accepted — [ADR-0070](./0070-relax-positive-form-rule-and-verbatim-builtin-overrides.md) Decision 3 の
README agent 2 本の model 配置、[ADR-0033](./0033-subagent-model-tier-by-downstream-verification.md)
Decision 2 の README reviewer の名指し、[ADR-0055](./0055-review-chain-single-pass-regression.md) の
「writing chain は対象外・不変更」のうち README chain の codex 既定配線を、部分的に弱める（注記は各 ADR 側）

## Date

2026-09-25

## Context

- 著者の依頼（2026-09-25）: 「レビューが判定器も含めて 3 つあるのは過剰だから、まとめて」。同じ日に、
  改修前の readme-writer のスナップショットを fresh context の agent に批評させ、24 件の指摘を得た。
- 旧構成は、改稿ループの判定器 `readme-judge`（verdict、opus）、panel の `readme-reviewer`（フロア・
  構成・視覚、fable）と `readme-clarity-reviewer`（初見読者・日本語 register・言語間、opus）、公開 repo
  では既定で panel に入る `codex-review`。批評の数えでは、2 言語の README 1 本で agent の起動が約 11 回、
  無条件の人間ゲートが 3 つ。
- 批評と旧ファイルの照合で確かめた、構成に関わる所見:
  - 造語の棚卸しは judge の R10 と clarity の §1 が重ねて行っていた。reviewer の本文の 2 つの境界文は、
    その持ち主を別々に書いていた
  - reviewer は 1 つの出力に 2 つのラベル（Overall Assessment の `MAJOR ISSUES` と Final Recommendation の
    `MAJOR REWRITE NEEDED`）を持ち、`skills/readme-writer/SKILL.md` は人間へ回す条件を `MAJOR REWRITE`、
    reviewer の境界文は `MAJOR ISSUES` で書いていた
  - readme-writer の Workflow では、フロアの有無を見るのは panel の reviewer で、binding の verdict には
    入っていなかった（implementation-chain では reviewer の `MAJOR ISSUES` が CRITICAL 停止に対応していた）
  - README の主張をコードと照らす工程が無かった。CA の実行記録
    （`skills/readme-writer/evals/fixtures/ca-readme-2026-08-19.expected.md` の Run log、2026-08-20）では、
    判定器の Publishable の後に著者通読が 5 件、codex の節レビューが事実の誤りを 5 件拾った
  - 最終判定は毎回質問を作り直し、凍結後に 1 文字でも直せば再実行で、回数の上限が無かった
- 最後の点は 2026-09-25 に起きた。jev-skill-router と jev-research-pipeline の README（各 2 言語）で、
  fresh の最終判定を 2 回ずつ回し、毎回新しい文単位の Fix が出た（記録は
  `skills/readme-writer/evals/read-through-log.md`）。
- 同じ日、repo を読める general-purpose agent に 2 つの README の古い記述を監査させたところ、判定器が
  見ていなかった事実の誤りが出た（例: jev-skill-router の README は project skill の閉じ込め範囲を skill の
  ディレクトリと書いていたが、実装は repo 単位で、repo 内の `.env` へのリンクは送られる）。
- `codex-review` は [ADR-0013](./0013-cross-model-review-seam-via-codex.md) の seam で、ADR-0055 が opt-in に
  絞ったうえで writing chain を対象外に残した。その例外により、readme-writer は公開 repo で codex を
  既定の panel に配線していた。

## Decision

1. readme-writer のレビュー agent を `readme-judge` 1 本にする。`readme-reviewer` と
   `readme-clarity-reviewer` を退役し、それぞれの問いを `skills/readme-writer/references/readme-judge-checklist.md`
   の §F（フロアの有無）、§J（日本語の文体と言語間の対応）、R10（造語の規則を 1 本に）へ移す。
   2 本を名指していた `skills/prose-translation/SKILL.md`・`skills/implementation-chain/SKILL.md`
   （verdict の対応表）・`skills/agent-stocktake` のコメント・zenn-content の `prose-clarity-reviewer` は
   `readme-judge` か checklist を指すように付け替える。
2. `readme-judge` は 1 回の起動で全言語版を読み、Phase A（README だけを読んで答えを凍結）→ Phase B
   （主張を repo のコード・設定・docs と照らし `file:line` を添える。llms.txt・llms-full.txt・
   graph.jsonld があれば、README と食い違う箇所も挙げる）→ Phase C（反証 3–5 問、集計しない named
   verdict）の順に進む。旧 Workflow Step 9 の README と機械面の照合は Phase B が持つ。tools は
   Read / Grep / Glob とし、証拠 JSON は orchestrator が作って path を渡す。model は opus のままにする。
   ADR-0033 の軸（出力を検査する層が下流にあるか）で見ると、統合後は判定器の後に別の agent の検査が
   無く、著者通読は README を読むが、主張とコードの照合は読まないため、上位のモデルに当たる。
3. 最終判定は fresh で 1 回にする。Fix なら span で直し、同じ質問セットで recheck を 1 回回して、結果に
   かかわらず著者通読へ渡す。新しい質問での再実行はしない。
4. `codex-review` は著者が求めたときだけ回す。readme-writer の既定の工程から外す（ADR-0055 の opt-in を
   README chain にも当てる）。
5. 付随して、readme-writer にモード（Rewrite / Incremental / Review-only / About-only）を置き、
   implementation-chain の Doc Sync は Incremental を使う。tagline は Step 1 で著者が選び、判定器に
   tagline を判定するモードは作らない。

同じ変更に含まれる次のものは、この ADR の対象外で、commit 本文に記録する: 冒頭の概要図の既定化、
「著者のほかの仕事」節、変わる事実の表、profile / hub README の型、DOI の無い repo の homepage の持ち主、
証拠スクリプトの新しい検出器（`register_ja`・`broken_anchors`・`own_repo`）。

## Review-when

- `skills/readme-writer/evals/read-through-log.md` の次の 3 行（言語版の組を 1 行と数える）のうち 2 行で、
  通読の指摘数が 5（CA 2026-08-20 の記録）を上回ったら、1 本の agent の注意に収まっていない疑いとして、
  lens を分け直すかを再検討する。CA の 5 件は codex も回したうえでの数で、統合後は codex が拾っていた
  事実の誤りも通読の数に入るので、この比較は早めに発火する側に偏る。
- 通読の「主な種類」の欄に事実の誤り（Phase B をすり抜けたもの）が 2 行続けて記録されたら、照合を
  別の agent に分けるか、codex を公開 repo で既定に戻す。記入は著者が通読のときに行う。
- recheck 1 回で止めた README で、判定器が拾う種類の欠陥（第一画面・論理・継ぎ足し）が公開後に
  見つかり、著者がそれを read-through-log に記録したら、打ち切りの規則を見直す。

## Alternatives Considered

- **現状維持**: codex の節レビューは CA で事実の誤りを 5 件拾った、唯一の実測がある reviewer だった。
  一方で 3 つの lens は重なり、起動回数と人間ゲートが多く、著者は 3 つを過剰と判断した。
- **判定器 + panel 1 本（reviewer と clarity をまとめる）**: 起動は減るが、verdict と findings が食い
  違ったときに人間へ回す経路と、そのラベルの管理が残る。panel と判定器で造語の棚卸しも重なる。
  著者は 1 本で足りる形を求めた。
- **公開 repo では codex を既定に残す（Phase B の実測が出るまで）**: 事実の誤りへの実測がある経路を
  保てる。著者の「過剰」の判断に反し、codex は著者が求めればいつでも回せるので、既定からは外す。
  未決 — 再訪条件は Review-when の 2 つ目。
- **主張の照合を別 agent に置く**: repo を読む agent と README だけを読む agent を分けるのは、repo の
  文脈が未定義語を補完して判定を甘くする問題への素直な対処。1 本の中で Phase A の答えを凍結してから
  Phase B で repo を開く順序で近い隔離を取り、agent を増やさない。未決 — 再訪条件は Review-when の
  2 つ目。
- **最終判定を「通るまで fresh で回す」のまま残す**: 2026-09-25 に各 repo で最終判定を 2 回回して
  収束しなかった。fresh の判定は毎回新しい細部を拾うので、回数で止める。
- **判定器を fable にする**（批評の提案）: 統合後の判定器には下流に別の意味的検査層が無いので、
  ADR-0033 の軸では上位のモデルに当たる。

## Consequences

### Positive

- 2 言語の README 1 本で、`readme-judge` の起動は 2〜4 回（draft、recheck、final、recheck）、無条件の
  人間ゲートは 2 つ（Step 1 と通読 GO）になる。
- 事実の照合が判定の中に入り、`file:line` の証拠つきで Fix の項目になる。README と機械面の照合にも
  持ち主ができる。
- 判定の出力が named verdict だけになり、人間へ回す条件のラベルの食い違いが無くなる。
- 判定器から Bash が外れ、[ADR-0046](./0046-skill-creator-shrink-in-place-and-creation-gate.md) が残した
  「readme-judge の Bash 付き judge の injection 面」の項が閉じる。

### Negative

- 1 本の agent が読む量が増える。checklist の固定質問は §F 3 + R 15 + §J 4 + K 6 の 28 問で、
  動的な質問は 10〜15 問から約 5 問に減らした。注意が薄まるかは Review-when の 1 つ目で見る。
- Phase A と Phase B の隔離は、同じ process の中の順序の指示で、別 process ほど強くない（Read / Grep /
  Glob は最初から使える）。
- 公開 repo での cross-model の脱相関が既定から消える。事実の誤りを拾った実測があるのは codex だけで、
  Phase B はまだ測っていない。
- 初見読者の読書体験を専任で模擬する agent が無くなる。第一画面の 1 文テストを Phase A と R1 に畳んだ。
- implementation-chain では、フロアの欠落が停止条件（reviewer の `MAJOR ISSUES` → CRITICAL）から、
  判定器の Fix（HIGH、継続して直す）に変わる。
- 最終判定を recheck 1 回で止めるので、残った文単位の指摘は著者通読が拾う。

### Neutral

- 運用の規則の正本は `skills/readme-writer/SKILL.md` と `agents/readme-judge.md`。`inspiration.md` は経緯の
  要約とこの ADR へのポインタだけを持つ。
- 元に戻すには、harness の revert に加えて、zenn-content の `prose-clarity-reviewer` と、harness-sync の後
  なら公開 copy（claude-harness と readme-writer の単独 repo）も戻す。

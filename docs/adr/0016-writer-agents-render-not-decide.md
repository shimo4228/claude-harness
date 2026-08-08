# ADR-0016: Writer agent は render 専任 — 委譲境界は semantic authority

## Status

accepted

## Date

2026-07-18

## Context

[ADR-0010](./0010-context-sync-cascade-and-writer-agents.md) は documentation authoring を skill + agent に分割し、その責務を「skill = orchestration、**agent = subjective body generation**」と framing した (`codemap-writer` / `adr-writer`)。

EN→JA 翻訳 capability の新設要求が、この framing が **too broad** であることを露呈させた。要求は当初「専用 translation agent を Sonnet で作る」だったが、grill と cross-model review (Codex, ADR-0013 の脱相関 seam) を通じて次が判明した:

- 品質不満（「英語のまま読みづらい / 専門用語が英語のまま」）の主因は **方法論の不在**（term policy・脱翻訳調 pass・QA が無い直訳）であって、モデル能力不足ではない。メインループは既に最上位モデル (Opus 4.8) で走るため、Sonnet の agent に落とすのは品質不満に対して逆効果。
- 委譲可否の正しい境界は「機械的か著述か」ではなく、委譲された出力が持つ **semantic authority の量**。`codemap-writer` の repo scan → token-lean summary は observation で低権限だが、翻訳の日本語 prose 生成は非収束な著者 voice を狙うため高権限。両者が同じ「body generation」に括られていた。
- **bounded input ≠ low judgment**: 原文が固定でも忠実な訳は多数あり、品質は激変しうる。入力が確定していることと変換が易しいことは別。
- **model 継承は能力しか救わず文脈損失は救わない**: agent が `model:` を省略してメインループの Opus を継承しても、なぜこう訳すか・著者の声という会話文脈は lossy handoff で失われる。隔離が不要なら「メインループ skill」が厳密に上位。

さらに既存の `adr-writer.md` が、この too-broad な framing の帰結として **意味的権限のリーク**を持っていた: `## Refactor input into the template` の Context 節が「consequence を logically entailed なら膨らませてよい」と明記していた。推論による consequence の追加は意味的判断であり、agent は「refactor, never invent」を掲げながら裏口でそれを許していた。

## Decision

Writer agent の委譲境界を **semantic authority 基準** で ref 定義する。**Writer agent は render する、decide しない。**

### 委譲基準

固定モデルの subagent へ委譲してよいのは、次をすべて満たすとき:

- 入力が明示的で bounded
- 出力が制約されている、または容易に検証可能
- agent が **意味・voice・rationale を決めない**（観察・変換のみ）
- 誤りが安価に検出・可逆

メインループに残す（または委譲するなら最上位モデル + rich context を明示的に手渡す）のは、次のいずれか:

- 出力がユーザー意図の **authoritative な表現**になる
- 重要な入力が会話に implicit に存在する
- 品質が voice / framing / terminology に高感度
- レビューで「著者が何を意図したか」を確実に再構成できない

> 経験則: **観察と、低権限で機械検証可能な変換は委譲してよい。semantic commitment — voice / 意味 / rationale を決める変換を含む — はメインループに残す。**（「変換だから委譲可」ではない: 翻訳の prose 生成は変換だが非収束な著者 voice を狙う高権限変換であり、委譲不可側に入る）

### 適用

1. **EN→JA 翻訳は主にメインループ skill** (`en-to-ja-translation`)。専用 translation/reviewer agent を作らない（姉妹 `ja-to-en-translation` の skill-only 設計を鏡像）。翻訳の変換ステップは非収束な著者 voice を狙う高権限作業のため。超長文のみ、継承モデルの subagent を skill 内オプションモードとして許可し、voice sample + term 表 + localization policy を明示的に手渡す。機械的前処理（term 抽出・保護スパン検出・一貫性 grep）は軽量モデルへ委譲可、最終 prose はメインループ。
2. **`adr-writer` は render agent として残す**（skill-only には崩さない）。ADR は decide（synthesis, 高権限）と render（固定ハウススタイルへの清書, 低権限・検証可能）にきれいに割れ、後者だけの委譲は安全。近隣 ADR 走査 + テンプレ機械処理 = observation の隔離実利も残る。ただし `adr-writer.md` の consequence 膨張許可を撤回し、`adr-writer` skill に「メインループが decision packet を確定・承認してから agent 起動、起動後にメインループが fidelity check」の規律を明文化する。
3. ADR-0010 の「agent = subjective body generation」framing を、本 ADR が **「agent = 承認済み packet の rendering」** に ref 定義する。

## Alternatives Considered

### 専用 EN→JA agent を Sonnet で作る（当初要求）

ユーザーの初案。不採用: 品質不満は方法論の不在が主因で、Sonnet はメインループの Opus より下位のため、品質に対して逆効果。翻訳は頻度の高い hot loop でなくコスト優位も弱い。

### 継承 Opus の翻訳 agent を default にする

`model:` を省略して隔離しつつ品質を保つ案。default 不採用: 継承は能力を救うが lossy handoff（会話文脈・voice 制約の喪失）は救わない。超長文向けの skill 内オプションモードとしてのみ残す（明示的な voice/term/policy 手渡しを条件に）。

### `adr-writer` を skill-only に崩す（翻訳と完全対称化）

synthesis + render をすべてメインループに戻し agent を廃止する案。不採用: ADR の render は固定ハウススタイルという収束的・検証可能な目標を狙うため低権限で、委譲が安全。近隣 ADR の文体走査・採番・テンプレ機械処理を隔離する実利もある。翻訳（非収束な著者 voice）とは変換ステップの権限が異なるため、対称化は不要。

### ADR-0010 の framing を据え置く

「subjective body generation」を維持する案。不採用: この broad な括りこそが `adr-writer.md:119` の意味権限リークを生んだ根であり、observation（低権限）と authoring（高権限）を同一視して誤った委譲を正当化する。

## Consequences

### Positive

- 「機械的 vs 著述」でなく semantic authority という一貫した軸で、任意の writer agent の委譲可否を判定できる
- `adr-writer` の意味権限リーク（推論 consequence の追加）が塞がれ、「refactor, never invent」contract が裏口なく成立する
- EN→JA 翻訳が最上位モデル + full context で走り、品質不満（翻訳調・専門用語）に方法論で直接対処できる
- 将来の writer skill（`llms-txt-writer` 等）の body generation が肥大化したとき、「render は委譲可、semantic commitment は残す」で切る指針ができる

### Negative

- ADR-0010 の framing を後から ref 定義するため、両 ADR を突き合わせないと writer-agent の責務が一目で分からない（相互参照で緩和）
- semantic authority は machine-checkable な閾値でなく judgment call。境界事例（render に見えて実は微妙な voice 判断を含む）では都度メインループの判断が要る

### Neutral / Follow-ups

- `codemap-writer` は本 ADR の基準で「observation → 委譲可」に該当し、現状維持でよい（変更不要の確認）
- 他の writer agent（`prompt-writer` 等）を本基準で棚卸しするのは別作業。本 ADR は adr-writer と翻訳に限定する
- EN→JA 翻訳の脱翻訳調ルールが実運用で不足した場合、term policy を skill 側に足す（rules への昇格は 2+ skill で再出現してから）

## Related

- [ADR-0010](./0010-context-sync-cascade-and-writer-agents.md): 本 ADR が「agent = subjective body generation」を「agent = 承認済み packet の rendering」に ref 定義する対象
- [ADR-0013](./0013-cross-model-review-seam-via-codex.md): 本判断の脱相関 seam（Codex による cross-model 第二意見）を提供
- 当時の `rules/common/patterns.md` にあった structural / semantic 軸。
  rule と global skill は ADR-0035 で退役。Contemplative Agent 系の判断として公開 repo に履歴を残す
- `skills/en-to-ja-translation/SKILL.md` / `skills/ja-to-en-translation/SKILL.md`: 翻訳は skill-only の適用先
- `agents/adr-writer.md` / `skills/adr-writer/SKILL.md`: render 専任 + packet discipline の適用先

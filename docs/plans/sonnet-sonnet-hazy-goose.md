# EN→JA 翻訳スキル新設 + adr-writer の意味権限リーク修正

## Context（なぜこの変更をするか）

**発端**: EN→JA 翻訳の出力が「英語のまま読みづらい／専門用語が特に」。ユーザーは専用エージェント化 + Sonnet を提案した。

**grill + クロスモデル（Codex）で判明した本質**:
- 不満の主因は **方法論の不在**（term policy・脱翻訳調 pass・QA が無く直訳的）であって、モデル能力不足ではない。→ モデルを Sonnet に落とすのは品質不満に対して逆効果。
- 委譲可否の正しい境界は「機械的 vs 著述」ではなく **意味的権限（semantic authority）の量**（Codex）。観察・変換は委譲自由、voice/rationale/訳語決定という意味的コミットメントはメインループに残す。
- **model 継承は能力しか救わず文脈損失は救わない**（Codex）。継承 Opus のサブエージェントでも会話文脈（なぜこう訳すか・著者の声）は lossy handoff で失われる。→ 隔離が不要なら「メインループ skill」が厳密に上位。
- 姉妹 `ja-to-en-translation` は意図的に skill-only（「新規 agent を作らない」）。EN→JA もこれに揃える。
- 検証で `agents/adr-writer.md:119` が「logically entailed な consequence は膨らませてよい」と明記＝意味権限の裏口。ADR-0010 の "agent = subjective body generation" は too broad。

**意図する結果**: (1) EN→JA を JA→EN の鏡像 skill として新設し、翻訳調と専門用語の不満を方法論で解消する。(2) writer-agent の権限を「rendering 専任」に締め、意味権限をメインループに戻す原則を明文化する。

## 非変更（ループを閉じる確認事項）

- **JA→EN 側はエージェント化しない**。当初発言「これも Sonnet エージェントで」は、実在しない agent を指していた前提誤り。skill-only のまま据え置く。
- EN→JA にも**常駐エージェントを作らない**。超長文向けの継承 Opus サブエージェントは skill 内の *オプションモード* に留める。

---

## Part 1: `en-to-ja-translation` skill 新設（feat）

**器**: 新規 `skills/en-to-ja-translation/SKILL.md`。メインループ（Opus 4.8）が実行。専用 reviewer/translator agent は作らない。
**作成手段**: `skill-creator` skill を使い、description の triggering と YAML 妥当性を担保する（`ja-to-en-translation` の description 生成の `: ` YAML 破壊に注意 — 適用後 YAML 検証必須）。

**構造は `ja-to-en-translation/SKILL.md` を鏡像化**。origin: shimo4228 / user-invocable: true。EN→JA 固有として以下を持たせる:

- **Scope**: EN→JA のみ。人間向け prose（essay / research doc / README / ADR / glossary）。対象外＝AI 向け doc（→ llms-txt-writer）、citation format（→ citation-formatter）。JA AI-slop / Voice 正本は `writing-ecosystem` に defer。
- **絶対ルール**: コードブロック・インラインコード・Markdown 構文・URL・DOI・画像パスは非翻訳（JA→EN と共通）。
- **term policy（不満の本丸①）**:
  - 既定は「訳す」。英語保持は**明示例外のみ**（製品名・コード識別子・定着した未訳語）。
  - 初出は日本語優先形 `依存性注入（dependency injection）`。以降は日本語。
  - term-lock 表: 語 / 訳語 / 保持理由（keep-EN か訳すか）を固定し grep で一貫性検証。
- **脱翻訳調 pass（不満の本丸②）**: 専用 pass「日本語の技術ライターは本当にこう書くか？」。英語語順の残存・冗長な受動態・カタカナ乱用・「の」連鎖・直訳された idiom を潰す。著者の既存日本語 prose にキャリブレート。
- **Methodology**: JA→EN と同型の Pre-pass（term-lock + voice fingerprint）→ Pass 1（意味 + voice 訳）→ Pass 2（脱翻訳調 self-edit）→ QA（back-translation spot-check: JA→EN に戻し drift 比較）→ 出典持ち越し。
- **エスケープハッチ**: 超長文のみ、継承 Opus のサブエージェントを skill 内オプションモードとして許可。起動時は voice sample + term 表 + localization policy を**明示的に手渡す**（handoff の lossy を補償）。デフォルトにしない・常駐 agent 化しない。機械的前処理（term 抽出・保護スパン検出・一貫性 grep）は Sonnet 委譲可、ただし最終 prose はメインループ。
- **Review（翻訳後）**: 新規 reviewer agent は作らない。back-translation QA を主とし、必要なら既存 `editor` / `essay-reviewer` を JA 出力にかける。
- **出力**: 別ファイル（原文非上書き）。命名は対象 repo 規約に従う。

**Portability**: 本文に個人 repo URL・特定プロジェクトパスを埋めない（skills.md Portability）。

### 変更ファイル
- 新規: `skills/en-to-ja-translation/SKILL.md`
- 参照（改変せず鏡像元）: `skills/ja-to-en-translation/SKILL.md`
- defer 先（既存・改変なし）: `skills/writing-ecosystem/SKILL.md`

## Part 2: adr-writer の意味権限リーク修正（refactor + ADR）

**原則（Codex 収束）**: writer-agent は「凍結された decision packet → 6-section テンプレートへの rendering」専任。**意味権限（context/rationale/rejected alternatives/consequences を推論・創作する権限）はメインループが保持**し、agent 起動前に packet を組み立て承認する。

**確定した disposition（grill back で再確認）**: adr-writer は **rendering agent として残す**（skill-only には崩さない）。理由: ADR は decide（synthesis, 高権限）と render（ハウススタイルへの清書, 低権限・検証可能）にきれいに割れ、後者だけを委譲するのは安全。隔離の実利（近隣 ADR 走査 + テンプレ機械処理 = observation）も残る。翻訳と違い、ADR の render は固定ハウススタイルを狙うため非収束な著者 voice の問題が起きない。よって最小変更（`:119` のリーク除去 + packet discipline 明文化）に留める。

### 変更ファイル
- `agents/adr-writer.md`:
  - `:119` の「consequence を logically entailed なら膨らませてよい」を撤回。供給された consequence の言い換えのみ許可、推論での追加は禁止に統一（`:15`「Never invent」と一貫させる）。
  - origin は shimo4228（自作）なので `-customized` サフィックス不要。frontmatter の description に「rendering only／supplied input のみ」を明確化。
- `skills/adr-writer/SKILL.md`（orchestrator 側）:
  - agent 起動前に「メインループが decision packet（Context / Decision / Alternatives+reject 理由 / Consequences）を確定・承認する」規律を明文化。起動後にメインループが fidelity check を行う。
- 新規 ADR `docs/adr/0016-writer-agents-render-not-decide.md`:
  - ADR-0010 の "agent = subjective body generation" 境界を **semantic-authority 基準** で ref定義（observation/transformation は委譲可、semantic commitment はメインループ）。ADR-0010 に本 ADR への参照追記（両面更新）。
  - `adr-writer` skill 経由で採番（collision 回避）。

## チェーンと並列化

```
種別: Part1 = feat（skill 新設） / Part2 = refactor + docs（agent + ADR）
Phase 0 External Research: 不要（既存 sibling skill が foundation。翻訳方法論は自己完結の内部設計）
Parallel Group（実装後・同一 diff 対象）: [code-reviewer, codex-review]
  - Python 変更なし（.md のみ）→ python-reviewer は非該当、code-reviewer が担当
  - security-reviewer: 非該当（入力処理・認証・秘匿・permission・hook を触らない）
Sequential: 実装 → 上記レビュー並列 → Verify
```

## Verify（コミット前）

1. **YAML 妥当性**: 新規 `en-to-ja-translation/SKILL.md` と改変 `adr-writer.md` の frontmatter を検証（description の `: ` 破壊チェック）。
2. **origin メタデータ**: 新規 skill に `origin: shimo4228` 付与を確認。
3. **skill triggering 確認**: skill-creator の eval で EN→JA タスク文が新 skill を発火するか点検（自発トリガー上限 ~40% を踏まえ user-invocable も担保）。
4. **リンク健全性**: 新 ADR-0016 ↔ ADR-0010 の相互参照、SKILL.md 内 defer 先パスが実在するか grep。
5. **doc sync**: ADR 新設 → ADR index 更新を同一 diff に含める（planning.md Doc Sync）。
6. **git status**: `daemon.lock` / `skills/herdr/` 等の無関係ファイルを混入させない。

全 PASS でのみコミット。FAIL は停止して報告。

## 人間介入点（2 点）

1. Plan 確認（本ファイル） ← 現在地
2. Verify 結果確認（コミット直前）

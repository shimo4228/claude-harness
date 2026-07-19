---
name: en-to-ja-translation
description: 英語→日本語の voice 保持翻訳スキル。エッセイ・研究ドキュメント・README・ADR 等の人間向け prose を、著者の声・register・発見調を保ったまま自然な日本語にする。逐語訳でも MT でもなく、term-lock（訳す-by-default／英語保持は明示例外）+ 脱翻訳調 pass +（EN→JA→EN の）back-translation QA で「英語のまま読みづらい」「専門用語が英語のまま」を潰す。英語記事を日本語にする EN→JA 翻訳タスクで使う。AI 向け doc は llms-txt-writer、学術 citation format は citation-formatter、日本語 AI-slop / Voice 規約は writing-ecosystem に defer。
user-invocable: true
origin: shimo4228
---

# en-to-ja-translation — 英語→日本語 voice 保持翻訳

英語の人間向け prose を、**著者の声を保ったまま**自然な日本語に訳すためのスキル。直訳でも DeepL 等の MT でもなく、LLM + voice ルーブリックで訳す（MT は register / 発見調 / 修辞を保てず、専門用語を英語のまま残しがち）。

姉妹スキル `ja-to-en-translation` の鏡像。**専用エージェントは作らない** — 翻訳本体はメインループ（最上位モデル）が本方法論に従って実行する。理由は [ADR-0016](../../docs/adr/0016-writer-agents-render-not-decide.md): 翻訳の変換ステップは非収束な著者 voice を狙うため意味的権限が高く、サブエージェントへの lossy handoff（会話文脈・声の制約の喪失）で品質が落ちる。

## Scope

- **対象**: EN→JA のみ。essay / opinion / research doc / README / ADR / glossary 等、人間向け prose。
- **対象外**:
  - JA→EN（逆方向）→ `ja-to-en-translation`
  - AI 向け doc（`llms.txt` / `llms-full.txt` / FAQ）→ `llms-txt-writer`
  - 学術 citation / reference list の format 検証 → `citation-formatter`
- **defer**: 日本語の AI-slop 禁止リスト・Voice 規約・Title 規約・出典編入（Citation & Sources Workflow）は `~/.claude/skills/writing-ecosystem/SKILL.md` を正本とする。本 skill では再掲せず、EN→JA 固有の脱翻訳調ルールと term policy のみ持つ。

## 絶対ルール（そのまま保持するもの）

- コードブロック（```）・インラインコード（`backtick`）は翻訳しない
- Markdown 構文（#, -, |, [], ![]）・画像パス・URL・DOI はそのまま保持
- frontmatter は title のみ訳す（他はそのまま）
- term-lock 表の `keep-EN` 項目はそのまま（下記 term policy 参照）

## Methodology — 5 ステップ

### 1. Pre-pass: term-lock と voice fingerprint

翻訳前に2つの表を作る。

**term-lock（不満の本丸① — 専門用語が英語のまま問題を潰す）**:

既定は「**訳す**」。英語保持は**明示例外のみ**。表で語ごとに方針を固定し、翻訳後に grep で一貫性を検証する。

| 種別 | 例 | 方針 |
|---|---|---|
| 定着した訳語がある術語 | dependency injection → 依存性注入 / idempotent → 冪等 | **訳す**。初出は日本語優先形 `依存性注入（dependency injection）`、以降は日本語 |
| 訳語が未定着・訳すと不明瞭な術語 | idempotency key / eventual consistency | 日本語 + 初出 gloss、または `結果整合性（eventual consistency）`。訳が流通していなければ原語併記を残す |
| 製品名・固有名詞・コード識別子 | PostgreSQL / `useState` / OAuth | **keep-EN**（訳さない） |
| 頭字語・記号 | API / URL / HTTP / JSON | **keep-EN**（ASCII のまま）。日本語文中で慣習的に ASCII で書かれる |
| カタカナが定着した動詞・名詞 | commit → コミット / merge → マージ / deploy → デプロイ | **カタカナ転写**。ASCII のまま残さない（残すこと自体が翻訳調）。頭字語と混同しない |
| 著者造語 | moral crumple zone | 初出で訳 + 原語併記して定義。以降は訳語で固定 |

判断基準: 「日本語の技術ライターがこの語をこの文脈で英語のまま書くか？」書くなら keep-EN、書かない（訳す／原語併記する）なら訳す。**"deterministic 優先" の惰性で全部 keep-EN にしない** — それが「英語のまま読みづらい」の主因。

**voice fingerprint（著者の声を日本語に写す指標）**:

- register: essayistic だが corporate でない英語 → だ/である調の、硬すぎない発見調の日本語。翻訳調の「〜することができる」「〜と言えるだろう」の乱発を避ける
- 発見調: "I suspect" / "it may be that" / 修辞疑問 → 「〜ではないか」「〜のように見える」。**断定に倒さない**
- 文長リズム: 短い断定文の連打は日本語でも短文で写す。英語の長い複文を「〜であり、〜だが、〜という」で1文に潰さない
- 修辞疑問: 原文の問いは日本語でも問いで残す（結論を叩きつけない）
- 未解決の正直さ: "still unclear" は smooth に解決させず「まだわからない」と正直に訳す

### 2. Pass 1 — 意味 + voice 訳

逐語でなく、日本語として自然に。段落・見出し構造は保つ。発見調・修辞疑問・未解決の正直さを保持。英語圏固有の参照（文化・法制度・慣用）は必要なら短い訳注を添える。

### 3. Pass 2 — 脱翻訳調 self-edit（不満の本丸②）

**「日本語の技術ライターは本当にこう書くか？」** を各段落に問う。以下の翻訳調シグナルを潰す:

- **英語語順の残存**: 主語の過剰な明示（"it" / "we" の逐語訳）、後置修飾の直訳。日本語の語順・省略に直す
- **冗長な受動態**: "is used by" の逐語受動。能動・自動詞に倒せないか
- **カタカナ乱用**: 定着訳があるのにカタカナで済ませていないか（"robust" → ロバスト より「堅牢」等）
- **「の」連鎖**: "X of Y of Z" の直訳「ZのYのX」。語順・複合語に再構成
- **直訳された idiom / 定型句**: "at the end of the day" 等を字義訳していないか
- **接続の機械訳**: "Moreover" → 「さらに」の惰性連発。日本語の論理接続に合わせる

writing-ecosystem の日本語 Voice 規約・AI-slop リストで自己添削。著者の既存日本語 prose があればそれにキャリブレートする。

### 4. QA — back-translation spot-check

鍵段落（lede・主張の核・結論）を 2–3 箇所選び、JA→EN に戻して原文と意味の drift を比較する。term-lock の一貫性も grep で確認（訳語がぶれていないか、keep-EN 語が誤って訳されていないか）。drift があれば Pass 1 に戻す。

**注意**: back-translation は**意味の drift** は捕まえるが **voice/自然さの drift は捕まえない**。翻訳調の残存は step 3 の脱翻訳調 pass が担う。両方を回す。

### 5. 出典の持ち越し

原文に出典セクションがあれば、**URL / DOI は保持**し description のみ和訳する。編入のポリシーは writing-ecosystem の **Citation & Sources Workflow** に従う。

## エスケープハッチ — 超長文の隔離モード（オプション）

超長文で、原文＋出力がメイン context を圧迫する場合のみ、Pass 1（意味 + voice 訳）の**ドラフト生成**を継承モデルのサブエージェントに隔離してよい（デフォルトにしない・常駐 agent 化しない）。lossy handoff を補償するため、起動時に以下を**明示的に手渡す**:

- voice sample（著者の既存日本語 prose の抜粋）
- 確定済み term-lock 表
- localization policy（訳す-by-default / keep-EN 例外リスト / 脱翻訳調チェック項目）

**所有権を明確にする**: サブエージェントの出力は**ドラフト扱い**で、確定訳ではない。メインループが必ず (a) 脱翻訳調 pass（step 3） (b) back-translation QA（step 4） (c) 最終承認 を行い、**最終的な voice の確定と semantic commitment はメインループが握る**（[ADR-0016](../../docs/adr/0016-writer-agents-render-not-decide.md)）。この finalization を省いてサブエージェント出力をそのまま確定訳にしてはならない（ADR 違反）。

機械的前処理（term 候補の抽出・保護スパン検出・訳語一貫性 grep）は、ドラフト生成とは別に軽量モデルへ委譲してよい。

## Review（翻訳後）

JA 出力を既存の review agent にかける（**新規 reviewer agent は作らない**）:

- idea / opinion essay → `essay-reviewer`（日本語で論理・voice・過積載）
- tech 記事 → `editor`（日本語で構造・コード・AI slop・用語）

原文との fidelity は step 4 の back-translation spot-check が担う。

## 出力

- 翻訳は**別ファイル**に出す（原文を上書きしない）。命名は対象 repo の規約に従う（例: EN 正本 + `*.ja.md`）。
- venue 固有規約は project overlay（`<project>/.claude/rules/*.md`）に置き、本 skill には入れない。

## Related

- `ja-to-en-translation` skill — 逆方向（JA→EN）。本 skill の鏡像元
- `writing-ecosystem` skill — 日本語 AI-slop / Voice 規約の正本（本 skill が defer する先）
- `essay-reviewer` / `editor` agent — 翻訳後の JA review
- `citation-formatter` agent — 学術 citation の format 検証（本 skill の対象外）
- `llms-txt-writer` skill — AI 向け doc（本 skill の対象外）
- [ADR-0016](../../docs/adr/0016-writer-agents-render-not-decide.md) — writer-agent は render 専任・翻訳はメインループ、の設計根拠

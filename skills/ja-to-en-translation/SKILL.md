---
name: ja-to-en-translation
description: 日本語→英語の voice 保持翻訳スキル。エッセイ・研究ドキュメント・README・ADR 等の人間向け prose を、著者の声・register・発見調を保ったまま自然な英語にする。逐語訳でも MT でもなく、term-lock + 2-pass（訳→自己添削）+ back-translation QA で品質を担保する。日本語記事を英語にする JA→EN 翻訳タスクで使う。AI 向け doc は llms-txt-writer、学術 citation format は citation-formatter、英語 AI-slop / Voice / Title 規約と出典編入は writing-ecosystem に defer。
user-invocable: true
origin: shimo4228
---

# ja-to-en-translation — 日本語→英語 voice 保持翻訳

日本語の人間向け prose を、**著者の声を保ったまま**自然な英語に訳すためのスキル。直訳でも DeepL 等の MT でもなく、LLM + voice ルーブリックで訳す（MT は register / 発見調 / 修辞を保てない）。

## Scope

- **対象**: JA→EN のみ。essay / opinion / research doc / README / ADR / glossary 等、人間向け prose。
- **対象外**:
  - EN→JA（逆方向。必要なら別の sibling skill）
  - AI 向け doc（`llms.txt` / `llms-full.txt` / FAQ）→ `llms-txt-writer`
  - 学術 citation / reference list の format 検証 → `citation-formatter`
- **defer**: 英語の AI-slop 禁止リスト・Voice 規約・Title 規約・出典編入（Citation & Sources Workflow）は `~/.claude/skills/writing-ecosystem/SKILL.md` を正本とする。本 skill では再掲しない。

## 絶対ルール（そのまま保持するもの）

- コードブロック（```）・インラインコード（`backtick`）は翻訳しない
- Markdown 構文（#, -, |, [], ![]）・画像パス・URL・DOI はそのまま保持
- frontmatter は title のみ訳す（他はそのまま）
- term-lock 表の `never_translate` 項目はそのまま

## Methodology — 5 ステップ

### 1. Pre-pass: term-lock と voice fingerprint

翻訳前に2つの表を作る。

**term-lock**（訳語を固定する語）:

| 種別 | 例 | 方針 |
|---|---|---|
| 造語・術語 | minimum disclosure set / moral crumple zone | 既存の英語術語があればそれを使う。著者造語は初出で定義 |
| 固有名詞 | 水俣病 → Minamata disease | 定訳。初出に短い gloss |
| 日本固有語 | 三権分立 / チッソ | 英語読者に通じる訳 + 必要なら短い gloss |

**voice fingerprint**（著者の声を英語に写す指標）:

- register: だ/である調 → essayistic だが corporate でない英語。硬くしすぎない
- 発見調: 「〜のではないか」→ "I suspect" / "it may be that" / 修辞疑問。「〜に見える」→ "seems" / "reads as"。**断定に倒さない**
- 文長リズム: 短い断定文の連打は英語でも短文で写す
- 修辞疑問: 原文の問いは英語でも問いで残す（結論を叩きつけない）
- 未解決の正直さ: 「まだわからない」は smooth に解決させず正直に訳す

### 2. Pass 1 — 意味 + voice 訳

逐語でなく、英語として自然に。段落・見出し構造は保つ。発見調・修辞疑問・未解決の正直さを保持。日本固有参照は inline gloss か軽い訳注を添える（例: Minamata, Japan's 1950s industrial mercury-poisoning disaster）。

### 3. Pass 2 — self-edit

writing-ecosystem の English AI-slop list（powerful tool / leverage / robust / "In today's rapidly evolving landscape" / Moreover 等）と Voice 規約で自己添削。corporate 調・宣言調に倒れていないか、発見調が保てているかを確認。日本語の謙遜・婉曲表現は、英語エッセイ/技術文の慣習に合わせて調整する。

### 4. QA — back-translation spot-check

鍵段落（lede・主張の核・結論）を 2–3 箇所選び、EN→JA に戻して原文と意味の drift を比較する。term-lock の一貫性も grep で確認。drift があれば Pass 1 に戻す。

### 5. 出典の持ち越し

原文に出典セクションがあれば、**URL / DOI は保持**し description のみ英訳する。編入のポリシーは writing-ecosystem の **Citation & Sources Workflow** に従う。

## Review（翻訳後）

EN 出力を既存の review agent にかける（**新規 reviewer agent は作らない**）:

- idea / opinion essay → `essay-reviewer`（英語で論理・voice・過積載）
- tech 記事 → `editor`（英語で構造・コード・AI slop・用語）

原文との fidelity は step 4 の back-translation spot-check が担う。

## 出力

- 翻訳は**別ファイル**に出す（原文を上書きしない）。命名は対象 repo の規約に従う（例: AAP は EN 正本 + `*.ja.md`、Substack draft は `*.en.md`）。
- venue 固有規約（dev.to のタグ・frontmatter、Substack の体裁等）は project overlay（`<project>/.claude/rules/*.md`）に置き、本 skill には入れない。

## Related

- `writing-ecosystem` skill — 英語 AI-slop / Voice / Title / 出典編入の正本（本 skill が defer する先）
- `essay-reviewer` / `editor` agent — 翻訳後の EN review
- `citation-formatter` agent — 学術 citation の format 検証（本 skill の対象外）
- `llms-txt-writer` skill — AI 向け doc（本 skill の対象外）

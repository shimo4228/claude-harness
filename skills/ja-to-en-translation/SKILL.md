---
name: ja-to-en-translation
description: 日本語⇄英語の voice 保持翻訳スキル（**両方向**）。エッセイ・研究ドキュメント・README・ADR 等の人間向け prose を、著者の声・register・発見調を保ったまま自然な訳文にする。逐語訳でも MT でもなく、term-lock + 2-pass（訳→自己添削）+ back-translation QA で品質を担保する。JA→EN は英語 AI-slop の自己添削、EN→JA は訳す-by-default の term policy と脱翻訳調 pass（英語語順残存・冗長受動態・カタカナ乱用・「の」連鎖・直訳 idiom・接続の機械訳）を追加で適用する。日本語記事を英語にするとき、英語記事・EN 正本 README を日本語にするときに使う。AI 向け doc は llms-txt-writer、学術 citation format は citation-formatter、AI-slop / Voice / Title 規約と出典編入は writing-ecosystem、出力先の語尾はチャンネル表に defer。
user-invocable: true
origin: shimo4228
---

# ja-to-en-translation — 日本語⇄英語 voice 保持翻訳（両方向）

日本語の人間向け prose を、**著者の声を保ったまま**自然な英語に訳すためのスキル。直訳でも DeepL 等の MT でもなく、LLM + voice ルーブリックで訳す（MT は register / 発見調 / 修辞を保てない）。

**voice 非収束な prose の翻訳本体は、メインループ（最上位モデル）が本方法論に従って実行する。**
理由は [ADR-0016](../../docs/adr/0016-writer-agents-render-not-decide.md): 翻訳の変換ステップは
非収束な著者 voice を狙うため意味的権限が高く、サブエージェントへの lossy handoff（会話文脈・
声の制約の喪失）で品質が落ちる。これは両方向に等しく効く。

**定型 pipeline の venue 翻訳はこの限りではない**（2026-08-23 追記）。用語集・タグ規約・投稿までを
一体で回すクロスポスト（例: zenn-content の `devto-translator`）は project agent が担ってよい。
その場合も**訳出の方法論は本 skill が正本**で、agent は起動時に本 skill を先に読む。

## Scope

- **対象**: **JA→EN と EN→JA の両方向**。essay / opinion / research doc / README / ADR / glossary 等、人間向け prose。
  共通骨格（絶対ルール・5 ステップ・QA・Review）は方向に依らず同じで、方向固有の判断だけを
  下の「EN→JA 方向の追加規約」が持つ（2026-08-23 に姉妹 skill `en-to-ja-translation` を統合 —
  本文の約 55% が同一で、骨格の片方だけが育つ drift が始まっていた）。
- **対象外**:
  - AI 向け doc（`llms.txt` / `llms-full.txt` / FAQ）→ `llms-txt-writer`
  - 学術 citation / reference list の format 検証 → `citation-formatter`
- **defer**: 英語の AI-slop 禁止リスト・Voice 規約・Title 規約・出典編入（Citation & Sources Workflow）は `~/.claude/skills/writing-ecosystem/SKILL.md` を正本とする。本 skill では再掲しない。
- **defer**: 出力先チャンネルの**語尾（文体）の実値**も本 skill は持たない。その project のチャンネル表（zenn-content では `.claude/rules/zenn-writing.md`「チャンネル表」）を正本として引く — 語尾を持つファイルが増えるほど、片方だけ更新されて分岐する

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

- register: **原文の語尾は前提にしない** — 原稿の出力元チャンネルを、その project の
  チャンネル表（zenn-content なら `.claude/rules/zenn-writing.md`）で引いてから訳す。
  規約のある日本語チャンネルは ですます（だ/である は規約のない場だけ）。どちらであっても
  英語側の狙いは essayistic だが corporate でない register で、硬くしすぎない
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

## EN→JA 方向の追加規約（2026-08-23 統合）

上の 5 ステップをそのまま使い、以下だけを差し替える。共通部分は再掲しない。

### term-lock は「訳す-by-default」

既定は**訳す**。英語保持は**明示例外のみ**。

| 種別 | 例 | 方針 |
|---|---|---|
| 定着した訳語がある術語 | dependency injection → 依存性注入 / idempotent → 冪等 | **訳す**。初出は `依存性注入（dependency injection）`、以降は日本語 |
| 訳語が未定着・訳すと不明瞭な術語 | idempotency key / eventual consistency | 日本語 + 初出 gloss、または `結果整合性（eventual consistency）` |
| 製品名・固有名詞・コード識別子 | PostgreSQL / `useState` / OAuth | **keep-EN** |
| 頭字語・記号 | API / URL / HTTP / JSON | **keep-EN**（ASCII のまま） |
| カタカナが定着した動詞・名詞 | commit → コミット / merge → マージ / deploy → デプロイ | **カタカナ転写**。ASCII のまま残さない（残すこと自体が翻訳調）。頭字語と混同しない |
| 著者造語 | moral crumple zone | 初出で訳 + 原語併記して定義。以降は訳語で固定 |

判断基準:「日本語の技術ライターがこの語をこの文脈で英語のまま書くか？」書くなら keep-EN、
書かないなら訳す。**"deterministic 優先" の惰性で全部 keep-EN にしない** — それが
「英語のまま読みづらい」の主因。

### Pass 2 は「脱翻訳調 self-edit」に差し替える

**「日本語の技術ライターは本当にこう書くか？」** を各段落に問い、以下 6 つの翻訳調シグナルを潰す
（**JA→EN 方向に対応物が無い、方向固有の判断**）:

- **英語語順の残存** — 主語の過剰な明示（"it" / "we" の逐語訳）、後置修飾の直訳
- **冗長な受動態** — "is used by" の逐語受動。能動・自動詞に倒せないか
- **カタカナ乱用** — 定着訳があるのにカタカナで済ませていないか（"robust" → ロバスト より「堅牢」）
- **「の」連鎖** — "X of Y of Z" の直訳「ZのYのX」。語順・複合語に再構成
- **直訳された idiom / 定型句** — "at the end of the day" 等の字義訳
- **接続の機械訳** — "Moreover" → 「さらに」の惰性連発

writing-ecosystem の日本語 Voice 規約・AI-slop リストで自己添削し、著者の既存日本語 prose が
あればそれにキャリブレートする。

### voice fingerprint の写し方

- 発見調: "I suspect" / "it may be that" / 修辞疑問 → 「〜ではないか」「〜のように見える」。**断定に倒さない**
- 文長リズム: 英語の長い複文を「〜であり、〜だが、〜という」で 1 文に潰さない
- 未解決の正直さ: "still unclear" は smooth に解決させず「まだわからない」と正直に訳す
- 語尾は上の defer に従う（チャンネル表を引く）

### QA の限界（両方向に効く）

back-translation は**意味の drift** を捕まえるが **voice / 自然さの drift は捕まえない**。
翻訳調の残存は Pass 2 が担う。**両方を回す**。

## エスケープハッチ — 超長文の隔離モード（オプション・両方向）

超長文で、原文＋出力がメイン context を圧迫する場合のみ、Pass 1（意味 + voice 訳）の
**ドラフト生成**を継承モデルのサブエージェントに隔離してよい（デフォルトにしない・
常駐 agent 化しない）。lossy handoff を補償するため、起動時に以下を**明示的に手渡す**:

- voice sample（著者の既存 prose の抜粋）
- 確定済み term-lock 表
- localization policy（term policy / 例外リスト / Pass 2 のチェック項目）

**所有権を明確にする**: サブエージェントの出力は**ドラフト扱い**で、確定訳ではない。
メインループが必ず (a) Pass 2 (b) back-translation QA (c) 最終承認 を行い、**最終的な voice の
確定と semantic commitment はメインループが握る**（[ADR-0016](../../docs/adr/0016-writer-agents-render-not-decide.md)）。
この finalization を省いてサブエージェント出力をそのまま確定訳にしてはならない（ADR 違反）。

機械的前処理（term 候補の抽出・保護スパン検出・訳語一貫性 grep）は、ドラフト生成とは別に
軽量モデルへ委譲してよい。

## Review（翻訳後）

EN 出力を既存の review agent にかける（**新規 reviewer agent は作らない**）:

- **出力先チャンネルの review agent に defer する**（記事の type では分岐しない）。どのチャンネルがどの agent かは、その project の rules のチャンネル表が正本（zenn-content では `.claude/rules/zenn-writing.md`）

原文との fidelity は step 4 の back-translation spot-check が担う。

## 出力

- 翻訳は**別ファイル**に出す（原文を上書きしない）。命名は対象 repo の規約に従う（例: AAP は EN 正本 + `*.ja.md`、Substack draft は `*.en.md`）。
- venue 固有規約（dev.to のタグ・frontmatter、Substack の体裁等）は project overlay（`<project>/.claude/rules/*.md`）に置き、本 skill には入れない。

## Related

- `writing-ecosystem` skill — 英語 AI-slop / Voice / Title / 出典編入の正本（本 skill が defer する先）
- `essay-reviewer` / `editor` agent — 翻訳後の EN review
- `citation-formatter` agent — 学術 citation の format 検証（本 skill の対象外）
- `llms-txt-writer` skill — AI 向け doc（本 skill の対象外）
- [ADR-0016](../../docs/adr/0016-writer-agents-render-not-decide.md) — writer agent は render 専任・翻訳は skill-only（メインループ実行、専用エージェントを作らない）の設計根拠。本 skill はその適用先

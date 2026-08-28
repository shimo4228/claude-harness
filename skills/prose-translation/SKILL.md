---
name: prose-translation
description: 日本語⇄英語の voice 保持翻訳スキル（**両方向**）。エッセイ・記事・README・ADR 等の人間向け prose を、出力先の publication channel contract が宣言する register と原文の確度を保って自然に訳す。逐語訳でも MT でもなく、term-lock + 2-pass（訳→自己添削）+ back-translation QA で品質を担保する。JA→EN は英語 AI-slop の自己添削、EN→JA は訳す-by-default の term policy と脱翻訳調 passを追加する。AI 向け doc は llms-txt-writer、学術 citation format は citation-formatter、shared craft は writing-ecosystemへ defer。
user-invocable: true
origin: shimo4228
---

# prose-translation — 日本語⇄英語 voice 保持翻訳（両方向）

人間向け prose を、**著者の声と出力先channelのregisterを保ったまま**自然に訳すためのスキル。

**voice 非収束な prose の翻訳本体は、メインループ（最上位モデル）が本方法論に従って実行する。**
サブエージェントへの handoff は会話文脈と voice 制約を落とす。

**定型 pipeline の venue 翻訳はこの限りではない**。用語集・タグ規約を使う宛先稿の準備は
project agent が担ってよい。その場合も**訳出の方法論は本 skill が正本**で、agent は起動時に
本 skill を先に読む。agent は準備で停止し、投稿は宛先稿自身のgate / 著者GO後にproject publisherが行う。

## Scope

- **対象**: **JA→EN と EN→JA の両方向**。essay / opinion / research doc / README / ADR / glossary 等、人間向け prose。
  共通骨格（絶対ルール・5 ステップ・QA・Review）は方向に依らず同じで、方向固有の判断だけを
  下の「EN→JA 方向の追加規約」が持つ。
- **対象外**:
  - AI 向け doc（`llms.txt` / `llms-full.txt` / FAQ）→ `llms-txt-writer`
  - 学術 citation / reference list の format 検証 → `citation-formatter`
- **defer**: AI-slop原則・Title規約・出典編入は`writing-ecosystem`、言語別slop診断は同skillの
  `references/style-diagnostics.md`を正本とする。
- **defer**: 出力先channelのvoice / register / 語尾の実値は、そのprojectのpublication channel contractを正本として引く。

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

- register: 原文の語尾を機械転写せず、出力先のpublication channel contractを引く。
- stance: 原文とtarget contractが発見調なら推論・修辞疑問を保持し、実用の直接指示ならhedgeへ弱めない。
- 文長リズム: 短い断定文の連打は英語でも短文で写す
- 修辞疑問: 原文の問いは英語でも問いで残す（結論を叩きつけない）
- 未解決の正直さ: 「まだわからない」は smooth に解決させず正直に訳す

### 2. Pass 1 — 意味 + voice 訳

逐語でなく、出力言語として自然にする。段落・見出し構造、原文の確度、target contractのvoiceを保つ。
日本固有参照はinline glossか軽い訳注を添える。

### 3. Pass 2 — self-edit

writing-ecosystemのAI-slop原則と、兆候がある場合のstyle diagnosticsで自己添削する。target contractの
direct / discoveryその他のvoiceを保ち、日本語の謙遜・婉曲表現は英語圏の該当channel慣習に合わせる。

### 4. QA — back-translation spot-check

鍵段落（lede・主張の核・結論）を 2–3 箇所選び、EN→JA に戻して原文と意味の drift を比較する。term-lock の一貫性も grep で確認。drift があれば Pass 1 に戻す。

### 5. 出典の持ち越し

原文に出典セクションがあれば、**URL / DOI は保持**し description のみ英訳する。編入のポリシーは writing-ecosystem の **Citation & Sources Workflow** に従う。

## EN→JA 方向の追加規約

上の 5 ステップをそのまま使い、以下だけを差し替える。

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

**「日本語の技術ライターは本当にこう書くか？」** を各段落に問い、以下 6 つの翻訳調シグナルを潰す:

- **英語語順の残存** — 主語の過剰な明示（"it" / "we" の逐語訳）、後置修飾の直訳
- **冗長な受動態** — "is used by" の逐語受動。能動・自動詞に倒せないか
- **カタカナ乱用** — 定着訳があるのにカタカナで済ませていないか（"robust" → ロバスト より「堅牢」）
- **「の」連鎖** — "X of Y of Z" の直訳「ZのYのX」。語順・複合語に再構成
- **直訳された idiom / 定型句** — "at the end of the day" 等の字義訳
- **接続の機械訳** — "Moreover" → 「さらに」の惰性連発

writing-ecosystemのAI-slop原則とtarget contractのvoiceで自己添削し、著者の既存日本語 prose が
あればそれにキャリブレートする。

### voice fingerprint の写し方

- stance: 原文とtarget contractが発見調なら推論・修辞疑問を保持し、direct voiceなら不要な弱化をしない
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
メインループが必ず (a) Pass 2 (b) back-translation QA (c) 最終承認 を行う。

機械的前処理（term 候補の抽出・保護スパン検出・訳語一貫性 grep）は、ドラフト生成とは別に
軽量モデルへ委譲してよい。

## Review（翻訳後）

訳文を既存の review agent にかける（**新規 reviewer agent は作らない**）。
**出力言語で分岐する**:

- **JA→EN（EN 出力）** — 出力先チャンネルの review agent に defer する（記事の type では
  分岐しない）。どのチャンネルがどの agent かは、その project の rules のチャンネル表が正本
- **EN→JA（JA 出力）** — 同じチャンネル表を JA 側の行で引く。README を訳したなら
  `readme-reviewer` + `readme-clarity-reviewer`（後者は日本語版も対象）、記事なら
  `editor` / `essay-reviewer`。チャンネル表に JA 行が無い出力先なら、脱翻訳調 pass の
  自己添削を 1 周増やして著者通読で閉じる

原文との fidelity は step 4 の back-translation spot-check が担う。

## 出力

- 翻訳は**別ファイル**に出す（原文を上書きしない）。命名は対象repoの規約に従う。
- venue固有規約（tags、frontmatter、投稿体裁等）はproject overlay（`<project>/.claude/rules/*.md`）に置き、本skillには入れない。

## Related

- `writing-ecosystem` skill — shared AI-slop / Title / 出典編入の正本（本 skill が defer する先）
- `essay-reviewer` / `editor` agent — 翻訳後の EN review
- `citation-formatter` agent — 学術 citation の format 検証（本 skill の対象外）
- `llms-txt-writer` skill — AI 向け doc（本 skill の対象外）

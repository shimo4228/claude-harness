---
name: wiki-query
description: Obsidian Vault の LLM wiki (wiki/concept/) に問い合わせ、[[ ]] 出典付きで合成回答する read-only クエリ。vault セッションだけでなく研究 repo (AKC / AAP / contemplative / authorship 等) のセッションからも呼べる。Use when the user invokes /wiki-query <問い>, asks 「wiki に聞いて」「wiki ではどうなってる？」, or when working in a research repo and a synthesized understanding of past daily-research notes would answer the question faster than grep. NOT for wiki への書き込み・ingest・lint (それらは vault セッション専用の /ingest・/lint-wiki)。
user-invocable: true
origin: shimo4228
---

# wiki-query — LLM wiki への出典付き問い合わせ

Obsidian Vault 内の LLM wiki に問い合わせ、**出典 `[[ ]]` を明記した合成回答**を返す。

> パターンの出自: wiki の運用モデル（LLM がメンテする markdown wiki、人間は curation と問いに集中）は Andrej Karpathy の「LLM Wiki」構想に由来する。この skill ファイル自体（query 手順・vault 固定・read-only 制約）は shimo4228 の実装。

このファイルが **query 手順の正本**。vault の `CLAUDE.md` §8-query はここに defer する。

## Vault パス（固定）

```
VAULT="/Users/shimomoto_tatsuya/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault"
```

- 概念ページ: `$VAULT/wiki/concept/<概念名>.md`
- インデックス: `$VAULT/wiki/index.md`
- 構造グラフ: `$VAULT/wiki/graph.jsonld`（symlink → `~/MyAI_Lab/daily-research/graph.jsonld`）
- 原資料: `$VAULT/daily-research/`, `$VAULT/archive/`

## 制約（CRITICAL）

- **read-only**。この skill から vault 内のいかなるファイルにも書き込まない。wiki の更新（ingest / index 再生成 / log 追記）は vault セッションの `/ingest` の領域。
- iCloud dataless プレースホルダに注意: 読んだファイルの本文が空なら未ダウンロードの可能性。その旨を報告する。

## 手順

1. `$VAULT/wiki/index.md` を Read し、問いに関連しそうな concept ページを特定する。
2. 該当 concept ページを Read する（複数可）。必要なら「言及ソース」節が指す `daily-research/` ノートまで遡って Read する。
3. **構造的な問い**（このクラスタに属する記事は？クラスタ間の関係は？）には `wiki/graph.jsonld` を、**合成された理解**には concept ページを使い、相互補完する。
4. **出典（`[[ ]]`）を明記して**合成回答する。claim ごとに、どの concept ページ / daily-research ノート由来かが追えること。
5. wiki に該当が無ければ「未 ingest」と明言し、vault セッションで `/ingest` することを提案する（このセッションで ingest を代行しない）。

## 研究 repo からの利用

研究 repo（wiki↔repo 対話的還元ループの対象 repo）から呼んだ場合も手順は同一。追加の注意:

- 回答を repo の docs / ADR に取り込む際は、wiki の concept ページではなく**一次出典（daily-research ノートが引く元文献）まで遡って**引用する（wiki は二次合成であり drift しうる）。
- repo 側から wiki への書き戻しはしない（知識の流れは source → wiki → repo の一方向）。

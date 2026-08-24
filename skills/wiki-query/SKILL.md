---
name: wiki-query
description: Obsidian Vault の LLM wiki (wiki/concept/) に問い合わせ、[[ ]] 出典付きで合成回答する query。vault セッションだけでなく研究 repo (AKC / AAP / contemplative / authorship 等) のセッションからも呼べる。複数ページを横断して合成した良回答は書き戻しプロトコルで wiki/concept/ に filing する（Karpathy 原典 parity、read-write）。Use when the user invokes /wiki-query <問い>, asks 「wiki に聞いて」「wiki ではどうなってる？」, or when working in a research repo and a synthesized understanding of past daily-research notes would answer the question faster than grep. NOT for source の新規取り込み・wiki 全体の健全性チェック (それらは vault セッション専用の /ingest・/lint-wiki)。
user-invocable: true
origin: shimo4228
---

# wiki-query — LLM wiki への出典付き問い合わせ

Obsidian Vault 内の LLM wiki に問い合わせ、**出典 `[[ ]]` を明記した合成回答**を返す。
複数ページを横断して合成した良回答は wiki に書き戻す（filing）。

> パターンの出自: wiki の運用モデル（LLM がメンテする markdown wiki、人間は curation と問いに集中）と query 書き戻し（"good answers can be filed back into the wiki as new pages"）は Andrej Karpathy の「LLM Wiki」構想に由来する。この skill ファイル自体は shimo4228 の実装。2026-06-12〜2026-08-06 は read-only 運用だったが、原典 parity のため書き戻しを復活（vault CLAUDE.md §8-query と同期済み）。

このファイルが **query 手順の正本**。vault の `CLAUDE.md` §8-query はここに defer する。

## Vault パス（固定）

```
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault"
```

- 概念ページ: `$VAULT/wiki/concept/<概念名>.md`
- インデックス: `$VAULT/wiki/index.md`
- 構造グラフ: `$VAULT/wiki/graph.jsonld`（symlink → `~/MyAI_Lab/daily-research/graph.jsonld`）
- 原資料: `$VAULT/daily-research/`, `$VAULT/archive/`

## 制約（CRITICAL）

- **source 層は不変**: `daily-research/` `archive/` `99_Attachment/` には書き込まない。
- 書き込み対象は **`wiki/concept/` + `wiki/log.md` + index 再生成**のみ。source の新規取り込み（ingest）と wiki 全体の lint は vault セッション専用のまま。
- **Obsidian 起動中に vault の .md を書かない**（iCloud 同期競合）。書き戻し手順 1 のチェックを必ず通す。
- iCloud dataless プレースホルダに注意: 読んだファイルの本文が空なら未ダウンロードの可能性。その旨を報告する。

## 手順（query）

1. `$VAULT/wiki/index.md` を Read し、問いに関連しそうな concept ページを特定する。
2. 該当 concept ページを Read する（複数可）。必要なら「言及ソース」節が指す `daily-research/` ノートまで遡って Read する。
3. **構造的な問い**（このクラスタに属する記事は？クラスタ間の関係は？）には `wiki/graph.jsonld` を、**合成された理解**には concept ページを使い、相互補完する。
4. **出典（`[[ ]]`）を明記して**合成回答する。claim ごとに、どの concept ページ / daily-research ノート由来かが追えること。
5. wiki に該当が無ければ「未 ingest」と明言し、vault セッションで `/ingest` することを提案する（このセッションで ingest を代行しない）。
6. 回答が下記の filing 基準を満たすなら、書き戻しを実行する。

## 書き戻し（query filing）

### Filing 基準

filing するのは、**複数の concept ページ / ソースを横断して新しく合成された**比較・分析・概念間の接続だけ。

- 単一ページの言い換え・要約 → filing しない（既にページがある）
- wiki 外の知識だけで答えた回答 → filing しない（それは ingest の領域）
- 迷ったら filing しない — wiki の信頼性 > 網羅性（原典: 不正確な回答を wiki に残さない）

形は 2 通り: **新規 concept ページ**（合成が独立した概念単位になる場合）か、**既存ページへの統合**（既存概念の「主要な主張」「関連概念」「オープンクエスチョン」に足す場合）。

### Filing 手順

1. **Obsidian チェック**: `pgrep -x Obsidian`。起動中なら graceful 終了（`osascript -e 'quit app "Obsidian"'` → 数秒待って再確認）。終了できなければ **filing を skip し、その旨と filing 候補の内容を報告**する（回答自体は返してよい）。
2. **名寄せ**: `wiki/index.md` と `$VAULT/scripts/tag_consolidate.py` の `TAG_MERGE_MAP` を確認し、新規ページか既存ページ統合かを決める。表記揺れ・英語名は新タグを作らず正規形 + `aliases` で吸収。
3. **新規ページ**は下記骨格で `wiki/concept/<正規概念名>.md` に作成。ファイル名 = `# 見出し` = 正規タグを一致させる。**関連概念に最低 2 リンク**を張り、相手ページの「関連概念」節にも逆リンクを追記する（孤立ページを作らない）。
4. **出典規律**: wiki 由来の claim は `[[ ]]` リンク。研究 repo 由来の claim は repo 名 + ファイルパスを素のテキストで併記する（repo へは wikilink を張れないが provenance は残す）。
5. **log 追記**: `wiki/log.md` に `## [YYYY-MM-DD] query-filing | <問い> → [[<concept>]]` を 1 行追記。
6. **index 再生成 + 検証**: `cd "$VAULT" && /opt/homebrew/bin/python3 scripts/wiki_index.py --apply && /opt/homebrew/bin/python3 scripts/wiki_lint.py`。lint がエラーを出したら自分の filing 分を修正する。

### 骨格

**正本は vault `CLAUDE.md` §5。複製を置かない** — 研究 repo セッションからは vault の
canon が自動ロードされないので写したくなるが、写した版は必ず drift する（2026-08-23 の
stocktake 時点で、この節の旧複製は `## 矛盾・論争` を落としており、それは `wiki-harvest`
Step 2 category ② が収穫する節だった。この skill 経由で filing したページが収穫面を
欠いたまま生まれていた）。filing の直前に読む:

```bash
sed -n '/^## 5\./,/^## 6\./p' "$VAULT/CLAUDE.md"
```

節構成の要点だけ（値は上のコマンドが正）: frontmatter（`category` / `type` / `status` /
`tags` / `aliases` / `topic` / `source`）→ `# 概念名` → `## 定義` → `## 主要な主張 (Key Claims)`
→ `## 関連概念` → `## オープンクエスチョン` → `## 矛盾・論争`（無ければ節ごと省略可）→
`## 言及ソース`（`wiki_index.py` が自動生成。手で編集しない）。
**ファイル名 = `# 見出し` = `tags` の正規タグ**を一致させる。

## 研究 repo からの利用

研究 repo（wiki↔repo 対話的還元ループの対象 repo）から呼んだ場合も手順は同一。追加の注意:

- 回答を repo の docs / ADR に取り込む際は、wiki の concept ページではなく**一次出典（daily-research ノートが引く元文献）まで遡って**引用する（wiki は二次合成であり drift しうる）。
- 研究 repo の文脈で合成された理解は **filing の最有力候補**（最も文脈豊富なセッションで生まれた接続を chat history に消さない）。repo 固有の実装詳細そのものは filing せず、概念レベルの合成だけを filing する。
- **repo 側に還元したいのが「1 問の答え」でなく「wiki 全体から拾える候補」なら
  `wiki-harvest`**。あちらは read-only で走査して一次出典つきのランク付き台帳を
  `.notes/` に生成する（本 skill は chat 上の自由質問 + filing で read-write）。
  filing した節は harvest の入力になる — 特に `## 矛盾・論争` は category ② として
  収穫されるので、埋めておくと後で効く。

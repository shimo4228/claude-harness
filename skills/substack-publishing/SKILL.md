---
name: substack-publishing
description: 完成・レビュー済みの human essay を Substack に公開し、LLM 発見のために corpus へミラーするワークフロー。Substack が raw Markdown 非対応なための MD→HTML rich-text paste、Title/Subtitle/body のフィールド分け、タグ戦略（archive 用 ≠ 拡散用）、カバー画像プロンプトの作り方、公開後の content repo `substack/` フォルダへのミラー + research repo からの cross-link を扱う。Voice / AI-slop / Title / 出典は writing-ecosystem、翻訳は ja-to-en-translation に defer。essay を Substack に出すとき使う。
user-invocable: true
origin: shimo4228
---

# substack-publishing — Substack 公開 + LLM corpus ミラー

レビュー済みの human essay を Substack に公開し、LLM に発見されるよう corpus へミラーするまでの手順。執筆・レビュー・翻訳は別 skill が担い、本 skill は **Substack 固有の公開機構** と **公開後のミラー / cross-link** だけを扱う。

## いつ使うか

writing-ecosystem の review（`essay-reviewer` / `fact-checker`）通過後。bilingual なら `ja-to-en-translation` の後。

## defer 先（本 skill では再掲しない）

- Voice / AI-slop / Title 規約 / 出典編入（Citation & Sources Workflow）→ `writing-ecosystem`
- JA→EN 翻訳 → `ja-to-en-translation`

## 1. Substack は raw Markdown を変換しない

エディタに Markdown を貼っても `##` や `[](url)` は literal のまま残る。経路は2つ:

- **入力時ショートカット**（短い編集向け）: `#`/`##`/`###`+space=見出し、`>`+space=引用、`---`=区切り線、`*`/`-`+space=リスト、cmd+B/I、cmd+K=リンク。**貼り付けでは変換されない**（タイプ時のみ効く）。
- **MD→HTML→リッチテキスト貼り付け**（全文向け・推奨）:

  ```
  pandoc essay.md -s -o essay.html
  ```

  ブラウザで `essay.html` を開く → 本文を選択 → コピー → Substack 本文に貼ると整形保持（見出し / 太字 / 斜体 / リンク / 区切り線）。Substack は貼り付け時に独自スタイルを当てるので、保持されるのは構造であって見た目の細部ではない。

## 2. フィールド分け（本文に重複させない）

| 原稿の要素 | Substack の置き場 |
|---|---|
| H1 タイトル | Title フィールド |
| deck / subtitle（先頭の `>` 行など） | Subtitle フィールド |
| 本文（最初の `##` 以降） | 本文エリア |

HTML を開いて貼るときは **最初のセクション見出しから**選択する（冒頭のタイトル・deck は本文に含めない）。全選択して貼ってしまったら、Substack 上で冒頭2行を Title / Subtitle 欄へ移すだけ。

## 3. タグ（= アーカイブ用、拡散用ではない）

- Substack の post タグは **discoverability ではなく、自分の publication 内のアーカイブ / 内部リンク / SEO** 用。効くのは **一貫性**（連作で同じ tag spine を使い回すとタグ別アーカイブページが育つ）。
- **拡散の本命は Notes のハッシュタグ**（post タグとは別物）+ recommendation。
- **Category は publication 単位**（記事ごとではない、実質1つ）。
- 推奨: 連作で固定する小さな tag spine（3-4個）+ 記事固有を 1-2 個。乱発するとアーカイブが散る。

## 4. カバー画像プロンプト（生成は外部 = ChatGPT 等）

essay の **core metaphor** を1つ視覚化する。プロンプト規約:

- **文字を入れない**（画像モデルは文字を崩す。タイトルは Substack のテキスト側で出す）
- **実在人物を描かない / 暴力を直接描かない**（構造を抽象化する）
- **16:9 横長**、編集イラスト / conceptual 調など essay のトーンに合わせる
- 2-3 個の concept 案を出してユーザーに選ばせる（収束図 / 二項対比図 / メタファー直写し 等）。要素が少ない案ほど画像モデルが破綻しにくい

## 5. 公開後: LLM corpus へミラー

Substack を canonical にしつつ、LLM クローラーに読ませるため content / corpus repo にミラーする。

- 置き場は **`substack/` フォルダ**（content repo 内に新設）。
  - **`drafts/` には置かない**（"下書き" 扱いで corpus 上 deprioritize されるため）
  - **その repo の記事公開フォルダ（例: Zenn の `articles/`）にも置かない**（媒体への誤公開を避ける）
  - 媒体の「下書きフラグ」frontmatter（例: Zenn `published: false`）は付けない（下書き signal を避ける）
  - **その repo の記事規約 / lint / スケジュール公開は `substack/` に適用しない**（corpus 拡張用の独立フォルダ）。この除外は content repo 側の context doc（`CLAUDE.md` 等）に明記しておく
- 原稿の出典セクションは URL / DOI を保持して持ち越す（bilingual なら両言語ミラー）。
- **research / project repo から cross-link**: その repo の lineage / related-writing 面（例: `docs/inspiration.md`）からミラー記事へリンク（GitHub blob URL 等、その repo の既存リンク方式に合わせる）。spine 本体ではなく companion / derivative として明記する。

## ワークフロー上の位置

```
draft (article-writing)
  → review (essay-reviewer / editor + fact-checker)
  → [translate (ja-to-en-translation)  ※bilingual なら]
  → 出典編入 (writing-ecosystem: Citation & Sources Workflow)
  → substack-publishing ←ここ
      ├ MD→HTML 変換 → Substack に貼る（Title / Subtitle / body 分け）
      ├ タグ spine + カバー画像プロンプト
      └ content repo の substack/ へミラー + research repo から cross-link
```

## Related

- `writing-ecosystem` skill — 執筆・レビューの orchestrator（Voice / AI-slop / Title / 出典の正本。本 skill の defer 先）
- `ja-to-en-translation` skill — bilingual 公開時の JA→EN 翻訳
- `paper-deposit` skill — 学術 paper を Zenodo / SSRN に出す姉妹ワークフロー（human essay ではなく academic 向け）

---
name: substack-publishing
description: 完成・レビュー済みの human essay を Substack に公開し、LLM 発見のために corpus へミラーするワークフロー。Substack が raw Markdown 非対応なための MD→HTML rich-text paste、Title/Subtitle/body のフィールド分け、タグ戦略（archive 用 ≠ 拡散用）、カバー画像プロンプトの作り方、Claude in Chrome によるエディタ自動操作（OS クリップボードへの HTML flavor 直接セット + cmd+V）、公開後の content repo `substack/` フォルダへのミラー + research repo からの cross-link、公開後の配信ファネル運用（Notes 3 型・organic recommendations・welcome email・ケイデンス）を扱う。Voice / AI-slop / Title / 出典は writing-ecosystem、翻訳は ja-to-en-translation に defer。essay を Substack に出すとき・Substack の配信運用を考えるときに使う。
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

## 5. ブラウザ自動化（Claude in Chrome）での投稿

エディタ操作をエージェントに任せる場合の実証済み手順（2026-07 実走で確立）。公開ゲートは維持する: **下書き構築まで自動、Publish はプレビューを人間が確認して OK した後のみ**。

### 本文投入 — OS クリップボードに HTML flavor を直接セットする

Substack エディタ（ProseMirror 系）への構造保持貼り付けは、**macOS システムクリップボードへ HTML flavor を直接書いて cmd+V** が最も確実:

```bash
pandoc -f gfm body.md -o body.html   # -f gfm 必須（下記）
hex=$(xxd -p body.html | tr -d '\n')
osascript -e "set the clipboard to «data HTML${hex}»"
# → エディタ本文をクリックして cmd+V
```

- **pandoc は `-f gfm` を指定**する。デフォルト方言は「blank line なしで段落直後に始まるリスト」を段落に潰す（GitHub 上のレンダリングと乖離する）。貼り付け後に `<ul>` の数などで構造を照合する
- **動かない経路（試行済みの落とし穴）**:
  - ページ内 JS の `navigator.clipboard.write()` → `Runtime.evaluate` がタイムアウト
  - ページ内 JS から `fetch("http://127.0.0.1:…")` → https ページからの localhost fetch は Chrome の Private Network Access に塞がれハング
  - 素の Markdown 貼り付け → §1 の通り変換されない

### 画像も同じ経路

```bash
osascript -e 'set the clipboard to (read (POSIX file "/path/cover.png") as «class PNGf»)'
# → 本文カーソル位置で cmd+V（アップロードは自動）
```

本文冒頭に挿入した画像はソーシャルプレビュー（カバー）に自動反映される。`file_upload` tool は本文画像には使いにくい（対応する `input[type=file]` が動的生成のため）。チャット添付画像はディスクに存在しないので、ユーザーにファイルとして保存してもらいセッション共有パスへコピーする。

### フィールド・タグ・公開フロー

- Title / Subtitle は座標クリック + type で直接入力
- タグは右下「設定」→ ポスト設定 → タグを追加。**1 個ずつ** type して「"x" を作成」をクリックする（type + Enter の連打はドロップダウンの遅延で取りこぼす）。設定後にチップ数を照合
- 「登録ボタンを追加」ダイアログ（公開時に出る）は widget を**カーソル位置に**挿入することがある。末尾に置きたければ挿入後に配置を確認し、ずれていたら node 選択（前の段落末尾で forward-delete 1 回目が node 選択、2 回目が削除）で移動する
- 長編はメール文字数上限の警告が出る — メール版が途中で "Read online" になるだけで Web 記事は全文。公開を妨げない

### 検証

貼り付け後、`get_page_text` で全文を取得し、原稿と (a) セクション数 (b) 末尾の一致 (c) リスト・引用の構造を照合してからプレビューへ進む。

## 6. 公開後: LLM corpus へミラー

Substack を canonical にしつつ、LLM クローラーに読ませるため content / corpus repo にミラーする。

- 置き場は **`substack/` フォルダ**（content repo 内に新設）。
  - **`drafts/` には置かない**（"下書き" 扱いで corpus 上 deprioritize されるため）
  - **その repo の記事公開フォルダ（例: Zenn の `articles/`）にも置かない**（媒体への誤公開を避ける）
  - 媒体の「下書きフラグ」frontmatter（例: Zenn `published: false`）は付けない（下書き signal を避ける）
  - **その repo の記事規約 / lint / スケジュール公開は `substack/` に適用しない**（corpus 拡張用の独立フォルダ）。この除外は content repo 側の context doc（`CLAUDE.md` 等）に明記しておく
- 原稿の出典セクションは URL / DOI を保持して持ち越す（bilingual なら両言語ミラー）。
- **research / project repo から cross-link**: その repo の lineage / related-writing 面（例: `docs/inspiration.md`）からミラー記事へリンク（GitHub blob URL 等、その repo の既存リンク方式に合わせる）。spine 本体ではなく companion / derivative として明記する。

## 7. 配信ファネル（公開後の growth 運用）

出典: Kaguura Gichuru "How I Got 20,585 Substack Subscribers in 90 Days" (The Write Path, 2026-07)。執筆 craft・構成・タイトル原則は `writing-ecosystem` に取り込み済み — ここは **Substack 固有の配信運用**のみを持つ。

### 3 つの配置

| 面 | 読者 | 役割 |
|---|---|---|
| Newsletter（長編） | 自分の購読者 | 主製品。完全無料で拡散させる（ペイウォールは viral 性を殺す） |
| Notes | For You フィードの stranger | テストラボ + トップオブファネル |
| コメント | 他の著者の読者 | より大きな audience への露出 |

### Notes 3 型（テンプレート）

短く（2 段落以下）、viral 狙いをしない。生アイデアのテスト → 反応検証 → 長編へ展開。

| 型 | ファネル位置 | 構造 |
|---|---|---|
| **Awareness** | トップ | 日常の現実への共感度の高い観察。世間の過剰複雑化への言及 → シンプルで地に足の着いた現実 → 鋭い結論（「finally someone said it」を起こす） |
| **Education** | 中段 | 確立された概念・歴史・法則を簡潔に分解。具体的な事象/フレームワーク → 教科書用語を削る → 今日の生活への応用 1-2 文 |
| **Conviction** | ボトム | ニッチへの本音 + 不快な真実。嫌いな一般的アドバイスを特定 → 不快な現実を共有 → 実質か近道かの選択を迫る。カジュアル層を意図的に撃退し、世界観の合う読者と深く繋がる |

- **1 エッセイ → 3 Notes**: 冒頭の逸話 → Awareness / 中核ルール → Education / 書きたくなった根底の信念 → Conviction
- **3 ヶ月逐語ルール**: 反応の良かった Note は数ヶ月後に同じ言葉で再投稿してよい（新規購読者には新規価値）
- **警告**: テンプレートを機械的に埋めない。固有の思考が 100% 必須（writing-ecosystem の slop 判定原則「別の場所に貼っても通じるなら slop」と同じ）

### ケイデンス

- 週 1 長編（800-2,000 語）+ 週 3-5 Notes
- 「1 傑作 → 1 ヶ月沈黙」は伸びない — プラットフォームが推すのは能動的で一貫した書き手。一貫性がフィールドに立たせ、スキルが試合に勝つ
- 100〜2,000 購読者の沈黙フェーズは戦略の故障ではない（ネットワーク効果の未発動）。フィードを 1 日 30 分のアイデア採集サンドボックスにし、浮かんだら完璧化せず即投稿する

### コメント（net-giver）

正本は `public-comment` skill（net-giver の 3 拍・空の褒め禁止・スレッド乗っ取り禁止）。Substack コメントでも同じ規約を適用する。

### Organic recommendations

- **する**: 本当に好きな publication だけを推奨する（読者は見抜く）。ラポール構築後の清潔で直接的な依頼は可
- **しない**: 推奨スワップの DM、20+ の大量推奨リスト（キュレーション価値が消える）、見返り前提の推奨

### 第一印象の整備（1 時間で終える）

- プロフィール写真: 高品質でクリーンな 1 枚。Bio: 自分は誰か・何が読めるか・なぜ読む価値があるかを曖昧にせず書く
- ヘッダー等の美観は 1 時間でセットアップし、フォント・色選びに 20 時間かけない（先延ばしの一形態）
- **Welcome email**: デフォルトテンプレートを使わない。短い暖かい手紙 + 発行ペース + 過去ベスト記事 3 本のリンク

### 無駄な時間チェックリスト（やらないこと）

- restack 交換（「share mine, I'll share yours」— 偽メトリクス。読者は気づく）
- 推奨スワップ（読者への品質約束を破る）
- 他人のコメント欄でのリンクドロップ（→ public-comment の宣伝禁止）
- 企業マーケ調に over-engineer したマルチパート Note（ロボット臭 → 空の like だけで購読者ゼロ）
- トレンド・ドラマ追い（声を毀損し、低品質読者を集める）
- 「Hi Substack, 〜な人と繋がりたい」型の物乞い投稿
- 完璧主義でドラフトを人質に取る（スキルは投稿を重ねてのみ育つ）

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

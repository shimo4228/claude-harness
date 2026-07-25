---
name: public-comment
description: "公開の技術ピア議論への返信コメントを書く skill。GitHub discussions / issues / PR コメント・Hugging Face discussions・技術フォーラムなど、初対面の技術者が読む公開スレッドへの返信を作成・改稿・投稿するときに使う。Use when the user says 「GitHub のコメントに返信して」「discussion にコメント書いて」「issue に返信」「このスレッドに参加したい」 or asks to draft/revise/post a reply in a public technical thread. 2026 年の OSS は AI slop 危機下にあり、tell（em-dash・対比構文・triad 等）は「未レビューの生ダンプ」のシグナルとして読まれる — 本 skill は content ownership・スレッド接地・脱 tell 改稿・日本語訳併記の人間 gate までを扱う。NOT for: 記事・エッセイ（→ writing-ecosystem）、AI 向け doc（→ llms-txt-writer）、既知の相手との Slack/Discord 会話、コードの PR 本体。"
user-invocable: true
origin: shimo4228
---

# public-comment — 公開技術スレッドへの返信規約

公開の技術ピア議論（GitHub discussions / issues / PR コメント、HF discussions、フォーラム）に返信するときの規約。genre を定義するのはプラットフォームではなく読者との関係: **初対面の技術者が、slop 検知器を作動させながら読む公開スレッド**。

## 前提: 2026 年の読者環境

AI 使用は OSS の前提（手でコードを書く方が珍しい）。読み手が検知しようとするのは AI ではなく「**未レビュー・非所有の生ダンプ**」であり、tell はその代理指標として機能する。tell を 1 つ出すだけで、内容が読まれる前に discount される。

したがって tell 除去の目的は偽装ではない。**人間の判断が通ったことをテキスト自体で示す**こと。effort ベースの逆圧が消えた時代（Ghostty/Hashimoto 2026-01）に、逆圧を自分のコメントに再インストールする行為。

## Content Ownership（最上位規約）

他のすべての規約に優先する:

- 自分が検証していない主張を書かない
- 自分のものでない経験を書かない
- 確認していない実装の詳細を書かない
- コメントの実質は必ずユーザー自身のもの。AI は起草を補助するが、全ての claim にユーザーの実感・実装・検証が対応していること

切実さを装わない。自分の運用で当たらない問題には「私の運用では当たらない」と書く（scope 付き同意は、全面同意より議論への貢献が大きい）。

## Disclosure

場の規範に従う:

1. 投稿前に相手コミュニティの AI ポリシーを確認する（CONTRIBUTING.md / community guidelines / discussion のピン留め）
2. 開示要求があれば従う
3. なければ開示しない（content ownership が満たされている限り、道具の開示義務はない）

## 文体規約

語彙・構造の tell リストの正本は [writing-ecosystem の AI Slop 禁止リスト + 文体・構造 tell](../writing-ecosystem/SKILL.md#ai-slop-禁止リスト) — ここに複製しない。コメント genre 固有の追加分のみ:

- **スレッドの register に合わせる**: 既存コメントの長さ・フォーマット水準を上限とする。自分の過去コメントがあるスレッドでは、その声との連続性も保つ（急な文体変化自体が不自然さの signal）
- **concede-first**: 相手の正しい点を具体的に認めてから差分を述べる
- **1 コメント 1 コア主張**: 網羅性は slop の匂い。論点が複数あるなら一番強いものに絞る
- **スレッド固有名詞への接地**: 実在のコメント・実在の争点・実在の発言を引用して書く。判定: 「このコメントは別のスレッドに貼っても通じるか？」→ Yes なら接地不足（slop 判定原則のコメント版）
- **宣伝をしない**: 自作物への言及は議論に必要な場合のみ。リンクは求められてから。DOI・repo 誘導を入れない
- **句読点置換の禁止**: em-dash を `:` / `;` に機械置換しない。「節: 補足」の等間隔リズムは記号が変わっても同じ指紋。修正は文の再構築（短文化・文長のばらつき・平文接続）で行う。コロンはリスト・定義・例示の前のみ
- **nuance 制御困難な口語を避ける**: "steal" のような、ネイティブには友好イディオムでも文脈次第で刺々しく読まれうる語は、非ネイティブとして制御しきれないので使わない

## 投稿前チェック

3 層。enumerate は機械、judge は人間（binary check の列挙、スコア化しない）:

1. **機械チェック**（binary、fail = 修正）:
   - em-dash（`—`）: 0 件
   - 絵文字: 0 件
   - bold 見出しリード: スレッド register の範囲内（目安 ≤ 2）
   - 文中コロン（リスト・例示前を除く）: 0 件
2. **意味チェック**:
   - 「It's not X, it's Y」構文・予告つき 3 点列挙・等間隔リズムが無いか
   - 別スレッドに貼っても通じるコメントになっていないか（接地不足）
   - 全 claim にユーザーの実感・検証が対応しているか（content ownership）
3. **人間 gate**（外部書き込み、承認必須）:
   - **EN コメントは必ず日本語訳を併記して提示する**（非英語話者のユーザーがニュアンスを確認できる形で）
   - ユーザーが全文を読んで承認してから投稿する。承認前に投稿コマンドを実行しない。
     ここで判断するのは文章の巧拙ではなく**これを自分の声として出すか**（コメント本文は
     公開・不可逆で、テキストが意図そのもの。`rules/common/human-gate.md`）

## 投稿手段

- GitHub discussion: `gh api graphql` の `addDiscussionComment` / `addDiscussionCommentReply` mutation
- GitHub issue / PR: `gh issue comment` / `gh pr comment`
- HF discussions / フォーラム: ブラウザ経由（ユーザー手動 or Claude in Chrome、いずれも承認後）

## Related

- 語彙・構造 tell の正本: `writing-ecosystem`（AI Slop 禁止リスト + 文体・構造 tell）
- 記事・エッセイ: `writing-ecosystem` / AI 向け doc: `llms-txt-writer`
- EN 起草時の翻訳品質: `ja-to-en-translation`（長文の場合のみ。コメントは本 skill の日本語訳併記で足りる）

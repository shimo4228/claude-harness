---
name: social-post
description: "Write X, Bluesky and Substack Notes posts and save them as Buffer drafts: an announcement of a newly published article, or a fragment the author wrote. Use when announcing an article (告知して) or sending a fragment to Buffer (Buffer に入れて). For a long X post from a daily-research report, use x-draft."
user-invocable: true
origin: shimo4228
---

# social-post — X / Bluesky / Substack Notes の投稿を Buffer の下書きにする

著者の投稿を、面ごとの制約に合わせて Buffer の下書き（draft）として入れる。予約と公開は
著者が Buffer の画面で行う。入力は 2 種類:

- **告知** — 公開した記事 1 本から、面ごとの告知文を書く
- **断片** — 著者が書いた短文を、そのまま各面に載せられる形にする

## 面の制約（as-of 2026-10-12）

| 面 | 長さ | リンク | その他 |
|---|---|---|---|
| X | 上限は手順 1 で読む channel 設定の値。本アカウントは Premium で 25,000（2026-10-12）。無料の上限は重み付き 280（日本語 1 字 = 2、URL は 23）。長文は feed で冒頭だけ見え、続きは畳まれる | 本文に置く | ハッシュタグとメディア種別に順位の加点は無い（公開コード） |
| Bluesky | 300 grapheme（URL も数える）かつ 3,000 byte。channel 設定の値も 300 | `metadata.bluesky.linkAttachment` でカードを付ける。カードは投稿側が作る | 画像は 4 枚まで、alt 必須 |
| Substack | Buffer から出るのは Notes だけ。上限 10,000 字 | `metadata.substack.linkAttachment`。カードは Substack が記事の OGP から作る | 添付は画像 6 枚・動画 1・リンク 1 のどれか 1 種。@ と # はリンクにならない |

- X のリンク位置: X の幹部が 2026-07 に「返信にリンクを置く必要はもうない」と発言した（二次報道）。小規模アカウントでどちらが効くかの実測は無い
- **X は LLM が書いたと判定された利用者に `llm_slop_user` ラベルを付け、30 日間フォロワー外へ配信しない**（公開コード）。判定方法は非公開。重複文の検知は日本語でも文字単位で動く
- Substack は 2026-07 から投稿に AI 生成の検出表示を出す。Notes が対象かは未確認
- 面ごとに書き分けると反応が増える、という実測は無い。書き分けは制約への適合と、面の文化への合わせ方（意見）として扱う

## 手順

### 1. Buffer の現況を読む

`get_account`（organizationId とタイムゾーン）、`list_channels`（面と channelId）を読む。
面ごとの文字数上限は `execute_query` で `configuration(input: {organizationId})` を引き、
`channels[].content[].rules` の `LengthRule`（`property: text` の `maxLength`）を使う。
`services[]` 側の値は契約を反映しない（X は Premium でも 280 のまま）。Substack は rule を返さないので上の表の 10,000 を使う。
各面で直近の `sent` を `list_posts` で 5 件ずつ読む。これが voice と言語の見本になる。
同時に、直近の告知の書き出しを控える。`sent` が 0 件の面は、voice を下の voice.md に合わせ、
言語を著者に 1 回聞く。

### 2. 書く

**告知**
- 記事本文を読む。zenn-content では日本語の正本が `note/<slug>.md`、Zenn 版が `articles/<slug>.md`、
  英語版が `substack/<slug>-en.md`。repo に無ければ公開 URL を読む。版が複数あるときは、
  面の言語に合う版の公開 URL を告知に使う
- 1 行目は記事の結論か、記事の中で一番具体的な事実にする。文はできるだけ記事本文から取る —
  著者の言葉になり、LLM の文型が減る。1 行目の案が要るときは skill: `headline-craft`
- 面ごとに長さを変える。Bluesky は 1〜2 文。X は上限が広くても、畳まれる前の冒頭で記事の中身が伝わる形にし、
  長さは手順 1 で読んだ直近の X 投稿に合わせる。Substack は記事の問いを数文で渡す
- 言語は、手順 1 で読んだその面の直近の投稿に合わせる
- 書き出しと文型は、手順 1 で控えた直近の告知と変える（重複の検知と slop の判定に効く）

**断片**
- 著者の文をそのまま使う。面の上限を超えたときだけ、削る箇所の案を示して著者が選ぶ
- 文が無い面（例: 長すぎて Bluesky に入らない）は、その面を外すか、著者が書き直すかを聞く

voice は `~/.claude/skills/x-draft/references/voice.md` と手順 1 の見本に合わせる。
文の原則は `~/MyAI_Lab/zenn-content/.claude/rules/writing-principles.md`、
tell の一覧は `~/MyAI_Lab/zenn-content/.claude/skills/writing-ecosystem/references/style-diagnostics.md`。

### 3. 著者に見せる

Buffer に入れる前に、面ごとの本文（コードブロック）と長さ、リンクの置き場（本文 / カード）を並べて著者に見せ、
著者の OK を待つ。著者の直しはこの段階で反映し、OK が出た文だけを次の手順で Buffer に入れる。
Buffer の `edit_post` は付けた linkAttachment を外せないので、リンクの有無もここで決めてもらう。

### 4. Buffer に下書きを入れる

面ごとに `create_post` を 1 回呼ぶ。引数は毎回この 3 つを明示する — `mode` の既定は
`addToQueue` で、`saveToDraft` を落とすと実際に予約される:

- `saveToDraft: true`
- `schedulingType: "automatic"`
- `channelId`: 手順 1 の `list_channels` の値

リンクは X では本文に書き、Bluesky と Substack では `metadata.<面>.linkAttachment.url` に入れて
本文には書かない（Bluesky は本文の URL も 300 に数える）。
`metadata.twitter.isAiGenerated` は著者が指定したときだけ設定する。

作った直後に、各 post を `get_post` で読み戻し、次の 3 点を確かめる。
- `status` が `draft` であること。`draft` 以外なら、post id と status をすぐ著者に伝える
- 本文が渡した文と一致すること
- Bluesky と Substack では、`metadata.<面>.linkAttachment.url` が残っていること。消えていたら
  `edit_post` で本文の末尾に URL を足し、Bluesky では 300 grapheme に収まるかを数え直す

429（rate limit）が返ったら止めて報告する。

### 5. 報告する

面ごとに、本文（コードブロック）、長さ（X は重み付きの値、Bluesky は grapheme 数）、post id、
読み戻した status を並べる。著者の直しは `edit_post` で反映し、また読み戻す。

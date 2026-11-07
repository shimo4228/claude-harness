# ADR-0030: 常駐テキストの書き方とユーザー向け出力の書き方を分離する

## Status

superseded by [ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) — output-register rule を退役し、
出力較正は substrate に委譲

## Date

2026-08-01

## Context

ユーザーから「Claude Code の説明が専門用語過多でわかりづらい。これは Claude Code のネイティブな
挙動か、自分のハーネスによるものか切り分けたい」という指摘があった。調査の結果、原因は 2 層に
分かれていた。

**層 1 — Explanatory output style。** `~/.claude/.claude/settings.local.json` の
`outputStyle: "Explanatory"`。Claude Code 組み込みのスタイルで（`~/.claude/output-styles/` は
存在せず自作ではない）、★Insight ブロックの付与と「教育的内容のためなら通常の長さ制約を超えて
よい」をシステムプロンプトに注入する。置き場所が project-local overlay 側なので `~/.claude`
repo のセッションでのみ有効（他 project の outputStyle は grep で 0 件）。これは冗長さの原因では
あるが難解さの原因ではない。

**層 2 — 常駐テキストの語調模倣。** グローバル常駐（`rules/common/*.md` + `CLAUDE.md`）計 3069 語に
対し、地の文中の英語技術語が延べ 1008（異なり 537）、造語・専門語が延べ 164（正本 21 / ゲート 26 /
台帳 18 / 常駐 13 ほか）。一方で文体を指示する記述は `grep -rniE
"簡潔|平易|わかりやすく|専門用語|jargon|concise|terse|tone|register|文体"` を rules/ CLAUDE.md
AGENTS.md に対して実行して 0 hits。

つまり難解な出力は「密に書け」という指示の結果ではなく、常駐テキストの語調をモデルが模倣した
結果だった。削除すべきルールは存在せず、不足している指示がある型の問題である。この点が診断上の
要で、「どのルールを消せば直るか」という問いには答えがない。

## Decision

`rules/common/output-register.md` を新設し（常駐 +66 語）、常駐テキストの圧縮された書き方を
ユーザー向け出力に持ち込まないことを常駐ルールにした。

1. rules 本文の圧縮自体は正しいものとして維持する（常駐は希少資源）。直すのは Claude から
   ユーザーへの出力側のみで、入力（常駐テキスト）と出力の書き方を分離する
2. 判定基準は「その語を知らない人が読んで意味が通るか」という自足した基準に置く
3. ユーザー発話の参照は、文体の手本としてではなく「その語を使ってよいか」という語彙の可否判定
   にのみ限定する。条件は「会話からユーザーがその語を理解していると分かる場合」
4. 層 1（Explanatory output style）は変更しない。ユーザーが「むしろ助かっている」と表明したため

## Alternatives Considered

### 判定基準をユーザー発話の模倣にする

初版はこの形で書いたが、ユーザーから「私はこの程度の短い発話しかしないから圧倒的にコンテキスト
が不足しないか」と指摘され却下した。サンプル量が足りないことに加え、ユーザーの発話は質問や指示
であって説明文ではないため、そこから説明文の書き方は導けない（ジャンル不一致）。語彙の可否判定
という限定用途でのみ残した。

### Explanatory output style を default に戻す

ユーザーが有用と判断して残した。難解さとは直交する（冗長さの原因ではあるが、語彙密度は変わらない）。

### rules 本文 3069 語の平易化

却下。平易化は語数増、すなわち常駐コスト増を意味する。rules は Claude 向けの内部表記であり圧縮が正しい。

## Consequences

### Positive

- ユーザー向けの説明文と常駐テキストの書き方が別の基準を持つようになった。常駐テキストは
  今後も圧縮してよい

### Negative

- rule であるため効果は確率的。決定論的な強制ではない
- 常駐が 13 ファイルから 14 ファイルに増えた

### Neutral / Follow-ups

- cross-model review（codex）で初版が自己適用に失敗している（ルール自身が「知らない読者に
  通じる文で書け」という基準を満たしていない）と指摘され、本文を書き直した。「Output Register」
  「自足させる」等の未説明語を排除し、「読みやすさを捨てた代償で成立している」という不自然な
  対立構図を削除し、例外条件を「ユーザーが一度書いた」から「理解していると分かる」へ限定した
- 失効条件は当該ファイルの `review-when` コメントに記載した（rules 本文の語彙密度が下がり
  出力への漏れが止まった時 / harness が出力の書き方を native に較正するようになった時）

## References

- [ADR-0018](0018-rules-rightsize-for-claude5.md) — rules rightsize。常駐は希少資源という
  前提を共有する
- [ADR-0019](0019-human-gate-layer.md) — 新規 rule ファイル追加の前例（第 2 軸の正本を
  1 ファイルに立てた判断）
- [`rules/README.md`](../../rules/README.md) — Rules vs Skills の判定（常駐に足すかどうかの基準）
- `rules/common/output-register.md` — ADR-0035 で退役

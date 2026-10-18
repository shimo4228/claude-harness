---
state: in_progress 2026-09-28
review-when: 試行 2 週間が終わったとき
---
## Summary

著者の指摘が成果物を変えたとき、その commit 本文に `指摘:`（著者の原文そのまま）、`Trigger:`（何が起きたか）、`Expect:`（外れたと分かる観測）を足す。最初の試行は zenn-content の記事で 2 週間。

## Motivation

指摘は記録の段階で消えている（RFC-0027）。著者はコードをレビューせず、harness と記事を直す — 指摘の単位は方針と文への修正で、どちらも commit で終わる。別の台帳は作らず、commit を一次記録にする（回収機構は作らない — ADR-0055 D5 と両立）。

## Guide-level explanation

記事では、構成中の指摘ごとに修正前後の抜粋と原文を下書きの台帳（`drafts/`、非公開）に積み、公開時の commit 本文へ写す。公開前の public-safety scan を通す。harness では変更 commit に直接書く。

## Unresolved questions

原文の引用が会話と一致するかを何で検査するか / 誰の指摘かの語彙（著者・判断役・レビュアー・機械）/ 修正前の稿を公開 repo に入れるか。

## Status

**2026-09-27 draft** — 予測（外れうる形）: 試行後の記事 commit を読者役（RFC-0031）が照合すると、4 環のうち 3 環以上が「確認」になる。撤退条件: 著者起点の変更のうち原文付きが半分未満、または引用が会話と食い違う。

**2026-09-28 in_progress** — 著者の指示で試行開始（2026-09-28〜10-12）。zenn-content に試行 rule `.claude/rules/correction-trailers.md` を置いた（zenn-content `76bcf5b`）。writing-ecosystem 本体は試行中は変えない（公開 skill repo に同期されるため）。Unresolved への仮の答え（指示に無かったので判断役が置いた — 違えば書き換える）: 引用の一致は試行の終わりに session ログと突き合わせて数える / 誰の指摘かは試行では著者だけを積み、reviewer・機械は既存の処分記録に任せる / 修正前の稿は公開しない（前後 2 行の抜粋を非公開の `drafts/<slug>.corrections.md` に残し、commit には原文・Trigger・Expect だけを写す）。harness 側の「変更 commit に直接書く」は試行の結果を見てから。

triage 2026-10-18（試行の読み — 判断役が数えた。体感は著者だけが答えられる）:
- 原文付きで commit に残った割合: zenn-content の非公開 `drafts/*.corrections.md` 7 本に 137 件、試行期間（2026-09-28〜10-12）の commit 本文に `指摘:` ブロック 122 件（22 commit）。撤退線「半分未満」には当たらない。件数の差は、1 本の記事の写しが試行期間外の commit・別 repo の commit にあることを含む（件ごとの突き合わせはしていない）
- 原文が会話と一致した割合: 原文の「」181 個を zenn-content の session ログと空白を除いて照合。著者の発言（user メッセージ）に一字一句で一致 171、tool の結果（artifact のコメント等）に一致 9、どこにも見つからない 1。食い違いと確定した件は 0、出所不明が 1
- 体感: 未回答（digest で著者に聞く）

**2026-10-18 著者判断: 続ける**（triage digest への回答「1a」）。出所不明の 1 件は確かめずに進める。次は試行 rule の手順を writing-ecosystem の処分規律へ移し、zenn-content の `.claude/rules/correction-trailers.md` を消す（skill の変更なので diff は著者が見る）。

## Next action

2026-10-12 に rule の「試行の読み」の 3 つを数え、続けるか撤退かを決める。

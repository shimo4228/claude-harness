---
state: in_progress 2026-09-21
review-when: Weekly·Fable 枠が回復し、RFC-0024 とまとめて採否を検討するとき。または Jev を使う判定が 1 つでも本番配線され、較正データの不在が実害になったとき
---

## Summary

Jev の判定を**版付きで貯める shadow registry** を harness に置き、質問文・model version・確率・後続の実 outcome を 1 行として残す提案。閾値はデータが溜まってから引く。

## Motivation

`measurement-discipline` は 3 つの原則で較正データを要求するが、harness にはそれを貯める場所が無い。

- **原則 2（ゲートは暦でなく観測量で）** — 「次へ進む」条件を日付にしない。必要な観測数を見積もり、溜まったら進む。**その観測数を数える場所が要る**
- **原則 3（発火率 0% と 100% はどちらも設計ミス）** — 「ガードを置いたら実データで発火率を測る」。較正できるデータが無いならガードでなく生の読み値を出す
- **原則 5（通過分だけのスコアで分布を語らない）** — 分布・較正・閾値の議論はフィルタ前の全量か、少なくとも棄却側のサンプルを添えてから

[RFC-0024](0024-typesafe-jev-as-offload-for-max-quota.md) の設計原則 4 は「較正は自分のデータで」と書いているが、**その執行装置を持たない**。判定を Jev へ降ろす設計は全体が閾値設計なので、貯める層が無いまま入れると閾値を「とりあえずの値」で固定することになり、後から較正できなくなる。

## Guide-level explanation

1 判定 = 1 行の追記ログ。読み手は後続の棚卸しセッションと、閾値を決めようとしている人間。

行に載るもの:

| 欄 | なぜ要るか |
|---|---|
| 時刻 / repo / session | 既存の `metrics/*.jsonl` と同じ join key |
| model version | alias は無通知で動く。版が違う行を同じ分布として読まない |
| 質問 ID と**質問文そのもの**（または hash） | **この欄が本 RFC の要点**。質問を書き換えると、同じ ID で意味の違う記録がまざる。名前だけでは版の差が記録されない |
| 確率（Noul / Choice / Score の生値） | 集計しない。生の読み値を残す（`llm-as-judge` ③） |
| 後続の実 outcome への join key | 「判定がこう出た結果、実際どうなったか」を後から突き合わせる |

**貯めるだけで、判定も分岐もしない。** 描画・読み戻し・状態機械・aging は持たない（CA ADR-0095 — 台帳を読む機構を足した版は 2 日で 5,000 行になり、そのバグを台帳に起票して直し続ける形になった）。

## Reference-level explanation

**先例が 1 本あったが、ファイルは残っていない。** 2026-09-20 に `hooks/security-surface-shadow.sh`（91 行）と `tests/security-surface-shadow.bats`（95 行）が書かれ、本 RFC 起票の直前に Rewind で削除された。git にも入っていないので復元できない —— **以下の schema は本 RFC が唯一の記録**。内容は commit 直前の staged diff を Noul 6 問（credentials / external_io / publication / unattended / llm_context / permission）で判定し、記録だけする。version pin・fail-open・送信範囲の限定（パス・hunk ヘッダ・追加行の先頭のみ）・symlink 防御まで揃っている。保存 schema は:

```json
{"ts":…, "project":…, "session":…, "n_files":…, "model":"jev-1.13.0",
 "surface":{"credentials":0.02, "external_io":0.91, …}, "input_tokens":812}
```

RFC-0024 の Status が記録するとおり、この hook は**着手順の誤りとして Rewind 対象になった**成果物で、security-reviewer が HIGH 2 件（敵対的 `.git/config` 経由の任意コマンド実行 / secret-scan の判定より先に追加行が外部へ出る）を出している。採用するのは**保存層の形だけ**で、この hook を書き直して配線する提案ではない。

その schema に足りないもの 3 点が、本 RFC の実装対象:

1. **質問文の版が無い。** 6 軸の名前と確率だけが残るので、`instructions` を書き換えた瞬間に過去行との比較が黙って壊れる
2. **outcome への join key が session だけ。** 「呼ぶべきだったのに呼ばれなかった」を数えるには commit hash 相当が要る（この hook 自身のコメントが「起動記録と突合する」を動機に挙げている）
3. **閾値と反例の置き場が無い。** 原則 5 のために全行を書く設計なのでデータは揃うが、「この行を見て閾値をこう決めた」「この行が反例だった」を残す場所が無い

守る規律は RFC-0024 の設計原則 1〜8 をそのまま継承する（集計しない / block に直結しない / fail-open / version pin / 日付と数え上げは code のまま）。

## Drawbacks

- **外部送信の範囲が増える。** registry 自体は送信しないが、貯める価値のある判定を増やすほど送る state も増える。RFC-0024 の Drawbacks「外部送信する hook は harness の脅威面を実際に広げる」がそのまま効く
- **観測ゼロのまま置くと、原則 3 の反例になる。** 発火率 0% のガードは「検査済み・問題なし」と誤読させる。registry は判定しないので厳密にはガードではないが、**空の registry を根拠に「測っている」と言えるようになる**のは同じ穴
- **判定器を増やすと検証対象も増える**（RFC-0024 の Drawbacks と同型）

## Rationale and alternatives

- **貯めずに、閾値を決めるときに都度測る** — 却下。原則 2 が暦ゲートを禁じており、「決めるとき」が暦で来る。判定はセッション中に流れて消えるので、後から遡れない
- **既存の `metrics/*.jsonl` に相乗りする** — 部分採用。`agent-usage.jsonl` / `skill-usage.jsonl` の「consumer-independent measurement layer」（consumer はファイルを読むだけ、計測はどの consumer にも依存しない。log が無いことを usage ゼロと読まない）は、そのまま継承すべき設計。ただし質問文の版を載せる欄が無いので、Jev 判定は別ファイルにする
- **判定のたびに人間が見て記録する** — 却下。頻度が合わない（Jev の想定は高頻度で小さな判断）

## Prior art

- `hooks/log-agent-usage.sh` / `log-skill-usage.sh` の measurement layer パターン（consumer 非依存、欠測を「未測定」として扱い決してゼロと読まない、symlink 先に書かない）
- TypeSafe docs が cookbook の閾値をすべて illustrative と明記していること（自分のデータで測る前提が vendor 側にもある）
- CA ADR-0095（台帳を読む機構を足さない）— registry に機能を足さない根拠

## Unresolved questions

- **質問文を変えたとき、過去行をどう扱うか。** 版を切って同じ ID を使い続けるか、新しい質問 ID にするか。前者は分布の連続性を壊し、後者は ID が増え続ける
- **outcome のラベルを誰が付けるか。** 決定論ゲートの結果（exit code / reviewer の起動有無）で自動的に埋まる範囲と、人間が付けるしかない範囲の境界
- **どこまで貯めたら閾値を引けるか。** 原則 2 は「必要な観測数を事前に見積もる」を要求するが、その見積もりの方法自体がまだ無い

## Status

**2026-09-20 draft** — 外部リサーチレポート（Jev 周辺の既製実装と構想の棚卸し、as-of 2026-09-20）の発散側から抽出した 2 本のうちの 1 本。もう 1 本は [RFC-0026](0026-jev-agent-trace-sensor.md)。採否は Fable 枠回復後に RFC-0024 とまとめて検討する。

**2026-09-21 in_progress** — registry の最小形を `metrics/jev-decisions.jsonl` として
RFC-0024 候補 2（`skills/jev-skill-router/`）に同梱して実装する。上の「足りないもの 3 点」への対応:
(1) 質問文の版 → `question_hash`（質問文定数から導出）+ `model` + `router_version`、
(2) outcome への join key → `session` + `ts`（`metrics/skill-usage.jsonl` と読む側で時系列突合。
ログには焼かない）、(3) 閾値と反例の置き場 → **未対応**（データが溜まってから決める）。
Unresolved「質問文を変えたとき」への暫定回答: ID を増やさず、hash が変わった行を別分布として読む。

## Next action

RFC-0024 / RFC-0026 と同時に採否を決める。**採用するなら実装順はこちらが先** — RFC-0026 の閾値がこの registry のデータに依存する。

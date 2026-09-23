---
state: draft 2026-09-20
review-when: Weekly·Fable 枠が回復し、RFC-0024 / RFC-0025 とまとめて採否を検討するとき。または loop-design-check が明示している 2 つの未解決（side-findings の policy / spawned work の admission）が実害として観測されたとき
---

## Summary

agent の**走り終わり**（会話・tool call とその結果・final message）を Noul 数問に割り、後続処理を 6 択へ仕分ける shadow sensor の提案。loop の done と stuck を機械で分ける。

## Motivation

`loop-design-check` の核心文はこれだ:

> **a loop that cannot mechanically tell done from stuck does not fail loudly — it keeps spending tokens.**

同 skill の Step 1（machine-decidable goal）が挙げる例は**すべて決定論側**にある — 全 test green、reconciliation diff < 0.01、AC-NNN、exit code。semantic 側は空白のままで、そこは今まで「決定論で書けないなら loop にしない」で塞いでいた。

さらに同 skill は末尾で 2 つの問いを名指しし、**運用ルールが誰にも検証されていない**として明示的に手を引いている。どちらも semantic 判定を要求する:

1. **side-findings mid-loop** — 走行中に別の問題を見つけた。今直すか / 起票するか / 捨てるか。「どの policy を採るにせよ *述べよ*、そして生む backlog を *測れ*」
2. **spawned-but-unstarted work の増殖** — 「WIP limit と budget は *実行* を絞るが、新規 node の *受け入れ* は何も絞っていない」

rule `task-tracking` と ADR-0055 は 1 に部分的な答えを持つ（review 指摘は loop 自身を壊す欠陥だけ起票、他は severity 不問で commit message に 1 行残して捨てる）。**その判定を今やっているのは人間か上位モデルで、しかも loop の中なので毎周回払っている。**

## Guide-level explanation

TypeSafe の公開 eval に、同じ問題を解く workflow がそのまま 1 本ある（Agent Trace Observability、as-of 2026-09-20）。入力は agent の instructions・全 turn の会話・各 tool call とその結果・final message・あれば feedback。出力は 6 択:`AUTO-CLOSE` / `NOT A BUG` / `HUMAN REVIEW` / `PRIORITY REVIEW` / `FILE ISSUE·ROUTE` / `PAGE ON-CALL`。

3 段で決める。

1. **不可逆 action をその時点の権限と照合する。** breach なら人を呼んで review はそこで終了
2. **「task が完了したか」と「依頼者が満足したか」を別々に聞く。** 互いの答えを汚染させないため
3. 2 つの答えが 4 outcome を選ぶ — healthy / expectation gap / overt failure / **silent failure** — 各 outcome が追加 1 問だけ聞いて終わる

この 3 段が、harness の既存資産とほぼ一対一で対応する。

| eval の段 | harness 側の対応物 |
|---|---|
| 不可逆 action × 権限の照合 | rule `boundary.md` の「人間に渡す」列挙 — **照合表が既に書かれている** |
| completion と satisfaction を別々に聞く | `llm-as-judge` の「binary 証拠を集め、集計せず、named verdict」 — **同じ契約** |
| 4 outcome の **silent failure** | `loop-design-check` の失敗モード #2「agent confidently says fine and stops」 — **skill は red と判定するが検出手段を持っていない** |
| 6 択の仕分け | `task-tracking` の「起票する / commit に 1 行で捨てる」の 2 択 — **今より粒度が細かい** |

## Reference-level explanation

**一次数値**（同 eval、4 workflow のうちこの 1 本の値。vendor measurement）:

| 構成 | 正解率 | 1 件あたり | 時間 |
|---|---|---|---|
| opus 5 · 丸ごと prompt | 63.5% | $0.1642 | 37.5 s |
| opus 5 · workflow（割って聞く） | 75.2% | $0.1033 | 27.4 s |
| Jev · workflow | **71.6%** | **$0.0003** | **0.5 s** |

割れば Jev は opus の一発プロンプトを 8.1pt 上回り、opus の workflow に 3.6pt 及ばず、コストは 1/344、時間は 1/55。**vendor 自身の測定**であり、harness の実データで再現するかは未検証。

**発火点。** `settings.json` に **Stop hook のセクションが無い**（現在は PreToolUse / PostToolUse / SessionStart / UserPromptSubmit のみ）。Stop hook の新設 1 本が実装本体になる。

**観測資産は既にある。** `metrics/agent-usage.jsonl`・`skill-usage.jsonl`・`ask-one-question.jsonl`、daily-research の 34 日分の生ログ。判定の保存先は [RFC-0025](0025-jev-decision-contract-registry.md) の registry。

**段の切り方。** shadow のみ（記録だけ、advisory も block も出さない）→ 判定が溜まってから閾値 → その後に advisory。RFC-0024 の設計原則 1〜8 を継承する（集計しない / block に直結しない / fail-open / `jev-1.13.0` を pin / 日付と数え上げは code のまま）。

## Drawbacks

- **送る state の設計が難しい。** session 全文を送るのは Jev の公式 jaggedness（長文・無関係情報の多い state で精度低下）と逆行し、送信範囲の問題も大きい。何を落として何を残すかがそのまま判定品質になる
- **誤判定の向きが悪い。** 「詰まっている」と誤って判定して介入すると、長いが健全なセッションを止める。`measurement-discipline` 原則 3 のとおり、発火率を測るまで advisory にしない
- **判定器を増やすと検証対象も増える**（RFC-0024 の Drawbacks と同型）。Stop hook は無人で走る経路なので、`security.md` の脅威面（無人実行 + 外部送信）に正面から乗る

## Rationale and alternatives

- **決定論だけで done / stuck を分ける**（turn 数・経過時間・同一 tool の反復回数の閾値） — 部分採用。安い guard として先に置けるが、**長いが健全なセッションと詰まったセッションを分離できない**。分離できる決定論条件が書けるなら loop-design-check Step 1 の既定どおりそちらが正しく、本 RFC は不要になる
- **上位モデルに判定させる** — 却下。判定が loop の中にあるので毎周回払う。RFC-0024 の Motivation そのまま（判定役が Max 枠を食っている）
- **既製の Stop hook plugin を入れる**（jevwire など、tool input / result / turn state を外部送信する hook 一体型） — 却下。RFC-0024 の Rationale が既製 plugin 系を却下した理由に加え、`security.md` が無人 hook への第三者コード投入を実在の脆弱性として扱う。**パターンだけ取って実体は入れない**
- **`/loop` や Workflow の budget guard で足りる** — 却下。budget guard は damping であって done / stuck の判別ではない（loop-design-check Step 4 と Step 1 は別のステップ）

## Prior art

- TypeSafe Agent Trace Observability eval（一次、as-of 2026-09-20）— 上の 3 段と数値
- `loop-design-check` の lineage（Osmani, *Loop Engineering*, 2026-06 が "done vs stuck" と inner/outer loop の出所）
- rule `task-tracking` / ADR-0055 — review 指摘の起票規律が 6 択の一部に対応する既存判断
- `hooks/security-surface-shadow.sh`（2026-09-20、Rewind で削除済み・git 未登録）— 同型の「Noul 群で判定して記録だけする」実装の先例。schema と security-reviewer の HIGH 2 件は [RFC-0025](0025-jev-decision-contract-registry.md) が記録している

## Unresolved questions

- **何を state として送るか。** 全文 / tool 名と結果の要約のみ / final message + 直近 N turn。送信範囲と判定品質の両方が変わる
- **silent failure が harness の実データで分離するか。** vendor の eval は customer support log で、コーディング agent の走り終わりとは分布が違う
- **side-findings の policy 測定を同じ sensor に載せるか。** loop-design-check の未解決 1 は「生む backlog を測れ」なので、6 択のうち起票系の 2 つを数えれば測れる可能性がある。別機構にするかは未決
- **daily-research のような `claude -p` の子プロセスで Stop hook が発火するか。** 実機確認が要る

## Status

**2026-09-20 draft** — 外部リサーチレポート（Jev 周辺の既製実装と構想の棚卸し、as-of 2026-09-20）の発散側から抽出した 2 本のうちの 1 本。同レポートの候補 15 件を Jev 自身に 7 軸の Noul で評価させたところ、「harness が名指ししている未解決を埋めるか」の軸で最高値（0.90）を返した候補がこれだった。ただしその評価に渡した state には本 RFC の Motivation より粗い要約が入っていたので、根拠は上の一次ソースで組み直してある。

**2026-09-21** — 自作しない方向（著者判断、RFC-0024 の同日追記）。同じ問題の一部（証拠なしの完了宣言 =
silent failure）を解く Claude Code plugin が既にある: `valentynkit/jev-belay`（MIT、Stop hook、
`jev-1.13.0` pin、shadow mode と decisions.jsonl を持つ。as-of 2026-09-21、README を確認・コード未読）。
試すなら shadow mode で、導入前に hook 本体を security-reviewer に 1 回通す。6 択の仕分けと
side-findings の計測は同 plugin の範囲外で、未解決のまま残る。

## Next action

RFC-0024 / RFC-0025 と同時に採否を決める。**実装順は RFC-0025 が先** — この sensor は閾値を持つので、閾値を自分のデータで決める場所が先に要る。

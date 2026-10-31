# ADR-0098: triage の digest を「1 cycle 1 枚の report・1 回の承認」にする

## Status

accepted — [ADR-0043](./0043-task-triage-loop-judge-build-human.md) の Decision 5（digest は 1 判断 1 メッセージ）、
[ADR-0045](./0045-triage-loop-launchd-tick-and-slack-digest.md) の digest の置き場（2026-08-30 注記でセッションの応答本文、
1 判断 1 メッセージ）、[ADR-0076](./0076-build-proposals-with-reproducer-and-opus-5-5-packet-rules.md) の Decision 5（逆提案を
起動前に 1 メッセージで見せる）を置き換える。3 本に注記する

## Date

2026-11-01

## Context

- 著者（2026-11-01、harness-stocktake の merge の直後）: 「task-triage だけど、これもこのスキルと同じようにアーティファクトで
  出して一括承認する方式に変えて」。「このスキル」は skill: `harness-stocktake`（[ADR-0097](./0097-batch-stocktake-report-and-two-decisions.md)）
- task-triage §2 は、判断を 1 メッセージに 1 件ずつ、背景 → 賭け → 選択肢 → 推奨 → コスト／可逆性の順で書き、著者が戻ったら
  `AskUserQuestion` で 1 件ずつ聞く形だった。無人 cycle ではその全件を閉じの応答に書き、Slack にはタイトルだけを 1 通送る
- 著者の答え方は既にまとめ返しだった: task-triage §2 自身が「"T-002 は done、RFC-0005 も done" のような一括の返事は普通で速い」と
  書いている。1 件ずつの問いは、まとめて返せなかった残りに対してだけ使われていた
- [ADR-0097](./0097-batch-stocktake-report-and-two-decisions.md) は棚卸しで同じ形（Artifact の `db` store に項目を置き、項目ごとに
  書き換え、承認ボタン 1 回）を入れた。初回の全体実行は 2026-10-31 に report を作り、80 項目を 1 回の承認で通して 2026-11-01 に
  適用した（commit `b876e3a`..`b757816`。report の store の `outcome` を数えて適用 65、未決 15）
- task-triage の判断には、棚卸しに無い種類がある: 自由記述でしか答えられない問い（受入条件、性能の指標、ground truth の定義 —
  ADR-0076 の逆提案）、公開 repo の dispatch の OK（公開に当たる）、判断の無い報告行（merge したもの、build ごとの effort 行）
- 無人 cycle は launchd の tick が起こし、著者は Remote Control で電話から読む（ADR-0045）。Slack は片方向

## Decision

1. 1 cycle で著者に要る判断は全部、cycle の終わりに公開する **1 枚の Artifact report**（`skills/task-triage/templates/digest.html`、
   `db` の store）に載せる。著者は書き換えたい項目と問いだけに答え、承認ボタンを 1 回押す。セッションは承認の後に各項目を
   実行し、結果を store に書き戻す。公開・読み戻し・判定表は skill: `harness-stocktake` の report の契約を参照して使う。
   報告の項目しか無い cycle は report を公開せず、応答と Slack の「0 decisions pending」で済ませる
2. 項目は 7 群に分ける: 終端の確認 / 採否 / 開始の OK（公開 repo の dispatch・bounce、逆提案の既定値）/ merge の OK（人間に渡す
   diff）/ 起票の判断 / 記帳（語彙の当てはめだけ。畳んで表示し、書き換えなければ実行）/ 報告（判断なし。畳んで表示）。規約の
   変更・リスクの受容・課金・drop は記帳に入れない
3. 自由記述の問いは項目の `question` に置き、`change` に既定値を書く。承認で既定値のまま進み、note があれば note が答えになる。
   note から動作が一つに決まらなければその項目は未決になり、次の report に持ち越す
4. 承認が答えるのは、ボタンを押した時点で report にあった項目だけ。後から足した項目は次の report を待つ。次の cycle の公開までに
   承認されなかった report は superseded にして、開いた項目を判定し直して新しい report に持ち越す。各 cycle は最初に、承認済みで
   結果の無い report を適用する。前の report は `~/.claude/.notes/triage/<repo dir name>.json`（URL と日付だけ）で見つける
5. Slack は cycle ごとに 1 通のまま。判断の件数・report の URL・各項目の 1 行タイトルを送り、理由は送らない。生存信号の役割は
   変えない。答えは report の判定と承認、または triage セッションでの著者自身の言葉だけ
6. Artifact の無い環境では、同じ項目を `~/.claude/.notes/triage/<repo dir name>-<date>.md` の表にし、承認はチャットで取る

## Review-when

- 著者が承認済みの項目を後から取り消した（「見落としていた」と言った、実行を戻した）— report では読まれていない。drop と公開の
  dispatch だけ承認を分けるか検討する
- 同じ repo で、承認されないまま superseded になった report が 2 cycle 続いた（各 report の `meta/run.phase`）— 電話から report を
  開く経路か、通知の形が合っていない
- 自由記述の問い（`question`）の項目で、note の答えが動作を一つに決めず `outcome: pending` になった件数が、どちらかの repo で 4 週の
  合計 3 件を超えた — 問いの書き方か、その種類を対話に戻すかを見直す
- Claude Code か claude.ai が、項目ごとの承認を一括で受ける UI を native に持った

## Alternatives Considered

- **1 判断 1 メッセージを残す** — 著者は実際にはまとめて返しており（Context）、1 件ずつの問いは残りにしか使われていなかった。却下
- **会話の中でまとめる**（1 回の `AskUserQuestion` に問いを並べる、または応答にチェックリストを書いて 1 回で返してもらう）— Artifact と
  `db` に依存しない。ただし無人 cycle では答える場が応答本文しか無く、電話で長い応答を遡ることになる。項目ごとの書き換えと結果の
  書き戻しを置く場所も無く、次の cycle が前の判断と実行の状態を読めない。Artifact の無い環境の代替（Decision 6）としてだけ残す
- **harness-stocktake のテンプレートを共有する** — 1 本で済むが、棚卸しの群（退役・統合・改善・維持）と Keep の選択肢が triage に
  合わず、片方の変更がもう片方を壊す。目的の違う 2 つの report は写しを持つ方が軽い。却下
- **repo ごとに常設の report を 1 枚置き、cycle ごとに中身を入れ替える** — URL が固定で pin できるが、前の cycle の判定と承認が
  store に残って混ざり、superseded の扱いが要らなくなる代わりに消し込みの手順が要る。cycle ごとに新しい report にした
- **ADR-0097 と同じ 2 回の判断（report の承認 + 完了 report の merge）** — triage の merge は §4 の検収を通せば判断役が取る
  （ADR-0069）。人間に渡す merge は report の 1 群として既に載るので、2 回目の判断は要らない。却下
- **自由記述の問いだけ対話に残す** — 問いが cycle をまたいで止まり、無人 cycle では答える場が無い。既定値つきの項目にして、
  答えない場合も進むようにした。未決の件数を Review-when で見る

## Consequences

- 著者の判断は 1 cycle につき 1 回になる。drop・公開の dispatch・人間に渡す merge もその 1 回に含まれる
- 「中身を見ない一括承認」の防ぎ手が、各項目の reason が単独で判断できることと群の並びに移る。reason の質が落ちると承認は形だけになる
- 判断の材料が応答本文から report に移るので、Remote Control で会話を遡らずに読める。代わりに Artifact と `db` に依存する
- テンプレートは harness-stocktake の写しなので、共通部分（`db` の配線、承認ボタン、safe-area）の修正は 2 本に入れる。写しの存在と
  この規則は `skills/task-triage/MAINTENANCE.md` が持つ
- 前の report の URL が `~/.claude/.notes/triage/` に残る（git の外）。消えると承認済みの report を次の cycle が拾えないが、判断と結果は
  report の store に残る
- 承認から実行までは、著者が triage セッションで話すか次の tick が来るまで空く。承認ボタンはセッションを起こさない
- 戻すときは、task-triage の §2 と tick の prompt（`scripts/triage-tick.sh`）を git revert すれば 1 判断 1 メッセージに戻る
- Contemplative Agent の土曜の cycle は `weekly-gate-ca` セッションの中で task-triage を回す。その prompt
  （`scripts/launchd/weekly-gate-ca-prompt.txt` の Step 8）も §2 の report に揃えた。weekly-gate 自身の承認待ち（CA repo の skill
  `weekly-gate`）は 1 件ずつのまま残り、変えるなら CA repo の作業になる
  > **注記（2026-11-01, CA ADR-0130）** 同日に CA repo の weekly-gate も 1 枚の署名つき report（既定の選択なし）に移した。
  > prompt の前半もそれに揃えた

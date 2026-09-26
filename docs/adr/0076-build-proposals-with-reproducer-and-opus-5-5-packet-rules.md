# ADR-0076: build の起票は再現手順つき提案まで開き、Opus 5.5 ガイドと claude.ai 高速化記事の規則を packet に入れる

## Status

accepted — [ADR-0055](./0055-review-chain-single-pass-regression.md) Decision 5 の digest への入口（loop を
壊す欠陥で producer を確かめたもの / probe 自身の起票要求）に 3 つ目（build の再現手順つき提案）を足し、
[ADR-0043](./0043-task-triage-loop-judge-build-human.md) の無人 dispatch の範囲を狭める（どちらも部分的に
弱める。注記は各 ADR 側）

## Date

2026-09-25

## Context

- 著者の依頼（2026-09-25）: claude.dev の記事 2 本を harness に取り込み、実装の dispatch に反映する。
  既にネイティブに動いているものは不要、著者の指示に欠けがあれば判断役が内容を逆提案する。続けて著者は
  「モデル性能が上がったのだから、自律性を高めるために Claude が自分で新しいスレッドを起票するのを許して
  よいか」と問い、全面解禁 / 再現手順つき提案 / 現状維持の 3 案から提案型を選んだ。
- 記事 1: Addy Osmani「Getting the Most Out of Opus 5.5 in Claude and Claude Code」
  （https://claude.dev/blog/getting-the-most-out-of-opus-5-5/ 、2026-09-22）。記事 2: Raymond Wang ほか
  「How we made claude.ai 3x faster in two weeks」（https://claude.dev/blog/how-we-made-claude-ai-faster/ 、
  2026-09-23）。判断役は WebFetch の要約経由で読み、adr-reviewer が原文を取得して照合した（2026-09-25）。
- dispatch の実体は skill `task-triage` §3 と `skills/task-triage/references/packet-template.md` で、cloud の
  build 役は `~/.claude` を読まない（[ADR-0075](./0075-cloud-session-as-default-build-executor.md)）。記事の
  推奨を packet と突き合わせた結果:
  - 既にある 6 項目: 完了条件を示して任せる（packet の Goal）、「よく考えて」を書かない・推論の中身を返答に
    書かせない（skills / agents / rules / output-styles を「よく考えて / think hard / think carefully /
    step by step / ultrathink」で grep して 0 件、2026-09-25）、人より先に review を回す（built-in
    `/code-review` medium）、1 packet 1 scope、テストを先に。
  - 欠けていた 8 項目: 止まらずに続ける規則、subagent 分割と証拠の確認、チェックリストのファイル化、
    報告の先頭に「要るもの」、確かめられなかったことの印、flag で旧モデルに切り替わったことの検出、UI で
    避けるスタイルの具体名と before/after、性能改善の測定先行（決定的な指標・実測との相関・ratchet）。
  - cloud の reviewer 指示には、記事 1 の review prompt にある「失敗を示す方法」が無かった。
- 記事 2 の起票まわりの記述: "ticket に回す" は Claude の既定の慎重さとして挙がり（"It tickets findings,
  hedges on feasibility, and pads its estimates"）、人間は範囲内でやり切るよう押した。Claude は自分で見つけた
  機会を追って、別の調査や nightly job の一部として新しいスレッドを開いた。どのスレッドにも名前のある人間の
  担当者がいて、ユーザーの目に見える変更の可否を判断し、すべての変更を人間が承認していた。スレッドは閉じずに
  続けることが多かった。再現手順を必須にするのはこの harness 側の設計で、記事から借りたものではない。
- この harness の前提は記事の現場と違う:
  - 台帳の起票と drop は人間側の操作で、判断役でも提案まで（`rules/common/boundary.md`）
  - `rfcs/` は公開で、終端エントリもその場に残る（ADR-0049）
  - task-triage §1 は開いている全件を毎 cycle 判断役（Fable 階層、使用限度あり — ADR-0057）で判定する
  - 著者はコードもレビュー報告も読まない運用で、「人間がすべての変更を承認する」ブレーキは成立しない
    （ADR-0055 Context）
  - 即時起票が結果を変えたのは diff 外 HIGH 6 件中 1 件（ADR-0055 Context、2026-08-26〜27）
  - `rfcs/` は 26 件中 5 件が開いている（`rfcs/[0-9]*.md` の `state:`、2026-09-25 時点のスナップショット）
  - 減衰の無い自己補充の先例: CA ADR-0098（weekly fix chain を 7 セッションから 1 に畳み、1,987 行 +
    テスト約 3,400 行を削除）、CA ADR-0095（台帳を扱うコードが 30 時間でコード 2,100 行 + テスト 2,400 行、
    review 由来の spawn は 1 件 close するごとに 1.3 件生まれていた）
  - ADR-0043 Decision 3 の red line「起票規約を計測中に変えない」は loop 自身への制約で、今回の変更は著者の
    決定。ただし突合型の goal（closed ≥ spawned、open が 4 週で増えない）の比較の窓は、この変更の日から
    数え直す
- packet と Review-when のしきい値（1 build 2 件、3 単位、手順 10、time cap 1 時間、提案 RFC 5 件で 1 件）は
  著者と判断役が置いた値で、記事は数値を出していない。

## Decision

1. packet テンプレートに「進め方」節を置く。共通行: 入力が要らない step は止まらずに続け、状況メモは次の
   行動と同じメッセージに書く（止まるのは Phase 0 の反証〔記録して正しく直せる範囲を除く〕・Review の
   CRITICAL・time cap・packet の外の操作が要るとき）/ 確かめられなかったことに「未確認」と印を付け、どこを
   見たかを書く / 方針を選んだ箇所は理由を 3 文で Report の Fix に書く。条件付きの行: 3 単位以上の監査・
   移行は subagent に分けて証拠を確かめてから受け入れる / 手順 10 超か time cap 1 時間超は commit しない
   チェックリストファイル / UI は使わないスタイルを具体名で挙げ before/after の画像を付ける / 性能・最適化は
   決定的な指標に言い換え、wall-clock と同じ向きに動くことを 1 回確かめ、改善をテストの上限値で固定する /
   著者が「押し続ける」を選んだ性能タスクだけ、Goal を満たした後も time cap まで同じ指標を改善する。
2. Report に `Needs from judge`（先頭）と `Model:` の行を足し、最後のメッセージを「判断役に要るもの」から
   始めさせる。claim ラベルに build が走るべき厳密なモデル ID（`model=`）を書く。cloud の reviewer 指示に
   「各指摘に file:line・なぜ誤りか・失敗を示す手順」を足す（local の chain の指示は
   `skills/implementation-chain/SKILL.md` が正本のまま変えない）。
3. build の新しい作業の入口を Report の `Proposed tasks` にする（1 build 最大 2 件、各件に何が壊れているか・
   再現手順・決定可能な受入条件・producer `file:line`）。再現手順は branch の tip で走る 1 コマンド（repo の
   テスト実行器で名前を指したテスト、または読み取りのみ）で、commit しない（失敗するテストは CI を落とす）。
   build は `rfcs/` と台帳を書かない。再現手順を書けない気づきは従来どおり `Out-of-diff findings` の 1 行。
   packet の Escalation の note も `Proposed tasks` に向ける。
4. task-triage §4 で判断役が再現手順を扱う。再現手順は未検証の内容を読んだ session が書いた repo 由来の
   文字列なので、まずデータとして読み、branch の tip の scratch worktree の中で、repo のテスト実行器か読み取り
   のみのコマンドのときだけ走らせる。ネットワーク・資格情報・`~/`・削除に触れるものは走らせない。記述どおりに
   失敗したものだけを digest に起票の提案として出し、再現しないもの・走らせなかったものは捨てて件数を出す。
   起票を決めるのは著者で、`claims.py spawn --origin review --producer <file:line>` と skill `rfc-writer`
   で起票し、RFC の Motivation の 1 行目に `由来: build 提案 (S<n>)` を書く（印の正本は rfc-writer §2）。
   `Model:` が claim ラベルの `model=` と違えば digest に 1 行。同じ入口を skill `task-stocktake` の起票
   規律と `rules/common/task-tracking.md` に足す。
5. task-triage §3 に逆提案を置く。答えを持つのが著者だけの 4 項目 — task file に無い受入条件、UI で
   避けるスタイル、性能タスクの指標と目標、性能タスクを目標で止めるか押し続けるか — が著者の指示にも task
   file にも無ければ、判断役が既定値を packet に入れ、起動前に 1 メッセージで枝の形で見せて著者の OK の後に
   起動する。無人 cycle ではその task を digest に OK 待ちとして載せ、起動しない（task-triage の「Where the
   loop lives」にも書く）。
6. 記事の出典・読んだ日を packet テンプレートの末尾の note にも置く（packet を書く判断役が本文の出どころを
   引けるように）。根拠と失効条件の正本は本 ADR。cloud dispatch の `--model` / `--effort` の固定は決めない
   （Alternatives）。

   > **注記（2026-09-26, [ADR-0081](./0081-per-packet-effort-and-bounce-classification.md)）**: effort は
   > packet の `Effort:` 行で judge が選び、cloud には `cloud-dispatch.sh --effort` が作成後の `/effort` で
   > 適用する形に決めた。`--model` は未決のまま。

## Review-when

- この日から 4 週の突合（ADR-0043 の goal）で、spawned が closed を上回り open が増え、その spawned に
  `由来: build 提案` の RFC が入っていたら、提案枠の上限を下げるか枠を外す。数えるのは task-triage の cycle
  （`claims.jsonl` の spawn / release と `rfcs/` の由来の印）。
- `由来: build 提案` の RFC が 5 件たまった時点で `done` が 1 件以下なら、提案枠を外す。固定するもの:
  再現手順の要件と 1 build 2 件の上限。どちらかを変えたら数え直す。
- 判断役が再現手順を走らせなかった（ネットワーク・資格情報・`~/`・削除に触れる）件が 1 件でも出たら、
  build が読んだ内容からの injection を疑い、提案枠の安全策を見直す。
- 次の Opus 世代向けの同種ガイドが出たとき、または Opus 5.5 が build 役でなくなったとき、packet の
  「進め方」と Report の行を照合し直す。
- `Model:` 行に claim ラベルと違うモデルが出たら、flag による切り替わりかを確かめ、cloud dispatch の
  model 固定（Alternatives の未決）を再訪する。

## Alternatives Considered

### build の起票を全面解禁する

build が `rfcs/` に直接起票する案。却下: 起票と drop を人間側に置く `boundary.md` の線を 2 段飛ばす。
公開 repo では判断役が見る前に branch 上で公開され、却下しても公開記録として残る。開いている件数に比例して
判断役の毎 cycle の判定が重くなる。記事 2 がこれを成立させていた前提（人間がすべての変更を承認し、目に
見える変更を担当者が判断する）がこの harness には無い。減衰の無い自己補充の先例が CA に 2 つある。

### 現状維持（diff 外の気づきは 1 行で捨てる）

却下の理由は観測ではなく著者の判断 — モデル性能が上がったので、build の発見を捨てる既定から、証拠つきで
拾う既定へ一段寄せる。1 行に埋もれた発見を取りこぼした実例はまだ無く、ADR-0055 の測定（6 件中 5 件は
遅れて扱っても結果が変わらなかった）はむしろ現状維持の側にある。だから枠は再現手順と上限 2 件で絞り、
Review-when の 2 条件で外せる実験にした。

### 記事を独立した skill にする

著者の最初の依頼の形。却下: dispatch が読むのは packet テンプレートだけで、別 skill は dispatch の時点で
読まれる保証が無い（自発発火は description の改良で伸びない — skill `skill-creator` §2）。テンプレートと
二重定義になり drift する。

### 止め方の規則を repo の CLAUDE.md に、モデル切り替えを `/config` に置く

記事 1 自身が勧める置き場。cloud session も clone した repo の CLAUDE.md を読む。却下: ADR-0075 は packet を
自己完結の契約にしており、repo ごとの CLAUDE.md（CA など）に harness の dispatch 規則を複製すると repo の数
だけ drift する。未決 — 再訪条件: `/config` の「Switch models when a message is flagged」が cloud session に
効くかを確かめたとき（効くなら `Model:` 行の観測より先にそちらで止める）。

### cloud dispatch で `--model` / `--effort` を固定する

記事 1 の「深さは prompt の語でなく effort で調整する」に沿う案。未決 — 再訪条件: `--cloud` と同時に渡した
`--model` / `--effort` が cloud session に効くかを probe で 1 回確かめたとき、または `Model:` 行に claim
ラベルと違うモデルが出たとき。

> **注記（2026-09-26, [ADR-0081](./0081-per-packet-effort-and-bounce-classification.md)）**: effort の側は probe で確かめ、決めた — 作成時の `--effort` は
> cloud session に効かず、作成後の `/effort` は効く。固定ではなく packet ごとに judge が選び、
> `cloud-dispatch.sh --effort` が 2 段起動で適用する。`--model` の側は未決のまま。

## Consequences

### Positive

- cloud の build に Opus 5.5 向けの進め方が届く — harness を読まない session でも packet だけで効く。
- 再現手順のある発見が残り、判断役は再現の実行で決定的に確かめられる。
- 著者にしか答えられない欠け（受入条件・避けるスタイル・性能の指標と目標・押し続けるか）が起動前に見える。
- flag による旧モデルへの切り替わりを観測する手がかりができる。照合が成り立つのは claim ラベルに厳密な
  モデル ID を書いたときだけ。

### Negative

- **新しい実行面**: 判断役（merge 権限と `~/.claude` を持つ session）が、未検証の内容を読んだ build の書いた
  コマンドを走らせる。scratch worktree・テスト実行器か読み取りのみ・ネットワーク / 資格情報 / `~/` / 削除の
  拒否で絞るが、テスト実行器で走るテストコードは worktree の中で任意のコードを実行できる — 残るリスクは
  sandbox ではなく「判断役が走らせる前に読む」ことで受ける。
- packet が長くなる。ADR-0075 が既に挙げた「自己完結させる分だけ長い」を上乗せする。
- digest の項目が 1 build あたり最大 2 件増え、再現の確認に判断役の時間を使う。
- 逆提案で対話中の dispatch に 1 往復増え、無人 cycle では該当 task が起動されずに残る。
- 提案から起票した RFC は公開記録として残り、枠を外しても消えない（ADR-0049）。
- 記事の出典は本 ADR と packet テンプレートの note の 2 か所にある（根拠と失効条件は本 ADR が正本）。

### Neutral

- `rules/common/boundary.md` と `scripts/claims.py` は変えない。起票の決定は著者、判断役は提案まで。
- ADR-0055 Decision 5 の「回収機構（tick sweep 等）は作らない」は維持する — 提案は検収時に 1 回だけ読まれる。
- 本 ADR は提案の経路と packet の規則の 2 つを束ねている。片方だけ覆すときは、覆す ADR が本 ADR の該当
  Decision に注記を残す。

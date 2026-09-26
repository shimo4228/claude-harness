# ADR-0080: review-when の見直し条件を jrp のノート × Jev で毎朝照合する job を、shadow を経ずに本番で回す

## Status

accepted — [ADR-0074](./0074-jev-skill-router-prompt-to-external-judge-shadow-first.md) の「shadow から入る」型を
この job には適用しない（ADR-0074 自体は skill ルーターの判断で、変えない）

## Date

2026-09-25

## Context

- RFC と ADR の review-when は失効条件で、書いた時点でしか捕捉できない（[ADR-0044](./0044-adr-review-when-and-dated-annotation.md)）。
  2026-09-25 時点で、RFC 16 本が frontmatter の `review-when:` に、ADR 37 本（superseded を除く）が
  `## Review-when` 節に持っている。多くは外の世界の出来事を待つ — 例: RFC-0017「substrate が skill listing の
  注入方式を変えた時」、RFC-0004「Zenodo が legacy deposition API を廃止・変更した時」。条件とニュースを
  照合する仕組みは無く、誰かが気づかない限り発火しない。
- 案の出所: 2026-09-25 のセッションで prompt-perturb の候補（TRIZ 発明原理 27「安価で短命なオブジェクトへの
  置換」）を文脈を遮断した agent に実行させ、出た 10 案のうち「すき間時間の『いまできる』リスト」を
  この harness に着地させたもの。daily-research が毎日集める外部ニュース × 条件を、Jev の安い判定で総当たりする。
- ADR-0074 は skill ルーターを shadow から入れ、観測量が溜まってから inject を点けると決めた。その Review-when の
  最終項は「観測量に達しないまま止まる」死に方を名指ししている。著者は本 job について 2026-09-25 に
  「shadow じゃなくてもう本番回して。じゃないと回ってること忘れるだけだから」と指示した。
- daily-research は今は jev-research-pipeline（`jrp`）が担う。launchd が毎日 05:00 に `jrp run` を 1 回起動し、
  約 15 分で `<JRP_VAULT_DIR>/daily-research/{date}_jrp_{slug}.md` を書く（jrp の README と `launchd/README.md`、
  2026-09-25 に一次確認）。`JRP_VAULT_DIR` は jrp の env ファイル `~/.config/jrp/env` にある。ノートは書かれた後も
  変わる — 著者がチェックを付け、翌朝の run がそれを収穫する。
- vault は iCloud Drive にある。macOS のプライバシー保護（TCC）は、launchd 配下の `/bin/bash` には vault を
  開かせるが、uv が管理する Python には開かせない。`open()` が見えない許可ダイアログで止まり続け、jrp の初回の
  定期実行は 2026-09-24 にこれで 80 分固まった。jrp の wrapper（`scripts/launchd-jrp.sh`）は、bash がノートを
  ローカルの stage へ rsync し Python には stage だけを読ませる形で避けている。
- ノートは Obsidian vault の私用ノート（公開ソースの要約）で、公開物ではない。
  [RFC-0024](../../rfcs/0024-typesafe-jev-as-offload-for-max-quota.md) の Drawbacks は、外部送信の経路を足すことを
  harness の脅威面の拡大として記録している。条件の本文は公開 repo にある。
- Jev の wire format は、jev-skill-router が 2026-09-21 に実 API で確かめた Noul（`instructions`）と Choice
  （`instructions` + `criteria`、答えは `probabilities`）だけを使う。build 環境（cloud session）からは
  `docs.typesafe.ai` が proxy で遮断され、Score の書式は一次確認できなかった。実 API への接続も build 環境では
  試していない — 結合の確認はローカルの stub server に対して行った。
- 較正データは無い。閾値はどれも自分のデータに基づかない（RFC-0025 の Unresolved と同じ状態）。

## Decision

1. `skills/review-when-watch/` を `origin: shimo4228` の sub-project として新設する（stdlib のみ、Python 3.11+）。
   launchd で毎日 06:10 に 1 回起動する（jrp run の 05:00 開始と約 15 分の所要の後。jrp は朝 1 回しか書かないので
   2 回目は空振りになる）。plist の正本は `scripts/launchd/com.shimomoto.review-when-watch.plist` で、登録
   （copy + `launchctl bootstrap`）は人間が行う。
2. plist は Python を直接起動せず、bash の wrapper `scripts/launchd-watch.sh` を起動する。wrapper は
   `JRP_VAULT_DIR`（環境変数か jrp の env ファイル。env ファイルは subshell で読み、この 1 値だけを取り出す）の
   `daily-research/*_jrp_*.md` をローカルの stage へ rsync し、Python には stage だけを読ませる
   （`REVIEW_WHEN_REPORTS_DIR`）。vault が分からないかコピーに失敗したら Slack に知らせて止まる。
3. 判定済みのノートはファイル名で記録する。ノートは後から書き換わるので、中身の sha を鍵にすると同じノートを
   判定し直して当たりを二重に送る。
4. 判定の単位は「レポート 1 本 × 条件 1 本」、1 組 1 request とし、条件を `state` に入れる（skill
   jev-judgment-design §2・§5）。通知するかは `met`（Noul: 条件が待つ出来事が実際に起きたとレポートが言うか）
   だけで決め、閾値は `MET_THRESHOLD = 0.5` を仮置きする。`overlap`（Choice: `words_only` / `same_area` /
   `precursor` / `event`、最下段は語の共有だけ）は並べ方にだけ使い、採否に混ぜない（同 §3・§4）。
5. shadow の段を置かない。代わりに通知が計器を兼ねる: 当たり / 初回 / 最後の通知から 7 日無音の週次
   （処理数と最高値）/ 失敗（1 日 1 回まで）を `scripts/notify-slack.sh` へ送る。1 回の実行で送るのは多くても
   1 通。届かなかった当たりの行は状態ファイルに残し、次の実行で再送する。
6. 実行ごとに canary を 1 組（通るべき・通ってはいけない）聞く。条件もレポートも自前の固定文にし、ledger の
   文言に依存させない。ずれたら通知する（同 §6）。
7. 全組の生の読み値を `metrics/review-when-watch.jsonl` に残す。RFC-0025 の registry の最小形として、
   model pin（`jev-1.13.0`）、`question_hash`、`condition_sha`、`report_sha`、`met` と `overlap` の生値、
   `threshold`、`hit`、`reason` を持つ。レポート本文は書かない。読み戻し・集計の機構は作らない。
8. Jev のクライアントは `skills/jev-skill-router/scripts/jev_client.py` をファイルパスで読み込んで使い、
   コピーしない。ADR-0074 Decision 8 の Security Review を通した host の固定・redirect の拒否・キーの解決を
   そのまま使うため。
9. 外へ出るもの: TypeSafe へは条件の本文、レポートのファイル名、本文の先頭 20,000 字。Slack へは条件 ID と題、
   Slack の記法を無害化したファイル名、数値だけ。vault ノートの送信を許容するかは著者の判断で、本 ADR の
   起票時点では未確認 — 著者が plist を登録した時点で許容として確定する。

## Review-when

- ログの `hit` 行が 20 に達した、または `pair` 行が 2,000 に達した → 著者が当たりの当否を読み、閾値と質問文を
  見直す（変えたら本 ADR に注記し、`question_hash` の違う行は別の分布として数える）。20 / 2,000 は置き値
- 当たりの通知が 4 週続けて「読んでも見直しに至らない」 → 閾値を上げるか質問文を直す。8 週続けて当たりが 0 で
  週次の最高値が 0.3 未満 → 条件の多くが外部ニュースで満たせない形か、daily-research の範囲外。対象を外部の
  出来事を待つ条件に絞るか、job を外す
- canary が 3 回続けてずれる → launchd から外し、質問文と state を直してから戻す
- 週次の通知で処理レポート 0 本が 2 週続く → jrp が止まったか出力の置き場所・形式が変わった。入力を
  直すか job を外す
- jrp の起動時刻・所要・出力先・env ファイルの場所が変わる → plist の時刻と wrapper を合わせる。Mac が 05:00 に
  眠っていて起床時に両方が走り、この job が先に終わる日が続く（当たりが 1 日遅れる）→ jrp run の終わりから
  この job を呼ぶ形に移す
- macOS が launchd 配下の bash にも iCloud を開かせなくなる → wrapper の stage も jrp と同じく止まるので、
  jrp 側の対処に合わせる
- TypeSafe が `jev-1.13.0` を廃止する、または料金・保持ポリシーを変える → pin の更新と送信範囲の再判断
- substrate か daily-research が条件とニュースの照合を持つ → job を外す（Scaffold Dissolution の downward）

## Alternatives Considered

- **shadow から入る（ADR-0074 の型）**: 却下。著者の指示。shadow のログは読まれなければ計器にならず、
  回っていること自体が忘れられる。通知の側に初回・週次・失敗を持たせ、同じ生の読み値はログに残す
- **1 日 2 回起動する**（当初案、08:40 / 20:40）: 却下。jrp は朝 1 回しか書かないので、2 回目は canary を聞くだけの
  空振りになる（著者の指摘、2026-09-25）
- **jrp run の最後から呼ぶ**（時刻の推測が要らない）: 未決 — 別 repo の wrapper を変える必要がある。再訪条件は
  Review-when の 3 項目目
- **LLM（Claude）に毎日照合させる**: 却下。条件 53 本 × レポート数の照合を Max 枠で払うことになり、
  RFC-0024 の動機（判定を枠の外へ逃がす）と逆になる
- **条件を外部の出来事を待つものに前処理で絞る**（Choice で条件を分類）: 未決 — 再訪条件: 週次の最高値が
  内部の出来事を待つ条件（「ADR-0049 が supersede された時」等）ばかりになったとき
- **Score で段階を聞く**: 今は採らない。wire format を一次確認できず、同じ段は Choice で表せる。再訪条件:
  Score の書式を実 API で確かめたとき
- **jev_client をコピーする**: 却下。security review を通したコードの二重化は drift する

## Consequences

- 外部の出来事を待つ review-when が、気づかれずに過ぎることが減る。当たりの通知は見直しの入口で、見直し
  そのものは著者が決める
- 全組の読み値が残るので、閾値を後から自分のデータで引ける（RFC-0025 の要求の一部を先に満たす）
- vault ノートを外へ送る経路が 1 本増える。送る範囲はレポート本文の先頭 20,000 字に限り、Slack には本文を
  出さない
- Slack の通知が週 1 通以上増える。閾値が未較正なので、初期の当たりには外れが混じる
- launchd の job が 1 本増える。取り消しは `launchctl bootout`、plist と `skills/review-when-watch/` の削除
- ノートは vault と stage（`~/.cache/review-when-watch/stage/`）の 2 か所に置かれる。stage は gitignore 対象の外
  （repo の外）で、rsync `--delete` で vault に合わせる

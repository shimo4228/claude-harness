---
name: review-when-watch
description: >
  launchd が毎朝 06:10（jev-research-pipeline の jrp run の後）に起動する job。jrp が vault の
  daily-research/ に書いた新しいノート 1 本ごとに、この harness の RFC（frontmatter の review-when:）と
  ADR（## Review-when 節）に書かれた見直し条件を TypeSafe Jev に 1 組ずつ聞き、条件を満たしたノートを
  Slack に送る。model からは呼ばない — この文書は運用手引き。
origin: shimo4228
disable-model-invocation: true
user-invocable: false
---

# review-when-watch

RFC と ADR の review-when は「この出来事が起きたら見直す」という条件で、多くは外の世界の出来事
（substrate が skill listing の注入方式を変えた、Zenodo が API を廃止した、など）を待っている。
誰かがニュースに気づかない限り発火しない。この job はその「気づく役」を、安い判定を総当たりで
回すことで引き受ける。判断の記録は [ADR-0080](../../docs/adr/0080-review-when-watch-production-first.md)。

stdlib のみ（Python 3.11+）。Jev の HTTP クライアントは `skills/jev-skill-router/scripts/jev_client.py` を
ファイルパスで読み込んで使う（host の固定・redirect の拒否・キーの解決をそのまま使う）。

## 配線

plist の正本は `scripts/launchd/com.shimomoto.review-when-watch.plist`（毎日 06:10、1 回）。jrp run は毎日
05:00 に始まり約 15 分で終わるので、その後に置いた。Mac が眠っていて両方が起床時にまとめて走り、この job が
先に終わった日は、その日のノートを翌朝拾う（直近 3 日を見るので落ちない）。登録は人間が行う:

```bash
cp ~/.claude/scripts/launchd/com.shimomoto.review-when-watch.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.shimomoto.review-when-watch.plist
launchctl kickstart gui/$(id -u)/com.shimomoto.review-when-watch   # 初回をすぐ回す
```

初回の実行で Slack に「稼働を始めた」が 1 通届けば配線は通っている。外すときは
`launchctl bootout gui/$(id -u)/com.shimomoto.review-when-watch`。

前提:

| もの | 場所 |
|---|---|
| ノート | `<JRP_VAULT_DIR>/daily-research/*_jrp_*.md`。`JRP_VAULT_DIR` は環境変数か jrp の env ファイル（`~/.config/jrp/env`、`JRP_ENV_FILE` で変えられる）から取る。env ファイルは source せず、この 1 値だけを読む |
| API キー | `TYPESAFE_API_KEY` → `~/.config/typesafe/api_key`（jev-skill-router と同じ解決。jrp の env ファイルのキーは使わない） |
| Slack | `scripts/notify-slack.sh`（webhook は `~/.config/wiki-notify/slack-webhook`。届かなければ macOS 通知へ落ちる） |

plist は Python を直接起動しない。`scripts/launchd-watch.sh`（bash）がノートを vault からローカルの stage
（`~/.cache/review-when-watch/stage/`）へ rsync でコピーし、Python には stage だけを読ませる
（`REVIEW_WHEN_REPORTS_DIR`）。vault は iCloud Drive にあり、macOS のプライバシー保護（TCC）は launchd の
`/bin/bash` には開かせるが uv の Python には開かせない — `open()` が見えない許可ダイアログで止まり続ける
（jrp の初回の定期実行が 2026-09-24 にこれで 80 分固まった。jrp の wrapper も同じ方法で避けている）。
vault が見つからないかコピーに失敗したら、wrapper が Slack に「動かせない」を送って止まる。

## 何が届くか

1 回の実行で送るのは多くても 1 通。

| 場面 | 題 |
|---|---|
| `met` が閾値以上の組がある | `review-when: 条件に当たったレポート N 件`（条件 ID・題・レポート名・met・overlap の最頻段） |
| 初回 | `review-when-watch: 稼働を始めた` |
| 当たりなしで最後の通知から 7 日 | `review-when-watch: 今週は当たりなし`（処理したレポート数と、その週の最高値） |
| 失敗（組の失敗・canary のずれ） | `review-when-watch: 失敗`（1 日 1 回まで） |
| 動かせない（config・キー・クライアントが無い） | `review-when-watch: 動かせない`（1 日 1 回まで） |

当たりの通知が Slack に届かなかったときは、その行を状態ファイルの `pending` に残し、次の実行の
通知の先頭に「前回届かなかった分」として付ける。

当たりが届いたら、該当する RFC / ADR の review-when を読み、見直すかどうかを決める。この job は
見直しを始めない。

## 判定

単位は「レポート 1 本 × 条件 1 本」で、1 組 1 request。比べる相手（条件）は `state` に入れる。

- `met`（Noul）— レポートは、条件が待っている出来事が実際に起きたと言っているか。同じ話題・提案・
  予測・噂は「いいえ」。**通知するかはこれだけで決める**（閾値 `MET_THRESHOLD`）
- `overlap`（Choice）— `words_only` / `same_area` / `precursor` / `event`。最下段は「語を共有するだけ」。
  通知の並びと読み手の手がかりにだけ使い、採否には混ぜない

閾値 0.5 は仮置きで、較正していない。変えるのはログを読んでからにし、変えたら ADR-0080 に注記する。
質問文を変えると `question_hash` が変わるので、ログを読むときは同じ hash の行だけを 1 つの分布として数える。

実行ごとに canary を 1 組（通るべきレポートと、語は同じだが通ってはいけないレポート）聞く。条件も
レポートも自前の固定文で、ledger の文言に依存しない。canary がずれたら、閾値より先に質問文と state を疑う。

## ログと状態

- `metrics/review-when-watch.jsonl` — 全組の生の読み値（`met`、`overlap` の分布、`truncated`、
  `model_returned`、`usage`）と、条件・レポートの sha。レポート本文は書かない。canary の行は `kind: canary`
- `metrics/review-when-watch-state.json` — 判定済みのノート（ファイル名で持つ）、最後の通知、未送信の行。
  jrp のノートは書かれた後も変わる（チェックを付ける、翌朝の run が収穫する）ので、中身の sha を鍵にすると
  同じノートを判定し直して当たりを二重に送る。ノートは全組が成功したときだけ判定済みにし、失敗した組は
  次の実行でその組だけやり直す

どちらも gitignore 済み。

## 手動で回す

```bash
bash ~/.claude/skills/review-when-watch/scripts/launchd-watch.sh --dry-run   # 数えるだけ。Jev も Slack も呼ばない
bash ~/.claude/skills/review-when-watch/scripts/launchd-watch.sh --preview   # Jev に聞いて表示するだけ。状態・ログ・Slack に触れない
bash ~/.claude/skills/review-when-watch/scripts/launchd-watch.sh --lookback-days 7 --preview
```

launchd と同じ wrapper を通すので、stage を経由する点も含めて本番と同じ経路を試せる。`--preview` を
付けずに手で回すと、launchd の実行と同じく状態を更新し通知する。

## 外へ出るもの

TypeSafe（`api.typesafe.ai` に固定）へ送るのは、条件の本文（公開 repo にある）と、レポートのファイル名と
本文の先頭 20,000 字。レポートは vault の私用ノートで、公開ソースの要約だが公開物ではない。この送信の
許容は ADR-0080 に記録する。Slack へ送るのは条件 ID と題、レポートのファイル名（Slack の記法を無害化して
120 字まで）、数値だけで、レポート本文は送らない。

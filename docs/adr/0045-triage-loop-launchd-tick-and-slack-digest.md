# ADR-0045: triage loop の timer を session の外（launchd tick）へ、digest は Slack 片方向、答えは session の中だけ

## Status

accepted

## Date

2026-08-19

## Context

著者の依頼（2026-08-19）: `.claude`（harness）と Contemplative Agent の 2 repo で
`task-stocktake` と `task-triage` を適切な頻度で loop させ、判断が要る時は Slack で呼んでほしい。

ADR-0043 と skill `task-triage` は三役（Judge = 常駐 triage セッション、Build = 新 Opus セッション、
Human = 最後のスイッチ）と red line を定め、cadence を「on-demand → 判定が安定したら週 1」とし、
駆動は「repo ごとの常駐 triage セッション内で `CronCreate` / `/loop`、headless 化するときは
digest を file + 通知 1 行に」と書いていた（[ADR-0043](./0043-task-triage-loop-judge-build-human.md)
§Decision 7、skill 旧 "Where the loop lives"）。初回 cycle は 2026-08-17 に手動で回り、
harness は 13→5 open、CA は 28→17 open まで進んだ。

その駆動には穴がある。`CronCreate` は session-only で 7 日で失効し、skill はこれを
「cycle の最後に自己更新して successor を spawn」で補っていたが、reboot / Herdr 再起動 /
自己更新失敗のいずれでも**静かに止まり、外から検知する手段が無い**。通知チャネルも
「digest + 通知 1 行」は予告のみで未実装だった。Slack は harness にも claude.ai connector にも
接続していない。

この Mac の unattended 実行の標準は launchd（`com.moltbook.*` 9 本、
`com.shimomoto.daily-research`、`com.shimo.wiki-refresh` 等）。Slack Incoming Webhook は
既に Obsidian Vault の `scripts/notify.sh` と aeon-shop の `scripts/lib/notify.sh` が
`~/.config/wiki-notify/slack-webhook`（repo 外、パーミッション 600）を共有して使っている。
両者とも**CLI 経路を意図的に持たない** — untrusted データを読む headless LLM が Bash 経由で
任意の body を Slack へ流せると injection の出力経路になるため、通知は LLM でなく呼び出し元の
shell が行う設計になっている。

Herdr CLI の実測: `herdr agent list` は JSON（`name` / `cwd` / `pane_id` / `agent_status`）を返す。
`agent rename` で固定名を付けられる。`agent prompt <target> <text> --wait --until working --timeout`
は受理のみ待てる。非 working な状態から 5 秒以内に状態変化が無いと `agent_prompt_stalled` になり、
これが spawn 直後の初回 prompt flake の実体である（`spawn-session` SKILL.md step 5: 2026-07-25 の
3 回中 1 回失敗）。未フォーカスの tab は `done` に落ち着くため `--until idle` 単独で待ってはいけない
（`skills/herdr/SKILL.md:59` の観測、本日 `--help` では再検証できない挙動）。

CA は土曜 09:00 に `com.moltbook.weekly-pipeline` が走り、packet 締切は 13:30、人間の
`/weekly-gate` も土曜。ADR-0043 は cloud routine を「CA の `.notes/` は gitignored で読めない」
として既に却下している。

`claims.py` は `CLAUDE_PROJECT_DIR=<repo>` を渡せば cross-repo で動く。harness の単一表
`.notes/TASKS.md` は triage セッションが直接読む対象。

## Decision

1. **timer は session の外、executor は session の中、答えは session の中だけ。** launchd が
   定刻に `~/.claude/scripts/triage-tick.sh <repo> <agent-name> "<display>"` を実行する。tick は
   (a) `herdr agent list` で固定名（`triage-harness` / `triage-ca`）または `cwd` 一致かつ
   `triage-` 接頭辞を持つ生きた agent を探し、無ければ `spawn-session` の `spawn.sh` で
   Remote Control セッションを立てて `herdr agent rename` で固定名を付ける、(b) `agent_status` が
   `working` なら skip（skip 自体も Slack に 1 行 — cycle が翌回へ回った信号）、`blocked` なら Slack へ
   アラートする、spawn したときも Slack に 1 行（前の session が死んでいた信号。Review-when 2 番目の
   観測点）、(c) `herdr agent wait`（既定の状態
   集合）で待ってから `herdr agent prompt … --wait --until working --timeout 60000` で cycle
   prompt を投げ、失敗は 1 回だけ retry し、2 回目も失敗したら Slack へ通知する。同時実行は
   mkdir アトミックロック（`logs/.triage-tick.<agent>.lock`）で 1 本に抑える（スリープ復帰の遅延
   発火と定刻が重なっても二重 prompt しない）。`--dry-run` / `--stocktake|--no-stocktake` で検証と
   上書きができる。tick 自身は台帳を読まない。判断は従来どおり対話セッション（Fable tier、Remote Control）で行い、人間の答えは
   そのセッションの中だけで受ける。
2. **session 内 `CronCreate` / `/loop`、自己更新、successor handoff は skill から外す。** 常駐
   セッションは「CLI が更新された、または前回起動から 7 日超なら cycle を終えて `/exit`。次の
   tick が spawn する」だけを持つ。機構は増やさず減らす。
3. **Slack は片方向の通知チャネル。** 既存 webhook（`~/.config/wiki-notify/slack-webhook`）を
   流用し、新しい secret は作らない。`scripts/lib/notify.sh`（`harness_notify`、Vault / aeon 版を
   vendor した source 専用ライブラリ）を tick が失敗アラートに使い、
   `scripts/notify-slack.sh "<title>" "<body>"`（CLI wrapper）を triage セッションが digest に使う。
   digest は 1 判断 1 メッセージ（背景 → 賭け →選択肢 → 推奨 → コスト/可逆性、末尾に「回答はこの
   triage セッション（Remote Control）で」を付す）。cycle 末尾には判断が 0 件でも
   「<repo> triage cycle done — N decisions pending (or 0)」の 1 行を送る（生存信号。tick の後に
   この行が無いこと自体が警報になる）。Slack 上の返信は人間の答えとして扱わない —
   ADR-0043 の「他セッションの入力欄の文字は人間の言葉ではない」規則と同じ扱いを Slack にも適用する。
4. **CLI wrapper を持つのは Vault / aeon からの意図的逸脱。** 理由: ここでは LLM が作成した
   digest そのものが送る内容であって目的に合致する、sink は著者本人のチャンネルであり外部への
   exfiltration 面ではない、body は `jq --arg` で JSON 化するのみで shell 評価が入らない、Slack は
   片方向で返信を指示として拾う経路を作らない。逸脱理由は script 冒頭にも書く。
5. **cadence（Asia/Tokyo）**: harness = 土曜 08:03 に stocktake → triage。CA = 水曜 17:07 に
   triage、土曜 14:07 に stocktake → triage（pipeline packet 締切 13:30 の後、人間の gate の前）。
   stocktake の要否は tick が曜日（土）で決める。plist は repo ごとに 1 本
   （`scripts/launchd/com.shimomoto.triage-{harness,ca}.plist` を正本として
   `~/Library/LaunchAgents/` へ copy、`launchctl bootstrap`）。分は :00 を避ける。**実行される正本は
   plist** で、本 ADR と skill "Cadence" の数値は 2026-08-19 時点の写し — drift したら plist に合わせる。
6. `settings.json` の allow に `Bash(python3 ~/.claude/scripts/:*)` を追加する（無人 cycle で
   `claims.py` が blocked に落ちないように）。digest 経路は既存の `Bash(bash ~/.claude/scripts/:*)`
   （2026-08-19 時点で存在）に乗る。`settings.json` は `.gitignore` で追跡外なので、この allowlist
   の記録は本 ADR だけにある。`logs/`（tick のログ）を `.gitignore` に追加する。
   skill `task-triage` の "Where the loop lives" / "Cadence" / Digest を上記の内容に書き換え、
   `skills/learned/claude-code-headless-automation.md` に第三の形として 1 行追記する。三役・
   red line（無人で merge しない、rules/ADR/hooks に触らない、drop しない、起票しない）は不変。
   ADR-0043 §Decision 7 には日付つき注記を付ける（ADR-0044 の注記規約の初適用、Status は変えない）。

## Review-when

- substrate が「生きた対話セッションへの耐久 scheduled prompt」を native に持ったら（7 日で
  失効しない cron、または gitignored な `.notes/` を読める routine）、tick を downward
  dissolution で溶かす。
- tick が 2 週連続で「session 死亡のため spawn」を記録したら、spawn-session / Herdr の安定性を
  再訪する（観測点: tick が spawn 時に出す Slack 1 行。ログは machine-local で誰も定期的に読まない
  ので、Slack 側で数える）。
- Slack 通知が 2 cycle 連続で読まれない（digest に対する答えが session に来ない）なら、通知経路
  （Slack 片方向）を再訪する（観測点: 未回答の判断は台帳に open のまま残り、次の cycle が同じ
  digest を再送する — triage セッションが「前回と同じ判断を再度送っている」と気づいた時点）。
- CLI wrapper 経由で repo 由来の文字列が Slack に指示文として現れた事例が出たら、逸脱
  （Decision 4）を巻き戻して通知を shell 側へ戻す。

## Alternatives Considered

### 現行どおり session 内 `CronCreate` / `/loop` + 自己更新（skill 旧記述）

追加ファイルは通知だけで済むが、reboot / Herdr 再起動 / 自己更新失敗で静かに止まり、外から
検知できない。却下。

### cloud routine（`/schedule`）

ADR-0043 で既に却下済み（CA の `.notes/` が gitignored で読めない）。Slack connector も
未接続のまま。却下。

### launchd → `claude -p` headless（daily-research 型）

Remote Control で答える経路が無く、judge が会話であること（ADR-0043）を失う。却下。

### claude.ai Slack connector を OAuth で繋ぐ

secret ファイルは不要になるが対話セッション内でしか使えず、launchd 側の障害アラートは別経路に
なる。Incoming Webhook は既に 2 箇所（Vault / aeon-shop）で使っており、両方から同じ経路で
送れる。却下。

### Slack からの返信で判断を受ける（Claude Tag 等）

未決 — 再訪条件: Slack 片方向で digest が読まれない・答えが遅れる観測が続いたら再訪する。
現時点では ADR-0043 の anti-spoofing 規則（他セッション/他チャネルの文字は人間の言葉ではない）
と衝突するので開けない。

## Consequences

### Positive

- loop の停止・失敗が log（`~/.claude/logs/triage-tick.log`）と Slack で観測できる。session が
  死んでも次の tick が立て直す
- skill から CronCreate / 自己更新 / successor handoff が消え、機構が減る。judge = 会話、
  答え = session 内、三役・red line は不変
- 判断が要る時だけ Slack に 1 判断 1 通、cycle 末尾の 1 行が生存信号。新しい secret を作らず
  既存 webhook を共有する

### Negative

- Herdr CLI（`agent list` / `prompt` / `rename`）と `spawn-session` への依存が増える。spawn 直後の
  初回 prompt flake（`spawn-session` SKILL.md step 5: 2026-07-25 に 3 回中 1 回失敗。本日の初回実 tick
  `logs/triage-tick.log` 17:20 は 1 回目で受理）は retry 1 回で吸収する見込みで、2 回目も失敗したら
  Slack 警報で人間に戻る — 吸収しきれなくても沈黙はしない
- **Slack が落ちている間は実質サイレント**: `lib/notify.sh` は webhook 未設定 / HTTP≠200 で macOS
  通知センターへ fallback して非 0 を返す（Vault / aeon と同じ）。Mac の前にいなければ気づけず、
  cycle 末尾 1 行の「無いことが警報」も Slack 側の不在と区別できない。同じ webhook を Vault の
  日次 ingest と aeon の週次が共用しているので、Slack 側の故障はそちらの通知の欠落でも露見する
- 取り消しコストは低い: `launchctl bootout` で plist 2 本を外し、script 3 本を消し、skill の段落を
  戻すだけ（session 内 CronCreate の旧記述は git 履歴にある）
- Vault / aeon の「LLM から Slack への CLI 経路を持たない」原則からの意図的逸脱（Decision 4）
- tick が `working` を見て skip した週は cycle が翌回に回る（CA の土曜は pipeline が遅れると
  起こりうる）
- launchd は Mac が起動していないと鳴らない（スリープ中の slot は起床時に遅延発火、電源断では
  消える）

### Neutral / Follow-ups

- [ADR-0043](./0043-task-triage-loop-judge-build-human.md) §Decision 7 を部分的に弱める（注記で
  表す、supersede しない）。[ADR-0044](./0044-adr-review-when-and-dated-annotation.md) の注記
  規約の初適用
- CA repo 側のファイルは触らない（Herdr セッション名だけ）。CA の `.notes/` handoff に
  「水/土の digest は Slack」を 1 行残すかは任意
- 初回の実 tick（`launchctl kickstart`）で spawn → rename → prompt → Slack の digest まで通ることを
  確認する
- [ADR-0016](./0016-writer-agents-render-not-decide.md)（writer は render 専任）は不変。本 ADR は
  main loop が承認した packet を記録するもので、adr-writer 自身は既存 ADR に触らない

# task-stocktake / task-triage の定期 loop（harness + CA）と Slack 通知

## Context

ADR-0043 と skill `task-triage` は「repo ごとの常駐 triage セッション + Judge / Build / Human の三役」を
定義済みで、初回 cycle は 2026-08-17 に手動で回した（harness 13→5 open、CA 28→17）。cadence は
「on-demand → 判定が安定したら週 1」。著者は今それを**定期 loop に載せ、判断が要る時だけ Slack で
呼ばれたい**。

現状の穴（agent 調査、file:line 確認済み）:
- skill が書く駆動は「常駐セッション内 `CronCreate`（7 日で失効）→ 自己更新で successor を spawn」
  （`skills/task-triage/SKILL.md:200-240`）。reboot / Herdr 再起動 / 自己更新失敗で**静かに止まり、
  検知手段が無い**
- 判断の依頼は会話内のみ。「digest + 通知 1 行」は skill:236-238 / ADR-0043:57 に予告されているだけで
  **通知チャネルは未実装**。Slack は harness にも claude.ai connector にも未接続
- `claims.py` は `CLAUDE_PROJECT_DIR=<repo>` で cross-repo 動作する（`--root` は無い）。harness の
  単一表 `.notes/TASKS.md` は programmatic reader が無く、triage が直接読む（現状どおり）
- launchd がこの Mac の unattended 標準（`com.moltbook.*` 9 本、`com.shimomoto.daily-research` 等）。
  CA は土 09:00 pipeline、packet 締切 13:30、人間の `/weekly-gate` が土曜

決定（ユーザー回答済み）: **Slack = Incoming Webhook**、**駆動 = launchd timer + 常駐セッション executor**、
cadence = harness 土 08:00 / CA 水 17:00 + 土 14:00。

## 設計原則

- **timer は session の外、executor は session の中、答えは session の中だけ。** launchd が定刻に
  `herdr agent prompt` で cycle を投げる。判断（Judge）は従来どおり対話セッション（Fable tier、
  Remote Control on）。Slack は**片方向**の通知 — Slack 上の返信は人間の答えとして扱わない
  （ADR-0043 の anti-spoofing 規則をそのまま適用）。答えは triage セッション（iPhone Remote Control）
- **機構は減らす。** CronCreate + 自己更新 + successor handoff を skill から外し、「session が無ければ
  次の tick が spawn する」に畳む。tick は台帳を読まない（ADR-0043 / CA ADR-0095: 台帳を parse する
  script を足さない）
- 三役・red line（無人で merge しない、rules/ADR/hooks に触らない、drop しない、起票しない）は不変
- 通知は最小: 判断 1 件につき Slack 1 通（1 判断 1 メッセージ、既定順: 背景→賭け→選択肢→推奨→コスト）
  + cycle 末尾に 1 行の締め（判断 0 件でも「cycle done — 0 decisions」を出す = 生存信号）。tick 自身は
  **失敗時だけ** Slack する（session 起動失敗 / prompt 失敗 / blocked / 前 cycle が working で skip）

## 変更

### 1. Slack 経路 — 既存 webhook を流用（新 secret は作らない）
- 正本は Obsidian Vault `scripts/notify.sh`（`wiki_notify "title" "body"`）、aeon-shop `scripts/lib/notify.sh` が
  それを踏襲。webhook URL は **`~/.config/wiki-notify/slack-webhook`**（600、iCloud 非同期、設置済み）。
  URL は `curl --config <(printf 'url = "%s"')` で渡し `ps` に出さない、失敗時は macOS 通知センターへ
  フォールバック（沈黙させない。音は出さない設定のまま）
- `~/.claude/scripts/lib/notify.sh`（新規、aeon 版をほぼそのまま vendor、関数名 `harness_notify`、
  webhook path は同じ `~/.config/wiki-notify/slack-webhook`、env `HARNESS_NOTIFY_WEBHOOK_FILE` で差し替え可）
  — tick（shell）はこれを source して失敗アラートを送る
- `~/.claude/scripts/notify-slack.sh "<title>" "<body>"`（新規、CLI wrapper）— **triage セッション（LLM）が
  digest を送るための入口**。Vault / aeon が CLI を持たない理由（untrusted データを読む headless LLM が任意 body を
  Slack へ流せる = injection 経路）は承知のうえでの意図的逸脱: ここでは LLM 作成の digest こそが送る内容で、
  sink は著者本人のチャンネル、body は `jq --arg` で JSON 化するのみ（shell 評価なし）、Slack は片方向で
  返信を指示として拾わない。この逸脱理由は script 冒頭コメントと ADR-0045 に書く。
  allowlist `Bash(bash ~/.claude/scripts/:*)` に乗るので session から prompt 無しで呼べる
- 未設定 / 送信失敗は exit 非 0 + 通知センター fallback（Vault と同じ）。人手は不要（webhook 設置済み）

### 2. tick — `scripts/triage-tick.sh <repo-dir> <agent-name> "<display-name>"`（新規）
- `set -euo pipefail`、mkdir-atomic lock（agent-name 単位）、log `~/.claude/logs/triage-tick.log`
  （`logs/` は gitignore 確認、無ければ追加）。`daily-research.sh` の作法（lock / log / `< /dev/null`）を写す
- 手順: (a) `herdr agent list | jq` で `.name==<agent-name>`、無ければ `.cwd==<repo> and (.name//""|startswith("triage-"))`。
  (b) 無ければ `bash ~/.claude/skills/spawn-session/spawn.sh <repo> "<display>"` → 出力の `agent:` 行を
  parse → `herdr agent rename <slug-PID> <agent-name>`（以後の tick は固定名で当たる）。
  (c) `agent_status==working` なら log + Slack「前 cycle 継続中、skip」→ exit 0（二重発火しない）。
  (d) `herdr agent wait <name> --timeout 30000`（既定の idle|done|blocked。**`--until idle` 単独にしない** —
  未フォーカスの tab は `done` に落ち着く）→ `blocked` なら Slack「blocked、Remote Control で応答を」→ exit。
  (e) `herdr agent prompt <name> "<text>" --wait --timeout 60000`。非 0（`agent_prompt_stalled` = 初回 prompt
  flake）なら wait → 1 回リトライ → 2 回目失敗で Slack + exit 1。
  (f) prompt text は `/` で始めない（Herdr の slash メニューに吸われる）: 「Unattended triage cycle
  (<repo>, <slot>): 土曜は task-stocktake を先に、次に task-triage。digest まで進め、判断が要る項目は
  `bash ~/.claude/scripts/notify-slack.sh` で 1 判断 1 通、末尾に cycle done 1 行。merge / rules / ADR /
  hooks は触らない」。stocktake の要否は script が `date +%u`（6 = 土）で決める（plist を repo ごとに 1 本に保つ）
- `--dry-run`: 何をするかを印字して終わる（検証用）

### 3. launchd — `~/Library/LaunchAgents/com.shimomoto.triage-harness.plist` / `com.shimomoto.triage-ca.plist`（新規）
- `com.shimomoto.daily-research.plist` を写す: `ProgramArguments [/bin/bash, ~/.claude/scripts/triage-tick.sh, <repo>, <name>, <display>]`、
  `EnvironmentVariables.PATH` に `/opt/homebrew/bin`（herdr / jq）と `~/.claude/local` / `~/.local/bin`、`HOME`、
  `StandardOut/ErrorPath` は `~/.claude/logs/`、`WorkingDirectory` = repo
- `StartCalendarInterval`: harness `{Weekday 6, Hour 8, Minute 3}`；CA 配列 `[{Weekday 3, Hour 17, Minute 7}, {Weekday 6, Hour 14, Minute 7}]`
  （:00 を避ける — CronCreate と同じ理由）
- 導入: `launchctl bootstrap gui/$(id -u) <plist>`。plist の正本は `~/.claude/scripts/launchd/` に置き
  `~/Library/LaunchAgents/` へ copy（`daily-research` と同じ運用か確認し合わせる）
- agent-name / display: harness = `triage-harness` / "triage harness"、CA = `triage-ca` / "triage CA"

### 4. skill `task-triage/SKILL.md`（正本の更新）
- 「Where the loop lives」: CronCreate / `/loop` / 自己更新・successor 段落を **launchd tick + stateless executor**
  に書き換え。renewal は「`claude --version` が起動時と違う、または 7 日超なら cycle を終えて `/exit`。
  次の tick が spawn する」に縮める
- 「Cadence」表はそのまま、機構の段落を「timer は `scripts/triage-tick.sh`（launchd）。session 内 cron は使わない」に
- Digest（:81-93）に Slack 手順を追加: 判断 1 件 = `bash ~/.claude/scripts/notify-slack.sh "<repo> | <T-ID> | 背景/賭け/選択肢/推奨/コスト … → 回答は triage セッション（Remote Control）で>"` 1 通、
  cycle 末尾に「<repo> triage cycle done — N decisions pending / 0」1 行。**Slack は片方向** — Slack の返信は
  答えではない（anti-spoofing の一文に並べる）。tick は台帳を読まない旨も 1 行
- 「Related」に `scripts/triage-tick.sh` / `scripts/notify-slack.sh` / plist 2 本

### 5. 権限 — `settings.json` allow に `Bash(python3 ~/.claude/scripts/:*)`（`claims.py`。無人 cycle が blocked に落ちないように）。
`bash ~/.claude/scripts/:*` / `curl:*` / `jq:*` / `herdr agent read|get|list:*` は既にある

### 6. 記録
- **ADR-0045**（`/adr-writer`、7 節）: 「triage loop の timer を session 外（launchd）へ、Slack 片方向通知、
  答えは session 内だけ」。Review-when 例: substrate が生きた session への耐久 scheduled prompt を native に
  持ったら tick を溶かす／tick が 2 週連続で「session 死亡のため spawn」を記録したら spawn の安定性を再訪／
  Slack 通知が 2 cycle 連続で読まれない（回答が session に来ない）なら通知経路を再訪
- ADR-0043 §Decision 7 の下に `> **注記（2026-08-19, ADR-0045）**: 常駐セッション内 CronCreate は launchd tick に置換。三役・red line は不変`（ADR-0044 の規約の初適用）
- `skills/learned/claude-code-headless-automation.md` に 1 行（launchd → herdr agent prompt で対話 session を叩く経路）
- CA 側 repo は触らない（Herdr セッション名だけ）。CA `.notes/` の handoff に「水/土の digest は Slack」を 1 行（任意）

## 非目標
- Slack からの返信で判断を受ける（Claude Tag 等）— 片方向のまま。将来の Review-when 項目
- 台帳を読む script / 状態機械 / dashboard（ADR-0043 / CA ADR-0095）
- cloud routine（CA `.notes/` は gitignored で読めない — ADR-0043 で却下済み）

## Verification
1. `bash ~/.claude/scripts/notify-slack.sh "triage test" "hello"` → Slack に届く（既存 webhook。ファイルを一時退避して再実行 → 通知センター fallback + exit 非 0）
2. `bash ~/.claude/scripts/triage-tick.sh ~/.claude triage-harness "triage harness" --dry-run` → 手順が印字される
3. 実 tick: `launchctl kickstart -k gui/$(id -u)/com.shimomoto.triage-harness` → `~/.claude/logs/triage-tick.log` に spawn / rename / prompt OK、`herdr agent list` に `triage-harness`、`herdr agent read triage-harness --lines 40` で cycle が走っている、Slack に digest（or「cycle done — 0 decisions」）
4. `launchctl print gui/$(id -u)/com.shimomoto.triage-harness` / `…triage-ca` に次回発火時刻
5. 障害系: triage セッションを `/exit` して kickstart → tick が spawn する。session を working 中に kickstart → skip + Slack
6. `python3 scripts/hooks/harness_lint.py`、`bats tests/`、`.claude/verify.sh` → pass（新 script は hooks/ ではないので lint 対象外だが、rules 内の path 参照を足す場合は実在チェックが効く）
7. `git status` で `logs/` が untracked に出ないこと（gitignore 効いている）。webhook ファイルは repo 外なので secret scan 対象外

## 実装時の注意
- spawn 直後の初回 `herdr agent prompt` は flaky（2/3）。`--wait --timeout` の非 0 で検知し 1 回だけ retry
- `foreground_cwd` は当てにならない。`.cwd` で照合
- 秘密は log にも Slack にも出さない。`set -x` 禁止
- CA の土曜 14:00 は pipeline packet 締切 13:30 の後 — pipeline が遅れて working 中なら tick は skip する設計で良い（翌週に回る。Slack で気づける）

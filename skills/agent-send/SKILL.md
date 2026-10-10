---
name: agent-send
description: "Send a prompt to an agent running in a Herdr pane and confirm it landed, or wait until its work is done. Use when handing a task to another session or Codex pane (このセッションに投げて). For other pane operations, use herdr."
user-invocable: true
origin: shimo4228
---

# agent-send

Herdr pane で動く agent（Claude Code / Codex など）へ指示を送り、**届いたか**と**終わったか**を
1 行と exit code で返す。script は `${CLAUDE_SKILL_DIR}/agent-send.sh`。

Herdr は turn を追跡せず、agent の状態を画面から検出する。そのため `herdr agent prompt --wait`
（`--until` なし）は turn の**完了**まで待ち、長い作業では `timeout` になる。届いたかどうかは
分からない。agent-send は、届いたかを「turn の開始を観測した」で判定し、完了は別のコマンドで待つ。

## 送る

```bash
${CLAUDE_SKILL_DIR}/agent-send.sh prompt <target> --file packet.md   # または --text "…"
```

- `<target>` は agent 名・pane ID・表示名（spawn-session の tab label、例 `AAP/release`）の
  どれでもよい。内部で pane ID に固定する
- 相手が working なら終わるまで待ってから送る（既定 10 分、`--busy-timeout MS`）。作業中に送った
  指示は queue に入って同じ turn に吸収され、届いたことを証明できない
- 本文は 1 回しか送らない。失敗しても再送しない — `timeout` や `stalled` は「届いていない」の
  証拠にならず、再送は二重送信になる
- 例外は `--retry-unseen`（spawn.sh が最初の指示に付ける）。起動直後の未 focus の pane では、指示が
  成功を装わずに消えることがある（herdr #4537。2026-10-10 に 0.9.3 の macOS で 2 回中 1 回）。宛先が
  Claude Code で transcript がまだ無い（一度もメッセージを処理していない）ときに限り、1 回だけ送り直す

| stdout の `result=` | exit | 意味と次の手 |
|---|---|---|
| `landed`（`via=working` / `seq` / `status` / `transcript`） | 0 | 届いた。完了を待つなら下の wait |
| `accepted via=command` | 0 | `/effort` などの slash command。turn は起きない |
| `typed` | 2 | 本文が入力欄に残り、Enter が入っていない。画面（stderr）を読み、人間の書きかけでなければ `herdr agent send-keys <pane> enter` を自分で判断する |
| `no_evidence` | 2 | 届いた証拠が無い。画面を読んでから決める。再送する前に transcript か画面で本文の有無を見る |
| `not_found` | 2 | 宛先が無い。`herdr agent list` で名前と cwd を確かめる |
| `blocked` | 3 | 承認か質問の dialog で止まっている。画面を読み、人間に渡す |
| `busy` | 4 | 期限内に作業が終わらなかった。送っていない |
| preflight 失敗（`herdr_unreachable` / `server_down` / `incompatible` / `server_too_old`） | 5 | Herdr に届かない・止まっている・版ずれ。stderr の理由を人間に渡す |

Enter を自動で押さないのは、blocked の検出が dialog の描画から 0.3 秒ほど遅れ、承認を押しうる
ため（herdr #4764）。

## 終わりを待つ

```bash
${CLAUDE_SKILL_DIR}/agent-send.sh wait <target> --timeout 3600000 \
  --done-if 'git -C <worktree> log -1 --format=%s | grep -q "<task>"'
```

**Bash tool の `run_in_background: true` で起動する。** 終わると通知が届くので、その間に画面を
読みに行かない。

- 完了は、settled（idle か done）が続けて観測されること（Claude は 2 回、他は 3 回。間隔 30 秒）と、
  `--done-if` の command が真であること
- 状態の読み方
  - Claude: `claude agents --json` の status（Claude Code 自身の報告。背景 subagent の実行中、
    Herdr の `done` 中も `busy` を返した — 2026-10-10 実測）
  - それ以外: Herdr の画面検出
- 画面検出には偽の idle がある（背景 subagent の実行中など）。成果物で判定できるときは `--done-if` を付ける
  - build の完了: commit が branch に現れた
  - 画像生成の完了: 出力ファイルがある
  - 背景 process の終了: `! pgrep -f '<pattern>'`
- exit 0 `done`: 成果物を読む / 3 `blocked`: 画面を読み、人間に渡す / 4 `timeout`: 画面と成果物を
  見て、延長か打ち切りを決める

## Herdr の版

`agent-send.sh preflight`（prompt の前にも自動で走る）は、server と client の互換性が無いとき、
または server が 0.9.0 より古いときに止まる。server が client より古いだけなら警告を出す。
警告と停止の理由は人間に渡す — server の再起動は全 pane の turn を止めるので、時刻は人間が決める
（brew 版は `herdr update --handoff` を使えず、再起動が要る）。`~/.claude/skills/herdr/SKILL.md` のコピーが
`herdr --skill` の出力と違うときも警告する（origin 行を残して置き換える）。

## 前提

- 宛先は、この session が起こした pane（spawn-session の出力の `herdr:` 行）か、人間が指名した
  pane に限る。それ以外の session へは送らない — 人間が操作中の会話に割り込むため
- 送信は Herdr への委譲に当たる。委譲してよい条件は環境の境界 rule が決める（著者の環境では
  `rules/common/boundary.md`: 明示指示が要る。spawn-session で自分が起こした pane へは `HERDR_ENV=1`
  無しで送ってよく、それ以外の pane へは `HERDR_ENV=1` も要る）
- `herdr`（server 0.9.0 以上）と `jq`
- 宛先が Claude Code のときは `claude` CLI（状態の読み取りに使う）
- テスト: `${CLAUDE_SKILL_DIR}/tests/agent-send.bats`（偽の `herdr` / `claude` を `tests/bin/` に置く）

---
name: growth-astra
description: "Astra — GitHub follower campaign の北極星（`.growth/NORTH_STAR.md`）を書く役。初回は新規設定、2 回目以降は状況に合わせて修正する。Use when — campaign 開始時の initial pass、growth-fable からの escalation、著者が「Astra を回して」「北極星を見直して」と言ったとき、/growth-astra。NOT for — 施策の立案と実行（→ growth-fable）。"
user-invocable: true
origin: shimo4228
---

# growth-astra — 北極星を書く

著者の目標（現 campaign: GitHub followers を 2026-12-07 までに 10,000）に対し、
`.growth/NORTH_STAR.md` を書く唯一の役。初回は新規に設定し、2 回目以降は
`.growth/EXPERIMENTS.md` と `.growth/SNAPSHOT.json` が示す状況に合わせて修正する。
中身の形式は決めない — 到達に必要だと判断したことを、Fable が施策を考えられる粒度で書く。

公開・評判に関わる action は著者が実行する（Astra も Fable も草稿で止める。境界は rule `boundary.md`）。

`SNAPSHOT.json` が無い / 2 日より古ければ先に collector を回す:
`uv run --project ~/.claude/skills/growth-fable python ~/.claude/skills/growth-fable/scripts/collect_snapshot.py --user shimo4228 --out .growth/SNAPSHOT.json --pull`

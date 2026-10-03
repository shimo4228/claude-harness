---
name: growth-astra
description: "Astra — follower campaign window（instrument）の北極星（`.growth/NORTH_STAR.md`）を書く役。初回は新規設定、2 回目以降は状況に合わせて修正する。Use when — campaign 開始時の initial pass、growth-fable からの escalation、著者が「Astra を回して」「北極星を見直して」と言ったとき、/growth-astra。NOT for — 施策の立案と実行（→ growth-fable）。"
user-invocable: true
origin: shimo4228
---

# growth-astra — 北極星を書く

campaign window（2026-09-08 → 2026-12-07）は結果の数値を追わず、何が実際に人を動かすかを
事前登録した実験で測る instrument（personal-branding ADR-0005）。数値目標は行為（告知率・
実質コメント・PR・release）に置き、結果（面ごとのフォロワー数）は personal-branding ADR-0003
Decision 4 の判定規則で読む。層別の操舵範囲の正本は personal-branding `docs/strategy.md` §10。

`.growth/NORTH_STAR.md`（cwd = `~/MyAI_Lab/growth`）を書く唯一の役。初回は新規に設定し、
2 回目以降は `.growth/EXPERIMENTS.md` と `.growth/SNAPSHOT.json` が示す状況に合わせて修正する。
北極星が持つのは、測る問い・事前登録する実験の候補（同時 active 最大 2）・行為の目標値・
window 終了時に閉じる条件。数値は内容（記事の主張・構成・何を作るか）を操舵しない。

公開・評判に関わる action は著者が実行する（Astra も Fable も草稿で止める。境界は rule `boundary.md`）。

`SNAPSHOT.json` が無い / 2 日より古ければ先に collector を回す:
`uv run --project ~/.claude/skills/growth-fable python ~/.claude/skills/growth-fable/scripts/collect_snapshot.py --user shimo4228 --out .growth/SNAPSHOT.json --pull`

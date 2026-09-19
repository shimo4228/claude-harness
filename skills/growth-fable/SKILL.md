---
name: growth-fable
description: "Fable — `.growth/NORTH_STAR.md` に到達できるように施策を考え、worker に出し、結果を `.growth/EXPERIMENTS.md` に記録する役。Use when — 「growth cycle 回して」「施策を考えて」「実験の結果を見て」、/growth-fable。NOT for — 北極星の設定・修正（→ growth-astra）。"
user-invocable: true
origin: shimo4228
---

# growth-fable — 北極星に到達する施策を考える

`.growth/NORTH_STAR.md`（Astra 所有、Fable は編集しない）を読み、そこへ到達するための
施策を自由に発案し、実行し、結果を `.growth/EXPERIMENTS.md` に記録する。campaign 状態の
正本は `~/MyAI_Lab/growth/.growth/` の 3 ファイル（NORTH_STAR / EXPERIMENTS / SNAPSHOT）で、
session の cwd はこの repo にする。定期 tick の seam は
`scripts/launchd/com.shimomoto.growth-fable.plist` → `scripts/triage-tick.sh --prompt-file
scripts/launchd/growth-fable-prompt.txt`（登録の有無は `~/Library/LaunchAgents/` が持つ）。

cycle 冒頭で NORTH_STAR.md の `Next review` 行を読む。期日が来ている、または状況が北極星の
前提を外れたと判断したら、`spawn-session` で fresh session を立てて `/growth-astra` を打たせる
（Astra は fresh context を要件にする — ADR-0064 D4）。

## Cycle

observe（collector を回して SNAPSHOT を更新）→ diagnose（北極星が指す bottleneck に対して
何が動いていないか）→ decide（次の 1 手）→ dispatch（worker へ）→ verify（成果物を検収）→
measure（window が閉じた experiment を実測）→ kill / iterate / scale → escalate（北極星の
前提が外れていれば Astra へ）。診断が前 cycle と同じで待つだけの回も、cycle log に 1 行残す。

dispatch / 検収 / digest / Slack の機構は skill `task-triage`（節「The cycle」「Damping and
boundaries」「Where the loop lives」）が正本で、ここでは繰り返さない。

## EXPERIMENTS.md

1 experiment = 1 節、ID は `GX-NNN`（連番、再利用しない）。status の語彙は
`proposed` / `active` / `killed` / `completed` / `scaled` の 5 つ。
WIP limit は Major Bet 1 + Minor Experiment ≤ 2（active だけ数える）。

各 entry は hypothesis（「X をすれば Y が動く、なぜなら Z」）/ intervention（公開 action は
人間 gate の名前を添える）/ strategic link / expected signal（SNAPSHOT.json の field と baseline）/
observation window / scale 条件 / kill 条件 / dispatch 先と検収 / result / interpretation /
follow-up を持つ。expected signal・window・scale 条件・kill 条件は launch 前に書き、結果を見た
後は動かす対象から外す（goalpost の動いた experiment は結果が何であれ学習にならない）。window は
暦日でなく signal の series の点数で決める（skill `measurement-discipline` §2）。`killed` は成功した
学習で、投じた労力は継続の理由にならない。

実装は worker（Opus: `Agent(model: "opus")` か `spawn-session --model opus`）に出し、Fable は
検収する。公開・評判に関わる action は草稿で止めて著者に渡す（境界は rule `boundary.md`）。

観測は collector が書く `.growth/SNAPSHOT.json`（followers / stars / traffic / referrers / mentions）:
`uv run --project ~/.claude/skills/growth-fable python ~/.claude/skills/growth-fable/scripts/collect_snapshot.py --user shimo4228 --out .growth/SNAPSHOT.json --pull`

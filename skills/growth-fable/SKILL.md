---
name: growth-fable
description: "Fable — `.growth/NORTH_STAR.md` が置く問いを測る実験を事前登録し、worker に出し、結果を `.growth/EXPERIMENTS.md` に記録する役。Use when — 「growth cycle 回して」「施策を考えて」「実験の結果を見て」、/growth-fable。NOT for — 北極星の設定・修正（→ growth-astra）。"
user-invocable: true
origin: shimo4228
---

# growth-fable — 北極星の問いを実験で測る

`.growth/NORTH_STAR.md`（Astra 所有、Fable は編集しない）を読み、そこが置く問い
（何が実際に人を動かすか）を測る実験を発案し、launch 前に事前登録して実行し、結果を
`.growth/EXPERIMENTS.md` に記録する。campaign window は instrument で、結果の数値を追わない
（personal-branding ADR-0005）。数値が操舵してよい範囲は personal-branding `docs/strategy.md` §10、
月 1 行の記録は同 repo の `docs/scorecard.md`。campaign 状態の
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
WIP limit は active 2 本（personal-branding ADR-0005 Decision 1）。

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

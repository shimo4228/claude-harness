kind: internal
# harness-stocktake と native（`/doctor`・`/doctor prompt-audit`・`/skill-doctor -p`）の項目別比較

as-of: 2026-11-01、Claude Code 2.1.316。plan [enumerated-petting-beaver](../enumerated-petting-beaver.md) Stage 0 手順 1。

## 結論

- **harness-stocktake の非 Keep 74 件のうち、native の実出力が同じ対処まで拾ったのは 0 件、部分 26 件、拾わない 48 件（65%）。**
  native の検査範囲として拾える種類か（機能）で数えても、拾われる 7 / 部分 20 / 拾われない 47（64%）。plan の判定「拾われない項目が
  非 Keep の半分未満なら位置取りを『`/doctor` の後に回す』へ下げる」には当たらない — 位置取り「`/doctor` の上の層」は維持
- 拾われない 48 件は source に偏る: assets 22/23、hooks 11/12、docs 3/4、distill 2/2。skills は 24 件中 18 件が「部分」（native は
  「未使用」と出すが、stocktake の Improve / Update の中身 — 古い参照・矛盾・置き換え — は出さない）。差別化の主張はこの 4 source
  （設定・script・metrics の持ち主の消失、hooks の配線とテスト、ADR / README の drift、rule の蒸留）に置ける
- **逆向きも大きい。** native の指摘のうち harness 自体に関する 28 件を stocktake の 192 項目と突き合わせると、拾っている 2 / 部分 4 /
  拾っていない 22。native だけが出すもの: plugin・MCP・synced skill の未使用（使用履歴が要る）、hook の実測遅延、`prompt-audit` の
  書き方の古さ（固定の数値上限・圧をかける強調・経緯の記述・存在しない tool 契約）。**二つは包含関係でなく補完関係** —
  README と記事は「`/doctor` を先に回し、その後に残るものを見る」と書く（plan の代理決定 3 と同じ向き）。「`/doctor` の代わり」とは書けない
- 一致しない点: native は使用履歴から skill を「未使用 → off」と勧め、stocktake は同じ skill の多くを Keep にした（例: 窓 10 日で未使用の
  learn-eval・readme-writer・skill-creator を `/doctor` は off に挙げ、自分で「累計では多い」と注記した）。使用頻度だけの判定と中身の
  判定は答えが割れる。stocktake の Phase 1 で `/skill-doctor -p` の出力を evidence として読む（plan の代理決定 3）

## 方法

- **対象**: 2026-10-31 の初回全体実行の 192 項目（`~/.claude/.notes/stocktake/2026-10-31/items-all.json`）。report の `base` は
  `c26e728`。その後 apply が main に入ったので、native は `git archive c26e728` で取り出した snapshot に当てた
- **native の実行**: snapshot を project scope として見せる fixture（空 dir に `.claude/{skills,agents,rules,hooks}` と `CLAUDE.md` を
  snapshot への symlink で置く）を cwd にして `claude -p "/doctor"`・`claude -p "/doctor prompt-audit"`・`claude -p "/skill-doctor -p"`
  （`--output-format json`）。別の `CLAUDE_CONFIG_DIR` は未ログインになるため user scope は live の `~/.claude`（apply 後）のまま。
  使用履歴は live の transcript（直近 50 session、10 日）
- **費用と時間**（`total_cost_usd` は API 換算、subscription で実行）: `/doctor` $5.02・8.5 分（model は既定の claude-fable-5-1）、
  `prompt-audit` $20.44・15.0 分、`/skill-doctor -p` $0・即時（表を出すだけ）
- **分類**: `claude -p --model opus --tools ""`（hooks・user CLAUDE.md を外した fresh context）に 3 本の出力全文と項目（id・target・verdict・
  reason 400 字・change 250 字）を 28 件ずつ渡し、項目ごとに 2 列を JSON schema で返させた（7 call、計 $2.51）
  - **実測**: 今回の native 出力がその項目を出したか。拾われる = 同じ target（または明示的にそれを含む集合）で同じ種類の問題・同じ対処 /
    部分 = target か問題のどちらかだけ、または違う対処 / 拾われない
  - **機能**: 今回の出力に関係なく、native が文書化・観測された検査範囲（未使用 extension、使用回数、context cost、CLAUDE.md の導出可能
    部分・重複、古い path / command、矛盾、古い model 向けの書き方、遅い hook、settings の parse、名前の重複、permission の拒否）で
    その種類を見るか
- **逆向き**: 同じ 3 本の出力から行動を勧める指摘を 1 件ずつ列挙させ、fixture 自体（symlink した snapshot が `~/.claude` を影にする、
  CLAUDE.md の写し）と install 環境（nvm の古い npm 版）を除いた 28 件を 192 項目と照合（$0.84）

## 限界

- 分類は LLM の判定で、人が全件を確かめていない。抜き取り 8 件は妥当だった（例: `hooks-31` metrics の書き手が消えた jsonl = 拾われない、
  `skills-36` repair-discipline の主張と hook のずれ = 部分、native は未使用としか言わない）
- native は fixture の snapshot と live の `~/.claude` を両方見ているので、指摘の一部は fixture 起因（逆向きの集計からは除外）。
  `/doctor` の使用履歴は 2026-10-21〜31 の窓で、10-31 時点の snapshot とほぼ同時期
- n = 1（著者の harness）。他人の harness で native と比べるのは Stage 3（plan）

## 192 項目

列: 実測 = 今回の native 出力、機能 = native の検査範囲。verdict は 28 字で切っている。

| # | id | source | target | verdict | 実測 | 機能 | native の該当（抜粋） |
|---|---|---|---|---|---|---|---|
| 1 | skills-64 | skills | `skills/synced` | Retire | 部分 | 部分 | 12 skills synced from claude.ai loaded but never invoked... turn them off on cla |
| 2 | hooks-11 | hooks | `hooks/docs-prewrite.sh` | Retire | 拾われない | 部分 | - |
| 3 | hooks-29 | hooks | `metrics/ask-one-question.jsonl` | Retire | 拾われない | 拾われない | - |
| 4 | hooks-30 | hooks | `metrics/costs.jsonl` | Retire | 拾われない | 拾われない | - |
| 5 | hooks-31 | hooks | `metrics/research-gate.jsonl` | Retire | 拾われない | 拾われない | - |
| 6 | assets-01 | assets | `scripts/claw.js` | Retire | 拾われない | 拾われない | - |
| 7 | assets-02 | assets | `scripts/setup-package-manager.js` | Retire | 拾われない | 拾われない | - |
| 8 | assets-03 | assets | `scripts/lib/package-manager.js` | Retire | 拾われない | 拾われない | - |
| 9 | assets-04 | assets | `scripts/lib/utils.js` | Retire | 拾われない | 拾われない | - |
| 10 | assets-05 | assets | `scripts/lib/session-aliases.js` | Retire | 拾われない | 拾われない | - |
| 11 | assets-06 | assets | `scripts/lib/session-manager.js` | Retire | 拾われない | 拾われない | - |
| 12 | assets-07 | assets | `scripts/lib/hook-flags.js` | Retire | 拾われない | 拾われない | - |
| 13 | assets-08 | assets | `scripts/lib/project-detect.js` | Retire | 拾われない | 拾われない | - |
| 14 | assets-09 | assets | `session-aliases.json` | Retire | 拾われない | 拾われない | - |
| 15 | assets-10 | assets | `metrics/costs.jsonl` | Retire | 拾われない | 拾われない | - |
| 16 | assets-11 | assets | `.mcp.json` | Retire | 拾われない | 部分 | - |
| 17 | assets-12 | assets | `scheduled-tasks/akc-plugin-catalog-watch/SKILL.md` | Retire | 拾われない | 拾われない | - |
| 18 | assets-13 | assets | `scheduled-tasks/gemini-gallery-rollout/SKILL.md` | Retire | 拾われない | 拾われない | - |
| 19 | assets-14 | assets | `scheduled-tasks/plugin-directory-status/SKILL.md` | Retire | 拾われない | 拾われない | - |
| 20 | assets-15 | assets | `scheduled-tasks/jrp-opus-first-morning-check/SKILL.md` | Retire | 拾われない | 拾われない | - |
| 21 | assets-16 | assets | `scheduled-tasks/gsc-index-requests-2026-10-13/SKILL.md` | Retire | 拾われない | 拾われない | - |
| 22 | assets-18 | assets | `templates/hybrid/AGENTS.md` | Retire | 拾われない | 拾われない | - |
| 23 | assets-19 | assets | `templates/hybrid/RULES.md` | Retire | 拾われない | 拾われない | - |
| 24 | assets-20 | assets | `templates/hybrid/spec-template.md` | Retire | 拾われない | 拾われない | - |
| 25 | rules-01 | rules | `rules/common/debugging.md` | Merge into boundary.md | 部分 | 部分 | ~/.claude で 2026-11-01 に退役した…rule 1 本（debugging.md）がここでは生きている |
| 26 | skills-07 | skills | `skills/collect-context/SKILL.md` | Improve | 拾われない | 拾われる | - |
| 27 | skills-08 | skills | `skills/context-sync/SKILL.md` | Improve | 拾われない | 拾われない | - |
| 28 | skills-12 | skills | `skills/harness-stocktake/SKILL.md` | Improve | 部分 | 拾われない | harness-stocktake  userSettings  -  -  0×  never |
| 29 | skills-13 | skills | `skills/harness-sync/SKILL.md` | Improve | 部分 | 部分 | H6 ~/.claude/skills/harness-sync/SKILL.md:87 python3 ~/.claude/skills/harness-sy |
| 30 | skills-16 | skills | `skills/hf-sync/SKILL.md` | Improve | 部分 | 拾われる | M11 project .claude/skills/hf-sync/SKILL.md:21 bash ~/.claude/skills/hf-sync/syn |
| 31 | skills-18 | skills | `skills/implementation-chain/SKILL.md` | Improve | 部分 | 部分 | L3 implementation-chain/SKILL.md:36,161-166 judge-tier のセッション（Fable）、model: "opu |
| 32 | skills-21 | skills | `skills/jsonld-knowledge-graph/SKILL.md` | Improve | 部分 | 拾われない | 未使用 skill 25 個 … jsonld-knowledge-graph … remove（skillOverrides で off） |
| 33 | skills-22 | skills | `skills/learn-eval/SKILL.md` | Improve | 部分 | 部分 | M7 learn-eval/SKILL.md:201 one at a time — never ask for batch approval |
| 34 | skills-32 | skills | `skills/public-comment/SKILL.md` | Improve | 部分 | 部分 | L7 public-comment/SKILL.md:12 ## 前提: 2026 年の読者環境 |
| 35 | skills-35 | skills | `skills/release-doi/SKILL.md` | Improve | 部分 | 部分 | M3 release-doi/SKILL.md:406-416 ## Worked example (abstracted) … remove |
| 36 | skills-36 | skills | `skills/repair-discipline/SKILL.md` | Update | 部分 | 部分 | 未使用 skill 25 個 … repair-discipline … |
| 37 | skills-39 | skills | `skills/review-when-watch/SKILL.md` | Update | 部分 | 部分 | H5/M9 ~/.claude で退役した skill … review-when-watch … ここでは生きている |
| 38 | skills-41 | skills | `skills/rules-distill/SKILL.md` | Improve | 部分 | 部分 | rules-distill  userSettings  -  6×  129 days |
| 39 | skills-42 | skills | `skills/rules-stocktake/SKILL.md` | Improve | 部分 | 拾われない | L6 rules-stocktake/SKILL.md:154 MUST surface |
| 40 | skills-48 | skills | `skills/skill-stocktake/SKILL.md` | Improve | 部分 | 拾われる | L9 skill-stocktake/SKILL.md:59 modem-dev/hunk#595 … flag |
| 41 | skills-50 | skills | `skills/spawn-session/SKILL.md` | Update | 部分 | 拾われる | H4 project spawn-session:45-49 「--model は省略時…判断層 = fable」 ↔ ~ 「--model opus」 |
| 42 | skills-52 | skills | `skills/task-triage/SKILL.md` | Improve | 部分 | 拾われる | M5 task-triage/SKILL.md:207 (medium on 2026-09-26, high two days earlier — ADR-0 |
| 43 | skills-59 | skills | `skills/agent-stocktake/SKILL.md` | Update | 部分 | 部分 | L6 agent-stocktake/SKILL.md:227 MUST surface |
| 44 | skills-60 | skills | `skills/measurement-discipline/MAINTENANCE.md` | Update | 拾われない | 拾われない | - |
| 45 | skills-61 | skills | `skills/skill-creator/MAINTENANCE.md` | Update | 部分 | 拾われない | diff 6,7 — skills/skill-creator/MAINTENANCE.md (§2 判断の出所 追加) |
| 46 | skills-62 | skills | `skills/harness-boundary/SKILL.md` | Update | 拾われない | 部分 | - |
| 47 | skills-63 | skills | `skills/skill-health/SKILL.md` | Improve | 拾われない | 拾われない | - |
| 48 | skills-65 | skills | `skills/skill-stocktake/results.json` | Update | 拾われない | 拾われない | - |
| 49 | rules-02 | rules | `rules/common/task-tracking.md` | Improve | 拾われない | 部分 | 常駐層（~/.claude/CLAUDE.md、rules 16 本、output-style）は clean |
| 50 | rules-18 | rules | `skills/rules-stocktake/results.json` | Update | 拾われない | 拾われない | - |
| 51 | agents-01 | agents | `agents/Explore.md` | Update | 部分 | 部分 | M10 ~/.claude/agents/Explore.md … 上流 built-in prompt の verbatim 写し … flag |
| 52 | agents-03 | agents | `agents/architect.md` | Improve | 拾われない | 部分 | - |
| 53 | agents-05 | agents | `agents/readme-judge.md` | Improve | 部分 | 拾われる | .claude/agents/readme-judge.md — description が ~/.claude/agents/readme-judge.md  |
| 54 | agents-07 | agents | `agents/security-reviewer.md` | Improve | 部分 | 部分 | H2 security-reviewer.md:65,96,107 「原則として出さない」 ↔ 「prior として低確信度に置く」 |
| 55 | agents-08 | agents | `agents/swift-reviewer.md` | Improve | 部分 | 部分 | M9 退役済み（swift-reviewer …）が復活する |
| 56 | agents-09 | agents | `skills/agent-stocktake/results.json` | Update | 拾われない | 拾われない | - |
| 57 | hooks-02 | hooks | `hooks/_episode-log-common.sh` | Improve | 拾われない | 拾われない | - |
| 58 | hooks-05 | hooks | `hooks/bandit-precommit.sh` | Improve | 拾われない | 拾われない | - |
| 59 | hooks-06 | hooks | `hooks/ruff-format-precommit.sh` | Improve | 拾われない | 拾われない | - |
| 60 | hooks-07 | hooks | `hooks/bats-autorun.sh` | Improve | 部分 | 拾われる | bats-autorun.sh（PostToolUse Edit\|Write）: 3 回とも約 149 秒、同期実行…`async` 化か matcher の絞 |
| 61 | hooks-24 | hooks | `hooks/validate-bash.sh` | Improve | 拾われない | 拾われない | - |
| 62 | hooks-28 | hooks | `hooks/README.md` | Update | 拾われない | 拾われない | - |
| 63 | hooks-32 | hooks | `skills/hook-stocktake/SKILL.md` | Update | 拾われない | 拾われない | - |
| 64 | hooks-33 | hooks | `skills/hook-stocktake/results.json` | Create | 拾われない | 拾われない | - |
| 65 | distill-01 | distill | `rules/common/evals.md` | Append | 拾われない | 拾われない | - |
| 66 | distill-04 | distill | `skills/rules-distill/results.json` | Update | 拾われない | 拾われない | - |
| 67 | docs-01 | docs | `hooks/README.md` | Update | 拾われない | 拾われない | - |
| 68 | docs-02 | docs | `CLAUDE.md` | Update | 部分 | 部分 | `CLAUDE.md` 14〜20 行目の Layout 節…は `ls` で分かる内容…削除対象 |
| 69 | docs-03 | docs | `AGENTS.md` | Update | 拾われない | 拾われない | 読まなかったもの: `~/.claude/AGENTS.md`（Claude Code は読み込まない |
| 70 | docs-06 | docs | `README.md` | Update | 拾われない | 拾われない | - |
| 71 | assets-21 | assets | `harness-scope/profiles/zenn-writing.json` | Update | 部分 | 拾われない | harness-scope \| plugin \| user（自作）\| no signal (passive) …使っていなければ remove |
| 72 | assets-22 | assets | `scheduled-tasks/README.md` | Update | 拾われない | 拾われない | - |
| 73 | assets-23 | assets | `.claude/verify.md` | Update | 拾われない | 拾われない | - |
| 74 | assets-24 | assets | `.repo-asset-stocktake.json` | Create | 拾われない | 拾われない | - |
| 75 | skills-01 | skills | `skills/adr-writer/SKILL.md` | Keep | 拾われる | 拾われる | 使用あり skill 17 個（adr-writer, …）\| … \| keep |
| 76 | skills-02 | skills | `skills/agent-send/SKILL.md` | Keep | 部分 | 部分 | skill 25 個を…`skillOverrides` に `"off"` で追加…: agent-send, … |
| 77 | skills-03 | skills | `skills/agent-stocktake/SKILL.md` | Keep | 拾われる | 拾われる | 非掲載 skill 16 個（`disable-model-invocation`、agent-stocktake 等）…触らない |
| 78 | skills-04 | skills | `skills/archify/SKILL.md` | Keep | 拾われる | 拾われる | 使用あり skill 17 個（adr-writer, archify, …）\| keep |
| 79 | skills-05 | skills | `skills/author-calibrated-eval/SKILL.md` | Keep | 部分 | 拾われる | author-calibrated-eval  userSettings  -  -  1×  29 days |
| 80 | skills-06 | skills | `skills/authorship-strategy/SKILL.md` | Keep | 部分 | 部分 | skill 25 個を…`"off"` で追加…: …, authorship-strategy, … |
| 81 | skills-09 | skills | `skills/detail-loop/SKILL.md` | Keep | 部分 | 部分 | detail-loop  userSettings  -  -  0×  never |
| 82 | skills-10 | skills | `skills/generation-audit/SKILL.md` | Keep | 部分 | 部分 | L5 \| `~/.claude/skills/generation-audit/SKILL.md:138-140` \| … \| Low \| flag |
| 83 | skills-11 | skills | `skills/grill-me/SKILL.md` | Keep | 拾われる | 拾われる | grill-me  userSettings  -  18.3m  81×  today |
| 84 | skills-14 | skills | `skills/headline-craft/SKILL.md` | Keep | 拾われる | 拾われる | 使用あり skill 17 個（…, headline-craft, …）\| keep |
| 85 | skills-15 | skills | `skills/herdr/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … remove（skillOverrides で off）: … herdr … |
| 86 | skills-17 | skills | `skills/hook-stocktake/SKILL.md` | Keep | 拾われない | 部分 | - |
| 87 | skills-19 | skills | `skills/jev-judgment-design/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … jev-judgment-design … |
| 88 | skills-20 | skills | `skills/jev-skill-router/SKILL.md` | Keep | 部分 | 部分 | H5 … `~/.claude/skills/jev-skill-router` … その path は `~/.claude` に無い（`b876e3a` で |
| 89 | skills-23 | skills | `skills/llm-as-judge/SKILL.md` | Keep | 拾われない | 部分 | - |
| 90 | skills-24 | skills | `skills/llms-txt-writer/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … llms-txt-writer … |
| 91 | skills-25 | skills | `skills/loop-design-check/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … loop-design-check … |
| 92 | skills-26 | skills | `skills/measurement-discipline/SKILL.md` | Keep | 部分 | 部分 | 使用あり skill 17 個（… measurement-discipline …）… keep |
| 93 | skills-27 | skills | `skills/mondo/SKILL.md` | Keep | 部分 | 部分 | eli5 … remove（skill `mondo` が参照。注意） |
| 94 | skills-28 | skills | `skills/mono-figure/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … mono-figure … |
| 95 | skills-29 | skills | `skills/persona-read-loop/SKILL.md` | Keep | 拾われる | 拾われる | 使用あり skill 17 個（… persona-read-loop …）… keep |
| 96 | skills-30 | skills | `skills/prompt-perturb/SKILL.md` | Keep | 拾われない | 部分 | - |
| 97 | skills-31 | skills | `skills/prose-translation/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … prose-translation … |
| 98 | skills-33 | skills | `skills/readme-writer/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … readme-writer …（49 回） |
| 99 | skills-34 | skills | `skills/refactor-clean/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … refactor-clean … |
| 100 | skills-37 | skills | `skills/repo-asset-stocktake/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … repo-asset-stocktake … |
| 101 | skills-38 | skills | `skills/review-to-lint/SKILL.md` | Keep | 拾われない | 部分 | - |
| 102 | skills-40 | skills | `skills/rfc-writer/SKILL.md` | Keep | 拾われる | 拾われる | 使用あり skill 17 個（… rfc-writer …）… keep |
| 103 | skills-43 | skills | `skills/search-first/SKILL.md` | Keep | 拾われる | 拾われる | 使用あり skill 17 個（… search-first …）… keep |
| 104 | skills-44 | skills | `skills/session-judgment-mining/SKILL.md` | Keep | 拾われない | 部分 | - |
| 105 | skills-45 | skills | `skills/skill-comply/SKILL.md` | Keep | 部分 | 部分 | 未使用 skill 25 個 … skill-comply … |
| 106 | skills-46 | skills | `skills/skill-creator/SKILL.md` | Keep | 部分 | 部分 | M6 `~/.claude/skills/skill-creator/SKILL.md:53-56` Source 列 … move |
| 107 | skills-49 | skills | `skills/social-post/SKILL.md` | Keep | 部分 | 拾われる | M4 social-post:34-36 `execute_query` … この session の Buffer MCP に `execute_query` |
| 108 | skills-51 | skills | `skills/task-stocktake/SKILL.md` | Keep | 拾われる | 部分 | 使用あり skill 17 個（… task-stocktake …）… keep |
| 109 | skills-53 | skills | `skills/verify-bootstrap/SKILL.md` | Keep | 拾われる | 拾われる | 使用あり skill 17 個（… verify-bootstrap …）… keep |
| 110 | skills-54 | skills | `skills/wait-what/SKILL.md` | Keep | 部分 | 部分 | 退役した skill 3 本（`jev-skill-router` / `review-when-watch` / `wait-what`）…ここでは生きている |
| 111 | skills-55 | skills | `skills/widen-the-ask/SKILL.md` | Keep | 部分 | 部分 | 使用あり skill 17 個（… widen-the-ask）… keep |
| 112 | skills-56 | skills | `skills/wiki-harvest/SKILL.md` | Keep | 拾われない | 部分 | - |
| 113 | skills-57 | skills | `skills/wiki-query/SKILL.md` | Keep | 部分 | 部分 | doctor Check 1: skill 25 個を skillOverrides で off … wiki-query |
| 114 | skills-58 | skills | `skills/x-draft/SKILL.md` | Keep | 部分 | 部分 | doctor Check 1: skill 25 個を skillOverrides で off … x-draft |
| 115 | skills-66 | skills | `skills/hunk-review` | Out of scope | 拾われる | 部分 | prompt-audit L9: hunk-review は外部 tool 同梱 … flag（hunk-review は報告のみ） |
| 116 | skills-67 | skills | `skills/mono-color` | Out of scope | 部分 | 部分 | prompt-audit M8: mono-color … 編集先は ~/MyAI_Lab/mono-color-skill（diff 11） |
| 117 | rules-03 | rules | `rules/common/llm-first-code.md` | Keep | 部分 | 部分 | prompt-audit 確認して指摘にしなかったもの: llm-first-code.md:10 の as-of |
| 118 | rules-04 | rules | `rules/common/boundary.md` | Keep | 部分 | 部分 | prompt-audit: boundary.md:27 … の incident 日付（制約の横の理由） |
| 119 | rules-05 | rules | `rules/common/akc-cycle.md` | Keep | 拾われない | 部分 | - |
| 120 | rules-06 | rules | `rules/common/planning.md` | Keep | 拾われない | 部分 | - |
| 121 | rules-07 | rules | `rules/common/security.md` | Keep | 部分 | 部分 | prompt-audit: security.md:24 の incident 日付（制約の横の理由） |
| 122 | rules-08 | rules | `rules/common/skills.md` | Keep | 拾われない | 部分 | - |
| 123 | rules-09 | rules | `rules/common/knowledge-staleness.md` | Keep | 拾われない | 部分 | - |
| 124 | rules-10 | rules | `rules/common/evals.md` | Keep | 拾われない | 部分 | - |
| 125 | rules-11 | rules | `rules/common/agents.md` | Keep | 拾われない | 部分 | - |
| 126 | rules-12 | rules | `rules/common/coding-style.md` | Keep | 拾われない | 部分 | - |
| 127 | rules-13 | rules | `rules/common/testing.md` | Keep | 拾われない | 部分 | - |
| 128 | rules-14 | rules | `rules/common/public-records.md` | Keep | 拾われない | 部分 | - |
| 129 | rules-15 | rules | `rules/common/contemplative-axioms.md` | Keep | 拾われない | 部分 | - |
| 130 | rules-16 | rules | `rules/common/practitioner-identity.md` | Keep | 拾われない | 部分 | - |
| 131 | rules-17 | rules | `rules/README.md` | Keep | 部分 | 部分 | doctor: rules/README.md（2,074 chars）は rule 一覧の索引ですが rules 配下にあるため毎 session 常駐 |
| 132 | agents-02 | agents | `agents/adr-reviewer.md` | Keep | 部分 | 部分 | prompt-audit L1/L2: adr-reviewer.md:170 docs/evidence/ … history narrative |
| 133 | agents-04 | agents | `agents/prompt-forager.md` | Keep | 拾われない | 部分 | - |
| 134 | agents-06 | agents | `agents/researcher.md` | Keep | 部分 | 部分 | prompt-audit M1/M2: researcher.md:80 200 語以内 / :30-31 incident 文 |
| 135 | hooks-01 | hooks | `hooks/_advisory-common.sh` | Keep | 拾われない | 拾われない | - |
| 136 | hooks-03 | hooks | `hooks/_git-target-common.sh` | Keep | 拾われない | 拾われない | - |
| 137 | hooks-04 | hooks | `hooks/_session-common.sh` | Keep | 拾われない | 拾われない | - |
| 138 | hooks-08 | hooks | `hooks/block-episode-logs-grep.sh` | Keep | 拾われない | 拾われない | - |
| 139 | hooks-09 | hooks | `hooks/block-episode-logs.sh` | Keep | 拾われない | 拾われない | - |
| 140 | hooks-10 | hooks | `hooks/contemplative-name-reminder.sh` | Keep | 拾われない | 部分 | - |
| 141 | hooks-12 | hooks | `hooks/harness-commit-notice.sh` | Keep | 拾われない | 部分 | - |
| 142 | hooks-13 | hooks | `hooks/harness-lint-precommit.sh` | Keep | 拾われない | 部分 | - |
| 143 | hooks-14 | hooks | `hooks/herdr-agent-state.sh` | Keep | 拾われない | 部分 | - |
| 144 | hooks-15 | hooks | `hooks/log-agent-usage.sh` | Keep | 拾われない | 部分 | - |
| 145 | hooks-16 | hooks | `hooks/log-skill-usage.sh` | Keep | 拾われない | 部分 | - |
| 146 | hooks-17 | hooks | `hooks/plan-executor-notice.sh` | Keep | 拾われない | 部分 | - |
| 147 | hooks-18 | hooks | `hooks/research-gate.sh` | Keep | 拾われない | 部分 | - |
| 148 | hooks-19 | hooks | `hooks/review-chain-notice.sh` | Keep | 部分 | 部分 | 記録のある分は各 80〜140ms（review-chain-notice 79ms、validate-bash 141ms） |
| 149 | hooks-20 | hooks | `hooks/review-model-notice.sh` | Keep | 拾われない | 部分 | - |
| 150 | hooks-21 | hooks | `hooks/secret-scan-precommit.sh` | Keep | 拾われない | 部分 | - |
| 151 | hooks-22 | hooks | `hooks/skill-create-notice.sh` | Keep | 拾われない | 部分 | - |
| 152 | hooks-23 | hooks | `hooks/task-claims-reminder.sh` | Keep | 拾われない | 部分 | - |
| 153 | hooks-25 | hooks | `hooks/verify-precommit.sh` | Keep | 部分 | 部分 | **verify-precommit.sh**: 中央値 1.5 秒、commit 時のみ。問題なし。 |
| 154 | hooks-26 | hooks | `scripts/hooks/harness_lint.py` | Keep | 拾われない | 拾われない | - |
| 155 | hooks-27 | hooks | `scripts/hooks/verify_allow.py` | Keep | 拾われない | 拾われない | - |
| 156 | distill-02 | distill | `skills/review-when-watch/SKILL.md` | Too Specific | 部分 | 拾われない | 退役した skill 3 本（`jev-skill-router` / `review-when-watch` / `wait-what`）…ここでは生きている |
| 157 | distill-03 | distill | `skills/repair-discipline/SKILL.md` | Too Specific | 部分 | 拾われない | 未使用 skill 25 個 … repair-discipline … remove（`skillOverrides` で off） |
| 158 | docs-04 | docs | `rules/README.md` | Keep | 部分 | 拾われない | `~/.claude/rules/README.md`（2,074 chars、~0.5k）は…毎 session 常駐しています |
| 159 | docs-05 | docs | `docs/adr/README.md` | Keep | 拾われない | 拾われない | - |
| 160 | assets-17 | assets | `scheduled-tasks/weekly-aeon-shopping/SKILL.md` | Keep | 拾われない | 拾われない | - |
| 161 | assets-25 | assets | `tests/` | Keep | 拾われない | 拾われない | - |
| 162 | assets-26 | assets | `scripts/replay/` | Keep | 拾われない | 拾われない | - |
| 163 | assets-27 | assets | `scripts/hooklint/` | Keep | 拾われない | 拾われない | - |
| 164 | assets-28 | assets | `scripts/claims.py` | Keep | 拾われない | 拾われない | - |
| 165 | assets-29 | assets | `scripts/triage-tick.sh` | Keep | 拾われない | 拾われない | - |
| 166 | assets-30 | assets | `scripts/notify-slack.sh` | Keep | 拾われない | 拾われない | - |
| 167 | assets-31 | assets | `scripts/cloud-dispatch.sh` | Keep | 拾われない | 拾われない | - |
| 168 | assets-32 | assets | `scripts/verify-public-detail.sh` | Keep | 拾われない | 拾われない | - |
| 169 | assets-33 | assets | `scripts/transcript-last-turn.sh` | Keep | 拾われない | 拾われない | - |
| 170 | assets-34 | assets | `scripts/lib/notify.sh` | Keep | 拾われない | 拾われない | - |
| 171 | assets-35 | assets | `scripts/launchd/` | Keep | 拾われない | 拾われない | - |
| 172 | assets-36 | assets | `.claude/verify.sh` | Keep | 拾われない | 拾われない | verify-precommit.sh: 中央値 1.5 秒、commit 時のみ。問題なし。 |
| 173 | assets-37 | assets | `.claude/ty-root.toml` | Keep | 拾われない | 拾われない | - |
| 174 | assets-38 | assets | `ruff.toml` | Keep | 拾われない | 拾われない | - |
| 175 | assets-39 | assets | `.gitignore` | Keep | 拾われない | 拾われない | - |
| 176 | assets-40 | assets | `statusline-command.sh` | Keep | 拾われない | 部分 | - |
| 177 | assets-41 | assets | `CLAUDE.md` | Keep | 拾われる | 拾われる | `~/.claude/CLAUDE.md` \| memory \| user（全 project） \| — \| — \| ~0.4k \| keep |
| 178 | assets-42 | assets | `AGENTS.md` | Keep | 部分 | 部分 | 読まなかったもの: `~/.claude/AGENTS.md`（Claude Code は読み込まない、非 Claude agent 向け） |
| 179 | assets-43 | assets | `gc_log.md` | Keep | 拾われない | 拾われない | - |
| 180 | assets-44 | assets | `docs/plans/` | Keep | 拾われない | 拾われない | - |
| 181 | assets-45 | assets | `docs/evals/` | Keep | 拾われない | 拾われない | - |
| 182 | assets-46 | assets | `docs/diagrams/` | Keep | 拾われない | 拾われない | - |
| 183 | assets-47 | assets | `.notes/TASKS.md` | Keep | 拾われない | 拾われない | - |
| 184 | assets-48 | assets | `.notes/archive/` | Keep | 拾われない | 拾われない | - |
| 185 | assets-49 | assets | `.notes/mirrors/` | Keep | 拾われない | 拾われない | - |
| 186 | assets-50 | assets | `.notes/s1-eval-native-reading-2026-09-13.md` | Keep | 拾われない | 拾われない | - |
| 187 | assets-51 | assets | `scheduled-tasks/weekly-article-metrics-collect/SKILL.md` | Keep | 拾われない | 拾われない | - |
| 188 | assets-52 | assets | `scheduled-tasks/admission-readings-monthly/SKILL.md` | Keep | 拾われない | 拾われない | - |
| 189 | assets-53 | assets | `scheduled-tasks/weekly-resonance-collect/SKILL.md` | Keep | 拾われない | 拾われない | - |
| 190 | assets-54 | assets | `scheduled-tasks/monthly-resonance-report/SKILL.md` | Keep | 拾われない | 拾われない | - |
| 191 | assets-55 | assets | `scheduled-tasks/listing-pr-daily/SKILL.md` | Keep | 拾われない | 拾われない | - |
| 192 | assets-56 | assets | `scheduled-tasks/listing-explore-rotation/SKILL.md` | Keep | 拾われない | 拾われない | - |

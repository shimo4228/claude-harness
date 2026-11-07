kind: internal
# 誰が実装するか、と常駐層の簡素化 — harness の実物と実績（2026-11-07）

外部調査の report は [2026-11-07-context-holder-implements.md](2026-11-07-context-holder-implements.md)。
調べ方: 読み取り専用の監査 4 本（委譲の実績 / task-triage の機構の地図 / 常駐層 / skill・hook・plugin）を並列に走らせた。
各監査の非 keep の発見は、別の反証役が再現と依存の grep を行った（56 件中 47 件で、主張の誇張か、提案が壊す依存を指摘）。
この report には、反証を通った形だけを書く。

## 再現

### 委譲の実績（contemplative-agent と ~/.claude、2026-08-17〜11-07）

- triage の build: 09-24 以降、contemplative-agent で 22 件。cloud 8、ローカル 14（Agent 9・spawn-session 4・session 1）。
  ~/.claude は cloud 0 件で、ローカルは spawn-session と Agent。数えたのは `.notes/claims.jsonl` と `logs/cloud-dispatch.jsonl` で、
  script を通らない cloud PR（ADR-0099 Context の claude-config の 4 本）は含まない。
- 差し戻し: `logs/effort-outcomes.jsonl` は 12 行で、bounce=true の 5 行はすべて「gate・rebase」（main が先に進んだ）。
  ただしこの log は 11-04 以降の build（RFC-0066・0067・0068）と、09 月の数本が欠けている。中身の差し戻しの実例は
  RFC-0067 S47（cloud build が security の HIGH を見落とし、判断役が別 process で回した security-reviewer が拾った）と、
  RFC-0046 S40（/code-review の指摘で分岐を足した）。
- 実際に起きた誤りの出所は判断役の側: contemplative-agent `rfcs/0022-wikiskill-fidelity-check.md:14-27`（設計 session が論文を 3 か所読み違え、
  packet 経由で build に伝わり、著者が見つけた）、`rfcs/0068`（digest で決めた上限 50 を、同じ判断役 session が翌日 300 に戻した —
  値が効く経路 `core/scheduler.py:101,141` を既定案を置く前に読んでいなかった）。
- Phase 0 での前提の反証: contemplative-agent の build commit で `Premise:` 行を持つ 69 件のうち約 10〜12 件（15〜18%）が、
  packet か判断役の前提を反証してから実装を続けた。止まった build は記録上 0。
- 時間: claim→release で、差し戻しなしの cloud 6〜30 分、ローカル Agent 9〜50 分、spawn-session 19〜76 分。cloud が速い証拠は無い（n 小、課題の大きさが揃わない）。
- 判断役 session: `logs/triage-tick.log` で 10-17 以降の 13 cycle すべてが新しい session で始まった（`scripts/triage-tick.sh:113-169` が
  CLI の版の変化か 7 日で作り直す。設計どおり）。1 cycle の context は約 15〜36 万 token で、中身は台帳全体の判定。
- 事前登録つき再生比較（[2026-10-27-replay-result.md](2026-10-27-replay-result.md)）: 「台帳を全部判定してから同じ session で実装」は
  2/16 失敗、「packet で fresh な build」は 0/16。規則 1 を満たさず既定は替えなかった。packet を書かずに文脈保持者が実装する形は測っていない。

### task-triage の重さ

- `skills/task-triage/SKILL.md` 488 行。§3 Dispatch（165-271）と §4 Judge（272-350）で 186 行（38%）。cloud の構文を含む行 51、effort を含む行 32。
- `references/packet-template.md` 185 行（14.6 KB）。小さな修正では packet が diff より長い（contemplative-agent S46 は packet 89 行・diff 46 行、S44 は 95 行・77 行）。
- packet ごとの effort 選択（ADR-0081）は毎回動いているが、「見落としで 1 段上げる」は 16 本以上で 1 回だけ発火し、効果の対照は無い。
  帳簿（effort-outcomes.jsonl）は 10-31 以降の手での追記が止まっている。

### 常駐層（~/.claude の session で約 12.9K token、他 repo で約 9.1K + その repo の CLAUDE.md）

数え方は CJK 1 字 1 token、その他 3.5 字 1 token の概算（`/context` は回していない）。CLAUDE.md 499 / AGENTS.md 435 / rules/README.md 630 /
rules/common 15 本 8,007 / MEMORY.md 3,375。rule の HTML コメント（origin・rationale・review-when）は注入時に除かれる（この session の system-reminder で確認）。

- hook の差し込み（直近 14 日、transcript 集計）: `hooks/task-claims-reminder.sh` 2,107 回・626K 字（台帳に触れるたびに同じ固定 3 行）、
  `hooks/review-chain-notice.sh` 3,140 回・267K 字（`merge-base` 等の非該当でも 108 回）、`hooks/contemplative-name-reminder.sh` 208 回（10-24 以降、55 session）。
- plugin: pr-review-toolkit の agent 説明が約 6.3K 字常駐し、ADR-0042 の 2026-09-12 注記（自発選択させない）の後も
  `pr-review-toolkit:code-reviewer` が 32 回起動（`metrics/agent-usage.jsonl`、同期間に silent-failure-hunter は 5 回）。
  claude-security は 60 日で 1 回、hookify は全 tool 呼び出しで起動して差し込み 0・rule 1 本（その rule は 33/33 が誤検知）、adhd と session-report は使用なし。
- skill 一覧: local の model-invocable 42 本の説明 9,995 字、claude.ai から同期された 15 本 10,169 字、plugin 11,584 字。この session の一覧でも
  同期分 7 本が説明なしで並ぶ（溢れか name-only か未特定）。
- `python3 scripts/hooks/harness_lint.py` は作業ツリーで rc=3（`skills/.trash/` に SKILL.md が無い。claude.ai の同期が作った未追跡 dir）。

## 原因

- 委譲を既定にしている行: `skills/implementation-chain/SKILL.md:35-55`（「judge-tier の既定は dispatch、文脈損失は packet の充実で救う」）と
  常駐の `rules/common/planning.md:11`。根拠の ADR-0057 は Fable の使用限度で、triage の判断役は commit 29bd389（2026-10-11）から build と同じ
  Opus 5.5。implementation-chain:36 は judge-tier を Fable と書き、planning.md:11 の「judge-tier」は Opus の session には当たらないが、語が残って読み手を迷わせる。
  `hooks/plan-executor-notice.sh:67-70` と `hooks/review-model-notice.sh` は Fable のときだけ鳴る（14 日で 51 回、Fable session は 30 日で 401/2397）。
- cloud を既定にしている行: `skills/task-triage/SKILL.md:6,22,173-178`、`references/packet-template.md:10-17`、implementation-chain:40-43（ADR-0075）。
- 実物とずれた記述: task-triage `SKILL.md:263-266`「Agent tool は effort を取らない」— CLI 2.1.319 の Agent tool は呼び出しごとの `effort` を取る
  （v2.1.292 以降、非 fork のみ。この session の Agent tool schema にも `effort` がある）。この 1 文が、docs 以外の local build を spawn-session に回している。
  `SKILL.md:437`「long-lived」は実態（毎 cycle 作り直し）とずれる。
- 常駐の重複と古い行: planning.md・task-tracking.md が hook の差し込み文面を繰り返す。MEMORY.md は 48 行中 23 行が幅 200 超、退役・終了した対象を
  進行中として載せる行が 6 本（:5 の「merge = 人間」は ADR-0069 で判断役の ff-only に変わった）。`rules/common/boundary.md:20` の `.growth/` は退役した
  growth loop（ADR-0064）。`CLAUDE.md:19` は output-styles を応答の register と書くが、`settings.json` に `outputStyle` が無く signal-first は無効。
- 全 repo に常駐するが ~/.claude の中でしか意味を持たない記述: `CLAUDE.md` の Layout・Origin、`rules/README.md`（rules/ 配下なので自動で読まれる）、
  `rules/common/security.md:17-32` の harness 脅威面、`rules/common/akc-cycle.md` の所有者表。

## 確認

- 反証役が数値を再現した（git log・claims.jsonl・gh api・transcript の集計）。外れた点は上に反映済み（S47 の diff 行数、S30 の所要時間、branch と task の対応など）。
- 依存の grep で、そのまま消すと壊れる箇所を確かめた:
  - `rules/README.md` を動かすと `docs/decision-history/0030…:91` の相対リンクが harness_lint の検査 5 で赤になる（scratch で rc=3 を再現）。
  - `rules/common/coding-style.md` を消すと `docs/decision-history/0019…:18` のリンクと `security.md:19` のスコープ参照が切れる。
  - `llm-first-code.md:26-34` は、repo の CLAUDE.md や ADR を書くときに常駐している唯一の写し（skill-writer は skill を書くときだけ読まれる）。
  - `boundary.md` の Herdr 例外は `skills/spawn-session/SKILL.md:93` と `agent-send/SKILL.md:82-84` が正本として指す。
  - MEMORY.md は gitignore 下で git から戻せない。
  - contemplative-agent の CLAUDE.md の表は 4 本のテストが読み先にしている。
- substrate の仕様は docs で確かめた（外部 report の C 群）。user-level rule の `paths:` は session の cwd 基準で、`~/.claude` だけに効かせる切り替えにはならない。
  `~/.claude/.claude/CLAUDE.md` が project 専用として読まれるかは docs に無い。fork mode が on の間、interactive session は subagent の完了を待てない（結果は後で届く）。
  非 fork の subagent は CLAUDE.md の階層を読み直すが MEMORY.md は読まない。

## Still unknown

- 「著者と plan を詰めた Opus session が packet を書かずに実装する」形と、fresh な build の品質差（内部も外部も測定なし）。
  文脈を持つ session の commit（全体の約 97%）には、差し戻しや review 所見の帳簿が無い。
- 著者の言う期限切れの「トークン」の特定。`claude auth status` は claude.ai login 有効（期限 2026-11-29）、`gh auth status` も有効なので、
  tick・Herdr・Remote Control・push は止まっていない。
- `~/.claude/.claude/CLAUDE.md` を置いたときの読み込み（cwd=~/.claude で二重読み込みが起きるか、AGENTS.md が読まれなくなるか）— 1 session の probe で決まる。
- 常駐層を削った効果をこの harness の作業で測った値（`/context`・`/skill-doctor` も未実行）。
- 無人の triage session から出した Agent build が、auto mode の permission と commit gate の hook をどう通るか（RFC-0016 の 2026-08-29 実測以降は未確認）。

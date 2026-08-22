# ADR-0046: skill-creator をその場で縮退し、作成時ゲートと命令形配線に置き換える

## Status

accepted

## Date

2026-08-22

## Context

skill-creator（origin `anthropics/skills-customized`、sha `b9e19e6`、2026-05-20 取り込み）は
工程の半分が description 最適化 loop だった。しかし自発トリガーは ≒40% が実測上の上限で、
description を磨く先は壁だった。一次出典は 1 件 — memory `feedback_autonomous_trigger_ceiling`
（2026-04-11、search-first で text 編集 27%→8%、悪化の大半は測定アーティファクトと自記）で、
[ADR-0013](./0013-cross-model-review-seam-via-codex.md) / [ADR-0018](./0018-rules-rightsize-for-claude5.md) /
[ADR-0026](./0026-retire-signal-first-residency.md) はそれを引用した再掲。skill-creator 自体では測っていない。発火測定の
計器自体も 2026-06-29 に定数 recall=0 で壊れていた（memory `reference_skill_creator_loop_gotchas`、
`run_eval.py` が評価対象文字列を command として注入していた構造バグ）。計測配線は subagent 通知 →
`timing.json` → HTML viewer → `feedback.json` という人力の連鎖で、invoke 実績は 67 日で 11 回、
直近 6 日は未使用だった。

著者の運用は「作って」と明示指示する形だが、skill-creator はその明示指示の場面でもほとんど
発火しない（著者観測 2026-08-22）。作成時に本来参照すべき判断（abstraction trap / 40% 上限を
理由に user-invocable を既定にする / redundant channel を避ける / recommender 型 skill は不適合）は
memory 各所に散っており、手順として skill 化されていなかった（`rules/README.md`: 手順は skill が
持つ、という区分と不整合）。

発端は NVIDIA SkillEvaluator（2026-08-19 公開）の検討だった（memory `reference_skillevaluator_pilot`、
v0.2.0 / commit e70f0e3 / as-of 2026-08-22）。Tier 1 を origin shimo4228 の 48 skill に実走したところ
真の欠陥は 0 件（全件 false positive、exit=1 は `metadata.author` 欠落）で、Tier 3 は `ANTHROPIC_API_KEY`
を必須としサブスクリプション運用では使えなかった。judge 自体も LLM であり、期待していた「外部評価」には
ならなかったため見送った。棄却理由の正本は Alternatives。

`claude plugin eval --ablation with-without` は同じ枠を substrate 側で占めうるが early access
gate の内側にあり（CLI 2.1.239 で確認）、台帳 T-SKILL-CREATOR-EVAL-NATIVE が毎週 probe している。

新設案として、readme-writer / readme-judge と同型の skill-writer（render + gate）+ skill-judge
（agent + checklist + evidence script）を検討したが、codex-plan-challenge（VERDICT premise-hole）と
architect agent が独立に棄却した。根拠は、台帳 T-002（skill 本数を減らす方針）と衝突すること、
静的 evidence script は SkillEvaluator Tier 1 が真の欠陥 0 を出したのと同じクラスの装置である
こと、fresh-context 判定はすでに skill-stocktake Phase 2 が持っていること、checklist を別ファイルに
写すと二重定義になることだった。architect は「作成頻度が低い（≒8〜9 日に 1 回）」も理由に挙げたが、
adr-reviewer の照合で誤りと判明した — `git log --diff-filter=A -- 'skills/*/SKILL.md'` では直近 60 日に
30 本（≒2 日に 1 本）で、architect は skill-creator の invoke 間隔（67 日 / 11 回）を作成頻度と
取り違えていた。頻度はむしろ作成時ゲートの必要性を支える側で、棄却は残る 3 理由で成立する。

## Decision

1. skill-creator を名前を維持したままその場で全面書き直す（`b81683e^` 時点 19 ファイル 5,886 行 →
   SKILL.md 96 行 + `references/portability.md` 38 行。`git ls-tree -r b81683e^ -- skills/skill-creator` で再現）。origin を
   `shimo4228` に反転し、`replaces:` で旧版との系譜を残す（`replaces:` は rules/common/skills.md に
   任意 field として追記。harness_lint は検査しない）。`scripts/` 全部、`agents/`（grader /
   analyzer / comparator）、`eval-viewer/`、`assets/`、`references/schemas.md` を削除する。
   `references/portability.md` は Skill Portability 規約の正本（[ADR-0018](./0018-rules-rightsize-for-claude5.md):50 で移設）
   なので残す。harness-boundary:107 はその消費者。
2. 新 SKILL.md を次の構成にする: §1 intent packet + 隣接 skill の library 全体 grep（形と境界は
   ここで判断し、build-or-not の判断自体は著者 / learn-eval が持つ）。§2 作成時の判断 4 つを
   memory から昇格する。§3 は Fable 向けの書き方（判断基準と罠を示し、逐条手順は書かない）。
   §4 は草稿ゲート — general-purpose subagent 1 体、tools は Read/Grep/Glob のみで Bash は
   持たせない（候補本文は untrusted データとして扱う）。skill-stocktake Phase 2 の 4 問に
   Generation fit と Trigger realism を加えて参照として渡し、集計はせず named verdict
   （Publishable / Fix / Drop）を出させる。同一質問での再判定は 1 回まで、上限 2 ラウンド。
   §5 with/without の比較は subagent 2 arm を著者が読む形にし、`claude plugin eval` が有効化
   されたら native に置き換える。§7 はゲート通過後に著者が見つけた指摘数を KPI として commit
   message に残す。§6 は配線（harness_lint / scan_refs / rule wiring / harness-sync）、末尾に
   「持たないもの」を列挙して再導入を止める。
3. 発火配線を 2 段にする。`rules/common/skills.md` に「新規作成・大幅改修は書く前に
   skill-creator を読む」という命令形を追加する（ADR-0018:83 の fallback 適用、rationale /
   review-when を更新）。0018 の fallback は「skill-comply で発火率を測り、立たなければ」と条件付き
   だが、skill-creator に対する測定は**行っていない** — 根拠は著者観測（分母なし）で、測定コストが
   配線 1 行より高く、Review-when 最終項で配線を外す経路を持つため先に配線した。加えて `hooks/skill-create-notice.sh`（PreToolUse Edit|Write）を追加し、
   `~/.claude/skills/<name>/SKILL.md` と `agents/<name>.md` の**未存在ファイル**への書き込みだけで
   発火させる。既存ファイルの編集・project-local パス・入れ子 path は沈黙させ、advisory には
   固定文のみを載せて `file_path` は載せない。bats を 8 本追加する。
4. 参照の意味を修正する: skill-health の Validation 定義を「benchmark」から「草稿ゲート記録」に
   変える、learn-eval の Promote 手順を更新する、skill-stocktake Phase 2 に「正本はここ、creator は
   参照」と明記する、llm-as-judge の Related を更新する。memory `reference_anthropic_skills_imports`
   の skill-creator 行と MEMORY.md の「稼働中」を「2026-08-22 ローカル書き直し、upstream 追従終了」に
   改める — 同 memory は同日朝の drift 検査で「維持」と結論しており、数時間で反転した記録になる。skill-creator という名前自体は変わらないため
   rename は 0 箇所で済む。
5. skill-judge agent を Build する条件を数値で固定する: 次の 3 回の skill 作成で、著者の通読指摘数が
   平均 2 件以上になったら Build する。それまでは作らない。

commit は `b81683e`（hook + rule。**旧資産の削除 5,363 行もここに入った** — `git rm` で staged した
削除が hook の commit に巻き込まれた。意図した分割ではないが履歴は正確に残す）と `cb902cc`（SKILL.md
書き直し + 参照修正、-469 行）。

## Review-when

- `claude plugin eval` がこのアカウントで単体 skill を target に有効化されたら、§5 を native に
  置き換える（台帳 T-SKILL-CREATOR-EVAL-NATIVE）。
- 3 回連続の skill 作成で著者の通読指摘数が平均 2 件以上になったら、inline subagent では足りず
  専用 judge agent + checklist を Build する（Decision 5）。
- 30 日間で skill / agent の新規作成（`git log --diff-filter=A --since=30.days -- 'skills/*/SKILL.md'
  'agents/*.md'`）があるのに、同窓の `metrics/skill-usage.jsonl` に skill-creator の read / invoke が
  無ければ、配線が失効している（hook 自体はログを持たない — 代理指標で見る）。
- KPI の数え方: 作成 commit の message に `skill-creator-gate: N 件` を残す（SKILL.md §7）。
  `git log --grep='skill-creator-gate:'` で 3 件集まったら判定。
- skill-creator の自発発火が 40% を安定して超えたら、`rules/common/skills.md` の命令形配線を外す。

## Alternatives Considered

### skill-writer + skill-judge の新設（readme-writer / readme-judge 同型）

readme-writer / readme-judge と同型で書く / 評価する agent を分ける案。台帳 T-002（skill 本数を
減らす方針）と衝突し、evidence 層は SkillEvaluator Tier 1 と同クラスで実測 yield 0、checklist が
別ファイルへ二重定義されると判断し、Codex（VERDICT premise-hole）と architect agent が独立に棄却した
（architect の「頻度が低い」は誤りで採らない — Context 参照）。

### NVIDIA SkillEvaluator の導入

Tier 1 を 48 skill に実走したところ真の欠陥 0（全件 false positive）、Tier 3 は
`ANTHROPIC_API_KEY` 必須でサブスクリプション運用に合わず、judge も LLM のため「外部評価」には
ならなかった。棄却。

### skill-creator を現状維持で description loop だけ削る

description 最適化 loop 以外の部分も旧世代向けの逐条手順のままで、発火しない問題自体は
残る。棄却。

### 現状維持

工程の半分が実測上の壁（≒40% 上限）を磨き続ける構成のまま残り、計測配線の破損（recall=0）も
放置される。棄却。

## Consequences

### Positive

- 常駐 description は 1 本のまま増えず、skill 数は不変（台帳 T-002 と整合する）
- 作成時の判断が memory 依存から skill 本文（§2）へ移り、recall に依らず参照できる
- 新規作成が hook（`skill-create-notice.sh`）で決定論的に思い出される
- 草稿ゲートの subagent に Bash を持たせないため、候補本文（untrusted）を読む judge への
  injection 面を新たに作らない

### Negative

- with/without の集計・世代管理・旧版 baseline・非弁別検出という native に無い 4 点
  （台帳 T-SKILL-CREATOR-EVAL-NATIVE に記録）を失い、2 ケースを人が読む形に縮退する
- `skill-create-notice.sh` は Write/Edit 経由の作成しか見ない（`cat >` 等は素通りする）。30 日の
  発火実績を見て `validate-bash.sh` への追加要否を判断する
- 大幅改修（既存 SKILL.md の書き直し）の検知は rule の命令形だけに依存し、hook の後ろ盾が無い
- 常駐コストは T-002 の物差し（文字数）では**増えている**: description 332 → 528 字（+196）、
  `rules/common/skills.md` +4 行、全 Edit|Write に PreToolUse hook 1 本。skill 本数は不変
- readme-judge にも同種の Bash 付き judge の injection 面があるが、本 ADR では扱わない
  （別途起票の候補）

### Neutral / Follow-ups

- 関係 ADR: [ADR-0018](./0018-rules-rightsize-for-claude5.md)（40% 上限 fallback を適用）、
  [ADR-0039](./0039-retire-python-reviewer-simplify-in-chain.md)（Review の順序）、
  [ADR-0044](./0044-adr-review-when-and-dated-annotation.md)（Review-when 節）。
  [ADR-0001](./0001-ecc-skill-management-policies.md) / [ADR-0008](./0008-ecc-local-only-management.md) /
  [ADR-0012](./0012-cross-tool-skill-sharing-via-agents-skills.md) は取り込み方針を定めた ADR で、
  ローカルでのその場書き直しを妨げない
- skill-creator という名前は変わらないため、他 skill / agent 側の参照更新は rename ではなく
  意味の修正（Decision 4）で済む

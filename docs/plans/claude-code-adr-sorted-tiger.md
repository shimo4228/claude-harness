# 新規アイデアへの制動を外す — ADR 照合配線の撤去 / memory 却下ガードの削除 / Build-or-not 4 問の廃止

## Context

著者の観測（2026-09-14）: 普段のセッションで Claude Code が新しいアイデアに取り組むことを拒む。
拒む根拠の頻度は著者申告で **ADR > memory > Build-or-not 4 問の儀式**。search-first は別セッションで
再設計中のため対象外。hook は SessionStart で何も注入せず block は commit 境界と危険コマンドだけなので
主因ではない（調査済み）。

同じ観測は ADR-0044（2026-08-19）が「読み方 protocol」（ADR は日付つき仮説、発散段階で却下記録を
反証に使わない）を 5 箇所に配線して対処しようとしたが、宣言型の対処では止まらなかった。ADR-0044 の
未決 Alternative「ADR を廃止し仮説台帳だけにする」の再訪条件（導入後も観測が続いたら）が発火している。

今回の方針は **「変更前に ADR / memory を確認せよ」という指示そのものを撤去する**。読まなければ
制動は掛からない。ADR は設計判断の記録として書き続け、既存機構を変更するときに経緯を読む。

**全編集に共通する書き方（著者指示 2026-09-14）**: 残す文・新しく書く文は「すること」だけを書く。
「〜しない」「〜ではない」「veto ではない」の形は対象を想起させるので、削除で済むものは削除し、
言い換えが要るものは肯定形の事実か手順にする。ADR-0065 の Decision も同じ形で書く。

実行者: 本セッション（散文編集 = judge-tier の本業。implementation-chain §dispatch 例外 (a)）。

## A. ADR を「変更前に確認する対象」から外す

| ファイル | 変更 |
|---|---|
| `AGENTS.md:9` | 行全体を「設計判断の記録は `[docs/adr/](docs/adr/README.md)`。既存機構を変更するとき経緯を読む」に置換 |
| `rules/common/akc-cycle.md:35-57` | 「ADR も足場である」「却下記録の読み方」の 2 節（約 24 行）を削除し、「ADR の扱い」1 節 3 行以内に置換: ADR は日付つきの経緯記録 / 既存機構を変更するとき経緯を読む / 新しい判断が旧 ADR と衝突したら supersede し、旧 ADR に `> **注記（日付, ADR-NNNN）**` を残す。memory への言及は書かない（B で却下ガード自体を消す）。frontmatter の `rationale` / `review-when` と 13 行目の表セル（AKC ADR-0026 の受け側）を新節名に合わせる |
| `skills/grill-me/SKILL.md:60-67` | rule 3 の ADR 読み方 protocol（Date / Review-when を先に見る、前提 Z を問う、veto ではない）を丸ごと削除。残るのは「docs first: 読んで分かることは読む。settled な決定は文書から取る」まで |
| `agents/architect.md` | 26-32 行の ADR / memory ガードの 2 箇条を削除（zero-base test が既に覆う。代替文は書かない）。6-9 行のヘッダコメントを「判定は常に最強モデルで。fable が引けない場合のみ opus」だけに。20-21 行「When delegated from the feature-challenge step in planning.md」を「When invoked」に |
| `docs/adr/README.md` | template 前文の読み方 protocol 参照句を削除し、注記の書き方（既存の末尾 3 行）だけ残す |
| `rules/README.md:17` | akc-cycle の説明を「Scaffold Dissolution / ADR の扱い（経緯記録・supersede・注記）」に |
| `skills/adr-writer/references/review-findings.md:10` | 「（akc-cycle の却下記録の読み方と同じ）」の括弧を削除 |
| `scripts/hooks/harness_lint.py:405` | コメントが旧節名を引いていれば新節名に（ロジック変更なし） |

残すもの: `adr-reviewer` の「先行 ADR との override 関係」チェック（ADR を**書く**時の検査で、アイデア段階には掛からない）、implementation-chain Doc Sync の「所有 ADR の追補」行、`rfcs/0001:83` の言及（done の履歴）。

## B. memory の却下ガードを刈る

基準: (a) 外部ツールの純粋な却下記録、(b) skill / ADR に昇格済で repo が既に持つもの、(c) 判断が ADR に
移った古い session log は削除。user profile・進行中 project・作業作法の feedback は残す。

**削除（14 ファイル）** — `projects/-Users-<user>--claude/memory/` 配下:

- 却下記録: `reference_delta_deltadb_observation.md`、`reference_skillevaluator_pilot.md`、`project_writing_agent_pi.md`
- 昇格済（skill-creator §2 / git-workflow / ADR-0039 / ADR-0046 が持つ）: `feedback_abstraction_trap.md`、`feedback_skill_design_intent.md`、`feedback_autonomous_trigger_ceiling.md`、`feedback_redundant_channel.md`、`feedback_git_dash_c_over_cd.md`、`feedback_python_review.md`、`reference_skill_creator_loop_gotchas.md`
- session log（ADR-0002〜0007 が判断を持つ）: `session-2026-02-23.md`、`session-2026-03-13-scout.md`、`session-2026-03-20-skill-comply.md`、`session-2026-03-24-context-sync.md`

**編集（ガード文 → 事実文）**:

- `reference_herdr_setup.md`: 137 行「herdr-ctx も不要。再提案しない」の文を削除 / 144 行「link_handlers は不要と判断」の文を削除 / 20 行「再有効化しないこと」の文を削除し、原因の事実文（on にすると desync する）だけ残す / 35 行「音は全層で恒久禁止」→「通知は視覚のみ」
- `user_depth_over_breadth.md`（6 hit）と `feedback_deterministic_semantic_layering.md`（3 hit）: 読んで「〜しない」の文は、することの記述に言い換えられるものは言い換え、言い換えられないものは削除
- `MEMORY.md`: 削除ファイルの行を消し、「履歴」節を丸ごと削除。残る行の hook から却下語（棄却 / 不採用 / 退役 / 終結 / 禁止）を外し、事実だけにする
- `feedback_permission_mode_preference.md`: 18 行「harness 側のゲートを外す提案（…）はしない」を「permission の提案は auto mode + allowlist 整備の形で出す」（16 行と同旨）に畳み、残りは無変更

## E. rule: することだけを書く

著者指示（2026-09-14）: 「するな」と書かれた対象は想起される。harness の文書（rule / skill / agent / memory / ADR）は、することだけを書く。

- 置き場所: `rules/common/skills.md` の「小さな追記でも現行規則として書く」段落に 1 文追加: **「することだけを書く。やめる項目は本文から消す」**。正本は skill: `skill-creator` §3（既存の「禁止は原理原則へ畳む」「tombstone 禁止」の段落を、この原則の下位項目として並べ直す — 見出し語も肯定形にする）
- rules 採用基準（環境固有の罠）に合う理由: substrate が否定形を想起の手がかりとして使うという観測は、この環境で反復して確認されている（ADR-0044 の宣言が効かなかった件、本日の観測）
- memory にも書く: `feedback_write_only_what_to_do.md`（type: feedback、Why に本日の著者発言、How to apply に「rule / skill / memory / ADR を書く・直すとき」）。MEMORY.md に 1 行
- 機械検査は足さない（「しない」の grep は作業作法の記述で誤検知する。判定は adr-reviewer / skill-creator の草稿ゲートが意味的に見る — 両 checklist に 1 項目追加）

## C. Build-or-not 4 問の廃止

| ファイル | 変更 |
|---|---|
| `rules/common/planning.md:7-9` | 「インフラ・機構・計器を新設/拡張する前は存在と大きさを問う（Build-or-not 4 問…）」の箇条を削除 |
| `skills/implementation-chain/SKILL.md:74` | `feat` / `chore` × Build-or-not の発動条件 1 行を削除。chain 表（50-68 行付近）に Build-or-not 行があれば同時に削除 |
| `skills/implementation-chain/SKILL.md:77` | `fix` × 機構ゲート行から「上の Build-or-not 行に従う（judge-tier は 4 問自答、build-tier は agent architect…）」を削り、「足すなら plan にその旨を 1 行書く」に。CA ADR-0095/0098 の根拠句は 1 つ残す |
| `skills/rfc-writer/SKILL.md:82` | 対応表の「Build-or-not（implementation-chain）」行を削除 |
| `agents/architect.md` | A で対応済（ヘッダコメント）。agent 自体は opt-in で残す — task-triage / loop-design-check / harness-boundary / mondo の「contested なら architect」ポインタは触らない |

`hooks/plan-executor-notice.sh` は「実行者の決定」句だけを見るので無関係（grep 済）。
`ADR-0062:103` の「4 問を既存機構の gate 化にも適用する」は履歴として残す。

## D. 記録

1. **ADR-0065** を skill: `adr-writer` で起票（adr-reviewer は skill 内ステップ）。packet:
   - Context: 著者観測 2026-09-14 と根拠頻度の順位 / ADR-0044 の宣言型対処が効かなかった事実 / Build-or-not 行は commit `1d4c4cf`（2026-08-25）で ADR 無しに導入、著者「儀式的で意味がない」
   - Decision: A / B / C / E の要約（ファイル名つき）。全項目を「削除する / 〜に置換する / 〜を書く」の形で書く
   - Review-when: 4 週間後も「拒む」観測が続く → ADR-0044 未決 Alternative「ADR 廃止・仮説台帳化」を実行する / 無人 chain の肥大（CA ADR-0095 型）が再発 → 機構ゲートを build-tier chain 限定で戻す
   - Alternatives: `--safe-mode` の frontier セッション（著者判断: 普段のセッションのままで乗れる形が要件）/ 読み方 protocol の命令形化（ADR-0044 Review-when の第 1 案。宣言を足す方向で、本日の観測と逆）/ ADR 廃止（未決のまま次段）
2. **ADR-0044** に注記: Alternatives「ADR を廃止し…」節と Review-when 節の下に `> **注記（2026-09-14, ADR-0065）**: 再訪条件が発火。照合配線を撤去する段を先に取る`
3. `docs/adr/README.md` の index に 0065 行

## Verify

- `.claude/verify.sh`（harness_lint: rules metadata / `lint_adr_review_when` / bats 全件）
- grep が 0 hit: `Build-or-not` in `rules/ skills/implementation-chain skills/rfc-writer agents/architect.md` / `却下記録の読み方` と `ADR も足場` in `rules/ skills/ agents/ AGENTS.md`（docs/adr と rfcs を除く）/ `変更前に関連 ADR` in `AGENTS.md`
- memory: `MEMORY.md` の全リンク先が存在する（`grep -o '(\./[^)]*)' MEMORY.md` で列挙し `ls`）、削除 14 ファイルが無い
- `rules/common/akc-cycle.md` の新節が 3 行以内で、rule 全体の行数が減っている（rules-rightsize 方向）
- 今回触った全ファイルの diff の追加行に「しない」「ではない」「禁止」「veto」が無い（`git diff | grep '^+' | grep -E 'しない|ではない|禁止|veto'` が空。例外は ADR-0065 の Context で著者発言を引用する箇所のみ）
- commit 時に `harness-lint-precommit` / `verify-precommit` が通る

## 後続（本 plan 外）

- skill: `harness-sync` で公開 copy を同期（akc-cycle repo の自己完結版 `rules/common/akc-cycle.md` は別内容なので触らない）
- search-first の再設計は別セッション

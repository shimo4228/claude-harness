# ADR を「従う文書」から「判断の経緯」へ — 全 repo

Date: 2026-11-07
Research: 本会話の内部調査（file:line は本文に）。Codex（gpt-6-astra）の意見を 1 回取得。

## Context

著者の観測（2026-08-14 / 08-19 / 09-14 / 11-07）: Claude が過去の ADR を理由に新しい発想を止める。
著者の意図は判断の記録であって、将来の決定の拘束ではない（君子豹変、`contemplative-axioms.md` の
Emptiness: directives are provisional）。Claude は substrate として変化を避ける側に傾くので、その傾向を
増幅する機構は取り除き、取るべきリスクを取る形にする。

同じ観測への介入は 2 回。ADR-0044（読み方 protocol の配線）と ADR-0065（配線の撤去）。どちらも
「ADR をどう読むか」の層で、ADR が **どう書かれ、何として扱われるか** は変えなかった。

今回の診断（Claude と Codex の一致点）: ADR は定義では経緯記録なのに、書き方と扱いが rule と同じ。

| 拘束の源 | 場所 |
|---|---|
| ADR の Decision / Review-when / Consequences を「LLM が従う文書」に数える | `rules/common/llm-first-code.md:26-28` |
| Decision を命令形で書く規約 | `skills/adr-writer/SKILL.md:154` |
| Decision が commitment として書かれているかの検査 | `agents/adr-reviewer.md:105` |
| 先行 ADR との override 関係の明示要求 | `agents/adr-reviewer.md:147-151` |
| `Status: accepted` — 現在形の状態語。100 本中 96 が accepted | `docs/adr/*.md`、`docs/adr/README.md` index、`skills/adr-writer/scripts/adr_lint.py:43-57` |
| 方針転換のたびに旧 ADR へ注記・Status 変更・新 ADR | `skills/adr-writer/SKILL.md:26, 242-244` |
| rule の `rationale:` が ADR 番号を根拠として引く | `rules/common/*.md` 冒頭コメント 15 本 |
| Review-when 節の存在 lint | `scripts/hooks/harness_lint.py:479-492` |

現行設計の所有者は既に決まっている: 実物（rule / skill / hook / test / code）と著者の今の指示
（`rules/common/knowledge-staleness.md` 「Written descriptions」、2026-10-26）。記録は理由を持ち、
現行を持たない。この変更は新しい思想でなく、ADR 層だけに残った矛盾を既存の worldview に合わせる作業。

他 repo（2026-11-07 実測、`docs/adr` を持つ repo）:

| repo | 件数 | Review-when | 拘束配線 |
|---|---|---|---|
| ~/.claude | 100 | 58 | 上表 |
| ~/MyAI_Lab/contemplative-agent | 248 | 230 | `CLAUDE.md:13` 機構変更は所有 ADR と script 冒頭を同じ PR で更新（ADR が spec） |
| ~/MyAI_Lab/authorship-strategy | 52 | 0 | 無し |
| ~/MyAI_Lab/agent-knowledge-cycle | 25 | 5 | `CLAUDE.md:104` 必須 section に Status と Relationship to other ADRs |
| ~/MyAI_Lab/agent-attribution-practice | 20 | 0 | `CLAUDE.md:34` 他 repo の対応 ADR を確認、`:63` 関連 ADR を読む |
| ~/MyAI_Lab/daily-research | 19 | 5 | `CLAUDE.md:96` 「再提案の前に読む」 |
| ~/MyAI_Lab/zenn-content | 15 | 6 | rules 2 本が ADR 番号を引く |
| ~/MyAI_Lab/aeon-shop | 12 | 0 | 無し |
| ~/MyAI_Lab/rules-adr0005 | 12 | 0 | 無し |
| ~/MyAI_Lab/contemplative-agent-rules | 10 | 0 | 無し |
| ~/MyAI_Lab/personal-branding | 8 | 5 | 無し |
| ~/MyAI_Lab/existence-proof | 6 | 0 | 無し |
| ~/MyAI_Lab/doctrine-corpus | 5 | 0 | 無し |
| ~/MyAI_Lab/contemplative-mcp | 3 | 0 | 無し |
| ~/MyAI_Lab/attention-not-self | 2 | 1 | 無し |
| ~/MyAI_Lab/daily-quest-generator | 2 | 0 | 無し |
| ~/MyAI_Lab/harness-stocktake-smoke | 1 | 0 | 無し |
| ~/MyAI_Lab/claude-harness | 98 | 56 | 公開 copy。`harness-sync` で同期するので直接編集しない |

## Decision（目標の形）

記録の名前は **判断の経緯（decision history）**、directory は `docs/decision-history/`。

1. **記録は過去形。** 「〜にした」「〜を外した」。現行は実物と今の指示が決める。記録は理由と当時の
   事実を持ち、読むのは経緯を知るとき。新しい判断は旧記録と衝突してよく、旧記録は触らない。
2. **Status 欄を持たない。** 節は Date / Context / Decision / Review-when（任意、失効条件） /
   Alternatives / Consequences。index は Date と Title。
3. **旧記録に注記・Status 変更をしない。** 新しい記録から過去へのリンクは任意（「関連する経緯: 0035」）。
4. **rule の `rationale:` は「今この rule が要る理由」だけ。** 経緯リンクは任意で `history:` に。
5. **番号は継続**（0101〜）。識別子は番号。旧本文の `ADR-NNNN` 表記は歴史としてそのまま。
6. **既存の記録本文は書き換えない。** README 冒頭に 1 行「ここの記録は書かれた日の判断。Status 欄も
   その日の状態」。

## Steps

### Phase 0 — harness（正本。他 repo が使う lint と skill を持つ）

1. `rules/common/llm-first-code.md:26-28`: 「LLM が従う文書」の列挙から ADR の Decision / Review-when /
   Consequences を外す。肯定形規約は残す（書き方の規約と拘束力は別）。著者の 2026-10-11 指示の
   「対象を広げる」意図のうち、書き方だけを残す。
2. `rules/common/akc-cycle.md:32-35` 「ADR の扱い」を「判断の経緯」節に書き換え: 上の Decision 1 を 3 行。
   `rules/README.md` の該当行も合わせる。
3. `git mv docs/adr docs/decision-history`。`docs/decision-history/README.md`: 題名・冒頭 1 行・index から
   Status 列を外す。Review-when・Status の説明は index 生成 script に合わせる。
4. `skills/adr-writer/` → `skills/decision-history/`（`replaces:` に adr-writer）。template から Status を
   外し Decision を過去形に、`:154` の命令形規約を過去形に、`:26` と Edge cases `:242-244` の旧記録への
   注記・Status 変更を削除、filing bar（3 条件）は維持。`scripts/adr_lint.py`: `DEFAULT_SECTIONS` から
   Status を外し、status enum 検査（`:53-80`）を削除。`evals/` の期待値を合わせる。
5. `agents/adr-reviewer.md` → `agents/decision-history-reviewer.md`: §3 を「packet との一致（fidelity）」
   だけに、§7 を「名指しした過去の記録へのリンクが切れていないか」だけに。
6. `scripts/hooks/harness_lint.py:479-492` `lint_adr_review_when` を削除（Review-when は任意）。
   `tests/harness-lint-precommit.bats` の 3 ケースと golden を更新。
7. `rules/common/*.md` 15 本の `rationale:` を書き直す: 今この rule が要る理由 1〜2 文。ADR 番号は
   `history:` へ移すか削除。本文中の `ADR-NNNN` リンクは path を新 directory に張り替え。
8. path 張り替え: `grep -rn "docs/adr\|adr-writer\|adr-reviewer" --include=*.md --include=*.py --include=*.sh
   --include=*.bats --include=*.json .` の全件。主なもの: `CLAUDE.md`、`AGENTS.md`、
   `skills/harness-sync/SKILL.md:45-50`、`skills/context-sync/SKILL.md:36-49`、
   `skills/implementation-chain/SKILL.md`（Doc Sync の「所有 ADR の追補」→「経緯を 1 件書く、任意」）、
   `skills/grill-me/SKILL.md:57,86`、`skills/rfc-writer`、`skills/task-stocktake`、hooks、tests。
9. この変更自体を新形式の最初の記録 `docs/decision-history/0101-*.md` に過去形で書く。
10. memory `MEMORY.md` の ADR 参照 path を張り替える（git 外、手で）。
11. commit: `docs(plan)` → 本体（Verify は `.claude/verify.sh` と bats）。`harness-sync` で claude-harness
    へ同期するのは公開操作なので著者が実行する。

### Phase 1 — 他 repo（harness の skill / lint が新形式になってから）

repo ごとに同じ pattern、1 repo 1 commit。実装は Opus の build session（ADR-0100）。小さい repo
（≤ 25 件）は 1 session が一覧を回し、contemplative-agent（248 件、機構層の凍結規則あり）は別 session。

- `git mv docs/adr docs/decision-history`、README 題名・冒頭 1 行・index の Status 列を外す
- `CLAUDE.md` と `.claude/rules/` の path 張り替え。拘束文の書き換え:
  - contemplative-agent `CLAUDE.md:13` 「所有 ADR と script 冒頭を同じ PR で更新」→ 現行は script 冒頭
    コメントが持つ。記録は任意
  - agent-attribution-practice `CLAUDE.md:34, 63` → 他 repo の記録との照合義務と「関連 ADR を読む」手順を
    削除し、記録の場所だけ残す
  - agent-knowledge-cycle `CLAUDE.md:104` 必須 section から Status と Relationship を外す。AKC は
    「expiry-conditioned knowledge」の概念 repo なので、Review-when は任意のまま残す
  - daily-research `CLAUDE.md:96-97` 「再提案の前に読む」→ 「過去の提案と実測は記録にある」。却下の
    verdict でなく実測値を引く形に
  - zenn-content rules 2 本の `ADR-NNNN` 引用 → path 張り替え、根拠文は理由を本文に
- `.claude/verify.sh` や CI が `docs/adr` path か adr_lint の Status を見ていれば直す
- 公開 repo（DOI 付き: agent-knowledge-cycle / contemplative-agent / authorship-strategy ほか）は path
  変更で外部リンクが切れる。release-doi の次回 release で README の link を更新する。旧 path の stub は
  置かない（機構を増やさない）

### Phase 2 — 観測の記録（gate にしない）

著者が「過去の判断を理由に止められた」と感じたとき、その引用を会話に貼る。session は
`~/.claude/.notes/decision-pull.md` に 1 行（日付 / 依頼 / 止めた発言 / 根拠に挙がった記録）を足す。
今回の変更は git で戻せるので、この記録は次の判断の材料であって今回の gate ではない。

## 代理決定（著者が反転できる）

- 識別子の全面改名（`ADR-NNNN` → 新 prefix）はしない。旧本文・commit message に数千件あり、歴史の
  改変に当たる。番号だけで引く
- 旧記録の過去形書き換えはしない（Codex 同意）
- Review-when 節は残す（任意）。失効条件は拘束でなく「いつ考え直すか」の予約で、expiry-conditioned
  knowledge の worldview と同じ向き
- 公開 repo も directory を改名する。旧 path の stub は置かない

## Out of scope — 同じ種類の機構（著者が選ぶ）

今回触らない。「変化を阻む」機構として同じ検討に乗る候補:

- plan mode が plan の作成にも承認を要する（substrate）。`rules/common/planning.md` の「plan は plan mode
  で」（ADR-0096）を「`docs/plans/` に直接書く」へ戻す案
- `hooks/research-gate.sh` の手順差し込み（ADR-0086 / 0096）
- `skills/implementation-chain/SKILL.md:71` fix × 機構ゲート「修理前に問う」
- agent-knowledge-cycle ADR-0005 Human Approval Gate（挙動を形成する artifact 全てに名前付き sign-off）
- contemplative-agent ADR-0080 機構層の凍結

## Verification

- harness: `.claude/verify.sh`、`bats tests/`、`python3 scripts/hooks/harness_lint.py`、golden の diff を読む
- 全 repo: `grep -rn "docs/adr" .` が 0 件（旧本文内の歴史的言及は除く: `docs/decision-history/` 配下は対象外）
- `adr_lint.py`（改名後）を各 repo の新 directory に `--gate` で通す
- `harness-sync` dry-run の delta が Phase 0 の変更だけであること

## 実行者の決定

Phase 0 はこの session（Fable）が実装する — (a) rule / skill / agent の散文が主体で、lint と test の変更は小さい。Review 群は Opus に降ろす。Phase 1 は Opus の build session に plan を渡す。

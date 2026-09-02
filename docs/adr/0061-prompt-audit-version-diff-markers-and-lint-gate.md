# ADR-0061: prompt-audit が検出した版差 marker を skill-creator §3 規律 + harness_lint 検査 13 として常設する

## Status

accepted

## Date

2026-09-02

## Context

2026-09-02 に `/claude-api prompt-audit`（Anthropic 公式 claude-api skill の subcommand、
target model = Claude Fable 5.1）を `~/.claude` の prompt surface 全体（skills 58 / agents 14 /
rules 13 / CLAUDE.md / settings.json）に対して実行した。結果は 88 件（High 3 / Medium 85）、
44 ファイル +141 / −421 行を適用した。

分布は次のとおり: 1d migration-relative（版差 marker「（2026-08-25 追加）」「Y から降格」
「旧 X は廃止」「2026-08-29 移設」と退役機構の tombstone）55 件 / 1c 過剰指定・反復・strategy
coaching 18 件 / Group 2 history narrative・volatile 9 件 / 1a 圧力語 7 件 / 1f 数値上限 1 件 /
Group 3 1 件。1a の CAPS 圧力語と 1b（think step by step / scratchpad / budget_tokens /
prefill）は grep で 0 件 —
[ADR-0018](./0018-rules-rightsize-for-claude5.md)（2026-07-25、常駐 5,789→2,463 words）と
[ADR-0035](./0035-commit-review-hook-and-rules-rightsize.md) で潰した旧世代向け
over-constraint は再発していない。再発している型は「改修時に前版との差分を本文へ書く」で、
これは skill-creator §3 の文章規律が既にある下で入った — 小さな追記は新規作成ゲート
（skill-creator）を通らないため。

High 3 件の内訳: (1) `skills/release-doi/SKILL.md` の release 手順は
`commit -m "$(cat <<EOF …)"` という heredoc 形式でバージョン管理コマンドを呼んでおり、
harness 自身の PreToolUse hook（skill `git-workflow` がこの heredoc 形式と `$(` の組を
block）と衝突し毎 release で弾かれる runbook だった。(2)
`skills/config-gc/SKILL.md` は L25 で「tracked file は削除、git が undo」と言いつつ L61 と
L113 の例が tracked skill dir を soft-delete していた（ECC 原本 2026-06-24 と著者改修
2026-08-23 の 2 版が同居）。(3) `skills/authorship-strategy/SKILL.md` は L184/L258 で型 (b) を
retired と言いつつ L186 が「badge 面と wiki 面の二刀流が最適配置」と推奨していた。

Fable 5.1 の migration guide（`shared/model-migration.md`）は
「prompts and skills written for prior models are often too prescriptive」
「migration-relative phrasing implies phantom alternatives」を挙げる。

同監査で flag のみ（未適用）の 1 件: `settings.json` の `outputStyle: Concise` が
update-suppressor 型で Claude Code system prompt の「Before you start, say in a line…
Close with a short recap」と直接矛盾する（product 同梱 style のため diff 不可、著者判断待ち）。

監査 report と diff は session scratchpad に保存した（`prompt-audit-2026-09-02.md` /
`.diff`）。repo には残さない。

## Decision

1. `skills/skill-creator/SKILL.md` §3「書き方 — Fable 向け」に 6 規律を追加する: 現行規則
   として書き前版との差分を書かない（as-of 日付は claim にだけ、edit 日付は git と ADR が
   持つ）/ 存在しないものを「やらない」と書かない（tombstone は消し、禁止の実体を正の形に
   書く）/ 経緯は ADR・本文は規則 / 改修は置換であって追記ではない（旧記述を grep して消す）
   / 条件を列挙したら tie-breaker（「迷ったら Y」）を置かない / 例は出力の register を固定
   するので register 例は置かない。§4 草稿ゲートの Hygiene 問に版差 marker・tombstone・
   同一ファイル内 2 版を追加する。
2. `rules/common/skills.md` に常駐 3 行を追加する: 小さな追記でも現行規則として書く — 正本は
   skill-creator §3、機械検査は `harness_lint.py`。
3. `scripts/hooks/harness_lint.py` に検査 13 `lint_version_diff_markers` を追加する。
   `skills/*/SKILL.md`（repo 内）/ `agents/*.md` / `rules/common/*.md` / `CLAUDE.md` の本文
   （frontmatter・code fence 除外）で、同一括弧内に日付 `20\d\d-\d\d-\d\d` と edit 動詞
   （追加|追記|移設|移管|再編|明文化|更新済み|移行済み）が共起する行を exit 3 で止める。
   動詞集合は edit 履歴だけに限定し、退役 / 廃止 / 降格 / 反転 / 復活は現状態の as-of 記述
   にも使われるため含めない（現 tree に正当な as-of 記述 2 例:
   authorship-strategy「2026-08-04 退役、再導入しない」、
   harness-sync「2026-07-31 に退役、ADR-0026」）。tombstone と経緯物語は機械判定できないので
   skill-creator の判断層に残す。bats 3 ケース（marker → exit 3 with line / 退役 as-of →
   exit 0 / fence 内 → exit 0）を追加する。適用後の tree で該当 0 件を baseline clean とする。
   precommit（`hooks/harness-lint-precommit.sh`）と `.claude/verify.sh` で発火する。
4. 監査の 88 件（High 3 / Medium 85）を適用する。Low 15 件は flag のみとし、適用しない。

## Review-when

- 次の Claude model release で `/claude-api prompt-audit` を再実行し、1d migration-relative が
  再び最多カテゴリなら lint の動詞集合を広げる（tombstone 語の追加を検討する）
- lint が正当な as-of 記述（退役日・観測日）を偽陽性で 2 回以上止めたら、動詞集合を狭めるか
  括弧内の共起条件を見直す
- Anthropic の migration guide が「migration-relative phrasing」を有害パターンから外したら
  §3 の規律 1 を再監査する

## Alternatives Considered

### 文章規律のみ（lint なし）

却下: 今回の 55 件は skill-creator §3 に「反復強調・トリビアルな禁止列挙を書かない」の規律が
既にある下で入った。改修時の追記はゲートを通らず、規律の文言では止まらない
（`llm-first-code`「執行者は機械ゲート」）。

### 退役 / 廃止 / 降格 / 反転も lint 対象に含める

却下: 現状態の as-of 記述（`knowledge-staleness` が要求する日付）を巻き込む偽陽性が現 tree に
2 例ある。edit 履歴と as-of の境目は動詞で引けるところまでを機械化する。

### generation-audit skill に統合する

却下: `generation-audit` は runtime 層（system prompt + tool description）との競合照合で、
自作資産内部の cruft 静的検査は別物。`generation-audit` の Related に
`/claude-api prompt-audit` を 1 行ポインタとして置く方が正本を割らない。

### 何もしない（監査結果だけ適用する）

却下: 同型は ADR-0018 後の 5 週間で 55 件蓄積した。次回まで放置すれば同量が再生産される。

## Consequences

### Positive

- 改修時の版差 marker が precommit で止まる（baseline 0 件）
- skill 本文が「現行規則 + 理由 + ADR 番号」の形に収束し、Fable が幻の代替を reconcile する
  思考消費が減る
- 再監査の手順が確定した（model release 時に `/claude-api prompt-audit` を再実行する）

### Negative

- `rules/common/skills.md` の常駐 +3 行
- `harness_lint.py` に regex 1 本が増える（edit 動詞の日本語集合はこの harness の語彙に依存し、
  英語圏の記述「(added 2026-08-25)」は拾わない）
- as-of と edit の境目は動詞で近似しているだけで、「（2026-08-25 決定）」型は通る

### Neutral / Follow-ups

- `outputStyle: Concise` の update-suppressor 矛盾は flag のみ（著者判断待ち）
- `generation-audit` Related への `/claude-api prompt-audit` ポインタ追加は任意
- 監査 report と diff は scratchpad 保存で repo には残さない（commit message に件数を残す）
- [ADR-0018](./0018-rules-rightsize-for-claude5.md)・
  [ADR-0035](./0035-commit-review-hook-and-rules-rightsize.md) の rightsize 系列の第 3 波
  として位置づく（supersede ではなく追加）

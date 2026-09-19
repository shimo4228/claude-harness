# ADR-0071: adr-reviewer の反復指摘を per-ADR evidence script へ降ろす — review-to-lint 第 2 弾（`adr_review_evidence.py`）

## Status

accepted

## Date

2026-09-16

## Context

著者の問い（2026-09-16）は「ADR を別 agent に書かせて review させるのは重い」「ADR の頻度が
多い」の 2 点。判断側（writer agent の要否・ADR 起票基準）は本 ADR の対象外で別途扱う。
本 ADR は著者の明示指示 `/review-to-lint ADR-reviewerの指摘事項をLintに落として` に対する
実施記録。

adr-reviewer の実績は commit 本文に残っている。2026-08-26〜09-15 の harness commit は
毎回 NEEDS REVISION または MAJOR ISSUES を出していた（[ADR-0055](./0055-review-chain-single-pass-regression.md):
5 件反映、[ADR-0063](./0063-rfc-0020-rust-pilot-hooklint.md):
Important 4 + Minor 2、[ADR-0065](./0065-drop-adr-consultation-wiring-and-build-or-not-gate.md):
9 件、[ADR-0069](./0069-boundary-rule-and-judge-merges.md): 4 件。commit `0181fa2` /
`11f8d01` / `dba8f14` / `43c357c` の Review 行）。`skills/adr-writer/references/review-findings.md`
の追記は 2026-08-26 で止まっていたが、これは頻出パターンを蒸留したときだけ足す派生カタログで
一次記録ではない。本 ADR を書いたセッション（2026-09-16）はこれを「reviewer の効果が 3 週間
観測されていない」と誤読し、著者が「毎回何かしら指摘して直させている」と訂正した。writer agent が
本 ADR を描画した際も ADR-0063 のリンク先ファイル名を実在しない名前で書き、`refs.links_broken` が
それを拾った（同日、本 ADR への最初の適用）。

履歴掘削（2 回目。1 回目は 2026-08-29、[RFC-0005](../../rfcs/0005-review-to-lint-rollout-ledger.md)）:
`~/.claude/projects/*/*/subagents/agent-*.jsonl` の mtime ≥ 2026-08-26 から、最終 assistant
message に `**Verdict**` を持ち adr-reviewer の起動文を含むものを抽出した。24 報告 / 4 repo
（レビュー対象 ADR の repo で数えて harness 13、contemplative-agent 8、agent-knowledge-cycle 2、
daily-research 1。1 報告が 3 ADR を扱う例と再レビュー 1 本を含む）/ Critical・Important・Minor
約 200 件。抽出 script は scratchpad で書いて捨てた（ADR-0055
Decision 5「回収機構は作らない」に触れないため）。クラス別の出現報告数（分母 24 報告。
1 報告に同クラスが複数あっても 1 と数える）:

| クラス | 報告数 |
|---|---|
| 数値の出典なし・実測と不一致・分母なし・単位誤り | 18 |
| Review-when が観測不能（計器・判定者・窓・記録先なし） | 17 |
| 引用 ADR / RFC / commit / 行番号の誤りと内容不一致 | 12 |
| 先行 ADR との関係（未名指し・注記なし・Status 未更新・index 不一致） | 11 |
| 有力な代替（特に「何もしない」）の欠落 | 10 |
| Decision と実体の diff の範囲不一致（両方向） | 8 |
| gitignored・repo 外・未追跡・実在しないパスの参照 | 7 |
| 第 2 の記録場所（同じ実測値が SKILL.md 等にもある）の未計上 | 7 |
| 巻き戻しコストの欠落 | 6 |
| 造語・未定義の参照語 | 4 |

既存の機械層との重なりを確認した。`adr_lint.py`（[ADR-0051](./0051-extract-mechanical-adr-checks-into-cross-repo-lint.md)）
は corpus 全体の節・Status・Date・index・命名・numeric_evidence（表・リストの件数対応）を持つ。
`skills/context-sync/scripts/context_checks.py` の `check_context_paths` は repo の context
file 群向けで、`~` と `/` 始まりのパスを除外し fence 内も除外する。`scripts/hooks/harness_lint.py`
の `lint_markdown_links` は `docs/` を含むが commit 時のみで、ADR 番号の実在・注記の往復・
パスの tracked / ignored 分類・diff 範囲・数値の出典は持たない。

search-first（as-of 2026-09-16、<https://github.com/mbeacom/adrkit>）: adrkit は pre-1.0、
Node 22+、MADR 3.x frontmatter / MADR 2.x / Nygard `## Status` を lint し supersession cycle
を検出する。旧 ADR 側の注記の往復、パス分類、diff 範囲照合、数値の出典は README に無い。
ADR-0051 の却下理由（as-of 2026-08-26）は維持される。

免除境界は 6 repo / 256 ADR（harness 70、contemplative-agent 110、agent-knowledge-cycle 24、
daily-research 17、authorship-strategy 23、zenn-content 12。`.ja.md` twin 除外、2026-09-16 実測、
sweep は scratchpad の使い捨て script）に初版を当て、偽陽性の上位を見て調整した。初版 → 調整版: `paths.missing` 3,107 → 1,026（`A/B`・`I/O`・
`anthropics/claude-code` 型の非パスを除外、`./NNNN-*.md` を ADR dir 相対で解決、bare basename
の未解決は `bare_name_unresolved` に分離して flagged から外す）; `numbers.relative_referents`
542 → 31（`now` / `today` / `現時点で` を外し会話参照語だけ残す）; `second_record.hits`
2,382 → 411（`%` を対象外、`*.html` / `*.css` / `*.js` / `*.svg` / `*.lock` を除外、値 ≥ 100
か単位が KB / tokens / セッション / repo 等の場合のみ）; `numbers.unanchored` 702 → 357
（単位なしは comma 付きのみ、1〜2 の小さな列挙と 0% / 100% を除外）。調整後の corpus 合計:
`refs.unresolved` 22（cross-repo 引用「CA ADR-0095」型を含む）、`links_broken` 2、
`line_refs_out_of_range` 3、`paths.ignored` 117、`paths.outside_repo` 190、relation target
518 file のうち往復あり 167 / 言及のみ 157 / 沈黙 194、Review-when の count 条件 59 のうち
記録先ヒントなし 35、Alternatives あり 245 のうち status quo 語あり 102、Decision に削除語
あり 145 のうち巻き戻し語なし 115。gate は無いのでこれらは違反数でなく信号量。

実走（2026-09-16、本 ADR の実装途中の worktree）: 未 commit の ADR-0070 に `--diff worktree` で
当てると `settings.json` を `ignored`
（[ADR-0057](./0057-judge-tier-default-dispatch-and-plan-boundary-advisory.md) で reviewer
が指摘した同型）、同一 worktree diff に ADR-0070 が触れないファイル（本 ADR の実装物。その時点で
2 ファイル、実装が進むほど増える）を `changed_not_mentioned` として検出した。JSON は 1 ADR で
約 400〜600 行（0069 / 0070 / 0071 で 489〜574 行。`diff_scope` と `second_record` は tree の
状態で変わるので固定値ではない）。

実装（2026-09-16）は `skills/adr-writer/scripts/adr_review_evidence.py`（非空・非コメント 856 行（ruff format 後）、
`awk 'NF' … | grep -v '^\s*#' | wc -l`）、tests 20 本（`skills/adr-writer/tests/test_adr_review_evidence.py`、
tmp git repo fixture）。既存 `test_adr_lint.py` 24 本と合わせ `uv run --project skills/adr-writer pytest`
44 pass。ruff（adr-writer pyproject の
select、C901 15、ANN）clean。`harness_lint.py` clean、
`adr_lint.py --gate --sections-from 44 --require-review-when-from 44` exit 0。実行者は
judge-tier セッション in-session（implementation-chain 例外 (c) 著者の明示指示）。

## Decision

1. `skills/adr-writer/scripts/adr_review_evidence.py` を新設する。入力は ADR 1 本（番号か
   パス）と任意の `--diff staged|worktree|<range>`、出力は JSON、exit 0（読めないときだけ 2）。
   `--gate` は持たない — 各 key は判断を要する信号で、判定は書き手（Step 4.5）と adr-reviewer
   （Step 0）が持つ。key: `refs`（ADR / RFC 番号の実在、Markdown link の解決）/ `relations`
   （Status と本文から取った forward target ごとに、旧 ADR 側の Status が指し返すか・日付つき
   注記があるか・言及だけか、自 ADR への inbound、index 行、注記書式の適合）/ `paths`
   （tracked / tracked_via_basename / untracked / ignored / missing / outside_repo /
   bare_name_unresolved / ambiguous_basename / metavariable、`file:line` 引用は行の実文を出す）/
   `diff_scope`（変更ファイルと ADR が名指すパスの両方向差）/ `numbers`（段落に日付・コマンド・
   sha・path:line・URL・実測語・分数のどれも無い数値、分母なし百分率、会話参照語）/
   `review_when`（count・期間条件の行と記録先ヒント）/ `alternatives`（status quo 語の有無、
   Decision の機構語数）/ `consequences`（小見出し、Decision の削除語数、巻き戻し語、第 2
   記録語）/ `second_record`（ADR の実測値が ADR dir 外の tracked file にもある箇所）。
2. code / LLM の境界を切る。実在・往復・分類・範囲差・出現位置は code。引用内容の一致、
   Context の後付け、藁人形、Review-when が観測可能か、第 2 記録の drift 扱い、full / partial
   の判定根拠、造語の出所は LLM に残す。「迷う項目は semantic に倒す」（review-to-lint §1）に
   従い、`review_when.venue_hint` と `alternatives.status_quo_present` は verdict にしない。
3. 実行座標を skill / agent のステップに置く: adr-writer Step 4.5（`skills/adr-writer/SKILL.md`。
   書き時、`--diff worktree`。書き手が直せる key を列挙）と adr-reviewer Step 0
   （`agents/adr-reviewer.md`。key → 基準 §番号の転記表）。`verify.sh` / commit hook には
   配線しない（ADR-0051 Decision 2 の課税判断を継ぐ）。
4. adr-reviewer の基準 §3 / §4 / §6 / §7 / §8 に対応 key を書き、数え直しを止める。基準文は
   残す（事例と基準を複製しない — ADR-0051 Decision 3）。同じ diff に同居する §8 の禁止条項の
   緩和行は [ADR-0070](./0070-relax-positive-form-rule-and-verbatim-builtin-overrides.md) の
   所有で、本 ADR は触れない。
5. `skills/adr-writer/references/review-findings.md` に §8（Decision と diff の範囲不一致）と
   §9（巻き戻しコスト・第 2 の記録場所）を追加し、冒頭に §1 / §2 / §4 / §5 / §6 / §7 と key の
   対応を書く。
6. `rfcs/0005-review-to-lint-rollout-ledger.md` に #17（実施済、本 ADR）と「履歴掘削の実測
   （2026-09-16）」を記録する。#14
   （同一の値の複数箇所ハードコード）は ADR スコープ分だけ `second_record` に吸収し、
   hook / skill 層は保留のまま。
7. ADR-0055 Decision 5 の再訪条件（手調査の 2 回目要求）は本作業で成立した。本 ADR では
   抽出 script を作らず、3 回目が要求されたときに ADR-0055 の supersede 込みで提案する
   （著者判断）。ADR-0055 Decision 5 の下に日付つき注記を置く。

## Review-when

- 本 ADR 以降の adr-reviewer 報告 5 本のうち、`refs` / `paths.flagged` / `relations` の key で
  機械的に出るはずのクラス（実在しない番号・gitignored パス・注記なし）が Critical /
  Important に 2 本以上残っていたら、regex か配線を見直す。記録先は各 commit 本文の Review 行、
  判定者は判断役（次の adr-writer 改修時に数える）。
- 新しい corpus で `numbers.unanchored` が 1 ADR あたり 10 件を超える報告が続いたら閾値
  （comma 付き・単位付き・値 ≥ 100）を上げる。記録先はその ADR の commit 本文。
- substrate が ADR corpus のクロスリファレンス検査（番号の実在・supersede の往復）を native に
  持ったら、該当 key を退役する（Scaffold Dissolution downward）。
- adrkit が frontmatter 無しの Nygard 形式を移行無しで lint し、旧 ADR 側の注記の往復を検査する
  ようになったら再照合する（as-of 2026-09-16 の README では無い）。

## Alternatives Considered

### `adr_lint.py` に同居させる

却下: adr_lint は corpus 全体を見て `--gate` を持ち、こちらは ADR 1 本の evidence のみで
契約が違う。非空・非コメント 400 行の script に本件（同じ物差しで 856 行、2026-09-19 ruff format 後に再測）を足すと
1 ファイルの locality を壊す（llm-first-code の context 経済）。

### `verify.sh` / commit hook へ常時配線

却下: ADR を触らない commit にも毎回課税する。ADR-0051 Decision 2 と同じ判断。形骸化が観測
されたら再訪（review-to-lint §5）。

### adrkit 採用

却下（as-of 2026-09-16）: 反復クラスの検査（注記の往復・パス分類・diff 範囲・数値の出典）が
無く、Node 22+ 依存、pre-1.0。再訪条件は Review-when に置く。

### adr-reviewer を退役し、チェックリストを adr-writer skill の書き時予防へ全面吸収する

却下: 2026-08-26 以降の 24 報告は全件 NEEDS REVISION 以上で、指摘の中心（数値の一致、
先行 ADR との関係、Review-when の観測可能性）は主ループが自分の文に対して構造的に盲目な
semantic 判定。fresh context の効果は commit 本文に残っている。ADR-0051 Alternatives
「レビュー知見の writer skill への全面吸収」と同じ結論。

### 何もしない（reviewer が毎回手で集める）

却下: 同じクラスを 3 週間・24 報告で集め直しており、集める部分（実在・往復・分類・範囲）は
判定を含まない。

### Review-when の観測可能性を regex で判定する（`venue_hint` を verdict にする）

却下: 判定の入力は「count の比較対象として何が固定か」で、文面からは決まらない（ADR-0046 の
事例）。count 条件の列挙までに留める。

### 抽出 script（transcript → reviewer 報告）を harness に置く

未決 — 再訪条件: 手調査の 3 回目が要求されたとき。ADR-0055 Decision 5 の supersede を伴うので
著者判断。

## Consequences

### Positive

- reviewer の注意が semantic 判定（後付け・藁人形・観測可能性・引用内容の一致）に集中する。
  数え直し（番号の実在、注記の有無、パスの存在、diff のファイル列挙）は JSON の行を開く作業
  になる。
- 書き手が Step 4.5 で 7 クラス（実在しない番号・切れたリンク・実在しないパス・gitignored
  根拠・行番号の範囲外・分母なし百分率・会話参照・diff の巻き込み）を reviewer の前に直せる。
- git 以外に依存が無く、README template の形にも依存しないので、他 5 repo の ADR corpus に
  そのまま動く（免除境界の実測は 6 repo で取った）。

### Negative

- 第 2 の記録場所: クラス別頻度は本 ADR Context（正本）、RFC-0005 #17（1 行）、
  review-findings §8 / §9（事例 2 件ずつ）の 3 箇所に載る。後 2 者は pointer と事例で、
  数値を直すときは本 ADR だけを直す。
- reviewer の入力が増える: JSON は 1 ADR で約 400〜600 行。転記表が無ければ読み飛ばされるので、
  Step 0 の表がその契約。`numbers.unanchored` は段落単位の anchor 判定なので、日付のある段落の
  誤った数値（本 ADR の初稿の test 本数 21 / 23 → 実測 20 / 24）は拾わない — `adr_lint` の
  `numeric_evidence.unpaired` を併読する（Step 0 表に明記）。
- 閾値は 2026-09-16 の 6 repo で調整した値で、`paths.missing` は歴史 ADR では退役済みファイル
  を多数拾う（1,026 / 256 ADR）— 書き時・レビュー時の新規 ADR 向けの信号で、corpus 監査には
  使わない。`bare_name_unresolved`（599）は runtime 成果物名と retired file を区別できないので
  flagged に含めない。
- git 管理外の tree では tracked 判定が全て missing になる。skill 経由しない ADR 編集には
  効かない（ADR-0051 Negative と同型）。
- script 本体は 856 行（非空・非コメント、2026-09-19 ruff format 後に再測）で adr-writer sub-project の 2 本目。
  tests 20 本が保存層。
- 巻き戻しは script と tests の削除、および `agents/adr-reviewer.md` / `skills/adr-writer/SKILL.md` /
  `review-findings.md` / RFC-0005 / index 行の revert。全て git 追跡下で、コストは 1 commit の revert。

### Neutral / Follow-ups

- `adr_lint.py` との重複は無い（key が別）。`harness_lint.lint_markdown_links` と
  `refs.links_broken` は `docs/` で重なるが、片方は commit gate、片方は書き時 evidence で、
  判定は同じ「存在」なので drift しない。
- 判断側の問い（adr-writer agent の要否、ADR 起票の足切り）は本 ADR の対象外。別 ADR で扱う。

  > **注記（2026-09-19, [ADR-0072](./0072-retire-adr-writer-agent-and-narrow-adr-filing.md)）**: 両方を
  > ADR-0072 が決めた（agent 退役、起票 2 条件）。本 ADR の Step 4.5 / Step 0 配線はそのまま。
- RFC-0005 #14 の hook / skill 層、#13 / #15 は保留のまま。

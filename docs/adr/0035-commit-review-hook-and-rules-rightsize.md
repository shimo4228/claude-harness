# ADR-0035: Commit 前 Review / Verify reminder の薄型化と rules/ の再 rightsize

## Status

accepted

## Date

2026-08-02

## Context

implementation-chain の Review reminder は、rules、hook、skill の 3 層で重複していた。
[ADR-0018](./0018-rules-rightsize-for-claude5.md) が review 手順を rules から移した後、feat / fix
あたりの codex-review 利用率は 0.54 から 0.20 に低下した。
[ADR-0027](./0027-restore-review-execution-check-to-verify-gate.md) は reviewer 名簿を rules に戻し、
[ADR-0028](./0028-review-notice-full-scope-and-adr-reviewer.md) は commit hook の発火カバレッジを
13% から 93% に引き上げた。ADR index の 89% は、ADR-0028 本文の 76 / 82 commit = 93% に
対する表記差であり、本 ADR では本文の値へ訂正する。

[ADR-0034](./0034-move-review-check-before-the-approval-gate.md) が追加した Stop advisory は、
827 bytes の同じメッセージを反復した。それ以前から存在した 3 本の Stop hook は stderr に
出力していたため、通知は debug log にしか届いていなかった。Review reminder を複数の層と
複数の時点に置く構成は、常駐コンテキスト、反復出力、正本の drift を同時に生んでいた。

2026-08-02 の現行 session-level instruction は、一般的な reasoning / debugging の進行を
substrate に委ね、blocking question は安全性または有用性を失う場合に限る方向を示していた。
これは安定した product contract ではなく、この時点の runtime observation からの推論である。
その既定に対し、custom human-gate は一律の停止を追加して競合していた。個人 harness は PR workflow を持たない
direct-main の履歴で運用されている。さらに `~/.claude` は live config であり、PR merge を
導入してもローカルでの有効化を gate できない。

hook を薄型化する過程で、global skill `when-code-when-llm` の構造 / 意味分離を一般原則として
適用したこと自体が、単純な reminder に diff 分類と Git 解析を持たせる過剰設計を後押ししたと
ユーザーが判断した。この軸は Contemplative Agent には適合するが、global harness の全 task に
常設する必要はないという明示的な退役要求を受けた。

## Decision

1. `hooks/review-chain-notice.sh` は `git commit` / `git revert` / `git merge` の
   PreToolUse だけに残す。diff・path・repo を解析せず、Review / Verify の完了を問い、未完了なら
   skill: `implementation-chain` を案内するだけの薄い reminder とする。
2. `hooks/review-chain-notice.sh` の Stop branch を退役する。加えて `evidence-file-notice` と
   既存の Stop hook 3 本、合計 4 本の advisory script を退役する。
3. reviewer roster と chain-level の Verify 順序・カテゴリは `skills/implementation-chain/SKILL.md`
   を正本とし、rules と hook には複製しない。repo 固有の Verify 実装は `.claude/verify.sh` が正本。
   custom approval gate は削除し、commit / publish の authority は task request と substrate に
   従わせる。通常の個人実装に PR を導入しない。
4. `rules/common/human-gate.md`、`rules/common/output-register.md`、
   `rules/common/patterns.md`、`rules/common/hooks.md` を退役する。残る rules は環境固有の事実、
   wiring、trap に絞る。
5. `rules/common/contemplative-axioms.md` は verbatim のまま保持する。
   `rules/common/akc-cycle.md` の Scaffold Dissolution 定義も、live skill が import しているため
   保持する。
6. human-gate repo に retirement note を公開し、claude-harness を同期する。圧縮した
   `rules/common/akc-cycle.md` は self-contained distribution repo へ同期しない。
7. global skill `when-code-when-llm` を退役する。この判断軸は Contemplative Agent には適合するが、
   global harness では局所的な構造 / 意味分離を一般原則へ膨らませ、hook の過剰設計を誘発した。
   standalone repo は研究履歴として残すが、global skill の同期対象から外す。

## Alternatives Considered

### Review hook を削除し、名簿を rules に戻す

commit という時点に結びつく確認は hook に属するため却下した。93% は退役した classifier の
historical file coverage であり、新しい固定 reminder の command-detection coverage は未測定である。

### rules と hook の重複を残す

常駐コンテキストを消費し続け、名簿 drift も残るため却下した。

### hook が diff を分類して reviewer 名簿を生成する

発火時刻の通知に不要な Git target 解決・diff 分類・件数集計を hook に持ち込み、依存設定などの
分類漏れと hostile repository config の攻撃面を増やすため却下した。hook は時刻、skill は手順を持つ。

### fingerprint suppression を加えて Stop hook を復帰する

commit 時の確認で足り、session を反復走査する必要がないため却下した。

### human approval を PR merge に移す

solo direct-main workflow に ceremony を加える一方、`~/.claude` の変更は merge 前から live で
あるため却下した。

### commit 前の human approval を残す

task-level authorization と substrate defaults に authority を委ねるため却下した。

### Scaffold Dissolution を削除または移設する

3 つの live skill がローカル定義を import しているため却下した。

### when-code-when-llm の trigger を狭めて global に残す

description を狭めても global skill listing と参照網は残り、局所判断を harness-wide doctrine に
昇格させる誘因を消せない。Contemplative Agent と standalone repo に研究履歴を残せるため却下した。

## Consequences

### Positive

- reviewer roster と chain-level の Verify 順序・カテゴリが implementation-chain 1 箇所にまとまる
- reminder が repository 内容を読まず、固定文だけを返す
- Contemplative Agent 固有の判断軸が global task を過剰に規定しなくなる
- resident context が減る
- advisory Stop output の反復がなくなる
- custom approval gate による摩擦がなくなる
- direct-main flow を維持できる

### Negative

- commit hook が失敗すると commit 時点の implementation-chain 再確認がなくなる
- Claude Code の Bash tool を経由しない commit は引き続き検出できない
- human-gate の退役により、task authorization の範囲では作業が継続するように挙動が変わる
- `when-code-when-llm` を明示的に必要とする作業は、global skill から自動では発火しなくなる
- 過去 ADR のリンクには retirement annotation が必要になる
- metrics に commit ID と session ID がないため、commit reminder の効果は day × repo 粒度でしか
  測れない

### Neutral / Follow-ups

- feat / fix commit を 20 件測定し、codex-review / feat-fix が 0.35 未満なら
  `rules/common/planning.md` に implementation-chain の明示的な起動命令を復元する。名簿自体は
  skill に置いたままにする。20 件と 0.35 は統計的に導出した閾値ではなく、
  短期に再点検でき、rules 移行後に観測した 0.20 を明確に上回ることを求める著者選択の運用値である
- Stop hook は測定結果にかかわらず復元しない
- ~~T-GIT-HOSTILE-CONFIG と T-SIGPIPE-HEAD-PIPE は deferred のまま残す~~ —— **2026-08-08 に両方解決** ([ADR-0037](0037-publish-harness-adrs-and-remediate-git-hostile-config.md))。commit 面 5 hook の敵対的 .git/config を無害化した

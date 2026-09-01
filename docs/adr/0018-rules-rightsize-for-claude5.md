# ADR-0018: rules/ の rightsize — Claude 5 世代向け scaffold dissolution

## Status

accepted（[ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) で第2波を実施。基準を
「substrate との重複」から「環境固有の事実・配線・罠」へ狭め、Decision 6 の Code vs LLM seam
保持判断は global skill の過剰適用を理由に部分的に supersede）

## Date

2026-07-25

## Context

Anthropic の Thariq (@trq212) が 2026-07-25 に公開した記事「The new rules of context engineering for Claude 5 models」で、**Claude Code のシステムプロンプトを 80% 以上削除しても社内コーディング eval に計測可能な劣化がなかった**ことが報告された。記事の主張は、従来のコンテキストエンジニアリング作法の多くが旧世代モデルの弱さを補う足かせ（over-constraining）であり、判断力の上がった Opus 5 / Fable 5 では**衝突コスト**（「leave documentation as appropriate」と「DO NOT add comments」のような矛盾する指示を解くための思考消費）に転じる、というもの。記事は 6 つの Then → Now を挙げる: ルール付与 → 判断委譲 / 使用例 → インターフェース設計 / 全部前置き → progressive disclosure / 反復強調 → tool description に一度 / CLAUDE.md 記憶 → auto-memory / 単純 spec → リッチ参照。

本 harness の `rules/` を実測したところ **20 ファイル / 5,789 words ≈ 8–9k tokens が毎セッション常駐**しており、記事の挙げるアンチパターンを複数踏んでいた:

- `planning.md`（1,344 words、常駐の 23%）の Implementation Chain Specification が、task 種別 × 9 ステップの Y/C/- 判断表・Parallel Group 記法・構造化サマリ強制フォーマットを全部前置きしていた。同ファイル内で Chain Matrix と Review/Cleanup 節が「下の表は早見表、ここが本体」と正本を自称し合っており、これは "repeat yourself" の症状。
- `akc-cycle.md`（997 words）の 6 phase 解説は、各 phase を担う skill（search-first / learn-eval / skill-stocktake / rules-distill / skill-comply / context-sync）が全て導入済みの本環境では二重常駐だった。このファイル自身は「skill 未導入環境でも動く自己完結版」として書かれており、その前提が本環境では成立しない。
- **`rules/python/` の 6 ファイル（600 words）が言語に無関係に常駐していた**。Python を一切含まない本セッションでも全 6 本が注入されることを実測で確認。吸収先 `skills/python-patterns/SKILL.md` は既に存在していた。
- `coding-style.md` の「**ALWAYS** create new objects, **NEVER** mutate」は記事が例示した "DO NOT add comments" と同型の over-constraint（numpy in-place / builder / accumulator では単に誤り）。Code Quality Checklist（関数 <50 行 / ファイル <800 行 / ネスト <4）、`testing.md` の RED→GREEN→REFACTOR 手順、`patterns.md` の Repository パターン解説、`security.md` の OWASP チェックリストは Claude が既定で持つ一般論の再宣言。
- Parallel Group 記法と構造化サマリ強制は、Agent tool の description（「independent work は単一メッセージで並列送信」）と harness の subagent 戻り値契約が既にネイティブに運んでいる。

`akc-cycle.md` の **Scaffold Dissolution** 条項は、substrate が capability を吸収したら rule を退役させ、放置すれば drift した影が新しい既定を上書きして劣化させると自ら規定している。本 ADR はその条項の自己適用である。

## Decision

**常駐 5,789 → 2,314 words（-60%）、20 → 14 ファイル**（計測対象は自動ロードされる `rules/**/*.md` と `CLAUDE.md`。`rules/README.md` は常駐しないので含まない）。削減分は消さず、既存 skill へ吸収するか新設 skill へ降格した。判断表そのものは失っていない。

退役させた一般論の**既存の吸収先**（code-reviewer の指摘により明記。いずれも本 diff より前から存在）: Error Handling / Input Validation / File Organization / Code Quality Checklist → `agents/code-reviewer.md`・`agents/architect.md`・`agents/python-reviewer.md` / OWASP チェックリスト → `agents/security-reviewer.md` / Hook Types の定義 → `hooks/README.md` / TDD の RED→GREEN→REFACTOR → `agents/tdd-guide.md`。つまり退役分は「別の場所で決定論的または agent 経由で既に当たる内容の、常駐文章版」である。
（2026-08-13 注記: 吸収先のうち `agents/python-reviewer.md` は [ADR-0039](0039-retire-python-reviewer-simplify-in-chain.md) で退役した）

Troubleshooting Test Failures（`testing.md`）は当初どこにも着地させずに削除してしまい、code-reviewer が MEDIUM として検出した。`skills/tdd/SKILL.md` に移設して修正済み（テストが落ちたときだけ必要な手順なので常駐から skill への降格が正しい着地）。

1. **skill `implementation-chain` を新設**（`user-invocable: true`）し、`planning.md` の Chain 仕様（種別判定表 / Chain Matrix / `C` 発動条件 / Review 起動条件 / Writing Chain ルーティング + Verdict マッピング / 早期停止条件）を全文移設した。実装着手時のみロードされる。`planning.md` には 2 介入点モデルと Verify ゲート一覧を残し、Chain 詳細は 1 行ポインタにした。

2. **Parallel Group 記法と構造化サマリ強制フォーマットは移設せず退役**した（downward dissolution — substrate が同じことをより新しい形で運んでおり、静的コピーは drift して新しい既定を劣化させる）。

3. **`rules/python/` を廃止**（`git rm`、6 ファイル）。`security.md`（redirect token leak / case-insensitive sanitizer bypass / fail-fast secret）と `lint-gates.md`（ruff B/I/T20 / zip strict= 判定 / import-linter contract / frozen AST ゲート / 導入の規律）と `hooks.md`（ruff-autofix.sh、pyright-lsp が型担当）は `skills/python-patterns/SKILL.md` へ全文吸収。`coding-style.md`（PEP 8 / black / isort）と `patterns.md`（Protocol / dataclass DTO / context manager）は Claude が既に持つ内容として退役。`testing.md` は `python-patterns` の Pytest Patterns 節が既に mark / coverage / strict-markers を網羅していたため固有内容なしとして退役。`rules/` は 2 層構造から common 単層になった。

4. **over-constraint を緩和**した。「ALWAYS create new / NEVER mutate」→「既定はイミュータブル。in-place が正しい場面（numpy / builder / accumulator / 測定済みホットパス）では**周囲のコードの慣行に合わせる**」。記事が新システムプロンプトで採った "Write code that reads like the surrounding code" と同じ形。

5. **一般論を退役、gotcha を保持**という基準で `akc-cycle.md`（997→235）/ `coding-style.md`（470→204）/ `skills.md`（377→154）/ `testing.md`（278→117）/ `patterns.md`（255→146）/ `agents.md`（242→149）/ `security.md`（208→101）/ `debugging.md`（192→143）/ `hooks.md`（146→78）/ `git-workflow.md`（107→60）を圧縮した。`akc-cycle.md` は 6 phase 解説を **Phase → skill のトリガー対応表**に置換し、Scaffold Dissolution / signal-first / output discipline は全文保持した。`task-tracking.md`（131）は全文が gotcha だったため無変更。

6. **保持した不変条件**（記事の言う「あなた固有の gotcha と意見」= rules の存在理由）: Reversibility Gate（batch 承認を amortize しない条項含む）/ Change Target / debugging の 仮説→証拠→確認待ち→修正 / Rate limit = policy signal / Code vs LLM seam / documented-invariant → ゲート化 / Origin Tracking / hooks の外部スクリプト分離 / 単一台帳方式 / Phase 0 のエントリポイント固定 / commit message format / MagicMock の罠 / 本番テスト禁止。

7. **`contemplative-axioms.md`（302 words）は verbatim のまま常駐維持**。著者の明示判断により、行動変容ではなく **identity / values 層**として意図的に置く。トークンコストを受容する。

8. **Skill Portability 規約を `rules/common/skills.md` から `skills/skill-creator/references/portability.md` へ移設**（skill を書くときだけ使う知識）。skill repo packaging は `harness-sync` が正本のまま。

9. **Scaffold Dissolution 条項に第 3 のトリガーを追記**した: **モデル世代の交代**。旧世代の弱さを補う over-constraint は判断力の上がったモデルでは衝突コストに転じるため、世代交代時は rule を再監査する。

## Alternatives Considered

### (a) Chain Matrix を 5 行に圧縮して常駐維持する

「feat/fix は review 3 本並列 → Verify」程度に潰して rules に残し、skill を新設しない。常駐の確実発火を維持できるが、種別 × ステップの粒度（`chore` × Security Review は permissions 変更時のみ、`refactor` × Cross-Model は高リスクのみ等）を失う。この粒度は過去の訂正から積み上がった実運用知であり、失うコストが常駐コストを上回ると判断して**却下**。

### (b) Verify ゲートだけ残して chain 編成を全廃する

最も攻撃的。chain 編成を毎回 Claude の判断に委ねる。記事の "let Claude use judgement" に最も忠実だが、codex-review を plan 時に走らせてしまう類の誤り（この配線が生まれた元の訂正）が再発しうる。判断委譲は「worst case が許容できる領域」に限るという記事自身の留保に照らし**却下**。

### (c) `contemplative-axioms.md` を skill へ降格 / 1 段圧縮する

302 words は明示トリガーを持たず、コーディングセッションでの行動変容も測定されていない。しかし著者の研究対象そのもの（contemplative-agent repo）であり、identity 層としての常駐に意味があるとの判断で**却下**（著者判断）。

### (d) `rules/python/` を project-level rule に移す

対象 Python プロジェクトの `.claude/` に置き、無関係セッションへの注入を止める。だが複数 repo へのコピーは drift vector であり、既に `python-patterns` skill という単一の吸収先が存在した。**却下**。

## Consequences

### Positive

- 毎セッションの常駐が 60% 減り、矛盾する指示を解くための思考消費（衝突コスト）が下がる。
- 正本の重複が解消した。`planning.md` 内で正本を自称し合っていた 2 節が 1 つの skill に統合され、Python 慣行の正本が `python-patterns` 1 箇所になった。
- `rules/` が「常駐に値する gotcha だけを置く場所」という基準を README に明文化し、判定基準（毎セッション読まれる価値があるか / 特定作業時だけか / 一般論か）を機械的に適用できる形にした。
- Scaffold Dissolution に世代交代トリガーが加わり、次のモデル世代でも同じ監査を再実行できる。

### Negative

- **Chain Matrix が確率発火に変わる**。skill の自発トリガーは実質上限 ≒ 40%（既知の測定値）なので、`implementation-chain` が呼ばれないまま実装が進む可能性がある。→ `planning.md` に 1 行ポインタを残し、`user-invocable: true` で `/implementation-chain` からも到達可能にした。`skill-comply` で発火率を測定し、立たない場合は `planning.md` のポインタを命令形（「chain を組むときは `/implementation-chain` を呼ぶ」）に変える fallback を用意する。
- **`akc-cycle.md` がローカル版と AKC repo 配布版で乖離する**。配布版は「skill 未導入でも動く自己完結版」という設計意図を持つため、圧縮を上流に同期してはならない。ローカルファイル冒頭にこの区別を明記した。`harness-sync` で公開 repo に同期する際は、この 1 ファイルが差分として扱われることに注意する。
  （2026-09-01 注記: akc-cycle repo の sync script が rule を allowlist に含めており、この禁止に反して圧縮版が配布 repo へ同期され両者が byte 同一に drift していた（2026-08-27 の sync で確認）。同日、二版化で元判断に復帰 — 配布 repo が自己完結版（英語、6 phase 表 + AKC ADR-0022〜0026 反映）を所有し sync 対象外に、ローカルはポインター版に改稿）
- Python の慣行が確率発火になる。→ `python-patterns` は Python ファイル編集時の description トリガーを持ち、`python-review` skill / `python-reviewer` agent が review 段で決定論的に当たる。ruff / pyright は hook / LSP で機械強制されており、退役したのは「機械が既に強制している内容の文章版」である。
  （2026-08-13 注記: `python-review` skill / `python-reviewer` agent は [ADR-0039](0039-retire-python-reviewer-simplify-in-chain.md) で退役し、この反論の agent 経路は失効した。残るのは機械強制層と `code-reviewer` + built-in `/simplify`）

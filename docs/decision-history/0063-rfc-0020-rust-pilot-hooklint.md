# ADR-0063: RFC-0020 pilot — hooks/*.sh の兄弟一貫性 lint `hooklint` を Rust で新設し、size 上限を 400 → 600 行に引き直す

## Status

accepted

## Date

2026-09-06

## Context

[RFC-0020](../../rfcs/0020-rust-for-resident-infra.md)（accepted 2026-09-06）は「harness の新規常駐
道具は Rust で書き、それを pilot とする」という greenfield 方針を定めた。著者は同日、発火条件 2
（新規常駐道具の機会）を能動的に立て、judge-tier（Fable）の plan session が pilot 対象・計測最小
セット・撤退条件を決め、build-tier（Opus 5、effort medium）の新規セッションへ dispatch した
（三役: [ADR-0043](./0043-task-triage-loop-judge-build-human.md) /
[ADR-0057](./0057-judge-tier-default-dispatch-and-plan-boundary-advisory.md)）。

pilot 対象の選定では、harness で「今ちょうど要る」新規常駐道具は 1 つだけ実需の producer を
持っていた — `rfcs/0005-review-to-lint-rollout-ledger.md`（review-to-lint rollout ledger）の候補
#13（兄弟 hook 群への防御イディオム横展開漏れ: `git` の `-c core.fsmonitor=` guard、
`| head -N` の SIGPIPE guard）と #15（helper 不在・`source` 失敗で検査が黙って無効化される
fail-open）。`rfcs/0005-review-to-lint-rollout-ledger.md:33` / `:35` によれば reviewer 履歴掘削
（2026-08-29）で各 6 セッションが反復指摘しており、修正は都度採用済みだが戻りを止める ratchet
が無い。素の grep は 7 hook 中 2 本が偽陽性（regex や block メッセージ文字列リテラル内の一致）を
出し、コメント・文字列を除外する shell 字句解析が要る — parser 型の道具である。発火条件「次に
hooks/ を触るとき」は、この pilot 自身が hooks/ の守り手を建てることで立てた（自己充足であること
をここに記録する）。

却下した他候補: triage digest 生成 script（`tests/golden/README.md` が凍結漏れとして挙げていた）
は digest 本文が LLM prose でセッション応答へ移り（ADR-0045 Decision 3 の 2026-08-30 注記）、著者
が「判断待ちのファイル永続化はしない」と確認済みのため生成器に実需が無い。重複リテラル検出
（RFC-0005 #14）は出力判定に毎回 LLM が要り、常設の commit gate に載らない。claims.py の時刻注入口
は既存移行で RFC-0020 発火条件 3 の対象であり、本 pilot の対象ではない。

前提は plan session（2026-09-06）が実測した: cargo / rustup / rustc は既に導入済み
（`~/.cargo/bin`、rustc 1.97.1、aarch64）— RFC-0020 の Drawback「cargo/rustup が新規依存」は半分
解消済み。`harness_lint.py --root .` は 182 ms、`python3 -c pass` は 21 ms。`|| exit 0` /
`|| true` は hooks/*.sh に 91 箇所あり、大半は matcher gating の正当な早期 exit で、一律に咎める
rule は飽和する（measurement-discipline 原則 3）。

事前登録した撤退条件（plan、2026-09-06）は次の 5 つ: (1) build が 2 セッション以内 / bounce 2 回
以内で受入条件に達しない (2) `src/` が 400 行を超える、または外部 crate 無しで現行 tree の偽陽性を
0 にできない (3) cold build が 60 s を超える、または verify.sh full run の増分が 30 s を超える
(4) 無人経路が黙って素通りする形しか作れない（fail-closed 不成立） (5) binary 実行が
`python3 -c pass`（21 ms）より遅い。

## Decision

1. `scripts/hooklint/`（Rust、std のみ、外部 crate 0）を新設する。`hooks/*.sh` を字句解析
   （コメント / 単引用 / 二引用 / heredoc / command substitution / backtick / 算術展開を区別、
   構文木は持たない）し、simple command 単位で 3 rule を当てる: `GIT_SAFE`（コマンド位置の `git`
   に `-c core.fsmonitor=` か `"${GIT_SAFE[@]}"` が無ければ違反、block）/ `HEAD_SIGPIPE`
   （パイプライン中の `head -N` が `|| true` で閉じなければ違反、block）/ `FAIL_OPEN`（block 可能
   hook 内の `source … || exit 0`、`[ -f/-x … ] || exit 0` を列挙、report-only — 発火率較正前は
   block しない）。出力は `hooks/<file>:<line>: <RULE> <message>` + 末尾
   `hooklint: N finding(s), M report-only`、exit 0 / 3（違反）/ 1（エラー）。golden は
   `tests/golden/hooklint/` + `tests/golden-hooklint.bats`。

   > **注記（2026-09-26, ADR-0082）**: FAIL_OPEN は block に昇格した。本項の「report-only — 発火率
   > 較正前は block しない」は FAIL_OPEN については失効。意図した素通しは同じ行の
   > `# hooklint: fail-open <理由>` で書く。出力書式（末尾行の `M report-only`）は不変で、現行 rule では
   > M = 0。GIT_SAFE / HEAD_SIGPIPE の記述と exit code は有効

2. 配線は `.claude/verify.sh`（hooks/*.sh は無改変）。staged mode は binary 実行のみ（build しない）、
   binary が不在 / stale のとき hooks/*.sh か scripts/hooklint/** が staged なら FAIL、そうでなければ
   warn。full mode は `cargo fmt --check` → `clippy -D warnings` → `test` → `build` → 実行、cargo
   不在は shellcheck 不在と同型の fail-soft。build 成果物は repo 外
   `${XDG_CACHE_HOME:-$HOME/.cache}/claude-harness-hooklint/`（security review HIGH: repo 内の
   非追跡 binary を commit 境界の hook が無人起動する経路を塞ぐ）、cargo は repo 外を cwd にして
   `--offline --locked` で起動（security review HIGH: repo 内 `.cargo/config.toml` の
   `[build] rustc-wrapper` による無人 RCE 経路。reviewer が PoC を示した）、
   `scripts/hooklint/` に未追跡ファイルがある間は build しない（cargo は build.rs / tests/*.rs を
   ビルド時に実行する）。
3. **撤退条件 (2) の size 上限 400 行は発火した**（`src/` 非テスト非空行 564 行。build 申告 602 は
   空行込み。内訳は lex.rs 349 / rules.rs 122 / main.rs 89 / lib.rs 4）。上限は plan 段の見積りで
   あり、超過分は review 12 件の修正由来 — lexer が算術左シフト `<<` を heredoc と誤読して以降を
   黙って食う fail-open の修正、security HIGH 2 件、GIT_SAFE / HEAD_SIGPIPE の偽陽性・見逃し 4 件
   などである。build が挙げた縮小 lever 3 つ（FAIL_OPEN rule を落とす -35 行 / backtick・
   herestring・算術の忠実度を落とす -45 行 / command substitution の二重引用内対応を落とす
   -12 行）はいずれも fail-open 方向に倒れる。**著者判断（2026-09-06）で上限を 600 行に引き直して
   accept する。これは事前登録した条件を事後に動かす判断であり、その旨をここに明記する**
   （measurement-discipline の趣旨: 動かしたことを隠さない）。他の撤退条件 4 件は通過した。
4. 計測は n=1 の読み値であり、RFC-0020 の仮説「bounce 減」の検証ではない
   （measurement-discipline 原則 1）。出典は commit `ab88358` の body（build 申告）と plan session
   の独立再測（同日、同一機）。結果: cold build 1.2 s（build 申告 1.74 s）/ warm 0.02 s /
   binary 493,984 B / verify.sh full run 増分 +5.3 s（93.7 → 99.0 s、build 申告）。bounce:
   1 セッション、判断役の bounce 0、compile error 0、clippy 0、cargo test 赤 4（いずれもテスト側
   期待値の不備）、着手〜commit 約 3.0 h（review 待ち含む）。latency:
   `hooklint --root ~/.claude` 中央値 3.9 ms（7 回、独立再測。build 申告 4.4 ms）vs
   `python3 -c pass` 21.1 ms vs `harness_lint.py` 182 ms — 起動コストの差だけを読む（検査内容が
   違うため直接比較の対象にしない）。較正: 現行 hooks/ で block 違反 0 / 23 hook、FAIL_OPEN
   report-only 5 / 23 hook（bats-autorun.sh:71 / harness-lint-precommit.sh:48 /
   review-model-notice.sh:72 / verify-precommit.sh:54 / verify-precommit.sh:98）、fixture 陽性
   GIT_SAFE 3 / HEAD_SIGPIPE 3 / FAIL_OPEN 3、偽陽性トラップ 0。承認台帳の再承認 1 回
   （verify.sh 編集、[ADR-0059](./0059-verify-precommit-block-on-stale-approval.md)）と
   `cargo build` 1 回を merge 後に著者が実行した。
5. hooklint は temporary 資産である（harness-boundary: Eval 層、hooks が bash である間だけ有効）。
   RFC-0020 の本文・state の更新は triage セッションの管轄で、本 ADR はそれを触らない。

## Review-when

- hooks/*.sh が bash でなくなる（RFC-0020 発火条件 3 で hook 本体が Rust 化される等）→ hooklint は
  対象消失で退役
- shellcheck 等の既存 shell linter が「特定 guard 引数の必須化」「head の `|| true` 終端」型の
  repo 固有 rule を持てるようになる → 置換を検討する
- RFC-0020 の発火条件 3（claims.py 級の既存移行）を再評価するとき、本 ADR の n=1 読み値を根拠に
  使うなら、その時点で 2 件目の pilot 読み値があるかを先に問う
- FAIL_OPEN の report-only 5 件が 3 cycle（verify.sh full run が走る triage tick 3 回）以上増減
  しないなら、block へ昇格するか rule を落とすかを決める（較正の完了条件）

  > **注記（2026-09-26, ADR-0082）**: 決着した — FAIL_OPEN は block に昇格した（Decision 1 の
  > report-only は FAIL_OPEN については失効）。発火条件の「3 cycle 不変」は観測されておらず、commit
  > `b522d0d` が 5 件を分類して 0 件にし、`# hooklint: fail-open <理由>` の waiver を足したことを受けた
  > 判断。出力書式（末尾行の `M report-only`）と `Finding.blocking` の枠は残っている。

- size 上限 600 行（`src/*.rs` の `#[cfg(test)]` を除く非空行。2026-09-06 時点 564）を再び超えたら、
  引き直しでなく設計縮小を先に問う（2 回目の goalpost 移動はしない）

## Alternatives Considered

### harness_lint.py に Python で同じ検査を足す

却下: 可能ではあったが、RFC-0020 が「新規常駐道具は Rust 第一候補」と定めた直後の最初の機会で
その既定を破る形になる。言語を問わず建てる根拠（RFC-0005 #13/#15）と Rust で建てる根拠
（RFC-0020）は別々に立っている。

### shell 字句解析 crate / 既存 shell linter（shellcheck、shuck）の採用

却下: build の search-first（2026-09-06）が Build 判定を返した — いずれも固定 rule set の汎用
linter で repo 固有 rule を持ち込む口が無く、crate は外部 crate 0 の制約と衝突する。

### 撤退条件 (2) 発火を受けて pilot 失敗として branch を破棄する

却下: 他 4 条件は通過しており、超過分は fail-open / security 修正由来である。ただし「条件を
動かした」事実は Decision 3 に残す。

### FAIL_OPEN rule を落として 400 行に収める

未決 — 再訪条件は Review-when の較正完了条件。較正データ（5/23 の発火）を捨てることになり、本
pilot の計測 4 の読み値が消えるため今回は採らなかった。

> **注記（2026-09-26, ADR-0082）**: 決着した — rule は落とさず block に昇格した（5 件中 2 件が実際の
> fail-open だったため）。size 上限 600 行は有効（ADR-0082 時点 597 行）

### 配線先を hooks/harness-lint-precommit.sh にする

却下: hooks/*.sh の編集を伴い、plan の境界（hooks 無改変）と衝突する。verify.sh は
harness_lint.py を staged / full 両 mode で既に呼んでおり、同じ場所に足した。

## Consequences

### Positive

- hooks/*.sh の `git` guard / `head` SIGPIPE guard の回帰が commit 時点で機械的に止まる
  （RFC-0005 #13 の ratchet）
- FAIL_OPEN の分布が verify.sh full run のたびに可視化される（従来は誰も見ていなかった）
- RFC-0020 の Unresolved（計測最小セット）に実測 1 件が入った。toolchain cold 1.2 s、
  full run 増分 +5.3 s、latency 3.9 ms は「常駐 gate に載せるには重い」の事前閾値
  （60 s / 30 s / 21 ms）を大きく下回る

### Negative

- `~/.claude` の verify.sh full run が cargo に依存する。cargo 不在は fail-soft だが、その環境では
  hooks の一貫性検査が黙って走らない（warn 1 行のみ）。binary は gitignore で clone 直後には無く、
  hooks/ か scripts/hooklint/ を staged した場合は `cargo build` を要求する
- 承認台帳の再承認が verify.sh 編集のたびに要る（ADR-0059）— 本件で 1 回。Rust 側の変更は
  verify.sh を触らないので以後は発生しない
- Rust の読者は次セッションの LLM だが、bounce 0 は n=1 で、Rust 固有の bounce（借用・
  ライフタイム）が無いとは言えない。2 件目の pilot か hooklint 自身の次の編集で観測する
- verify.sh への配線は plan 見積 25 行に対し 63 行（うちコメント 34 行。security review 3 件と
  「report-only が不可視」「golden が初回 skip」の修正分）— 次の pilot の配線見積りはこの比で引く
- 事前登録した size 上限を事後に動かした。以後の pilot で上限を宣言するときは「review 修正分の
  余白」を見積りに含めるか、上限を「非テスト非空行」で定義してから宣言する

### Neutral / Follow-ups

- 実測の出典は commit `ab88358` の body と本 ADR の 2 箇所。集約カウントの正本は本 ADR
  （commit body は build 申告、本 ADR は独立再測を優先する）
- 同 commit の Out-of-diff MEDIUM: `.claude/verify.sh` の `bats -r tests/` は非追跡 `.bats` を無人
  full run で実行する（本 diff が塞いだ security HIGH 2 件と同型の穴が bats 段に残る）。本 pilot で
  無人実行経路が全部塞がれたと読まない
- [RFC-0020](../../rfcs/0020-rust-for-resident-infra.md) の state 更新は triage セッションの管轄
- [rfcs/0005-review-to-lint-rollout-ledger.md](../../rfcs/0005-review-to-lint-rollout-ledger.md)
  候補 #13 は本 ADR の ratchet で塞がれ、#15 は report-only で較正中（ledger 側の記帳は
  triage セッションの管轄）

  > **注記（2026-09-26, ADR-0082）**: #15 も block の ratchet になった（較正は終了）。ledger 側の
  > 記帳は引き続き triage セッションの管轄

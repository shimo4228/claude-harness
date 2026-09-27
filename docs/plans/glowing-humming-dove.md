# RFC-0020 pilot plan — `hooklint`（hooks/*.sh の兄弟一貫性 lint を Rust で書く）

judge-tier プランセッション（Fable）。実装は build-tier へ dispatch、本セッションは packet 執筆と検収に残る。

## Context

RFC-0020（accepted 2026-09-06）は「次に新しく作る常駐道具から Rust で書く」greenfield pilot 方針。著者が発火条件 2 を能動的に立てたので、pilot 対象・計測最小セット・撤退条件を決める。

候補探索（Explore agent + 自前確認）の結果、harness に「今ちょうど要る」新規常駐道具は 1 つだけ実需の producer を持っていた:

- **RFC-0005 候補台帳 #13 / #15**（`rfcs/0005-review-to-lint-rollout-ledger.md:34-35`）— `hooks/*.sh` の兄弟間で防御イディオム（`core.fsmonitor=` guard / `| head -N || true` の SIGPIPE guard）が一部にしか入らないクラスと、helper 不在・`source` 失敗で検査が黙って無効化される fail-open クラス。reviewer 履歴掘削で **各 6 セッションが反復指摘**、修正は採用済み、**戻りを止める ratchet が無い**ため反復。素の grep は 7 本中 2 本が偽陽性（regex / block メッセージの文字列リテラル）で、**コメント・文字列を除外する shell 字句解析が要る** = parser 型
- 発火条件は「次に `hooks/` を触るとき」。本 pilot は hooks/ の守り手を建てるので条件を自分で立てる形（正直に記録する）

却下した他候補: triage digest 生成 script（`tests/golden/README.md:39` の凍結漏れ）— digest 本文は LLM prose でセッション応答へ移った（ADR-0045 注記 2026-08-30、著者確認「ファイル永続化しない」）ため生成器の実需が無い。重複リテラル検出（#14）— 出力の判定に毎回 LLM が要り、commit gate に載らない。claims.py 時刻注入 — 既存移行（発火条件 3）で pilot 対象外。

前提の実測（2026-09-06、このセッション）:

| 観測 | 値 |
|---|---|
| cargo / rustup / rustc | **既に導入済み**（`~/.cargo/bin`、rustc 1.97.1、stable aarch64） |
| `harness_lint.py --root .` 壁時計 | 182 ms（python3 起動 21 ms） |
| PreToolUse Bash 非 commit 経路の hook 7 本合計 | ≈150 ms（validate-bash 50 / 他 15–18 each） |
| `\|\| exit 0` / `\|\| true` の出現 | 91 箇所（大半は matcher gating の正当な早期 exit → これを一律に咎める rule は飽和する） |
| `\| head -N` に `\|\| true` 無し | 0 箇所（現行は全部 guard 済み → ratchet の初期発火 0） |

RFC Drawback「cargo/rustup が新規依存」は既に半分解消。残る drawback は「バイナリを commit できず build step が verify の前提に入る」— これを pilot で実測する。

## 決定 1: pilot 対象 = `scripts/hooklint/`（Rust、std のみ、外部 crate 0）

`hooks/*.sh` を字句解析（コメント / 単引用 / 二引用 / heredoc / `$(...)` を区別、それ以上の構文木は持たない）し、**簡単コマンド（simple command）単位**で 3 rule を当てる。

| rule | 対象 | 判定 | 現行 tree での期待発火 |
|---|---|---|---|
| `GIT_SAFE` | コマンド位置の `git` 語（配列代入 `x=(git …)` も含む） | 同一 simple command 内に `-c core.fsmonitor=` リテラル **または** `"${GIT_SAFE[@]}"` が無ければ違反 | 0（bandit / ruff / secret は GIT_SAFE、harness-lint は `-c` 直書き、task-claims-reminder:61 は `4766e2b` で修正済み） |
| `HEAD_SIGPIPE` | パイプライン中の `head -N` / `head -n N` | 同じパイプラインが `\|\| true` で終わらなければ違反（`set -e` / `pipefail` 有無は問わない — hook は全部どちらか有効） | 0 |
| `FAIL_OPEN`（**report-only**） | block 可能 hook（本文に `"decision"` か `exit 2` を持つ）内の `source … \|\| exit 0`、および外部検査器の実在ガード `[[ -f/-x … ]] \|\| exit 0` | 列挙して stdout に出す。**exit code に効かせない**（発火率較正前に block しない — measurement-discipline 原則 3） | 数件（harness-lint-precommit:48 型）— **この件数が較正の読み値** |

- `GIT_SAFE` / `HEAD_SIGPIPE` は違反で exit 3（block）。**現行 HEAD で 0 件**が受入条件 — 0 でなければ rule 定義か tree のどちらかが間違いで、build 側は「反証を記録して報告」（修正して合わせるのは禁止）
- 対象は `hooks/*.sh` のみ（`_*-common.sh` 含む）。`tests/` `scripts/` は対象外
- 出力契約（harness_lint.py と同型、golden 凍結対象）: 1 行 `hooks/<file>:<line>: <RULE> <message>`、末尾に `hooklint: N finding(s), M report-only` 1 行。exit `0` clean / `3` 違反 / `1` 予期しないエラー（root 不在等）。引数 `--root PATH`（既定 `~/.claude`）、`--json` は持たない（消費者が居ない）
- **サイズ上限（事前宣言）**: `src/` 合計 ≤ 400 行（unit test 含まず）、外部 crate 0、`Cargo.lock` commit、`target/` は `.gitignore`。上限に当たったら止めて報告（設計の縮小は判断役）
- LLM-first の機械ゲート（verify-bootstrap Step 2 の 4 軸）: `cargo fmt --check`（正準形）/ `cargo clippy -- -D warnings`（バグクラス）/ `cargo test`（境界の固定）。人間美学系 lint は select しない

### 配線（`.claude/verify.sh` に置く。hooks/*.sh は触らない）

`verify.sh` は harness_lint.py を staged / full 両 mode で回している（`:155`）ので同じ場所に足す:

- **staged mode**（数秒契約を守る）: バイナリ `scripts/hooklint/target/release/hooklint --root "$ROOT"` を実行するだけ（ビルドしない）。バイナリが**無い / `src/*.rs` より古い**ときは、staged に `hooks/*.sh` か `scripts/hooklint/**` が含まれる場合だけ **FAIL（exit 1）**「`cargo build --release` して再実行」、含まれなければ warn 1 行で素通し（守る対象が動いていないときは無関係な commit を止めない — fail-open クラスそのものを持ち込まない形で）
- **full mode**: `cargo fmt --check` → `cargo clippy --release -- -D warnings` → `cargo test --release` → `cargo build --release` → バイナリ実行。cargo は `command -v cargo || $HOME/.cargo/bin/cargo` で解決（launchd 起動の full run は PATH に `~/.cargo/bin` が無い前提で書く）、不在なら **exit 2 相当の warn**（他ツールと同じ fail-soft 規約 — `shellcheck 不在` 行と同型）
- **verify.sh 編集 = 承認台帳のハッシュ失効**（ADR-0059: main へ merge 後、著者が `verify_allow.py approve` するまで ~/.claude への commit は exit 71 で block）。これは pilot の toolchain コストの一部として実測対象に含める。worktree 内では台帳に無い repo（exit 70）扱いで commit は通る
- `.gitignore` に `scripts/hooklint/target/` を追加

### Build-or-not 4 問（judge-tier 自答）

1. **存在すべきか** — 同クラスの指摘が reviewer 履歴で 6+6 セッション反復し、採用済みなのに戻りを止める検査が無い（shellcheck は汎用 style、harness_lint.py は document 層のみ）。削除や既存流用では解けない: harness_lint.py に Python で足すことは可能だが、それは RFC-0020 が「新規常駐道具は Rust 第一候補」と定めた直後にその既定を最初の機会で破る形。**言語を問わず建てる根拠は RFC-0005 #13/#15、Rust で建てる根拠は RFC-0020**（別々に立っている）
2. **適正な大きさ** — Rust ≤ 400 行 / crate 0 / rule 3（block 2 + report-only 1）/ verify.sh 追記 ≤ 25 行 / .gitignore 1 行。段は「lexer → simple command 分割 → rule」の 3 段で固定
3. **誰が消費するか** — `verify.sh`（commit 境界で block）、`hooks/` を編集する次の build セッション（違反行を読んで直す）、RFC-0020 の再評価（計測値）。report-only の FAIL_OPEN 行は本 pilot の判断役が較正に読む
4. **失効条件** — (a) hooks/*.sh が bash でなくなる（RFC-0020 条件 3 で hook 本体が Rust 化される等）→ 対象消失で退役 (b) shellcheck 等が同型の兄弟一貫性 / fail-open 検査を持つ → 置換 (c) pilot が下の撤退条件に当たる → `git revert` で丸ごと戻す（git 追跡下なので復元可能）

### harness-boundary（1 行）

Eval 層（commit gate の機械検査）。runtime 固有部分は verify.sh の配線 ≤ 25 行のみ。hooks が bash である間だけ有効な **temporary** 資産（失効条件 (a)）。

### 種別と chain

- 種別 **feat**（新規モジュール）。chain は skill `implementation-chain` の Chain Matrix に委譲（packet は reviewer を列挙しない）
- 条件付きの判定: Phase 0 search-first **Y**（shell lexer crate / 既存 shell linter で #13/#15 型を検査できるものが無いかを 1 回。ただし採用しても crate 0 の宣言と衝突するので、見つけたら「Adopt 候補として報告して止まる」）/ TDD **Y**（rule の境界条件 — 文字列内の `git`、heredoc 内、配列代入 — がテストで初めて確定する種類）/ Security Review **Y**（無人実行の起動経路を 1 本足す: verify.sh が repo 内でビルドした binary を実行。信頼境界は harness_lint.py を python3 で実行する現行と同じ repo 内資産だが、脅威面を「動かした」ので回す）/ Code Review effort medium / Doc Sync **Y**（下）/ E2E **-**

## 決定 2: 計測の最小セット（RFC Unresolved の 3 項目 + 2 項目）

すべて build セッションの commit body と判断役の再測で取る。**n=1 の読み値であって RFC の仮説（bounce 減）の検証ではない**（measurement-discipline 原則 1 — RFC の review-when も「1 件完走で発火条件を再評価」であって採否確定ではない）。

| # | 項目 | 取り方 | 事前に決める「読み方」 |
|---|---|---|---|
| M1 | toolchain コスト | `cargo build --release` cold（`target/` 削除後）と warm の壁時計、バイナリサイズ、verify.sh full run の増分秒、承認台帳の再承認が要った回数 | cold > 60s か full run 増分 > 30s なら「常駐 gate に載せるには重い」と読む |
| M2 | bounce | 判断役の検収で bounce した回数と理由（packet 逸脱 / 受入条件不達 / Rust 固有）、build セッション自身が報告する「`cargo build`/`clippy` が赤くなった回数」と「セッション数」 | 直近の同規模 Python lint 作業（RFC-0006〜0010 の build、いずれも 1 セッション完走）と並べて記録。数字の比較で結論は出さない |
| M3 | hook レイテンシ | `hooklint --root ~/.claude` を 5 回、中央値。比較対象は `harness_lint.py` 182 ms と `python3 -c pass` 21 ms（同一機・同日） | 検査内容が違うので起動コストの差だけを読む。binary が 21 ms を下回らなければ嬉しさ (3) は本 pilot では観測されずと記録 |
| M4 | 発火率較正 | 現行 HEAD での block rule 発火 0 の確認 + FAIL_OPEN の report-only 件数 + fixture での陽性検出数 | 0/0 なら rule が空振り（原則 3）、fixture 陽性が無ければ検査になっていない |
| M5 | context 経済 | `src/` 行数、Cargo.toml 行数、次の編集者が読む必要のあるファイル数 | 400 行上限との比。llm-first-code の物差し |

削るもの: 「Rust vs Python の等価実装の行数比較」— 等価実装を書かないと測れず、書けば pilot が二重になるので測らない。

## 決定 3: 撤退条件（事前登録。1 つでも当たれば pilot 失敗として報告、RFC-0020 の再評価は triage が行う）

1. build セッションが **2 セッション以内 / bounce 2 回以内**で受入条件に達しない
2. `src/` が 400 行を超える、または外部 crate 無しでは rule の偽陽性を現行 tree で 0 にできない（parser 型が Rust std で収まらない）
3. `cargo build --release` cold が 60 s 超、または verify.sh full run の増分が 30 s 超
4. 承認台帳・launchd PATH・bash 3.2 のいずれかで**無人経路が黙って素通り**する形しか作れない（fail-closed が成立しない）
5. hooklint バイナリの実行が `python3 -c pass`（21 ms）より遅い

撤退時の処置: task branch を merge しない（または merge 後なら 1 commit で revert）。RFC-0020 本文への追記は triage セッションの管轄（本セッションは state 行を触らない）。

## 実行者の決定

**dispatch する**（judge-tier の既定）。実装は build-tier の新規セッション、本セッションは packet を書き、検収（独立再測 M1/M3/M4、`git diff --stat main..task/…`、verify full run）と RFC-0020 の release を行う。

### 承認後の手順（このセッション）

1. `python3 ~/.claude/scripts/claims.py claim RFC-0020 --label "S1: hooklint Rust pilot (Opus session, worktree task/rfc-0020-hooklint; judge=this Fable session, merge=human)"`
2. `git -C ~/.claude worktree add .claude/worktrees/rfc-0020-hooklint -b task/rfc-0020-hooklint main`（現在の main の未 commit 変更 — rules / rfcs/0020 の state 行 / skills/archify — は触らない。worktree は main HEAD から切る）。`settings.local.json` があれば worktree へコピー
3. packet を `skills/task-triage/references/packet-template.md` の形で書く（下の要点）。書き場所は scratchpad、本文は `herdr agent prompt` で渡す
4. `bash ~/.claude/skills/spawn-session/spawn.sh <worktree> "harness/s1-hooklint"` → `herdr agent prompt … --wait`。Herdr が使えなければ `claude --bg -w rfc-0020-hooklint --model opus`（判定は起動時。どちらも著者の「dispatch すること」が明示指示）
5. 成果物（task branch の commit）を `Monitor` で待つ。検収 → 著者へ merge 判断を提示 → merge 後に著者が `verify_allow.py approve` と `cargo build --release` を 1 回ずつ実行（この 2 手順は merge 案内に明記）
6. 完走後、計測値と判断を **ADR 提案**として著者に提示（ADR-0063 案「RFC-0020 pilot: hooklint」— 執筆は adr-writer 経由、著者承認後）。RFC-0020 の release は `claims.py release --outcome done|abandoned`

### packet 要点（build セッション向け、feat / worktree）

- Goal（決定可能）: (1) `scripts/hooklint/` に Cargo project、`cargo fmt --check && cargo clippy --release -- -D warnings && cargo test --release` exit 0 (2) `target/release/hooklint --root <worktree>` が **現行 hooks/ で exit 0、findings 0、FAIL_OPEN report-only N 件を出力** (3) fixture（`tests/fixtures/hooklint/*.sh`）で GIT_SAFE / HEAD_SIGPIPE 各 ≥ 2 陽性 + 偽陽性トラップ（文字列内 `git`、コメント内、heredoc 内、regex リテラル）各 0 (4) `.claude/verify.sh` に staged / full の配線（上の仕様どおり）、`bash .claude/verify.sh` 引数なし exit 0 (5) golden `tests/golden/hooklint/` + `tests/golden-hooklint.bats`（出力の全形）(6) `src/` ≤ 400 行
- Phase 0: RFC-0005 `:34-35` の #13/#15 記述と現行 hooks/ の突合（GIT_SAFE 未 guard が 0 件であることの再確認。1 件でもあれば**直さず報告** — 台帳の外の修正になる）。search-first 1 回（shell lexer crate / 既存 linter）— Adopt が出たら止めて報告
- Must-not: `hooks/*.sh` を編集しない / `rules/` `docs/adr/` `rfcs/` `settings.json` を触らない / 外部 crate を足さない / テストを弱めない / `git add -A` 禁止 / main へ merge・push しない / 台帳の状態を書かない / 時間上限 3 時間
- Report（commit body）: Packet / Premise / Fix / Regression / Verify / Review / Deviations / Out-of-diff findings に加え **Measurements**: M1（cold・warm 秒、binary bytes、full run 増分）、M2（自己申告: cargo/clippy 赤の回数、所要時間）、M3（5 回の壁時計）、M4（HEAD の findings 数、FAIL_OPEN 件数、fixture 陽性数）、M5（行数）
- Doc Sync（同 diff）: `.claude/verify.md` に cargo / clippy / rustfmt の選定と再調査トリガー節（as-of 日付）、`tests/golden/README.md` の凍結一覧に hooklint 出力を追加、`scripts/hooklint/README.md` は書かない（読者は次セッションの LLM。`src/main.rs` 冒頭コメントに契約 — 3 rule / exit code / 対象 — を置く。llm-first-code）

## 検証（判断役 = このセッションが再実行）

```
git -C ~/.claude/.claude/worktrees/rfc-0020-hooklint diff --stat main..task/rfc-0020-hooklint
cd <worktree> && bash .claude/verify.sh            # full: fmt / clippy / test / build / hooklint / bats / golden
rm -rf <worktree>/scripts/hooklint/target && time cargo build --release --manifest-path <worktree>/scripts/hooklint/Cargo.toml   # M1 cold
for i in 1 2 3 4 5; do time <worktree>/scripts/hooklint/target/release/hooklint --root ~/.claude; done   # M3、HEAD に対して
<worktree>/scripts/hooklint/target/release/hooklint --root <fixture-root>   # M4 陽性
```

- diff が packet の許可範囲（`scripts/hooklint/**`、`.claude/verify.sh`、`.claude/verify.md`、`.gitignore`、`tests/golden*`、`tests/fixtures/hooklint/**`）に収まる
- 撤退条件 1–5 を 1 つずつ照合して結果を著者に提示

## 触らないもの（境界）

rules / ADR 本文 / hooks/*.sh / settings.json / rfcs/0020 の state 行 / 他 RFC。ADR が要るなら提案止まり。commit するときは自分が触ったファイルだけ `git -C … add <path>`。

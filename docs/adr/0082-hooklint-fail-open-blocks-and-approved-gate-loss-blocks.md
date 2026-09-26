# ADR-0082: hooklint の FAIL_OPEN を block に昇格し、承認済み repo のゲート消失で commit を止める

## Status

accepted — [ADR-0063](./0063-rfc-0020-rust-pilot-hooklint.md) Decision 1 の「FAIL_OPEN は report-only」と、
同 Review-when の較正条件・未決の Alternative（FAIL_OPEN rule を落とす）を決める。
[ADR-0038](./0038-publish-curated-commit-hooks.md) の「`~/.claude` 固定の再配置制約」を部分的に緩める
（いずれも部分的に弱める。注記は各 ADR 側）

## Date

2026-09-26

## Context

- ADR-0063 は FAIL_OPEN（block 可能 hook 内の `source … || exit 0` / `[ -f/-x … ] || exit 0`）を
  「発火率較正前は block しない」report-only で入れ、Review-when に「5 件が 3 cycle 以上増減しないなら
  block へ昇格するか rule を落とすかを決める」を置いた。
- commit `b522d0d`（2026-09-26）がその 5 件を分類した: 2 件は実際の fail-open で fail-closed に直し、
  3 件は意図した素通しで、同じ行の `# hooklint: fail-open <理由>` waiver（理由が空なら効かない。
  FAIL_OPEN 以外は抑止しない）で明示した。report-only は 0 件になった。**Review-when の条件
  （3 cycle 不変）が観測されたのではない。** 5 件中 3 件が意図した素通しだったので偽陽性は無くなって
  いないが、理由付きの waiver 1 行で書けるようになり、偽陽性のコストが下がった。昇格は判断役と著者が
  2026-09-26 に決めた（dispatch packet は追跡されないので、記録は本 ADR と commit 本文だけ）。
- 同じ `b522d0d` の security-reviewer が MEDIUM を 1 件残した: `hooks/verify-precommit.sh` の
  `[[ -x "$GATE" ]] || exit 0` は、台帳外 repo の「ゲート未導入」と、承認済み repo の verify.sh の
  削除・`-x` 喪失を同じ経路で黙って通す。ゲートの実行は承認済みバイト列の 0700 の一時 copy
  （`scripts/hooks/verify_allow.py` の `run`）なので、repo 側の mode bit は実行に関係しない。
  [ADR-0059](./0059-verify-precommit-block-on-stale-approval.md) は「台帳に載っている repo のゲートが
  眠った状態（exit 71）」を block にしたが、ゲートが消えた状態は台帳照合より前で素通しになっていた。
  本 ADR の review（2026-09-26、security-reviewer と code review が独立に MEDIUM）は、ゲートが
  ファイルとしてはあるが照合できない形（読めない、repo 外を指す symlink = exit 72）も同じ素通しだと
  示した。
- `hooks/harness-lint-precommit.sh` には同じ日に 3 つの穴が見つかった（packet と `b522d0d` の review）:
  `HARNESS_LINT_BYPASS=1` がコマンドのどこにあっても効く（commit message に書くだけで lint が外れる）、
  lint 本体の異常終了（rc が 0 / 3 以外）を設計コメントどおり fail-soft で通す、harness の linked
  worktree（`.claude/worktrees/*`）からの commit では top level が harness root と一致せず発火しない。
  本 ADR の security review は、verify / secret-scan / harness-lint の 3 hook に共通の bypass 判定
  （`grep -E '^…'`）が行単位なので、複数行 commit message の行頭に書いた文字列でも効くことも示した。
- verify-precommit の bats は hook を `$HOME/.claude/hooks/` から起動しており、hook も起動器を
  `$HOME/.claude/scripts/hooks/verify_allow.py` 固定で引いていた。worktree の変更（新しい `known` を
  含む）は、merge されるまでテストで検査できなかった。

## Decision

1. `scripts/hooklint/src/rules.rs` の FAIL_OPEN を `blocking: true` にする。exit 3 で verify.sh の
   staged / full が FAIL になる。意図した素通しは同じ行の `# hooklint: fail-open <理由>` で書く。
   出力書式は変えない — 末尾行 `hooklint: <N> finding(s), <M> report-only` を保ち、現行 rule では
   M = 0。`Finding.blocking = false` の枠は、新 rule を較正してから block にするために残す。golden
   `tests/golden/hooklint/fixture.txt` の末尾行は `6 finding(s), 3 report-only` から
   `9 finding(s), 0 report-only` に変わる（本 ADR が宣言する出力変更）。size 上限 600 行
   （ADR-0063）に対し、変更後の非テスト非空行は 597 行のまま。
2. `hooks/verify-precommit.sh` は、ゲートの有無を `-x` ではなく存在（`-f`）で見る。承認済み repo の
   ゲートが実行できない形になったら block する。形は 2 つ: ゲートが無い（削除・壊れた symlink・
   ディレクトリ化）と、ファイルはあるが照合できない（`run` の exit 72 = 読めない・repo 外を指す
   symlink）。reason には「誤って消えた・壊れたなら戻す／廃止なら人間が `verify_allow.py revoke`」と
   `VERIFY_BYPASS=1` を書く。台帳に無い repo は、ゲートが無ければ従来どおり無言で素通し（waiver の
   理由をこの区別に書き換える）、exit 72 なら従来どおり stderr 通知で素通し。台帳が壊れている（73）
   ときは stderr に通知して素通し（`run` の `load_or_empty` と同じ側）。

   > **注記（2026-09-26, ADR-0083）**: block は main が承認済みの linked worktree のゲート消失・exit 72 にも
   > 及ぶ。そのときの revoke の対象は main の key で、main と全 worktree の承認が外れるので、reason は
   > branch に戻す・`VERIFY_BYPASS=1` を先に示し、revoke を merge 後の操作として書く。
3. `verify_allow.py` に読み取り専用の `known <repo>` を足す（0 = 台帳にある / 70 = 無い / 73 = 台帳破損。
   key の正規化は approve / revoke と同じ realpath）。承認の書き込み側（approve / revoke / 台帳形式）は
   変えない。hook は起動器を `$HOME/.claude/…` 固定ではなく、自分と同じ harness の版
   （`${BASH_SOURCE[0]%/*}/../scripts/hooks/`、共有部品の source と同じ解決）から引く。bats も hook と
   起動器を `BATS_TEST_DIRNAME` から引く（`b522d0d` の先例）。

   > **注記（2026-09-26, ADR-0083）**: `known` の key は approve / revoke と同じ正規化ではなくなった。
   > run / check と同じ `ledger_key` で引き（repo 自身が無ければ登録先の main worktree）、0 のときは
   > 一致した key を stdout に出す。approve / revoke は無変更。
4. `hooks/harness-lint-precommit.sh`:
   - lint の異常終了（rc が 0 / 3 以外）は block する。rc 3 の違反も含め、lint の出力は上限 4000 字で
     切り、「repo 由来の未検証データ」の枠に入れて reason に載せる（`rules/common/security.md` の
     脅威面第 3 項）
   - 「harness への commit か」を `git rev-parse --git-common-dir` の一致で判定し、linked worktree から
     の commit でも発火する。検査対象は commit する側の tree（`--root <top level>`）、検査器は harness
     root（main checkout）の `harness_lint.py` — worktree の版は未検収の branch コードなので無人で
     実行しない

   > **注記（2026-09-26, ADR-0083）**: この hook の検査器は main の版のまま。ただし「未検収の branch
   > コードを commit 境界で無人実行しない」は commit 境界全体では成り立たなくなった: 承認済みの
   > `.claude/verify.sh` が worktree の root で走り、branch の `harness_lint.py` を実行する。ADR-0083
   > Decision 8 はこれを、main checkout で branch を checkout したときと同じ露出として受け入れた。
5. bypass（`VERIFY_BYPASS` / `SECRET_SCAN_BYPASS` / `HARNESS_LINT_BYPASS`）は 3 hook とも同じ判定にする:
   コマンド文字列**全体**の先頭に並ぶ env 代入の中にあるときだけ効く（bash の `=~` で判定する。grep の
   行単位の `^` は使わない）。

## Review-when

- `hooks/*.sh` の `# hooklint: fail-open` waiver が、理由の使い回しや中身の無い理由で増える（本 ADR 時点で
  3 行。hooks/*.sh を触る diff の検収で判断役が `grep -c` で数え、6 行を超えたら中身を読み直す）→ waiver に
  review を課すか、rule を再設計する
- 承認済み repo でゲートを廃止する正当な作業が、revoke 前に block され続ける観測が出る → 通知だけに
  するか、猶予を付ける（ADR-0059 の 71 と同じ再訪条件）
- harness の worktree で `harness_lint.py` とその検査対象を一緒に変える branch が、main の古い lint に
  止められ `HARNESS_LINT_BYPASS` で通す運用が繰り返される → 検査器の版の選び方を見直す
- `verify_allow.py` の台帳 key（repo の realpath）や exit code 体系が変わる → `known` と hook の分岐の
  前提が崩れる
- hooks/*.sh が bash でなくなる → hooklint は対象を失う（ADR-0063 と同じ）

> **注記（2026-09-26, ADR-0083）**: 台帳 key の条件が発火した。key の正規化（realpath）は変えずに引き方を
> 足した — repo 自身が台帳に無く、main worktree に登録された linked worktree のときは main の key で引く。
> exit code の値は不変で、70 の意味が「main の承認済みの版と違う linked worktree」にも広がった。

## Alternatives Considered

### FAIL_OPEN rule を落とす（ADR-0063 で未決だった選択肢）

却下: 5 件中 2 件は実際の fail-open で、`b522d0d` が fail-closed に直した。rule を落とすと、
兄弟 hook へ同じ形が戻るのを止める ratchet（RFC-0005 #15）が消える。

### report-only のまま維持する

却下: report-only の行は `.claude/verify.sh` の full run だけが印字し、commit 境界（staged mode）では
exit 0 なので止まらない。新しい fail-open は commit を通ったあと、誰かが full run の出力を読むまで
残る。件数が 0 で waiver 構文があるので、block のコストは新しい fail-open 1 つにつき 1 行の修正か
waiver で済む。

### report-only の枠（`Finding.blocking` と末尾行の `M report-only`）ごと削除する

却下: 末尾行は commit block の理由として model が読む出力で、golden が凍結している。書式を変えずに
閾値だけを動かす方が差分が小さい。新 rule を block 前に較正する枠としても使える。

### verify-precommit のゲート消失を放置する（`b522d0d` の waiver 理由に穴を明記した状態のまま、または stderr 通知だけ足す）

却下: 通知だけのチャネルは、ADR-0059 の Context で 3 週間・15 回以上発火して一度も行動につながら
なかった。`b522d0d` の security-reviewer の第一推奨（waiver を外して report を残す）は、FAIL_OPEN を
block に昇格すると harness 自身の全 commit を赤にする（hooklint は harness の verify.sh の中で
`hooks/*.sh` を検査する）。その指摘を消す手は waiver か fail-closed への書き換えしかなく、後者は
ゲート未導入の repo の commit まで止める。

### verify-precommit で `-x` 判定のまま台帳照合だけを足す

却下: `-x` は実行に関係しない（一時 copy を chmod して実行する）。`chmod -x` だけで承認済みゲートが
黙って外れる経路が残る。

### ゲートが無ければ台帳に関係なく block する

却下: ADR-0059 の exit 70 と同じ理由で、ゲートを持たない全 repo の commit を止めてしまう。

### hook が台帳 JSON を直接読む

却下: 台帳の path と key の正規化（realpath）を hook 側に複製することになり、drift の原因になる。
読み取り専用の subcommand を 1 つ足す方が、正規化を 1 箇所に保てる。

### 起動器の path を `$HOME/.claude/…` 固定のままにする

却下: worktree の hook が main の `verify_allow.py` を呼ぶので、hook と起動器の版がずれる（新しい
`known` は merge まで存在しない）。テストも main の版しか検査できない。共有部品の source と同じ
相対解決にすれば、hook と起動器は常に同じ checkout の版になる。

### worktree からの commit では worktree の `harness_lint.py` で検査する

却下: branch 上の未検収コードを commit 境界で無人実行することになる（`rules/common/security.md` の
脅威面第 1 項）。版のずれで止まるコストは Review-when で見る。

## Consequences

### Positive

- block 可能 hook に新しい `source … || exit 0` / `[ -f/-x … ] || exit 0` を書くと、commit 時点で
  止まる（理由を書いた waiver か、fail-closed への修正を要求する）
- 承認済み repo のゲートが、削除・壊れた symlink・読めない mode・repo 外への symlink・`chmod -x` で
  黙って外れなくなる。`-x` を失ったゲートはそのまま実行される
- harness への commit は、worktree からでも lint を通り、lint が壊れていれば止まる。commit message に
  bypass の名前を書いても gate は外れない
- 戻すのは安い: FAIL_OPEN は `blocking` を false に戻して golden の末尾行を戻す 2 箇所、他は hook の
  該当分岐の revert

### Negative

- block 可能 hook の編集で、意図した素通しにも 1 行の waiver が要る。waiver の理由の質は機械では
  検査しない（自己申告）
- 承認済み repo でゲートを廃止するには、人間の `revoke` が 1 手増える
- 台帳が壊れているとき、または `verify_allow.py` が見つからないときは、承認済み repo のゲート消失も
  素通しになる（前者は stderr 通知、後者は既存の「承認台帳が無い」通知がゲートのある repo にだけ出る）
- worktree から harness へ commit するとき、lint は main checkout の版で走る。branch が lint 本体と
  その検査対象を一緒に変えると、merge まで古い lint に止められることがある（脱出口は
  `HARNESS_LINT_BYPASS`）
- 台帳に無い repo で、`-x` の無い verify.sh を持つものは、従来の無言の素通しから、exit 70 の
  stderr 通知（承認手順の案内）付きの素通しに変わる

### Neutral / Follow-ups

- `.claude/verify.sh` full mode の「FAIL_OPEN 行を exit 0 でも印字する」分岐は、現行 rule では
  発火しなくなる。verify.sh は承認 hash の対象なので本 ADR では変えない（`.claude/verify.md` に記述だけ
  合わせた）。report-only の新 rule を足すときは、この分岐が rule 名 `FAIL_OPEN` でしか絞っていない点を
  直す必要がある
- `hooks/bandit-precommit.sh` と `hooks/ruff-format-precommit.sh` は「repo がゲートを持つか」を今も
  `-x` で見る。`-x` の無いゲートでは verify と Python hook の両方が走る（二重検査で無害）。定義が 2 つ
  あることだけが残る

  > **注記（2026-09-26, ADR-0083）**: 2 hook とも `-f` にして定義を 1 つにした（ADR-0083 Decision 7）。
- 公開 repo（claude-harness）の `docs/hooks.md` にある再配置制約の記述は、harness-sync 時に追従が要る
  （ADR-0038 側に注記）
- ADR-0063 の Decision 1・未決 Alternative・Review-when・Follow-ups（RFC-0005 #15）に注記を入れた

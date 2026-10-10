# ADR-0094: VERIFY_BYPASS を廃止し、ゲートが止めたら原因かゲートの検査を直す

## Status

accepted — [ADR-0082](./0082-hooklint-fail-open-blocks-and-approved-gate-loss-blocks.md) Decision 5（3 hook の bypass 判定を
そろえる）から `VERIFY_BYPASS` を外し、[ADR-0083](./0083-verify-gate-in-linked-worktrees-via-main-checkout-approval.md)
Decision 5 と Review-when が出口に挙げた `VERIFY_BYPASS=1` を rebase に替え、
[ADR-0059](./0059-verify-precommit-block-on-stale-approval.md) Decision 2 の「緊急時は `VERIFY_BYPASS=1`」を外す。
3 ADR の該当節に注記する

## Date

2026-10-09

## Context

著者（2026-10-09）: 「VERIFY_BYPASS=1これ禁止して。その場しのぎせずに根本解決する規約にして」。

`hooks/verify-precommit.sh` は、コマンド文字列の先頭に `VERIFY_BYPASS=1` があるとゲートを走らせずに通していた。
案内文は「偽陽性ならユーザーに確認のうえ」と書くが、機械は止めない。

この hook は Claude の Bash 呼び出しにだけ掛かり、著者が自分の端末で行う commit には掛からない。したがって
hook からバイパスを外して縛られるのは Claude だけになる。

外したあとも、行き詰まる場面は無い。

- FAIL: 原因を直す。偽陽性なら `.claude/verify.sh` の検査を直す。直した verify.sh は exit 71 になり、ADR-0093 の
  確認画面で人間が承認する
- 承認済み repo のゲートの消失・照合不能: verify.sh を戻すか、人間が `revoke` する。linked worktree で verify.sh 導入前の
  commit から作った branch は、main に rebase して verify.sh を取り込む

廃止の作業中に、対象 repo を取り出す共有部品（`hooks/_git-target-common.sh`）の穴が見つかった。先頭に環境変数の
代入があるコマンド（`FOO=1 git -C X commit`）では `-C` の行き先を取りこぼしてカレント repo のゲートを走らせ、
代入を 1 つ前に付けるだけで X のゲートを避けられた。

## Decision

1. **`verify-precommit.sh` から `VERIFY_BYPASS` の判定を外す。** block の案内文からもバイパスを外し、FAIL は「原因を
   直して再 stage。偽陽性ならゲート（`.claude/verify.sh`）の検査を直し、理由を commit 本文に書く。直せないときは
   止まってユーザーに報告する」と書く。worktree のゲート消失は「main に rebase して verify.sh を取り込む」を案内する
2. **規約は `rules/common/security.md` に置く**（上と同じ文）。止まる条件は boundary.md の「同じ方針で 2 回失敗」に従う
3. **`_git-target-common.sh` の照合を、先頭の環境変数の代入を読み飛ばす形にする**（7 hook が共有）
4. skill `repair-discipline` §3 の例を `SECRET_SCAN_BYPASS=1` に替える。構成図（`docs/diagrams/verify-commit-gate.architecture.json`）
   の bypass の記述を外す
5. 回帰テスト: `tests/verify-precommit.bats`（旧バイパスの印でもゲートが走って止める、消失したゲートも止める、FAIL と
   承認切れの reason にバイパスが出ない）、`tests/git-target-extraction.bats`（代入が前に付いても `-C` の行き先を取る）

## Review-when

- ゲートの偽陽性を直せずに止まる報告が、1 か月に 2 回を超える — ゲートの書き方（verify-bootstrap）を見直す
- Claude がゲートの検査を外す・弱める編集をして、その理由が偽陽性の修正でなかったと後から分かる
- この hook が Claude の Bash 以外（著者の端末の git hook など）にも掛かるようになった — 著者の手を縛る

## Alternatives Considered

- **バイパスを残し、使ったら commit 本文に理由を書かせる** — 不採用。著者が求めたのは「その場しのぎをしない」で、
  理由を書いても通す形はその場しのぎのまま
- **バイパスを著者だけが使えるようにする（確認画面を挟む）** — 不採用。著者の端末の commit には hook が掛からないので、
  著者には元からバイパスが要らない
- **`SECRET_SCAN_BYPASS` と `BANDIT_SCAN_BYPASS` も同時に廃止する** — Open — revisit when: 著者がこの 2 つも廃止すると
  決めたとき。secret scan の偽陽性は検出器の調整が repo の外（detect-secrets の baseline）にあり、直し方が verify と違う

## Consequences

- 良: Claude はゲートを避けて commit できなくなり、FAIL は原因かゲートの検査を直すことで片づく
- 良: 環境変数を前に付けて対象 repo を取り違える穴が、7 hook 共通で閉じる
- 悪: ゲートが壊れて直せないとき、Claude は commit できずに止まる。著者が自分の端末で commit するか、ゲートを直す
- 悪: 偽陽性をゲート側で直すと、その修正は ADR-0093 の確認画面を通る（1 回の承認が増える）
- 戻すコスト: `verify-precommit.sh` の bypass 判定と案内文、security.md の 1 項、repair-discipline の例、構成図の 2 か所、
  bats のテストを戻す。`_git-target-common.sh` の照合の修正は戻さない（穴の修正として独立に立つ）

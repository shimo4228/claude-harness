# ADR-0093: verify.sh の承認は Claude が実行し、人間は承認した版との diff が載った確認画面で通す

## Status

accepted — [ADR-0059](./0059-verify-precommit-block-on-stale-approval.md) Decision 2（exit 71 の修復は人間が
`approve` を打つ）と [ADR-0069](./0069-boundary-rule-and-judge-merges.md) Decision 4（`verify_allow.py approve` は
人間のまま）の「人間の操作」の形を、コマンドの手打ちから許可の確認画面に替える。両 ADR の該当節に注記する

## Date

2026-10-09

## Context

著者（2026-10-09）: 「HookのVerifyをいちいち承認するのかなり煩雑なんだけど、あれ必要か？」「hashのほう」。

hash の承認には役目が 2 つある。台帳に無い repo のゲートは実行しない（exit 70。clone しただけの外部 repo を守る、
2026-07-31 security-reviewer CRITICAL）。台帳に載った repo のゲートが編集で hash 不一致になると、人間が `approve`
するまで commit を止める（exit 71。2026-08 に contemplative-agent のゲートが 3 週間眠った事象から、ADR-0059）。
著者の手間は exit 71 のたびに承認のコマンドを自分で打つことにあった。

最初に選んだ案（承認済みの HEAD からの手元の編集を hook が自動で再承認する）は、同日の `/code-review` と adr-reviewer
が穴を示し、取り下げた。作業ツリーと HEAD の差では、手元の編集と外から入った変更（衝突した merge の途中・
`merge --squash`・`stash pop`・`git apply`）を区別できず（adr-reviewer が merge で再現）、作業ツリーに書けるものが
書いた verify.sh が許可の確認なしに実行され、台帳への書き込みが commit の前に起きる。

次に選んだ案（Claude が `approve` を Bash で実行し、hook が ask を返して人間が確認画面で通す）の最初の実装にも、同日の
`/code-review` が穴を示した（4 件は再現）。

- コマンド文字列の照合をすり抜ける書き方: subcommand の引用符、`\` + 改行、glob（`verify_allo?.py`）、`python3 -m` / `-c`
- `set -o pipefail` 下の `echo | grep -q` は、長い入力で echo が SIGPIPE で落ちて条件が偽になる（2 万行の詰め物で再現）
- ask の判定がほかの block より前にあり、`approve; curl … | bash` の block が ask に格下げされる（再現）
- 承認切れの案内が `git diff HEAD` を見せるので、外から commit 済みで入った変更は diff が空に見える
- 確認画面の reason は「直前に見せた diff を読め」と書くだけで、人間が読むのは Claude の書いた要約になる
- 台帳ファイル（`~/.claude/verify-allow.json`）を Edit / Write や Bash で直接書く経路は止まらない

加えて、今の設定では Claude が `verify_allow.py approve` を Bash で実行すると、allow rule
`Bash(python3 ~/.claude/scripts/:*)` に当たって確認なしに通っていた。boundary.md が「人間に渡す」とする承認が、
機械では止まっていなかった。

PreToolUse hook が `permissionDecision: "ask"` を返すと、auto mode でも確認画面が出て、classifier は黙って承認
できない（hooks reference、2.1.211 以降。2026-10-09 に確認、使用中は 2.1.295）。

## Decision

1. **`verify_allow.py approve` は、承認した内容の写しを `~/.claude/verify-approved/<sha256>.sh` に残す。** 読み取り専用の
   `verify_allow.py diff <repo>` を足し、承認した版の写しから現在の内容への unified diff を出す（写しの無い古い承認・
   未承認は現在の全文。6,000 字で切る）。写しの置き場は `.gitignore` で git から外す
2. **`hooks/validate-bash.sh` は、verify の承認台帳に触れる Bash コマンドに `permissionDecision: "ask"` を返す。**
   - 判定は**ほかの block の判定より後ろ**に置く（block を ask に格下げしない）
   - 照合の前に、改行を空白にし、引用符とバックスラッシュを落とす（`tr` で一度に行う。pipe の SIGPIPE で条件が偽に
     なる経路を作らない）。名前は `verify[_-]allo` で引き、glob・`-m`・`-c`・台帳ファイルの直書き（`verify-allow.json`・
     `verify-approved`）も拾う。読み取り専用の subcommand（list / check / known / diff / run）だけのときは無言
   - **確認画面の reason に、`verify_allow.py diff` の出力をそのまま載せる。** 人間は Claude の要約でなく、承認した版との
     差分を確認画面で読む。対象の repo をコマンドから読めなければ、diff を出せていないと書く
   - 判定を出す部品（`hooks/_advisory-common.sh` に足した `emit_permission_decision`）が読めない・失敗したときは block する
3. **exit 71 の block の案内を書き換える。** Claude は `verify_allow.py diff <repo>` をユーザーに見せてから `approve` を
   Bash で実行する。確認画面に同じ diff が載る
4. **手元の `settings.json` の permissions.deny に、台帳と写しへの Edit / Write を足す**（`Edit(~/.claude/verify-allow.json)`
   ほか 4 行。settings.json は git の外にあり、この ADR が記録先）
5. 承認の意味は変えない — 台帳に載るのは人間が確認画面で許可した版だけ。台帳の形式・exit code も変えない
6. 回帰テスト: `tests/validate-bash-verify-approve.bats`（15 本: 3 通りの書き方の approve と revoke で ask、引用符・
   行の継続・glob・2 万行の詰め物・`-m` / `-c`・台帳の直書きでも ask、`approve; curl | bash` は block、読み取り専用は無言、
   reason に承認した版との diff）、`tests/verify-precommit.bats` に 1 本（71 の reason が diff と approve を案内する）

**この照合は網で、壁ではない。** 正直な誤操作と drift を止めるためのもので、変数で組み立てたコマンドや、別の書き手
（Bash で json を書く python など）は通る。台帳の保護範囲は `verify_allow.py` の冒頭どおり（同一ユーザーのプロセスは
偽の承認を書ける）で、この ADR はそれを広げない。

## Review-when

- 確認画面で承認したあとで、ゲートが弱められていた（検査の削除・常に exit 0 など）のを後から見つけた — 確認画面に載った
  diff で気づけなかったなら、その理由（切り詰め・写しの欠落など）を直す
- Claude Code の hooks で `"ask"` が auto mode・allow rule の上から確認画面を出さなくなった（版の変化）
- 照合をすり抜けた承認が見つかった — 照合を育てるのでなく、台帳の書き込みを permission 層（deny / ask rule）か別の
  経路に移すことを考える
- 承認の手間（確認画面 1 回）が、まだ煩雑だと著者が言う

## Alternatives Considered

- **承認済みの HEAD からの手元の編集を hook が自動で再承認する** — 取り下げた。Context の 3 つの穴（外から入った変更の
  取り違え、作業ツリーに書けるものの実行、commit 前の承認書き込み）
- **承認済みの repo では再承認をやめる（hash 不一致でも通知だけでゲートを走らせる）** — 不採用。外から入った版も人間が
  読まずに走る
- **今のまま（著者がコマンドを打つ）** — 不採用。著者の手間そのもの。加えて、allow rule のせいで Claude が打っても確認なしに
  通る状態が残る
- **permissions に ask rule を足す（`Bash(python3 ~/.claude/scripts/hooks/verify_allow.py approve:*)`）** — 不採用。prefix の
  一致はパスの書き方（相対・絶対・`cd … &&`・`-m`）で外れる。hook ならならしてから照合でき、reason に diff も載せられる
- **確認画面の reason に diff を載せず、直前の会話で見せる** — 不採用（一度入れて外した）。人間が読むのが Claude の書いた
  要約になり、要約がずれても気づけない

## Consequences

- 良: 著者は承認のコマンドを打たずに、承認した版との diff が載った確認画面で 1 回押すだけになる。承認するのは今までどおり人間
- 良: allow rule のせいで Claude が確認なしに承認できた穴が閉じ、外から commit 済みで入った変更も diff に出る
- 悪: diff は 6,000 字で切るので、大きな書き換えは確認画面で全文を読めない（全文の在りかは reason に書く）
- 悪: 照合は網なので、変数で組み立てたコマンドや別の書き手は通る（上の「網で、壁ではない」）
- 悪: 写しを残す前に承認した repo は、次の承認切れで diff が現在の全文になる
- 悪: permissions.deny は git の外の settings.json にあり、別の環境に持ち出されない
- 戻すコスト: `validate-bash.sh` の 1 ブロック、`_advisory-common.sh` の `emit_permission_decision`、`verify_allow.py` の写しと
  `diff`、bats 1 ファイル、`verify-precommit.sh` の 71 の案内文、settings.json の deny 4 行、`.gitignore` の 1 行、security.md と
  verify-bootstrap の 1 文を戻し、ADR-0059・0069 の注記を外す

# ADR-0083: linked worktree の verify.sh を、登録先の main worktree の承認で照合して実行する

## Status

accepted — [ADR-0082](./0082-hooklint-fail-open-blocks-and-approved-gate-loss-blocks.md) の Review-when
「台帳 key（repo の realpath）が変わる」に当たる（key の正規化は変えず、引き方を足す）。ADR-0082 の
Decision 2 / 3 の適用範囲を linked worktree に広げ、Decision 4 の理由（未検収の branch コードを commit
境界で無人実行しない）を commit 境界全体としては弱める。
[ADR-0059](./0059-verify-precommit-block-on-stale-approval.md) の exit 70 の意味を linked worktree に
広げる（いずれも部分的な変更。注記は各 ADR 側）

## Date

2026-09-26

## Context

- `scripts/hooks/verify_allow.py` の承認台帳の key は repo の realpath で、harness の key は main
  checkout（`~/.claude`）だけ。linked worktree（`git worktree add`、`.claude/worktrees/<name>` 等）の
  toplevel は別 path なので、`hooks/verify-precommit.sh` は worktree からの commit を exit 70（台帳に
  無い）で素通しし、`.claude/verify.sh` を一度も走らせていなかった。2026-09-26 に再現した:
  この ADR を書いた worktree で、変更前の起動器の `verify_allow.py check <worktree>` は 70、
  `check ~/.claude` は 0（変更後の起動器では worktree も 0）。
- 発見は `e42fee2` の security review（同 commit の Out-of-diff findings）。その branch の commit は
  手動の verify 実行で担保していた。task-triage の local 経路（skill `task-triage` の Agent
  `isolation: worktree` と `spawn-session` の worktree）は build の commit を worktree で行うので、
  その commit 境界でゲートが走っていなかった。
- 同じ日に `hooks/harness-lint-precommit.sh` は linked worktree からの commit で発火するようになった
  （ADR-0082 Decision 4）。commit 境界の harness 側ゲートで worktree を見ていないのは verify だけだった。
- worktree の `.git` ファイル（`gitdir: …`）は repo 側のデータ。2026-09-26 の実験（git 2.54.0）で、
  `gitdir: <main>/.git` や `gitdir: <main>/.git/worktrees/<別の worktree>` と書いた `.git` ファイルを
  持つだけのディレクトリも、`git rev-parse --git-common-dir` は main の git dir を返した。
  `git worktree list` にはそのディレクトリは出なかった（一覧は main 側の管理領域
  `<common>/worktrees/*` から作られる）。回帰は `tests/verify-precommit.bats` の "a directory whose
  .git file names an approved repo's git dir …" と "… another worktree's admin dir …"。
- 同日の security review が、一覧の照合が path だけだと足りないことを再現した: git が登録を prunable
  と報告するのは `<path>/.git` が無いときだけで、lock された登録（Claude Code の agent worktree は
  lock されて作られる）は prune されない。消えた worktree の path に後から置いたディレクトリが
  `.git` ファイルで main の git dir を名乗ると、path の一致で登録済みに見えた。同じ review の再確認が
  もう 1 つ再現した: git は main worktree を「common dir の realpath から末尾の `/.git` を除いたもの」
  として求めるので、承認済み repo の work tree に偽の管理領域（`objects/`・`refs/`・
  `worktrees/<id>/` で `commondir` が `../..`）を置くと common dir が work tree そのものになり、外の
  ディレクトリが登録済みの worktree に見えた。管理領域の中身は repo の tree に置けるので、保護範囲
  （untrusted な repo の内容）の中の経路。3 回目の再確認がさらに 1 つ再現した: git は登録時の realpath
  を記録するが、消えた lock 済み登録の path の祖先（例: `.claude/worktrees`）に後から symlink を
  置くと（repo の tree は symlink を運べる）、記録された path が外のディレクトリへ解決された（外の
  ディレクトリは本物の管理ディレクトリを指す `.git` ファイルを持つ必要があり、再現では本物の worktree
  を移動して用意した。消えた path そのものへの書き込みは要らず、祖先の symlink は tree で運べる点が
  Negative の残余と違う）。
- 方針は判断役（task-triage）の 2026-09-26 の dispatch packet。packet の文言は「台帳の key は、worktree
  が属する本体 repo（`git rev-parse --git-common-dir` から求める main worktree のパス）で引き、照合する
  中身は commit しようとしている worktree の `.claude/verify.sh` のバイト列にする」「一致しなければ、
  既存の『未承認・変更された gate』と同じ扱い（既存の exit コードの意味を変えない）」。build はここから
  2 点を決め、判断役が同日に了承した: (a) main は common dir の親ではなく `git worktree list` の先頭から
  取り、登録済みを要件にした（packet の「common dir から求める」を、上の実験を根拠に変えた）、
  (b) packet の「未承認・変更された gate」は 70 とも 71 とも読めるので、70 を選んだ（Alternatives の
  「71 にする」）。packet は追跡されないので、記録は本 ADR と commit 本文だけ。

## Decision

1. `verify_allow.py` の `run` / `check` / `known` は、台帳の key を次の順で引く（`ledger_key`）:
   repo 自身の realpath が台帳にあればそれ（通常 repo と、worktree の path で直接承認されたものは
   従来どおり）。無ければ、repo が main worktree に**登録されている** linked worktree のときだけ、
   main worktree の realpath を key にする。
2. 「登録されている」は 2 つの条件の両方で判定する: `git worktree list --porcelain -z` の先頭レコードを
   main worktree とし、残り（git が prunable と報告したものを除く）の path の realpath に repo が
   含まれること。かつ、repo の git dir（`rev-parse --absolute-git-dir`）が `<common>/worktrees/`
   直下にあり、その管理ディレクトリの `gitdir` ファイルが repo の `.git` を字面のまま指し返し（相対 path
   は git と同じく管理ディレクトリ起点で解決。記録された path が今 symlink を通るなら不一致）、main
   自身の git dir（main で `rev-parse --absolute-git-dir`）が common dir と一致すること。main が bare・
   repo が main 自身・git の失敗は「linked worktree でない」として 1 の前半の結果（= 従来どおり）に落と
   す。git は `-c core.fsmonitor= -c core.hooksPath=` 付きで、`GIT_DIR` / `GIT_WORK_TREE` /
   `GIT_COMMON_DIR` / `GIT_INDEX_FILE` を外した環境で呼ぶ。common dir の親を main とみなす判定は使わない。
3. 照合・実行するのは commit する worktree 自身の `.claude/verify.sh` のバイト列。経路の検査
   （symlink の包含判定、exit 72）は worktree の root に対して行う — main checkout の verify.sh を
   指す symlink も repo 外として 72。実行時の cwd と `VERIFY_REPO_ROOT` は worktree の root。
4. main の key で引いて hash が違うときは 71 ではなく 70（未承認）を返す。起動器の stderr と hook の
   70 の案内は、worktree の path ではなく main の key を承認先として示し、「merge 後に main で承認」と
   書く。71 は「承認した repo 自身のゲートが編集で眠った」の意味のまま（ADR-0059）。
5. `known` は一致した key を stdout に 1 行出す。worktree のゲートの消失・exit 72 も、main が承認済みなら
   block する（ADR-0082 Decision 2 と同じ扱いを worktree に広げる）。worktree のときの reason は、
   branch の verify.sh を main と同じ内容で戻す・verify.sh 導入前の commit から作った worktree なら
   `VERIFY_BYPASS=1`、を先に示し、revoke は「merge 後に main で。main と全 worktree の承認が外れる」と
   書く。
6. `approve` / `revoke` と台帳の形式は変えない。
7. `hooks/bandit-precommit.sh` と `hooks/ruff-format-precommit.sh` の「repo がゲートを持つか」を
   `-x` から `-f` にする（ADR-0082 Follow-ups の残り。verify-precommit と同じ定義にする）。
8. ADR-0082 Decision 4 との関係: 承認済みの `.claude/verify.sh` は worktree の root を
   `VERIFY_REPO_ROOT` として走るので、harness では staged mode でも branch の
   `scripts/hooks/harness_lint.py` が commit 境界で無人実行される（ADR-0082 Decision 4 が
   harness-lint hook では避けたもの）。これを受け入れる。承認台帳が pin するのはゲートの script で
   あって、それが実行する tree ではない — main checkout でも verify.sh は working tree の未 commit の
   `harness_lint.py` を実行してきた。worktree での露出は、その branch を main checkout で checkout して
   commit するときと同じ — どちらでも、session が `harness_lint.py` を編集してから allowlist 済みの
   `git commit` を打てば、permission プロンプトなしでその編集が走る。この等価は、tree が承認済み repo の
   本物の branch であること（Decision 2 の登録判定）に依る。harness-lint hook が main の検査器を使う
   ことは変えない。そちらの残る価値は実行の安全ではなく判定の完全性で、branch が自分の commit を
   止める lint を弱めても、main の lint が止める。

## Review-when

- 判断役の検収（local 経路の merge）で、verify.sh を変える branch の commit 本文に手動 verify の記録が
  要るケースが 30 日で 2 件を超える（その branch の worktree の commit ではゲートが 70 の通知だけで
  走らない）→ 未 merge のゲート編集の扱いを再設計する
- `git worktree list --porcelain` の形式や worktree の登録方法が変わり、実在する worktree が 70 に
  落ちる観測が出る（例: 判断役の検収で、worktree からの commit なのに verify が走っていない）→
  登録判定の方法を見直す（安全側に倒れる失敗なので block はしない）
- 台帳の key の正規化（realpath）や exit code 体系が変わる → `ledger_key` と hook の分岐の前提が崩れる
- 判断役の検収で、worktree のゲート消失の block（verify.sh 導入前の commit から作った worktree を
  含む）を `VERIFY_BYPASS` で通した commit が 30 日で 2 件を超える → worktree では消失を block でなく
  通知にする（ADR-0082 の「ゲート廃止が revoke 前に block され続ける」と一緒に見直す）

## Alternatives Considered

### 現状維持（worktree の commit は build が手動で verify を回し、commit 本文に記録する）

却下: 担保が build の自己申告になる。commit 境界のゲートは「実行したかどうかを実行者に委ねない」
ためにあり、worktree だけがその外に出ていた。`e42fee2` はこの形で担保した実例で、判断役は本文の
記録を信じるしかなかった。

### key を `git rev-parse --git-common-dir` の親ディレクトリで引く（登録を確かめない）

却下: common dir は worktree 側の `.git` ファイルが決める。`gitdir:` に承認済み repo の git dir を
書いたディレクトリに同じバイト列の verify.sh を置けば、そのディレクトリの tree に対して承認済みの
ゲートが無人で走る（Context の実験）。登録の確認は main 側の管理領域から読むので、偽の `.git`
ファイルでは通らない。

### worktree の verify.sh が承認済みと違うとき、main の承認済みのバイト列で worktree の tree を検査する

却下（本 ADR の選択は、その場合ゲートを走らせない = 70）: 比べるのは「古いゲートで新しい tree を検査
する」と「何も走らせない」。見逃しの軸では前者が勝つ。それでも選ばないのは誤った block のため:
branch がゲートとその契約（検査対象・テスト）を一緒に変えると、古いゲートは新しい tree を誤って
止め、build はそれを直せない（直すにはゲートを戻すしかない）。一方、何も走らせない期間の
リスクは次の 3 つで抑えられている: skill `task-triage` は build が `.claude/verify.sh` を変える diff を
bounce するので該当 branch は例外に限られる、同 skill の local 経路では判断役が merge 前に worktree で
verify.sh を自分で走らせる、merge 後の main の最初の commit は 71 で止まり人間の approve を強制する
（ADR-0059 が 70 型の通知だけでは 3 週間放置されたと記録したのと違い、失効は merge 時点で block に
変わる）。

### worktree の path をそのつど人間が approve する運用にする

却下: 使い捨ての path が台帳に溜まり、worktree を消しても revoke されずに残る。path の key は main の
key より優先されるので、残った key は同じ path に後で作る worktree の判定にも効く。worktree を作る
たびに人間の操作が 1 手要る。この運用は今も可能（Decision 1）だが既定にしない。main が承認済みの
ときは hook も案内しない（Decision 4）。main が台帳に無いときは worktree かどうかを台帳から判定でき
ないので、hook は従来どおり toplevel（= worktree の path）の approve を案内する（変更前と同じ）。

### main の key で hash が違うときも 71（block）にする

却下: branch で verify.sh を編集すると、その worktree からの commit がすべて止まる。branch の
バイト列の承認は merge 後に main で行う（skill `task-triage` の merge 手順）ので、未 merge の編集を
「承認済みゲートの失効」とは扱わない。

### 台帳の key を git common dir 単位に変える

却下: common dir は `.git` ファイルが決めるので、key の引き方として「common dir の親」案と同じ偽装を
受ける。加えて台帳の形式と approve / revoke を変え、既存の承認の移行も要る（packet は「承認の書き込み
側（approve / revoke と台帳の形式）は変えない」と指定していた）。

## Consequences

### Positive

- 承認済み repo の linked worktree からの commit で、worktree の verify.sh が承認済みのバイト列と
  同じならゲートが走る。harness の build branch の commit も commit 境界で検査される
- 偽の `.git` ファイルで承認済み repo を名乗るディレクトリ、消えた登録の path に後から置いた
  ディレクトリ、承認済み repo の work tree に置いた偽の管理領域に登録されたディレクトリ、消えた登録の
  path の祖先に置いた symlink の先のディレクトリでは走らない。
  `--relative-paths` で登録された worktree では走る
- 通常 repo、main worktree 自身、path で直接承認された worktree の挙動は変わらない
- bandit / ruff-format と verify-precommit で「ゲートがある」の定義が 1 つになる。`-x` の無い
  verify.sh では bandit / ruff-format も譲る（二重検査が消える）。ディレクトリの `.claude/verify.sh`
  には譲らない

### Negative

- 承認済みのゲートが、未 merge の branch の tree を無人で検査する。ゲートが tree のコード（harness の
  `harness_lint.py`、テスト等）を実行する repo では、branch のコードが commit 境界で走る。露出は、
  その branch を main checkout で checkout して commit するときと同じで、書き手が build でも第三者でも
  変わらない（Decision 8）
- verify.sh を編集する branch では、その worktree の commit でゲートが走らない（70 の通知）。変更前と
  同じ状態で、merge 後に main で approve するまで続く
- worktree の verify.sh の削除・worktree の外を指す symlink 化が block になる。verify.sh 導入前の commit から作った
  worktree も同じく block になり、出口は commit ごとの `VERIFY_BYPASS=1` になる（新しい摩擦）
- worktree のゲート消失への revoke は main の key に効くので、main と全 worktree の承認が外れる
  （ADR-0082 では消失した repo だけだった）。reason は revoke を merge 後の操作として最後に置く
- 登録の管理ディレクトリそのものを指す `.git` ファイルを持つディレクトリを、消えた登録の path
  そのものに置く形は区別できない。`.git` ファイルは repo の tree では運べず、その path へのローカル
  書き込みが要るので、保護範囲（untrusted な repo の内容）の外に置く
- main が bare の worktree、main が `--separate-git-dir` の repo や submodule の work tree の worktree
  （git 2.54.0 の `worktree list` は main を git dir の path で報告するので台帳の key と一致しない）、
  common dir が main 自身の git dir と一致しない構成の worktree、登録後に path の祖先が symlink に
  置き換わった（移動して symlink で戻した等）本物の worktree は、従来どおり 70（安全側）
- 台帳に無い repo の commit で subprocess が増える: 起動器の中で git が 1 回（worktree の path が一覧に
  一致したときは 3 回）。ゲートがあって 70 になった commit では、hook が案内のために `known` の
  python3 を 1 回余分に起動し、その中で同じ回数の git が走る。ゲートが無い repo では `known` 経由で
  同じ回数。git はそれぞれ 10 秒の timeout を持つが、`known` の python3 自体には外側の timeout が無い
- `-x` の無い **未承認の** verify.sh を持つ repo では、bandit / ruff-format も譲るようになり、
  verify（70）と合わせて 3 つの Python 側ゲートが揃って黙る範囲が広がる。`-x` は repo 側で git の mode
  として付けられるので、守りとしては変わらない（bandit-precommit.sh の NOTE の既知の性質の延長）

### Neutral / Follow-ups

- 戻すのは安い: `ledger_key` を「repo 自身の key だけ」に戻す 1 関数と、hook の 70 と消失の案内の
  worktree 分岐、bandit / ruff-format の 1 行ずつ
- 回帰は `tests/verify-precommit.bats` の「a linked worktree is judged by its main checkout's approval」
  節と、`tests/bandit-precommit.bats` / `tests/ruff-format-precommit.bats` の stand-down の 2 本ずつ（計 4 本）
- harness の `hooks/README.md` の verify-precommit 行は本 ADR と同じ commit で追従した
- 公開 repo（claude-harness）の hooks の記述（ゲートの有無の定義と worktree の扱い）は harness-sync
  時に追従が要る（公開は人間の操作）
- ADR-0082 の Decision 2 / 3 / 4・Review-when・Follow-ups、ADR-0059 の Decision に注記を入れた

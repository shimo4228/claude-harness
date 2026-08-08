---
name: spawn-session
description: "新しい detached な Claude Code Remote Control セッションを Herdr 内に起動し、Claude モバイルアプリのセッション一覧に出す。生きている任意のセッションから（多くは iPhone の Remote Control 越しに）呼んで、別プロジェクトの新規セッションを Mac に触れず立ち上げる。Use when the user says 「新しいセッション立てて」「AAP のセッション開いて／立ち上げて」「contemplative のセッション作って」「spawn a (new) session」「launch a remote control session」「start a session for X」, or invokes `/spawn-session [project]`. NOT for: 既存会話の resume（`--continue`/`--resume`）、同一セッション内の文脈リセット（`/clear`）、現セッションの model 切替。"
user-invocable: true
origin: shimo4228
---

# spawn-session

生きている任意のセッションから、**名前付き・detached な新しい Claude Code Remote Control セッション**を Herdr 内に起動する。新セッションは自分の RC を登録するので Claude モバイルアプリのセッション一覧に出る。iPhone から Remote Control 越しに操作している最中に、Mac に触れず別プロジェクトのセッションを増やすのが主用途。Herdr の艦隊ビュー（サイドバー・agent status）にもそのまま並ぶ。

## When to use

- 新しいセッションが欲しい（多くは別プロジェクト用）でモバイルアプリ一覧に出したい
- トリガー例: 「新しいセッション立てて」「AAP のセッション開いて」「spawn a session for X」/ `/spawn-session [project]`

## When NOT to use

- 既存の会話を続けたい → `claude --continue` / `--resume`
- 現在のセッションの文脈を消したいだけ → `/clear`
- 現在のセッションの model / effort 切替 → `/model`, `--effort`
- **同じ repo で複数セッションが欲しいだけ** → 公式 server mode（`claude remote-control --spawn worktree --capacity N`）で足りる。この skill は要らない
- **Dispatch で足りる用件** → Cowork タブの Dispatch に投げると、開発作業なら **Code タブのセッション**が起きる（Dispatch バッジ付きでサイドバーに出る）。**`~/.claude` の設定系は読まれる** — personal skills in `~/.claude/skills/` は local session に効き、`~/.claude/settings.json` も Desktop と共有される（設定が claude.ai 同期になるのは **Cowork タブ側**の skills / plugins / connectors であって Code セッションではない）。この skill を使う理由は設定の届き方ではなく、**Desktop アプリが実行主体になり Herdr 艦隊ビューに並ばないこと**と、**起こす repo をこちらが選べないこと**（Dispatch が種別で振り分ける）。Pro/Max 限定で Team/Enterprise では使えない
- **cloud session**（Claude Code on the web）→ Anthropic 側で実行されるので、ローカル FS / MCP / Herdr と無関係。手元の repo を触らせたいなら対象外

## How it works

埋めているギャップは **cwd の壁**であって、セッション数の壁ではない（2026-08-01 に公式 docs で確認）。公式 Remote Control には server mode があり `--spawn <same-dir|worktree|session>` / `--capacity <N>`（既定 32）/ `--[no-]create-session-in-dir` で **1 プロセスから複数セッション**を持てる。ただし **server mode の全セッションはその server プロセスの cwd（= 1 repo）に縛られる** — `same-dir` は cwd 共有、`worktree` はその repo の worktree。**別プロジェクトのセッションを起こす手段が公式には無い**。回避策: 生きている任意のセッションが Bash で別の `claude --remote-control "<名前>"` を、指定した repo の cwd で Herdr の pane 内に detached 起動する。新プロセスが自分の RC を登録し、アプリ一覧に出る。Herdr の persistent session（server）が pty を保持するので、Ghostty/SSH の切断や起動元セッションの終了後も生き残る。server が動いていなければ spawn.sh が headless server を自動起動する（tmux のサーバー自動起動と同等のセマンティクス）。

配置は repo 単位 workspace 運用に合わせる: **同じルート（cwd）の workspace が既にあればそこに新 tab、無ければ新 workspace を作成**（workspace label は repo 名、表示名は tab label）。

前提: 呼び出し元として **最低 1 つのセッションが生きている**こと（Mac 稼働中は通常複数生存している）。Mac 再起動直後で何も動いていない場合は Mac の前で 1 つ起動する。どのみち Mac が落ちていればモバイル側からは何もできない。

## Execution

1. **プロジェクトを解決する。** `$ARGUMENTS` またはユーザーの言い回しから、`$CC_PROJECTS_ROOT`（既定 `~/MyAI_Lab`）配下のディレクトリを 1 つ特定する。
   - 名前でマッチ。ニックネームは推論で解決する（例: "AAP" → `agent-attribution-practice`、"CA"/"contemplative" → `contemplative-agent`、"AKC" → `agent-knowledge-cycle`）。
   - 不確かなら `ls "${CC_PROJECTS_ROOT:-$HOME/MyAI_Lab}"` で確認。曖昧 or 該当なしなら**候補を出して聞く**。誤った repo を当て推量で起動しない。
   - 表示名はユーザー向けの綺麗なラベルにする（例: "AAP", "Contemplative Agent"）。dir 名と user-facing 名が違う場合は user-facing 名を使う。
   - **命名規約 `<label>/<purpose>`**: ユーザーの発話にセッションの目的が含まれていれば、1〜2 語の英小文字スラッグにして表示名に付ける（「AAP のリリース作業やらせたい」→ "AAP/release"、「issue 42 直して」→ "AAP/issue-42"）。目的が読み取れなければ label のみでよい — 同名セッションが既に生きている場合の " #n" 付与は spawn.sh が自動で行う（意味づけはここ、重複解消は script、の分担）。目的を聞き返してまで埋めない。

2. **起動する。** `spawn.sh` は本 SKILL.md と同じディレクトリにある（直置きなら
   `~/.claude/skills/spawn-session/`、plugin 導入なら plugin の skill ディレクトリ）:
   ```
   bash <この skill のディレクトリ>/spawn.sh <解決した絶対パスの project-dir> "<表示名>"
   ```

3. **報告する。** 返ってきたセッション名をユーザーに伝える（アプリ一覧で何をタップすればよいかの目印になる）。

4. **そのまま仕事を投げるなら、agent 名は出力の `agent:` 行から取る。**
   `herdr agent *` に渡すのは**表示名ではない** — spawn.sh が
   `slug(表示名 を小文字化・[a-z0-9_-] 以外を - に・20 文字で切る) + "-" + PID` で
   別名を生成している（agent 名の制約 `[a-z][a-z0-9_-]{0,31}` + live 中一意のため）。
   表示名をそのまま渡すと `agent_not_found` になる。出力を取り損ねたら
   `herdr agent list` の `name` から引く（`cwd` で目的の pane を特定できる）。

5. **着弾を確認する。** 起動直後の agent への最初の `herdr agent prompt` は
   **落ちることがある**（毎回ではない。2026-07-25 実測で 3 回中 2 回成功・1 回失敗）。
   `spawn.sh` が「claude idle 到達 ✓」を出し、`agent get` が
   `agent_status: idle` / `interactive_ready: true` を返していても起きる。

   ```bash
   herdr agent prompt "<agent 名>" "$(cat task.txt)" --wait --timeout 180000
   herdr agent get "<agent 名>"   # 状態を必ず見る。ここを省かない
   ```

   **`agent_status` だけで着弾判定しない。** `done` は「作業を終えて応答待ち」でもあり、
   prompt 直後でも**着弾して即答した場合に `done` が返る**（2026-07-25 実測: 58 秒
   working したあと done に落ち、ステータスだけ見て失敗と誤読しかけた）。
   確定させるには `herdr agent read "<agent 名>" --source visible` で pane を見る。

   **失敗の出方が 2 通りあり、片方は成功と区別できない**:
   - `agent_prompt_stalled` が返り、入力欄は空 — エラーなので気づける
   - **成功形の空レスポンス `{"result":{}}`** が返り、テキストは
     `[Pasted text #1 +N lines]` として入力欄に残るが Enter が入らない。
     エラーが出ないので、送ったつもりで idle 放置になる。これが危険な方

   後者の復旧は `herdr agent send-keys "<agent 名>" enter`。ただし**入力欄の中身が
   人間の書きかけなら押さない** — Enter はユーザーの操作であって、代理で押すものではない。

   **長さは無関係** — 落ち着いた agent なら 42 行の複数行プロンプトも 1 発で通り、
   短文でも起動直後なら落ちる。変数はタイミングだけ。
   （初見では「長文だから」と推定しかけたが、短文でも同じく落ちることと、長文が
   落ち着いた agent には通ることを実測して否定した。1 回の観察から原因を決めると、
   効かない対処が固定化される）

## Plan mode で起動したいとき

**`spawn.sh` は claude のフラグを転送しない。** 起動行は
`agent start ... -- --remote-control "$NAME"` に固定で、`--permission-mode plan`
を通す口が無い（引数 `$2` は表示名として消費される）。フラグを増やしたくなったら
それは spawn.sh の変更であって、呼び出し側の工夫では届かない。

**効く手順は「起動 → 最初のプロンプトで入らせる」。** plan mode は
`EnterPlanMode` で新セッション自身が入れるので、kickoff プロンプトの冒頭に
そう書く。2026-07-26 に実測: pane が `⏸ plan mode on` を表示し、同じプロンプト内で
指定した `/grill-me` がそのまま plan mode 下で走った。

```
まず plan mode に入って（EnterPlanMode）、そのうえで /grill-me を起動してほしい。
題材は <...>
```

- **スラッシュコマンドは同じプロンプトに同居できる**。`/grill-me` のような
  user-invocable skill は kickoff 本文に書けば起動する（別送しなくてよい）。
- **`send-keys` で shift+tab を送って切り替えようとしない。** モード循環はキー列の
  当て推量で、pane の状態に依存する。プロンプトで入らせる方が決定論的で、しかも
  「なぜ plan mode なのか」が新セッションの文脈に残る。
- **背景を持たせる。** plan mode の新セッションは前セッションの文脈を持たない。
  台帳の該当行・却下済みの選択肢・触ってはいけない前提を kickoff に書いておくと、
  最初の質問から本題に入る（書かないと現状把握の往復に 1 ラウンド消える）。
- 逆に **`--permission-mode dontAsk` 等で起動したい場合も同じ制約**。フラグが要るなら
  spawn.sh 側に足す（そのときは「表示名」と「claude へ渡す引数」の境界を壊さないこと）。

## Failure modes

- `no such directory` → プロジェクト解決が誤り。再解決するか候補を出して聞く。
- `herdr not found` → `brew install herdr`。
- `herdr server を起動できませんでした` → headless 自動起動が失敗。`herdr status` で server の状態を確認する。
- `claude が idle に到達しませんでした` 警告（pane の直近出力付き）→ 生やした claude が起動に失敗した。典型原因は Claude Code の auth（OAuth）切れ — Mac 側でのブラウザ再ログインが必要で、モバイル側からは対処できない。または `claude` が pane シェルの PATH に無い。
- **workspace trust ダイアログで止まる（未対応・既知の制約）** → その repo で一度も Claude Code を開いたことがない場合、起動直後に trust の確認が出るが、detached 起動には**押す人がいない**。`spawn.sh` は trust を一切扱わない（2026-08-01 確認）。**自動で `~/.claude.json` の `hasTrustDialogAccepted` を立てる回避はしない** — それは security gate を黙って外す行為で、モバイルから未知の repo を trust させる経路を作ってしまう。**対処は「初回だけ Mac 側で一度開いておく」**。pane に入れば人間が押せるので、`herdr agent read` で画面を見て判断する。

## Notes

- `spawn.sh` は解決済みの dir と名前を受け取るだけの dumb な起動器（プロジェクト解決の知能はこの SKILL.md 側に置く＝エイリアス表をハードコードしないことで移植性を保つ）。
- プロジェクト群が `~/MyAI_Lab` 以外にある環境では `CC_PROJECTS_ROOT` を設定して上書きする。
- ターミナルからは `cc-spawn <dir> [name]`（`~/bin/cc-spawn` → 本 `spawn.sh` への symlink）でも同じことができる。
- **herdr skill の `HERDR_ENV=1` ゲートとの整合**: あのゲートは既存 pane の inspect/control 用。spawn-session は **create-only**（新 workspace/tab の作成と、自分が作った pane への `pane run` のみ）+ `--no-focus` の socket 利用で、既存の pane・focus・他クライアントに触れないため、HERDR_ENV 外からの実行を認めた sanctioned exception（前提は server 稼働のみ。2026-07-21 の tmux → herdr 乗り換えで決定）。

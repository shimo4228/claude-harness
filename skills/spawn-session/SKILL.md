---
name: spawn-session
description: "Start a new detached Claude Code Remote Control session inside Herdr, so it shows in the Claude mobile app. Use when asked to start a session for a project (新しいセッション立てて)."
user-invocable: true
origin: shimo4228
---

# spawn-session

生きている任意のセッションから、**名前付き・detached な新しい Claude Code Remote Control セッション**を Herdr 内に起動する。新セッションは自分の RC を登録するので Claude モバイルアプリのセッション一覧に出る。iPhone から Remote Control 越しに操作している最中に、Mac に触れず別プロジェクトのセッションを増やすのが主用途。Herdr の艦隊ビュー（サイドバー・agent status）にもそのまま並び、skill: `agent-send` で指示を送れる。session や script（task-triage の dispatch、launchd の tick）から起こす経路でもある。

## When to use

- 新しいセッションが欲しい（多くは別プロジェクト用）でモバイルアプリ一覧に出したい
- トリガー例: 「新しいセッション立てて」「AAP のセッション開いて」「spawn a session for X」/ `/spawn-session [project]`

## When NOT to use

- 既存の会話を続けたい → `claude --continue` / `--resume`
- 現在のセッションの文脈を消したいだけ → `/clear`
- 現在のセッションの model / effort 切替 → `/model`, `--effort`
- **よく使うフォルダで phone から 1 本起こしたいだけで、Herdr pane に置かなくてよい** → Desktop アプリの Settings > Claude Code の「スマートフォンと claude.ai からここでセッションを開始できるようにする」をオンにすると、アプリが開いている間、Claude アプリの Code タブに Mac の device card が出る。選べるのは登録フォルダ（Claude Code でよく使う 6 個まで + ピン留め・追加したもの）で、任意の directory はたどれない（2026-10-10、Desktop の設定画面で確認）。その session は Desktop アプリの下で動き、Herdr pane には並ばず agent-send も届かない。Desktop が公開中のフォルダでは CLI の `claude remote-control` は起動を拒む
- **同じ repo で複数セッションが欲しいだけ** → 公式 server mode（`claude remote-control --spawn worktree --capacity N`）で足りる。この skill は要らない
- **Dispatch で足りる用件** → Cowork タブの Dispatch に投げると、開発作業なら **Code タブのセッション**が起きる（Dispatch バッジ付きでサイドバーに出る）。**`~/.claude` の設定系は読まれる** — personal skills in `~/.claude/skills/` は local session に効き、`~/.claude/settings.json` も Desktop と共有される（設定が claude.ai 同期になるのは **Cowork タブ側**の skills / plugins / connectors であって Code セッションではない）。この skill を使う理由は設定の届き方ではなく、**Desktop アプリが実行主体になり Herdr 艦隊ビューに並ばないこと**と、**起こす repo をこちらが選べないこと**（Dispatch が種別で振り分ける）。Pro/Max 限定で Team/Enterprise では使えない
- **cloud session**（Claude Code on the web）→ Anthropic 側で実行されるので、ローカル FS / MCP / Herdr と無関係。手元の repo を触らせたいなら対象外

## How it works

埋めているギャップは **cwd の壁**であって、セッション数の壁ではない（2026-08-01 に公式 docs で確認）。公式 Remote Control には server mode があり `--spawn <same-dir|worktree|session>` / `--capacity <N>`（既定 32）/ `--[no-]create-session-in-dir` で **1 プロセスから複数セッション**を持てる。ただし **server mode の全セッションはその server プロセスの cwd（= 1 repo）に縛られる** — `same-dir` は cwd 共有、`worktree` はその repo の worktree。phone から別プロジェクトを起こす公式の道は、上の device card（登録フォルダに限る）。この skill は、登録していないプロジェクトをニックネームから解決し、Herdr の pane に置き、session や script からも起こせる道で、生きている任意のセッションが Bash で別の `claude --remote-control "<名前>"` を、指定した repo の cwd で Herdr の pane 内に detached 起動する。新プロセスが自分の RC を登録し、アプリ一覧に出る。Herdr の persistent session（server）が pty を保持するので、Ghostty/SSH の切断や起動元セッションの終了後も生き残る。server が動いていなければ spawn.sh が headless server を自動起動する（tmux のサーバー自動起動と同等のセマンティクス）。

配置は repo 単位 workspace 運用に合わせる: **同じ repo の workspace が既にあればそこに新 tab、無ければ新 workspace を作成**（workspace label は repo 名、表示名は tab label）。同じ repo かは git の main worktree root で判定するので、linked worktree（`<repo>/.claude/worktrees/<name>` や scratchpad 下）を渡しても repo の workspace に合流し、tab の cwd だけが worktree になる。

前提: 呼び出し元として **最低 1 つのセッションが生きている**こと（Mac 稼働中は通常複数生存している）。Mac 再起動直後で何も動いていない場合は Mac の前で 1 つ起動する。どのみち Mac が落ちていればモバイル側からは何もできない。

## Execution

1. **プロジェクトを解決する。** `$ARGUMENTS` またはユーザーの言い回しから、`$CC_PROJECTS_ROOT`（既定 `~/MyAI_Lab`）配下のディレクトリを 1 つ特定する。
   - 名前でマッチ。ニックネームは推論で解決する（例: "AAP" → `agent-attribution-practice`、"CA"/"contemplative" → `contemplative-agent`、"AKC" → `agent-knowledge-cycle`）。
   - 不確かなら `ls "${CC_PROJECTS_ROOT:-$HOME/MyAI_Lab}"` で確認。曖昧 or 該当なしなら**候補を出して聞く**。誤った repo を当て推量で起動しない。
   - 表示名はユーザー向けの綺麗なラベルにする（例: "AAP", "Contemplative Agent"）。dir 名と user-facing 名が違う場合は user-facing 名を使う。
   - **命名規約 `<label>/<purpose>`**: ユーザーの発話にセッションの目的が含まれていれば、1〜2 語の英小文字スラッグにして表示名に付ける（「AAP のリリース作業やらせたい」→ "AAP/release"、「issue 42 直して」→ "AAP/issue-42"）。目的が読み取れなければ label のみでよい — 同名セッションが既に生きている場合の " #n" 付与は spawn.sh が自動で行う（意味づけはここ、重複解消は script、の分担）。目的を聞き返してまで埋めない。

2. **起動する。**
   ```
   ${CLAUDE_SKILL_DIR}/spawn.sh <解決した絶対パスの project-dir> "<表示名>" \
     [--model <model>] [--effort <level>] [--permission-mode <mode>] [--prompt-file <path>]
   ```
   - `--model` は省略時 settings.json の既定（判断層 = fable）。build 層の worker session
     （task-triage の dispatch）は `--model opus` で立てる（判断は fable、実装は opus の三役分担のため）
   - `--effort`（low / medium / high / xhigh / max）と `--permission-mode`（manual / acceptEdits /
     auto / dontAsk / plan）は claude の同名 flag に渡る。`bypassPermissions` は受けない
     （phone から起こす session の権限を広げないため）。`/effort` を後から prompt で送らない —
     slash command は turn を起こさず、着弾を確かめられない
   - `--prompt-file` は起動後に skill: `agent-send` でファイルを最初の指示として送り、結果を
     `prompt: result=…` 行に出す。届かなければ agent-send の exit code（2 / 3 / 4）で終わる。
     session は残っているので、`result=` を見て次の手を決める（agent-send の表）

3. **報告する。** 返ってきたセッション名をユーザーに伝える（アプリ一覧で何をタップすればよいかの目印になる）。

4. **後から仕事を投げる・終わりを待つ** ときは skill: `agent-send` を使う。宛先は出力の
   `herdr:` 行の pane ID か表示名でよい（`agent:` 行の名前は `herdr agent *` に直接渡すとき用 —
   表示名は agent 名ではないので、`herdr agent *` に渡すと `agent_not_found` になる）。
   作業中の session に送らない・本文を再送しない・完了は `agent-send.sh wait` を background で待つ、
   の判断は agent-send が持つ。

## Plan mode で起動したいとき

`--permission-mode plan` で起動し、題材は `--prompt-file` で渡す。

- **スラッシュコマンドは同じ kickoff に同居できる**。`/grill-me` のような user-invocable skill は
  kickoff 本文に書けば起動する（別送しなくてよい）
- **背景を持たせる。** 新セッションは前セッションの文脈を持たない。台帳の該当行・却下済みの選択肢・
  触ってはいけない前提を kickoff に書いておくと、最初の質問から本題に入る（書かないと現状把握の往復に
  1 ラウンド消える）

## Failure modes

- `no such directory` → プロジェクト解決が誤り。再解決するか候補を出して聞く。
- `herdr not found` → `brew install herdr`。
- `herdr server を起動できませんでした` → headless 自動起動が失敗。`herdr status` で server の状態を確認する。
- `herdr の preflight に失敗しました` → client と server の版ずれ。直前の stderr（agent-send の preflight）の手順に従う。
- `claude が idle に到達しませんでした` 警告（pane の直近出力付き）→ 生やした claude が起動に失敗した。典型原因は Claude Code の auth（OAuth）切れ — Mac 側でのブラウザ再ログインが必要で、モバイル側からは対処できない。または `claude` が pane シェルの PATH に無い。
- **`原因: workspace trust の確認で停止`** → その repo で一度も Claude Code を開いたことがない場合、起動直後に trust の確認が出るが、detached 起動には**押す人がいない**。spawn.sh は画面の文言で検知して名指しするだけで、trust は通さない。**自動で `~/.claude.json` の `hasTrustDialogAccepted` を立てる回避はしない** — それは security gate を黙って外す行為で、モバイルから未知の repo を trust させる経路を作ってしまう。**対処は「初回だけ Mac 側で一度開いておく」**。pane に入れば人間が押せるので、`herdr agent read` で画面を見て判断する。

## Notes

- `spawn.sh` は解決済みの dir と名前を受け取るだけの dumb な起動器（プロジェクト解決の知能はこの SKILL.md 側に置く＝エイリアス表をハードコードしないことで移植性を保つ）。
- プロジェクト群が `~/MyAI_Lab` 以外にある環境では `CC_PROJECTS_ROOT` を設定して上書きする。
- テスト: `${CLAUDE_SKILL_DIR}/tests/spawn.bats`（偽の herdr は agent-send の `tests/bin/` を共用）。
- ターミナルからは `cc-spawn <dir> [name]`（`~/bin/cc-spawn` → 本 `spawn.sh` への symlink）でも同じことができる。
- **herdr skill の `HERDR_ENV=1` ゲートとの整合**: 例外は `rules/common/boundary.md` の「人間に渡す」節の Herdr 委譲の項に記載済み（そちらが正本）。根拠は本 skill が **create-only** であること — 新 workspace/tab の作成と自分が作った pane への `pane run` のみ、`--no-focus` の socket 利用で既存の pane・focus・他クライアントに触れない。前提は server 稼働のみ。

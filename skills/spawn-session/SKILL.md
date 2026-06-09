---
name: spawn-session
description: 新しい detached な Claude Code Remote Control セッションを tmux で起動し、Claude モバイルアプリのセッション一覧に出す。生きている任意のセッションから（多くは iPhone の Remote Control 越しに）呼んで、別プロジェクトの新規セッションを Mac に触れず立ち上げる。Use when the user says 「新しいセッション立てて」「AAP のセッション開いて／立ち上げて」「contemplative のセッション作って」「spawn a (new) session」「launch a remote control session」「start a session for X」, or invokes `/spawn-session [project]`. NOT for: 既存会話の resume（`--continue`/`--resume`）、同一セッション内の文脈リセット（`/clear`）、現セッションの model 切替。
user-invocable: true
origin: shimo4228
---

# spawn-session

生きている任意のセッションから、**名前付き・detached な新しい Claude Code Remote Control セッション**を tmux で起動する。新セッションは自分の RC を登録するので Claude モバイルアプリのセッション一覧に出る。iPhone から Remote Control 越しに操作している最中に、Mac に触れず別プロジェクトのセッションを増やすのが主用途。

## When to use

- 新しいセッションが欲しい（多くは別プロジェクト用）でモバイルアプリ一覧に出したい
- トリガー例: 「新しいセッション立てて」「AAP のセッション開いて」「spawn a session for X」/ `/spawn-session [project]`

## When NOT to use

- 既存の会話を続けたい → `claude --continue` / `--resume`
- 現在のセッションの文脈を消したいだけ → `/clear`
- 現在のセッションの model / effort 切替 → `/model`, `--effort`

## How it works

公式 Remote Control はモバイル側から新セッションを起こせない（1 マシン基本 1 セッション）。回避策: 生きている任意のセッションが Bash で別の `claude --remote-control "<名前>"` を tmux 内に detached 起動する。新プロセスが自分の RC を登録し、アプリ一覧に出る。tmux が pty を保持するので SSH/ネットワーク切断や起動元セッションの終了後も生き残る。

前提: 呼び出し元として **最低 1 つのセッションが生きている**こと（Mac 稼働中は通常複数生存している）。Mac 再起動直後で何も動いていない場合は Mac の前で 1 つ起動する。どのみち Mac が落ちていればモバイル側からは何もできない。

## Execution

1. **プロジェクトを解決する。** `$ARGUMENTS` またはユーザーの言い回しから、`$CC_PROJECTS_ROOT`（既定 `~/MyAI_Lab`）配下のディレクトリを 1 つ特定する。
   - 名前でマッチ。ニックネームは推論で解決する（例: "AAP" → `agent-attribution-practice`、"CA"/"contemplative" → `contemplative-agent`、"AKC" → `agent-knowledge-cycle`）。
   - 不確かなら `ls "${CC_PROJECTS_ROOT:-$HOME/MyAI_Lab}"` で確認。曖昧 or 該当なしなら**候補を出して聞く**。誤った repo を当て推量で起動しない。
   - 表示名はユーザー向けの綺麗なラベルにする（例: "AAP", "Contemplative Agent"）。dir 名と user-facing 名が違う場合は user-facing 名を使う。

2. **起動する:**
   ```
   bash ~/.claude/skills/spawn-session/spawn.sh <解決した絶対パスの project-dir> "<表示名>"
   ```

3. **報告する。** 返ってきたセッション名をユーザーに伝える（アプリ一覧で何をタップすればよいかの目印になる）。

## Failure modes

- `no such directory` → プロジェクト解決が誤り。再解決するか候補を出して聞く。
- `tmux not found` → `brew install tmux`。
- 起動はしたが直後に `tmux セッションが消えた` 警告 → 生やした claude が即終了した。典型原因は Claude Code の auth（OAuth）切れ — Mac 側でのブラウザ再ログインが必要で、モバイル側からは対処できない。または `claude` がログインシェルの PATH に無い。

## Notes

- `spawn.sh` は解決済みの dir と名前を受け取るだけの dumb な起動器（プロジェクト解決の知能はこの SKILL.md 側に置く＝エイリアス表をハードコードしないことで移植性を保つ）。
- プロジェクト群が `~/MyAI_Lab` 以外にある環境では `CC_PROJECTS_ROOT` を設定して上書きする。
- ターミナルからは `cc-spawn <dir> [name]`（`~/bin/cc-spawn` → 本 `spawn.sh` への symlink）でも同じことができる。

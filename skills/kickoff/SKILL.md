---
name: kickoff
description: "新セッションの定型立ち上げルーチン。dispatch でローカル新セッションを起こした直後の最初のプロンプト（または任意のセッション開始時）に `/kickoff [フォーカス]` と打つと、repo 状態の把握（git status / branch 同期 / 直近コミット / 構成）、未完了シグナル検出（dirty / stash / 未 push / open PR）、固定フォーマットの状態報告までを一発で行う。Use when the user invokes /kickoff, or opens a session with 「まず状態を確認して」「立ち上げルーチンやって」「今どんな状態か教えて」. NOT for: 新セッションの起動そのもの（それは dispatch UI / spawn-session）、既存会話の resume（--continue / --resume）、特定バグや機能の深掘り調査（それは通常のタスクとして依頼する）。"
user-invocable: true
origin: shimo4228
---

# kickoff

新セッション開始時の定型立ち上げルーチン。dispatch のプロンプト欄に毎回自然言語で
「〜のセッション立ち上げて。まず git status と直近コミットを確認して…」と書く代わりに、
`/kickoff` の 1 コマンドで同じ品質の立ち上げを再現する。

`$ARGUMENTS` は任意のフォーカス指定。例: `/kickoff READMEレビューの続き`。
指定があれば報告の最後をそのフォーカスへの応答にする。なければ履歴から次の一手を推定する。

## When to use

- dispatch でローカル新セッションを起こした直後の最初のプロンプト（主用途）
- ターミナルで新しくセッションを開いた直後の状態把握
- しばらく触っていなかった repo に戻ってきたとき

## When NOT to use

- 新セッションの起動そのもの → dispatch UI（または旧 spawn-session）
- 既存会話の続き → `claude --continue` / `--resume`
- 状態把握でなく特定タスクの実行 → 直接そのタスクを依頼する

## Execution

**Step 1 — repo 状態把握**（独立コマンドは 1 メッセージで並列実行）:

```
git status --short --branch
git log --oneline -10
ls -la
```

- branch 行（`## main...origin/main [ahead 2]` 等）から同期状態を読む
- git repo でない場合はこの Step を `ls -la` + 主要ファイル（README 等）の確認に差し替える

**Step 2 — 未完了シグナル検出**（fail-soft: 使えないものは黙って skip）:

```
git stash list
git log --oneline @{u}..HEAD   # 未 push コミット（upstream が無ければ skip）
gh pr list --state open --limit 10   # remote が GitHub で gh が使える場合のみ
```

- dirty / staged ファイルは Step 1 の `git status` から読む
- `gh` の認証切れ・remote なしはエラー報告せず「確認不能」として扱う

**Step 3 — 固定フォーマットで報告**:

```
## 状態サマリ
ブランチ / origin との同期 / ツリー clean or dirty

## 直近の動き
コミット履歴から「最近何をしていたか」を 2-4 行で要約
（コミットメッセージの羅列でなく、作業のまとまりとして読む）

## 未完了シグナル
dirty files / stash / 未 push / open PR — なければ「なし」と明記

## 次の一手
$ARGUMENTS があればそれへの応答。
なければ履歴と未完了シグナルから着手候補を 1-3 個提示（押し付けず、質問で締める）
```

## Notes

- **プロジェクト解決はしない**。dispatch が cwd を決めてから起動されるので、この skill は
  カレントディレクトリをそのまま対象にする（project-agnostic）。
- 深掘り（個別ファイルの diff、CI ログ、issue 精査）はルーチンに含めない。
  報告後にユーザーが指示した分だけやる — kickoff は「地図を出す」までが仕事。
- CLAUDE.md / rules はセッションが自動ロードするので、この skill から再読み込みしない。

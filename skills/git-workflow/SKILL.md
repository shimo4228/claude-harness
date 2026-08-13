---
name: git-workflow
description: この環境で git コマンドを Bash 実行するときの permission 摩擦回避作法。git add / commit / push / status 等を実行する前に参照する。git 同士の && 連結は通るが、cd を git と混ぜると双方許可済みでもプロンプトする（git -C を使う）。commit メッセージに $( ) を含めない。push は sandbox 無効化が必要。
origin: shimo4228
---

# git-workflow — この環境での git コマンド実行作法

許可設定は `Bash(git:*)`（`~/.claude/settings.json` の permissions.allow）。照合エンジンは
複合コマンドを**分解して各セグメントを独立照合**する（区切り: `&&` `||` `;` `|` `&` 改行）。
全セグメントが git なら自動許可されるが、以下の罠は allowlist で回避できない。

## 規則

1. **git 同士の連結（`git add … && git commit …` 等）は可** — 各セグメントが
   `Bash(git:*)` に載るため auto-approve される（2026-08-13 実測 + 公式 permissions doc）。
   非 git コマンドを 1 つでも挟むとそのセグメントで照合が外れる
2. **cd を git と混ぜない — `git -C <dir>` を使う**。cd + git の組み合わせは、双方が
   個別に許可済みでも**ハードコードの特例としてプロンプトする**（移動先ディレクトリの
   git hooks 実行リスクのため。公式 permissions doc 明記）。`Bash(cd:*)` を足しても回避不能
3. コミットメッセージは `-m "…"` の単純形（複数 `-m` 可）または `-F <file>`。
   バッククォート・`$( )`・heredoc は injection 検出で必ず承認要求になる
   （v2.1.218 以降は `--dangerously-skip-permissions` でも昇格。無効化オプションなし）
4. `git push` は sandbox の network / credential 制約で失敗するため
   `dangerouslyDisableSandbox: true` を付けて実行する
   （認証は `gh auth setup-git` 済み — memory: github-auth-git-gh-disconnect-2026-06）
5. commit 前の secret scan は PreToolUse hook が自動実行する（rules/common/security.md）。
   手動で scan を連結する必要はない。連結 commit でも hook は全 git ターゲットを走査する
   （ADR-0038）が、迷ったら commit だけ単発にするのが安全側

## 適用外

- git 以外のコマンド同士の連結は本 skill の対象外（同じ分解照合の原理は働くので、
  全セグメントが許可済み prefix に載っていれば通る）

## 失効条件

本 skill は Claude Code の permission 実装（v2.1.x、as-of 2026-08-13）に依存する。
cd + git 特例の緩和・injection 検出の変更・sandbox 内 push の解禁があれば該当規則を再監査する。
規則がすべて product / allowlist 側に吸収されたら skill ごと退役する。

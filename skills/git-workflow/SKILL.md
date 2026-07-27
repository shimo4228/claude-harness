---
name: git-workflow
description: この環境で git コマンドを Bash 実行するときの permission 摩擦回避作法。git add / commit / push / status 等を実行する前に参照する。git を && やパイプで他コマンドと連結すると Bash(git:*) の自動許可が外れて手動承認プロンプトになるため、1 Bash call = 1 git コマンドで実行する。push は sandbox 無効化が必要。
origin: shimo4228
---

# git-workflow — この環境での git コマンド実行作法

許可設定は `Bash(git:*)`（`~/.claude/settings.json` の permissions.allow）。
**単発の git コマンドは自動許可される。複合コマンドは手動の permission プロンプトを誘発し、
ユーザーを待たせる**（本人から複数回指摘あり）。以下を守る。

## 規則

1. **1 Bash call = 1 git コマンド**。`&&` / `;` / パイプ / `$( )` / `<( )` で git を
   他コマンド（別の git コマンド含む）と連結しない。プレフィックス照合が外れて手動承認になる
2. add → commit → push のような順序依存の列も**別々の Bash 呼び出し**で順に実行する。
   独立な検証系（`git status` と `git log` 等）は並列の別 call にしてよい
3. コミットメッセージは `-m "…"` の単純形。バッククォート・`$`・heredoc を含めない
   （injection 検出で承認要求になる）
4. `git push` は sandbox の network / credential 制約で失敗するため
   `dangerouslyDisableSandbox: true` を付けて実行する
   （認証は `gh auth setup-git` 済み — memory: github-auth-git-gh-disconnect-2026-06）
5. commit 前の secret scan は PreToolUse hook が自動実行する（rules/common/security.md）。
   手動で scan を連結する必要はない

## 適用外

- git 以外のコマンド同士の連結は本 skill の対象外（ただし同じ照合原理は働くので、
  許可済みプレフィックスのコマンドは単発実行が常に安全側）

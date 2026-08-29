---
state: done 2026-08-29
review-when: substrate がサブエージェント内の hooks/skills 発火保証を公式に文書化したら、実測せず注記だけ更新して閉じてよい
---
## Summary

Agent tool 実装経路（`Agent(model: opus, isolation: worktree)`）で hooks と skills が主セッションと同一に発火するかを実測し、task-triage の 2026-08-17 未検証注記を解消する。

## Motivation

「Fable = judge / Opus = build」の dispatch 経路のうち、モデル pin が機械的に効くのは Agent tool だけだが、skill: `task-triage` の dispatch 表には「hooks がサブエージェント内で同一に発火するか、chain の skills が同様に使えるか未検証 (2026-08-17)」の注記が残り、実装 dispatch がこの経路に載らない要因になっている。plan 承認境界の advisory hook 導入（2026-08-28、実行者の決定の既定反転と同一プラン）で dispatch が既定になったため、経路の検証価値が上がった。

## Reference-level explanation

task-triage 既存注記の手順を踏襲: measurement / read-only の軽量タスクを Agent tool 経路で先に流し、① PreToolUse / PostToolUse hook（例: review-model-notice、secret-scan）の発火ログ ② Skill tool の可用性 ③ verify.sh ゲートの挙動、を主セッション実行時と突き合わせる。判定は差分の有無の列挙で足りる（新しい計器は建てない）。

## Unresolved questions

- サブエージェントの transcript にセッションモデル判定用の `"model"` フィールドが主セッションと同形で載るか（transcript 依存 hook の前提）

## Status

done 2026-08-29 — S1 packet（T-002 の skill 棚卸し監査に相乗り）で実測。commit `56c5ae8`、読みメモ `.notes/s1-skill-count-audit-2026-08-29.md` §B。

### 実測結果（3 点 + 追加 1 点）

1. **hooks — parity gap は commit 境界まで含めて観測されなかった。** PostToolUse は毎回発火し （`[claims]` / `[tasks]` advisory、session id も正しく解決）、`log-skill-usage.sh` が子の Skill 起動を、親側 `log-agent-usage.sh` が起動そのものを記録した。PreToolUse の `review-model-notice` は発火した上で正しく沈黙（セッションが Opus = build-tier のため）。commit 境界では `review-chain-notice.sh` が発火し、secret-scan / verify-precommit / bandit / ruff-format / harness-lint の 5 本は無言で通過した（沈黙設計のため「呼ばれて通った」と「呼ばれなかった」は出力から区別できない、という限界は残る）。
2. **Skill tool は使えた。** `skill-stocktake` を実起動し、usage log にも `invoke` として記録された。
3. **`./.claude/verify.sh` は無人で完走し、承認台帳の prompt も出ない**（台帳は commit 境界の PreToolUse が掛けるもので、直接実行には掛からない）。初回 exit 1 で監査 script 自身の欠陥を検出、修正後 exit 0。
4. **Unresolved question は解決（載る）。** subagent の transcript は `"model":"claude-opus-5"` を主セッションと同形で持ち（74 箇所）、しかも親子で session id と transcript を共有する。transcript 依存 hook の前提は崩れない。

### 実コストとして記録すること

**権限プロンプトは 0 件だったが、worktree 隔離ガードがプロンプト無しで Bash を 3 回ハード拒否した。**shell の `for` ループ 2 件と heredoc 1 件で、いずれも git を含まない。拒否理由文は "git operations" と名指すが実際は構文複雑度のヒューリスティックらしく、同型の heredoc が通ったり落ちたりする。回避策は「ループを複数 path の 1 コマンドに畳む」「解析は file に書いて `python3 <file>` で回す」。build セッションは shell ループを常用するので、この経路を実装タスクに使うときの既知コスト。

### 判断役が独立に潰した論点

build は「注入された skill listing が 65 本中 30 本ほど name-only で description が落ちている」を未解決として残したが、**主セッション側の listing も同じパターン**（`agent-stocktake` / `e2e` / `paper-writing` ほかが name-only）であることを triage セッションが自身の context で確認した。subagent 固有の省略ではなく listing 生成側の挙動で、dispatch 経路の不利にはならない（2026-08-29）。

### task-triage への含意

skill `task-triage` の dispatch 表が持つ「hooks がサブエージェント内で同一に発火するか未検証 (2026-08-17)」の注記は解消してよい。ただし上の worktree ガードの件は新しい既知コストなので、注記を消すときに置き換える。

## Next action

完了。残るのは skill `task-triage` の未検証注記の差し替え（上記「task-triage への含意」）で、これは本 RFC ではなく skill 側の編集として別途扱う。

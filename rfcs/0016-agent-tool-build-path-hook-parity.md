---
state: accepted 2026-08-28
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

accepted — 起票のみ、未着手（2026-08-28）。plan 承認境界 advisory hook のプランから分離された検証タスク。

## Next action

measurement batch の軽量タスクが次に発生したとき、Agent tool 経路で流して上記 3 点を記録する。

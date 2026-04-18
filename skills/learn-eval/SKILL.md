---
name: learn-eval
description: "Extract reusable patterns from the session, self-evaluate quality before saving, and determine the right save location (Global vs Project)."
user-invocable: true
origin: shimo4228
---

# /learn-eval - Extract, Evaluate, then Save

`/learn` の全フローに、保存前の品質評価と保存先判断を追加したコマンド。

## What to Extract

Look for:

1. **Error Resolution Patterns** — root cause + fix + reusability
2. **Debugging Techniques** — non-obvious steps, tool combinations
3. **Workarounds** — library quirks, API limitations, version-specific fixes
4. **Project-Specific Patterns** — conventions, architecture decisions, integration patterns

## Process

1. Review the session for extractable patterns
2. Identify the most valuable/reusable insight

3. **Determine save location:**
   - Ask: "Would this pattern be useful in a different project?"
   - **Global** (`~/.claude/skills/learned/`): 2+ プロジェクトで使える汎用パターン（bash 互換性、LLM API の挙動、デバッグ技法など）
   - **Project** (`.claude/skills/learned/` in current project): このプロジェクト固有の知見（特定の設定ファイルの癖、プロジェクト固有のアーキテクチャ判断など）
   - 迷ったら Global（後でプロジェクトに移動する方が逆より楽）

4. Draft the skill file using this format:

```markdown
---
name: pattern-name
description: "130文字以内の説明"
user-invocable: false
origin: auto-extracted
---

# [Descriptive Pattern Name]

**Extracted:** [Date]
**Context:** [Brief description of when this applies]

## Problem
[What problem this solves - be specific]

## Solution
[The pattern/technique/workaround - with code examples]

## When to Use
[Trigger conditions]
```

5. **Quality gate — チェックリスト + ホリスティック判定**

   #### 5a. 必須チェックリスト（実際にファイルを読んで確認）

   以下を **すべて実行** してからドラフトを評価する:

   - [ ] `~/.claude/skills/` 配下をキーワード grep し、内容重複を確認した
   - [ ] MEMORY.md（プロジェクト + グローバル）との重複を確認した
   - [ ] 既存スキルへの追記で済むか検討した（knowledge-placement-decision 参照）
   - [ ] 一回限りの修正ではなく、再利用可能なパターンであることを確認した

   #### 5b. ホリスティック判定

   チェックリスト結果とドラフトを総合し、以下の **1つ** を選ぶ:

   | Verdict | 意味 | 次のアクション |
   |---------|------|---------------|
   | **Save** | 独自・具体的・適切なスコープ | Step 6 へ |
   | **Improve then Save** | 価値はあるが要改善 | 改善点リスト → 修正 → 再判定（1回まで） |
   | **Absorb into [X]** | 既存スキルの一部として追記すべき | 追記先と追加内容を提示 → Step 6 へ |
   | **Drop** | 些末・冗長・抽象的 | 理由を説明して終了 |

   **観点ガイドライン**（採点ではなく判定の参考）:

   - **具体性・行動可能性**: コード例・コマンドがあり、即座に使えるか
   - **スコープ適切性**: 名前・トリガー・内容が一致し、1パターンに集中しているか
   - **独自性**: チェックリスト結果を踏まえ、既存知識で代替できない価値があるか
   - **再利用性**: 将来のセッションで現実的にトリガーされる場面があるか

6. **Verdict 別の確認フロー**

   - **Save**: 保存先パス + チェックリスト結果 + 判定理由1行 + ドラフト全文を提示 → ユーザー確認後に保存
   - **Absorb into [X]**: 追記先パス + 追加内容（diff 形式）+ チェックリスト結果 + 判定理由を提示 → ユーザー確認後に追記
   - **Drop**: チェックリスト結果 + 理由のみ表示（確認不要で終了）

7. Save / Absorb to the determined location

## Output Format for Step 5

```
### Checklist
- [x] skills/ grep: 重複なし（or 重複あり → 詳細）
- [x] MEMORY.md: 重複なし（or 重複あり → 詳細）
- [x] 既存スキル追記検討: 新規が適切（or [X] に追記すべき）
- [x] 再利用性: 確認済み（or 一回限り → Drop）

### Verdict: Save / Improve then Save / Absorb into [X] / Drop

**理由:** （1-2文で判定の根拠を説明）
```

## Notes

- Don't extract trivial fixes (typos, simple syntax errors)
- Don't extract one-time issues (specific API outages, etc.)
- Focus on patterns that will save time in future sessions
- Keep skills focused — one pattern per skill
- Absorb verdict が出た場合は新規ファイルを作らず、既存スキルへの追記を優先する

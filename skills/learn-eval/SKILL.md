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
   - [ ] パターンを**セッションの観測記録**（実際のツール出力・エラー・ユーザーの訂正）に照合した。自分の要約・言い換えではなく「何が実際に起きたか」に基づいているか

   続けて、**ドラフト固有の原子的 yes/no 質問を 3〜5 個生成して回答する**。
   固定チェックリストはハーネス不変の検査（重複・再利用性）であり、ドラフト自身の主張
   （Problem / Solution / When to Use に書いたこと）は検査しないため、ここで補う:

   - **原子性**: 各質問は単一の検証可能な主張だけを問う
   - **反証志向**: ドラフトの記述をそのまま肯定する質問ではなく、反証を探す形にする。
     例:「コード例は記載環境でそのまま実行可能か」「トリガー条件は将来セッションの
     プロンプト文面から観測可能か」「Solution はセッションの観測記録のどの行に対応するか」
   - **集約しない**: 回答は Yes/No + 一行の根拠。数値スコア（肯定率等）に変換しない。
     消費される出力は 5b の verdict のみで、binary 回答はその evidence に徹する

   #### 5b. ホリスティック判定

   チェックリスト結果・binary 質問の回答・ドラフトを総合し、以下の **1つ** を選ぶ。
   **No が付いた質問は verdict の根拠として必ず列挙する**（隠れた No は判定のブレの温床）:

   | Verdict | 意味 | 次のアクション |
   |---------|------|---------------|
   | **Save** | 独自・具体的・適切なスコープ | Step 6 へ |
   | **Improve then Save** | 価値はあるが要改善 | No 質問 = 改善項目 → 修正 → 同一質問で再判定（1回まで） |
   | **Absorb into [X]** | 既存スキルの一部として追記すべき | 追記先と追加内容を提示 → Step 6 へ |
   | **Drop** | 些末・冗長・抽象的 | 理由を説明して終了 |

   **観点ガイドライン**（採点ではなく判定の参考）:

   - **具体性・行動可能性**: コード例・コマンドがあり、即座に使えるか
   - **スコープ適切性**: 名前・トリガー・内容が一致し、1パターンに集中しているか
   - **独自性**: チェックリスト結果を踏まえ、既存知識で代替できない価値があるか
   - **再利用性**: 将来のセッションで現実的にトリガーされる場面があるか
   - **接地性 (grounding)**: 抽出元が観測記録（実際に起きたこと）か、自分の解釈・要約か。自己評価だけのループは drift する（自分の言い換えが事実として再固定される）ため、観測に接地しない抽出は Drop 寄りに倒す。**接地性系の質問が No なら、他が全 Yes でも Drop 寄り**（平均化で支配的な No を薄めない）

   **Improve then Save の改善リスト**: No だった質問がそのまま改善項目になる。各 No について「何を直せば Yes になるか」を 1 行で書き、修正後は**同じ質問セット**で再判定する（1 回まで。質問を再生成しない — 基準が動くと、修正が効いたのか基準が緩んだのか区別できない）。

6. **Verdict 別の確認フロー（1 件ずつ、`[y/n/skip]`）**

   セッションから複数パターンを抽出した場合も、**まとめて承認を求めず 1 件ずつ**確認する
   （config-gc の confirm-each 設計を踏襲。「全部保存する？ [y/n]」の一括承認は禁止）。
   各候補につき証拠（チェックリスト結果 + 判定理由）を先に提示してから `[y/n/skip]` を聞く。
   ユーザーはどの時点でも中断できる。`n` = 破棄、`skip` = 今回は保留（理由を 1 行残す）:

   - **Save**: 保存先パス + チェックリスト結果 + 判定理由1行 + ドラフト全文を提示 → `[y/n/skip]` 確認後に保存
   - **Absorb into [X]**: 追記先パス + 追加内容（diff 形式）+ チェックリスト結果 + 判定理由を提示 → `[y/n/skip]` 確認後に追記
   - **Drop**: チェックリスト結果 + 理由のみ表示（確認不要で終了）

7. Save / Absorb to the determined location

8. **昇格確認（Save 保存後のみ）**

   `learned/` 配下はフラットな `.md` ファイル置き場であり、`skills/<name>/SKILL.md` 形式の discovery に乗らない。つまり description ベースの自動トリガーは効かず、参照ノートとして grep される受動的な存在に留まる。Save 完了後、ユーザーに 1 回だけ確認する:

   - **learned のまま置く**（default）— 参照資料・grep 対象として十分な場合。確認に応答がなければこちら
   - **アクティブ skill に昇格** — 今後のセッションで description トリガーによる自動適用を効かせたい場合。Claude Code では Anthropic 公式の **skill-creator** skill を learned ドラフトに対して実行し、`~/.claude/skills/<name>/SKILL.md` として構造化・description 最適化・eval まで行うのがベストプラクティス（learn-eval = 抽出と品質ゲート / skill-creator = 構造化と eval、で役割が分かれる）。昇格完了後は `learned/` 側のファイルを削除し、二重管理を残さない

## Output Format for Step 5

```
### Checklist
- [x] skills/ grep: 重複なし（or 重複あり → 詳細）
- [x] MEMORY.md: 重複なし（or 重複あり → 詳細）
- [x] 既存スキル追記検討: 新規が適切（or [X] に追記すべき）
- [x] 再利用性: 確認済み（or 一回限り → Drop）

### Draft-specific questions
- [Yes] Q1: ... — 根拠1行
- [No]  Q2: ... — 根拠1行 →（Improve 時: 修正方針1行）

### Verdict: Save / Improve then Save / Absorb into [X] / Drop

**理由:** （1-2文で判定の根拠を説明。No 質問があれば必ず言及）
```

## Notes

- Don't extract trivial fixes (typos, simple syntax errors)
- Don't extract one-time issues (specific API outages, etc.)
- Focus on patterns that will save time in future sessions
- Keep skills focused — one pattern per skill
- Absorb verdict が出た場合は新規ファイルを作らず、既存スキルへの追記を優先する

## References

Step 5 の 2 層設計（binary 質問分解 → ホリスティック判定）の設計根拠:

- BinEval — "Ask, Don't Judge: Binary Questions for Interpretable LLM Evaluation and Self-Improvement" ([arXiv:2606.27226](https://arxiv.org/abs/2606.27226))。評価基準を原子的 yes/no 質問に分解し、失敗質問を改善フィードバックに直結するフレームワーク。ドラフト固有質問の動的生成と「No 質問 = 改善項目」の導線はここから移植
- 同系統のチェックリスト型評価研究ライン: CheckEval (arXiv:2403.18771)、TICK (arXiv:2410.03608)、FActScore (arXiv:2305.14251)、UniEval (arXiv:2210.07197)
- 数値スコア（肯定率）を**採用しない**判断も BinEval 自身の limitations に基づく: 主観的・全体論的な品質次元では過剰分解が人間評価との相関を損ない、肯定質問の割合は品質に線形対応しない。N=1 のドラフト評価では消費される出力は verdict のみで、binary 回答はその evidence に徹する

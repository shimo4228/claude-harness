# Plan — Research Plan Mode（plan の前に調査を必ず走らせる）

承認: 著者 2026-10-04（設計案 v2 と「内部調査」分岐への合意）。種別 feat（harness 自体の変更）。
実行者の決定: このセッションが実装する — skill / agent / rule の散文編集が主で、著者の明示指示がある。

## 問題

plan mode に入っても、Claude は外部調査の前に設計を書き始める。2026-10-02〜03 の claude-prose-mod
「RFC1をプランして」2 セッションで、著者が外部調査を求めるまで local の型定義から plan を組んだ
（usage report 2026-10-03 の friction 記録）。search-first の発火数は ADR-0066 の改修後に回復した
（invoke: 9/1〜14 は 0 件、9/21〜10/2 は 19 件 — `metrics/skill-usage.jsonl`）が、plan の入口では
効いていない。ExitPlanMode で止めても plan ができた後で遅い。

## 外部調査（as-of 2026-10-04、4 方向を並列）

- plan mode は auto mode 下でコマンドを classifier に回し、plan ファイル以外への書き込みだけを止める
  （`useAutoModeDuringPlan` 既定 on — code.claude.com/docs/en/permission-modes）
- 親が plan mode のとき、`permissionMode` を持つ custom subagent はその mode で動く
  （code.claude.com/docs/en/sub-agents、要約読み）
- HumanLayer / superpowers / feature-dev / spec-kit は純正 plan mode を使わず、research-before-plan は
  prompt の規約と「前段成果物の存在」止まり。hook で強制する実装は見つからない。spec-kit は
  research.md の完了を設計の前提にする
- OpenCode / Gemini CLI / Roo Code の plan mode はモード別の書き込み許可（plans だけ allow）
- ExitPlanMode への PreToolUse deny は無視される（anthropics/claude-code#50660、not planned）
- Anthropic の multi-agent research: 比較型は subagent 2〜4 × 各 10〜15 calls、複雑型は 10+。
  token 使用量が BrowseComp の分散の 80% を説明。STORM: 視点分割で網羅 +10pt
- Cursor 2.2 / Kiro / Roo は plan に Mermaid を入れる。ultraplan は廃止

## 設計

1. `agents/researcher.md` — tools を Read / Grep / Glob / WebSearch / WebFetch / Write に限り、
   `permissionMode: acceptEdits`。plan mode のまま notes と report を書ける
2. skill search-first の Full を並列多視点に置換 — brief → 3〜5 角度（1 本は反証役）を researcher で
   並列 → lead が notes を読み漏れと矛盾を洗う → 追加は 1 波 → 決定に効く主張を原典で検証 → report
3. `hooks/research-gate.sh`
   - plan mode の入口（UserPromptSubmit / EnterPlanMode 直後）で調査手順を差し込む
   - researcher の書き込み先を `~/.claude/research-notes/` と `*/docs/plans/research/*.md` に限る
   - researcher が report（先頭行 `kind: external` か `kind: internal`）を書いたら session に印を付ける
   - plan mode 中、印が無ければ `docs/plans/*.md`（research/ を除く）への Write / Edit を止める
   - 著者のプロンプトに「調査不要」/ "skip research" があれば開ける
4. 調査は 2 種: 外部調査（search-first）と内部調査（再現・原因 `file:line`・確認）。種別は brief の
   1 行目に書き、著者が止められる
5. plan は report にリンクし、構造・流れは Mermaid で示す

## 確かめること（Phase 0、使い捨て設定で headless）

- plan mode 中の plan ファイルへの Write を PreToolUse の block で止められるか
- plan mode の親の下で researcher（acceptEdits）が書けるか、hook の `session_id` が親と同じか
- plan mode 中の WebSearch / WebFetch が確認なしで走るか

どれかが駄目なら、その部品だけ Mod の `tool.check` に置き換える。

## Chain

Plan（本書）→ TDD（gate の境界条件を bats で先に）→ Code Review（medium）+ Security Review
（権限境界と外部コンテンツの書き込み経路を動かす）→ Doc Sync（hooks/README、ADR、search-first、
rules/planning.md）→ Verify。

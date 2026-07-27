<!-- origin: shimo4228 -->
# Rules

毎セッション自動ロードされる常駐層。**常駐は希少資源**なので、ここに置くのは
「Claude が既定で持っていない、この環境固有の gotcha と意見」だけ。手順の詳細・
判断表・言語固有の慣行は skill 側に置き、ポインタで参照する（progressive disclosure）。

現在 `common/` 13 ファイル（語数は volatile のため記載しない — `wc -w` で都度実測する。
2026-07-25 の rightsize → [ADR-0018](../docs/adr/0018-rules-rightsize-for-claude5.md)、
同日の `human-gate.md` 新設 → [ADR-0019](../docs/adr/0019-human-gate-layer.md)、
2026-07-26 の system-prompt 整合調整で作成ゲート行を削除、同日 `git-workflow.md` を substrate 吸収で退役）。

各ファイル先頭の `<!-- rationale: -->` / `<!-- review-when: -->` コメントは存在根拠と
失効条件のメタデータ（[ADR-0021](../docs/adr/0021-rules-metadata-and-premise-lint-gates.md)）。
HTML コメントはセッション注入時に strip されるため常駐コストゼロ — `wc -w` の disk 値は
注入実測より大きく出る。存在は harness_lint が検査し、消費者は rules-stocktake。

## Structure

```
rules/
└── common/          # 言語非依存（python/ 層は 2026-07-25 に廃止 → skills/python-patterns へ吸収）
    ├── agents.md           # Author-Reviewer 分離、cross-agent 共有 / 委譲のゲート条件
    ├── akc-cycle.md        # Phase → skill 対応、signal-first、Scaffold Dissolution
    ├── coding-style.md     # Reversibility Gate、Iteration Bounds、Change Target
    ├── contemplative-axioms.md  # Contemplative Constitutional AI 条項（verbatim）
    ├── debugging.md        # 根本原因優先フロー、Rate limit = policy signal
    ├── hooks.md            # hooks vs skills の決定論性、外部スクリプト分離
    ├── human-gate.md       # ゲートの第 2 軸 — artifact は機械 / intent は人間、提示物の対象分岐
    ├── patterns.md         # Code vs LLM seam、documented-invariant → ゲート化
    ├── planning.md         # Phase 0、複雑性チャレンジ、2 介入点モデル、Verify ゲート
    ├── security.md         # シークレット管理、LLM 信頼境界
    ├── skills.md           # Origin Tracking、Knowledge Placement
    ├── task-tracking.md    # 単一タスク台帳（1 repo 1 ファイル）
    └── testing.md          # カバレッジ 80%、MagicMock の罠、本番テスト禁止
```

## Rules vs Skills

- **Rules** — 常駐。確実に適用されるが、全セッションのコンテキストを消費する
- **Skills** — description に基づいて確率的にトリガー（自発発火は保証されない）。
  深さを持てる。確実に効かせたいものは `user-invocable: true` で明示呼び出しにする

**判定**: そのファイルは毎セッション読まれる価値があるか？ 特定の作業を始めた時だけ
必要なら skill。Claude が既に知っている一般論なら削除。

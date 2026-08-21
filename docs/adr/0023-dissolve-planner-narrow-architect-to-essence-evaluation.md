# ADR-0023: planner agent の Dissolve と architect の本質評価専任化 — fresh/rich context 軸によるサブエージェント適性判定

## Status

accepted

## Date

2026-07-27

## Context

2026-07-27 の agent-stocktake 初回 full 実行（generation-audit の Phase 4 委譲）は planner
agent を Improve と判定した。Dissolve を反証した根拠は「native Plan agent は Agent tool を
持たず scout へ委譲できないが、planner は Agent(scout) を持つ」という能力差だった。

直後にユーザーが「planning はサブエージェントでなくオーケストレーター（メインループ）の
仕事ではないか」と指摘し、再評価の結果この反証は崩れた。

- **(1) 能力差の前提が無効**。メインループ自身が Agent tool をフルに持つオーケストレーター
  であり、scout 委譲能力は planner を経由せず最初から手元にある。能力の有無は吸収判定の
  必要条件であって十分条件ではなく、「その能力を使う場所はどこか」を見る必要があった。
- **(2) Phase 0 エントリポイント規定への違反**。`rules/common/planning.md` は Phase 0 の
  エントリポイントを `/search-first` skill（メインループから呼ぶ）に固定している。planner
  サブエージェントが内部で Phase 0 を回すと、Step 0（要件の text 出力）によるユーザーの
  course-correct ウィンドウが閉じる。
- **(3) 2 介入点モデルへの抵触**。介入点 1（Plan 確認）は、plan がユーザーとの対話の場＝
  メインループで練られることを要件とする。サブエージェントが返す plan は lossy な
  round-trip を挟み、この要件を満たさない。
- **(4) substrate 吸収の完成**。plan mode（EnterPlanMode / ExitPlanMode）と
  implementation-chain skill（chain の front-load をメインループに指示）が planner の職務を
  覆っている。planner は Claude Code に plan mode が存在しなかった時期の ECC パターンである。
- **(5) 一般原則としての context 資産の向き**。review は fresh context が資産（著者バイアス
  除去、`agents.md` の Author-Reviewer 分離）だが、planning はユーザー意図・会話中の制約・
  過去の決定という rich context が資産であり、委譲は品質を下げる方向にしか働かない。

architect も同じ再評価にかけた結果、役割が二分された。generic なシステム設計提案は
オーケストレーターの仕事だが、planning.md の機能要求チャレンジが委託する「本質評価
（build すべきか）」は、機能を推進してきたメインループのサンクコストと推進慣性から切り
離された fresh context こそが要件であり、Author-Reviewer 分離と同型の設計として分離が
機能する。

## Decision

1. **planner agent を Dissolve する**。`agents/planner.md` を削除する（git 履歴で復元
   可能）。参照 3 箇所を書き換える。
   - implementation-chain の Chain Matrix「Plan (planner)」→「Plan（メインループ /
     plan mode。sub-agent へ委譲しない — plan は rich context と介入点 1 の対話が要件）」

     > **注記（2026-08-22）**: 「sub-agent へ委譲しない」は plan 本文と採否について維持。
     > 探索（Explore の並列）と設計代替案の生成（Plan agent の観点違い並列）は委譲してよい
     > と Matrix の Plan 行を改め、Plan 段の cross-model 前提反証（Premise Challenge 行、
     > skill: `codex-review` plan mode）を追加した。介入点 1 がメインループにある要件は不変。
   - council の When NOT to Use 2 行（implementation steps → main-loop plan mode、
     system architecture → main-loop plan mode）
   - e2e の「Use the planner agent to identify critical journeys」→ メインループの
     plan step で行う
2. **architect agent を「独立本質評価人」に純化する**。description を書き換え（fresh-context
   judge / build-or-not 専用 / NOT for designing implementations と明記）、body から
   generic な設計チェックリスト群（Architecture Review Process / Architectural
   Principles / Common Patterns / System Design Checklist / 数値 Red Flags）を削除し、
   Essence Evaluation・Trade-Off Analysis・Anti-Pattern Lens・adr-writer へのポインタ・
   verdict 出力規約（Build / Don't build / Build smaller、numeric score 禁止）に絞る。
   origin は ECC-customized。
3. **サブエージェント適性の判定軸として「fresh context が資産になるか負債になるか」を
   採用する**。検証・審査（review、本質評価）は fresh が資産、生成・計画（plan、実装）は
   rich が資産。

## Alternatives Considered

### planner を Improve（本文縮小）に留める

Agent(scout) の能力差はメインループが Agent tool を持つ時点で無効であり、縮小しても
「rich context を失う場所で plan を作る」構造問題と Phase 0 メインループ固定への違反
リスクは残る。**却下**。

### architect も併せて Dissolve する

本質評価は提案者（メインループ）自身に審査させない構造が価値であり、planning.md が
明示的に外部委託している。fresh context が要件の役割はサブエージェントが正しい置き場所。
**却下**。

### architect を council に統合する

council は多声の意思決定 skill であり、build-or-not は planning.md が直接指す単独判断の
委譲。council 自身が architect をパネリストとして消費する側でもある。**却下**。

## Consequences

### Positive

- plan が rich context と介入点 1 の対話がある場所で作られるようになる。
- agent listing の常駐 description が 1 件（25 語）減る。
- architect の description が実役割と一致し、毎セッションの委譲誤誘導が解消する。
- 「fresh vs rich context」軸が今後の agent 設計・stocktake の吸収判定に使える明示的
  基準になる。

### Negative

- planner の ECC 上流との diff 比較ができなくなる（ファイル削除。git 履歴で復元可能）。
- architect は ECC-customized 化し上流から乖離する。

### Neutral / Follow-ups

- agent-stocktake の results.json を更新する（planner → Dissolve、architect の reason
  更新）。
- generation-audit の証拠台帳の処分状況に追記する。
- agent-stocktake の Stage 2 反証質問に「能力があるとして、それを使う場所はメインループ
  ではないか」を加える改善余地は将来の skill 改訂候補とする。

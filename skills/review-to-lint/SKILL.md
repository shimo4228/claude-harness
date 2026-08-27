---
name: review-to-lint
description: "既存 reviewer（agent / review skill）のチェックリストから機械判定可能な項目を決定論 script に抽出し、reviewer を意味的チェック専任に薄化する手順。著者が「このレビュアーを lint 化して」「レビューを lint に吸収して」「機械チェックを script に降ろして」と言ったとき、または reviewer の指摘に機械的項目の反復が目立つときに /review-to-lint で使う。NOT for — 新規 reviewer の作成（→ skill-creator）、意味的基準そのものの変更（各 reviewer の正本）、judge の設計（→ llm-as-judge）、既に evidence script を持つ reviewer の再抽出（readme-writer / adr-writer は実施済み）。"
user-invocable: true
origin: shimo4228
---

# Review → Lint 吸収

reviewer のチェックリストには、LLM が数えるより script が数える方が正確で安い項目が混ざる。
この skill はその境界を引き、機械側を script へ降ろし、reviewer の注意を意味的チェックに
集中させる。先行実例: `readme_evidence.py`（readme-writer）、`adr_lint.py`（adr-writer、
ADR-0051）。分業原理は「存在 = code、内容 = LLM」（ADR-0021 が導入、ADR-0044 が ADR へ適用）と
feedback: deterministic_semantic_layering（script 計測 + LLM 解釈）。

## 1. 棚卸しと 3 分類（この skill の核）

対象 reviewer のチェックリストを 1 項目ずつ分類する。判断基準:

| 分類 | 判定の入力 | 行き先 |
|---|---|---|
| **deterministic** | 構造・書式・実在・一致（節の有無、enum、日付書式、リンク解決、index drift、命名規則、相互参照の整合） | script |
| **semantic** | 意図・忠実性・両面性・妥当性（後付け正当化、藁人形、片面 Consequences、主張と証拠の対応） | reviewer に残す |
| **hybrid** | script が数え、LLM が解釈する（カウント条件の固定対象、数値の分母、用語の出現分布） | script が evidence を出し、reviewer が解釈 |

迷う項目は semantic に倒す — 誤って機械化した項目は偽陰性を「検査済み」の顔で通す。

## 2. search-first 照合

書く前に外部 lint ツールと harness 内の既存 evidence script（`skills/*/scripts/`）を探す。
既存が対象 corpus を**移行なしで**検査できるなら書かない。移行が要るなら移行コストと
自作コストを比べ、却下理由を ADR に残す（先例: adrkit の照合、ADR-0051）。

## 3. script 設計

- 置き場: 当該ドメインの writer skill 配下 `skills/<owner>/scripts/`（cross-repo で動く
  単一正本）。uv sub-project（pyproject + tests、verify.sh full が自動発見）
- 既定は **evidence モード**: JSON を出力・判定しない・exit 0。「evidence, not a verdict」—
  判定は fresh-context の judge / reviewer が持つ。blocking が要る場合だけ `--gate` を足す
- **免除境界を先に実測する**: 既存 corpus 全件に当てて違反数を数えてから、prefix 判定・
  番号/日付境界・repo ローカル規約の自動適応（正本 doc から期待値を読む）を決める。
  ゲートを初日に赤くする lint は免除境界の設計ミス
- 検出パターンには実測根拠（どの repo の何件か）をコメントで残す

## 4. reviewer 薄化

- 機械項目をチェックリストから削除し、冒頭に Step 0 を配線: 「script を実行 → JSON の
  逸脱を findings に転記 → 目視で数え直さない → 注意は意味的チェックへ」
- 対象 repo のローカル規約（テンプレの正本 doc）を読む指示を残す — corpus ごとに規約が
  違う前提で reviewer を書く
- 頻出指摘の**事例**は `references/` の日付・commit 参照つきカタログへ（writer skill の
  書き時予防に配線）。**基準**は reviewer が正本のまま — 事例と基準を複製しない

## 5. 配線しないもの

- commit hook / verify.sh への常時配線は既定でしない — 対象ドキュメントを触らない commit
  にも毎回課税する（著者判断 2026-08-26、ADR-0051）。実行座標は writer skill のステップと
  reviewer の Step 0。形骸化が観測されたら commit 面への配線を再訪
- 集計・viewer・grader agent は持たない（skill-creator「持たないもの」と同じ理由）

## 6. 記録

ADR に残す: code/LLM の境界線（どの項目をどちらへ）、既存検査との重複箇所と drift しない
根拠、免除境界の実測値、search-first の却下理由。

## 適用候補

候補台帳は [RFC-0005](../../rfcs/0005-review-to-lint-rollout-ledger.md) が正本
（12 候補・需要駆動の発火条件・やらない判定。2026-08-26 sweep）。実施は 1 件ずつ
別セッション、優先順は機械化余地でなく需要の発火条件で決める。

# per-model effort 設定（Fable = judge / Opus = build 構成）

## Context

モデルごとの規定 effort が設定可能になった（既に `settings.json` の `modelSettings` に両モデル `high` で存在）。ユーザーの構成は Fable = 判断層（triage/plan）、Opus = 実装層（build session、ADR-0043）。「Opus は medium がコーディングベンチで良い」という伝聞の裏取りと、各層の推奨値を決める。

## 調査結果（as of 2026-08-29）

- 引用記事（claude.com blog 2026-07-07）に medium 優位の記述は無い
- 公式 effort docs: Fable 5 は「high で開始、capability-sensitive なら xhigh」/ Opus 5 は「high で開始、eval で品質が保てるなら medium/low を積極利用」
- 「Opus 5 medium が coding bench で near-peak（compute ~半分）」は二次資料（SitePoint/FrontierCode、Vellum 等）。単発ベンチ構成であり、長時間 agentic session への転写は未検証
- 失効条件: 次のモデルリリース or effort docs 更新で再照合

## 変更内容

`~/.claude/settings.json` の `modelSettings` を編集:

- `claude-fable-5.effortLevel`: `high` 据え置き（判断層は intelligence-sensitive。公式推奨どおり）
- `claude-opus-5.effortLevel`: `medium` へ変更（ユーザー決定 2026-08-29。コスト約半減の試行。判断層 Fable が独立検収するため品質低下は bounce として観測でき、悪化したら high へ戻す）

## Verification

- `python3 -c "import json; print(json.load(open('$HOME/.claude/settings.json'))['modelSettings'])"` で反映確認
- medium にした場合: 次の Opus build session の成果物を Fable triage 検収で観察し、bounce 率が上がるなら high へ戻す

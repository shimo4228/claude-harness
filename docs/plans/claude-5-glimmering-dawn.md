# 世代交代監査スキルの新設 — generation-audit（オーケストレータ）+ agent-stocktake

## Context

Zenn 記事「Claude 5 世代でルールの書き方は公式に変わった」の棚卸し手順（runtime 層採取 →
競合/冗長/ドリフト 3 分類 → 意図・根拠・鮮度・失効条件の 4 観点判定）を、AKC の
Scaffold Dissolution の具体手順としてスキル化する。grill-me インタビューの結論:

- **既存の rules-stocktake への追記では足りない** — 照合手順は rules / CLAUDE.md /
  skills / agents の 4 資産クラスに跨る（記事の実例「確信度 80%」は agent 定義）。
  横断手順を片方に追記するともう片方に届かないため、Knowledge Placement の
  新規スキル条件を満たす
- **形はオーケストレータ型** — 新スキルは採取と分類と判定枠だけを持ち、verdict 確定と
  処分実行は既存 stocktake に証拠を渡して委譲する。独立監査型は verdict 表の正本を
  割る（ADR-0018 が潰した「正本の自称し合い」の再演）ため却下
- **agents の受け手として agent-stocktake を新設** — 専用 stocktake が存在しない穴を
  埋める。agent は description 層（毎セッション常駐 = residency コスト）と body 層
  （起動時ロード = 確率発火コスト）のハイブリッド cost model を持ち、既存 2 スキルの
  どちらにも収まらない。skill-stocktake / rules-stocktake に続く第 3 の兄弟として設計
- **AKC への還元はローカル実証後の別タスク**（Prototype Before Scale）。AKC 側には
  構想メモ 1 行のみ残す

## 決定事項（grill-me の合意）

| 論点 | 決定 |
|------|------|
| 着地先 | 新規スキル（rules-stocktake 拡張ではない） |
| 形 | A. オーケストレータ型 — 採取 + 3 分類 + 4 観点判定枠のみ保持、verdict は委譲 |
| 委譲マップ | rules → rules-stocktake / skills → skill-stocktake / agents → **agent-stocktake（新設）** / CLAUDE.md → オーケストレータ inline（1 ファイルのみ） |
| 「反転」処分 | 新 verdict にしない。既存 Improve の一形態として扱い、「方向転換した指示は削除でなく逆向きに書き直す」を証拠注記としてオーケストレータが渡す |
| AKC 還元 | 今回はしない。次の世代交代で実証してから harness 中立化して還元 |
| 発火 | `user-invocable: true`。世代交代は稀・明示的イベントなので自発トリガーに依存しない（40% 上限問題の回避） |

## 作成物

### 1. `skills/generation-audit/SKILL.md`（新規、origin: shimo4228）

記事の手順を skill 化。構成:

- **Phase 1 — runtime 層採取**: テーマ別に system prompt / tool description を逐語引用で
  採取する手順（記事 Step 1）。自己申告スクリーニングの限界と別セッション再現確認の
  注意書きを含める
- **Phase 2 — 3 分類**: 資産クラスごとに競合 / 冗長 / ドリフトへ分類（記事 Step 2）。
  競合の成立条件（同一 context に同時ロード — rules は常時、skills/agents は発火時）を明記
- **Phase 3 — 4 観点判定枠**: 意図 / 根拠 / 鮮度 / 失効条件（記事 Step 3）。
  「競合 = 悪」の機械適用禁止、「モデル自己検証 vs 機械検証」の区別（記事の落とし穴）
- **Phase 4 — 委譲**: 分類結果 + 判定枠の証拠を各 stocktake に渡す。rules-stocktake の
  Stage 2 が持つ「外部証拠を読む口」（skill-comply results と同型）を差し込み点にする
- Related: rules-stocktake / skill-stocktake / agent-stocktake / adr-writer（Dissolve の
  why 記録）/ akc-cycle.md の Scaffold Dissolution 3 トリガー

### 2. `skills/agent-stocktake/SKILL.md`（新規、origin: shimo4228）

rules-stocktake（`skills/rules-stocktake/SKILL.md`）を雛形に、cost model を
ハイブリッドに置換した兄弟スキル:

- 監査対象: `~/.claude/agents/*.md`
- cost model: description 層 = residency（Available agent types 一覧に毎セッション常駐）、
  body 層 = invocation（起動時ロード）。Stage 1 の質問セットを 2 層に合わせて再構成
- verdict 表・confirm-each（1 件ずつ承認）・ledger（results.json）・Reason quality は
  rules-stocktake の設計を踏襲
- 抑制指示の検出（「確信度 N% 以上のみ報告」型 — Opus 5 プロンプトガイドが戒める形）を
  Stage 1 質問に含める（記事のドリフト実例の一般化）

### 3. 既存ファイルへの小変更

- `rules/common/akc-cycle.md`: Curate 行の skill 列に `generation-audit` を追記
  （世代交代トリガー時の呼び先。1 行）
- `skills/rules-stocktake/SKILL.md` / `skills/skill-stocktake/SKILL.md`: Related 節に
  generation-audit を 1 行追記（証拠の受け口であることを明記）
- `rules/README.md`: 変更なし（rules は増えない）

### 4. ADR（提案 — 実行時にユーザー確認）

「世代交代監査の 3 兄弟構成（オーケストレータ + 資産クラス別 stocktake）」は
ADR テスト 3 条件（可逆性が低い構造決定 / 文脈なしでは驚く / 実在した代替案との
トレードオフ）を満たすため、`/adr-writer` での記録を提案する。

## 実行順

1. agent-stocktake 作成（skill-creator の規約に沿う。委譲先が先に無いとオーケストレータが空を指す）
2. generation-audit 作成
3. 既存ファイルへのポインタ追記（akc-cycle.md ほか）
4. ADR 記録（ユーザー承認後）
5. human gate: 両 SKILL.md は behavior-shaping artifact なので**本文提示**で意図確認
   （human-gate.md）。承認後 commit
6. harness-sync の follow-up をユーザーに案内（origin: shimo4228 の新スキル 2 本）

## 検証

- 両 SKILL.md の YAML frontmatter 検証（skill-creator の既知 gotcha:
  description 中の `: ` が YAML を破壊）
- `grep -l "^origin: shimo4228"` で origin 付与確認
- harness_lint（`scripts/hooks/harness_lint.py`）が通ること
- 機能検証は次の世代交代まで実施不能（稀イベント駆動のため）。dry-run として
  現世代の採取 Phase 1 だけを 1 テーマ実行し、手順が回ることを確認する

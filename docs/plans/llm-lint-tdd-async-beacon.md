# Lint の LLM-first 最適化（harness）

## Context

mondo → golden 層導入の続き。「人間可読を考えず LLM 最優先」の観点で lint を棚卸しした結果:
現構成に人間美学専用の規則は無く、**削るものは無い**。残る最適化は (a) 議論で価値が確認された
「境界の明示型強制」の導入、(b) pin の鮮度回復、(c) 正当化の語彙と再調査トリガーの記録。

外部調査（scout、as-of 2026-08-31）の要点:
- ruff 最新 0.16.5（pin 0.16.1 から 4 patch。明示 select 方式なので 0.16.0 の default 拡大の影響なし）
- ANN の設計制約: **引数注釈 (ANN001-003) は public/private を区別できない**（ruff#16863 未解決）。
  public 限定にできるのは戻り値側のみ（ANN201 select / ANN202,204-206 除外が setuptools 等の定石）
- ty は 0.0.75、まだ 0.0.x で strict mode 無し → pin 継続が妥当
- 「コードの LLM 可読性を lint する」専用ツールは**市場に存在しない**（agentlint 系は CLAUDE.md 等の
  設定ファイル対象で別物）→ 自前 compose 継続
- ファイル LOC の外部標準も無し → 800 維持（自分の分布から引く現方法論が既に LLM-first）
- 「型強化が agent 成功率を上げる」は一次ソース未確認 → 断定表現は書かない（as-of 注記のみ）

実測（2026-08-31、ruff 0.16.1）: ANN を production 側に有効化した場合の違反は
root (hooks/scripts/tests) 5 件 + skills/*/scripts 15 件 ≈ **drain 18 箇所**（ANN001 系 16、ANN401 が 2）。
skills/*/tests は 277 件 → テストは除外する（テスト関数は消費される境界ではない）。

## 変更 1: 境界の型強制（ANN 系の導入）

**対象 10 ファイル**: `ruff.toml`（root）+ `skills/{learn-eval, skill-stocktake, agent-stocktake,
context-sync, llms-txt-writer, skill-health, readme-writer, adr-writer, skill-comply}/pyproject.toml`
（select 行は全ファイル同一なので同じパターンで編集）:

- select に追加: `ANN001, ANN002, ANN003`（引数 — 全関数に発火する制約は受容）、
  `ANN201`（public 戻り値のみ）、`ANN401`（Any 禁止）
- 追加しない: `ANN202, ANN204-206`（private / special の戻り値 — 境界ではない）
- per-file-ignores: `tests/**` → ANN 全除外（root ruff.toml と各 pyproject の両方に記載）
- コメントに導入理由 1 行: 境界の明示型は LLM の再生成・編集の凍結端（as-of 2026-08-31、
  一次実証は未確認の旨を verify.md 側に書く）

**drain（同じ diff で）**: 検出された約 18 箇所に注釈を付ける / ANN401 の 2 箇所は Any を実型に
置き換える。既存挙動の変更はゼロ（注釈のみ）。golden 層が形の非変更を機械保証する。

## 変更 2: pin の鮮度回復（verify.sh — 要再承認）

- `.claude/verify.sh` の `RUFF=("$UVX" 'ruff==0.16.1')` → `0.16.5`、ty の pin も現行 0.0.75 へ
- **verify.sh を編集すると hash が失効し、次 commit が block される** — 適用後にユーザーが
  `python3 ~/.claude/scripts/hooks/verify_allow.py approve ~/.claude` で再承認する（1 コマンド、人間の操作）
- bump 後に full verify を回し、新版で新たに鳴る指摘が無いか確認（あれば上げずに刈る）

## 変更 3: 記録（.claude/verify.md）

日付つき節を追加:
- lint 棚卸しの結論: 削除ゼロ（人間美学系は元々 select していない）。format / I / C901 / LOC 800 の
  正当化を LLM-first の語彙（正準形 = diff 安定・編集信頼性予算・context 予算）で再記載
- ANN 導入の select 構成と「引数は public 限定不可」の設計制約（ruff#16863、as-of）
- 再調査トリガー: PLR0913/0914/0915（複雑度予算の補強候補）が preview を出たら再評価 /
  ty の strict mode 実装 or 1.0 で再評価 / 「LLM 可読性 lint」ツール市場は 2026-08 時点で不在、
  出現したら search-first で再調査

## 変更しないもの（判断済み）

- 削除する rule: 無し
- MAX_FILE_LOC 800: 維持（外部標準不在。方法論は自分の分布 + 実測）
- shellcheck: 0.11.0 が最新のまま、SC2329 はグローバル除外されていない（`-e SC1091` のみ）— 対応不要
- pyright / pyrefly 併用: 見送り（二次ソースのみで併用根拠が弱い。ty の再調査トリガーに含める）

## Verification

1. `~/.local/bin/uvx ruff==0.16.5 check hooks scripts tests skills/*/scripts` — 新 select で clean
2. `bash .claude/verify.sh`（full）— exit 0。golden 8 本 + pytest 群が green のまま（注釈のみの変更で
   出力が変わっていないことの機械証明）
3. 変異注入: 注釈の無い関数を 1 つ一時追加 → ruff が ANN001 で赤 → 削除
4. staged mode の注意: **ruff.toml / pyproject.toml の変更は drain と同じ commit に stage する**
   （staged mode は index から config を展開するため — verify.md 記載の既知の罠）
5. commit 後、ユーザーが verify_allow.py approve を実行（変更 2 の再承認）

## 変更ファイル

- 編集: `ruff.toml`、`skills/*/pyproject.toml` × 9（select + per-file-ignores）、
  `.claude/verify.sh`（pin 2 行のみ）、`.claude/verify.md`（日付つき節）
- drain: `hooks/` `scripts/` `skills/*/scripts/` の約 18 箇所（注釈追加、挙動変更なし)

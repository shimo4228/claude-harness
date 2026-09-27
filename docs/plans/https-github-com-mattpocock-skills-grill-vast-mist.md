# grill-me の docs 連携強化（grilling / grill-with-docs 取り込み判断）

## Context

ユーザーの問い: 「grill-me だけ入れて grilling / grill-with-docs が無いのは片手落ちでは？特に自分の repo は CODEMAPS・ADR・graph.jsonld までありドキュメントが上流の想定以上に充実しているので、宝の持ち腐れになっていないか？」

## 調査結果（事実）

### 上流 mattpocock/skills の構造

| skill | 実体 | 役割 |
|---|---|---|
| `grilling` | ~10 行 | インタビューループの核（model-invocable）。1問ずつ / 推奨回答付き / fact は codebase 参照・decision はユーザーに |
| `grill-me` | 薄いラッパー | grilling の user 起動版（非コード文脈向け） |
| `grill-with-docs` | **本文 1 行** — 「Run a `/grilling` session, using the `/domain-modeling` skill.」 | docs 生成付き grill |
| `domain-modeling` | 実質の本体 | glossary (CONTEXT.md) との衝突検出・用語の先鋭化・具体シナリオ・コード照合・**inline での CONTEXT.md 更新**・ADR 3 条件テスト |

### ローカルの現状

- `~/.claude/skills/grill-me/SKILL.md`（origin: `mattpocock/skills`）は本文が「Adapted from Matt Pocock's grill-me / **grilling** skills」と明記しており、**grilling の中身（5 Rules）は既に統合済み**。
- `grilling` を別途入れる上流側の理由は「model-invocable な核の分離」だが、ローカルの実測（feedback: 自発トリガー実質上限 ≒ 40%、user-invocable へ pivot 済み）ではこの分離の価値は低い。
- `grill-with-docs` 本体は 1 行で、価値の全部が `domain-modeling` にある。だが domain-modeling は **docs が無い repo に CONTEXT.md を lazily 生成する**前提の設計。ユーザーの repo は glossary / docs/adr（自前 6 セクションテンプレート + adr-writer skill/agent）/ CODEMAPS / graph.jsonld が既にあり、そのまま輸入すると並行構造（CONTEXT.md 規約）が衝突する。

### 結論（評価）

1. **grilling: 欠落していない**。既に grill-me に吸収済み。導入不要。
2. **grill-with-docs: 「片手落ち」の指摘は半分正しい**。欠けているのはラッパーではなく domain-modeling の**インタビュー中の振る舞い規律**:
   - 既存 glossary / ADR / CODEMAPS を fact 源として参照する（現状の Rule 3 は「codebase を探索」とだけ書いてあり docs に言及なし → ここが「宝の持ち腐れ」の実体）
   - ユーザーの用語が既存 glossary と衝突したら即指摘
   - 収束時、ADR 3 条件テスト（不可逆 / 文脈なしで不可解 / 実トレードオフ）を通る決定を `/adr-writer` へルーティング
3. 対応は**新スキル追加ではなく grill-me への追記**（rules/common/skills.md の Knowledge Placement: 既存スキルへの追記優先）。

## 変更内容

**対象ファイル: `~/.claude/skills/grill-me/SKILL.md` のみ**（1 ファイル編集、新規作成なし）

### 1. frontmatter の origin 修正

`origin: mattpocock/skills` → `origin: mattpocock/skills-customized`
（skills.md ルール: 外部 origin 由来を内容編集したら `-customized` を付す。現状すでに adapted なのに未付与 — 今回の編集で確実に該当）

### 2. Method セクションに docs-aware ルールを追加

Rule 3（explore codebase before asking）を拡張 + 新ルールを追加。趣旨:

- **Fact 源に docs を含める**: 質問する前に `docs/adr/`・`docs/CODEMAPS/`・glossary・`graph.jsonld`・`CLAUDE.md` があれば参照する。既に決定済みの事項（既存 ADR）を再度ユーザーに問わない — 代わりに「ADR-000X はこう決めているが、この計画はそれと矛盾する。上書きするか？」と衝突として提示する
- **用語チャレンジ**: ユーザーの用語が repo の glossary / 既存 docs の定義と食い違ったら即座に指摘し、正準用語を提案する（domain-modeling の Challenge / Sharpen を移植）
- **コード照合**: ユーザーの「〜のはず」発言はコードと照合し、矛盾があればその場で提示（domain-modeling の Cross-reference を移植）

### 3. Output セクションに決定のルーティングを追加

収束時のサマリに加えて:

- 各決定を **ADR 3 条件テスト**（①後から覆すコストが大きい ②将来の読者が文脈なしでは「なぜ？」となる ③実在した代替案からのトレードオフ）にかけ、3 つ全部満たすものだけ `/adr-writer` での記録を**提案**する（Reversibility Gate: 新規ファイル作成は確認してから — 自動作成しない）
- glossary 持ちの repo で新しい用語が確定したら、glossary への追記を**提案**する
- 上流 attribution 行を更新: 「Adapted from grill-me / grilling / grill-with-docs (domain-modeling)」

### 導入しないもの（Alternatives）

- `grilling` 単体スキル — 吸収済み。二重管理になるだけ
- `grill-with-docs` ラッパー — 1 行の価値しかなく、ローカルでは grill-me 自体を docs-aware にする方が lean
- `domain-modeling` 独立スキル + CONTEXT.md / CONTEXT-MAP.md 規約 — 既存の glossary / ADR / CODEMAPS 規約と並行構造が生じ context-sync のロールモデル（Context / Architecture / Decisions / External）とも競合。ubiquitous language の独立運用が将来必要になったら、その時に切り出す（YAGNI）

## Verification

1. `python3 -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('~/.claude/skills/grill-me/SKILL.md').expanduser().read_text().split('---')[1])"` で frontmatter の YAML 妥当性確認（skill-creator の既知 gotcha: 生成 description の `: ` が YAML を破壊）
2. 本文を通読し、5 Rules の番号整合・「When NOT to use」の分岐（council / product-lens / debugging.md）が壊れていないこと
3. `git -C ~/.claude status` で意図しないファイルが無いこと（変更は SKILL.md 1 ファイルのみ）

種別: `chore`（harness スキル編集、コード変更なし）。Chain Matrix 上 Code/Security Review は非該当、Verify のみ。

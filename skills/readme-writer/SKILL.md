---
name: readme-writer
description: 人間向け README（人間 + 検索 + AI Overviews が着地する単一正準入口）を書く・改善するスキル。llms-txt-writer の人間版。構造的衛生（H1 単一・見出しレベル・alt-text・ローカルリンク健全性）は決定論的な readme_lint で検査し、意味的品質（lead が人を掴むか・価値提案の明快さ・物語の流れ）は LLM のホリスティック review で扱う。後者にスコアは付けない。AI 専用 doc（llms.txt 等）には使わない。
user-invocable: true
origin: shimo4228
---

# readme-writer — Human-Facing README Skill

人間（と、人間が着地する検索 / AI Overviews）に向けた README を書く・改善するスキル。`llms-txt-writer` が AI surface を担うのに対し、本 skill は **人間 surface の単一正準入口**を担う。

## When to Use

- README.md / README.ja.md を新規作成・改善する
- repo / プロジェクトの「人間が最初に着地するページ」を整える
- 既存 README が「機械寄りで人間に中途半端」なのを人間ファーストに直す

**使わない場面**:
- `llms.txt` / `llms-full.txt` / FAQ など AI 専用 doc（→ `llms-txt-writer`）
- 記事・エッセイ・ブログ等の長文 prose（→ `writing-ecosystem`）
- graph.jsonld の設計（→ `jsonld-knowledge-graph`）

---

## なぜ「構造 lint」と「ホリスティック review」を分けるのか

README 品質には 2 種類の property が混在する。**AKC ADR-0008 "Code-LLM Layering"** に従い、所有者を分ける:

- [agent-knowledge-cycle/docs/adr/0008-code-and-llm-collaboration.md](https://github.com/shimo4228/agent-knowledge-cycle/blob/main/docs/adr/0008-code-and-llm-collaboration.md)（Agent Knowledge Cycle research line, concept DOI [10.5281/zenodo.19200726](https://doi.org/10.5281/zenodo.19200726)）
- 判定の軸は [`when-code-when-llm`](../when-code-when-llm/SKILL.md): 「同じバイト列が文脈で違う意味になりうるか?」

| property | 例 | 種別 | 所有者 |
|---|---|---|---|
| 構造的 | H1 が 1 個か / 見出しレベル飛ばし / alt-text 有無 / ローカルリンク解決 | structural | **code（`readme_lint.py`）** 100% 精度 |
| 意味的 | lead が人を掴むか / 価値提案の明快さ / 物語の流れ / 用語の適切さ | semantic | **LLM のホリスティック review** |

**`geo_check.py` のような研究値ベースのスコアは README には作らない**。llms.txt のセクション比率（ski-ramp 等）は LLM 引用研究で検証された決定論的シグナルだが、README の「良い人間入口か」は意味的判断であり、同等の決定論的知見は存在しない。entity density 等の AI surface 指標を人間 README に持ち込むのは anti-pattern。

---

## Workflow（Code filter → LLM → 人間 gate）

AKC の layering パターンそのまま。

### 1. Code filter — `readme_lint.py`（決定論的、structural only）

```
uv run --directory ~/.claude/skills/readme-writer python -m scripts.readme_lint "$ARGUMENTS"
```

引数は README の絶対パス。`--json` で機械可読出力。exit code が code-owned gate（0=clean / 1=issue / 2=not found）。

検査項目（すべて structural、**スコアではなく具体 issue**）:
- `single_h1` — H1 はちょうど 1 個
- `heading_levels` — 見出しレベルを飛ばさない（H2→H4 等）
- `alt_text` — すべての画像に alt（accessibility + 画像 SEO）
- `local_link` — ローカル相対リンク / 画像 src が実在する

### 2. LLM holistic review（rubric-as-lens、**スコア無し**、signal-first）

lint が通ったら、Claude が README を**ホリスティックに読み**、次の lens（採点表ではなく「注目すべき次元」）で**直接の所見 + 具体 diff** を出す:

- **Lead の What / Who / Why** — 最初のスクリーンで「何で・誰向けで・なぜ気にすべきか」が分かるか
- **人間フック** — 読み手が「自分ごと」と感じる入口があるか
- **価値提案の明快さ** — 抽象語でなく具体で価値が言えているか
- **物語 / scannability** — 段落・見出し・list が人間に追えるか
- **keyword を意識した見出し** — GitHub / Google の検索意図に合うか（ただし詰め込みは逆効果）
- **fact 一致** — 主張が機械層（llms.txt / graph.jsonld）と矛盾しないか → **`context-sync` に委譲**

**スコアを付けない理由**（signal-first + scaffold-dissolution）: 「次の行動を変える情報」だけを出す。`Lead: 6/10` は行動を変えない。「lead が誰向けか言っていない」という具体所見が行動を変える。消費する code gate のないスコアは scaffolding であり、モデルの判断を数値に圧縮して殺す。出力は diff 形式で `y/n` 承認できる粒度に分割する。

author-reviewer separation のため、review は実装者と別 agent プロセスで回すのが望ましい（`editor` / `essay-reviewer` と同型。README 用の lens は上記）。

### 3. fact 一致確認 → `context-sync`

README の事実が llms.txt / llms-full.txt / graph.jsonld と一致するか（cloaking 回避 = 全 surface で事実一致）は `context-sync` が正本。本 skill では再実装しない。

### 4. 人間 gate

diff を人間が承認して適用。

---

## What This Skill Does NOT Do（境界）

- `llms.txt` / `llms-full.txt` を書かない（→ `llms-txt-writer`）
- `graph.jsonld` を設計しない（→ `jsonld-knowledge-graph`）
- cross-surface の drift 検出 / 同期をしない（→ `context-sync` / `release-doi`）
- 記事 / エッセイを編集しない（→ `writing-ecosystem`）
- repo の description / topics / social-preview を設定しない（`gh repo edit` / `release-doi` 側。本 skill は checklist として提示するのみ）
- **品質スコア / grade / 評点を出さない**

---

## Anti-patterns

- 数値スコアだけ出して具体案なしで終わる（recommender 型の罠）
- 構造 lint で済む項目を LLM に判断させる / 意味的判断を regex で代用する（`when-code-when-llm` 参照）
- AI surface の指標（ski-ramp / entity density）を人間 README に流用する（可読性低下）
- 人間向けに事実を盛る / マネタイズ訴求を足す（authenticity 毀損 + 機械層との矛盾 = cloaking リスク。梱包は変えても主張は変えない）

---

## Verification

```bash
cd ~/.claude/skills/readme-writer
uv sync --dev
uv run pytest tests/ --cov=scripts --cov-report=term-missing
```

`fixtures/sample_clean.md`（issue 0）と `fixtures/sample_issues.md`（複数 issue）で基本挙動を確認できる。

---

## Related

- [`llms-txt-writer`](../llms-txt-writer/SKILL.md) — AI surface の対になる writer（研究値ベースの `geo_check.py` を持つ）。本 skill は人間 surface。
- [`when-code-when-llm`](../when-code-when-llm/SKILL.md) — structural / semantic の判定軸
- **AKC ADR-0008 "Code-LLM Layering"** — [agent-knowledge-cycle/docs/adr/0008-code-and-llm-collaboration.md](https://github.com/shimo4228/agent-knowledge-cycle/blob/main/docs/adr/0008-code-and-llm-collaboration.md)
- [`context-sync`](../context-sync/SKILL.md) — README ↔ 機械層の fact 一致 / drift（fact 検証はこちらに委譲）
- [`writing-ecosystem`](../writing-ecosystem/SKILL.md) — 人間向け長文 prose の orchestrator（役割分離）

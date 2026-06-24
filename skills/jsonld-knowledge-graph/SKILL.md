---
name: jsonld-knowledge-graph
description: Design and ship a companion JSON-LD knowledge graph (graph.jsonld) next to llms.txt for projects with stable concept-level structure. Encodes domain entities and relationships as schema.org triples for LLM citation. Use when project has matrix / hierarchy / phase-binding structure that prose alone leaves implicit, AND that structure is stable across releases. Defers llms.txt navigator wording to llms-txt-writer.
origin: shimo4228
user-invocable: true
---

# JSON-LD Knowledge Graph

`graph.jsonld` を `llms.txt` の隣に置いて、project の concept-level architecture を schema.org JSON-LD triples として encode する skill。LLM が prose だけでは引き出しにくい entity 間の関係（matrix / hierarchy / phase-binding）を triple として citation 可能にする。

## When to Use

以下を **すべて** 満たす project に適用する:

- 安定した concept-level 構造を持つ
  - 例: matrix（4 Quadrants × N ADRs）、ordered hierarchy（prohibition-strength 3 levels）、phase-skill binding（6:6 bijective）、layered architecture（3 memory layers）
- 構造が **release を跨いで安定**（vX.Y.Z bump で entity が増減しない）
- LLM に当該関係を訊いた時に **prose だけでは答が出にくい / 誤答する** 経験的証拠がある
- すでに `llms.txt` + `llms-full.txt`（Answer.AI 標準）を持っている

## When NOT to Use

以下のいずれかに該当する場合は **適用しない**:

- 単一目的の linear project（matrix / hierarchy 構造がない）
- 内部構造が release ごとに churn する（graph が編集負債になる）
- `llms-full.txt` の prose Q&A で関係問題が既に十分答えられる
- 「LLM citation 向上を狙いたい」だけで具体的な entity 関係問題がない（GEO 目的なら llms-txt-writer の方が direct）

`graph.jsonld` は prose の代替ではなく **補完**。prose で表現しきれない構造があるとき、その構造をやっと拾える。

## CODEMAPS との関係（正本）

`graph.jsonld` と CODEMAPS（典型的には `docs/CODEMAPS/architecture.md`）は **同じ project を異なる abstraction 層で扱う**:

| | CODEMAPS | graph.jsonld |
|---|---|---|
| **対象** | ファイル / モジュール | 概念 / エンティティ |
| **抽象層** | file-level | concept-level |
| **答える質問** | 「X はどのファイルに住んでいるか」 | 「X とは何か、X と Y はどう関係するか」 |
| **形式** | prose（Markdown） | JSON-LD triples |
| **主読者** | 人間 + agent が code を navigate する時 | AI search engine + LLM が entity を citation する時 |
| **trigger** | code 構造の変化 | concept / 関係の変化 |

両者は **重複せず相補的**。同じ entity を別角度から見る。例えば AAP の `Quadrant` ノード:

- CODEMAPS は「Quadrants の解説は `docs/quadrants/README.md` に住む、`governance-mapping.md` が matrix 表」と書く（file-level）
- graph.jsonld は「Quadrant 3 (LLM Workflow) に ADR-0001/0003-0007 が `appliesTo`、`governanceTier: medium`、`xAxis: semantic-judgment`」と書く（concept-level）

### Drift 防止のための運用規約

新規 entity を追加する時は **両面で更新する**:

- 新規 ADR / Concept / Quadrant 等を追加 → graph.jsonld にノード追加 + CODEMAPS の該当 file path 言及を更新
- ファイルパスが変わった → CODEMAPS 更新（graph.jsonld の `@id` は GitHub blob URL を使っているなら追従が必要）
- 概念の semantics が変わった → graph.jsonld の description 更新（CODEMAPS は触らなくてよい）

context-sync skill（Maintain phase 担当）がこの drift を audit する。詳細は `~/.claude/skills/context-sync/SKILL.md` 参照。

## Required Design Moves

実装で観察された 9 つの再利用可能な move。すべて適用が default、外す場合は理由を明示する。

### 1. Dual `@type` on every node

```json
{
  "@id": "...",
  "@type": ["ResearchLine", "ScholarlyArticle"]
}
```

custom namespace type（domain semantics を持つ）+ schema.org base type（AI search engine が citation target として認識）。両方つけることで、schema.org に親しい crawler も custom vocab に親しい LLM も同じノードを認識できる。

### 2. Language-tagged literals for bilingual

```json
"alternateName": [
  {"@value": "Four Business AI Quadrants", "@language": "en"},
  {"@value": "ビジネスAIの四象限", "@language": "ja"}
]
```

**1 file で en/ja 両対応**。`graph.ja.jsonld` を別ファイルにするのは禁止（同期負債が発生する）。Concept DOI / repo URL / `@id` は言語中立なので二重管理不要。

### 3. Schema absence で禁止関係を構造的に強制

「X と Y は **絶対に dependency 関係ではない**」を保証したい場合、`dependsOn` のような edge type を **そもそも `@context` に定義しない**。schema の vocabulary 自体が構造的 commitment になり、表現できない関係は表現されない。

例: 3 つの sibling research line が独立進化することを強制するため、共通 vocab には `dependsOn` edge type を **そもそも定義しない**。代わりに `siblingOf`（symmetric）と `derivesFrom`（historical / 一方向、ある line が別 line から実装的に派生した事実を encode する場合のみ使う）の 2 種類だけを定義する。

### 4. Cross-graph `@id` reuse で triple merge

複数の `graph.jsonld` ファイルが存在する場合（hub-and-spoke topology）、共有 entity の `@id` は **byte-identical** にする。例:

- 3 つの memory layers が 2 つの sibling line repo の graph に登場
- 両方とも `@id: "https://<owner>.github.io/<owner>/vocab#memory-layer/episode-log"` を使う（owner namespace は project ごとに置換）
- LLM がふたつの graph を crawl すると triple が自動 merge され、「同じ概念」として認識される

これは JSON-LD 1.1 の標準動作。pyld など conformant processor で実装可能。

### 5. Volatile state を schema レベルで除外

graph.jsonld に **以下の field を持たせない**:

- version 番号 (`version`, `versionNumber`, `vX.Y.Z`)
- count（ADR 数、test 数、ノード数）
- 流動的 enumeration（churning skill list, dynamic capability list）

schema に存在しない field は entity に乗らないので、routine release が graph に漏れない。`grep -E '"version"|"count"|v[0-9]+\.[0-9]+' graph.jsonld` が常に空を返すことを CI で検証可能。

### 6. Matrix encoding via paired edges

`A × B` matrix を encode する場合、片方向の edge だけでは不十分。**2 つの complementary edge** を使う:

- `appliesTo` (`ADR → Quadrant`): 各 ADR が適用される Quadrant 群
- `realizedBy` (`ProhibitionLevel → ADR`): 各 prohibition tier が実現される ADR

silence is signal: 「Quadrant 1, 2 (Script, Algorithmic Search) は AAP 適用外」は `appliesTo` edge の **不在** で表現する。`governanceTier: "out-of-scope"` プロパティで明示的にも stamp する。

### 7. Root `Dataset` node で graph self-description

`@graph` array の先頭に schema.org `Dataset` 型のルートノードを置く:

```json
{
  "@id": "https://github.com/owner/repo#knowledge-graph",
  "@type": ["Dataset", "CreativeWork"],
  "name": "Project Knowledge Graph",
  "description": "...",
  "isBasedOn": "https://github.com/owner/repo",
  "mainEntity": [<primary entity @ids>]
}
```

schema.org `Dataset` は Google AI Overviews / Perplexity が structured data として認識する。graph の **目的と entry points** を crawler に明示する役割。

### 8. Reading-order block で AI 入口導線を明示

`llms.txt` 冒頭に Graph-first reading order block を置く。詳細手順は llms-txt-writer skill 参照。要点:

- タイトル直下に `> AI agents should read graph.jsonld first` blockquote
- 直後に numbered "Recommended reading order" section
- Core documentation navigator の最上位に graph.jsonld

### 9. Reverse-link で hub-and-spoke 経路双方向化

hub-and-spoke topology の場合、各 line repo の README に **hub graph への逆リンク**を置く:

```markdown
For the canonical relationship map of <ecosystem>'s research ecosystem, see:
https://github.com/<owner>/<hub>/blob/main/graph.jsonld
```

LLM が個別 line repo から入ってきた場合でも hub graph へ戻れる。1 段目の探索後に broader context へ広げる経路。

**散文リンクだけでは不十分** — README 逆リンクは人間/プレーンテキスト向け。グラフ層でも各 spoke の **self-node に機械可読な上向き edge** を張る:

```json
// 各 line / supporting repo の self-node (ResearchLine or Dataset) に:
"isPartOf": "https://github.com/<owner>/<hub>"   // hub の canonical @id (bare-repo URL に統一)
```

- hub→spoke は `mainEntity` / `siblingOf`、spoke→hub は `isPartOf` で双方向化 (`isPartOf` の厳密な逆は `hasPart` だが、独立 triple として有効)
- target @id は **全 repo で同一の canonical hub node** に揃える (bare-repo `github.com/<owner>/<hub>` 推奨)。揃わないと merge 時に hub が複数ノードに割れて join 不能
- `isPartOf` は context に `{"@id":"https://schema.org/isPartOf","@type":"@id"}` を宣言 (無いと「IRI 文字列の literal 化」と同じく literal になる)。context を触れない content graph では inline `{"@id":"..."}` で node 参照を強制
- self-node を持たない content-only graph (Article 列挙のみ等) には最小 Dataset self-node を1個新設し、そこに `isPartOf` を張る
- **監査**: 新 repo 追加時、全 spoke の self-node が `isPartOf→hub` を持つか確認。実地では下向き (hub→spoke) だけ張られ、上向きが大半の spoke で抜けていた

## Schema Vocabulary 設計

新規 type / edge を導入する判断基準:

### 新規 node type を作る条件

- **closed / bounded set**: 「4 axioms」「3 memory layers」のように member が limited で stable
- **ordering invariant が必要**: `ProhibitionLevel` のように `level` integer で順序を保つ必要がある
- **distinct semantics**: `Axiom` は swappable preset の 1 instance、`Concept` は free-form term — 同じ `Concept` 扱いだと意味が混ざる

これに当てはまらない場合は、既存の `Concept` instance として encode する（4 code-LLM patterns のように、4 件しかなく新規 type 化に値しない場合）。

### 新規 edge type を作る条件

- **既存 edge では semantic が違う**: `extends` (EcosystemRepo → ResearchLine) と `appliesTo` (ADR → Quadrant) は別の関係。reuse すると混乱
- **matrix の片側を成す**: `appliesTo` + `realizedBy` のように、matrix encoding に必須

新規 edge は schema.org base vocabulary に該当があれば優先する（`url`, `identifier`, `citation`, `isBasedOn`, `mainEntity` 等）。custom vocab に追加するのは schema.org base で表現できない時のみ。

### `@id` namespace 設計

- ResearchLine: 既存 DOI URL を使う（`https://doi.org/10.5281/zenodo.NNNN`、**concept DOI** 必須、latest DOI は使わない）
- EcosystemRepo: GitHub repo URL（`https://github.com/owner/repo`）
- Concept: custom vocab namespace（`https://<owner>.github.io/<owner>/vocab#concept/<slug>` 等）
- ADR: GitHub blob URL（`https://github.com/owner/repo/blob/main/docs/adr/NNNN-slug.md`）

namespace は dereferenceable である必要なし（典型的な "private vocab" pattern）。重要なのは **byte-identical re-use** が cross-graph で実現できること。

## Cross-graph @id Discipline

hub-and-spoke topology で複数 graph を持つ場合の規約:

1. **Hub graph に登場する entity の `@id` を canonical** とする
2. 各 line graph で同じ entity を参照する時は、**copy-paste で `@id` を再利用**（手入力しない、typo 防止）
3. 新規 entity を追加する時は hub graph 側にまず登録してから line graph で参照
4. `@id` を変更する場合は、すべての graph を同時に更新（cross-graph grep で漏れ確認）

verification:

```bash
# Hub graph の primary entity @id を抽出
jq -r '.["@graph"][] | select(.["@type"][] | contains("ResearchLine")) | .["@id"]' hub/graph.jsonld

# 各 line graph でも同じ @id が登場することを確認
grep -h "doi.org/10.5281/zenodo" */graph.jsonld | sort -u
```

## Bilingual Strategy

JSON-LD 1.1 の language-tagged literal を使い、**1 file で en/ja を保持**:

```json
{
  "alternateName": [
    {"@value": "Agent Knowledge Cycle", "@language": "en"},
    {"@value": "エージェント知識サイクル", "@language": "ja"}
  ]
}
```

### やってはいけないこと

- `graph.ja.jsonld` を別ファイルにする → 同期負債発生
- 一部の literal だけ多言語化する → 一貫性が崩れて LLM 解釈に揺れ
- `@language` を省略する → デフォルト言語が不明、crawler の解釈が undefined

### やるべきこと

- ResearchLine `name` と `alternateName` は必ず両言語
- Concept / Axiom / Quadrant など concept-level node は `alternateName` で両言語
- description は en 単独でもよい（prose は llms-full.txt が正本、graph は entity 識別が主目的）
- ADR title は en 単独でよい（GitHub の英語 prose が正本）

## Companion File Wiring

graph.jsonld を作っただけでは crawler に見つからない。`llms.txt` / `llms-full.txt` / README に wiring が必要:

| ファイル | 何を追加 |
|---|---|
| `llms.txt` | (1) 冒頭に Graph-first reading order blockquote と numbered section、(2) Core documentation navigator の最上位に graph.jsonld entry |
| `llms-full.txt` | 末尾に question-form H2（"How do X and Y relate as a graph?"）+ graph.jsonld への link + 3 つ程度の load-bearing design choice 説明 |
| `README.md` (人間向け) | 冒頭に `<details><summary>AI-facing reading order</summary>` 折りたたみ block。維持している language mirror があれば同 block を mirror にも入れる |
| `README.{lang}.md` (追加 mirror がある場合) | summary tag と intro 行のみ localize、bullet list は paths なので en 共通でよい。**ja を超えて mirror を維持するかは traffic data に基づき判断**: human viewers が統計的に存在しない mirror は LLM crawler が en source から多言語 answer する現状を踏まえると不要 |
| hub-and-spoke の line README | hub graph への reverse-link を上記 block 内に追加 |

詳細な wording は `~/.claude/skills/llms-txt-writer/SKILL.md` の Companion JSON-LD Graph セクション参照。

## Verification Workflow

graph.jsonld を作成・編集したら以下を実行:

```bash
# 1. JSON 構文
python3 -m json.tool < graph.jsonld > /dev/null

# 2. JSON-LD expansion + N-Quads triple count
uvx --quiet --from pyld python3 -c "
from pyld import jsonld
import json
doc = json.load(open('graph.jsonld'))
expanded = jsonld.expand(doc)
nquads = jsonld.to_rdf(doc, {'format': 'application/n-quads'})
lines = [l for l in nquads.strip().split(chr(10)) if l]
print(f'{len(expanded)} nodes / {len(lines)} triples')
"

# 3. Volatile state 検出（empty が期待値）
grep -E '"version"|"versionNumber"|"adrCount"|"testCount"|v[0-9]+\.[0-9]+' graph.jsonld

# 4. Reading-order presence in llms.txt
head -30 llms.txt | grep -c "Recommended reading order\|graph.jsonld"

# 5. Concept DOI 整合（latest ではなく concept DOI が @id に使われている）
# (manual: 各 ResearchLine @id を Zenodo で開いて parent record であることを確認)
```

### Context pitfalls — edge が静かに消える 2 パターン

production graph 6 本の監査 (2026-06) で実際に発生した。いずれも JSON は valid のまま、
triple count も変わらないため、上記 step 1-2 では検出できない:

1. **IRI 文字列の literal 化**: `@vocab` があっても、context で `@type: "@id"` 強制の
   ない property（schema.org の `author` / `creator` 等）に IRI を文字列で渡すと literal
   になり、node への edge にならない。Person node が graph に居ても誰からも参照されない。
   - 対策: IRI 参照は常に `{"@id": "https://..."}` オブジェクト形式で書く
2. **未定義 key の無言ドロップ**: `@vocab` なしの明示マッピング型 context では、context に
   無い key（`sameAs` 等）が expansion で警告なく消える。
   - 対策: graph に新しい property を導入する前に context マッピングの存在を確認する

検出は同梱の lint script が決定論的に行う（上記 step 1-3 の機械チェックも包含するので、編集後はこれ 1 コマンドでよい）:

```bash
# 6. graph lint — JSON validity / expansion / DROPPED-KEY / URL-LITERAL / VOLATILE を一括検査
#    exit 0 = clean, 1 = findings, 2 = fatal。複数ファイル可
uv run --with pyld python3 ~/.claude/skills/jsonld-knowledge-graph/scripts/graph_lint.py graph.jsonld

# locator 系 property（url / license / contentUrl）は literal URL を許容。変更する場合:
#   --allow-literal-url url,license,contentUrl,codeRepository

# 複数 graph を渡すと cross-file の NAME-DRIFT も検査する
# （同一 IRI に複数の異なる en name → 検出は構造的・決定論的。どれを正とするかの
#   解決だけが judgment なので、lint は報告のみ。表記揺れの正解は alternateName に置く）
uv run --with pyld python3 ~/.claude/skills/jsonld-knowledge-graph/scripts/graph_lint.py hub/graph.jsonld line1/graph.jsonld line2/graph.jsonld
#   --skip-name-drift で省略可
```

修正の定石: 値の書き換えではなく **@context への coercion 追加** で直す（`"sameAs": {"@id": "https://schema.org/sameAs", "@type": "@id"}` を足せば既存の文字列値がそのまま IRI として解釈される。diff が context の数行で済む）。

#### なぜ自作 lint か（external research, 2026-06）

標準ツールを調査した上での Build 判定。再調査不要:

- **[pySHACL](https://github.com/RDFLib/pySHACL)** (RDFLib): 活発に維持されている W3C 標準の RDF 検証器。ただし**展開後の RDF graph に対して動く**ため、DROPPED-KEY は原理的に検出できない（落ちた key は SHACL が見る前に消えている）。URL-LITERAL は `sh:nodeKind sh:IRI` で書けるが、predicate ごとの shapes ファイル維持が必要
- **[jsonld-lint](https://github.com/mattrglobal/jsonld-lint)** (Mattr): un-mapped term 検出（= DROPPED-KEY）を持つ唯一の専用 linter だったが **2024-12 にアーカイブ済み**。採用不可
- **jsonld.js の safe mode**: 展開時に未定義 term をエラー化できるが JS 専用。Python 側の pyld に相当機能なし

つまり最も危険な DROPPED-KEY が標準ツールの死角にあり、VOLATILE はプロジェクト固有ポリシーなので、薄い自作 lint が正当。

**pySHACL への移行条件**: 「すべての ResearchLine ノードは author と sameAs を持つ」のような**クラス単位の必須制約**を宣言的に強制したくなった時点で、URL-LITERAL 検査を shapes.ttl + pyshacl に置き換え、DROPPED-KEY / VOLATILE のみ graph_lint.py に残す構成に移行する。

### Manual checks

- **JSON-LD playground**: https://json-ld.org/playground/ に paste して `@context` が解決し triple として展開されることを確認
- **schema.org validator**: https://validator.schema.org/ で `Dataset` / `ScholarlyArticle` 等の type が認識されることを確認
- **LLM citation probe**: graph push 後 1-2 週間（crawler refresh 待ち）、ChatGPT / Perplexity に「<project> の X と Y はどう関係しますか？graph.jsonld を参照してください」と質問し、graph が citation されるか確認

## Mirror Sync to Hugging Face Datasets

graph.jsonld を更新したら、Hugging Face Datasets 上の mirror にも同期する。HF は LLM training pipeline / knowledge-graph crawler の primary ingest source として機能する（HF dataset は Auto-converted to Parquet が走り、`pandas` / `Polars` / `Datasets` ライブラリから直接 load 可能になる）。

**正本は [`hf-sync`](../hf-sync/SKILL.md) skill にある**。`/hf-sync <Owner/dataset>` または `bash ~/.claude/skills/hf-sync/sync.sh <Owner/dataset>` を project root で実行すれば、`graph.jsonld` の structural check → `graph.jsonl` flatten → `hf upload` 2 ファイルが 1 コマンドで走る。Local の `hf login` token を使うので CI auth setup は不要。

`release-doi` skill の Phase 5 末尾（tag push + `gh release create` の後）で呼ぶのが標準フロー。ad-hoc resync にも同じ skill を使う。

**Wikidata QID の sameAs 編入は [`wikidata-federation`](../wikidata-federation/SKILL.md) skill が担う**（Wikidata item 作成 → graph ノードへの QID アンカー。フォーマット保存編集と意味的検証つき）。graph 設計の正本は本 skill、Wikidata 連邦の operational layer は wikidata-federation、という役割分離。

HF 側の `README.md` (dataset card) は graph 更新では同期しない。Dataset card は HF 用に customize されている（sibling dataset への link、mirror notice 等）ので、文面を変えたい場合は手動で `hf upload <Owner/dataset> README.md --repo-type dataset`。

### Repo mapping (project-specific)

GitHub repo ↔ HF dataset の mapping は project ごとに違うので、skill invoke 時に参照できる場所（project の `CLAUDE.md`、または skill 同一 dir の `inspiration.md`）に記録する。`hf-sync` 本文には embed しない（portability 確保）。

Mapping の記録 format 例:

```markdown
| GitHub repo | HF dataset |
|---|---|
| `owner/project-a` | `Owner/project-a` |
| `owner/hub` | `Owner/research-program-hub` |
```

### When NOT to use this sync

- HF dataset がまだ存在しない project（先に `hf repo create <Owner/dataset> --repo-type dataset` で repo 作成、README.md を draft してから initial upload）
- そもそも graph.jsonld を持たない project（HF mirror は graph を持つ project のみ）
- Token が write scope を持たない（HF settings で Fine-grained / Write token を発行し直す）

## Maintenance Contract

graph.jsonld を **編集する trigger**:

- ecosystem repo の追加 / 退役 → `EcosystemRepo` ノード add/remove
- 新しい stable structural concept の登場 → `Concept` / `Axiom` / `Quadrant` ノード add + 関連 edges
- 新 research line の開始 → `ResearchLine` ノード + `siblingOf` edges
- Concept DOI 自体が移動（稀、Zenodo record restructuring 時のみ）

graph.jsonld を **編集してはいけない trigger**（routine release では触らない）:

- 任意 module の `vX.Y.Z` release
- ADR count, skill count, test count, version bump
- 内部 module の restructuring（CODEMAPS は更新するが graph は触らない）
- model version bump（`qwen3.5:9b` から `qwen4:9b` 等）

schema に version / count / churning field を持たせていない限り、これらは graph に **そもそも encode できない** ので構造的に強制される。

## Reference Implementation

このパターンの canonical implementation pointer（具体 repo URL / DOI / vocab namespace）は本 skill 本文に含めず、同一ディレクトリの [`inspiration.md`](inspiration.md) に記録する（portability 確保）。pattern を新しい project に適用する場合、以下の構造目安が参考になる:

- **Hub-and-spoke 構成**: 1 つの hub graph が sibling line graph 群を `siblingOf` で繋ぐ
- **Hub graph 規模目安**: 3-5 ResearchLine + 10-20 EcosystemRepo + 5-10 Concept + 3-5 ExternalReference
- **Per-line graph 規模目安**: 1 ResearchLine + line 内部構造（matrix / hierarchy / phase-binding）を 20-40 nodes で encode
- **共通 vocab**: 全 graph が同じ namespace を使い、shared `@id` で triple merge を実現

単一 repo（hub なし）でも matrix / hierarchy 構造があれば適用可能。その場合 hub-related の sibling/derivesFrom 系 edge は不要。

## What This Skill Does NOT Do

- llms.txt / llms-full.txt の文章設計 — use `llms-txt-writer`
- Project doc role の overlap 検出 / 整理 — use `context-sync`
- CODEMAPS の生成 / 更新 — use `update-codemaps`
- Articles / blog post の文体 設計 — use `article-writing` / `writing-ecosystem`

## Related

- `llms-txt-writer` — llms.txt / llms-full.txt 本体の書き方、navigator 設計、GEO/AEO 最適化
- `context-sync` — graph.jsonld と CODEMAPS の drift audit（Maintain phase）
- `update-codemaps` — file-level architecture documentation の正本

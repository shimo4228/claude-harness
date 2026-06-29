---
name: wiki-harvest
description: 研究 repo セッションから LLM wiki (Obsidian Vault wiki/concept/) を read-only で走査し、その repo の主担当 concept ページから「repo の次アクションを変えうる候補」だけを抽出して、一次出典付き・landing slot マップ付きのランク付き候補台帳 (ledger) を repo の .notes/ に生成する。Use when the user invokes /wiki-harvest, asks「wiki から repo に還元して」「wiki の有益分を AKC/AAP/CA/authorship に持ってきて」, or when closing the daily-research→wiki→repo loop. wiki への書き込みは行わない（それは vault セッションの /ingest）。chat 上の自由質問は wiki-query。
user-invocable: true
origin: shimo4228
---

# wiki-harvest — LLM wiki から研究 repo への還元

研究 repo セッションで実行し、LLM wiki（Obsidian Vault）の合成知識から **その repo の次アクションを変えうる候補だけ**を抽出して、一次出典付きのランク付き候補台帳（ledger）を repo 内に生成する。

各研究 repo の `CLAUDE.md`「Research Wiki Consultation」節に *passive prose* で書かれている還元マップ（4カテゴリ）を、再現可能な能動手続きに形式化したもの。構造的には `gap-review`（diff → ランク付き候補 → two-tier ledger）の **wiki→repo 版**。daily-research → wiki（合成層）→ repo（昇格）という一方向ループの最終辺を1コマンドで回す。

> 兄弟スキル: `wiki-query` = chat 上の自由 Q&A（read-only）。`wiki-harvest` = repo 向け定型抽出 → 台帳。両者とも wiki に対し **read-only**。置き換えではない。

## Vault パス（固定）

```
VAULT="/Users/shimomoto_tatsuya/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault"
```

- 概念ページ: `$VAULT/wiki/concept/<概念名>.md`
- インデックス: `$VAULT/wiki/index.md`
- 構造グラフ: `$VAULT/wiki/graph.jsonld`（symlink → `~/MyAI_Lab/daily-research/graph.jsonld`）
- 原資料: `$VAULT/daily-research/`

> この skill は shimo4228 の個人運用（固定 vault + 自分の研究 repo 群）に紐づく。repo→concept マッピングは skill にハードコードせず、各 repo の CLAUDE.md から読む（下記 Step 1）。

## 制約（CRITICAL）

- **wiki は read-only**。この skill から vault 内のいかなるファイルにも書き込まない。wiki の更新（ingest / index / log）は vault セッションの `/ingest` の領域。一方向ループ（source → wiki → repo）を保全する。
- **書き込みは repo 内の ledger のみ**。`.notes/wiki-harvest/ledger.md`（working/non-citable・gitignore 対象）だけを生成・更新する。
- **durable/citable な成果物（`docs/adr/` / `graph.jsonld` / `glossary.md` / `manifesto.md`）には書かない**。それらへの昇格は人間承認の別ステップ（reversibility gate + 既存ルール「promotion は repo author が判断」）。
- iCloud dataless プレースホルダに注意: 読んだ concept ページ本文が空なら未ダウンロードの可能性。その旨を報告する。

## 手順

### Step 1 — repo と対象 concept の特定

1. cwd / git remote から現在の研究 repo を判定（`agent-knowledge-cycle` / `agent-attribution-practice` / `contemplative-agent` / `authorship-strategy` 等）。
2. その repo の `CLAUDE.md` 内「Research Wiki Consultation」節を Read し、`主担当ページ` + `隣接` に挙がっている concept 名を取得する。**マッピングはここ（repo 側）が正本**。skill にハードコードしない。
3. 節が無い repo（現状 AKC）は fallback: `$VAULT/wiki/graph.jsonld` の `track` 値（akc / aap / contemplative / authorship）と repo 名から対象 concept を推定し、**「consultation 節が欠落している」ことを報告**する（後で節を backfill すべき signal）。

### Step 2 — wiki 走査（read-only）

`$VAULT/wiki/index.md` で対象 concept ページの所在を確認 → 各ページを Read し、以下の4カテゴリを抽出する（CLAUDE.md consultation 節の還元マップを正本化）:

| # | 抽出元（concept ページの節） | 還元先 landing slot | 候補の性質 |
|---|---|---|---|
| ① | `## オープンクエスチョン` の「ADR 候補」マーク | `docs/adr/` | 新規 ADR の種 |
| ② | `## 矛盾・論争` | repo の既存 ADR/claim と突合（stale-doc / conflict check） | 既存決定の見直し |
| ③ | `## 主要な主張` の外部出典（arXiv/DOI） | `graph.jsonld` の `ExternalReference` / citation | 引用辺の追加 |
| ④ | `## 関連概念` リンク | `graph.jsonld` の新辺 / 新 Concept ノード | repo graph に無い隣接 |

抽出・列挙は機械的に網羅する（enumerate）。採否は次の Step で絞る（decide）。

### Step 3 — signal フィルタ（品質ゲート）

`signal-first-research` の output discipline を適用する。**各候補は repo の具体的アクションを名指しできなければ捨てる**:

- どの ADR 番号を更新 / 新設するか
- どの graph 辺 / glossary 語 / manifesto 項を足す・解消するか

スコアや grade（「6/10」等）は付けない。**「action を変える具体的観察」**を記す（例:「ADR-0013 の前提を覆す」「graph に [[X]]↔[[Y]] の辺が無い」）。アクションを名指せない一般論・既知事項は ledger に載せない。

### Step 4 — 一次出典への遡行（citation discipline）

カテゴリ③（外部出典）の候補は、concept ページの `## 言及ソース` → `$VAULT/daily-research/YYYY-MM-DD_*.md` → 一次文献（arXiv ID / DOI）まで辿り、**一次 ID を候補に記録**する。

既存ルール厳守: 公開成果物には wiki ページや vault パスを引用しない。一次出典まで遡って引く（wiki は二次合成であり drift しうる）。wiki concept ページ・daily-research ノートは **provenance（追跡経路）としてのみ**候補に併記する。

### Step 5 — ledger 生成（two-tier 規律）

`.notes/wiki-harvest/ledger.md` を生成 or 追記する。

1. **gitignore 確保**: repo root の `.gitignore` に `.notes/` が無ければ1行追記する（`.gitignore` が無ければ作成）。これで working/non-citable な private ledger を git 追跡から物理的に外す（gap-review の two-tier 規律を担保）。
2. **冪等性**: 各候補に `status`（new / pending / promoted / dismissed）を持たせる。dedup キー = `concept ページ名 + 節 + claim の安定キー`。再実行時、既 `promoted`/`dismissed` は再浮上させない。`pending` は内容が変化した時のみ更新（重複追記しない）。
3. ranking: signal の強さ（repo アクションへの影響度）で `high` / `med` / `low`。

完了後、生成した候補の要約（件数・カテゴリ別内訳・high rank の見出し）を chat に返す。**ADR/graph への昇格は提案に留め、自動で書かない**。承認されたら既存 `adr-writer` agent / `citation-sync` / `jsonld-knowledge-graph` skill に人間が手動で引き継ぐ。

## Ledger フォーマット

```markdown
<!-- working ledger / NOT a citable artifact / gitignored (.notes/)。
     /wiki-harvest が生成・更新。昇格 (ADR/graph 書き込み) は人間承認の別ステップ。 -->
# wiki-harvest ledger: <repo-name>

## [YYYY-MM-DD] harvest | 対象 concept: [[<concept-A>]], [[<concept-B>]]

### 候補A (rank: high, status: new) → docs/adr/
- カテゴリ: ① OQ「ADR 候補」
- 抽出元: [[<concept>]] §オープンクエスチョン
- signal: <repo の具体的アクション。例「memory-layer の ADR が無い → 新規 ADR-00NN の種」>
- 一次出典: arXiv:25xx.xxxxx（[[daily-research/YYYY-MM-DD_...]] 経由）
- アクション: ADR 起草（人間承認待ち）

### 候補B (rank: med, status: pending) → graph.jsonld
- カテゴリ: ③ 外部出典 / ④ 関連概念辺
- ...
```

## 還元先と昇格の引き継ぎ先（landing slot 早見表）

| カテゴリ | landing slot | 昇格に使う既存ツール（人間承認後・手動） |
|---|---|---|
| ① OQ→ADR | `docs/adr/` | `adr-writer` agent / `/adr-writer` skill |
| ② 矛盾→見直し | 既存 `docs/adr/` の改訂 / `docs/manifesto.md` | 手動編集 |
| ③ 外部出典 | `graph.jsonld` / `.zenodo.json` | `citation-sync` skill |
| ④ 関連概念辺 | `graph.jsonld` | `jsonld-knowledge-graph` skill |

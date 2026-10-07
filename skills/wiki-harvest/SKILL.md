---
name: wiki-harvest
description: 研究 repo セッションから LLM wiki (Obsidian Vault wiki/concept/) を走査し、その repo の主担当 concept ページから「repo の次アクションを変えうる候補」だけを抽出して、一次出典付き・landing slot マップ付きのランク付き候補台帳 (ledger) を repo の .notes/ に生成する。Use when the user invokes /wiki-harvest, asks「wiki から repo に還元して」「wiki の有益分を AKC/AAP/CA/authorship に持ってきて」, or when closing the daily-research→wiki→repo loop.
user-invocable: true
origin: shimo4228
disable-model-invocation: true
---

# wiki-harvest — LLM wiki から研究 repo への還元

研究 repo セッションで実行し、LLM wiki（Obsidian Vault）の合成知識から **その repo の次アクションを変えうる候補だけ**を抽出して、一次出典付きのランク付き候補台帳（ledger）を repo 内に生成する。

> 兄弟スキル: `wiki-query` = chat 上の自由 Q&A（良回答は `wiki/concept/` へ書き戻す）。`wiki-harvest` = repo 向け定型抽出 → 台帳。

## Vault パス（固定）

```
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault"
```

- 概念ページ: `$VAULT/wiki/concept/<概念名>.md`
- インデックス: `$VAULT/wiki/index.md`
- 構造グラフ: `$VAULT/wiki/graph.jsonld`（symlink → `~/MyAI_Lab/daily-research/graph.jsonld`）
- 原資料: `$VAULT/daily-research/`

> この skill は shimo4228 の個人運用（固定 vault + 自分の研究 repo 群）に紐づく。repo→concept マッピングは skill にハードコードせず、各 repo の CLAUDE.md から読む（下記 Step 1）。

## 制約

- **wiki は read-only**。この skill から vault 内のいかなるファイルにも書き込まない。wiki の更新（ingest / index / log）は vault セッションの `/ingest` の領域。一方向ループ（source → wiki → repo）を保全する。
- **書き込みは repo 内の ledger（+ 初回の `.gitignore` 1 行）のみ**。`.notes/wiki-harvest/ledger.md`（working/non-citable・gitignore 対象）だけを生成・更新する。
- **durable/citable な成果物（`docs/adr/` / `graph.jsonld` / `glossary.md` / `manifesto.md`）には書かない**。それらへの昇格は人間承認の別ステップで、昇格するかは repo author が判断する（durable 成果物は戻しにくい — reversibility gate）。
- **prototype 系候補（`response-type: prototype`）のコード・計器も自動で実装しない**。この skill は候補の抽出と triage までで、計器/spike の実行は人間承認の別ステップ。harvest がやるのは「何を測るべきか」を ledger に書くところまで。
- iCloud dataless プレースホルダに注意: 読んだ concept ページ本文が空なら未ダウンロードの可能性。その旨を報告する。

## 手順

### Step 1 — repo と対象 concept の特定

1. cwd / git remote から現在の研究 repo を判定（`agent-knowledge-cycle` / `agent-attribution-practice` / `contemplative-agent` / `authorship-strategy` 等）。
2. その repo の `CLAUDE.md` 内「Research Wiki Consultation」節を Read し（`contemplative-agent` は節が sibling repo `~/MyAI_Lab/contemplative-agent-rules/CLAUDE.md` にあるので、そちらも見てから欠落と判定する）、`主担当ページ` + `隣接` に挙がっている concept 名を取得する。**マッピングはここ（repo 側）が正本**。skill にハードコードしない。
3. 節が無い repo は fallback（節の有無は `grep 'Research Wiki Consultation' <repo>/CLAUDE.md` で
   毎回確かめる）: `$VAULT/wiki/graph.jsonld` の `track` 値（akc / aap / contemplative / authorship）と repo 名から対象 concept を推定し、**「consultation 節が欠落している」ことを報告**する（後で節を backfill すべき signal）。

### Step 2 — wiki 走査

`$VAULT/wiki/index.md` で対象 concept ページの所在を確認 → 各ページを Read し、以下の5カテゴリを抽出する（この表が還元マップの正本）:

| # | 抽出元（concept ページの節） | 候補の性質 | 次段 |
|---|---|---|---|
| ① | `## オープンクエスチョン` の「ADR 候補」マーク | 決定を要する論点 | → Step 3.5 triage |
| ② | `## 矛盾・論争` | 既存 ADR/claim との突合（stale-doc / conflict check） | → Step 3.5 triage |
| ③ | `## 主要な主張` の外部出典（arXiv/DOI） | 引用辺の追加（機械的） | → `graph.jsonld` / citation |
| ④ | `## 関連概念` リンク | repo graph に無い隣接（機械的） | → `graph.jsonld` |
| ⑤ | `## 主要な主張` の実装・計測に落ちる知見 | prototype 候補（gate/test/計器） | → Step 3.5 triage |

抽出・列挙は機械的に網羅する（enumerate）。採否は次の Step で絞る（decide）。

### Step 3 — signal フィルタ（品質ゲート）

signal フィルタを適用する（正本はこの節）。**各候補は repo の具体的アクションを名指しできなければ捨てる**:

- どの ADR 番号を更新 / 新設するか
- どの graph 辺 / glossary 語 / manifesto 項を足す・解消するか

スコアや grade（「6/10」等）は付けない。**「action を変える具体的観察」**を記す（例:「ADR-0013 の前提を覆す」「graph に [[X]]↔[[Y]] の辺が無い」）。アクションを名指せない一般論・既知事項は ledger に載せない。

### Step 3.5 — response-type triage

signal フィルタを生き残った ①②⑤ の各候補に **response-type** を振る。この表が response-type の正本（判定基準・第一アクション・ADR の位置・昇格先ツール）。
昇格/実行は人間承認後に手動で引き継ぐ。

| response-type | 判定基準 | 第一アクション | ADR の位置（ADR は下した決定の記録で、デフォルトの着地点ではない。終端になるのは `framing` だけ） | 昇格/実行に使うツール（人間承認後・手動） |
|---|---|---|---|---|
| `framing` | 実装コードを伴わない stance/定義の決定（公理の運用定義、主体性の姿勢、接地系統の選択）。「文書化された姿勢そのもの」が成果物 | author が stance を確定 | **終端**（成果物そのもの） | `/adr-writer` skill（主ループが書く。+ 公理なら `contemplative-axioms.md` 脚注） |
| `prototype` | **対象 repo の振る舞いを変える**設計変更（gate / test / verification の追加）。問題が repo 固有に実在するか未測定 | 計器/spike で実在性を先に測る（read-only 計器が第一手） → build 判断 | 判断が出た後に従属記録 | `read-only-instruments` / `replayable-audit-logs`（`~/MyAI_Lab/agent-observability-patterns/skills/`、`~/MyAI_Lab/contemplative-agent/.claude/skills/` にも同梱）、`chaos-tdd-fault-injection`（`~/MyAI_Lab/chaos-tdd-fault-injection/skills/`）— いずれも global library には無い project skill で、`--add-dir` で開いた当該 repo のセッションから使う |
| `defer` | 論点は真だが repo で今 live でない（解のある問題の先取り／repo が採らない外部系との対立） | 再訪トリガーを記録して保留（廃止でなく＝再生成時の重複排除） | 書かない | （ツールなし。ledger に残すだけ） |
| `citation` | ③（機械的） | 一次照合 → citation-sync | 対象外 | `citation-sync` skill（`~/MyAI_Lab/paper-lab` 常駐） |
| `graph-edge` | ④（機械的） | 辺/ノード追加 | 対象外 | `jsonld-knowledge-graph` skill |

判定の 4 問（`architect` agent の build-or-not 判定「複雑性 × 価値 × 使用頻度」を harvest に適用）:

0. **surface-existence check（先に通す dismiss ゲート）** — この候補の元になった外部研究が前提とする surface
   （行動時 retrieval 経路・特定の gate・特定の層）を、repo は**実コードで**持つか？ **wiki concept ページの要約でなく
   repo のコードで照合する**（wiki は repo 内部についても drift する）。前提 surface が無ければ、response-type を振らず
   **dismiss**（前提の無い repo では外部研究の問いが測定不能になる）。
   **`prototype` が共有リソース（store / pool / パイプライン段）を読む・測る場合は、設計前に `grep` で
   そのリソースの *全 reader* をコードで列挙してから軸を決める**（一部の消費者しか数えない計器は嘘の分布を出し、
   「未消費 = dead weight」型の誤った finding を生む）。
1. **これはコードを変えるか、姿勢を書くだけか** — 姿勢だけなら `framing`。
2. **その問題は repo 固有に実在するか、外部研究が言うだけか** — 未測定なら `prototype`（計器で先に測る）。
   repo が採らない設計との対立・低頻度で顕在化しない問題なら `defer`。
3. **「せっかく wiki を調べたから」で成果物を作ろうとしていないか** — サンクコストは判断材料にしない。
   今ゼロから始めるとして、この決定を今優先するか？ No なら `defer`。

ledger の要約で triage 結果を type 別内訳で示す。

### Step 4 — 一次出典への遡行（citation discipline）

カテゴリ③（外部出典）の候補は、concept ページの `## 言及ソース` → `$VAULT/daily-research/YYYY-MM-DD_*.md` → 一次文献（arXiv ID / DOI）まで辿り、**一次 ID を候補に記録**する。

公開成果物には wiki ページや vault パスを引用しない。一次出典まで遡って引く（wiki は二次合成であり drift しうる）。wiki concept ページ・daily-research ノートは **provenance（追跡経路）としてのみ**候補に併記する。

### Step 5 — ledger 生成（two-tier 規律: working tier と durable tier）

working tier = この ledger（`.notes/wiki-harvest/ledger.md`。gitignore・non-citable）、durable tier = 制約節の citable 成果物。
この Step は working tier の `.notes/wiki-harvest/ledger.md` だけを生成 or 追記する。

1. **gitignore 確保**: repo root の `.gitignore` に `.notes/` が無ければ1行追記する（`.gitignore` が無ければ作成）。これで working/non-citable な private ledger を git 追跡から物理的に外す（候補台帳は採否前の作業用であり citable でない）。
2. **冪等性**: 各候補に `status`（new / pending / promoted / dismissed）を持たせる。dedup キー = `concept ページ名 + 節 + claim の安定キー`。再実行時、既 `promoted`/`dismissed` は再浮上させない。`pending` は内容が変化した時のみ更新（重複追記しない）。
3. **response-type 併記（必須）**: 各候補に Step 3.5 の `response-type`（framing / prototype / defer / citation / graph-edge）を持たせ、`アクション` 行はその type の第一アクションを書く。`defer` は再訪トリガーを併記。
4. ranking: signal の強さ（repo アクションへの影響度）で `high` / `med` / `low`。
5. **task 台帳との関係**: この ledger は**候補台帳**であってタスク台帳ではない（rule `common/task-tracking.md` の単一台帳の対象外 — 採否判断前の候補はタスクでない）。候補が `promoted` になり、昇格作業がそのセッション内で完結しない場合は、repo の task 台帳に 1 行立てて引き継ぐ。

完了後、生成した候補の要約（件数・**response-type 別内訳**・high rank の見出し）を chat に返す。承認されたら Step 3.5 の表の「昇格/実行に使うツール」列に従って人間が手動で引き継ぐ。

### Step 6 — 採用ゲート（load-bearing 前の一次照合 / fact-check）

候補の signal は wiki concept ページ・daily-research 経由の **digest 由来（一次未照合）**である。候補を `promoted` にして
**その主張が load-bear する瞬間**（= prototype コードがその論文の機構を前提に組まれる／ADR がその知見に依拠する／
citation を durable artifact に deposit する）**の前に、元の一次文献に対して主張を fact-check する**。抽出段（Step 4）は
一次 ID を*見つける*だけ。この Step 6 はその一次が digest の言う通りの内容かを*確認*する — 別工程。

- **機構・手法の主張**（「論文 X はこういう仕組み」）→ **`fact-checker` agent**（`~/MyAI_Lab/zenn-content` 常駐）に一次（arXiv/DOI）照合を依頼。
- **数値・実証・access-blocked な一次** → **`cited-source-mirror-verification` skill**（③ citation は従来どおりこれ。`~/MyAI_Lab/paper-lab` 常駐）。
- **一次が到達不能**なら claim は `UNVERIFIABLE` のまま。採用するなら durable artifact に「**未照合の前提**」と明記するか、`defer`。

各候補に `一次照合: needed | done(<verdict>) | unverifiable` を持たせ、digest 依存の主張が load-bear する候補は
`一次照合 = done` になるまで `promoted` にしない（または未照合前提を明記して採用）。

## Ledger フォーマット

候補 1 件の例（illustrative。`defer` は `再訪トリガー:` 行を足す）:

```markdown
<!-- working ledger / NOT a citable artifact / gitignored (.notes/)。
     /wiki-harvest が生成・更新。昇格 (ADR/graph 書き込み) は人間承認の別ステップ。 -->
# wiki-harvest ledger: <repo-name>

## [YYYY-MM-DD] harvest | 対象 concept: [[<concept-A>]], [[<concept-B>]]

### 候補A (rank: med, response-type: prototype, status: new) → 計器/spike
- カテゴリ: ⑤ 主要な主張
- 抽出元: [[<concept>]] §主要な主張
- signal: <action を変える具体的観察>
- 一次出典: arXiv:25xx.xxxxx（[[daily-research/YYYY-MM-DD_...]] 経由）
- 一次照合: needed | done(<verdict>) | unverifiable
- アクション: <response-type の第一アクション>（人間承認待ち）
```

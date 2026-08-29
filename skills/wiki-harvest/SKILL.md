---
name: wiki-harvest
description: 研究 repo セッションから LLM wiki (Obsidian Vault wiki/concept/) を read-only で走査し、その repo の主担当 concept ページから「repo の次アクションを変えうる候補」だけを抽出して、一次出典付き・landing slot マップ付きのランク付き候補台帳 (ledger) を repo の .notes/ に生成する。Use when the user invokes /wiki-harvest, asks「wiki から repo に還元して」「wiki の有益分を AKC/AAP/CA/authorship に持ってきて」, or when closing the daily-research→wiki→repo loop. wiki への書き込みは行わない（それは vault セッションの /ingest）。chat 上の自由質問は wiki-query。
user-invocable: true
origin: shimo4228
disable-model-invocation: true
---

# wiki-harvest — LLM wiki から研究 repo への還元

研究 repo セッションで実行し、LLM wiki（Obsidian Vault）の合成知識から **その repo の次アクションを変えうる候補だけ**を抽出して、一次出典付きのランク付き候補台帳（ledger）を repo 内に生成する。

各研究 repo の `CLAUDE.md`「Research Wiki Consultation」節に *passive prose* で書かれている還元マップ（4カテゴリ）を、再現可能な能動手続きに形式化したもの。wiki の合成知識を diff → ランク付き候補 → repo 内 ledger に落とす。daily-research → wiki（合成層）→ repo（昇格）という一方向ループの最終辺を1コマンドで回す。

> 兄弟スキル: `wiki-query` = chat 上の自由 Q&A（良回答は `wiki/concept/` へ書き戻す read-write。2026-08-06 に復活）。`wiki-harvest` = repo 向け定型抽出 → 台帳で、**wiki には書き込まない**。置き換えではない。

## Vault パス（固定）

```
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault"
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
- **prototype 系候補（`response-type: prototype`）のコード・計器も自動で実装しない**。この skill は候補の抽出と triage までで、計器/spike の実行は人間承認の別ステップ。harvest がやるのは「何を測るべきか」を ledger に書くところまで。
- iCloud dataless プレースホルダに注意: 読んだ concept ページ本文が空なら未ダウンロードの可能性。その旨を報告する。

## 手順

### Step 1 — repo と対象 concept の特定

1. cwd / git remote から現在の研究 repo を判定（`agent-knowledge-cycle` / `agent-attribution-practice` / `contemplative-agent` / `authorship-strategy` 等）。
2. その repo の `CLAUDE.md` 内「Research Wiki Consultation」節を Read し、`主担当ページ` + `隣接` に挙がっている concept 名を取得する。**マッピングはここ（repo 側）が正本**。skill にハードコードしない。
3. 節が無い repo は fallback（節を持つ repo のほうが少ない — 実測 2026-08-23 では
   agent-attribution-practice と authorship-strategy のみ。repo 名の列挙はすぐ腐るので
   `grep 'Research Wiki Consultation' <repo>/CLAUDE.md` で毎回確かめる）: `$VAULT/wiki/graph.jsonld` の `track` 値（akc / aap / contemplative / authorship）と repo 名から対象 concept を推定し、**「consultation 節が欠落している」ことを報告**する（後で節を backfill すべき signal）。

### Step 2 — wiki 走査（read-only）

`$VAULT/wiki/index.md` で対象 concept ページの所在を確認 → 各ページを Read し、以下の4カテゴリを抽出する（CLAUDE.md consultation 節の還元マップを正本化）:

| # | 抽出元（concept ページの節） | 候補の性質 | 次段 |
|---|---|---|---|
| ① | `## オープンクエスチョン` の「ADR 候補」マーク | 決定を要する論点 | → Step 3.5 triage |
| ② | `## 矛盾・論争` | 既存 ADR/claim との突合（stale-doc / conflict check） | → Step 3.5 triage |
| ③ | `## 主要な主張` の外部出典（arXiv/DOI） | 引用辺の追加（機械的） | → `graph.jsonld` / citation |
| ④ | `## 関連概念` リンク | repo graph に無い隣接（機械的） | → `graph.jsonld` |
| ⑤ | `## 主要な主張` の実装・計測に落ちる知見 | prototype 候補（gate/test/計器） | → Step 3.5 triage |

> **⑤ を落とすと ADR 節偏重になる**: ①② は「決定を要する論点」＝ ADR/framing になりやすい節、③④ は機械的な引用/辺。だが
> `## 主要な主張` には **build/measure に落ちる signal**（外部研究が実証した機構を repo で計器化・prototype 化できる類）が
> 埋まっている。ここを抽出対象に入れないと skill は構造的に「ADR 化しやすい節」だけを見て prototype 候補を素通りする。

抽出・列挙は機械的に網羅する（enumerate）。採否は次の Step で絞る（decide）。

> **CRITICAL — 「ADR 候補」マークを ADR 直行と読まない**: concept ページの「ADR 候補」は *論点の提起*
> であって *ADR 化の指示ではない*。ADR は「すでに下した決定の記録」であり、決定する装置ではない。
> ①② は必ず Step 3.5 の response-type triage を通す。ここを飛ばすと「研究知見 → ADR の種」が直結し、
> 実装判断を飛ばして成果物を先に作る（調べた労力を回収したくて成果物に走るサンクコスト罠）。

### Step 3 — signal フィルタ（品質ゲート）

output discipline を適用する（正本はこの節 — 旧 `rules/common/akc-cycle.md` の Signal-first 常駐節は [ADR-0026](../../docs/adr/0026-retire-signal-first-residency.md) で退役、原則は本 skill にインライン内在化済み）。**各候補は repo の具体的アクションを名指しできなければ捨てる**:

- どの ADR 番号を更新 / 新設するか
- どの graph 辺 / glossary 語 / manifesto 項を足す・解消するか

スコアや grade（「6/10」等）は付けない。**「action を変える具体的観察」**を記す（例:「ADR-0013 の前提を覆す」「graph に [[X]]↔[[Y]] の辺が無い」）。アクションを名指せない一般論・既知事項は ledger に載せない。

### Step 3.5 — response-type triage（実装判断を ADR より前に置く）

signal フィルタを生き残った ①② の各候補に **response-type** を振る。**ADR はデフォルトの着地点ではない** —
「下した決定の記録」なので、実装を伴う候補では ADR がゴールになってはいけない（まず問題実在性の確認 →
prototype → build 判断、ADR はその後に従属記録）。framing/stance だけの候補のみ ADR が終端。

| response-type | 判定基準 | 第一アクション | ADR の位置 |
|---|---|---|---|
| `framing` | 実装コードを伴わない stance/定義の決定（公理の運用定義、主体性の姿勢、接地系統の選択）。「文書化された姿勢そのもの」が成果物 | author が stance を確定 | **終端**（成果物そのもの） |
| `prototype` | CA の**振る舞いを変える**設計変更（gate / test / verification の追加）。問題が repo 固有に実在するか未測定 | 計器/spike で実在性を先に測る（read-only 計器が第一手） → build 判断 | 判断が出た後に従属記録 |
| `defer` | 論点は真だが repo で今 live でない（解のある問題の先取り／repo が採らない外部系との対立） | 再訪トリガーを記録して保留（廃止でなく＝再生成時の重複排除） | 書かない |
| `citation` | ③（機械的） | 一次照合 → citation-sync | 対象外 |
| `graph-edge` | ④（機械的） | jsonld-knowledge-graph | 対象外 |

判定の 4 問（`architect` agent の build-or-not 判定「複雑性 × 価値 × 使用頻度」を harvest に適用）:

0. **surface-existence check（先に通す dismiss ゲート）** — この候補の元になった外部研究が前提とする surface
   （行動時 retrieval 経路・特定の gate・特定の層）を、repo は**実コードで**持つか？ **wiki concept ページの要約でなく
   repo のコードで照合する**（wiki は repo 内部についても drift する — 実例: 「knowledge 昇格は人間承認」という
   wiki 記述が実際は自動だった）。前提 surface が無ければ、response-type を振らず **dismiss**（外部 framing の空 import。
   実例: memory-pollution 研究は「経験を*行動時に*注入する」agent を前提とするが、対象 repo が pattern を行動時に
   注入していなければ「pollution が行動を害するか」は測定不能 → dismiss）。
   **`prototype` が共有リソース（store / pool / パイプライン段）を読む・測る場合は、設計前にそのリソースの
   *消費者を全部*コードで列挙する**（一部の消費者しか数えないと計器が嘘の分布を出す。実例: pattern pool の消費者を
   distill-identity / amend だけ数えて **insight のクラスタリング消費を漏らし**、「未消費 = dead weight」の誤った
   finding と無意味なクロス集計を生んで実装後に revert した — `grep` で `get_live_patterns` / 対象 store の全 reader を
   洗ってから軸を決める）。
1. **これはコードを変えるか、姿勢を書くだけか** — 姿勢だけなら `framing`（ADR 終端で正しい）。
2. **その問題は repo 固有に実在するか、外部研究が言うだけか** — 未測定なら `prototype`（計器で先に測る、
   ADR/実装はその後）。repo が採らない設計との対立・低頻度で顕在化しない問題なら `defer`。
3. **「せっかく wiki を調べたから」で ADR 化しようとしていないか** — サンクコストは判断材料にしない。
   今ゼロから始めるとして、この決定を今優先するか？ No なら `defer`。

triage しない（＝ ①② を全部 ADR 候補として起こす）と、`defer`/`prototype` 相当の候補が **偽の ADR タスク**
として量産される。ledger の要約でこの triage 結果を必ず示す（type 別内訳）。

### Step 4 — 一次出典への遡行（citation discipline）

カテゴリ③（外部出典）の候補は、concept ページの `## 言及ソース` → `$VAULT/daily-research/YYYY-MM-DD_*.md` → 一次文献（arXiv ID / DOI）まで辿り、**一次 ID を候補に記録**する。

既存ルール厳守: 公開成果物には wiki ページや vault パスを引用しない。一次出典まで遡って引く（wiki は二次合成であり drift しうる）。wiki concept ページ・daily-research ノートは **provenance（追跡経路）としてのみ**候補に併記する。

### Step 5 — ledger 生成（two-tier 規律）

`.notes/wiki-harvest/ledger.md` を生成 or 追記する。

1. **gitignore 確保**: repo root の `.gitignore` に `.notes/` が無ければ1行追記する（`.gitignore` が無ければ作成）。これで working/non-citable な private ledger を git 追跡から物理的に外す（候補台帳は採否前の作業用であり citable でない）。
2. **冪等性**: 各候補に `status`（new / pending / promoted / dismissed）を持たせる。dedup キー = `concept ページ名 + 節 + claim の安定キー`。再実行時、既 `promoted`/`dismissed` は再浮上させない。`pending` は内容が変化した時のみ更新（重複追記しない）。
3. **response-type 併記（必須）**: 各候補に Step 3.5 の `response-type`（framing / prototype / defer / citation / graph-edge）を持たせ、`アクション` 行はその type の第一アクションを書く（`framing` 以外は ADR を第一アクションにしない）。`defer` は再訪トリガーを併記。
4. ranking: signal の強さ（repo アクションへの影響度）で `high` / `med` / `low`。
5. **task 台帳との関係**: この ledger は**候補台帳**であってタスク台帳ではない（rule `common/task-tracking.md` の単一台帳の対象外 — 採否判断前の候補はタスクでない）。候補が `promoted` になり、昇格作業がそのセッション内で完結しない場合は、repo の task 台帳に 1 行立てて引き継ぐ。

完了後、生成した候補の要約（件数・**response-type 別内訳**・high rank の見出し）を chat に返す。**ADR/graph への昇格も prototype の着手も提案に留め、自動で書かない・自動で実装しない**。承認されたら `framing` は `adr-writer`、`prototype` は計器/spike の実行（read-only 計器が第一手）、③④ は `citation-sync`（`~/MyAI_Lab/paper-lab` 常駐、2026-08-29 移設） / `jsonld-knowledge-graph` に人間が手動で引き継ぐ。

### Step 6 — 採用ゲート（load-bearing 前の一次照合 / fact-check）

候補の signal は wiki concept ページ・daily-research 経由の **digest 由来（一次未照合）**である。候補を `promoted` にして
**その主張が load-bear する瞬間**（= prototype コードがその論文の機構を前提に組まれる／ADR がその知見に依拠する／
citation を durable artifact に deposit する）**の前に、元の一次文献に対して主張を fact-check する**。抽出段（Step 4）は
一次 ID を*見つける*だけ。この Step 6 はその一次が digest の言う通りの内容かを*確認*する — 別工程。

- **機構・手法の主張**（「論文 X はこういう仕組み」）→ **`fact-checker` agent**（`~/MyAI_Lab/zenn-content` 常駐、2026-08-29 移設）に一次（arXiv/DOI）照合を依頼。
- **数値・実証・access-blocked な一次** → **`cited-source-mirror-verification` skill**（③ citation は従来どおりこれ。`~/MyAI_Lab/paper-lab` 常駐、2026-08-29 移設）。
- **一次が到達不能**なら claim は `UNVERIFIABLE` のまま。採用するなら durable artifact に「**未照合の前提**」と明記するか、`defer`。

**なぜ（この Step が防ぐ具体的失敗）**: digest は論文の手法を reframe しうる。prototype を「論文 X は Surprise×Utility
ゲートを使う」という digest 記述の上に組んだのに、その前提を一次で確認せず、後から食い違いが露見する—という順序ミスを防ぐ。
**fact-check は load-bearing 採用の *前*に置く。後追いにしない。** surface-existence check（Step 3.5 #0、repo コードで照合）が
「repo がその surface を持つか」を見るのと対に、Step 6 は「一次がその主張を支持するか」を見る。

各候補に `一次照合: needed | done(<verdict>) | unverifiable` を持たせ、digest 依存の主張が load-bear する候補は
`一次照合 = done` になるまで `promoted` にしない（または未照合前提を明記して採用）。

## Ledger フォーマット

```markdown
<!-- working ledger / NOT a citable artifact / gitignored (.notes/)。
     /wiki-harvest が生成・更新。昇格 (ADR/graph 書き込み) は人間承認の別ステップ。 -->
# wiki-harvest ledger: <repo-name>

## [YYYY-MM-DD] harvest | 対象 concept: [[<concept-A>]], [[<concept-B>]]

### 候補A (rank: high, response-type: framing, status: new) → docs/adr/（終端）
- カテゴリ: ① OQ「ADR 候補」
- 抽出元: [[<concept>]] §オープンクエスチョン
- signal: <実装コード無しの stance/定義の決定。例「主体性の姿勢を ADR に明記」>
- 一次出典: arXiv:25xx.xxxxx（[[daily-research/YYYY-MM-DD_...]] 経由）
- アクション: author が stance を確定 → adr-writer（人間承認待ち）

### 候補B (rank: med, response-type: prototype, status: new) → 計器/spike → ADR は判断後
- カテゴリ: ① OQ「ADR 候補」
- signal: <CA の振る舞いを変える設計変更。問題実在性が未測定。例「distill 汚染が CA で起きるか未測定」>
- アクション: prototype 先行 — read-only 計器で実在性を 1 サイクル測る → 実在すれば設計 + ADR（人間承認待ち）

### 候補C (rank: low, response-type: defer, status: new) → 保留（再訪トリガー付き）
- カテゴリ: ② 矛盾・論争
- signal: <論点は真だが repo で今 live でない理由>
- 再訪トリガー: <この条件が満たされたら再訪>
- アクション: defer（廃止でなく保留＝再生成時の重複排除）

### 候補D (rank: med, response-type: citation, status: pending) → graph.jsonld / .zenodo.json
- カテゴリ: ③ 外部出典 / ④ 関連概念辺
- アクション: 一次照合 → citation-sync（機械的・人間承認待ち）
```

## 還元先と昇格の引き継ぎ先（response-type 別 早見表）

**ADR は「決定を下した後の記録」**。①② は Step 3.5 の triage を経て response-type が決まり、着地点が分かれる。
ADR に直行するのは `framing`（実装を伴わない stance/定義の決定）だけ。

| response-type | 第一アクション | 昇格/実行に使うツール（人間承認後・手動） |
|---|---|---|
| `framing` | author が stance 確定 → **ADR 終端** | `adr-writer` agent / `/adr-writer` skill（+ 公理なら `contemplative-axioms.md` 脚注） |
| `prototype` | read-only 計器/spike で実在性を測る → build 判断 | `read-only-instruments` / `replayable-audit-logs` / `chaos-tdd-fault-injection` 系。実在確定後に ADR は従属記録 |
| `defer` | 再訪トリガーを記録して保留 | （ツールなし。ledger に残すだけ） |
| ③ `citation` | 一次照合 → 下層から同期 | `citation-sync` skill |
| ④ `graph-edge` | 辺/ノード追加 | `jsonld-knowledge-graph` skill |

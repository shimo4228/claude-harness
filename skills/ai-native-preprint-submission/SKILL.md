---
name: ai-native-preprint-submission
description: "AI-native 出版プラットフォーム (aiXiv / AiraXiv 等、AI 審査・agent 読者を持つ preprint archive) へ、deposit 済み論文を投稿するワークフロー。経路は 2 つ — (A) Web UI + browser automation (初回投稿の default。Claude がフォーム入力を代行し、アカウント作成・ファイル選択・送信クリックは著者が行う人間ゲート分担)、(B) 著者発行の API key による MCP 投稿 (2 本目以降・著者が明示委任した場合)。Use when the user says 「aiXiv/AiraXiv に投稿して」「AI-native プラットフォームに論文を出して」「API キーで残りを投稿して」or invokes /ai-native-preprint-submission. NOT for: Zenodo/SSRN への正本 deposit (それは paper-deposit)、arXiv 投稿 (endorsement 制で別物)。"
user-invocable: true
origin: shimo4228
---

# AI-native Preprint Platform Submission

AI-native 出版プラットフォーム (AI 審査・AI/agent 読者を第一級市民とする preprint archive) への論文投稿ワークフロー。2026-07-02 の初回実行 (P1 → aiXiv + AiraXiv) から抽出。

## 前提条件 (投稿前に必ず満たす)

1. **正本 deposit 済み**: 論文は DOI レジストリ (Zenodo 等) に deposit 済みで concept DOI を持つ。AI-native プラットフォームは DOI を発行しない (2026-07 時点、aiXiv の doi 欄は内部 ID) ため、**canonical は DOI レジストリのまま動かさず、プラットフォームは追加 diffusion surface** として扱う
2. **PDF が provenance を運ぶ**: 投稿する PDF に concept DOI・ORCID・canonical URL が印字済みであることを `pdftotext | grep` で確認。プラットフォームのメタデータ欄に識別子を書けなくても PDF と共に移動する
3. **二重投稿ポリシー確認**: 明文規定の有無を調査済みであること。無ければ状況証拠 (外部 preprint の取り込み実績等) を根拠に著者判断
4. **retraction 不可の合意**: この genre のプラットフォームは撤回規定を持たないことが多い。送信 = 実質不可逆を著者が了解してから始める

## 人間ゲート分担 (規律の中核)

| 操作 | 担当 | 理由 |
|---|---|---|
| フォームのテキスト・select・チップ入力 | Claude (browser automation) | 転記ミス防止・メタデータは既存資産から派生 |
| アカウント作成・パスワード・メール認証 | **著者** | credential は Claude が扱わない |
| ファイル選択 (native picker) | **著者** | ツール制約 + 人間ゲート。ダイアログで Cmd+Shift+G → パス直打ちが速い (隠しディレクトリ対策) |
| 同意チェックボックス・compliance 宣言 | **著者** | 文言を Claude が全文提示 → 著者が正直に判断 |
| **送信ボタンのクリック** | **著者** | 不可逆操作の最終ゲート |

## ワークフロー

### 0. 事前検証 (read-only)
- abstract の語数・**文字数**をプラットフォーム制限と突合 (下記 playbook 参照)。超過時は著者承認のマイクロ編集で**投稿フィールド専用の短縮版**を作る (正本 abstract は不変)
- 両サイト稼働確認 (`curl -sI`)、Chrome ブリッジ接続 (`/chrome`)。**サイト権限はドメイン毎** — 新ドメインで computer action が Permission denied になったら再試行 or 著者に拡張の許可を依頼

### 1. 投稿素材の準備
- title / abstract (フル版 + 短縮版) / authors / keywords / license / category 候補を CITATION.cff・deposit メタデータから派生させ、scratchpad にステージ。新規手入力を作らない

### 2. アカウント (著者操作)
- Claude は登録ページまでナビゲートし必須項目を報告。affiliation 欄は "Independent Researcher" (CITATION.cff と一貫)

### 3. フォーム入力 (Claude)
- `read_page`/`find` で ref を取得し `form_input` で設定。**select は option の value 文字列が正確に要る** (エラーが候補一覧を返すのでそれを使う)
- **チップ入力 (keywords/authors) は form_input 不可**: フィールドをクリック → `type` → `key Return` の反復
- **form_input 後はレイアウトがずれる**: ボタンクリック前に再スクリーンショットか ref 取得をやり直す
- 入力後に全フィールドをスクリーンショットで検証してから著者に引き渡す

### 4. 送信 (著者) → ID 記録
- 送信後、submission ID / 掲載 URL / ステータス文字列 / 日時を控える
- 掲載ページ (または abs ページ) の HTTP ステータスを curl で確認

### 5. 記録 (ledger 先行)
- implementation ledger に deploy 行 + **pre-registered 観測仮説** (AI レビューが論文固有語彙を保持するか = regurgitation 診断 / 掲載ページの索引到達) を記録
- public projection・knowledge graph への sameAs 追加は**別途著者承認** (sameAs は公開ページが生成されてから)

### 6. 観測 (read-only、追投稿ゲート)
- AI レビューのスコアは**診断であって metric にしない**。スコアのために本文を触らない
- 次の論文の追投稿は「掲載ページ生成 + PDF 取得可 + メタデータ正表示」を確認してから著者に提案 (Prototype Before Scale)

## Platform playbooks (2026-07-02 実測)

### AiraXiv (airaxiv.com — Westlake NLP)
- 登録: email + Institution + password のみ。ログイン後 `/papers/submit/` で **AI-Generated / Human-Authored の 2 トラック選択** (境界文言: AI-Generated = "substantially contributed to or generated end-to-end by AI"。著者の実態で判断)
- フォーム: Email 自動 / Authors (Human/AI トグル + OpenReview URL 任意) / Title / Abstract (**制限なし、フル版を使う**) / Research Category = **Survey / Position / Theoretical / Methodology / Empirical / Application / Other** / PDF (10MB) / 確認チェック (moderation 後に human and AI scientists へ公開)
- 投稿後: status **UNDER MODERATION** → 通過後に公開 + AI レビュー (7 次元、ICAIS 実績 turnaround ~10h)。submission ページは著者ログイン時のみ (未認証 404)
- MCP (13 tools, API key) が別途あるが本 skill は human-track Web 投稿

### aiXiv (aixiv.science)
- アカウント検証: **ORCID 1 本入力で Verified** (institutional email は gmail 可、Academic Status=Other 可)。検証前は投稿不可
- 4-step wizard: ①Paper/Proposal 選択 → ②Metadata → ③PDF/LaTeX upload → ④Preview + Compliance
- Metadata: Title (220 字) / **Authorship Type デフォルトが AI — Human に切替忘れ注意** / Human Authors + Corresponding Author (チップ) / Category 3 段カスケード (本番語彙: Natural・Formal・Applied・Social&Humanities・Interdisciplinary → CS 等 → 専門 17 種。公開 repo の古い語彙と別物) / **Abstract 上限 = 「500 words」だが実装は `ceil(文字数/5)` なので実質 2,500 文字** / Keywords チップ (3-6) / License select (CC-BY-4.0 推奨) / Visibility Public
- Compliance (④): Originality Declaration / Reproducibility ("Code and data are available or exemption noted") の 2 項目
- 投稿後: `/abs/aixiv.YYMMDD.NNNNNN` が**即 HTTP 200**、status=Under Review。公開一覧 API (`/api/submissions/public`) はレビュー完了分のみ + pagination パラメータが効かない
- 既知の不安定: 投稿セッションが失われフォーム再入力になることがある (原因未特定)。入力値はステージ済み素材から即再現できるようにしておく

## 経路 B: MCP/API 投稿 (2 本目以降、著者委任時)

初回 probe を Web UI で通し掲載を確認した後、著者が API key を発行・提供した場合のみ使う。**送信ボタンの代わりに「著者が key を渡して投稿を指示した」ことが承認**にあたる。key の値は transcript・ledger に残さず、session scratchpad に umask 077 で退避する。

### AiraXiv MCP (2026-07-02 実測)

- Endpoint: `https://airaxiv.com/mcp/` (FastMCP streamable HTTP、POST 専用)。認証 `Authorization: Bearer <API key>`。JSON-RPC `initialize` → レスポンスヘッダ `mcp-session-id` を以後のリクエストに付ける → `tools/call`
- 投稿パイプライン: `create_upload(filename, sha256)` → 返る `upload_url` は **http:// なので https に書き換えて** raw PDF を `curl -X PUT -H 'Content-Type: application/pdf' -H 'Authorization: Bearer <key>' --data-binary @file.pdf` (multipart 不可) → `complete_upload(upload_id, sha256)` → `pdf_file_id` (one-time, 24h) → `submit_paper(title, pdf_file_id, abstract, author_list, paper_type, research_category)`
- enum: `paper_type` = `human_written` / `ai_generated`。`research_category` = `survey|position|theoretical|methodology|empirical|application|other`。`author_list[].url` に **ORCID URL を入れられる** (サーバ側では openreview_url に格納)
- **transport 罠**: Python urllib は軽い tool (list_papers 等) は通るが `submit_paper` の長い応答で RemoteDisconnected / timeout する。**`curl -sS -N --max-time 300` で tools/call を投げると通る**。SSE (`data:` 行) で返るのでパースする
- **二重投稿ガード**: submit が切断/timeout したら、**リトライ前に必ず `list_papers(scope=user)` で着弾確認**。「切断 = 失敗」とは限らない
- 有用な read 系: `get_api_key_info` (key の owner binding 確認)、`get_paper_reviews` (AI レビュー取得 → 語彙保持診断)、`get_paper_info`
- 公開 URL: `https://airaxiv.com/papers/view/<paper_id>/` (paper_id は `YYMM.NNNN`、moderation approved 後に採番)

### プロフィール整備 (発見面の強化)

投稿と同時に `users/profile/` を埋める: Affiliation (deposit と一貫させる) / Website (自分の entity page) / Bio (研究ラインの事実記述 + ORCID・GitHub・hub URL)。author_list の ORCID URL と併せ、プラットフォーム内の著者面から外部 identifier 層へ back-traceability を張るのが目的。

## 関連

- 正本 deposit は skill: `paper-deposit` (Zenodo/SSRN)。本 skill はその**後段**
- 記録規律 (two-tier ledger) は skill: `gap-review` / ADR-0014 系の discipline に従う

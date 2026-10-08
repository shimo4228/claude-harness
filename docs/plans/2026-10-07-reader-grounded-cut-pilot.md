kind: external
# 読者を宣言した「cut-only」pass は、著者自身の skipped / unnecessary 印と一致するか — 5〜10 本の過去 README / Zenn 記事での pilot に効く外部知見

as-of 2026-10-07。5 本の notes（reader-specification / subtraction-pass / verbosity-causes / craft-tradition / adversarial、`~/.cache/claude-research-notes/2026-10-07-reader-grounded-subtraction/`）を統合し、lead が 2026-10-07 に arXiv abstract page を直接読んで確認した 2 件を反映した。notes に無い主張は足していない。

読み深さの凡例: 全文 = 本文を読んだ / 要旨 = abstract page / snippet = 検索結果の文面のみ / 二次資料 = 要約ページ経由。notes の WebFetch は小型 summarizer 経由のため、「全文」でも引用は byte 照合していない。数値は ADR / plan に入れる前に原典で再確認する。

## Scope searched

- 範囲: 読者の伝え方（persona / evidence / 構造的制限）、cut-only pass の先行実装、LLM の冗長性の原因と vendor 指針、craft 伝統（Pinker / Vonnegut / King / Bell / Hemingway / Nielsen）、反証（低知識読者・caveat 欠落・over-credit・Goodhart）。5 角度で合計約 100 回の WebSearch / WebFetch（各 14〜27 回。目安 10〜15 を超過。理由は summarizer 出力しか返らない fetch の読み直し）。
- lead による一次確認（2026-10-07、arXiv abstract page を直接読んだ）: 2608.30033、2607.28887。
- harness 内部の実測（本 session で lead が計測、内部データ）: 3 節の末尾。
- 見つからなかったもの（不在の証明ではなく検索範囲の限界）:
  - 「宣言した読者」を証拠として渡し、文単位で「その読者が同じ理解・行動に至るか」を試す公開 skill / tool。
  - SKILL.md 型 cut pass の before/after（長さ + 理解）の実測。
  - 「persona 記述」対「読者自身の語・履歴」を、冗長性 / 読者較正で直接比べた研究。
  - LLM 読者モデルの cut 判定と実読者の skip 印の一致を調べた研究。
  - 日本語・Zenn 体裁の結果。Claude 5 系の日本語長文の冗長性測定。
  - 糸井重里 / 古賀史健 / 谷山雅計の一次テキスト。Strunk Rule 13（bartleby 403）。McNamara 1996 / Kalyuga の本文。BMAD editorial-review の raw SKILL.md（v6.11 で `bmad-review` lens の shim 化）。

## Found

### 内部データ（前提。外部調査ではない）

- zenn-content の disposition record 3 件で、適用された review 指摘は ADD:CUT ≈ 2.4:1。
- finding 適用 commit 11 件中 10 件が文字数増（中央値 +348 字）。
- `~/.claude/skills/readme-writer/evals/read-through-log.md` は誤り件数のみを記録し、直近 4 件が 0。「skipped / unnecessary」列が無い。つまり現状は付加方向の偏りが測れ、削除方向の usage data が存在しない。

### (1) 読者の伝え方: persona / evidence / 構造的制限

**1-a. persona は読者の知識を制限できない（最も強い根拠）**
- Balog & Bakken, "'Act Like a 5th Grader' is Not Enough: Bounding Knowledge in LLM-Based User Simulators", arXiv 2608.30033（2026-08-30 submit、要旨を lead が直接確認 2026-10-07）。
  - 小学 4〜6 年生 2,359 人・71,000 超の読解回答に対し、persona prompting は決定論的にほぼ完全な成績（"superhuman bias"）を出す。
  - 対処は構造的な制限で、CBUS（episodic bottleneck で作業記憶を制限する）。
  - 訂正: reader-specification / adversarial notes の「task-relevant evidence を渡す knowledge bounding through evidence が効く」は要旨で支持されない（summarizer 由来の不確かな記述）。採用してよい主張は「persona のみでは不十分」「シミュレータが参照・保持できるものをアーキテクチャで狭めると gap が縮む」まで。
  - 移せる部分: 読者を persona 文で宣言するだけでは cut 判定が over-credit になる前提で pilot を組む。context-starve（本文以外を渡さない）は構造的制限の一種として位置づけられるが、本文自体が語彙を含むため、読者が「知らない」状態は作れない（adversarial A5 の推論。論文の主張ではない）。

**1-b. persona 系の周辺根拠（いずれも直接の読者較正ではない）**
- Wharton GAIL "Playing Pretend: Expert Personas Don't Improve Factual Accuracy"（Basil et al., 2025-12、snippet）: expert persona は GPQA Diamond / MMLU-Pro で無 persona に勝たず、layperson / child 等の低知識 persona はしばしば精度を下げる。反論 arXiv 2603.20225（Mullens & Shen、設計欠陥の指摘で再現ではない、要旨）。応答側 persona の精度の話であり、読者側 persona と文長ではない。
- CoMPosT（EMNLP 2023、snippet）: persona simulation は caricature（個別性が低く誇張）。社会集団 persona の話。
- arXiv 2602.18462（snippet）: World Values Survey で persona 条件づけは集計上の明確な利得なし、しばしば悪化。arXiv 2309.10433（2023、snippet）: 作者定義の audience persona のフィードバックは「冗長で非特異」になりがち。
- Hooshyar et al., arXiv 2512.23036（要旨）: LLM は学習者の習熟状態を時系列で一貫して更新できない（DKT AUC 0.83、fine-tuned LLM は 6% 低い）。「読者が既に知っていること」は明示しないと推論されない、という設計上の示唆（書くことの研究ではない）。
- Common-ToM arXiv 2403.02451（snippet）: 信念を明示表現にすると ToM 性能が上がる。「読者が知っていること / 読んだもの」を明示リストで渡す設計の示唆（snippet のみ）。

**1-c. evidence（本人の語・履歴）で条件づけると近い人物を再現できる、が書き方の較正には未検証**
- Park et al., "Generative Agent Simulations of 1,000 People", arXiv 2411.10109（要旨、summarizer 抽出）: 1,052 人。interview 逐語 83% / survey 82% / 併用 86% / demographics のみ 74%（本人の test-retest で正規化）。回答予測であり散文ではない。demographics は薄い属性リストで persona 文の対照ではなく、interview 条件は情報量も多い（「evidence か description か」と「情報量」が交絡）。
- "Catch Me If You Can? Not Yet"（EMNLP Findings 2025、arXiv 2509.14543、HTML を summarizer 経由＋snippet）: 6 LLM・400+ 著者・各 40,000+ 生成。5-shot は 0-shot に全指標で勝つ。2〜10 例で飽和。news / email は 5-shot AV 95% 超、blog / forum は AV 約 17-21%。style 記述条件は未検証なので「exemplar > 無し」であり「exemplar > 記述」ではない。自動指標のみ・英語。Zenn は blog に近く、不利な側。
- LongLaMP arXiv 2407.11016（snippet）: user history 検索で ROUGE-1 約 +30.2%、ROUGE-L 約 +47.5%。ただし著者側 history による style 一致で、読者の既知の較正ではない（軸が違う）。

**1-d. 反対側: 派生した記述は raw 履歴に匹敵する**
- Richardson et al., arXiv 2310.20081（2023-10、要旨、summarizer 経由）: LaMP で task-aware の LLM 要約が検索データ 75% 減で同等以上。6 タスク中 5 で同等以上、2 で厳密に上。形式（記述 vs raw）より「ユーザの実データから導出された記述」であることが効く可能性（第 3 の腕）。タスクは分類・見出し・短文。文長は未検証。2023 年で古い。

**1-e. 状態**
- Claude Styles（vendor blog＋二次記事）は「文例のアップロード」か「記述」の 2 経路。計測なし、かつ著者の声であって読者ではない。reader を history / evidence として冗長性制御に使う practitioner write-up は見つからなかった。
- haowjy `llm-writing` skill（2026-07-09 更新、全文 mirror 経由）: 先に「読者は開始時に何を知り、終了時に何を知るべきか」を問い、beat に分けて LLM 定型句を削る。読者を person でなく知識状態として書く点が設計に最も近い（実測なし）。

### (2) cut-only pass の設計部品（借りられるもの）

**2-a. petar-djukic/writing-skills `tighten-style`**（`.agents/skills/tighten-style/SKILL.md`、summarizer 経由）
- 決定的 checker が規則違反（無駄語・強調語・hedge の積み重ね・名詞化）を出し、tightener は**別 model family** に instead→do の対（「規則の散文は渡さない」）で書き直させる。match-voice の verify 段、register marker 検査（passive / agentive / 名詞化 / 接続詞のシフト）で締める。
- 不変条件: 引用・規範要件・citation・数値は触らない。
- 停止規則: 「対象 register 自身の密度で止まる。Shorter is not the target」。既定の floor は著者自身の散文密度。
- 差: floor は著者密度（スタイル基準）で、宣言した読者の必要ではない。edit は書き直しで削除でない。読者がループに居ない。実測値なし。
- 移せる部分: (a) 別 model family（著者側 model が必要と思う箇所と脱相関）、(b) 不変条件リスト、(c) 非長さの停止規則。floor を「deletion test で落ちない箇所」へ置き換える案（subtraction-pass の提案）。
- 補強: arXiv 2607.22653（2026-07、snippet）— 自己改稿を繰り返すと model 選好の不動点に収束し edit が減衰。同一 model の改稿ループは信号を足さない示唆。

**2-b. BMAD-METHOD `bmad-editorial-review-structure` / `-prose`**（claudemarketplaces.com の page を summarizer 経由、snippet 級。raw 未読。v6.11 で shim 化）
- structure pass の判定語彙: CUT / MERGE / MOVE / CONDENSE / QUESTION / PRESERVE。`reader_type = humans | llm`（humans は例と視覚的余白を保つ、llm は精度最適化）。purpose と target audience を取り、無ければ推論。prose pass は理解阻害のみ（文体は対象外）、Original / Revised / Changes の表。
- 差: 読者は 2 値 enum で証拠ではない。判定単位は section で文でない。実測なし。
- 移せる部分: 6 動詞語彙と、明示的な PRESERVE（deletion test の「残す」側の判定）。cut を polish より先に行う順序。

**2-c. 他 skill（実装の型）**
- blader/humanizer（RAW-ish）: 事実・名前・数値・日付・引用・citation を変えない不変条件、「run-up は tone でなく文ごと切る」。パターン基準で読者基準でない。25.2k stars（採用実績のみ）。
- petergyang/no-ai-slop（2026-07、summarizer 経由）: 「minimum effective edit」と「What changed」ログ。CUT:ADD 比を監査できる。読者は「不明なら 1 問尋ねる」だけ。eval.md は 404 で未読。
- 他（strunkify, writing-clearly-and-concisely, dangeles/claude editor, Simon Willison omit-needless-words）は snippet のみ未読。いずれも規則 catalog、自己 review は著者 context 内で、宣言読者を削除基準にするものは無い。

**2-d. 削除回避と、測定の補助**
- "To Add Is Machine, To Delete Is Human: Measuring and Mitigating Deletion Avoidance in LLM Code Editing", arXiv 2607.28887（2026-07-30 submit、要旨を lead が直接確認）: 削除 recall ≤71.7%、行の正確な削除 52%、Guard-and-Go 29.0%、CanItDelete は 200 タスク、削除テストを厳しくすると pass rate 63.2%→41.9%。code 領域（tests が oracle）。示唆: (i) cut pass は長さだけでなく削除 recall で採点する、(ii) 「削除でなく hedge / 限定で包む」の散文版が出ていないか出力で確認する（推測であって論文の主張ではない）。
- "More is More: Addition Bias in LLMs", arXiv 2409.02569（2024-09、要旨）: 追加偏重は model の性質で、プロンプトの「削れ」併記では直りにくい。cut-only pass は追加の選択肢を物理的に消す。小型・旧世代・おもちゃタスク。harness の ADD:CUT ≈ 2.4:1 と整合する独立 base rate。
- ConCISE, arXiv 2511.16846（v2 2026-03-12、summarizer 経由）: 参照無し簡潔性。word-removal 圧縮率＋意味保持の LLM 判定。著者自身の limitation が「非必須の定義は domain で変わる」で、読者依存の仮説を支持する。Likert 相関 0.628 は弱い。長さ非依存の冗長性スコアとして pilot の補助指標に使える。
- 文単位の ablation の鋳型: Thought Anchors arXiv 2506.19143（snippet、100 rollouts で高価）。pilot では 1 回の leave-one-out で代替する案。arXiv 2605.29000（要旨）: 復元可能なものは冗長という考えは同型だが、測るのは復元性であって読者の判断関連性でない。

### (3) pilot が測るべき危険

**3-a. 低知識読者では cohesion が削られる（符号反転）**
- McNamara 1996 / Graesser & McNamara 2011（Frontiers 2020 の引用経由、snippet のみ）: 低知識読者は明示的な接続語と指示語の反復（高 cohesion）で伸び、高知識読者は低 cohesion で深く処理する（reverse cohesion effect）。Kalyuga の expertise reversal effect（Wikipedia と Kalyuga 2007 PDF、snippet のみ）: redundancy principle は専門家向けで、初心者では追加説明が保持と転移を上げ、専門家で逆転する。教材・図表中心で README 散文ではない。
- pilot への含意: 宣言する読者の「知識水準」が cut の符号を決める。役割だけでなく、読んだもの・知っている語を宣言する。cut された文のうち「接続・橋渡し」型と「冗長」型を分けて数える。cut pass は両者を区別できない（adversarial の推論）。
- 追補（二次資料）: Newton の tapping 実験 — 打ち手の予測 50% に対し聞き手は 2.5%（secretGeek COIK ページ経由、原典未読）。社内語彙（ADR / harness / scaffold / judge-tier）は「平文に隠れた jargon」。列挙できる語は grep で拾え、列挙できないものは cold reader が要る。

**3-b. caveat・否定・数値の欠落**
- Peters & Chin-Yee 2025, Royal Society Open Science（PMC12042776、arXiv 2504.00025、全文を summarizer 経由）: 4,900 要約・10 model。過汎化は ChatGPT-4o 45-60%、LLaMA 3.3 70B 69-73%、DeepSeek 26-67%、人間要約比 OR 4.85（95% CI 3.06-7.70）。「正確に」と頼むと過汎化は約 2 倍。temperature 0 で 76% 減。典型は数量化主張の一般化、過去形→現在形。**Claude 系は原文と有意差なし**（Claude 3.7 Sonnet 含む）。医学中心（200 抄録中 100）、書き直し型で cut-only は未検証。
- pilot への含意: cut-only は tense / generic 化を避けるが、caveat 文そのものを消し得る。reader の次の行動に影響しない caveat は「不要」と判定されやすい。保護クラス（限定・数値・scope 限定・否定: 「〜でない」「〜のときだけ」）を設け、cut 前後の数値・否定語の個数を機械 diff で数える。
- 補強: Agrawal & Carpuat（4-b）の削除による理解低下。blader/humanizer と tighten-style の不変条件を流用できる。

**3-c. simulated reader の過大評価（over-credit → over-cut）**
- 2608.30033 は 1-a のとおり。
- "LLMs as Students Who Think Aloud: Overly Coherent, Verbose, and Confident", arXiv 2602.01015（summarizer 水準）: 模擬 novice は実際より整合的・冗長・自信過剰で、迷いと誤概念が無い。
- arXiv 2602.00459（snippet、fetch 失敗）: LLM の内部 salience は人間判断と弱相関で内省で取り出せない。
- 方向: 読者モデルが「自分で補える」と見積もり、deletion test が通りすぎる（false unnecessary）。cut pass の自己申告と著者の skip 印を食い違いの方向別に集計する（cut したが著者は読んだ / 残したが著者は skip）。over-cut 側の誤りを先に見る。
- 追補: Melumad & Yun 2025, PNAS Nexus（snippet、10,462 人・7 実験）: 事実が同一でも LLM 合成から学ぶと web 検索リンクより浅い知識になる。「同じ次の行動に至る」だけでは理解の深さの低下を見逃す。記事（Zenn）は README より理解が目的のため cut の危険が大きい可能性。

**3-d. 長さを指標にする Goodhart**
- 長さ削減のみを成功とすると過剰削除を報いる。「Shorter is not the target」（tighten-style）。King の「2 稿 = 1 稿 − 10%」（二次資料）は人間用の予算で LLM 出力では未検証。
- 判定側の長さ bias: arXiv 2604.23178（2026-04、要旨）— 5 judge で verbosity bias は不均一（Pro / Flash / Llama は長文を好み、Claude は短文を好み、GPT-4o は中立）。markdown など style / format の bias の方が大きい（効果量 0.10-0.76）。arXiv 2606.19544（2026-06、要旨）— 21 judge・約 541k 判定で verbosity bias は単一 pairwise rubric 下で 0.011 未満（rubric 限定の注意書き付き）。arXiv 2606.01629（snippet）— 長文 judge は最も未検証。いずれも文単位の necessity 判定ではなく全体応答比較。pilot の指標は長さ前後と著者印にとどめ、LLM 採点を指標にしない。
- 長さ以外に測る案（adversarial B1 の提案）: 主張が冒頭 3 行に在るか、著者の最初の skip 印が文書のどの位置か。冒頭に近い skip は失敗、末尾に近い skip は layered なら無害。
- 代替の枠組み: Nielsen, progressive disclosure（2006-12、全文）— 重要な少数を先に示し、専門的なものは要求時に出す。split が正しいことが条件で、split は usage data で決める。2 階層超は usability が低い。cut でなく「降格」。README = 第 1 層＋リンク。複数読者を残したまま順序で捌く。誤削除の被害も小さい（検索範囲では制御実験なし）。

### (4) 冗長性の原因と vendor 指針

**4-a. Anthropic 公式（全文、2026-10-07 取得）**
- Prompting Claude Opus 5（platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5）: 既定の応答は先代 Opus より長い。effort は「考える量」を制御し、「言う量」は確実には短くしない。「To control response length, prompt for it explicitly.」ディスクに書く文書（reports、Markdown）も先代より長いことが多い。推奨文: 「Match the length of written documents to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate.」「A short conciseness instruction is effective.」長い system prompt では短い reminder を末尾近くに繰り返す。「don't」より肯定的な例が効く。数値開示なし。
- Prompting Claude Sonnet 5: 応答長を課題の複雑さに合わせる。過剰説明には「Provide concise, focused responses. Skip non-essential context, and keep examples minimal.」。literal instruction following — 指示は 1 項目から別項目へ黙って一般化されないので、scope を明示する。長文の散文 style は model ごとに変わり得るので style prompt を再評価する。
- Claude prompting best practices「Communication style and verbosity」: 「Claude Opus 5 is an exception on verbosity」。Fable 5.1 は逆に更新が少ない。冗長性は model 世代ごとの調整可能な属性。Opus 5 の review では「全部報告させて別 pass で絞る」（generate-then-filter。コード review findings の話で散文ではない）。
- 含意: 文書長は model 既定の drift で、プロンプトで制御できる。ただし「一人の読者向けに書け」は「簡潔に」と同じではなく、内容損失については何も言わない。cut 指示は Sonnet 5 では scope を明示する。model 世代ごとに再測定（失効条件: 次の Opus / Sonnet release note）。

**4-b. 学習由来の原因（実験・benchmark）**
- Singhal et al. arXiv 2310.03716（COLM 2024、snippet）: RLHF の報酬向上の多くは長さの変化。length-only 報酬で下流利得の大半を再現（2023、open model）。DPO 系: arXiv 2403.19159 / 2409.06411（10-40% 短い）/ 2406.11817（snippets）— 長さは分離可能な軸。AAAI 2026-03 の Kim et al. causal lens（snippet）。いずれも学習側の対策で、利用者側からは触れない。
- YapBench, arXiv 2601.00624（2026-01、要旨）: 76 model・300+ の簡潔が理想な prompt。過剰長の中央値に桁違いの差。failure mode は「曖昧入力での vacuum-filling」と「一行の技術依頼への説明 / 整形の過剰」。冗長性は世代・能力に単調でない。短い英語プロンプトであり長文散文ではない。「曖昧入力で空白を埋める」は、読者未指定→冗長という仮説と整合（推論）。
- Verbosity != Veracity, arXiv 2411.07858（要旨）: 14 model・5 QA。GPT-4 の VC 50.40%、冗長な応答は不確実性が高い、Qasper で accuracy gap 27.61%（冗長が悪い）。cascade で Mistral VC 63.81%→16.16%。短答 QA で、不確実性→語数増の機構。「読者が分からないと不確実→水増し」は未検証の推論。
- 指示の効果: arXiv 2506.08686（summary）— 「簡潔に」で長さ約 60% 減、ROUGE-L F1 は多くで上昇。事実 QA で、著者自身が長文には不向きかもしれないと述べる。arXiv 2503.01141（snippet）— CoT 圧縮の指示は長さ-精度の普遍曲線に載る（reasoning 設定）。プロンプトによる短縮は内容と長さの交換になり得る。
- audience の影響: 「LLM は不慣れな聴衆に長く、慣れた聴衆に固有名詞を多く書く」（escholarship、snippet）。persona が冗長性を「わずかしか変えない」という 2505.08143 の summarizer 主張は、要旨で確認できず破棄（notes が検証済み）。

### (5) 流用できる ground-truth 設計

- **Agrawal & Carpuat, "Do Text Simplification Systems Preserve Meaning? A Human Evaluation via Reading Comprehension"**, TACL（2024-02 改訂）、arXiv 2312.10126（要旨、PDF 解析不可）: 9 システムを読解質問で評価し、最良の教師ありでも ≥14% の質問が簡約文から答えられない。(snippet、本文未確認) 削除が理解低下の主因で、トークン削除率はシステム間で 9.3% 対 50.7% と開く。
  - 差: 対象は pre-LLM の簡約系・一般読者・質問が原文基準（宣言読者の課題ではない）。
  - 移せる部分: 「cut 後の文から答えられる読解質問」を ground truth にする設計。14% は読者条件づけ無しの cut の被害の桁。pilot では、原文から作った質問を cut 版で答えさせる（小規模なら質問は著者または別 context が作る）。
- **著者の skip 印を usage data にする**: Nielsen（3-d）は split を usage data で決めると述べる。King の Ideal Reader（二次資料）は add / cut の双方の基準。Clark & Brennan 1991 grounding（二次資料）の「書き言葉には確認チャネルが無く、書き手が grounding コストを全て負う」は notes 側の推論で原典の主張ではない。著者が読み飛ばした箇所＝その読者に不要だった grounding、という対応づけ（推論）。現状 `read-through-log.md` に列が無く、新設が要る。
- 注意: 著者は「最も読者に遠い側」（Pinker）で、著者の skip は公開読者の必要と一致しない。skip 印は「宣言した読者 = 著者」への一致度の測定であり、公開読者の理解の測定ではない。ground truth を 2 層（著者印 / 質問ベース）に分けると、このずれが見える。

## Contradictions

1. **「一人に書け」（Vonnegut rule 7、King の ideal reader）対「単一読者による歪み」（Terry Yu、expertise reversal）**
   - Vonnegut「Write to please just one person」（goodreads 経由 snippet、二次資料）と King（二次資料）は、読者を一人に決めると hedging が減り、add / cut の基準になると述べる。いずれも格言で検証手順は無い。King の ideal reader は起稿の標的でなく、改稿時の reviewer 役。
   - Terry Yu, "Teaching Audience Awareness Using LLMs", 2025-03-03（全文）: 一人の読者（教師）に書くと audience awareness が狭まり curse of knowledge が強まる（「single-reader distortion」）。複数視点を LLM に模擬させて共有文脈の仮定を炎上させる教育実践。評価用に選ばれた読者の話で、情報差で選んだ読者ではない。
   - expertise reversal / reverse cohesion（3-a）は、同じ cut が専門家で良く初心者で悪いことを示し、「一人に決める」こと自体は支持するが、その一人の知識水準が cut の符号を決める。
   - 強さ: 機構の根拠（Yu は教育実践の記述、Kalyuga / McNamara は実験だが二次引用・snippet）は格言より強い。ただし対象は教材・学生で、公開 README / 記事ではない。つまり「一人に決める」のは必要条件でも、その一人の宣言の仕方（情報差で選ぶか）が結果を分ける。

2. **「著者を addressee にする」対 Pinker / Bell**
   - Marmorstein, Atomic Object「Write Documentation for Yourself」（2026-08-05、全文）: 自分向けに書くと安く、書かれる。ただし長期に自分が owner であることが前提で、LLM・skip jargon は扱わない。
   - Pinker（APS Observer、全文・本は二次）: curse of knowledge が不透明な文章の主因。Pinker の remedy は、知識が書き手より少ない実在の読者（minimum expertise）に初稿を見せること。「canonical reader」の語は supersummary の snippet で、本文では未確認。Bell 1984 audience design（Wikipedia と snippet、二次資料）: style は addressee に最も合わせられ、auditor / overhearer への適応は弱い。公開 README / Zenn の読者は auditor / overhearer なので、著者を addressee にすると著者に合った文になる。Bell は話し言葉のデータ。
   - 解釈: 「著者」に project 語彙を差し引いた読者（Pinker の canonical reader 形）なら両立する。ただし差し引く語彙は「平文に隠れた jargon」（3-a 追補）で、列挙しきれない。逆側（Hemingway iceberg: 書き手が持つものだけ省ける）は LLM の cut と向きが逆で、LLM は沈んだ部分を保持しているが読者の分を知らない。cut の判定は「書き手が知っているか」でなく「読者が既に持っているか」。
   - 強さ: Pinker・Bell・COIK は機構の根拠。Marmorstein は実践記述で、対象が人間 docs。

3. **Richardson（派生要約 ≈ raw 履歴）対「記述より evidence」仮説**
   - reader-specification note の仮説 (a) は「読者を記述でなく evidence（本人の語・履歴）で渡す方が良い」。Park et al.（interview 逐語 83% 対 demographics 74%）はこれを間接的に支持する。
   - Richardson 2310.20081 は、LLM が実データから導出した要約が raw 履歴と同等以上（75% 減）と述べ、形式でなく「実データに由来する記述」であることが効く可能性を示す。
   - さらに、lead 確認済みの 2608.30033 により、「evidence を渡せば bounding できる」という notes の第 3 の根拠は要旨で支持されない。支持されるのは「persona のみでは不十分」と「アーキテクチャで参照・保持を制限すると改善」まで。
   - 結論: 三者（persona 文 / raw evidence / 実データ由来の記述）の優劣は未検証。支持が最も強いのは「persona のみでは足りない」で、「evidence が persona に勝つ」は間接根拠（Park、散文でなく回答予測）のみ。pilot で腕を 2〜3 本置いて比べる価値がある。

4. **追加の食い違い**
   - 過汎化リスク: Peters & Chin-Yee は多くの model で caveat 欠落（OR 4.85）を示すが、Claude 系は有意差なし。実行 model が Claude なら 3-b の危険は小さい可能性があるが、cut-only は未検証なので pilot で測る。
   - 判定側の長さ bias: 2604.23178 は model 間不均一（Claude は短文選好）、2606.19544 は全体に小さい（0.011 未満）。いずれも pairwise 応答比較で、文単位の necessity 判定には転移しない。「簡潔に」指示は QA で効く（約 60% 減、2506.08686）が、CoT では長さ-精度の交換曲線に載る（2503.01141）。長文散文での内容保持は未検証。
   - cut で足りるか上流で足りるか: Verbosity Compensation（2411.07858）は冗長を不確実性の症状とみなし、上流（主張を先に確定）を示唆する。Anthropic 文書は長さを prompt で制御可能とみなす。後者は長さ、前者は内容の問題で衝突ではないが、核が無い文章を cut すると「核の無い短い文章」になる。冒頭 3 行に主張があるかを併せて測る。

## Still unknown

- 宣言した読者の deletion test（LLM）が、実読者・著者の skip 印と一致するか。直接研究なし。pilot が唯一の経路。
- 読者を persona 文 / raw evidence / 実データ由来の記述で渡したとき、冗長性と過剰削除が変わるか。誰も未検証。pilot は regression gate 規模（n=5-10）であり hillclimb に使えない（`~/.claude/rules/common/evals.md`、holdout 4-8 件はノイズ）。
- cut-only（書き直し無し）で Claude が caveat・否定・数値を落とす率。Peters & Chin-Yee は書き直し型。
- 散文（コードでなく）で frontier model が削除回避（Guard-and-Go 相当）を示すか。2607.28887 は code のみ。
- Claude 5 系の日本語長文の冗長性。全証拠が英語。Sonnet 5 は新 tokenizer のため token 数は比較不能、文字数で測る。
- Claude の reviewer / judge が長さ・markdown 構造を長文散文で報いるか。
- 日本語・Zenn の結果、日本語の craft 一次資料（糸井・古賀・谷山）、layered と cut のどちらが日本語技術記事に効くか。
- 未読の全文: 2509.14543、2411.10109、2310.20081、2312.10126、2601.00624、2604.23178、2606.19544、2606.01629、2602.01015、2602.00459、McNamara 1996、Kalyuga、BMAD の raw SKILL.md、no-ai-slop の eval.md。数値は summarizer 抽出で、ADR 化の前に再確認する。
- 失効条件: practitioner 投稿（2025-05〜2026-08）は 2027-01 または検証済みの手法が出た時点で鮮度不明。vendor 指針は次の Opus / Sonnet release note で再確認。craft の出典（Pinker / Bell / Nielsen）は長期に安定。

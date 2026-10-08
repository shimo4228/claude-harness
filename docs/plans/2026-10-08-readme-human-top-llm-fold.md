kind: external
# README を「上は人間（約 3 行 + 摩擦除去）、下は畳んだ `<details>` の LLM フロア（全体長に上限）」へ組み替えてよいか

as-of 2026-10-08。統合元: notes 4 本（`~/.cache/claude-research-notes/2026-10-08-readme-grounding-surface/` の chat-assistant-fetch / code-indexers / human-readme-reading / adversarial）、一次実験 `~/.claude/skills/readme-writer/evals/grounding-canary/PROTOCOL.md`、pilot `~/.claude/skills/readme-writer/evals/reader-cut/marks-2026-10-08.json`、現行前提 `~/.claude/skills/readme-writer/SKILL.md` ほか。読んだ深さは 全文 / 要旨 / snippet / 二次資料 で付す（notes 内の「summarizer 経由」は二次資料扱い）。

## Scope searched

- notes 4 本は全文 Read。各 note の探索範囲: chat-assistant-fetch は公式 doc 4 件 + 検索 + 自前 WebFetch 実験、code-indexers は 17 call（llms.txt 採用・DeepWiki・Context7・gitingest・Copilot・AGENTS.md）、human-readme-reading は約 14 call（README 内容研究・読み方研究・guidance）、adversarial は 13 call（llms.txt 実測・折りたたみ・GEO・短い README）。
- 一次実験（canary）は PROTOCOL.md を全文 Read。repo `https://github.com/shimo4228/readme-fetch-canary`（README 約 2.6 万字）自体は未 fetch（結果表の記載を信頼）。
- pilot: `marks-2026-10-08.json` 全文 Read、`units/jev-skill-router.README.ja.json` の該当行を部分 Read。
- **commit `0529e0b` の本文は読めていない**（この実行では Bash が使えず `git show` を実行できなかった）。「冒頭を読んでも結局何をするものなのか全くわからない」「人間向け README はキャッチコピー: 機能の説明は 3 行ほど、残りは摩擦除去」「記事と README は違う」「人間の読者が最近増えた（以前は LLM 検索のみ）」は、依頼文で渡された著者発言の転記であり、commit 本文と突き合わせていない。marks JSON 側は全文で確認した。
- 現行前提: SKILL.md 全文、`inspiration.md` L45-94、`references/readme-judge-checklist.md` の F1/F3 行を Read。
- 見つからなかった範囲: README 長 vs 理解・採用の因果研究、「3 行 pitch + 摩擦除去」の直接研究、README が人間と LLM のどちらにも効くかの比較研究、2026-06〜10 に ChatGPT / Claude.ai / Gemini / Perplexity / Copilot が貼付 URL から何を読むかを測った公開実験（canary 以外）、`<details>` を assistant がどう扱うかを書いた公式 doc。

## Found

### A. 一次実験: grounding canary（2026-10-08、PROTOCOL.md 全文、自前実験、各条件 n=1）

設計: 置き場所ごとに別のランダム語を埋め、答えに出た語で「読んだ場所」を判定する。V = README 冒頭（見える）、D = 冒頭近くの `<details>` 内、T = 約 2.6 万字 README の末尾（見える）、L = llms.txt、S = README からリンクした `docs/setup.md`。全 assistant に同一の質問文（5 問、「推測せず not found と言え」）。README から llms.txt へのリンクは無い。

| assistant（モデル / プラン / モード） | V | D | T | L | S | 備考 |
|---|---|---|---|---|---|---|
| ChatGPT（GPT-6 / Plus / 一時チャット / effort 高） | ○ | ○ | ○ | − | ○ | 出典に README.md と docs/setup.md を挙げた |
| Claude.ai（Opus 5.5 / Max / effort 中 / シークレット） | ○ | ○ | ○ | ○ | ○ | README.md / llms.txt / docs/setup.md を読んだと申告。docs/ 一覧は取れなかったと申告 |
| Grok（自動、おそらく 4.7 / X Premium / シークレット） | ○ | ○ | ○ | ○ | ○ | 途中経過で「The README is truncated, so I'm reading the rest of the repo files」。初回取得で README が切れ、自分で残りを取りにいった |
| Qwen（Qwen3.7 Plus / 無料 / Auto / 一時チャット） | ○ | ○ | ○ | ○ | ○ | 持ち主の実名にも触れた（repo 外のプロフィールを見た可能性） |
| Gemini 1 回目（3.6 Flash / 無料 / 一時チャット / 思考設定なし） | − | − | × | − | − | 取得失敗。3 は URL の持ち主名から推測した作り話（×） |
| Gemini 2 回目（Pro 選択 →「アクセス集中」で Flash に切替） | − | − | − | − | − | 全問 not found。取得失敗 |
| Gemini 3 回目（3.6 Flash / 無料 / 思考モード強化 / 通常チャット） | ○ | ○ | ○ | ○ | ○ | 1・2 回目との差は「一時チャット → 通常」と「思考なし → 思考強化」の 2 点で、どちらが効いたか分離できない |
| Perplexity（モデル指定なし / 無料） | − | − | − | − | − | 取得せず、検索の断片（repo の About 説明文）だけを見た。作り話はせず全問 not found |

場所別の読み（取得できた 5 回 = ChatGPT / Claude.ai / Grok / Qwen / Gemini 3 回目）:
- **V、D、T は取得できた全回で ○**。つまり取得できた assistant は `<details>` の中（D）も 2.6 万字 README の末尾（T）も読んだ。
- L（llms.txt）は ChatGPT だけ −、他 4 回は ○。S（リンク先 docs）は 5 回とも ○。README の外へ自分で取りにいく挙動が複数 assistant で出た。
- 取得に失敗した回（Gemini 1・2 回目、Perplexity）は V から全滅しており、「README のどこまで読むか」でなく「取得するか否か」で分かれた。作り話は Gemini 1 回目の問 3 のみ。
- 分かれ目の解釈（著者）: 変数はモデルよりプラン・取得経路・モード設計。著者の補正として、無料の Qwen は全 ○ なので有料/無料の二分ではなく、プラットフォーム側の提供範囲の問題。Gemini は 3 回目で全 ○ になったため、一時チャット・思考なしモードで取得機能が働かない提供側設計の可能性（未分離）。Perplexity と Gemini は索引が追いつく日を置いて再試行すると「索引待ち」か「取得しない経路」かを分けられる（未実施）。
- 限界: 各条件 n=1、設問の語は架空ツールで pretraining の混入が無い代わりに、実在 repo の知名度効果は測っていない。折りたたみの「重み」（読んだが無視されるか）は測れておらず、読んだか否かだけが分かる。T は「約 2.6 万字」の1点のみで、より長い README の切り詰め点は不明。Grok の「README is truncated」は、長い README が初回取得で切れうることの実測（下記 B-6 の Claude Code WebFetch での切れと整合）。

### B. 取得経路・折りたたみ・切り詰め（notes: chat-assistant-fetch、adversarial）

1. Anthropic web fetch tool 仕様（API server tool）。https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool — 全文（notes 経由の記述）。`max_content_tokens`（例 100000）超過で切り詰め、既定値は未記載。JS 描画サイトは非対応。会話に出た URL しか取らない。`web_fetch_20260209` 以降は dynamic filtering で長い page を部分読みしうる。HTML→text の変換方式と `<details>` の扱いは doc に無い。consumer の claude.ai は別実装で未記載。
2. Gemini API URL context（https://ai.google.dev/gemini-api/docs/url-context、要旨）、OpenAI bots page（https://developers.openai.com/api/docs/bots、要旨）、Perplexity fetch_url（https://docs.perplexity.ai/docs/agent-api/tools/fetch-url、要旨）。Perplexity は「snippets に抽出され、長い page は切り詰められうる」と明記（数値なし）。OpenAI は fetcher があることしか書いていない。いずれも `<details>` に言及なし。
3. 自前 WebFetch 実験（Claude Code の WebFetch、n=1 repo、中間 summarizer 経由）: github.com の描画 HTML でも `<details>` の本文 3 件は落ちずに返った。GitHub は `<details>` 本文を初期 HTML に載せ、折りたたみは client 側の表示のみ。同じ tool で yamadashy/repomix（README 2.5 万字超）は描画 page だと表の途中（"Ou"）で切れ、raw は完走。短い README（contemplative-agent）は切れなかった。canary の Grok 挙動と整合する（二次資料の二次的裏付け）。
4. 失敗様式は JS であって `<details>` ではない: SEJ 2026-01-08（https://www.searchenginejournal.com/ask-an-seo-can-ai-systems-llms-render-javascript-to-read-hidden-content/563731、二次資料）。CSS で隠れたアコーディオンは HTML→Markdown 変換で読まれる（writesonic / clearwater の要旨のみ、snippet）。`<details>` が cloaking とみなされた証拠は無い（adversarial の推論）。
5. 残るリスク（未測定）: Readability / trafilatura 系の本文抽出や Perplexity 型の snippet 抽出が、折りたたみや低密度部分を落とす可能性。`<details>` を測った研究は無い。canary は「読まれたか」を測ったが「重み」は未測定。

### C. llms.txt の利用実測（notes: code-indexers、adversarial）

- Ahrefs 2026-05（137,000 domains、server log）: llms.txt の約 97% が 2026-05 に AI リクエスト 0。AI 検索 bot はそのうち 1.1%。https://ppc.land/llms-txt-adoption-rises-8-8x-but-97-of-files-get-zero-ai-requests/ — 二次資料（一次の Ahrefs 投稿は未読）。
- EZY Research 12 週（83 sites、2026-04-27〜07-19）: llms.txt fetch vs robots.txt fetch は GPTBot 7 vs 3,990、ClaudeBot 9 vs 3,120、PerplexityBot 0 vs 775。https://somethinginc.com/blog/llms-txt-ai-crawlers-fetch-data/ — 全文（二次資料）。
- Complete SEO（6,455 domains、30 日、〜2026-06-14）: 取得 site は一桁 %、ChatGPT-User / Claude-User / Perplexity-User は無視できるほど少ない（指定 page しか取らない）。https://completeseo.com/are-ai-bots-actually-reading-llms-txt-files/ — 要旨。plugin 自動生成 site に偏る。
- Google Search Central AI optimization guide（最終更新 2026-07-10）: 「新しい machine readable file / AI text file / Markdown は不要」。https://developers.google.com/search/docs/fundamentals/ai-optimization-guide — 全文。範囲は Google Search/AI Overviews のみ。Lighthouse 13.3.0（2026-05-07）には llms.txt 監査があり（二次資料）、方針は割れている。
- Anthropic 自身の docs は llms.txt を公開し本文で agent に fetch を促す（code.claude.com 側、全文）。サーバログで Claude Code が自動 fetch する証拠は無い。Mintlify 2026-03: coding agent が docs 流量の約 45%（Claude Code 25.2%、Cursor 18.0%）だが llms.txt 利用は書かれていない（全文）。

### D. repo の機械読者は README を経由しない（code-indexers）

- Claude Code は README を自動ロードしない。CLAUDE.md（または repo の AGENTS.md）と auto memory のみ（https://code.claude.com/docs/en/memory、全文）。AGENTS.md は「README を人間向けに簡潔に保つため」の agent 向け README（https://agents.md、全文）。DeepWiki は `.devin/wiki.json`、Context7 は `context7.json` で steer できる（どちらも要旨）。gitingest は file 内容を生で出力するので `<details>` は保持される見込み（README の記述からの推論）。DeepWiki / Copilot / Cursor が README を優先するか、`<details>` を剥がすかは一次資料なし。
- 2026 年の実務の収斂（snippet 多数、測定なし）: README = 人間の物語（何・install・license）、AGENTS.md = 運用詳細。Upsun blog 2025-08-12（意見、数値なし）は逆に「良い README があれば別 config は不要」。AGENTS.md は repo の内側で作業する agent 向けで、外から repo を説明する chat assistant の grounding 面ではない（別の読者）。

### E. 人間の README 読解（notes: human-readme-reading）

- Prana et al. arXiv 1802.06997（2018）: 393 repos・4,226 section。含有率は What 97.0%、How 88.5%、Why 25.7%、When 21.4%。section 数では How が 58.4%。Why が最も欠ける。要旨（summarizer 経由）。README が人間に効くかは測っていない。
- arXiv 2206.10772（2022、1,950 README）: 人気 repo は構造化され、リストと画像と外部リンクを持つ。相関のみ、要旨。短さとの関係は述べていない。
- arXiv 2502.18440（CHASE 2025、2025-02-25）: Debian 系 FLOSS で README は最小で先に作られる。初期 README の読み時間中央値 14.79 秒（snippet のみ）。実務の記述であって読者の必要ではない。
- Meng et al.（2019、API doc、n=11、eye tracking）: 概念概要の使用は doc 時間の 0〜43% と人により差が大きく、「opportunistic（コードへ飛ぶ）」と「systematic（枠組みを先に読む）」の 2 型。code と reference で約 40%。全文（summarizer）。README ではなく API doc、n 小。
- Nielsen（NN/g 1997-09-30）: 新規 page を常に走査する人 79%、1 語ずつ読む人 16%。簡潔 +58%、走査しやすい layout +47%、3 つ併用 +124%（usability）。全文。29 年前の一般 web で、一般 prior としてのみ。
- Steinmacher 系（snippet のみ）: 新規貢献者の障壁で環境構築が大きい。利用者ではなく contributor の話。
- GitHub Docs About READMEs（全文）: what / why useful / get started / help / who maintains の 5 問。500 KiB 超で切り詰め。長さ規則ではない。

### F. pilot: reader-cut の著者印（`marks-2026-10-08.json` 全文、n=著者 1 名、2026-10-08）

- contemplative-agent.README.ja: 冒頭 11 単位（i<=10）で離脱。印は i=1–8, 10 の全部が `stop`（9 は印なし）。著者の申告として「冒頭を読んでも結局何をするものなのか全くわからない」「情報過多」（commit 本文は未読。依頼文の転記）。
- jev-skill-router.README.ja: 「ほぼ全文」読了。`stop` 計 17 単位、`skip` 計 18 単位。`skip` は i=52 と、**i=77–93 の連続 17 単位**（section 8 の冒頭 i=77 から。i=77 は `api.typesafe.ai` へ送られるデータの詳述）。著者の申告として §8–9 のブロックを丸ごと飛ばした。i=94–96 は印なし、i=97 は `stop`。
- ecc-journey-part1（記事）は全文・印なし、part2（記事）は全文だが「全体が情報過多で離脱しかけた」。印は 66, 85, 86 の `stop` のみ。著者の発言（転記）: 記事と README は別物、人間向け README は「機能 3 行 + 残りは摩擦除去」。
- 著者の発言（2026-10-08、転記）: README の前提が変わった。人間の読者が最近増え、以前は LLM 検索だけだった。
- 限界: 著者 1 名、README 2 本と記事 2 本、離脱の理由は「何をするものか不明」「情報過多」と著者の言語化のみ。人間の README 読者一般への推定には使えない。

### G. 現行前提（改稿対象）

- `~/.claude/skills/readme-writer/SKILL.md:14-17`: README は grounding 経路（AI 検索・チャットへの URL 貼付）で LLM が確実に前提にできる唯一の surface。人間向けに短く・走査しやすく保ちつつ、README 一枚で復元できる小さなフロアを必ず残す。
- `SKILL.md:33-37`: 軸は「人間の注意 × LLM の情報」で、トレードオフでなく設計で両取りする。
- `SKILL.md:60-82`: フロア 5 要素（identity 文、why、canonical 事実、具体例 1 つ、link-map はポインタのみ）。L65 に「画像のみ・`<details>` の中のみ・リンク先のみ は不可」。L80-82 に「フロアは小さな非交渉コア。…README が偽装 llms-full.txt に肥大する」。
- `SKILL.md:121-130`: Length budget。語数目標なし。L130「`<details>` は二次的な bulk のみ（option 表・FAQ・troubleshooting）。フロアを入れない」。L145-146 に機械可読導線は `<details>` に入れず末尾平文 1–2 行（折りたたみは rendered-HTML の crawler と HTML ブロックを不透明扱いする抽出器に見えない）。
- `references/readme-judge-checklist.md:39` F1: フロア 5 要素が本文の文として在るか（`<details>` の中だけは数えない）。`:41` F3: フロア以外の情報が `<details>` や図やフロア節に溜まっていないか（偽装 llms-full.txt）。`:20` は `details_blocks` 証拠が「フロアや AI 向け導線が隠れていないか（F3）」を見る。
- `inspiration.md:53-61`: 「LLM は README しか読まない」は強すぎる。正確には「汎用の貼付 URL / 検索 grounding が確実に前提にできる唯一の面」。routed coding agent は llms.txt を on-demand で読む。`inspiration.md:63-87`（2026-06 extension）: AI 検索 crawler は llms.txt を実質 fetch せず（Ahrefs 2026-05 の 97% 等）、`graph.jsonld` は直接 fetch で plain text 扱い（SearchVIU 2025-10）、人間向けだけの README は LLM の理解を低下させうる（ReadMe.LLM arXiv:2504.09798、DeepSeek-R1 の事例）。ReadMe.LLM は元の論文本文を今回再確認していない（inspiration.md の記述の転記）。
- 本調査との差: 現行の禁止「`<details>` の中のみ不可」は、2026-06 の根拠（折りたたみの crawler 不可視性の懸念）が canary（取得できた 5 回すべてで D を読んだ）と WebFetch 実験（本文が落ちない）では観測されなかった。ただし canary は 5 assistant・各 n=1、取得に失敗する assistant（Perplexity、Gemini の一部モード）では D 以前に V も届かない。

## Contradictions

1. **makeareadme「too long is better than too short」/ ripgrep の長い README vs 「3 行 + 摩擦除去」**。makeareadme（https://www.makeareadme.com/、全文）は長すぎる方が短すぎるよりよいと明言し、多すぎれば wiki/docs へ移す（削らない）。ripgrep（`raw.githubusercontent.com/BurntSushi/ripgrep/master/README.md`、2026-10-08、要旨。約 3,500 語・install は 3/4 付近は summarizer の概数で未検証）は why / benchmark を前に置く超人気の長い README。どちらも意見・事例 1 件で測定ではない。3 行モデルの側にも README 長を測った証拠は無い。強い根拠は、新規 page は走査される（NN/g、古い一般 prior）と、著者の pilot（2 README で離脱 / skip）。いずれも弱い。ripgrep は「長くても人気」であって「長いから人気」ではない。Art of README の funnel（一般→具体、途中で止められる）は snippet のみで一次未確認、Diataxis の README 解釈も二次ブログのみ。決着は付かず、著者 1 名の観察が最も直接的。
2. **GEO「密で見える事実」 vs 折りたたみ**。arXiv 2604.25707（2026-04、602 prompts / 18,151 pages、ChatGPT・Google・Perplexity、要旨のみ）は、influence が高い page は「長く、構造化され、抽出できる証拠（定義・数値・比較・手順）が豊富」と報告する。3 行 + 畳んだ下層は見える面を薄くする方向で、この相関と逆を向く。ただし対象は一般 web page で相関、README ではなく、見える/畳んだの区別は測っていない。canary は、GitHub 貼付 URL では畳んだ D も読まれたので、少なくとも取得できる assistant では「畳む」ことで事実が消えない。GEO の効果が「見える密度」でなく「page 内にある」かは未分離。GEO の「40% 増」は blog snippet のみで不採用。
3. **inspiration.md の ReadMe.LLM（人間向けだけの README は LLM の理解を下げうる） vs 人間専用の上部**。折りたたみ下層に LLM フロアを残す案は、この論拠と衝突せず、むしろ維持する側（フロア自体は残る）。衝突するのは「フロアは本文の文として在る（`<details>` の中のみ不可）」という現行 F1。canary では D も読まれたので F1 の「`<details>` 不可」の観測根拠は弱まった。ただし ReadMe.LLM は DeepSeek-R1 1 事例で、コード用ライブラリの doc が対象。論文本文は今回再読していない。
4. **llms.txt: canary で Claude.ai / Grok / Qwen / Gemini が fetch（○）した vs server log 研究で llms.txt はほぼ読まれない**。経路が違う。canary は利用者が貼った URL を assistant が agentic に深掘りする user-triggered fetch（README に llms.txt へのリンクは無いのに取りにいった）。log 研究（Ahrefs / EZY / Complete SEO）は crawler の定期巡回で、Complete SEO では user-triggered の ChatGPT-User / Claude-User / Perplexity-User も少ない（指定 page しか取らないため）。canary の ChatGPT が L だけ − で、Claude.ai は自己申告が根拠。両者は矛盾せず、「貼付 URL の深掘りで拾われる」と「crawler は拾わない」が併存する。ただし llms.txt を floor の置き場にする根拠にはならない（5 回中 4 回が ○ でも、取得に失敗する assistant には届かない）。
5. **README vs AGENTS.md の分担（2026 年の実務の収斂）vs 現行「LLM フロアは README に」**。実務の収斂（snippet 多数、測定なし）は README = 人間、運用詳細 = AGENTS.md。ただし AGENTS.md は repo の内側で作業する agent 向けで、外から repo を説明する chat assistant の grounding 面ではない（adversarial、Upsun blog は逆の意見）。読者が違うので、分担論は畳んだ LLM フロアの是非を直接決めない。
6. **Google「機械可読 file 不要」 vs Lighthouse の llms.txt 監査**。同じ Google 内で割れており、llms.txt を置き場にする案も外す案も決定打に欠ける。

## Still unknown

- 畳んだ D の本文が答えにどれだけ重く効くか（読んだことは確認、重みは未測定）。D のみに事実を置き V に無い条件で読まれるかは、canary 設計で D の語は D にしか無いため「読まれた」は言えるが、V に同じ事実がある場合の優先は未測定。
- 取得に失敗した assistant（Perplexity 無料、Gemini 一時チャット/思考なし）での改善策。索引が追いつく日を置いた再試行は未実施。Perplexity は About 説明文だけを見たので、**About 行の鋭さが唯一の面になる**（snippet の観察であって実験結果の一般化ではない）。
- T の切り詰め閾値（2.6 万字より長い README、より長い page）。Grok の初回取得で README が切れた長さ、Claude Code WebFetch の repomix（2.5 万字超）の切れと整合するが、assistant ごとの上限は未測定。全体長の上限値を何字にするかの証拠は無い。
- 各条件 n=1 のばらつき。再実行での一貫性。
- 人間の読者が増えたという前提（著者の観察）を裏づける数値。GitHub traffic / README anchor click の取得可否も未確認。
- 「3 行 + 摩擦除去」が採用・理解を上げるかの直接研究。troubleshooting を README に置く効果の証拠も無い。
- DeepWiki / Copilot / Cursor が README を優先するか、`<details>` を剥がすか。Sourcegraph / Cody と Codex CLI の取り込み。
- Ahrefs 一次 post、EZY 一次 report、Vercel/MERJ 一次は未読。ReadMe.LLM（arXiv:2504.09798）本文は再読していない。
- 失効条件: canary の結果は各 assistant のモード設計に依存し、1〜数週間で変わりうる。次の同条件再実行まで、または assistant の取得機能更新（Gemini / Perplexity / ChatGPT 主要更新）までを暫定の有効期間とする。
- commit `0529e0b` 本文は未読（上記 Scope searched）。

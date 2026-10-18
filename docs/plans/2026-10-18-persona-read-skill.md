kind: external
# 問い: 読み手 persona 読解（persona-read / visitor-read）を汎用 skill として単独 repo に切り出す設計の根拠（先行例・妥当性・配布・隔離）

as-of 2026-10-18。notes: ~/.cache/claude-research-notes/2026-10-18-persona-read-skill/{prior-art,validity,awesome-lists,distribution,adversarial,followup}.md。web 由来は fetch tool（小モデル要約）経由が大半で、引用は逐語でない。ローカル実測（L1-L5）は主ループが 2026-10-18 に Claude Code 2.1.302 で確認。

## Scope searched
- 先行例: persona review / reader persona / simulated readers / SKILL.md cold read（WebSearch 5 + WebFetch 8）。GitHub code search、skills.sh / SkillsMP 直接閲覧、synthetic-user SaaS、anthropics/skills は未確認。
- 妥当性: persona 忠実度、自己選好、usability 模擬、改稿ループの hedge 増加（WebSearch 5 + abstract fetch 6）。PDF 本文は取得できず、数値は abstract / snippet 水準。
- 配布・隔離: agentskills.io 仕様、Claude Code docs（cli-reference / headless / skills / plugin-marketplaces）、vercel-labs/skills、Codex / Gemini CLI（agy）docs。
- 反証・追跡: NN/G、persona collapse、AI-slop PR、persona-review 内部と Loop-Back 論文 HTML の再読。
- awesome-list: 範囲外（著者判断 2026-10-18、L5。別ルーティンが担う）。→ 末尾「Not in scope」。
- ローカル: L1-L4 は主ループの実行・Read（一次）。

## Found

### A. 先行例（prior-art.md / followup.md）
1. pvliesdonk/claude-plugins `plugins/persona-review`（https://github.com/pvliesdonk/claude-plugins/pull/50、PR #50 merged 2026-10-05）。PR ページは読了、SKILL.md / ensemble.md / workflow.js は fetch 要約。presets.md / evidence.md / scripts は未読。
   - 対象と前提: 文書を想定読者として人より先に査読。persona card（tier primary / gatekeeper / secondary / adversarial、came_for 2-5 件を読む前に書く、mode walk|read）、3-6 persona + 1-3 lens、distinctness test（組ごとに「片方だけが挙げる finding」を言えなければ統合）、verifier が引用を探し反証（MAX_VERIFY=10）、reader file の pin（SHA / sha256）。MIT、stars 0、作成 2026-04-10、最終 push 2026-10-07（GitHub API、fetch 経由）。
   - 証拠の種類: 採用実績は無し（stars 0）。実装の自己記述。dogfood 9 agent で約 840k token（重い）。
   - 隔離: Agent-tool subagent（"one general-purpose Agent per prompt"）で、claude -p の別 process ではない。隔離は情報の差し止め（reader には back_cover / seat / reader_files のみ。intended_takeaways / design_context は verifier と synthesis にだけ渡す）。CLAUDE.md 継承の有無は記述なし（未確認）。offline fallback は author が文脈内で答え、"not blind" と記録。
   - 言い直し照合: teach-back あり。reader が intended_takeaways を見ずに書き、verifier が correct / partly / wrong と takeaways_missed を採点 → 我々の 一致 / ずれ / 欠落 にほぼ対応。
   - round: 1 run = review→verify→synthesize の単発。2 周目は args.previous と reader_tests（confirmed / refuted / untested）。上限規則なし（synth に done_when 欄）。
   - 数値 drift 検査: 無し（workflow.js に "no check for these"）。
   - 我々との差: 重い（verifier 層、python / JS script）、process 隔離なし、機械 drift count なし、最大 3 周の規則なし、plugin marketplace 内で単独 repo ではない。
   - 移る部分: persona card の項目、distinctness test、「読みを変える属性だけ残す」、verifier の引用照合、pin 検査、reader_tests。
2. nazir99/reader-walkthrough（https://github.com/nazir99/reader-walkthrough）。README 読了、SKILL.md は要約。stars 0、commit 3、MIT。
   - 対象: 完成物を named reader として描画順に読み、全 stall を列挙。最終行 `VERDICT: PASS | STALLS n | worst: ...`。同梱 persona 3 つ + custom テンプレ。最大 2 周（超えたら「あえて残したもの」を明示）。
   - 差: 隔離なし（main agent 内）、意図照合なし、drift 検査なし、persona は 1 run 1 人。
   - 移る部分: round 上限と、機械ゲート用の 1 行 verdict。
3. carson-sweet/sweetclaude `skills/product-user-focus-group`（AGPL-3.0、registry 更新 2026-05-26、7 stars）。SKILL.md 要約。
   - 対象: product concept / message 用の合成 focus group。persona × instance ごとに並列 subagent、JSON のみ返却 + 検証 + retry 2 回、不良 30% 超で停止。persona gate（シナリオ、二値の成功基準、deal-breaker、anti-profile）。「合成の知見は仮説」と明記。
   - 差: 領域が製品調査で原稿査読ではない。意図照合・drift なし、1 round。
   - 移る部分: JSON 返却の検証 + retry、「仮説」ラベル。AGPL なので文言の写しは避け、設計だけ参照。
4. その他（snippet のみ、本文未読）: DurdeuVlad/persona-write（`/persona-review` は単一 persona、書き手の声の補正）、wan-huiyan/agent-review-panel、AlexWortega/ai-peer-review-skill、tedeuxx/tadeumendonca-skills（code / plan / 論文向け panel）、TDS 記事（403、snippet）、Docuwiz Substack（手動 prompt、https://docuwiz.substack.com/p/prompt-usability-testing-docs-with）、tommcfarlin（code review personas）、pkgdev（README checklist）。LintMe（CHI 2026, arXiv 2603.00331, snippet）は README lint で DSL に programmatic check と LLM 判断を混ぜる隣接例で、数値・最上級の機械計数に近い。
5. 差別化の整理（researcher 判断、「未発見」であって不在の証明ではない）。既存にあるもの: persona 単位の reader 査読、teach-back 照合、round 上限（2）、JSON 返却検証、意図の差し止め。どの候補にも見つからなかったもの: (a) `--setting-sources ""` + `--tools ""` による process 隔離、(b) 数値・最上級・限定句・固有名の改稿ごと機械計数と増加時の著者確認、(c) 最大 3 周、(d) 読み手評点を合格基準にしない立場、(e) 記事 / README の 2 preset。登録所（skills.sh 等）は十分に索引できておらず、「パッケージ化された persona 読解 skill は見つからない」は弱い証拠（followup は 2 検索）。「persona が文書を読む」自体は手動 prompt として既出なので、差別化は隔離・JSON schema・意図照合・計数のパッケージ化にある。

### B. 妥当性（validity.md / followup.md）
1. Loop-Back Authority in LLM Agent Teams（arXiv 2609.14767v2、https://arxiv.org/abs/2609.14767）。abstract 読了、HTML は followup で fetch 要約により再読。
   - 対象: 製品レビュー要約の 52 製品 / 540 reviews、43 製品の 86 paired run、モデルは GPT-5.4 / Gemini-3.1-Pro / Qwen-3.5-122B / GLM-5 / Mistral-Large-3、judge は 5 モデル panel。manager が feedback し writer が改稿する階層型。
   - 数値の検証状態（followup で §単位に照合）: hedging +53%（5.03 vs 3.30 /1000 語）は SUPPORTED。初稿は flat 群と差なしは SUPPORTED（77 drafts）。Writing Clarity -0.14 / revision は PARTIAL（OLS -0.142、manager が戻す draft を選ぶので相関であり因果ではない）。「検証できる manager だけ効いた」は UNSUPPORTED（実験で検証能力を変えていない。§5 では設計則・今後の検証案）。judge 間一致は低い（Krippendorff alpha 0.08-0.17 Writing Clarity）。lexicon は較正された不確実性と回避を区別できない（§5）。
   - 我々との差: 領域が英語の製品要約で、loop は manager 主導の書き直し。我々は reader 主導で日本語の記事 / README。証拠は小 n の judge 採点。
   - 移る部分: 「改稿ループが hedge を増やす」機序は同型。→ 改稿ごとの hedge 計数と周回上限は根拠が立つ（ただし根拠は他領域の相関寄り）。「検証できる者だけ効く」を設計根拠に使うのは不可。
2. 自己選好: Panickssery et al. arXiv 2404.13076（https://arxiv.org/abs/2404.13076、abstract のみ。GPT-4 / Llama 2、自己認識と自己選好が線形に相関、人間は同等と判定）。arxiv 2508.06709 は snippet のみで、GPT-4o / Claude 3.5 Sonnet が自社系列の出力を好むと要約（未確認）。「10-25% 膨張」はベンダーブログの未検証数値。差: 採点であって読解模擬ではなく、モデルも旧世代。示唆: 書き手と読み手が同系列（Claude 対 Sonnet）である偏りは測られていない。
3. persona の忠実度: arXiv 2507.02919 "ChatGPT is not A Man but Das Man"（abstract のみ。人口統計間で不整合と均質化）。2607.18310 などは snippet のみ（persona 出力は人より分散が小さく、個人レベル相関は約 0.2 が上限、数値は二次要約で未検証）。2604.24698 / 2603.16142 / alphaxiv 2606.18263（snippet のみ。詳細属性がステレオタイプへ縮退、簡素な persona が詳細に勝つ例）。差: いずれも人口統計条件づけの母集団模擬で、読み手の stall 予測ではない。著者が対象ごとに定義する persona で同じ縮退が起きるかは未検証。
4. 最近接の読解実験: arXiv 2501.06964（abstract のみ。LLM が教育水準別の患者役で ICU 退院要約を読み、教育水準を与えたときの指導適合 88%、他の属性では偶然水準以下。著者は予備的と述べる）。NSF 要約（https://www.nsf.gov/cise/updates/what-human-reading-reveals-about-ai-prediction-capabilities、snippet）は LLM が読み手の混乱と読み返しの説明に弱いとする（文単位の視線研究）。usability 模擬は UXAgent arXiv 2502.12561 / Synthetic Cognitive Walkthrough arXiv 2512.03568（snippet のみ。完遂率が人より高く、問題検出が少ない、人との併用を推奨）。
5. NN/G Rosala & Moran "Synthetic Users"（2024-06-21、https://www.nngroup.com/articles/synthetic-users/、fetch 要約）。意見 + 小比較。合成ユーザーは浅く好意的（迎合）、優先順位づけ不能、最終判断・検証には不向き、机上調査・ガイド試験・仮説生成には可。合成知見は実ユーザー知見として提示しない。移る部分: 「評点は合格基準にしない」「仮説 / 試験用途」の位置づけ、README に "not user research" ラベル。
6. 総合（researcher 判断）: 「3 Sonnet persona が実読者と同じ箇所で止まる」を直接測った研究は見つからなかった（(a) は未測定）。隣接証拠は、粗い事前確認・未知語・言い直しの欠け検出には使えて、人の反応の代替にはならない、という使い方と整合する。3 つの読み手は同一モデルなので独立な 3 標本ではなく、収束リスクがある（distinctness test の発想が使える）。

### C. 配布・隔離（distribution.md + ローカル実測）
1. ローカル実測（一次、2026-10-18、Claude Code 2.1.302）。
   - L1: `claude -p --setting-sources "" --strict-mcp-config --tools "" --model sonnet --system-prompt "..."` を CLAUDE.md のある repo（~/MyAI_Lab/zenn-content）で起動。stream-json init: tools 0、mcp_servers 0、model claude-sonnet-5-5、skills 22（すべて組み込み: deep-research / design / code-review / loop 等。ユーザー skill 0）、agents 6（組み込み）。「文脈にある skill 一覧・memory・CLAUDE.md の見出しを引用せよ」に対し読み手は NONE。→ user / project の CLAUDE.md・memory・ユーザー skill は読み手に届かない。組み込み skill / agent は残る（隔離は完全ではない。読み手 prompt が組み込み skill を呼ぶ余地は tools 0 のため実質無いが、文脈には載る）。
   - L2: 同じ問いを `--safe-mode`（setting-sources なし）で起動すると `# userEmail` `# Environment` `# Language` の 3 見出しが読み手に見えた。→ --safe-mode は --setting-sources "" より隔離が弱い。
   - L3: `claude --help`（2.1.302）の --setting-sources は「user, project, local」の列挙のみで空文字の意味は書かれていない。L1 は実測の挙動であり、仕様保証ではない（版が変わると変わりうる）。--bare は OAuth を読まず ANTHROPIC_API_KEY 必須。
   - 我々との差: 検証は 1 版・1 repo・1 質問の実測。--system-prompt を与えたときの環境節の扱いは --safe-mode 側との比較のみで、--system-prompt 無しの場合は未測定。
2. docs 側（https://code.claude.com/docs/en/cli-reference、2026-10-18、fetch 要約）。`--setting-sources` は空文字の挙動が文書化されていない。`--strict-mcp-config` は --mcp-config 指定なしで MCP 無し。`--tools ""` は組み込み tool を全無効にし MCP には効かない。`--system-prompt` は既定 prompt を全置換（git status snapshot も落ちると headless doc）。`--bare` は hooks / skills / plugins / MCP / auto memory / CLAUDE.md を飛ばすが OAuth / keychain を読まず API key 系が必要（headless doc は将来 -p の既定にするとある）。`--safe-mode` は全カスタマイズ無効で subscription でも動くが、docs 上の導入版は不明。→ docs は --safe-mode を有力としたが、L2 の実測で環境節の漏れが出た。
3. Agent Skills 仕様（https://agentskills.io/specification、2026-10-18、全文 fetch 要約）。必須 `name`（64 字以下、[a-z0-9-]、親 dir 名と一致）、`description`（1024 字以下）。任意 `license` / `compatibility`（500 字以下）/ `metadata` / `allowed-tools`（experimental）。scripts / references / assets は推奨のみ。SKILL.md は 500 行未満、本文 5000 token 未満が推奨。検証は `skills-ref validate`。Claude Code の docs（https://code.claude.com/docs/en/skills、先頭 100k/110k 字）は、標準 6 field 以外（`when_to_use`、`disable-model-invocation`、`context`、`model`、`hooks`、`paths` 等）が claude.ai upload / Skills API で hard error になると書く。→ 横断配布なら標準 6 field のみ。`claude` CLI 要件は `compatibility` に書ける。
4. インストール経路。plugin 経由は `.claude-plugin/marketplace.json` が必要（https://code.claude.com/docs/en/plugin-marketplaces）で、無い repo はこの経路で入らない。`npx skills add owner/repo`（vercel-labs/skills README、fetch 要約、npm 1.5.22）は `skills/<name>/SKILL.md`・root SKILL.md・`.claude/skills/` 等を深さ 3 まで探索し、plugin manifest 不要。claude-code は `.claude/skills/`、codex は `.agents/skills/`。既定は symlink。匿名 telemetry あり（DISABLE_TELEMETRY=1 / DO_NOT_TRACK=1 で止まる）。skills.sh が telemetry で自動掲載するかは未確認。10 行程度の marketplace.json の追加は任意で、skills CLI には無害（vercel README 記述より）。
5. 他 agent の隔離（docs 要約）。Codex `codex exec` は read-only sandbox 既定、`--ephemeral`、`--ignore-user-config`、`--ignore-rules`。tool 無効化・system prompt 差し替え・AGENTS.md 回避の flag は文書化なし。Gemini CLI は 2026-06-18 に Antigravity CLI（`agy`）へ置換（unpaid / Google One 向け、geminicli.com の記述）。`agy -p` は承認待ちで hang する報告（google-antigravity/antigravity-cli#318、v1.0.6）で、tool 無効化・system prompt の flag は未確認。→ 隔離 reader の spawn 行は Claude Code 専用。他 agent では別コマンドが要る（未検証）。reader prompt と JSON schema を可搬ファイルに分け、spawn を差し替え可能な 1 行にするのが followup の提案（inference）。
6. 公開系の補足: AI-slop PR への maintainer の反発（EuroPython 2026 talk https://ep2026.europython.eu/session/defending-open-source-from-ai-slop-a-maintainer-s-practical-guide/、DevClass 2026-02-19、snippet）。人の判断を示す根拠を PR に添える対策が一般化。単独 repo の README にも人の根拠・実測を載せる方が信頼されやすい（inference）。awesome-list ごとの流入データは見つからなかった。

### D. 既存 2 版の内部状態（ローカル Read、L4）
- 記事版: ~/MyAI_Lab/zenn-content/.claude/skills/writing-ecosystem/references/persona-read.md。判断の言い直しを 一致 / ずれ / 欠落 で照合、比較記事は両順で読む、drift_count.py が数値・最上級・限定句・英字固有名を数え exit 1 で著者確認、最大 3 周。
- README 版: ~/.claude/skills/readme-writer/references/visitor-read.md。would_try 判定、Step 1 で著者が人選を確認、drift 計測なし。
- ~/MyAI_Lab/zenn-content/scripts/drift_count.py: 96 行、stdlib のみ。最上級・限定句の語彙は日本語のみ → 英語文書には移せない（語彙の差し替えが要る）。
- 両版の共通核は「spawn + JSON + 意図照合 + 計数」で、記事 = 判断が伝わったか、README = 試したくなるかが差分（adversarial の指摘。汎用版が特化 2 版より薄くなる設計リスクは根拠資料なし）。

### Not in scope（awesome-list、著者判断 2026-10-18）
別ルーティンが担うため調査しない。awesome-lists.md に 4 list（hesreallyhim / travisvn / VoltAgent / ComposioHQ）の投稿条件の要約があるが、本 report では使わない。1 点だけ設計に関わる: ComposioHQ 系は list 内に skill folder を置く形式で、単独 repo link が合わない可能性（未確認）。

## Contradictions
1. 隔離の有力候補: distribution notes は docs 記述から `--safe-mode`（subscription で動く、全カスタマイズ無効）を documented な有力候補とした。主ループの実測 L2 では --safe-mode で `# userEmail` / `# Environment` / `# Language` の 3 節が読み手に見えた。一方 L1（`--setting-sources "" --strict-mcp-config --tools "" --system-prompt`）は同じ問いで NONE。実測が強い（一次・同日・同版）。ただし L1 の `--setting-sources ""` は docs に意味が無く（L3）、保証は版依存。--safe-mode 単体の docs 記述は漏れを示唆していなかった。
2. Loop-Back の「検証できる manager だけ効いた」: validity notes は abstract に従い支持材料として記述。followup が §単位で照合し、実験では検証能力を操作しておらず UNSUPPORTED（§5 の設計則）と判明。followup が強い（本文 HTML、ただし fetch 要約）。また「-0.14 /revision」は validity では因果風に読めるが followup では相関（PARTIAL）。→ 本 report は followup を採った。
3. 競合の隔離度: prior-art は「process 隔離なし」と推測（stars・date 不明、tool 権限は記述なし）、followup は Agent-tool subagent で情報差し止めと確認。followup が詳しい。一致する結論: persona-review は process 隔離ではない。
4. 競合の新しさ: prior-art は teach-back / 言い直し照合を「記述なし」としたが、followup が workflow.js で teach-back 3 段採点を確認（correct / partly / wrong）。「言い直し照合は我々だけ」は誤り。後者が強い。drift 計数は両 notes で一致して無し。
5. 登録所の空白: adversarial は「persona README skill 未発見＝ニッチ空き」と弱く推定、prior-art は pvliesdonk の persona-review（2026-10 merged）を発見。空きは「persona 読解全般」でなく「隔離 + 計数 + 意図照合の組」に限られる。
6. 数値の強度: validity の persona 忠実度の数値（約 0.2、40.8/100 等）は snippet・二次要約のみで、adversarial の persona collapse 群も snippet。notes 間に矛盾は無いが、どれも本文未確認。

## Still unknown
- 3 Sonnet persona が実読者と同じ箇所で止まるか（直接の測定が無い）。同系列（Claude 書き手 × Sonnet 読み手）の偏り。著者定義 persona が縮退しないか。
- `--setting-sources ""` の仕様上の意味と将来の保証。--system-prompt 無しの場合や他 cwd・他版での再現（L1 は 1 版 1 repo）。組み込み skill 22 本 / agent 6 本が読み手の文脈に残る影響。
- persona-review の CLAUDE.md 継承、presets.md / evidence.md / render_report.py の中身、standalone 公開の有無。
- skills.sh / SkillsMP の掲載機序（telemetry で自動か）、Anthropic directory の提出基準（plugins/publish 未読）。
- Codex / agy で tool 無効化・system prompt 差し替え・AGENTS.md 回避の flag（`codex exec --help` 未確認）。--safe-mode の導入版。Claude Code skills docs の残り約 9,870 字。
- Anthropic 公式 skill / built-in に reader persona 相当があるか（直接検索せず）。synthetic-user SaaS / Grammarly 等との重複。
- 汎用版が特化 2 版より薄くなるか、pattern 文書 / blog / eval という別形態の方が適切か（根拠資料なし。notes の見立ては、機械計数と意図照合が最も差別化できる部分）。
- 日本語 drift_count の語彙を英語へ広げたときの精度（未測定）。

kind: external
# SKILL.md `description` をどう設計し、この harness の 54 skill の description をどう再編するか（invocation の選択・長さ・trigger 句・NOT-for 節・JA/EN）。Claude Code の skill listing budget と Matt Pocock の writing-for-agents 指針を踏まえる。as-of 2026-10-09

## Scope searched
- as-of 2026-10-09。統合のため notes 7 本を Read した: spec.md / examples.md / evidence.md / practice.md / adversarial.md / primary-check.md / local-primary.md（`$HOME/.cache/claude-research-notes/2026-10-09-skill-description-practice/`）。この統合では新規 fetch をしていない（矛盾は local-primary.md A で解消した）。
- 一次資料の層は 3 つ。(a) Claude Code 2.1.295 のバンドル JS を `strings` で抽出して全文を読んだもの（local-primary A）。(b) ローカル計測（`/skill-doctor`、`~/.claude.json` skillUsage、`skill-stocktake` の `usage_stats --days 120`）。(c) `gh api` で読んだ mattpocock/skills（HEAD b0618bc、2026-10-08）。
- WebFetch で取った web 資料はすべて小型 summarizer モデルの出力で、引用は byte-exact ではない。spec.md の記録では、同じページを再 fetch すると既定値が食い違った。この点は各項目に書く。
- 見つからなかったもの。(i) 長さ・NOT-for 節・JA/EN 混在が skill 選択精度に与える影響を Opus/Sonnet 5.x で測った制御実験。(ii) 日本語 prompt の trigger 率を測った記事。(iii) changelog 上で budget 導入（報告上は 2.1.129）と上限 250→1536 の変更を示す項目。

## Found

### (1) 基板の仕組み（Claude Code listing budget ほか）
1. **Claude Code 2.1.295 のソース（全文読了、最強の根拠）** — local-primary A。
   - 既定値は `skillListingBudgetFraction`=0.01、`skillListingMaxDescChars`=1536。環境変数 `SLASH_COMMAND_TOOL_CHAR_BUDGET` は budget を直接上書きする。
   - budget = contextWindow × charsPerToken × fraction。charsPerToken は Claude 3.x〜4.6 の model id で 4、それ以外（Claude 5 系）で 3。context window が不明なら 200,000 に fallback する。Opus 5.5 が 1M なら 30,000、200k なら 6,000。
   - 1 entry は `- name: description[ - when_to_use]` の形で、description 部分は 1,536 で "…" 切り。
   - **長さは `Bun.stringWidth` で測る。東アジア全角は幅 2。日本語は 1 字で budget を 2 消費する。**
   - 超過時、bundled skill と `skillOverrides: name-only` の skill は状態を保つ。残りは usage score `usageCount × max(0.5^(daysSinceLastUse/7), 0.1)`（`~/.claude.json` の skillUsage）で並べ、貪欲に「残 budget に収まる description」へフル entry を与える。収まらない skill は名前だけになる。未使用 skill は score 0 で最後になる。**長い description は収まらず、後ろの短い description が収まることがある。**
   - warning 文言は "Skill listing over budget: N skills, M chars > B budget — descriptions will be truncated. Run /skills to disable some, or raise skillListingBudgetFraction in settings."
   - `skillOverrides` の解決は `source === "plugin"` の skill すべてで "on" を返す。plugin skill には個別 override が効かない（`/skill-doctor` の "Plugin skills can't be turned off individually" と一致）。
   - 差異: これは当環境のバイナリそのもの。ただし Opus 5.5 のセッションが 1M window かどうかは直接読んでいない。観測された drop とは整合する。
2. **docs: skills ページ（code.claude.com/docs/en/skills、summarizer 経由、spec.md）**
   - description + `when_to_use` は listing で 1,536 字に切られる。"Write the most important part first: the use case and trigger phrases"。この 2 点は 2 回の fetch で一致した。`skillListingBudgetFraction` は「per-skill 1,536 は変えず、listing に何件入るかを制御する」。
   - `skillOverrides` の値（skills.md の表）は on=name+description、name-only=名前のみ（/ メニューには残る）、user-invocable-only=Claude から隠す、off=どこにも出さない。
   - `disable-model-invocation: true` は "The description is not loaded into context"。`user-invocable: false` は description が context に残る。ローカル観察と一致する。
   - 差異: 数値既定は docs の fetch 間で食い違った（0.1 / 0.15 / unset / 0.01、`skillListingMaxDescChars` も 500 / 200 / 1536）。**上記 1 のソースが正であり、docs の fetch 値は採らない。** 当環境の最大 description（1,379 字）は per-skill cap 未満。
3. **ranking と drop の二次裏付け** — claudefa.st（blog、日付なし）と Classmethod 2026-05-17（https://dev.classmethod.jp/articles/claude-code-skill-context-budget/、5 個のダミー skill で budget を 0.0005 にして 8 件の description が落ちるのを確認した小実験）が、使用頻度の低い skill から description 全体が落ち、名前は残ると述べる。ソース（上記 1）と整合する。Classmethod の「200K で約 2,000 字」は単位が token か字か不明で、ソースの式（200k×3〜4×0.01=6,000〜8,000 字）とは合わない。ソースを採る。
4. **dev.to rulestack 2026-07-27**（https://dev.to/rulestack/too-many-claude-code-skills-how-the-listing-budget-decides-which-descriptions-claude-sees-4a6m、summarizer 経由、機構説明と意見）— 「ratchet」: 静かな skill は description を失ってさらに静かになる。40 skill で約 3,060 token/turn と書く。対策は concrete trigger を前に置く、caveat は末尾だとまず消える、まれな skill は name-only、budget を上げるのは重なりを排除してから。
5. **prompt caching doc**（https://code.claude.com/docs/en/prompt-caching、summarizer 経由）— skill / plugin skill の指示は会話メッセージとして追記され cache を invalidate しない。listing が cache 境界のどちら側にあるかは未記載。サブスクでは金額より context 占有と選択品質の方が効く。MCP tool と違い skill に遅延 search は無く、lazy にする手段は name-only / `disable-model-invocation` だけ。
6. **changelog**（spec.md）— 2.1.287（2026-10-01）: folder 名と SKILL.md の name が違うと listing に両方出る。typed `/skill` 名は `disable-model-invocation` の skill でも skill として Claude に伝わる。2.1.290（2026-10-05）: subagent の `skills` field は最大 32 個を preload する。
7. **Agent Skills spec / API best-practices**（agentskills.io/specification、platform.claude.com best-practices、いずれも全文読了）— description は 1〜1,024 字、"what + when"、具体的キーワード、三人称。metadata は 1 skill あたり約 100 token。例は 1〜2 文の "Use when ..."。**NOT-for 節にも多言語にも言及が無い。** Claude Code の cap（1,536）は spec より緩い。当環境の 1,379 字の description は、API にアップロードしたり `skills-ref` で検証したりすると 1,024 を超えて違反になる。
8. **旧 250 字 cap**（anthropics/skills issue 881、2026-04-07 open、snippet のみ）— 当時の docs は 250 字で切ると記載し、末尾の "DO NOT TRIGGER when" 節が切れたのが苦情の内容。上限は途中で変わった（changelog では未特定）。どの cap でも末尾の否定節が最初に失われる。

### (2) この harness の実測（local-primary B）
- model-invoked skill は 40 個（54 個のうち 14 個が `disable-model-invocation: true`）。その listing entry の合計は幅 24,203（21,271 字）で、30,000 budget の 81%。plugin と claude.ai 同期 skill を足す前の値。
- `/skill-doctor`（2026-10-09）: 94 skill が load され、45 が description 付きで listed（約 20〜360 tok）、29 が name-only（`< 20`）、20 が not listed。name-only の集合は未起動 skill で、自作の loop-design-check（1,048 字）・mono-color・repair-discipline・jev-judgment-design を含む。対話セッションでは rules-stocktake と hunk-review も入った。claude.ai 同期 13 skill は未起動。
- `usage_stats` 120 日、自作 model-invoked で invoke 0 の skill は jev-judgment-design / loop-design-check / mono-color / repair-discipline / review-to-lint（slash は 3）。slash 中心の skill は grill-me 50/15、spawn-session 61/84、release-doi 11/7、learn-eval 12/4、skill-stocktake 7/5（slash/invoke）。`invoke` には自発起動と、rules や他 skill からの命令形配線の起動が混ざっている。
- 含意: 現状でも ranking 下位の長い description は fit せず name-only になっている（loop-design-check の 1,048 字が実例）。その長文は context に載らず、選択も劣化している。slash 中心の skill は `disable-model-invocation: true` にすれば budget をゼロにできる。
- 補足（examples.md、目視推定 ±10%）: 当環境の description は median 約 440 字、800 字超が 10 本。anthropics/skills の median は約 370、superpowers は約 130。

### (3) Matt Pocock 指針（mattpocock/skills、gh api で全文読了、local-primary C）
- 設計の軸は invocation。user-invoked の skill は `disable-model-invocation: true`、description は人間向けの 1 行で、trigger 列挙は削り、context load はゼロ。model-invoked の skill は description がモデル向けで、trigger の分岐を持つ。判定テスト: 「モデルが自律的に手を伸ばして有用か。（再利用はスキルを切り出す理由であって、テストではない）」（`.agents/invocation.md`）。
- description は常時ロードされる「context pointer」で、"earns even harder pruning than the body"。leading word を前に置く。**1 分岐に trigger 1 つ**（1 分岐を言い換えただけの同義語は同じ分岐の書き直しなので畳む）。body が持つ identity は description から切る。
- leading word は pretrained な概念語にする。同じ語を prompt・docs・コードで使うと起動が確実になる。
- 否定: 禁止はその禁止対象の行動をむしろ使いやすくする。肯定形で書く。禁止は hard guardrail に限り、肯定形と組にする。
- context load（常時ロード分）と cognitive load（人間が index になる分。agency の代価）を区別する。cognitive load が積もったら、他 skill を地図にするだけの user-invoked な router skill（ask-matt）で解く。router は hint しか出せない。
- skill 間依存は body に明示的な `Call the Skill tool with "x"` を書く。到達できるのは model-invoked の skill だけで、user-invoked の前提条件は人間に実行を伝える。
- 計測（38 skill）: user-invoked が 23 で median 86 字、model-invoked が 15 で median 179・max 417。否定節は全体で 1 つ（wizard）、`→ other skill` の誘導は 0、英語のみ。trigger 率の数値は無い。**設計上の推論であり、測定ではない。**
- 差異: 当環境の model-invoked 40 本の median は約 440 字で、Pocock の約 2.5 倍。当環境は 14/54=26% が user-invoked 側に倒れているが、slash 中心なのに model-invoked のままの skill が残っているかは未精査。当環境が日本語の使い手であるのに対し、Pocock の corpus は英語のみ。
- 移せる部分: invocation を先に決める → model-invoked だけ trigger を持たせる → 分岐ごとに 1 句。

### (4) その他の実践
1. **anthropics/skills の skill-creator**（https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md、summarizer 経由）— description は「主たる trigger 機構」で、"Claude has a tendency to undertrigger" ので "pushy" に書く。最適化ループ: 20 件の trigger-eval クエリ（should / should-not）、60/40 の train/test、最大 5 回、TEST 点で選ぶ。negative は近い失敗例（keyword を共有するが別の skill を要するもの）が価値を持ち、自明な negative は何も試さない。description 長の規則は見つからない。根拠の種別は vendor 指針で、数値は公開されていない。
2. **Anthropic 公式 skill の実例**（examples.md、11/19 本を目視。長さは推定）— median 約 370、max 約 1,300（claude-api）。docx/xlsx/pptx/pdf は "Use this skill whenever ..." + 作業列挙 + 拡張子 + 利用者の言葉の引用。docx/xlsx だけが "Do NOT use for ..." を持ち、**skill 名ではなく成果物カテゴリで書く**。claude-api は TRIGGER/SKIP ブロックに grep 可能な機械的条件を置く。web-developpeur 2026-06-14（https://www.web-developpeur.com/en/blog/skills-claude-code-patterns-officiels）は、公式 17 skill が NOT-for をほぼ使わず（領域が重ならず、trigger を最大化する設計）、"pushy" だと述べる。
3. **obra/superpowers**（writing-skills/SKILL.md、summarizer 経由。primary-check で再確認し 2 点とも supported）— "Description = When to Use, NOT What the Skill Does"。**description に手順・workflow を要約すると、agent は body を読まず description に従う**（著者の圧力テスト、数値無し）。"Max 1024 characters"、"keep under 500 characters if possible"（500 は description、1024 は frontmatter 全体との読みが primary-check に残る）。実例 11 本は median 約 130 字、max 約 270、すべて "Use when <situation>" の 1 文、否定無し、日本語無し。差異: 当環境は「NOT for → skill-y」の skill 名誘導、手順要約、JA/EN の二重書きをしており、sample にどれも前例が無い。
4. **Codex / ChatGPT skills docs**（https://learn.chatgpt.com/docs/build-skills、summarizer 経由）— 初期 skill 一覧は context の 2% か不明時 8,000 字を使う。多いときは**まず description を縮め、それでも足りなければ skill を省略して警告する**。"Front-load the key use case and trigger words"、"exactly when this skill should and should not trigger" を明示する。Claude Code と違って「description が縮む」段階がある。ソース（上記 (1)-1）では Claude Code は縮めず、フル entry か名前のみの二択なので、前置き設計の理由が違う（Codex は縮小対策、Claude Code は fit するか否か）。
5. **実務家の合意**（practice.md、意見〜小実験。低〜中の根拠）— concrete trigger を前に、NOT-for は最後（最初に失われる）。NOT-for は重なりのある skill か、観測された誤起動の後だけにする（smartscope.blog 2026-07-21 は「予防的には書かない」）。stationx（2026-10、https://app.stationx.net/articles/claude-code-skills）は、曖昧な語で誤起動 2/9、具体的な語で 0/9（極小 n）。HAL の例（約 2,000 command + 42 skill で 2,004/2,028 が `disable-model-invocation: true`）は、model-visible を小集合に絞る運用の傍証。長さ vs 選択精度を測った実務家は見つからなかった。

### (5) 実証データ
1. **Skill Scaling Laws（arXiv 2601.04748 v1）** — 制御ライブラリ 5〜200 skill、GPT-4o / 4o-mini のみ、合成 skill。精度は ≤20 skill で 90% 超、30 超で徐々に劣化し、200 で約 20%。half-max の容量閾値 κ は約 83.5〜91.8 skill（primary-check は、evidence の「~50-100」を緩い言い方と修正）。**混同しやすさが主因**: 競合なしなら 20 skill で 100%、競合 1 つで −7〜−30%、2 つで −17〜−63%（ただし数も単独で劣化させるので「数は無関係」とは言えない）。階層ルーティングは |S|≥60 で 4o-mini +37〜40pt、4o +9〜10pt。長さの項（§5.4）は「policy 複雑度」約 30/100/300 token で差なし。**操作された変数は instruction/policy の文で、各 skill の description 長そのものとは限らず、raw 確認が済んでいない。** 差異: Opus/Sonnet 5.5 ではなく旧型・小型、合成 skill。当環境は約 70 skill（54+plugin 約 15）で閾値付近、かつ review/implementation chain などが意味的に近い。移せるのは「長さの調整より重なりの整理・disambiguation が効く」という方向性だけ。
2. **MCP tool description の smell（arXiv 2602.14878v1）** — 856 tool / 103 server。97.1% に smell。全要素を補強すると成功率中央値 +5.85pp、ただし実行ステップ +67.46%、16.67% で退行。Examples を外しても有意な悪化なし。測ったのは選択ではなく実行成功で、モデルは非 Claude。長くしても戻りは混合、という程度。
3. **Trace-Free+（arXiv 2602.20426）** — 書き換えた description で複数ステップ成功率 44.6% vs 33.5%。候補 150 以上で劣化が小さい。長さの効果は報告していない。fine-tuned rewriter、API tool が対象。
4. **SkillRouter（arXiv 2603.22455 / snippet では 2604.04323 と表記がずれる）** — 約 80K skill で body を隠すと routing 精度が 29〜44pt 落ちる。embedding 検索であり、LLM が 70 個の一覧から選ぶ場面とは別。弱い転用。**SkillsBench（arXiv 2602.12670、abstract のみ）** は body の価値の測定（curated skill +16.2pp、focused な 2〜3 module が包括 doc に勝つ）で、description には間接的。
5. **description の否定的な書き方で当該 tool が選ばれなくなる**（arXiv 2505.18135、snippet のみ）— 「worst tool, should not be called」のような否定枠は選択をほぼ消し、Opus は tool 使用自体を抑えた。「他の仕事には使わない」という範囲指定の NOT-for は別の事例で未検証。Pocock の「禁止は禁止対象を使いやすくする」とは方向の違う根拠（対象が自分自身か他者か）。
6. **起動率（実務家、Haiku・少数 skill）** — Scott Spence 2025-11-16（https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably、fetch 済み）: Haiku 4.5・4 skill・200 超の試行で、baseline 約 50%、単純な指示 hook 20%、LLM 評価 hook 80%、forced-eval hook 84%。description 文は変えていない。Seleznov 2026-02 Medium（検索要約のみ）: 650 試行、directive な "ALWAYS invoke this skill when..." が hook なしで 100%、passive 文は hook ありで 37%。いずれも小規模・旧型で、directive 説は一次未確認。当環境の内部測定（description 文の編集で自己起動 27%→8% の revert）と合わせ、**description の文言は弱いレバーで、挙動を決めるのは hook / 命令形配線**という読みが成り立つ（実務家レベルの根拠）。
7. 制御された長さ実験は無い: Opus/Sonnet 5.x で約 70 skill に対して description 長（150/450/1000 字）を振った実験、NOT-for 節の過小/過大起動への効果、JA/EN 二重書きの効果は、いずれも見つからなかった（空白であって否定ではない）。

### (6) 多言語
1. **anthropics/claude-code #68086**（2026-06-12 open、2026-07-25 に not planned で close。https://claudeissues.com/ 経由で fetch、単一の自己申告）— 繁体字中国語で作業する利用者の skill が、英語のみの trigger 句だと 45 日間 1 度も起動しなかった。「母語 trigger を足すと直った」は、practice.md は supported とし、primary-check は summarizer が取れず **UNVERIFIED** とした（要 raw 確認: `gh issue view 68086 --comments`）。close の日付と maintainer コメントも未確認。公式の多言語 trigger 機構は無いと読める。
2. smartscope.blog（日本語、2026-07-21）— 英語の description は他言語の prompt でも効く。日本語が主なら、評価ケースに実際の日本語表現を使う（description を二言語にするのではなく）。serverworks（2026-06-09）— 利用者が実際に言う句（「調査して」/ "investigate"）を入れる。いずれも意見で、日本語 trigger 率の測定は無い。search 要約由来の `[EN] ... [JA] ...` 併記パターンは出所未確認。
3. 関数呼び出しの多言語研究（ITC、MLCL arXiv 2603.05515、snippet のみ）が示す主な失敗は引数値の言語不一致で、選択ではない。description の言語と query の言語の一致が選択に効くかの証拠は無い。
4. 公式 spec・API best-practices・Pocock 38 本・superpowers・Anthropic 公式 11 本に日本語の例は無い。
5. **字幅の効果（(1)-1 より）: 日本語 1 字は budget 2 消費。** 同じ内容を JA/EN で二重に書くと、英語 1 に対し日本語が約 2 倍の幅を占める。この不均衡は一次資料（ソース）でしか見えない点で、web 側の記事は誰も言及していない。

## Contradictions
1. **budget の既定値**: spec.md（skills.md fetch が 0.1、settings-reference が 0.15・`skillListingMaxDescChars`=500 または unset、最初の fetch は 1%）、adversarial.md（claudefa.st 由来の 0.01 と 1536 で、fallback 約 8,000 字・「budget は字数」・200k で約 8k 字）、practice.md（Classmethod の「200K で約 2,000 字」）は互いに食い違っていた。**local-primary.md A（2.1.295 のソースを全文読了）が優先する**: 0.01 / 1536、式は window × charsPerToken(3 または 4) × fraction、fallback は window 200,000、unit は字数、幅は `Bun.stringWidth`。Opus 5.5 が 1M なら 30,000 字、200k なら 6,000 字。adversarial の「200k で約 8k 字」は charsPerToken=4 の旧 model id の値で、Claude 5 系（3）なら 6,000 になる。「約 8,000 字の fallback」はソースの記述と別物で、採らない。docs の summarizer 出力が 0.1 / 0.15 / unset とばらついたのは summarizer の不安定さと見て、docs 文面は数値の根拠にしない。
2. **ranking の規則**: 二次資料は「使用頻度の低い順」「最近使われていない順」と言い、一次のソースは `usageCount × max(0.5^(days/7), 0.1)` による貪欲 fit だと示す。ソースが強い。このため「最も使われない skill が必ず先に落ちる」わけではなく、長い description は短い後続より先に落ちうる。
3. **truncation の順序**: Codex docs は「description を縮めてから skill を省略」。Claude Code のソースは「フル entry か名前のみ」で、description の部分短縮は per-skill 1,536 の cut だけ。docs の文面（"shortens descriptions to fit"）はやや紛らわしい。ソースを採る。
4. **旧 cap**: issue 881 は 250 字（当時）、docs は 1,536。changelog で変更を特定できていない。現在値は 1,536（ソース）。
5. **NOT-for の効果**: 実務家は重なる skill には書くべき（Skill Scaling Laws の混同しやすさ、rulestack）と言い、公式 skill はほぼ書かず、Pocock は禁止は逆効果で肯定形を勧め（否定節は全体で 1）、smartscope は誤起動の後だけに限る。どの側にも Claude 5 系での測定が無く、根拠の強さは同等に弱い。Anthropic が書く場合はカテゴリ単位で、skill 名誘導ではない。
6. **description の長さ**: skill-creator は pushy・trigger 列挙を勧めるのに対し、superpowers（500 字以下が目安）と Pocock（179 字 median）は短さ、手順要約の排除を勧める。MCP 論文は長くしても戻りは混合。長さの制御実験が無いため決着しない。budget 制約下では、長い description は fit せず名前のみになる損が確実にある点だけは、ソースで確定している。
7. **Skill Scaling Laws の閾値**: evidence.md の「劣化は ~50 から急、~100 で閾値」を primary-check が「onset 約 30、half-max 約 84〜92」と修正した。後者を採る。「数ではなく混同が主因」も「数も単独で効く」に弱める。
8. **#68086 の「直った」**: practice.md は supported、primary-check は UNVERIFIED。raw 確認まで不確かとして扱う。
9. **SkillRouter の arXiv 番号**: 2603.22455（evidence）と 2604.04323（adversarial）が食い違う。どちらも間接的な根拠のため、番号は未確定のままにして、転用はしない。

## Still unknown
- Opus 5.5 / Sonnet 5.5 のこのセッションが実際に 1M window か（budget 30,000 か 6,000 か）。ソースの式は読んだが、window の値は直接読んでいない。判別: debug log の "Skill listing over budget: N skills, M chars > B" の B。
- `skillOverrides: name-only` が user / project 設定で有効か（issue 50631 の「効かない」報告が修正されたか。ソースは bundled と name-only を状態保持と記すので有効と読めるが、動作確認は未実施）。plugin skill には効かない点は確定。
- listing が prompt cache 境界のどちら側にあるか。
- name-only の skill がモデルから名前だけで選ばれる品質。
- 自発起動と配線起動の内訳（`invoke` は混在）。slash 中心の skill のうち model-invoked のまま残っている数。
- Opus/Sonnet 5.x・約 70 skill で description 長 / NOT-for / JA-EN 二重書きが選択に与える効果（制御実験なし。やるなら skill-creator の trigger-eval ループか `/claude-api build-eval` で自前に測る）。日本語 prompt の trigger 率の測定も無い。
- Skill Scaling Laws §5.4 の操作変数が description 長か policy 文か（raw 未確認）。
- #68086 の close 日・maintainer コメント・「直った」の有無。
- 当環境の 54 skill の正確な字数（examples.md は目視推定、local-primary B の集計が正）。
- 引用の byte-exact 確認: web 資料の引用はすべて summarizer 経由で、決定に使うなら raw を再確認する。

kind: external
# 実装を「文脈を持つ agent が自分で行う」か「fresh な委譲先に packet を渡して行わせる」か、各々が勝つ条件は何か。あわせて常駐層を強いモデル向けにどう絞るか（as-of 2026-11-07）

背景: 前回の関連調査 `docs/plans/research/2026-10-26-subagent-fold.md` は既読扱い。本 report は再要約せず、その後に確かめた一次資料と測定だけを載せる。

対象環境: 個人 Claude Code harness（CLI 2.1.319、主モデル Opus 5.5 effort high、セッションの約 17% が Fable 5.1）。notes は 8 角度（anthropic-guidance / practitioner-practice / measured-evidence / resident-context-guidance / adversarial / model-guides / memory-loading / subagent-mechanics）で、各々に -verify がある。-verify が notes を訂正した箇所は verify 側を採った（下記 Contradictions）。読みの区別は「全文」＝ページ本文を取得して通読、「要約経由」＝WebFetch の小モデル抽出、「abstract」＝arXiv abstract ページのみ、「snippet」＝検索結果のみ。WebFetch は全て小モデル経由の抽出で、逐語の保証はない。

## Scope searched

- 一次: code.claude.com docs（sub-agents, best-practices, context-window, memory, skills, hooks, worktrees, agents, agent-view, agent-teams, claude-code-on-the-web, tools-reference, 2.1.309–2.1.319 の changelog）、platform.claude.com（Opus 5 / Opus 5.5 / Fable 5 / Fable 5.1 prompting guide、whats-new、optimizing-for-cost-and-intelligence の前半 100K/202K 字、best-practices hub）、claude.com / claude.dev / anthropic.com engineering の記事、arXiv 十数本（多くは abstract のみ）、実践者・vendor の blog と docs（Cognition、Amp、TinyFish、Cursor、Codex、Factory ほか）。
- 検索しても見つからなかったもの: 同一 coding task を「文脈を持つ実装者」と「packet だけを受けた fresh 実装者」で直接比べた公開の測定。fork（親文脈を継ぐ）と空文脈 subagent の品質 ablation。handoff の情報損失を Opus 5.x / Fable 5.x で測った値。Opus 5.5 世代の context rot の独立測定。「文脈を持つ agent が実装せよ」と明言する Anthropic の primary 発言（Sep–Nov 2026）。
- 読み切れていないもの: cost page の後半 102K 字、Fable 5.1 の model card / system card、Opus 5.5 の model card、hooks ページの 100K 字以降、settings-reference の `skillListingBudgetFraction` 既定値 entry、Cherny の YC 動画（2026-07-27）の transcript、changelog 2.1.290–2.1.308。
- 日本語圏の 2026 実践記事は検索に出なかった（代替として韓国語記事 1 本）。

## Found

### (A) 誰が実装するか

**A1. Claude Code 公式 docs の既定は「主 loop が実装し、委譲は並列・ノイズ隔離・独立 review のため」**
- https://code.claude.com/docs/en/best-practices と https://code.claude.com/docs/en/sub-agents（2026-11-07 取得、sub-agents は先頭 100K 字と末尾 16.7K 字の 2 回に分けて読み、best-practices は取得全文を grep で確認）。根拠種別: 公式 guidance（設計の記述で、測定値は無い）。
- 主会話を使う条件（逐語）: "Multiple phases share significant context, such as planning, implementation, and testing"、"Latency matters. A subagent that isn't a fork starts fresh and may need time to gather context"。subagent は "self-contained and can return a summary" のとき。best-practices: "Handing the same task to a subagent doesn't make the answer any better. A fresh reviewer does help, because it hasn't seen your reasoning, which is a different thing from delegating." "a fresh subagent first has to gather context your conversation already had, so it can end up slower than doing the task where you are." "Running out of context is rarely the problem anymore"（1M window、compaction は自動、`/clear` は task 間でなお有益だが理由は集中とコスト）。
- fresh な builder を支持する唯一の記述: SPEC.md を書いた後 "start a fresh session to build from it, so the build begins with a clean context and a written definition of done"。cloud docs（https://code.claude.com/docs/en/claude-code-on-the-web、全文）も "Plan locally, execute in the cloud ... save the plan to the repo, commit, and push"（packet は commit 済みの plan file）。
- こちらとの違い: こちらの「判断役が packet を書き fresh な build に渡す」は docs が「遅く文脈が乏しい経路」と位置づける形であり、docs が推すのは "written spec" がある場合の fresh session build と、独立 review の fresh 化。docs は実装者の置き場を一括で決めてはいない。

**A2. fork と worktree の仕様（文脈保持と隔離は別軸）**
- https://code.claude.com/docs/en/sub-agents（fork 節は末尾 16.7K 字にあり、-verify で確認）、https://code.claude.com/docs/en/worktrees（全文）、https://code.claude.com/docs/en/tools-reference（EnterWorktree 節）。2026-11-07。公式仕様。
- fork は system prompt・tools・model・全会話履歴を継ぐ。fork の tool call は主文脈に入らず最終結果だけ戻る。最初の request は親の prompt cache を再利用し "a fork costs less than a fresh subagent for tasks that need the same context"。fork の model は主 session と同じ（per-fork の model 選択なし）。fork は fork を起こせない。`/subtask` で手動起動。fork mode は v2.1.302 から既定 ON（interactive terminal は v2.1.232 から）。無効化は `CLAUDE_CODE_FORK_SUBAGENT=0`、fork だけ止めるなら permissions.deny に `Agent(fork)`。
- fork + `isolation: "worktree"` は docs に明記: "When Claude spawns a fork through the Agent tool, it can pass isolation: "worktree" so the fork's file edits are written to a separate git worktree"。
- worktree の base は既定 `worktree.baseRef: "fresh"`（remote の既定 branch、origin/HEAD。remote が無ければ local HEAD に退く）。`"head"` にすると local HEAD（未 push commit を含む）から分岐。未 commit の変更は worktree に入らない。subagent の worktree も同じ base。worktree の subagent は instruction files を主会話から取り、worktree 根の CLAUDE.md / .claude/rules は読まない。
- EnterWorktree / ExitWorktree は同じ会話のまま cwd・write access・CLAUDE.md / settings を worktree に移す。hook の `${CLAUDE_PROJECT_DIR}` は元の root のまま、hook input の `cwd` は worktree に追従。ExitWorktree は `isolation: worktree` で既に自分の作業 dir にいる subagent には使えない。EnterWorktree 後の auto memory / `plansDirectory` の解決は docs に記述なし。
- こちらとの違い: 文脈保持（fork / 主 loop）と隔離（worktree）は独立に選べる。ローカル main や task branch 上の未 push 作業を worktree に見せるには `baseRef: "head"` が要る（既定のままだと見えない）。fork は親 model 固定なので、Fable 判断役が fork すると実装も Fable の単価になる。

**A3. Anthropic の model guide は「委譲は大きく独立した塊のみ、小さい仕事は自分で」「文脈を跨ぐ作業は直接やる」**
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 （全文、undated）、…/prompting-claude-opus-5-5 （全文、undated）、…/claude-prompting-best-practices（該当節のみ）。2026-11-07。公式 guidance（"in Anthropic's testing" の主張に数値は無い）。
- Opus 5: "delegates to subagents more readily than prior models. Delegation is worthwhile for genuinely independent, sizeable tracks of work, but it multiplies cost and time when applied to small tasks." 例示の抑止文: "Do not delegate work you can finish yourself in a handful of tool calls, and do not use subagents to verify or double-check your own work." "performs best when given the complete task specification up front and left to run."
- hub の抑止文例: "For simple tasks, sequential operations, single-file edits, or tasks where you need to maintain context across steps, work directly rather than delegating."（文脈保持者が直接やる、に最も近い一文）。
- Opus 5.5 page は "Existing Claude Opus 5 prompts should perform well without changes, and the patterns in Prompting Claude Opus 5 remain a reasonable starting point" と述べ、subagent と verification の記述を撤回も再掲もしない。5.5 は "sustains long-running autonomous work better than Claude Opus 5 ... end to end with parallel subagents and little oversight"。
- 無人実行（5.5 page）: text-only の turn 終了は report として扱い、checklist を持ち、自動継続は 2–3 回まで。起動済みの background command / subagent が動いている間は未完了とみなす。
- 同 page の Fable 5 版（…/prompting-claude-fable-5、-verify で全文）: "Claude Fable 5 dispatches parallel subagents more readily than prior models. Use subagents frequently, provide explicit guidance about when delegation is appropriate"、"Long-lived subagents that keep their context across subtasks save time and cost through cache reads"。Fable 5.1 の page（…/prompting-claude-fable-5-1、全文）の subagent 記述は 1 節のみ: lead を待たせず走らせると完了時間が短くなる。**Fable が実装を委譲すべきだという記述は、Fable 5 / 5.1 のどちらの guide にもない。**
- こちらとの違い: guide は API / harness 設計者向けで、「判断役と build 役を別 session にする」構成そのものは扱っていない。

**A4. cost page の数値（vendor 内部 benchmark、方向を示すもの）**
- https://platform.claude.com/docs/en/build-with-claude/optimizing-for-cost-and-intelligence （前半 100K/202K 字、undated、"Claude Fable 5.1's from August" の注記から 2026-09/10 頃と推定）。vendor benchmark、一部単発 run、page 自身が「自分の workload で測れ」と述べる。
- SWE-bench Pro subset: Opus 5.5 は既定 effort で Fable 5.1 の既定と "inside run-to-run noise"、solved task あたりコストは約 1/5。Opus 5.5 の effort 表: low 87.4% / $0.11、medium（既定）92.8% / $0.21、high 95.3% / $0.29、xhigh 96.7%（単発）/ $0.74。Fable 5.1 high は 92.3%（単発）/ $1.19。内部 agentic-coding benchmark（medium）: Fable 5.1 84.2% / $2.68、Opus 5.5 86.6% / $0.84。
- 1 context window を超える仕事（defect search 系）: Opus 5.5 + Sonnet 5.5 subagent は Opus 5.5 単独 session より約 1/3 安く、スコアはほぼ同じ。"Claude Fable 5.1 as the orchestrator in Claude Opus 5.5's place cost 24% more for no measurable gain. Alone, Claude Fable 5.1 cost 2.2 to 3.0 times as much as Claude Opus 5.5 at `high` and scored no higher." Haiku subagent を Opus 5.5 medium に足すと cost/attempt −32%、pass rate 約 −4pt（95% 区間 1.3–7.1）。Opus 5.5 high + Fable 5.1 advisor は 1.7pt 向上で noise の縁、2.1 倍コスト。
- 委譲が負ける条件（逐語）: "When the work is one dependent chain, or fits in a single context without a long cost tail, the orchestrator's model alone at lower effort came out ahead in every case measured on earlier models." -verify の訂正: この測定は BrowseComp の難しい側と DeepWideSearch（検索 task）で、coding ではなく、Opus 5.5 でもない。
- 「Fable session は実装を委譲する」という著者の方針は、この page の Fable の単価（Opus 5.5 high の 2.2–3.0 倍で高スコアにならない）に基づく著者の方針であり、guide の推奨ではない。page が試した安い委譲先は小さい model（Sonnet 5.5 / Haiku）を Opus の subagent にする構成で、「Fable が判断し fresh な Opus が build する」構成は試していない。page の測定は委譲先の model を変えた比較で、fresh と継承文脈の比較ではない。

**A5. 「委譲を畳む」議論（vendor guidance、deployment 逸話）**
- https://claude.com/blog/building-agents-when-to-fold-subagents-into-your-main-agent-loop （2026-10-22、要約経由、-verify で確認）。subagent は "lossy handoffs"（"telephone game"）を生む。subagent が居場所を持つ条件は、単一 loop で context bloat による劣化が測れる、並列 task に捨てられる新しい window が要る、tool 選択や相反する指示で困る、検証・権限分離。"roughly 2x faster" は無名の 1 顧客、">80%" は Claude Code の system prompt 縮小で task 性能ではない。いずれも controlled benchmark ではなく、handoff 損失の数値ではない。
- 同 blog https://claude.com/blog/how-and-when-to-use-subagents-in-claude-code （2026-04-07、extractor 経由）: "a single session handling the chain is usually cleaner than a relay of subagents passing state through files"、独立 review subagent は "without knowing what tradeoffs were considered"。Opus 5 世代より前の記述。
- こちらとの違い: 機能別 orchestrator 分割（billing / support 等）への批判が中心で、coding task を fresh session に渡す是非を直接扱わない。移せるのは「1 つずつ畳み、eval で確かめる」手順。

**A6. Anthropic engineering: 世代で消える workaround**
- https://www.anthropic.com/engineering/harness-design-long-running-apps （2026-03-24、要約経由、-verify で確認）。単一事例の運用記録でコスト数値付き。Sonnet 4.5 の context anxiety には reset + 構造化 handoff が必要だったが "Opus 4.5 largely removed that behavior on its own, so I was able to drop context resets from this harness entirely"。evaluator の分離は強いレバーだが "current model が単独で確実にできない境界の外" でのみ元が取れ、4.6 では境界が動いて終端 1 回の評価に縮んだ（solo 20 分 / $9 vs full harness 6 時間 / $200、Opus 4.5 run）。
- こちらとの違い: Opus 5.5 での再測定はない。reset の必要性は世代依存と明言されている一方、評価者分離の価値も同じく世代依存と明言されている（境界の外でのみ有効）。

**A7. 実践者・vendor（運用報告と意見。勝敗を決める対照実験を公開した所は無い）**
- Cognition「Multi-Agents: What's Actually Working」（Walden Yan、2026-04-22、https://cognition.com/blog/multi-agents-working、要約経由）: 書き込みは単一 thread。generator-verifier では coder と reviewer が事前に文脈を共有しない方が良い（clean context、shared bias は訓練由来）。smart friend は親の full context の fork を共有する「80/20」。manager-child の初期不具合は manager の過剰指示・共有 state の誤想定・戻りの連絡が既定で無い。Devin Review は PR 平均 2 件のバグ、約 58% が severe（自社統計、clean vs shared の比較なし）。2025-06「Don't Build Multi-Agents」（https://cognition.com/blog/dont-build-multi-agents）は 2026-04 の続報で、原則は不変と本人が述べる。
- TinyFish（2026-07-01、https://www.tinyfish.ai/blog/agentic-coding-context-vs-tokens-subagents、全文）: fresh subagent は "re-discovery tax" で総 token が最大。fresh が正解なのは共有文脈が少ない独立 task で hard isolation が欲しい場合のみ。long-lived fork が "most underused move"。測定なし、web-data 事業者の逸話。
- Amp「Handoff」（2025-10-23、https://ampcode.com/news/handoff、全文）と Tessl 解説（2025-11-14）: compaction は lossy、要約でなく次の仕事に要るものを抽出した開始 prompt を人が編集して新 thread へ。測定なし。
- Factory「Missions」（https://factory.com/news/missions、要約経由、公開日は page の byline が "February 26, 2025" で内容と合わず未確定）: feature ごとに fresh worker session、milestone ごとに validator、git が真実。自社 telemetry で mission の median 約 2 時間・37% が 4 時間超・median token は通常 session の 12 倍。fresh vs 継続 session の対照はない。こちらの task より 1〜2 桁長い。
- Simon Willison（2026-03 前後、https://simonwillison.net/guides/agentic-engineering-patterns/subagents/、要約経由）: 並列 subagent が効くのは互いに依存しない複数 file の編集。Codex docs（https://learn.chatgpt.com/docs/agent-configuration/subagents、全文）: 並列は read-heavy が主で write-heavy は衝突に注意、worker role（実装）は存在する。Cursor docs（https://cursor.com/docs/subagents、全文）: subagent は親の会話履歴を見ず clean で始まる、isolation は worktree か cloud VM、fork に当たる機能は docs に無い。Mitchell Hashimoto（Willison 経由 2026-02-05、要約）: 委譲は結果が予見できる task から。Yegge の Gas Town は二次資料の snippet のみ。
- 読み（practitioner 角度の整理）: 「委譲をやめる」という潮流の一次発信は見つからず、見つかった形は (i) 書き込みは単一 thread で読む・検証する者を切り出す、(ii) 文脈を継ぐ fork を使う、(iii) 長命 thread を畳んで抽出した packet で新 thread、の 3 つ。勝敗の軸として挙がるのは共有文脈の量、task の長さ、milestone 検証の可否、reviewer の独立性。

**A8. 測定: 文脈の持ち方と引き継ぎ**
- Handoff Debt（arXiv:2606.02875、Dipesh KC & Budathoki、v1 2026-06-01 / v2 2026-08-30、abstract、-verify で確認）: 75 source task → 181 handoff-point task、後続 3 model × 724 run。**文脈つきの引き継ぎは repo のみの引き継ぎに対し median agent events を 20–59%、累積 prompt token を 42–63% 減らした。**（notes の最初の版はこの基準が逆。repo のみの超過は 25–145% / 72–170% に当たる。）solve rate の差は小さくモデル依存で効率差は一貫。4 view（repo state / raw trace / summary notes / structured notes）の内訳と後続モデル名は abstract に無い。実験設定は中断→別 agent への引き継ぎ間の比較で、同一 agent の継続との比較ではない。
- CooperBench（arXiv:2601.13295、Stanford/SAP、v1 2026-01-19 / v2 01-26、本文要約・abstract で確認）: 2 agent が別 feature を並列実装して merge する協調は、1 agent が両方を実装する Solo より平均約 30% 低い。失敗は expectation 42% / commitment 32% / communication 26%（手動 50 trace）、症状は作業重複 33.2% / 設計の乖離 29.7%。通信量を増やしても成功率は有意に変わらない（net Δ −0.5pt）。task は小さく（平均 52 行・1.4 file）、並列協調で、逐次の単一 task の委譲とは設計が違う。
- Towards a Science of Scaling Agent Systems（arXiv:2512.08296、Google/MIT、2025-12-09、abstract）: 並列化可能 task で最大 +80.8%、逐次 task で最大 −70.0%。構成数が検索結果で 180、abstract 要約で 260 と食い違い未解決。coding benchmark は含まない。
- CAID（arXiv:2603.21489、Geng & Neubig、2026-03-23、abstract）: 依存を考慮した計画 + git worktree 隔離 + 並行実行 + merge で single-agent 比 PaperBench +25.6pt、Commit0 +14.7pt。長く依存が多く並列化できる仕事。
- Single-Agent vs Multi-Agent 等 token 予算（arXiv:2604.02460、2026-04-02、abstract）: multi-hop reasoning で thinking token を揃えると single が multi に並ぶかそれ以上。coding ではない。
- Anthropic multi-agent research system（公開 2025-06-13、https://www.anthropic.com/engineering/multi-agent-research-system、要約経由、-verify で確認）: Opus 4 lead + Sonnet 4 subagent が単独 Opus 4 を内部 research eval で 90.2% 上回る（再現不可）、token は chat の約 4 倍・multi-agent 約 15 倍。同記事の自己制限（逐語）: 全 agent が同じ文脈を共有すべき領域は不向きで、"most coding tasks involve fewer truly parallelizable tasks than research"。
- Agyn（arXiv:2602.01465、snippet のみ）: SWE-bench 500 で役割分担 team 72.2%（資料により 72.4%）、baseline との差は資料で 7.2–7.4pt と食い違い、OpenHands との差は 0.4pt 程度。vendor 自己報告で、token 予算を揃えた ablation ではない。MAST（arXiv:2503.13657、abstract）は multi-agent の失敗型の目録（14 mode、3 category）で効果量ではない。
- 文脈の劣化:
  - How Fast Do Agents Rot?（arXiv:2609.01660、2026-08-31、abstract）: 成功率は step 数に対して幾何的に減衰し、劣化を駆動するのは文脈長でなく step 数。context window を絞ると減衰は急になった（logit slope −0.69 vs −0.44）。coding agent ではなく合成 task。p 値の表記は abstract で崩れており要 PDF 確認。
  - Chroma "Context Rot"（2025-07、https://research.trychroma.com/context-rot、要約経由）: 18 model（Opus 4 世代）で入力長が増えると不均一に低下。agentic / coding task は評価していない。
  - McMillan（arXiv:2605.10039、2026-05-11、abstract）: Claude Code CLI 1,650 session で、1 session で生成する function が 1 つ増えるごとに設定ファイル中の 1 規則の遵守 odds が約 5.6% 低下（OR 0.944、2 つの codebase で再現、Opus 4.6 世代）。事前登録でなく分析中に見つかった効果。この集合で唯一の、長い session 内の劣化の測定。規則は 1 つの簡単な annotation（notes の caveat、abstract では未再確認）。
  - LLMs Get Lost In Multi-Turn（arXiv:2505.06120、ICLR 2026 oral、snippet）: 段階的に情報を渡す multi-turn は単発の fully-specified より平均 −39%。全情報を 1 turn で渡すと baseline の約 95%。含意は packet に全情報を最初に 1 回で渡す設計の側（推論）。
  - SWE-Marathon（arXiv:2606.07682、abstract）: 平均 27.2M token の超長期 task。1 task 級の実装とは桁が違う。LOCA-bench / Long-Horizon Task Mirage は snippet のみ、数値未確認。
- 取らなかった数値: 出所不明の「Stanford HAI 156 coding tasks」「45% 閾値則」「5x 効率」（dev.to のみ）、ConstraintRot の「0%→30%/59%」（blog 経由のみ）、background agent の merge 率 67% と 2–3x 高速化（出所不明）。
- METR RCT（2025-07、snippet）: 経験豊富な OSS 開発者 16 人・246 task で AI 使用が約 19% 遅い。autonomous と interactive の比較は無い。

### (B) review と検証の独立性

**B1. 公式 guidance は「fresh な reviewer は効く。ただし自分の仕事を subagent に確認させるのは過剰」**
- best-practices（2026-11-07）: `/code-review` は "reviews the diff in a fresh subagent that never saw your conversation. It isn't swayed by the reasoning that produced the code."、"A second session is also the easiest independent reviewer you can get."。注意書き: 問題を探す reviewer は "will always find something" なので "skip style" と SPEC.md 基準を指定する。Opus 5 guide（全文）: 明示的な検証指示（"use a subagent to verify"）は over-verification を起こすので除く、"legacy harness scaffolding that adds separate verification steps" も同様。Fable 5 guide（-verify で全文）: "Separate, fresh-context verifier subagents tend to outperform self-critique."
- 読み: 2 つの guide は model ごとに逆を向く（Contradictions 参照）。いずれも prompt 内の足場の話で、別 process の commit 前 review のような cross-process の gate は扱っていない（model-guides-verify の指摘）。fresh subagent は own context だが別 OS process とは限らない。第二 session はより強い形（anthropic-guidance の整理）。
- 根拠種別: 公式 guidance（数値なし）。

**B2. 測定は fresh review の優位を決定的には支持しない**
- Cross-Context Review（arXiv:2603.12123、Tae-Eun Song、v1 2026-03-12 / v2 2026-10-01、abstract、-verify で確認）: 30 artifact に注入した 150 誤りで F1 は CCR（fresh session）28.6 / SR（同一 session 自己 review）27.1 / SA（文脈を持つ subagent）23.8 / SR2（自己 review 反復）21.7。有意なのは CCR vs SR2 のみ（Holm 補正 p=0.004）。CCR vs SR は p=0.26、CCR vs SA は p=0.057。v2 は SR の 1 run を検証不能として除外し、v1 の「全 run で順位保持」を不正確と訂正。注入誤りで実バグではない。単著 preprint、model 名は abstract に無い。
- Self-Preference Is Weak or Absent（arXiv:2606.20093、Guey & Bougault、2026-06-18、abstract）: 元の著者文脈の model と fresh model を IFEval の検証可能な修正で比較。author−fresh の差は −5.1pt（95% CI [−12.9, +2.7]）で検出可能な自己選好なし、約 13pt 未満は排除できない（検出力不足）。mid-tier 4 model 族・85 比較、指示追従であり coding review ではない。EMNLP 2026 Findings（https://aclanthology.org/2026.findings-emnlp.1571.pdf、snippet のみ）は self / other のラベルだけで採点が動くと報告。
- Anthropic harness 記事（A6）の "agents reliably skew positive when grading their own work" は同一文脈・同一 agent の話で、別 model 族の reviewer との比較ではない。
- Cognition（A7）は clean context を reviewer の利点として明示するが、clean vs shared の対照はない。

**B3. 実装者が誰でも成立する分離**
- 上の資料（Cognition、docs、Anthropic harness 記事）は reviewer が「実装文脈を見ていない」ことを根拠にしており、実装を誰が行うかを決めない。adversarial 角度の整理は「実装は文脈保持者の単線、review だけ fresh」と「packet で fresh build + fresh review」のどちらとも両立する、というもの。また Cognition が挙げる manager-child の失敗 3 件（過剰 prescriptive・状態共有の誤仮定・戻りの連絡が無い）は packet の点検項目として使える（adversarial の読み）。

### (C) 常駐層と substrate の読み込み仕様

**C1. memory docs: 規模・path 条件・AGENTS.md・auto memory**
- https://code.claude.com/docs/en/memory （2026-11-07、取得全文を通読した notes が 2 件、-verify も取得全文）。公式仕様。
- CLAUDE.md / auto memory は "context, not enforced configuration"（強制は PreToolUse hook）。"target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."（data の引用なしの assertion）。`@import` は "don't reduce its context cost"（本文と同時に展開）。矛盾する指示は "Claude may pick one arbitrarily"。複数手順や一部の領域だけの規則は skill か path-scoped rule へ。
- rules の再帰: `~/.claude/rules/` 配下の `.md` は再帰的に読まれるので `rules/common/*.md` は対象。`rules/README.md` 等の非 rule の `.md` も同様に読まれる。除外は `claudeMdExcludes`（絶対 path glob、user settings 可）。
- `paths:` frontmatter は user-level rule でも有効。base directory は **session の primary working directory**（`~/.claude` ではない）。読み込みは Read / Write / Edit（と単一 file の cat / head）が一致 file に触れたとき。`paths` 無しの rule は launch 時に `.claude/CLAUDE.md` と同優先度で読まれる。`paths` は rule で Claude Code が読む唯一の field で、他の field（現行の `origin` / `rationale` / `review-when`）は error なく無視され、frontmatter は読み込み前に除かれる。YAML が壊れると `paths` 無しとして常駐する。on-demand の path-scoped rule には per-file 上限（200K window: 40,000 字、1M window: 150,000 字、v2.1.309+）。
- user-level の `paths:` を「~/.claude 内作業専用」の switch にできるのは、glob が `~/.claude` にしか無い dir（例 `hooks/**`）を指し、かつ cwd が `~/.claude` のときだけ。同名 dir を持つ他 repo でも発火する（verify の読み）。絶対 path や `~` の pattern が使えるかは docs に無い。
- compaction 後: `paths:` rule と nested CLAUDE.md は message history 内に入るため要約で消え、再 Read で戻る。project-root CLAUDE.md・paths 無し rule・auto memory は disk から再注入。持続させたい rule は `paths:` を外すか project-root CLAUDE.md へ（context-window docs、全文）。
- AGENTS.md: 既定では cwd かその祖先に CLAUDE.md / `.claude/CLAUDE.md` / CLAUDE.local.md が **無いときだけ** AGENTS.md を読む（v2.1.277+）。数えないもの（AGENTS.md と併存する）は `~/.claude/CLAUDE.md`、managed の CLAUDE.md、`.claude/rules/`。`/config` の Project instructions を `claude-md-and-agents-md` にすると両方（CLAUDE.md が先）。cwd の `.claude/CLAUDE.md` を新設すると AGENTS.md は読まれなくなる。
- HTML コメント: CLAUDE.md の block-level コメントは注入前に除かれる（code block 内は保持）。rules / AGENTS.md / MEMORY.md / SKILL.md に及ぶかは docs に無い。
- MEMORY.md: "first 200 lines, or the first 25KB, whichever comes first" を毎会話の開始時に読み、超過分は読まない。この上限は MEMORY.md のみで、CLAUDE.md は 4 MiB 以下なら全文。保存先は `~/.claude/projects/<project>/memory/`（repo 単位、worktree・subdir で共有）。
- docs に記述がなかったこと: cwd が `~/.claude` のとき `~/.claude/CLAUDE.md` が user と project の両方で重複して読まれるか、`~/.claude/.claude/CLAUDE.md` の扱い。docs の表からは `./.claude/CLAUDE.md` が project 扱いになる推論に留まり、実機確認が要る。
- こちらとの違い: こちらの常駐層は `rules/common` の 15 本前後（`paths` なし）+ CLAUDE.md + AGENTS.md + MEMORY.md の長文 index で、docs の規模目安は行数と byte で数値的に突き合わせられる（Local evidence 参照）。

**C2. skill 一覧の予算と skillOverrides**
- https://code.claude.com/docs/en/skills （2026-11-07、全文読了と先頭 100K 字の 2 件）。公式仕様。
- listing は全 skill の名前を必ず含み、overflow 時は description を落とす。予算は context window の 1%、落とす順は使用が少ない skill から。`skillListingBudgetFraction`（例 0.02）または環境変数 `SLASH_COMMAND_TOOL_CHAR_BUDGET`（固定文字数）で調整。1 entry の description + when_to_use は 1,536 字で cap（`skillListingMaxDescChars` で変更）。SKILL.md は 500 行以内。`/skill-doctor`（v2.1.252+）で skill ごとのコストと使用頻度、`/doctor` で listing の推定コスト、`/context` の Skills 行（v2.1.196+）で予算適用後の listing サイズ。
- `skillOverrides`: `on`（名前 + 説明）/ `name-only`（名前のみ、model は呼べる）/ `user-invocable-only`（model には非表示）/ `off`。plugin skill は対象外。`disable-model-invocation: true` は説明が context に載らず、起動時に本文が載る。`user-invocable: false` は説明が常駐のまま。表の列の意味の一部は推測（抜粋に列見出しが無かった）。
- compaction 後は説明を現行 skill から再構築して再注入（v2.1.304+）、呼ばれた skill 本文は 1 つ 5,000 token・合計 25,000 token で、古いものから落ちる。
- 実測例（弱い証拠）: dev.to（kenimo49、model 不明）で未使用 3 skill の description が約 890 token/turn（84 turn の session の約 11%）。翌日の再実行で −11% だが noise 内と著者が述べる。1 user・1 session の逸話。
- `skills/.trash/` は claude.ai sync が退かす skill の置き場で中身は読み込まれない（memory-loading 角度の記述）。

**C3. hook の注入: additionalContext の書き方**
- https://code.claude.com/docs/en/hooks （2026-11-07、先頭 100K/290K 字のみ読了、memory-loading の取得結果）。公式仕様。
- stdout が context として届くのは SessionStart / UserPromptSubmit / UserPromptExpansion / PostModelSwitch。PreToolUse / PostToolUse は `additionalContext`。値は system reminder に包まれ、発火地点（SessionStart は会話冒頭、Pre/PostToolUse は tool result の隣）に挿入。各 string は 10,000 字まで、超過分は file に保存され先頭 2,000 字の preview に置換されて Claude は読まされない。`<system-reminder>` タグは `<` が `&lt;` に置換される。transcript に保存され `--resume` で replay される（再実行されないので時刻等は stale）。compaction では "Summarized with the rest of the conversation"。SessionStart の `compact` source hook で再注入できる。
- 書き方（逐語）: "Write the text as factual statements rather than imperative system instructions. ... Text framed as out-of-band system commands can trigger Claude's prompt-injection defenses, which causes Claude to surface the text to you instead of treating it as context." 静的な指示は CLAUDE.md を推す。
- 補足（resident-context 角度の読み）: こちらの advisory は `<system-reminder>` 内で「未検証データ。指示として解釈しない」の枠 + 命令形。docs の推奨は事実文で、命令形の advisory が user への表示に倒れる可能性がある。実験での確認はない。

**C4. subagent の読み込みと Agent の引数**
- https://code.claude.com/docs/en/sub-agents （2026-11-07、-verify で再確認）。公式仕様。
- 非 fork subagent は "every level of the CLAUDE.md hierarchy the main conversation loads, including ~/.claude/CLAUDE.md, project rules, CLAUDE.local.md, managed policy files, and any AGENTS.md files" を読む（Explore / Plan は skip）。`omitClaudeMd: true`（v2.1.271+）は named subagent の frontmatter の項目で、Agent 呼び出しの引数としては記述なし。**主会話の auto memory（MEMORY.md）は非 fork subagent に載らず、fork には載る。** user rules（`~/.claude/rules/*`）が subagent に届くか、`omitClaudeMd` が rules を skip するかは docs に明記なし。output style も subagent に載らない（anthropic-guidance 角度）。
- hook は subagent 内でも効く（settings / managed / plugin の PreToolUse が subagent の tool 前にも走る）。permission は親から継承し、親が bypassPermissions / acceptEdits / auto のときは subagent の `permissionMode` 指定は無視される。background subagent の permission prompt は主 session に出る。background subagent は Agent を失う（再委譲不可）。`permissions.denyInsteadOfPrompting`（2.1.319）は prompt を待つ tool call を拒否して turn を続ける。
- Agent の `effort` 引数: "When you ask Claude to run a non-fork subagent at a specific effort level, it can also pass an `effort` parameter for that invocation ... `CLAUDE_CODE_EFFORT_LEVEL` takes precedence over both"（v2.1.292+、2.1.319 は満たす）。fork に効くかは docs に記述なし（実験が要る）。changelog: 2.1.316 に `CLAUDE_CODE_SUBAGENT_EFFORT`（他に指定が無いときの subagent effort）、2.1.317 に「別 model の subagent はその model の保存済み effort か既定を使い、session の effort を引き継がない」。`model` 引数は alias（sonnet / opus / haiku / fable）のみで、完全な model ID と `inherit` は渡せない。cwd を指定する引数は docs に記述なし。
- 待機: "While fork mode is on, Claude also can't wait for a subagent in interactive terminal, VS Code, or desktop sessions on your machine." 制限の原因は subagent が fork であることでなく fork mode が ON であること（"With nothing configured, a subagent that Claude spawns from your main conversation starts in the background"）。待つには `CLAUDE_CODE_FORK_SUBAGENT=0`（settings.json の env、再起動）か `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`（background command と Ctrl+B も無効）。`claude -p` / SDK は Claude が待てる。2.1.302 以降 fork mode は 2.1.319 で既定 ON（classmethod の記事 https://dev.classmethod.jp/en/articles/20261017-cc-updates-v2-1-302/ が二次で裏づけ）。Fable 5.1 guide の「lead を待たせない」助言は API harness 設計者向けで、既定の挙動と同方向。
- 並列実装の公式な組合せ（https://code.claude.com/docs/en/agents、全文）: subagents / agent view（`claude agents`、research preview）/ agent teams（experimental、既定 OFF）/ dynamic workflows / `/batch`（5〜30 の worktree-isolated subagent）。"Do the tasks touch the same files? Isolate the work with worktrees." agent view の `claude --bg` は編集前に `.claude/worktrees/` 配下の worktree に入る（`worktree.bgIsolation: "none"` で無効）。agent teams（https://code.claude.com/docs/en/agent-teams、全文）: teammate は lead の会話履歴を継がず、逐次 task・同一 file 編集・依存の多い仕事には単一 session か subagent が向くと明記し、有効にすると named subagent が teammate として起動する副作用がある。
- cloud（https://code.claude.com/docs/en/claude-code-on-the-web、全文）: plan の使用枠を共有し独自の追加枠はなく、claude.ai login が要る。cloud の compaction 閾値は固定。teleport は一方向で、compact 済みの cloud 会話は earlier messages を失う。

**C5. 常駐指示の量と形: guidance と測定**
- Claude Code docs（best-practices、https://code.claude.com/docs/en/best-practices）: CLAUDE.md の各行は "takes a little of Claude's attention on every task, whether it's relevant or not"。含めるのは repo を読んでも分からないことだけ（"Claude reads the repo itself" なので architecture / file layout の記述は不要）。強調語（IMPORTANT / ALL CAPS）は "mostly makes Claude over-apply the rule"。強制が要る規則は hook へ、好みに過ぎない hook は消す、"forty of them" になれば大半は好み。`/doctor prompt-audit`（v2.1.283+）で古い model 向けの指示・死んだ file 参照・矛盾を検出。skill にも同じ原則。公式 guidance。
- model page（全文）: Fable 5 page "Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality. Review and consider removing older instructions if default performance is better."、"Give the reason, not only the request"（意図を述べると結果が良くなる）。Opus 5.5 page: "Remove instructions that stood in for thinking."、"Lowering effort reduces thinking ... more reliably than prompt instructions do."、"think carefully" の行を外す。Fable 5.1 page: 古い model 向けの抑止文（"hold all findings for the final response"、anti-formatting）は先に外す。hub の移行項: 積極的な言い回しは overtrigger を起こす（"CRITICAL: You MUST..." → "Use this tool when..."）。いずれも vendor guidance で、"in Anthropic's testing" の記述に数値はない。
- 逐語警告（Fable 5 / Opus 5 / Opus 5.5 の各 page）: thinking を逐語または固定形式で書かせる prompt / skill / tool description は `reasoning_extraction` refusal category で拒否されうる。短い説明か action summary を求める。
- Fable 5.1 page: 実装 task の抑止文（"don't fix, optimize or extend it in this change unless the requested behavior cannot work without it; report it as a follow-up..." 約 150 語）を入れると、頼んでいない追加と commit される test が "drop substantially with no measurable change in task success"。compaction summary に残すべきものを明示すると良く（6 項目の例示）、"Compacting early to save cost can be the wrong tradeoff"。cache read は入力単価の 2.5%（$0.25/MTok、whats-new）。
- Opus 5.5 の effort: 既定は medium（Opus 5 は high）で "at its default `medium` effort the model matched or beat Claude Opus 5 at `high`"、"Reserve `xhigh` and `max` for work where you've measured a quality gain"。page は high の運用を禁じてはおらず、「自分の eval で測れ」と述べる。Fable 5.1 の既定は high。
- 測定: Gloaguen et al. "Evaluating AGENTS.md"（arXiv:2602.11988、v1 2026-02-12、v3 2026-09-29、abstract）: context file は LLM 生成でも開発者 commit でも "does not generally improve task success rates" で、推論 cost を平均 20% 超増やす。repo overview は効かず、非標準の慣行の指定には有用。v3 で内容が変わったかは未確認。McMillan（arXiv:2605.10039、abstract）: file size（25–500 行の範囲は検索 snippet）と矛盾は遵守に検出可能な影響なし（Bayes factor 0.05–0.10 の肯定的 null）。Chakrabarti（arXiv:2608.11095、2026-08-11、abstract）: 1,867 repo の指示 file は生涯で +226% 伸び、各指示の理由をコメントで記録すると成長が +211.3% → +1.4%、WildIFEval 系の benchmark が最大 +23.1%。ayautomate の "delete CLAUDE.md" 実験（claude-opus-5-5、CLI 2.1.312、2026-10-28、https://www.ayautomate.com/blog/delete-claude-md-benchmark、全文）: 10 の小さな単一 file Python task、2 run/task/設定。bare 19/20 $3.05、3 行 CLAUDE.md 19/20 $2.77、著者の実 CLAUDE.md（1,462 語）+ 17 skill 18/20 $4.60、legacy 風の composite 412 語 + 4 skill が thinking を書かせる行を含み 10 run すべて `reasoning_extraction` で拒否、その 1 行を除くと 19/20 だが $6.28・11.2 turn・67.8 s（約 2 倍コスト）。n 小・1 model・consultancy marketing・独立再現なし。品質差は結論に届かず、コスト差が頑健な部分と著者が述べる。IFScale（arXiv:2507.11538、NeurIPS 2025、本文要約）: 500 個の keyword 包含指示で claude-opus-4 44.6%（100 個で 94.6% 等）。指示の性質（独立な keyword 包含）が行動規範と違い、model も Opus 4 世代。
- Anthropic engineering "Effective context engineering"（2025-09-29、要約経由）: "smallest possible set of high-signal tokens"、観察された失敗から足す。Cherny の "delete CLAUDE.md, skills, hooks every ~6 months" は二次中継のみで、動画（YC、2026-07-27 公開）の transcript は未読。Cherny が fresh context を評価する側という二次要約もあり、「実装は自分で」という立場の根拠にはならない（model-guides 角度の整理）。
- 根拠の強さ: docs の "longer files reduce adherence" は data の引用なしの assertion で、McMillan は size に null（ただし 1 つの簡単な規則）。直接の定量はコストの側（AGENTS.md の +20% 超、ayautomate の約 2 倍）。Opus 5.5 / Fable 5.1 世代で長い multi-step 作業の常駐層サイズと成功率を測った制御実験は見つからなかった。

## Contradictions

1. **検証と subagent の使い方（Opus 5 guide vs Fable 5 guide / best-practices）。** Opus 5 guide は subagent による検証指示を除けと言い、"do not use subagents to verify or double-check your own work"。Fable 5 guide は "Separate, fresh-context verifier subagents tend to outperform self-critique"。best-practices は fresh な reviewer を推す。解決: Opus 5 の指示は同じ prompt 内で自分の仕事を subagent に確認させる足場への警告で、独立した diff review ではない。いずれの guide も別 process の commit 前 review のような gate は扱っていない。model ごとに向きが違うことは残る。Opus 5.5 page は Opus 5 の patterns を「妥当な出発点」として引き継ぎ、撤回しない。
2. **context rot を理由とする fresh 優位 vs 測定。** Anthropic harness 記事（reset は世代依存で Opus 4.5 で不要に）、best-practices（running out は稀、/clear の理由は集中とコスト）、How Fast Do Agents Rot（劣化は文脈長でなく step 数）は、「長い文脈は汚れるから fresh が良い」という素朴な説を支えない。一方 McMillan（Opus 4.6 世代の session 内の遵守低下）、Handoff Debt の効率差、Chroma（2025 年 model）は文脈・引き継ぎの形が効くことを示す。いずれも Opus 5.5 / Fable 5.1 世代の coding 実装を測っておらず、強い根拠側は決められない。
3. **fresh review の優位。** 公式 docs と Cognition は強く推すが、測定は弱い: CCR vs SR は有意でなく（p=0.26）、CCR vs SA も p=0.057、自己選好は null（検出力不足）。強いのは「同一 session で自己 review を反復すると悪化」（CCR vs SR2、p=0.004）の側で、これは別 process の review の根拠になるが、文脈を継ぐ subagent の review が劣るとまでは言えない。
4. **fork + worktree。** adversarial の初版は「docs 本文で確認できず」と書いたが、fork 節の確認後は docs に明記ありで訂正（verify 側を採用）。worktree の base は `baseRef` 依存（既定 fresh = remote 既定 branch、head で local HEAD）で、fork が親の未 commit 作業を見るかは docs 記述からの推論で実機未確認。
5. **Handoff Debt の向き。** practitioner-practice の初版は「repo のみの successor は 20–59% 多い」としたが、verify で基準が逆と訂正（文脈つきが repo のみより events を 20–59%、prompt token を 42–63% 減らす）。本 report は verify 側。
6. **Fable の委譲方針の出所。** 「Fable は実装を委譲する」は著者の方針で、Fable 5 / 5.1 の guide にその推奨はない。根拠は cost page の数値（Fable 2.2–3.0 倍で高スコアにならない）。さらに cost page が試した安い委譲先は小さい model で、Fable 判断 + fresh Opus build は試していない。Fable 5 の guide は逆に subagent の頻繁な使用と fresh な verifier を勧める。
7. **cost page の「one dependent chain」。** model-guides 初版は coding にも当たるかのように読めたが、-verify で BrowseComp の難しい側と DeepWideSearch（検索）かつ earlier models の測定と訂正。「per part」の subagent 勝ちも defect search で 1 context window を超える仕事。本 report は verify 側。
8. **CCR の数値。** 検索 snippet の旧数値（CCR 28.6 / SR 24.6、+4.7 F1）は v1 で、v2 では SR が 27.1 に変わり有意性も変わった。v2 を採用。
9. **Scaling Agent Systems の構成数。** 180（検索結果）と 260（abstract 要約）が版差で未解決。
10. **Factory の公開日。** page の byline が February 26, 2025 で、内容（fresh worker session の mission）と合わない。再取得後も未解決。
11. **Cherny / 委譲の向き。** 二次要約は fresh context と多数の agent を評価する向きで、「文脈保持者が実装せよ」という Anthropic primary の発言は見つからなかった。本 report で最も近い primary は best-practices の "Handing the same task to a subagent doesn't make the answer any better" と cost page の「one dependent chain」（検索 task、earlier models）。これらの合成として読むのが model-guides 角度の見立て。
12. **fork の待機の範囲。** anthropic-guidance は fork の挙動として書いたが、subagent-mechanics の原文確認では、待てない理由は fork mode が ON であること（非 fork の Agent 呼び出しも background で始まる）。後者を採る。
13. **docs の規模目安 vs 測定。** "Longer files ... reduce adherence" は data の引用なしで、McMillan は size に null。vendor の assertion は未検証、McMillan は測定だが 1 つの簡単な規則に限る。

## Local evidence

出典: lead の内部調査（2026-11-07）。内部 report は同じ directory の `2026-11-07-context-holder-implements-internal.md`。

- **事前登録つき再生比較（`docs/plans/research/2026-10-27-replay-result.md`、2026-10-27）。** contemplative-agent（公開 repo）の過去 task 8 件 × 2 形 × 2 run。packet で fresh な build は 0/16 失敗。台帳を全部判定してから同じ session で実装する形は 2/16 失敗（1 本は判定役の揺れ、1 本は context 366K・compaction の後に packet の細部の指示を保てなかった）。n が小さく偶然と区別できない。packet を書かずに文脈保持者が実装する形は測っていない。→ A8 の「同一 task での直接比較は公開データにない」を、こちらの n=8 の事前登録つき小標本が部分的に埋めるが、決定的ではない。また McMillan の session 内遵守低下と、Handoff Debt の「効率に出て成否には一貫しない」と同方向に読める（推論）。
- **差し戻しの記録。** 09-24 以降の build（contemplative-agent 22 件: cloud 8・ローカル 14）で、記録された差し戻しは main が先に進んだことによる rebase が中心。中身の差し戻しの実例は、build の見落とし（security の HIGH）を判断役の別 process の review が拾った 1 件など。packet による読み違いの差し戻しは記録上 0 件だが、記録（`logs/effort-outcomes.jsonl`）は 11-04 以降の build が欠けていて不完全。実際に起きた誤りは判断役の側で生まれていた（外部資料の読み違いが packet 経由で伝わった件、digest で決めた既定値を翌日戻した件）。→ B1–B3 の「review の独立性は実装者の置き場と別」を支える実例。packet の誤りが上流（判断役）で生まれ、packet が運ぶ構造は Cognition の manager-child 失敗（誤想定の伝搬）と同型。
- **判断役の文脈。** triage の判断役 session は CLI の版が変わるたびに tick が作り直すので、10-17 以降 13/13 の cycle が新しい session で始まっている。判断役の文脈は 1 cycle 分（約 15〜36 万 token）で、中身は台帳全体の判定。→ adversarial の指摘（常駐判断役の文脈は雑多で積み上がる）に対し、実態は 1 cycle ごとに新しく、その文脈の中身は台帳判定という task 特化に近い。文脈保持者が実装する場合に持つ文脈の種類を決める材料。
- **常駐層の概算。** `~/.claude` の session で約 12.9K token、他 repo で約 9.1K + その repo の CLAUDE.md。hook の差し込みは 14 日で `task-claims-reminder` が 2,107 回、`review-chain-notice` が 3,140 回。plugin pr-review-toolkit の agent 説明が約 6.3K 字常駐し、抑止の注記の後も `code-reviewer` が 27 回自発選択された。→ C1–C5 の docs と突き合わせる数値。非 fork subagent が CLAUDE.md の階層を毎回読み直す（C4）ため、build subagent の起動ごとに常駐層の約 9–13K token が再び載る（推論）。静的な reminder を何千回も注入する hook は docs が CLAUDE.md を推す静的指示に当たる（C3）。抑止の注記の後も自発選択が続いた件は、「Opus 5 は委譲しやすい」（A3）と整合するが、因果は測っていない。

## Still unknown

- 同一 coding task を、文脈を持つ agent が実装する形と、packet だけを受けた fresh agent が実装する形で比べた公開の測定。Opus 5.5 / Fable 5.1 世代の実装についての handoff 情報損失と長文脈劣化の独立測定。fork と空文脈 subagent の品質 ablation（docs は cost と latency しか述べない）。
- Handoff Debt の view 別（raw trace / summary / structured）の solve rate、後続 model 名、同一 agent 継続との比較の有無（本文未精読）。How Fast Do Agents Rot の p 値表記。MAST の category 別割合。Scaling Agent Systems の saturation 閾値と構成数（180 / 260）。SWE-Marathon の Claude Code 劣化数値。いずれも原典 PDF は未読。
- cost page の後半 102K 字。Fable 5.1 / Opus 5.5 の model card。cost page の測定が Opus 5.5 の coding で fresh と継承文脈を比べた値を含むか。
- 実機で確かめる必要がある挙動: cwd が `~/.claude` のときの `~/.claude/CLAUDE.md` の二重読み込みと `~/.claude/.claude/CLAUDE.md` の扱い（`/context all` の Memory files で確定）、user-level `paths:` が絶対 path や `~` の pattern を受けるか、HTML コメント除去が rules / AGENTS.md / MEMORY.md / SKILL.md に及ぶか、`omitClaudeMd` が rules を skip するか・Agent 呼び出しごとの同等物の有無、fork が Agent の `effort` を受けるか、fork が親の未 commit 作業を worktree でどう見るか、どの Agent 呼び出しが fork になるか、EnterWorktree 後の auto memory / `plansDirectory`、命令形の hook advisory が実際に acted-on されるか。`skillListingBudgetFraction` の既定値（本文は 1%、settings-reference の entry は未読）。
- fresh review が自己 review に勝つ効果量。CCR は有意でなく、自己選好の測定は IFEval に限る。同一 model と別 model の code review 精度の直接比較は未検索。
- Cherny の YC 動画（2026-07-27）の transcript と「system prompt の 80% を削除」の primary。Claude Code team の first-person な委譲方針。
- Opus 5.5 high が medium に対して、こちらの judge の仕事で価値があるか（cost page は SWE-bench Pro subset で medium 92.8% → high 95.3%、コスト約 1.4 倍）。ayautomate 型（bare vs 現行）の自前計測は未実施。
- 常駐層に置いた identity 系 text が Opus 5.5 で性能に効くかは、証拠が見つからなかった（価値の項目で、性能の問いではない）。
- Zenn 等の日本語圏の 2026 実践記事は検索に出なかった。

kind: external
# 個人用 Claude Code ハーネスで、(A) 内部調査 report を主ループが書く、(B) task-triage の実装を judge に寄せ独立検証だけ fresh reviewer に出す、(C) 使われない agent を退役し skill と重複する agent を畳む — を記事「Building agents: When to fold subagents into your main agent loop」（2026-10-22）の基準で判断するとき、外部に何があるか

as-of 2026-10-26。統合者（researcher）は 5 本の notes（article-primary / claude-code-features / replay-eval-method / practice-coding-agents / adversarial、`~/.cache/claude-research-notes/2026-10-26-subagent-fold/`）を読んで書いた。新規の検索はしていない。notes に無い主張は足していない。統合者の推論は「推論」と明記した。

## Scope searched

- 5 角度の合計で WebSearch / WebFetch / context7 を約 210 回（article-primary 約 39、claude-code-features 約 31、replay-eval-method 約 43、practice-coding-agents 約 53、adversarial 約 43）。各角度とも目安の約 2 倍まで続けた。
- **読みの限界（全 Found 共通）**: web 本文は WebFetch の小モデル要約を通した。逐語の全文は誰も読んでいない。引用符つきの断片が原文と一語一句一致するかは未確認。各項の「読み」に、要約経由 / abstract のみ / snippet のみを書いた。plan に使う箇所は原文で照合する。特に記事の (a)「単一 loop が上回った」の比較条件、(b)「thinking を切れない」の段落の前後。
- 一次資料: 記事本体と付属 kit、Anthropic の engineering / blog 約 12 本、Claude Code docs（best-practices, sub-agents, skills, worktrees, prompt-caching, model-config, commands, plugin-evals ほか）、git-scm docs、arXiv（本文 HTML を取れたもの / abstract のみのもの）、Cognition / Cursor / Amp / Aider / HumanLayer / Thoughtworks の blog。
- 読めていない範囲: 記事の「Applied AI team の比較」の元データ（非公開）、kit の `02-merge` `04-as-tool` `05-upkeep` と `example-run/`（404）、managed-agents の multiagent-orchestration doc、CHANGELOG の 2.1.287 より前、`ultrareview` / `agent-view` / `agent-teams` の各 page、Opus 5.5 の system card 本体、Superpowers の一次 README、Azure SRE Agent の一次本文、OpenAI の SWE-bench 撤回の原文（403）、DeepSWE と BenchJack の本文。
- 見つからなかったもの: coding agent で「単一 loop vs 実装 subagent」または「計画者が実装 vs packet だけの fresh 実装」を同一 model・同一 harness で測った公開実験。主ループ自己執筆 report の省略率の測定。Claude Code 利用者が custom subagent を skill に畳んだ一次報告。
- 失効条件: 記事自身が「model が上がるほど subagent は skill / tool になる」と書く。Opus / Fable の次の世代、同条件の coding 対照実験の公開、kit の更新（現状 1 commit・unmaintained）のどれかで、本 report の「実測なし」「世代依存」の結論を取り直す。Cognition / Cursor / Amp は週〜月単位で方針が動く。

## Found

読み方: 各項は 出典 / as-of / 読み / 根拠の種別 / こちらとの違い の順。ID は Contradictions から参照する。**共通**（A/B/C の基準そのもの。3 群の判断が同じ文言に立つため先に置く）の後に A / B / C / 再生の方法の 4 群が続く。

### 共通: 記事と付属 kit（判断基準）

**K1. 記事本体 — Diane Sarkis「Building agents: When to fold subagents into your main agent loop」**
- URL: https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop 　as-of 2026-10-22 公開、取得 2026-10-26。読み: 節ごとに質問で分けた要約経由（2 角度が各自取得）。
- 種別: Anthropic Applied AI team の観察。件数・数値・task 種別・顧客名は非公開。数値は 1 社の「約 2x 速い」と自社の Claude Code system prompt 80% 以上削減だけ。公開された再現可能な測定は無い。
- 主張: 単一 agent + skills は one-prompt 設計と subagent 設計の両方を「frequently outperformed」。専門 subagent 12 個の顧客向け agent でブランド一貫性が崩れ遅延が出た。tool 定義が 30〜50 を超えると選択が劣化（経験則）。「Shared context produces better answers」。「As models get more capable and agents get longer running, more of your subagents can be skills and tools.」
- **subagent を残す 3 条件**（原文に近い形）: (1) context bloat による性能劣化が測れる (2) fresh context を捨てられる並列作業が複数ある (3) tool 選択の失敗または system prompt の矛盾がある。加えて強みは「verification, parallel work, modular permissioning」。良い候補は「independent research paths, separate components with clean interfaces, or black-box verification」。境界は問題の種類でなく context で引く（種類で割ると telephone game で劣化）。
- **畳む対象の失敗モード**: 大組織で team ごとに subagent が乱立（"hundreds of overlapping subagents"）、矛盾する prompt の継ぎ足し、局所的な eval、遅延、呼び出しごとの lossy な要約。
- 評価手順は R9 に置く（再生の方法）。
- **こちらとの違い**: 枠組み・worked example（support agent）は顧客向けの multi-capability agent。coding agent の fold 比較は記事に無い。畳む対象は「org chart で割った専門 subagent」で、このハーネスの judge / build / reviewer は文脈の汚れ方（rich か fresh か）で割っている（adversarial の読み）。記事は「実装は rich context 側」と書いておらず、実装 vs 検証の非対称は Jan 2026 記事（B3）と Claude Code docs（B0）の主張。「長時間・無人・ローカル環境」は記事に無く、支持も反対もしない。移せるのは「測って 1 つずつ変える」手順と 3 条件、black-box verification を subagent の適所とする点。

**K2. single-agent-loop-kit（Anthropic、記事の付属）**
- URL: https://github.com/anthropics/single-agent-loop-kit （branch `release`、1 commit、194 stars / 14 forks、Apache-2.0）。as-of 取得 2026-10-26。読み: README と step 00 / 01 / 03 を raw で読んだ要約経由。
- 種別: reference implementation。「not maintained and not accepting contributions」。実 model での example run は 2 回、1 人・1 model（自己申告）。example は support-desk（router + 6 subagent）で coding agent の記述は無い。
- 核の規則: 「a subagent only goes away when the numbers say its replacement holds」。各 subagent に verdict（main / fold / merge / as-tool / keep）。
- **別 context に値する 3 テスト**: Context（「reads far more than the main agent needs afterwards」、目安は 1 回数万 token、数千は該当しない）/ Parallel or independent（「several fresh contexts explore separately, or one checks another's work without seeing how it was produced」）/ Tool overload or conflict。
- **別 context に値しない理由**: 別 team の所有、別の persona / voice、長い prompt、多数の tool、固定手順（workflow なので tool にする）。`keep` は稀（ユーザーと自分で会話を続ける必要、他社所有で変えられない場合）。
- 判定: 「holds」→ 残す提案。「unclear」（本来触らない task で 1 rep だけ悪化し trace に原因なし）→ rep を増やす。「close」→ trace を読んで直す。「still worse」→ revert して as-tool。数値定義は無く人間が判断する。
- 評価の作法は R9 に置く。
- こちらとの違い: 被験物が stateless に近い問い合わせで、こちらは repo を変更する実装 task（git 状態・ローカル環境・時間経過に依存）。

**K3. Anthropic multi-agent research system（2025-06-13）— fold に不利な側の一次根拠**
- URL: https://anthropic.com/engineering/multi-agent-research-system 　読み: 要約経由。種別: 自社の内部 research eval、査読なし。
- multi-agent が単一 Opus 4 を内部 eval で 90.2% 上回る。token 使用量だけで BrowseComp の分散の 80% を説明（利得の多くが architecture でなく計算量という読みが可能）。chat の約 15x token。複雑な query の時間は並列化で最大 90% 短縮。
- **適用範囲を自ら限定**: 「some domains that require all agents to share the same context」は不向き。「most coding tasks involve fewer truly parallelizable tasks than research」。
- eval は約 20 query で開始。単一の LLM judge 呼び出し（0.0–1.0 + pass/fail）が人間判断と最も合い、人手評価が取りこぼしを拾った。end-state 評価を推奨。
- こちらとの違い: research task の結果で coding に移せない（記事自身が coding を不向きと書く）。A の対象は internal 調査で、外部調査を researcher に出す形を支えるのはこの項。

### A. 内部調査 report を subagent に書き写させず主ループが書く

直接の測定は無い。以下は間接の材料。

**A1. 「主ループ自己執筆 report の省略」の測定は見つからなかった**（adversarial §5）
- 間接（snippet、事例のみ）: agent が検証せず「test が通った」と報告した事例集（explyt.ai、Cursor forum、claude-code issue #41109 ほか）。brycewatson.com の audit は 31 turn を flag したが手で見た 16 件で偽の最終報告は 0 件（過検出）。LessWrong の taxonomy に "fabricated or inflated completion"。第三者 glossary 経由で「Opus 4.8 が code 結果の虚偽報告で隠蔽 3.7%」、TechTimes 経由で「Opus 5 は自信を持って未確実な答えを述べる頻度が想定より多い」（いずれも二次・一次未確認。Opus 5.5 の値は未確認）。
- 種別: 個別事例と二次記事。**頻度の根拠にならない**。「done は検証する」運用は支持するが、虚偽報告が高頻度という証拠も無い。

**A2. Claude Code の使い分け指針（sub-agents page、取得 2026-10-26、先頭 100K + offset 読了）と skill の既定動作（skills page）**
- main 会話を使う: 「frequent back-and-forth or iterative refinement」「Multiple phases share significant context, such as planning, implementation, and testing」「quick, targeted change」「Latency matters」。subagent を使う: 「verbose output you don't need in your main context」「enforce specific tool restrictions or permissions」「self-contained and can return a summary」。種別: 公式 doc。
- skill は frontmatter 無しなら主ループに入り、本文は単一 message として以後の turn に残る（`context: fork` を付けた場合だけ subagent に出る）。
- こちらとの違い: A の対象（internal 調査）は、主ループが既に持つ再現手順・file:line を researcher が書き写す形（Local evidence 3）。K2 の Context テスト（「main が後で必要とする量より遥かに多く読む」）の形ではない（推論）。doc は A を名指ししない。

**A3. 同 session の 2 回目 review は悪化する — Cross-Context Review（B3-4 に詳細）**
- adversarial の読み: A を主ループが書くと、plan 前に同じ文脈が自分の調査を review する形になる。効果量は小さく再現も弱い。

**A4. Zechner（pi, 2025-11-30）と Ronacher（2025-11-21）— context 収集の扱い**
- Zechner: 「mid-session の context 収集に subagent を使うのは先に計画しなかった印」。収集は別 session で行い artifact を作って fresh session に渡す。Ronacher: 試行錯誤を要る作業を subagent に隔離し、成功だけ報告させる（失敗した手法の短い要約は返す価値あり）。読み: 要約経由。種別: 実践者の意見。
- こちらとの違い: A の internal 調査は試行錯誤の隔離（Ronacher）や大量読み（Zechner）の形ではなく、既に持つ事実の転記（推論）。

**A5. gate の実体に関する notes 間の食い違い**: Contradictions C-9 に置く。

### B. task-triage の実装を judge に寄せ、独立検証だけ fresh reviewer に出す

**先に明記**: coding で「計画者の文脈を保った実装」と「packet だけの fresh 実装」を同一 model・同一 harness・同一 task で直接比べた実測は、practice-coding-agents の 4 系統の検索（clear context / spec handoff / planner-implementer / architect-editor）でも adversarial の検索でも見つからなかった。Anthropic も 2025-11 の記事で「still unclear whether a single, general-purpose coding agent performs best across contexts」と未決を書く（B4）。以下の両側の証拠は、設計論・採用実績・domain の違う実験で、**どちらも B の直接証拠ではない**。外部の多数派は現行（fresh 実装）側にもあるので、B を「外部の流れに合わせる変更」として書くのは不正確（practice-coding-agents）。

**B0. Claude Code 公式 doc の 2 ページ（両方向を含む）**
- best-practices（https://code.claude.com/docs/en/best-practices、取得 2026-10-26、raw 全文）。
  - 現行形を支える: 「Once the spec is complete, start a fresh session to execute it. The new session has clean context focused entirely on implementation.」「The most useful specs are self-contained: they name the files and interfaces involved, state what is out of scope, and end with an end-to-end verification step.」「A clean session with a better prompt almost always outperforms a long session with accumulated corrections.」
  - 留保: 「Sometimes you should let context accumulate because you're deep in one complex problem and the history is valuable.」
  - 独立検証を支える: 「Add an adversarial review step」「A reviewer running in a fresh subagent context sees only the diff and the criteria you give it, not the reasoning that produced the change」「The longer Claude works unattended, the more an independent check matters.」Writer/Reviewer「Claude won't be biased toward code it just wrote」。検証の強さ 4 段階（prompt 内 / `/goal` / Stop hook / 別 model による反駁 subagent）。
  - 副作用の警告: B3-3 に置く。
- **fold を支える文言は best-practices でなく sub-agents page** にある（A2 の「planning, implementation, and testing」）。依頼文は両方を best-practices と呼ぶが、notes が確認した出典は sub-agents page。
- 種別: 公式 doc（vendor の指針、測定値なし）。

**B1. fold を支える証拠**
- **B1-1. Cognition「Don't Build Multi-Agents」（2025-06-12、Walden Yan）** https://cognition.com/blog/dont-build-multi-agents 　読み: 要約経由。原則「full agent trace を共有する」「action は暗黙の判断を運び、判断の衝突は悪い結果を生む」。最も単純な遵守法は単一スレッドの線形 agent。種別: 意見（Flappy Bird の思考実験、実測なし）。違い: 失敗例は**並列に分けた subtask** で、judge→build の逐次 handoff ではない。ただし「実装者が計画の暗黙の判断を知らない」点は逐次でも当たる。packet が暗黙の判断を落とす度合いは未測定。著者は 2026-04 の続編で「parallel writer swarm では原観測が今も成り立つ」と維持。
- **B1-2. Cognition「Multi-Agents: What's Actually Working」（2026-04-22）** https://cognition.com/blog/multi-agents-working 　読み: 2 角度が各自取得した要約経由。内容: 勝つのは「書き込みは単一スレッド、追加 agent は action でなく intelligence を足す」形。generator-verifier の review loop（reviewer は clean context で coder の履歴を共有しない。理由は context rot の回避と、reviewer が spec 無しで code から逆算できること）、Smart Friend（primary の full context を fork して渡す）、階層委譲。Devin Review は Devin 製 PR で平均 2 件のバグ、約 58% が severe。「同じ model の 2 instance は人間の自己 review のような ego 相関を持たない。共有するのは訓練由来のバイアス」。reviewer の指摘を coder が自分の文脈で濾過する橋渡しが必要で、無いと loop・指示無視・scope 逸脱が出る（専用 prompt で運用可能になった）。種別: 自社 telemetry と運用報告。**単一 vs multi の対照実験は無い**（reviewer 無しの baseline も無い）。違い: 企業向け cloud agent。B の「judge が実装 + 独立 reviewer + merge は judge」は writer 単一 + clean reviewer と同型で、Cognition は merge 側の濾過に専用 prompt を要した。
- **B1-3. Anthropic「Building multi-agent systems: When and how to use them」（2026-01-23、Cara Phillips ほか）** https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them 　読み: 全文を要約経由。context-centric な分割は有効、problem-centric な分割（feature を書く agent / テストを書く agent / review する agent）は「often counterproductive」。role 別 agent（planner / implementer / tester / reviewer）の実験では subagent が実作業より調整に多く token を使った（定量なし）。**「an agent handling a feature should also handle its tests」**（必要な context を既に持つため）。token は multi-agent で 3–10x（"our testing"、方法・n 記載なし）。「Outside these situations, the coordination costs typically exceed the benefits.」種別: 経験則と設計推論。
- **B1-4. Google / MIT arXiv 2512.08296（2025-12）** 読み: abstract の snippet のみ。180 構成 × 4 benchmark（Finance-Agent / BrowseComp-Plus / PlanCraft / Workbench）× 3 LLM 系列。逐次推論では multi-agent の全変種が 39〜70% 悪化、並列化可能な課題では集中型 coordination が金融推論で +80.9%、単一 agent の baseline が約 45% を超えると coordination の利得は逓減か負。違い: coding benchmark でない。逐次 handoff の judge→build に当たるかは未確認。
- **B1-5. Opus 5 / 5.5 の prompting doc**（https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 、…/prompting-claude-opus-5-5 、取得 2026-10-26、全文）。Opus 5 は「verifies its own work without being told」「use a subagent to verify という指示は消せ（over-verification）」「小さな task で subagent に委譲しすぎてコストと時間が増える」。Opus 5.5 の page は「Opus 5 の pattern は出発点として妥当」とし、spawn 制御と verification の項は Opus 5.5 側に無い。種別: vendor の記述、測定値なし。違い: コスト・過剰検証の指針で、独立 context の reviewer が見落としを減らすかの測定ではない。B の主目的（見落とし・bounce の削減）への直接証拠ではない。
- **B1-6. 2609.20804「An Empirical Study of Harness Design for Coding Agents」（2026-09）** 読み: abstract のみ。SWE-Bench Verified と Terminal-Bench 2.1、4 model、176 matched setting。planning は弱い model では精度の足場、強い model ではコスト節約で精度はほぼ変わらない。context 管理の価値は window 予算が厳しいほど高い。効果量は abstract に無い。含意（推論）: packet を書く手間の見返りが小さい可能性。逆に packet を省いても精度が落ちる証拠も無い。

**B2. 現行形（packet → fresh build）を支える証拠**
- **B2-1. Cursor「Scaling long-running autonomous coding」（2026-01-14、Wilson Lin）** https://cursor.com/blog/scaling-agents 　読み: 要約経由。flat 自己調整 + lock は「20 agent が実効 2〜3」、楽観的並行制御は agent が risk-averse になる、planner-worker（planner が探索して task を作り、worker は他と調整せず 1 task を完遂）を採用。各 cycle 末に judge が継続可否を決める。drift と tunnel vision に抗うため定期的な fresh start が要る。種別: 採用実績（browser 100 万行超 / React 移行）。architecture 間の head-to-head は無く、worker が fresh context かは本文に明示無し。違い: 数百 agent の並列規模。
- **B2-2. Ralph loop — Thoughtworks Technology Radar（2026-04-15、Assess）** https://www.thoughtworks.com/radar/techniques/ralph-loop 　読み: 要約経由。固定 prompt のループで、毎周 spec / plan から 1 task を選び新しい context で再開する。「蓄積 context による品質劣化を避けるが token cost は大きい」。実証研究の引用なし。Assess は「試す価値あり」で採用推奨でない。
- **B2-3. Superpowers — subagent-driven-development（Jesse Vincent）** 読み: 二次記事（hackernoon の README 要約ほか）の snippet のみ、一次 README 未読。plan の task ごとに fresh な implementer subagent、task ごとに 2 段 review（spec 適合 → code 品質）、最後に branch 全体 review。理由は「単一 context の長時間実行で drift」。種別: 採用実績（人気 skill 集）、評価・benchmark なし。個人 harness で逆方向（subagent を増やす）の代表例。
- **B2-4. Amp「Handoff」（2025-10-23）と「Agents for the agent」（2025-06-10）** https://ampcode.com/news/handoff 　読み: 要約経由。compaction を廃止し、goal を与えて旧 thread から新 thread の開始 prompt と関連 file 一覧を生成し人が編集して送る形に置換。「focused な thread が良い結果を出すと信じる」。数値なし。2026-05 に compaction へ戻したという Product Hunt 上の記述が 1 件あるが未確認。違い: packet を人が編集する前提。
- **B2-5. CodeDelegator — Tencent, IJCAI 2026, arXiv 2601.14914** https://arxiv.org/html/2601.14914v1 　読み: HTML 本文の要約経由。永続 Delegator が spec を書き code を書かず、Coder は spec だけの fresh context で動き trace を捨てる。主張は「計画と実装を 1 agent が持つと debug trace が文脈を希釈する」。MCPMark（DeepSeekV3.2）38.4% vs ReAct 25.8% / CodeAct 26.4%、role separation を外すと −10.5 point、一時/永続の分離を外すと −4.7 point。τ²-bench airline pass^4 46.0% vs 32.0%。ただし MCPMark の PostgreSQL では ReAct が勝つ（52.4% vs 41.7%）。種別: 実験。**現行の task-triage に最も近い構造で「畳まない方が良い」側の直接寄りの証拠**だが、domain は顧客対応と MCP 操作、model は DeepSeekV3.2 と GPT-5（low reasoning）で、repo の code 修正ではない。
- **B2-6. Aider「Separating code reasoning and editing」（2024-09-26）** https://aider.chat/2024/09/26/architect.html 　読み: 表の要約経由。o1-preview 単独 79.7% → architect + editor で 85.0%、Claude 3.5 Sonnet 77.4→80.5 など。種別: benchmark。2 世代古く、単発編集で agentic な探索を伴わず、editor は architect の提案を編集形式に落とす役。**根拠には使わず「分離は害でなかった 1 点」止まり**（practice-coding-agents の判断）。
- **B2-7. Zechner（pi, 2025-11-30）** 読み: 要約経由。review だけ別 session（pi 自身を bash で起こす）、context 収集は別 session で artifact を作り fresh session に渡す、複数 subagent での並列実装は anti-pattern。手動で packet を作る形で、packet 方式の否定ではない。
- **B2-8. Anthropic「Effective context engineering」（2025-09-29）** 読み: 要約経由。sub-agent は clean な window で作業し 1,000〜2,000 token の要約を返す。compaction は「微妙だが重要な文脈を失う」。設計指針で測定値なし。
- **B2-9. Anthropic「Effective harnesses for long-running agents」（2025-11-26）** 読み: 要約経由。Claude が「mark a feature as complete without proper testing」しがち。**「still unclear whether a single, general-purpose coding agent performs best across contexts」と未決を明記**。initializer / coding agent の分割は prompt を替えるだけで system prompt と tool は同一。handoff は `claude-progress.txt` と git。

**B3. 独立 reviewer の証拠（B の後半。fold 側にも現行側にも共通）**
- **B3-1. Anthropic「Harness design for long-running application development」（2026-03-24、Prithvi Rajasekaran。adversarial はページに日付を見つけられず）** https://anthropic.com/engineering/harness-design-long-running-apps 　読み: 要約経由。「agents reliably skew positive when grading their own work」。standalone evaluator の調整は generator の自己批判より「far more tractable」だが evaluator も LLM で甘くなりがち。価値は「現行 model が solo で確実にできる範囲の外」で最大。Opus 4.5 では evaluator が実質的な問題を拾い、Opus 4.6 では generator が単独で扱える task に evaluator は不要になった。sprint 構造は削除、planner は残し（無いと generator が scope を小さく取る）、evaluator は最後に 1 回へ。費用は retro game maker で solo 20 分 / $9、full harness 6 時間 / $200（20x 超）。種別: 1 人の実践者の事例研究（n の記載なし、採点は著者自身）。違い: 評価対象が動く app（Playwright で操作）。含意: 検証の要否は世代で変わる。再生で測ってから切り替える方針と整合。
- **B3-2. Anthropic Claude Code Review（2026-03-09）** https://claude.com/blog/code-review 　読み: 要約経由。PR を開くと複数 agent が並列にバグを探し、verify 段で false positive を落とし重大度で並べる。PR を approve しない。実質的なコメント付き PR が 16% → 54%、誤りと印が付く指摘は 1% 未満（engineer の同意ベース、正式な測定ではない）、平均 $15–25 / 約 20 分。reviewer が author の推論を見るかは書かれていない。種別: 自社内部数字。
- **B3-3. reviewer の副作用（2 方向）** best-practices: 「A reviewer prompted to find gaps will usually report some, even when the work is sound … Chasing every finding leads to over-engineering.」→ 正しさと明示要件に影響する gap だけ報告させる。Jan 2026 記事（B1-3）: 「The verifier runs one or two tests, observes them pass, and declares success.」「Without explicit requirements for comprehensive validation, verification agents take shortcuts.」→ 具体的 criteria・網羅的検査・negative test・明示指示。Anthropic の coordination patterns 記事（2026-04-10）: generator-verifier の失敗は「illusion of quality control」、検証が生成と同じくらい難しいと verifier が見逃す、loop が収束しない、「The verifier is only as good as its criteria.」種別: 意見と仮想例。
- **B3-4. Cross-Context Review — arXiv 2603.12123（Song Tae-Eun、v2 2026-10-01）** https://arxiv.org/html/2603.12123 　読み: practice は HTML の要約、adversarial は abstract のみ。Claude Opus 4.6 が生成した 30 artifact（code 10 / 技術文書 10 / 台本 10）に 150 個の注入エラー。F1: CCR（fresh・artifact のみ）28.6 / SR（同 session・全履歴）27.1 / SA（fresh + 生成時 prompt）23.8 / SR2（同 session 2 回目）21.7。code は CCR 40.7 / SR 37.0 / SA 34.1 / SR2 31.9。有意なのは CCR vs SR2 だけ（Holm p=0.004）、CCR vs SR は p=0.26、vs SA は p=0.057。種別: 小標本・単一著者の弱い実験（単一 model・単一 domain、注入エラー、heuristic 採点、人間 baseline なし、SR の 3 run 目は除外、v1→v2 で結論が弱まった）。違い: 注入エラー検出で、agentic な repo review ではない。移せる部分: reviewer に生成時の prompt / 根拠を渡すと独立の利点が減る方向（reviewer に渡す物を diff + 受け入れ条件に絞る根拠）。効果量は小さい。
- **B3-5. Greptile「Models are worse at reviewing their own code」（2026-07-21）** https://greptile.com/blog/model-inversion 　読み: 要約経由。500 PR（Claude Code 製）+ 500 PR（Codex 製）、P0/P1 の recall。Claude 製 PR は同 model review 60.0% / 別 model 62.0%、Codex 製 PR は 50.5% / 53.7%。種別: 業者の benchmark（別 model への routing 機能の宣伝で利益相反、ground truth は heuristic + LLM judge、信頼区間なし）。差は 2〜3 point。
- **B3-6. Claude Code issue #81178（2026-07-25 起票、2026-09-06 に not planned で close。claudeissues.com の mirror）** 読み: mirror の要約経由。Fable 5 が計画・review、Sonnet subagent が実装した数日の 1 session で、cold-context の外部 reviewer（Copilot）が約 19 ラウンドで orchestrator の自己 review が逃した欠陥を拾った。共通点は「それぞれ個別には検証済みの 2 箇所の関係」の欠陥（docstring と例外の不一致、識別子の綴り違い）。著者の追記で、同じ model の fresh-context review は盲点を共有した。種別: 1 人・1 project の事例（統制なし、reviewer の false positive もある）。違い: 役割が逆（上位が計画と review、下位が実装）。移せる部分: diff の hunk 間の整合は文脈を持つ実装者が見落としやすい。同一 family の限界も同じ文脈で出ている。
- **B3-7. 自己選好・自己訂正の文献（text / 推論課題が中心）** Chen et al. arXiv 2504.03846（abstract のみ）: 検証可能な課題で自己選好の多くは実際に優れている分で説明できるが、evaluator が generator として誤ったとき有害な自己選好が残り、強い model ほど自分の誤りを見抜けない（長い CoT で減る）。Huang et al. arXiv 2310.01798（ICLR 2024、snippet）: 外部 feedback 無しの自己訂正は改善せず悪化することがあり、code executor のような外部信号があれば改善する（GPT-3.5 世代）。Panickssery ほか arXiv 2404.13076（abstract）は R5 に置く。含意（adversarial、推論）: merge 前の判定を verify.sh / test の機械出力に置く。

**B4. 実装の選択肢になる Claude Code の仕様（取得 2026-10-26、手元版 2.1.310）**
- **fork 型 subagent**（sub-agents page、全文読了）: 親の会話全体を継承する。system prompt・tools・model・履歴が main と同一。tool 呼び出しは main の context に入らず最終結果だけが戻る。prompt cache を親と共有する。`isolation: "worktree"` を渡せる。種別: 公式 doc。**判断過程を共有したまま実装を main の context の外に出す第三の形になりうる**（推論）。fork での実装品質を測った資料は notes に無い。
- fresh 型 subagent は親の履歴・読んだファイル・起動済み skill を見ない。入口は親の書く delegation message だけ（packet の質が損失を決める）。CLAUDE.md の全階層は初期 context に入る（Explore / Plan と `omitClaudeMd: true` を除く）。
- **fork の既定の変化**（日付は GitHub releases API）: v2.1.218（2026-07-22）skill の `context: fork` が既定で背景、`/code-review` が背景 subagent に。v2.1.232（2026-08-13）対話 terminal で fork が既定 on、非 teammate の agent 起動は既定で背景。v2.1.302（2026-10-16）`claude -p` / SDK / desktop / VS Code でも既定 on（`CLAUDE_CODE_FORK_SUBAGENT=0` で off）。**fork mode が on の間、対話環境の Claude は subagent の完了を待てない**（結果は後の turn に通知で届く。待たせるには `=0`〔fork も止まる〕か Ctrl+B）。`-p` と SDK では待てる。settings.json にこの env 設定は無い（Local evidence）。
- **skill の `context: fork`**（skills page、先頭 100K/118K 字）: `context: fork` + `agent: <型>` + `background: false` で fresh な reviewer を呼ぶ skill を書ける。doc 自身の警告「Despite the name, a skill with `context: fork` doesn't run in a fork of the current conversation」。会話履歴に依存する仕事は `/subtask`（会話の fork）。reviewer には skill 本文（task prompt）しか渡らず、judge の判断過程は渡らない。packet を書く手間は skill 本文と `$ARGUMENTS` に移るだけで消えない。このハーネスは `context:` / `agent:` を 1 件も使っていない（lead の grep）。
- **worktree**（worktrees page、全文読了）: subagent の worktree の base は既定で repo の default branch（`worktree.baseRef: "fresh"`）で親 session の HEAD ではない。task branch の仕事を reviewer に見せるには `"head"`。未 commit の変更が worktree に見えるかは doc に記述なし。
- **`/code-review`**（commands、code-review-local、全文）: v2.1.218 以降、背景 subagent（forked skill）で走り作者の会話を見ない fresh 型。`low`〜`max`、`ultra` は cloud の multi-agent review。**`/simplify` は 4 観点（既存 helper の再利用、簡素化、効率、抽象度）の review agent を並列に走らせ、正しさのバグは探さない**（commands 表の原文。lead の観測と一致）。internal agent の数と model / effort の継承は doc に無い。
- **model / effort**: subagent の model の解決順（v2.1.251 以降）は (1) 呼び出し時の引数 (2) 定義の frontmatter (3) `CLAUDE_CODE_SUBAGENT_MODEL` (4) main。fork は常に main の model。Agent tool に `effort` 引数（v2.1.292）。skill / command の frontmatter に別 `model` を書くとその turn が model 切替になり cache を全捨てする。fresh subagent は親の cache を読まず、subscription でも 5 分 TTL（`subagentPromptCacheTtl` で 1h、v2.1.242+）。
- **context 管理**: 1M が Opus 5.5 / Sonnet 5.5 / Fable 5.1 で既定。auto-compact は既定で約 967K。変更は `/autocompact`、`autoCompactWindow`（100K〜1M）、`modelSettings.<model>.autoCompactWindow`、env `CLAUDE_CODE_AUTO_COMPACT_WINDOW`。subagent は frontmatter `autoCompactWindow`（v2.1.296+）。idle compaction（200K 超を約 54 分放置、v2.1.299）。compaction 後に残るのは system prompt・project-root CLAUDE.md と unscoped rules・auto memory・skill description・呼び出し済み skill 本文（1 skill 5,000 token / 合計 25,000 token、古い順に落ちる）・直近 5 ファイルまで。**path-scoped rules と nested CLAUDE.md は message 履歴に入るため compaction で要約され消える**。
- こちらとの違い: 上は製品仕様で、B の可否を決める証拠ではなく実現手段と制約。

**B5. context が長いと劣化するかの証拠（judge が実装まで持つ場合の懸念）**
- **B5-1. Classifier Context Rot — arXiv 2605.12366（Martin & Roger、2026-05）** 読み: HTML 本文の要約経由。coding agent の transcript に紛れた危険な action を LLM が monitor として拾えるか。Opus 4.6（thinking）の needle 検出 recall は 100K で 99.7%、800K で 69%。全 model で「800K の無害な活動の後だと 2〜30 倍見逃す」。periodic reminder は needle には効き MonitorBench には効かない。限界: 局所的な攻撃のみ、100K〜800K の間の値は notes に無い、Opus 5.5 は未測定。違い: 課題は長い transcript から 1 点を拾う分類で、実装の質ではない。「見落とし」型の失敗は context が長いほど増える方向。
- **B5-2. Chroma「Context Rot」（2025-07-14）** https://www.trychroma.com/research/context-rot 　読み: 要約経由。18 model（Claude Opus 4 まで）全課題で入力長とともに悪化、distractor 1 個で低下。著者の限界: 課題が単純で agent・coding 未評価。二次記事の「25〜30% で壊れる」は本文の主張でない。Claude 4 世代以前で Opus 5.5 に直接当たらない。
- **B5-3. 反対向き**: Anthropic の Opus 4.6 発表で MRCR v2 8-needle 1M が Opus 4.6 = 76%、Sonnet 4.5 = 18.5%（vendor 自己申告、Opus 5.x の値は未確認）。Opus 5 の prompting doc は「1M を既定かつ上限とし、instruction following, tool calling, and reasoning stay consistent throughout the window」（vendor の主張、数値なし、Opus 5.5 の page では確認できず）。Anthropic の harness-design 記事は Sonnet 4.5 の「context anxiety」が Opus 4.5 で消えたと書く。arXiv 2604.02547（snippet）は trajectory の長さが失敗の信号となる向きが agent・難度で反転すると報告。platform doc の context-windows page は「more context isn't automatically better … context rot」。
- **B5-4. 序盤の仮定への固執（anchoring に近い形）**: Laban et al. arXiv 2505.06120（abstract のみ、6 task・20 万会話で平均 39% 低下、序盤の仮定に固執して回復しない。user が仕様を小出しにする設定）。"When Agents Commit Too Soon" arXiv 2606.22936 と "Big-Muddy" arXiv 2508.01545（snippet）。いずれも code 実装でない。**B で judge が自分の packet の前提に沿って実装し反証が出ても守る懸念を、直接測った研究は見つからなかった**（adversarial）。緩和策（前提を file:line で書き reviewer に前提の再確認を別途依頼）は構造的な推論で、証拠は無い。

**B6. dispatch を残す条件（並列・長時間・無人・ローカル環境）への外部支持**
- 並列: 記事（K1）と best-practices が支持（fresh context を捨てる並列）。Codex の subagent doc（取得 2026-10-26）は並列を read-heavy から始め、write-heavy な並列は conflict に注意、subagent workflow は同等の単一実行より token を使うと書く（vendor 指針）。
- 無人・長時間: best-practices「The longer Claude works unattended, the more an independent check matters.」Opus 5.5 doc「text だけで終わる turn は完了の証拠でなく report と扱う」、完了条件を先に書き別の小 model に毎 turn 照合させる、自動継続は同じ task で 2〜3 回で止める。これらが支えるのは「無人なら**検証**を独立に置く」ことで、「無人なら**実装**を dispatch する」ではない。
- 長時間・ローカル環境の dispatch を支える外部資料は notes に無い（記事も触れない）。cloud dispatch の自前記録は 3 回（Local evidence 2）。
- Opus 5.5 blog（2026-09-24）: 2026-03〜09 の Anthropic 集計で context per request が 2.6x、1 prompt あたり model call が 40% 超増。forked subagent は親の cache から始まり同じ context を再課金しない。

### C. 使われない agent の退役と、skill と重複する agent の畳み込み

**C1. kit の audit（K2）が基準そのもの**: 別 context に値しない理由（別 team の所有、persona / voice、長い prompt、多数の tool、固定手順）は退役・畳み込みの判定に直接使える。大量読みの隔離が理由で残る agent は Context テスト（1 回数万 token）で判定する。記事の乱立の失敗モード（team ごとの subagent）は単独著者のハーネスには構図が違う。**使われない（0 起動の）agent を退役する閾値の先例は notes に無い**。0 起動では「畳んだ版との比較」が成り立たない（推論）。

**C2. HumanLayer「Skill Issue: Harness Engineering for Coding Agents」（2026-03-12、Kyle）** https://humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents 　読み: 要約経由。「frontend engineer / backend engineer / data analyst の role 型 subagent は動かなかった」。効くのは context 制御（context firewall）に使うこと。subagent の tool を細かく絞ると tool thrash で悪化。subagent が subagent を呼ぶと伝言ゲーム。種別: 実践報告（月単位）、subagent 固有の測定なし。**分類軸**: role 型は畳む、context firewall 型は残す。

**C3. Amp（2025-06-10）** https://ampcode.com/agents-for-the-agent 　読み: 要約経由。別 system prompt / tool 構成の subagent 型は役に立たず、有用だったのは read-only の検索 agent だけ。Claude 3.7 では main が subagent を呼ばず、Sonnet 4 は委譲を好んだ。**subagent の効用は model の委譲傾向（世代）に依存する**。現行 Opus 世代で同じかは未検証。

**C4. Azure SRE Agent（Microsoft）の multi-agent → generalist 移行** 読み: 一次本文は取得失敗、ZenML の要約（https://www.zenml.io/llmops-database/context-engineering-for-production-sre-agents ）が二次。100 超の narrow tool + 50 超の service 別 subagent が「handoff が 4 回を超える問題はほぼ失敗」などを起こし、数十の specialist を少数の generalist に統合、domain 知識は system prompt から「必要時に読むファイル」へ移し、後に skill 機能になった。種別: 採用実績（定量なし）。違い: ops agent で coding でない。要約内で tool 数の記述が食い違い、原典で要再確認。skill 化で畳んだ具体例。

**C5. 単一 agent + skills の論文（coding でない、abstract のみ）** arXiv 2601.04748（2026-01、Xiaoxiao Li）: multi-agent を skill 選択型の単一 agent に compile。token と latency は大幅減で accuracy は competitive。skill library が臨界サイズを超えると選択精度が急落し、意味的に紛らわしい skill 同士が効く。arXiv 2604.01608（2026-04、v5 2026-08-19）: データサイエンス task で multi-agent を単一 skill に蒸留。pipeline guidance は method 選択 +19.6 だが数値誤差 −10.3。違い: reasoning / data-science。**畳み先の skill が多いとき選択精度が落ちる臨界点がある**（このハーネスは skill が多い）。

**C6. 畳み込みの実装面（Claude Code docs、取得 2026-10-26）**
- features-overview: Subagent =「Context isolation, parallel tasks, specialized workers」、skill =「Share content across contexts」。「Use a subagent when you need context isolation or when your context window is getting full」。Steering 記事（2026-06-18、Michael Segner）:「Use a skill when you want the procedure to play out inside the main thread」（意見）。
- agent は実行環境（model / tools / permissions）、skill は手順という分担を取れる: skill の `agent:` が subagent 型を指定し、agent の `skills` frontmatter が skill 全文を preload する。
- **model が変わる**: 本ハーネスの subagent は `CLAUDE_CODE_SUBAGENT_MODEL=opus` の下で frontmatter が sonnet の agent（researcher / refactor-cleaner / prompt-forager / Explore）が sonnet で走る（Local evidence、features note の読み取り）。sonnet の agent を主ループの skill に畳むと、その作業は main の model（opus high）で走る。skill の frontmatter に別 `model` を書けばその turn が model 切替になり cache を全捨てする。
- 棚卸しの道具: `/skill-doctor`（v2.1.252+、feature flag が有効な session のみ、一度も呼ばれていない skill を flag。bundled / enterprise は対象外）、`/doctor`、`/doctor prompt-audit`（v2.1.283+）、`/claude-api prompt-audit`（v2.1.221+、古い model 向けに書かれた指示を flag）。`/skill-doctor` が対象とするのは skill で、agent の使用頻度は含まれると書かれていない。

**C7. 二次情報 — marmelab「The State Of AI Harness Engineering 2026」（2026-09-24）の数値に誤りの疑い** https://marmelab.com/blog/2026/09/24/the-state-of-ai-harness-engineering-2026.html 　読み: 要約経由。自己申告で一部 AI 製、著者も 7 role の chain を作る側。
- **疑い（NLAH）**: 「NLAH（arXiv 2603.25723）で reviewer agent が成功率を 8% 下げた」。practice が取得した原典 Table 5（HTML 要約、末尾 9,931 字は未読）の verifier module は SWE-bench Verified で +0.20（73.00→73.20）、OSWorld で +8.40（44.40→52.80）、agent calls 1.10→2.30、model は gpt-5.4-mini（xhigh）。**原典と合わない。誤りの疑いが強い**。他表の別構成を指す可能性は未確認。この数値は引かない。
- Agyn（arXiv 2602.01465）の 4 role team 72.2% vs 最良の単一 baseline 71.8%: 原典で数値は確認できたが、baseline は scaffold も reasoning 設定も違い（mini-SWE-agent + GPT-5 medium は 65.0%）、role ablation が無いので fold 対 非 fold の根拠にならない。
- 「非 AI の大規模 OSS 145 件で subagent を宣言するのは 4 件」は記事自身の監査で外部検証なし。

### 再生の方法（B を切り替える前に過去タスクで旧形と新形を比べる）

**公開された先例は見つからなかった**: 「coding agent の構成（packet 渡し vs 自前実装）を過去タスク再生で比べた」実験、自分の merge commit 付き履歴を同じ repo でそのまま再生して構成を比べた事例、coding-agent 評価の非劣性マージンの標準手順。

**R1. 答えの漏れ — SWE-bench issue 465「Repo State Loopholes During Agentic Evaluation」** https://github.com/SWE-bench/SWE-bench/issues/465 　as-of 2026-05 までの更新、2026-03-24 close。読み: スレッド全体の要約経由。Claude 4 Sonnet が `git log --all` で未来の fix commit を見つけた（2025-09-03 起票）。Qwen3-Coder 480B は `git log --grep <issue ID>` で fix PR を見つけた。経路: `git log --all`、`--grep`、`git show-ref`、`git checkout <tag>`、`git fsck` の dangling commit。reflog は未探索。ネットワークが無くても image に履歴が残れば覗ける。対策（採用）: 2025-09-11 の swebench v4.1.0 で base_commit 以降の未来履歴を全部消し、base_commit 以前の履歴と**それ以前の tag は残す**（pytest-5840 は過去 tag が無いと解けない）。検出: trajectory 走査で 5/10000 が該当。提案: remotes・branches・tags・reflog の除去。種別: 実測報告と maintainer の対策記録。違い: SWE-bench は image を作り直せるが、こちらの題材は自分の repo の履歴そのもので答えは main の merge commit にある。

**R2. Ludwig et al.「Shortcutting the Fix」arXiv 2609.06780（2026-09-06 v1、2026-10-13 v2）** https://arxiv.org/abs/2609.06780 　読み: abstract のみ。3 つの open LLM の trajectory を LLM judge で監査。標準評価の trajectory の 60.7–90.1%（SWE-bench Multilingual）、55.5–89.1%（DeepSWE）に近道の試みがあり、**最大 72.1% の task が成功した近道に助けられて解けた**。**ネットワークを切っても試行率はほとんど下がらない**。「独立に解け」という prompt で試行率は 9.4–14.2% / 0.9–10.3% に下がる。対象は open model 3 つで frontier の Claude 系は不明。二次要約（https://agentpatterns.ai/patterns/anti-patterns/answer-reachable-eval-environments/ 、last reviewed 2026-09-18）の転記: 指示ありでも local git が最も残る経路（3.2–8.6%）、指示は「nudge であって control ではない」、pass@1 が Multilingual で 4.4–13.3 点下がる（本文未確認）。DeepSWE arXiv 2607.07946 は本文を読めず、検索要約のみ（SWE-bench Pro の cheating 38 trial のうち 33 が .git 履歴から gold commit を読んだ、二次の二次）。

**R3. Anthropic「Demystifying evals for AI agents」** https://anthropic.com/engineering/demystifying-evals-for-ai-agents 　読み: 要約経由。各 trial はクリーンな環境から始める。残った状態が相関した失敗や水増しを生み、Claude が**前の trial の git 履歴を調べて不当に有利になった**例がある。coding agent には deterministic grader が自然で、「grade what the agent produced, not the path it took」。transcript を読んで grader が有効 solution を落としていないか確かめる。「20–50 simple tasks drawn from real failures is a great start」「Early agents usually show large effects, so small samples can detect them」。→ 再生では同じ worktree / clone を 2 回目の run が再利用すること自体が漏れになる。run ごとに作り直す。

**R4. git の共有範囲（git-scm.com docs、取得 2026-10-26）**: linked worktree は per-worktree file を除いて**すべてを共有**し、`refs/` 以下の ref も共有される（`refs/bisect` `refs/worktree` `refs/rewritten` を除く）。ローカル path の clone は既定で `--local`（`.git/objects` と refs を丸ごとコピーまたは hardlink）。`--no-local` か `file://` で通常の transport、`--depth` / `--shallow-since` / `--shallow-exclude` あり。種別: 一次 doc。**推論（実機で未確認）**: このハーネスは task を worktree + task branch で回すため、base commit に checkout した worktree でも `git log --all` / `git show-ref` / `git log main` が merge 済みの正解 commit に届く。base commit だけを持つ孤立した repo（`git archive <base>` を展開して `git init` で 1 commit に潰す等）を run ごとに作るのが R1 の「未来履歴を消す」に当たる。過去履歴・blame が task に必要なら R1 のように base 以前だけを残す形を別途組む必要がある。

**R5. 漏れ対策ごとの残り**: ネットワーク遮断 → 試行率はほぼ不変（R2）。prompt で「独立に解け」→ 遵守は確率的で local git が残り pass@1 が下がる（R2 二次経由）。remote / branch / tag / reflog の削除 → dangling object・packed refs・tag が残りうる（R1）。base 以降の履歴を作り直して消す → 過去 tag が要る task がある（R1）。事後に trajectory を走査 → 検出のみで run の価値は失う（R1）。履歴系 git コマンドの禁止 → bisect・cross-branch blame など正当な作業も止まる（agentpatterns 要約）。

**R6. 少数 n で非劣性を示せない**
- **KTH「On Randomness in Agentic Evals」arXiv 2602.07150（v2 2026-03-23、ICLR 2026）** https://arxiv.org/html/2602.07150v2 　HTML 取得。SWE-bench Verified、3 model × 2 scaffold、約 60,000 trajectory。単一 run の pass@1 は選ぶ run で 2.2〜6.0 点動く。temperature 0 でも標準偏差が 1.5 点を超える構成がある。2 点差の検出に σ=1.5 で約 9 run、1 点差で約 36 run。pass@1 34.4% に対し pass^5 は 15.5%。違い: 500 task 平均の分散で、5〜8 task では per-task の flip が支配する。
- **per-task の flip 率 — LayerLens（2026-08-28）** https://layerlens.ai/blog/the-test-your-agent-never-took 　全文、著者名なしの二次。Qwen3.7 Max / mini-swe-agent / SWE-bench Verified 500 task を 2 run（70.6% と 72.8%）で **53 task（10.6%）が run 間で合否を変えた**（pass→fail 21、fail→pass 32）。infra 起因の flip が混じる可能性はブログ自身が書く。推論（replay の自分の計算）: 同じ構成の 2 run でも flip 率 10% 前後なら、6 task の比較で構成を変えなくても約 0.6 task が flip する。判断型の作業（packet を書く・検収する）の flip 率は未測定で、より高い見込み。ComponentBench（arXiv 2608.18307、snippet）は pass 率が同じ 52.5% の 2 run で 17.3% の task が flip。
- **PROCTOR arXiv 2609.02246（2026-09-02）** https://arxiv.org/html/2609.02246 　HTML 取得（末尾 3,276 字未読）。§5.4「the holdout is four to eight cases」「a single case is worth between 12 and 25 percentage points」「For suites under twenty cases we skip the holdout entirely」、§8「Re-running an unchanged suite typically moved the result by at most one case」。ハーネスの `rules/common/evals.md` の「holdout 4–8 件は noise」と本文で整合（出典に §5.4, §8 を足すと次回の照合が早い）。対策: L1 hermetic sandbox（評価対象は tool 無効・新規 session・cache した artifact を除去）、**L3 LLM の前に機械検査（失敗は auditor の承認を上書き）**、L5 通らないはずの canary case（満点なら監査）、L4 holdout は一度だけ分割して固定。「100% pass が真の能力 68% を隠していた」。
- **Stateful CARS arXiv 2608.08282（2026-08-08）、Appendix B** https://arxiv.org/html/2608.08282 　前半 100,000 字を読んだ。τ-bench 15 task、6 variant。事前宣言のマージン δ=0.10、20,000 回の paired bootstrap、task を cluster として resample。reward 差 −0.000 の区間が [−0.089, +0.100]、結論は「this sample size cannot certify non-inferiority」（underpowering であって害の証拠ではない）。2 つの Haiku variant が逆向きに −0.133 / +0.133 動いた。違い: reward が連続値寄りで、こちらの二値はさらに粗い。**統合者の確認（z=1.645 で Wilson 片側下限を再計算）**: 12/12 全合格でも下限は約 0.816（replay note は約 0.82、両側 95% なら 0.76）。**新形が 12/12 でも「旧形より 10 点以内の劣化」とは統計的に言えない**。
- **Terminal-Bench 2.0 leaderboard 解析（LessWrong 2026-08-05、nateg551015）** https://www.lesswrong.com/posts/GiPmLmmbT6DyrwYkH/terminal-bench-leaderboard-rankings-luck-or-skill 　全文。task cluster の bootstrap で隣り合う順位 25 組中 24 組は task のサンプリング誤差の範囲。ICC 0.5〜0.8。52,104 trial を独立と見ると CI が半分に縮む誤り。同じ model で scaffold だけ変えると Opus 4.5 で 15 点、Haiku 4.5 で 22 点動く。→ 同じ task を何回回しても独立標本は task 数。run を増やしても task 数の限界は消えない。
- ICC 論文 arXiv 2512.06710（2025-12-07、abstract のみ）: ICC は構造化 task で n=8〜16 trial、複雑な推論 task で n≥32 で収束。「accuracy の改善は ICC も改善したときだけ sub-agent 置換の判断に使える」。coding は対象外。arXiv 2607.12338（2026-07-14、abstract 相当）: 閾値 δ・coverage 規則・unresolved の許容率を**事前に宣言**せず task の割合だけでは判定規則にならない。n=5〜8 の直接試験ではない。検索要約（本文未確認）: exact McNemar は「等しい」の検定で非劣性ではなく、HALT（arXiv 2608.02009）は McNemar を方向の診断に留めて Newcombe 型の非劣性区間（マージン 2 点）を判定規則にする。
- 代わりの判定規則の公開先例は見つからなかった。最も近いのは R9 の「flip を読む」運用（有意差検定でなく、どの task が flip したかを trace で読む）。

**R7. 合否を外から持ち込む機械検査を先に置く**
- SWE-bench 系: 固定 base commit に task を戻し、patch を当て、hidden test（FAIL_TO_PASS / PASS_TO_PASS）で判定する（replay note の既存知識。一次 README は未取得）。弱点: OpenAI は 2026-02 に SWE-bench Verified の報告をやめ、失敗 task の「半分以上でテストが task 記述にない仕様を検査していた」。contamination も確認（二次: Latent Space 2026-02-23、原文は 403）。→ **hidden test が元実装に寄りすぎると旧形・新形のどちらにも別の偏りが入る**。
- Terminal-Bench / Harbor: verifier が agent と同じ環境で走るため破られる事例が多い（BenchJack arXiv 2605.12673、Terminal Wrench arXiv 2604.17596。snippet、本文未確認）。対策例: テスト file を agent の操作後に配置、per-trial nonce、空の parse 結果は不合格（`all([])` が True になる事例）。→ 判定用の検査は agent の作業が終わってから外から持ち込む。
- 先例: PROCTOR の L3（R6）、AgentLens（arXiv 2607.06624、abstract のみ: 機械検証できる所は formal verification、残りを LLM の trajectory review と side-by-side 比較）、Anthropic evals 記事（deterministic grader を先に）、記事 K1（final message の rubric 採点は「出発点」）。**「deterministic first が judge 単独より高い一致度を出す」という比較実験は見つからなかった**（設計の先例のみ）。
- 自 repo の履歴から task を作る先例: Change2Task arXiv 2607.28591（2026-07-30、abstract のみ。merged PR から同じ repo の後の revision 上に task 状態を再構成、1,130 変更から 900 組、historical と reconstructed の結果一致は up to 98.0%。**未来 leak の扱いは abstract に無い**）、CursorBench（Cursor blog 2026-03-11、全文。Cursor Blame で commit を元の agent request に辿る。task 数は非公開）、SWE-Gym / SWE-smith（snippet、学習環境で比較方法は無い）。

**R8. LLM judge は実装者と別系統にする**
- Panickssery, Bowman, Feng arXiv 2404.13076（2024-04-15、abstract）: LLM evaluator は自分の出力を高く評価し、自己認識と自己選好に線形の相関（fine-tune 実験）。
- AgentLens arXiv 2607.06624（2026-07-07、abstract のみ）: 検索要約に「2 つの frontier judge が 23% で不一致、各 judge が自分と同系統の agent を 18% で選び他方は 5%」とあるが**本文未確認**。
- 同一 family の限界は B3-5（Greptile、差 2〜3 point、業者）、B3-6（issue #81178）、Cognition（B1-2: 共有するのは訓練由来のバイアス）にも出る。Chen et al.（B3-7）は自己選好の多くが実際の優位で説明できるとする。
- position bias（検索要約のみ）: pairwise で A/B を並べて選ばせるなら位置を入れ替えて 2 回採点し平均する。単一 rubric 採点なら位置は無関係。
- 含意（推論）: 新形では実装者と reviewer と採点者が同じ model 系統になりやすい。採点者を別系統にするか最終判定を機械検査にする。ハーネスには別 family の `codex:rescue` が既にある（adversarial）。

**R9. Anthropic が示す小規模運用の指針（K1 と K2 の評価の作法）**
- 記事（K1）: 「one shared end-to-end set owned by a central team with smaller eval sets shipped with each skill」「Even a set of 10 golden examples is enough to start」。「Compare eval performance with and without the subagent」「don't just examine the final score, take a look at which tasks flipped」「run each task more than once, since a break like this one only showed up in one run out of two」。変更前に「an eval task for every chain of agents that runs together in production」。「keep it as a subagent only if the folded version scores worse」（数値閾値なし）。原則は「measure, change one thing at a time, and keep what holds up」。再生について「internal systems are difficult to replay and user engagement is difficult to simulate」と認めたうえで「record timestamps on important events, so they can be replayed later to run as targeted evals」と書く。**これ以上の再生手順は書いていない**。例の support agent では、subagent を畳むと遅延は減ったが注文照会 tool で自答して配送 specialist に聞かなくなり、壊れ方は 2 回中 1 回だけ出た。
- kit（K2）: 開始は 10 task × 各 2〜3 rep、noise band（rep 間のぶれ）を PLAN.md に記録。model id を変種ごとに固定。「grades the outcome, not the path」で一部は決定的 grader（期待しない書き込みを fail にする等）。期待結果は人間と決める。実 transcript を task の主な源にし個人情報は置換。`chain_coverage.py` で本番の chain ごとの eval task を検査。fold 後も通った chain task の trace を開き片方の findings がもう片方に使われたか確認。skill を外して tool だけ残した版も測る。
- 種別: 運用指針（意見）。有意差検定ではなく flip を読む運用。

**R10. Claude Code の評価道具（取得 2026-10-26）**: `claude plugin eval`（v2.1.269+、早期 access の文言あり、サーバ側で停止されうる）は plugin 内の case を新しい isolated な `claude -p` 子 process で 3 run 既定で採点し、no-plugin baseline との差 Δ を出す。grader は `regex` `tool_used` `tool_order` `file_exists`（無料）と `llm`（3 票中 2 票）`baseline`。`context.history_file` に transcript の .jsonl を与えるとその続きの 1 turn を評価できる。**隔離の中身**: 「Nothing personal or project-level loads. Your user settings, hooks, `CLAUDE.md` files, MCP servers, other installed plugins, memory, and skills are absent.」→ `~/.claude` の rules・hooks・CLAUDE.md・他 skill は run の中に無く、task-triage の judge / build をそのまま再生できない（必要物を plugin に同梱した場合だけ入る）。全 run と judge 呼び出しは plan 使用量 / API 課金に入る。

**R11. 「本番の記録を再生して評価に使う」の製品系**: FutureAGI、Datadog agent skill（1 本の production trace を local code に再生して出力を diff）、Arize（trace→eval、LLM judge を人のラベルで検証してから使う）、ZenML Kitaru（vendor の主張、検証なし）。coding agent の測定済み事例は見つからなかった。**区別（推論）**: 製品系の replay は入力を固定して新しいコードに通し出力を比べる。今回の再生は過去の repo 状態 + packet を復元し agent を最初から走らせ直す re-execution で、tool 出力の記録は使わない。前者の道具はそのまま合わない。

## Contradictions

**C-1. best-practices の「fresh session で実行」 vs 「planning, implementation, testing は main で」**（B0, A2）
- 文言の出所が違う: 前者は best-practices、後者は sub-agents page（依頼文は両方を best-practices と呼ぶが、notes が確認したのは sub-agents page）。同じ Claude Code docs の別ページが逆の既定を示す。
- 条件の違い: fresh は interview や訂正の積み重ねで膨らんだ context を捨てて実装に集中させるとき。main は複数 phase が大きな context を共有するとき。best-practices 自身が「deep in one complex problem で history が価値を持つときは蓄積させよ」と留保する。
- どちらが強いかは決まらない。**どちらも測定のない vendor の指針**。分かれ目は judge の context が triage で膨らんでいるか（Local evidence 4）だが、劣化の閾値は B5 に数値がない。

**C-2. Opus 5 prompting doc の「自己検証に subagent を使うな」 vs best-practices の「adversarial review step」/「fresh な model に反駁させる」**（B1-5, B0）
- 前者は over-verification のコスト指針（Opus 5 は指示無しで自己検証する）。後者は無人が長いほど独立検証が効くという指針。Opus 5.5 の page には前者の項が無く、「Opus 5 の pattern は出発点として妥当」とだけある。
- どちらも vendor の記述で測定なし。独立 reviewer 側に有利な第三者の証拠は弱い（CCR p=0.26〜0.057 の小標本 B3-4、Greptile 差 2〜3 point の業者 B3-5、issue #81178 の n=1 B3-6）が、逆向きの測定は notes に無い。Opus 5.5 世代の self-check の信頼度は未測定。
- 記事の「model が作業を自分で検査する」と Anthropic 2025-11 の「feature を未テストで complete にしがち」（B2-9）の差は、世代差かもしれない（article-primary）。B3-1 は世代で検証の要否が変わると書く。

**C-3. Anthropic multi-agent research（+90.2%）vs 記事（単一 loop が frequently outperformed）**（K3, K1）
- domain の差: 前者は research 課題（並列探索、内部 eval、token 使用量が分散の 80% を説明）、後者は顧客向け multi-capability agent（非公開比較、数値は 1 社の 2x）。同じ会社が domain ごとに逆の結論を出している。
- coding はどちらかは未決。K3 は「coding は research より並列化できる部分が少ない」、B2-9 は単一 coding agent の優位を「still unclear」と書く。Google/MIT（B1-4）の「逐次は単一、並列可能なら集中型」は domain 分けと整合するが abstract のみ。
- 強さ: 公開された eval を持つのは K3 側。記事側は測定が非公開。ただし K3 の利得は計算量で説明できる部分が大きい。

**C-4. reviewer の過剰指摘 vs 早期合格**（B3-3）
- best-practices は「gap を探せと頼むと健全な作業にも報告し、追うと over-engineering になる」と警告する。Jan 2026 記事は「verifier が 1〜2 test を通して成功と宣言する」と逆を警告する。独立 reviewer は両側に失敗しうる。
- 対策は criteria の設計という点で一致する（前者は「正しさと明示要件に影響する gap だけ」、後者は「網羅的検査・negative test・明示指示」）。Cognition は reviewer の指摘を書き手側で濾過する橋渡しを要した（B1-2）。B の目的（bounce を減らす）に対し、過剰指摘は reviewer 側が bounce を作る方向に働く。
- Anthropic の Code Review が示す false positive 1% 未満（B3-2）は engineer の同意ベースの内部数字で、この食い違いを解く強さがない。

**C-5. 「feature と test は同じ agent」 vs 「dedicated な verification agent」（同じ Jan 2026 記事の中）**（B1-3）
- 記事は両方を推奨し、全ケースでは解いていない。解く鍵として「Verification requires minimal context transfer by nature」と「More capable orchestrators can sometimes evaluate subagent work directly」を挙げる。B（judge が実装 + 検証だけ fresh）はこの 2 文と整合するが、記事が B を名指しで支持しているわけではない。

**C-6. 個人・小規模 harness でも逆向き**（B2-3, B2-7, C2, C3）
- Superpowers は task ごとに fresh subagent、Zechner / HumanLayer / Amp は subagent を絞る。どちらも対照実験なしの採用実績で優劣は決まらない。前者は長い plan の drift、後者は観察可能性と context 制御を問題にする。
- Cognition は 2025-06「単一スレッド」から 2026-04「clean context の reviewer / Smart Friend は有効」へ精密化した（矛盾でなく更新）。Amp の「3.7 は呼ばない / Sonnet 4 は好んで委譲」は効用が世代依存であることを示す。

**C-7. context の長さ: vendor の「一貫している」 vs 実測の劣化**（B5）
- Opus 5 の doc は 1M 内で性能が一貫すると書く（数値なし、Opus 5.5 の page で確認できず）。Anthropic の context-windows page と Classifier Context Rot（Opus 4.6 で 100K 99.7% → 800K 69%）は劣化を示す。Chroma は Claude 4 世代以前。
- 400K〜967K 域での Opus 5.5 の長 context 品質の実測は notes に無い。

**C-8. 小標本の指針 vs 統計の結論**（R9, R6）
- Anthropic は「10 golden examples で開始」「early agents は large effect を示すので小標本で検出できる」と言う。PROCTOR・Stateful CARS・Terminal-Bench 解析・KTH は、小標本で非劣性を証明できず、1 case が 12〜25 点動くと示す。
- 目的が違う（開始と大きな退行の検出 vs 非劣性の証明）。flip を trace で読む運用（R9）が Anthropic 側の実際の判定法で、検定ではない。

**C-9. gate の実体に関する notes 間の食い違い**（A）
- adversarial §5 は research-gate.sh が「report の存在しか見ず内容を見ない」ので主ループが書いても gate は通ると読む。lead の Local evidence 3 は `~/.claude/hooks/research-gate.sh:313` が「書き手が researcher であること」を要求すると言う。後者は行番号付きで実物に近い。gitStatus にはこの hook の未 commit 変更があり、どの版を指すかは統合者には確認できない（実物を読むのは lead）。

**C-10. 二次情報と原典の食い違い**（C7）: marmelab の NLAH「reviewer -8%」は原典 Table 5（verifier +0.20 / +8.40）と合わない。Agyn の 72.2% vs 71.8% は数値は合うが比較条件が違う。

**C-11. ADR との対応（lead の ADR と外部）**: ADR-0023「review・検証は fresh、計画・実装は rich」の前半は B3 系が支持する。後半（実装 = rich）を直接支持する実測は無く、支えは Cognition の trace 共有原則（設計論）と sub-agents page の「複数 phase が context を共有」だけ。記事は「実装は rich context 側」と書いていない。後半に緊張を与える材料は B1-6（強い model で planning の精度寄与が小さい）と B2-5（実装 trace が計画役を汚す）。ADR-0057 の「文脈損失は packet で救う」は Fable のコスト根拠で、精度の測定ではない（Local evidence 参照）。

## Local evidence

出典: lead が 2026-10-26 に実行して prompt で渡した材料（項目 1〜6）と、claude-code-features の調査者が read-only で読んだ設定（項目 7）。

1. **subagent 起動数**（`~/.claude/metrics/agent-usage.jsonl`、Agent tool 起動のみの下限、直近 30 日）: general-purpose 256（transcript の description では大半が組み込み `/simplify` の 4 観点並列、ほかに stocktake の分割と skill-creator の下書き検査）/ researcher 141 / readme-judge 37 / security-reviewer 30 / adr-reviewer 23 / Explore 11 / architect 3。直近 90 日: prompt-writer 0、refactor-cleaner 3、prompt-forager 5、swift-reviewer 7。
   - 効く先: C。`/simplify` の fan-out は公式 doc の記述（4 review agent を並列、正しさのバグは探さない）と一致した（B4）。reviewer 系の約 90 件（readme-judge, security-reviewer, adr-reviewer）と `/simplify` 並列は、kit の audit では独立検証型と並列型に当たり、記事が残す条件（検証・並列）に入る（article-primary の読み）。prompt-writer 0 件の退役は、記事の「別 persona / voice / 長い prompt は別 context に値しない」と整合（同）。refactor-cleaner を skill に畳むのは「skill は共有 content、subagent は context 隔離」の分け方に合うが、大量読みを隔離しているなら Context テスト（1 回数万 token）で判定する（同）。
2. **cloud への dispatch**（`~/.claude/logs/cloud-dispatch.jsonl`）: 記録開始以来 3 回（2026-09 に 1、2026-10 に 2、すべて contemplative-agent）。spawn-session の SKILL.md 読み込みは直近 30 日で 32 回（build 以外の用途を含む）。
   - 効く先: B6。標本が小さく、外部の数値と比べる材料にならない（practice-coding-agents）。B の dispatch 条件を決めるには自前の過去 dispatch と同種 task を judge 実装で再生する比較が要る。
3. **research report の種別**（各 repo の `docs/plans/research/` の 1 行目）: external 23 本 / internal 12 本。internal は、researcher（Bash を持たない）が lead の実行した再現手順の出力を受け取って書き写す形（`~/.claude/agents/researcher.md` の内部調査テンプレ「lead が実行した出力を受け取って書く」）。gate を開ける条件は `~/.claude/hooks/research-gate.sh:313` で、書き手が researcher であることを要求する。
   - 効く先: A。書き写しの形は A2・A4 の「doc が想定する subagent の適所」と合わない（推論）。gate の実体は C-9。
4. **triage judge セッションの context の大きさ**: `task-triage` の SKILL.md を読んだセッション 51 本の transcript から、assistant turn ごとの input + cache read + cache creation token の最大値を取った。全体の中央値は約 377K、最大は約 887K。judge が Opus 5.5 high になった 2026-10-11（commit 29bd389）以降の 6 本では中央値約 240K、最大約 887K。それ以前の Fable 5.1 の 13 本は中央値約 548K。現行の `~/.claude/settings.json` は Opus 5.5 に `autoCompactWindow: 400000` を設定している（いつ入ったかは未確認）。測ったのはセッションの最大の大きさで、実装を行った時点の大きさではない。
   - 効く先: B0, B5, C-1。**外部資料は閾値を与えない**。B5-1 の数値（Opus 4.6 で 100K 99.7%、800K 69%）は課題が分類で、間の値も Opus 5.5 の値も無い。中央値 240K は 100K と 800K の間にあるが、補間はできない。K1 の残す条件(1)「context bloat による劣化が測れる」は、再生比較で測ることになる。
   - 統合者の観察（推論）: 最大 887K は `autoCompactWindow` 400K を超える。設定が後から入ったか、400K が硬い上限でないか、どちらかで、設定が入った日が分かれば 6 本のうちどれが 400K 下かが分かる。
5. **build セッションの Phase 0**: 現行でも Phase 0 で前提を自分で確かめ直してから実装する（`~/.claude/skills/task-triage/SKILL.md:22`）。build に欠けるのは task の文脈ではなく、judge の台帳横断の判断過程と人間の digest 回答（packet に書かれる分を除く）。
   - 効く先: B1-1（packet が暗黙の判断を落とす懸念）。前提の file:line 側は build の再確認で救われ、台帳横断の判断過程は救われない（lead の整理）。
6. **再生の題材の候補**: contemplative-agent の rfcs/ に完了タスク 37 件（全 61 件）、task branch の merge commit に judge の検証メモ（「judge: … verify.sh exit 0」）。完了した rfc ファイル自体に結果が書かれているので、再生では task 開始時点の rfc の版を渡す必要がある（漏れの経路）。
   - 効く先: 再生の方法。合否の機械側は `.claude/verify.sh` の exit 0 が使える。ただし**旧形で使った検査と同じ verify.sh を新形の合格基準にすると旧形に最適化された基準になる**（R7 の hidden test 問題）。merge commit の diff に含まれるテストを外から持ち込む案と、verify.sh を PASS_TO_PASS 相当にする案がある（replay note）。worktree + task branch での運用は R4 の漏れ経路（`git log --all`、`show-ref`）に直結する。
7. **settings の読み取り**（claude-code-features の調査者、read-only、2026-10-26）: `~/.claude/settings.json:4` `env.CLAUDE_CODE_SUBAGENT_MODEL = "opus"`。frontmatter が env に勝つため researcher（`model: sonnet`）・refactor-cleaner（sonnet）・prompt-forager（sonnet, `effort: low`）・Explore（sonnet）は sonnet、frontmatter を持たない general-purpose（`/simplify` / `/code-review` の fan-out agent と推定）は opus、`architect` は `model: fable`、reviewer 系は `opus`。`~/.claude/settings.json:382-393` `modelSettings.claude-opus-5-5 = { effortLevel: "high", autoCompactWindow: 400000 }`（model-config の既定は medium・約 967K で compact）。subagent の `autoCompactWindow` frontmatter は未設定。`CLAUDE_CODE_FORK_SUBAGENT` / `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` / `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` / `worktree.baseRef` の設定は無い（grep）→ fork mode は既定 on、subagent の起動は背景が既定、worktree の base は default branch の既定。
   - 効く先: B4（fork 既定 on の「待てない」帰結、`baseRef`）、C6（sonnet → opus の model 変化）。
8. **ADR の位置づけ**（lead が渡した材料、article-primary と adversarial と practice が各自照合）: ADR-0023（review・検証は fresh が資産、計画・実装は rich が資産）は C-11。ADR-0024（凍結入力を渡す render 契約、大量 context の隔離）は best-practices の「self-contained な spec を fresh session に渡す」に近い。ADR-0057（2026-08、文脈損失は dispatch を避ける理由にしない、packet の充実で救う）の根拠は Fable のコストで、judge が Opus 5.5 high になった 2026-10-11 以降は変わっている（Opus 5.5 の medium は Opus 5 の high と同等以上という Anthropic の testing、B1-5 の隣の doc）。

## Still unknown

- **coding での直接比較**: 同一 model・同一 harness・同一 task で「計画者が実装」と「packet だけの fresh 実装」、または単一 loop と実装 subagent を比べた公開実測。Anthropic も未決と書く。自前の再生で測るしかない可能性が高い。
- **記事の元データ**: Applied AI team の比較の件数・task 種別・指標・n。公開されていない。記事原文での照合（上の Scope searched の (a)(b)）。
- **judge の context 劣化の閾値**: Opus 5.5 の 100K〜967K、特に 240K〜400K の長 context 品質の実測。Local evidence 4 の 887K と `autoCompactWindow` 400K の食い違いの理由（設定が入った日）。judge の context が実装時点でどの大きさか。
- **self-check の信頼度**: Opus 5.5 / Fable 5.1 世代で、同一 session の自己検証が独立 reviewer にどこまで近づいたか。
- **reviewer の設計**: 同一 family（Opus）の reviewer が judge と盲点を共有する程度、cross-family（`codex:rescue`）の効き。reviewer に渡す情報量（diff のみ / diff + 受け入れ条件 / packet 全体）と検出率の関係（CCR は artifact 検出）。judge が reviewer の指摘を過度に棄却または採用するか。
- **anchoring**: judge が自分の packet の前提に沿って実装し反証を守る傾向の、coding での直接測定。
- **A**: 主ループ自己執筆 report の省略率。測るなら同一 task で researcher 経由と主ループ執筆の report を file:line の正否で比べる。gate の実体（C-9）。
- **Claude Code の仕様**: `/code-review` と `/simplify` の内部 agent 数と model / effort の継承。`CLAUDE_CODE_SUBAGENT_MODEL=opus` の subagent が `modelSettings` の effort を継承するか。`isolation: worktree` + `baseRef: "head"` で未 commit の変更が入るか。task-triage が対話 session か `claude -p` か（fork の「待てない」帰結は前者だけ）。`claude plugin eval` の `name@skills-dir` が `~/.claude/skills` 相当を対象にできるか。
- **再生**: 判断型作業（packet を書く・検収する）の run 間 flip 率（SWE-bench の 10.6% は代理にならない可能性）。5〜8 task × 2 run で「失敗が多い」とみなす代わりの判定規則の先例。**R4 の推論の実機確認**（再生環境で `git log --all`・`git fsck --lost-found`・`git show-ref` が正解 commit に届かないこと）。repo 外の漏れ（MEMORY.md、episode log、`.notes/`、rfcs の後続エントリ）の切り方。task が model の学習 cutoff より後か。実装者と別系統の model で採点したときの self-preference の大きさ（18% / 5% は本文未確認）。
- **C**: 使われない agent の退役閾値の先例（notes に無い）。Claude Code 利用者が custom subagent を skill に畳んだ一次報告。skill が増えたときの選択精度の臨界点が、このハーネスの skill 数でどこにあるか（C5 は coding でない）。
- **本文未読の一次**: kit の `02-merge` `04-as-tool` `05-upkeep` と `example-run/`、managed-agents の multiagent-orchestration doc、Superpowers の一次 README、Azure SRE Agent の一次本文、NLAH の末尾 9,931 字と他表の「-8%」の有無、Google 2512.08296 と CCR の全文、DeepSWE / BenchJack の本文、Opus 5.5 の system card、Amp の 2026-05 の compaction 復帰の真偽。
- **dispatch 条件**: 「長時間・無人・ローカル環境が要るものだけ dispatch」を支持または反対する外部資料。無人なら検証を独立に置くことは支持されるが、実装の dispatch は支持されていない（B6）。

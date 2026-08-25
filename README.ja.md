Language: [English](README.md) | 日本語

# claude-harness

shimo4228 が日常的に使っている Claude Code ハーネス (skills / agents / rules / hooks) の公開版。

skills / agents / rules は `~/.claude/` 配下から `origin: shimo4228` タグを持つ資産を機械的に集約したもので、ECC 由来 (origin: ECC / ECC-customized) や自動抽出物 (origin: auto-extracted) は含まない。ADR は丸ごと、hooks は curated allowlist で同期する — hooks の公開可否は「誰が書いたか」ではなく「このマシンの外で再利用できるか」の判断。

## 位置付け

- **対象**: Claude Code (CLI + IDE extensions) のユーザー、および agent skill / rule エコシステムを研究する開発者
- **運用方針**: `~/.claude/` が source of truth、この repo は [`scripts/sync-from-local.sh`](scripts/sync-from-local.sh) による一方向エクスポート (origin filter + hook allowlist → secret scan → subtree 置換)
- **ライセンス**: MIT。自由にコピー・改変・再配布可能。fork して自分用にカスタマイズする使い方を歓迎

## 中身

### Skills

<!-- BEGIN GENERATED: skills-table -->
| Skill | Purpose |
| --- | --- |
| [search-first](skills/search-first/SKILL.md) | Research-before-coding workflow。scout agent を呼び出して既存ツールを探索 |
| [learn-eval](skills/learn-eval/SKILL.md) | セッションから再利用可能なパターンを抽出し、品質評価を経て保存先を決める |
| [skill-stocktake](skills/skill-stocktake/SKILL.md) | Skill の品質監査 — Glob インベントリ + 単一コンテキスト holistic 評価、Keep/Improve/Update/Retire/Merge 判定 |
| [skill-health](skills/skill-health/SKILL.md) | Skill ライブラリの構造的 debt スキャン — "missing artifacts"（SKILL.md が参照する script / agent / sibling skill がディスク上に存在しない）を検出。決定論的で、品質 / risk / validation は skill-stocktake / security-scan / skill-comply に委譲 |
| [rules-distill](skills/rules-distill/SKILL.md) | Skill 群から共通原則を抽出し、rule として昇格させる |
| [rules-stocktake](skills/rules-stocktake/SKILL.md) | Rules の品質監査 — residency cost（全行が毎セッションの token 税）モデル、staleness / substrate absorption 検査、Keep/Improve/Update/Merge/Demote/Dissolve/Retire 判定。rules-distill の逆方向 |
| [skill-comply](skills/skill-comply/SKILL.md) | Skill / rule / agent の実際の遵守率を計測。3 段階 prompt で行動シーケンスを分類 |
| [context-sync](skills/context-sync/SKILL.md) | プロジェクト documentation を監査・修正。役割重複検出、鮮度チェック、欠損作成 |
| [codex-review](skills/codex-review/SKILL.md) | OpenAI Codex CLI（別モデルファミリ）の read-only セカンドオピニオン（argv と config の両面で pin）— (1) 現在の diff のコードレビューを review chain に統合、(2) plan 段で設計パケットの前提を反証（反証 / 欠落制約 / 代替のみ、設計はさせない） |
| [llms-txt-writer](skills/llms-txt-writer/SKILL.md) | llms.txt / llms-full.txt 等の AI 向けドキュメントを書く。Answer.AI 標準 + GEO/AEO 静的解析 |
| [jsonld-knowledge-graph](skills/jsonld-knowledge-graph/SKILL.md) | `llms.txt` の companion となる JSON-LD ナレッジグラフ (`graph.jsonld`) を設計・出荷。ドメインエンティティと関係を schema.org triple として encode して LLM 引用を最適化 |
| [writing-ecosystem](skills/writing-ecosystem/SKILL.md) | 人間向け執筆・レビューの orchestrator。editor / essay-reviewer / fact-checker の使い分け |
| [collect-context](skills/collect-context/SKILL.md) | セッション内外のコンテキストを集めて記事執筆用の素材を作る |
| [authorship-strategy](skills/authorship-strategy/SKILL.md) | DOI 登録された idea-rescue 研究 repo 向けの 4 層 framework (Authenticity / Attribution diffusion / Idea-vs-scaffold / Tactics) |
| [release-doi](skills/release-doi/SKILL.md) | DOI 登録された研究 repo のバージョン release を切る (Zenodo concept DOI 意味論、CHANGELOG / tag / asset packaging) |
| [adr-writer](skills/adr-writer/SKILL.md) | 設計判断を連番 ADR として記録 — ディレクトリ検出・採番・index 更新。本文生成は adr-writer agent に委譲 |
| [paper-ecosystem](skills/paper-ecosystem/SKILL.md) | 学術論文の執筆・レビュー orchestrator — paper-writing + 5 reviewer agent の役割境界と Source Fidelity / Vocabulary / Voice / Clarity / Citation 規約の正本 |
| [paper-writing](skills/paper-writing/SKILL.md) | 学術論文の draft 手順 — title / outline / section / abstract / references。claim と cite の 1:1 mapping を強制 |
| [paper-deposit](skills/paper-deposit/SKILL.md) | レビュー済み論文を Zenodo に単独 DOI record として登録、SSRN cross-post と研究 repo への DOI 編入まで |
| [ai-native-preprint-submission](skills/ai-native-preprint-submission/SKILL.md) | deposit 済み論文を AI-native preprint プラットフォーム (aiXiv / AiraXiv) へ投稿 — 人間ゲート付き browser automation または著者委任の API/MCP 投稿 |
| [readme-writer](skills/readme-writer/SKILL.md) | 人間向け README を書く — 決定論的な構造 lint + スコアなしのホリスティック LLM review |
| [hf-sync](skills/hf-sync/SKILL.md) | graph.jsonld を持つ研究 repo の Hugging Face Datasets ミラー同期 |
| [citation-sync](skills/citation-sync/SKILL.md) | 研究 repo の引用 4 層 (docs / .zenodo.json / graph.jsonld / Wikidata P2860) を監査し下層から同期 |
| [spawn-session](skills/spawn-session/SKILL.md) | Herdr の pane に detached な Claude Code Remote Control セッションを起動し、モバイルアプリの一覧に出す |
| [harness-sync](skills/harness-sync/SKILL.md) | 生きた harness から本 repo への origin filter 付き一方向エクスポート — 収集・secret scan・subtree 置換 |
| [cited-source-mirror-verification](skills/cited-source-mirror-verification/SKILL.md) | access-blocked / digest 由来の数値主張を、durable な引用の前にオープンミラーで検証する guardrail |
| [wiki-harvest](skills/wiki-harvest/SKILL.md) | 研究 repo セッションから Obsidian LLM wiki (wiki/concept/) を read-only で走査し、repo の次アクションを変えうる候補だけを一次出典付き・ランク付き ledger として repo の `.notes/` に抽出 |
| [wiki-query](skills/wiki-query/SKILL.md) | Obsidian LLM wiki (wiki/concept/) への read-only クエリ。`[[ ]]` 出典付きで合成回答 |
| [repo-asset-stocktake](skills/repo-asset-stocktake/SKILL.md) | プロジェクト repo の非コード資産（ツール設定・CI workflow・runbook）の価値劣化を監査 — 消費者が消えた資産を検出し Keep/Update/Retire/Merge 判定 |
| [task-stocktake](skills/task-stocktake/SKILL.md) | repo の pending タスク追跡を単一台帳へ棚卸し・統合 — 台帳の bootstrap、散在タスク行の収集、git log・実コードとの既済照合 |
| [llm-as-judge](skills/llm-as-judge/SKILL.md) | Design pattern for LLM-as-judge evaluators — binary checks as evidence, one named holistic verdict, no score aggregation |
| [implementation-chain](skills/implementation-chain/SKILL.md) | task 種別（feat / fix / refactor / chore / prototype / writing）を判定し、対応する agent chain を plan に front-load する判断表 — Chain Matrix、レビュアー routing、早期停止条件 |
| [public-comment](skills/public-comment/SKILL.md) | 公開技術スレッドへの返信 — AI slop tell の除去、スレッド接地、投稿前の日本語訳併記による人間 gate |
| [agent-stocktake](skills/agent-stocktake/SKILL.md) | subagent 定義をハイブリッド cost model（description = 毎セッション常駐 / body = 起動時ロード）で監査 — 抑制指示と substrate 吸収を検出する第 3 の stocktake |
| [generation-audit](skills/generation-audit/SKILL.md) | モデル世代交代時に runtime 層（system prompt + tool description）を実セッションから採取し、競合 / 冗長 / ドリフトに分類して各 stocktake に証拠として渡すオーケストレータ |
| [git-workflow](skills/git-workflow/SKILL.md) | この環境での git 実行作法 — 1 Bash call = 1 git コマンド。&& やパイプで連結すると Bash(git:*) の自動許可が外れて手動承認になる |
| [headline-craft](skills/headline-craft/SKILL.md) | 「開かせる一行」の craft — タイトル・tagline・subtitle・SNS 告知文の候補生成と、流入経路 2 軸（検索 / フィード）での評価 |
| [herdr-delegate](skills/herdr-delegate/SKILL.md) | Herdr の pane に別プロセスの CLI エージェント（Codex 等）を立てて実装タスクを丸ごと委譲する。ユーザーの明示指示があるときだけ使う — 並列化できそう、は理由にならない |
| [prompt-perturb](skills/prompt-perturb/SKILL.md) | 多様性の注入。文脈をあえて持たない forager agent が外部の創造技法カタログからプロンプトを拾ってくるので、角度がセッション自身の手癖の外から来る |
| [session-judgment-mining](skills/session-judgment-mining/SKILL.md) | 過去のセッション記録から、ユーザーが繰り返し下した判断を発掘し、再出現するものを skill / rule に正本化する |
| [verify-bootstrap](skills/verify-bootstrap/SKILL.md) | repo の機械ゲート（format / lint / type check / security / dependency / test）を立てる、または古びたゲートを棚卸しする。ツール選定は skill に焼き込まず、その時点で調べ直す |
| [x-draft](skills/x-draft/SKILL.md) | リサーチレポートを長文 1 ポストの下書きにする。pull 型で、通知もノルマもなく、投稿したいと思ったときだけ呼ぶ。一次ソースの再確認と陳腐化ゲートを通し、AI tell を落として下書きで止まる（投稿は人間） |
| [task-triage](skills/task-triage/SKILL.md) | タスク台帳を回す loop の 1 周: 開いている全タスクを判定（前提・着手条件・価値）し、ready を新しい build セッションへ dispatch、成果を独立に検収 — merge の言葉は人間が持つ |
| [harness-boundary](skills/harness-boundary/SKILL.md) | mechanism（rule / skill / hook / agent / workflow）を足す前の設計レンズ — 6 層のどこに置くか、モデルに任せられないか、runtime 交換後も残るか。harness を捨てても残るものだけを資産にする |
| [skill-creator](skills/skill-creator/SKILL.md) | skill / agent 定義を書く・書き直す入口 — intent packet、library 全体での境界確認、Fable 向けの書き方、fresh-context の草稿ゲート（Publishable / Fix / Drop、集計なし）、著者通読。upstream の anthropics skill-creator をその場で置換（ADR-0046） |
| [measurement-discipline](skills/measurement-discipline/SKILL.md) | 測定に基づく主張・閾値・ガード・実験結果を設計または評価するときの規律。Use when the user says 「この実験結果で判断していい？」「閾値を決めたい」「ガード/検査を足したい」「1 回通ったから大丈夫」, when a design places a numer |
| [prose-translation](skills/prose-translation/SKILL.md) | 日本語⇄英語の voice 保持翻訳スキル（**両方向**）。エッセイ・記事・README・ADR 等の人間向け prose を、出力先の publication channel contract が宣言する register と原文の確度を保って自然に訳す。逐語訳でも MT で |
| [quality-gate](skills/quality-gate/SKILL.md) | 人間向け公開物の受け入れゲート。完成稿と project の publication channel contract を読み、必須 reviewer verdict・機械検査・最新 title-reviewer findings が揃ったかを集約して PASS / FAIL / |
| [repair-discipline](skills/repair-discipline/SKILL.md) | バグ修正・残課題・schema/storage 変更に着手するときの規律。Use when the user says 「このバグ直して」「残課題をやって」「この schema を変えたい」, when picking up a stale task file, or when |
| [session-theme-mining](skills/session-theme-mining/SKILL.md) | 過去の Claude Code / Codex セッションを横断し、記事になりうる未解決の問いを 0〜3 件の同格な候補カードとして発見する。Use when — 「過去セッションから記事テーマを探して」「まだ書いていない問いを発掘して」「セッション履歴から collect-co |
<!-- END GENERATED: skills-table -->

> 最初の 6 つ (search-first, learn-eval, skill-stocktake, rules-distill, skill-comply, context-sync) は [Agent Knowledge Cycle (AKC)](https://doi.org/10.5281/zenodo.19200726) の構成要素。独立 repo として個別公開もしているが、この harness でも丸ごと読めるように重複収録している。

### Agents

<!-- BEGIN GENERATED: agents-table -->
| Agent | Purpose |
| --- | --- |
| [scout](agents/scout.md) | Pre-implementation solution discovery。npm / PyPI / MCP registry / GitHub から既存解を検索 |
| [prompt-writer](agents/prompt-writer.md) | 軽量モデルで簡潔な prompt を生成。LLM prompt template の作成・書き換え |
| [editor](agents/editor.md) | Strict technical article editor。コード正確性、AI slop、narrative flow、用語一貫性を厳格にレビュー |
| [essay-reviewer](agents/essay-reviewer.md) | Strict essay editor。社会理論 / 組織論 / デザイン哲学 / 個人ナラティブが混ざる idea 記事を対象 |
| [fact-checker](agents/fact-checker.md) | 事実検証スペシャリスト。記事から検証可能な claim を抽出し web で verify |
| [adr-writer](agents/adr-writer.md) | ADR 7 セクション本文（`Review-when` 失効条件を含む）を入力のみから生成 — context・失効条件・代替案の invention 禁止 |
| [codemap-writer](agents/codemap-writer.md) | `docs/CODEMAPS/` の生成・refresh — 各 map ~1000 token の token-lean アーキテクチャ文書 |
| [paper-reviewer](agents/paper-reviewer.md) | 学術論文の構造 review — argument flow / section transition / claim sharpness / evidence-claim alignment |
| [source-fidelity-checker](agents/source-fidelity-checker.md) | 引用された一次ソースを直接読み、論文 claim との drift を検出 |
| [vocabulary-consistency-checker](agents/vocabulary-consistency-checker.md) | 導入 term の定義一貫性と sub-classification の明示性を検証 |
| [clarity-reviewer](agents/clarity-reviewer.md) | 初見読者目線の明瞭性 review — 新語予算 / タイトル軸 / メタ語り / 内部文脈依存 |
| [citation-formatter](agents/citation-formatter.md) | In-text citation と reference list の整合・format・DOI / arXiv ID 検証 |
| [readme-reviewer](agents/readme-reviewer.md) | README / repo トップページの厳格レビュアー — LLM 読解フロア / lead 明瞭性 / human hook / 走査性 / 長さ規律 / 視覚効果。readme-writer の companion |
| [readme-clarity-reviewer](agents/readme-clarity-reviewer.md) | README の初見読者目線レビュー — 造語予算 / 内部文脈依存 / 日本語 register（ですます）。readme-reviewer の並列相方 |
| [adr-reviewer](agents/adr-reviewer.md) | ADR の「決定」ではなく「記録」を検査する — Context が検証可能な根拠を持つか、`Review-when` が観測可能な失効条件か、Alternatives が藁人形でないか（「未決 — 再訪条件」付きの対抗案は可）、Consequences が両面あるか、先行 ADR との関係（部分弱化は日付つき注記）が明示されているか |
| [prompt-forager](agents/prompt-forager.md) | prompt-perturb の、文脈を持たない側。目的の一行だけを受け取り他は意図的に渡さないので、見つかるものが依頼元のセッションに引きずられない |
| [swift-reviewer](agents/swift-reviewer.md) | Swift / SwiftUI レビュー — Swift 6 strict concurrency、値セマンティクス、SwiftUI の状態所有、retain cycle、HIG 準拠 |
| [readme-judge](agents/readme-judge.md) | README の fresh-context 判定器。証拠 JSON と README を 1 回読み、固定チェックリストに引用付きで答えて named verdict（Publishable / Fix / Rewrite）を返す |
| [prose-clarity-reviewer](agents/prose-clarity-reviewer.md) | First-contact reader clarity reviewer for human-primary articles, essays, blog posts, and newsletters |
| [theme-reviewer](agents/theme-reviewer.md) | 人間向け記事・エッセイの執筆前テーマレビュアー。選択済みの問い一文と素材を fresh context で読み、非自明性・一次アクセス・読者接続・外部言説との差分を点検して findings と深化の問いだけを返す。Use before editorial brief |
| [title-reviewer](agents/title-reviewer.md) | 凍結した人間向け原稿のタイトルレビュアー。headline-craft の候補と現行タイトルを fresh context で読み、中心命題との軸一致・誠実さ・具体性・好奇心の回収・channel 制約を点検して findings だけを返す。Use after 本文の構造凍結、 |
<!-- END GENERATED: agents-table -->

### Rules

毎セッション自動ロードされる行動原則 (rule/common/ 配下):

<!-- BEGIN GENERATED: rules-table -->
| Rule | Purpose |
| --- | --- |
| [agents](rules/common/agents.md) | Agent orchestration 規約。いつどの agent を使うか、並列実行のパターン |
| [akc-cycle](rules/common/akc-cycle.md) | Agent Knowledge Cycle の 6 フェーズ行動規約 (Research / Extract / Curate / Promote / Measure / Maintain) |
| [debugging](rules/common/debugging.md) | 根本原因優先のデバッグフロー (仮説 → 証拠 → 確認 → 修正)、AI のリーセンシーバイアス対策、retry-with-context |
| [planning](rules/common/planning.md) | 計画時の必須項目 (What / Why / Alternatives)。Phase 0 外部調査の義務化 |
| [skills](rules/common/skills.md) | Skill origin tracking の仕様と knowledge placement の原則 |
| [contemplative-axioms](rules/common/contemplative-axioms.md) | Laukkonen et al. (2025) の Contemplative Constitutional AI 原則 (verbatim) |
| [task-tracking](rules/common/task-tracking.md) | 単一タスク台帳（1 repo 1 ファイル）の原則 — 詳細資料にタスク行の正本を持たせない、MEMORY.md はポインタのみ、完了行は Done 節へ |
| [knowledge-staleness](rules/common/knowledge-staleness.md) | LLM 分野の外部知識は 1 週間スケールで陳腐化するという世界観を既定にする — 手法・仕様・相場観を記憶から断言せず検索時点で照合し、根拠に as-of 日付を、推奨に失効条件を付ける |
| [practitioner-identity](rules/common/practitioner-identity.md) | 著者の自己定義 (verbatim) — AI 時代に何が良い考え・良い手段かを探し続ける。DOI は手段の一つで研究者志向ではない。コードは消えるが考えは消えない |
<!-- END GENERATED: rules-table -->

### Hooks

`hooks/` には `git commit` 境界で走る PreToolUse hook 5 本 — secret scan、repo 自身の機械ゲートの起動、bandit scan、`ruff format --check`、レビュー確認 — と、それらが必要とする共有部品 2 つ、そして `rfcs/` 台帳とともに公開した session 面の hook 2 本（台帳作法のリマインダー + 台帳 CLI `scripts/claims.py`、judge-tier のレビュー起動ガード）が入っています。複数の ADR がこれらの内部挙動を論じているため、判断だけが宙に浮かないようコードも置いています。skills / rules と違い hooks は `settings.json` への手動配線が要ります。すべてに bats があり、いずれも負のコントロール（性質を壊した hook に対してテストが実際に落ちること）で確認済みです。導入手順・verify ゲートの承認モデル・意図的に公開していないものは [docs/hooks.md](docs/hooks.md) にあります。

### 設計判断 (ADR) と提案 (RFC)

`docs/adr/` には、このハーネスがなぜ今の形なのか — 採用・退役・方針転換 — を日付付きの Architecture Decision Record として記録し、コンポーネントと一緒に実働ハーネスから同期しています。上の skills / agents / rules が「何があるか」だとすれば、ADR は「なぜそうなったか」— 失敗も含めた監査証跡です。[ADR index](docs/adr/README.md) から読めます。

`rfcs/` はハーネスの公開タスク・提案台帳です（[ADR-0049](docs/adr/0049-unify-task-ledger-into-public-rfcs.md)）。1 エントリ 1 ファイル、本文は Rust RFC テンプレ準拠、状態は frontmatter。終端エントリも残置するので、却下された提案が理由ごと読めます。ADR が「決めたこと」、`rfcs/` が「まだ開いていること」— 建てないと決めたものが残るのが要点です。

## 使い方

### 全部入り

```bash
git clone https://github.com/shimo4228/claude-harness.git ~/.claude-harness
# skills / agents / rules を ~/.claude/ にコピー
cp -r ~/.claude-harness/skills/* ~/.claude/skills/
cp -r ~/.claude-harness/agents/* ~/.claude/agents/
cp -r ~/.claude-harness/rules/common/* ~/.claude/rules/common/
```

hooks は別扱いです。`~/.claude` 配下に置いたうえで `settings.json` へ手動で配線してください。手順は [docs/hooks.md](docs/hooks.md) にあります。

### つまみ食い

個別に欲しいものだけコピー:

```bash
cp -r ~/.claude-harness/skills/search-first ~/.claude/skills/
```

### Python 実装付き skill のセットアップ

`llms-txt-writer`, `skill-comply`, `rules-distill`, `skill-stocktake`, `skill-health` は Python 実装を含む。各 skill dir で:

```bash
cd ~/.claude/skills/<skill-name>
uv sync  # or: pip install -e .
```

## origin タグ

各ファイルの frontmatter (YAML または HTML コメント) に `origin` フィールドが付いている:

| origin | 意味 |
|--------|------|
| `shimo4228` | shimo4228 作。この repo の対象 |
| `ECC` | Everything Claude Code 由来。内容は含めない — 名前のみ英語版 README に列挙 |
| `ECC-customized` | ECC 派生 + shimo4228 改良。内容は含めない — 名前のみ英語版 README に列挙 |
| `auto-extracted` | `learn-eval` が自動抽出した learned skill。含めない |

この repo は `origin: shimo4228` のみを機械収集した結果物。外部 origin コンポーネントの名前一覧（内容は非再配布、script 生成）は [README.md の Upstream components 節](README.md#upstream-components-names-only) を参照。

## 関連 repo

- [shimo4228](https://github.com/shimo4228/shimo4228) — 5 実践ライン (AKC / Contemplative Agent / AAP / Authorship Strategy / Attention Not Self) とエコシステムを集約するハブ repo。この repo の clone/view トラフィックは[公開 dashboard](https://shimo4228.github.io/shimo4228/traffic/dashboard/) で観測できる
- [agent-knowledge-cycle](https://github.com/shimo4228/agent-knowledge-cycle) — AKC の概念と DOI 付きリリース (Zenodo: 10.5281/zenodo.19200726)
- [contemplative-agent-rules](https://github.com/shimo4228/contemplative-agent-rules) — Contemplative Constitutional AI の rule 実装
- 個別 skill repo 群 — AKC 各 skill の独立版 (search-first / learn-eval / skill-stocktake / rules-distill / skill-comply / context-sync) + 隣接スキル (llms-txt-writer / daily-research / jsonld-knowledge-graph / writing-ecosystem / when-code-when-llm / signal-first-research / rules-stocktake)

## Contributing

この repo は shimo4228 個人の harness artifact なので、外部からの PR は受け付けない。代わりに:
- Fork してご自由にカスタマイズ
- Issue で質問・提案は歓迎

バグ修正の upstream 反映は `~/.claude/` 側に shimo4228 自身が取り込む。

## License

MIT License. See [LICENSE](LICENSE).

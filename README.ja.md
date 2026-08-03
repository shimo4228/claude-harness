Language: [English](README.md) | 日本語

# claude-harness

shimo4228 が日常的に使っている Claude Code ハーネス (skills / agents / rules) の公開版。

`~/.claude/` 配下から `origin: shimo4228` タグを持つ資産を機械的に集約したもの。ECC 由来 (origin: ECC / ECC-customized) や自動抽出物 (origin: auto-extracted) は含まない。

## 位置付け

- **対象**: Claude Code (CLI + IDE extensions) のユーザー、および agent skill / rule エコシステムを研究する開発者
- **運用方針**: `~/.claude/` が source of truth、この repo は [`scripts/sync-from-local.sh`](scripts/sync-from-local.sh) による一方向エクスポート (origin filter → secret scan → subtree 置換)
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
| [codex-review](skills/codex-review/SKILL.md) | クロスモデルのコードレビュー — 現在の diff に対し OpenAI Codex CLI (別モデルファミリ) の read-only セカンドオピニオンを取り、code-reviewer / security-reviewer と並行して Claude Code review chain に統合 |
| [llms-txt-writer](skills/llms-txt-writer/SKILL.md) | llms.txt / llms-full.txt 等の AI 向けドキュメントを書く。Answer.AI 標準 + GEO/AEO 静的解析 |
| [jsonld-knowledge-graph](skills/jsonld-knowledge-graph/SKILL.md) | `llms.txt` の companion となる JSON-LD ナレッジグラフ (`graph.jsonld`) を設計・出荷。ドメインエンティティと関係を schema.org triple として encode して LLM 引用を最適化 |
| [writing-ecosystem](skills/writing-ecosystem/SKILL.md) | 人間向け執筆・レビューの orchestrator。editor / essay-reviewer / fact-checker の使い分け |
| [write-prompt](skills/write-prompt/SKILL.md) | 軽量モデル設定の prompt-writer agent で簡潔な prompt を生成 |
| [collect-context](skills/collect-context/SKILL.md) | セッション内外のコンテキストを集めて記事執筆用の素材を作る |
| [authorship-strategy](skills/authorship-strategy/SKILL.md) | DOI 登録された idea-rescue 研究 repo 向けの 4 層 framework (Authenticity / Attribution diffusion / Idea-vs-scaffold / Tactics) |
| [release-doi](skills/release-doi/SKILL.md) | DOI 登録された研究 repo のバージョン release を切る (Zenodo concept DOI 意味論、CHANGELOG / tag / asset packaging) |
| [adr-writer](skills/adr-writer/SKILL.md) | 設計判断を連番 ADR として記録 — ディレクトリ検出・採番・index 更新。本文生成は adr-writer agent に委譲 |
| [paper-ecosystem](skills/paper-ecosystem/SKILL.md) | 学術論文の執筆・レビュー orchestrator — paper-writing + 5 reviewer agent の役割境界と Source Fidelity / Vocabulary / Voice / Clarity / Citation 規約の正本 |
| [paper-writing](skills/paper-writing/SKILL.md) | 学術論文の draft 手順 — title / outline / section / abstract / references。claim と cite の 1:1 mapping を強制 |
| [paper-deposit](skills/paper-deposit/SKILL.md) | レビュー済み論文を Zenodo に単独 DOI record として登録、SSRN cross-post と研究 repo への DOI 編入まで |
| [ai-native-preprint-submission](skills/ai-native-preprint-submission/SKILL.md) | deposit 済み論文を AI-native preprint プラットフォーム (aiXiv / AiraXiv) へ投稿 — 人間ゲート付き browser automation または著者委任の API/MCP 投稿 |
| [readme-writer](skills/readme-writer/SKILL.md) | 人間向け README を書く — 決定論的な構造 lint + スコアなしのホリスティック LLM review |
| [ja-to-en-translation](skills/ja-to-en-translation/SKILL.md) | voice 保持の日英翻訳 — term-lock + 2-pass + back-translation QA |
| [substack-publishing](skills/substack-publishing/SKILL.md) | レビュー済み essay の Substack 公開と LLM 発見用 corpus へのミラー |
| [hf-sync](skills/hf-sync/SKILL.md) | graph.jsonld を持つ研究 repo の Hugging Face Datasets ミラー同期 |
| [citation-sync](skills/citation-sync/SKILL.md) | 研究 repo の引用 4 層 (docs / .zenodo.json / graph.jsonld / Wikidata P2860) を監査し下層から同期 |
| [spawn-session](skills/spawn-session/SKILL.md) | Herdr の pane に detached な Claude Code Remote Control セッションを起動し、モバイルアプリの一覧に出す |
| [harness-sync](skills/harness-sync/SKILL.md) | 生きた harness から本 repo への origin filter 付き一方向エクスポート — 収集・secret scan・subtree 置換 |
| [cited-source-mirror-verification](skills/cited-source-mirror-verification/SKILL.md) | access-blocked / digest 由来の数値主張を、durable な引用の前にオープンミラーで検証する guardrail |
| [wiki-harvest](skills/wiki-harvest/SKILL.md) | 研究 repo セッションから Obsidian LLM wiki (wiki/concept/) を read-only で走査し、repo の次アクションを変えうる候補だけを一次出典付き・ランク付き ledger として repo の `.notes/` に抽出 |
| [wiki-query](skills/wiki-query/SKILL.md) | Obsidian LLM wiki (wiki/concept/) への read-only クエリ。`[[ ]]` 出典付きで合成回答 |
| [repo-asset-stocktake](skills/repo-asset-stocktake/SKILL.md) | プロジェクト repo の非コード資産（ツール設定・CI workflow・runbook）の価値劣化を監査 — 消費者が消えた資産を検出し Keep/Update/Retire/Merge 判定 |
| [task-stocktake](skills/task-stocktake/SKILL.md) | repo の pending タスク追跡を単一台帳へ棚卸し・統合 — 台帳の bootstrap、散在タスク行の収集、git log・実コードとの既済照合 |
| [en-to-ja-translation](skills/en-to-ja-translation/SKILL.md) | 英語→日本語の voice 保持翻訳スキル。エッセイ・研究ドキュメント・README・ADR 等の人間向け prose を、著者の声・register・発見調を保ったまま自然な日本語にする。逐語訳でも MT でもなく、term-lock（訳す-by-default／英語保持は明示 |
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
| [adr-writer](agents/adr-writer.md) | ADR 6 セクション本文を入力のみから生成 — context や代替案の invention 禁止 |
| [codemap-writer](agents/codemap-writer.md) | `docs/CODEMAPS/` の生成・refresh — 各 map ~1000 token の token-lean アーキテクチャ文書 |
| [paper-reviewer](agents/paper-reviewer.md) | 学術論文の構造 review — argument flow / section transition / claim sharpness / evidence-claim alignment |
| [source-fidelity-checker](agents/source-fidelity-checker.md) | 引用された一次ソースを直接読み、論文 claim との drift を検出 |
| [vocabulary-consistency-checker](agents/vocabulary-consistency-checker.md) | 導入 term の定義一貫性と sub-classification の明示性を検証 |
| [clarity-reviewer](agents/clarity-reviewer.md) | 初見読者目線の明瞭性 review — 新語予算 / タイトル軸 / メタ語り / 内部文脈依存 |
| [citation-formatter](agents/citation-formatter.md) | In-text citation と reference list の整合・format・DOI / arXiv ID 検証 |
| [readme-reviewer](agents/readme-reviewer.md) | README / repo トップページの厳格レビュアー — LLM 読解フロア / lead 明瞭性 / human hook / 走査性 / 長さ規律 / 視覚効果。readme-writer の companion |
| [readme-clarity-reviewer](agents/readme-clarity-reviewer.md) | README の初見読者目線レビュー — 造語予算 / 内部文脈依存 / 日本語 register（ですます）。readme-reviewer の並列相方 |
| [adr-reviewer](agents/adr-reviewer.md) | ADR の「決定」ではなく「記録」を検査する — Context が検証可能な根拠を持つか、Alternatives が藁人形でないか、Consequences が両面あるか、先行 ADR との override 関係が明示されているか |
| [prompt-forager](agents/prompt-forager.md) | prompt-perturb の、文脈を持たない側。目的の一行だけを受け取り他は意図的に渡さないので、見つかるものが依頼元のセッションに引きずられない |
| [swift-reviewer](agents/swift-reviewer.md) | Swift / SwiftUI レビュー — Swift 6 strict concurrency、値セマンティクス、SwiftUI の状態所有、retain cycle、HIG 準拠 |
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
<!-- END GENERATED: rules-table -->

## 使い方

### 全部入り

```bash
git clone https://github.com/shimo4228/claude-harness.git ~/.claude-harness
# skills / agents / rules を ~/.claude/ にコピー
cp -r ~/.claude-harness/skills/* ~/.claude/skills/
cp -r ~/.claude-harness/agents/* ~/.claude/agents/
cp -r ~/.claude-harness/rules/common/* ~/.claude/rules/common/
```

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

- [shimo4228](https://github.com/shimo4228/shimo4228) — 3 研究ライン (AKC / Contemplative Agent / AAP) とエコシステムを集約するハブ repo
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

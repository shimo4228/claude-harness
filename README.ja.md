Language: [English](README.md) | 日本語

# claude-harness

shimo4228 が日常的に使っている Claude Code ハーネス (skills / agents / rules / hooks) の公開版です。ハーネスとは、著者のマシンで Claude Code の動きを決めている `~/.claude/` 配下のファイル群のことです。skill・subagent・rule・hook を 1 つずつ自分の環境へ持ち帰りたい Claude Code のユーザーと、実際に動いているエージェントのハーネスがどう組まれているかを、各部品の背後にある日付付きの判断ごと調べたい開発者に向けています。

部品のフォルダ（`skills/`、`agents/`、`rules/`、`hooks/`）と判断の記録（`docs/adr/`、`rfcs/`、`docs/plans/`、`docs/evals/`）は、著者の実働環境 `~/.claude/` から [`scripts/sync-from-local.sh`](scripts/sync-from-local.sh) で一方向に書き出したもので、このスクリプトは secret scan をかけたうえで同期のたびにそれらのフォルダを上書きします。skills / agents / rules は origin タグが著者自身のものを示すものだけを公開し（[origin タグ](#origin-タグ)）、hooks は著者がこのマシンの外でも再利用できると判断したものだけを公開しています。ハーネスを扱った記事と関連 repo は [著者のほかの仕事](#著者のほかの仕事) にあります。

## 使い方

Claude Code と `git` が必要です。Python 実装付きの skill には `uv` も要ります。導入に鍵は要りませんが、一部の skill は実行時に外部サービスを呼ぶので、そのサービスのアカウントか API キーが要ります（例: hf-sync は Hugging Face へアップロードし、review-when-watch は Slack へ投稿し、jev-skill-router と review-when-watch は `TYPESAFE_API_KEY` で TypeSafe Jev（閉じた問いに確率で答える判定専用のモデル）を呼びます）。著者自身の道具を前提にする skill もあります。spawn-session はターミナルマルチプレクサの Herdr を必要とし、wiki-query と wiki-harvest は Obsidian の wiki を読みます。必要なものは各 `SKILL.md` に書いてあります。

まず一度 clone し（下の最初のコマンド）、全部入りか、つまみ食いでその clone から `~/.claude/` へコピーします。`cp` は同じ名前のファイルを上書きしますが、既にある同名の skill フォルダのほかのファイルは残ります。先に `~/.claude/` をバックアップし、まっさらに入れ直すなら古いフォルダを消してください。

### 全部入り

```bash
git clone https://github.com/shimo4228/claude-harness.git ~/.claude-harness
# skills / agents / rules を ~/.claude/ にコピー
mkdir -p ~/.claude/skills ~/.claude/agents ~/.claude/rules/common
cp -r ~/.claude-harness/skills/* ~/.claude/skills/
cp -r ~/.claude-harness/agents/* ~/.claude/agents/
cp -r ~/.claude-harness/rules/common/* ~/.claude/rules/common/
```

`~/.claude/rules/common/` にコピーした rule はすべて毎セッション読み込まれ、著者個人の rule（practitioner-identity、contemplative-axioms）も含みます。要らない rule は外してください。

hooks は別扱いです。`~/.claude` 配下に置いたうえで `settings.json` へ手動で配線してください（[docs/hooks.md](docs/hooks.md)、英語）。

### つまみ食い

欲しいものだけをコピーします。どこから始めるか迷ったら、search-first、learn-eval、skill-stocktake、rules-distill、skill-comply、context-sync の 6 つが候補です。この 6 つはエージェントの繰り返しの経験を skill と rule に変える著者のサイクル [Agent Knowledge Cycle (AKC)](https://doi.org/10.5281/zenodo.19200726) を構成します。それぞれ独立 repo としても公開しており、ハーネスを通して読めるようにここにも収録しています。

```bash
cp -r ~/.claude-harness/skills/search-first ~/.claude/skills/
```

### Python skill のセットアップ

`pyproject.toml` を持つ skill のフォルダ（`ls ~/.claude-harness/skills/*/pyproject.toml` で一覧できます）で `uv sync` か `pip install -e .` を実行します。jsonld-knowledge-graph の linter は代わりに `uv run --with pyld` で動かします（その `SKILL.md` 参照）。

## 中身

### Skills

<!-- BEGIN GENERATED: skills-table -->
| Skill | Purpose |
| --- | --- |
| [search-first](skills/search-first/SKILL.md) | 決める前に外を見る — ウェブ・レジストリ・一次ソースを判断時点で検索し、呼び出し側が選べる報告を返却 |
| [learn-eval](skills/learn-eval/SKILL.md) | セッションから再利用可能なパターンを抽出し、品質評価を経て保存先を決める |
| [skill-stocktake](skills/skill-stocktake/SKILL.md) | Skill の品質監査 — Glob インベントリ + 単一コンテキストでの全体評価、Keep/Improve/Update/Retire/Merge 判定 |
| [skill-health](skills/skill-health/SKILL.md) | Skill ライブラリの構造的な不備のスキャン — "missing artifacts"（SKILL.md が参照する script / agent / sibling skill がディスク上に存在しない）を検出。決定論的で、品質・リスク・検証は skill-stocktake / security-scan / skill-comply に委譲 |
| [rules-distill](skills/rules-distill/SKILL.md) | Skill 群から共通原則を抽出し、rule として昇格させる |
| [rules-stocktake](skills/rules-stocktake/SKILL.md) | Rules の品質監査 — residency cost（全行が毎セッションの token 税）モデル、古くなった rule や、ハーネス自身が担うようになって不要になった rule の検査、Keep/Improve/Update/Merge/Demote/Dissolve/Retire 判定。rules-distill の逆方向 |
| [skill-comply](skills/skill-comply/SKILL.md) | Skill / rule / agent の実際の遵守率を計測。3 段階 prompt で行動シーケンスを分類 |
| [context-sync](skills/context-sync/SKILL.md) | プロジェクトのドキュメントを監査・修正。役割重複検出、鮮度チェック、欠損作成 |
| [llms-txt-writer](skills/llms-txt-writer/SKILL.md) | llms.txt / llms-full.txt 等の AI 向けドキュメントを書く。Answer.AI 標準 + GEO/AEO 静的解析 |
| [jsonld-knowledge-graph](skills/jsonld-knowledge-graph/SKILL.md) | `llms.txt` と対になる JSON-LD ナレッジグラフ (`graph.jsonld`) を設計して公開。ドメインのエンティティと関係を schema.org triple として書き表し、LLM に引用されやすくする |
| [collect-context](skills/collect-context/SKILL.md) | セッション内外のコンテキストを集めて記事執筆用の素材を作る |
| [authorship-strategy](skills/authorship-strategy/SKILL.md) | DOI 登録された研究 repo 向けの 4 層 framework (Authenticity / Attribution diffusion / Idea-vs-scaffold / Tactics) |
| [release-doi](skills/release-doi/SKILL.md) | DOI 登録された研究 repo のバージョン release を切る (Zenodo の concept DOI の扱い、CHANGELOG / tag / asset packaging) |
| [adr-writer](skills/adr-writer/SKILL.md) | 設計判断を連番 ADR として記録 — ディレクトリ検出・採番・index 更新。本文は確定した decision packet から主ループが執筆、evidence script と adr-reviewer agent が検査 |
| [readme-writer](skills/readme-writer/SKILL.md) | 人間向け README を書く — 決定論的な構造 lint + スコアなしのホリスティック LLM review |
| [hf-sync](skills/hf-sync/SKILL.md) | graph.jsonld を持つ研究 repo の Hugging Face Datasets ミラー同期 |
| [spawn-session](skills/spawn-session/SKILL.md) | Herdr の pane に detached な Claude Code Remote Control セッションを起動し、モバイルアプリの一覧に出す |
| [harness-sync](skills/harness-sync/SKILL.md) | 生きた harness から本 repo への origin filter 付き一方向エクスポート — 収集・secret scan・subtree 置換 |
| [wiki-harvest](skills/wiki-harvest/SKILL.md) | 研究 repo セッションから Obsidian LLM wiki (wiki/concept/) を read-only で走査し、repo の次アクションを変えうる候補だけを一次出典付き・ランク付き台帳として repo の `.notes/` に抽出 |
| [wiki-query](skills/wiki-query/SKILL.md) | Obsidian LLM wiki (wiki/concept/) への read-only クエリ。`[[ ]]` 出典付きで合成回答 |
| [repo-asset-stocktake](skills/repo-asset-stocktake/SKILL.md) | プロジェクト repo の非コード資産（ツール設定・CI workflow・runbook）の価値劣化を監査 — 消費者が消えた資産を検出し Keep/Update/Retire/Merge 判定 |
| [task-stocktake](skills/task-stocktake/SKILL.md) | repo の pending タスク追跡を単一台帳へ棚卸し・統合 — 台帳の bootstrap、散在タスク行の収集、git log・実コードとの既済照合 |
| [llm-as-judge](skills/llm-as-judge/SKILL.md) | LLM-as-judge 評価器の設計パターン — 証拠としての二値チェック、名前のついた全体判定 1 つ、スコア集計なし |
| [implementation-chain](skills/implementation-chain/SKILL.md) | task 種別（feat / fix / refactor / chore / prototype / writing）を判定し、対応する agent chain を plan に前もって組み込む判断表 — Chain Matrix、レビュアー routing、早期停止条件 |
| [public-comment](skills/public-comment/SKILL.md) | 公開技術スレッドへの返信 — AI slop tell の除去、スレッド接地、投稿前の日本語訳併記による人間 gate |
| [agent-stocktake](skills/agent-stocktake/SKILL.md) | subagent 定義をハイブリッド cost model（description = 毎セッション常駐 / body = 起動時ロード）で監査 — 抑制指示と、ハーネスが既に担うようになった agent を検出する第 3 の stocktake |
| [generation-audit](skills/generation-audit/SKILL.md) | モデル世代交代時に runtime 層（system prompt + tool description）を実セッションから採取し、競合 / 冗長 / ドリフトに分類して各 stocktake に証拠として渡すオーケストレータ |
| [headline-craft](skills/headline-craft/SKILL.md) | 「開かせる一行」の craft — タイトル・tagline・subtitle・SNS 告知文の候補生成と、流入経路 2 軸（検索 / フィード）での評価 |
| [prompt-perturb](skills/prompt-perturb/SKILL.md) | 多様性の注入。文脈をあえて持たない forager agent が外部の創造技法カタログからプロンプトを拾ってくるので、角度がセッション自身の手癖の外から来る |
| [session-judgment-mining](skills/session-judgment-mining/SKILL.md) | 過去のセッション記録から、ユーザーが繰り返し下した判断を発掘し、再出現するものを skill / rule に正本化する |
| [verify-bootstrap](skills/verify-bootstrap/SKILL.md) | repo の機械ゲート（format / lint / type check / security / dependency / test）を立てる、または古びたゲートを棚卸しする。ツール選定は skill に焼き込まず、その時点で調べ直す |
| [x-draft](skills/x-draft/SKILL.md) | リサーチレポートを長文 1 ポストの下書きにする。pull 型で、通知もノルマもなく、投稿したいと思ったときだけ呼ぶ。一次ソースの再確認と陳腐化ゲートを通し、AI tell を落として下書きで止まる（投稿は人間） |
| [task-triage](skills/task-triage/SKILL.md) | タスク台帳を回す loop の 1 周: 開いている全タスクを判定（前提・着手条件・価値）し、ready を新しい build セッションへ dispatch、成果を独立に検収 — merge の言葉は人間が持つ |
| [harness-boundary](skills/harness-boundary/SKILL.md) | mechanism（rule / skill / hook / agent / workflow）を足す前の設計レンズ — 6 層のどこに置くか、モデルに任せられないか、runtime 交換後も残るか。harness を捨てても残るものだけを資産にする |
| [skill-creator](skills/skill-creator/SKILL.md) | skill / agent 定義を書く・書き直す入口 — intent packet、library 全体での境界確認、Fable 向けの書き方、fresh-context の草稿ゲート（Publishable / Fix / Drop、集計なし）、著者通読。upstream の anthropics skill-creator をその場で置換（ADR-0046） |
| [measurement-discipline](skills/measurement-discipline/SKILL.md) | 測定に基づく主張の規律。実験結果で判断する、閾値やガードを決める、観察期間を選ぶ、候補を本番と比べるときに使う |
| [prose-translation](skills/prose-translation/SKILL.md) | エッセイ・記事・README・ADR などの人間向けの文章を、日本語と英語の両方向に、著者の声と出力先の文体を保って訳す |
| [repair-discipline](skills/repair-discipline/SKILL.md) | 修正の前に、今なにが本当かを一次証拠で確かめる規律。バグ、古いタスク、止まる・不安定な処理、他のコードが読む schema や保存形式の変更に使う |
| [rfc-writer](skills/rfc-writer/SKILL.md) | 公開 `rfcs/` 台帳へ 1 エントリを起票する手順（足切り・採番・様式・公開規約・index 行） |
| [review-to-lint](skills/review-to-lint/SKILL.md) | reviewer のチェックリストのうち機械で判定できる項目を決定論 script に移し、reviewer（agent / review skill）には判断の要るチェックだけを残す |
| [jev-skill-router](skills/jev-skill-router/SKILL.md) | prompt に合う skill を TypeSafe Jev に選ばせる UserPromptSubmit hook。shadow 計測が先、inject は精度が出てから |
| [jev-judgment-design](skills/jev-judgment-design/SKILL.md) | LLM の閉じた判定（関係あるか・新しいか・証拠の強さ）を TypeSafe Jev に移す設計。比べる相手を state に入れ、採否は Jev の確率からコードが決め、canary で落としすぎを見る |
| [author-calibrated-eval](skills/author-calibrated-eval/SKILL.md) | LLM が書く読み物を著者の読みを正解にして磨くループ。材料の固定、難所セット、強いモデルの参照稿を混ぜた blind 読み比べ、LLM 判定役は忠実さの足切り専任 |
| [review-when-watch](skills/review-when-watch/SKILL.md) | 毎朝の launchd job。新しいリサーチノートを ADR と RFC の Review-when 条件に TypeSafe Jev で 1 組ずつ照合し、当たりを Slack に送る。model からは呼ばない |
| [mono-figure](skills/mono-figure/SKILL.md) | 記事や README の静的な説明図（線・矢印・数字・ラベル）を mono-color の見た目（紙・インク・書体・余白）で作る。既定は Claude が SVG で描き、必要な platform では PNG に撮る |
<!-- END GENERATED: skills-table -->

### Agents

<!-- BEGIN GENERATED: agents-table -->
| Agent | Purpose |
| --- | --- |
| [prompt-writer](agents/prompt-writer.md) | 軽量モデルで簡潔な prompt を生成。LLM prompt template の作成・書き換え |
| [adr-reviewer](agents/adr-reviewer.md) | ADR の「決定」ではなく「記録」を検査する — Context が検証可能な根拠を持つか、`Review-when` が観測可能な失効条件か、Alternatives が藁人形でないか（「未決 — 再訪条件」付きの対抗案は可）、Consequences が両面あるか、先行 ADR との関係（部分弱化は日付つき注記）が明示されているか |
| [prompt-forager](agents/prompt-forager.md) | prompt-perturb の、文脈を持たない側。目的の一行だけを受け取り他は意図的に渡さないので、見つかるものが依頼元のセッションに引きずられない |
| [swift-reviewer](agents/swift-reviewer.md) | Swift / SwiftUI レビュー — Swift 6 strict concurrency、値セマンティクス、SwiftUI の状態所有、retain cycle、HIG 準拠 |
| [readme-judge](agents/readme-judge.md) | README の fresh-context 判定器。証拠 JSON と README を 1 回読み、固定チェックリストに引用付きで答えて named verdict（Publishable / Fix / Rewrite）を返す |
| [researcher](agents/researcher.md) | search-first の並列 Full で 1 角度を担う調査 worker。web・registry・一次資料を調べ、日付付きの notes 1 本か、plan の research gate を開ける統合 report 1 本を書く |
<!-- END GENERATED: agents-table -->

### Rules

`rules/common/` 配下の rule は毎セッション読み込まれます。多くはこの環境固有の事実・配線・罠で、残りは著者個人の rule と、llm-first-code のような仕事の原則です。手順は skill が、発火のタイミングが要る検査は hook が持ちます。

<!-- BEGIN GENERATED: rules-table -->
| Rule | Purpose |
| --- | --- |
| [agents](rules/common/agents.md) | agent catalog へのポインタ（正本は `agents/*.md` の frontmatter）、Review は実装者と別の agent process で走らせる規則、Herdr 委譲 skill への入口 |
| [akc-cycle](rules/common/akc-cycle.md) | Agent Knowledge Cycle のポインタ版 — 各機構と所有する skill・rule の対応表、足場をいつ外してよいか（Scaffold Dissolution）の判定基準、ADR の扱い（日付つき経緯記録・supersede と日付つき注記・起票の 2 条件） |
| [debugging](rules/common/debugging.md) | Rate limit signal — 外部 platform への大量書き込み中の rate limit 連発は一時的なエラーでなく方針の合図。backoff で押し切らず、書き込みの連続を止めて人間へ報告 |
| [planning](rules/common/planning.md) | Planning の配線 — 既存解がありうるものの前は search-first、実装は判定役のセッションから別の build セッションへ渡すのが既定、chain 種別と reviewer 条件は implementation-chain、Verify の正本は repo の `.claude/verify.sh` |
| [skills](rules/common/skills.md) | skill / agent / rule の origin 語彙（正本の表）、系譜を残す `replaces:` field、skill を書く・大改修する前に skill-creator を読む命令形の配線、文書の書き方（既定は肯定形、禁止は 3 条件を満たすときだけ） |
| [contemplative-axioms](rules/common/contemplative-axioms.md) | Laukkonen et al. (2025) の Contemplative Constitutional AI 原則 (verbatim) |
| [task-tracking](rules/common/task-tracking.md) | Pending task の正本は repo ごとに 1 つ、形は 2 つ — 単一表 `.notes/TASKS.md` か、1 タスク 1 ファイルの公開 store `rfcs/`（`claims.py ready` で問う）。並行セッションの claim / release、レビュー指摘は loop 自身を壊す欠陥だけを、問題を示すファイルと行を引用して起票 |
| [knowledge-staleness](rules/common/knowledge-staleness.md) | LLM 分野の外部知識は 1 週間スケールで陳腐化するという世界観を既定にする — 手法・仕様・相場観を記憶から断言せず検索時点で照合し、根拠に as-of 日付を、推奨に失効条件を付ける |
| [practitioner-identity](rules/common/practitioner-identity.md) | 著者の自己定義 (verbatim) — AI 時代に何が良い考え・良い手段かを探し続ける。DOI は手段の一つで研究者志向ではない。コードは消えるが考えは消えない |
| [llm-first-code](rules/common/llm-first-code.md) | コードを実際の読者 = 次セッションの LLM に最適化する — 可読性でなく検証可能性（型・テスト・golden）を保存し、品質は機械ゲートで執行、人間可読性の予算は README と出力の文面にだけ払う |
| [boundary](rules/common/boundary.md) | 境界の正本 — 人間に渡す操作（公開・課金・外部送信・台帳の起票・permissions / hooks / rules / ADR の無人変更）、確認を待たずにとってよいリスク、止まって報告する条件 |
| [evals](rules/common/evals.md) | Eval の配線 — eval の問いを持ち主へ振り分ける。eval を作る・eval で改善するは `/claude-api build-eval` → `hillclimb`、なじみのない領域では採点方式を決める前に search-first。harness の skill・agent が対象なら runner は `claude -p` |
<!-- END GENERATED: rules-table -->

### Hooks

`hooks/` には、`git commit` の境界で走る PreToolUse hook が 5 本（secret scan、あなたが承認してから走る repo 自身の `.claude/verify.sh`、bandit、`ruff format --check`、レビューを思い出させる通知）と、commit 以外で発火する hook が 2 本あります。どれも `tests/` に bats テストがあります。導入手順、verify hook の承認モデル、各テストが何を固定しているか、公開していないものは [docs/hooks.md](docs/hooks.md)（英語）に、各 hook の説明は llms-full.txt（英語）にあります。

### 設計判断 (ADR) と提案 (RFC)

`docs/adr/` は部品の「なぜ」です。採用・退役・方針転換を、失敗も含めて日付付きの Architecture Decision Record に残しています（[ADR index](docs/adr/README.md)）。`rfcs/` は公開のタスク・提案台帳で、閉じたエントリも理由ごと残します（[ADR-0049](docs/adr/0049-unify-task-ledger-into-public-rfcs.md)、[index](rfcs/README.md)）。`docs/plans/` は承認済みの plan（plan mode の計画）です（[ADR-0085](docs/adr/0085-plans-as-records-in-docs-plans.md)）。`docs/evals/` は ハーネスが自分を測る計器の Eval カードです（[RFC-0030](rfcs/0030-eval-cards-for-ready-instruments.md)、[index](docs/evals/README.md)）。ADR、`rfcs/`、`docs/plans/`、`docs/evals/` は日本語で書いています。それぞれの運用は llms-full.txt（英語）の同名の節にあります。

## origin タグ

skill・agent・rule の各ファイルには、frontmatter か HTML コメントに `origin` タグが付いています。公開しているファイルは著者自身の `shimo4228` で、rule の contemplative-axioms は著者がこのタグで持っている逐語の引用です。Everything Claude Code などの外部由来のコンポーネントは内容を含めず、名前だけを載せます。その一覧は同期スクリプトが英語版 README にだけ生成します（[README.md の Upstream components 節](README.md#upstream-components-names-only)、英語）。表の全体は [llms-full.txt](llms-full.txt)（英語）の Origin tags 節に、タグの語彙の最新情報は [rules/common/skills.md](rules/common/skills.md) にあります。

## 著者のほかの仕事

- **[AIレビューを6系統から1系統へ——「指摘ゼロ」で終われないループの切り方](https://zenn.dev/shimo4228/articles/review-chain-damping)**（[English](https://dev.to/shimo4228/i-cut-my-ai-review-chain-from-6-stages-to-1-breaking-the-loop-that-never-hits-zero-findings-1moi)）: このハーネスが常設のレビューを 6 系統から 1 系統（+条件付き 1 系統）へ縮めた理由と、ADR-0055 の裏付けになった実測が分かります。
- **[AIレビューの指摘をタスクへ送り続けたら、修理が終わらなくなった——4,541行を捨てるまで](https://zenn.dev/shimo4228/articles/ai-review-task-loop)**（[English](https://dev.to/shimo4228/ai-review-kept-creating-work-why-i-deleted-4541-lines-22ec)）: レビューの指摘をタスク台帳へ送り続けると仕事が増え続けた経緯と、著者が採った基準（前提を検証できたか、人間が探索する価値を選んだときだけタスクにする）が分かります。
- **[akc-cycle](https://github.com/shimo4228/akc-cycle)**: [Agent Knowledge Cycle](https://github.com/shimo4228/agent-knowledge-cycle)（その repo に日付付きの設計判断と concept DOI があります）を、1 つの Claude Code プラグインと自己完結版の rules ファイルとして導入できます。この repo の `rules/common/akc-cycle.md` はそのポインタ版です。
- **[harness-scope](https://github.com/shimo4228/harness-scope)**: このようなグローバルなハーネスを、名前付きの profile で repo ごとに on/off する Claude Code Mod です。
- **[harness-pruning](https://github.com/shimo4228/harness-pruning)**: このハーネスから退役させた skill・rule・agent・hook を、それぞれの判断記録とともに日付順に残した記録です。
- **[shimo4228](https://github.com/shimo4228/shimo4228)**: 著者のハブです。5 つの長期プロジェクトと DOI、この repo の clone・閲覧数を記録した[公開 dashboard](https://shimo4228.github.io/shimo4228/traffic/dashboard/) があります。

## Contributing

この repo は shimo4228 個人のハーネスです。Fork してご自由にカスタマイズし、質問・提案は Issue でお寄せください。外部からの PR は受け付けていません。バグ修正は、shimo4228 が `~/.claude/` 側に取り込むことで反映されます。

## License

MIT License です。詳しくは [LICENSE](LICENSE) をご覧ください。

<details>
<summary>ツールと AI アシスタント向けの資料</summary>

claude-harness は、著者 shimo4228 が毎日使っている Claude Code ハーネスを、再利用と調査のために一方向に公開したものです。

存在する理由は、ADR が論じている対象のファイルの隣にあって初めて意味を持つからです。

基本情報: MIT ライセンスです。skills / agents / rules は Markdown、hooks は Bash で、Python の skill は `uv` で動かします（Python 3.11 以上がほとんど）。記録と一部の新しい skill の説明は日本語です。状態: 稼働中で、一方向に同期しています。同期スクリプト（harness-sync skill が走らせます）は `scripts/hooks/` と `tests/` も上書きし、README では部品一覧の表だけを作り直します。README の本文、`docs/hooks.md`、llms ファイル、LICENSE、同期スクリプトは手で保守しています。導入に有料の鍵は要りません。

例: つまみ食いのコマンドで search-first を導入すると、エージェントは決める前に web・レジストリ・一次資料を検索し、呼び出し側が選べる報告を返します。

リンク: [llms.txt](llms.txt) と [llms-full.txt](llms-full.txt)（英語）です。AKC の skill は [Agent Knowledge Cycle](https://github.com/shimo4228/agent-knowledge-cycle)（concept DOI [10.5281/zenodo.19200726](https://doi.org/10.5281/zenodo.19200726)）を実装しています。AKC はこの DOI で引用してください。著者のハブは [shimo4228/shimo4228](https://github.com/shimo4228/shimo4228) です。

</details>

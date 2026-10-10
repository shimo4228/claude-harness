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

この repo には skill（`skills/`）、agent（`agents/`）、rule（`rules/common/`、毎セッション読み込まれます）と、下の hook・設計記録が入っています。skill・agent・rule の一覧と用途は [docs/components.ja.md](docs/components.ja.md) にあります。

### Hooks

`hooks/` には、`git commit` の境界で走る PreToolUse hook が 5 本（secret scan、あなたが承認してから走る repo 自身の `.claude/verify.sh`、bandit、`ruff format --check`、レビューを思い出させる通知）と、commit 以外で発火する hook が 2 本あります。どれも `tests/` に bats テストがあります。導入手順、verify hook の承認モデル、各テストが何を固定しているか、公開していないものは [docs/hooks.md](docs/hooks.md)（英語）に、各 hook の説明は llms-full.txt（英語）にあります。

### 設計判断 (ADR) と提案 (RFC)

`docs/adr/` は部品の「なぜ」です。採用・退役・方針転換を、失敗も含めて日付付きの Architecture Decision Record に残しています（[ADR index](docs/adr/README.md)）。`rfcs/` は公開のタスク・提案台帳で、閉じたエントリも理由ごと残します（[ADR-0049](docs/adr/0049-unify-task-ledger-into-public-rfcs.md)、[index](rfcs/README.md)）。`docs/plans/` は承認済みの plan（plan mode の計画）です（[ADR-0085](docs/adr/0085-plans-as-records-in-docs-plans.md)）。`docs/evals/` は ハーネスが自分を測る計器の Eval カードです（[RFC-0030](rfcs/0030-eval-cards-for-ready-instruments.md)、[index](docs/evals/README.md)）。ADR、`rfcs/`、`docs/plans/`、`docs/evals/` は日本語で書いています。それぞれの運用は llms-full.txt（英語）の同名の節にあります。

## origin タグ

skill・agent・rule の各ファイルには、frontmatter か HTML コメントに `origin` タグが付いています。公開しているファイルは著者自身の `shimo4228` で、rule の contemplative-axioms は著者がこのタグで持っている逐語の引用です。Everything Claude Code などの外部由来のコンポーネントは内容を含めず、名前だけを載せます。その一覧は [docs/components.md の Upstream components 節](docs/components.md#upstream-components-names-only)（英語）にあります。表の全体は [llms-full.txt](llms-full.txt)（英語）の Origin tags 節に、タグの語彙の最新情報は [rules/common/skills.md](rules/common/skills.md) にあります。

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

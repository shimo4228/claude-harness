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

| Skill | Purpose |
|-------|---------|
| [search-first](skills/search-first/SKILL.md) | Research-before-coding workflow。scout agent を呼び出して既存ツールを探索 |
| [signal-first-research](skills/signal-first-research/SKILL.md) | 次の行動を変えうる情報だけを取り込む research intake filter の設計ガイド |
| [learn-eval](skills/learn-eval/SKILL.md) | セッションから再利用可能なパターンを抽出し、品質評価を経て保存先を決める |
| [skill-stocktake](skills/skill-stocktake/SKILL.md) | Skill の品質監査 — Glob インベントリ + 単一コンテキスト holistic 評価、Keep/Improve/Update/Retire/Merge 判定 |
| [rules-distill](skills/rules-distill/SKILL.md) | Skill 群から共通原則を抽出し、rule として昇格させる |
| [skill-comply](skills/skill-comply/SKILL.md) | Skill / rule / agent の実際の遵守率を計測。3 段階 prompt で行動シーケンスを分類 |
| [context-sync](skills/context-sync/SKILL.md) | プロジェクト documentation を監査・修正。役割重複検出、鮮度チェック、欠損作成 |
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
| [readme-writer](skills/readme-writer/SKILL.md) | 人間向け README を書く — 決定論的な構造 lint + スコアなしのホリスティック LLM review |
| [ja-to-en-translation](skills/ja-to-en-translation/SKILL.md) | voice 保持の日英翻訳 — term-lock + 2-pass + back-translation QA |
| [substack-publishing](skills/substack-publishing/SKILL.md) | レビュー済み essay の Substack 公開と LLM 発見用 corpus へのミラー |
| [hf-sync](skills/hf-sync/SKILL.md) | graph.jsonld を持つ研究 repo の Hugging Face Datasets ミラー同期 |
| [wikidata-federation](skills/wikidata-federation/SKILL.md) | 研究者・論文・repo の Wikidata item 作成と ORCID / DOI / graph.jsonld への QID 連邦 |
| [citation-sync](skills/citation-sync/SKILL.md) | 研究 repo の引用 4 層 (docs / .zenodo.json / graph.jsonld / Wikidata P2860) を監査し下層から同期 |
| [when-code-when-llm](skills/when-code-when-llm/SKILL.md) | 決定論的 code vs LLM 処理の判断 framework — 構造/意味軸と false-positive テスト |
| [spawn-session](skills/spawn-session/SKILL.md) | tmux で detached な Claude Code Remote Control セッションを起動し、モバイルアプリの一覧に出す |
| [harness-sync](skills/harness-sync/SKILL.md) | 生きた harness から本 repo への origin filter 付き一方向エクスポート — 収集・secret scan・subtree 置換 |
| [cited-source-mirror-verification](skills/cited-source-mirror-verification/SKILL.md) | access-blocked / digest 由来の数値主張を、durable な引用の前にオープンミラーで検証する guardrail |
| [gap-review](skills/gap-review/SKILL.md) | 継続運用する戦略の「次の一手」候補をランク付き生成 — deployed tactics × catalog × open questions × 最新文献の差分 |
| [wiki-query](skills/wiki-query/SKILL.md) | Obsidian LLM wiki (wiki/concept/) への read-only クエリ。`[[ ]]` 出典付きで合成回答 |

> 最初の 6 つ (search-first, learn-eval, skill-stocktake, rules-distill, skill-comply, context-sync) は [Agent Knowledge Cycle (AKC)](https://zenodo.org/records/19200727) の構成要素。独立 repo として個別公開もしているが、この harness でも丸ごと読めるように重複収録している。

### Agents

| Agent | Purpose |
|-------|---------|
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

### Rules

毎セッション自動ロードされる行動原則 (rule/common/ 配下):

| Rule | Purpose |
|------|---------|
| [agents](rules/common/agents.md) | Agent orchestration 規約。いつどの agent を使うか、並列実行のパターン |
| [akc-cycle](rules/common/akc-cycle.md) | Agent Knowledge Cycle の 6 フェーズ行動規約 (Research / Extract / Curate / Promote / Measure / Maintain) |
| [authorship-strategy](rules/common/authorship-strategy.md) | DOI 登録された idea-rescue 研究 repo で作業する際に authorship-strategy framework を起動するポインタ rule |
| [planning](rules/common/planning.md) | 計画時の必須項目 (What / Why / Alternatives)。Phase 0 外部調査の義務化 |
| [skills](rules/common/skills.md) | Skill origin tracking の仕様と knowledge placement の原則 |
| [contemplative-axioms](rules/common/contemplative-axioms.md) | Laukkonen et al. (2025) の Contemplative Constitutional AI 原則 (verbatim) |

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

`llms-txt-writer`, `skill-comply`, `rules-distill`, `skill-stocktake` は Python 実装を含む。各 skill dir で:

```bash
cd ~/.claude/skills/<skill-name>
uv sync  # or: pip install -e .
```

## origin タグ

各ファイルの frontmatter (YAML または HTML コメント) に `origin` フィールドが付いている:

| origin | 意味 |
|--------|------|
| `shimo4228` | shimo4228 作。この repo の対象 |
| `ECC` | Everything Claude Code 由来。この repo には含めない |
| `ECC-customized` | ECC 派生 + shimo4228 改良。含めない |
| `auto-extracted` | `learn-eval` が自動抽出した learned skill。含めない |

この repo は `origin: shimo4228` のみを機械収集した結果物。

## 関連 repo

- [shimo4228](https://github.com/shimo4228/shimo4228) — 3 研究ライン (AKC / Contemplative Agent / AAP) とエコシステムを集約するハブ repo
- [agent-knowledge-cycle](https://github.com/shimo4228/agent-knowledge-cycle) — AKC の概念と DOI 付きリリース (Zenodo: 10.5281/zenodo.19200726)
- [contemplative-agent-rules](https://github.com/shimo4228/contemplative-agent-rules) — Contemplative Constitutional AI の rule 実装
- 個別 skill repo 群 — AKC 各 skill の独立版 (search-first / learn-eval / skill-stocktake / rules-distill / skill-comply / context-sync) + 隣接スキル (llms-txt-writer / daily-research / jsonld-knowledge-graph / writing-ecosystem / when-code-when-llm / signal-first-research)

## Contributing

この repo は shimo4228 個人の harness artifact なので、外部からの PR は受け付けない。代わりに:
- Fork してご自由にカスタマイズ
- Issue で質問・提案は歓迎

バグ修正の upstream 反映は `~/.claude/` 側に shimo4228 自身が取り込む。

## License

MIT License. See [LICENSE](LICENSE).

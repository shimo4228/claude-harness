Language: [English](README.md) | 日本語

# claude-harness

shimo4228 が日常的に使っている Claude Code ハーネス (skills / agents / rules) の公開版。

`~/.claude/` 配下から `origin: shimo4228` タグを持つ資産を機械的に集約したもの。ECC 由来 (origin: ECC / ECC-customized) や自動抽出物 (origin: auto-extracted) は含まない。

## 位置付け

- **対象**: Claude Code (CLI + IDE extensions) のユーザー、および agent skill / rule エコシステムを研究する開発者
- **運用方針**: `~/.claude/` が source of truth、この repo は artifact として手動で同期。頻度が上がれば収集スクリプトで自動化する
- **ライセンス**: MIT。自由にコピー・改変・再配布可能。fork して自分用にカスタマイズする使い方を歓迎

## 中身

### Skills

| Skill | Purpose |
|-------|---------|
| [search-first](skills/search-first/SKILL.md) | Research-before-coding workflow。scout agent を呼び出して既存ツールを探索 |
| [learn-eval](skills/learn-eval/SKILL.md) | セッションから再利用可能なパターンを抽出し、品質評価を経て保存先を決める |
| [skill-stocktake](skills/skill-stocktake/SKILL.md) | Skill の品質監査。Quick Scan / Full Stocktake モードで並列評価 |
| [rules-distill](skills/rules-distill/SKILL.md) | Skill 群から共通原則を抽出し、rule として昇格させる |
| [skill-comply](skills/skill-comply/SKILL.md) | Skill / rule / agent の実際の遵守率を計測。3 段階 prompt で行動シーケンスを分類 |
| [context-sync](skills/context-sync/SKILL.md) | プロジェクト documentation を監査・修正。役割重複検出、鮮度チェック、欠損作成 |
| [llms-txt-writer](skills/llms-txt-writer/SKILL.md) | llms.txt / llms-full.txt 等の AI 向けドキュメントを書く。Answer.AI 標準 + GEO/AEO 静的解析 |
| [jsonld-knowledge-graph](skills/jsonld-knowledge-graph/SKILL.md) | `llms.txt` の companion となる JSON-LD ナレッジグラフ (`graph.jsonld`) を設計・出荷。ドメインエンティティと関係を schema.org triple として encode して LLM 引用を最適化 |
| [writing-ecosystem](skills/writing-ecosystem/SKILL.md) | 人間向け執筆・レビューの orchestrator。editor / essay-reviewer / fact-checker の使い分け |
| [write-prompt](skills/write-prompt/SKILL.md) | Haiku-powered prompt-writer agent で簡潔な prompt を生成 |
| [collect-context](skills/collect-context/SKILL.md) | セッション内外のコンテキストを集めて記事執筆用の素材を作る |
| [authorship-strategy](skills/authorship-strategy/SKILL.md) | DOI 登録された idea-rescue 研究 repo 向けの 4 層 framework (Authenticity / Attribution diffusion / Idea-vs-scaffold / Tactics) |
| [release-doi](skills/release-doi/SKILL.md) | DOI 登録された研究 repo のバージョン release を切る (Zenodo concept DOI 意味論、CHANGELOG / tag / asset packaging) |

> 最初の 6 つ (search-first, learn-eval, skill-stocktake, rules-distill, skill-comply, context-sync) は [Agent Knowledge Cycle (AKC)](https://zenodo.org/records/19200727) の構成要素。独立 repo として個別公開もしているが、この harness でも丸ごと読めるように重複収録している。

### Agents

| Agent | Purpose |
|-------|---------|
| [scout](agents/scout.md) | Pre-implementation solution discovery。npm / PyPI / MCP registry / GitHub から既存解を検索 |
| [prompt-writer](agents/prompt-writer.md) | 軽量モデルで簡潔な prompt を生成。LLM prompt template の作成・書き換え |
| [editor](agents/editor.md) | Strict technical article editor。コード正確性、AI slop、narrative flow、用語一貫性を厳格にレビュー |
| [essay-reviewer](agents/essay-reviewer.md) | Strict essay editor。社会理論 / 組織論 / デザイン哲学 / 個人ナラティブが混ざる idea 記事を対象 |
| [fact-checker](agents/fact-checker.md) | 事実検証スペシャリスト。記事から検証可能な claim を抽出し web で verify |

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
- `claude-skill-*` 個別 repo 群 — AKC 各 skill の独立版 (search-first / learn-eval / skill-stocktake / rules-distill / skill-comply / context-sync) + 隣接スキル (llms-txt-writer / daily-research / jsonld-knowledge-graph / writing-ecosystem)

## Contributing

この repo は shimo4228 個人の harness artifact なので、外部からの PR は受け付けない。代わりに:
- Fork してご自由にカスタマイズ
- Issue で質問・提案は歓迎

バグ修正の upstream 反映は `~/.claude/` 側に shimo4228 自身が取り込む。

## License

MIT License. See [LICENSE](LICENSE).

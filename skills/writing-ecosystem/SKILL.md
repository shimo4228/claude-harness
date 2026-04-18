---
name: writing-ecosystem
description: 人間向け執筆・レビューエコシステムの orchestrator。記事・エッセイ・ブログポスト・ニュースレター等の **人間 primary** コンテンツを書く / レビューするときに使う。article-writing / editor / essay-reviewer / fact-checker の役割境界と使い分け、AI slop 禁止リスト（日英）、Voice 規約（だ/である × 発見調）、タイトル規約を正本として保持する。AI 向けドキュメント（llms.txt 等）には `llms-txt-writer` を使う。
user-invocable: true
origin: shimo4228
---

# writing-ecosystem — 人間向け執筆・レビューエコシステムの正本

人間読者向けコンテンツ（記事・エッセイ・ブログポスト・ニュースレター等）の執筆とレビューに関わるコンポーネント（skill と agent）の役割境界・使い分け・共通規約をまとめた正本。

> `article-writing` skill の Banned Patterns を **包含する superset**。AI slop / Voice / タイトル規約は本ファイルを正とする。

## Scope

**人間 primary のコンテンツのみ扱う**。AI-facing ドキュメント（`llms.txt` / `llms-full.txt` / FAQ ページ等）には `llms-txt-writer` skill を使う。audience 判定と役割分担は [Audience Separation: Human vs AI](../llms-txt-writer/SKILL.md#audience-separation-human-vs-ai) を参照。

---

## Ecosystem Map

執筆関連コンポーネントは **「Write / Review」 × 「品質 / 論理 / 事実」** のマトリクスで役割分離されている。

| フェーズ | コンポーネント | 軸 | トリガー |
|---------|---------------|-----|----------|
| **Write** | `article-writing` skill | 汎用書き方 | 執筆タスク全般（初稿・構造設計） |
| **Review: 品質** | `editor` agent | tech 記事の構造・コード・AI slop・用語 | tech 記事レビュー時 |
| **Review: 論理** | `essay-reviewer` agent | idea 記事の論理構成・過積載・トーン | idea 記事レビュー時 |
| **Review: 事実** | `fact-checker` agent | 事実主張の Web 検証 | 公開前検証時 |
| **Shared** | `writing-ecosystem` skill | AI slop / Voice / エコシステム map | 執筆 + レビュー時（自動発火） |
| **Overlay** | `<project>/.claude/rules/*.md` | プラットフォーム固有ルール | プロジェクト内作業時のみ |

---

## When to Use What

```
┌─ 初稿作成 ─────────────────────────────────┐
│ article-writing skill                      │
│  → 構造・Voice・基本的な禁止表現           │
└──┬─────────────────────────────────────────┘
   │
   ▼
┌─ 記事の type で分岐 ───────────────────────┐
│                                            │
│  tech 記事（code/tutorial）                │
│   → editor agent                           │
│                                            │
│  idea 記事（essay/opinion）                │
│   → essay-reviewer agent                   │
│                                            │
│  両方含む mixed                            │
│   → 両方並列で実行                         │
│                                            │
└──┬─────────────────────────────────────────┘
   │
   ▼
┌─ 事実チェック（任意、tech/idea 問わず） ───┐
│ fact-checker agent                         │
└────────────────────────────────────────────┘
```

### エージェント並列実行の原則

`editor` と `essay-reviewer` は **観点が異なる** ので、mixed 記事では両方並列実行したほうがカバレッジが高い。`fact-checker` は常に並列で回せる。

---

## AI Slop 禁止リスト

### 判定原則

> その表現を別の記事にそのまま挿入しても意味が通るなら、それは AI slop。

著者の具体的な観察・経験・数値を伴わない汎用表現を使わない。

### 日本語

| 禁止語 | 代替アプローチ |
|-------|-------------|
| 画期的 | 具体的に何が変わったかを書く |
| 革命的 / 革新的 | 従来との差分を数値や事例で示す |
| 素晴らしい | 何がどう良いのかを具体的に書く |
| 驚くべき | 何に驚いたか、なぜ予想外だったかを書く |
| 感動的 | 何が心を動かしたかを描写する |
| シームレス | 実際のユーザー体験を書く |
| パワフルな / ロバストな | 性能指標や具体的な強みを示す |
| レバレッジする / 活用する（漠然と） | 具体的にどう使うかを書く |
| 本質的な問いを投げかける | 問い自体を書く |
| 深い洞察 / 示唆に富む | 洞察の内容を直接書く |
| パラダイムシフト | 何がどう変わったかを書く |
| 重要な示唆を与える | 示唆の内容を具体的に書く |
| 最先端の / 先進的な | 何が新しいかを具体的に書く |

### English

| Banned | Alternative |
|--------|------------|
| powerful tool | describe what it actually does |
| revolutionize / revolutionary | describe the specific change |
| cutting-edge | describe what makes it novel |
| game-changer | describe the concrete impact |
| seamless / seamlessly | describe the actual user experience |
| leverage | use "use" or describe the specific action |
| robust | describe what it handles well |
| effortlessly | describe the actual effort required |
| In today's rapidly evolving landscape | start with the concrete thing |
| Moreover / Furthermore | connect ideas directly without filler transition |
| at the end of the day | cut or rewrite |

*最後の 3 項目は `article-writing` skill の Banned Patterns を包含。本リストは superset。*

---

## Voice & Tone Rules

### 文体: だ/である調 × 発見調

type（tech / idea）にかかわらず、**だ/である調 × 発見調** で統一する。

| 使う表現（発見調） | 避ける表現（宣言調） |
|---------------|-------------------|
| 「〜だった」「〜と気づいた」 | 「〜すべきだ」 |
| 「〜と感じた」「〜に見えた」 | 「〜に違いない」 |
| 「気づいたらそうなっていた」 | 「〜を示している」 |
| 「少なくとも方向としては悪くない」 | 「設計は正しかった」 |

### 未解決の正直さ

解決していない問題は解決したふりをしない。「まだわからない」「今後の課題」と正直に書く。完璧な結論に無理に収束させない。

### 感情語の扱い

- **タイトル**: 禁止（「壊れている」「地獄」「最強」など）
- **本文**: 著者の自然な体験描写なら OK（「正直つらかった」「ここで詰まった」）

---

## Title Conventions

### 目的

読み手がタイトルだけで「この記事が何の概念を提案しているか」を理解できること。

### 基本ルール

- **具体性**: 何についての記事かがタイトルだけでわかる
- **誠実さ**: 記事の内容以上のことを約束しない
- **問いの形**: 「どう〜するか」「なぜ〜か」は知的関心に訴える — 活用 OK

### 禁止事項

- **煽りタイトル**: 「壊れている」「地獄」「最強」などの感情語でクリックを誘わない
- **数字が主役のタイトル**: 「N 選」「N 倍」など。数字の使用自体は禁止しない（「3 つのレイヤーで考える〜」は OK）
- **挑発・断定**: 「〇〇の真価は△△ではない」式の論争誘発をしない
- **過度な省略**: 概念を犠牲にして短くしない

*文字数上限はプラットフォーム依存。プロジェクト overlay で定義する（例: Zenn は 50–60 字）。*

---

## Section Length Guidelines

- 1 つのセクションが記事全体の 30% を超える場合は、分割を検討する（ハードルールではなく目安）
- セクション長は重要度に比例させる。主要な論点に厚く、補足に薄く
- 1 つの記事に独立した論点が 4 つを超える場合は、記事の分割を検討する

---

## How to Extend (Project Overlay)

プラットフォーム固有ルール（Zenn の文字数上限、Qiita のタグ仕様、社内ブログの禁止表現など）は **プロジェクトの rules/ に overlay** として置く:

```
<project>/.claude/rules/<platform>-writing.md
```

例:
- `zenn-content/.claude/rules/zenn-writing.md`
- `company-blog/.claude/rules/corp-writing.md`

overlay 側のファイル冒頭に「本 skill を base とする」旨を明記し、追加ルールだけ書く。base の AI slop / Voice は overlay で再掲しない。

---

## Related

- `article-writing` skill — 執筆時の汎用フレームワーク（本 skill の Banned Patterns を包含）
- `editor` agent — tech 記事レビュー（構造・コード・AI slop・用語）
- `essay-reviewer` agent — idea 記事レビュー（論理構成・過積載・トーン）
- `fact-checker` agent — 事実主張の Web 検証
- `llms-txt-writer` skill — **AI 向けドキュメント（llms.txt / llms-full.txt / FAQ 等）専用**。audience が AI なら本 skill ではなくあちらを使う

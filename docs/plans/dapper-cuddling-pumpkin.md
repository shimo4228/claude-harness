# マルチエージェント・ハーネス共有(rules 正本 = ~/.claude、Claude 無変更)

## Context

複数のコーディングエージェント(モデル: Kimi/GLM/Qwen 等、CLI: Codex/Antigravity)で
`~/.claude/rules/` を共有したい。制約と方針(セッション内で確定済み):

- **正本は `~/.claude/`(rules 14 ファイル + CLAUDE.md)。Claude Code 側は一切変更しない**
- 一方向(他エージェントから書き戻さない)、メンテナンスコスト最小、既製 OSS 優先
- 検証済みの事実: rulesync は global モードで rules 20 ファイルを Codex/OpenCode に配布できず(実測)、
  Qwen 向け生成は読み込まれない孤児 → 同期ツール路線は棄却
- skills 層は ADR-0012(`~/.agents/skills`)で共有済み。hooks/permissions はエージェント固有資産として共有しない

解の構図: **「参照 > 生成 > 同期」**。同期 OSS を導入するのではなく、
(1) モデル試用はルーターで rules 問題自体を消し、(2) Antigravity はディレクトリ発見機構に symlink で接続、
(3) Codex のみ指示文で参照させる。

## Steps

### 1. claude-code-router 導入(モデル切替 — rules 作業ゼロ)

- `npm install -g @musistudio/claude-code-router`(実パッケージ名は導入時に確認。CLI は `ccr`)
- プロバイダ設定: Kimi(`api.moonshot.ai/anthropic`)/ GLM(`api.z.ai/api/anthropic`)/
  Qwen(`dashscope.aliyuncs.com/apps/anthropic`)— **API キーはユーザーが用意**(取得済みのものだけ設定)
- Claude Code がハーネスのままなので rules/skills/hooks は通常どおり決定論的ロード
- 留意: 非公式エンドポイント時は MCP tool search が無効化(`ENABLE_TOOL_SEARCH=true` で再有効化)、
  GLM は `API_TIMEOUT_MS` 延長推奨、Moonshot は temperature 0.6 倍スケール

### 2. Antigravity CLI — symlink 1 本(zero-copy)

- `ln -s ~/.claude/rules ~/.gemini/config/rules`
- 根拠(agy v1.1.2 バイナリ内 docs で確認済み): Global Configuration = `~/.gemini/config/`、
  customization root 直下の `rules/` を自動発見
- **要検証**: `rules/*.md` の glob が `common/` `python/` サブディレクトリを再帰するか。
  しない場合の fallback: フラットな per-file symlink 群を 1 回だけ生成(`ln -s ~/.claude/rules/*/*.md`)
- symlink は Gemini 側に張る(Claude 側無変更の制約を満たす)

### 3. Codex CLI — 指示文方式(何も作らない)

- `~/.codex/AGENTS.md`(60 行、復元済み)の末尾にマーカー付きブロックを追記:
  「セッション開始時に `~/.claude/rules/common/*.md` と `~/.claude/rules/python/*.md` を読み、従うこと」
- 既存内容(ADR-0012 の Codex 固有行を含む)は温存。追記のみ
- 既知の代償(ユーザー了承済み): 読むかは確率的、毎セッション tool call を消費。
  遵守率が実用に足りなければ連結スクリプト方式に後日切替可能

### 4. 検証残骸の掃除(1 件ずつ確認して削除)

- `~/.rulesync/`(import 中間キャッシュ 21 ファイル)
- `~/.qwen/`(孤児の QWEN.md + rules 20 ファイル)
- `~/.config/opencode/`(AGENTS.md 1 枚)
- いずれも 7/18 の rulesync 検証で生成されたもの。git 管理外のため削除前に内容を最終確認

### 5. (オプション)壊れた ~/.claude/AGENTS.md の修理

- 現状は CLAUDE.md の「Claude→Codex」一括置換で壊れたコピー(`~/.Codex/`、「Everything Codex」等)。
  Codex が `~/.claude` を cwd にした時に読む project-doc なので、直すなら
  「このリポジトリの説明 + rules/ を読め」の簡潔な内容に書き直す(Claude Code はこのファイルを読まないため制約違反なし)

## Verification

1. **Router**: `ccr` 経由で GLM(または取得済みキーのプロバイダ)を起動し、応答モデルの確認 +
   rules がロードされていること(Claude Code 側機能なので設定表示で確認可)
2. **Antigravity**: `agy` セッションで rules 固有の内容(例: Immutability 規約、planning の What/Why 要件)を
   質問し、参照できているか確認。サブディレクトリ再帰の可否をここで判定
3. **Codex**: `codex` セッションを任意 repo で開始し、rules を読む挙動(tool call)と遵守を観察。
   数セッション試して遵守率が低ければ連結方式への切替を提案
4. 掃除後: `ls ~/.rulesync ~/.qwen ~/.config/opencode` が not found であること

## 決定記録(実装後に提案)

ADR 候補: 「クロスエージェント rules 共有は 参照 > 生成 > 同期 の優先で、エージェント側アタッチポイント
(router / symlink / 指示文)を使う。同期ツール(rulesync 等)は不採用」
— 意外性・トレードオフあり。可逆性は高いので ADR テスト 2/3。ユーザーに要否を確認する。

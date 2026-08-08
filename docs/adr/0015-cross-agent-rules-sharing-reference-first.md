# ADR-0015: クロスエージェント rules 共有は「参照 > 生成 > 同期」— エージェント側アタッチポイント方式

## Status

accepted

## Date

2026-07-18

## Context

`~/.claude/rules/`（common/ 14 ファイル + python/ 5 ファイル）は行動原則の正本であり、Claude Code の全セッションに毎回自動ロードされる。skills 層は [ADR-0012](./0012-cross-tool-skill-sharing-via-agents-skills.md) で `~/.agents/skills` を介して Codex CLI・Antigravity CLI 等の他ツールと既に共有済みだが、rules 層は未着手だった。hooks / permissions はエージェント固有の実行環境に強く依存する資産であり、共有対象から外している。

この rules 層を、Claude Code 以外のエージェント — Codex CLI、Antigravity CLI、および claude-code-router 経由で試す Kimi / GLM / Qwen 等の他モデル — と共有したい、という要求が起点。

共有方式には以下 3 つの制約がある。

1. **Claude Code 側（`~/.claude`）は一切変更しない**。`CLAUDE.md` の symlink 化のような、正本側に手を入れる方式は不可。
2. **一方向共有**。他エージェント側から `~/.claude` への書き戻しは想定しない。
3. **メンテナンスコスト最小、既製 OSS 優先**。自前の同期スクリプトを新設する前に、既存ツールで賄えないかを検証する。

## Decision

「参照 > 生成 > 同期」を優先原則として採用する。`~/.claude` 側には共有用の仕掛け（symlink・frontmatter 付与・生成物）を一切置かず、各エージェント側が既に持つアタッチポイントから `~/.claude/rules` を参照させる。

1. **他モデル試用（Kimi / GLM / Qwen）は claude-code-router を使う**。Claude Code ハーネスそのものを維持したままモデルだけ差し替えるため、rules 共有問題自体が発生しない。
2. **Codex CLI** は `~/.codex/AGENTS.md` 末尾にマーカーブロック（`<!-- BEGIN shared-rules -->`）を追加し、「`~/.claude/rules/common/*.md`（Python 案件なら `python/*.md` も）を読んで従え」と指示する。
3. **Antigravity CLI** は `~/.gemini/config/rules/shared-claude-rules.md` に同じ指示を置く。Antigravity の仕様上 frontmatter に `trigger: always_on` が必須なため、この指示ファイル自体には frontmatter を付与する（`~/.claude/rules` 側のファイルには一切手を入れない）。

## Alternatives Considered

### rulesync（同期ツール）

最有力候補として実測したが棄却した。global モードでは non-root の rules 20 ファイルが「ignoring them」として Codex / OpenCode に配布されず、root の `CLAUDE.md` 相当のみしか渡らない。Qwen 向けに生成される `~/.qwen/rules/` は Qwen 側に自動読み込み機構が無く孤児化する。さらに `--output-roots` が global モードで無視され実ホームに直接書き込む事故挙動を確認した（検証中に `~/.codex/AGENTS.md` を上書きし、セッションログから復元する事態になった）。

### Ruler / agent-rules-sync

正本を自ツールのディレクトリへ移すことを要求する、または rules フォルダ構造をそのまま扱えないため棄却。前者は制約 1（`~/.claude` 側を変更しない）に抵触する。

### symlink / @import による zero-copy 参照

Antigravity で実測棄却。rules ファイルは frontmatter（`trigger`）必須で、symlink・実ファイルのいずれであっても frontmatter が無ければ無視される。rules 内での `@import` 構文も展開されない。`~/.claude/rules` 側に frontmatter を足すことは制約 1 違反になるため採用できない。

### 連結スクリプト生成（rules を単一 AGENTS.md に焼き込む）

決定論的に配布できる利点はあるが、rules 編集のたびに再生成の運用が必要になる。今回選んだ指示文方式（アタッチポイントから読ませる）の遵守率が実用に足りないと判明した場合の、将来の切替先として保留する。

## Consequences

### Positive

- 同期・生成・コピーがゼロになる。rules を編集すれば次セッションから全エージェントに即反映され、drift が構造的に起きない。
- エージェント追加は指示ファイル 1 枚（約 10 行）を置くだけで完了する。
- 検証済み: Codex・Antigravity の実セッションで、rules 固有の内容（`planning.md` の What / Why / Alternatives）を正しく参照して回答することを確認した。

### Negative

- Codex・Antigravity での rules ロードは確率的（指示に従って読むかどうかはモデル次第）。決定論的注入が保証されるのは Claude Code のみ。
- 毎セッション、rules 読み込みの tool call とトークンを消費する（Codex で実測 約 29k トークン）。

### Neutral / Follow-ups

- skills 層の共有は [ADR-0012](./0012-cross-tool-skill-sharing-via-agents-skills.md) が正本、本 ADR は rules 層のみを扱う。両者は独立した ADR として残す。
- 連結スクリプト生成（Alternatives の 4 番目）は、指示文方式の遵守率が不十分と判明した場合の切替候補として保留する。

## Related

- [ADR-0012](./0012-cross-tool-skill-sharing-via-agents-skills.md): skills 層のクロスツール共有（`~/.agents/skills`）— 本 ADR の rules 版に相当する前例
- [ADR-0008](./0008-ecc-local-only-management.md): ローカル一本化方針 — 外部同期ツールより手元管理を優先する根拠

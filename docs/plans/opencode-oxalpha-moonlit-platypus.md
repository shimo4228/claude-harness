# opencode セットアップ + ハーネス共有（Ox Alpha 試用）

## Context

Ox Alpha（2026-08-20 公開、1M context、期間限定無料の stealth model。匿名の第三者が運用）を
opencode で試したい。opencode は未インストール。

同時に、`~/.claude` ハーネスを opencode からも使えるようにする。既存のクロスエージェント共有は
[ADR-0012](../adr/0012-cross-tool-skill-sharing-via-agents-skills.md)（skills 層）と
[ADR-0015](../adr/0015-cross-agent-rules-sharing-reference-first.md)（rules 層、Codex CLI /
Antigravity CLI の 2 ツール）で構築済み。opencode は 3 ツール目になる。

調査で判明した「既に効くもの / 穴が空くもの」:

| 層 | opencode での状態 | 対応 |
|---|---|---|
| skills | `~/.claude/skills/*/SKILL.md` と `~/.agents/skills/*/SKILL.md` を native に探索（[docs](https://opencode.ai/docs/skills/)） | 不要（install した瞬間に効く） |
| CLAUDE.md | `~/.claude/CLAUDE.md` を fallback として自動読み込み（[docs](https://opencode.ai/docs/rules/)） | 不要 |
| **rules/common/*.md** | **到達しない。** `CLAUDE.md` に `@` import は無く通常の markdown リンクのみ（`CLAUDE.md:8,16`）。rules をロードするのは Claude Code 固有の機構 | **本 plan の主対象** |
| hooks / permissions | — | 共有しない（ADR-0015 の境界を踏襲） |

rules 層で opencode は他 2 ツールに無い選択肢を持つ: config の `instructions` が絶対パス・`~` 展開・
glob を受ける（[docs](https://opencode.ai/docs/config/)）。Codex / Antigravity の指示文方式
（読むかはモデル次第、実測 ~29k トークン）と違い、**決定論的に注入できる**。

## 決定事項（ユーザー確認済み）

- 経路: **OpenCode Zen**（`Ox Alpha Free` = Zen 表記 `x-preview-f-free`。zero-retention を明記）
- 既定モデルに**固定しない** — 期間限定 stealth model を config に焼くと失効時に全セッションが壊れる
- rules 注入: **instructions glob + AGENTS.md 併用**
- 記録: **ADR-0015 に追記 + memory 更新**

## 手順

### 1. install

```bash
brew install anomalyco/tap/opencode
opencode --version
```

docs は「最新版は tap を推奨」。npm / bun global でなく brew に寄せる（他ツールと同じ管理面）。

### 2. rules 層の配線

**`~/.config/opencode/opencode.json`**（新規）:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["~/.claude/rules/common/*.md"]
}
```

**`~/.config/opencode/AGENTS.md`**（新規）— glob で表現できない 2 点だけを指示文で持つ。
`common/*.md` の内容は instructions が入れるので**重複させない**（二重定義は必ず drift する）。
マーカーは Codex の `~/.codex/AGENTS.md` と同じ形式に揃える:

```markdown
<!-- BEGIN shared-rules (managed by claude-harness; do not edit inside markers) -->
## Shared Rules（正本: ~/.claude/rules）

`~/.claude/rules/common/*.md` は opencode.json の `instructions` で自動注入済み。追加で:

- Python を扱うタスクでは `~/.claude/rules/python/*.md` も読む
- `~/.claude/` 配下は Claude Code ハーネスの正本。一方向参照であり、編集・削除してはならない
<!-- END shared-rules -->
```

`~/.claude` 側は**一切変更しない**（ADR-0015 制約 1）。

### 3. Zen 接続（ユーザー操作）

TUI 内の対話なのでこちらからは駆動できない。ユーザーが実行:

```
opencode          # scratch ディレクトリで起動
/connect          # → OpenCode Zen を選択
                  # → opencode.ai/auth でサインイン、billing 登録、API key を取得して貼る
/models           # → Ox Alpha Free を選択
```

Ox Alpha 自体は $0 だが Zen は billing 情報の登録を要求する（pay-as-you-go、他モデルは課金）。

### 4. 検証

```bash
opencode models | grep -i -E 'ox|alpha'    # 実際の model id を実測（provider prefix は未確認）
```

TUI で以下を確認:

1. **rules が入っているか** — rules 固有の内容を聞く。例:「外部 platform への大量書き込みで
   rate limit が連発したらどうする？」→ `debugging.md` の「transient error でなく policy signal
   として burst を止め、人間へ報告」「2026-07-16 にアカウント無期限 block」を答えられれば注入成功
2. **skills が見えるか** — skill 一覧に `search-first` / `implementation-chain` 等が出るか
3. **skills が二重列挙されないか** — `~/.claude/skills` と `~/.agents/skills` は同一実体を指す
   symlink で、重複時の precedence は未文書。二重に出た場合は opencode 側の permission /
   設定で片方を抑えられるか調べる（`~/.agents/skills` は Codex が使うので削除しない）
4. Ox Alpha で簡単なコーディングタスクを 1 本回す（scratch ディレクトリ）

作業ディレクトリはスクラッチ:
`/private/tmp/claude-501/-Users-<user>--claude/eb381777-1e9e-47c6-ad59-38a63d407972/scratchpad/opencode-trial`
— `/init` が `AGENTS.md` を書くので既存 repo では起動しない。

### 5. 記録

- **`docs/adr/0015-cross-agent-rules-sharing-reference-first.md`** — 日付つき追記:
  - Decision に 4 番目として opencode を追加（`~/.config/opencode/opencode.json` の `instructions`
    + `AGENTS.md` マーカーブロック）
  - Consequences / Negative の「rules ロードは確率的」に注記: opencode は `instructions` が
    決定論的に注入するため、この Negative は Codex / Antigravity のみに残る
  - skills 層は ADR-0012 の symlink に加え opencode が `~/.claude/skills` を直接探索する旨を
    Neutral に 1 行
- **`memory/reference_cross_agent_rules_sharing.md`** — opencode 行を追加（アタッチポイントと
  「決定論的注入が可能」の実測）
- ADR 変更は skill: `harness-sync` で公開 repo へ同期。`~/.config/opencode/` は `~/.claude` 外
  なので同期対象外

## 注意

- **stealth model の秘匿性** — Ox Alpha は匿名の第三者が運用。Zen は zero-retention を明記するが
  [OpenRouter 側の同モデル](https://openrouter.ai/stealth/ox-alpha)は「provider がプロンプトと出力を
  保持する（学習には使わない）」と条件が異なる。運用主体が名乗っていない以上、機密を含む repo では
  使わない
- **失効前提** — 期間限定無料。config に焼かない判断の根拠。数週間後に消えている可能性がある
- opencode は `~/.claude/CLAUDE.md` も自動で読むため、harness 以外の repo でも harness 向けの
  記述が文脈に入る。Codex と同じ既存挙動で、実害は無い

## Sources

- [opencode Providers](https://opencode.ai/docs/providers/) / [Config](https://opencode.ai/docs/config/) / [Rules](https://opencode.ai/docs/rules/) / [Skills](https://opencode.ai/docs/skills/) / [Zen](https://opencode.ai/docs/zen/)
- [Ox Alpha on OpenRouter](https://openrouter.ai/stealth/ox-alpha)

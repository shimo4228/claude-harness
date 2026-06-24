<!-- origin: shimo4228 -->
# Skill Origin Tracking

すべてのスキルファイルには出自（origin）メタデータを付与する。
スキルの管理・棚卸し・アップデート判断に使う。

## Origin 値

| origin | 意味 |
|--------|------|
| `shimo4228` | shimo4228 が作成 (旧 `original`) |
| `ECC` | ECC から導入 (未改変) |
| `ECC-customized` | ECC 由来で shimo4228 がカスタマイズ |
| `{origin}-customized` | 任意の外部 origin 由来で shimo4228 が内容を編集（例: `ECC-customized`, `oh-my-agent-check-customized`）。base 名は上流値を保持 |
| `{org/repo}` | 特定外部リポジトリから導入 |
| `auto-extracted` | learn-eval が自動抽出 |
| `skill-create` | skill-create が git 履歴から生成 |

## 記法

### YAML frontmatter がある場合

```yaml
---
name: skill-name
description: ...
origin: shimo4228
---
```

### YAML frontmatter がない場合

```markdown
<!-- origin: shimo4228 -->
# Skill Title
```

## ルール

- **新規スキル作成時**: 必ず origin を付与する
- **外部スキル導入時**: 導入元のリポジトリ URL またはプロジェクト名を記録する
- **auto-extracted**: learn-eval が生成する learned/ スキルに自動付与する
- **外部 origin 由来スキルの内容を編集したら**: origin に `-customized` サフィックスを付す（`ECC`→`ECC-customized`、`oh-my-agent-check`→`oh-my-agent-check-customized`、`{org/repo}`→`{org/repo}-customized`）。参照の repoint・本文修正を含む。**frontmatter の name 修正のみは対象外**。**自作 origin（`shimo4228` / `auto-extracted` / `skill-create`）は対象外** — 上流ベースラインを持たないため customized 概念が不要。目的は「無改変の外部資産から乖離したか」を origin で表し、ECC/外部のアップデート取り込み時の diff 判断を可能にすること
- **棚卸し時**: origin を基準に、アップデート確認（ECC/外部）や削除判断（不要な auto-extracted）を行う

## Skills as Canonical（commands/ は使わない）

スキル定義は `skills/<name>.md` または `skills/<name>/SKILL.md` を**正本**とする。
`commands/` ディレクトリは使用しない（2026-04-07 廃止）。

### Slash 呼び出し

`/skill-name` でのスラッシュ呼び出しは、skill 側 frontmatter に `user-invocable: true` を付与すれば機能する:

```yaml
---
name: skill-name
description: ...
user-invocable: true
origin: shimo4228
---
```

### Runtime 実行コマンドの記述

スキルが外部スクリプトを呼ぶ場合、実行コマンドは SKILL.md 本文に直接記述する。
別ファイル（commands/ シム等）に分離してはならない。

```markdown
## Execution

uv run python -m scripts.run $ARGUMENTS
```

### 二重管理の発見時

過去の遺物として skill と command の両方が見つかったら:
1. skill 側に内容を集約
2. command 側を削除
3. runtime script が command パスを参照していたら script を更新

## Knowledge Placement

新しい知識を保存する際は、既存スキルへの追記を新規ファイル作成より優先する:
1. 既存スキルがそのドメインをカバーしている → 追記する
2. 独立スキルとして十分な量がある（3+ ルールまたはワークフロー） → 新規スキル
3. それ以外 → MEMORY.md（1-2行）

既存スキルには確立された発見経路がある。新規ファイルは発見されないリスクがある。

## Skill Portability（内容ガイドライン）

スキルは複数の文脈で再利用されることを前提とする。作成時に以下を守る。

- **本文は汎用的に書く**: パターン・決定・ワークフローを、誰でも自分の状況に当てはめられる形で記述する
- **個人プロジェクト URL を本文に埋め込まない**: 自分の canonical implementation、個人 repo、特定プロジェクト内のパスへの link は、skill を一人のユーザの filesystem / 一つのプロジェクトのライフサイクルに縛るため、本文に入れない
- **具体例・origin story の置き場所**:
  - 抽象的 worked example（仮想シナリオ） → skill 本文内 OK
  - 個人プロジェクト参照・origin story・canonical implementation → `inspiration.md`、ADR Notes、memory、または同一 repo 内の "Related Projects" ファイルへ
  - ユーザ固有の設定 → skill parameter / 環境変数。本文にハードコードしない
- **自プロジェクト内リンクは許容**: skill が置かれている同一 repo 内の README / docs / config template への相対リンクは、skill を動作させるのに必要な文脈なので本文に入れてよい
- **Portability test**: 他人が install して、著者の個人文脈を一切知らずに使えるか？「この skill を理解するには `claude-skill-foo` を読む必要がある」状態なら、skill が原則違反している

この rule は cycle skill（外部 repo）と design-pattern skill（in-repo `docs/skills/` 等）の両方に適用する。Origin Tracking は *誰が作ったか* を記録するが、Portability は *誰が使えるか* を決める。

## Skill Repo Packaging（subagent 同梱と命名）

skill repo を GitHub 公開する際、その skill が呼ぶ **subagent も同梱**する。同梱しないと installer が agent を別途探す羽目になり、canonical rules を agent が SKILL.md から参照する orchestrator skill は両方入れるまで壊れる。

### 非対称（命名・compatibility の根拠）

- **skill（SKILL.md）= オープンな cross-tool 標準**（Agent Skills / agentskills.io）。同じ skill が Codex / Gemini CLI / Cursor 等でも動く。
- **subagent（`agents/*.md`）= Claude Code 固有**（標準は subagent を扱わない）。
- → **agent を同梱する repo は Claude 固有**。repo 名は `claude-skill-` prefix を維持し `compatibility` frontmatter に Claude Code 向けと明記する。**pure-skill repo は cross-tool** なので prefix を外す（`<owner>/<skill-name>`）。awesome-list 掲載は `owner/skill-name` で並び repo prefix を見ないので、prefix は掲載可否に影響しない（命名は意味の正確さで決める）。

### レイアウトと installer

```
repo/
├── install.sh              # skills/* → ~/.claude/skills/、agents/*.md → ~/.claude/agents/
├── skills/<name>/SKILL.md
└── agents/<agent>.md       # top-level フラット（~/.claude/agents/ の peer）。nest しない
```

`install.sh` は **冪等**にする: 同一なら skip、異なれば `*.bak-<ts>` に退避してから上書き（`--force` / `--dry-run`）。全 repo で byte-identical に保つ（script 実体は各 repo に vendor、この rule では原則のみ）。README install 節は Option A（`./install.sh`）/ Option B（手動 `cp`）/ SkillsMP の 3 つを書く。

### SkillsMP の caveat

`/skills add <owner/repo>` は **`skills/` のみ install し `agents/` は入れない**。README に必ず注記する: SkillsMP 利用者は `cp agents/*.md ~/.claude/agents/`（または `install.sh`）を実行する。さもないと orchestrator が委譲先 agent を持たない。

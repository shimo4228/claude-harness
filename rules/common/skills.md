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

## Skill Repo Packaging

skill repo の GitHub 公開手順（命名規約 `claude-skill-` prefix の要否、subagent 同梱、
install.sh、SkillsMP caveat）の正本は `harness-sync` skill の **Skill repo packaging**
セクション（2026-07-03 rules-stocktake 監査で移動 — repo 公開時にしか使わない詳細は
常駐 rule でなく公開 workflow を持つ skill 側に置く）。

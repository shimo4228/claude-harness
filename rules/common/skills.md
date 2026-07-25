<!-- origin: shimo4228 -->
# Skill Origin Tracking

すべてのスキルファイルには出自（origin）メタデータを付与する。ECC / 外部のアップデート
取り込み時に「無改変の外部資産から乖離したか」を diff 判断するための機構。

| origin | 意味 |
|--------|------|
| `shimo4228` | shimo4228 が作成 |
| `ECC` | ECC から導入 (未改変) |
| `{org/repo}` | 特定外部リポジトリから導入 |
| `auto-extracted` | learn-eval が自動抽出 |
| `skill-create` | skill-create が git 履歴から生成 |
| `{origin}-customized` | 外部 origin 由来で内容を編集した（`ECC-customized` 等）。base 名は上流値を保持 |

記法: YAML frontmatter があれば `origin:` フィールド、無ければ先頭に `<!-- origin: ... -->`。

**`-customized` を付す条件**: 参照の repoint・本文修正を含む内容編集をしたとき。
frontmatter の `name` 修正のみは対象外。自作 origin（`shimo4228` / `auto-extracted` /
`skill-create`）は上流ベースラインを持たないため対象外。

## Skills as Canonical（commands/ は使わない）

スキル定義は `skills/<name>.md` または `skills/<name>/SKILL.md` を**正本**とする。
`commands/` ディレクトリは使用しない（2026-04-07 廃止）。

- `/skill-name` のスラッシュ呼び出しは frontmatter に `user-invocable: true` を付ければ機能する
- 外部スクリプトの実行コマンドは SKILL.md 本文に直接書く（別ファイルのシムに分離しない）
- skill と command の両方が見つかったら skill に集約 → command 削除 → 参照元 script を更新

## Knowledge Placement

新しい知識は既存スキルへの追記を新規ファイル作成より優先する（既存スキルには確立された
発見経路があり、新規ファイルは発見されないリスクがある）:

1. 既存スキルがそのドメインをカバーしている → 追記する
2. 独立スキルとして十分な量がある（3+ ルールまたはワークフロー） → 新規スキル
3. それ以外 → MEMORY.md（1-2行）

skill を**書く / 公開する**ときの規約（Portability test、repo packaging）は
skill: `skill-creator` / `harness-sync` が正本。

<!-- origin: shimo4228 -->
<!-- rationale: ADR-0001 + ADR-0035 — 外部更新との diff に必要な origin schema と探索パスだけ常駐 -->
<!-- review-when: origin 管理または skill discovery path を変えた時 -->
# Skill Origin Tracking

skill / agent / rule には `origin` を付ける。YAML frontmatter が無い文書は先頭の
`<!-- origin: ... -->` を使う。

| origin | 意味 |
|---|---|
| `shimo4228` | 自作 |
| `ECC` | ECC 未改変 |
| `{org/repo}` | 外部 repo |
| `community` | 出所を特定しない外部導入 |
| `auto-extracted` | learn-eval 出力 |
| `{origin}-customized` | 外部由来を内容編集 |

skill の正本は `skills/<name>/SKILL.md`。`commands/` は使わない。配置・作成・公開手順は
skills: `skill-creator` / `harness-sync` が持つ。

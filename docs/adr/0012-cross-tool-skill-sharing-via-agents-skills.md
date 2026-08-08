# ADR-0012: クロスツールのスキル共有を ~/.agents/skills 経由に一本化

## Status

accepted

## Date

2026-06-28

## Context

ユーザーは Claude Code に加えて OpenAI の Codex CLI も使用する。`~/.claude/skills/` を唯一の母体 (canonical source) に保ったまま、Codex からも Claude スキルをゼロメンテで使いたい、という要望があった。管理コストを 0 にする — つまり新スキルを追加しても Codex 側で追加操作が不要 — という制約が前提となる。

2026-06-28 の調査で、同日中に 2 本の橋が二重に架かっていたことが判明した。① ディレクトリ symlink `~/.agents/skills -> ~/.claude/skills/`（07:02 作成）。② per-skill symlink 51 本 `~/.codex/skills/<name> -> ~/.claude/skills/<name>`（07:08 作成）。どちらもドリフトがなく、2 本の橋が並走している状態だった。

Codex 公式ドキュメント（`developers.openai.com/codex/skills`）は user-level のスキル探索パスを `$HOME/.agents/skills` と明記している。一方 `~/.codex/skills/` は公式探索パスではなく、Codex 自前の `.system/` スキルと `skill-installer` が GitHub からコピーする先に過ぎない。Codex はスキル変更を自動検出する仕様であるため、① のディレクトリ symlink 1 本で現在・将来すべての Claude スキルを Codex がゼロメンテで発見できる。`~/.claude/skills/<name>/` を作るだけで `~/.agents/skills` 配下に自動で現れることは end-to-end で検証済みである。

② の per-skill symlink 51 本は冗長であり、ハーネス唯一のメンテ負債だった。新スキルを追加するたびに手動で `ln -s` が必要で、削除したスキルは dangling link として蓄積する。2026-06-28 に全 51 本を削除し（復元用スナップショットを `~/.claude/plans/codex-skills-symlink-snapshot.txt` に保存）、`~/.codex/skills/.system/` のみ保持した。安全性の確認として、Codex hook `~/.codex/hooks/log-skill-usage.sh` はスキル使用を `*/.claude/skills/*.md` という canonical パスでログに記録しており、両橋ともこのパスに解決されるため ② を削除してもログ集計は壊れない。

## Decision

以下の 3 点を適用する。

1. **`~/.claude/skills/` をスキルの唯一の母体 (canonical source of truth) とする**。Codex を含む他ツールへのスキル共有は、この母体から派生させる形で行い、母体の二重化は行わない。

2. **クロスツール共有には Agent Skills 標準のディレクトリ symlink `~/.agents/skills -> ~/.claude/skills/` 1 本のみを使う**。この 1 本で現在・将来の全スキルが Codex に自動的に露出する。Codex 自前スキル（`imagegen`, `openai-docs`, `plugin-creator`, `skill-creator`, `skill-installer`）は `~/.codex/skills/.system/` にローカル保持し、本 symlink の対象外とする。

3. **`~/.codex/skills/` 直下への per-skill symlink を再生成しない**。将来のセッションが per-skill symlink を追加した場合、ディレクトリ symlink 1 本に剪定して元に戻す。

## Alternatives Considered

### (a) ~/.codex/skills/ 配下の per-skill symlink（削除した ② 方式）

`~/.agents/skills` が存在する状態では完全に冗長。新スキルを追加するたびに手動 `ln -s` が必要、削除スキルは dangling link として蓄積、Codex でのスキル二重列挙のリスクもある。管理コスト 0 という要件を満たさないため不採用。

### (b) sync スクリプト + hook で両橋を自動維持（belt-and-suspenders）

スクリプトと hook の管理対象が増えるだけで、将来スキルを自動カバーするディレクトリ symlink 単体に対する利点がない。複雑性を追加せず同等の保証が得られる単一 symlink を優先するため不採用。

### (c) skill-installer で GitHub repo からスキルを ~/.codex/skills/ にコピーする

母体を `~/.claude/skills/` と `~/.codex/skills/` の 2 箇所に分散させ、ドリフトを再導入することになる。canonical source of truth を単一に保つという前提と矛盾するため不採用。

## Consequences

### Positive

- 新スキルの追加は `~/.claude/skills/<name>/` を作る単一アクションで完結し、Codex への反映は自動 — 管理コスト 0
- per-skill symlink 51 本のメンテ負債が消滅し、dangling link の蓄積リスクがなくなる
- Agent Skills 標準パス（`$HOME/.agents/skills`）に従っているため、Codex 以外の Agent Skills 準拠ツールが追加された際も同じ symlink で対応可能

### Negative

- `~/.claude/skills/` の内容が丸ごと Codex に露出する。Claude subagent への委譲を前提とするスキル（`spawn-session`, `context-sync`, `update-codemaps`, `adr-writer` 等）も Codex のスキル一覧に表示されるが、Codex には対応 subagent が存在しないため同一には機能しない可能性がある。Codex を壊すことはなく、使わなければ無害。per-skill フィルタリングは管理コストを増やしゼロコスト方針に反するため実施しない
- Claude の `rules/` および `CLAUDE.md` は本 symlink の対象外であり Codex に自動移植されない。ユーザーは `~/.codex/AGENTS.md` と `~/.codex/rules/` を別途整備済みであり、本 ADR はスキルのみを対象とする

### Neutral / Follow-ups

- ② の削除スナップショットは `~/.claude/plans/codex-skills-symlink-snapshot.txt` から完全復元可能
- `~/.codex/skills/.system/` の Codex 自前スキルは本 ADR の管理対象外として保持。将来 Codex が公式探索パスを変更した場合は再評価する

## Related

- [ADR-0001](./0001-ecc-skill-management-policies.md): Origin tracking — 新規 symlink 追加でも既存 skill の origin は変わらない
- [ADR-0008](./0008-ecc-local-only-management.md): ECC ローカル管理一本化 — `~/.claude/skills/` canonical 化の前提

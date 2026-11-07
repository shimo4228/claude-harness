# ADR-0020: security-scan を退役し risk 面を claude-security プラグインへ委譲

## Status

accepted

## Date

2026-07-26

## Context

`skills/security-scan`（origin: ECC）は `npx ecc-agentshield` の薄いラッパー文書だった。
`.claude/` 設定（CLAUDE.md / settings.json / mcp.json / hooks / agents/*.md）の
misconfiguration・injection 面を静的スキャンし A–F グレードを出すツールの使い方を記述していた。

[ADR-0011](0011-retire-builtin-duplicate-skills-and-version-dependent-rules.md)（2026-06-10）は
本 skill を「AgentShield wrapper として固有機能」と明示して Keep 判定していた。しかしその後の
実績は薄い。`metrics/skill-usage.jsonl` を見ると invoke / slash とも 0 件（5 ヶ月間）で、
記録された 8 件のヒットはすべて棚卸し時の read にすぎない。`skill-stocktake` の verdict も
Improve — 記載されている flag 群は ecc-agentshield 1.4.0 の stale subset になっており、
CI snippet も `affaan-m/agentshield@v1` に pin されたままだった。

2026-07-25、公式の `claude-security` プラグイン v0.10.0（Anthropic 製）を導入・有効化し、
`~/.claude` 全体を初回スキャンした（189 agents / 11.2M tokens / 20 findings → 根本原因 8 個、
7 個修正。レポート: `CLAUDE-SECURITY-20260725-022756/`）。プラグインのドキュメント上は
「`.claude/` 設定は trust model の前提であり検査対象外」（plugin README / SECURITY.md /
SKILL.md）とされているが、**実測ではこの前提が成立しなかった**。scanRoot を `~/.claude` に
すると、ハーネスの設定成果物そのもの（settings.json の権限設計・hooks・agents 定義・
scheduled-tasks の散文）がプロダクションコードとして監査対象に入った。このハーネスでは
設定こそがコードベースであるため、ドキュメントが想定するスコープ外扱いにはならなかった
（台帳 T-006 の観察記録）。

`skill-health` の Risk 次元はこれまで security-scan へ委譲していたが、「latest grade if
present」という grade 格納パスは一度も定義されておらず、実装上は常に不在だった。

## Decision

1. `skills/security-scan/` を完全削除する（`git rm`）。ADR-0011 と同様に `_archived/` は使わず、
   復元経路は git 履歴 + commit message へ記録する checkout コマンドとする。
2. ADR-0011 の Keep 判定を本 ADR で override する。
3. risk 面の委譲先を `/claude-security` プラグインへ repoint する — 生きた参照 13 箇所
   （`rules/common/security.md` のポインタ 1 / `agent-architecture-audit` 2 / `config-gc` 1 /
   `skill-health` SKILL.md 6 + `scripts/scan_refs.py` 2 + `pyproject.toml` 1）。
4. `skill-stocktake/results.json` 等の stale エントリは手動 prune せず、次回実行の再生成に
   任せる（ADR-0011 Negative 節の既決に従う）。

退役の根拠は、5 ヶ月間 invoke 0 件という不使用実績、ドキュメントの stale 化、第三者 npm
（ecc-agentshield）への supply chain 依存、そして公式プラグインが設定監査面を実測でカバーした
ことの 4 点が重なったことにある。

## Alternatives Considered

### ADR-0011 どおり Keep 継続

却下。Keep の根拠だった「AgentShield wrapper として固有機能」は、公式プラグインが同じ監査面を
実測でカバーした時点で失効した。5 ヶ月間 invoke 0 件という実績は、その固有機能がそもそも
消費されていなかったことを示している。

### risk 次元の空席化 + 決定論ゲート化の別途起票

当初案。プラグインのドキュメント読解が「`.claude/` 設定は見ない」だったため、risk 面は
別途ゲート化を起票する前提だった。却下。2026-07-25 の実スキャンで scanRoot が `~/.claude`
なら設定成果物が監査されることが実証され、この前提自体が覆った。

### `_archived/` へ移動

却下。ADR-0011 の Alternatives で既に決着済み — 完全削除 + git 履歴を soft-delete 層とする方針。

### security-scan のドキュメントを agentshield 1.4.0 に追随更新

`skill-stocktake` の Improve verdict を素直に実行する案。却下。未使用の第三者 npm ラッパーの
文書整備は消費者のいない保守コストにしかならない。origin: ECC は無改変保持が方針であるため、
更新には ECC-customized への fork が伴うが、その対価に見合う利用実績が存在しない。

## Consequences

### Positive

- セキュリティ面の入口が `/claude-security` に一本化され、二重面が解消する。
- 第三者 npm（ecc-agentshield）への supply chain 依存が消える。
- skill listing の常駐コストが 1 本分減る（台帳 T-002 の方向と整合）。
- `skill-health` の Risk 次元が、一度も存在しなかった grade でなく実在する成果物
  （`CLAUDE-SECURITY-*/CLAUDE-SECURITY-RESULTS.md`）を指すようになる。

### Negative

- agentshield の A–F グレードと `--fix` 自動修正は失われる。ただし 5 ヶ月間未使用だったため、
  実害は理論上のものにとどまる。
- プラグインが `.claude/` 設定監査面をカバーするのは**実測ベース**であり、ドキュメント上の
  契約ではない。将来のプラグイン更新でスコープが狭まると risk 面が静かに薄くなりうる。
  緩和策として、本 ADR と台帳 T-006 の観察記録を再判断のトリガー条件として残す。
- `results.json` の stale エントリは次回 `/skill-stocktake` 実行まで残る。

### Neutral / Follow-ups

- Revert 手順: `git checkout <退役 commit の直前 hash> -- skills/security-scan/`
  （実 hash は退役コミット時に commit message へ記録する）。

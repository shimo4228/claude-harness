# ADR-0021: rules メタデータ（rationale / review-when）と構造的前提の lint ゲート化

## Status

accepted

## Date

2026-07-26

## Context

ADR-0018 の rightsize 棚卸しで、rule の退役判定コストに非対称があった: ADR が残っていたルール（agents.md の Author-Reviewer 分離）は数分で判定できたが、記録の無いルール（旧 planning.md の plan mode 禁止）は git log の考古学が必要だった。さらに git-workflow.md の「Attribution disabled globally via settings.json」は、参照先の設定キー（includeCoAuthoredBy）が存在しないまま常駐し続け、消えた時期も特定できなかった（幽霊設定）。構造的前提なのに機械検証が無かったのが根因である。

検証で確定した事実:

- **HTML コメントはセッション注入時に strip される**（実測: 全 rules の 1 行目 `<!-- origin -->` が注入本文に現れない）。コメント形式のメタデータは常駐 words コストゼロ。
- 失効条件は**書いた時点でしか捕捉できない** — 幽霊設定は監査時にはもう「なぜ・いつから」が失われていた。監査側の汎用質問（rules-stocktake Stage 1 の 6 問）では per-file トリガーを復元できない。
- 既存 harness_lint.py は settings.json→hook パス / markdown リンク / See-skill / origin を検査済みだが、**rules 本文が inline code で参照する hook スクリプトパスは未検査**だった（幽霊設定と同クラスのギャップ）。対象を棚卸しした結果、fail ゲートに値するのは hooks スクリプトパス参照 3 件のクラスのみ。

## Decision

1. **rules/common/*.md 全 13 ファイルに `<!-- rationale: ... -->`（ADR 番号 or 一行の存在根拠）と `<!-- review-when: ... -->`（失効条件 / 見直しトリガー）を origin コメント直後に付与する**。frontmatter でなくコメント形式（origin と同形式、常駐ゼロ）。README.md は index なので対象外。
2. **harness_lint.py を 2 点拡張する**: (a) rules/common/*.md の rationale / review-when コメント存在チェック（先頭 10 行、origin と同列の fail）、(b) rules/**/*.md の inline code が **bare path** で参照する `hooks/*.sh` / `scripts/hooks/*.py` の実在チェック。`bash ~/.claude/hooks/my-hook.sh` のようなコマンド込み例示は対象外（inline code 全体が path のものだけ — テンプレ例示の偽陽性回避）。違反注入 → rc=3 赤化 → revert で発火実証済み。
3. **rules-stocktake を接続する**: Phase 1 チェックリストにメタデータ存在（harness_lint の結果を読み off）、Stage 2 で review-when 宣言を最優先の refutation question として消費、Phase 4 で verdict 変更時に同 diff でメタデータを更新。

メタデータの分業: **存在チェックは code**（harness_lint、構造的性質）、**内容の評価は LLM**（rules-stocktake、意味的性質）— patterns.md の enumerate/decide 分割の適用。「documented-invariant はゲートに落とす」原則の、メタデータ規約自身への自己適用でもある。

## Alternatives Considered

### (a) frontmatter 形式でメタデータを持つ

rules は frontmatter を使わない慣例で、YAML パースの検証も増える。コメント形式で strip 実測が取れている以上、利点がない。**却下**。

### (b) rules-stocktake の監査質問に 2 問足すだけ（ファイル側に書かない）

常駐もファイル変更も増えない最軽量案だが、失効条件は書いた時点でしか捕捉できず、監査時の ad hoc 生成では per-file トリガーを復元できない（幽霊設定がその実証）。**却下**。

### (c) 全構造的前提の網羅ゲート（設定キー・外部パス・数値クレーム含む）

棚卸しの結果: `permissions.allow` は散文中のキー名で構造的検出に向かず、`~/.codex/AGENTS.md` 等は repo 外の環境資産、数値クレームは stocktake が live 計測を既に義務化。fail に値するのは hook スクリプトパスのクラスのみ。**縮小採用**（YAGNI）。

## Consequences

### Positive

- rules 棚卸しの考古学コストが下がる: 存在根拠は 1 行目に、失効条件は事前宣言として監査の第一質問になる。
- 幽霊参照（存在しないスクリプトパス）は commit 前に決定論的に検出される。
- 新規 rule 作成時に rationale / review-when の記述が lint で強制され、記録の無い rule が増えない。

### Negative

- strip は substrate の挙動であり将来変わりうる。変わった場合の上限コストは 2 行 × 13 ファイル ≒ 300 words（disk 実測差分）で、rules-stocktake の live 計測が検知する。
- `wc -w` の disk 値と注入実測が乖離する（README に注記済み）。
- 変更は origin: shimo4228 / ECC-customized の rules に及ぶため、公開 repo（claude-harness）との diff が増える。harness-sync での follow-up が必要。

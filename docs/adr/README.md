# Architecture Decision Records

このハーネス（~/.claude）に関する設計判断を記録する。

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-ecc-skill-management-policies.md) | ECC スキル管理ポリシー | accepted | 2026-03-08 |
| [0002](0002-disable-claude-mem.md) | claude-mem プラグイン無効化 | accepted | 2026-03-08 |
| [0003](0003-regex-to-llm-classification.md) | 正規表現から LLM 分類への転換 | accepted | 2026-03-20 |
| [0004](0004-retire-documentation-rule.md) | documentation.md ルール退役 | accepted | 2026-03-13 |
| [0005](0005-retire-kimi-delegation-rule.md) | kimi-delegation.md ルール退役 | accepted | 2026-03-13 |
| [0006](0006-stop-ecc-contributions.md) | ECC へのコントリビューション終了 | accepted | 2026-03-24 |
| [0007](0007-open-concept-network-effect.md) | 開放型ネットワーク効果 — 概念を囲い込まない公開戦略 | accepted | 2026-03-25 |
| [0008](0008-ecc-local-only-management.md) | ECC ローカル管理一本化 — プラグイン廃止と選択的取り込み | accepted | 2026-03-29 |
| [0009](0009-implementation-chain-front-loaded-in-plan.md) | Implementation Chain を plan に front-load（2介入点モデルは ADR-0035 で退役） | accepted | 2026-05-02 |
| [0010](0010-context-sync-cascade-and-writer-agents.md) | context-sync の cascade 化と writer agent 新設 (codemap-writer / adr-writer) | accepted | 2026-05-22 |
| [0011](0011-retire-builtin-duplicate-skills-and-version-dependent-rules.md) | built-in 重複 skill とバージョン依存 rules の退役 | accepted | 2026-06-10 |
| [0012](0012-cross-tool-skill-sharing-via-agents-skills.md) | クロスツールのスキル共有を ~/.agents/skills 経由に一本化 | accepted | 2026-06-28 |
| [0013](0013-cross-model-review-seam-via-codex.md) | クロスモデルレビュー seam を Codex で開く — 多エージェントは脱相関の一点に限定 | accepted | 2026-06-28 |
| [0014](0014-retire-multi-agent-orchestration-rule.md) | multi-agent-orchestration.md ルール退役 — native 部分は公式ハーネスに委譲 | accepted | 2026-06-30 |
| [0015](0015-cross-agent-rules-sharing-reference-first.md) | クロスエージェント rules 共有は「参照 > 生成 > 同期」— エージェント側アタッチポイント方式 | accepted | 2026-07-18 |
| [0016](0016-writer-agents-render-not-decide.md) | Writer agent は render 専任 — 委譲境界は semantic authority (EN→JA 翻訳は skill-only / adr-writer リーク修正) | accepted | 2026-07-18 |
| [0017](0017-retire-authorship-strategy-rule-absorbed-by-skill.md) | authorship-strategy.md ルール退役 — skill が凝縮重複を吸収 | accepted | 2026-07-19 |
| [0018](0018-rules-rightsize-for-claude5.md) | rules/ の rightsize — Claude 5 世代向け scaffold dissolution（第2波は ADR-0035） | accepted | 2026-07-25 |
| [0019](0019-human-gate-layer.md) | custom human gate（ADR-0035 で substrate 既定へ委譲） | superseded | 2026-07-25 |
| [0020](0020-retire-security-scan-delegate-risk-to-claude-security.md) | security-scan を退役し risk 面を claude-security プラグインへ委譲 — ADR-0011 Keep の override | accepted | 2026-07-26 |
| [0021](0021-rules-metadata-and-premise-lint-gates.md) | rules メタデータ（rationale / review-when）と構造的前提の lint ゲート化 — コメント形式で常駐ゼロ、幽霊参照の再発防止 | accepted | 2026-07-26 |
| [0022](0022-generation-audit-three-sibling-stocktakes.md) | 世代交代監査の 3 兄弟構成 — generation-audit オーケストレータ + agent-stocktake 新設（verdict は stocktake に委譲） | accepted | 2026-07-26 |
| [0023](0023-dissolve-planner-narrow-architect-to-essence-evaluation.md) | planner agent の Dissolve と architect の本質評価専任化 — fresh/rich context 軸によるサブエージェント適性判定 | accepted | 2026-07-27 |
| [0024](0024-dissolve-tdd-guide-and-axis-auxiliary-rationales.md) | tdd-guide agent の Dissolve と fresh/rich 軸の補助則 2 件（frozen-input render / bulk context isolation）— 軸の全 corpus 適用 | accepted | 2026-07-27 |
| [0025](0025-global-vs-project-asset-placement.md) | Global vs Project の資産配置基準を rules/common/skills.md に正本化 — 2+ repo/channel なら global、単一固有なら project overlay | accepted | 2026-07-27 |
| [0026](0026-retire-signal-first-residency.md) | Signal-first 常駐節の退役 — 消費 skill へのインライン内在化完了 + grill-me 質問抑制の衝突コスト（grill-me に Interview mode override と 6 次元停止条件を追加） | accepted | 2026-07-31 |
| [0027](0027-restore-review-execution-check-to-verify-gate.md) | Review 名簿の rules 復元（ADR-0035 で skill 正本 + commit reminder へ） | superseded | 2026-08-01 |
| [0028](0028-review-notice-full-scope-and-adr-reviewer.md) | 3区分検出と adr-reviewer 新設 — classifier は ADR-0035 で退役、adr-reviewer は維持 | accepted（一部 superseded） | 2026-08-01 |
| [0029](0029-skill-comply-parallel-scenarios-and-stderr-progress.md) | skill-comply のシナリオ 3 本を並列実行し、進捗を stderr へ — 無音の真因は stdout バッファでなく `tail` が EOF まで保留すること（実測）。完了順はレポートに漏らさず level 順に固定 | accepted | 2026-08-01 |
| [0030](0030-separate-output-writing-from-residency-register.md) | ユーザー向け出力 register（ADR-0035 で substrate へ委譲） | superseded | 2026-08-01 |
| [0031](0031-child-permission-envelope-via-permissions-deny.md) | 無人の子セッションの封じ込めは `--settings` の `permissions.deny` で行う — `--allowedTools` は自動承認リストでツールを外さない（実測、ADR-0011 期の前提が偽）。F3/F4 の緩和は実際には入っておらず、`--allow-bash` は opt-in として機能していなかった | accepted | 2026-08-02 |
| [0032](0032-skill-comply-measurement-validity.md) | skill-comply は「測定が成立していたか」をレポートの一級市民にする — project skill を Tier 1（stub）/ Tier 2（本文）で測り、`<sandbox>/.claude/` と `.git/` をツール専有にし、`files:` で中身を渡す。読み込めなかった run はスコアから除外し終了コード 1 | accepted | 2026-08-02 |
| [0033](0033-subagent-model-tier-by-downstream-verification.md) | サブエージェントのモデル階層は「その出力を検査する層が下流にあるか」で決める — 決定論ゲートは意味的 review の代替として数えない（planning.md）。`model` 未指定は inherit で親セッションを継承するため全 agent に明示し、harness_lint で決定論化 | accepted | 2026-08-02 |
| [0034](0034-move-review-check-before-the-approval-gate.md) | Review 通知の Stop 配線（ADR-0035 で custom gate とともに退役） | superseded | 2026-08-02 |
| [0035](0035-commit-review-hook-and-rules-rightsize.md) | Commit 前 Review / Verify reminder の薄型化、rules/ rightsize、global when-code-when-llm の退役 | accepted | 2026-08-02 |
| [0036](0036-herdr-toolkit-skills-only-plugin.md) | herdr 系スキルは skills-only plugin (herdr-toolkit) として公開する | accepted | 2026-08-03 |
| [0037](0037-publish-harness-adrs-and-remediate-git-hostile-config.md) | harness ADR を claude-harness へ公開し、前提として commit 面 hook の敵対的 .git/config を無害化する | accepted | 2026-08-08 |
| [0038](0038-publish-curated-commit-hooks.md) | commit 面 hook を curated allowlist で claude-harness へ公開し、前提として抽出器の 2 経路と textconv を塞ぐ — 公開判定は provenance でなく curation。公開前レビューが secret gate の 2 バイパスと 1 RCE を実測、右端一致は左端と対称のため全ターゲット走査へ | accepted | 2026-08-08 |
| [0039](0039-retire-python-reviewer-simplify-in-chain.md) | python-reviewer を退役し、chain を bug 軸 (code-reviewer) × quality 軸 (/simplify) に直交化 — 決定論チェックは verify.sh、idiom は substrate が吸収 (Downward dissolution) | accepted | 2026-08-13 |
| [0040](0040-demote-feat-tdd-to-conditional.md) | feat × TDD を必須から条件付き発火へ降格 — 現行世代で残る価値は RED→GREEN の儀式でなく「実装を見る前に振る舞いを固定する」spec pinning だけ。テストの要否は不変 (coverage floor は Verify が担保) | accepted | 2026-08-15 |

## Template

新しい ADR を追加する際は以下のフォーマットに従う:

```markdown
# ADR-NNNN: [Title]

## Status
accepted | superseded | deprecated

## Date
YYYY-MM-DD

## Context
[何が問題だったか]

## Decision
[何を決めたか]

## Alternatives Considered
[他に検討した選択肢]

## Consequences
[この判断の結果、何が容易/困難になるか]
```

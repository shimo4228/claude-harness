# ADR-0013: クロスモデルレビュー seam を Codex で開く — 多エージェントは脱相関の一点に限定

## Status

accepted

## Date

2026-06-28

## Context

レビューチェーン（[`planning.md`](../../rules/common/planning.md) の Chain Matrix）は Claude 内部の subagent（`code-reviewer` / `python-reviewer` / `security-reviewer`）のみで構成されていた。これらは同一モデル族であり、作者と同じ盲点を共有する（相関した盲点）。`agents.md` の Author-Reviewer Separation は「重要判断では別モデルを peer reviewer に」と既に述べているが、ハーネスにその実体（別モデルへの接点）は無かった。

ユーザーは OpenAI Codex CLI を併用しており（[ADR-0012](./0012-cross-tool-skill-sharing-via-agents-skills.md)）、「レビューに Codex を絡められないか」という要望が起点。実装前に Phase 0 として ECC v2.0（affaan-m/ECC, main, 271 skills）のマルチエージェント群を調査した結果、次が判明した:

- **orch-\*（6本）/ team-agent-orchestration / plan-orchestrate / parallel-execution-optimizer** は Claude 内部 subagent のオーケストレーションで、既存の **Workflow tool + planning.md chain と機能重複**（ADR-0009 で確立済み）。
- **dmux-workflows** は tmux ペインで Codex を含む異種ハーネスを並べるが、**対話・手動**でチェーンに組み込めない。
- **multi-execute（`scripts/orchestrate-codex-worker.sh`）** は Codex をプログラム的に呼ぶ唯一の実体だが、外部 npm ランタイム **`ccg-workflow` 依存**で重く、plan→implement→audit の**実行オーケストレータ**でレビュー単機能ではない。

これらはいずれも「別モデルによるレビュー」という空白を埋めない。調査を通じて、多エージェントの価値が **2 軸に割れる**ことを特定した: **同一モデルを増やす = スループット/文脈スケール**（判断の質は上がらない、盲点が相関）と、**別モデルを足す = 判断の脱相関**（別系統だけが構造的盲点を捕まえる、代償は cold handoff 税）。

## Decision

1. **cross-model seam を、脱相関が最も効く review に一点だけ開く**。`codex-review` skill を新設し、read-only な `codex review` を薄くラップする。read-only 不変条件は**外部 CLI の仕様に依存させず、フラグ allowlist でコード側に保証**する（未知 / `-c` / `--write` 等は exit 64 で拒否）。Codex 出力は untrusted input として扱い、verdict は Claude が所有する。

2. **スループット系は全て Claude native（Workflow tool）に寄せる**。ECC の orch-\* / team-\* / multi-execute / dmux は採用しない。理由は既存資産との重複（Workflow + planning.md chain）と外部ランタイム依存・solo 不適合。

3. **判断軸を rule に昇格**する。`rules/common/multi-agent-orchestration.md`（2 軸 + 9 普遍則 + 反パターン + ハーネス方針）を新設し、今後の多エージェント/クロスモデル判断の正本とする。

## Alternatives Considered

### (a) ECC multi-execute を丸採用

`ccg-workflow` 外部ランタイム依存で重く、ローカル一本化方針（ADR-0008）と衝突。実行特化でレビュー単機能でない。設計原則（Code Sovereignty / 構造化ハンドオフ / dirty-prototype 扱い）のみ lift し実装は採らない。**Verdict: Compose**。

### (b) dmux-workflows

tmux ペインの対話・手動オーケストレーション。チェーンの自動ステップにできない。ad-hoc 並列セッション向けで用途が違う。

### (c) MCP server（`codex mcp-server`）登録

統合度は高いが Codex をフルエージェントとして起動する形で review 単機能には過剰。Codex を常用するようになった時の昇格先として保留。

### (d) hook で全自動発火

決定論的発火は得られるが、別モデルの課金が毎編集で走り、`feedback_autonomous_trigger_ceiling`（autonomous trigger ~40% 上限、user-invocable へ pivot）にも反する。Verify 限定の自動ゲートにしたくなった時の昇格先として保留。

### (e) Claude subagent で「codex-reviewer」を作る

Claude Code の subagent は常に Claude 自身で、別モデルにならない。脱相関の目的を達成できない。別モデルの唯一の接点は Bash 経由の外部 CLI 呼び出しである。

## Consequences

### Positive

- 別モデルによる脱相関した second opinion を、最小依存（codex CLI のみ、外部ランタイム無し）で review チェーンに追加できる。
- スループットは Workflow に集約され、orch-\*/team-\* の重複を抱え込まない。
- 多エージェント判断が rule 化され、将来「team-OS を組むべきか」等の問いに毎回ぶれずに答えられる。

### Negative

- Codex は別 auth・別課金・別 context（共有メモリ無し）の cold handoff であり、レビューのたびにフル文脈を渡すコストがかかる。ライブ実走は課金を伴う。
- 不変条件は codex CLI のフラグ仕様に対する allowlist で守るため、Codex が新フラグを追加した際は allowlist の追従が要る（回帰テストで固定済み）。

### Neutral / Follow-ups

- 次の脱相関 seam 候補（同じ軸）: **アンサンブル決定**（高リスク設計判断を別モデルと突き合わせ）、**敵対的検証**（deep-research / verify の claim を別モデルに反証させる）。
- **team-orchestration / autonomous-OS 方向には行かない**（solo + local-first と構造的に不適合）。
- ECC v2.0 評価の詳細は memory `reference_ecc_v2_eval.md` を参照。

## Related

- [ADR-0012](./0012-cross-tool-skill-sharing-via-agents-skills.md): Codex CLI 併用前提（本 ADR と同じ Codex を対象）
- [ADR-0009](./0009-implementation-chain-front-loaded-in-plan.md): orchestrate 系を Workflow + planning.md chain に集約した前提
- [ADR-0008](./0008-ecc-local-only-management.md): ECC ローカル一本化 — 外部ランタイム依存を避ける根拠
- skill `codex-review`, rule `multi-agent-orchestration.md` (dissolved 2026-07-03 rules-stocktake — substrate 吸収により退役。判断軸の残存分は `rules/common/agents.md`)

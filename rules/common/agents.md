<!-- origin: shimo4228 -->
<!-- rationale: ADR-0015（cross-agent 参照 > 生成 > 同期）+ ADR-0018 §5 — agent 一覧の手書きコピーを廃し、分離原則と外部エージェント境界のみ常駐 -->
<!-- review-when: Codex / Antigravity / Qwen のアタッチポイント構成を変えた時 / Herdr 環境を退役した時 / harness の native agent カタログ提示が変質した時 -->
# Agent Orchestration

agent カタログの正本は `~/.claude/agents/*.md` の frontmatter。セッション中は harness が
Available agent types として全 agent の説明を自動提示するため、**ここに一覧の手書きコピーを
置かない**（同じ frontmatter から生成される native 一覧に対して drift するだけ）。
起動順は skill: `implementation-chain` の Chain Matrix。

## Author-Reviewer Separation

レビューは実装者とは**別の agent プロセス**で走らせる。同一 context = 著者バイアスの盲点。
戦略的判断では別モデルを peer reviewer にする（→ `codex-review`）。

## Cross-Agent Harness Sharing（Claude Code の外）

上記は Claude Code 内のサブエージェント編成。ここは別プロセスの CLI エージェント
(Codex CLI / Antigravity CLI / Qwen Code 等) との rules 共有 — 別概念なので混同しない。

原則は「参照 > 生成 > 同期」([ADR-0015](../../docs/adr/0015-cross-agent-rules-sharing-reference-first.md))。
`~/.claude/rules` は正本のまま変更せず、各エージェント側のアタッチポイントで参照させる:

- **Codex CLI**: `~/.codex/AGENTS.md` の指示文ブロックで参照（グローバル→repo→cwd の順で連結）
- **Antigravity CLI**: `~/.gemini/config/rules/shared-claude-rules.md`（`trigger: always_on` 必須）
- **Qwen Code**: `~/.qwen/QWEN.md` の `@絶対パス` import

モデル試用（Kimi/GLM/Qwen をモデルとして使う）は `claude-code-router` でハーネスを維持したまま
モデルだけ差し替える — この場合は rules 共有そのものが不要。

## Cross-Agent Task Delegation（herdr 経由、上記とも別概念）

**実行中のタスクを別プロセスの CLI エージェントに委譲する**話。手順・コマンド仕様の正本は
skill: `herdr`（ここに複製しない — 実装詳細の再説明は drift すると実証済み）。

**ゲート条件**: (1) Herdr 管理下の pane にいる（`HERDR_ENV=1`）こと — バイナリの有無だけで
判定しない、(2) **ユーザーが明示的に Herdr 経由の委譲を求めた場合のみ**使う。
委譲や並列化が有益そうというだけで自発的に使い始めない（`codex-review` はこの依存を持たず
blocking exec で完結しており、それが既定路線）。

<!-- origin: shimo4228 -->
# Agent Orchestration

## Available Agents

Located in `~/.claude/agents/`:

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| planner | Implementation planning | Complex features, refactoring |
| architect | System design | Architectural decisions |
| tdd-guide | Test-driven development | New features, bug fixes |
| code-reviewer | Code review (汎用) | After writing non-Python code |
| python-reviewer | Python code review | After writing Python code |
| security-reviewer | Security analysis | Before commits |
| e2e-runner | E2E testing | Critical user flows |
| refactor-cleaner | Dead code cleanup | Code maintenance |
| scout | Pre-implementation solution discovery | New module/utility creation |
| prompt-writer | LLM prompt generation | Creating/rewriting prompts |
| codemap-writer | `docs/CODEMAPS/` 生成・refresh (scan + write の重い処理) | `update-codemaps` skill から自動呼び出し / context-sync Phase 0 drift 検出時 |
| adr-writer | ADR 6 セクション本文生成 (invention 禁止) | `adr-writer` skill から自動呼び出し / context-sync Phase 3 ADR 抽出時 |
| editor | Technical article の辛口レビュー (code 正確性, AI slop, narrative flow, 用語一貫性) | `writing-ecosystem` から呼び出し / tech tutorial・implementation guide draft 後 |
| essay-reviewer | Opinion essay の辛口レビュー (論理構造, argument overload, tone 一貫性) | `writing-ecosystem` から呼び出し / opinion・社会論・design philosophy 系 essay draft 後 |
| fact-checker | 記事内の検証可能な事実主張を web search で照合 | `writing-ecosystem` から呼び出し / 歴史・統計・citation を含む記事の公開前 |
| paper-reviewer | Academic paper の structure / claim sharpness / evidence-claim alignment review | `paper-ecosystem` から呼び出し / position paper・preprint draft 後 |
| source-fidelity-checker | Cited primary source を直接読み、paper claim との drift を検出 | `paper-ecosystem` から呼び出し / 既存 essay 群から抽出した paper の deposit 前 |
| vocabulary-consistency-checker | Paper 内の term definition / sub-classification の一貫性検証 | `paper-ecosystem` から呼び出し / paper draft 後、source-fidelity-checker と並列 |
| clarity-reviewer | 初見読者目線の明瞭性 review (新語予算 / タイトル軸の貫通 / メタ語り / 内部文脈依存 / 一文テスト) | `paper-ecosystem` から呼び出し / paper draft・大幅改稿後、他 3 reviewer と並列 |
| citation-formatter | In-text citation と reference list の整合・format 検証 (DOI / arXiv ID) | `paper-ecosystem` から呼び出し / paper deposit 直前、source-fidelity / vocabulary 通過後 |

## Immediate Agent Usage

各 agent をどの順序で起動するかは [`common/planning.md`](planning.md) の
**Implementation Chain Specification** で定義する Chain Matrix に従う。
このファイルは agent カタログ（上記）の正本。

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker

### Author-Reviewer Separation

Run reviews in a separate agent process from the implementer:
- Same context = author bias blind spots
- For strategic decisions, use a second model as peer reviewer


<!-- origin: shimo4228 -->
# Rules

毎セッション自動ロードされる常駐層。採用基準は「この環境固有の事実・配線・罠」。
思考や作業の手順は skill、発火時刻を要する検査は hook、一般的な判断は substrate が持つ。
経緯は [ADR-0018](../docs/adr/0018-rules-rightsize-for-claude5.md) と
[ADR-0035](../docs/adr/0035-commit-review-hook-and-rules-rightsize.md)。

各 rule は `origin`、`rationale`、`review-when` を持つ。存在は `harness_lint.py`、
意味と失効条件は skill: `rules-stocktake` が検査する。

## Structure

| Rule | 常駐する情報 |
|---|---|
| `agents.md` | agent catalog と外部 agent の境界 |
| `akc-cycle.md` | Scaffold Dissolution / ADR は一時的判断（Emptiness） |
| `coding-style.md` | global harness の変更対象 |
| `contemplative-axioms.md` | identity / values（verbatim） |
| `debugging.md` | rate limit の実証済み policy signal |
| `knowledge-staleness.md` | LLM 界隈 1 週間陳腐化 worldview — 検索時点照合と失効条件の既定 |
| `llm-first-code.md` | LLM 可読性を最優先する worldview — 読者は次セッションの LLM、執行者は機械ゲート |
| `planning.md` | search / chain / verify の入口 |
| `practitioner-identity.md` | 著者の自己定義（verbatim）— DOI は手段、研究者ではない |
| `security.md` | commit hook と trust boundary |
| `skills.md` | origin schema と skill path、skill-creator への命令形配線 |
| `task-tracking.md` | repo ごとの task ledger path |
| `testing.md` | coverage と production 境界 |

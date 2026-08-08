# ADR-0010: Context-Sync Cascade and Writer Agents

## Status

accepted

## Date

2026-05-22

## Context

ハーネスには documentation hygiene 用の skill が 2 つある: `context-sync` (5 phases: Discover / Overlap / Migrate / Freshness / Report) と `update-codemaps` (5 steps で `docs/CODEMAPS/` を生成)。両者は独立しており、context-sync の Phase 4 が codemap の drift を **検出はできても修正できない** 構造になっていた。update-codemaps 側も context-sync を認識していなかった。

結果として再発する failure mode が観測された: ソースコードが drift → codemap が stale → context-sync が Phase 2 (Overlap detection) を **stale な codemap に対して** 実行 → fictional な構造を前提に migration を提案する、というカスケード。

加えて、context-sync の Detection 対象は README.md だけが "External" role として登録されていた。`llms.txt` / `llms-full.txt` といった **AI-facing document** (shimo4228 の MyAI_Lab projects 13 件で repo root に存在) は検出対象から完全に外れており、これらの repo に対する context-sync は documentation role を 1 つ取りこぼした状態で動いていた。

さらに ADR / Codemap の生成品質がセッション間で不安定だった: Decision section が aspirational voice で書かれる、Alternatives が fabricated reject 理由で水増しされる、Codemap file が 1000 token budget を超える、といった事象が散発。これらを構造的に押さえる specialized agent が存在しなかった。

## Decision

3 つの変更を同時に適用する。

### 1. context-sync に Phase 0 (Codemap Freshness Pre-check) を追加する

3 つの OR signal で codemap stale を検知する:

- 7-day timestamp lag
- ±20% file count drift
- CODEMAPS が欠落

いずれかが hit した時点で skill は **自動で `codemap-writer` agent を Task ツール経由で invoke** する。`docs/CODEMAPS/` が既存の場合 (= edit) は確認なしで regen。signal C (CODEMAPS 不在 = 新規 directory + 新規 file 作成) のみ user に 1 回確認を取る。

Skill が agent を Task ツール経由で呼ぶのは agent-from-agent ではなく **1 段 nesting** であり Claude Code がサポートする範囲内。これに気付いたことで「ask once, pause」設計の前提が崩れた。

### 2. confirmation policy を「新規 file / directory 作成時のみ」に絞る

全 phase を通じて、確認 prompt は **不可逆な操作 (新規 file 作成 / 新規 directory 作成) のみに集約**する。既存 file への edit は git diff が audit trail、`git checkout -- <file>` が undo なので確認不要。Phase 3 で複数の新規 file 作成が必要な場合は **batch confirmation** (1 度の Y/n) で済ませる。

この policy は ADR-0007 の "開放型ネットワーク効果" とは別軸の判断 — user の連続実行性 (`/context-sync` を毎回 5-6 回中断させない) を優先する。

### 3. context-sync Detection に AI-facing role を追加する

Phase 1 の Detection target に `llms.txt` と `llms-full.txt` (repo root) を追加し、README と同等の rigor で扱う "AI-facing" role として登録する。Phase 4 には対応する freshness check を追加する: link resolution、README との duplication detection、CODEMAPS に対する freshness 検証。

### 4. writer agent 2 つと skill 1 つを新設する

skill+agent split pattern (skill = ユーザー向け orchestration、agent = subjective body generation) を適用:

- `codemap-writer` agent: `~/.claude/agents/codemap-writer.md`
- `adr-writer` agent: `~/.claude/agents/adr-writer.md`
- `adr-writer` skill: `~/.claude/skills/adr-writer/{SKILL.md, evals/evals.json}`

既存の `update-codemaps` skill は scan + write を `codemap-writer` agent に delegate する形に refactor する。既存の `context-sync` skill は ADR body generation を `/adr-writer` に delegate し、inline template を持たない。

## Alternatives Considered

### Phase 0 を "ask once, pause" にする (初稿で一度採用→破棄)

stale 検出時に user に「`/update-codemaps` を先に走らせろ」と prompt して context-sync を pause する案。本 ADR の初稿ではこちらが Decision 1 だった。不採用理由: (a) `/context-sync` の連続実行性が損なわれる (毎回中断が発生)、(b) 前提だった「Claude Code は agent-from-agent call を support しない」は context-sync 自身が skill であり、skill が Task ツールで agent を呼ぶのは 1 段 nesting で合法という事実を見落としていた、(c) ユーザーの明示指示「新規文書作成以外は確認なしにしてくれ」と整合しない。

### Confirmation を全 phase で取る (status quo)

Phase 1-4 で毎回確認を取る現行設計。不採用: ユーザーの認知負荷が高い割に、確認の大半は既存 file の edit (= 可逆) に対するもので、git diff があれば事後検証可能。新規 file / 新規 directory 作成 (不可逆) のみに confirmation を集約する方が cost/benefit が良い。

### ADR template を context-sync Phase 3 に embed する (status quo を維持)

canonical template を duplicate することになり、context-sync 版と adr-writer 版が時間と共に drift する。skill delegation による single source of truth の方が維持コストが低い。不採用。

### codemap と ADR を 1 つの mega-agent に統合する

ハーネスの Knowledge Placement rule (`rules/common/skills.md`) に反する — domain が異なり、input が異なり、style 制約が異なる。bundling すると両方に対して中途半端な agent になる。不採用。

### llms.txt 検出だけ追加し freshness check は省略する

検出だけ追加しても Phase 1 の output に noise が増えるだけで、検証 (link resolution, README dedupe) が無いと実用にならない。Phase 4 の freshness check と組み合わせて初めて新検出が機能する。不採用。

## Consequences

### Positive

- context-sync が stale codemap に対して migration を提案しなくなる。Phase 0 が downstream phase の前に drift を捕える
- Phase 0 が **自動 cascade** するため `/context-sync` 1 回の呼び出しで codemap regen まで完結する。user は毎回手動で `/update-codemaps` を挟む必要がない
- Confirmation が「新規 file / directory 作成」のみに集約され、`/context-sync` の連続実行性が大幅に改善する
- AI-facing document (`llms.txt`, `llms-full.txt`) が全 repo で README と同等の hygiene treatment を受けるようになる
- ADR の品質が `adr-writer` agent の invention-prevention contract で bounded になる — Decision は imperative voice、Alternatives の reject 理由は input に trace、Consequences は Positive / Negative / Neutral に split
- Codemap file 生成が `codemap-writer` agent の token budget により ≤1000 tokens/file で enforce される
- 新しい skill+agent pair (`adr-writer`) が future writer skill の template になる (例: `llms-txt-writer` の body generation が肥大化したら同じ split を採用可能)

### Negative

- 維持対象ファイルが 3 つ増える (agent 2 + skill 1 + evals.json 1)
- Phase 0 の false-negative リスク: 3 signal すべてが threshold 直下 (例: 6-day lag, +15% file drift, INDEX.md present) で stale な codemap を見逃す可能性。verbose mode で raw signal value を表示し、`--skip-cascade` フラグで bypass を提供することで緩和
- **Phase 0 の false-positive リスク**: stale 判定が誤検出だった場合 (例: 大規模 refactor 直後で source 側 ctime が新しいが構造は等価) に codemap が無駄に regen される。コスト的には agent 1 回起動分なので致命的ではないが、user が「触ってないのに codemap が変わった」体験をする可能性。verbose log で signal 値を残しているので事後に検証可能
- skill+agent split が 1 段 indirection を追加する — 新規 contributor がどのファイルが何を担うかを理解するのに一瞬かかる。各 SKILL.md に「skill = orchestration, agent = body」の framing を明記して緩和

### Neutral / Follow-ups

- `llms.txt` / `graph.jsonld` writer (`llms-txt-writer`, `jsonld-knowledge-graph`) は **まだ** context-sync から cascade されていない。本 ADR では cascade pattern を codemap に限定する。AI-facing doc の writer cascade は pattern の有用性が確認できたら別 ADR で扱う
- 本 ADR 自体が `adr-writer` skill を使って生成されている (self-test)。読んだ結果が natural なら agent contract は機能している。stilted / padded に感じる箇所があれば、他 project に展開する前に agent prompt を refine する
- `rules/common/agents.md` の agent catalog に `codemap-writer` と `adr-writer` を origin: shimo4228 で登録する

## Related

- [ADR-0001](./0001-ecc-skill-management-policies.md): Origin tracking (`codemap-writer`, `adr-writer` は origin: shimo4228)
- [ADR-0009](./0009-implementation-chain-front-loaded-in-plan.md): skill+agent 責務分離の前例 (code-review ↔ security-review)
- [ADR-0016](./0016-writer-agents-render-not-decide.md): 本 ADR の「agent = subjective body generation」framing を **ref 定義** する。writer agent は render 専任で意味的権限を持たず、decide はメインループに残る (Decision 4 の framing が too broad で `adr-writer` に意味権限リークを生んだため)
- `rules/common/skills.md` の Knowledge Placement 原則 (mega-agent 不採用の根拠)

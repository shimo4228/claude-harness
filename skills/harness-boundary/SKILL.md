---
name: harness-boundary
description: "agent 環境に mechanism（rule / skill / hook / agent / workflow / runtime 拡張 / prompt chain）を追加・変更・レビューするとき、それが 6 層（model capability / skill = 手続き記憶 / values・policy / eval / data・memory / runtime）のどこに属するか、なぜモデル自身に任せられないか、次のモデル世代で不要になるか、runtime を Claude Code → Pi → Codex と交換しても残す価値があるかを問い、Keep / Move / Simplify / Make temporary / Delete / Defer を返す設計レンズ。Use when — 「これはハーネスに入れるべきか」「どの層に置くか」「モデルに任せられないか」「runtime 変えても残るか」「harness が肥大している」「この hook / rule / workflow を足していい？」, when implementation-chain の Plan で harness 自体（~/.claude の rules / skills / hooks / agents / settings）を変更する task と判定されたとき, or /harness-boundary. Delete / Simplify は成功として扱う。NOT for — 未構築物の build-or-not 単体（→ agent architect）、設置済み資産の定期監査と Retire / Dissolve の verdict（→ rules-stocktake / skill-stocktake / agent-stocktake。本 skill は証拠を渡すだけ）、世代交代時の一括照合（→ generation-audit）、loop 構造の妥当性（→ loop-design-check）、harness の作り方の処方（→ agent-harness-construction）。"
user-invocable: true
origin: shimo4228
---

# harness-boundary — harness を捨てても残るものだけを資産にする設計レンズ

「ハーネスこそ資産」は半分しか正しくない。モデル固有の弱点を補う harness logic は
モデル世代ごとに陳腐化し、runtime（tool 実行・permission・state・retry・agent loop）は
標準化と置換が進む。残るのは harness の中に**混在している別の層**だ。この skill は
mechanism を追加・変更・レビューするときに、その混在を分解するための問いを出す。

これは architecture の強制ではなく、資産境界・可搬性・陳腐化を判断するレンズである。

## 中心原則

- Model capability はモデルに置く。harness で再実装しない
- Procedural knowledge は skill に置く
- Values と責任境界は明示的で検査可能な形に保つ
- Quality の定義は eval に置く
- Domain 知識と履歴は data / memory に置く
- Runtime は実用上できる限り薄く、交換可能に保つ

そして: **harness を保存するために最適化しない。harness を交換しても残るべきものを
保存するために最適化する。** 新しいモデルが既存 logic を不要にしたなら、それは設計の
失敗ではなく削除のタイミングである。Delete / Simplify は成功として扱う。

## 6 層

| 層 | 中身 | この harness での対応物 | 既存語彙 |
|---|---|---|---|
| Model capability | reasoning / planning / coding / tool-use 判断 / self-correction / decomposition / reflection | Claude 本体（system prompt + tool description を含む） | substrate、generation-audit の runtime 層 |
| Skills（手続き記憶） | この task はこの手順 / このレビューはこの観点 / この障害はこの runbook / この成果物はこの検証 | `skills/*/SKILL.md`、`agents/*.md` の本文 | 「手順は skill」（rules/README.md） |
| Values / Policies / 責任境界 | 何を優先するか / 何をしないか / 人間承認が要る操作 / 委譲範囲 / 正本 / 失敗時の優先 | `rules/common/`（identity / values 層、ADR-0018 D7）、`settings.json` の permissions、task request の権限 | 「環境固有の事実・配線・罠」（ADR-0035） |
| Evals | acceptance criteria / tests / rubric / benchmark / regression / quality gate | `.claude/verify.sh`、`tests/`、`skill-comply`、`llm-as-judge`、judge agent（readme-judge 等） | Verify、binding 判定 |
| Data / Memory | 成果物 / decision history / domain 知識 / preferences / provenance / 履歴状態 | `docs/adr/`、auto-memory、`.notes/`、`metrics/*.jsonl`、wiki | ADR = 日付つき仮説 |
| Runtime | tool calling / shell・fs / permission 実装 / sandbox / connector / retry / logging / state / routing / agent loop | Claude Code 本体、`hooks/*.sh`、MCP server、Workflow / Agent tool、launchd tick | control plane（ADR-0019）、hook は時刻（ADR-0035） |

hooks は runtime 層に座るが、**policy を黙って encode しやすい**（例: 承認 gate の条件、
何を block するか）。hook を見るときは「時刻の配線」と「中に埋まった policy」を分けて、
後者は rule / ADR に見える形で出ているかを問う。

## 6 問

対象 1 件につき、規模に応じて必要な問いだけ使う。

- **A. どの層か。** 複数にまたがるなら分離できないか
- **B. なぜモデル自身に任せられないか。** 明確な理由が言えなければ harness に足さない。
  「前のモデルが苦手だった」は理由にならない — 今のモデルで試したか
- **C. 次のモデル世代で不要になりそうか。** 能力不足の workaround なら恒久 architecture に
  しない。temporary / removable と明示し、失効条件を書く
- **D. Runtime を交換しても残す価値があるか。** Claude Code → Pi → Codex → 未知の runtime に
  移しても要るなら、runtime から切り離して保持する候補。要らないなら runtime 固有として薄く
- **E. 必要なインフラか、差別化資産か。** 両方「重要」だが混同しない。インフラは借りる・
  置換する前提、差別化資産は可搬な形で持つ
- **F. もっと単純な層へ移せないか。** 典型の移送:
  custom agent loop → model / hard-coded workflow → skill / runtime 内の条件分岐 → policy /
  prompt による品質判定 → eval / 埋め込まれた知識 → data

## 強く疑う対象

自動的に否定はしない。だが以下は B〜D を省略せずに通す:

elaborate agent loop / 必須の reflection / 必須の planning 段 / 固定の multi-agent
orchestration / 過剰な routing / 長い system prompt / モデル固有の行動 workaround /
モデル能力の重複実装 / 古いモデルが要したから残っている workflow / domain 知識を含む
runtime 固有抽象 / policy を黙って encode する hook / 責任境界を隠す不透明な自動化 /
既存 harness 設計を温存すること自体が目的の機構

## 出力

大げさにしない。1 行で済むなら 1 行（例: 「これは skill 層。runtime に置く理由なし → Move」）。
**毎回全項目を出さない。** 判断が分かれる・影響が広い場合だけ次の形:

```
Classification        : 層（複数なら分離案）
Keep outside model because : モデル外に置く理由（無ければ Delete 候補）
Portability           : runtime / model 交換時に残すか
Obsolescence risk     : Low / Medium / High（根拠 1 行、可能なら失効条件）
Recommendation        : Keep / Move / Simplify / Make temporary / Delete / Defer
```

## 既存 verdict との接続

本 skill が Recommendation を直接出すのは**提案中・変更中の mechanism** に対してだけ。
**設置済み資産**に遡及適用した場合は結論を自分で実行せず、該当 stocktake に証拠として渡す
（generation-audit と同じ「読む、要求しない」契約。verdict 表の正本を割らない — ADR-0022）。

| 本 skill | 設置済み資産での対応先 |
|---|---|
| Delete | rules / skill / agent-stocktake の Retire / Dissolve |
| Move | 同 Demote / Merge、または rules-distill（skill → rule 方向） |
| Simplify | 同 Improve、built-in `/simplify` |
| Make temporary | rule なら `review-when:`、ADR なら `## Review-when`、skill なら `## 失効条件` に期限を書く |
| Defer | skill: `rfc-writer` で `draft` として起票（単一表だけの小 repo は `.notes/TASKS.md` へ 1 行） |
| Keep | 理由を 1 行残す（将来の stocktake の根拠になる） |

## 適用外

- 未構築物の build-or-not 単体 → agent `architect`（zero-base test）。本 skill は「作るなら
  どの層に・いつまで」を答える
- loop 構造の妥当性（servo / 判定可能性 / damping）→ skill: `loop-design-check`
- 世代交代時の一括照合 → skill: `generation-audit`
- harness の作り方（action space / observation / recovery）→ skill: `agent-harness-construction`
- 人間可搬性（他人が install して使えるか）→ `skill-creator/references/portability.md`

## 失効条件

- substrate が層分解・可搬性・陳腐化の判断を native に持ち、harness 変更時に自発的に問うように
  なったら本 skill は退役する（Downward、`rules/common/akc-cycle.md`）
- 6 層の区分自体が崩れたら（例: eval が model capability に吸収される、skill と data の境界が
  消える）区分を書き直す。問い A〜F は区分より長く残る想定
- 本 skill が 150 行を超えたら、本 skill 自身に 6 問を当てる

## Related

- `architect` agent — 事前の双子: build-or-not。本 skill は「作るならどの層に・どこまで」
- `loop-design-check` — Step 0 の subtract gate と同型（足す前に引く）
- `generation-audit` — 世代交代時の事後照合。本 skill は設計時の事前判断、証拠の向きは同じ
- `rules-stocktake` / `skill-stocktake` / `agent-stocktake` — verdict の正本。本 skill の
  Delete / Move は設置済み資産ではこれらへの証拠になる
- `rules-distill` — skill → rule の昇格基準（tests 1–3 は問い A・B の rule 版）
- `agent-harness-construction` — 作り方の処方。本 skill は置き場と寿命の判断
- `rules/common/akc-cycle.md` — Scaffold Dissolution（Inward / Downward）。問い C はその予測版
- ADR-0012 / 0015 / 0038 — runtime 可搬性の先例（skills → symlink 共有、rules → reference-first、
  hooks / permissions は共有外だが hooks 配線節は移植可）。問い D の実測根拠

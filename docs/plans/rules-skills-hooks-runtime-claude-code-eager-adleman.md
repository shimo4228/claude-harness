# Plan: skill `harness-boundary` — 層分解・可搬性・陳腐化の設計レンズ

## Context

「ハーネスこそ資産」という通説に対し、モデル能力の急伸で model 固有の補助ロジックは急速に
陳腐化する。harness に混在するものを 6 層（model capability / skills / values-policies /
evals / data-memory / runtime）に分解し、**runtime・model を交換しても残るものだけを資産として
設計する**レンズを skill 化したい。

### 調査結果（既存資産の確認）

| 確認した資産 | 判明したこと |
|---|---|
| `rules/README.md:4-5` | 唯一の層文: 「手順は skill、発火時刻を要する検査は hook、一般的な判断は substrate」— 4 way routing。6 層モデルは未命名 |
| `rules/common/akc-cycle.md` Scaffold Dissolution | Inward / Downward + モデル世代交代が Downward trigger。**事後**（吸収済みか）の判定 |
| `skills/generation-audit` | 意図/根拠/鮮度/失効条件 frame、**verdict を持たない**（ADR-0022: 正本を割らない） |
| `skills/rules-stocktake` / `skill-stocktake` / `agent-stocktake` | Keep/Improve/Update/Merge/Demote/Dissolve/Retire の verdict 正本。cost model = residency / trigger pollution / invocation |
| `skills/rules-distill` tests 1–3 | 「環境固有 / substrate 非 native / 手順でない」の admission 基準 |
| `skills/loop-design-check` Step 0 | subtract gate（そもそも loop が要るか）— 同型の「足し算前の引き算」 |
| `skills/config-gc` | 存在・孤児の GC。hooks は孤児判定のみで**層監査が無い**（coverage の穴） |
| `skills/agent-harness-construction` | ECC-customized、121 行、処方的、Related 無しの孤立 skill |
| `agents/architect.md` | 未構築物の build-or-not（複雑性 × 価値 × 使用頻度、zero-base）。本 skill の「事前の双子」 |
| ADR-0018 / 0035 | rules rightsize。0018 Decision 7 に「identity / values 層」が一度だけ命名済み。Decision 8 で portability.md を skills へ |
| ADR-0012 / 0015 / 0038 | runtime 可搬性の**個別判断**はある（skills → Codex symlink、rules → reference-first、hooks/permissions は共有外、hooks 節は移植可）が、再利用可能な frame は無い |
| `skills/skill-creator/references/portability.md` | **人間**可搬性（他人が install できるか）。runtime 可搬性ではない |
| `.notes/TASKS.md` | 直接の task 無し。`T-SKILL-CREATOR-EVAL-NATIVE`（substrate native eval に downward 委譲）、`T-EVAL-AXIS-BOOTSTRAP`（eval 軸の欠落）が本 lens の実例 |
| `scripts/hooks/harness_lint.py` / `.claude/verify.sh` | SKILL.md の必須 frontmatter = `name` / `description` / `origin`、`name` == dir 名。Markdown のみなら lint 以外のゲート無し |

### 新規に追加する価値（既存と重複しない部分）

1. **前向きの陳腐化リスク**（次世代で不要になるか）— 既存は全部「もう吸収されたか」の事後判定
2. **runtime 交換耐性**（Claude Code → Pi → Codex → 未知）を mechanism 単位で問う再利用 frame
3. **Make temporary / Defer** — 既存 verdict 表に無い「期限付きで残す」「判断を保留」
4. **hooks / runtime extension** を層の観点で見る入口
5. 「必要なインフラ」と「差別化資産」の区別

## Decision: 新 skill として追加（統合しない理由）

- generation-audit は verdict を持たない設計（ADR-0022）— 推奨を出す lens を足すと設計意図を壊す
- stocktake 群は**設置済み資産**の定期監査。本 lens は**追加・変更時**（設計レビュー時）に使う
- architect は build-or-not を答え、「どこに置くか・何年もつか」は答えない
- agent-harness-construction は「どう作るか」の処方で、目的が違う。Related で双方向に接続するだけにする

**verdict 正本を割らない位置付け**: 本 skill の Recommendation（Keep / Move / Simplify /
Make temporary / Delete / Defer）は**提案中の mechanism** に対する設計時の判断。設置済み資産に
遡及適用するときは、結論を自分で実行せず、該当 stocktake の証拠として渡す
（generation-audit と同じ「読む、要求しない」契約）。Delete は stocktake の Retire / Dissolve に、
Move は Demote / Merge に対応すると明記する。

## 名前

`harness-boundary`（推奨）。理由: 既存語彙が「scaffold / substrate / 資産 / 境界」で、
本 skill の主語は「harness の中の境界を引く」こと。`harness-distill` は `rules-distill` と
動詞が衝突し（distill = 昇格）、`harness-prune` は Delete 側に偏り、`runtime-portability` は
6 問のうち 1 問しか表さない。

## 実装

### 作成: `skills/harness-boundary/SKILL.md`（目標 90–130 行、Markdown のみ）

frontmatter:

```yaml
---
name: harness-boundary
description: "agent 環境に mechanism（rule / skill / hook / agent / workflow / runtime 拡張 / prompt chain）を追加・変更・レビューするとき、それが 6 層（model capability / skill = 手続き記憶 / values・policy / eval / data・memory / runtime）のどこに属するか、なぜモデル自身に任せられないか、次のモデル世代で不要になるか、runtime を Claude Code → Pi → Codex と交換しても残す価値があるかを問い、Keep / Move / Simplify / Make temporary / Delete / Defer を返す設計レンズ。Use when — 「これはハーネスに入れるべきか」「どの層に置くか」「モデルに任せられないか」「runtime 変えても残るか」「harness が肥大している」, when implementation-chain の Plan で harness 自体を変更する task と判定されたとき, or /harness-boundary. Delete / Simplify は成功として扱う。NOT for — 未構築物の build-or-not 単体（→ agent architect）、設置済み資産の定期監査と Retire / Dissolve の verdict（→ rules-stocktake / skill-stocktake / agent-stocktake。本 skill は証拠を渡すだけ）、世代交代時の一括照合（→ generation-audit）、loop 構造の妥当性（→ loop-design-check）、harness の作り方の処方（→ agent-harness-construction）。"
user-invocable: true
origin: shimo4228
---
```

本文構成（house style: `# name — 一行gloss`、JA 本文、`skill:` 表記）:

1. `## 中心原則` — 6 行の "should live in" 原則 + 「harness を守るな、harness を捨てても残るものを守れ」。
   Delete / Simplify = 成功、と明記
2. `## 6 層` — 表 1 枚（層 / 例 / この harness での対応物 / 置き場）。対応物列で既存語彙に接続:
   model capability = substrate、skills = `skills/`、values = `rules/common/`（identity / values 層, ADR-0018 D7）・
   `settings.json` permissions、evals = `verify.sh` / `skill-comply` / `llm-as-judge` / tests、data = `docs/adr/` / memory /
   `.notes/` / metrics、runtime = Claude Code 本体 / hooks / MCP / agent loop
3. `## 6 問`（A–F、各 1–2 行）— 層 / なぜモデル外 / 次世代で不要か / runtime 交換で残すか /
   インフラか差別化か / より単純な層へ移せないか（移送例 5 行: agent loop → model、workflow → skill、
   runtime 条件 → policy、prompt 品質判定 → eval、埋め込み知識 → data）
4. `## 強く疑う対象` — ユーザー列挙 13 項目をそのまま（自動否定ではなく疑う、と前置き）
5. `## 出力` — 規模に応じて 1 行〜。必要時のみ 5 見出し
   （Classification / Keep outside model because / Portability / Obsolescence risk L-M-H / Recommendation）。
   **毎回全 checklist を出さない**と明記
6. `## 既存 verdict との接続` — 提案中 = 本 skill が答える。設置済み = stocktake へ証拠渡し。
   対応表（Delete → Retire/Dissolve、Move → Demote/Merge、Make temporary → `review-when:` / ADR Review-when に期限を書く、
   Defer → `.notes/TASKS.md` に `candidate`）
7. `## 適用外`
8. `## 失効条件` — git-workflow 様式。「substrate が層分解・可搬性判断を native に持ったら退役」
   「6 層の区分自体が崩れたら（例: eval と skill が融合）再設計」「本 skill が 150 行を超えたら自分に適用する」
9. `## Related` — architect / loop-design-check / generation-audit / 3 stocktake / rules-distill /
   agent-harness-construction / akc-cycle(Scaffold Dissolution) / ADR-0012・0015・0038（runtime 可搬性の先例）

### 意図的に入れないもの

- 固定 Phase / 毎回の全 checklist 出力 / 計測 script / 独自 verdict 台帳（results.json）
- 各層の詳細ガイド（portability.md・rules-distill・verify-bootstrap が既に持つ）
- モデル固有の behavioral instruction（「必ず〜せよ」の反復）
- 一般論（「harness は薄く」の説教）— 原則 6 行 + 質問 6 問に留める

### 配線（最小）

- `skills/implementation-chain/SKILL.md` の Chain Matrix / タスク種別判定に 1 行: harness 自体
  （`~/.claude` の rules / skills / hooks / agents / settings）を変更する task は Plan 段階で
  skill: `harness-boundary` を通す（条件 = 対象 path が harness 資産。重い chain ではなく 1 行の参照）
- `skills/agent-harness-construction/SKILL.md` に `## Related` を新設し双方向接続（孤立解消）
- `skills/generation-audit` / 3 stocktake の Related に 1 行ずつ「設計時の層判断は harness-boundary」
- rules には**書かない**（常駐基準「環境固有の事実・配線・罠」に該当しない。ADR-0035）
- ADR: 書かない。先例（loop-design-check / wait-what / x-draft）どおり lens skill 単体で出す。
  ただし本 skill は harness 設計方針を含むため、著者が望めば後から `adr-writer` で起票可。
  `.notes/TASKS.md` に記録行は不要（完了物なので）

## Verification

1. `python3 scripts/hooks/harness_lint.py --root ~/.claude` → exit 0（frontmatter 3 keys、name == dir、`See skill:` 解決）
2. `bash .claude/verify.sh --staged` を commit 前に通す（Markdown のみなので lint + markdownlint advisory）
3. description の YAML 検証: `python3 -c "import yaml,sys; yaml.safe_load(open('skills/harness-boundary/SKILL.md').read().split('---')[1])"`
4. 自己適用テスト: 本 skill 自身に 6 問を当てて 1 段落で答え、本文末尾に置かず会話で報告する
   （期待: 層 = values/policy + skill の境界、obsolescence = Medium、Recommendation = Keep with 失効条件）
5. 発火確認（軽量）: 本セッションで「この hook をハーネスに足していい？」型の質問を 1 つ投げ、
   skill が参照されるかを確認（skill-comply のフル計測は不要 — 自発上限 40% の先例）

## 完了報告に含める 6 点

1. 確認した既存資産（上表）
2. 新 skill（統合しなかった理由 3 点）
3. 中心原則（6 行 + 1 行）
4. 発火場面（description の Use when + implementation-chain 配線）
5. 入れなかったもの（上「意図的に入れないもの」）
6. 交換耐性の理由: Markdown の判断原則のみ、runtime API / hook 機構 / script 非依存、
   verdict 正本を持たず既存台帳へ接続するだけなので、Claude Code 固有部分がゼロ

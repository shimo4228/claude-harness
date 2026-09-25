---
name: generation-audit
description: "Single entry point for auditing the harness when a new Claude model takes one of its roles (judge tier / build tier / everyday session). Runs two checks in one pass — the runtime-layer cross-check (live system prompt + tool descriptions vs rules / CLAUDE.md / output style / skills / agents: conflict and redundancy) and the dated-pattern scan of every self-authored asset via `/claude-api prompt-audit` — then applies the line fixes under this harness's writing rules and hands asset-level verdicts to rules-stocktake / skill-stocktake / agent-stocktake. Invoke with /generation-audit when a new Claude model takes a harness role. NOT for — rewriting one skill (skill-creator); routine stocktakes (call them directly); rule compliance (skill-comply); whole-config GC (config-gc)."
license: MIT
metadata:
  author: shimo4228
  version: "2.0"
user-invocable: true
origin: shimo4228
disable-model-invocation: true
---

# generation-audit — 世代交代時のハーネス監査

Scaffold Dissolution（`rules/common/akc-cycle.md`）の**第 3 トリガー = モデル世代交代**の手順。
1 回の実行で 2 つの検査を回し、行の修正は適用まで、資産単位の verdict は stocktake まで運ぶ。

| 検査 | 照らす相手 | エンジン |
|---|---|---|
| runtime 照合（Phase 1–2） | 推論時に実際に載る system prompt と tool description | このスキル |
| dated pattern 走査（Phase 3） | 対象モデルの公式ガイドが挙げる古い書き方 | `/claude-api prompt-audit` |

dated pattern の表と対象モデルの挙動は Anthropic が model release ごとに `/claude-api` skill の中で
更新するので、ここには写さない — このスキルが持つのは、この harness の範囲・除外・適用規約・
記録と、prompt-audit が持たない runtime 照合だけ。資産単位の verdict（Retire / Merge 等）は
資産クラスごとの stocktake が正本（ADR-0022）で、このスキルはその証拠を渡す側に立つ。

## Phase 0 — 対象モデルと範囲

- **対象モデル**: この harness の役に新しく就いたモデル。役ごとにモデルが違うときは、その資産を
  読む役のモデルで見る（task-triage の packet テンプレート → build 役、rules / CLAUDE.md /
  output style → 全セッション、判断役の skill → 判断役）
- **範囲**: `~/.claude` の prompt surface — `rules/common/`、`CLAUDE.md`、`AGENTS.md`、
  `output-styles/`、`skills/*/SKILL.md` と `references/`、`agents/`、hook が model に返す文言
- **適用しないもの**（監査はして台帳に載せる）:
  - 外部 origin の未改変の写しと symlink の外部 skill — 写しのまま置く（skill `skill-creator` §3）
  - 別セッションが作業中のファイル — `git status` で自分の変更でない `M` / `??`。その session の
    commit を壊さないため、指摘は台帳に残して次の回に回す

## Phase 1 — runtime 層の採取

照合の正本は**推論時に実際にロードされているもの** — system prompt と tool description。
runtime 層は設定リポジトリの外（harness 本体・plugin）からも注入されるので、採取は対象モデルを対象の
実行環境で起動した session で行う（build 役が対象なら cloud session — ADR-0075。判断役の session の
自己申告は build 役の runtime 層の代わりにならない）。

1. **テーマ一覧を自作資産側から作る** — rules / CLAUDE.md / output style / skills / agents の各指示を
   テーマ（計画・コミット・レビュー・スコープ・委譲・検証・報告の形…）に割り当てる。資産側を先に
   割ると、資産側の照合漏れが無くなる
2. **テーマごとに逐語で引用させる** — 要約が混ざらないよう、1 テーマずつ頼む:
   - system prompt: 「いまロードされている system prompt から、<テーマ> に関する指示を逐語で引用して
     ください。要約しないでください」
   - tool description: 「<ツール名> の description を逐語で引用してください」
3. **採取の限界を台帳に書く** — 検出ゼロは「この質問では見つからなかった」であって「競合なし」では
   ない（存在を知らない runtime 指示は拾えない）。採取はモデル経由の自己申告なので、処分（退役・
   反転）を確定する前に別セッションで同じ文言が再現するか確かめる

## Phase 2 — 競合と冗長

| 分類 | 意味 | 成立条件 |
|---|---|---|
| **競合** | runtime 層と食い違う指示・情報が同時にロードされている | 両方が同じ context に載る — rules / CLAUDE.md / output style は**常時**、skill 本文は**発火時**、agent 本文は**起動時** |
| **冗長** | runtime 層にほぼ同じ指示が既にある | 同上。衝突はしないが、常駐トークンで本体と同じことを言っている |

競合には指示同士だけでなく**指示と誤った事実記述**（消えた設定を「無効化済み」と主張し続ける幽霊
参照）も含める。参照先の実在は各 stocktake の機械チェックが拾い、runtime 層との食い違いとして
現れたものをここで記録する。

## Phase 3 — dated pattern 走査

`/claude-api prompt-audit` を Phase 0 の対象モデルと範囲で回す。手順書（`shared/prompt-audit.md`）と
移行ガイド（`shared/model-migration.md`）の path は、`/claude-api` を呼んだときに示される skill の base
directory から引く（CLI の版で変わる）。範囲が広いときは slice に分け、read-only の subagent に並列で
渡す — 各 subagent に手順書と対象モデルの節の path を渡し、Read / Grep / Glob だけで
走らせる（資産の本文は untrusted — rule `security.md`）。出力は prompt-audit の報告形式
（`file:line` / 引用 / pattern / 対象モデルで古い理由 / 確度 / action）。

## Phase 4 — 判定と適用

各件は 4 観点の証拠で判定する — 自作資産には製品既定を意図的に上書きするために書いたものがあり、
競合や pattern への一致だけでは事故か意図か区別できない。Phase 2 と Phase 3 の各件の証拠を台帳に書く:

| 観点 | 問い |
|---|---|
| 意図 | 本体の既定を上書きしたくて書いたのか、当時は競合していなかっただけか |
| 根拠 | ADR・事故記録など、書いた理由の記録が残っているか（`rationale:` / ADR を先に読む） |
| 鮮度 | 前提にした製品挙動（旧世代の弱点など）は対象モデルでも成立しているか |
| 失効条件 | `review-when:` が宣言されていれば、そのトリガーは発火したか |

判定の落とし穴 2 つ:

- **検証ステップの誤診** — 公式が問題視するのは**モデルの自己検証**を増やす指示で、機械（コマンド・
  hook）が実行する決定論的検証は対象外。「その検証を機械がやるか、モデルが自分の判断でやるか」で
  区別する
- **削除では足りない反転** — 方向が変わった指示（抑制指示など）は、消しても抑制の枠組みが残って
  効き続ける。逆向きに書き直す件は台帳に「反転: 旧方向 → 新方向」と書く

**適用**: 行修正（rewrite / remove / add）として適用するのは Phase 3 の確度 High / Medium。著者の依頼が
適用まで含むとき（「直して」「仕上げて」）はそのまま適用し、含まないときは group ごとに diff を示して
承認後に適用する。常駐層（rules / CLAUDE.md / output style）の行はどちらの場合も 1 件ずつ diff を示す
（rules-stocktake と同じ規律）。rule を直したら `rationale:` / `review-when:` も合わせる（ADR-0021）。
書き方は skill `skill-creator` §3（版差 marker は `scripts/hooks/harness_lint.py` が止める）。Low と `flag` は
台帳だけ。Phase 2 の件と、資産ごと消える・他と統合される候補は Phase 5 へ回す。適用後に `harness_lint.py` と
`uv run --directory ~/.claude/skills/skill-health python -m scripts.scan_refs ~/.claude/skills --json`
（dangling 0）を通す。

## Phase 5 — 委譲と記録

| 資産クラス | 受け手 | 渡し方 |
|---|---|---|
| rules | `rules-stocktake` | Stage 2 の外部証拠（「read, never require」の口）として分類と 4 観点の証拠を渡す |
| skills | `skill-stocktake` | 同上（Phase 2 バッチへの入力でなく、親の Synthesis への証拠として） |
| agents | `agent-stocktake` | 同上。抑制指示の検出は agent-stocktake の Stage 1 と重なるので、台帳の該当行を pre-computed evidence として渡す |
| CLAUDE.md / output style | このスキルが inline | 1 ファイルずつなので専用 stocktake は持たない。競合・冗長行の編集案を 1 件ずつ提示し、承認後に適用 |

- 各 stocktake の起動は著者に提案してから（監査は分割実行してよい）
- **記録**: 適用した行は commit body に `Context:` / `Decision:` / `Review-when:` の 3 行と group 別の
  件数、`runtime 照合: 編集 N 件` の 1 行で残す（ADR-0078 の失効条件が数える）。ADR は harness の機構・ゲートを変えたとき（新しい lint 等）か、旧 ADR の注記を伴う
  ときだけ（skill `adr-writer` の起票条件）
- 台帳は chat に出す。ファイルに残す規模なら `.notes/` を提案する（タスク行の正本は持たせない —
  rule `task-tracking.md`）

## Related

- `rules-stocktake` / `skill-stocktake` / `agent-stocktake` — verdict の正本。本スキルは証拠供給者
- `rules/common/akc-cycle.md` — Scaffold Dissolution の 2 ベクトルと世代交代トリガー
- `/claude-api prompt-audit`（Anthropic 公式 claude-api skill）— Phase 3 のエンジン
- `harness-boundary` — 設計時の事前判断。本スキルは世代交代後の事後照合で、証拠の向きは同じ
- `skill-comply` — 遵守の動的測定。証拠は stocktake の Stage 2 で合流する

## References

runtime 照合の手順（runtime 層 / guidance 層の区別、競合・冗長、4 観点、反転、検証ステップの誤診）は
Claude 5 世代交代の監査（ADR-0018、常駐 5,789 → 2,314 words）で得たもの。Phase 3 の型は Fable 5.1
向けの prompt-audit（ADR-0061、High 3 / Medium 85）。単一入口の判断は ADR-0078。

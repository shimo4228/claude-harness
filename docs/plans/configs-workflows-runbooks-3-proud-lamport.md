# Plan: `repo-asset-stocktake` skill

## Context

**問題**: リポジトリには、価値を失ったのに残り続ける非コード資産がある — 起動されなくなったツール設定（例: 誰も走らせない `.textlintrc`）、参照切れ/恒偽トリガーで機能しない GitHub workflow、記述対象プロセスが retired な runbook 等。これらは既存ツールの網から漏れる。

**なぜ既存で埋まらないか**（2 回の外部調査 + harness 内調査で確定）:
- **構造レイヤー(a)** — MegaLinter / super-linter / repolinter が YAML 妥当性・dead-link・unused-dep を検出。コモディティ。だが測るのは *構文品質* で *価値* ではない。
- **意味レイヤー(b)** — 「この資産はまだ意味を持って存在に値するか」の判断。単一既製品なし（Dosu は docs-drift 限定・商用 SaaS、Repo Doctor は未成熟）。**これが本当の gap**。
- **harness 内** — 「LLM が資産クラスを価値監査 → Keep/Retire verdict → human-gate」という stocktake 機構は既に4回実装済み（config-gc / rules-stocktake / skill-stocktake / context-sync）。欠けているのは *機構* でなく *対象*: プロジェクト repo の非コード資産に向けた instance だけが無い。

**意図する成果**: `skill-stocktake` / `rules-stocktake` の sibling として、プロジェクト repo の非コード資産を「価値が薄れていないか」で棚卸しする user-invocable skill。**スコープは configs/workflows/runbooks の3例に限定しない** — 「あらゆる非コード資産には consumer がいる。consumer が消えた/資産が consumer に奉仕しなくなったら review 候補」を core 原則とし、3例は拡張可能な seed カテゴリとして提示する。

**確定した設計判断**（ユーザー承認済み）:
- tier-1 決定論スキャン = **inline grep/find、新規外部依存なし**（stocktake ファミリーの「単一 context・no script」設計に合わせる。MegaLinter shell-out は前案から撤回 — 型を壊し、判断軸が構文品質にズレるため）。
- skill 名 = **`repo-asset-stocktake`**。

## Design: two-tier（harness の when-code-when-llm 原則 = enumerate/decide 分割）

- **tier-1（code, inline）**: consumer-reachability を決定論的に列挙。gray-zone を絞る pre-filter。
- **tier-2（LLM, holistic）**: 絞られた候補だけに「まだ意味があるか」の価値判断 → verdict。数値スコア無し。

### Consumer 型タクソノミー（seed = 拡張可能、3例に限定しない）

| consumer 型 | seed 資産 | tier-1 reachability チェック（inline） |
|---|---|---|
| **tool-invocation** | `.textlintrc` 等ツール設定 | ツール名を `package.json` scripts / `.pre-commit-config.yaml` / `Makefile` / CI で grep。起動サイト0件 = 候補 |
| **CI-trigger** | `.github/workflows/*.yml` | `uses:`/`run:` の参照 action/script が実在するか parse。`on:` トリガー到達性・`if: false` 恒偽・重複を検出 |
| **human-navigation** | runbook / docs | inbound-link グラフを grep（`[..](path)`）。他 doc/README からの参照0件 = 候補 |
| _（拡張）_ | issue/PR template, dependabot/renovate 設定, governance ファイル等 | 各 consumer に応じて定義。skill は一般原則を述べ新カテゴリを歓迎 |

**mandatory-surface rule**: tier-1 reachability がゼロ（起動サイト0 / 全参照 dead / inbound-link0）の資産は、最低でも Retire 候補として **必ず surface する**（rules-stocktake の absorption rule・skill-stocktake の zero-usage rule と同型）。

### Verdict タクソノミー（skill-stocktake の集合に整合、asset 向けに調整）

`Keep`（consumer live + 内容有意）/ `Update`（consumer live だが内容 stale → refresh・トリガー修復）/ `Retire`（consumer 消失 or 形骸化 → 削除）/ `Merge into [X]`（重複・superseded → 統合）。

## Files to create

**単一ファイル skill**（tier-1 が inline なので `scripts/` 不要。skill-creator の「繰り返し work が出たら script 抽出」ヒューリスティックに従い、reachability スキャンが repeat したら後から `scripts/asset_scan.py` に抽出）:

- `~/.claude/skills/repo-asset-stocktake/SKILL.md` — 新規作成。
- `~/.claude/skills/repo-asset-stocktake/results.json` — **runtime 生成**（作成時は書かない。lean ledger）。

### SKILL.md 構造（rules-stocktake / skill-stocktake の spine を踏襲）

1. **Frontmatter**: `name: repo-asset-stocktake` / `description`（末尾に NOT-for 境界節 + EN/JA トリガー句）/ `license: MIT` / `metadata: {author: shimo4228, version: "1.0"}` / `user-invocable: true` / `origin: shimo4228`。
   - ⚠️ description 内の `: ` が YAML を壊す既知 gotcha（memory: reference_skill_creator_loop_gotchas）→ 作成後に YAML parse 検証。
2. **H1 + 一行 mandate + Design note**（two-tier の根拠 = when-code-when-llm）。
3. **Modes (`$ARGUMENTS`)**: `full`（default, repo 全体）/ `changed`（前回 `evaluated_at` 以降に変更された資産のみ再評価、`find -newermt`）。REPO_DIR は引数 or cwd（portability — 個人 repo URL を埋めない）。
4. **Phase 1 — Inventory + tier-1 reachability**: 資産を Glob 列挙 → consumer 型ごとに inline grep/find で reachability 計測。「detection は structural → code」を明記。
5. **Phase 2 — Evaluation（inline, holistic）**: Stage 1 binary screen（Yes/No、No のみ surface）+ Stage 2 verdict pressure-test（非 Keep に 1–3 反証質問）+ verdict-meaning 表 + mandatory-surface rule。数値スコア禁止。
6. **Phase 3 — Summary**: 単一テーブル `Asset | Consumer | Reachability | Verdict | Reason`。
7. **Phase 4 — Consolidation**: config-gc の `[y/n/skip]` confirm-each（never batch）。Retire は **soft-delete 先行**（`.disabled` rename → trash、coding-style.md Reversibility Gate: 自律 hard-delete 禁止）。Update の機械的修正（トリガー修復・ref 修正）は confirm 後 inline 適用、prose 重い runbook 改稿はユーザー/writing skill へ委譲。
8. **Reason quality (required)**: 自己完結 reason、verdict ごと Bad/Good 例。
9. **results.json (lean ledger)**: inline JSON schema、`evaluated_at`（`date -u`）、`changed` mode は前 verdict を carry-forward。
10. **Related（境界明記）**:
    - `refactor-clean` — **code-consumed** データの *構造的* dead-consumer sweep（consumption edge が有るか＝binary）。本 skill は **non-code-consumed**（tool/CI/human consumer）を *意味的 value* で判断（edge が有っても「まだ意味があるか」を問う。例: 発火するが no-op の workflow、link されているが dead プロセスの runbook）。
    - `context-sync` — 4 doc-role の *配置重複 + code 鮮度*。本 skill は doc に限らず非コード資産全般の *価値*。runbook は overlap 域だが、context-sync は「役割が正しく code と整合か」、本 skill は「まだ実在する何かを記述しているか」。
    - `config-gc` — `~/.claude` harness 設定の GC。本 skill は **プロジェクト repo**。対象ディレクトリが別。
    - `skill-stocktake` / `rules-stocktake` — 同一 stocktake 型・別資産クラス（skills / rules）。本 skill は repo 非コード資産の sibling。
    - `harness-sync` — `origin: shimo4228` skill を公開 repo に同期。
11. **References**: ファミリー共通の学術行（BinEval arXiv:2606.27226 / CheckEval arXiv:2403.18771 / TICK arXiv:2410.03608）= binary-question 分解を score 集約なしで正当化。

## Chain（種別: feat — 新規 skill）

- **Doc Sync**: 本 skill は `-stocktake` ファミリー新設 → `skills.md` の Knowledge Placement / `config-gc`・`skill-stocktake`・`rules-stocktake` の Related 相互リンクに sibling 追記（同一 diff）。ADR 級の設計判断（gap の存在・harness 内 Compose 選択・MegaLinter 撤回理由）は adr-writer で ADR 化を検討。
- **Review**: code-reviewer（SKILL.md は prose だが構造/コマンド含むため）。security-reviewer は該当薄（外部書き込み・secret なし、soft-delete のみ）→ `-`。
- **Verify**: (1) YAML frontmatter parse 検証（gotcha ガード） (2) `/repo-asset-stocktake` トリガー確認 (3) 実 repo で smoke（下記）。

## Verification（end-to-end）

1. **YAML 健全性**: `python3 -c "import yaml,sys; yaml.safe_load(open('.../SKILL.md').read().split('---')[1])"` で frontmatter parse。
2. **トリガー**: `/repo-asset-stocktake` がスラッシュ起動する（`user-invocable: true`）。
3. **Smoke（full mode）**: 実 repo（例: `~/MyAI_Lab/g-kentei-ios` か harness repo 自身）で実行し、
   - tier-1 が実在候補を挙げる（孤立設定 / 参照切れ workflow / inbound-link0 doc のいずれか）、
   - tier-2 が verdict 表を出す、
   - Phase 4 が `[y/n/skip]` を1件ずつ出す（batch しない）、
   - `results.json` が `evaluated_at` 付きで生成される。
4. **境界確認**: 同じ入力で refactor-clean / context-sync が出す指摘と重複しない（構造 dead-code や doc-role でなく、非コード資産の *価値* を返す）。
5. **changed mode**: 資産1件を touch → `changed` 実行が当該のみ再評価し他は前 verdict を carry。

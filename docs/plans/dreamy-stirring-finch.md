# スキル・ルール文言 vs システムプロンプト矛盾調査 — 修正プラン

## Context

スキル・ルールの文言見直しの一環として、現行システムプロンプト（Claude Fable 5 世代）と
矛盾・陳腐化した記述を全数調査した（rules 14 ファイルは直接照合、skills 61 + learned +
agents 21 は Explore agent 3 並列）。akc-cycle.md の「substrate が capability を吸収したら
rule を退役させる」原則の実行。**明確な矛盾 7 件、陳腐化 10 件強、緊張 5 件**を検出。
本プランはうち編集する範囲と保留する範囲を確定する。

## ユーザー決定済み事項

1. **Attribution（git-workflow.md:Note 行 + release-doi/SKILL.md:171)**: 設定実体が
   settings.json に存在しないまま「disabled 済み」と記述。→ **今回は調査のみ・保留**（編集しない）
2. **coding-style.md Reversibility Gate「作成 (やや不可逆) — 新規ファイル / ディレクトリは
   確認してから」**: → **行ごと削除**（作成の区分を消し、システムプロンプトの可逆性判断に委譲）

## 編集計画

### P1. Rules 層（behavior-shaping — コミット前に本文 diff を提示）

| ファイル | 変更 |
|---|---|
| `rules/common/coding-style.md` | Reversibility Gate の「**作成 (やや不可逆)** — 新規ファイル / ディレクトリは確認してから」の行を削除 |
| `rules/common/task-tracking.md` | 台帳解決順序 3 の「（Reversibility Gate:「新規作成は確認してから」）」引用が宙に浮くため、「（作成は task-stocktake skill がユーザー確認の上で行う）」等、rule 引用なしの文言に修正 |
| `rules/README.md` | 編集後に `wc -w` を再実測し、words 数の記載を更新（実測値の宣言なので） |

### P2. Skills / agents — 機能影響のある明確な矛盾（優先）

| # | ファイル:行 | 問題 | 修正 |
|---|---|---|---|
| 1 | `skills/skill-comply/prompts/spec_generator.md:44,80` | ツール名列挙に `Task`, `TodoWrite`（不存在）— compliance 判定の spec に stale 名が焼き込まれ測定精度に直結 | `Agent`, `TaskCreate` 等の現行名に更新。:80 の Good 例も書き換え |
| 2 | `skills/skill-comply/scripts/runner.py:19` | `ALLOWED_MODELS = {haiku, sonnet, opus}` — 現行最上位 `fable` を指定できない | `"fable"` を追加。SKILL.md:47,76-78 の 3 択前提の記述も追随 |
| 3 | `skills/learn-eval/knowledge-placement-decision.md:35,45,49` | 「MEMORY.md に 1-2 行本文を書く」— 現行メモリ仕様（MEMORY.md はポインタのみ、本文は memory/ 1 事実 1 ファイル）と矛盾。同ファイル内で新旧仕様が混在しメモリ汚染を誘発 | 「memory/ に小ファイルを作り MEMORY.md にはポインタ 1 行」へ統一 |
| 4 | `skills/skill-creator/SKILL.md:375,446,447` | `/tmp` 直書き ×3（scratchpad 指針と矛盾） | 「session scratchpad ディレクトリ」表記に置換。:490 の `TodoList` 名指しも現行 task tools 表現に |
| 5 | `agents/planner.md:30-32` | 「nested Agent calls are not supported」— 現行は Agent-in-Agent 可能。誤った制約で Phase 0 の迂回手順を強制 | Note と迂回手順を削除し、planner が scout を直接起動できる前提に書き換え |
| 6 | `agents/codemap-writer.md:154` | bash 手順に `/tmp/new-$f` ハードコード | scratchpad パスに置換 |
| 7 | `agents/fact-checker.md:132` | ソース優先順位 4 位が「MEMORY.md = session end に書かれる本文」前提 | 「memory/*.md 個別ファイル（MEMORY.md は索引）」に修正 |

### P3. R2 決定（作成ゲート削除）の波及 — 確認要求の緩和

ルール行の削除に合わせ、同じ規範を実装していた skill 側ゲートを整合させる:

| ファイル:行 | 現状 | 修正方向 |
|---|---|---|
| `skills/task-stocktake/SKILL.md:19` | 台帳新規作成前に「ユーザーに確認してから」 | 「作るか」は聞かず、**置き場所**（.notes/ を git 管理するか等）だけ確認する形に絞る |
| `skills/update-codemaps/SKILL.md:61,107` | diff>30% で確認待ち / 再生成前に確認 | 61: 差分を報告して続行（git で戻せる旨併記）。107: 新鮮ならスキップして報告のみ |
| `agents/codemap-writer.md:159` | 「>30% は wait for caller confirmation」 | 上と同方向に緩和 |
| `skills/adr-writer/SKILL.md:40`, `skills/context-sync/SKILL.md:51` | 新規ファイル・ディレクトリ作成時の確認 | 削除済みルールへの依拠なら緩和（編集時に文脈を読んで判断。ADR 新規作成は依頼範囲内なので自動作成可） |

### P4. 軽微な陳腐化 — 注記追加・小修正

| ファイル:行 | 修正 |
|---|---|
| `skills/skill-creator/references/schemas.md:228` | `"claude-sonnet-4-20250514"` 例示 → 世代非依存の書き方（`analyzer_model` と同様）に |
| `skills/config-gc/SKILL.md:38` | Scheduled jobs の所在「wherever the user keeps them」→ CronList / routines を正とする記述に |
| `skills/learned/claude-code-headless-automation.md` | 冒頭に 1 行注記「in-session の定時実行は現行 CronCreate / ScheduleWakeup を先に検討（本ノートは外部 launchd 経路の記録）」— 歴史記録なので本文は書き換えない |
| `skills/learned/claude-code-self-generation-over-api.md:103` | 「自動化: 不可」セルを「ハーネス内スケジュール機構で可（CronCreate 等）」に修正（判断表の誤りは意思決定を歪めるため注記でなく修正） |
| `skills/learned/parallel-subagent-batch-merge.md:43` | 擬似コードの引数名を現行 Agent ツールのスキーマ（`model`, `run_in_background` は実在するので実は概ね正 — 編集時に実スキーマと突き合わせて最小修正） |
| `skills/harness-sync/SKILL.md:68` | main 直コミットが意図的である旨を 1 行明記（branch-first 不適用の理由） |
| `agents/adr-writer.md:135` | 「Do not stage in /tmp」→ scratchpad への言及に更新 |

### 保留・報告のみ（編集しない）

- **Attribution 系**（git-workflow.md / release-doi:171）— ユーザー決定により保留
- **`skills/mcp-builder/`**（evaluation.py の `claude-3-7-sonnet-20250219` 既定 ×3 箇所）—
  未改変 `anthropics/skills`。編集すると `-customized` 昇格が必要で diff 比較性を失う。
  **推奨: 上流の更新を取り込む方が筋** → 保留し報告に記載
- **`skills/security-scan/SKILL.md:90`**「Opus 4.6 Deep Analysis」見出し — 未改変 `ECC`。
  外装的な見出しのために customized 昇格するコストが見合わない → 保留
- **skill-comply の Haiku タイムアウト実測値**（SKILL.md:76-78）— 前世代での実測。
  再計測してから書き換えるべきで、文言だけ先に変えない
- **spawn-session:25**（公式 RC はモバイルから新セッション不可）— 外部プロダクトの能力主張。
  要実機検証、スキル存廃に直結するため今回は触らない
- **contemplative-axioms.md** — verbatim 研究資料。意図的配置と判断し現状維持
- **planning.md 介入点 1 と native plan mode の紐付け** — 矛盾ではなく参照不足。
  今回のスコープ（矛盾解消）から外し、次回 rules-stocktake の議題に
- **ECC 由来 agent 群の英語出力テンプレート** — 無害（親セッションが日本語で要約する運用）
- **prompt-writer の haiku pin / write-prompt の存在意義**（「メインモデルの考えすぎ回避」が
  Fable 5 世代でも成立するか）— 存廃判断はスキル棚卸しの議題であり今回は触らない

## Origin 取り扱い

- 編集対象のうち外部 origin: `planner.md` / `config-gc` / `update-codemaps`（ECC-customized 済み）、
  `skill-creator`（anthropics/skills-customized 済み）→ そのまま編集可
- shimo4228 / auto-extracted origin → 制約なし
- 未改変外部 origin（mcp-builder, security-scan）は上記のとおり**編集しない**

## 検証

1. 再 grep: `grep -rn "TodoWrite\|Task tool" skills/ agents/ rules/` が 0 件（意図的な歴史注記を除く）、
   `grep -rn "/tmp" skills/*/SKILL.md agents/*.md` が 0 件（skill-comply sandbox の意図的隔離は
   コメント付きで残すか scratchpad 配下へ — 編集時判断）
2. frontmatter を触ったファイルは YAML パース検証（learned gotcha: description の `: ` が YAML を破壊）
3. `python3 -c "import ast; ast.parse(open('skills/skill-comply/scripts/runner.py').read())"` で構文確認
4. rules/README.md の words 実測値更新（`wc -w rules/common/*.md`）
5. コミットはユーザーの指示があってから。rules / skills は behavior-shaping artifact のため、
   human-gate.md に従い**コミット前に本文 diff を提示**する。なお attribution 保留中のため、
   コミット時の trailer の扱い（現行ハーネスは Co-Authored-By を付ける指示）はその時点で確認

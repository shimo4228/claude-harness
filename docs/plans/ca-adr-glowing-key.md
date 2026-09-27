# ADR lint + 書き手側予防チェック + review→lint 吸収の汎用 skill 化プラン

2 部構成: **Part 1** = ADR の具体実装（lint script + 予防カタログ + reviewer 薄化）。
**Part 2** = その手続きを汎用 skill `review-to-lint` に蒸留し、他のレビュアーへ水平展開可能にする。
Part 1 を先に実装する — 動く実例（readme_evidence.py に次ぐ 2 例目）を持ってから一般化する
（feedback: abstraction_trap — 一般化しても行動変容を起こせるかは実例で検証してから）。

## Context

adr-reviewer（opus agent）は現在、機械判定可能なチェック（7 節存在・Review-when 有無・Status 語彙・Date 書式）と意味的チェック（後付け正当化・藁人形・片面 Consequences）を両方持つ。前者は決定論化できる（feedback: deterministic/semantic layering）。ADR-0044 Decision #5 が既に「存在 = code、内容 = LLM」の分業を引いており、`harness_lint.py` に `lint_adr_review_when` が 1 本ある。

CA (contemplative-agent) には ADR 98 件とレビュー修正の git 履歴があり、頻出指摘パターンが抽出済み（調査結果は下記「頻出指摘カタログの素材」）。CA のテンプレは 7 節目が `References`（harness は `Review-when`）で、repo ごとにテンプレが違う事実が lint 設計の制約。

方針（ユーザー合意済み）: **全置換ではなくハイブリッド** —
1. 機械チェックを script に抽出（cross-repo で動く単一正本）
2. adr-writer skill に頻出指摘の予防チェックを追加（書き時の上流予防）
3. adr-reviewer は薄くして存続（意味的・敵対的チェック専任、script の JSON を入力に取る）

配置は **skill 内単一 script** を採用（AskUserQuestion はユーザーが省略を選択、推奨案で進行）:
harness_lint.py 拡張だと ~/.claude 専用で CA に届かず、両方だと二重実装で drift する。

## search-first 照合（as-of 2026-08-26）

ADR に単一の拘束的標準は無い — Nygard 形式（2011、Title/Status/Context/Decision/Consequences）が事実上の最小形、[MADR](https://adr.github.io/adr-templates/) が最も構造化された現行テンプレ族。本 harness の 7 節は Nygard 拡張（+ Review-when + Alternatives Considered）で、どの外部標準の schema にも一致しない。

lint 既存ツールの照合: [adrkit](https://github.com/mbeacom/adrkit)（2026、lint/CI/MCP 搭載、MADR superset）が最有力候補だが、**YAML frontmatter（id/status/reversibility/blastRadius/affects）必須**で、frontmatter を持たない自前テンプレの 300+ 件（18 repo）は全件移行が要る。Review-when 境界・注記形式・index drift 等の自前規約は対象外。pre-1.0 + Node 22 依存。→ **自作を採用**し、adrkit は ADR-0051 の Alternatives Considered に却下理由つきで記録（再訪条件: 自前テンプレを MADR 系へ寄せる判断をしたとき）。

## Part 1: ADR の具体実装

### Step 0: skill-creator を読む

adr-writer skill の大幅改修 + Part 2 の新規 skill 作成に当たるため、rules/common/skills.md の配線に従い skill: `skill-creator` を先に読む（intent packet と草稿ゲートの規約に従う）。

### Step 1: `skills/adr-writer/scripts/adr_lint.py` 新設（唯一の正本）

readme-writer の `skills/readme-writer/scripts/readme_evidence.py` パターン（uv sub-project: pyproject.toml + tests/）に倣う。stdlib のみ。

**2 モード**:
- 既定 = **evidence モード**: JSON を stdout に出す。判定しない・exit 0（"evidence, not a verdict"）
- `--gate` = **blocking モード**: 違反を stderr + 非ゼロ exit（harness の verify.sh 用）

**テンプレ適応**: 対象 repo の `docs/adr/README.md` の `## Template` fenced block から期待節セットを読む。無ければ harness 7 節（Status / Date / Context / Decision / Review-when / Alternatives Considered / Consequences）を既定に。CA は References 節テンプレのまま正しく検査される。

**検査項目**（調査で実在を確認した逸脱パターンに対応）:
| 検査 | 実測根拠 |
|---|---|
| 節の存在（テンプレ由来セット。大小文字ゆれも検出） | CA に `## Alternatives considered` 2 件、zenn に Date 欠落 6 件 |
| Review-when の有無（`--require-review-when-from NNNN`、harness は 0044） | harness_lint 既存検査と同基準 |
| Status 先頭語が enum（accepted / superseded / deprecated / proposed 等。**prefix 判定** — 散文続き 8 件を許容） | harness で散文続き 4+4 件が常態 |
| supersede 参照の表記ゆれ（`superseded-by 0030` / `superseded by ADR-0036` 等 4 表記並存の検出） | CA corpus 実測 |
| Date 書式 `YYYY-MM-DD` | 現状違反 0、退行防止 |
| index (README.md) とファイルの drift（行数一致・番号対応） | 現状 drift 0、退行防止 |
| 命名規則 `NNNN-slug.md`（4 桁ゼロ埋め）と番号衝突・欠番 | g-kentei-ios が `ADR-002-` 形式 |

**gate の免除境界**（既存違反で commit を止めないため）: 節存在チェックは `--sections-from NNNN`（harness は 0044 — 0009 の 2 節欠落を免除）、Status は prefix 判定。Date / index は全件（違反 0 のため安全）。

テスト: `skills/adr-writer/tests/test_adr_lint.py`（pytest）。verify.sh full mode が `skills/*/pyproject.toml` を自動発見するので配線済み。

### Step 2: harness の commit ゲート配線

`~/.claude/.claude/verify.sh` に 1 行追加:
```
check adr-lint python3 "$ROOT/skills/adr-writer/scripts/adr_lint.py" --gate --root "$ROOT" --require-review-when-from 0044 --sections-from 0044
```
staged / full 両モードに載せる（harness-lint と同じ扱い）。verify.sh の内容 hash が変わるため `scripts/hooks/verify_allow.py` の承認台帳更新が必要（人間承認フロー — 実装後にユーザーへ明示依頼）。

`harness_lint.py` の既存 `lint_adr_review_when` は**触らない**（ADR-0044 Decision #5 の配置。adr_lint と重複するが両者は同一規約の参照で drift しない。ADR に重複を明記）。

### Step 3: 頻出指摘カタログ `skills/adr-writer/references/review-findings.md`

CA の git 履歴 + harness ADR-0044 事例から蒸留した**日付・commit 参照つき事例集**。役割は「予防のための事例」であり、レビュー基準の正本は adr-reviewer のまま（二重定義にしない — 事例と基準で役割分離、相互リンク）。

収載する頻出パターン（調査で確認済みの実例つき）:
1. **引用した ADR の誤引用** — 引用先番号の実在と内容一致を書き時に確認（CA `0ce5430`: ADR-0072 誤引用の差し戻し）
2. **surviving scope の置き場所** — forward half は「自分が退役させたもの」だけ、生存 scope は backward half（CA `423c732`: 5 件中 4 件誤り → README 規約化）
3. **造語の出所** — 引用元に無い自作語を引用元の語として書かない（CA `008ac94`: "Step 0" は ADR-0026 に無い）
4. **full vs partial supersede の判定根拠** — コード実在で判定（CA `008ac94`: NOISE_THRESHOLD 等の不在を根拠に full と訂正）
5. **gitignored パス参照禁止** — `.notes/` 参照は evidence 昇格か文言書き換え（CA `25b88f9`: 20 箇所一括）
6. **数値の出典と分母** — adr-reviewer 基準 6 と同一（正本参照のみ）
7. **カウント条件の固定対象** — 「N 回連続」は何が固定なら比較可能かを名指し（harness ADR-0046 事例、2026-08-22）

### Step 4: `skills/adr-writer/SKILL.md` 改修

- Step 3（packet 組立）に「予防チェック」小節を追加: 上記カタログを読み、該当パターンを packet 確定前に自己点検（意味的レビューの代替ではない旨を明記）
- Step 4 の後に「Step 4.5: `adr_lint.py` を evidence モードで実行し、JSON の逸脱を修正」を追加
- Step 1 の新規 repo 向け index テンプレを harness 実形式に合わせる: ヘッダ `| ADR | Title | Status | Date |`・番号を相対リンクに（現状 `| ID |` リンク無しで drift している — 調査で確認）
- Reference Files に adr_lint.py と review-findings.md を追記

### Step 5: `agents/adr-reviewer.md` 薄化

- **§1 Section Completeness の機械項目を削除**し、冒頭に Post-script Interpretation 指示を追加: 「まず `python3 ~/.claude/skills/adr-writer/scripts/adr_lint.py --root <repo>` を実行し、JSON の機械的逸脱は結果に転記、レビューの注意は意味的チェックに集中する」（feedback: deterministic_semantic_layering の SKILL.md 様式）
- §1 のうち意味的な項目（Review-when が**観測可能**か、カウント条件の固定対象、Title が決定を述べるか）は残す
- 新規追加: 「対象 repo の `docs/adr/README.md` のローカル規約（テンプレ・supersede half 規約等）を読んで適用する」— CA のような harness 外 repo での運用を明示
- 意味的チェックリストに review-findings.md への参照を 1 行追加（事例は重複記載しない）

### Step 6: ADR-0051 起票（skill: adr-writer 使用）

決定の記録: 機械/意味の分業を ADR-0044 から拡張（存在チェックを cross-repo script に一般化、正本は skill 側）。ADR-0044 との関係は「補完・部分拡張」（supersede しない。harness_lint の既存検査は残置し重複を Consequences に明記）。Review-when 候補: 「adr_lint と lint_adr_review_when の判定が食い違う事象が起きたら重複を解消」。

### Step 7: 締め

- `.claude/verify.sh` full 実行（bats + pytest + 両 lint が通ること）
- git status 確認、doc sync（docs/adr/README.md の Template 前文に adr_lint.py への言及を追加するか確認）
- commit はユーザー承認後。verify.sh 変更の承認台帳更新を依頼
- 公開 repo への同期は skill: `harness-sync`（ユーザー起動、範囲外）

## Part 2: 汎用 skill `review-to-lint` の新設

### 目的

Part 1 で踏んだ手続き — 「reviewer のチェックリストから機械判定可能な項目を決定論 script に抽出し、reviewer を意味的チェック専任に薄化する」 — を再利用可能な user-invocable skill にする。既に 2 実例がある（readme-writer の `readme_evidence.py`、Part 1 の `adr_lint.py`）ので一般化の根拠は足りる。正当化の系譜: feedback_deterministic_semantic_layering（script 計測 + LLM 解釈）、ADR-0044（存在 = code、内容 = LLM）。

### 作成物

`skills/review-to-lint/SKILL.md`（origin: shimo4228、user-invocable: true）。skill-creator の草稿ゲート（fresh-context の named verdict）を通す。

### SKILL.md の設計骨子

**Use when**: 「このレビュアーを lint 化して」「レビューを lint に吸収」「機械チェックを script に降ろして」、または reviewer の指摘に機械的項目の反復が目立つとき。
**NOT for**: 新規 reviewer の作成（→ skill-creator）、意味的基準そのものの変更、judge 設計（→ llm-as-judge）、既に evidence script を持つ reviewer の再抽出。

**Workflow**（Part 1 の手続きの一般形）:

1. **棚卸しと分類** — 対象 reviewer のチェックリストを 3 分類する。分類基準が本 skill の核:
   - *deterministic*: 構造・書式・実在・一致の検査（節の有無、enum、日付書式、リンク解決、index drift、命名規則）→ script へ
   - *semantic*: 意図・忠実性・両面性・妥当性の判断（後付け正当化、藁人形、片面 Consequences）→ reviewer に残す
   - *hybrid*: script が計測し LLM が解釈（カウント条件の固定対象、数値の分母）→ script は evidence を出し、reviewer に Post-script Interpretation を書く
2. **search-first 照合** — 外部 lint ツールと harness 内の既存 evidence script を先に探す（Part 1 の adrkit 照合が先例。既存があれば書かない）
3. **script 設計** — 置き場所は当該ドメインの writer skill 配下 `skills/<owner>/scripts/`（cross-repo で動く単一正本）。既定 = evidence モード（JSON・判定しない・exit 0）、blocking が要る場合のみ `--gate`。**免除境界を先に実測する**: 既存 corpus に lint を当てて違反数を数え、prefix 判定・番号/日付境界でゲートを赤くしない形を決めてから書く
4. **reviewer 薄化** — 機械項目を削除し、冒頭に「script を実行 → JSON を転記 → 注意は意味的チェックへ」の Post-script Interpretation を配線。reviewer には repo ローカル規約（テンプレの正本）を読む指示を残す
5. **配線とテスト** — pytest（uv sub-project、verify.sh full が自動発見）。commit ゲートに載せるのは blocking が必要な repo のみ（verify.sh へ 1 行。承認台帳更新を依頼）
6. **記録** — ADR に分業（code/LLM の境界線）・重複箇所・免除境界を明記

**正本規則**（skill 本文に明記）: 検査ロジックの正本は script 1 箇所。reviewer は意味的基準のみ。頻出指摘の事例カタログは `references/`（基準と事例で役割分離、相互リンク — 二重定義にしない）。

### 水平展開の候補（skill 本文に例示として記載、実施は範囲外）

機械化余地の大きい順: **citation-formatter**（DOI/arXiv 実在・orphan 参照 — ほぼ全項目 deterministic）、**vocabulary-consistency-checker**（用語の定義位置と使用の grep 照合）、**editor / essay-reviewer の terminology consistency 項目**、**paper-reviewer の構造項目**。readme-reviewer 系は実施済み（readme_evidence.py）。

## 範囲外（明示）

- CA など他 repo への lint 配線（CA は自前の `test_adr_status_consistency.py` 等で既に厚い。adr-reviewer が ad hoc に script を実行する経路で足りる。必要なら別途）
- 既存 ADR の違反修正（0009 の節欠落、Status 散文 — 免除境界で対応、遡及修正しない）
- adr-reviewer の意味的基準の変更（薄化のみ）
- 水平展開の実施（citation-formatter 等への適用は `review-to-lint` skill 完成後、別セッションで 1 件ずつ）

## 変更ファイル一覧

| ファイル | 種別 |
|---|---|
| `skills/adr-writer/scripts/adr_lint.py` | 新規（正本） |
| `skills/adr-writer/pyproject.toml` + `tests/test_adr_lint.py` | 新規 |
| `skills/adr-writer/references/review-findings.md` | 新規 |
| `skills/adr-writer/SKILL.md` | 改修 |
| `agents/adr-reviewer.md` | 薄化 |
| `.claude/verify.sh` | 1 行追加（要承認台帳更新） |
| `docs/adr/0051-*.md` + `docs/adr/README.md` index | 新規 ADR |
| `skills/review-to-lint/SKILL.md` | 新規 skill（Part 2、skill-creator ゲート経由） |

## 検証方法

1. `pytest skills/adr-writer/tests/` — lint 単体（fixture: 正常 ADR / 節欠落 / 大小文字ゆれ / Status 散文 / index drift / CA 型 References テンプレ）
2. `python3 skills/adr-writer/scripts/adr_lint.py --root ~/.claude` — 既存 50 件で **違反 0**（免除境界の確認）
3. 同 `--root ~/MyAI_Lab/contemplative-agent` — CA 98 件で既知の逸脱（Alternatives considered 小文字 2 件等）を evidence として報告し、exit 0
4. `--gate` で harness に故意の違反 ADR を置き非ゼロ exit を確認 → 削除
5. `.claude/verify.sh`（full）が全て通る
6. Part 2: skill-creator の fresh-context 草稿ゲートで `review-to-lint` が Publishable verdict を得る。検収として SKILL.md の Workflow だけを見て Part 1 の adr_lint 実装が再現可能か（手順の自己完結性）を確認

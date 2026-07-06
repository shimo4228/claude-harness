<!-- origin: shimo4228 -->
# Planning Standards

提案・推薦・方針の提示など、ユーザーに判断を求める場面では、必ず以下を含めること。

## 各ステップに必須
- **What**: 何をするか
- **Why**: なぜそうするのか（理由・根拠）
- **Alternatives**: 他に検討した選択肢（あれば）

## 原則
- 「何をするか」だけのリストは不完全。必ず「なぜ」を添える
- トレードオフがある場合は明示する
- 前提条件・仮定があれば述べる

## Phase 0: External Research (Plan Mode)

計画のステップを書き出す**前に**、既存ソリューションを調査する。

**エントリポイントは `/search-first` skill の呼び出しに固定する**。WebSearch / scout を直接呼んで Phase 0 を済ませてはいけない — skill body が定める Step 0 (要件の text 出力) を skip すると、ユーザーに対する course-correct ウィンドウが閉じ、後段の Decide / Implement に必要な articulation が記録に残らない。scout は search-first の **Full Mode 内部** で起動される実装詳細であり、Phase 0 と等価ではない。

### トリガー条件

以下のいずれかに該当する場合、Phase 0 を実行する:

- 新機能で既存ライブラリ・ツールが存在しうる場合
- 新規依存の追加・技術選定
- ユーティリティ・ヘルパー・抽象化の新規作成

### スキップ条件

以下に該当する場合、Phase 0 を省略してよい:

- バグ修正、リファクタリング、設定変更
- プロトタイプ・スパイク（学習目的で本番コードでない場合）
- プロジェクト固有のビジネスロジック（外部解がありえない）

### 出力要件

計画に **External Research Findings** セクションを必ず含める。
内容: `/search-first` skill が返した Verdict (Quick Mode チェックリスト結果、または Full Mode で起動した scout の結果)。Verdict は skill 内部で確定するため、planning.md レイヤーでは "search-first を呼んだ" ことと "Verdict を受け取った" ことだけを保証する。

### Verdict に基づく判断

search-first skill が返した Verdict をそのまま計画の方向性に反映する:

| Verdict | 計画への影響 |
|---------|-------------|
| **Adopt** | そのまま採用。計画はインテグレーション中心に |
| **Extend** | 採用 + 薄いラッパー・設定の計画を追加 |
| **Compose** | 統合コストを評価してから計画確定 |
| **Build** | 自作する。何を調査し何が不適だったかを記録 |

### 構造的強制

Stop hook (`hooks/search-first-verdict-check.sh`, advisory) が Verdict の存在を検査する。
PreToolUse による hard 強制は非導入と判断（2026-07-06: false positive で実装が止まるコスト >
advisory + LLM 裁量の遵守率、が現時点の評価。enforcement は secret scan / ruff など
決定論的に判定できる箇所に限定して hook 化する方針）。

## 証拠ベースの意思決定

- アーキテクチャ判断・技術選定・API 設計には証拠を添える（ドキュメント、ベンチマーク、既存パターン）
- 「X が最適と思う」は不十分 →「X が最適。理由: [証拠]」
- 証拠が見つからない場合はその旨を明記し、仮定として扱う

## 機能要求のチャレンジ（複雑性を足す前に）

新機能・アーキテクチャ変更・依存追加・抽象化導入の前に、**実装方法でなく存在意義**を問う。
「そもそもこれは必要か / 誰が本当に求めているか / 解こうとする問題は実在するか」。
判断時は ROI を**時間見積もりで計算しない**（不確実）。代わりに 複雑性 × 価値 × 使用頻度（毎回/時々/稀）の表で代替案と比較し、同じ複雑性でより高い価値の選択肢がないか確認する。

**警戒すべきトリガーワード**（口に出たら一度立ち止まる）:
- 「将来のために…」→ YAGNI 違反の可能性
- 「きれいな設計だから…」→ 過剰設計（Architectural Vanity）
- 「せっかく調査したから…」→ サンクコストの罠（Research Justification）
- 「クレジット/予算が余ってる…」→ アンカリング（Credit Anchoring）
- 「すぐできる…」→ 時間ベース ROI の誤り

サンクコスト（調査・ドキュメント済み）は判断材料にしない。正しい問いは「今ゼロから始めるとして、これを優先するか？」。疑わしいときは architect に**忌憚ない本質評価**（実装可否でなく "build すべきか") を依頼する。

## 実行バイアス

- 直接的な実装指示には即座に実行する。plan mode に入らない
- 「〜を実装して」「〜を修正して」→ 即実行
- 「〜を検討して」「〜の方針を考えて」→ 計画モードが適切
- 指示が明確なのに過剰な質問をしない（最大1つまで）
- スコープが指定されたら厳守する（「scripts/ のみ」なら他は触らない）

### Prototype Before Scale

スケール実行（データ生成、自律ループ、API マイグレーション等）の前に:
1. 小規模トライアル（3-5件、1サイクル）を先に実行
2. トライアル出力から品質ベースラインを確立
3. ベースライン確認後にフルスケール実行

## Implementation Chain Specification

実装に着手する前に、タスク種別を判定し、対応する chain を **plan に front-load** する。
実装中は判定をやり直さず、定義済みの chain をそのまま実行する。
ユーザー介入点は **「Plan 確認」と「Verify 結果確認」の 2 点のみ**。

### タスク種別判定（最初の plan ステップ）

| 種別 | 判定基準 | 例 |
|------|---------|-----|
| `feat` | 新規機能・新規モジュール追加 | API 追加, 新ページ |
| `fix` | バグ修正（再現可能な不具合） | crash, 誤動作 |
| `refactor` | 振る舞いを変えない構造変更 | 抽出, 改名, 整理 |
| `chore` | 設定 / 依存更新 / コード付随の docs 追従 | settings, CI |
| `prototype` | 学習・スパイク・本番外コード | 検証スクリプト |
| `writing` | 文書自体が一次成果物 | README 改稿, 記事, 論文, llms.txt |

`prototype` を選ぶ場合は **「prototype として扱う理由」を plan に必須記載**（fix/feat の悪用防止）。

**README の種別判定**: README 自体の改善・書き直しが目的なら `writing`（Writing Chain → readme-writer）。コード変更に付随する README 追従更新なら従来通りコードチェーンの Doc Sync 内で扱う。

### Chain Matrix（種別 × ステップ）

各セルの値: `Y` 必須 / `C` 条件付き / `-` 省略可。

| ステップ | feat | fix | refactor | chore | prototype |
|---|:-:|:-:|:-:|:-:|:-:|
| Plan (planner) | Y | Y | Y | - | - |
| Phase 0 External Research | Y | - | - | - | - |
| TDD (tdd-guide) | Y | Y | - | - | - |
| Refactor Clean (refactor-cleaner) | - | - | Y | - | - |
| Code Review (code-reviewer / python-reviewer) | Y | Y | Y | C | - |
| Security Review (security-reviewer) | Y | C | - | C | - |
| Cross-Model Review (codex-review) | Y | Y | C | - | - |
| Doc Sync (context files) | C | C | C | C | - |
| Verify (build / types / lint / tests / secrets / doc sync / git status) | Y | Y | Y | Y | - |

**条件付き発火 `C` の発動条件**:

- `fix` × Security Review: 入力検証・認証・秘匿情報を触る fix のみ Y。ロジック誤り単独は `-`
- `chore` × Code Review: settings.json / hooks / permissions / CI 変更時のみ Y
- `chore` × Security Review: secrets 設定 / 認証関連 hook / permissions 変更時のみ Y
- `refactor` × Cross-Model Review: 公開 API / 並行処理 / セキュリティ境界に触れる高リスク refactor のみ Y。純粋な内部整理は `-`
- 全種別 × Doc Sync: 変更が以下のいずれかに該当する場合のみ Y。該当 doc を**同じ diff** で更新する（後追い PR にしない）
  - 機構・ゲート・閾値・段構成の変更 → CODEMAPS の Data Flow / architecture（プロジェクトに鮮度規約があればそれに従う）
  - ADR 新設・廃止 → knowledge graph（graph.jsonld 等）+ CODEMAPS 言及（両面更新）
  - パッケージ資産（プロンプト・シード・テンプレート・サービス定義）の増減 → 設定リファレンスの canonical 節
  - CLI / user-facing 挙動の変更 → README / llms.txt
  - 数値クレームの規律: 集約カウントの正本は 1 箇所のみ（他はポインタ）。機械検証可能な doc↔実体対応は prose 修正でなくテストで固定する（検出は code、削除判断は人間）

### Writing Chain（`writing` 種別のルーティング）

`writing` 種別は上の Chain Matrix を**使わない**。doc 分類を判定し、対応する orchestrator skill にルーティングする:

| doc 分類 | orchestrator skill |
|---|---|
| 記事 / エッセイ / newsletter（人間向け prose） | `writing-ecosystem` |
| 学術論文 / preprint / position paper | `paper-ecosystem` |
| README / repo トップページ | `readme-writer` |
| llms.txt 等 AI-doc | `llms-txt-writer` |

チェーン本体（agent 起動順・並列化・最終 gate）の**正本は各 skill の定義**（ここに複製しない）。
planning.md 層が規定するのは以下の糊のみ:

**Verdict マッピング**（writing agent の出力 → chain verdict への変換。構造化サマリの `Verdict:` 欄にはこの変換値を書く）:

| agent 出力 | chain 上の扱い |
|---|---|
| MAJOR ISSUES（editor / essay-reviewer / readme-reviewer） | CRITICAL → 停止 |
| ❌ INACCURATE（fact-checker） | CRITICAL → 停止 |
| DRIFT（source-fidelity-checker） | CRITICAL → 停止 |
| NEEDS REVISION（editor / essay-reviewer / readme-reviewer） | HIGH → 継続 + 修正 |
| readme_lint exit 1 / geo_check FAIL | Verify FAIL → 停止 |

**Cross-Model Review（条件付き）**: 公開・deposit 前の高 stakes 文書（公開 repo README / 論文 / 公開記事）のみ codex-review を Claude 側レビュアーと並列起動。**prompt-driven モード必須**（scoped モードはコード向け組み込み指示のため prose 不適）。private ドラフト・下書き段階は `-`。

**Verify 相当（writing 版）**: build / types / tests は非該当。代わりに (1) 決定論 lint（readme_lint.py / geo_check.py / textlint 等、doc 分類に該当するもの） (2) fact / citation gate（fact-checker verdict の出典編入、paper なら citation-formatter） (3) `git status` 確認。

**人間 gate**: 公開・deposit・commit 直前の diff 承認。2 介入点モデルの「Verify 結果確認」に対応する。

### 並列化指定（plan 時に確定）

実装中の判断分岐を排除するため、並列化を **plan 出力に明示**する。

- **作成系並列**: Phase 0 (`/search-first` 呼び出し) は独立 → planner と並列起動可。scout は search-first 内部で fan-out されるので、planning.md レイヤーでは並列単位として扱わない
- **レビュー系並列**: Code Review + Security Review + Cross-Model Review (codex-review) は同じ diff 対象 → **default で並列起動**
- **逐次必須**: TDD は Plan の後、Verify は全レビュー後（並列化禁止）
- **writing**: Parallel Group は orchestrator skill 側の並列原則に従う（例: editor + essay-reviewer + fact-checker 並列 / paper 4 reviewer 並列 → citation-formatter は逐次）。Parallel Group を plan 出力に明記するルール自体は writing にも適用

plan 出力に以下のフォーマットで記載:

```
Parallel Group 1: [planner, scout]
Parallel Group 2: [code-reviewer, security-reviewer, codex-review]
Sequential: TDD (Plan 後) → Verify (全レビュー後)
```

### 早期停止条件

以下を検出した時点で chain を中断し、ユーザーに報告する:

- Code Review / Security Review / Cross-Model Review (codex-review) が **`CRITICAL`** を返した
- Verify ステップで build / types / tests のいずれかが失敗
- `fix` で根本原因の仮説が証拠で支持されない（`debugging.md` 参照、唯一の例外的ユーザー確認待ち）
- Phase 0 (`/search-first`) で `Adopt` Verdict → 実装方針の再 plan を要請
- `writing` で Verdict マッピング表の CRITICAL 相当（MAJOR ISSUES / ❌ INACCURATE / DRIFT）を検出

### 要約出力の強制（context 圧迫防止）

各 agent の出力は **raw を保持せず**、以下の構造化サマリで親 context に戻す:

```
Agent: <name>
Verdict: <PASS | CRITICAL | HIGH | MEDIUM | LOW>
Findings (top 3): <one-line each>
Files touched: <path:line>
Next action: <continue | stop | re-plan>
```

raw 出力は agent 内部 / artifact に留め、親 context には引用しない。

### Review / Cleanup ステップ（実装直後・Verify 前）

実装が一段落したら、**Verify に進む前に**、変更内容・task 種別に応じて agent を**必ず起動**する（下の Chain Matrix は「どの種別で要るか」の早見表。ここは「実際に何を走らせるか」の本体）:

- **refactor-cleaner** — `refactor` 種別のとき（dead code / 重複の除去）
- **python-reviewer** — Python (`.py`) を変更したとき
- **code-reviewer** — Python 以外のコード（TS / Swift / shell 等）を変更したとき
- **security-reviewer** — 入力処理・認証・秘匿情報・permissions・hook を触ったとき
- **codex-review** — `feat` / `fix` で非自明な diff を実装したとき（cross-model 脱相関レビュー、read-only、code-reviewer / security-reviewer と並列）。**diff ベースのレビュアーなので plan 時には走らせない — plan には chain entry として列挙するだけで、実装後に diff へ走らせる。「実装差分が無い」を理由に plan（設計）を codex で直接レビューする即興代替をしてはならない**（その訂正待ちが本配線の発端）。

Code Review（python-reviewer / code-reviewer）・Security Review・Cross-Model Review（codex-review）は同じ diff が対象なので **並列起動**してよい。いずれかが `CRITICAL` を返したら chain を止めてユーザーに報告する（→ 早期停止条件）。

### Verify ステップ（chain 最終ステップ）

**Review 実行確認**: 直前の Review / Cleanup ステップ（refactor-cleaner / python-reviewer / code-reviewer / security-reviewer / codex-review）を変更内容・種別に応じて起動済みか確認する。未起動なら commit せず Review に戻る。

続けて以下を実行:

1. **build** — 該当言語のビルドコマンド
2. **type check** — mypy / pyright / tsc 等
3. **lint** — ruff / eslint / textlint 等
4. **tests** — pytest / vitest 等。coverage ≥ 80%
5. **secret scan** — hardcoded keys / tokens の不在確認（`security.md` 参照）
6. **doc sync 確認** — Chain Matrix の Doc Sync 発火条件に該当する変更なら、対応 doc が同じ diff に含まれているか確認。含まれていなければ commit せず Doc Sync に戻る
7. **`git status` 確認** — 意図しないファイルが含まれていないか

全 PASS でのみコミット可。FAIL があれば停止し、ユーザーに報告。

### 2 介入点モデル

ユーザーの介入は以下 2 点のみ:

1. **Plan 確認** — chain と並列化が確定した時点（`writing` では doc 分類とルーティング先 skill が確定した時点）
2. **Verify 結果確認** — コミット直前（`writing` では公開・deposit 直前の人間 gate と同一点）

途中の agent 起動・サマリ生成・ステップ遷移は **ユーザー介入なし**で進める。
ただし `fix` 種別の根本原因確認待ち（`debugging.md` の 仮説 → 証拠 → 確認待ち → 修正フロー）は **明示的な例外**として残す。


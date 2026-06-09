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

現時点ではルールレベルの規約として運用。将来的に PreToolUse hook による自動強制を検討。

## 証拠ベースの意思決定

- アーキテクチャ判断・技術選定・API 設計には証拠を添える（ドキュメント、ベンチマーク、既存パターン）
- 「X が最適と思う」は不十分 →「X が最適。理由: [証拠]」
- 証拠が見つからない場合はその旨を明記し、仮定として扱う

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
| `chore` | 設定 / docs / 依存更新 | settings, README |
| `prototype` | 学習・スパイク・本番外コード | 検証スクリプト |

`prototype` を選ぶ場合は **「prototype として扱う理由」を plan に必須記載**（fix/feat の悪用防止）。

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
| Verify (build / types / lint / tests / secrets / git status) | Y | Y | Y | Y | - |

**条件付き発火 `C` の発動条件**:

- `fix` × Security Review: 入力検証・認証・秘匿情報を触る fix のみ Y。ロジック誤り単独は `-`
- `chore` × Code Review: settings.json / hooks / permissions / CI 変更時のみ Y
- `chore` × Security Review: secrets 設定 / 認証関連 hook / permissions 変更時のみ Y

### 並列化指定（plan 時に確定）

実装中の判断分岐を排除するため、並列化を **plan 出力に明示**する。

- **作成系並列**: Phase 0 (`/search-first` 呼び出し) は独立 → planner と並列起動可。scout は search-first 内部で fan-out されるので、planning.md レイヤーでは並列単位として扱わない
- **レビュー系並列**: Code Review + Security Review は同じコード対象 → **default で並列起動**
- **逐次必須**: TDD は Plan の後、Verify は全レビュー後（並列化禁止）

plan 出力に以下のフォーマットで記載:

```
Parallel Group 1: [planner, scout]
Parallel Group 2: [code-reviewer, security-reviewer]
Sequential: TDD (Plan 後) → Verify (全レビュー後)
```

### 早期停止条件

以下を検出した時点で chain を中断し、ユーザーに報告する:

- Code Review / Security Review が **`CRITICAL`** を返した
- Verify ステップで build / types / tests のいずれかが失敗
- `fix` で根本原因の仮説が証拠で支持されない（`debugging.md` 参照、唯一の例外的ユーザー確認待ち）
- Phase 0 (`/search-first`) で `Adopt` Verdict → 実装方針の再 plan を要請

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

### Verify ステップ（chain 最終ステップ）

以下を実行:

1. **build** — 該当言語のビルドコマンド
2. **type check** — mypy / pyright / tsc 等
3. **lint** — ruff / eslint / textlint 等
4. **tests** — pytest / vitest 等。coverage ≥ 80%
5. **secret scan** — hardcoded keys / tokens の不在確認（`security.md` 参照）
6. **`git status` 確認** — 意図しないファイルが含まれていないか

全 PASS でのみコミット可。FAIL があれば停止し、ユーザーに報告。

### 2 介入点モデル

ユーザーの介入は以下 2 点のみ:

1. **Plan 確認** — chain と並列化が確定した時点
2. **Verify 結果確認** — コミット直前

途中の agent 起動・サマリ生成・ステップ遷移は **ユーザー介入なし**で進める。
ただし `fix` 種別の根本原因確認待ち（`debugging.md` の 仮説 → 証拠 → 確認待ち → 修正フロー）は **明示的な例外**として残す。


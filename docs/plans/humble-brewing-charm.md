# rules/ の scaffold dissolution — Opus 5 / Fable 5 向け rightsize

## Context

Anthropic の Thariq が公開した「The new rules of context engineering for Claude 5 models」（2026-07-25）で、**Claude Code のシステムプロンプトを 80% 以上削除してもコーディング eval に計測可能な劣化がなかった**ことが報告された。従来のコンテキストエンジニアリング作法の多くは旧世代モデルの弱さを補う足かせ（over-constraining）であり、Opus 5 / Fable 5 では衝突コスト（矛盾する指示を解くための思考消費）として負に効く。

この harness の `rules/` は **20 ファイル / 5,789 words ≈ 8–9k tokens が毎セッション常駐**しており、記事が挙げる 6 つのアンチパターンを複数踏んでいる。`akc-cycle.md` の **Scaffold Dissolution** 条項（inward / downward の 2 ベクトル）は既にこの退役判断を自ら規定しているため、これはその条項の自己適用にあたる。

**目標**: 常駐 5,789 → 約 2,200 words（**-62%**）。削減分は消さず、既存 skill へ吸収するか新設 skill へ降格して progressive disclosure に載せる。判断表そのものは失わない。

**測定済みの最大の取りこぼし**: `rules/python/` の 6 ファイル（600 words）は言語に無関係に常駐している。本セッション（Python ゼロ）でも全 6 本が注入されていることを実測で確認した。吸収先 `skills/python-patterns/SKILL.md`（2,870 words）は既に存在する。

## 保持する不変条件（削らないもの）

記事が言う「あなた固有の gotcha と意見」= rules の存在理由。以下は圧縮対象から除外する:

- **Reversibility Gate**（可逆性で承認強度を変える / batch 承認を N 件に amortize しない）
- **Change Target**（global 版のみ、repo コピーは触らない）
- **debugging: 仮説 → 証拠 → 確認待ち → 修正**（2 介入点モデルの明示例外）
- **Rate limit = policy signal**（2026-07-16 のアカウント block で実証）
- **Code vs LLM seam** / **文書化された不変条件はゲートに落とす**
- **Origin Tracking**（ECC diff 判断に必要な機構）
- **hooks のロジックは外部スクリプトへ**（JSON エスケープの罠）
- **単一台帳方式** / **commit message format**
- **Phase 0 のエントリポイントは `/search-first` に固定**（scout 直呼び禁止）
- **contemplative-axioms.md は verbatim のまま常駐**（ユーザー判断: identity 層として意図的に置く）

## 変更

### 1. 新設 `skills/implementation-chain/SKILL.md`（降格先）

`planning.md` の Implementation Chain Specification（約 900 words）を全文移設。`user-invocable: true` + `origin: shimo4228`。description は「feat / fix / refactor / chore / writing の実装チェーンを組む時」でトリガーさせる。

移設する内容（内容は削らず、そのまま持っていく）:
- タスク種別判定表（feat / fix / refactor / chore / prototype / writing）
- Chain Matrix（種別 × 9 ステップの Y / C / -）と `C` の発動条件
- Writing Chain ルーティング + Verdict マッピング表
- Review / Cleanup ステップの本体（どの reviewer をいつ起動するか、codex-review の diff-only 制約を含む）
- 早期停止条件

**移設しない（substrate 吸収済みとして退役）**:
- **Parallel Group 記法** — Agent tool の description が「independent work は単一メッセージで並列送信」を常時教えている（downward dissolution）
- **構造化サマリ強制フォーマット** — subagent の戻り値契約は harness 側が管理している

### 2. `rules/common/planning.md` 1,344 → 約 380 words

残す: What/Why/Alternatives、Phase 0（`/search-first` 固定 + Verdict 表 + トリガー / スキップ）、証拠ベースの意思決定、機能要求のチャレンジ（トリガーワード込み）、実行バイアス、Prototype Before Scale、**2 介入点モデル**、**Verify ゲート一覧**（build / types / lint / tests / secret scan / doc sync / git status）。

Chain 詳細は `See skill: implementation-chain` の 1 行ポインタに置換。Writing Chain 表も同 skill へ。

### 3. `rules/python/` 全 6 ファイルを削除、gotcha を `python-patterns` へ吸収

`git rm`（追跡下なので履歴が soft-delete 層）。吸収先は `skills/python-patterns/SKILL.md` の既存セクション:

| 移送元 | 移送先セクション | 扱い |
|---|---|---|
| `python/security.md`（redirect token leak / case-insensitive sanitizer bypass） | 新設 **Security Gotchas** | 全文保持（実 gotcha） |
| `python/lint-gates.md`（ruff B/I/T20、zip strict= 判定、import-linter contract、frozen AST ゲート） | **Python Tooling Integration** | 全文保持 |
| `python/hooks.md`（ruff-autofix.sh の PostToolUse、pyright-lsp が型を担当） | **Python Tooling Integration** | 全文保持 |
| `python/testing.md`（pytest / coverage / mark） | **Pytest Patterns** | 既存重複を除いた差分のみ |
| `python/coding-style.md`（PEP 8、type annotations、black/isort/ruff） | — | **退役**（Claude が既に持つ常識） |
| `python/patterns.md`（Protocol、dataclass DTO、context manager） | — | **退役**（`python-patterns` が既にカバー） |

`rules/` は 2 層構造から **common 単層**になる。

### 4. `rules/common/` 各ファイルの圧縮

| ファイル | words | → | 主な削除 |
|---|---:|---:|---|
| `akc-cycle.md` | 997 | ~260 | 6 phase の解説本文 → **トリガー → skill 対応表**に圧縮（各 phase は既に skill を持つ: search-first / learn-eval / skill-stocktake / rules-distill / skill-comply / context-sync）。**Scaffold Dissolution 節と signal-first / output discipline は全文保持** |
| `coding-style.md` | 470 | ~200 | 「ALWAYS create new / NEVER mutate」→ 「既定はイミュータブル。in-place が正しい場面（numpy / builder / accumulator）では周囲の慣行に合わせる」へ緩和。Code Quality Checklist（関数 <50 行 / ファイル <800 行 / ネスト <4）を退役。**Reversibility Gate / Change Target / Iteration Bounds は全文保持** |
| `skills.md` | 377 | ~170 | Skill Portability 節（skill を書くときだけ使う）→ `skill-creator` へ移送。**Origin 値表と運用ルールは保持** |
| `testing.md` | 278 | ~110 | TDD の RED→GREEN→REFACTOR 手順・テスト種別の一般論を退役。**MagicMock ではなく Namespace / sleep 禁止 / 本番でテストしない / coverage 80% を保持** |
| `patterns.md` | 255 | ~110 | Repository パターン・API エンベロープの一般解説を退役。**Code vs LLM 節と documented-invariant → ゲート化を全文保持** |
| `agents.md` | 242 | ~130 | Multi-Perspective Analysis のロール列挙を退役（Agent tool description が運ぶ）。**Author-Reviewer 分離 / cross-agent 共有・委譲のポインタを保持** |
| `security.md` | 208 | ~110 | OWASP チェックリストの一般項目を退役。**Secret 管理 + hook ポインタ / LLM Trust Boundaries / Security Response Protocol を保持** |
| `debugging.md` | 192 | ~140 | 「Retry with Context」の一般論を退役。**根本原因優先フロー / AI デバッグ注意点 / Rate limit = policy signal を全文保持** |
| `hooks.md` | 146 | ~90 | Hook 種別の一般説明を退役。**hooks vs skills の決定論性対比 / 外部スクリプト分離の gotcha を保持** |
| `task-tracking.md` | 131 | ~110 | 軽微 |
| `git-workflow.md` | 107 | ~70 | 軽微 |
| `contemplative-axioms.md` | 302 | 302 | **変更なし** |

### 5. Doc Sync（同一 diff 内で行う）

- `rules/README.md` — 2 層構造 → common 単層へ。ファイル一覧の説明文を実体に合わせる
- `CLAUDE.md` — 「`rules/` は common + python/ の2層構造」の記述を修正
- **`docs/adr/0018-rules-rightsize-for-claude5.md` 新設** — 記事を出典に、退役した各項目とその根拠（inward / downward のどちらか）を記録。`akc-cycle.md` から本文を減らす判断の正本をここに置く
- リンク切れ検査 — `grep -rn "rules/python" ~/.claude` で参照元を洗い、`python-patterns` へ repoint

## 変更するファイル

- 新規: `skills/implementation-chain/SKILL.md`, `docs/adr/0018-rules-rightsize-for-claude5.md`
- 全面改稿: `rules/common/planning.md`, `rules/common/akc-cycle.md`, `rules/README.md`
- 部分改稿: `rules/common/{coding-style,skills,testing,patterns,agents,security,debugging,hooks,task-tracking,git-workflow}.md`, `skills/python-patterns/SKILL.md`, `skills/skill-creator/SKILL.md`, `CLAUDE.md`
- 削除: `rules/python/` 6 ファイル（`git rm`）

作業ツリーには既存の未コミット変更（`settings.json`, `scheduled-tasks/weekly-aeon-shopping/SKILL.md`）があるため、**本作業は独立コミットに分ける**。

## Verification

1. **常駐量の実測** — `cat rules/common/*.md CLAUDE.md | wc -w` が約 2,200 に収まること。before は 5,789（実測済み）
2. **`/doctor` の before / after 比較** — ユーザーが実行。substrate 側の診断が残す指摘を、この diff が既に解消しているか照合する（自作 stocktake と `/doctor` の重複範囲の実測にもなる）
3. **リンク健全性** — `grep -rn "rules/python" ~/.claude` が 0 件、および各 rule の `See skill:` / 相対リンク先が実在すること（`skill-health` skill で走査）
4. **降格 skill の発火確認** — `skill-comply` で `implementation-chain` の発火を測定。自発トリガーが立たない場合は `user-invocable` 経由の明示呼び出し前提に切り替え、`planning.md` のポインタ行を「chain を組むときは `/implementation-chain` を呼ぶ」と命令形に変える（既知の自発トリガー上限 ≒ 40% を踏まえた fallback）
5. **回帰の目視** — 保持リスト（Reversibility Gate / Change Target / 根本原因優先 / Rate limit signal / Origin Tracking / Code vs LLM / 単一台帳）が全て圧縮後の本文に残っていることを確認

## 注記（今回のスコープ外）

`skills/python-patterns/SKILL.md` は吸収後 3,000 words 超の単一ファイルになる。記事は長い skill の複数ファイル分割を推奨しているため分割候補だが、常駐コストではない（呼ばれた時のみロード）ので今回は触らない。

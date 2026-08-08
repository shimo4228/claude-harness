# ADR 0009: Implementation Chain を plan に front-load し、orchestrate / verification-loop / python-testing skill を廃止

## Status

accepted（chain の front-load は維持。2介入点モデルだけ
[ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) で supersede）

## Context

ハーネス内で「実装フローでどの agent をどの順序で呼ぶか」が **3 レイヤーに散在** し、互いに矛盾していた:

- `rules/common/git-workflow.md` の **Feature Implementation Workflow** (planner → tdd-guide → code-reviewer → commit)
- `rules/common/agents.md` の **Immediate Agent Usage** (parallel 推奨) と **Parallel Task Execution**
- `skills/orchestrate/SKILL.md` (sequential chain を hardcode)

加えて以下の責務重複があった:

- `verify` skill ↔ `verification-loop` skill (build / types / lint / tests / secrets を両方が実装)
- `code-reviewer` agent ↔ `security-reviewer` agent (CRITICAL 領域 = secrets / SQLi / XSS が重複)
- `python-testing` skill (815 行、9 割が一般 pytest 知識) ↔ `tdd-guide` agent

ユーザー意図 (2026-05-02 セッションで明示):

> 実装に入ったら必要に応じて TDD・コードレビュー・セキュリティレビュー・リファクタークリーンを一気通貫にやる。
> ただし「実装時に判断させる」のではなく、**plan 時にその一気通貫の実装プランを含めて、実装前に私が確認して、コミット前に最終チェックを私がするだけという状況** を作りたい。

## Decision

1. `rules/common/planning.md` に **Implementation Chain Specification** セクションを新設。これを **唯一の source of truth** にする。
2. **タスク種別 × ステップのマトリクス** で chain を front-load する。
3. **2 介入点モデル** (Plan 確認 + Verify 結果確認) に統一。
4. 重複する記述・skill を削除または planning.md への参照に置換。

### 削除した skill

| skill | パス | 削除理由 |
|---|---|---|
| `orchestrate` | `~/.claude/skills/orchestrate/` | planner → tdd-guide → code-reviewer → security-reviewer chain を hardcode しており、planning.md の Chain Matrix と直接競合 (origin: ECC) |
| `verification-loop` | `~/.claude/skills/verification-loop/` | `verify` skill と機能完全重複 (Phase 1-4 で同じ build/type/lint/test/security 実行) |
| `python-testing` | `~/.claude/skills/python-testing/` | 815 行のうち 9 割が一般 pytest 知識 (Claude の訓練データに既に存在)。Python 固有の判断パターン 7 つを `rules/python/testing.md` に圧縮 migrate |

### Migration: `python-testing` → `rules/python/testing.md`

migrate した 7 パターン:

1. Fixture Scope の使い分け (function / module / session の判断軸)
2. Conftest.py の責務 (どこに置くか、200 行で分割)
3. Parametrize の `ids` 必須化 (test ID 可読性)
4. Mock の選択基準 (MagicMock 直接生成は禁止、autospec / PropertyMock の使い分け)
5. `tmp_path` fixture の優先 (NamedTemporaryFile より安全)
6. Async テストは `@pytest.mark.asyncio` 必須 (silent skip 防止)
7. pytest 設定は `pyproject.toml` に集約 (`--strict-markers` 必須)

削除した内容: 一般的な pytest 文法 (assertion 種類、fixture 基礎、parametrize 構文、mocking 基礎、test 組織構成等)。これらは Claude の訓練データに既に存在する。

### 不採用案とその理由

| 不採用案 | 理由 |
|---|---|
| `orchestrate` を「planning.md を読んで chain を実行する thin executor」に再定義 | (1) planning.md と executor の 2 つの source of truth が生まれ、divergent micro-instructions (timeout / retry / Python skip 等) が蓄積する。(2) skill は probabilistic trigger なので「run the chain」では発火しても本来の implementation trigger では発火しないなど asymmetric coverage を生む。(3) rule は毎セッション auto-load されるため executor 不要 |
| `verification-loop` を `verify` への deprecation redirect として残置 | dead path が probabilistic trigger を残し、200 行 skill load が無駄に発火するリスク。完全削除が適切 |
| `python-testing` を skill のまま残置 | 9 割が一般知識で、reference 価値が低い。判断が分かれる Python 固有パターンだけ rule に上げる方が発火率と密度が両立 |

## Consequences

### Positive

- **唯一の source of truth**: 「実装フローでどの agent を呼ぶか」が `planning.md` に集約された
- **2 介入点モデルの実現**: ユーザー介入が「Plan 確認 + Verify 結果確認」の 2 点だけになった
- **akc-cycle.md の Promote 原則の実践例**: 3 箇所以上の重複 → rule 昇格 + 下位削除
- **責務境界の明文化**: `code-review` ↔ `security-review` skill が reciprocal one-liner で分離
- **rules/python/testing.md の密度向上**: 一般 pytest ≒ 0、Python 固有判断 = 7 パターン

### Negative

- **muscle memory のロス**: `/orchestrate` / `/verification-loop` を打つ習慣がある場合、最初の 1-2 回はエラーになる
- **migration 時の見落としリスク**: `python-testing` の 815 行から 7 パターンに圧縮した際、未抽出パターンが silent に消える可能性 (commit message に migrate / 削除パターンを全列挙して緩和)
- **planning.md の肥大化**: 77 行 → 約 200 行 (将来的に目次追加を検討)

### Neutral

- **skill カウントの減少**: 3 skill 削除 (45 → 42 程度)。skill-stocktake で manifest 再生成が必要

## Migration Path (revert を要する場合)

削除した skill は git 履歴に残っている (`~/.claude/.git`):

```bash
# 削除前のコミットを確認
git log --all --pretty=format:'%h %s' -- skills/orchestrate/
git log --all --pretty=format:'%h %s' -- skills/verification-loop/
git log --all --pretty=format:'%h %s' -- skills/python-testing/

# 特定コミットから skill を復元
git checkout <commit-hash> -- skills/orchestrate/
git checkout <commit-hash> -- skills/verification-loop/
git checkout <commit-hash> -- skills/python-testing/
```

## Verification

実装直後の検証:

- `grep -rn "orchestrate\|verification-loop\|python-testing" ~/.claude/rules/ ~/.claude/skills/ ~/.claude/agents/` で残存参照がゼロ (artifact JSON は除く)
- skill 一覧から 3 skill が消えていることを確認 (Skill tool 描画で確認済み)

後続検証 (次セッション以降):

- `/skill-stocktake` で manifest 再生成
- `/rules-distill` でルール総覧更新
- `/skill-comply` で Implementation Chain Specification の compliance シナリオを生成し、実測 compliance rate を本 ADR に追記

## Related

- ADR-0001: ECC Skill Management Policies (origin tracking)
- `rules/common/akc-cycle.md` の **Promote** 原則
- `rules/common/skills.md` の **Knowledge Placement** 原則
- 旧 plan ファイル: `~/.claude/plans/shimmying-forging-flamingo.md`

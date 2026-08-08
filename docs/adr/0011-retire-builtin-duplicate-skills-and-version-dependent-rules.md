# ADR-0011: built-in 重複 skill とバージョン依存 rules の退役

## Status

accepted

## Date

2026-06-10

## Context

スキル・ルールの棚卸しで、現行 Claude Code の性能・built-in 機能に対して冗長になった記述を **3 カテゴリ** に分類して洗い出した。

**カテゴリ 1 — built-in skill との名前衝突・責務重複**: セッションのスキル一覧で `verify` / `code-review` / `security-review` がローカル版と built-in 版で 2 重出現していた。`plan` も plan mode の native 化により built-in と重複している。Claude Code の built-in が同名 skill を持つ場合、ローカル版は probabilistic trigger を消費しながら実質の差分を提供しない。

**カテゴリ 2 — Claude Code 本体バージョン依存の記述**: `rules/common/performance.md` は「Opus 4.6 + 1M context + MAX Plan」前提で全節が特定バージョンに縛られている。`rules/common/hooks.md` の TodoWrite 節は現行ハーネスで TaskCreate / TaskUpdate に移行済みであり記述が stale。`rules/common/agents.md` の **Parallel Task Execution** 節は現行 Claude Code が system prompt レベルで標準指示するようになった挙動の重複記述。

**カテゴリ 3 — broken reference**: 存在しないスキル・ファイルへの参照が 4 件確認された — `django-security` skill、`scaffold-dissolution.md`、`tdd-workflow`、`~/.claude.json` の `allowedTools` 記述。これらは Claude が参照先を辿っても 404 になるため、guidance として機能していない。

加えて `build-fix` / `test-coverage` 2 skill については、本文の大半が現行モデルの訓練知識として自明化しており、probabilistic trigger 枠の消費に見合うコンテンツ密度がないことをユーザーとの確認で確定した。

## Decision

判断基準は 3 軸: **built-in 重複** / **現行モデル性能による自明化** / **バージョン依存記述**。この基準に基づき以下を実施する。

1. **ローカル skill 6 件を完全削除する**。退役先は `_archived/` ではなく完全削除 ([ADR-0008](./0008-ecc-local-only-management.md) 準拠 — `rules/` は再帰ロードされるため archived 置きは退役したルールをセッションの context に戻す)。復元経路は git 履歴と本 ADR 末尾のコマンド。

   | skill | 削除理由 |
   |---|---|
   | `code-review` | built-in `code-review` と名前衝突・責務重複 |
   | `security-review` | built-in `security-review` と名前衝突・責務重複 |
   | `verify` | built-in `verify` と名前衝突・責務重複 |
   | `plan` | plan mode の native 化により built-in と重複 |
   | `build-fix` | 本文が現行モデルの訓練知識で自明化 |
   | `test-coverage` | 本文が現行モデルの訓練知識で自明化 |

2. **`rules/common/performance.md` を削除する**。全節が「Opus 4.6 + 1M context + MAX Plan」前提のバージョン依存記述であり、Build Troubleshooting 3 行も自明のため migrate せず削除する。

3. **`rules/common/hooks.md` を編集する**: TodoWrite 節を削除、`allowedTools` 記述を `settings.json` の `permissions` への参照に修正、origin マーカーを実態に合わせ `ECC` → `ECC-customized` に修正。**`rules/common/agents.md` を編集する**: **Parallel Task Execution** 節を削除 (現行 Claude Code が system prompt レベルで同等の指示を標準保持)。

4. **`rules/common/planning.md` の Verify ステップから「/verify skill を呼び」の文言を除去し、チェックリストをインライン正本化する**。built-in `verify` は behavioral 検証 (アプリ起動して挙動観察) であり、ローカル `verify` (build / types / lint / tests / secrets / git status の静的ゲート) と同名だが別物である。skill 削除と同時に planning.md の参照を切り、チェックリストを planning.md に直接保持することで静的ゲートの source of truth を維持する。

5. **`skills/tdd` を thin entry に trim する**。一般 TDD 解説は `rules/common/testing.md` と `tdd-guide` agent に委譲する。**`skills/write-prompt` のモデル名依存表現 (Haiku / Opus) を非依存表現に更新する**。

6. **broken reference 4 件を解消する**: `django-security` 参照行、`scaffold-dissolution.md` 参照行、`tdd-workflow` 参照行、`~/.claude.json` `allowedTools` 記述をそれぞれ削除または修正する。

7. **以下 4 skill は Keep と判定する**:

   | skill | Keep 理由 |
   |---|---|
   | `refactor-clean` | `refactor-cleaner` agent の user-invocable 入口として固有の役割がある |
   | `e2e` | Playwright artifact 収集の具体的手順を持ち、built-in に相当物がない |
   | `security-scan` | AgentShield wrapper として固有機能。`SKILL.md:90` の「Opus 4.6 Deep Analysis」は ECC 原本につき不改変で known-stale として容認 |
   | `skill-comply` | Haiku timeout 記述は実測根拠があり自明化していない |

## Alternatives Considered

### security-review の OWASP checklist (453 行) を reference として保持する

453 行のコード例付き OWASP checklist を削除せず reference document として残置する案。不採用: [ADR-0009](./0009-implementation-chain-front-loaded-in-plan.md) の `python-testing` 削除 (「9 割が一般知識 → 削除」) と同型の判断であり、内容は現行モデルの訓練知識。専用 agent (`security-reviewer`) がローカルに残存しており、checklist を skill として保持する必要はない。

### Wave 2 skill (build-fix / test-coverage / tdd) を全 Keep し built-in 名前衝突分のみ整理する

built-in と明白に衝突する `code-review` / `security-review` / `verify` / `plan` の 4 件だけ削除し、Wave 2 は手をつけない案。不採用: ユーザー確認の上で退役を承認済み。本文の大半が自明化しており、probabilistic trigger 枠の消費に見合わない。

### `_archived/` ディレクトリへ移動する

削除でなく `_archived/` への移動で退役する案。不採用: [ADR-0008](./0008-ecc-local-only-management.md) で確認済みのとおり `rules/` は再帰ロードされる。`_archived/` に置くことは退役したルールを毎セッション context に戻すことと等価であり、退役の目的を達成しない。

### `rules/common/hooks.md` の origin マーカーを `ECC` のまま維持する

diff 比較を容易にするため ECC 原本マーカーを保持する案 ([ADR-0001](./0001-ecc-skill-management-policies.md) の Trim 可否判定の前提でもある)。不採用: 実態はローカル追記済みであり `ECC` マーカーが既に不正確。`ECC-customized` に修正することで [ADR-0001](./0001-ecc-skill-management-policies.md) の Trim 可否判定が正しく機能するようになる。

## Consequences

### Positive

- **名前衝突の解消**: `verify` / `code-review` / `security-review` がセッションのスキル一覧で built-in 1 件ずつに収まる
- **probabilistic trigger 枠の節約**: 削除 6 skill 分の枠が空き、残存 skill の発火精度が相対的に向上する
- **バージョン依存記述の保守負担消滅**: `performance.md` 削除により、モデル名・コンテキスト長・料金プランが変わるたびに rule を更新する義務がなくなる
- **broken reference ゼロ化**: 存在しないファイル・skill への参照が 4 件すべて解消される
- **Verify チェックリストの意味が明確化**: planning.md がインライン保持する静的ゲート (build / types / lint / tests / secrets / git status) と built-in `verify` (behavioral) の非対称性が明文化される

### Negative

- **将来の built-in 構成変更リスク**: 退役根拠が「built-in の存在」であるため、Claude Code 本体の将来バージョンで built-in 構成が変わると静的ゲートに穴が開く可能性がある。緩和策: planning.md が Verify チェックリストをインライン保持し、agent 群 (`code-reviewer` / `security-reviewer` / `tdd-guide`) はローカルに残存するため、built-in が消えてもエージェント層での補完は可能
- **skill-stocktake の results.json の stale 化**: 削除 skill のエントリが残るが、次回 `/skill-stocktake` 実行で再生成されるため手動 prune は不要。ただし次回実行まで manifest が stale になる

### Neutral / Follow-ups

- built-in `verify` (behavioral 検証) とローカル `verify` (静的ゲート) は同名だが別物であるという非対称性を本 ADR に記録する。将来 built-in 構成が変更された際の再判断材料とする
- `rules/common/agents.md` の **Parallel Task Execution** 節削除後、現行 Claude Code の system prompt レベル標準指示が変わった場合は節を再追加する
- `security-scan` の `SKILL.md:90` の「Opus 4.6 Deep Analysis」記述は ECC 原本につき不改変。known-stale として容認済みだが、次回 ECC 棚卸し時に上流を確認する

## Revert

削除した skill および rule は git 履歴に残っている:

```bash
git checkout 9adb0e0 -- skills/code-review skills/security-review skills/verify skills/plan skills/build-fix skills/test-coverage rules/common/performance.md
```

## Related

- [ADR-0001](./0001-ecc-skill-management-policies.md): ECC スキル管理ポリシー — origin tracking と Trim 可否判定
- [ADR-0008](./0008-ecc-local-only-management.md): ECC ローカル管理一本化 — `_archived/` 不採用の根拠 (rules/ 再帰ロード)
- [ADR-0009](./0009-implementation-chain-front-loaded-in-plan.md): Implementation Chain front-load — `python-testing` 削除 (一般知識自明化) の前例
- `rules/common/akc-cycle.md` の **Curate** 原則

# ADR-0039: python-reviewer を退役し、chain を bug 軸 (Code Review) × quality 軸 (Simplify) に直交化する

## Status

accepted

## Date

2026-08-13

## Context

implementation-chain の Code Review category は、Python diff に対して `code-reviewer` と
`python-reviewer` を並列起動する定義だった。この重複は単発の観測ではなく chain 定義そのものに
由来する — skill-comply の pinned spec（`skills/skill-comply/results/implementation-chain.spec.yaml`）
も code_review step として両者の起動を要求している。ユーザーは両者が同じ diff に重複した指摘を
返す実行を観測し、解消を求めた（2026-08-13）。

python-reviewer 側の担当領域を分解すると、chain の他ステップと重複していた:

- **決定論ツールの再実行** — `python-review` skill は pyright / ruff / bandit / pip-audit /
  pytest の実行を規定し、`agents/python-reviewer.md` は ruff / mypy / pylint / black --check を
  実行していた。決定論層の現在の正本は、ruff format / bandit が commit 面 hook、
  ruff check / pyright / pip-audit / pytest が repo の `.claude/verify.sh`
  （[ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) / [ADR-0038](0038-publish-curated-commit-hooks.md)）。
  agent による再実行はこの層の複製である。ただし verify.sh 未導入（または承認台帳未登録）の
  repo では pyright / pip-audit が走らない穴が ADR-0038 Consequences に記録されており、
  本 ADR はこの穴を埋めない（Negative に計上）
- **セキュリティ** — `security-reviewer` + bandit と重複
- **Pythonic idiom**（mutable default / bare except / comprehension 等）— ruff の bugbear 系
  ルールが機械検出し、残る意味的判定は Claude 5 世代の `code-reviewer` が native に持つ。
  idiom fix の正本は既に skill: `python-patterns` へ移してあり、python-review skill 自身が
  重複回避のため defer を明記していた

これは `rules/common/akc-cycle.md` の Downward dissolution（substrate が capability を
native に持ち、旧世代向けの手書き足場が冗長化する）に該当する。

**先行決定との関係**: 本 ADR は 2 つの先行決定を部分的に反転する。

- [ADR-0018](0018-rules-rightsize-for-claude5.md) を **partially overrides** — ADR-0018 は
  `rules/python/` 退役の反論処理で「`python-review` skill / `python-reviewer` agent が
  review 段で決定論的に当たる」ことを保証に使い、退役 rules の吸収先にも
  `agents/python-reviewer.md` を挙げていた。本 ADR はその agent 経路を失効させる
  （残るのは機械強制層と code-reviewer + /simplify。ADR-0018 側に注記済み）
- `.notes/t-004-builtin-review-surface.md` の「built-in review は追加であって退役ではない。
  自動枠（code-reviewer / python-reviewer / …）は変更しない」を部分反転する — built-in
  `/simplify` を chain の正規ステップに置き、自動枠から python-reviewer を退役させる
- [ADR-0033](0033-subagent-model-tier-by-downstream-verification.md) の opus tier 名簿から
  python-reviewer が消える。同 ADR は「Chain Matrix 変更時は階層の前提を同時に見直す」と
  自ら規定しており、本 ADR がその見直しに当たる。Simplify は built-in skill であって
  agent ではないため、tier 割当の対象外（ADR-0033 側に注記済み）

2026-07-25 の feedback memory「Python では /python-review を使う」は python-review skill /
python-reviewer agent が決定論ツールを実際に実行することを根拠としていたが、決定論層の
verify.sh / hook への移設によりこの前提は失効していた。

一方、built-in の `/code-review`（correctness bug 軸）と `/simplify`（quality 軸のみ、
bug を探さないと明記、fix を working tree に適用）は観点が直交しており、重複報告を構造的に
生まない。refactor 種別では既に Refactor Clean が「built-in simplify → refactor-cleaner」の
並びを使っていた。

## Decision

> **注記（2026-08-27, ADR-0055）**: Decision 1–2 の per-commit Simplify step と
> 「Review 群の前」の順序は退役した — built-in `/code-review` が quality 軸
> （Reuse / Simplification / Efficiency / Altitude）を内蔵するため、`/simplify` は
> batch opt-in（数 commit まとめて）へ降格し、順序強制 hook
> （simplify-order-notice.sh）も同時退役。bug 軸 × quality 軸の直交という本 ADR の
> 分析、および Decision 3 以降（python-reviewer 退役ほか）は生きている。

1. Chain Matrix に **Simplify** step（built-in `/simplify`、quality 軸の cleanup 適用）を
   追加する。feat = Y、fix = C（新規ロジックを含む fix のみ。typo・設定値のみは `-`）、
   refactor は Refactor Clean 内で実行済みのため `-`、chore / prototype は `-`。
2. Simplify は Review 群の**前**に実行する。`/simplify` は fix を working tree に適用する
   ため、reviewer には適用後の diff を見せる。
3. Code Review category から `python-reviewer` を外し、`code-reviewer` 単独とする
   （Swift の `swift-reviewer` 追加は維持）。
4. `skills/python-review/` と `agents/python-reviewer.md` を退役（削除）する。両者は
   git 追跡下にあり、履歴から復元できる。idiom の正本は skill: `python-patterns` が
   引き続き保持し、python-review skill が列挙していた framework 固有チェックリスト
   （Django N+1 / FastAPI CORS / Flask context 等）は同 skill へ移設して保持する。
5. 参照掃除: `skills/codex-review/SKILL.md`・`skills/context-sync/SKILL.md`・
   `skills/agent-architecture-audit/SKILL.md` の python-reviewer / python-review 参照を
   repoint する。`skills/implementation-chain/SKILL.md` の「built-in review は任意の上乗せ」
   規定に Simplify の例外（chain 正規ステップ化）を明記する。
6. feedback memory `feedback_python_review` を反転内容で更新する。
7. 先行 ADR への in-place 注記: ADR-0018（吸収先と反論の失効）、ADR-0033（tier 名簿）。
8. `swift-reviewer` には同じ dissolution の問いが立つが、本 ADR では判断しない。

## Alternatives Considered

### python-reviewer を残したまま Simplify を追加する

決定論ツールの再実行を除いても、python-reviewer に残る意味的指摘（idiom / 一般品質）は
code-reviewer と同一領域であり、重複報告が残るため却下した。

### python-reviewer の scope を idiom / framework 固有チェックに絞って残す

絞った後に残る判定は substrate が native に持つ層そのもので、Python diff ごとに agent
1 体を追加起動するコストと catalog 面積に見合わない。framework 固有の観点は agent である
必要がなく、参照資料として `python-patterns` に置けば code-reviewer が読める（Decision 4 で
実施）ため却下した。

### chain から外すだけで python-review skill を user-invocable として温存する

chain からも feedback memory からも参照されない skill は listing とメンテ面積を占有し、
config-gc の退役候補になるだけである。必要になれば git 履歴から復元できるため却下した。

### /code-review の cleanup 検出（--fix）に quality 軸も兼ねさせる

built-in code-review の cleanup 網羅は effort level 依存であり、quality 軸を専任で持つ
/simplify（bug を探さないと役割を明記）との分担の方が chain 定義として安定するため却下した。

### swift-reviewer も同時に退役する

Swift 6 strict concurrency 等の判定を code-reviewer が同等に代替できるかを未検証のため
保留した。generation-audit の次回対象として記録する。

## Consequences

### Positive

- Python diff での重複報告が構造的に消える（bug 軸と quality 軸が直交）
- agent 1 + skill 1 の退役で catalog とメンテ面積が減る
- 決定論チェックの正本が verify.sh / hook の層に保たれる（agent による再実行の廃止）
- framework 固有チェックリストは `python-patterns` に残り、参照経路は保たれる

### Negative

- 「Python 固有の観点を必ず見る」という構造的保証がなくなり、code-reviewer の一般能力と
  `python-patterns` の確率発火に依存する
- verify.sh 未導入 repo では、python-review skill という pyright / pip-audit の最後の
  呼び手も消える（pip-audit の残る呼び手は security-reviewer のみで、fix では C、
  refactor では `-`）。ADR-0038 記録済みの穴が 1 経路広がる
- /simplify が working tree に fix を適用するため、Review 前に diff が変化する
  （Review 前実行の順序規定で reviewer は最終形を見る）

### Neutral / Follow-ups

- skill-comply の pinned spec `results/implementation-chain.spec.yaml` は旧 chain
  （python-reviewer 要求・Simplify 無し）を固定したままで、再生成するまで遵守測定が
  誤採点になる → 台帳 T-SC-SPEC-STALE
- `skills/agent-stocktake/results.json` の python-reviewer `keep` 判定は時点記録として
  残す。次回 agent-stocktake / generation-audit の run が上書きする
- swift-reviewer の dissolution 判定は次回 generation-audit で行う
- 公開 repo (claude-harness) は origin: shimo4228 フィルタで収集しており、
  origin: ECC-customized の python-review は同期対象外の見込み。次回 harness-sync で
  公開側に残骸がないことを確認する

## References

- `skills/implementation-chain/SKILL.md` — Chain Matrix / reviewer roster の正本
- `skills/python-patterns/SKILL.md` — idiom + framework checklist の正本
- `.notes/t-004-builtin-review-surface.md` — 部分反転した built-in review 面の決定
- `.notes/TASKS.md` T-SC-SPEC-STALE — pinned spec の再生成タスク
- memory: `feedback_python_review`（反転更新済み）
- [ADR-0018](0018-rules-rightsize-for-claude5.md)（partially overridden）・
  [ADR-0033](0033-subagent-model-tier-by-downstream-verification.md)（tier 名簿）・
  [ADR-0035](0035-commit-review-hook-and-rules-rightsize.md)・
  [ADR-0038](0038-publish-curated-commit-hooks.md)（決定論層の所在と穴）

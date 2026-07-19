<!-- origin: shimo4228 -->
# Python Lint Gates

> This file extends [common/patterns.md](../common/patterns.md) "Code vs LLM" —
> 文書化された構造的不変条件は決定論ゲートに落とす。レシピの正本は
> learned note: [documented-invariant-lint-gates](../../skills/learned/documented-invariant-lint-gates.md)

## Ruff baseline

新規 Python プロジェクトの `[tool.ruff.lint]` は defaults (E4/E7/E9/F) に加えて:

```toml
extend-select = ["B", "I", "T20"]
```

- **B** (bugbear): `zip()` の silent truncation、mutable default 等
- **I** (isort): `combine-as-imports = true` で re-export ブロックの爆発を防ぐ
- **T20**: library code での print 禁止（logging を使う）。CLI 出力・TTY 承認表示など
  **print が interface そのものの seam は per-file-ignores で明示除外**する
  （黙って全域無効化しない — 除外リスト自体が「どこが console UI か」の機械可読な記録になる）

## zip strict= の判定

- `strict=True`: 両 iterable が構成上同長と**その場で証明できる**箇所のみ
  （直前の shape/len guard、lockstep append）。長さ不一致 = バグを loud に
- `strict=False`: truncation が意図（`zip(x, x[1:])` 型の隣接ペア走査）、
  または挙動凍結が必要な箇所（replay gate 対象のパーサ等）。明示することに意味がある

## 構造ゲートのトリガー

| 文書化された規約 | 機械強制 |
|---|---|
| レイヤ import 方向（ADR 等に記載） | import-linter layers contract |
| アダプタ・モジュール間の独立 | import-linter independence contract |
| 「dataclass は frozen=True（例外なし）」 | AST スキャンテスト + **理由付き allowlist**（例外は allowlist に書かれたものだけ、という機械可読な形に規約を締める） |

contract / ゲートには**修正方針をコメントで併記**する（違反時に AI が読む修正ガイド。
"どの層に下ろすか・注入で解くか" まで書く）。

## 導入の規律

- ゲート新設時は**違反を一時注入して発火を実証**してから commit（one-run-not-evidence）
- fail か warning かは「更新判断が機械か人間か」で選ぶ — 検出は code、判断が人間に残る
  もの（doc の統計値等）は warning-only

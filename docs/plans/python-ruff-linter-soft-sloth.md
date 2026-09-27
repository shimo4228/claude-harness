# 複雑度・サイズ予算の実測パス（read-only）

## Context

X の投稿（Nate Berkopec / Sam Saffron, 2026-08-27）が挙げた「人間には厳しすぎるが agent には
効く」4 つの lint — サイクロマティック複雑度予算 / ファイル毎 LOC 制限 / CSS・JS サイズ制限 /
ABC スコア — が、自分の環境でどれだけカバーされているかを確認した。

**結果: 4 項目すべて未カバー。** 104 config / 82 repo を走査して `C901` `mccabe`
`max-complexity` `PLR09*` `max-lines` `max-module-lines` `size-limit` `radon` `lizard` は
ヒット 0 件。内訳:

| 項目 | Ruff の対応 | 現状 |
|---|---|---|
| 複雑度予算 | `C901` / `PLR0911-0917` は**存在する** | 全 repo で未選択。0.16 の 413 default にも `C90`/`PLR` は非該当 |
| ファイル毎 LOC | **Ruff に無い**（pylint `C0302` は astral-sh/ruff#970 で未実装） | 皆無 |
| CSS/JS サイズ | 対象外 | xmetrics-web はカスタムルール無し、bundle 予算も無し |
| ABC スコア | **無い**（RuboCop 由来の Ruby 指標） | 皆無。近縁の cognitive complexity も ruff#2418 が open |

唯一 zafu-ios だけが SwiftLint のデフォルト有効ルール（`cyclomatic_complexity` 10/20、
`file_length` 400/1000、`type_body_length`、`function_body_length`、
`function_parameter_count`）で項目 1・2 を**無自覚に**enforce している。

一方で `verify-bootstrap` の lint カテゴリの問いは「構造的な誤り・**複雑度**・デッドコード」と
複雑度を明記済み。つまりこれは却下された穴ではなく**宣言済みの未着手の穴**。

### なぜ実測が先か

閾値を先に決めない。`review-to-lint` の規律「**免除境界を先に実測する** — 既存 corpus 全件に
当てて違反数を数えてから閾値を決める。ゲートを初日に赤くする lint は免除境界の設計ミス」に
従う。加えて ADR-0042 の診断「トリビアの原因は発火頻度でなく **repo と一致しない固定
チェックリスト**」があるので、「全 repo 一律の 1 つの数値」が成立するかどうか自体が
実測で答えるべき問いになる。

このパスの成果物は**測定レポート 1 枚のみ**。repo は一切変更しない。採否・閾値・配線は
数字を見てから別途決める。

## 到達点

`repo × メトリック` の分布表と、候補閾値での違反件数表。特に答えたい 3 問:

1. 各メトリックの p50 / p90 / p99 / max はいくつか
2. 候補閾値（例 C901 = 10/15/20、LOC = 300/500/800）で違反が何件出るか = drain コスト
3. **repo 間で分布が割れるか** — 割れるなら「全 repo 一律の数値」は ADR-0042 の失敗モードに
   なるので、repo ローカル所有が正しいという実証になる

## 測定対象

所有権があり、かつ計器が意味を持つ範囲に絞る（82 repo 全部は対象外）。

| 層 | repo | 対象 |
|---|---|---|
| A. 一次 | `~/.claude` | `hooks/` `scripts/` `skills/*/scripts/` `tests/` の owned Python |
| A. 一次 | `MyAI_Lab/contemplative-agent` | `src` `tests` `scripts` `evals` |
| A. 一次 | `MyAI_Lab/zafu-ios` | `Sources` `Tests`（Swift） |
| B. 二次 | ruff config を持つ Python repo 群 | aeon-shop, g-kentei-tool, pdf2anki, tiny-lm-lab, daily-quest-generator, active-inference-viz, einstein-arena |
| C. 参考 | `MyAI_Lab/xmetrics-web` | ソースの CSS/TS バイト数のみ（bundle 実測は build が要るので範囲外・レポートに明記） |

## 手順

### Step 1 — 計器を 1 本に固定

全 repo を**同一の ruff 版**で測る（比較可能性のため）。ハーネスの pin に合わせて
`uvx ruff==0.16.1`。各 repo の `select` / `ignore` / `per-file-ignores` が干渉しないよう
`--isolated` で走らせ、測りたいルールだけを明示 select する。

### Step 2 — 複雑度の「全数値」を 1 回で取る

閾値を最小に倒すと**全関数が実際の値つきで報告される**ので、これで分布が丸ごと取れる:

```
uvx ruff@0.16.1 check --isolated --no-cache --output-format json \
  --select C901 --config "lint.mccabe.max-complexity=0" <paths>
```

同じ手で PLR 系も取る（`lint.pylint.max-args` / `max-branches` / `max-returns` /
`max-statements` / `max-locals` / `max-bool-expr` / `max-positional-args` /
`max-public-methods` を最小値に）。preview 扱いのルール（PLR0904/0914/0916/0917）は
`--preview` 付きの別 run にし、レポートで stable と区別して記す。

JSON の `message` に実測値が入る（例 `` `foo` is too complex (7 > 0) ``）ので、そこから
数値を抽出して repo ごとの分布にする。

### Step 3 — LOC / ファイルサイズ

ツール不要。`git ls-files` で対象を列挙して行数・バイト数を集計する。Swift は
`swiftlint --strict --quiet` を zafu-ios で 1 回走らせ、既に効いているデフォルト閾値の
現在の余裕（`file_length` の warn 400 に対してどこまで来ているか）を記録。

### Step 4 — レポート生成

集計スクリプトは scratchpad に置く**使い捨て**。`skills/*/scripts/` には置かない —
これは evidence script の新設ではなく 1 回の調査で、常設したくなったら改めて
review-to-lint の手順に乗せる。

出力先: `/private/tmp/claude-501/-Users-<user>--claude/ccf937d0-893a-4aa5-ae7d-6a73b87a90e0/scratchpad/complexity-budget-survey.md`

レポートの構成:
- メトリック × repo の分布表（p50/p90/p99/max、件数）
- 候補閾値ごとの違反件数（drain コスト）
- 上位違反ファイル（`file:line` 付き）
- **repo 間の分布差**の所見 — 一律閾値が成立するか否かの判断材料
- 測定日と ruff 版（`review-to-lint` の as-of 規律）

## 触らないもの

- `ruff.toml` / 各 `pyproject.toml` / `.swiftlint.yml` — 変更しない
- `.claude/verify.sh` / `verify.md` / `harness_lint.py` — 変更しない
- ADR / RFC — 起票しない（採否を決める前段なので、記録すべき判断がまだ無い）
- ADR-0055 が却下した「行数/機能の比率ダイヤル等の監視計器」との関係整理は、実測後に
  採用を検討する段で正面から書く（今回は 1 回の調査であって常設計器ではない）

## 検証

1. 集計スクリプトを 2 回走らせて件数が一致すること（決定論性）
2. 手検算 1 件 — `scripts/hooks/harness_lint.py`（630 行、12 個の `lint_*` 関数）について、
   レポートの LOC と最大複雑度を実ファイルと突き合わせる
3. `--isolated` が効いていることの確認 — 同じ repo を `--isolated` なしで走らせ、repo 側の
   `ignore` で結果が動く（= isolated が必要だった）ことを 1 例で示す
4. `git status` が全 repo でクリーンなまま（read-only の確認）

# T-004: Chain Matrix に「ユーザー実行 (U)」枠を新設し、ビルトイン /code-review を追加する

## Context

`implementation-chain` の Chain Matrix は自作 agent（code-reviewer / python-reviewer /
security-reviewer）+ codex-review だけで組まれ、同領域のビルトイン `/code-review` を参照して
いない。2026-07-25 の試行で以下が実測確定済み（`.notes/t-004-builtin-review-surface.md`、退役済み）:

- `/code-review` は `disable-model-invocation` で **Claude から起動できない** → 自動枠（`Y`/`C`）には構造的に入れられない
- 自作側の退役は自動レビューの 1 枚化 = 弱体化（能力と可用性の混同）
- `/review` は GitHub PR 専用、`/simplify` は Claude から起動可能（cleanup 側・bug は探さない）

**方針は「退役ではなく追加」**: 新記号 `U` で「Verify 結果確認 gate でユーザー実行を提案する面」を
表し、自動枠は温存する。2 介入点モデルに新しい介入点は足さず、既存の第 2 点（Verify 結果確認）に
相乗りさせる。

**ユーザー確定済みの判断**（AskUserQuestion, 2026-07-25）:

1. **codex-review は昇格しない** — 自動枠は現状維持。低リスク refactor / chore の bug 探索の薄さは U 枠でカバー
2. **U 記号・非自明 diff のみ提案** — feat / fix / refactor に付与、自明 diff では省略、effort 目安を添える

## 変更対象

**`skills/implementation-chain/SKILL.md` のみ**（+ 台帳 `.notes/TASKS.md` の T-004 行を Done へ）。
`rules/common/planning.md` は触らない — Review 起動条件の正本は skill 側（ADR-0018 の lean 方針、
planning.md L75 が既に skill へ defer 済み）。

## 編集内容（SKILL.md）

### 1. Chain Matrix（L29–43）

- 凡例に `U` を追加: 「`U` = Verify 結果確認 gate でユーザー実行を**提案**（Claude からは起動不可・gate ではない）」
- Matrix に行を追加:

  | ステップ | feat | fix | refactor | chore | prototype |
  |---|:-:|:-:|:-:|:-:|:-:|
  | User-Run Review (`/code-review`) | U | U | U | - | - |

- `C` 発動条件リストの下に **`U` の発動目安**を追加:
  - 提案するのは**非自明な diff のみ**（typo 級・数行の自明変更では省略）
  - effort 目安: 通常 → 無印 `/code-review`、高 stakes（公開前・広範囲・セキュリティ境界）→ `/code-review high`、公開前の大型変更 → `/code-review ultra`
  - **advisory であり gate ではない** — chain は実行結果を待たず、早期停止条件にも入れない。実行判断・結果の取り込みはユーザーに属する

### 2. Review / Cleanup ステップ（L58–69）

- **`/simplify` を `refactor` の cleanup 第一手に追加**: refactor-cleaner の項を
  「`refactor` 種別のとき、まず `/simplify`（ビルトイン・reuse / simplification / efficiency の修正まで適用、bug は探さない）、次に refactor-cleaner（knip / depcheck 等による dead code / 重複除去）」の順に改稿
- 節末尾に 1 行追記: Verify 結果確認 gate で U 枠の `/code-review` を提案する旨（Matrix の U 定義へのポインタ）

### 3. 非対象の明記（新規の短い注記）

- `/review` は **GitHub PR 専用**（description が明示: ローカル diff は `/code-review`）のため chain 非対象
- `/security-review` の帰属判定は **T-006（claude-security plugin 再編）のスコープ** — この diff では触らない

### 4. frontmatter description の更新

「ユーザー実行枠（/code-review 提案）もここが正本」相当の一句を追加。
**注意**: description は quoted string のまま維持し、編集後に YAML パースを検証する
（memory: 生成 description の `: ` が YAML を破壊した実績あり）。

## 台帳更新（同じ diff 内）

- `.notes/TASKS.md`: T-004 行を **Done 節へ移動**（完了日・判断結果 = 「U 記号 / codex 昇格せず」を一行で記録、詳細ノートへのリンク維持）
- `t-004-builtin-review-surface.md` は詳細資料としてそのまま残す（Done 行から参照）

## 検討済みの問題点（プラン設計に織り込み済み）

1. **U は gate にできない** — 実行を Claude が検証できないため advisory に限定。早期停止条件・Verify PASS 条件に含めない（含めると chain が永遠に待つ設計になる）
2. **凡例の意味二重化** — `Y`/`C` と同記号でユーザー実行を表すと「Claude が起動する」意味と衝突するため `U` を新設（台帳の指摘どおり）
3. **提案ノイズ** — 常時提案は小型 fix で毎回ノイズになるため「非自明 diff のみ」条件を凡例側に明記
4. **ADR は不要** — 退役なし・ADR-0011 の Keep 判定への override なし（ADR が要るのは T-006 側）。CODEMAPS も本 repo に存在せず Doc Sync 対象外
5. **planning.md への複製リスク** — rules 側には足さない。U 提案の発生点（Verify 結果確認）は planning.md が既に定義する介入点なので、skill 側の記述だけで整合する
6. **/simplify と refactor-cleaner の役割重複** — 「/simplify = 変更コードの質的改善（modify）」「refactor-cleaner = ツール駆動の dead code 除去」と分担を一文で明記して重複解釈を防ぐ

## Verify

1. 編集後の SKILL.md frontmatter を YAML パース検証: `python3 -c "import yaml,sys; yaml.safe_load(open('...').read().split('---')[1])"`
2. Matrix の行・凡例・発動条件の相互整合を目視確認（U 行に凡例未定義の値がないこと）
3. `git diff` で意図した 2 ファイル（SKILL.md / TASKS.md）のみが変更されていること
4. secret scan は既存 PreToolUse hook が commit 時に自動実行
5. コミット: `feat(implementation-chain): Chain Matrix にユーザー実行 (U) 枠を新設し /code-review を追加` 系（種別は chore でも可、ユーザー確認後）

# ADR-0028: review-chain-notice の閾値撤廃と 3 区分検出 — adr-reviewer 新設

## Status

accepted — adr-reviewer の新設と chain 登録は維持。3区分 diff 分類、対象外規定、分類テスト、
reviewer roster の3箇所配置は [ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) が supersede

## Date

2026-08-01

## Context

[ADR-0027](0027-restore-review-execution-check-to-verify-gate.md) は rules 側に Review 実行確認を
復元し、hook 層の強化は「8 月中の実行率を測ってから判断する」として保留した。その保留を、
hook 自身の発火カバレッジが判明したため前倒しで解除する。

### 測定の定義

以下すべて `~/.claude`、range は **`git log --since=2026-07-15 4d24612`**（4d24612 = 本 ADR の
一連の変更を始める前の HEAD。当日の commit を除外するため rev 指定で固定）。merge commit は
この repo に存在しない（直近 135 commit すべて親 1）。判定は当時の hook のロジックを
そのまま適用した — 旧: `CODE_RE` に一致するファイル数 ≥ 3 または追加行 ≥ 150。
新: `CODE_RE` / `SHAPE_RE` / `ADR_RE` のいずれかに 1 件でも一致。

再現スクリプトは本 ADR の diff には含めない（一時ファイル）。3 つの正規表現は
`hooks/review-chain-notice.sh` にあり、`git log <range> --pretty=%h` の各 commit に対し
`git show --name-only --pretty=format: <sha>` の出力を grep して数えれば再現できる。

### 発火カバレッジ（全 82 commit）

| ロジック | 発火 | 率 |
|---|---:|---:|
| 旧（閾値あり・コード拡張子のみ） | 11 | **13%** |
| 新（閾値なし・3 区分） | 76 | **93%** |

旧ロジックの不発 71 件の内訳:

- **コードを含むが閾値未満**: 17 件（閾値が落とした分）
- **コードを 1 件も含まない**: 54 件（`CODE_RE` が落とした分）

**取りこぼしの主因は閾値ではなく射程**だった。閾値の撤廃だけなら 11 → 28 件（34%）にしか
ならず、`CODE_RE` の拡張が残りを担う。この 2 つは別々の変更で、コストの帰属も別である。

落ちていた 54 件が触っていたファイルを**延べ出現回数**で数えると（commit 数ではない。
1 commit が複数パスに触れるため合計は 54 を超える）、`rules/common/` 23・`docs/adr/` 23・
`.notes/` 16・`agents/` 14・`settings.json` 10、`skills/**` は延べ 108（distinct 68）。
`human-gate.md` が本文提示を要求する **behavior-shaping artifact のうち md で書かれたもの**が、
まとめて検出面の外にあった。control plane は完全に抜けていたわけではない —
`hooks/*.sh` は `CODE_RE` に一致するので、閾値を超えれば当時も鳴っていた。

### 閾値の設計根拠が部分的にしか成立していなかった

当時のヘッダは閾値を「advisory のノイズ抑制であって品質フィルタではない — 小さな chore/fix
連発でリマインドが鳴り続けると gate complacency を招く」と説明していた。

`additionalContext` は Claude の context に注入されるだけで**人間には表示されない**ため、
この根拠のうち「人間が通知に慣れて見なくなる」部分は成立しない。一方 **Claude 側のノイズ
コストは残る** — 毎 commit の注入トークンと、同じ文が繰り返されることによる信号価値の低下は
実在する。撤廃の判断は「人間側コストがゼロ」＋「取りこぼし 87% のコストがそれを上回る」で
あって、「ノイズコストが存在しない」ではない。Claude 側コストは Consequences に計上する。

### ファイル種別以外のすり抜け経路

1. **`.bats` が `CODE_RE` に無い** — repo に 11 ファイル存在（`git ls-files '*.bats'`）。
   テストは `human-gate.md` が「検査の証拠を作るもの」として本文提示を求める区分で、
   `hooks/evidence-file-notice.sh` は `^tests?/` で拾っていたが、本 hook は
   **テスト変更を一切検出しなかった**
2. **`AGENTS.md`** — Codex CLI 向け cross-agent 指示文（[ADR-0015](0015-cross-agent-rules-sharing-reference-first.md)）
3. **`git commit -a` で index が空** — 検査が `git diff --cached` のみだったため、
   index を経由しない `-am` を使うと**ファイル種別によらず全件すり抜けた**
4. **`git revert` / `git merge`** — 判定が `commit` の語に一致する必要があった（実績 0 件だが、
   PR 運用を始めた時点で穴になる）

### ADR にレビュー面が無い

`docs/adr/` を検出対象に含めると、起動すべき reviewer が存在しないことが判明した。
`adr-writer` は [ADR-0016](0016-writer-agents-render-not-decide.md) で render 専任と規定済み、
`architect` は決定の是非を judge する agent で、**記録の質を検査する担当がいなかった**。

## Decision

### 1. 閾値を撤廃し、検出を 3 区分に分ける

区分ごとに要求されるレビューが異なるため、メッセージも分ける:

| 区分 | 対象 | 促すもの |
|---|---|---|
| `code` | 実装コード + テスト（`.bats` を追加） | code-reviewer 系 / security-reviewer / codex-review |
| `shaping` | `skills/` `rules/` `agents/` `hooks/` `CLAUDE.md` `AGENTS.md` `settings.json`（`.claude/` 接頭辞は任意） | 本文提示（human-gate.md）+ 高 stakes なら codex-review |
| `adr` | `docs/adr/**.md` | adr-reviewer + codex-review（prompt-driven） |

**区分は排他ではない。** `hooks/*.sh` は「コード」であると同時に「control plane」でもあり、
code-reviewer による欠陥検査と本文提示の**両方**が要る。重複計上を許容する。

`SHAPE_RE` は `.claude/` 接頭辞を任意にする。harness repo では `skills/...` が repo 直下だが、
他 repo では project overlay として `.claude/skills/...` に置かれる（[ADR-0025](0025-global-vs-project-asset-placement.md)）。
この hook は全 repo で走るため、行頭固定だと **harness 以外では shaping 区分が一切効かない**。

### 2. すり抜け 4 経路を塞ぐ

- `CODE_RE` に `.bats` を追加、`SHAPE_RE` に `AGENTS.md` を追加
- staged が空なら `git diff HEAD` にフォールバック（`commit -a` 対策）
- 対象コマンド判定を `(commit|revert|merge)` に拡張

### 3. adr-reviewer agent を新設し、chain に配線する

ADR の**記録としての質**のみを検査する。決定の是非は `architect`、生成は `adr-writer` で、
三者の境界を保つ。検査軸は 8 項目で、中核は次の 3 つ:

- **Context が検証可能な根拠を持つか** — 決定の後付け正当化になっていないか。
  「Context が chosen Decision への導入としてしか意味を成さないなら flag」
- **Alternatives が藁人形でないか** — 少なくとも 1 つは真に有力な選択肢が書かれているか
- **Consequences が両面あるか** — 利点のみの Consequences は ADR 最多の失敗形として毎回 flag

あわせて `skills/implementation-chain/SKILL.md` に 2 箇所登録する — Review / Cleanup ステップの
起動条件（`docs/adr/` を触ったとき）と、Writing Chain のルーティング表（ADR 行）。
hook・rules・skill の 3 面で同じ agent を指すことになる（コストは Consequences に記載）。

### 4. 対象外として残すもの

`.notes/`（タスク台帳）、`docs/` の adr 以外、`scheduled-tasks/`（データ）。
実測でも新ロジックの無音 6 件はこの 3 つだけだった（`.notes/TASKS.md` 4 件、
`scheduled-tasks/` 2 件）。**93% と 100% の差は意図した除外と一致している**。

### 5. 挙動を bats で固定

`tests/review-chain-notice.bats` に 16 ケース。3 区分・すり抜け経路・対象外の各パターンに加え、
本 ADR の実装中に発見した 2 件のバグの回帰を固定する（`rules/common/debugging.md`:
確定したバグは機械的ガードに変換してから完了）:

- `hooks/*.sh` を shaping 区分から除外していたため control plane の本文提示が促されなかった
- `SHAPE_RE` が行頭固定で `.claude/` overlay を検出しなかった（adr-reviewer の指摘）

## Alternatives Considered

- **閾値だけ撤廃し `CODE_RE` は据え置き** — 却下。実測で 11 → 28 件（34%）にしかならず、
  落ちている 54 件の behavior-shaping artifact がそのまま残る。最も本文提示が要る区分が漏れる
- **`CODE_RE` 拡張だけして閾値は残す** — 却下。閾値は 17 件を落としており、そのうち
  1 ファイルだけの hook 変更や 1 行の権限追加といった**小さいが control plane を触る commit**が
  含まれる。変更の大きさは review 要否の代理指標にならない
- **md を一律で対象に追加** — 却下。`.notes/` の作業メモでも鳴り、「Claude の行動を変えるもの」
  という区分の意味が失われる。93% と 100% の差を意図的な除外として保つ方が、信号の意味が残る
- **block（exit 2）に昇格** — 却下。「review を起動したか」は agent がファイル痕跡を残さない
  ため機械検証できず、block すると偽陽性で作業が止まる。なお `codex-review` だけは
  `metrics/skill-usage.jsonl` に invoke が残るので照合可能で、将来の強化余地として残す
  （ADR-0027 で言及、今回は未実装）

  > **前提失効の注記（[ADR-0034](0034-move-review-check-before-the-approval-gate.md) で追記）**:
  > 「agent がファイル痕跡を残さない」は現在は**偽**。`hooks/log-agent-usage.sh` が PostToolUse
  > (Task|Agent) で `metrics/agent-usage.jsonl` に agent 名・repo・時刻を記録しており、
  > 「codex-review だけ照合可能」の範囲は agent 全体に広がっている。**ただし block 却下という
  > 結論は 0034 でも維持**した（別の理由 —— 実装途中の停止まで止めるため、かつ
  > `additionalContext` がブロックせず届くことを実測したため）。前提は失効したが結論は同じ。
- **`.git/hooks/pre-commit` に移す** — 却下（目的が違う）。git hook は誰が打っても効くが、
  Claude の context に情報を注入できない。本 hook の目的は「Claude に思い出させる」ことなので
  PreToolUse が正しい層。**結果として Bash tool を経由しない commit（ターミナル直打ち / IDE /
  別 pane の CLI エージェント）は構造的に検出できない** — 受容する穴
- **既存 reviewer に ADR 検査軸を足す（agent を増やさない）** — 却下。`editor` に ADR 用の
  8 軸を追記すれば agent 総数は増えず、description 層の常駐も増えない。却下理由は
  **description の判別性**: `editor` は「tech article の code accuracy / AI slop / narrative flow」で
  発火する定義で、ここに ADR 軸を混ぜると 2 つの異なる文書種を 1 つの description が担うことになり、
  どちらの発火精度も落ちる（`skill-creator` の description 設計で繰り返し観測した劣化パターン）。
  加えて ADR は「先行 ADR との override 関係」という**ディレクトリ横断の検査**を要求し、
  単一ファイルを読む editor の tools（Read / Grep / Glob）では Bash による `git show` 照合ができない。
  agent 1 つ分のコストを払う判断
- **何もせず ADR-0027 の観測を待つ** — 却下。カバレッジ実測により hook が 13% しか
  鳴っていないと判明したため、観測の前提（hook が一定量鳴っている）が成立していない
- **なお ADR-0027 はこれらのうち「hook の閾値撤廃 / CODE_RE 拡張のみで対処」を却下している。**
  その却下は「**単独では**時刻の問題を解けない」という理由であり、rules 復元を否定するものでは
  なかった。本 ADR は rules 復元（0027）の上に hook 面を重ねるもので、却下された案を
  単独案として採り直したのではない

## Consequences

- **容易になる**: 発火カバレッジが 13% → 93%（同一 82 commit で再測定）。behavior-shaping
  artifact と ADR が初めて検出面に入る
- **容易になる**: `commit -a` を使っても検出が効く。ファイル種別の拡充と違い、これは
  「打ち方によって全件無効化される」経路だったので影響が種別横断
- **容易になる**: 他 repo の `.claude/` overlay も shaping として検出される。この hook が
  harness 専用でなくなる
- **容易になる**: ADR の記録品質に専任の検査層ができる。本 ADR 自身が最初の被検査対象となり、
  数値の再現不能・単位の曖昧さ・藁人形の alternative・未記載の変更を検出した（下記 References の
  レビュー結果を反映済み）
- **困難になる**: agent が 1 つ増える。`agent-stocktake` の監査対象と description 層の常駐が
  その分増える。ADR 執筆は月 2-3 本程度で、使用頻度は中位
- **困難になる**: reviewer の名簿が rules（planning.md）・skill（implementation-chain）・
  hook（review-chain-notice.sh）の **3 箇所**に載る。ADR-0027 で 2 箇所になったものが 3 箇所に
  なった。hook はメッセージ生成のため名前を持たざるを得ず、drift 検査の自動化は無い —
  reviewer を追加・改名するときは 3 箇所を同時に見る必要がある
- **困難になる**: Claude 側の注入コストが増える。実測 82 commit / 17 日 = 日次 4.8 commit、
  うち 93% が発火するので**日次およそ 4.5 回**。1 回の `additionalContext` は区分の組み合わせで
  変動し、3 区分すべてに該当する最長ケースで約 600 字（日本語なので概ね同数のトークン規模）。
  人間には表示されないが、context への注入は毎 commit 発生する
- **観測**: 発火率が上がったことで、ADR-0027 の「rules 復元だけで実行率が戻るか」という
  切り分けはできなくなった。今後測るのは**合計効果**（rules + hook）で、8 月中の feat/fix に
  対する codex-review 実行率が 54% 水準を回復するかを見る

## References

- [ADR-0027](0027-restore-review-execution-check-to-verify-gate.md) — rules 側の Review 実行確認復元。本 ADR はその hook 面（0027 の Consequences に前方参照を追記済み）
- [ADR-0016](0016-writer-agents-render-not-decide.md) — writer agent は render 専任（adr-writer と adr-reviewer を分ける根拠）
- [ADR-0015](0015-cross-agent-rules-sharing-reference-first.md) — AGENTS.md が behavior-shaping である根拠
- [ADR-0025](0025-global-vs-project-asset-placement.md) — project overlay が `.claude/` 配下に置かれる根拠
- `hooks/review-chain-notice.sh` / `tests/review-chain-notice.bats`
- `agents/adr-reviewer.md`
- `skills/implementation-chain/SKILL.md` — Review 起動条件と Writing Chain ルーティングへの登録
- `rules/common/human-gate.md` — 当時の本文提示区分。rule は ADR-0035 で退役

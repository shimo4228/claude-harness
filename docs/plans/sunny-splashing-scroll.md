# 棚卸しを「1 枚の report → 一括承認 → task branch で適用 → ff」に変える

調査: [research/2026-10-31-batch-stocktake-report.md](research/2026-10-31-batch-stocktake-report.md)

## Context

棚卸し skill 群（skill / rules / agent stocktake、rules-distill、repo-asset-stocktake、generation-audit）は非 Keep を
1 件ずつ `[y/n/skip]` で聞く（commit `f8b08bc`、ADR 無し）。さらに skill-stocktake → skill-creator の経路で §1 / §7 が
著者で止まるので、Improve N 件で判断が 2N 回になる。著者は harness 全体を一気に棚卸ししたいので、判断点を
**提案 report の承認**と**完了 report を見た ff 取り込み**の 2 回にまとめる。設計は 2026-10-31 の grill-me で確定した:

1. 全件に推奨判定・証拠・具体的変更を付けた report 1 枚。著者は直したい項目だけ書き換えて 1 回で返す。Retire も含む（git で戻せる）
2. 媒体は Artifact + `db`。判定履歴の正本は各 skill の `results.json` のまま
3. 取りまとめ役 skill `harness-stocktake` を新設。report 契約の正本をここに置き、各棚卸し skill は判定まで出して契約に渡す。単独で呼んだときも同じ契約で 1 本分の report
4. skill-creator の §1 は report 承認で代え、§2〜§6 は止めずに回す。変更は task branch に入れ、§7 は完了 report を見た ff-only 取り込み 1 回
5. 範囲: 4 本 + context-sync + repo-asset-stocktake + 新設 `hook-stocktake`（独立 skill）。generation-audit は契約に揃えるだけ
6. rules の退役: Dissolve 候補だけ、rule の有無で `claude -p` を比べる transfer 検証。verbatim の 2 rule は対象外
7. 起動: 手動 + 月 1 回 launchd（report の公開まで無人、Slack で知らせる）
8. 成功基準: 判断 2 回 / 各項目が単独で判断できる / 台帳と実物の食い違い 0 / 書き換えた判定どおりに適用
9. 古い report: 項目ごとに blob hash を持ち、適用時に不一致の項目だけ評価し直す。判定が変わったら完了 report の「未決」へ。曖昧なコメントも「未決」

## 代理で決めたこと（plan 承認で一緒に確認）

- **媒体に依存しない契約**: rules-stocktake / agent-stocktake / rules-distill は単独の公開 repo にも同期される。契約の正本は項目 schema（JSON）とし、この harness では Artifact に描画、Artifact が無い環境では `.notes/stocktake/YYYY-MM-DD.md` に同じ schema で書く
- **review-when-watch を rules に広げる**: 毎日動く watch（ADR-0080）は RFC と ADR の review-when だけを見ている。rules の `<!-- review-when: -->` も照合対象に足し、当たった rule を次の report で Stage 2 の最初の問いに使う。「rules の退役を見る仕組み」の、気づく側にあたる
- **plan ファイル名**: plan mode が割り当てた `sunny-splashing-scroll.md` のまま使う

## 手順

### 1. 契約と ADR

- `skills/harness-stocktake/SKILL.md` を skill: `skill-creator` 経由で新設する（skills.md の命令配線）。持つもの:
  - **項目 schema**: `id` / `source`（どの棚卸しか）/ `target`（path）/ `blob`（`git hash-object`）/ `verdict` / `reason`（各 skill の Reason quality 規約）/ `evidence`（No 判定 + 1 行証拠）/ `change`（diff 要約、Improve は skill-creator の intent packet）/ `impact`（依存先）/ `conflicts`（他項目 id）/ `decision`（既定 = 推奨）/ `note`（著者コメント）
  - **並び**: Retire / Dissolve → Merge / Retire-and-absorb → Demote → Improve / Update → distill の Append → Keep（折りたたみ）
  - **集約後の衝突検査**: Demote で増える skill、Retire で切れる参照（rules の ``skill: `x` ``、agents、MEMORY）、同じ file に当たる複数項目
  - **適用手順**: worktree の `stocktake/<date>` branch → 項目ごとに blob 照合 → 適用（rules / agents / hooks / docs はその場で、skills は skill-creator の report 経路）→ source ごとに commit（verify を通す）→ 台帳更新 → 完了 report（同じ Artifact に適用済み / 著者が書き換えた項目と diff の対応 / 未決）→ 著者の GO で main に ff-only
  - **単独呼び出し**: 各棚卸し skill から呼ばれたときは対象 1 本分で同じ手順
  - Artifact ページの雛形 `skills/harness-stocktake/templates/report.html`（実装前に skill: `artifact-capabilities` と `artifact-design` を読み、`db` の形を決める）
- ADR を 1 本（skill: `adr-writer`）: confirm-each（`f8b08bc`）の置き換え、skill-creator §1 / §7 の代替、boundary.md の「検収済み task branch の ff-only」との接続。agent: `adr-reviewer` を通す

### 2. 既存 skill を契約に揃える

同じパターンを当てる: Consolidation / User Review 節の逐次 `[y/n/skip]` を消し、「判定と項目を出して skill: `harness-stocktake` の契約で承認・適用する」に置き換える。判定・Reason quality・台帳の規約は各 skill に残す。

- `skills/skill-stocktake/SKILL.md`（Phase 5）、`skills/rules-stocktake/SKILL.md`（Phase 4、Design note 2 と `MAINTENANCE.md`）、`skills/agent-stocktake/SKILL.md`（Phase 4）、`skills/rules-distill/SKILL.md`（Phase 3。hard gate は「承認済み report の項目だけ適用」に言い換える）、`skills/repo-asset-stocktake/SKILL.md`、`skills/generation-audit/SKILL.md`（:103, :117）
- `skills/context-sync/SKILL.md`: harness に対して回すときは、編集と新規作成の候補を項目として report に出す（単独で回すときの既定は今のまま）
- `skills/skill-creator/SKILL.md`: 入口に「承認済み report の項目から呼ばれたとき」の経路を足す — §1 は項目の intent packet で済み、§4 の草稿ゲートで 2 回通らなければ未決として返し、§7 は完了 report に回す
- 各 skill は skill-creator の §4 草稿ゲートを通す。公開 repo への同期（skill: `harness-sync`）は著者に渡す

### 3. 新しく作る

- `skills/hook-stocktake/SKILL.md`（skill-creator 経由）: 対象は `hooks/*.sh` と `scripts/hooks/*`。見る点は `settings.json` の配線（孤児・settings 側に埋め込まれたロジック）、発火記録（`metrics/*.jsonl` があるもの）、`tests/*.bats` の有無、substrate による吸収（Dissolve）、`security.md` の harness 脅威面。判定語彙は 3 本の stocktake と同じ。台帳は `skills/hook-stocktake/results.json`
- rules-stocktake の transfer 検証: Dissolve 候補について、rule を外した状態と残した状態で同じ場面を新しい `claude -p` で走らせて比べる script（置き場所は `skills/rules-stocktake/scripts/`）。外し方（一時的な `CLAUDE_CONFIG_DIR` か `--settings`）は最初に実測で決める。子が user 設定を継承する罠（memory `reference_claude_p_child_inheritance`）に従い、設定は隔離し、失敗したら大きく失敗させる。結果は項目の `evidence` に入れる
- `skills/review-when-watch/scripts/watch.py`: rules の review-when を照合対象に足す。テストは `skills/review-when-watch/tests/`

### 4. 台帳の機械検査

- `scripts/hooks/harness_lint.py` に「skill / rules / agent / hook の `results.json` のキー = ディスク上の実物」の検査を足す。golden は `tests/golden/harness-lint/`、回帰は `tests/golden-harness-lint.bats`
- 現状の台帳は食い違っているので、lint は警告で入れる。手順 6 の初回実行で 0 件にしてから error に上げる

### 5. 月 1 回の定期実行

- `scripts/launchd/com.shimomoto.harness-stocktake.plist` + prompt ファイル。起動は既存の `scripts/triage-tick.sh --prompt-file`（find → spawn → prompt → 失敗時 Slack）を使う
- 無人で回すのは report の公開と Slack 通知まで。plist の登録は著者が行う
- 調査で残った不明点「spawn-session の session で Artifact が使えるか」を dry-run で確かめる。使えなければ `.notes/stocktake/` に書き、公開は著者がいる session に回す

### 6. 初回の全体実行

`/harness-stocktake` を対話の session で 1 回回し、成功基準 4 つを確かめる。rules の台帳の食い違いはここで解消する。

## 実装 chain

- 種別は feat。実行者と reviewer は skill: `implementation-chain` に従って最初に決める
- 最初の commit は plan と調査 report だけ（`docs(plan): batch-stocktake-report`）。後続の commit 本文に `Plan:` 行を入れる
- hooks / scripts への変更（手順 3・4）があるので、security review の条件は implementation-chain の Security Review 行で判定する

## Verification

- `python3 scripts/hooks/harness_lint.py` と `bats tests/`（golden 含む）、`.claude/verify.sh`
- `skills/review-when-watch/tests/` と `skills/skill-stocktake/tests/` の pytest
- 単独呼び出しの確認: `/rules-stocktake` を 1 回回し、Artifact に report が出る / 途中で `[y/n]` を聞かない / 書き換えた判定どおりに branch に入る / 完了 report → ff で取り込める、を見る
- transfer 検証の確認: 吸収済みとわかっている挙動を 1 つ選び、外した場合と残した場合で差が出ないことを確かめる。比較対象として、差が出るはずの rule 1 本でも走らせる
- 手順 6 の初回の全体実行で、成功基準 4 つを確かめる（judge には report だけを渡し、各項目が単独で判断できるかを問う）

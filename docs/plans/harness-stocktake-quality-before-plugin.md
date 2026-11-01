kind: plan
# harness-stocktake の品質修正（plugin 化の前）

as-of: 2026-11-01。親 plan [enumerated-petting-beaver](enumerated-petting-beaver.md) の Stage 0 と Stage 1（plugin 化）の間に入れる。
根拠は [2026-11-01-premise-test.md](research/2026-11-01-premise-test.md)（24 run の実測）と
[2026-11-01-doctor-comparison.md](research/2026-11-01-doctor-comparison.md)。対象は `skills/harness-stocktake/` と source skill 7 本、
`scripts/isolated-dry-run.sh`。状態: 著者の承認待ちの草案。

## 目標

plugin の利用者が最初の 1 回で「3 分で最初の指摘、10 分で report 全体」を得て、その指摘が当たっている。Stage 0 で前半は
成り立った（最初の非 Keep 中央値 134.5 秒、20/20 が 200 秒以内）。後半と「当たっている」が未達か未測定。

## 修正項目（優先順）

### 1. Phase 2–3 を短くする（report 全体 10 分）

実測: 全 source の section は 20 本すべて 707 秒以内に揃う。最後の section から report.md までが P01 377 秒、P02 405 秒、
P06 771 秒、P11 1065 秒。P19 は 1800 秒 timeout、P16 は report を組まずに終了。10 分以内に report が揃ったのは 12/20。

- cross-check（Phase 2）は非 Keep 項目どうしの衝突だけを見る。Keep は読まない
- report.md の組み立ては決定的な script にする: `sections/*.md` を表の順に連結し、Phase 2 の衝突と `order` を追記する。
  model が表を書き直さない（Stage 0 の `render.py` が叩き台。scratchpad にあり、repo には無い）
- Phase 2–3 に time cap を置く。cap を越えたら衝突の追記なしで script の連結だけを report.md にして終える

完了: 公開 20 本の再走で report.md が 20/20 で書かれ、10 分以内が 16/20 以上。

### 2. run を report.md なしで終わらせない

実測: P16 で main loop が「skills source の完了を待つ」と書いて turn を終え、`-p` の process は report.md を書かずに rc=0 で
終わった。

- SKILL.md に終了条件を書く: run は report.md を書いた時点で終わる。source subagent は foreground で待つ
- `isolated-dry-run.sh` は END の前に report.md の有無を見て、無ければ items から組み立てた report を `report.assembled.md` に
  書き、`timeline.tsv` に印を残す（測定器としての穴埋め。skill 側の修正の代わりにはしない）

完了: bats に「report.md が無い run で assembled が書かれる」を追加。再走で report 未作成 0 件。

### 3. 大きい skill library を確実に分割する

実測: skills 139 / 383 / 52 の 3 本で、12 本ずつの分割が一度も起きなかった（items-skills.json が 1 本）。P16 は skills の
非 Keep 209 件がほぼ一つのパターン（repo の仕事と関係しない汎用 skill の一括同梱）。

- 分割を model の判断でなく手順にする: main loop が dispatch の前に Glob で skill 数を数え、12 を越えたら batch 数を決めて
  一度に dispatch する
- 同じ理由の Retire が多数並ぶときは 1 項目にまとめる（`target` は glob か一覧、`evidence` に件数）。report の行数と
  判断回数を減らす

完了: 再走で 3 本とも `items-skills-<k>.json` が複数。P16 の skills の非 Keep 行が 20 以下。

### 4. 指摘が当たっているかを測る

Stage 0 で測ったのは「読んで決められるか」だけで、指摘の正しさは測っていない。判定役も同系統の model が 1 回ずつ。

- 公開 20 本から非 Keep を層別に 60 件抜き、別 agent が repo を開いて事実を照合する（参照が本当に切れているか、
  使われていないか）。正答率を source 別に出す
- judge を 2 回走らせ、decidable の一致率を出す
- 驚きの閾値「5 件」は 19/20 が越えて区別しない。Stage 3 の判定は source 別の非 Keep 率・正答率・report 到達時間に置き換える
  （親 plan の Stage 3 判定の改訂案として著者に渡す）

完了: 正答率と一致率を `docs/plans/research/<date>-precision.md` に記録。source 別正答率 80% 未満の source は 1 に戻って直す。

### 5. native と並べて見せる

比較で native だけが拾ったのは 28 件中 22 件（plugin / MCP の未使用、prompt-audit の書き方）。互いに補い合う。

- report の末尾に「native が見るもの」を 1 段落置き、`/doctor` と `/doctor prompt-audit` を案内する（実行はしない）

### 6. 文書と実物のずれを直す

- 親 plan Stage 0 手順 4 の「`--bare` か `--settings`」: `--bare` は API key だけを受け OAuth を受けない。隔離は
  `--restricted` と cwd 分離と書き換える
- 親 plan Stage 0 手順 5 の「assets を先頭に」: 実測で最も遅い source。commit 44e05e3 の順序に合わせる
- SKILL.md の最終版に skill-creator の草稿ゲートを 1 回通す（Stage 0 では 2 回とも Fix で終わり、反映後の確認をしていない。
  44e05e3 の並べ替えもゲート未通過）

## 実行の順

1 → 2 → 3 は同じ SKILL.md を触るので 1 つの build session で順に。4 は 1–3 の後の再走と同時に別 session で回せる（読むだけ）。
5・6 は小さく、1–3 の session の最後に入れる。再走は公開 20 本 + 著者 4 本、`isolated-dry-run.sh` で Stage 0 と同じ条件。
費用の目安は Stage 0 と同程度（API 換算 1 本 $4–21、subscription 枠）。

## 失効条件

- native の `/doctor` 系が横断判定か branch 適用を持った → 親 plan の失効条件に従い止まる
- 4 の正答率が全 source で 60% 未満 → plugin 化を止め、source skill の判定基準から見直す

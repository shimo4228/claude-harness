<!-- origin: shimo4228 -->

# ADR レビュー頻出指摘カタログ（書き時の予防用・日付つき事例集）

adr-reviewer の指摘履歴（contemplative-agent の git 履歴 + harness の事例、2026-08-26 採掘）から
蒸留した頻出パターン。**役割は予防のための事例集** — レビュー基準の正本は
`~/.claude/agents/adr-reviewer.md`、機械チェックの正本は `scripts/adr_lint.py`。ここは
「書く前に自己点検する具体例」だけを持ち、基準を複製しない。

各事例は commit 参照つきの日付つき仮説として読む（akc-cycle の却下記録の読み方と同じ）。

## 1. 引用した ADR の誤引用

引用先の番号が実在し、**引用した内容がその ADR に実際に書かれているか**を書き時に開いて確認する。
記憶で引用した ADR 番号は高頻度で間違う。

- 事例: CA `0ce5430` (2026-08-24) — ADR-0069 の Review-when 追補が adr-reviewer に差し戻し。
  ADR-0072 の誤引用と 0044 の誤参照を除去、引用元の主張強度を原文に復帰

## 2. surviving scope の置き場所（partial supersede）

forward half（新 ADR 側）には「自分が退役させたもの」だけを書く。**何が生き残るか**は
backward half（旧 ADR 側）にだけ書く — 後続の partial supersede が重なると forward 側の
生存記述は日付時点で偽になる。

- 事例: CA `423c732` (2026-08-15) — 新設 5 件中 4 件で surviving scope が誤り。
  CA `docs/adr/README.md` の「Which half states which scope.」節はこの指摘の産物

## 3. 造語の出所

自分が作った語を、引用元がその語を使っているかのように書かない。引用元に無い語は
「本 ADR の呼称」と明示するか、引用元の実際の語で書く。

- 事例: CA `008ac94` (2026-08-15) — "Step 0" は ADR-0060 の造語で ADR-0026 のどこにも無い。
  実体（Phase 2 の distill.py 半分）で書き直し

## 4. full vs partial supersede の判定根拠

supersede の全部/一部は印象でなく**コードの実在**で判定する。旧 ADR の前提とする機構が
src/ に残っていなければ full。

- 事例: CA `008ac94` (2026-08-15) — ADR-0027 を partial と書いたが、NOISE_THRESHOLD /
  re_classify 等の不在を根拠に full と訂正。連鎖して edge 定義の HIGH 2 件も同時修正

## 5. gitignored パス参照の禁止

ADR 本文から `.notes/` 等の gitignored パスを参照しない。根拠が要るなら成果物を
`docs/evidence/` へ昇格するか、文言をパス非依存に書き換える。

- 事例: CA `25b88f9` (2026-08-15) — 機械スキャンが 20 箇所検出、3 件を evidence 昇格・
  7 箇所を書き換えで一括クローズ

## 6. 数値の出典と分母

正本は adr-reviewer 基準 §6（Numeric Claims）。書き時の要点だけ: 数値にはコマンド/ログ/
測定日を添え、百分率は分母を書く（"54% (45/83)"）。drift する数（ファイル数等）は
測定日つきスナップショットと明示する。

## 7. カウント条件の固定対象（Review-when を書くとき）

「N 回連続」「30 日で M 件」型の失効条件は、**何が固定なら比較可能か**（検査対象の節・
判定器・slot）を名指しする。名指しできなければ測定不能 — イベント条件か著者判断に書き換える。

- 事例: harness ADR-0046 (2026-08-22) — ゲートの観測 0 回のまま対象と判定器が両方入れ替わり、
  カウントが無意味化。adr-reviewer 基準 §1 に昇格済み

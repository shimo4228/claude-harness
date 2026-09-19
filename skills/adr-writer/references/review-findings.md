<!-- origin: shimo4228 -->

# ADR レビュー頻出指摘カタログ（書き時の予防用・日付つき事例集）

adr-reviewer の指摘履歴（contemplative-agent の git 履歴 + harness の事例、2026-08-26 採掘）から
蒸留した頻出パターン。**役割は予防のための事例集** — レビュー基準の正本は
`~/.claude/agents/adr-reviewer.md`、機械チェックの正本は `scripts/adr_lint.py`。ここは
「書く前に自己点検する具体例」だけを持ち、基準を複製しない。

各事例は commit 参照つきの日付つき仮説として読む。

**機械検査との対応（2026-09-16、ADR-0071）.** §1 の番号実在は `adr_review_evidence.py` の
`refs`、§2 / §4 の旧 ADR 側の注記の有無は `relations.targets[].annotation_lines`、§5 は
`paths.flagged` の `ignored` / `outside_repo`、§6 の分母は `numbers.percent_without_denominator`、
§7 の count 条件の検出は `review_when.items[].count_condition` が出す。**引用内容の一致（§1 後半）、
surviving scope の置き場所（§2）、造語の出所（§3）、full / partial の判定根拠（§4）は script の外**
— evidence の行を開いて自分で読む。

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

## 8. 記録と実体の diff の範囲不一致

Decision に書いた変更と、同じ commit に入る diff を両方向で照合する。ADR が触れない変更が同じ
diff に混ざる形が最頻（別作業の巻き込み）。書き時に `adr_review_evidence.py --diff worktree` の
`diff_scope.changed_not_mentioned` を見て、Decision に足すか commit を分ける。

- 事例: harness ADR-0057 (2026-08-28) — 同一 diff に ADR が言及しない SKILL.md 変更が混在。
  ADR-0066 (2026-09-14) — Decision 5「消費者の書き換え 5 か所」に対し実体は 6 ファイル。
  2026-08-26〜09-15 の 24 報告中 8 報告で反復

## 9. 巻き戻しコストと第 2 の記録場所（Consequences）

削除・退役を含む Decision には巻き戻しコスト（git 管理外の資産は復元不能）を、実測値を
SKILL.md 等にも書いた Decision には「第 2 の記録場所」とその drift の扱いを Consequences に置く。

- 事例: harness ADR-0065 (2026-09-14) — memory 14 ファイル削除の退避先が session scratchpad
  で、ベースラインがセッション終了後に再現不能。ADR-0056 (2026-08-28) — 82 repo / 104 config の
  実測が ADR・SKILL.md・index 行の 3 箇所に載り、正本が未指定。24 報告中それぞれ 6 / 7 報告で反復

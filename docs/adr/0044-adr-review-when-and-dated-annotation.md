# ADR-0044: ADR を日付つき仮説として持つ — `## Review-when`（失効条件）節と旧 ADR への日付つき注記、読み方 protocol を拘束箇所へ

## Status

accepted

## Date

2026-08-19

## Context

著者の観測（2026-08-19 の申告）: harness は過去 ADR に書いたことにとらわれ、自由なアイデアを
出せないことが多い。**この害そのものの事例記録は無い** — session や commit に紐づく「ADR を
理由にアイデアを止めた」事例は 1 件も残っておらず、著者の主観的観測のみである。先行する信号は
2026-08-14 の著者指示（`akc-cycle.md` に「ADR も足場である」を追記）で、宣言から 5 日後も観測が
続いていることが本 ADR の起点。したがって Review-when の第 1 トリガーの**ベースラインは
「記録された事例 0 件（2026-08-19）」**で、以後は事例が出た時点で日付つきで残す。並行して進めて
いる desire-frontier repo（`~/MyAI_Lab/desire-frontier`、ADR ディレクトリ無し）はそこを打破
できている。desire-frontier の機構は宣言ではなく構造
（agent 調査で file:line 確認済み）で、次の 5 点からなる:

- 書く時点で失効条件を予約する（`concepts.md:119`「失効条件：…証言が 1 本出たら反故」）
- 反証は削除でなく同じ行に日付つきで「一段弱まった」と追記する（commit `1562939` は旧文を
  残して追記のみ）
- 対抗モデルを閉じず節として維持し「傾く」止まりにする（`concepts.md:124-147`）
- 全見出しに生年月日を付け「仮」を既定にし、固定は外部ゲート（graduation）に委ねる
- 固定するのは結論でなく手続きの規律だけ（`concepts.md:168-172`）

global harness 側の現状: `rules/common/akc-cycle.md:18-24` に「ADR も足場である／supersede
が正常系」の宣言（2026-08-14 著者指示）だけがあり、機構が無い。ADR template
（`docs/adr/README.md`、`agents/adr-writer.md`）に失効条件の欄が無い。rules 層には
`review-when:` コメントが [ADR-0021](./0021-rules-metadata-and-premise-lint-gates.md) で入り、
`harness_lint.py` が存在を、`rules-stocktake` が内容を検査しているのに、ADR は対象外だった。
[ADR-0041](./0041-file-review-findings-on-a-verified-premise.md) と
[ADR-0043](./0043-task-triage-loop-judge-build-human.md) だけが Consequences 内に
「失効条件:」を手書きしている（43 件中 2 件）。

43 ADR 中 39 が accepted（0028 の「accepted — 一部 superseded」を含む）、4 が superseded
（0019 / 0027 / 0030 / 0034）。supersede **事象**は [ADR-0035](./0035-commit-review-hook-and-rules-rightsize.md)
の 1 回で、その 1 回が 4 件を一括した（2026-08-19 実測:
`grep -h -A2 "^## Status" docs/adr/00*.md | grep -v "^## Status\|^--\|^$" | sort | uniq -c`）。
旧 ADR への日付つき注記は [ADR-0018](./0018-rules-rightsize-for-claude5.md) §Consequences
（`（2026-08-13 注記: …）` — 日付あり・ADR 番号なし）と
[ADR-0028](./0028-review-notice-full-scope-and-adr-reviewer.md)
（`> **前提失効の注記（ADR-0034 で追記）**` — ADR 番号あり・日付なし）に非公式に存在するが、
形式が揃っておらず規約も無い。本 ADR の `> **注記（YYYY-MM-DD, ADR-NNNN）**` は両者の和集合で、
どちらとも一致しない — backfill しない判断はこの不揃いも理由の一つ。

最も強い拘束箇所は `skills/grill-me/SKILL.md` rule 3 "Never re-ask a decision an existing
ADR already settles; if the plan contradicts one, present it as a conflict"。
`AGENTS.md:9`「変更前に関連 ADR を確認する」。`agents/architect.md` は sunk cost を無視するが
ADR を sunk cost として名指ししていない。

~/.claude は単一の心の足場（memory: concept-dissolution-boundary-immutability — single-mind
scaffold は溶ける）なので、ADR を軽く持つことに構造上の障害は無い。

## Decision

1. ADR template に `## Review-when` 節（失効条件 — この判断を反故／弱める観測・前提の失効を
   1〜3 行）を `## Decision` の直後、`## Alternatives Considered` の前に追加する。ADR-0044
   以降必須、0043 以前は backfill しない。書けなければ「無し — 恒久判断ではなく記録」と明記
   する。節名は rules の `review-when:` と同じ語彙にし、両層を同じ grep で引けるようにする。
2. `## Alternatives Considered` は却下理由に加えて「未決 — 再訪条件: …」を許す。生きている
   対抗案は閉じない。
3. 新しい観測・ADR が旧 ADR を部分的に弱める（supersede しない）ときは、Status を変えず、
   旧 ADR の該当節の下に `> **注記（YYYY-MM-DD, ADR-NNNN）**: …` を追記する。削除しない。
   これは main loop の明示ステップであり、`adr-writer` agent は既存 ADR に触らない
   （[ADR-0016](./0016-writer-agents-render-not-decide.md) 不変）。Status enum に `weakened`
   は足さない。
4. 読み方 protocol を拘束箇所へ入れる。`rules/common/akc-cycle.md` の「ADR も足場である」節に
   「ADR は日付つき仮説。Date と Review-when（無い旧 ADR は Context の前提と Date で重み）を
   先に見る。失効条件が発火した・前提が消えた ADR に拘束力は無い — 衝突は supersede 候補として
   提示し、旧 ADR に日付つき注記を残す」を追記する。`skills/grill-me/SKILL.md` rule 3 を
   「ゼロから再質問はしないが ADR は日付つき仮説として読み、衝突時は前提 Z がまだ成立するかを
   問い、アイデアの展開は止めない」に書き換える。`AGENTS.md:9` に一句、`agents/architect.md`
   に「既存 ADR は prior context であって veto ではない — 同じ zero-base test を適用する」を
   1 項目追加する。**protocol の正本は `akc-cycle.md` の 4 行だけ**で、他の 4 箇所
   （grill-me / AGENTS.md / architect / `docs/adr/README.md` template 前文）は 1 句の参照に
   留め、drift したら正本に合わせる。
5. `scripts/hooks/harness_lint.py` に `lint_adr_review_when`（`docs/adr/NNNN-*.md` の
   NNNN >= 0044 に `## Review-when` 見出しがあるかの存在チェックのみ）を追加し、
   `tests/harness-lint-precommit.bats` に 3 ケース（0044 以降で無し → exit 3 / あり → clean /
   0043 以前で無し → clean）を足す。内容の評価（観測可能な条件か、注記の存在）は
   `agents/adr-reviewer.md` の checklist に置く（ADR-0021 の分業: 存在 = code、内容 = LLM）。
6. 7 節化に伴い次を更新する: `skills/adr-writer/SKILL.md`（入力 7 個、edge case に部分弱化の
   注記行、Boundaries を明示 2 ステップだけ許す形に）、`agents/adr-writer.md`
   （template・入力・render 規則）、`agents/adr-reviewer.md`（7 節、Review-when の観測可能性、
   未決の対抗案は藁人形でない、注記の存在）、`skills/context-sync/SKILL.md`（7 入力、
   Review-when 発火済み ADR の注記チェック）、`skills/adr-writer/evals/evals.json`。

> **注記（2026-08-26, ADR-0051）**: Decision #6 が `agents/adr-reviewer.md` へ置いた
> 7 節存在チェック（および Status enum / Date 書式の目視項目）は、ADR-0051 で
> `skills/adr-writer/scripts/adr_lint.py` へ移した。adr-reviewer に残るのは意味的項目
> （Review-when の観測可能性・注記の存在・藁人形判定）のみ。Decision #5 の
> `lint_adr_review_when` は残置（重複解消条件は ADR-0051 Review-when）。

## Review-when

grill-me / adr-reviewer / plan が Review-when と Date を読まずに旧 ADR を conflict や veto
として提示した事例が出たら、rule 層の protocol が効いていない — 表現を命令形に強めるか、
位置を planning.md へ移すことを検討する。新規 ADR 3 件連続で Review-when が「無し」になったら、
節を Consequences 内の任意項目へ降格する（0041/0043 の形へ戻す）ことを検討する。substrate が
決定記録の鮮度管理（日付・失効条件の照合）を native に持ったら downward dissolution の対象。

## Alternatives Considered

### 何もしない（`akc-cycle.md` の宣言だけで運用を続ける）

宣言は 2026-08-14 から常駐していたが、著者の観測は 08-19 も続いている。事例記録が無いので
「宣言が効かなかった」とは断言できないが、宣言単独で足りる根拠も無い。desire-frontier では
宣言でなく構造が効いている（Context）ので、構造側を試す。却下。

### 読み方だけ変える（rule / grill-me / architect のみ、template は触らない）

既存 43 件には即効くが、新 ADR は失効条件を持たないまま増える。失効条件は書いた時点でしか
捕捉できない（ADR-0021 と同じ論理）ので却下。

### `### Review-when` を Consequences 内の小見出しに置く（ADR-0041 / 0043 の現行形）

節数の文言更新が不要だが、一様に grep できず、最長の節の後ろに埋もれ、「先に読む」protocol
と位置が一致しない。却下。

### Status に `weakened` を足す

enum を増やし状態遷移の churn を生む。日付つき注記が同じ情報を場所つきで残す。却下。

### ADR を廃止し desire-frontier のように仮説台帳だけにする

未決 — 再訪条件: Review-when 導入後も「ADR に縛られる」観測が続いたら再訪する。~/.claude は
single-mind scaffold なので溶かすこと自体は可能。

## Consequences

### Positive

- 失効条件が書いた時点で捕捉され、rules と ADR が同じ `review-when` 語彙で引ける
- 旧 ADR の弱化履歴が削除されずその場で読める（desire-frontier の (b) と同形）
- 拘束箇所（grill-me / AGENTS.md / architect）が「override するか」の問いから「前提はまだ
  成立するか」の問いに変わる
- 対抗案を「未決」のまま ADR に残せる（desire-frontier の (c)）

### Negative

- 7 節化の文言更新箇所が多い（agent / skill / reviewer / context-sync / evals）— 一括で更新
  したが、次に節を触るときも同じ数の箇所を追う
- 公開 copy `~/MyAI_Lab/claude-harness/README.md`（"6-section ADR body"）は次の
  `harness-sync` まで drift する
- ADR を書くとき入力が 1 つ増える
- 旧 43 件は Review-when を持たないまま。読み方 protocol（Context の前提 + Date）に依存する
- 常駐 rules 層が 4 行増える（`akc-cycle.md`）。読み方 protocol は正本 1 + 参照 4 箇所の
  多重定義で、CLAUDE.md の「二重定義は必ず drift する」の対象になる — drift 時は正本に合わせる

### Neutral / Follow-ups

- ADR-0021 の review-when 語彙を ADR 層に拡張する。ADR-0016（writer は render 専任）は不変。
  supersede する ADR は無い
- [ADR-0018](./0018-rules-rightsize-for-claude5.md) / ADR-0035 の rules 採用基準（環境固有の
  事実・配線・罠。手順は skill）との関係: `akc-cycle.md` へ足す 4 行は「ADR 層をどう読むか」
  という**配線**として置く。手順（何をどう書くか）は `adr-writer` skill / agent と template に
  あり、rules には移していない。両 ADR の基準は弱めないので注記は付けない
- [ADR-0028](./0028-review-notice-full-scope-and-adr-reviewer.md) が新設した adr-reviewer の
  checklist は 7 節化で拡張される（弱化ではない）
- 本 ADR が `## Review-when` を持つ最初の ADR
- `harness-sync` で公開 copy を同期する（別セッション）
- 他 repo（AKC 等）には template が `adr-writer` agent 経由で効くが、既存 ADR は触らない

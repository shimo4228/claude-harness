# ADR-0089: 新しい ADR は 3 条件の積を満たす判断だけに書き、満たさない更新は旧 ADR への注記で済ませる

## Status

accepted — partially-supersedes [ADR-0072](./0072-retire-adr-writer-agent-and-narrow-adr-filing.md) Decision 2（起票の 2 条件）
と Decision 3（rule に起票条件を 2 文足す）。ADR-0072 の Decision 1・4・5・6 は対象外。ADR-0072 に注記する

## Date

2026-10-07

## Context

- ADR-0072 の Review-when は「2026-10-19 時点で、2026-09-19 以降に追加された ADR が 15 本を超えていたら 2 条件が
  効いていない」とし、計器を `git log --diff-filter=A --since=2026-09-19 --format=%h -- 'docs/adr/0*.md' | wc -l`
  と定めた。2026-10-07 に実行して 19 本（ADR-0072 自身を含む。除けば 18 本）。判定期日より 12 日早く閾値を超えた
- 18 本の Status 行を読むと、13 本（0073、0076〜0084、0086、0087、0088）が旧 ADR の置き換えか部分弱化を名指す
  — 起票させたのは条件 (b)（旧 ADR の supersede / 注記）で、旧 ADR を名指さないのは 5 本（0070、0071、0074、0075、
  0085）。harness の機構はほぼすべて ADR を持つので、機構を触る変更は (b) を経由して新しい ADR を 1 本生む。
  (a) だけを絞っても本数はほとんど減らない
- skill `grill-me` の ADR test（戻しにくい / 文脈なしでは意外 / 本物の代替案の間のトレードオフ。3 つすべてで
  起票を提案。由来は `mattpocock/skills`）は ADR-0072 の条件と食い違っていた。2026-10-07 の skill-stocktake は
  この食い違いを矛盾として挙げ、台帳 `skills/skill-stocktake/results.json` には逆向きの推奨（grill-me の test を
  adr-writer への pointer に置き換え、現行の条件に合わせる）を記録した。著者はその推奨を採らず、grill-me の
  3 条件を正本にする側を選んだ（2026-10-07）。「戻しにくい」は git で戻せるかでなく、戻すときに他の artifact
  や公開物も直す必要があるかで読む

## Decision

1. 新しい ADR を書くのは、判断が次の 3 条件を**すべて**満たすときだけにする。ADR-0072 Decision 2 の条件 (a)
   はこの積で置き換える:
   - **戻しにくい** — 戻すと他の artifact（skill・rule・hook・script）や公開物も直す必要がある。git で
     revert できるだけでは満たさない。harness の変更の多くはこれを満たすので、この条件は範囲が局所的に
     閉じる変更を外す役にとどまる
   - **文脈なしでは意外** — 後の読者が「なぜこうなっている？」と問う
   - **本物のトレードオフの結果** — 実在する代替案の間で選んだ。ふるいとして効くのは主にこの条件と前の条件
2. ADR-0072 Decision 2 の条件 (b)（旧 ADR の supersede / 部分弱化）は、それ単独では新しい ADR を要求しない。
   旧 ADR を置き換える・弱める判断も、Decision 1 を満たすときだけ新しい ADR にする。満たさないときは、旧 ADR
   の該当節に `> **注記（YYYY-MM-DD, commit「<subject>」）**: <何が変わり、何が残るか>` を足し、判断は同じ
   commit の本文に `Context:` / `Decision:` / `Review-when:` の 3 行で残す。`<subject>` は `git log --grep` で 1 件に
   決まる commit の件名にする（同じ commit の中で書くので hash は持てない）。旧 ADR の Status は変えない
3. どちらにも当たらない判断は commit 本文の 3 行で残す。後に supersede されるか他の artifact から引かれたら、
   その時に commit を引用して ADR へ昇格する（ADR-0072 のまま）
4. 起票条件の正本は skill `adr-writer` の When to Use に置く。`rules/common/akc-cycle.md` の「ADR の扱い」は
   条件を書き写さず、正本への pointer だけを持つ（ADR-0072 Decision 3 の 2 文を置き換える）。skill `grill-me`
   は自前の条件を持たず、skill `adr-writer` の When to Use を参照する。注記の書式に commit を出典とする形が増えるので、
   `skills/adr-writer/scripts/adr_review_evidence.py` の `_ANNOTATION_WELL_FORMED_RE` をこの形も受けるよう広げる
   （回帰は `skills/adr-writer/tests/test_adr_review_evidence.py`）。adr-writer の注記の書式は `注記` に揃える
5. ADR-0072 の Decision 2 の下と、Review-when の 1 項目目の下に日付つき注記を足す

## Review-when

- 2026-12-07 に、2026-10-07 以降に追加された ADR の数
  （`git log --diff-filter=A --since=2026-10-07 --format=%h -- 'docs/adr/0*.md' | wc -l`）が 10 を超えていたら、
  3 条件が効いていない — 条件の書き方を見直す。10 は直近 18 日の約 1 本 / 日を約 1 本 / 週（61 日で 8.7 本）
  に下げる狙いから置いた。計器のコマンドと期間を固定し、判定者はその時点の skill-stocktake か rules-stocktake
  を回す判断役。同じ時点で、旧 ADR に足された注記の数
  （`git log --since=2026-10-07 -p -- 'docs/adr/0*.md' | grep -cE '^\+\s*> \*\*(注記|Note)'` — 字下げと英語の
  `Note` も数える。`adr_review_evidence.py` の `_ANNOTATION_RE` と同じ範囲）も読み、本数の減少が注記へ
  移っただけかを見る
- 2026-12-07 までに、機構変更の経緯を追うときに commit 本文と注記しか無く、著者が「経緯が追えない」と 2 回
  観測したら（記録先: その場で書く ADR の Context か `.notes/TASKS.md`）、条件を広げる（ADR-0072 の Review-when
  2 項目目を引き継ぎ、期限を本 ADR の観察期間に合わせて 2026-12-19 から 2026-12-07 へ前倒しする）
- 3 条件をすべて満たすのに注記か commit 本文だけで済まされた判断を、stocktake か adr-reviewer が見つけたら、
  条件の文言を締める
- substrate が決定記録の作成・supersede を native に持ったら、起票条件ごと溶かす

## Alternatives Considered

- **条件 (a) のまま 2026-10-19 の判定を待つ** — 却下。計器は判定期日より前に閾値を超えており、待っても読みは
  変わらない
- **条件 (a) だけを 3 条件に絞り、(b) は新しい ADR を要求したまま残す** — 却下。超過 18 本のうち 13 本は (b)
  経由で、(a) を絞っても本数がほぼ減らない
- **(b) を外し、旧 ADR に注記もしない** — 却下。前提の崩れた ADR が注記なしに残り、経緯を読む人が古い記述を
  正しいと読む
- **「戻しにくい」を字義どおり（git で戻せない）に読む** — 却下。harness の変更はすべて git で戻せるので、
  ADR がほぼ書かれなくなる
- **grill-me を現行の条件 (a) に合わせる**（skill-stocktake の台帳の推奨）— 却下。計器が示したのは現行の条件が
  効いていないことで、合わせると効かない基準が 2 か所に広がる

## Consequences

### Positive

- 機構を触るたびに新しい ADR が 1 本増える経路が閉じ、ADR の index が 3 条件を満たす判断に絞られる見込み
  （実際に減るかは Review-when の 1 項目目で読む）
- adr-reviewer を回す回数が減る（skill `adr-writer` が adr-reviewer の唯一の配線のため）
- 起票基準の記述が skill `adr-writer` の 1 か所になる（rule と grill-me は pointer）

### Negative

- 旧 ADR への注記と commit 本文にしか残らない判断が増え、経緯を探す手段が `git log --grep` と旧 ADR の注記に
  寄る。1 本の ADR に注記が積み重なると読みにくくなる
- 3 条件の判定、特に「意外」と「本物のトレードオフ」に書き手の主観が入る。揺れは Review-when の 3 項目目で
  しか拾えない
- 本 ADR 自身は 3 条件を満たす: 戻すには skill `adr-writer`（本文と evidence script）・`grill-me`・
  `rules/common/akc-cycle.md`・ADR-0072 の注記を直す必要がある

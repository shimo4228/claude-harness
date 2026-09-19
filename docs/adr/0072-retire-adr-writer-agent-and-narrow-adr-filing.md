# ADR-0072: `adr-writer` render agent を退役し主ループが直接書く — 起票を 2 条件に絞り、それ以外は commit 本文へ

## Status

accepted — partially-supersedes [ADR-0016](./0016-writer-agents-render-not-decide.md) Decision 2（`adr-writer` を render agent として残す）と [ADR-0010](./0010-context-sync-cascade-and-writer-agents.md) の `adr-writer` agent 部分。render / decide の分離原則と委譲基準は有効

## Date

2026-09-19

## Context

著者（2026-09-16）:「ADR をいちいち別エージェントに書かせてレビューさせるのちょっと重すぎじゃない？
あと、ADR 各頻度も多すぎない？」。判断役の評価と実測を受け、著者（2026-09-19）:「Writer agent は
外して。起票もその方針でお願い」。判断の材料は次の実測（2026-09-16、`~/.claude`）。

**頻度.** ADR は 71 本（`ls docs/adr/[0-9]*.md | wc -l`、本 ADR を除く、未 commit の 0070 / 0071
を含む）。2026-07-18 以降に追加されたファイルは commit 済み 54 本
（`git log --diff-filter=A --since=2026-07-18 --name-only --format= -- 'docs/adr/0*.md' | sort -u | wc -l`）
+ 未 commit 2 本 = 56 本。窓は 2026-07-18〜09-16 の 60 日で、0.9 本 / 日。バーストは 2026-08-01〜02
の 9 本と 2026-09-15 の 5 本（同コマンドの日付集計）。総語数 46,621（`wc -w docs/adr/0*.md`、
README を除く 71 本、注記込み、2026-09-19）、中央値 605 語（2026-09-16）。2026-07-18 以降の commit
332 本のうち 88 本（26%）が ADR を触る（2026-09-16）。ADR-0057〜0070 の 14 本のうち、skills / rules /
agents / hooks / scripts から `ADR-00NN` で参照されるものが 0〜1 件のものが 7 本（`grep -rl`
2026-09-16）。この参照数は若い ADR ほど低く出る遅行指標で（0070 は測定日に 0 件、3 日後に 5 件）、
単独では「まだ引かれていない」とも読める — 頻度と commit 比率の補助としてだけ使う。
0068（skill 5 本の退役）や 0070（rule 1 行の緩和）のような変更は、git が持つ日付つき経緯で足りる
種類で、ADR が「設計判断の記録」と「作業日誌」の両方を引き受けていた。
[ADR-0065](./0065-drop-adr-consultation-wiring-and-build-or-not-gate.md)（2026-09-14）は
「ADR が新しいアイデアの制動になる」観測で読み側の配線を外したが、書き側がこの量なら制動の供給元は
残る。

**writer agent.** `agents/adr-writer.md`（`model: sonnet`、165 行、退役時点）は Step 3 で主ループが
確定した packet を 7 節テンプレへ描画する専任 agent だった（ADR-0016 Decision 2）。実際の流れは、
主ループが packet を組む → agent が描画 → 主ループが fidelity check で全文を読み直す → adr_lint →
adr-reviewer → 主ループが採否、で、主ループは同じ内容を 3 回読む。ADR-0016 自身が「隔離が不要なら
『メインループ skill』が厳密に上位」と書いており、描画に隔離は要らない。描画専任のはずの agent が
意味側へ漏れた記録が 2 件ある: commit `11f8d01`（ADR-0063、fidelity check で推論 1 箇所を削除）と
2026-09-16 の ADR-0071 描画（実在しないファイル名のリンクを生成し、`adr_review_evidence.py` の
`refs.links_broken` が検出 — [ADR-0071](./0071-adr-review-evidence-script-for-recurring-reviewer-findings.md) Context）。
agent の描画が担っていた近隣 ADR の文体走査は skill の 1 ステップ（直近 2 本を読む）で足り、リンクの
実在は Step 4.5 の evidence が機械で見る。

**reviewer.** adr-reviewer は残す。2026-08-26 以降の 24 報告は全件 NEEDS REVISION 以上で、指摘の
中心は数値・先行 ADR との関係・Review-when の観測可能性という、主ループが自分の文に対して盲目な
判定（ADR-0071 Context の表）。本 ADR は主ループ直書きの初例で、その reviewer 判定が最初の
比較データになる。

**既存の起票規約.** skill `adr-writer` の When NOT to Use は「bug fix / 可逆な refactor / 好み」の
3 行だけで、機構変更でない rule・skill の文言変更や stocktake の結果を ADR にしない根拠が無かった。
`rules/common/akc-cycle.md` の「ADR の扱い」は読み方と supersede の 2 文（ADR-0065）で起票条件を
持たない。commit 本文には implementation-chain の Review / Verify 行が既にあり、決定を 3 行で
残す場所として使える。

## Decision

1. `agents/adr-writer.md` を退役する（git 追跡下、復元可能）。skill `adr-writer` Step 4 を
   「主ループが書く」に書き換える: 直近 2 本を読んで house style を取り、Step 3 の packet から
   7 節を書く。書く時に packet に無い帰結・根拠を足さない（render / decide の分離は packet 規律
   として残す — ADR-0016 の原則は有効、process 境界としての別 agent は持たない）。sibling ADR への
   リンクは `ls` で取ったファイル名を使い、Step 4.5 の `refs.links_broken` で検査する。
   fidelity check のステップは消す（agent が無いので対象が無い）。
2. 起票の条件を skill `adr-writer` の When to Use に正本として置く。ADR を書くのは次のどちらか:
   (a) 他の artifact が引く機構・ゲート・閾値・agent 階層の変更（hook、lint の境界、chain の段、
   rule の既定、model pin）、(b) 旧 ADR の supersede または部分弱化（Status 変更か日付つき注記を
   伴う）。どちらでもない判断は commit 本文に `Context:` / `Decision:` / `Review-when:` の 3 行で
   残す。後に supersede されるか他 artifact から引かれたら、その時に commit を引用して ADR へ昇格する。
3. `rules/common/akc-cycle.md` の「ADR の扱い」に起票条件を 2 文足す（正本は skill、rule は pointer）。
4. 参照の更新: `agents/adr-reviewer.md`（description と正本注記）、`agents/architect.md`、
   `skills/context-sync/SKILL.md` Phase 3、`skills/implementation-chain/SKILL.md` の writing 表、
   `skills/wiki-harvest/SKILL.md` の framing 行。`skills/adr-writer/evals/evals.json` の
   scenario 3 (a) は「agent が 'needs more input' で拒否する」という agent 前提の挙動契約だったので
   「skill が不足 field を尋ねて止まり、部分 ADR を書かない」に書き換える。
5. 注記: ADR-0016 Decision 2 の下、ADR-0010 の Status 行、ADR-0044 Decision 3 の下（「`adr-writer`
   agent は既存 ADR に触らない」の担い手が消える）、ADR-0071 Neutral の「別 ADR で扱う」の下。
   index は部分 supersede された 0010 / 0016 の行を `accepted（一部 superseded）` にする
   （0028 行の先例に揃える。Status 行に注記がある場合も index を揃える）。
6. adr-reviewer の配線（Step 4.6）と `adr_review_evidence.py`（Step 4.5）は ADR-0071 のまま。

## Review-when

- 2026-10-19 時点で、2026-09-19 以降に追加された ADR が 15 本（0.5 本 / 日）を超えていたら、
  2 条件が効いていない — 条件の書き方か、commit 本文への逃がし方を見直す。計器:
  `git log --diff-filter=A --since=2026-09-19 --format=%h -- 'docs/adr/0*.md' | wc -l`、
  判定者は判断役（次の rules-stocktake か skill-stocktake の回）。
- 2026-12-19 までに、機構変更の経緯を追うときに commit 本文の 3 行が無く、著者が「経緯が追えない」
  と 2 回観測したら（記録先: その場で書く ADR の Context か `.notes/TASKS.md`）、commit 本文経路を
  弱いと判断し、条件 (a) を広げる。
- 主ループ直書きの ADR 5 本（本 ADR を 1 本目とする）のうち 2 本以上で adr-reviewer が **Critical**
  （報告書式の固定ラベル。judge は本 ADR 時点の `agents/adr-reviewer.md`、`model: opus`）を出したら、
  Step 4 に描画の self-check 箇条を足す。agent 描画時代の比較値は取らない — commit 本文の Review 行は
  severity を分離していない（`0181fa2` / `dba8f14` は件数のみ）ので、比較可能な baseline が無い。
  記録先は各 commit 本文の Review 行、判定者は判断役。
- substrate が決定記録の作成・supersede を native に持ったら、Step 4 と本 ADR の起票条件を溶かす
  （Scaffold Dissolution downward）。

## Alternatives Considered

### agent を残して `model: opus` に上げる

却下: sonnet 品質の問題（リンクの捏造）は直るが、主ループが packet を組んで全文を読み直す二重読みは
残る。ADR-0016 の「隔離が不要ならメインループ skill が上位」に照らして、隔離の実利（文体走査・
テンプレ処理）は skill の 1 ステップと evidence script で代替できている。

### agent を残して fidelity check だけ消す

却下: 2026-09-16 に agent が意味側へ漏れた（捏造リンク）直後で、検査を外す根拠が無い。

### adr-reviewer も退役して writer skill の予防チェックに吸収する

却下: ADR-0071 Alternatives と同じ理由（24 報告全件 NEEDS REVISION 以上、指摘は semantic 判定）。
本 ADR は reviewer を主ループ直書きの比較計器として使う。

### 起票条件を変えず agent 退役だけ行う

却下: 著者の問いは重さと頻度の 2 つで、頻度側の供給（1 本 / 日、commit の 26% = 88 / 332、
Context の実測）は agent 退役では変わらない。

### ADR を廃止して RFC 台帳（提案）だけにする

却下: [ADR-0044](./0044-adr-review-when-and-dated-annotation.md) Alternatives が「未決」で残した
案だが、rfcs/ は提案・未決、ADR は決定の記録で役割が違う（rule `task-tracking.md`、skill
`rfc-writer`）。小さな決定の受け皿は commit 本文で足りる。

### 起票条件を rule に正本として置く

却下: rule は常駐で毎セッション読まれるが、条件の細部（(a) の例示、昇格の手順）は skill の
入口に置く方が context 経済で勝る。rule には 2 文の pointer だけ置く（ADR-0065 の「ADR の扱い」
縮約と同じ方針）。

### 何もしない

却下: 著者が重さと頻度の両方を名指しし、2026-09-19 に方針を決めた。

## Consequences

### Positive

- ADR 1 本あたり agent 起動 1 回と主ループの全文読み 1 回が減る（手順上の計数で測定ではない:
  packet 作成・fidelity check・reviewer 採否の 3 回 → 書く・reviewer 採否の 2 回）。
- 起票の判断が 2 条件に固定され、rule 文言の変更や stocktake の結果は commit 本文で終わる。
  ADR-0065 が外した読み側の制動に対して、書き側の供給も絞られる。
- ADR-0016 の原則（render / decide）は packet 規律として残り、`prompt-writer` 等の他の writer
  agent の委譲基準はそのまま。

### Negative

- 主ループ（judge-tier）が描画のトークンを払う。sonnet の描画コストと引き換えで、単価は上がる。
- 決定の記録場所が ADR と commit 本文の 2 つになる。commit 本文側の検索経路は
  `git log --grep='^Review-when:'` で、index からは辿れない。昇格の手順（Decision 2）が
  その橋。
- 2 条件には書き時の判断が要る（rule の既定変更は (a) に入る、rule の文言整理は入らない）。
  迷ったら commit 本文に置き、引かれた時に昇格する — 遅延の側に倒す。
- 頻度の計器（Review-when 1 項目）は 1 か月の遅行指標で、その間の過剰起票は止まらない。
- 巻き戻しは `agents/adr-writer.md` の git 復元と skill Step 4 / rule 2 文 / 参照 6 箇所の
  revert（全て git 追跡下）。

### Neutral / Follow-ups

- 本 ADR が主ループ直書きの初例。adr-reviewer の判定を commit 本文の Review 行に残し、
  Review-when 3 項目目の起点にする。
- `skills/agent-stocktake/results.json` の `adr-writer.md` 行は次回 stocktake で消える（実測結果
  ファイルは手で直さない）。
- 他 repo（contemplative-agent / agent-knowledge-cycle / daily-research 等）の ADR corpus は
  同じ skill を使うので、起票条件も同時に効く。各 repo の `docs/adr/README.md` は変更しない。

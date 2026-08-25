# ADR-0049: store 形タスク台帳を公開 rfcs/ に一元化する

## Status

accepted

## Date

2026-08-25

## Context

タスク台帳は、どの形でも公開経路に乗っていなかった。決定時点の実測（2026-08-25）: store 形
`.notes/tasks/T-XXX.md` を現に持つ repo は 0 件（過去の先例 contemplative-agent は
`.notes/` ごと gitignore、`.gitignore:48`）。本 harness は単一表 `.notes/TASKS.md` で、
private repo（`shimo4228/claude-config`）に追跡されてはいるが、公開ミラー
claude-harness の収集範囲（`sync-from-local.sh` の SUBTREES）には台帳が含まれない。

この結果、提案・却下理由・系譜という判断の記録が、非公開の作業場に留まり続けていた。これは
著者が [ADR-0007](./0007-open-concept-network-effect.md) で定めた「概念を囲い込まず開放し、
DOI で帰属を守る」戦略 — 「RFC を書いた人の名前は消えない」という TCP/IP RFC モデルの引用 —
と食い違う。2026-08-25、著者はこの食い違いを「それこそが私の見出した原則の実践ではないか」と
指摘した。

同日、[ADR-0048](./0048-sdlc-playbook-translation-and-rfc-conformance.md) で提案本文は
Rust RFC テンプレートに完全準拠する方針がすでに決まっており、残っていたのは置き場所の問題
だけだった — `.notes/` は公開ジャンルとして無名だった。

検討は 3 案を順に経由した。α 案は `.notes/` をそのまま公開する（gitignore の負パターンを
手術する）案、β′ 案は公開 `rfcs/` に提案だけを置き作業用の台帳とは分離する案（Rust の
「RFC → tracking issue」という型を借用）、γ 案は両者を一元化する案で、最終的に γ 案を
採用した。

現行の台帳はもともと提案も作業も 1 店舗で回しており、β′ 案が持ち込んだ分離は Rust 特有の
事情（RFC repo とコード repo が別で、issue が議論を担う）を借りたものだった。

先行 ADR との関係も決定の一部である。[ADR-0038](./0038-publish-curated-commit-hooks.md)
は「公開は provenance でなく curation の判断」と定めた — 本 ADR は既定を反転させるのでは
なく、`rfcs/` という**公開可能な書き方を既定とする curated class を 1 つ追加**する
（既存の非公開資産の扱いは変えない）。[ADR-0043](./0043-task-triage-loop-judge-build-human.md)
の red line「無人セッションは公開物に触れない」とは、台帳が公開物になることで交差する —
両立の形は「無人 triage は working tree の台帳ファイルに書けるが、公開へ出る commit /
push / merge は従来通り人間の側にある」（0043 の human merge がそのまま防波堤）。
同じく 0043 の「台帳を parse する script を足さない」は、既存 parser（claims.py の
`ready`）の走査対象追加であって新 parser の追加ではない。

## Decision

store 形台帳の家を repo トップレベルの公開 `rfcs/` に一元化する（γ 案を採用する）。

1. 台帳を 1 エントリ 1 ファイル `rfcs/NNNN-slug.md` として置く。番号は 4 桁採番・欠番不再利用
   とし、`docs/adr/` と同じ規約に揃える（`ADR-NNNN` と `RFC-NNNN` は同じ数字の形を別
   namespace で使う — prefix が区別を担う）。ID は stem 先頭 4 桁から `RFC-NNNN` を導出する。
   index は `rfcs/README.md` に置くが、**state は各ファイルの frontmatter を唯一の正本とし
   index には複製しない**（二重記録は drift する）。
2. 提案と作業を 1 店舗に統合する。提案専用の別置き場は作らない。
3. 状態語彙は既存の台帳語彙 8 語（`candidate` / `ready` / `in_progress` / `blocked` /
   `done` / `decided` / `dropped` / `retired`）を frontmatter `state:` にそのまま流用し、
   第二語彙を作らない。RFC lifecycle との対応（例: candidate=Draft、ready=Accepted、
   done=Implemented、decided=判断で決着、dropped=Rejected/Withdrawn）は skill:
   `task-stocktake` を正本とする。
4. archive 機構は持たない。終端エントリは削除・退避せずその場に残す — dropped も却下理由
   ごと残ることが公開判断記録の価値であり、この設計は `rules/common/akc-cycle.md` の
   「却下記録の読み方」と同じ思想に立つ。pending の視界は `claims.py ready` の state
   フィルタで保つ。旧 store の終端エントリだけ、従来どおり `.notes/archive/tasks/` へ
   退避する。
5. 公開可能な書き方を既定にする。本文は公開できる形で書き、機微な情報はリンク先へ
   逃がす。**本 ADR の時点で公開経路は未接続**である — `rfcs/` は private repo
   （claude-config）内にあり、公開ミラー claude-harness の収集範囲への追加は RFC-0001 が
   担う。公開は撤回不能（clone / クロール済みになりうる — ADR-0037 Alternatives の記録）
   なので、書き方の既定を接続より先に立てる。
6. 機構改修は最小に留める（実測: `claims.py` +61/−16、`task-claims-reminder.sh` +7/−3、
   bats 11 本追加 +100 行 — 正は本 commit の `git diff --numstat`。suite は全 green だが
   総数は並行変更を含むため本変更の baseline にしない）。`claims.py` の ID 正規表現を
   `^(?:T|RFC)-` に緩め、`ready` / `known_tasks` の走査対象に `rfcs/` を追加する。
   `task-claims-reminder.sh` のディレクトリ検知にも `rfcs/` を追加する。旧 `.notes/tasks/`
   は移行期間中 dual-read の対象として残す。**dual-read の閉じ条件**: 旧 store が空に
   なった repo から対象を外れ、全対象 repo で空になったら dual-read コードを畳む
   （RFC-0001 の完了条件に含める）。`claims.jsonl`（lease という運用状態であり判断記録
   ではない）は `.notes/` のまま非公開とする。
7. CA ADR-0095（[contemplative-agent ADR-0095](https://github.com/shimo4228/contemplative-agent/blob/main/docs/adr/0095-retire-task-ledger-machinery.md)）
   が定めた「台帳を扱うコードを増やさない」制約を維持する。描画・読み戻し・状態機械・
   aging は今回も持たない。追加は正規表現とパス走査、および単一表併存時の誘導 1 行のみと
   し、台帳コードの総量はほぼ変えない。
8. 全 repo への展開・既存行の移送判断・harness-sync の収集範囲拡張は RFC-0001
   （`rfcs/0001-public-rfcs-rollout.md`）が追跡する。本 ADR の時点で harness 自身の
   `rfcs/` は初期化済みで、RFC-0001 と RFC-0002 が実例として存在する。

## Review-when

- `rfcs/` への流入が 3 ヶ月間 0 のとき — 形骸化と判断し、畳む方向を検討する。流入 =
  新規エントリファイル数（`git log --diff-filter=A -- 'rfcs/[0-9]*.md'` で数える。state
  遷移は数えない）。
- 公開が原因の機微情報事故が 1 件でも発生したとき — 「公開を既定にする」方針自体を
  再検討する。
- 台帳の読み書きにさらにコードを足したくなったとき — 要件を先に疑う。
  `rules/common/task-tracking.md` の review-when と同文。

## Alternatives Considered

### α: `.notes/tasks/` を追跡化して公開する

gitignore の負パターンを手術し、`.notes/tasks/` をそのまま公開する案。却下: `.notes/` は
公開ジャンルとして無名で、外部の読者や LLM が提案の置き場として発見できない。repo ごとに
ignore の負パターンを維持するコストも残る。

### β′: 公開 `rfcs/`（提案）と台帳（作業）を分離する

公開 `rfcs/` には提案だけを置き、作業用の台帳とは別に保つ案（Rust の
「RFC → tracking issue」という型を借用）。却下: 状態を持つ店舗が**恒久的に** 2 つになり、
分散した台帳は誰も刈らないという既往パターン（状態語彙が 4 文書に分散して 6 語まで肥大した
2026-08-16 の事件 — `rules/common/task-tracking.md` の rationale が記録する、および
CA ADR-0095）に当たる。分離は Rust 特有の事情（RFC repo ≠ code repo、issue が議論を担う）
の借用であり、現行台帳の意味論はもともと一元的だった。なお採用した γ も**移行期間中は**
2 店舗を経る — 恒久化しないための閉じ条件は Decision 6 に置いた。

### RFC 独自の状態語彙（Draft / FCP / Accepted / Rejected）を新設する

RFC lifecycle 専用の語彙を新たに導入する案。却下: 既存の 8 語と二重定義になり drift する。
既存語彙で RFC lifecycle を十分に写像できる。

## Consequences

### Positive

- 判断記録が公開可能な形になる（実公開は RFC-0001 の経路接続後）。却下（dropped）も
  理由ごと残り、[ADR-0007](./0007-open-concept-network-effect.md) の原則が台帳レベルで
  実践される。
- archive 機構が要らなくなる（終端エントリをその場に残すため）。
- [ADR-0048](./0048-sdlc-playbook-translation-and-rfc-conformance.md) の翻訳マップが挙げる
  playbook の「intent home」（共有・version 管理された提案置き場）に 1:1 対応する。

### Negative

- 起票のたびに公開可能な書き方を要する。機微情報の逃がし先を考えるコストが毎回乗る。
  公開後の撤回は不能（clone / クロール — ADR-0037 の記録）で、Review-when 第 2 項の
  事故検知は事後にしか働かない。
- 既存行の移送は 1 件ずつの人手判断になる（機微点検を機械化しない）。残作業として
  RFC-0001 に残る。
- CA ADR-0095 が定めた「台帳コードを増やさない」制約に数十行分触れた。総量はほぼ不変で
  許容と判断したが、Review-when 第 3 項で監視する。

### Neutral / Follow-ups

- 単一表形式 `TASKS.md`（小 repo 向け）の形は残る。2 つの形（単一表 / store）は現行の
  まま維持するが、**併存する repo**（本 harness が移行期間中これに当たる）では `ready` が
  store 経路に入ると単一表の行が黙って隠れる回帰を実装時に検出した — `ready` 末尾の
  単一表誘導行と bats 2 本で pin 済み。harness の `TASKS.md` 冒頭には rfcs/ への誘導を
  1 行足した。

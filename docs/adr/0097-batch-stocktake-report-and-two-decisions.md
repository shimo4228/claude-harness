# ADR-0097: 棚卸しの承認を「1 枚の report」と「完了 report の ff 取り込み」の 2 回にまとめる

## Status

accepted — [ADR-0078](./0078-generation-audit-single-entry-with-prompt-audit-engine.md) の Decision 2（常駐層の行を
1 件ずつ示す）、[ADR-0022](./0022-generation-audit-three-sibling-stocktakes.md) の Decision 1（CLAUDE.md の inline
confirm-each）を部分的に置き換え、[ADR-0046](./0046-skill-creator-shrink-in-place-and-creation-gate.md) の
Decision 2（§1 と §7 の著者ゲート）を report 経路の分だけ狭める。3 本に注記する

> **注記（2026-11-01, commit「chore(stocktake): skills の棚卸しを適用」）** 初回の全体実行で review-when-watch を退役したので、Decision 6 の後続に挙げた「review-when-watch の rules 対応」は機構ごと無くなった。

## Date

2026-10-31

## Context

Plan: [docs/plans/sunny-splashing-scroll.md](../plans/sunny-splashing-scroll.md)（承認 2026-10-31）。調査:
[docs/plans/research/2026-10-31-batch-stocktake-report.md](../plans/research/2026-10-31-batch-stocktake-report.md)

- 著者（2026-10-31、`/grill-me` の依頼文）: 「skill-stocktake が 1 個 1 個私に判断を聞く形だから、一括承認しづらい。
  レポートをするような形に変えて私にまとめて承認および修正を依頼して、それに基づいて一気に棚卸しする」「出来るだけ
  私の判断箇所は 1 つにまとめて、かつ私が参照しやすい方式でレポートしてほしい」
- 1 件ずつの `[y/n/skip]` と一括承認の禁止は、skill-stocktake / rules-stocktake / rules-distill には commit `f8b08bc`
  （2026-07-03「config-gc の confirm-each 設計を stocktake/distill 系 3 skill に適用」）で入り、この 3 本についての ADR は
  無い。本文に残る理由は "apply all 5? [y/n] defeats the design" とその言い換え（skill ごとに 4 通り）だけ。
  agent-stocktake（`7584620`）と repo-asset-stocktake（`68d77df`）が同じ文言を写した。generation-audit の常駐層の行
  （ADR-0078 Decision 2）と CLAUDE.md（ADR-0022 Decision 1）の 1 件ずつの承認は ADR に記録がある
- skill-stocktake は Improve / Update を skill-creator に渡すかを 1 件ずつ聞き、skill-creator は §1（intent の確認）と
  §7（著者の通読）で著者に止まる（ADR-0046 Decision 2）。Improve が N 件なら著者の判断は 3N 回になる
- 一括の先例が harness にある: context-sync は既存ファイルの編集を自動で適用し、新規作成だけを 1 回まとめて確認する。
  task-triage の digest は語彙の当てはめを一括 OK にし、rule の変更・リスクの受容・drop を個別にする
- rule `boundary.md` は「検収を通した task branch の main への ff-only 取り込み」を確認なしで取る側に、「rules・skills の
  無人変更（その diff を含む取り込みも）」を人間に渡す側に置く
- rules-stocktake / agent-stocktake / rules-distill は単独の公開 repo に同期される（skill: `harness-sync` の同期表）。
  Artifact は Claude アプリと claude.ai に固有の媒体
- rules の台帳 `skills/rules-stocktake/results.json` の `evaluated_at` は 2026-07-26 で、実在しない rule 3 本を持ち、
  実在する rule 6 本を持たない（2026-10-31 に台帳のキーと `rules/` の一覧を突き合わせた）。定期的に棚卸しを起こす
  仕組みは無い
- 著者の判断（同日の面接、各問いに推奨を示した）: 承認は report 1 枚で全件（Retire を含む。git で戻せるため）、媒体は
  Artifact + `db`、入口は取りまとめ役の skill を新設、適用は task branch → 完了 report → ff、範囲に context-sync・
  repo-asset-stocktake・hooks の棚卸しを加える（hooks は Claude の推奨「別タスク」に反して範囲に入れ、独立 skill に
  した）、rules の Dissolve 候補に transfer 検証、起動は手動 + 月 1 回の launchd、作成後に変わった項目はその項目だけ
  評価し直す

## Decision

1. 棚卸しで著者が判断するのは 2 回にする: **提案 report の承認**（直したい項目だけ書き換えて 1 回で返す）と、
   **完了 report を見た main への ff-only 取り込み**。各棚卸し skill の 1 件ずつの確認手順は消す
2. report の契約（項目 schema・並び順・集約後の衝突検査・適用手順・完了 report）の正本は skill:
   `harness-stocktake` に置く。各棚卸し skill（skill / rules / agent / hook の各 stocktake、rules-distill、
   context-sync、repo-asset-stocktake）は判定までを持ち、承認と適用はこの契約に渡す。単独で呼んだときも同じ契約で
   1 本分の report にする。generation-audit の修正行もこの report に載せる
3. 媒体は Artifact + `db`（項目は `items`、著者の判定は `decisions`、承認は `meta/approval`）。Artifact の無い環境では
   同じ schema の Markdown に書き、承認はチャットで取る。判定履歴の正本は各 skill の `results.json` のまま。
   集めている途中の項目と最新 report の URL は `.notes/stocktake/` に置き、`.gitignore` で追跡から外す（記録は store と
   台帳が持つ）
4. skill-creator に report 経路を足す: 承認済み report の項目から呼ばれたとき、§1 は項目の intent packet で済ませ、
   §2〜§6 は止めずに回し、§4 の草稿ゲートを 2 回で通らない項目は未決として返し、§7 は完了 report に回す
5. 適用は worktree の task branch で行う。項目ごとに作成時の blob hash を照合し、変わっていた項目はその項目だけ
   評価し直す（判定が同じなら適用、変われば未決）。著者のコメントから変更が一つに決まらない項目も未決にする
6. hooks の棚卸しは独立した skill `hook-stocktake` にする。rules の Dissolve 候補には、rule を外した `claude -p` と
   残した `claude -p` を比べる transfer 検証を足す（verbatim の rule は対象外）
7. 月 1 回の launchd が report の公開と Slack 通知までを無人で回す。Artifact は非公開で作られるので、boundary.md の
   「公開」には当たらない。承認と適用は著者がいる session で行う
8. git の外にある対象（`settings.json` の hook の配線）は branch に載らないので、ff 取り込みの後に変え、変える前の
   写しを `.notes/stocktake/` に置く

Decision 6 の transfer 検証、review-when-watch の rules 対応、台帳と実物の一致の lint、Decision 7 の launchd の plist は
後続の commit で入れる（plan の手順 3〜5）。

## Review-when

- 完了 report を見たあとで、著者が承認済みの項目を取り消した（revert した、または「見落としていた」と言った）—
  report の形では中身を読まれていない。影響の大きい群（退役）だけ承認を分けるか検討する
- 初回の全体実行で、著者の判断が 2 回を超えた（途中で `[y/n]` を聞いた、skill-creator が止まった）
- 月 1 回の無人実行の最初の 3 回で、spawn-session で起こした session に Artifact と `db` が無く、report が Markdown に
  なった — 媒体の既定を見直す
- Claude Code か claude.ai が、項目ごとの承認を一括で受ける UI を native に持った

## Alternatives Considered

- **1 件ずつの確認を残す** — 著者が名指しした不満そのもので、Improve を skill-creator に渡すと判断は 2N 回になる。却下
- **task-triage 型の 2 層**（機械的な修正は一括 OK、設計判断を含む項目は個別）— 個別の判断が残り、判断点を 1 つに
  まとめるという依頼に届かない。著者が選ばなかった
- **退役だけ承認を分ける** — 削除は git で戻せ、判断が 1 回増える。著者が選ばなかった。Open — Review-when の 1 つ目
  が起きたら再検討する
- **承認後に main へ直接 commit し、気に入らなければ revert** — 判断は 1 回になるが、著者が承認するのは提案で、
  skill-creator が書き上げた仕上がりは誰も見ないまま main に入る。rule `boundary.md` は rules・skills の変更を「その diff を
  含む取り込みも」人間に渡す。却下
- **skill ごとに別の report** — 4〜7 本の承認に分かれ、Demote で増える skill や Retire で切れる参照といった
  棚卸しをまたぐ衝突を誰も見ない。却下
- **既存の skill に `all` モードを足す** — skill は増えないが、skill-stocktake が rules・agents・hooks まで持ち役割が
  にじむ。却下
- **hooks の棚卸しを取りまとめ役の 1 phase にする** — skill が増えない分軽い（Claude の推奨）。著者は他の 3 本と
  並べて単独で呼べる形を選んだ
- **媒体を repo の Markdown またはチャットの表にする** — 前者はエディタを置かない著者の環境で書き換えが重く、後者は
  数十件で読みにくく残らない。Artifact の無い環境の代替としてだけ残す

## Consequences

- 著者の判断は棚卸し 1 回につき 2 回になる。単独の棚卸しでも同じ
- 棚卸しをまたぐ衝突（Demote と新設、Retire と参照）が 1 枚の report で見える
- 「中身を見ない一括承認」の防ぎ手が、承認の回数から report の質（各項目が単独で判断できる Reason quality と、
  影響の大きい順の並び）に移る。report の質が落ちると承認は形だけになる
- skill-creator に 2 本目の入口ができる。report 経路は承認済み report の項目からだけ使い、著者の直接の依頼では
  今までどおり §1 と §7 で止まる
- Artifact と `db` に依存する。公開 repo の sibling は Markdown の代替で動くが、そちらは一括承認の画面を持たない
- 月 1 回の無人実行が、skill-stocktake の並列 subagent と transfer 検証の `claude -p` の分だけ使用量を使う
- 戻すときは、7 本の棚卸し skill と skill-creator の入口の変更を git revert すれば 1 件ずつの確認に戻る

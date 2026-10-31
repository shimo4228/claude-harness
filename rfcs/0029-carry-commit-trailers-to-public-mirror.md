---
state: done 2026-10-25
review-when: harness-sync の同期方式が変わったとき
---
## Summary

claude-harness への同期で、公開対象を触った source commit の trailer を同期 commit の本文に写す。

## Motivation

harness-sync は tree だけを渡し、commit 本文を落とす。予備測定（RFC-0027）で RFC-0021 の 4 環が「記述のみ」だったのは、根拠の commit 本文が private repo にしか無いため。

## Drawbacks

trailer に私的なパスや機微が混ざりうる（同期の secret scan と `$HOME` scan を通す）。ミラーの commit 本文が長くなる。

## Unresolved questions

写す範囲（全 trailer か Review / Context / Decision / Review-when / Plan だけか）/ 前回同期からの commit の列挙方法。

## Status

**2026-09-27 draft**

**2026-09-28 blocked** — 著者 OK。Next action が「RFC-0028 の試行結果を見てから」だったので、その条件を 3 行にした。

再開条件: RFC-0028 の試行（2026-09-28〜10-12）の読みで「続ける」と決まる
照合先:   `rfcs/0028-correction-commit-trailers.md` の state と Status
成立時:   accepted（claude-harness の同期 script に、公開対象を触った source commit の trailer を同期 commit の本文へ写す処理を足す）

triage 2026-10-11: RFC-0028 は in_progress のまま（試行の読みは 2026-10-12）。未成立。

triage 2026-10-18: RFC-0028 は in_progress のまま。試行の読み（数えた値）は RFC-0028 の Status に記録したが、「続ける / 撤退」は著者の判断待ち。未成立。

triage 2026-10-18（続き）: 再開条件が成立 — RFC-0028 の試行は著者が「続ける」と決めた（RFC-0028 Status 2026-10-18）。成立時どおり accepted。実装先は harness-sync の同期 script で、skill の変更なので merge は著者の diff。

triage 2026-10-25: accepted のまま未 dispatch。受入条件が本文に無い（Unresolved の 2 点）ので、判断役が既定を置いて digest で著者の OK を待つ（ADR-0076）。加えて ~/.claude の main に未 push の commit が 4 本あり（2026-10-24、著者の作業）、cloud dispatch の preflight が通らない。

**2026-10-25 done** — 著者が受入条件の既定を承認（写す trailer 8 種、`Source:` 行から列挙・無ければ最新の同期 commit の日時）。build（spawn-session、Opus 5.5、packet [docs/plans/rfc-0029-s1-sync-source-trailers.md](../docs/plans/rfc-0029-s1-sync-source-trailers.md)）が `scripts/sync_trailers.py` と `scripts/tests/sync-trailers.bats`（12 件）を足し、`sync-from-local.sh` が commit 本文の下書き `.git/SYNC_COMMIT_BODY` を作って既存の 2 つの scan に通す（claude-harness `1f4fe43`、判断役の再実行で bats 12/12・263/263、shellcheck 0）。逸脱 4 件は build が名指し（対象パスに削除を含める、起点を最新の同期 commit に、Source の sha が祖先でないときの fallback、指摘ブロックを 1 件と数える）。

script の scan は `~/MyAI_Lab/<非公開 repo>` 形式を止めない（security-reviewer MEDIUM、source の log に 15 行）。著者判断で script は機械的な scan のままにし、harness-sync SKILL.md の「5. コミット」に、下書きを `verify-public-detail.sh --llm` に通して HIT を下書きの編集で伏せる手順を足した（下書きは `.git/` の中でも検査できることを確認済み）。build 提案の 1 件（claude-harness に gate が無い）は著者判断で RFC-0036 に起票。diff 外 findings: 1 件、claude-harness `1f4fe43` の commit body 参照。

## Next action

上の照合先を 10-12 以降の triage で確かめる。

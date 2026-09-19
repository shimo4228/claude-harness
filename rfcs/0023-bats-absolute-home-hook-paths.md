---
state: draft 2026-09-14
review-when: bats が repo の verify から外れる（hooks の Rust 化等で bats 自体が退役）→ obsoleted
---
## Summary

`tests/*.bats` の 26 本中 18 本が検査対象の hook / script を `$HOME/.claude/hooks/...` の絶対パスで source するため、worktree で走る build の full verify は自分の作業ツリーでなく main checkout の hook を検査する — 参照を repo root 相対（`BATS_TEST_DIRNAME` 基準）に揃えて、worktree の verify が worktree 自身を検査するようにする。

## Motivation

task-triage loop の build は git worktree で走り、受入条件に `./.claude/verify.sh` full exit 0 を持つ。2026-09-14 の S2（RFC-0021）は tests/ しか触っていないのに `tests/episode-log-guards.bats` 11 本が赤で受入条件を落とした。原因は同 bats の L16–19 が `$HOME/.claude/hooks/_episode-log-common.sh` 等を絶対パスで読み、main checkout に未コミットの hook 改修（episode log の置き場を `logs/episodes/` へ移す作業）が載っていたこと。worktree 側の commit 済み bats は旧仕様を検査していた。

producer → sink: `tests/episode-log-guards.bats:16`（`COMMON="$HOME/.claude/hooks/_episode-log-common.sh"`）→ `.claude/verify.sh` full mode の bats 実行。同型は 18 ファイル（`grep -l 'HOME/.claude/hooks' tests/*.bats`）。`BATS_TEST_DIRNAME` 基準で書いている bats は 9 本あり、そちらが正準形。

loop 側の欠陥として起票する理由: 別セッションが main checkout の hook を編集中である限り、hook に無関係な build も同じ形で bounce する（build は main に触れないので自力で解消できない）。

## Guide-level explanation

bats は検査対象を `"$BATS_TEST_DIRNAME/../hooks/<name>.sh"` の形で解決する。`$HOME/.claude` が repo 本体と一致する通常運用では挙動は同じで、worktree では worktree 自身の hook を検査するようになる。hook が `$HOME/.claude/hooks/_common.sh` 等を内部で絶対パス source している場合はその hook 側の設計（インストール先固定）であり、本 RFC の対象外 — bats の参照だけを直す。

## Reference-level explanation

受入条件: (1) `grep -c 'HOME/.claude/hooks' tests/*.bats` が 0（hook の内部 source を検査する意図で `$HOME` を使う箇所があれば理由を注記して残す）(2) `./.claude/verify.sh` full exit 0（main checkout）(3) worktree を切り、hook を 1 つ意図的に壊した状態で同 bats が worktree 側の壊れを検出することを 1 回実測（対照実験、commit body に記録）。

## Drawbacks

18 ファイルの機械的な置換。hook が内部で `$HOME` を source する箇所は残るので、worktree 隔離は完全にはならない（bats の参照層だけが直る）。

## Rationale and alternatives

- build に「main checkout の未コミット変更が原因なら受入条件 3 を免除」と書く: 判定を build に委ねることになり、無言の逸脱の温床。却下
- worktree で `HOME` を差し替えて bats を走らせる: hook 側の `$HOME` source まで付いてくるが、build の Bash guard が `HOME` 差し替えを拒否した実績（S2 の Deviation 2）。却下

## Status

draft 2026-09-14 — S2 build の Out-of-diff finding から、著者判断で起票（review 由来、producer 付き）。採否と修正の形は未決。

## Next action

著者が accepted にしたら chore build（tests/ のみ、hook 本体は触らない）を dispatch。

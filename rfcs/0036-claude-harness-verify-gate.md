---
state: withdrawn 2026-11-08
review-when: claude-harness に CI か repo gate が別の経路で入ったとき
---
## Summary

公開 repo claude-harness に `.claude/verify.sh` を置き、`bats scripts/tests` と `bats tests/` を回す。受入条件: `./.claude/verify.sh` が引数なしで両 suite を走らせ、どちらかが落ちれば exit 非 0。

## Motivation

由来: build 提案 (S1)。RFC-0029 の build（claude-harness `1f4fe43`）が同期 script のテスト `scripts/tests/sync-trailers.bats`（12 件）を足したが、claude-harness には `.claude/verify.sh` も CI も無く、この suite も既存の `tests/`（263 件）も自動では誰も回さない。再現: claude-harness の root で `ls .claude/verify.sh` → 無い（判断役が 2026-10-25 に確認）。gate が無いので、この repo の作業は cloud build の既定経路（CI が verify を回す）にも乗れず、RFC-0029 は local の build で回した。

## Reference-level explanation

producer: claude-harness `scripts/tests/sync-trailers.bats:1`（gate の外にある suite）。`tests/` は同期で丸ごと置き換わる subtree、`scripts/tests/` は置き換わらない — gate はどちらも回す。gate の作り方と承認（`verify_allow.py` の hash）は skill: `verify-bootstrap` と rule `security.md` に従い、承認は著者が通す。CI（`.github/`）を足すかは別の判断。

## Unresolved questions

CI まで足して cloud build の経路に乗せるか / gate に shellcheck と ruff を含めるか。

## Status

**2026-10-25 draft** — 著者の起票指示（triage digest の回答）。RFC-0029 の build 提案を判断役が再現して出したもの。

triage 2026-11-08: 前提は残る — claude-harness に `.claude/` も `.github/workflows/` も無い（`ls`、HEAD c2a1e12）。採否を digest に出した。

**2026-11-08 accepted** — triage digest 2026-11-08 の承認。`.claude/verify.sh` は gate script なので無人では dispatch しない（boundary.md）— 著者が在席する session で verify-bootstrap を回し、`verify_allow.py approve` まで通す。

**2026-11-08 withdrawn** — 著者判断（triage session）: ミラーに gate は要らない。同期元 ~/.claude の `.claude/verify.sh` は `.github/workflows/verify.yml` の CI で回っている（2026-11-07 の run 3 本 success）。判断役注: ミラーにしか無い `scripts/sync-from-local.sh` とそのテスト `scripts/tests/sync-trailers.bats`（12 件）は同期元の CI の対象外で、手で回すまで走らない。

**2026-11-08（続き）** — 著者と合意: 守られていなかった 12 件は、ミラーに gate を置かず、同期元の skill `harness-sync` の手順 1 で同期の前に `bats <公開repo>/scripts/tests/` を回す形で拾う（同 commit）。追加時点で 12 / 12 ok。state は withdrawn のまま（ミラーの gate はやらない）。

## Next action

採否を決める。採るなら verify-bootstrap で gate を作る（承認は著者）。

---
state: done 2026-09-14
review-when: ty の pin（.claude/verify.sh の `ty==0.0.75`）を上げたとき、tests/ の添字アクセスに対する診断が変わっていないかを同 sub-project で再確認する
---
## Summary

`.claude/verify.sh` の full run が main で exit 1 になる（`uvx ty==0.0.75 check --project skills/growth-fable` が `tests/test_collect_snapshot.py` に 30 件）— tests 側を型付きアクセスに直して full gate を緑に戻す。

## Motivation

full mode は launchd 起動の triage セッションが merge 後の検収に無人で回す唯一のゲート。main で赤いままだと、以後の build はすべて「変更と無関係な赤」で bounce し、ADR-0063 の hooklint 較正（full run の回数で数える）も進まない。commit 境界は `--staged` で staged ファイルだけを見るので、この赤は commit では検出されず、2026-09-13 の triage cycle の full run で初めて出た。

producer → sink: `skills/growth-fable/tests/test_collect_snapshot.py:36`（`snap["followers"]["count"]` — `JsonDict = dict[str, object]` の値を添字）→ `.claude/verify.sh:503`（sub-project ごとの `ty check --project`）。`scripts/` 単体は clean、pytest 12 本は通る。初回 commit 52b75cd（2026-09-08）の body は「ty clean / verify.sh full exit 0」と書いているが、同ファイルはその後変更されておらず、pin 版で再現する。

## Guide-level explanation

tests は `as_dict()` / `as_list()`（`scripts/collect_snapshot.py:49-54` に既にある境界関数）を通して値を取り出すか、型付きのローカルに束ねる。ty の設定を緩めない（tests/ の除外・`ignore` の追加はしない）— ANN 境界型強制（ADR-0056）の趣旨を tests にも通す。

## Reference-level explanation

受入条件: (1) `uvx ty==0.0.75 check --project skills/growth-fable` exit 0 (2) `cd skills/growth-fable && uv run pytest -q` 12 passed (3) `./.claude/verify.sh` 引数なし exit 0（他 stage を壊さない）(4) `scripts/collect_snapshot.py` の公開シグネチャは変えない（変えるなら理由を commit body に）。

## Drawbacks

tests の行数が増える。`object` を境界関数で剥がすのは冗長に見えるが、LLM 読者には型が beacon になる（rule llm-first-code）。

## Rationale and alternatives

- tests/ を ty から除外（pyproject `[tool.ty]`）: 5 分で消えるが、次に tests が型を破ってもゲートが黙る。却下
- `# ty: ignore` を 30 箇所: 診断を隠すだけ。却下
- ty の pin を上げて診断が消えるのを待つ: 0.0.x の診断は増減しうるが、この診断（`object` の添字）は正しい指摘で、消える方が異常。却下

## Status

done 2026-09-14 — S2 build（commit 258ca6c、tests/test_collect_snapshot.py のみ +45/−31、`as_dict` / `as_list` を tests 先頭で束ねる形）を著者 merge。判断役の再実行: ty 0 件 / pytest 12 passed / `.claude/verify.sh` full exit 0（main、2026-09-14）。

（旧 Status: accepted 2026-09-14 — triage cycle 2026-09-13 の full run で検出、著者判断（決定 1 = a）で起票と build dispatch）

## Next action

なし（終端）。

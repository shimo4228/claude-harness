---
state: draft 2026-09-27
review-when: 振り分けが終わったとき。または ADR-0085 の 2026-10-11 の計測で plan の記録層そのものが見直されたとき
---
## Summary

global の legacy 置き場 `~/.claude/plans/` にある過去の plan（2026-09-27 時点で 253 本）を、それぞれ作られた repo の plan 置き場へ振り分ける。公開 repo は `docs/plans/`、除外 repo（contemplative-agent は `.notes/plans`、zenn-content は `planning/plans`）は非公開の置き場へ。

## Motivation

ADR-0085 で新しい plan は repo の `docs/plans/` に残るようになったが、過去の plan は repo と切り離されたまま global に溜まっている。過去の ADR / RFC の多くは plan mode を通っていて、その原本（実装前の意図と検証手順）が辿れない。ADR-0009 のように既に消えた plan もあり、置き場が 1 か所で repo に属さない状態が続くほど失われる。

## Reference-level explanation

- **どの repo の plan か**: 253 本すべてについて、plan のファイル名を含む会話ログ（`~/.claude/projects/<cwd>/<session>.jsonl`）が見つかる（2026-09-27 実測）。会話ログのディレクトリ名がセッションの cwd を表すので、そこから repo を決める
- **公開 repo へ入れる plan は点検を通す**: legacy の plan は公開前提で書かれていない。秘密・第三者の本文・私的な戦略・`$HOME` 実値を点検し、出せないものは非公開の置き場に残すか除外する
- **ADR / RFC からのリンク**: 振り分けた plan が特定の ADR / RFC の原本なら、その ADR / RFC に日付付きの注記でリンクを足す（任意）

## Drawbacks

- ADR-0085 Decision 6（既存 255 本は移さない — 中身の点検なしに repo へ入れない）を開き直す。点検の手間がそのまま費用になる
- 点検をすり抜けた機微が公開される危険。公開は撤回できない
- worktree・`/private/tmp`・repo でない cwd で作られた plan は、振り分け先が一意に決まらない

## Rationale and alternatives

- **何もしない（ADR-0085 の既定）**: 過去の判断の原本が辿れないまま残る
- **全部を各 repo の非公開置き場へ**: 点検の手間は消えるが、公開の照合可能性は増えない。公開 repo に出すのは点検を通った分だけ、という中間案が本 RFC

## Unresolved questions

- 点検を人がやるか、エージェントの一次仕分け + 人の確認にするか
- 承認されなかった・放棄された plan をどう扱うか（ADR-0085 では commit しなくてよい）
- worktree 由来の plan を元の repo に寄せるか

## Status

**2026-09-27 draft** — 著者の起票指示。親は RFC-0027（指摘と Eval の照合可能な公開）。着手時に ADR-0085 Decision 6 へ日付付き注記が要る。

## Next action

会話ログから plan → cwd → repo の対応表を作り、repo ごとの本数を出す。

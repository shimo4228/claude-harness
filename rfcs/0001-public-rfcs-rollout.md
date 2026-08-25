---
state: candidate 2026-08-25
review-when: 対象 repo すべてで展開が完了し dual-read を畳んだ時、または ADR-0049 が supersede された時
---

## Summary

タスク台帳を持つ全 repo に公開 `rfcs/` 台帳を展開し、store 形の正本を
`.notes/tasks/`（非公開）から `rfcs/`（公開）へ移し切る。

## Motivation

判断の記録を非公開の作業場に置くのは、概念を囲い込まず開放して DOI で帰属を守る戦略
（harness ADR-0007「RFC を書いた人の名前は消えない」）と食い違っていた。ADR-0049 で
harness 本体には `rfcs/` を初設済み — 残りの repo に同じ形を展開し、移行期間の
dual-read を畳むのがこの提案。消費者は、公開 repo を読む人間と LLM（判断の系譜が
読める）、および将来のセッション自身（却下理由が残る）。

## Guide-level explanation

各対象 repo で: ① `rfcs/README.md`（index）を置く ② 既存の store / 単一表の開いている
行を 1 件ずつ移送判断する（そのまま `rfcs/NNNN-slug.md` 化 / 単一表に残す / 終端化）
③ 旧 store が空になったら dual-read の対象から外れる（機構は自然に rfcs/ だけを読む）。
harness の公開ミラーには harness-sync の収集範囲に `rfcs/` を足して載せる。

## Reference-level explanation

- 対象 repo の同定も本作業に含む: `.notes/TASKS.md` または `.notes/tasks/` を持つ repo を
  洗い出す（少なくとも: 本 harness、agent-knowledge-cycle、contemplative-agent 系）
- 展開前に repo ごとに**機微点検を 1 回**行う: 既存タスク本文に公開不可の記述
  （非公開 repo のパス・内部事情）が無いか。あれば本文を公開可能な書き方に直してから
  移送する（機微はリンク先へ — task-stocktake の公開規約）
- 単一表だけの小 repo は移行必須ではない（形は 2 つのまま）。提案性の行が生まれた時に
  rfcs/ を初設する
- harness-sync: 収集 script の対象に `rfcs/` を追加し、公開 repo（claude-harness）に
  含める。secret scan は既存の precommit 経路がそのまま適用される

**進捗（2026-08-25）**: harness 分は実施済み — claude-harness の SUBTREES に `rfcs/` を
追加、HOOK_ALLOWLIST に task-claims-reminder.sh / review-model-notice.sh / claims.py /
両 bats を追加して公開。残りは他 repo への展開と既存台帳行の移送判断。

## Drawbacks

- 公開が既定になるため、起票時に公開可能な書き方を要する（機微の逃がし先を毎回考える
  コストが乗る）
- 移送判断は 1 行ずつの人手判断で、無人化できない（それが正しい — 機微点検を機械に
  丸めない）

## Rationale and alternatives

- `rfcs/` 新設ではなく `.notes/tasks/` の追跡化（gitignore 手術）も検討した — 公開
  ジャンルとして無名で、repo ごとに ignore の負パターンを維持する形になるため退けた
  （ADR-0049 の Alternatives）
- 提案だけ `rfcs/`、作業は台帳という分離案（Rust の RFC → tracking issue 型）は、状態を
  持つ店舗が 2 つになり分散→肥大の既往パターンに当たるため退けた（同上）

## Prior art

- Rust RFC repo（rfcs/NNNN-slug.md、merge された RFC は恒久に残る）
- Anthropic「The AI-native SDLC playbook」（2026-08-21）の intent home
  （共有・version 管理された提案置き場）— 対応は AKC 側の correspondence doc が正本
- harness ADR-0007（open-concept 戦略、TCP/IP RFC モデルの帰属構造）

## Unresolved questions

- private repo（公開先が無い repo）の台帳も rfcs/ 形に揃えるか、`.notes/tasks/` のまま
  残すか（形の統一 vs 公開の意味が無い場所での儀式）
- 既存 ID（T-XXX）の参照が commit message・ADR に残る — 移送時に旧 ID を本文へ併記する
  規約で足りるか

## Future possibilities

- AKC の correspondence doc から「実践している repo 群」として相互参照する
- 却下（dropped）エントリの蓄積が、発散段階の反証に使わない規律（akc-cycle
  「却下記録の読み方」）の実測データになる

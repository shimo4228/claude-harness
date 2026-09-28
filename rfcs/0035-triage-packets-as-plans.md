---
state: done 2026-09-28
review-when: task-triage の dispatch 経路（packet の置き場・cloud-dispatch.sh の前提）が変わったとき。または ADR-0085 の plan 記録層が見直されたとき
---
## Summary

task-triage が build セッションへ渡す kickoff packet を、その repo の `docs/plans/` に plan として commit してから dispatch する。build の commit 本文は `Plan: docs/plans/<file>` でそれを指し、RFC の Status からもリンクする。

## Motivation

packet は build の契約そのもの（受入条件・Phase 0・must-not・review・effort）で、判断役は §4 の検収でこれと diff を突き合わせる。ところが今の置き場は追跡外の `.notes/packets/` か scratchpad で（task-triage §3 step 3）、git にも公開物にも残らない。2026-09-28 時点で各 repo の `.notes/packets/` に 24 本あり、どれも commit から辿れない。

結果として、merge された commit を後から読んでも「何を頼まれて、どこで止まるはずだったか」が分からない。bounce の分類（見落とし / 読み違い）も packet の文面と比べて初めて判定できるのに、その文面が公開記録に無い。ADR-0085 が plan mode の plan について解いたのと同じ問題が、plan mode を通らない dispatch の側に残っている。

## Guide-level explanation

判断役の手順は 1 か所だけ変わる。packet を書く先が `.notes/packets/s<n>.md` から `docs/plans/<slug>.md` になり、dispatch の前に `docs(plan): <slug>` として単独で commit・push する。cloud-dispatch.sh は `main` が clean かつ push 済みであることを既に要求しているので、packet の commit はその前提に自然に収まる。build は clone した `main` の中に自分の packet を読めるようになる。

build の commit 本文には `Plan: docs/plans/<slug>.md` を 1 行足す（ADR-0085 Decision 3 と同じ形）。RFC の Status には `**YYYY-MM-DD plan** — [docs/plans/<slug>](../docs/plans/<slug>.md)` を置く。

## Reference-level explanation

- **変わる artifact**: skill `task-triage` §3 step 3（置き場と commit 手順）、`references/packet-template.md`（`Plan:` 行を commit 本文様式へ、must-not に「`docs/plans/` の自分の packet を編集しない」）。`scripts/cloud-dispatch.sh` は packet のパスを引数に取るだけなので、置き場が変わっても動くかを確かめる
- **packet は凍結する**: dispatch 後に packet を書き換えない。bounce の指示は claim ラベルと bounce message、結果は build の commit 本文に残る。packet の誤り（仮説が外れていた）は packet 自身ではなく、build の Phase 0 報告として残る — それが packet を仮説として扱う template の前提と合う
- **非公開の packet は今の置き場のまま**: `.notes/` の中身や行ログの本文（他 agent の投稿本文・復号した prompt）を含む packet は、もともと local 経路で（task-triage §3 の表）、`.notes/packets/` に残す。公開してよいかの判定は packet-template が既に要求している「rfcs/ エントリと同じ書き方」をそのまま使う
- **公開 repo**: `main` への push は公開にあたる。公開 repo の cloud dispatch は既に人間の OK を待つので（§3 step 4）、packet の push は同じ OK に含める
- **命名**: `<RFC-ID 小文字>-s<n>-<slug>.md`（例 `rfc-0017-s1-...`）とし、plan mode 由来の plan と見分けられるようにする

## Drawbacks

- `main` に dispatch ごとの commit が 1 本増える。bundle で 1 packet にまとめても、1 cycle で数本
- 無人 cycle で private repo に dispatch すると、判断役が人間の確認なしに `docs/plans/` へ commit する。今も task branch の merge は判断役がとる範囲だが、`main` に直接書く種類の commit が 1 つ増える
- 間違っていた packet も公開記録に残る。消せないので、書き方の規律（pointers only）に頼る部分が増える
- task-triage は skill なので、この変更の diff は人間が見る（`boundary.md`）

## Rationale and alternatives

- **何もしない**: packet は判断役の手元にだけ残り、検収後は誰も読まない。build の出力が何に対する出力だったかが公開物から辿れない
- **packet を RFC の Status に直接書く**: 置き場は増えないが、RFC 本文が肥大し、1 packet が複数 RFC を束ねるときに置き場が決まらない
- **`.notes/packets/` を追跡対象にする**: 非公開の repo でしか成り立たず、`.notes/` の非公開前提を崩す
- **cloud-dispatch.jsonl に packet の hash を記録するだけ**: 同一性は確かめられるが、中身は読めないまま

`docs/plans/` を選ぶのは、ADR-0085 が既に「実装前の意図を公開の原本として残す」置き場として定め、`Plan:` 行と harness-sync の同期経路を持っているから。新しい置き場も新しい trailer も要らない。

## Prior art

- ADR-0085（plan を repo の `docs/plans/` に残す。`docs(plan)` の単独 commit と `Plan:` 行）
- RFC-0033（legacy plan を repo へ振り分けた際の公開点検の区分: PUBLIC / FIX / PRIVATE など）
- RFC-0027（指摘と Eval を公開物だけで照合できるようにする親提案）— packet は「何を頼んだか」の環にあたる

## Unresolved questions

- 既存の `.notes/packets/` 24 本を RFC-0033 と同じ点検を通して移すか、ADR-0085 Decision 6 と同じく移さないか
- plan mode の plan と packet が同じタスクに両方あるとき、1 ファイルにまとめるか別ファイルでリンクするか
- local 経路（Agent / spawn-session）の packet も同じ扱いにするか。worktree は `main` から切るので、packet の commit を先に入れれば同じ形になる
- ADR が要るか。task-triage と packet-template は他の artifact から引かれる機構なので、ADR-0085 への注記か新 ADR が要る見込み

## Status

**2026-09-28 draft** — 著者の起票指示（triage cycle 中の発案）。

**2026-09-28 accepted → done** — 著者が採用（「こっちの方が実装として綺麗」）。skill `task-triage` §3 step 2・3 と local path、`references/packet-template.md`（冒頭の説明・Report の `Plan:` 行・must-not）、`scripts/cloud-dispatch.sh` の使用例を変え、ADR-0085 Decision 3 に注記した。Unresolved の決着: 既存の `.notes/packets/` は移さない（ADR-0085 Decision 6 の元の既定と同じく、中身の点検なしに公開しない）/ plan mode の plan と packet は別ファイルにし、packet の「最初に読む」に plan を書く / local 経路も同じ扱い（worktree は packet の commit 後に `main` から切る）/ ADR は新設せず ADR-0085 への注記。

## Next action

なし。最初の実例は次の dispatch の packet。

# 0101: ADR を「従う文書」から「判断の経緯」に変えた — Status と注記手続きを外し、rule の根拠配線を解いた

## Date

2026-11-07

## Context

Plan: [docs/plans/decision-history-not-binding.md](../plans/decision-history-not-binding.md)（承認 2026-11-07）

著者は 2026-08-14 / 08-19 / 09-14 / 11-07 に、Claude が過去の ADR を理由に新しい発想を止めると観測した。
著者の意図は判断の記録で、将来の決定の拘束ではなかった（`contemplative-axioms.md` の Emptiness: directives
are provisional）。同じ観測への介入は 2 回あった。0044（2026-08-19）は「ADR は日付つき仮説」という読み方
protocol を 5 箇所に配線し、0065（2026-09-14）はその配線を撤去した。どちらも ADR をどう読むかの層で、
ADR がどう書かれ何として扱われるかは変えなかった。0065 の Review-when は「2026-10-12 までに観測の記録が
0 件なら満了」としていて MEMORY.md の記録は 0 件だったが、観測は続いていた。止めているのはモデル自身なので
「止めた」と自覚して記録することがなかった。

2026-11-07 の診断（Claude と Codex gpt-6-astra の一致点）: ADR は定義では経緯記録なのに、書き方と扱いが
rule と同じだった。`rules/common/llm-first-code.md:26-28` が ADR の Decision / Review-when / Consequences を
「LLM が従う文書」に数え、skill adr-writer が Decision を命令形で書かせ、agent adr-reviewer が commitment として
書かれているかと先行 ADR との override 関係を検査し、`Status: accepted` が現在形の状態語として 100 本中 96 本に
あり、方針転換のたびに旧 ADR への注記・Status 変更・新 ADR が要り、常駐 rule 15 本の `rationale:` が ADR 番号を
根拠として引いていた。rule として書かれた文書に rule として従うのは、モデルの欠陥でなく仕様どおりの挙動だった。

現行設計の所有者は既に決まっていた: 実物（rule / skill / hook / test / code）と著者の今の指示
（`rules/common/knowledge-staleness.md`「Written descriptions」、2026-10-26）。ADR 層だけに「従う文書」が残り、
harness 自身の worldview と矛盾していた。

`docs/adr` を持つ repo は harness を含め 19（2026-11-07 実測、plan の表）。

## Decision

ADR を「判断の経緯（decision history）」に変えた。記録は過去形で、現行は実物と今の指示が決め、新しい判断は
旧記録と衝突してよく、旧記録は触らない。harness で行ったこと:

- `docs/adr/` を `docs/decision-history/` に、skill `adr-writer` を `decision-history` に、agent `adr-reviewer` を
  `decision-history-reviewer` に改名した。script 名（`adr_lint.py` ほか）と番号は変えなかった。
- `rules/common/llm-first-code.md` の「LLM が従う文書」から ADR を外し、判断の経緯は過去形の記録だと書いた。
  肯定形の書き方規約は残した（書き方の規約と拘束力は別）。著者の 2026-10-11 指示は「肯定形の対象を広げる」で、
  「従え」ではなかったことを著者が 2026-11-07 に確認した。
- `rules/common/akc-cycle.md` の「ADR の扱い」を「判断の経緯」節に書き換えた。
- Status 欄を template から外した。index は番号・題名・日付。0100 以前の `## Status` は書かれた日の状態として
  そのまま残し、README 冒頭にそう書いた。
- skill の Decision を過去形にし、旧記録への注記・Status 変更の手続きを削除した。reviewer の §3 を「何をしたか
  と理由が過去形で書かれているか」に、§7 を「名指した過去の記録へのリンクが実在するか」に変えた。
- 常駐 rule 15 本の `rationale:` を「今この rule が要る理由」に書き直し、記録の番号は任意の `history:`
  コメントに移した。rule・CLAUDE.md・AGENTS.md の本文の `ADR-NNNN` は `経緯 NNNN` にした。
- `scripts/hooks/harness_lint.py` の Review-when 存在 lint（0044 Decision 5）と bats 3 件を退役した。
  `adr_lint.py` は Status を evidence だけにし、directory を `docs/decision-history` → `docs/adr` の順で解決する
  ようにした（未改名の repo でも動く）。context-sync の script も同じ解決にした。
- 既存の記録本文は書き換えなかった。識別子の全面改名（旧本文・commit message の `ADR-NNNN`）もしなかった。
- 他 repo 18 件は Opus の build session に plan を渡して同じ pattern で進める（Phase 1）。

## Review-when

- 著者が「過去の判断を理由に止められた」と感じて引用を貼ったとき、session は `~/.claude/.notes/decision-pull.md`
  に 1 行（日付 / 依頼 / 止めた発言 / 根拠に挙がった記録）を足す。この記録が増え続けるなら、原因は記録の形より
  substrate 側（safety への傾き）にあり、記録を減らす方向でなく「取るべきリスクを取る」側の配線を見る。
- Status 無しの記録で「今どれが現行か」を見失う事故が出たら、現行は実物が持つという前提が repo ごとに成立して
  いない — その repo の README / rule に現行の所在を書く（記録に Status を戻すのではなく）。
- substrate が決定記録の鮮度管理を native に持ったら、この形ごと溶かす。

## Alternatives Considered

### 改名だけ（`docs/adr` → 別名、他はそのまま）

名前は genre の prior を運ぶが、Status・手続き・根拠配線が残れば同じ挙動になる（Claude と Codex の一致）。
改名は役割分離の一部として入れ、単独では採らなかった。

### 読み方 protocol を強める（3 回目）

0044 と 0065 で 2 回、同じ層で効かなかった。文面で「従うな」と書くほど従う対象として想起される
（0065 の「しない型の記述をやめる」原則と同じ理由）。

### 現行設計を所有ファイルへ全件移してから Status を消す（Codex の提案）

方向は正しいが、101 本分の移行は大仕事で、`docs/design/<topic>.md` のような「現行設計の文書」を新設すると
同じ拘束を別名で再生産する。現行の所有者は `knowledge-staleness.md` により実物と決まっているので、移行なしで
Status を消した。未実装の意図や運用上の約束は rule か skill の本文に書く。

### 旧記録を過去形に書き換える

歴史の改変に当たり、コストに見合わない（Codex 同意）。README 冒頭の 1 行で読み方を示した。

### 観測を記録してから介入する

0065 の Review-when がそれを要求して記録は 0 件だった。変更は git で戻せるので、記録は次の判断の材料であって
今回の gate にしなかった。

## Consequences

容易になること:

- 記録を書くコストが下がる（Status の選択、旧記録の注記、Status 変更が消えた）。方針転換が維持より高コストで
  なくなる。
- rule の `rationale:` が自己完結し、rule を変えるのに記録を supersede する手続きが要らない。
- 記録の形が harness の worldview（実物が現行、記述は snapshot）と一致した。

困難になること:

- 「今どれが現行か」を記録から読めない。実物を見る必要がある（これは意図した方向）。
- 旧記録 100 本に `## Status` が残り、新旧で形が違う。README 冒頭の 1 行で読み方を示すに留めた。
- 周辺 skill の散文に「ADR」の語が残る（context-sync、rfc-writer ほか）。Phase 1 と棚卸しで触れたときに直す。
- 公開 copy（claude-harness）の `docs/decision-history/` は harness-sync で同期するまで旧 path のまま。外部からのリンクは
  同期後に切れる。

関連する経緯: [0044](./0044-adr-review-when-and-dated-annotation.md)、[0065](./0065-drop-adr-consultation-wiring-and-build-or-not-gate.md)、[0070](./0070-relax-positive-form-rule-and-verbatim-builtin-overrides.md)、[0089](./0089-adr-filing-bar-three-conditions.md)

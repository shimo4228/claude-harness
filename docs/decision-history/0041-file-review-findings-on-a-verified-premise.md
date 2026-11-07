# ADR-0041: レビュー指摘の起票条件を severity から前提の検証へ移す

## Status

accepted

## Date

2026-08-16

## Context

Contemplative Agent の `scripts/build_decision_packet.py`（週次承認パケットのビルダー）は、
2026-07-29 の初出から 19 日で 12 commit を受け、1366 行のうち 234 行がサニタイズ用ヘルパー、
84 テストのうち 18 本が偽造耐性の主張になった。日付つき review 引用は 18 行ある。
承認セッションの実績は 3 回（年 52 回想定）で、実データに異常値が現れたことは一度もない。

2026-08-16 の security review は同ファイルに 4 つの「サニタイズされていない値が人間の読む
出力に届く」経路を挙げ、それが HIGH の 1 タスク `T-PACKET-FLOOR-BYPASS` として起票された。
調査すると、**4 つとも producer が machine-fixed だった** — `fix_id` は
`parse_findings.py:32` の `^### (F1\.\d+)\.\s+`、`round` は `weekly-pipeline.sh:750` の整数
カウンタ、prompt patch の filename は `weekly-pipeline.sh:850-851`（`local patch=` で構成し
`cp` で書く）。

そして**起票された内容自体が誤っていた**。「filename は fix セッションが `Write(./**)` で
選ぶ」という前提は、`_path_tokens` の docstring（昇格パス一覧の話。あちらでは正しい）からの
横滑りで、`weekly-pipeline.sh:850` を 1 回 grep すれば消えていた。起票したのは reviewer では
なく本ループで、`f0f8c53` の commit message がそう記録している。

受け取り側の既存規則（`rules/common/task-tracking.md`「diff の外の指摘は HIGH 以上だけ起票」）
は**守られていた**。reviewer が HIGH と付けたからである。**severity を付けるのは生成器で、
濾す側は同じ次元で測っていた。**

計測: `security-reviewer` が回った commit は 24 件（fix 20 / feat 2 / refactor 1 / docs 1）、
直近の fix commit はほぼ全部が前の指摘の修理、`.notes/claims.jsonl` の origin は
12 review / 15。CA の ADR-0095 は同じ構造を台帳機構について既に記録している —
「起票が最安の経路だと台帳は減らない」。

## Decision

> **注記（2026-08-27, ADR-0055）**: producer 検証の機構（`--producer` 必須、真偽は
> 起票側の責任、破棄規律）は維持。ただし足切りは「HIGH 以上は起票可」から
> 「loop 自身を壊す欠陥のみ即時起票、他は severity 不問で commit body 1 行」へ
> 更に絞られた（実測の正本は ADR-0055）。

**起票の条件を severity でなく前提に置き、ハーネスが既に持つ唯一の機械的
チョークポイントで強制する。**

- `~/.claude/scripts/claims.py` の `spawn` に `--producer PATH:LINE` を追加する（複数可）。
  **`--origin review` では必須**で、無ければ spawn を拒否する。形式検査は `PATH:LINE` の
  shape のみで、**真偽は検証しない** — それは起票する側の仕事。行番号を必須にするのは
  「このファイルのどこか」を弾くため。それはファイルを開いていない者が書く形である
- 記録先は `.notes/claims.jsonl` の spawn レコードのみ。**タスク frontmatter には書かない** —
  CA ADR-0095 が退役させたのはまさに台帳への writer で、frontmatter を書く claims.py は
  その機構の再導入になる
- `rules/common/task-tracking.md` に、**起票にも修理にも前提の検証を先に要求する**規約を
  書く。時間切れなら**破棄のみ**（修理は逃げ道にならない — 未検証のまま直すと投機的な
  コード変更になり、起票より証拠が少なく残る）。捨てた指摘は severity に関わらず
  commit message に 1 行残す
- **reviewer の定義とルーティング表は変更しない。** 全 reviewer は従来どおり全て起動し、
  全て報告する

## Alternatives Considered

1. **reviewer に producer を引用させ、machine-fixed なら起票させない**（`security-reviewer.md`
   に remit 節を足す）。却下: 後半が抑制規則で、producer を誤判定した reviewer は**本物の
   指摘を無音で落とす**。落ちた指摘は観測できない。本ループが捨てる形なら誤りは commit
   message に残る。実際にこの流れには本物の指摘があった（ambient allow-rules と
   コマンドフラグ経由の書き込み、symlink 追従書き込み）。**同じ論拠を提示した判定者自身が
   「provenance の追跡は LLM がまさに失敗した作業」と述べており、それは抑制を reviewer 側に
   置く案にこそ強く当たる**

2. **引用は課すが抑制はさせない（A-lite）**。無音の性質を持たず、本ループの検証を安くする。
   **却下せず保留** — 今回の失敗は「reviewer が引用しなかった」ではなく「本ループが偽の
   producer を足した」なので、先に入れると効果の帰属が分からなくなる。下の tripwire が
   鳴ったら入れる

3. **ルーティング条件を「境界を新設・拡張する diff のみ」に切り替える**。却下:
   **`f0f8c53` でも発火する** — あの diff はサニタイズの床を動かしたので条件を満たす。
   volume の調整弁であって、この指摘のフィルタではない

4. **「前の指摘の修理は同じ reviewer を回さない」終端規則**。却下: 判定誤りが fail-open
   （不完全な修理が無レビューで通る。実例: `f0f8c53` は `_cell` を通る側だけを閉じた）。
   `feedback_review_agents_not_optional` とも衝突する

5. **受け取り側の severity 閾値を上げる**。却下: severity は生成器が設定する次元

6. **何もしない**。却下: 受け取り側の対処は既に入っており、それでも 12/15 が `origin: review`

## Consequences

- **解決しないこと**: 生成コストと anchoring は減らない。境界を 1 バイトも増やさない feat にも
  Security Review が無条件で回り、既存 enum を狭めるだけの fix でも発火する。前提の検証は
  **台帳**を守るが、レビューの所要時間・トークン・文脈の圧迫は戻らない。`security-reviewer.md`
  は web アプリ向けの OWASP テンプレートのまま
- 新しい偽陰性リスク: 形だけ整った誤った引用は機械的に弾けない。真偽の判定は本ループに残る
- **ゲートが縛るのは journal であって store ではない。** `.notes/tasks/T-XXX.md` を直接書けば、
  引用も spawn レコードも無いまま `claims.py ready` に載るタスクができる。強制されるのは
  「系譜を記録するなら引用を付ける」であって「起票するなら引用を付ける」ではない。
  したがって効果測定は、cited spawn の減少を**遵守と読んではならない** — 回避の可能性がある。
  下の 3 値の記録が store 側の新規ファイルも数えるのはこのため
- 効果測定は次の 20 発火で、候補ごとの処分を `verified-repair` / `verified-file` /
  `discarded-unverified` の 3 値と、**候補件数・レビュー所要時間**で記録する。
  `origin: review` 比率は使わない — タスクになった指摘しか数えないので、
  「本ループが偽候補を全部**修理**で処理する」失敗を取り逃す
- **tripwire**: `discarded-unverified` が候補の 50% を超え続ける、または候補件数が減らないまま
  検証時間が 1 発火あたり 15 分を超えたら、Alternative 2（A-lite）を再検討する。
  台帳に載った件数だけを見ると、コストが台帳の外に移っただけの状態を「改善」と読み違える
- **失効条件**: ① 上の tripwire ② 前提検証を通した指摘の誤りが判明した（1 件で再判断に値する）
  ③ substrate が provenance 判定を native に持った（Scaffold Dissolution の downward、
  `generation-audit` の再監査対象）

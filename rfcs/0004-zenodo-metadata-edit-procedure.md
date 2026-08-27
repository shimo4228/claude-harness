---
state: draft 2026-08-25
review-when: Zenodo が legacy deposition API（/api/deposit/depositions）を廃止・変更した時、または Zenodo の relation 語彙が DataCite 4.6+ に追随した時（後者は release-doi の SWHID review-when と同時に本提案の適用場面が 1 つ増える）
---

## Summary

Zenodo published record への relation metadata 反映（新 version なしの metadata-only edit）を、使い捨て script から再利用可能な手順・道具へ昇格するかを検討する。

2026-08-25 に DataCite relation 完成作業（authorship-strategy ADR-0002 の相互宣言規律の
執行）で、6 つの published record を unlock → merge → publish の API 3 手で編集し、
DataCite への伝播を実測確認した。実装はセッション scratchpad の ad-hoc script で、
セッション終了とともに消える。同型の作業は再発が見込まれるため、手順の固定先と
自動化の度合いを判断したい。

## Motivation

再発が見込まれる場面（いずれも release cadence を待たずに registry を直したい場面）:

1. **相互宣言の欠落発見**: ADR-0002 は A→B 宣言に B→A の逆 relation を求めるが、
   実際には片側だけの宣言が数ヶ月残っていた（2026-08-25 の評価で発見・修正）。
   次の欠落も点検のたびに出うる
2. **新 sibling 追加時の retrofit**: ADR-0002 自身が「既存 record は管理画面で
   metadata 編集して retrofit する」と定めるが、API 版の手順はどこにも収載されていない
3. **Zenodo の relation 語彙が DataCite 4.6+ に追随した時**: release-doi skill の
   review-when 注記どおり、全 repo の version DOI → SWHID relation を一括投影する
   場面が来る（本 RFC の道具があればその日の作業が 1 セッションで済む）
4. **local `.zenodo.json` と registry の既知 drift**（未 release 編集が registry に
   届いていない状態）の点検・選択的解消

現状、手順の knowledge は authorship-strategy の task 台帳 D45 行と本セッションの
記録にしか無く、scratchpad の動作実績 script は揮発する。

## Guide-level explanation

採用された場合: 「record X に relation Y を足して」という指示が、release を待たず、
管理画面を開かず、dry-run → --apply の 2 段で完了する。既定は dry-run（現状と追加差分の
表示のみ）で、publish は明示 flag。実行は対話セッション限定 — 外部 platform への
書き込みなので無人 cron には載せない。

## Reference-level explanation

動作確認済みの API flow（2026-08-25、6 record で実証）:

```
GET  /api/deposit/depositions/{id}            # 現 metadata 取得
POST /api/deposit/depositions/{id}/actions/edit    # published record を unlock
PUT  /api/deposit/depositions/{id}            # metadata 全置換（related_identifiers を merge）
POST /api/deposit/depositions/{id}/actions/publish # 再公開（新 version は増えない）
# PUT 失敗時は POST …/actions/discard で draft を破棄
```

- 対象 record の同定: concept DOI → `GET /api/records/{concept_id}` が latest version に
  解決される（redirect 追随要）
- dedup: (relation, identifier) の組で既存 entry と照合してから merge
- 伝播: publish 後数十秒で DataCite relatedIdentifiers に反映（実測）。concept record の
  metadata も latest version に追随する
- rate-limit 規律: 逐次実行 + sleep。連発時は policy signal として停止（rules/common/debugging.md）

候補となる形（排他ではない）:

- **A. 手順化のみ**: release-doi skill に「published-record metadata edit」節を追記し、
  API flow を収載。script は都度書く
- **B. script 昇格**: 動作実績 script（引数 = record id、ADDITIONS 相当は入力ファイル化、
  dry-run 既定）を release-doi skill の scripts/ に置く
- **C. drift 検査の追加**: local `.zenodo.json` と registry の related_identifiers diff を
  表示する read-only subcommand（B の随伴。書き込みはしない）

## Drawbacks

- 使用頻度が低ければ道具は純増コスト（CA ADR-0095: 台帳を扱うコードの肥大の先例。
  Build-or-not 4 問の対象）。年数回なら A（手順化のみ）で足りる可能性が高い
- 書き込み道具の常設は「registry を気軽に触る」誘因になる。ADR-0002 の建前は
  release 同梱が正常系で、metadata edit は retrofit の例外経路 — 道具がその主従を
  逆転させないよう、skill 側に使用条件を書く必要がある

## Rationale and alternatives

- **既存流用の検討（search-first 未実施 — 採用判断の前に要照合)**: `zenodo-client` /
  `zenodo_get` 等の既存 CLI・ライブラリが metadata-only edit を安全にカバーするか。
  カバーするなら B は不要で A + 依存 1 つになる
- **何もしない**: 手順は task 台帳の done 行に残っており、次回も再導出は可能。
  ただし再導出コスト（API の discard 挙動・concept→latest 解決などの罠）は毎回払う
- **Zenodo 管理画面での手作業**: ADR-0002 の原案。record 数が増えた現在
  （6 repo × 累積 version）はスケールしない

## Prior art

- authorship-strategy ADR-0002 "Application discipline"（retrofit 操作の宣言元）と
  2026-08-25 日付つき注記（相互宣言の完成 + Event Data 停止の環境変化）
- release-doi skill の SWHID review-when 注記（本道具の将来の適用場面 3）
- 2026-08-25 実施記録: authorship-strategy 台帳 D45（6 record 編集、
  AS 40→44 / AKC 38→39 / CA 28→29 / AAP 23→24 / doctrine-corpus 7→8 /
  existence-proof 4→5、DataCite 伝播実測）

## Unresolved questions

- 置き場所: release-doi skill の scripts/ か、独立 script か（skill 内が第一候補 —
  使用文脈が release/retrofit に限られるため）
- C（drift 検査）を初回 scope に含めるか、B の使用実績を待つか
- 既存 CLI の search-first 結果次第で B 自体が不要になるか

## Future possibilities

- Zenodo が SWHID relation type に対応した日の一括投影（全 repo × version DOI）を
  本道具 + 入力ファイル生成（CITATION.cff の swh entry から）で 1 セッション化
- citation-sync skill の 4 層同期に「registry 層」を第 5 層として繋ぐ（現状は
  local `.zenodo.json` まで）

## Status

draft — 起票のみ（2026-08-25、authorship-strategy セッションでの 6 record 編集の直後）。
採否判断・search-first・build-or-not は未実施。

## Next action

次に同型の retrofit 需要が出た時、または著者が採否を判断する時: ①既存 CLI の
search-first → ②Build-or-not 自答（頻度見積り込み）→ ③A/B/C の選択。A だけなら
release-doi skill への追記で即完了できる。

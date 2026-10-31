kind: internal
# 再生比較の結果 — judge が実装する形は、packet で dispatch する形より悪くならないか

事前登録: [2026-10-26-replay-prereg.md](2026-10-26-replay-prereg.md)（規則と計器の修正の注記はそちらが正本）。
Plan: [subagent-fold.html](../subagent-fold.html) claim 3・4。script: `~/.claude/scripts/replay/`（`analyze.py` で再集計できる）。
run の生データ（stream・判定・verify ログ）は `~/MyAI_Lab/replay-runs/`（git 管理外）。

## 結論

**規則 1 を満たさないので、task-triage の既定は替えない**（plan claim 4 は実施しない）。旧形（packet で fresh な
build session）は 16 run すべて合格、新形（台帳を全部判定したあと同じ session で実装）は 16 run のうち 2 run が落ちた。
1 本は判定役が環境由来の verify 失敗を拾ったもので実装の差ではないが、それを除いても 1/16 対 0/16 で結論は同じ。

## 再現

8 タスク × 2 形 × 2 run = 32 run、Opus（settings の effort）、auto mode、実 repo・他 session の transcript・GitHub の
repo の取得は deny。採点は run の後に外から: verify（正解の木と比べて増えた失敗）・Claude Fable の受入条件判定・漏れ。

| task | 正解 | 旧形 r1 r2 | 新形 r1 r2 | run 全体の context の最大（千 token, 旧 / 新） | compact（旧 / 新） |
|---|---|---|---|---|---|
| s1 | ✓ | ✓ ✓ | ✓ ✓ | 226, 224 / 253, 265 | 0, 0 / 0, 0 |
| s2 | ✓ | ✓ ✓ | ✓ ✓ | 290, 286 / 316, 319 | 0, 0 / 0, 0 |
| s3 | ✗ 4 | ✓ ✓ | ✓ ✓ | 254, 264 / 300, 314 | 0, 0 / 0, 0 |
| s4 | ✓ | ✓ ✓ | ✓ ✓ | 331, 365 / 366, 362 | 0, 0 / 0, 1 |
| a | ✗ 8 | ✓ ✓ | ✓ ✓ | 365, 366 / 365, 359 | 1, 1 / 1, 1 |
| a1 | ✓ | ✓ ✓ | **✗** ✓ | 241, 254 / 318, 305 | 0, 0 / 0, 0 |
| s29 | ✓ | ✓ ✓ | **✗** ✓ | 347, 364 / 366, 367 | 0, 1 / 1, 1 |
| s32 | ✓ | ✓ ✓ | ✓ ✓ | 282, 231 / 321, 350 | 0, 0 / 0, 0 |

（context の列は run 全体の最大値。新形は判定の段で約 15〜25 万 token を積んでから実装に入る）

| 形 | 失敗 | 費用（list 価格の合計） | 平均時間 | 平均 context 最大 | 平均 turn |
|---|---|---|---|---|---|
| 旧形 packet | 0 / 16 | $122.8 | 17.1 分 | 293K | 57 |
| 新形 judge | 2 / 16 | $151.8 | 20.7 分 | 328K | 80 |

## 原因（規則 2）

- **a1 新形 r1** — 未達は「verify が exit 0」の 1 項目だけ。落ちたのは `tests/test_claude_cli_backend.py::test_environment_is_an_allowlist`
  と eval-staleness で、正解の木でも同じく落ちる（`grade.py --verify-diff` で増えた失敗は 0）。同じ失敗を持つ a1 の他の 3 run は、
  判定役が環境由来と読んで met にした。**判定役の揺れで、実装の差ではない。**
- **s29 新形 r1** — ADR-0113 の Consumption plan を「RFC-0046 と同文」とする指示から外れた。adr-reviewer の指摘で (c) を書き換え、
  Review 行には書いたが Deviations 行で名指ししなかった。この run は context が 366K まで育ち、compact が 1 回起きた。
  ただし s29 は旧形 r2・新形 r2 も compact して合格しており、compact だけでは落ちない。**packet の細部の指示（「同文」）が、
  大きな context と compact の後に保たれなかった可能性が高い。** 確かめるには n が足りない。

## 規則 3・4

- 規則 3: s29 型（ADR と doc を多く伴う feat で、context が compact の閾値 400K に近づくタスク）は、judge の context の大きさが
  効く候補。既定を替えないので、この型を例外に残す判断も今は要らない。
- 規則 4: 旧形の 2 run で片方だけ落ちたタスクは 0 件（新形は 2 件）。

## 計器について（結果を読む前に直したもの。詳細は事前登録の注記）

- s3・s4 の base を正解の直接の親に直した（S1〜S4 は merge で main に入った）。誤った base の 4 run は両形とも Phase 0 で
  正しく止まり、比較から外した
- 漏れの検出を 2 度直した（自分の session の退避ファイル・upstream PR の `gh`・`graph.jsonld` の URL 文字列は数えない）。
  直した後の漏れは 0 run
- 判定役を codex から Claude Fable 5.1 に替えた。codex は gpt-6-astra しか使えず、5 時間の枠で 2〜3 本で上限に達した。
  Fable は実装者（Opus）と同系統で独立性は下がるが、偏りは両形に同じく効く
- 判定の厳しさ: 正解 commit は Fable で 6/8 合格（s3 は 4 項目、a は 8 項目未達）。codex は正解 s1 にも 8 項目未達を付けた
  （Fable は 0）。正解が落ちる項目を再生は満たしていることがあり、正解は packet の後で著者と方針を変えた箇所を含む
- 正解テストを後から置く検査は、関数名の違いで両形ともほぼ同じ件数が落ちた（補助の読み値。合否に入れていない）

## 限界

- 8 タスク × 2 run。非劣性は統計で示せない。2/16 対 0/16 も、偶然と区別できない
- wiki の 6 タスクは同じ RFC 系統で相関する
- 新形にも同じ packet を渡した。この比較が測ったのは「判定で積んだ context が実装を悪くするか」で、judge が packet 相当の
  設計を自分で書けるかは測っていない。本番の新形では packet を書く工程が消えるので、そこで失われる情報（設計の取り違え）は
  この比較の外にある
- 新形は平均で費用 +24%、時間 +21%、turn +40%。判定の段の分を含む

## Still unknown

- s29 の失敗が context の大きさによるものか、run の揺れか（同じタスクを n を増やして回せば分かる）
- 判断役の session（本番は数十万 token）で、実装の質が context の大きさとともにどう落ちるか

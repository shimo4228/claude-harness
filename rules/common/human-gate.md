<!-- origin: shimo4228 -->
<!-- rationale: ADR-0019 — ゲートの第 2 軸（artifact は機械 / intent は人間）を Reversibility Gate から分離して新設。AKC harness-alignment（ADR-0017 / DOI 10.5281/zenodo.20578272）の human-gated 条項と line of approval（AKC glossary）の運用版（定義本文は複製しない）。2026-07-28: 証拠生成物カテゴリ・昇格規則・固定スキーマを cross-model review 起点で追加。2026-07-29: substrate 照合監査で根拠 prose を ADR-0019 へ層分離、redundancy（列挙・ログ保存条項）を hook/ADR へ退避、固定 5 フィールドスキーマを「差分宣言 1 点必須」に縮退（worst case 防御の核だけ残して形式はモデルの較正に委譲） -->
<!-- review-when: harness の native 承認 UI が本文提示 / 意図要約の分岐を運ぶようになった時 / AKC 側 harness-alignment 条項が改版された時 -->
# Human Gate — 人間は何を判断するか

**いつ止まるか**は可逆性で決まる（[`coding-style.md`](coding-style.md) の Reversibility Gate）。
**止まったとき人間が何を判断するか**がこのファイル（経緯と根拠:
[ADR-0019](../../docs/adr/0019-human-gate-layer.md)）。

## artifact は機械、intent は人間

機械化された検査で判定できる正しさは決定論ゲートと review agent が持ち、**人間を artifact 検査に
戻さない**（一次責任の割り当てであって保証ではない — 残余リスクは昇格規則で受ける）。
review agent は**検査者であって承認者ではない**（generator–verifier gap）。承認は
「決定論ゲートの PASS」＋「人間の intent 判断」で構成し、**LLM 単独の承認経路を作らない**。

## ゲートで提示するもの（対象で分岐）

- **behavior-shaping artifact**（rules / skills / identity / 公開ドキュメント）・**control plane**
  （hooks / permissions 等の権限・自動実行定義）・**検査の証拠を作るもの**（検出の正本:
  `hooks/evidence-file-notice.sh`）→ **本文を提示**。要約に畳むと「検査を緩める変更」が隠れる
- **実装コード・生成物** → **意図の要約**。diff 本文と PASS 一覧は提示しない
- **昇格規則** — 不可逆・高影響な変更は対象区分にかかわらず本文または該当差分を提示する
  （第 1 軸が第 2 軸を上書きする）
- **FAIL は例外** — 決定論ゲートの FAIL は**検出行そのもの**を提示する。秘密の実値はマスクし、
  偽陽性判定（[`security.md`](security.md) の `*_BYPASS`）の持ち主は人間

## 1 作業 1 ゲート

意図確認は作業単位の完了点に **1 回**。commit / push / 公開 / 付随更新は**件数とスコープを
明示列挙した 1 回の承認**に束ねる。例外は決定論ゲートの FAIL と `plan との差分: 再承認が必要` のみ。

## 意図の要約 — 差分宣言だけは必須

要約の形は対象に合わせて較正してよい。ただし **`plan との差分`（なし / あり / 再承認が必要）**の
3 値宣言を必ず含め、照合先は介入点 1（[`planning.md`](planning.md)）で承認した plan に固定する。

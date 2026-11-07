<!-- origin: shimo4228 -->
<!-- rationale: skill 導入済み環境向けのポインター版。全機構を所有者へのポインターとして登載し、本 rule 自身が所有するのは Scaffold Dissolution（判定基準含む）と判断の経緯の扱いのみ。skill 未導入環境向けの自己完結版は akc-cycle repo が別内容で持つ -->
<!-- review-when: ポインター先の skill / rule が改廃された時 / substrate が knowledge cycle を native 化した時 / モデル世代交代時 / substrate が決定記録の鮮度管理を native に持った時（判断の経緯の節を溶かす） -->
<!-- history: docs/decision-history/0018, 0035, 0065, 0101 -->
# AKC Rules (pointer edition)

AKC の全機構と所有者。手順・本文は所有者側が正本で、ここには複製しない。

| 機構 | 所有者 |
|---|---|
| 6 phase 手順 | Research→skill: `search-first` / Extract→`learn-eval` / Curate→`skill-health`・`*-stocktake` / Promote→`rules-distill` / Measure→`skill-comply` / Maintain→`context-sync`・`repo-asset-stocktake` |
| 三役ループ・LLM-first・expiry-conditioned knowledge（AKC 経緯 0024〜0026） | skill: `task-triage`、rule: `llm-first-code.md`・`knowledge-staleness.md`、skill: `decision-history` |
| 自己完結版（skill 未導入環境向け） | akc-cycle repo の `rules/common/akc-cycle.md`（本ファイルとは別内容） |

## Scaffold Dissolution

rule は足場であり、実践が自然に回るようになれば簡素化・削除する。

- **Inward** — 原則が会話パターンに吸収された
- **Downward** — substrate が capability を native に持ち、手書き rule が古い既定を上書きする

モデル世代交代も downward のトリガー。旧世代向けの禁止・網羅的手順・反復強調は
skill: `generation-audit` で再監査する。

判定基準（AKC 経緯 0022 / 経緯 0023）:

- **完了証拠は held-out transfer** — 同一文脈での ablation 判別不能は必要証拠止まり。
  溶かしてよい証拠は、scaffold 無しの新文脈で挙動が再現すること
- **負の極は積極削除** — 負の情報差分を持つ artifact（古い既定を上書きする drift した
  rule 等）は放置でなく削除する。沈黙・ablation・transfer はいずれも「不在」しか検出
  できず負の差分に盲目なので、モデル世代交代時の generation review で監査する

## 判断の経緯

`docs/decision-history/` は起きたことの記録で、過去形で書く。現行の設計は実物（rule / skill / hook / test /
code）と著者の今の指示が決め、記録は理由と当時の事実を持つ。新しい判断は旧記録と衝突してよく、旧記録は
そのまま置く。記録を書くか commit 本文で済ませるかの条件は skill: `decision-history` が持つ。

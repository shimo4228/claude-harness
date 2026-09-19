<!-- origin: shimo4228 -->
<!-- rationale: ADR-0018 + ADR-0035 + 二版化（2026-09-01）— skill 導入済み環境向けのポインター版。全機構を所有者へのポインターとして登載し、本 rule 自身が所有するのは Scaffold Dissolution（判定基準含む）と ADR の扱いのみ。skill 未導入環境向けの自己完結版は akc-cycle repo が別内容で持つ -->
<!-- review-when: ポインター先の skill / rule が改廃された時 / substrate が knowledge cycle を native 化した時 / モデル世代交代時 / substrate が決定記録の鮮度管理を native に持った時（ADR の扱い節を溶かす） -->
# AKC Rules (pointer edition)

AKC の全機構と所有者。手順・本文は所有者側が正本で、ここには複製しない。

| 機構 | 所有者 |
|---|---|
| 6 phase 手順 | Research→skill: `search-first` / Extract→`learn-eval` / Curate→`skill-health`+`skill-stocktake`+`rules-stocktake`+`agent-stocktake` / Promote→`rules-distill` / Measure→`skill-comply` / Maintain→`context-sync`+`repo-asset-stocktake`（mutable snapshot — AKC ADR-0019） |
| 三役ループ judge/build/human（AKC ADR-0024） | skill: `task-triage`、rule: `planning.md` |
| LLM-first artifact readability（AKC ADR-0025） | rule: `llm-first-code.md` |
| expiry-conditioned knowledge（AKC ADR-0026） | rule: `knowledge-staleness.md` + 本 rule の「ADR の扱い」節 |
| mental model / instance の区別（AKC ADR-0027） | AKC repo の CLAUDE.md（harness rule の対象外） |
| 自己完結版（skill 未導入環境向け） | akc-cycle repo `rules/common/akc-cycle.md`（本ファイルとは別内容 — 二版化 2026-09-01） |

## Scaffold Dissolution

rule は足場であり、実践が自然に回るようになれば簡素化・削除する。

- **Inward** — 原則が会話パターンに吸収された
- **Downward** — substrate が capability を native に持ち、手書き rule が古い既定を上書きする

モデル世代交代も downward のトリガー。旧世代向けの禁止・網羅的手順・反復強調は
skill: `generation-audit` で再監査する。

判定基準（AKC ADR-0022 / ADR-0023）:

- **完了証拠は held-out transfer** — 同一文脈での ablation 判別不能は必要証拠止まり。
  溶かしてよい証拠は、scaffold 無しの新文脈で挙動が再現すること
- **負の極は積極削除** — 負の情報差分を持つ artifact（古い既定を上書きする drift した
  rule 等）は放置でなく削除する。沈黙・ablation・transfer はいずれも「不在」しか検出
  できず負の差分に盲目なので、モデル世代交代時の generation review で監査する

## ADR の扱い

ADR は日付つきの経緯記録。既存機構を変更するとき経緯を読む。新しい判断が旧 ADR と衝突したら
supersede し、旧 ADR の該当節に `> **注記（YYYY-MM-DD, ADR-NNNN）**` を残す（ADR-0044）。
起票するのは、他の artifact が引く機構・ゲート・閾値・agent 階層の変更か、旧 ADR の supersede /
注記を伴うときだけ。それ以外の判断は commit 本文に `Context:` / `Decision:` / `Review-when:` の
3 行で残す（正本は skill: `adr-writer`、ADR-0072）。

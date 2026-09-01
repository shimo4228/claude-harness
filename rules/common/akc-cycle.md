<!-- origin: shimo4228 -->
<!-- rationale: ADR-0018 + ADR-0035 + 二版化（2026-09-01）— skill 導入済み環境向けのポインター版。全機構を所有者へのポインターとして登載し、本 rule 自身が所有するのは Scaffold Dissolution（判定基準含む）と ADR / 却下記録の読み方のみ。skill 未導入環境向けの自己完結版は akc-cycle repo が別内容で持つ -->
<!-- review-when: ポインター先の skill / rule が改廃された時 / substrate が knowledge cycle を native 化した時 / モデル世代交代時 / 発散と照合の分離が会話パターンに吸収された時（却下記録の読み方節を溶かす） -->
# AKC Rules (pointer edition)

AKC の全機構と所有者。手順・本文は所有者側が正本で、ここには複製しない。

| 機構 | 所有者 |
|---|---|
| 6 phase 手順 | Research→skill: `search-first` / Extract→`learn-eval` / Curate→`skill-health`+`skill-stocktake`+`rules-stocktake`+`agent-stocktake` / Promote→`rules-distill` / Measure→`skill-comply` / Maintain→`context-sync`+`repo-asset-stocktake`（mutable snapshot — AKC ADR-0019） |
| 三役ループ judge/build/human（AKC ADR-0024） | skill: `task-triage`、rule: `planning.md` |
| LLM-first artifact readability（AKC ADR-0025） | rule: `llm-first-code.md` |
| expiry-conditioned knowledge（AKC ADR-0026） | rule: `knowledge-staleness.md` + 本 rule の「ADR も足場」「却下記録の読み方」節 |
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

## ADR も足場である（2026-08-14 著者指示）

ADR はその時点の一時的判断の記録であって、恒久的な拘束ではない。新しいアイデアや
観測が既存 ADR と衝突するとき、ADR を理由にアイデアを狭めない — supersede が正常系。
これは公理 Emptiness（全 directive は文脈依存の guideline であり固定した本質を持たない）
の適用でもある。記録は残し、判断は上書きする。初期コンセプト・初期構造にも同じことが
言える: プロジェクトの発展を初期の足場が阻害し始めたら、足場の方を溶かす。

読み方（ADR-0044）: ADR は日付つき仮説。`Date` と `## Review-when`（失効条件。0044 以降は
必須、無い旧 ADR は Context の前提と Date で重みを決める）を先に見る。失効条件が発火した・
前提が消えた ADR に拘束力は無い — 衝突は「supersede 候補」として提示し、旧 ADR には削除で
なく日付つき注記を残す。

## 却下記録の読み方（2026-08-24 著者指示）

memory の「再提案しない」ガードにも上と同じ読み方を適用する — 日付つき仮説であり、
失効条件の無いガードは弱い推定として扱う（knowledge-staleness の受け側。却下判断だけ
陳腐化しない扱いにしない）。

**発散と照合を分離する**: 新アイデアの発散段階では ADR・memory の却下記録を反証に
使わない。照合は採用判断の段で初めて行い、衝突は却下理由でなく supersede 候補として
提示する。「再提案しない」は re-deploy の禁止であって問い空間には適用しない
（具体手順の先例: skill `authorship-strategy` の inquiry-first）。

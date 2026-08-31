---
state: done 2026-08-30
review-when: review-to-lint skill 自体が改廃されたら。候補の正本 skill が大幅改修されたら該当行の sweep 実測は失効
---
## Summary

review-to-lint（ADR-0051）の水平展開候補 12 件の台帳。優先順は機械化余地でなく需要の発火条件で決め、確定 5 件（RFC-0006〜0010）は Opus 実装セッションへ委譲、残りは発火条件つきで保留する。

## Motivation

skill 新設時の適用候補リスト（SKILL.md 末尾、citation-formatter 起点の 4 件）は sweep 前の推定だった。2026-08-26 の grill-me セッションで agents/ 25 本 + skills/ 67 本を Explore 2 体で走査した結果、候補は 12 件あり、「機械化余地の大きい順」は誤った優先軸だと判明した（機械化率最大の citation-formatter は直近需要が無い）。リストを SKILL.md に持つと sweep のたびに skill 本文が肥大するため、台帳は本 RFC に移し SKILL.md はポインタだけ持つ（著者指示 2026-08-26）。

## Reference-level explanation

駆動原理: **需要駆動** — 「明確な需要 × 安定した正本」の交差だけ実施。作り置きは形骸化リスク（ADR-0051 Negative「skill を経由しない編集に効かない」がそのまま増える）。

### 候補台帳

| # | 候補 | 状態 | 発火条件 |
|---|---|---|---|
| 1 | context-sync — チェックリスト 20 項目中 15 が deterministic、実行コマンド既載で抽出コスト最小 | **RFC-0006** | 確定 |
| 2 | paper 系の束 — citation-formatter ほぼ丸ごと（約 16 項目中 14）+ paper-ecosystem / paper-writing の deposit gate（orphan 双方向 mapping・脚注 1:1・style 混在・DOI/arXiv 形式）+ vocabulary-consistency-checker の term inventory 層 + paper-reviewer 構造項目 | 保留 | 次の paper 作業開始時。WebFetch 実在確認は `--online` flag に隔離し evidence モードは offline 完結（方針のみ先に固定） |
| 3 | writing-ecosystem 系の束 — editor / essay-reviewer / prose-clarity-reviewer / clarity-reviewer + quality-gate + collect-context + x-draft。readme_evidence.py の骨格（term_candidates / insider_refs / prose_signals）流用可 | 保留（global 側のみ） | writing-ecosystem の設計安定後（著者判断 2026-08-26: 流動中の正本への接木は drift 負債）。**2026-08-27 注記**: zenn-content の project-local な Zenn 層は先行実施済み（`scripts/zenn_evidence.py`、zenn-content ADR-0012）。channel contract 固有で cross-repo 性が無く、流動中の global 正本に触れないため保留の射程外。global 側を実施するとき fence 除外パーサ・register カウント・self-link 位置の重複を引き直す |
| 4 | agent-stocktake — harness_lint 未カバー分: name=stem・tools 実在・description 近似重複・suppression 文言の regex 列挙（hybrid の教科書例） | **RFC-0007** | 確定 |
| 5 | config-gc — 8 チャンネルを 1 scan script に束ねる（orphan hook / permission 重複 / cache は script 済み） | 保留 | 次の月次 GC 前 |
| 6 | URL liveness 共通部品 — skill-stocktake / context-sync / paper-ecosystem の 3 箇所が要求、既存 script のどれも持たない | **RFC-0008** | 確定（#1/#7 の依存） |
| 7 | skill-stocktake 残余 — URL live check + usage 集計 4 補正規則の script 化（毎回 LLM が jq を再実装している） | **RFC-0009** | 確定 |
| 8 | citation-sync 残余 — arXiv/Crossref API 照合（hallucinated ID 検出、実害事例あり）+ graph_lint 既知バグ（1 行ノード形式・DOI regex の `)` 終端）修正 | 保留 | 次の引用追加時 |
| 9 | fact-checker local evidence 層 — 機械化率でなく injection 面: transcript metadata 抽出を script に降ろし「message body を読めない」をコードの性質にする（2026-07-25 F20） | 保留 | 価値主導・任意 |
| 10 | learn-eval — grounding checklist の overlap 候補（既存 skill / MEMORY.md）の機械列挙 | **RFC-0010** | 確定 |
| 11 | task-stocktake — enum 検証・日付書式・obsoleted の引用存在 | 保留 | CA ADR-0095 系「台帳を読む機構を足さない」宣言との衝突を解いてから |
| 12 | repo-asset-stocktake — tier-1 reachability scan | 保留 | 本文自身の保留条件「同じ scan が複数 run 繰り返されたら」の成立後 |
| 13 | **兄弟 hook 群への横展開漏れ** — 同型の防御・イディオムが兄弟 hook の一部にしか入っていない。実測（2026-08-29 再測）: git を呼ぶ hook は 7 本でうち `-c core.fsmonitor=` guard 済み 5 本、欠落は `hooks/task-claims-reminder.sh:61` の 1 行。`${BASH_SOURCE[0]%/*}` 移行と `\| head -N` の SIGPIPE ガードは解消済み | 保留 | 履歴掘削で発見（2026-08-29）。**hybrid** — 素の grep は 7 本中 2 本を偽陽性にした（`validate-bash.sh` の block メッセージは文字列リテラルであって git 呼び出しではない）ので、コメント・文字列の除外が要る。producer: 6 セッション（`9032200a` / `d16c74ae` / `f9ef3213` / `e47c0c17` / `a1278e97` / `948c2e02`）。採用実績: commit `21f51cc`（7 hook 一括修正）、T-007（secret-scan と bandit の同型修正）。`rules/common/security.md` の Response Protocol 5「同種の問題を洗う」に対応する検査が無い。**指摘は概ね採用済みで、クラスが反復するのは戻りを止める ratchet が無いため** — 価値は残 1 行の解消より回帰防止にある |
| 14 | **同一の値・narrative の複数箇所ハードコード** — 正本参照でなく複製。実測: Chain Matrix セル値が hook に直書き、baseline 実測値が 3 箇所、「実測 4.3ms」が 1 commit 内で 2 値、advisory truncation が 2 箇所 | 保留 | 履歴掘削で発見（2026-08-29）。hybrid — script が「2 箇所以上に現れる数値リテラル / 固有文字列」を列挙し、LLM が正本かを判定。producer: 5 セッション（`9e6c8386` / `ceb75c19` / `9032200a` / `d16c74ae` / `9b5187d8`）。採用実績: `references/review-output-format.md` への統合、ADR-0055「重複配線の解消」。#4 の「description 近似重複」は skill description のみで射程が違う |
| 15 | **hook の fail-open** — helper 不在・`source` 失敗・marker 不在で検査が黙って無効化される | 保留 | 履歴掘削で発見（2026-08-29）。hybrid〜semantic — `\|\| exit 0` / `\|\| true` が block 判定より前にある形は grep できるが、意図的な fail-soft との区別に LLM が要る。producer: 6 セッション（`9032200a` / `f041e797` / `9e6c8386` / `f9ef3213` / `ceb75c19` / `12692db3`）。採用実績: ADR-0057 / commit `90a92c8` |

### 履歴掘削の実測（2026-08-29）

候補 #1〜#12 は **reviewer のチェックリストを読んで**出した供給側の棚卸しだった。これが
履歴に残る反復指摘を見落としていないかを 1 回だけ手で調べた（コード資産ゼロ、機構は作らない
—— ADR-0055 Decision 5 の「回収機構は作らない」に触れないため）。

- corpus: `projects/<project>/<session-id>/subagents/agent-*.jsonl` の最終 assistant message。
  harness 63 セッション / 248 agent のうち reviewer 系 135 本 / 39 セッション
- 事前登録した閾値: 同一クラスが 3 回以上 かつ 2 セッション以上、採用実績 1 件以上、
  退役 reviewer（python-reviewer = ADR-0039、旧 code-reviewer = ADR-0042）由来のみのクラスは数えない
- 結果: **見落とし 3 件**（#13〜#15）。いずれも harness 自身の**実行資産（`hooks/*.sh`）**を
  対象とするクラスで、#1〜#12 はすべて document / skill-asset 層を対象としており該当が無い。
  `harness_lint.py`（frontmatter / name=stem / markdown link / rules metadata / ADR Review-when）も
  document 層のみ、`verify.sh` の shellcheck（`-S style -e SC1091`）は汎用 shell style のみで、
  兄弟 hook 間の一貫性は誰も見ていない
- 需要駆動は維持する。#13〜#15 も発火条件つきの保留であり、作り置きはしない。
  **#13 の残 gap は 1 行**（再測で判明）で、価値は回帰防止の ratchet にある。次に `hooks/` を触るときが発火条件
- 手調査が 2 回目に要求されたら、それが抽出 script の需要トリガー。その時点で ADR-0055 の
  supersede 込みで再提案する（今回は 1 回の調査で足りた）

### やらない（判定理由ごと記録）

- **swift-reviewer**: script を書かず SwiftLint / swift-format / Swift 6 strict concurrency へ委譲して削るのが正解だが、著者は agent 自体の退役を検討中（2026-08-26）— 別件
- **security-reviewer**: 既に「既存ゲートへ委譲して薄化」した完成形（件数表も拒否）。#3 以降の着地の先例として引く
- **rules-stocktake**: harness_lint.py がほぼカバー済み（残余は README ツリー整合のみ）
- **title-reviewer / theme-reviewer / generation-audit / loop-design-check / authorship-strategy**: 機械化余地が低い、または頻度がほぼゼロで ROI が立たない
- **llm-as-judge / skill-health**: 適用対象でなく review-to-lint の理論的正本・完成見本

## Rationale and alternatives

- 供給駆動で一括消化する案 — 却下: 使われない lint は形骸化し、正本改修のたびに drift 負債になる
- リストを SKILL.md に置き続ける案 — 却下: sweep のたびに skill 本文が肥大。skill は手順、台帳は rfcs/ という分担（ADR-0049 と同型）

## Unresolved questions

- #11 の CA ADR-0095 衝突の解き方（enum lint と引用存在検査は非侵襲に足せる余地あり）
- WebFetch 依存検査の script 側配置の一般則（#2 着手時に ADR 化）

## Status

accepted — 確定 5 件（RFC-0006〜0010）は 2026-08-27 に全件実装・merge 完了（ADR-0052/0053/0054）。build の diff 外 HIGH 4 件を RFC-0011〜0014 として起票し S4 で実装中。保留 7 件は発火条件待ち。2026-08-27

**triage 照合 2026-08-29**: RFC-0011〜0015 も merge 済み（`0ee9ce6` / `851c12e`）で、本 RFC 由来の着手可能な作業は残っていない。残る 7 件はそれぞれ別の発火条件を持つ**候補台帳**であり、`accepted`（= 今選べば着手できる）のままだと `claims.py ready` が毎 cycle これを dispatch 可能として出す。状態語彙の当て直しをオーナーに確認中（候補台帳としてこのまま残すか、`blocked` 相当へ落とすか）。

**履歴掘削 2026-08-29**: reviewer 履歴 135 本 / 39 セッションを 1 回手調査し、候補 #13〜#15 を追加した（見落とし 3 件）。いずれも `hooks/*.sh` を対象とするクラスで、#1〜#12 の document / skill-asset 層とは重ならない。抽出機構は作っていない（ADR-0055 Decision 5「回収機構は作らない」に触れないため）。保留は 10 件になった。

## Next action

**done 2026-08-30（オーナー確認済み）— 本エントリは以後「候補台帳」として参照専用。**
#13 が名指していた具体的欠陥（`hooks/task-claims-reminder.sh:61` の `core.fsmonitor` guard 欠落）は
commit `4766e2b` で解消し、確定 5 件（RFC-0006〜0010）と派生 RFC-0011〜0015 も全て merge 済みで、
本 RFC 由来の着手可能な作業は残っていない。残る保留 10 件はそれぞれ別の発火条件を持つ候補であり、
`accepted` のままだと `claims.py ready` が毎 cycle これを dispatchable として誤報するため終端した
（rfcs は archive しない規約なので、候補台帳としての参照は切れない）。

保留候補は各発火条件が成立したセッションで本 RFC を参照して**個別に新規起票**する。

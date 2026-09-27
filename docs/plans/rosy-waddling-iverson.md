# 設計パケット: 期間 KPI の非定常性（2026-08-22、反証後）

**著者決定 2026-08-22: 案 a（採用案 1–4 全部）。T-002 は ready へ戻す。**

入口: `.notes/handoff-eval-window-nonstationarity.md`（commit 4cc7b8c）。このセッションは実装しない。

## Context

著者の問い: Eval は期間を区切って実績を見るが、この界隈は 1 週間で陳腐化する。窓が閉じる前に
skill / code 自体を変えるし外部環境も変わる。期間 KPI はどうあるべきか。
ADR-0046 Review-when「3 回連続の skill 作成で通読指摘 ≥2」を書いた直後に出た。

## 前提（一次照合済み 2026-08-22、反証で修正した箇所は ✎）

- F1 ✎ **意味のある版の寿命は 1〜2 週、窓（3 回作成 ≈ 6 日）と同じ桁。** skill-creator は 30 日で
  4 commit だが実質改稿は cb902cc の 1 回（他は 1〜8 行）。readme-writer は 79 日 11 commit のうち
  20 行超の改稿 6 回（≈13 日に 1 回）。commit 数 ≠ 版数（Codex 指摘を採用）。作成率は
  `git log --diff-filter=A --since=60.days -- 'skills/*/SKILL.md' 'agents/*.md'` = 32 commit / 36 file
  → ADR-0046 の「2 日に 1 本」は再現（architect の「3.2 日」は reflog 件名だけの集計で不採用）
- F2 **判定器も同じ速さで変わる。** readme-judge checklist は 08-19 新設 → 08-22 K1–K6 拡張（2.4 日）。
  さらに ADR-0046 の判定器は checklist でなく**著者**（skill-creator:85）で、版管理できない
- F3 **計測器が版を持たない。** `metrics/skill-usage.jsonl` 2,700 行、key に版 / hash 無し
- F4 ✎ **窓 KPI は 12 か所だが 5 file、うち 5 つは今日書いた ADR-0046。** Review-when を持つ ADR は
  3 本（0044 / 0045 / 0046）で **3 本とも件数条件を含む**。rules の `review-when:` 12 件は全部
  事象型。「1 週間前に始まった書き方」であって repo 横断の規約ではない
- F5 **窓 KPI が正しく発火した先例** authorship-strategy:184（対象 = 外部 counter で固定）
- F6 ✎ **T-002 の 成立時 が名指す機構（zero-usage rule）は 08-15 に撤廃済み**（47d0a38、
  skill-stocktake:210）。再開条件（log 90 日）自体は生きている。無人 cycle 2 回は日付だけ照合。
  ただし同じ表の T-EVAL-AXIS は 照合先 消滅を 08-17 に既存手順で捕捉済 — 取りこぼし率 1/2
- F7 ✎ **ADR-0046 の gate 観測は 0 件**。`git log --grep` が拾う 2b2de30 は KPI を*定義*した
  commit で、観測ではない（architect 指摘を一次照合で確認）
- F8 ✎ adr-reviewer:37 は観測可能性だけ、task-triage:54-66 の dead-band は 照合先 だけ見る。
  **task-stocktake:81-87「イベント条件の決着規約」が「発火源が消えたら retired」を既に持つ**
  （CA T-B4 先例）— ただし対象は 再開条件 が待つ artifact で、成立時 が名指す機構は範囲外
- F9 adr-reviewer の実使用 43 回 / 22 日 / 8 repo（`metrics/agent-usage.jsonl`）— ここに書けば読まれる

## 目的

件数・期間の条件を書くとき、「窓の間に固定されているべき対象（本文の節 / 判定器 / slot）」を
**書く時点で名指し**、名指せなければ件数をやめて事象条件にする。機構も語彙も増やさない。

## 採用案（3 編集 + 台帳 1 セル。新規機構・新規 ADR なし）

1. **`agents/adr-reviewer.md` §1 に 1 項目**（:38 の直後）:
   「件数・期間の条件は、窓の間 固定されている対象（本文の節 / 判定器 / slot）を名指しているか。
   名指せないなら件数条件をやめて事象条件に書き直す」。検出のみ（:24）、偽陽性は 1 行のコスト
2. **`skills/task-stocktake/SKILL.md:81-82` の決着規約を 1 語広げる**: 再開条件・照合先 に加えて
   **成立時 が名指す機構**（閾値 / rule / 判定器）が消えた場合も決着（`retired` か条件の書き直し）。
   task-stocktake は triage の直前に毎週回る（task-triage:245）ので dead-band を壊さない
3. **ADR-0046 Review-when 2 行目に日付つき注記**（削除しない、ADR-0044 の形）:
   「2026-08-22: 数値ゲートは測定不能 — gate 観測 0 件、対象本文と判定器（著者）が週単位で
   変わる。Decision 5 は著者判断に戻す」。版 pin は書かない（P1 を再輸入するため）
4. **T-002（TASKS.md:13）を今日直す**: 成立時 の zero-usage rule は撤廃済。本数削減は
   skill-stocktake の「観測頻度 vs description の期待頻度」で**今すぐ**回せる → `ready` に戻して
   再開条件を外す（`retired` でなく条件の書き直し。usage 90 日は不要になった）

著者の問いへの答え（1 行）: **速く変わる対象に件数窓は成立しない。件数は slot（name /
description）と固定機構にだけ使い、本文・判定器の質は事象条件か著者判断で見る。**

## 捨てた案（反証結果つき）

| 案 | 処分 | 根拠 |
|---|---|---|
| 版 hash で機械リセット（前 session 案 1） | 捨て | P1: F1 で 1 版 ≈ 窓、F7 観測 0 — 永遠に N に届かない |
| 観測に sha を刻み読む側が判断（本 packet 初稿 B） | 捨て | architect: コストを毎回の判定に移すだけ。Codex: 判定器 = 著者で版復元不能（P3） |
| 同期 eval 主・縦断は判定器校正のみ（前 session 案 2） | 捨て | F2: 判定器も 2.4 日で変わる。slot 到達（T-002 型）は縦断でしか見えない |
| 3 型の表 (a)(b)(c)（本 packet 初稿 A） | 捨て | architect: (c) は窓なしの残余で型でない。表より「1 問」（task-stocktake:71 の形）→ 採用 1 に畳む |
| task-triage Condition に前提 grep を足す（初稿 C-2） | 捨て | Codex + architect 一致: dead-band 行では Condition が走らず F6 を直さない。gitignore で grep が偽 0 を返し live task を retired にする失敗面が元の欠陥より重い |
| knowledge-staleness.md に内向き条項 | 捨て | 常駐 rule は環境固有事実の層。原則の常駐は 40% 天井 |
| 何も書かず git で戻す | 捨て | F6 で取りこぼし 1/2。ただし採用 2 は既存規約の 1 語拡張なので「ほぼ何もしない」に近い |
| readme-writer:207 に「checklist 版ごと集計」 | 捨て | 観測 n=1（通読 5 件、1 回）で版分割する意味が無い |
| skill-usage.jsonl に版 hash 列 | 捨て | slot 型に不要、hook 実行時間がログ長比例（hooks/README:55） |
| 独立 ADR を切る | 捨て | architect: 注記 3 に理由を畳めば足りる。F4 の母集団は 5 file |

## 失効条件

- `claude plugin eval` が iteration 世代管理 / 旧版 baseline を native に持ったら、採用 1 の
  「名指し」は native の版管理に委ね、項目を外す
- skill 本文の実質改稿が 30 日に 1 回以下に鈍化したら、件数窓を時間窓として復活させてよい
- 採用 1 の項目が拾った件数は adr-reviewer 出力がログされないため**観測できない**（architect
  指摘）。代わりに「次に Review-when を書く ADR 3 本で、件数条件が固定対象を名指しているか」を
  著者が目視 — 3 本とも自然に名指していたら項目は Inward 吸収として外す

## 反証ログ（採る / 捨てる、折衷なし）

Codex（gpt-5.6-sol、VERDICT premise-hole）:
- REFUTE commit 数 ≠ 版数 → **採る**（F1 修正）
- REFUTE C-2 は dead-band 行で走らない → **採る**（C-2 破棄）
- MISSING 判定器 = 著者で版復元不能 → **採る**（B 破棄の決定打）

architect（VERDICT Build smaller）:
- F1 作成率 3.2 日 → **捨てる**（reflog 件名集計。`--diff-filter=A` 一次照合で 32/60 日）
- F7 観測 0 件 → **採る**
- F8 task-stocktake 決着規約の先例 → **採る**（採用 2 の置き場）
- A 表 / B / C-2 / D-3 Don't build → **採る**
- C-1 adr-reviewer Build（43 回/22 日実使用） → **採る**（一次照合済）
- D-1 版 pin でなく「測定不能、著者判断へ」 → **採る**
- 失効条件 3 が観測不能 → **採る**（書き直し）
- T-002 は今日 1 セル → **採る**（ただし retired でなく ready へ — 再開条件の前提が消えただけで
  タスク本体は生きている。architect は処分を指定していない）

## 実装セッションへの verification

- adr-reviewer に ADR-0046 を再レビューさせ、追加項目が Review-when 2 行目（件数条件）を拾う
- task-stocktake を harness に 1 回回し、T-002 の 成立時 失効を新規約で拾う
- `bats tests/harness-lint-precommit.bats` green（lint は触らない。内容検査は LLM 側 — ADR-0021）
- `git diff --stat` が 4 file 以内（adr-reviewer.md / task-stocktake SKILL.md / ADR-0046 / TASKS.md）

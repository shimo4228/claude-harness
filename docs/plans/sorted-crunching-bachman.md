# Plan: gap-review を retire、ledger 廃止、public timeline のみ authorship に残す

## Context（なぜこの変更か）

**発端**: gap-review が「新しいアイデアを出してほしい」場面で必ず発動し、スコープを
非常に狭める。

**診断（対話で確定）**:
- gap-review は設計上の**収束（exploitation）ツール** — Step 2「既存 catalog との差分」＋
  Step 4「既存 gate で濾過」。発散（新アイデア/catalog 拡張）は構造的に生成できない。
- 真の力の源は description でなく **上流 authorship-strategy**。rule
  (`rules/common/authorship-strategy.md:32`) と skill 判断チェックリスト
  (`authorship-strategy/SKILL.md:215`) が「次の一手 → gap-review を先に回す」と
  **発散の前段に収束を強制**していた。doctrine は line 20 で「候補生成は常に full space を
  母集団に」と発散を義務づけているのに、入口を収束ツールに固定する自己矛盾。
- gap-review は **premature abstraction**。hard 依存する framework は authorship-strategy
  ただ 1 つ（他 3 skill は soft 参照）。akc-cycle の scaffold-dissolution（inward）の典型。

**ledger の再評価（対話で確定）**:
- gap-review の "two-tier ledger" のうち **Tier 1（private operational ledger）は冗長**。
  「ランク付き候補」＝未 triage の task、「deploy status」＝完了 task / git の劣化コピー。
  TASKS.md（task-tracking の単一台帳）と二重で、これが「task 責務曖昧」の元。
- **triage/dedup メモリ**（検討済み案の記録）は実在する需要だが、専用 ledger 不要:
  - **promoted**（採用）→ 既に TASKS.md の行（active/Done）
  - **dismissed**（却下）→ TASKS.md の**廃止行 + 理由**で残す（task-tracking rule が既に
    「廃止タスクは Done 節へ移動、判断履歴を残す」と規定）
  - **wiki 由来候補** → wiki-harvest が自前 `.notes/wiki-harvest/ledger.md` で status 冪等管理
- **Tier 2（public effect-claim-free timeline）だけ残す**。「いつ何を撃ったか」の日付付き・
  因果主張なし記録は将来 attribution 遡源の基盤（authorship thesis の実証）で on-thesis。
  ただし apparatus 不要 — 単なる公開 changelog。Tier 1 消滅で「two-tier」は解消し、
  **単一 public timeline** になる（update-order も private ledger 消滅で不要）。

**ユーザー制約（決定的）**: authorship-strategy で gap-review の代わりに **wiki-harvest を
必須ステップに据えない**。wiki-harvest も source 制限された収束生成器 = 必須入口にすると
同じ narrowing を再発させる。wiki-harvest は user-invoked のまま据え置く。

**意図する結果**: gap-review skill を削除して trigger 面を消し発火問題を根絶。「次の一手」を
`full-space 発散生成 → 判断チェックリスト gate → 生き残りは TASKS.md 行（却下は廃止行）→
deploy したら public timeline に1行` に簡素化。専用 ledger apparatus は全廃、正本は
TASKS.md 一本。

---

## Changes

### 1. gap-review skill を削除
- `skills/gap-review/`（`SKILL.md` + `evals/`）を削除。
- `gc_log.md` に retirement エントリを追記: 日付・理由（premature abstraction /
  ledger は TASKS.md へ吸収）・復元経路（git 履歴）。

### 2. `skills/authorship-strategy/SKILL.md` — "Operating over time" 節を書き換え
gap-review skill への正本委譲を除去し、簡素化した手続きを**自己完結の doctrine text** 化:
- **default の明示**: 「次の一手」の default は **full-space 発散生成**（line 20 母集団 =
  開発者コミュニティ / content platform / creative-reuse seeding / 各言語圏 / catalog
  未収載の新型 channel）→ 判断チェックリスト gate。**catalog-diff apparatus は載せない** —
  既出荷の重複確認は「TASKS.md（active/Done/廃止）+ git を見る」で足りると明記。
- **triage メモリ**: 採用した案は TASKS.md 行に、**却下した案は TASKS.md の廃止行 + 理由**に
  残す（再生成時の重複排除）。専用 ledger は持たない。
- **Tier 2 のみ残す**: deploy した手は **public effect-claim-free timeline**（日付付き・
  因果主張なし changelog）に 1 行記録。source は git/現実/TASKS.md。private ledger を
  経由しない（update-order は不要）。「two-tier」呼称は廃し「public intervention timeline」に。
- **wiki-harvest を代替入口として据えない**（本文で必須ステップ化しない）。
- L215 判断チェックリスト項目を書き換え: 「gap-review を先に回したか？」→
  「**full-space 発散生成 → gate → TASKS.md 記録（却下は廃止行）→ deploy したら public
  timeline に1行**、の順か？既出荷は TASKS.md + git で確認」。skill / wiki-harvest pointer は置かない。
- L186/188/192/194 の gap-review 正本委譲・two-tier 記述を上記に整理。two-tier discipline の
  根拠 ADR-0014 参照は、Tier 1 廃止に伴い「public timeline のみ」に整合する形へ調整
  （ADR 番号は研究 repo 側、据え置き）。

### 3. `rules/common/authorship-strategy.md:32` — rule 書き換え（先の in-flight 編集を上書き）
> 注: plan mode 前に L32 へ reposition 編集を 1 つ入れ済み。本 plan で完全に上書きする。

書き換え内容: 「次の一手 → full-space 発散生成を先に（既存 catalog に縛らない）→ 判断
チェックリスト gate → 生き残りは TASKS.md（却下は廃止行）→ deploy した手は public
effect-claim-free timeline に日付付き・因果主張なしで記録」。**gap-review skill 名を名指し
しない。wiki-harvest を必須入口にしない。private operational ledger を持たない。**
手続き正本は authorship-strategy skill "Operating over time"（自己完結先）を指す。

### 4. soft 参照の清掃（3 ファイル）
- `skills/wiki-harvest/SKILL.md`: L12「gap-review の wiki→repo 版」/ L76「gap-review の
  two-tier 規律を担保」の gap-review 参照句を削除し自己完結の平文へ。**wiki-harvest を
  authorship へ格上げしない**。自前 ledger の記述はそのまま。
- `skills/ai-native-preprint-submission/SKILL.md:201`: 「two-tier ledger は gap-review /
  ADR-0014」→ gap-review 参照を除去。Tier 1 廃止に伴い「public timeline のみ」に整合させ
  authorship-strategy "Operating over time" or ADR-0014 に repoint。
- `skills/task-stocktake/SKILL.md:57`: 例示列挙から `gap-review /` を削り「wiki-harvest 型の」に。

### 5. 二次確認（非ブロッキング）
- ADR-0014 / ADR-0021 参照は研究 repo 側の ADR 採番（portability 上正常）。除去するのは
  co-located な "gap-review skill" pointer のみ。ADR 番号は据え置き。
- repo コピー（claude-harness 公開 repo）は触らない。global のみ変更。削除の公開反映は
  後日 harness-sync が伝播する。

---

## Verification（chain 最終ステップ）

1. **See-skill pointer lint**: harness_lint（doc リンク / See-skill pointer 検査、直近
   commit c03a052）を実行。retire 後に `gap-review` への live skill pointer が残れば fail
   → 決定論ゲート。gc_log.md の履歴以外に live 参照が無いことを確認。
2. **grep 確認**: `grep -rn "gap-review" ~/.claude --include="*.md" | grep -v gc_log` が
   空（or 履歴的言及のみ）。
3. **自己完結・再発防止の目視**: authorship "Operating over time" と rule L32 が dangling
   pointer 無しで読め、**full-space 発散が default、catalog-diff / wiki-harvest が必須入口に
   なっていない**こと。**private operational ledger の記述が残っていない**こと。triage は
   TASKS.md（廃止行）に委ねられていること。
4. **YAML 検証**: 編集した各 skill の frontmatter が有効。
5. **git status 確認**: 意図しないファイル無し。`skills/gap-review/` が削除ステージに乗る。

全 PASS でユーザーに diff 提示 → 承認後 commit
（`chore(skills): gap-review retire、ledger を TASKS.md へ吸収、public timeline のみ authorship に残す`）。

---

## 触らないもの（スコープ厳守）
- **wiki-harvest**: standalone user-invoked skill のまま。authorship の必須ステップに格上げしない。自前 ledger も残す。
- **gap-review を "発散モード追加" で延命しない**（却下済み）。
- **TASKS.md の task-tracking rule 本体**は変更しない（既存の「廃止行を Done 節に残す」規約を
  triage メモリとして活用するだけ。rule 追記は不要）。
- repo コピー / 公開 repo。

# RFC-0018 実施プラン — description 挙動汚染軸の検査・撤去の恒常配線

## Context

RFC-0018（draft）は、skill description を「字数コスト」でなく「未監査の常駐指示層（第 2 の rules 層）」として検査・撤去する軸を立てる提案。前提条件だった RFC-0017 は完了済み（commit 3fee7d1）。

調査で確定した事実:

- RFC-0017 の恒常配線（skill-health Phase 3 / skill-stocktake Hygiene 問 / skill-creator §1・§3）は**すべて字数・bloat 軸**。description 内の指示文の挙動監査は 1 行も入っていない — RFC-0018 の空き地はここ
- 検査項目 2（狙いと実測の照合）は既存計器 `skills/skill-stocktake/scripts/usage_stats.py` で足りる。新規計測は不要
- **検査項目 3 は前提消滅**: 「RFC-0017 で B を割り当てた `ai-native-preprint-submission`」は実際には B 適用 0 本で、手段 D により paper-lab へ移設済み（global に存在しない）。RFC 本文の修正が要る
- 著者判断（2026-08-29、AskUserQuestion）: **配線のみ・A/B 計器は建てない**。skill-comply 拡張の測定案は Unresolved に残す

## Build-or-not 4 問（judge-tier 自答 — implementation-chain L74）

1. **存在すべきか**: 新規機構・script・agent は建てない。既存 3 skill への散文追記 + RFC 本文修正 + 初回監査 1 パスのみ。計器は既存 usage_stats を「読み方だけ変えて」流用
2. **適正な大きさ**: skill-stocktake +1 問（6 行以内）、skill-health 判断軸の書き換え 2 行、skill-creator 追記 1〜2 行。**追記合計 15 行以内**を上限とする
3. **誰が消費するか**: 次回以降の skill-stocktake / skill-health 実行セッション（列挙・判定）、skill-creator の新規作成時（予防）。読み手のいない出力は作らない
4. **失効条件**: RFC-0018 の review-when と同一 — substrate が listing 注入方式を変えた時 / 善意 description の干渉効果量を直接測った研究・計器が得られた時

## 変更内容

### 1. skills/skill-stocktake/SKILL.md — Stage 1 に 6 問目「Description audit」

RFC-0017 が Hygiene（5 問目）を足したのと同じ手つきで追加する:

- 問い: description 内の**常駐指示文**（NOT for ルーティング、「Use PROACTIVELY」型発火指示、他 skill への言及）を列挙し、「この指示の狙い（自発発火・誤発火防止）を invoke 実測が裏づけるか。裏づけない指示は body / 既存 rule に降ろせるか」を問う
- 抽出は semantic（LLM 分類）— regex script は作らない（feedback_regex_vs_semantic）
- usage は parent-owned dimension の既存規約を崩さない（batch agent には渡さない — anchoring 回避）
- 「five questions」→「six questions」の全箇所修正（RFC-0017 の four→five と同じ）

### 2. skills/skill-health/SKILL.md — Phase 3 判断軸の更新（B 案の格下げ）

residency-fold の判断軸「listing が唯一の入口 → 1 行 description」を書き換える:

- 「1 行でも常駐は常駐（Contextual Entrainment は token 単位で効く）。**到達経路を明示参照（他 skill / rule からの 1 行）で作った上での `disable-model-invocation`（A）が既定**。1 行 description は明示参照を張る先が無い場合の次善」

### 3. skills/skill-creator/SKILL.md — 挙動汚染の根拠 1 行

§1 / §3 の「disable-model-invocation を既定に検討」の行へ、字数でなく挙動の根拠を 1 行追加: 「description は未監査の常駐指示層 — listing に載るだけで挙動に干渉しうる（RFC-0018）」。

### 4. rfcs/0018-description-behavior-contamination.md — 本文修正と採否記録

- 検査項目 3 に前提消滅の日付つき注記（`ai-native-preprint-submission` は B でなく手段 D で移設済み。B 適用は 0 本）
- Status に採否と実施内容（配線のみ・計器は建てない、Build-or-not 自答の要点）を追記
- Unresolved の測定案（skill-comply Tier 1 + sandbox 注入で「足す方向 A/B」の足場はある / listing から抜く制御口は無い）を調査結果で具体化して残す
- state: `draft` → 実装完了時に `done`

### 5. 初回監査パス（残る description の棚卸し）

RFC-0018 の切り分け（「軸の恒常化**と残る description の監査**」）に従い、新 6 問目を 1 回適用する:

- 対象: listing に残る skill（`disable-model-invocation` なし、~55 本）。窓不足 3 本（measurement-discipline / repair-discipline / loop-design-check）は判定禁止のまま除外
- `usage_stats.py --days 90` の実測と突き合わせ、**指示文を含み・かつ invoke 実測が狙いを裏づけないもの**だけを表にする（狙いと実測が一致している trigger surface は巻き込まない — RFC の Drawbacks）
- 表を著者に提示し **confirm-each** で適用（description から指示文を body へ降ろす / 削る）。一括適用しない

## 実行者・chain（implementation-chain）

- 種別: chore。**このセッションで自己実装** — 例外 (a)「skill / rule の散文編集は judge-tier の本業」を適用（この 1 行がその記録）
- 散文編集のみ・コード変更なし。commit 前は `hooks/review-chain-notice.sh` の確認と `git status`（doc sync: rfcs/README.md の index 行の state 更新を含む）
- 公開 repo への同期は別途 skill: `harness-sync`（このプランの範囲外、必要なら著者が呼ぶ）

## 検証

1. 追記合計が 15 行以内であることを diff で確認（Build-or-not ②の宣言と照合）
2. skill-stocktake の「six questions」表記が全箇所一致していることを grep で確認
3. YAML frontmatter を触らないため YAML 検証は不要だが、`python3 scripts/harness_lint.py`（存在すれば）を 1 回通す
4. 初回監査パスの表: 各行に description の指示文引用 + usage_stats の実測値（deliberate / read）が付いていること — 引用の無い行は出さない

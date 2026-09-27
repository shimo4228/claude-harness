# メモリー全面棚卸し + 発散/照合分離の harness 配線

## Context

却下記録（memory の「再提案しない」スレッド + ADR）が新アイデアの発散段階で免疫系として働き、アイデアが広がらない。Explore 調査の実測:

- 明示的な再提案抑止は 12 群（A1–A12）+ 却下記録 18 件（B 群）。**失効条件が明確なのは少数**（模範例は A8 mmr-retrieval: 3 択 OR 条件 + 再開時に読む path + 凍結 verdict）。A3 は照合先（`.notes/TASKS.md` T-SKILLSEL）が ADR-0095 で廃止済み、A9⑤（Gemma 12B deferred）は発火源の MLX 自体が退役した「死んだ deferred」、A9②（LiteLLM 却下）は as-of 依存の外部調査なのに valid-until なし
- **MEMORY.md 索引では「禁止」だけが無料で伝播し、失効条件を運ぶ行は 1 本のみ**（38 行目、しかも照合先廃止済み）
- `akc-cycle.md` の読み方プロトコル（日付つき仮説・failed Review-when に拘束力なし・supersede 正常系）は **ADR にしか適用されておらず、memory ガードはその外**にいる。`knowledge-staleness.md` は「失効条件の無い推奨は弱く扱う」と言うが、受け側（失効条件の無い**抑止**をどう読むか）が無い
- 求める分離手順は新規発明でなく、`skills/authorship-strategy/SKILL.md:196-224` の **inquiry-first**（問い段階では台帳・却下ガードを読まない / 「再提案しない」は re-deploy の禁止であって問い空間には適用しない / dedup は記録段で初めて）に完成形がある。これを global に持ち上げる

範囲の確定事項: メモリーは全面棚卸し、harness 配線 (b) を含む、ADR 監査は今回見送り。

## Part 1: memory 全面棚卸し

対象: `~/.claude/projects/-Users-<user>-MyAI-Lab-contemplative-agent/memory/`

### 1-1. 却下・抑止系スレッドの失効条件付け（A 群 12 + B 群該当分）

各「再提案しない / 却下 / 見送り / deferred」記述を次の形式に統一:

> 再提案しない。**失効条件**: 〜（無効化イベント or valid-until）。再評価時は〜を読む。

- 失効条件が既にあるもの（A2, A8, A11 等）: 形式を揃えるだけ
- 書けるのに書かれていないもの（A5 consolidator, A6 task-state, A10 jargon 等）: ファイル内の根拠（読み値・根本原因）から失効条件を起こす。例: A10 は「根 D（insight 抽出プロンプトの jargon クローン量産）が直ったら」
- **どうしても書けないもの**: 「失効条件を言語化できない = 弱い却下（日付つき推定）」と明記して格下げ。恒久寄りの原理的却下（A7 observation-over-steering, A9①）は「恒久（原理due）」と明記して区別
- 個別修理:
  - A3 `project_skill_loading_all_injected.md`: 照合先を現行の `.notes/tasks/` 形式へ更新（T-SKILLSEL の生死を実ファイルで確認してから）
  - A9 `project_mlx_backend.md`: ⑤ Gemma 12B deferred は発火源消滅を注記して閉じる。② LiteLLM 却下に as-of 日付 + 「次に backend 選定が起きたら search-first で再調査」を付ける

### 1-2. 済んだ・古いスレッドの削除と統合

- `project_2stage_distill.md`（ADR-0060/0072 に委譲済みの経緯のみ）等、ADR / 実コードが正本を持ち memory が経緯の複製になっているものは削除（要旨 1 行を統合先 or MEMORY.md に残す）
- `project_mlx_backend.md` 等の長大スレッドは完了項を圧縮
- 削除は 1 件ずつ内容確認の上で行い、判断に迷うものは削除せず「stale 候補」と注記に留める

### 1-3. MEMORY.md 索引の書式規約と スリム化

- **抑止を運ぶ索引行の新規約: 禁止文言を載せるなら失効条件の要旨を同じ行に載せる。** 載せられない行は禁止文言を索引から外し本文参照にする（索引層で「禁止」だけが無料伝播する非対称の解消）
- 削除・統合に合わせて索引行を刈る。規約自体は MEMORY.md 冒頭に 1 行で明記

## Part 2: harness 配線（正本 `~/.claude/`）

前提: harness 変更なので着手時に skill: `harness-boundary` を 1 回通す（implementation-chain の規約）。公開 copy への同期は harness-sync で別途。

### 2-1. `rules/common/akc-cycle.md` — 「却下記録の読み方」追記（3–6 行）

「ADR も足場である」節の直後に:

1. **memory の「再提案しない」ガードも同じ読み方**を適用する — 日付つき仮説であり、失効条件の無いガードは弱い推定として扱う（knowledge-staleness の受け側）
2. **発散と照合の分離** — 新アイデアの発散段階では ADR・memory の却下記録を反証に使わない。照合は採用判断の段で初めて行い、衝突は「却下理由」でなく supersede 候補として提示する。「再提案しない」は re-deploy の禁止であって問い空間には適用しない（具体手順の先例: skill `authorship-strategy` の inquiry-first）

ファイル冒頭の `review-when` コメントも整合更新。

### 2-2. `agents/architect.md` — 1 文追記

既存の「An existing ADR is prior context, not a veto」bullet の直後に、memory の抑止ガードにも同じ zero-base test を適用する（失効条件が無ければ日付と根拠の性質で重みを決める）旨を並置。

### 2-3. `planning.md` は触らない

純粋配線表（ADR-0035）であり、akc-cycle が常駐 rule として同じセッションに載るため新入口は不要。

## Verification

- `python3 ~/.claude/scripts/harness_lint.py`（rules の存在検査）が通ること
- MEMORY.md の before/after 行数と、抑止索引行のうち失効条件を運ぶ行の数（before: 1 / 12+）を報告
- 棚卸し結果の一覧（書き換え / 削除 / 格下げ / 恒久明記の別）をセッション末尾に提示し、削除分は要旨を残したことを確認
- akc-cycle / architect の追記は grill-me `:56-60` の複製箇所と矛盾しないか目視照合

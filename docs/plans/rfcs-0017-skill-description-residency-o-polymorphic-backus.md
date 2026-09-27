# RFC-0017 実施計画 — skill description の常駐削減 + skill 衛生の恒常配線

## Context

RFC-0017（accepted 2026-08-29）: skill listing の常駐コストを本数でなく description 側から削る。S1 実測で「意図的使用 0 だが read はある」skill が 15 本（約 6,600 字）あり、description だけ畳めば本数を減らさず常駐を約 7 倍削れる。

**セッション中の分岐（確定済み）**: 著者の危惧「description = 第 2 の rules 層（挙動汚染）」は外部知見照合の上で **RFC-0018 として分離起票済み**（`rfcs/0018-description-behavior-contamination.md`、draft、ファイル作成済み）。本セッションは**元の RFC-0017（字数軸）に基づいて**作業する — B 案の廃止や description 内指示文の監査は RFC-0018 の採否判断に委ね、ここではやらない。

RFC-0017 の実施にあたり著者が確定した方針 3 点:

1. 機構は **skill-health に入れる**（RFC 3 択の「既存 skill への追記、新規機構は建てない」の変種）
2. **skill-creator に規約追加**（description = trigger surface、disable-model-invocation の設計選択肢化）
3. **既存 skill 本文の肥大**も衛生として恒常検査に載せる — 新規作成時は skill-creator が守るが、既存は膨らむ一方。skill-health（列挙）+ skill-stocktake（判定）に配線

## 調査で確定した事実

- 対象 15 本すべて `disable-model-invocation` 未設定。到達経路の実測: **13 本は他 skill / rule からの明示参照あり → A**、`ai-native-preprint-submission` のみ逆参照ゼロ → B
- **A は frontmatter 1 行追加のみで description は温存できる**（`wait-what` の実例: `disable-model-invocation: true` だけで listing から消え、slash は `user-invocable` 併記なしで動く — skills/wait-what/SKILL.md:1-6）
- 窓不足 3 本（measurement-discipline / repair-discipline / loop-design-check)は III-a/III-b に**含まれていない**（監査 .notes/s1-skill-count-audit-2026-08-29.md:203-206 で隔離済み）→ RFC Next action 1 は確認のみで完了
- **review-to-lint は今回除外**（著者判断 2026-08-29）: 昨日 commit 34d1401 で description を意図的に延伸したばかり（387→433 字）。次回棚卸しで再判定
- RFC 本文の「RFC-0005 #7 に相乗り」は前提が古い（RFC-0009 として 2026-08-27 done 済み）
- harness_lint.py は description の存在のみ検査（意味的品質は stocktake 系の領分 — scripts/hooks/harness_lint.py:46-47）。今回 lint 変更は不要

## 変更内容

### 1. A: `disable-model-invocation: true` を 13 本の frontmatter に追加

description・本文は無改変（人間の slash メニューと grep 到達用に温存）。

- III-a（10 本）: `skill-health`, `paper-deposit`, `rules-distill`, `llm-as-judge`, `paper-ecosystem`, `python-patterns`, `agent-harness-construction`, `paper-writing`, `ai-regression-testing`, `e2e`
- III-b（3 本）: `wiki-harvest`, `prompt-perturb`, `session-theme-mining`

各 `skills/<name>/SKILL.md` の frontmatter 末尾（`origin:` の後）に 1 行追加。

注: `e2e` / `agent-harness-construction` は Retire 候補（候補群 I）でもあるが、A は退役判断を妨げない（RFC Status の「1 件ずつ別途確認」方針のまま）。

### 2. B: `ai-native-preprint-submission` の description を 1 行へ

現 476 字 → 1 行（`/ai-native-preprint-submission` の slash 名と一言。例:「AI-native 前提の preprint 投稿手順。/ai-native-preprint-submission で使う」程度）。本文は無改変。畳む前に現 description が何を許していたかを確認する（ADR-0058 の縮約事故の教訓）。

### 3. skill-health Phase 3（Utility 節）に列挙 2 項目を追記

`skills/skill-health/SKILL.md` L139-151 の Utility bullet に追加。**enumerate のみ、decide は著者 / skill-stocktake**（既存 boundary「良し悪しは判定しない」を守る）:

- **residency-fold 候補の列挙**: `usage_stats --days 90` の出力から deliberate 0 かつ read > 0 の skill を列挙し「description 撤去候補（RFC-0017）。判断軸 = 到達経路の有無（他 skill / rule の明示参照があれば A、listing しか入口が無ければ B）」として渡す。窓不足（`span_shorter_than_window` / 追加から日が浅い）は候補にしない
- **本文サイズの列挙**: `wc -l skills/*/SKILL.md` で目安 100 行（skill-creator §3）超を列挙。判定は skill-stocktake の Hygiene 問いへ

### 4. skill-stocktake Phase 2 Stage 1 に Hygiene 問いを追加

`skills/skill-stocktake/SKILL.md` の Stage 1 二値スクリーン質問群に 1 問追加:

> **Hygiene** — 本文が肥大していないか。トリビアルな禁止列挙・反復強調・手順の羅列は原理原則へ畳めるか。ただし grep 可能な検出語・自己執行力のある禁止・数値閾値は畳まない（ADR-0058 が「一律短縮」を却下した理由）

skill-creator §4 の草稿ゲートは stocktake Phase 2 を質問の正本として参照しているため、作成時ゲートにも自動伝播する（複製しない）。

### 5. skill-creator の規約追加（`skills/skill-creator/SKILL.md`）

- **§3 の禁止列挙行を一般化**: 現行「手順の羅列・反復強調・旧世代向けの禁止列挙は書かない」の「旧世代向けの」限定を外し、トリビアルな禁止列挙一般を原理原則へ落とす旨に。ADR-0058 の例外（検出語・自己執行・数値閾値は畳まない）を同じ行に 1 句で
- **§3 frontmatter 規約に追加**: description は trigger surface — 常駐は毎セッション課金される。自発発火を狙わない skill（slash / rule の命令形 / 他 skill の参照で届くもの）は `disable-model-invocation: true` を既定に検討（RFC-0017）。その場合 §1 の「発話例 3 つ」は不要（発話例は自発発火を狙う description のみの要求）— §1 側にも 1 句注記

### 6. RFC-0017 の記録更新（`rfcs/0017-skill-description-residency-optimization.md`）

- `state: done`（実施日付き）
- Status に追記: A/B 割当の確定（A 13 / B 1）、review-to-lint の除外理由、機構の決定（3 択 → 「新規機構は建てない + skill-health / skill-stocktake への追記」、Build-or-not の自答 1 行）、RFC-0005 #7 参照の陳腐化注記（RFC-0009 done）

### 7. RFC-0018 の起票残作業（ファイルは作成済み）

- `python3 ~/.claude/scripts/claims.py spawn RFC-0018 --origin idea`
- `rfcs/README.md` の index 表に `| [0018](0018-description-behavior-contamination.md) | description の挙動汚染（第 2 の rules 層化）の検査・撤去 |` を追加

## 実施手順

1. ~~claim RFC-0017~~ **済**（`claims.py claim RFC-0017` 実行済み）
2. 変更 1→2→3→4→5→6→7 の順に編集
3. 検証（下記）→ commit（RFC-0017 実施と RFC-0018 起票は別 commit に分ける）→ `claims.py release --outcome done`

## 検証

- `python3 scripts/hooks/harness_lint.py` — frontmatter YAML / 必須 field が全 skill で clean（B の 1 行 description に `: ` を入れない）
- `uv run --directory ~/.claude/skills/skill-health python -m scripts.scan_refs ~/.claude/skills --json` — dangling 0
- `uv run --project ~/.claude/skills/skill-stocktake python -m scripts.usage_stats --days 90` — 従来どおり動く（今回 script 変更なし）
- 新セッション（または `claude -p` 子）で skill listing に A の 13 本の名前が出ないこと、`/skill-health` 等の slash が生きていることを 1 本サンプル確認
- `git status` で意図したファイルのみ変更（skill 14 + skill-health + skill-stocktake + skill-creator + rfcs/0017 + rfcs/0018 + rfcs/README.md）

## スコープ外（記録のみ）

- 手段 C（paper cluster の sub-skill を references/ へ降格）— A で常駐は消えるため今回は見送り
- Retire 候補 3 件（e2e / thermo / agent-harness-construction）— RFC Status の方針どおり別途 1 件ずつ
- 分母（plugin / built-in の description 量）の測定 — RFC Next action 4 のとおり対外的に削減率を語るときだけ
- 公開 mirror への同期は skill: `harness-sync`（著者指示時に別途）

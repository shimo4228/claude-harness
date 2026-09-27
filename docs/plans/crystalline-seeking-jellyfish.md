# rules メタデータ（rationale / review-when）+ 構造的前提の決定論ゲート — 検証と計画

## Context

ADR-0018 の rightsize で判明した非対称: ADR が残っていた rule は棚卸し判定が数分、記録の無い rule は git 考古学が必要、参照先が消えた「幽霊設定」（git-workflow.md の includeCoAuthoredBy）は消えた時期すら特定不能だった。zenn-content セッションからの 2 段提案（① 各 rule に rationale / review-when メタデータ、② 構造的前提の決定論ゲート化）を検証した。

## 検証結果（証拠付き）

### 実測 1 — HTML コメントは常駐に載らない（決定的）

全 rules ファイルの 1 行目には `<!-- origin: ... -->` があるが、本セッションに注入された rules 本文には**含まれていない**（注入版 planning.md は `# Planning Standards` から始まる）。→ **コメント形式のメタデータは常駐 words コストゼロ**。提案の最大の懸念（14 ファイル × 2 行の常駐増が rightsize と矛盾）は解消。frontmatter は rules で未使用の上、検証不要（コメントで足りる）。

注意点: strip は substrate の挙動であり将来変わりうる。変わった場合の上限コストは 2 行 × 13 ファイル ≒ 150 words で、rules-stocktake の live 計測が検知する（ADR に記録）。また `rules/README.md` の「2,321 words（wc -w 実測）」は disk 基準なので +150 words 程度増える — 注入コストと計測値の乖離を README に 1 行注記する。

### 実測 2 — 既存機構との重複は無い、ただし統合先は既存資産

- **harness_lint.py**（PreToolUse hook で ~/.claude への commit 前に決定論発火）は既に「settings.json→hook パス実在 / markdown リンク切れ / See-skill 解決 / origin 存在」を検査。**rules 本文が inline code で参照する hook スクリプトパスは未検査**（リンクでないため対象外）— これが幽霊設定と同クラスのギャップ。
- **rules-stocktake** Stage 1 の staleness / absorption 質問は汎用 6 問。review-when はこれと重複せず、**ファイル固有の失効トリガーを書いた時点で事前宣言**する入力データになる（Stage 2 の「rule-specific atomic questions」を毎回 ad hoc 生成している箇所に事前 seed を与える形）。
- **results.json の `reason`** は「前回監査の判定理由」であり、「rule の存在根拠」ではない。役割は別。
- **config-gc / Scaffold Dissolution** とは衝突しない（前者は whole-config GC、後者は退役判断の原則で、review-when はその発火条件をファイル側に書く運用）。

### 実測 3 — ゲート化対象の棚卸し（現 rules 内の構造的前提）

| 参照 | 場所 | 判定 |
|---|---|---|
| `hooks/secret-scan-precommit.sh` / `hooks/bandit-precommit.sh` | security.md | **fail ゲート対象**（実在チェック） |
| `hooks/search-first-verdict-check.sh` | planning.md | **fail ゲート対象** |
| `permissions.allow` キー | hooks.md | 対象外（散文中のキー名検出は構造的でない。stocktake の領分） |
| `~/.codex/AGENTS.md` 等 3 パス | agents.md | 対象外（repo 外の環境資産。stocktake の Technical-references-current 質問で拾う） |
| 数値クレーム（README の words） | README.md | 対象外（stocktake が live 計測を既に義務化） |

→ fail ゲート化する価値があるのは **hook スクリプトパス 3 件のクラス**のみ。新規 lint 基盤は不要で、harness_lint.py に 1 関数足す規模。

### プロトタイプ（Prototype Before Scale）— 3 ファイルで下書き

```markdown
# planning.md
<!-- rationale: ADR-0018 — Chain 詳細を skill へ降格し、2 介入点モデルと Verify ゲートのみ常駐 -->
<!-- review-when: implementation-chain の自発発火率が実測で立った時 / harness が plan・verify を native 強制し始めた時 -->

# testing.md
<!-- rationale: ADR-0018 §5 — 一般論退役後に残した gotcha 集。MagicMock 罠は実障害由来 -->
<!-- review-when: TDD chain の起動が hook 化された時 / MagicMock の truthy 挙動が変わった時 -->

# contemplative-axioms.md（最難ケース）
<!-- rationale: ADR-0018 §7 — 行動変容でなく identity/values 層として著者判断で verbatim 常駐 -->
<!-- review-when: 著者の明示判断のみ（機械トリガーなし） -->
```

最難ケース（ADR 逸脱の著者判断・identity 層）でも素直に書けた。ADR の無い rule（task-tracking.md 等）も「feedback memory / 実障害」を一行で書ける。**全 13 ファイルで書ける見込み**。

### YAGNI チャレンジの結論

代替案「rules-stocktake の監査質問に 2 問足すだけ」は**不採用**。理由: 失効条件は**書いた時点でしか捕捉できない**（git-workflow の幽霊設定は、監査時にはもう「なぜ・いつから」が失われていた — これがまさに実証）。監査側の汎用質問では per-file トリガーを復元できない。一方 rationale は既存の本文中 ADR リンクと部分重複するが、ファイル単位に 1 行へ集約するコストはゼロ（strip される）で、監査の第一参照点になる。

## 推奨

- **提案 1: 修正採用** — frontmatter でなく **`<!-- rationale: -->` / `<!-- review-when: -->` コメント形式**（origin と同形式、常駐コストゼロ実測済み）。rules-stocktake への接続込み。
- **提案 2: 縮小採用** — 新設ゲートでなく **harness_lint.py の拡張 2 点**: (a) rules 本文 inline code 中の `hooks/*.sh` / `scripts/hooks/*.py` パス実在チェック、(b) rationale / review-when コメントの存在チェック（origin と同列の fail。メタデータ規約自体を「文書化された不変条件」としてゲートに落とす — patterns.md の原則の自己適用）。

## 実装ステップ（承認後）

1. **rules/common/*.md 13 ファイル**に `<!-- rationale: -->` `<!-- review-when: -->` を origin コメント直後に追記（README.md は index なので対象外）。上記プロトタイプの流儀で各ファイル固有に書く。
2. **`scripts/hooks/harness_lint.py`** に追加:
   - `lint_rule_asset_refs()` — rules/**/*.md の inline code から `hooks/[\w-]+\.sh` / `scripts/hooks/[\w-]+\.py` トークンを抽出し `~/.claude` 起点で実在確認（既存 `INLINE_CODE_RE` / `strip_code` を再利用。fence 内は除外）
   - `lint_origin_files()` を拡張 or 隣接関数で rationale / review-when コメント存在チェック（既存 `has_origin` と同パターン。対象: rules/common/*.md のみ — skills/learned は対象外）
   - **発火実証**: 違反を一時注入 → rc=3 赤化確認 → revert（documented-invariant-lint-gates レシピ）
3. **`skills/rules-stocktake/SKILL.md`** 更新:
   - Phase 1 チェックリストに「rationale / review-when コメント存在」を追加（harness_lint の結果を読み off）
   - Stage 2 に「review-when 宣言があればそれを最優先の refutation question として使う」を追記
   - Phase 4 に「監査で verdict が変わったら rationale / review-when コメントを同 diff で更新」を追記
4. **`rules/README.md`** — 計測注記 1 行（「メタデータコメントは注入されない。wc -w disk 値との乖離 ≒ +150 words」）。
5. **ADR-0021 起草**（adr-writer 経由）: 骨子は下記。
6. **harness-sync 注意** — 変更は origin: shimo4228 / ECC-customized の rules に及ぶため、公開 repo への同期 follow-up をユーザーに提示。

## ADR-0021 骨子（案）

- **Title**: rules メタデータ（rationale / review-when）と構造的前提の lint ゲート化
- **Context**: ADR-0018 棚卸しで判明した判定コスト非対称と幽霊設定（includeCoAuthoredBy）。失効条件は書いた時点でしか捕捉できない。
- **Decision**: (1) コメント形式メタデータ（常駐ゼロ実測: HTML コメントはセッション注入時に strip される）、(2) harness_lint 拡張 2 点、(3) rules-stocktake 接続。
- **Alternatives**: frontmatter 形式（rules の慣例外・検証不要で却下）/ 監査側質問のみ（書き込み時捕捉不能で却下）/ 全構造的前提の網羅ゲート（対象 3 件クラスのみで YAGNI、縮小）。
- **Consequences**: strip 挙動が substrate 依存（変化時の上限 +150 words、stocktake live 計測が検知）/ 新 rule 作成時に 2 行の記述義務（lint が強制）/ 公開 repo との diff 増。

## 検証方法

- `python3 scripts/hooks/harness_lint.py` が clean → 違反注入（rationale 行削除 / 偽 hook パス記入）で rc=3 → revert で clean
- 新セッションで rules 注入内容にコメントが載らないことを再確認（`/context` または注入本文の目視）
- rules-stocktake を `changed` モードで 1 回走らせ、review-when が Stage 2 質問として消費されることを確認

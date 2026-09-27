# readme-reviewer agent 新設 — readme-writer のレビューを他 writing 系エコシステム並みに充実させる

## Context

前タスクで planning.md に Writing Chain（ルーティング方式）を追加し、README 改稿は `writing` 種別 → readme-writer チェーンに乗るようになった。しかし readme-writer の Step 2「LLM holistic review」は **7 つの lens 名 + 各 1 行だけ**で、editor / essay-reviewer が持つ Review Criteria 詳細・pass 構成・Output Format・Overall Assessment 語彙が無い。専用レビュー agent も存在しない。SKILL.md 自身が「author-reviewer separation のため review は実装者と別 agent プロセスで回すのが望ましい（`editor` / `essay-reviewer` と同型）」と拡充を予告済み。

**ユーザー確定済みの方針**:
- レビュー基準の正本は新 agent `readme-reviewer` に移す。SKILL.md Step 2 は「agent 起動 + 一行サマリ」に縮む。執筆原則（フロア 5 要素 / two-sided rule / visual-first / length budget）は SKILL.md に残し、agent は defer で参照
- 今回はローカル（~/.claude/）のみ。単独公開 repo readme-writer への subagent 同梱は別タスク（集約 repo claude-harness は次回 /harness-sync で自動追随）

**追加方針（ユーザー確定済み）**: codex-review を writing チェーンに**条件付き C** で組み込む — 公開・deposit 前の高 stakes 文書（公開 repo の README、論文、公開記事）のみ。prompt-driven モードで writing 観点の指示を渡す（scoped モードは Codex 組み込みのコード向けレビュー指示が走るため prose 不適）。readme-reviewer 等の Claude 側レビュアーと並列起動。Verdict は codex-review 既存の構造化サマリ（CRITICAL/HIGH/…）で chain に接続済み。

## 変更対象（4 ファイル）

### 1. 新規: `agents/readme-reviewer.md`

editor.md / essay-reviewer.md の共通シェルに従う（骨格: frontmatter → Role → Review Criteria → Output Format → Review Process → When to Use vs 他 agent → Related → Your goal）。

**frontmatter**:
```yaml
name: readme-reviewer
description: "Strict README / repo top-page reviewer. Reviews READMEs for LLM-read floor recovery, lead clarity, scannability, length discipline, and visual effectiveness. Use PROACTIVELY after drafting or substantially revising a README, after readme_lint passes, before the human gate."
tools: ["Read", "Grep", "Glob"]
model: sonnet
origin: shimo4228
```
※ description は必ず全体をクォート（`: ` が YAML を破壊した前例あり — memory: reference_skill_creator_loop_gotchas）

**Role**: 辛口 README レビュアーのペルソナ。正本ポインタ引用ブロック — 執筆原則（最小 LLM-read フロア 5 要素 / two-sided rule / visual-first / length budget / anti-patterns）は `skills/readme-writer/SKILL.md` が正本、この agent はそれをレビュー基準として適用する。**Important:** ブロックで住み分け宣言（記事 → editor、エッセイ → essay-reviewer、llms.txt 等 AI-doc → llms-txt-writer の管轄）。

**Review Criteria**（現行 7 lens を番号付きサブセクション + checkbox に昇格。素材は SKILL.md に既在）:

1. **README-only recovery** — `This is the most important criterion.` と名指し宣言（essay-reviewer の Overload Detection と同じ置き方）。README のテキストだけから identity / 対象者 / 問題 / 差別化点 / DOI・引用（該当時）/ 3-6 core concepts / 例 1 つ / 次への link を復元できるか。欠落を具体的に列挙させる checkbox（「対象者が書かれていない」形式）。画像のみ・`<details>` 内・リンク先のみはフロア充足と認めない
2. **Lead の What / Who / Why** — 最初の画面（above-the-fold）で判断できるか
3. **人間フック / 価値提案** — 抽象語でなく具体で価値が言えているか
4. **物語 / scannability** — 段落・見出し・list・Mermaid が人間に追えるか。散文の壁の検出
5. **短さの検証（逆方向チェック）** — フロア以外が relocate されているか。Mermaid / `<details>` / フロア温存による**偽装 llms-full.txt 肥大**の検出
6. **Visual の妥当性** — 図は Mermaid か（raster ならテキスト等価があるか）、全図に一文のテキスト等価（hard rule）、badge は 2-4 個の高信号か（vanity 判定）
7. **Lint warning の意味判断（引き継ぎ）** — readme_lint.py の warning 5 項目に対する意味判断はこの agent の担当: badge_budget（数）→ vanity か / raster_diagram_hint（検出）→ Mermaid 化すべきか / details_floor_leak（トークン）→ 真にフロアか / identity_lead（存在）→ lead が Who/What/Why を言えているか。**構造チェック 9 項目（error 4 + warning 5）の再実装は禁止** — lint が code-owned

fact 一致（llms.txt / graph.jsonld との矛盾）は現行どおり `context-sync` に委譲 — agent は気づいたら flag するだけで検証はしない。

**スコア規律**: 数値スコア（`Lead: 6/10`）は出さない — 所見は「次の行動を変える」具体指摘 + 具体 diff（y/n 承認できる粒度）で。Overall Assessment（verdict）は chain の早期停止判断が消費するため出す（judge + enforce として正当、when-code-when-llm 準拠）。

**Output Format**: editor / essay-reviewer と**完全同一シェル** — `📊 Review Summary` + `Overall Assessment: [EXCELLENT / GOOD / NEEDS REVISION / MAJOR ISSUES]` + 🔴 CRITICAL / 🟡 MEDIUM / 🟢 MINOR / 💡 Suggestions + `✅ Final Recommendation`。同語彙採用で planning.md の Verdict マッピング表がそのまま機能する。

**Review Process**（4 pass、editor 同型）:
1. First pass — **blind read**: repo を見ずに README テキストだけ読み、README-only recovery を判定（フロア欠落列挙）
2. Second pass — repo と照合: canonical facts の正確性、リンク先の存在、フロア要素の実体整合
3. Third pass — 構造と visual: scannability、Mermaid / badge / `<details>` の妥当性、偽装 llms-full 検出
4. Fourth pass — lint warnings の意味判断 + 全所見を diff 粒度に整形

**When to Use This Agent vs. Editor / Essay-Reviewer**: 振り分け表（README / repo 入口 → this、tech 記事 → editor、idea 記事 → essay-reviewer）。

**Related**: readme-writer skill（執筆原則の正本）、editor / essay-reviewer（姉妹 agent）、context-sync（fact 一致）。

行数感: editor (259 行) / essay-reviewer (201 行) と同程度の 200 行前後。

### 2. 更新: `skills/readme-writer/SKILL.md`

- **Step 2（L153-165）を書き換え**: 7 lens の詳細を削り、「`readme-reviewer` agent を起動する（author-reviewer separation）。レビュー基準の正本は agent 定義」+ lens の一行サマリ（何を見るかの見出しだけ）+ スコア無し原則の要旨は 1-2 文残してポインタ化
- **Step 2 に cross-model の条件付き並列を追記**: 公開 repo の README なら `codex-review`（prompt-driven、writing 観点の指示文例を 1 つ記載）を readme-reviewer と並列起動してよい
- **Workflow 見出しの整合**: 「Code filter → LLM review → 人間 gate」の LLM review を agent 起動として書く
- **Related セクション**に readme-reviewer agent・codex-review を追加
- frontmatter の origin は `shimo4228` のまま（自作なので -customized 不要）

### 3. 更新: `rules/common/planning.md`（Writing Chain セクション）

- **Verdict マッピング表（2 行）**: `（editor / essay-reviewer）` → `（editor / essay-reviewer / readme-reviewer）` に追記
- **Cross-Model Review の条件付き発火を Writing Chain に追加**（糊セクションの一項として）:
  - `writing` × Cross-Model Review (codex-review): 公開・deposit 前の高 stakes 文書（公開 repo README / 論文 / 公開記事）のみ Y。**prompt-driven モード必須**（scoped モードはコード向け組み込み指示のため prose 不適）。Claude 側レビュアーと並列起動。private ドラフト・下書き段階は `-`

### 4. 更新: `skills/codex-review/SKILL.md`（When to Use に 1 項目）

- 「公開・deposit 前の高 stakes 文書（README / 論文 / 記事）の prose diff にも使える — その場合は prompt-driven モードで writing 観点の指示を渡す（scoped モードのコード向け組み込み指示を避ける）」を When to Use に追記。origin は `shimo4228` なので -customized 不要

## 実装時の注意

- **重複させない境界**: 執筆原則の全文（フロア 5 要素の詳細・視覚形式選択表・two-sided rule の採用/禁止リスト）は SKILL.md 正本のまま。agent 側は checkbox 化した「レビューとしての問い」に変換して持ち、原則本文はポインタで defer（editor が AI-slop 正本を writing-ecosystem に defer するのと同型）
- **Portability**: agent 本文に個人 repo URL・個人パスを入れない（rules/common/skills.md の Portability 原則）
- writing-ecosystem SKILL.md は README を scope 外としているので**触らない**（住み分け維持）
- akc-cycle.md L30 の `See skills: readme-writer` はスコア無し原則のポインタなので変更不要
- 変更は global 版（~/.claude/）のみ

## Verification

1. 新 agent の YAML frontmatter を検証（`python3 -c "import yaml; ..."` 等で parse 確認 — description の `: ` 破壊の前例対策）
2. editor.md / essay-reviewer.md と並べてセクション骨格が同型か確認（Role / Review Criteria / Output Format / Review Process / Related / Your goal）
3. Verdict 語彙が planning.md マッピング表と一致するか grep（`MAJOR ISSUES` / `NEEDS REVISION`）
4. SKILL.md Step 2 → agent → Output Format → 人間 gate の流れをシナリオ素振り（「README を読みやすく書き直して」）。lint がカバーする 9 項目を agent が再実装していないことを突き合わせ
5. コミットはユーザー確認後。scope: `agents/readme-reviewer.md` + `skills/readme-writer/SKILL.md` + `rules/common/planning.md` + `skills/codex-review/SKILL.md` の 4 ファイル（他の未コミット変更と混ぜない）

## スコープ外（今回やらない）

- 単独公開 repo readme-writer への subagent 同梱（harness-sync packaging 規約に従う別タスク。集約 repo claude-harness は次回 /harness-sync で自動追随）
- writing-ecosystem への README 統合（住み分け維持）
- fact 一致検証の agent 内実装（context-sync 委譲のまま）

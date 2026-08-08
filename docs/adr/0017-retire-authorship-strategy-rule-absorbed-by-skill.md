# ADR-0017: authorship-strategy.md ルール退役 — skill が凝縮重複を吸収

## Status

accepted

## Date

2026-07-19

## Context

`rules/common/authorship-strategy.md`（41 行、常時ロード rule）が、著者自身の DOI-registered idea-rescue 研究 repo での authorship strategy 判断軸を always-loaded で提示していた。この rule 自身が冒頭で「要点 inline / 詳細は skill、本 rule は always-loaded trigger + 要点」と自己規定し、末尾に `See skill: authorship-strategy` を持つ「要点 inline + 詳細 skill」構造だった。

「常時注入が重すぎる」という問題提起を受けて内容を点検した結果、rule の 5 セクション（Trigger 判定 / 適用しない / Framework 要点 / 禁止事項 / Persona）は**すべて skill `authorship-strategy`（281 行）側に、より詳しい形で既に存在する上位集合**であることが確定した:

- Trigger 判定 → skill `## Trigger 条件 > ### 適用される`（3 条件が 1:1 一致）
- 適用しない → skill `### 適用されない`（5 項目一致、収益注記は skill 側が精密）
- Framework 要点 → skill の 4 層 Framework + Stance セクション（各層とも skill 側が格段に厚い）
- 禁止事項（特に community 統治 platform への self-created 登録 = Wikidata 禁止） → skill `## 禁止事項`（ADR-0021 明記、109 item 一括削除の実例・変種同罪まで内包）
- Persona / stance → skill `## Stance`（最上位セクション）

rule 固有で skill に欠けている実質内容は無く、rule は純粋な凝縮重複だった。唯一の固有価値は「always-loaded トリガー」機構のみ。

この rule は毎セッション（無関係な作業を含む）決定論ロードされるが、実際に適用されるのは著者自身の ~6 repo に限られる。それらの repo は各々 CLAUDE.md / project memory / ADR-0021 に guardrail（禁止事項の grounding）を別途持つ。akc-cycle.md `## Scaffold Dissolution`（skill が capability を吸収したら rule を retire、why は ADR に記録）と、rules-stocktake の Dissolve verdict にそのまま該当する。rule retirement を ADR 化した先例は ADR-0004 / 0005 / 0011 / 0014。

## Decision

1. **`rules/common/authorship-strategy.md` を削除する**（git 管理下のため hard-delete、履歴で復元可能）。authorship strategy 判断の正本を skill `authorship-strategy` に一本化する。

2. **発火はトリガー機構に委ねる**。skill の description は「著者自身の DOI-registered idea-rescue repo 群で適用」というトリガー意味論を保持し、常時カタログに存在する。`user-invocable: true` により `/authorship-strategy` slash でも到達できる。加えて各対象 repo の CLAUDE.md / memory / ADR-0021 が禁止事項の repo-level guardrail を持つ。

3. **依存参照を repoint する**。rules/README.md のツリーから 1 行削除。rules-stocktake skill が Demote verdict の模範例に引用していた「the authorship-strategy.md pointer pattern」を、同構造で生き残る「the task-tracking.md pointer pattern」に付け替え。learned note `platform-governance-aggregate-pattern.md` の関連 rule 参照を `skill: authorship-strategy` に付け替え。

4. **常時ロードの禁止事項発火は失われる**。安全上重要な Wikidata self-registration 禁止が always-loaded で確実発火する機構は撤去され、skill の確率発火 + repo-level guardrail に委ねられる。このトレードオフを著者が明示的に受容した。

## Alternatives Considered

### (a) 薄いトリガースタブに縮小する

rule を 41 行 → 6-8 行（トリガー条件 1 行 + 禁止事項の要 1 行 + `See skill:`）に痩せ、常時ロードの確実発火を維持する。task-tracking.md と同じ姉妹パターン。しかし「内容を skill に一本化」と「禁止事項を常時ロード」は原理的に両立せず、スタブに禁止事項を残せば重複が残る。純粋な一本化を優先して**却下**。

### (b) project-level rule に移す

対象 ~6 repo それぞれの `.claude/` に rule を置き、無関係セッションへの注入を止める。だが 6 repo へのコピーは drift vector であり、single source of truth を各所に分散させる。skill の description が既にトリガーを担うため冗長。**却下**。

### (c) `_archived/` へ soft-delete

可逆性ゲートの慣例。だが git 管理下で履歴から完全復元でき、二重の安全網で冗長（ADR-0014 と同判断）。hard-delete を選択。

## Consequences

### Positive

- 毎セッションの常時注入コストが削減され、authorship strategy 判断の発見経路が skill 単一に集約される。
- rule と skill の凝縮重複が解消し、drift（rule だけ更新されず staler 化）リスクが消える。
- rules-stocktake の模範例が生きたファイル（task-tracking.md）を指すようになり、ドキュメント整合が回復する。

### Negative

- 禁止事項（特に Wikidata self-registration 禁止）を毎セッション決定論ロードする安全機構が無くなる。→ ただし対象 repo は各々 CLAUDE.md / memory / ADR-0021 に guardrail を持ち、skill description は常時カタログに在る。無関係セッションで禁止事項が問題になる場面は構造上ほぼ生じないと判断。
- always-loaded rule によるトリガーが確率発火（skill description ベース）に変わる。→ skill description がトリガー条件を明示保持し、slash 発火も可能なため、実務上の到達性は維持される。

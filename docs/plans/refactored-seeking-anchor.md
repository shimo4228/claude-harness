# Plan: authorship-strategy rule を skill に一本化（rule 完全削除）

## Context

`~/.claude/rules/common/authorship-strategy.md`（41行、常時ロード rule）が「常時注入が重すぎる」。
調査の結果、この rule の 5 セクション（Trigger 判定 / 適用しない / Framework 要点 / 禁止事項 / Persona）は
**すべて skill `authorship-strategy`（281行）側に、より詳しい形で既に存在する上位集合**であることが確定した。
rule 固有の実質内容はゼロ（純粋な凝縮重複）で、唯一の固有価値は「always-loaded トリガー」機構のみ。

著者判断: **rule を完全削除**し、skill を唯一の正本とする（純粋な一本化）。
発火は skill の description（常時カタログに存在）+ `/authorship-strategy` slash に委ねる。
安全上重要な禁止事項（Wikidata self-registration 禁止）は skill 本文 + 各 repo の CLAUDE.md / memory / ADR-0021 が別途 grounding を持つため、常時ロード撤去の緩衝になる。

種別: `chore`（config/docs リファクタ）。build/test 非該当。Verify = 参照整合 + dangling ref grep + git status。
適用先: **global `~/.claude/` のみ**（repo コピーは触らない）。`~/.claude` は git 管理下 → `git rm` を使う。

## 設計根拠

- **skill が完全上位集合**: 内容の一本化に情報損失がない（migration 不要）。
- **skill description が既にトリガー意味論を保持**: 「著者自身の DOI-registered idea-rescue repo 群で適用」を description が明示。`user-invocable: true` で slash 発火も可能。
- **先例に合致**: akc-cycle.md `## Scaffold Dissolution` が「skill が capability を吸収したら rule を retire、why は ADR に記録」と規定。rules-stocktake SKILL.md L125（Dissolve verdict）も同旨。ADR-0011 / ADR-0014 が rule retirement を ADR 化した先例。

## 変更ファイル

### 1. rule 削除
- `git rm ~/.claude/rules/common/authorship-strategy.md`

### 2. 参照の repoint（要対応 3 箇所）
- **`rules/README.md` L10** — 構造ツリーから `authorship-strategy.md` の行を削除。
- **`skills/rules-stocktake/SKILL.md` L124** — Demote verdict の模範例引用
  「the authorship-strategy.md pointer pattern」を、同じ「要点 inline + See skill」構造で**生き残る**姉妹 rule
  「the task-tracking.md pointer pattern」に repoint（削除するファイルを模範例に残さない）。
- **`skills/learned/platform-governance-aggregate-pattern.md` L59–61** — 関連 rule 列挙中の
  `common/authorship-strategy.md`（idea-rescue repo 文脈での禁止事項）を `skill: authorship-strategy` に repoint。

### 3. 放置（監査スナップショット・履歴ログ、書き換えない）
- `gc_log.md` L80 / `skills/rules-stocktake/results.json` L89–90 — 過去時点の記録なので現状のまま。

### 4. ADR 記録（推奨・分離可）
- `~/.claude/docs/adr/0017-retire-authorship-strategy-rule-absorbed-by-skill.md` を新規作成。
  Scaffold Dissolution / rules-stocktake Dissolve verdict の「why は ADR に」規律 + ADR-0011/0014 の先例に沿う。
  内容: rule は skill の凝縮重複だった / 常時注入コスト削減 / トリガーは skill description + slash + repo-level guardrail に委譲 / 禁止事項の常時ロード撤去のトレードオフを著者が受容。
  adr-writer agent で 6 セクション（Status/Date/Context/Decision/Alternatives/Consequences）を render。
  ※ 著者が「ADR は不要」と判断すれば skip 可。

## Verify

1. `grep -rn "authorship-strategy.md" ~/.claude --include="*.md" --include="*.json"` で、
   残存参照が gc_log / results.json（意図的放置）のみであることを確認（dangling ref ゼロ）。
2. `grep -rn "common/authorship-strategy" ~/.claude` で rule パス参照が消えたことを確認。
3. skill `authorship-strategy` が単体で完結していることを再確認（description + 本文で trigger/禁止事項/framework 全カバー）。
4. `git -C ~/.claude status` で意図したファイルのみ変更（削除1 + 編集3 [+ADR新規1]）であることを確認。
5. ADR を作った場合、`docs/adr/README.md` index に 0017 行を追加。

## Commit（Verify 全 PASS 後・著者確認点）

`git -C ~/.claude` で 1 コミット。message 案:
`refactor(rules): retire authorship-strategy rule, consolidate into skill`
（ADR を含む場合は本文で ADR-0017 を参照）。

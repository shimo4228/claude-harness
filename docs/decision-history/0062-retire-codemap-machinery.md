# ADR-0062: codemap 機構（update-codemaps / codemap-writer / context-sync Phase 0）の退役 — file-level 構造は保存せず LSP で導出する

## Status

accepted — supersedes ADR-0060、ADR-0010 の Phase 0 と codemap-writer 部分を無効化

## Date

2026-09-05

## Context

harness は file-level のコード構造文書 `docs/CODEMAPS/` を全 repo に配っていた: `update-codemaps`
skill（生成の orchestration）、`codemap-writer` agent（repo scan → token-lean summary の描画）、
`context-sync` Phase 0（3 signal で stale を検知し再生成へ cascade）、`release-doi` Phase 2
（release 前の再生成）、`codemap_evidence.py`（[ADR-0060](./0060-codemap-evidence-script-and-freshness-gate-mechanization.md)、
2026-09-01 に freshness gate を script 化）。想定読者は「次セッションの LLM」だった。

contemplative-agent（以下 CA）で 2026-09-05 に前提を実測した（正本は
[CA ADR-0102](https://github.com/shimo4228/contemplative-agent/blob/main/docs/adr/0102-retire-codemaps.md)）:

- codemap 6 枚 205 KB、architecture.md 単体 ~30k token。2026-06-01 以降 src 197 commit に対し
  codemap 159 commit — ソース commit 1 件あたり同期 commit 約 1 件
- 著者は読まない。LLM セッションが読んだ証拠も無い。CLAUDE.md の 12 行と harness 側の参照
  （`grep -rn CODEMAPS rules/common/*.md skills/{context-sync,implementation-chain,update-codemaps}/SKILL.md`
  で 44 行、2026-09-05。skill / agent 全体では 16 ファイル約 120 行）は読者を*誘導*していたが、
  セッションは実際には language server・grep・docstring が引く ADR に向かう
- Claude Code の LSP tool（pyright）が `workspaceSymbol` / `findReferences` / `incomingCalls` を
  その repo で実走で答えた。import 構造は grimp / import-linter が既に持つ
- 外部ツール調査: codemap の内容のうち段構成と incident 理由以外はコードから都度導出可能。
  code-graph MCP 群（2026 年製、常駐 index）は codemap の代替として不採用。Archify（JSON IR から
  図を生成・検証する作図 skill、著者が別セッションで試用中 — `skills/archify/` は本 ADR 時点で
  untracked）は**コードから構造を導出するものではない**ので代替候補にならない。作図 skill としての
  採否は本 ADR の対象外
- architect（独立 build-or-not）が Data Flow 節を実読: 大半がコードの再述、日付つき括弧は本文に
  inline された changelog。縮退案は「hook が残る限り 1 ヶ月で再肥大する同じ罠」と判定

architect の harness 側への勧告は **per-repo opt-out**（1 repo の読みは 1 回の測定。global は
2 repo 目の同結論で）。著者はこれを聞いた上で「機構として再生産されないように」と global 撤去を
指示した（2026-09-05）。本 ADR はその判断の記録で、勧告との差分を明示する。

これは rule `akc-cycle.md` の Scaffold Dissolution **Downward**（substrate が capability を native
に持った）の一例: codemap は読者 LLM が symbol index を持たなかった世代の足場で、LSP tool が
その構造機能を吸収した。残った散文部分は git log の inline 写しで、情報差分は負（保守コストだけ
が残る）。AKC 側の記録は `agent-knowledge-cycle/docs/scaffold-dissolution.md` の 2026-09-05 節。

## Decision

1. **削除**: `skills/update-codemaps/`（SKILL.md、`scripts/codemap_evidence.py`、tests、pyproject、
   uv.lock）、`agents/codemap-writer.md`。公開 copy（claude-harness）は `harness-sync` で消す。
2. **context-sync から Phase 0（Codemap Freshness Pre-check）を削除**し、`context_checks.py` の
   codemap 依存読み（`_codemaps_prose` / `concepts_not_in_codemaps_prose` / `llms_txt.codemaps_dates`）
   と CODEMAPS 例外を落とす。context-sync の役割表は「file-level は保存しない」に書き換える。
3. **release-doi から Phase 2 の再生成と Phase 4 の `git add docs/CODEMAPS/*.md` を削除。**
4. **`implementation-chain` の Doc Sync 行**: 機構・段構成の変更 → 所有 ADR の追補 + それを走らせる
   script の冒頭コメント。ADR 新設・廃止 → knowledge graph。CODEMAPS は行から消える。
5. **`jsonld-knowledge-graph` の役割境界**: concept 層 = graph.jsonld、file 層は問いごとに LSP / grimp
   で導出し保存しない。graph にコードノードは持たない。
6. **file-level 構造文書は harness のどの skill も生成しない。** 構造の問いは LSP tool、理由は
   ADR、段構成は script header — これを context-sync / grill-me 等の「repo を読む」手順の既定にする。
7. **harness 全体の CODEMAPS 参照を掃く**: grill-me / repo-asset-stocktake / agent-stocktake /
   readme-writer / llms-txt-writer / harness-sync の 1 行言及、`skill-comply/results/implementation-chain.spec.yaml`
   の doc-sync 文面、release-doi の phase 連番（5 → 4）とそれを指す hf-sync の 3 箇所。合計 20 ファイル。
8. **他 repo の既存 `docs/CODEMAPS/` は本 ADR では消さない。** producer が消えるので以後更新されない
   静的文書になる。各 repo の次回接触時に削除し、導線を CA ADR-0102 の定型（構造は LSP / grimp、
   理由は ADR、段構成は script header）へ書き換える。

## Review-when

- LSP tool が主要言語で使えない repo が出た（language server 未導入、または tool の撤去）—
  その repo だけ導出層の源が無い。codemap の復活でなく language server の導入で解く
- 段構成の読み違いによる修理事故が 2 件 — 置き場（script header / ADR）が見つかっていない印。
  直し方は置き場の明示で、codemap ではない
- 残り 9 repo の codemap 削除が完了した — Consequences の一覧を閉じ、本 ADR は完了扱い
- 「1 repo の読みで global を変えた」判断の transfer 証拠: 残り 9 repo の次回接触時に、codemap 無しで
  構造問いが解けたかをその repo の削除 commit message に 1 行残す（観測者は当該セッション、窓は
  9 repo の接触が終わるまで、暦の期限は置かない）。2 repo で成立すれば architect 勧告との差分は解消。
  **解けなかった repo が出た場合**は codemap も opt-out も戻さず、その repo に language server を
  入れる（LSP の源を作る）か段構成を script header に書く — 失敗の解は導出層の補強で、保存層の復活ではない

## Alternatives Considered

**per-repo opt-out（architect 勧告）。** context-sync Signal C に「repo が ADR 付きで退役を宣言
していれば skip」を足し、producer は残す。却下: producer が残る限り context-sync は他 9 repo で
再生成を要求し続け、opt-out 宣言を持たない新 repo では codemap がまた生える。1 repo の読みで
global を変える弱さは認め、上の Review-when に transfer 条件として残す。

**update-codemaps を残し context-sync の cascade だけ切る。** 却下: skill が存在する限り
`/update-codemaps` は呼べ、実行すれば同じ 30k token の文書が再生される。存在自体が再生産経路。

**codemap を「導出型」に置き換える**（Aider 型 tree-sitter repo-map を skill 化）。保留: LSP tool
と Glob で cold start の問いに足りる間は不要。cold start の失敗が観測されたら search-first から。

**ADR-0060 の script（4 日前）を活かして gate だけ残す。** 却下: gate は生成物の検収器で、生成物
が無ければ検収対象も無い。sunk cost は判断の根拠にしない。

## Consequences

- context-sync は Phase 1 から始まる。Phase 0 が担っていた「stale codemap に対して overlap 検出を
  走らせる」事故は、比較対象の codemap が無くなることで消える
- `implementation-chain` の Doc Sync 対象が 1 つ減る。機構変更の doc は所有 ADR と script header
- ADR-0060 は 4 日で superseded。review-to-lint の適用自体は正しかったが、対象機構の存在価値を先に
  問わなかった — Build-or-not 4 問（planning.md）は「既存機構の gate 化」にも適用する
- codemap を持つ repo 9 つに静的文書が残る（2026-09-05 時点）: aeon-shop / aeon-shop-t004 /
  agent-attribution-practice / agent-knowledge-cycle / authorship-strategy / contemplative-agent-rules /
  doctrine-corpus / gai-passport-ios / zenn-content。各 repo の次回接触時に削除。削除するまで
  その repo の CLAUDE.md が codemap を正本と呼んでいれば、読者は古い機構記述を掴みうる
- harness の skill 数と agent 数が 1 つずつ減る。`skill-stocktake` / `agent-stocktake` の results.json
  は次回実行で追随。`rfcs/0005-review-to-lint-rollout-ledger.md` の codemap-writer 行（ADR-0060 で実施済）は
  歴史記録としてそのまま — 対象 script は本 ADR で削除
- 復旧コストは git 履歴からの掘り起こし（`skills/update-codemaps/` は tests / uv.lock ごと削除、最終版は
  本 ADR 直前の commit）。Review-when が発火しても復元は既定でなく、まず導出層の補強を試す
- 公開 repo claude-harness と単独 skill repo 群への反映は `harness-sync`

## References

- [CA ADR-0102](https://github.com/shimo4228/contemplative-agent/blob/main/docs/adr/0102-retire-codemaps.md) — 実測と repo 側の削除
- [ADR-0060](./0060-codemap-evidence-script-and-freshness-gate-mechanization.md) — superseded
- [ADR-0010](./0010-context-sync-cascade-and-writer-agents.md) — Phase 0 と codemap-writer の導入（本 ADR で該当部分が失効）
- [ADR-0016](./0016-writer-agents-render-not-decide.md) — codemap-writer を「observation → 委譲可」と分類（agent 自体が退役）
- rule `rules/common/akc-cycle.md` Scaffold Dissolution — Downward
- agent-knowledge-cycle `docs/scaffold-dissolution.md` 2026-09-05 節

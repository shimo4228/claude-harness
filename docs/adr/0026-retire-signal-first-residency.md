# ADR-0026: Signal-first 常駐節の退役（消費 skill へのインライン内在化完了 + 質問抑制の衝突コスト）

## Status

accepted

## Date

2026-07-31

## Context

`rules/common/akc-cycle.md`（local edition）は [ADR-0018](./0018-rules-rightsize-for-claude5.md)
の rightsize 時に Signal-first 節（「広く探し、狭く取り込む」+ Output discipline「行動を
変えるものだけ出力する」）を全文保持で常駐させた。直近の rules-stocktake（2026-07-26）も
「absorber なし」で Keep 判定しており、この時点までは節の存在に問題は見つかっていなかった。

その後、2 つの状況変化があった。

第一に、**インライン内在化が完了した**。原則は消費点にすべて内在化済みである — `search-first`
Step 2（数値スコア・grade 禁止、evidence-backed verdict）、`wiki-harvest` Step 3（signal
フィルタ）、`readme-writer` のレビュー出力規約（「Lead: 6/10 は行動を変えない」）、
`readme-clarity-reviewer` agent（"Never emit numeric scores"）。常駐で原則を保持し続ける
必要性が薄れ、常駐は冗長になった。

第二に、**能動的な害の証拠**が出た。常駐の抑制圧力（signal-first の output discipline +
planning.md の 2 介入点モデル + system prompt の autonomous 既定）が、要件明確化フェーズの
質問行動（grill-me skill）を抑制している。grill-me は chain に配線されておらず pull-only
（自発トリガー実質上限 ≒ 40% の実測知見により自発発火は期待できない）。ユーザーはハーネス
なし環境（職場の Copilot）で grill-me 相当を実行した際、遥かに多くの質問が出たことを観察
した。質問数の差の一部は docs-first 自己回答（ADR / glossary を読んで質問を消化する正当な
差）で説明されるが、「Stop when sharp」の vibe 判定が常駐圧力下で早期収束する分は実害と
判断した。

第三に、モデル世代（Claude 5 世代）は signal-first 相当の確認・取捨選択を既定で行えると
判断した。これは `akc-cycle.md` 自身の Scaffold Dissolution が定義する「モデル世代交代 =
downward トリガー」に該当する。

## Decision

1. `rules/common/akc-cycle.md` から Signal-first 節（Output discipline 小節を含む）を
   削除し、常駐を退役する。原則の正本は消費 skill 側（`search-first` Step 2 /
   `wiki-harvest` Step 3 ほか）に移す。
2. 参照の後始末を行う: `rules/README.md` のツリー行と履歴行、`wiki-harvest` SKILL.md
   Step 3 の正本ポインタ（自己完結化）、`harness-sync` SKILL.md の signal-first-research
   行 2 箇所（原則正本ポインタの差し替え）。
3. `grill-me` SKILL.md に対項目を加える。(a) Interview mode 節 — 明示起動中は質問が
   デリバラブルであり、2 介入点モデル・autonomous 既定・output discipline を適用除外する
   宣言、(b) Rule 7 を「Stop when sharp（vibe 判定）」から 6 次元カバレッジ判定
   （success criteria / scope & non-goals / 不可逆判断 / failure modes / users /
   dependencies）へ置換する。
4. AKC repo の配布版（自己完結版）は別正本であり触らない。公開 akc-cycle repo へは次回
   harness-sync で伝播する。

## Alternatives Considered

### 常駐を維持（前回 stocktake の Keep 判定を踏襲）

前回 stocktake 判定の軸は「冗長かどうか（absorber の有無）」であり「能動的に害するか」
ではない。抑制の害の証拠が出た時点で Keep の前提が崩れた。**却下**。

### grill-me 側の override 追記のみで rule は残す

世代的に不要な常駐が残り続け、override と常駐の恒常的な衝突摩擦になる。Scaffold
Dissolution の設計上、内在化完了時の正規パスは退役である。**却下**。

### インライン内在化コピー（search-first / readme-writer 等）も含めて原則を全面削除

インラインコピーは原則が実際に行動を変える消費点にあり、常駐コストを持たない。消すと
review 出力への score 混入が再発しうる。**却下**。

### grill-me の description 改善で自発発火に期待（明示起動に頼らない）

自発トリガー実質上限 ≒ 40% の実測により description 改善では突破できない。明示コマンド
起動（user-invocable）を正とする。**却下**。

## Consequences

### Positive

- /grill-me 明示起動時の要件質問が常駐圧力と衝突しなくなる。
- 常駐予算が軽くなる。
- `wiki-harvest` が自己完結し、外部ポインタ切れリスクが消える。

### Negative

- インラインコピーの無い文脈では「score を出さない」常駐リマインダーが消える — review
  skill 外での score 混入の再発は rules-stocktake / skill-comply で監視する。
- 公開 akc-cycle repo は次回 harness-sync まで drift する。
- 凍結 repo signal-first-research の「原則の正本」ポインタは消費 skill 名指しに変更する。

### Neutral / Follow-ups

- 効果の実測は、曖昧な plan 1 本への /grill-me 実行で行う。判定指標は質問数ではなく
  「インタビュー終了時に未解決のまま残った decision point の数」とする。

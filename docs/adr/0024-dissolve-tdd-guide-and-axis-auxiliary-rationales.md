# ADR-0024: tdd-guide agent の Dissolve と fresh/rich 軸の補助則 2 件 — 軸の全 corpus 適用

## Status

accepted

## Date

2026-07-27

## Context

[ADR-0023](./0023-dissolve-planner-narrow-architect-to-essence-evaluation.md) で採用した
fresh/rich context 軸を、ユーザーの提案（「この観点で他のエージェントも整理できるか」）を
受けて残り 20 agent の corpus 全体に適用した。結果は 3 グループに分かれた。

- **(1) fresh context が役割の本体である 13 件**（review 系・checker 系・純化済み
  architect）は軸がそのまま正当化する。clarity-reviewer が最純粋例で、「companion repo も
  著者の前作も編集過程も知らない読者として読む」という役割定義そのものが fresh context を
  要件にしている。
- **(2) 6 件は軸の 2 極（fresh / rich）だけでは説明できず**、暗黙だった 2 つの補助則で
  正当化されることが分かった。
  - **frozen-input render 契約** — 呼び出し前に self-contained なパケットを凍結するので
    会話 context が設計上不要になる。adr-writer は
    [ADR-0016](./0016-writer-agents-render-not-decide.md) の render-not-decide 契約、
    prompt-writer も同型。入力が会話でなく repo / レジストリである codemap-writer /
    scout もこの群に属する。
  - **bulk context isolation** — 大量のファイル読み・出力をメイン context から隔離すること
    自体が価値。e2e-runner / refactor-cleaner が該当する。
- **(3) tdd-guide 1 件だけが planner と同型のミスマッチとして残った**。Write / Edit / Bash
  を持つ実装 agent であり、テストと最小実装を書く作業は会話中の仕様・制約という rich
  context が資産になる生成作業である。absorber は具体名で指せる — skill `tdd`
  （職務記述がほぼ同一でメインループに指示として載る）+ `rules/common/testing.md`
  （規約は常駐済み）+ メインループ自身。agent-stocktake に今回追加した Stage 2 の
  カウンター質問も通過する: tdd-guide に固有の能力はなく、「その能力を使う場所」は
  仕様を持つメインループである。

planner と tdd-guide が同型なのは偶然ではない。どちらも plan mode も skill 機構もなかった
時期の ECC の「工程を agent 化する」設計であり、世代交代後の再配置は「工程は skill
（指示）、独立審査だけ agent（別 context）」という構図に収束する。

## Decision

1. **tdd-guide agent を Dissolve する**。`agents/tdd-guide.md` を削除する（git 履歴で
   復元可能）。参照 5 箇所を書き換える。
   - implementation-chain の Chain Matrix「TDD (tdd-guide)」→
     「TDD（メインループ、skill: tdd）」
   - skill `tdd` の冒頭を「メインループで実行する。仕様は会話にあるのでテスト・実装の
     執筆を sub-agent へ委譲しない」に変更し、「実行 agent」ポインタ行を削除する
   - 同 skill の Troubleshooting 手順 step 1「agent tdd-guide を起動する」を削除して
     以降のステップを繰り上げる
   - `rules/common/testing.md` の「skill: tdd / agent: tdd-guide」から agent 参照を
     削除する
   - scout の「Before tdd-guide」→「Before the TDD step」
2. **fresh/rich 軸に補助則 2 件を追加し、agent-stocktake の Stage 1 吸収質問に折り込む**。
   (a) frozen-input render 契約 — 呼び出し側が self-contained パケットを凍結すれば rich
   context は設計上不要になる。(b) bulk context isolation — メイン context を汚染する量の
   読み書きを隔離すること自体が委譲の正当な根拠になる。
3. **軸適用の結果を確定する**。20 agent 中 19 が正当（fresh 13 件 / 補助則 6 件）、
   ミスマッチは tdd-guide のみで解消済み。corpus 全体が軸で分類可能になった。

## Alternatives Considered

### tdd-guide を Demote to skill にする

skill `tdd` が既に存在し方法論を運んでいる。agent 側の残余（npm 前提コマンド・エッジ
ケース一覧）は skill と `testing.md` の重複であり、移設するものがない。**却下**。

### 規律の強制者（RED を確認してから GREEN）として agent を残す

順序の強制は指示の形をしており skill が既にロードしている。別 context は仕様の lossy
round-trip を足すだけで脱相関の利得がない。強制は成果物への敵対的審査ではなく（それは
Verify ゲートと reviewer 群の仕事）。**却下**。

### tdd-guide を test 品質の review 専用 agent に書き換える

テスト品質の検査は code-reviewer（missing tests 検査）と Verify の coverage ゲートが
既にカバーしており、空いたニッチがないまま 14 本目の reviewer を足すと listing の常駐
費だけが増える。**却下**。

## Consequences

### Positive

- TDD が仕様の在る場所（メインループ）で実行されるようになる。
- agent listing の常駐 description が 21 語減る（864 → 843 語）。
- fresh/rich 軸が補助則 2 件を得て corpus 全体を分類できる完成度になり、今後の agent
  新設・stocktake の判定基準として機能する。
- Chain Matrix の Plan / TDD ステップは agent ゼロ（メインループ + skill）となり、
  chain の前半 = 生成はメインループ、後半 = 審査は agent という構図が明示化された。

### Negative

- tdd-guide の ECC 上流との diff 比較ができなくなる（ファイル削除。git 履歴で復元可能）。

### Neutral / Follow-ups

- agent-stocktake の `results.json` を更新する（tdd-guide → Dissolve、総語数 843、
  set-level note に補助則適用を記録）。
- generation-audit の証拠台帳の処分状況に追記する。
- `skills/skill-comply/results/testing.md` 内の tdd-guide 言及は過去の測定記録であり
  書き換えない。

# ADR-0033: サブエージェントのモデル階層は下流の検査層の有無で決める

## Status

accepted

## Date

2026-08-02

## Context

`~/.claude/agents/*.md` の frontmatter `model` は既定値が `inherit` で、未指定の場合は
親セッションのモデルを継承する（公式ドキュメント code.claude.com/docs/en/sub-agents で確認）。

2026-08-02 時点で `ls ~/.claude/agents/*.md | wc -l` は 23、うち
`grep -L '^model:' ~/.claude/agents/*.md` が 2 件（prompt-forager / swift-reviewer）を返した。
セッション既定を Fable 5（Opus の上位ティア）のような高位モデルにすると、web 検索して
候補を数件返すだけの機械的な作業まで最上位モデルで走る。

残り 21 体には階層が明示されていたが、割り当ての根拠が記録されていなかった。今回の検討で
当初、code reviewer 系を sonnet に据え置く理由として「`.claude/verify.sh` が下流で欠陥を
拾うから」と説明されたが、これは誤りだった。`rules/common/planning.md` 自身が「決定論ゲート
の全 PASS は review の代替にならない（テストが通っても残る欠陥 — 認可・並行性・設計盲点 —
を見る別の層）」と定めている。format / lint / type check / test は既知パターンの検査であり、
code reviewer が探す欠陥とは検査対象が直交する。

あわせて、正本である `skills/implementation-chain/SKILL.md` の routing 表に swift-reviewer
が存在せず、Swift の変更は code-reviewer に流れる指定になっていた。swift-reviewer の名前は
`rules/common/planning.md` にのみ残っており、正本側に起動経路が無い drift だった。これは
[ADR-0027](0027-restore-review-execution-check-to-verify-gate.md) が定めた「表は skill、
時刻に紐づく動詞は rules」という分担の破れにあたる。swift-reviewer は agent ファイルのみ
新設され、rules への記載は ADR-0027 の変更で入り、正本の routing 表には今回まで存在
しなかった。override ではなく修復である。

## Decision

サブエージェントのモデル階層を決める軸を、タスクの難易度ではなく **その agent の出力を
検査する層が下流に存在するか** に置く。

1. 下流に意味的検査層が無い、または誤りが不可逆な agent は opus —
   code-reviewer / ~~python-reviewer~~（2026-08-13: [ADR-0039](0039-retire-python-reviewer-simplify-in-chain.md) で退役） / swift-reviewer / security-reviewer / adr-reviewer /
   paper-reviewer / architect / source-fidelity-checker
2. 下流に人間 gate または別 agent の検査がある判断系は sonnet — 記事 / README / 論文の
   レビュアー群（editor / essay-reviewer / readme-reviewer / clarity-reviewer /
   fact-checker / vocabulary-consistency-checker 等）がここに入る。paper-reviewer だけが
   opus なのは、deposit（DOI 採番）で出力が不可逆に外部化され、argument flow の質を
   後段で検査する層が無いため。essay-reviewer / editor は公開前に人間が読む前提
3. 構造的検査のみ（バイト列の形で答えが決まる）を行う agent は haiku —
   citation-formatter / prompt-writer
4. **条項が競合したときは 3 が 1 に優先する**。citation-formatter は不可逆な deposit の
   直前に立つ最終 gate だが、行う検査が構造的（引用と参照の突合、format 一貫性）である
   以上、上位モデルを当てても精度が上がらない。1 の「誤りが不可逆」条項は、意味的判断の
   質が結果を左右する場合にのみ効く
5. **`~/.claude/agents/*.md` のカタログ agent すべてに `model` を明示する**。未指定
   （inherit）を許容しない。skill 本文から ad-hoc に起動する継承モード
   （[ADR-0016](0016-writer-agents-render-not-decide.md) が残した Pass 隔離等）は対象外
6. 決定論ゲートは意味的 review の層として数えない（正本は `rules/common/planning.md` の
   Verify 節。ここはその再掲であり、第 2 の正本を作る意図はない）
7. 指定には Claude Code のエイリアス（`opus` / `sonnet` / `haiku` / `fable`）を使い、
   世代を固定する完全 model ID と `inherit` は使わない。現時点で `fable` を使う agent は
   無いが、エイリアス集合としては許可する — 実際に置くなら階層 1 の再検討を伴う

あわせて implementation-chain の routing 表に swift-reviewer を追加し、Swift を
code-reviewer の担当から外す。

## Alternatives Considered

### 全 agent を inherit のままにする

セッション既定を上げた瞬間に全 agent が追随し、機械的作業と判断作業の区別が消える。棄却。

### code reviewer 系を sonnet に据え置く（当初案）

根拠として想定した codex-review による脱相関が効くのは Chain Matrix 上 feat / fix に
限られる。refactor では codex-review が条件付き（公開 API・並行処理・セキュリティ境界の
みで発火）、security-reviewer は非適用のため、code-reviewer が単独の意味的検査層になる。
また据え置きのもう一つの動機だった「高頻度だから高コスト」は見積もり違いで、reviewer は
diff を読んで指摘を返す短命な agent であり、ツールを多数回呼ぶ長い agentic ループを回さない
ため 1 回あたりのトークン量が小さい。棄却。

### 全 review agent を一律 opus にする

構造的検査しかしない citation-formatter まで上がる。当時の `rules/common/patterns.md` にあった
code vs LLM 判定に反し、精度が上がらない箇所に費用を払う。棄却。同 rule は ADR-0035 で退役した。

### task 種別ごとに階層を変える

レビュー層の厚みは種別によって違う（feat は 3 層、純粋な refactor は 1 層）ため最も精度が
高いが、frontmatter は agent 単位でしかモデルを持てず表現できない。実行時パラメータでの
上書きは可能だが指定が chain の各所に散る。見送り。

## Consequences

### Positive

- 高位モデルをセッション既定にしても、機械的作業が最上位モデルに引きずられない
- 新規 agent を追加するとき「下流に検査層があるか」を問えば階層が決まる
- Swift の変更が専用 reviewer に届く
- `model` の指定漏れとエイリアス逸脱は `scripts/hooks/harness_lint.py` が決定論的に検出する
  （当時の `rules/common/patterns.md` にあった「文書化された不変条件はゲートに落とす」の適用。
  同 rule は ADR-0035 で退役）

### Negative

- 階層は agent 単位でしか持てないため、種別ごとのレビュー層の厚みの差を表現できない
  （Alternative「task 種別ごとに階層を変える」参照）
- 「下流に検査層があるか」は chain の構成に依存する。Chain Matrix を変更すると階層の前提が
  静かに崩れるため、両者は同時に見直す必要がある
- エイリアス表記を lint で強制するため、再現性のために特定世代へ pin したい agent が
  現れた場合は `harness_lint.py` の検査ごと見直す必要がある
- reviewer 3 種（code-reviewer / python-reviewer / security-reviewer。2026-08-13: python-reviewer は [ADR-0039](0039-retire-python-reviewer-simplify-in-chain.md) で退役し 2 種）は feat / fix /
  refactor のほぼ全 chain で発火するため、sonnet → opus の引き上げ分だけ Claude 側の
  コストが増える。増加量は未測定。Alternative で否定したのは「頻度が高いから高コスト」
  という見積もりの立て方であって、コストの存在そのものではない
  （[ADR-0028](0028-review-notice-full-scope-and-adr-reviewer.md) の「Claude 側コストは
  Consequences に計上する」に従う）

### Neutral / Follow-ups

- effort は機械的な検索のみを行う prompt-forager に `low` を設定し、それ以外は未設定とした。
  一律設定を避けた根拠は 2 つとも Anthropic の公式ドキュメント（skill: `claude-api` が
  保持するモデル表と Opus 5 migration 節）に拠る — Haiku 4.5 は effort パラメータに
  非対応であること、Opus 5 の code review は低い effort でも精度が落ちにくいこと。
  こちらでの実測はしていないため、残りの割り当ては skill-comply による測定を経て決める

## References

- `rules/common/planning.md` — Verify 節（決定論ゲートは review の代替にならない）
- `rules/common/patterns.md` — 当時の正本。ADR-0035 で退役し、
  `skills/learned/documented-invariant-lint-gates.md` が内容を保持
- `skills/implementation-chain/SKILL.md` — Chain Matrix（種別ごとのレビュー層）
- `scripts/hooks/harness_lint.py` / `tests/harness-lint-precommit.bats` — 本 ADR の決定論ゲート
- code.claude.com/docs/en/sub-agents — frontmatter 仕様（`model` の既定は `inherit`）

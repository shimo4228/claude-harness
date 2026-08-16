# ADR-0042: code-reviewer を退役して Code Review を built-in へ寄せ、Security Review を脅威面の変化に紐付ける

## Status

accepted

## Date

2026-08-16

## Context

ECC 由来の `code-reviewer` / `security-reviewer` が陳腐化しているのではないか、という
問いから調査した。結論は「陳腐化している」だが、原因は当初の見立てと違った。

### ECC 上流との差分

ローカルの 2 agent は ECC `ada4cd75`（2026-03-03）派生で、上流は `f1923017` まで
2,500 PR 進んでいた。しかし差分の実質は小さい:

- `agents/code-reviewer.md` +101/-2 — Prompt Defense Baseline、Pre-Report Gate 4 問、
  confidence >80% ゲートの**強化**
- `agents/security-reviewer.md` +10/-1 — Prompt Defense Baseline のみ。本体は 5 ヶ月無変化
- `skills/security-review/` +23/-14 — CSP 文言と Prisma/Zod パターンの微修正

confidence ゲート強化は、ローカルで意図的に外した判断（「濾すのは呼び手の別パス」）の
逆行にあたる。取り込む価値のある実質は Pre-Report Gate 1 つだった。

### Anthropic 側（CLI 2.1.233 のバイナリから抽出して確認）

`/code-review` は markdown skill ではなく動的プロンプト生成器である。Angle A–E
（行単位 diff scan / 削除された振る舞いの監査 / cross-file tracer / 言語別 pitfall /
wrapper-proxy 誤配線）に加え、Reuse / Simplification / Efficiency / Altitude /
**Conventions（CLAUDE.md を読み、規則を引用して違反を指摘）** を持つ。effort tier ごとに
出力上限があり、`ReportFindings` に構造化出力する。既定では編集しない。

判定の既定も直交している — CONFIRMED / PLAUSIBLE / REFUTED で、「**PLAUSIBLE by default**、
speculative だからと refute するな」。これはローカル改変（confidence で濾すな）と同じ立場で、
ECC 上流とは逆である。

### 計測

`metrics/agent-usage.jsonl`（2026-07-26〜08-16）:

| agent | 発火 |
|---|---:|
| security-reviewer | 54 |
| code-reviewer | 46 |
| python-reviewer | 41（ADR-0039 で退役） |
| swift-reviewer | 7（全て zafu-ios、2 日間に集中、以降 2 週間ゼロ） |

`security-reviewer` の 54 回のうち 51 回（95%）は Code Review category の agent と
±120 秒以内で対になっていた。**Matrix は守られていた** — 発火過多は Matrix の
`feat × Security Review = Y` が無条件だったことによる。

（調査の途中で `code-reviewer` だけを対照に取り「38% が Matrix 外の単独発火」と誤診した。
`python-reviewer` を対照に入れると 7%、`swift-reviewer` も入れると 5% に落ちる。
CA は Python なので Code Review category は `python-reviewer` 側で満たされていた。）

### トリビアの原因

`security-reviewer` のチェックリストは ECC 由来で、`express-rate-limit` / Supabase RLS /
JWT を httpOnly cookie へ / Solana の wallet signature 検証 / `npm audit` を列挙している。
実際の対象は CA（Python、外部 SNS API、資格情報、無人 scheduler、外部コンテンツ→LLM 文脈）と
この harness（bash hook、markdown 実行物、bypass 経路）である。**存在しないものを探した
reviewer は、形の似た何かを返す。** 発火頻度を下げてもこれは残る。

### `/security-review` を採らない理由

built-in `/security-review` は 3 段（発見 → 並列 FP フィルタ → confidence≥8）で、
出力を絞る設計としては優れている。しかし採用しない:

- ハード除外 #16「documentation files such as markdown files」— この harness の
  `skills/*/SKILL.md`・`agents/*.md`・`rules/*.md` は agent が実行する制御プログラムであり、
  human gate の順序破壊や injection 経路は実在の脆弱性である
- ハード除外 #1 / #3（DoS / rate limiting）— CA の実害（2026-07-16、アカウント無期限 block と
  全作成物削除。`rules/common/debugging.md`）はこの区分に落ちる
- precedent #14「Including user-controlled content in AI system prompts is not a
  vulnerability」— CA は外部コンテンツを LLM 文脈へ取り込む経路を持ち、`core/llm/guard.py` が
  それを守っている
- diff 範囲が `git diff origin/HEAD...` 前提で、main 直コミット運用では空になる

判例そのものは有用なので、prior として `security-reviewer` に取り込む。

### 前提の検証（2026-08-16）

`.notes/t-004-builtin-review-surface.md` は「`/code-review` は Claude から起動できない
（`disable-model-invocation`）」を 2026-07-25 実測の**確定した制約**として記録していた。
本 ADR の Decision 1 はこの制約が失効していることに依存する。同日、実セッションで
`Skill(skill="code-review")` が通ることを確認した（skill-usage.jsonl に
`{"event":"invoke","skill":"code-review","path":""}` が残る）。当該 notes には失効注記を、
`.notes/TASKS.md` の T-004 行には反転先ポインタを入れた。

## Decision

1. `agents/code-reviewer.md` を**退役（削除）**し、Code Review category の起動先を
   built-in `/code-review` にする。effort は種別で固定する（`feat` / `refactor` = `high`、
   `fix` / `chore` = `medium`）— 無指定だと「最後に打ったレベル」を再利用する仕様なので、
   chain がセッション状態に依存してしまう。
2. Chain Matrix の `feat × Security Review` を `Y` → `C` に降格し、条件を
   「脅威面を動かす feat のみ」とする。脅威面 = 資格情報の取得・保管・送出 / 外部 IO /
   公開経路 / 無人実行の起動経路とブラスト半径 / 外部コンテンツを LLM 文脈へ取り込む経路 /
   権限と bypass の境界。
3. `agents/security-reviewer.md` から**固定チェックリストを外す**。Phase 1 で repo の
   脅威面（資産 / 入口 / 出口 / 自動実行 / 既存の防御とその意図）を同定し、Phase 2 は
   それに接続する脆弱性クラスだけを producer→sink の経路付きで検査する。Phase 3 に
   Anthropic の判例を **prior** として置き、repo 側の反証（PoC / 回帰テスト / 既存 guard の
   存在 / repo の脅威モデル記述）で覆せることを明記する。**特定 repo の固有事情は書かない** —
   脅威モデルは repo が持ち、agent は導出手順と反証の資格だけを持つ。
4. `security-reviewer` の description から自発トリガー（`Use PROACTIVELY after …`）を外し、
   発火条件の正本を Matrix 一本にする。**これは過剰発火への対処ではない**（95% は Matrix
   由来だった）— 指揮系統を 1 つにするための整理である。あわせて `tools` から `Write` /
   `Edit` を外す（実運用で使われておらず、ECC 上流も #2442 で read-only reviewer contract へ
   移行済み）。
5. `hooks/simplify-order-notice.sh` の名簿を `<機構>:<名前>` の 1 本にする
   （`REVIEWERS=(skill:code-review agent:swift-reviewer)`）。機構タグが payload の読み方と
   境界ログの置き場を決めるので、reviewer が増えたときどちらの機構でも 1 語の追記で済む。
   `settings.json` の matcher を `Task|Agent|Skill` へ。レビュー境界は機構ごとに別ログへ
   落ちるので新しい方を採り、built-in には `path == ""`（署名）を要求する。
   **`settings.json` は git 追跡外で diff にも lint にも現れない** — matcher から `Skill` が
   落ちても他の全テストが緑のまま built-in 経路だけ死ぬので、matcher を pin する bats を
   新設した（負のコントロールで発火を確認）。
6. 参照の repoint: `skills/codex-review`・`skills/herdr-delegate`・`skills/python-patterns`・
   `hooks/README.md`。ADR / `.notes/` / hook のコメント内にある `code-reviewer` の言及は
   **過去の出来事の記録**なので書き換えない。
7. `swift-reviewer` は本 ADR では判断しない（下記）。

## Alternatives Considered

### ECC 上流を取り込んで更新する

差分の実質は Pre-Report Gate 1 つで、同梱の confidence ゲート強化はローカル判断の逆行に
あたる。加えて ECC の agent は単体配布物として description に発火条件（`PROACTIVELY`）を
持つ設計で、Matrix を持つ harness に入れると必ず二重指揮になる。取り込みでは解けない。

### `security-reviewer` も退役し、日常の floor を機械ゲートだけにする

CA の `verify.sh` は bandit（`check_empty` で出力ゼロ強制）+ pip-audit + ruff + pytest を
持ち、決定論層は強い。しかし意味的な信頼境界の推論（2026-07-31 の git target 乗っ取りは
この層でしか出ない）を代替するものが無い。`/code-review` にも専任の security angle は無い。
呼び出しが適切になれば reviewer としての価値は残るため却下した。

### 脅威面の変化を検出する advisory hook を足して呼び忘れを防ぐ

検出 hook は「呼び忘れ」を防ぐ機構であり、観測された問題（呼びすぎ）には効かない。
過剰発火を止められるのはオーケストレーターの判断だけである。Matrix の条件化で足りる。

### Security Review をタスク境界 / 週次スケジュールへ移す

この repo 群では 1 タスク ≒ 1 実装なので、タスク境界は現状と同じ粒度になる。週次は
脅威面が動いていない週の空振りと、動いた週の数日遅れの両方を持つ。頻度ではなく変数
（何に紐付けるか）が問題だったため却下した。

### `/security-review` を採用する

上記 Context の 4 点（markdown 除外 / DoS 除外 / precedent #14 / diff 範囲）により、
この repo 群で最も重要な脅威クラスが構造的に落ちる。判例のみ prior として取り込む。

### `swift-reviewer` も同時に退役する

観点の大半（Swift 6 strict concurrency、retain cycle、値意味論、API 慣行）は
`/code-review` の Angle D と Conventions angle でカバーされうる。しかし
HIG / アクセシビリティは `/code-review` の定義（correctness bugs + cleanup）の射程外で、
かつ「実装時の参照資料」に降格するのは誤り — これらは完成物を観察して初めて現れる
acceptance の関心である。発火 7 回は**利用頻度の証拠であって不要性の証拠ではない**。
退役するなら受け皿（runtime observation / XCUITest / iOS acceptance review）を先に
決める必要があるため、本 ADR では判断しない。

## Consequences

### Positive

- Code Review が effort tier / `ReportFindings` / `--fix` / Conventions angle（CLAUDE.md
  違反を引用付きで指摘）を得る。239 行の TypeScript/React 前提チェックリストの保守が消える
- Security Review の発火が「脅威面を動かしたとき」に限定され、空振りが減る
- `security-reviewer` の指摘が repo の実際の脅威面に接続する。空の報告が正当な結果になる
  （件数表を廃止したのはそのため — 埋めるために指摘を作る圧力を外す）
- 発火条件の正本が Matrix 一本になり、二重指揮が消える

### Negative

- `code-reviewer` が持っていた Security (CRITICAL) 節の二重被覆が消える。とくに
  `refactor × Security Review = -` の種別では security の目が無くなる。**発火回数で埋める
  対処は採らない**（それが今回退役させた過剰発火そのもの）。`refactor` で信頼境界に触れる
  場合は Cross-Model Review が `C` で拾い、決定論層は verify ゲートが持つ
- `security-reviewer` が Phase 1 で脅威面を毎回導出するので、1 回あたりのトークンが増える。
  発火回数の削減がこれを上回るかは未観測
- built-in `/code-review` の中身は Anthropic 側の実装であり、CLI 更新で挙動が変わりうる。
  ADR-0011 が記録した「built-in 構成変更リスク」と同種の依存を 1 つ増やす
- `swift-reviewer` の判断を再び先送りした（ADR-0039 に続き 2 回目）

### 観測として記録する（本 ADR では扱わない）

- **`Verify` の語彙衝突。** この harness の Verify は `.claude/verify.sh`（lint / type /
  test / secret / deps）だが、CLI 同梱の `verify` skill は実行時観測を指し、
  「Don't run tests. Don't typecheck.」と明示している。現在 feature flag off で衝突は
  潜在だが、Matrix 10 段のどこにも「動かして見る」段が無いという実質の欠落は今もある
  （2026-08-15 の bats assertion 握り潰しは、ゲートが PASS し続けたまま 4 箇所が一度も
  検証されていなかった事例）
- **`implementation-chain` が front-load 構造であること自体。** substrate が実装後チェーンを
  内蔵した以上、Matrix の価値は「起動手順」ではなく「repo 固有の条件分岐」に移っている
- **PR を使わない運用。** `/code-review --comment` / `--post` / `artifact-pr-review` /
  `/security-review` の diff 範囲は全て PR 前提で、main 直コミットでは使えない。ただし
  必要なのは PR ではなく安定した比較基点であり、レビュー契約とは直交する

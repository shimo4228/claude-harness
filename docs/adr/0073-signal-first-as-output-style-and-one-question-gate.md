# ADR-0073: Signal-first を output style と AskUserQuestion 1 問ゲートで持つ — 読者の注意は 1 チャネル

## Status

accepted — [ADR-0026](./0026-retire-signal-first-residency.md) Context 第三（Claude 5 世代は signal-first 相当を既定で行える）を対話の形について部分的に弱める（生き残る範囲は ADR-0026 側の注記が持つ）

## Date

2026-09-19

## Context

著者（2026-09-19）:「以前モデルの進化とともに signal first を外したのだが、やはりあった方がいい気が
してきた。ただ、そのまま置いとくのよりも今のモデルとハーネスに最適なやり方があるだろうから、
その形を提案してほしい」。症状を問うと、著者は「報告・応答が肥大」を選び、自由記述で
「一度に複数のことを聞いてくることがあるが、あれを 1 番やめてほしい」と答えた。経路は
「対話セッション全般」。調査の発散（旧節の intake 側）は挙がらなかった。この問い自体を判断役は
AskUserQuestion の 2 問同時で出しており、同じセッションが症状の 1 例になった。

旧 Signal-first 節は ADR-0026（2026-07-31）で `rules/common/akc-cycle.md` から退役した。理由は
3 つ — 消費 skill への内在化完了、常駐の抑制圧力が skill `grill-me` の要件質問を減らした実害、
Claude 5 世代は signal-first 相当を既定で行えるという判断。今回の症状は 3 つ目を対話の形について
弱める。「score を出さない」類の出力規律は消費 skill への内在化で足りているが、読者に求める判断を
1 メッセージに 1 つへ直列化する挙動は既定で出ていない。観測は著者の申告と上の 2 問同時の 1 例で、
頻度の実測は無い — Decision 2 の計測ログが初めて与える。AskUserQuestion の tool 定義（Claude Code が
model に渡す schema、2026-09-19 時点）は `questions` を「1-4 questions」とし、まとめ聞きは substrate 側の
既定として出る。

戻し方を縛る先例:

- 出力の形を常駐 rule で持つ試みは 2 度退役している — `rules/common/output-register.md`
  （[ADR-0030](./0030-separate-output-writing-from-residency-register.md) で新設、
  [ADR-0035](./0035-commit-review-hook-and-rules-rightsize.md) Decision 4 で退役）と旧 Signal-first 節
- Stop hook の反復 advisory は ADR-0035 で全廃された
- 旧節は「行動を変えないものを出すな」という抑制で、grill-me と衝突した。今回の要求は問いの
  総数を減らすことではなく直列化で、grill-me の 1 問ずつの形と同じ向きにある
- `settings.json` の `outputStyle` は組み込み `Concise` だった。
  [ADR-0061](./0061-prompt-audit-version-diff-markers-and-lint-gate.md) Context が、Claude Code
  system prompt の recap 指示と矛盾する update-suppressor として flag し、著者判断待ちのまま残っていた

一次ソース照合（2026-09-19、`https://code.claude.com/docs/en/output-styles.md` と
`https://code.claude.com/docs/en/hooks.md`）: 自作 output style は `~/.claude/output-styles/` に置く
Markdown で現役。`keep-coding-instructions: true` を付けないと Claude Code 組み込みの software
engineering 指示が外れる。subagent は自前の system prompt で走り style を継がない。組み込み
`Concise` は「結果を先頭に置き、前置きと実況を省き、既定で短く保つ」style — 結論先頭と短さは
既に `Concise` が運んでおり、肥大と複数質問はその下で観測された。PreToolUse は exit 2 で tool
call を block し、stderr が model に渡る。`AskUserQuestion` を matcher に書けるかは docs に記載が
無い（未確認）。この harness では同じ tool 名方式の matcher `ExitPlanMode` が
`hooks/plan-executor-notice.sh` で稼働している。

`outputStyle` は project-local が user 設定に勝つ。2026-09-19 時点で `outputStyle` を自前で持つ
project-local は 2 つ（`grep -rl outputStyle ~/.claude/.claude/ ~/MyAI_Lab/*/.claude/`）:
`~/.claude/.claude/settings.local.json` の `"default"`（この harness repo 自身）と
`~/MyAI_Lab/systems-thinking-learning/.claude/settings.local.json` の `"Sounding board"`。
この 2 repo のセッションには user 設定の style が届かない。

## Decision

1. `output-styles/signal-first.md` を新設し、user 設定 `settings.json` の `outputStyle` を `Concise` から
   `Signal-first` に替える。project-local の上書きは外して user 設定を効かせる（著者指示 2026-09-19
   「全部今回の output style が効くように」）: harness repo の `"outputStyle": "default"` の行は外した。
   `systems-thinking-learning` の `"Sounding board"` は判断役の編集が permission 層に拒否されたので
   著者が手で外す（その repo の `.claude/output-styles/sounding-board.md` は残り、行を戻せば復帰する）。
   本文は規則の列挙でなく読者の記述から始める —「読者は 1 人の
   practitioner で、注意は 1 チャネル」。そこから 4 項を肯定形で置く: 応答は次の行動を変える情報で
   構成し冒頭 1〜2 文で結論を言う / 読者に求める判断は 1 メッセージに 1 つで、答えに依存しない作業は
   聞く前に進める / 問いには推奨とその帰結を添える / 明示起動された interview（`/grill-me`、
   `/mondo`）の間は問いが成果物で、総数は絞らず 1 問ずつ出す。`keep-coding-instructions: true` を付ける。
2. `hooks/ask-one-question.sh` を PreToolUse（matcher `AskUserQuestion`）に配線する。
   `tool_input.questions` が 2 件以上なら exit 2 + stderr の固定文言で block する。文言は tool input の
   中身も shell のエラー行も運ばない。件数が読めない入力（欠落 / 配列でない / 不正 JSON）は allow する。
   件数が読めた呼び出しは allow / block とも計測ログへ 1 行（ts / 件数 / blocked / session）を残す —
   allow 行が分母で、最初の 1 行が hook の発火確認を兼ねる。path と schema の正本は hook 冒頭コメント。
   回帰は `tests/ask-one-question.bats`。hook は user 設定に配線するので、Decision 1 の style が
   届かない repo でも block する。
3. 散文の中の複数質問は機械ゲートにしない。意味の判定は regex に載らないので、Decision 1 の style
   本文が担う。
4. 旧節の intake 側（調査の前に signal を定義する）は戻さない。原則の正本は ADR-0026 のとおり
   消費 skill 側（`search-first` ほか）に置いたままにする。
5. doc sync: `hooks/README.md` の Active Hooks 表、`CLAUDE.md` の Layout、`.gitignore` の計測ログ行、
   本 index。注記を ADR-0026 Context 第三の下と ADR-0061 の Concise follow-up の下に置く。

## Review-when

- **hook の発火確認が先。** matcher `AskUserQuestion` は docs 未確認なので、計測ログに最初の 1 行
  （allow でも block でも）が載るまで、ログの 0 件を証拠に使わない（ログ不在は「未計測」）。
  AskUserQuestion が呼ばれたのにログが空のまま 2026-10-19 を過ぎたら matcher が効いていないと見て、
  hook を外し style 本文だけにする。判定者は判断役（2026-10-19 以降で最初の rules-stocktake の回）。
- 発火確認の後、allow 行が 10 行以上ある連続 30 日で block 行が 0 件なら hook を溶かす（allow 行が
  10 行に満たない窓は「未使用」で、遵守の証拠に数えない）。固定するもの: 本 ADR 時点の
  `hooks/ask-one-question.sh` の判定（`questions` 配列長 ≥ 2）と matcher、user 設定の `outputStyle` が
  `Signal-first` のままであること、style 本文の「判断は 1 メッセージに 1 つ」の項が無改訂であること。
  どれかが変われば数え直す。判定者は判断役（次の rules-stocktake の回）。
- 著者が `/grill-me` の終了後に「聞かれるべきことが聞かれなかった」と観測したら、Decision 1 の
  interview 項を見直す（記録先: 本 ADR への注記）。ADR-0026 Follow-ups の指標（終了時に未解決の
  decision point 数）は実測された記録が無く、比較の baseline にできないので、著者の観測を条件にする。
- 著者が「複数のことを一度に聞かれた」を散文の問いについて 2 回観測したら（記録先: 本 ADR への
  注記、1 回ごとに 1 行）、style 本文の「判断は 1 メッセージに 1 つ」の項を書き直す。機械ゲートへは
  広げない。書き直したら上の 30 日の窓を数え直す。
- Claude Code が output style の仕様を変えた、または AskUserQuestion の `questions` 上限を 1 にしたら、
  該当する Decision を溶かす（Scaffold Dissolution downward）。

## Alternatives Considered

### 旧 Signal-first 節を `rules/common/` にそのまま戻す

却下: ADR-0026 の実害（grill-me の質問抑制）がそのまま再発する。旧節は抑制形で、著者が今回挙げた
症状（複数質問）を名指ししてもいない。常駐 rule は subagent を含む全経路に載り、読者が LLM の経路
にも人間向けの register を運ぶ。

### 同じ本文を新しい常駐 rule に置く

未決 — 再訪条件: (a) project-local の `outputStyle` 上書きが再発して style が黙って外れているのを
著者が見つけたとき、(b) 別の style（`Concise`、repo 固有の style）と併用したくなったとき、
(c) output style の仕様変更で自作 style が使えなくなったとき。今回採らない理由は、
`rules/README.md` の採用基準（環境固有の事実・配線・罠）に出力の作法が乗りにくく、同種の rule が
2 度退役していること。output style は product が人間向け応答のために用意した枠で、`Concise` との
1 増 1 減になり常駐は純増しない。実装後に判断役は rule への移設を勧めた — style の枠は排他で
他の style と重ねられない、project-local の上書きで黙って無効になる（導入当日に 2 件）、
`Concise` が結論先頭と短さを既に運んでおり固有分は 3 項だけ、の 3 点が理由。著者は output style の
まま運用して様子を見ると決めた（2026-09-19）。移設するときの形: 固有の 3 項と読者の記述を
`rules/common/` に置き、`outputStyle` を `Concise` に戻し、hook は変えない。

### `Concise` のまま、1 問ゲートの hook だけ足す

却下: hook が見られるのは AskUserQuestion の件数だけで、散文の複数質問と肥大には届かない。
ADR-0061 が flag した `Concise` の矛盾も残る。

### Stop hook で応答の問いの数を数える

却下: 問いの数は意味の判定で regex に載らない。ADR-0035 が全廃した反復 advisory と同じ形になる。

### 何もしない

却下: 著者が症状を名指しし、判断役が同じセッションでそれを再現した。

## Consequences

### Positive

- 著者が一番やめてほしいと言った挙動のうち grep 可能な 1 点（AskUserQuestion の件数）が機械で止まる。
  model への文言は違反時だけ出るので、常駐の文面コストは無い（hook 自体は呼び出しごとに走り 1 行記録する）。
- 人間向けの register（style）が product の正規の枠に入り、subagent と style を pin する utility
  呼び出し（`skills/skill-comply/scripts/child_settings.py`）には届かない。hook は別で、user 設定に
  配線されるため AskUserQuestion を呼ぶ全経路に届き、block 文言（人間向け register の 1 行）も
  そこへ出る。
- ADR-0061 が flag した矛盾は「product 同梱 style のため diff 不可」だった。style が自作になり、
  recap 指示との整合は著者が本文を直せる対象になる — この意味で follow-up は閉じる。自作本文は
  着手前の 1 行と結びの recap を止めていない（結論を先頭に置く、経緯は求められたときに出す、の
  2 点だけ）。update-suppressor 型を再生産していないかの判定は次回の prompt-audit に渡す。

### Negative

- `Concise` の組み込み本文（結論先頭・短さ）を手放す。自作 style の 1 項目が同じ向きを持つが、
  文面は product の更新を受けなくなる。
- project-local に `outputStyle` が書かれた repo には style が届かず、hook だけが効く。`/config` は
  project-local に書くので、どこかの repo で style を切り替えると同じ上書きが黙って再発する。
  検出は Context の `grep` 1 本。
- hook は 1 呼び出しの件数しか見ない。同じ応答の中で 1 件の AskUserQuestion を複数並べる形は通る
  （呼び出し間の状態を持たない。code review 2026-09-19 の指摘、設計範囲外として受け入れる）。
- 独立で本当に同時に要る複数の判断（互いに依存しない 2 問）も往復が 1 回増える。著者の注意を
  1 チャネルとして扱う対価として受け入れる。
- plan mode の組み込み手順は AskUserQuestion を促す。1 件ずつなら通るが、block されると model は
  1 往復を失う。
- `keep-coding-instructions: true` の意味は product 側の定義に依存し、外れると coding 指示が黙って消える。
- hook の発火は本 ADR 時点で未確認（Review-when 1 項目）。効いていなければ、しばらくの間ゲートは
  存在しないのと同じになる。
- 巻き戻しは 2 層に分かれる。hook / bats / style の 3 ファイルと doc は git 追跡下で revert できる。
  `settings.json` は gitignore 対象（live config）で git は戻してくれない — 手で `outputStyle` を
  `Concise` に戻し、PreToolUse の matcher `AskUserQuestion` の entry を消す（user 設定の変更はこの
  2 箇所）。project-local は Decision 1 に書いた元の値（`"default"` / `"Sounding board"`）を 1 行戻す。
  同じ理由で、配線の存在は commit に残らない。配線の記録は本 ADR の Decision 1・2 と
  `hooks/README.md` の表が持つ。計測ログも gitignore 対象で復元不能だが、巻き戻し時には不要。

### Neutral / Follow-ups

- skill `task-triage` の Digest は recommendation を 4 番目に置く順序で、同じ原則の適用先候補。
  経路が対話でないので本 ADR では触らない。
- output style は harness-sync の origin 収集対象に入っていない。公開するかは次回の harness-sync で
  著者が決める。origin は frontmatter に置いた（収集対象に入れるとき既存の filter がそのまま効く形）。
- 計測ログは ADR と hook コメントの 2 箇所に schema の言及がある。正本は hook 冒頭コメント。

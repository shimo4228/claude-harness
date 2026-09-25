# ADR-0078: generation-audit を世代交代監査の単一入口にし、dated pattern 走査を `/claude-api prompt-audit` に委ねる — Opus 5.5 監査の実施記録

## Status

accepted — [ADR-0061](./0061-prompt-audit-version-diff-markers-and-lint-gate.md) の Alternatives「generation-audit
skill に統合する」の却下を覆し、[ADR-0022](./0022-generation-audit-three-sibling-stocktakes.md) Decision 1 の
「verdict も処分も持たない・3 分類」を狭める（どちらも部分的に弱める。注記は各 ADR 側）

## Date

2026-09-25

## Context

- 著者の依頼（2026-09-25）: dispatch 周りの改修（ADR-0076）の仕上げに `/claude-api prompt-audit` を掛けるよう
  求め、続けて範囲を「dispatch 用だけでなくハーネス全体に」と広げ、「generation-audit と役割が被るから統合か
  退役か、ベストな形にして」と判断を任せた。
- 本 ADR の用語: **dated pattern** = 旧世代のモデル向けに書かれ、対象モデルでは不要か有害になった書き方
  （prompt-audit の Group 1–4）。**slice** = 監査対象のファイル群を行数で均した、互いに重ならない組。
- 世代交代の入口が 2 つあった。skill `generation-audit`（ADR-0022、2026-07）は runtime 層（system prompt +
  tool description）と自作資産の照合、`/claude-api prompt-audit` は資産内部の dated pattern の静的検査で、
  ADR-0061（2026-09-02、Fable 5.1）は 2 つを「別物なので model release ごとに併走させる」とした。
- 実行の記録: generation-audit は 2026-07-26 の Fable 5 世代交代で一度通しで実行された（証拠台帳
  `.notes/archive/generation-audit-2026-07-26.md`。skill 本文の「次の世代交代が初回フル実行」は古いままだった）。
  local の skill 使用記録（`~/.claude/metrics/skill-usage.jsonl`、gitignore 下）は、本 session を除くと read 11・
  slash 1（07-26）・invoke 1（08-15）。その後の 2 回の世代交代（Fable 5.1 = ADR-0061、Opus 5.5 = 本 ADR）は
  どちらも prompt-audit だけで行われた。
- runtime 照合の実績: Claude 5 世代交代の常駐削減（ADR-0018、5,789 → 2,314 words）と、07-26 台帳の競合 10 件
  （台帳の記載のまま: 意図的な上書き 1、幽霊参照・誤事実 8、skill 間の指示矛盾 2 — 内訳の和は 11 で合計と 1 件
  ずれる）と冗長（rules 4 部分・agents 3・learned 1）。このうち runtime 照合にしか無いのは、Claude Code の
  system prompt の文面そのものとの突き合わせ — 「本体側で運ぶようになった指示を自作資産が重ねて言っている」
  冗長の検出（例: 台帳 R-02、coding-style の Reversibility Gate と system prompt の confirm-first）。prompt-audit の
  Step 3（trained default の言い直し）も一般論としての冗長は拾うが、system prompt の文面は見ない。幽霊参照は各 stocktake の機械チェックと重なる。ADR-0061 Context の Concise
  style の矛盾は、prompt-audit の update-suppressor の行が見つけたもので、runtime 照合の実績ではない。
- prompt-audit の手順書と pattern 表は Claude Code 同梱の claude-api skill の中にあり（本 ADR 時点は CLI 2.1.280
  の bundle）、Anthropic が model release ごとに更新する。
- generation-audit は `git grep -l generation-audit` で tracked 25 ファイル（bc96b8b 時点、`docs/adr` と `.notes`
  を除くと 13）から参照され、単独 skill の公開 repo（shimo4228/generation-audit、public）がある。

## Decision

1. skill `generation-audit` を世代交代監査の単一入口にする。Phase 0 で対象モデル（新しく役に就いたモデル。
   資産を読む役のモデルで見る）・範囲（`~/.claude` の prompt surface）・適用除外（外部 origin の未改変の写し、
   別セッションが作業中のファイル）を決め、Phase 1–2 で runtime 照合（競合・冗長。採取は対象モデルを対象の
   実行環境で起動した session で行う）、Phase 3 で `/claude-api prompt-audit` を read-only の subagent に slice で
   並列に回し、Phase 4 で 4 観点の判定と行修正の適用、Phase 5 で資産単位の verdict を stocktake に渡して記録する。
   ADR-0022 の 3 分類のうち「ドリフト」は prompt-audit の pattern 表（stale な事実は Group 2 の Volatile
   specifics）に委ねる。
2. **適用の同意**: `/generation-audit` の起動に加え、著者の依頼が適用まで含むとき（「直して」「仕上げて」）は
   Phase 3 の High / Medium を適用し、含まないときは group ごとに diff を示して承認後に適用する。常駐層
   （rules / CLAUDE.md / output style）の行はどちらの場合も 1 件ずつ diff を示す。
3. pattern 表と対象モデルの挙動は、実行のたびに prompt-audit の手順書と移行ガイドから読む（path は `/claude-api`
   の base directory から引く）。
4. rules-stocktake / skill-stocktake / agent-stocktake の Related を runtime 照合 + prompt-audit の所見に合わせ、
   rules-stocktake の NOT for に generation-audit への案内を足す。
5. Opus 5.5 監査の実施記録（件数の正本は本 ADR）:
   - 対象: Claude Opus 5.5（build 役と日常の session）。根拠は bundle 2.1.280 の `shared/model-migration.md`
     「Migrating to Claude Opus 5.5」と「Migrating to Claude Opus 5 › Behavioral shifts」。
   - 範囲: rules 14・CLAUDE.md・AGENTS.md・output style 1・agents 9（別 session が削除中の 2 本を除く）・skills 58
     （symlink の hunk-review を含み、適用からは外す）と `skills/*/references/`・hook の model 向け文言。5 slice。
   - 所見 107 件（5 つの subagent の報告の集計。報告は保存していない — ADR-0061 と同じ扱い。slice は重ならない
     ので重複除去はしていない）: 1a 4 / 1b 4 / 1c 13 / 1d 32 / 1e 3 / 1f 5 / Group 2 41 / Group 3 1 / Group 4 1 /
     範囲外・別 slice 3（どの slice の所見とも重ならない）。確度は High 8 / Medium 60 / Low・flag・deferred 39。
   - 適用 64 件 = High 8 + Medium 56（ファイル削除 1 件 — `skills/tdd/references/example.md`、単一の gold
     example）。うち packet の字義どおりの縛り・zsh 専用構文・task-triage 本文の経緯の日付は、同じファイルを
     扱った ADR-0076 の commit（bc96b8b）に入った。適用しなかった 43 件 = Medium 4（別 session が作業中の
     readme-writer 2、外部の写しの Explore 1、公開状態を確かめられなかった jev-judgment-design の記事 1）+
     Low・flag・deferred 39。
   - 常駐層の 2 件: `rules/common/akc-cycle.md` の本文の編集日付（lint と同種の修正として `boundary.md` の
     「聞かずに直す軽微な修正」で扱い、個別の承認は取っていない）と、`output-styles/
     signal-first.md` の経過報告の行（update suppressor → 作業中は要所で 1 文ずつ出す。著者が 1 件として承認、
     2026-09-25）。後者は ADR-0073 が次回の prompt-audit に渡していた判定の答え。ただし 2026-09-25 時点で
     signal-first style は有効になっておらず（settings.json に `outputStyle` が無く、Desktop の session は
     `default`）、著者は `default` のままを選んだ（ADR-0079）— この行は style を有効にしたときから効く。
   - High のうち security-reviewer の「確信度の低い指摘は捨てる」は、ADR-0042（濾すのは呼び手の別パス）に
     反して後から入った行で、「全件に確信度を付けて返す」に戻した。
   - Opus 5.5 固有の型（thinking の深さを散文で操る・推論の再現を求める・曖昧な「汎用的な見た目を避ける」）は
     0 件。最多は Group 2（経緯の語り・退役物の名残・版に縛られた記述）41 件、次が 1d（移行の経緯を語る過去形・
     版差）32 件。ADR-0061 Review-when の「1d が再び最多なら lint の動詞集合を広げる」は判定できない —
     ADR-0061 は退役機構の tombstone を 1d に数えたが、今回の subagent は退役物の名残を Group 2 に入れており、
     報告を保存していないので数え直せない（比較不能）。lint は変えず、次回は tombstone を 1d に数える。
   - runtime 照合は Phase 1 の手順（テーマ別の逐語引用）ではなく、監査した session が自分に載った system prompt と
     突き合わせた ad hoc なもの。commit / push の既定（「頼まれたときだけ、default branch なら branch を切る」）と
     `boundary.md` の「とる」の食い違い 1 件を、system prompt 自身の「unless durably authorized」の例外に当たる
     意図的な上書き（ADR-0069）と判定し、編集はしない。

## Review-when

- 次の世代交代で監査が generation-audit を通らずに prompt-audit だけで行われたら（その監査の commit body に
  Phase 5 の `runtime 照合:` 行があるかで見る）、単一入口の設計は定着していない — generation-audit の退役
  （prompt-audit 単独）を再訪する。
- Phase 1 の手順で行った runtime 照合が 2 回続けて編集に至る所見を 1 件も出さなかったら、Phase 1–2 を溶かす。
  数えるのは監査を回した session で、監査の commit body に「runtime 照合: 編集 N 件」の 1 行を残す。数え始めは
  次の世代交代（本 ADR の ad hoc な照合は数えない）。固定するもの: Phase 1 のテーマ別逐語引用の手順。
- `/claude-api` skill から prompt-audit の手順書が消える・呼び出し方が変わったら、Phase 3 のエンジンを再訪する。

## Alternatives Considered

### generation-audit を退役し、prompt-audit だけにする

却下: prompt-audit は資産の中の書き方を見るが、自作資産と system prompt の重複（本体側に吸収された指示）を照合
しない — ADR-0018 の常駐削減と 07-26 台帳の冗長はこの照合で見つかった。範囲・除外・適用の規約（ADR-0061 の
ときは commit body にしか無かった）も毎回作り直しになる。25 ファイルの参照と公開 repo の付け替えも要る。

### 2 つを別の入口のまま併走させる（ADR-0061 の現状）

却下: 直近 2 回の世代交代はどちらも prompt-audit しか回らなかった。統合後も `/claude-api prompt-audit` は単独で
呼べるので、入口の一本化は完全ではない（Negative）— それでも、世代交代の手順とこの harness の規約が 1 か所に
あれば、著者が打つ入口は 1 つで済む。

### prompt-audit の pattern 表を generation-audit に写して自前で持つ

却下: 表は Anthropic が model release ごとに更新する。写しは次の release で drift し、それを刈る所有者がいない
（skill `skill-creator` §2 の Redundant channel）。

## Consequences

### Positive

- 世代交代の手順とこの harness の規約（範囲・除外・適用の同意・記録）が generation-audit の 1 か所に集まり、
  runtime 照合と dated pattern 走査が同じ実行で回る。
- pattern 表は Anthropic 側の更新をそのまま使える。
- Opus 5.5 監査で、build の packet の字義どおりの縛り、security-reviewer の見逃しを増やすフィルタ、退役した
  agent の名残、同一ファイル内の食い違いなどが直った。

### Negative

- 単一入口は著者が `/generation-audit` を打つか、`rules/common/akc-cycle.md` の行で思い出すことに依存する
  （generation-audit は `disable-model-invocation: true`、model は `/claude-api prompt-audit` を直接呼べる）。
- Phase 3 は Claude Code に同梱された skill のファイルに依存し、path は CLI の版で変わる。
- 今回の適用は約 40 ファイルを一度に直した。機械ゲート（`harness_lint.py`、`scan_refs` の dangling 0、HEAD の
  `verify.sh`）は通したが、prompt-audit の Step 7 が勧める変更ごとの挙動の確かめは行っていない。
- Phase 1 の採取はモデルの自己申告で、スクリーニングにとどまる。
- 公開 repo（shimo4228/generation-audit）: v2 の本文は harness の path と同梱 skill に依存し、公開 README
  （ドリフト分類・処分の委譲を説明する v1 の文面）と食い違う。その repo の次の harness-sync は著者の公開判断で、
  それまで公開側は v1 のまま。

### Neutral

- 資産単位の verdict（Retire / Merge 等）の正本は各 stocktake のまま。generation-audit が持つのは行修正の適用まで
  （ADR-0022 Decision 1 への注記）。
- ADR-0061 の lint（版差 marker の検査）はそのまま効く。
- 戻すときは generation-audit の本文、3 stocktake の Related と rules-stocktake の NOT for、旧 ADR の注記
  （0022 に 2 件・0061 に 4 件・0073 に 1 件）を戻す。公開 repo へ同期した後なら、その v2 も戻す。適用した 64 件は
  判断から独立している。

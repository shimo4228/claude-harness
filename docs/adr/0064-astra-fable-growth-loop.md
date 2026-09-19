# ADR-0064: Astra–Fable growth loop — 戦略 / 制御 / 実行 / 観測 / 人間の五役を既存の triage loop 基盤の上に建て、状態は `.growth/` の 3 ファイルだけ持つ

## Status

accepted

## Date

2026-09-08

## Context

著者は 2026-09-08、「GitHub follower を 90 日で 10,000 へ」という campaign 目標に対し、固定の
90 日 plan ではなく**観測から tactic を適応させる閉 loop**を要求した。五役: Astra（戦略、
14 日スケール、North Star の唯一の書き手）/ Fable（制御、observe → diagnose → decide →
dispatch → verify → measure → kill-iterate-scale → escalate）/ worker（実行）/ collector
（決定論の観測）/ 人間（公開・評判に関わる最後のスイッチ）。永続状態は
`.growth/NORTH_STAR.md`・`EXPERIMENTS.md`・`SNAPSHOT.json` の 3 つだけ、DB・dashboard・
orchestration runtime は「観測された必要」の後にしか建てない、という制約付き。

出発点の実測（2026-09-08、`collect_snapshot.py` の初回 run）: followers 61 / 公開 repo 60 /
stars 合計 81 / 最多 star repo 6（contemplative-agent、pdf2anki）/ 追跡 20 repo の 14 日 views 240
（前 14 日 118）/ clones 2,110（crawler 支配、hub `traffic/README.md` の 30:1 超が常態）。
必要軌道は 61 → 10,000 を 90 日で: 線形なら 1 日 110 人、指数なら日率 5.8%。観測 slope
（personal-branding ADR-0003: 2 か月で 54 → 62）とは桁が違う。

既存資産で再利用できるもの:

- 観測: hub repo `shimo4228/shimo4228` の `.github/workflows/traffic-daily.yml`（日次 clones /
  views を `traffic/data/*.jsonl` に append、9 repo、CC0）。followers / stars の日次 series は無い
- loop 基盤: skill `task-triage`（judge / build / human の三役、ADR-0043）、`scripts/triage-tick.sh`
  + launchd plist（timer は session の外、executor は Remote Control 付き常駐 Herdr session、
  ADR-0045）、skill `spawn-session`、packet template、digest の型
- 人間 gate: skill `x-draft`（投稿は人間）、`public-comment`（返信は人間）、zenn-content の
  publication GO（著者のみ）、rule `debugging.md`（rate limit = policy signal、2026-07-16 BAN）
- worker: `readme-writer` / `llms-txt-writer` / `headline-craft` / `collect-context` →
  writing-ecosystem / `search-first` / `scout` / `release-doi` / `harness-sync`

campaign と衝突しうる既存判断（Explore agent の報告、2026-09-08）:

- personal-branding ADR-0003 Decision 4「reach は目標だが**数値目標は置かない**」— 10,000 という
  goal と正面衝突。Decision 6（bulk 投稿 / mass follow / 自動投稿の禁止）は本 loop の growth
  ethics と同方向
- authorship-strategy ADR-0007 第 2 項（backlink campaign・自己宣伝投稿は戦略活動でない）は
  ADR-0022 の層別化後も doctrine 層・essay 層の両方で有効。**practitioner 層（claude-harness、
  skill repo 群、実践記事）は対象外** — campaign の資産はこの層に限る必要がある
- personal-branding CLAUDE.md「positioning は著者の authorial act」— Astra が決める
  positioning は campaign の narrative であって著者の自己定義ではない

## Decision

1. **skill を 2 つに分け、所有権を file 境界にする。** `skills/growth-astra`（`NORTH_STAR.md` の
   唯一の書き手、fresh context で走る、dispatch しない）と `skills/growth-fable`（cycle の判断・
   `EXPERIMENTS.md` の運用所有・dispatch / verify / escalation）。両方とも Skill tool の listing に
   載せる（`disable-model-invocation` は付けない）: 入口は人間の slash、launchd tick の本文 prompt
   "Run skill growth-fable"、Fable → Astra の本文 prompt "Run skill growth-astra" の 3 つで全部明示
   だが、本文 prompt の名指しは listing に無い skill を解決できない（skill-creator の fresh-context
   判定が Fix で指摘、task-triage と同じ置き方に揃えた）。dispatch・worktree・検収・digest の
   **機構**は `task-triage` §2–§4 を参照し複製しない。
2. **状態は `~/MyAI_Lab/personal-branding/.growth/` に置く。** personal-branding は「著者を主語に
   する唯一の repo」で Phase 3 = reach、local-only（remote 無し）。Fable session の cwd をここに
   すると同 repo の CLAUDE.md / strategy / ADR が制約として自動で載る。`~/.claude` は control
   plane で campaign 状態を持たない。
> **注記（2026-09-15, ADR-0068 監査時）**: campaign 状態の正本は著者の台帳追記（personal-branding/.growth/EXPERIMENTS.md 追記 5）と `~/MyAI_Lab/growth/README.md` により `~/MyAI_Lab/growth/.growth/` へ移った。personal-branding/.growth/ は凍結。skill growth-fable と plist は growth を指す。新 repo の台帳は `GX-NNN` / `status` / `Next review` の契約を持たず、次 cycle で migrate するか契約側を緩めるかを決める。

3. **collector は local script** `skills/growth-fable/scripts/collect_snapshot.py`（stdlib + `gh`、
   tests 12 本）。hub の traffic JSONL を読み（既存 collector の再利用）、`gh api` で followers /
   stars / `starred_at` からの star velocity（7・14・30 日、履歴不要）/ 14 日 referrers / code-search
   mentions（query を記録、10 req/min throttle）を足す。followers と stars_total だけ時刻付き
   source が無いので collector 自身の日次 series を SNAPSHOT 内に持つ。**hub CI の拡張
   （followers / stars の日次 snapshot）は breakout 中に日次粒度が要ると観測されてから** worker
   task として出す。取れない値は null + `errors[]`、推定しない。
4. **timer は `scripts/triage-tick.sh` に `--prompt-file` seam を足して再利用する。** 常駐 Herdr
   session `growth-fable`（cwd = personal-branding）、launchd 月・木 07:10（ADR-0045: 分は :00 を
   避ける。plist `scripts/launchd/com.shimomoto.growth-fable.plist` は本 session の classifier が
   作成を止めたため人間が copy + `launchctl bootstrap` で登録した、2026-09-08）。Astra に timer は無い: Fable が cycle 冒頭で
   NORTH_STAR の `Next review` と escalation 条件を検査し、必要なら `spawn-session` で fresh session を
   立てて `/growth-astra` を打たせる（timer は 1 本）。定例の間隔は phase 依存 — active な Major Bet が
   無い間は 7 日、active な window があれば 14 日（window 前の数字で thesis を書き換えない。著者
   2026-09-08「最初は週 1 の方がよい」）。変更なしのレビューは日付更新だけで終わる。
> **注記（2026-09-15, ADR-0068 監査時）**: launchd 登録は著者が 2026-09 に解除し `~/Library/LaunchAgents/…plist.disabled` になっている（cycle は手動 `/growth-fable`）。prompt 本文は `scripts/launchd/growth-fable-prompt.txt`（skill の references/ は撤去、6072dab）。再登録時は repo 版 plist（cwd = `~/MyAI_Lab/growth`）を copy する。

5. **worker は既存 skill / agent / session 機構から選び、model は Opus（build 層）に固定する。**
   Fable と Astra は判断層（settings.json の既定 model = fable）、worker は `Agent(model: "opus")` /
   `spawn.sh --model opus` / `claude --bg --model opus` のどれか（tier 分担は ADR-0043 と同じ。
   spawn.sh の `--model` はこの決定で追加、2026-09-08 著者指示「部員は Opus」）。新しい worker 種・
   agent 定義は作らない。公開・評判に関わる action は worker も Fable も実行せず草稿で止め、
   既存 gate を通す。
6. **harness-boundary の 6 問**（著者の要求「機構を足す前に harness-boundary test に通す」）:

| 機構 | 層 | モデルに任せられない理由 | 次世代で不要か | Recommendation |
|---|---|---|---|---|
| growth-astra / growth-fable SKILL.md | Skills（手続き記憶）+ Values（責任境界の file 所有権） | 役の分離と状態 file の契約は session を跨いで保存されない | 戦略/制御の分離を substrate が native に持てば Downward | Keep（失効条件を SKILL.md に記載） |
| `.growth/` 3 ファイル | Data / Memory | cycle 間の唯一の記憶。session memory は compaction で消える | 不要にならない（成果物そのもの） | Keep |
| `collect_snapshot.py` | Runtime（観測）| 「測定はモデルが再構成しない」— 決定論の要求 | GitHub 側が series API を出せば縮む | Keep、拡張は観測後 |
| `triage-tick.sh --prompt-file` | Runtime（timer 配線） | 発火時刻は session の外にしか置けない（ADR-0045） | Claude Code が cron-driven standing session を native に持てば Delete | Keep（seam 1 行） |
| 人間 gate | Values / Policies | 既存のものを参照するだけ。新設なし | — | Move（参照） |

7. **supersede candidate は NORTH_STAR.md の Constraints に書き、人間が決めるまで衝突する
   action を dispatch しない。** 本 ADR は personal-branding ADR-0003 D4 を上書きしない
   （他 repo の ADR は他 repo が持つ）。personal-branding 側には ADR-0004 を置き、採否は著者。

   > **注記（2026-09-08）**: 著者は同日 ADR-0004 を Accepted にし、層 scope も ADR-0004 D5 で確定
   > （authorship-strategy ADR-0022 に日付つき注記 e659139）。Astra review #2（aa93c47）が
   > North Star の Constraints を決定済みに差し替え、Fable cycle 1 を同日投入した。

## Review-when

- campaign window 終了（2026-12-07）: 次 campaign が無ければ 2 skill と tick seam を削除する
- Fable が NORTH_STAR.md を書き換えた / worker を忙しくするための dispatch をした実測 → file 境界
  を hook か packet must-not に降ろす（Decision 1 の前提「file 所有権で足りる」が偽）
- breakout 中に followers の日次粒度が要ると観測された → hub CI 拡張（Decision 3 の deferral 解除）
- substrate が observe → decide → dispatch → verify の standing controller を native に持った →
  Downward で溶かす
- 人間が ADR-0003 D4 の supersede を却下した → goal の数値化を外し、本 ADR の Context を書き直す

## Alternatives Considered

- **1 skill + mode 引数**（`/growth-loop astra|fable`）— 却下。所有権の境界が prompt 引数になり、
  同じ session が両役を演じて Astra の fresh-context 要件が消える。file 境界の方が検査可能
- **Workflow tool script を controller にする** — 却下。cycle の途中で人間の答え（publication GO、
  supersede の判断）が要り、Workflow は opt-in の in-process 実行で Remote Control から答えられない。
  Workflow は worker の並列（同一 setup 3 件以上）にだけ使う
- **experiment を `rfcs/` の store に置く** — 却下。experiment の語彙（proposed / active / killed /
  completed / scaled）は台帳の状態語彙（ADR-0050）と別物で、混ぜると task-stocktake が刈る対象に
  なる。著者の要求も単一 file
- **hub CI に followers / stars の日次 snapshot を今足す** — 未決（再訪条件: breakout 中の日次
  粒度の必要が EXPERIMENTS.md に観測されたとき）。今足すと公開 repo の CI 変更（人間 push）と
  README 更新を、必要が出る前に払う
- **`.growth/` を `~/.claude` に置く** — 却下。harness repo は control plane で、campaign 状態の
  commit が harness の履歴に混ざる。personal-branding の制約 ADR も自動で載らない
- **専用 worker agent 定義（growth-writer 等）** — 却下。既存 skill が各成果物の judge と gate を
  内蔵している（readme-writer の judge + 著者通読 GO 等）。新 agent はその gate を迂回する経路になる

## Consequences

- 制御系は 2 skill（約 320 行）+ collector（約 490 行、tests 付き）+ tick の seam 1 flag + template
  4 本。成長作業（記事・README・skill 公開）より薄い
- 人間 gate は全て既存の再利用で、新しい承認面が増えない。半面、公開 action の待ち時間は人間の
  応答速度で決まる（loop はそこで止まるのが正しい）
- followers series の粒度は collector の実行頻度（週 2 + 手動）。breakout の日次追跡には足りない
  可能性があり、その時点で hub CI 拡張を出す
- 10,000 / 90 日という goal は必要軌道が観測 slope と桁違いで、Astra は線形 plan でなく breakout の
  創出・検出・集中で thesis を組む必要がある。invalidation 条件を数値で置くのは Astra の責務
- personal-branding ADR-0003 D4 との衝突は人間が決めるまで残り、Fable は数値目標に依存する
  action を dispatch しない（campaign は goal の数値を持ちながら、数値を外へ出す action は待つ）。
  同日に ADR-0004 Accepted で解消（Decision 7 の注記）
- Astra の fresh-context 要件は review ごとに session spawn 1 回のコスト。14 日に 1 回なので許容

# harness-stocktake を外へ届ける campaign — 他人の harness で月 1 回回り続け、勧められ続ける状態まで

調査: [research/2026-11-01-stocktake-campaign.md](research/2026-11-01-stocktake-campaign.md)（外部 8 角度 + 手元の実測）。
出発点: [research/2026-11-01-stocktake-campaign-frame.md](research/2026-11-01-stocktake-campaign-frame.md)（widen-the-ask の出力、2026-11-01）。
前段の設計: [sunny-splashing-scroll.md](sunny-splashing-scroll.md)、[ADR-0097](../adr/0097-batch-stocktake-report-and-two-decisions.md)。
再利用する手順: personal-branding の skill `plugin-directory-submit`（directory 提出。初回にしか読まれない欄の一覧を持つ）、
routine `listing-pr-daily`（掲載 PR / issue を queue から 1 日 3 件、`~/.claude/scheduled-tasks/listing-pr-daily/SKILL.md`）、
`docs/research/listing-queue.md`（掲載 queue の正本）。

## Context

harness-stocktake は 2026-10-31 に著者の `~/.claude` で初回の全体実行を終えた（7 source・192 項目・非 Keep 74・判断 2 回・開始から
report まで約 30 分、承認から適用まで約 35 分）。著者はこれを「他人の harness で繰り返し回り、勧められ続ける状態」まで届けたい。
目指す方向は「入れてから驚くまで 3 分、6 か月後に外部の公開 repo 1,000 本で月 1 回回っている」。

調査（2026-11-01）と著者の指摘（plan 初稿への返答）が campaign の形を決めた事実:

1. **Anthropic が commodity の検査を native に持った。** `/doctor`（未使用 extension、CLAUDE.md の導出可能部分、2.1.205〜）、
   `/doctor prompt-audit`（古い path・command・矛盾する指示、2.1.283）、`/skill-doctor`（skill ごとの context cost と未発火、
   2.1.252〜）、公式 plugin `claude-md-management`（31.5 万 install）。report-and-confirm 型はここまで。**native に無いのは
   横断の判定（skills / rules / agents / hooks / ADR / assets の重複・失効条件・substrate 吸収）、hooks の配線とテスト、台帳と実物、
   項目間の衝突、1 回の承認での branch 適用**。Skills Janitor（Product Hunt 230 票）は native 吸収で maintenance mode に入った —
   「`/doctor` の上の層」以外の位置取りは失効する
2. **入れてもらえるが、使われない。** akc-cycle は 2026-07-15 に directory へ提出し、live になっている（調査 report の「無い」は
   marketplace.json だけを見た誤り）。2026-10-12 の portal Usage（30 日）: **install 268（266 account）、使っている account 3**
   （akc-cycle RFC-0001）。原因として既に分かっているのは、short description に「最初に打つコマンド」が無く、README の「"audit my
   skills" と頼めば動く」では skill が発火しないこと。v1.5.0 は reviewer 待ち。→ campaign の中心は「入れた直後の 3 分」で、
   掲載数ではない
3. **audit 系の launch は HN で 1〜4 点、「CLAUDE.md の書き方」は 450〜750 点。** 道具を売る投稿は効かず、実測を伴う技術記事
   （Knip は Smashing の記事 1 本で 2.2 万 dependents、Ruff は本人の投稿 4 点・翌日の他人の投稿 148 点）が効く
4. **「月 1 回」を人の意志で回している前例は無い。** 回り続けているのは自動化（Action / CI）だけ。Renovate は onboarding PR で
   「何が起きるか」を先に見せ、merge まで何も変えない — こちらの「1 枚の report → 1 回の承認」と同型
5. **directory の listing には初回提出でしか読まれない欄がある**（`icon` / `documentationUrl` / `supportUrl` / `author` /
   `keywords`。akc-cycle はこれらを空のまま提出し、portal からも直せなかった）。`name` は永続。提出の前に全部そろえる
   （skill `plugin-directory-submit` §1〜§4）
6. **GitHub Action の経路は公式に揃っている。** `anthropics/claude-code-action@v1`（v1.0.266）に "Run a skill" の recipe と cron の
   例があり、利用者本人の `CLAUDE_CODE_OAUTH_TOKEN`（Max の `claude setup-token`）で動く。Artifact は `-p` と Action で無効
   （Markdown が唯一の report 経路）。`--bare` が `-p` の既定になると subscription + plugin の経路は壊れる（失効条件）
7. **他人の repo に頼まれずに issue / PR を出す経路、招待制の呼びかけ、見知らぬ人の usability 募集は、どれもやらない。** GitHub は
   2026 年に PR / issue の受付を絞る設定を出し、Waterloo の研究者は手動 15 issue + 15 PR で spam 判定、Nesbitt は「automated
   audits は maintainer の有限な注意からの引き出し」と名指しした。著者の判断: 利用者がいない今の状態で招待や募集をするのは
   格好がつかない。**代わりに、公開 harness を手元に clone して read-only で回し、集計だけを公開する**（AUP §7: open access で
   公開する研究利用は許される。連絡はしない、repo 名は出さない）
8. **ECC は経路にしない。** `everything-claude-code`（29.4 万★）の `skill-stocktake` の写しが公開 repo に 1,776 件あるが、著者は
   ECC の有料化以降 PR を出していない。写しの数は「この種の skill が入る repo の母数」の参考にだけ使う
9. **掲載 PR は Claude が出す。** routine `listing-pr-daily` が queue（区分 A は承認済み扱い）から毎朝 3 件まで出し、行為ログに
   書く仕組みが動いている。著者の操作は、sign-in が要る web form（directory portal、hesreallyhim の issue form、Show HN、Marketplace
   の publish）と、公開物ごとの 1 回の承認に絞る

## 目指す状態と物差し

> **状態**: harness-stocktake が他人の harness で月 1 回回り、外の反応を拾って skill を直し、新しい実例を発信するループを、著者が
> merge の判断だけで回せる。

「回っている」の定義（利用者自身が自分の repo に置いた印だけを数える。同意の要らない計測）:

| 指標 | 取り方 | 意味 |
|---|---|---|
| **外部で月 1 回回る repo 数**（主） | code search `uses: shimo4228/harness-stocktake-action` を 1 日 1 query + Action repo の dependents | workflow ファイルを置いた = 本人の選択。public だけ数える |
| **install → 最初の実行** | directory の Usage tab（install 数・使っている account 数・component の使用回数） | akc-cycle の 268 → 3 を超えるか。これが「3 分」の成否 |
| 見知らぬ人の issue / PR / 言及 | `gh`、HN Algolia（URL 検索）、Bluesky `searchPosts`、F5Bot（Reddit）、Buffer の metrics、Dev.to API | 勧められているか |

桁違いの目標（6 か月で 1,000 本）は方向で、合否ではない。合否は段階ごとの観測ゲートで決め、最初の反証可能な節目を
**公開から 90 日で `uses:` 100 本、directory の「使っている account / install」が 10% 以上**に置く（Renovate は Marketplace 込みで
14 か月で 5,000 project）。

## 判定の原則（skill: `measurement-discipline`）

- ゲートは暦でなく観測数。各段階に n と到達見込み日を書き、n に届いたその日に判定する。cap（既定 14 日）を過ぎたら延長せず決める
- 判定の置き場所は frame の順: **現実に当てる** > **見ていない repo で予測を当てる** > **fresh な judge**。自己見直しは判定に使わない
- 著者の harness の 192 項目は n = 1。著者の驚きは測定器にしない。驚きは「非 Keep の件数」「fresh judge が単独で判断できると
  答えた項目数」「最初の項目が見えるまでの秒数」で測る

## Verdict（skill: `search-first` §3 — 手段ごと）

| 部品 | 判定 | 根拠 |
|---|---|---|
| 回り続ける形 | **Adopt** `anthropics/claude-code-action@v1`（composite action で包む） | "Run a skill" recipe と cron が公式。利用者本人の token。`--bare` 既定化が失効条件 |
| 承認の形 | **Adopt-part** Renovate の dashboard issue（1 枚の issue をその場で更新、checkbox = 承認）+ `claude/` 固定 branch の PR | 「report 1 枚・承認 1 回」と同型。issue を毎月増やさない |
| 配布の単位 | **Build** 単独 plugin repo `harness-stocktake`（7 source を同梱） | akc-cycle は AKC 全体の層で入口が広すぎる（install 268 → 使用 3）。directory は plugin folder 単位、skills.sh は plugin.json を読む。丸コピは著者の方針 |
| directory 提出 | **Adopt** skill `plugin-directory-submit`（personal-branding） | 初回にしか読まれない欄・validator で落ちた実例・portal の手順を既に持つ |
| 掲載 PR / issue | **Adopt** routine `listing-pr-daily` + `listing-queue.md` | 動いている。queue に行を足すだけ |
| 入れずに試す | **Build-small** repo 内の sample harness + sample report + `--dry-run`。server 側の「URL を貼る」版は**作らない** | SDK hosting は API key 課金で運営者負担、"pay on users' behalf" 条項が曖昧、abuse 対策が自前（stop 2・3） |
| 利用者の観察 | **Build-small** fresh `claude -p` の persona 3 体に README だけ渡して install → 実行させ、詰まる場所と秒数を取る（skill `persona-read-loop` の拡張）+ 公開 harness 20〜50 本の手元 dry-run | 見知らぬ人の募集はしない（著者）。人の観察は issue で来た人に限る |
| 動画・画像 | **Adopt** Remotion 4.0.539（Free License）+ OpenAI tts-1（45 秒 ≈ $0.01）+ scene 単位の字幕。terminal は charmbracelet/vhs | 1 project で video と still。2 次チャネル（成功した CLI 5 本中 3 本は demo 媒体なし） |
| 反応の収集 | **Adopt** `gh api`（traffic 14 日、`stargazers/history`、code search）+ HN Algolia + Bluesky `searchPosts` + Buffer MCP + Dev.to API + F5Bot。**Build** 150 行前後の収集 script 1 本 | Reddit API は承認制、X API は従量課金（課金は著者） |
| 利用の計測 | **Adopt** workflow 参照の code search + dependents + directory Usage tab + 利用者が自分で付ける badge。telemetry は**入れない** | Go は opt-out から opt-in に戻った。設定全体を読む skill の ping は Homebrew より重い依頼 |

## 代理で決めたこと（plan 承認で一緒に確認）

1. **経路 1（公開 harness をこちらから棚卸しする）は「手元で回して集計だけ公開する」形に限る。** 対象 repo を clone して read-only の
   `--dry-run` を回す（連絡しない、issue も PR も出さない）。公開するのは集計（source 別の非 Keep 率、native に拾われない項目の
   割合、harness の大きさと非 Keep 件数の関係）だけで、repo 名・owner 名は出さず、n < 10 のセルは伏せ、選定 query と tool の版を
   添える。「State of Claude Code Harness Hygiene 2026」として Zenodo に DOI（skill `release-doi`）。maintainer が自分の都合で
   来られるよう、同じ集計を出す手順（`--dry-run`）を plugin に同梱する（pull 型）
2. **外部の正しさを「他人の repo の台帳（`results.json` の `evaluated_at`）」で測らない。** 台帳は出力であって設定ではなく、個人の
   活動の時刻を漏らす beacon になる。しかも `evals/results.json` と名前が衝突する（code search 19 件中 17 件は skill-creator の eval
   出力）。代わりに上の表の指標を使う
3. **位置取りは「`/doctor` の上の層」。** README・記事・申請文は native が何を見るかを先に書き、こちらは横断判定・配線・台帳・衝突・
   branch 適用だけを主張する。`/skill-doctor -p` の出力を Phase 1 の入力として読む。「first」「only」は書かない（community に
   audit 系 48 本）
4. **公開 repo は 2 つ**: `harness-stocktake`（plugin。repo root が plugin、7 source 同梱、Markdown report が既定）と
   `harness-stocktake-action`（composite action。plugin を pin して呼ぶ）。akc-cycle は AKC 全体の層として残し、`harness-sync` の
   同期表に `harness-stocktake` を 1 行足す
5. **英語一次、日本語二次。** README・issue template・report の文面は英語。Zenn は技術記事（実測の記録）だけ、動画は YouTube URL
6. **動画は Stage 4 の中の 2 次チャネル。** 集計記事が出てから作る
7. **telemetry は入れない**
8. **著者の操作は sign-in が要る web form と公開物ごとの 1 回の承認だけに絞る。** `gh` で済むものは全部 Claude が実行する
9. **plan ファイル名**: plan mode が割り当てた `enumerated-petting-beaver.md` のまま

## 段階

各段階に「やること / 成果物 / 判定（現実に当てる方法）/ 著者が行うこと」。**実装はすべて Opus の build session へ dispatch する**
（著者の指示 2026-11-01、rule `planning.md` の三役）。この Fable session は判断役: Stage ごとの brief を書き、戻った成果物を観測
ゲートに当て、著者に渡す操作だけを並べる。

### Stage 0 — 前提を壊しにいく（公開前。すべて手元）

**やること**

1. **native との実機比較。** 著者の harness で `/doctor`、`/doctor prompt-audit`、`/skill-doctor -p` を回し、192 項目それぞれが
   native に拾われるか（拾われる / 部分 / 拾われない）を表にする。差別化の主張はこの表から書く
2. **project 対象の実行モード。** `harness-stocktake --project <repo-path>` — 対象は repo の `.claude/`（skills / agents /
   settings の hooks / rules）と `CLAUDE.md`・`docs/adr`。global は除外。worktree と branch はその repo に切る。report の既定は
   Markdown（`.notes/stocktake/<date>/report.md`、Artifact は desktop app で使えるときだけ）。`--dry-run`（report だけ、branch も
   worktree も作らない）を足す。各 source skill の `~/.claude` 前提の行を root 引数に置き換える（akc-cycle 側は既に
   `${CLAUDE_SKILL_DIR}` 化済み — その差分を取り込む）
3. **前提の検証 — 著者の 4 repo。** contemplative-agent（skill 11 / CLAUDE.md 184 行）、zenn-content（8 / agent 6 / 78 行）、
   paper-lab（6 / 5 / 20 行）、jev-research-pipeline（1 / 1 / 0 行）で project モードを回し、repo ごとに記録: 非 Keep 件数、source 別
   内訳、最初の項目が report に出るまでの秒数、report までの秒数、`total_cost_usd`、fresh judge（report だけを渡した `claude -p`、
   `--settings` で style と hooks を隔離）が「単独で判断できる」と答えた件数
4. **前提の検証 — 公開 harness 20 本。** code search（`path:.claude/skills filename:SKILL.md`、fork 除外、90 日以内に push、
   skill 5 本以上）から 20 repo を選び、clone して `--dry-run` を回す（連絡しない）。同じ項目を記録する。最初の 10 本で「驚きが出る
   条件」の見立て（例: skill 数 × CLAUDE.md 行数 × 最終更新からの月数）を書いてから、残り 10 本で当たるかを見る。他人の
   `.claude/settings.json` の hooks と `.mcp.json` は **cwd を repo の外の空 dir にし、`--restricted` と `--strict-mcp-config` で切って**
   走らせる（`-p` は trust dialog なしに hooks を実行する。`--bare` は API key だけを受け subscription の OAuth を受けないので使えない。
   実装は `skills/harness-stocktake/scripts/isolated-dry-run.sh`）
5. **3 分の設計。** 初回実行の items JSON と時刻から時間の内訳を再生する。source の実行順を「非 Keep が出る確率 ÷ 完了秒」の大きい順
   （24 run の実測で hooks → docs → agents → distill → skills → assets → rules。assets は非 Keep が多いが最も遅い source で、
   commit 44e05e3 で表を並べ替えた）にし、source が終わるたびに report に追記する。目標: 最初の非 Keep 項目が見える
   まで 3 分、report 全体 10 分

**成果物**: `docs/plans/research/<date>-doctor-comparison.md`（192 行の表）/ project モードと `--dry-run`（SKILL.md と source 7 本の
差分、tests）/ `docs/plans/research/<date>-premise-test.md`（24 repo の数値、見立てと的中、repo 名は著者の 4 本だけ出す）/ 実行順と
逐次 report の差分

**判定**: 驚きの事前定義 = **report から 10 分以内に、fresh judge が単独で判断できると答えた非 Keep 項目が 5 件以上**。公開 20 本の
うち半数以上で成立し、見立てが残り 10 本で当たれば次へ。成立が半数未満なら相手を大きい harness（skill 10 本以上、plugin 10 本以上）
に絞り、README の最初の行で対象を言う。native 比較で拾われない項目が非 Keep の半分未満なら、位置取りを「`/doctor` の後に回す」へ
下げる。

**著者**: なし。

### Stage 1 — 汎用 plugin と「入れてから 3 分」

**前提**: git-target 修理 session の決着 → `harness-sync` と akc-cycle のリリース（著者の既定順序）。

**やること**

1. 公開 repo `shimo4228/harness-stocktake`（MIT。`gh repo create` は Claude、最初は private）。構成: repo root に
   `.claude-plugin/plugin.json` + `marketplace.json` / `skills/harness-stocktake` + 7 source / `README.md`（英語）/ `LICENSE` /
   `examples/`（sample harness と sample report）/ `CHANGELOG.md`。harness 固有の依存（Herdr、Slack、launchd、`triage-tick.sh`、
   ADR 番号）は外す。hooks は同梱しない。`package.json` / lockfile / 環境変数の読み取りを plugin folder に置かない
   （`plugin-directory-submit` §4 の落ちた実例）
2. **初回提出でしか読まれない欄を先にそろえる**（§1）: `name: harness-stocktake`（永続）、`displayName`、`description` は 1 行で
   「何をするか + 最初に打つ `/harness-stocktake:harness-stocktake --dry-run`」、`documentationUrl`（README）、`supportUrl`（issues）、
   `author`、`keywords`、`icon`。icon は §3 の手順（`/codex:rescue` で 3〜4 案 → 著者が 1 案 → `sips -z 1024 1024` → 32px で形を
   確認 → `"icon": "./.claude-plugin/icon.png"`）。`claude plugin validate --strict` を通す
3. install の一行: `claude plugin install harness-stocktake --marketplace shimo4228/harness-stocktake`。README の最初の 3 行に install、
   `--dry-run`、「`/doctor` の後に残るものを見る」を置く。README は「何を読み、何を書き、何も送らない」を 1 節で書く
4. 計測 script `bench/time-to-first-item.sh`: 一時 `CLAUDE_CONFIG_DIR` + `claude -p "/harness-stocktake:harness-stocktake --dry-run"
   --output-format json` で、最初の項目・report 完成・`total_cost_usd` を記録。sample harness で毎 release 回す
5. **persona による install 観察**: fresh `claude -p` の persona 3 体（「ECC を入れたままの人」「CLAUDE.md が 200 行の人」
   「`/doctor` で足りると思っている人」）に README だけを渡し、一時 HOME で install → 実行させ、詰まった場所・秒数・最初の感想を
   取る（`persona-read-loop` の形。judge の点数で登らない）。README と sample report は `readme-writer`（readme-judge）にも通す
6. harness-sync の同期表に `harness-stocktake` repo を足し、`origin: shimo4228` の 8 skill を一方向で写す
7. directory への提出準備（skill `plugin-directory-submit` §2〜§6）: Data handling 4 問の下書き、Source の 3 値、README の開示節。
   portal の操作は著者（§6 の表、15 分程度）

**成果物**: 公開 repo / bench の数値 / persona 3 体の記録 / readme-judge の verdict / 提出用の値一式

**判定**: persona 3 体全員が README だけで report に到達し、最初の項目まで中央値 3 分以内、sample harness の `--dry-run` で
`total_cost_usd` が記録される。届かなければ README の最初の 10 行と `--dry-run` の出力を直して再試行（最大 2 回）。人の観察は
issue で来た人に限り、来たら `rfcs/` に記録する。

**著者**: icon の 1 案選び / repo の public 化の OK / directory portal の操作（提出）。

### Stage 2 — 回り続ける形（GitHub Action）

**やること**

1. 公開 repo `shimo4228/harness-stocktake-action`（composite action、`action.yml` を repo root に 1 つ）。中身は
   `anthropics/claude-code-action@v1` を `plugin_marketplaces: shimo4228/harness-stocktake`・`plugins: harness-stocktake@harness-stocktake`
   ・`prompt: "/harness-stocktake:harness-stocktake --project ."` で呼ぶ。plugin の版を `ref` で pin。`--bare` は付けない
2. 利用者の workflow（README の雛形）: `on: schedule: cron: "0 7 1 * *"` + `workflow_dispatch` + `pull_request: paths: ['.claude/**',
   'CLAUDE.md']`。`permissions: contents: write, issues: write, pull-requests: write, id-token: write`。認証は利用者本人の
   `CLAUDE_CODE_OAUTH_TOKEN` か `ANTHROPIC_API_KEY`（両方を README に書く。著者の token は使わない・集めない）
3. report の出し方: `display_report: true`（Step Summary）+ **tracked issue 1 枚**（title 固定 "Harness stocktake"、本文をその場で
   更新、項目ごとの checkbox = 承認）。承認済みの項目は固定 branch `claude/stocktake` に適用して PR 1 本（既存 PR があれば更新）。
   「1 回の承認」は PR の merge
4. 60 日の inactivity で schedule が止まる仕様への対処: README に `workflow_dispatch` を書き、tracked issue に「前回の実行日」を出す
5. smoke test: 捨て repo で 1 時間。sibling SKILL.md を読む plugin が Action の中で install されるか、`-p` で subagent が走り切るか、
   OAuth token で動くか、cost と時間
6. 著者の 4 repo に workflow を置く（Claude が PR）。secret は著者が 1 行:
   `claude setup-token | gh secret set CLAUDE_CODE_OAUTH_TOKEN -R shimo4228/<repo>`（Claude が repo ごとの行を渡す）
7. GitHub Marketplace への掲載: `gh release create` は Claude、Marketplace の publish checkbox は web（著者）

**成果物**: Action repo / 雛形 workflow / smoke test の記録（cost・時間）/ Marketplace 掲載

**判定**: **著者の 4 repo で run 8 回、silent failure 0**（失敗は issue に出る）。Stage 3 以降と並行。

**著者**: secret の 1 行 × 4 / Marketplace の publish。

### Stage 3 — 公開 harness の実測と「State of Claude Code Harness Hygiene 2026」

**やること**

1. Stage 0 の 20 本を **50 本**に広げる（同じ選定 query。clone は手元、連絡なし）。plugin 版で `--dry-run` を回し、同じ項目を記録
2. 集計: source 別の非 Keep 率、native（Stage 0 の比較表の分類）に拾われない項目の割合、harness の大きさと非 Keep 件数の関係、
   見立ての的中率。repo 名なし、n < 10 のセルは伏せる、query・版・日付を添える
3. 技術記事 1 本（英: Dev.to、日: Zenn。skill `writing-ecosystem` の手順）: 「`/doctor` の後に何が残るか — 公開 harness 50 本の
   実測」。著者の harness の before / after（192 項目 → 2 回の判断）を 1 本の物語として添える。一つの数字に絞る
4. 集計のデータ（CSV）と記事の英語版を plugin repo の `docs/state-of-2026/` に置き、GitHub release → Zenodo の DOI（skill
   `release-doi`。webhook は Claude が設定、release は著者の OK 1 回）
5. 反応の収集 script（Stage 5 の 1）をここで動かし始める

**成果物**: 50 本の集計 / 記事（英・日）/ DOI 付きのデータ / 画像 1 枚（Remotion still）

**判定**: 50 本の集計で Stage 0 の見立てが的中率 70% 以上なら、記事の「対象」を見立てどおりに書く。70% 未満なら対象を書かず
分布だけを出す。記事は `persona-read-loop` 3 round と `readme-judge`（記事版は writing-ecosystem の reviewer）を通す。

**著者**: 記事 2 本の公開の OK（1 回ずつ）/ release の OK。

### Stage 4 — 公開

**順序**（Claude が出すものは `listing-queue.md` に行を足して routine に任せる。著者の行為は web form だけ）:

| # | 場 | 誰が・どう | いつ |
|---|---|---|---|
| 1 | 公式 plugin directory | Claude が `plugin-directory-submit` で値をそろえる → **著者が portal で提出**（約 15 分）。先に akc-cycle v1.5.0 の状態と、10-04 の harness-scope の状態を portal で見る | Stage 1 完了直後（審査期間は非公開なので早く） |
| 2 | karanb192/awesome-claude-skills → Meta Skills | queue に行（区分 A）。routine が PR | Stage 1 の public 化翌日 |
| 3 | Chat2AnyLLM/awesome-repo-configs | queue に行。routine が JSON の PR + test | 2 と同日 |
| 4 | walkinglabs/awesome-harness-engineering | queue に行。開示 + 記事 URL を添える | Stage 3 の記事公開後 |
| 5 | hesreallyhim/awesome-claude-code → Linting / Configuration | `manual`（web の issue form を人が出す規約）。Claude が本文を用意 | public 化 + 14 日 |
| 6 | VoltAgent/awesome-agent-skills | queue に `hold: 外部の利用者が出てから` | Stage 5 で `uses:` 10 本 |
| 7 | skills.sh / claudemarketplaces.com | 申請なし | — |
| 8 | Changelog News | queue に行（self-submit form。Claude が `gh` で出せない形なら `manual`） | 記事と同時 |
| 9 | Show HN | Claude が題と本文を用意。投稿は web（著者、または built-in browser で著者の OK 1 回）。条件: sign-up なしで試せる（sample harness + `--dry-run`）。期待値 1〜4 点 — 外れても計画は変えない | 記事と同週、12:00–15:00 UTC |
| 10 | X / Bluesky | skill `social-post` で Buffer に下書き → 著者が Buffer で承認。記事の告知 1 回 + 画像 1 枚 | 記事と同日 |
| 11 | 動画（2 次） | Remotion + tts-1、45 秒以内、scene 字幕。README は MP4 ≤ 10 MB、Zenn は YouTube URL（upload は著者） | 10 の後 |

**成果物**: 各掲載の URL と日付（行為ログ Acts 節に routine が書く。public-records に従う）

**判定**: 公開から **90 日で `uses:` 100 本、directory の「使っている account / install」10% 以上**（1 日 1 query の記録と portal の
Usage）。30 日時点で `uses:` 10 本未満なら、経路より「3 分」の中身（Stage 0 の再計測）を疑う。星と HN の点数は記録するが判定に
使わない。

**著者**: 表の 1・5・9・10・11 の web 操作。

### Stage 5 — ループ（反応 → `rfcs/` → task-triage → 著者の merge）

**やること**

1. `scripts/campaign-monitor.py`（150 行前後、launchd 日次）: `gh api repos/.../traffic/{views,clones,popular/referrers}`（14 日しか
   残らないので毎日 `.notes/campaign/traffic.jsonl` に追記）/ `stargazers/history` / code search `uses: shimo4228/harness-stocktake-action`
   （1 query）/ HN Algolia `search_by_date?query=<repo URL>&restrictSearchableAttributes=url` / Bluesky `searchPosts?url=`（app
   password）/ Dev.to `analytics` / F5Bot の RSS（Reddit）。週 1 で Buffer MCP `get_aggregated_post_metrics`。directory の Usage は
   CSV を著者が月 1 回落とす（portal。それが面倒なら「使っている account」の数字 1 つを Slack に 1 行）。**429 / 403 は停止して
   報告**（backoff しない）
2. 反応のうち「skill への指摘」（issue、言及の中の主張）は skill: `rfc-writer` で `rfcs/` に起票（公開可能な書き方、原文は
   `.notes/`）。task-triage が拾い、build session が直し、著者が merge する
3. 月次: 集計を `rfcs/` の campaign エントリに 1 行（`uses:` 本数、directory install / 使用 account、言及数、起票数）。
   personal-branding の scorecard にも同じ数字
4. 「State of」は半年ごとに同じ query で再集計し、Zenodo の新 version にする

**成果物**: monitor script + launchd plist / `rfcs/` の campaign エントリ / 月次の 1 行

**判定**: ループが回っている = **外部起点の `rfcs/` エントリが月 3 件以上、うち 1 件以上が merge まで行く**を 2 か月続ける。
0 件の月が 2 回続いたら Stage 3〜4 を見直す。

**著者**: merge / 課金が要る収集（X API）の可否 / directory Usage の月 1 回。

## 順序と依存

```
git-target 修理の決着 ──► harness-sync + akc-cycle release ──► Stage 1 ──► Stage 2 ─┐
Stage 0（今すぐ、手元）──────────────────────────────────────────────┘          ├► Stage 4 ──► Stage 5（Stage 3 から並行）
                                                           Stage 0 の 20 本 ──► Stage 3 ─┘
```

- Stage 0 は修理の決着を待たない。Stage 3 の 50 本の dry-run も plugin 版を待たずに harness 版で始められる（集計は plugin 版で
  取り直す）
- Stage 4 の表 1（directory 提出）は Stage 1 直後

## 失効条件（campaign 全体。見つけたら止まって報告）

- `/doctor` 系が横断の判定か branch 適用を native に持った（`code.claude.com/docs/en/commands` の `/doctor` 行と release notes を
  release ごとに見る） → 位置取りを「`/doctor` の後工程」へ縮めるか、Skills Janitor と同じく maintenance mode を宣言する
- `--bare` が `-p` の既定になった、または subscription token の CI 利用の方針が変わった（support 記事は 2026 年に 1 度反転した）
  → Action の認証と flag を直す。直せなければ Action 経路を API key 専用にする
- Stage 0 の前提検証が落ちた（公開 20 本の半数で驚きが出ない） → 相手を大きい harness に絞る
- 公開後 30 日で `uses:` 10 本未満、または directory の「使っている / install」が akc-cycle 並み（1%） → 3 分の中身を再計測
- GitHub で 403 / 429、spam 判定の兆候（PR の自動 close、制限の通知）、maintainer の咎めるコメント → 外部への書き込みを全部止めて報告
  （`listing-pr-daily` の停止条件と同じ）
- Remotion 5.0 の license 変更 / 関与者が 4 人以上 → 動画の経路を見直す
- 6 か月の地平: 2027-05-01。「状態の委任」が成立していなければ campaign を閉じて学びを AKC に書く

## 著者に残る操作（rule `boundary.md` の「人間に渡す」のうち、`gh` で代替できないもの）

plan の承認 / icon の 1 案選び / directory portal の提出（Stage 1）と Usage の月 1 回 / `claude setup-token | gh secret set …` ×
4 repo / Marketplace の publish checkbox / hesreallyhim の issue form / Show HN の投稿（または built-in browser で OK 1 回）/
Buffer の承認 / YouTube の upload / 記事 2 本と release の OK（各 1 回）/ 課金（X API）の可否。
それ以外（repo 作成、PR、release、queue の行、記事の執筆と push の準備、Zenodo webhook、monitor）は Claude が行う。

## 記録

- 承認した plan はこのファイルを実装の最初の commit に単独で入れる（`docs(plan): enumerated-petting-beaver`）
- ADR 1 本（skill: `adr-writer`）: 「campaign の位置取りと 2 つの留保の判断」— 経路 1 は手元で回して集計だけ公開、台帳を数えない、
  `/doctor` の上の層、telemetry なし、招待・募集・ECC をしない理由。Review-when に上の失効条件を写す
- `rfcs/` に campaign のエントリ 1 本（state: accepted、各 Stage の観測ゲートと月次の 1 行）。Stage ごとの作業は task-triage が
  build session に dispatch する
- `listing-queue.md` の行と行為ログは routine の規約どおり（public-records）
- 調査 report の `## Sources`（URL 一覧）は plan 承認後に researcher が追記する（plan mode 中は書けなかった）

## Verification（end to end）

- Stage 0: `/doctor` 比較表が 192 行 / project モードと `--dry-run` が 24 repo で走り `.notes/stocktake/<date>/report.md` を書く /
  premise-test の report に数値と「見立て → 的中」がある / bench で最初の項目までの秒数が出る。`.claude/verify.sh` が通る
- Stage 1: 一時 `CLAUDE_CONFIG_DIR` で `claude plugin install … --marketplace shimo4228/harness-stocktake` → `claude -p
  "/harness-stocktake:harness-stocktake --dry-run"` が sample harness で report を出す / `claude plugin validate --strict` が通る /
  plugin.json に §1 の欄が全部ある / readme-judge が Publishable / persona 3 体の記録が閾値と並ぶ
- Stage 2: 捨て repo の Action run が tracked issue と PR を作る / 著者の 4 repo で run 8 回・失敗 0
- Stage 3〜5: 集計 CSV に repo 名が無く n < 10 のセルが伏せてある / `rfcs/` の campaign エントリに観測数と到達日が毎月 1 行ずつ
  増える / monitor の jsonl が日次で増える / 429 で止まった記録が無い

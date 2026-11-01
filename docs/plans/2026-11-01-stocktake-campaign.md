kind: external
# harness-stocktake（Claude Code の harness 全体を 1 枚の report・1 回の承認・branch 適用で棚卸しする skill）を、他人の harness で月 1 回回り続け、勧められ続ける状態に届けるには、2026-11-01 時点で外に何があるか

統合元: `~/.cache/claude-research-notes/2026-11-01-stocktake-campaign/` の 9 ファイル（awesome-lists / plugin-directory / competitors / devtool-activation / github-action / video-pipeline / ethics-unsolicited / reaction-monitor / local-evidence）。notes に無い主張は足していない。as-of は特記がなければ 2026-11-01。
読み方の注記: notes の「full」は WebFetch の要約モデルに全文を通した意味で、生 HTML の逐語読みではない。SNIPPET は検索結果の要約のみ。

## Scope searched

| 角度 | notes | 呼び出し規模 | 主な一次資料 | 見つからなかった範囲 |
|---|---|---|---|---|
| 1 awesome list / catalog | awesome-lists | 約 27 | 各 list の CONTRIBUTING.md（raw.githubusercontent.com）、vercel-labs/skills docs | list への掲載が生んだ流入の実測値、各 list の最終 merge 日（commit 日が render されなかった）、2026-10-04 以降の新 list |
| 2 公式 directory と `/doctor` 系 | plugin-directory（+ competitors A） | docs 約 20 ページ + 検索 | claude.com/docs/plugins/*、code.claude.com/docs/en/*、support.claude.com Policy 13145358、anthropics/claude-plugins-* | 公式 Discord / newsletter / spotlight、review SLA、featured の申請手段 |
| 3 競合と需要 | competitors | 約 30 | 各 repo README、HN Algolia API、Anthropic docs、v2.1.283 release page | Reddit / X の反応数、各 repo の最終 commit 日、npm download 数、Zenn/Qiita 原典の like 数 |
| 4 dev tool の広がり方と activation | devtool-activation | 約 33 | Changelog #289、Renovate docs、Astral blog、HN Algolia、arXiv 2511.04453、telemetry docs | 「1,000 repo に達するまでの時間」の公表値、Lighthouse CI / Danger / giscus / Biome 等の履歴、Zenn の trending algorithm |
| 5 GitHub Action と「入れずに試す」 | github-action | 22 | code.claude.com の github-actions / headless / authentication / legal / artifacts / agent-sdk/hosting、claude-code-action の action.yml、GitHub docs | claude-code-base-action の現況、Socket/Snyk/deps.dev 型の paste-a-URL 先例、Dependabot/pre-commit.ci 等の idempotency |
| 6 動画・画像 pipeline | video-pipeline | 約 32 | context7 の Remotion v4.0.539 docs、npm registry、Remotion LICENSE.md、OpenAI/ElevenLabs 価格ページ、GitHub docs | Apple Silicon での Remotion 実測、X / Bluesky / YouTube の公式数値、Google Cloud TTS / Apple `say` |
| 7 倫理と platform rule | ethics-unsolicited | 約 26 | GitHub AUP / ToS / rate-limit docs、arXiv 論文、The Register、Nesbitt の essay | Allstar の opt-in 受容、ADOPTERS.md の先例、Zenodo の派生データ policy、Gold & Krinke の全文 |
| 8 反応監視 API | reaction-monitor | 約 30 | GitHub docs / changelog、Buffer developers、Forem API、F5Bot FAQ、Bluesky lexicon（mirror） | Reddit / X の公式ページ（403 / 402）、Syften / Google Alerts、Renovate 等の adoption 数の算出法 |

## Found

### 1. awesome list と auto-index catalog（awesome-lists.md、2026-11-01 の repo ページ読み + CONTRIBUTING.md 全文）

先に押さえる 5 点:
- 「~3% acceptance」（lead の 10-04 survey）は**未検証**。ecosyste.ms が 8 issues / 19 PRs を示し、repo ページの 1.1k open issues と合わない（tracker が古い）。受理率の統計は見つからなかった。
- 掲載の流入を実測した公開数値は見つからない（検索 2 回）。逸話のみ: 「良く置かれた掲載で 50–200 stars/月」という出所不明の dev.to 推計、AI newsletter が最大の star 源だった Skyvern の自己申告、newsletter + tweet で約 1,200 stars の spike。
- 「Meta Skills / skill-audit」という category は hesreallyhim には**無い**。適合先は Linting または Configuration。
- 近い先行者は既に掲載済み。hesreallyhim の Linting に agnix、Ctxlint、Schliff、Upkeep、BlockWatch。Multi-Purpose に TÂCHES（"skill-auditor"）。
- danshari と skillreaper は hesreallyhim に載っていない（読んだ約 200k / 242k 字の範囲）。

| list | 規模（2026-11-01） | 経路と条件（CONTRIBUTING.md 全文） | harness-stocktake への示唆 |
|---|---|---|---|
| hesreallyhim/awesome-claude-code | 57.0k★、1.1k open issues | Web UI の issue form のみ（gh CLI は block、PR は一時制限の恐れ）。bot が機械検証。推薦文は人間が作る（著者本人の申請で満たす）。初 commit から 14 日以上 + その後の commit、または 100★ 以上。満たさないと auto-close。自己宣伝の開示規則は無い。説明は 1 行・宣伝調なし・emoji なし | 適格性は容易。リスクは「前 list と重なるものは保留して少しずつ再追加」という holdback と、Linting の先行者 |
| karanb192/awesome-claude-skills | 580★（小さい） | 1 skill 1 PR。有効な SKILL.md、直近 6 か月の commit、public source、security review。star 数は bonus。年齢制限なし。表の 1 行（description < 150 字、alphabetical） | **Meta Skills**（12 番目の最終 category）に danshari-skill（18 件中 3 番目）と reap/skillreaper（7 番目）が既に居る。障壁は最低で category も既製。reach は小さい |
| walkinglabs/awesome-harness-engineering | 4.6k★、61 open PRs（lead の 10-04 時点は 35） | 箇条書き 1 行 + 「harness engineering として何が重要か」。**開示が必須**: 独立開発者は自作を出せるが PR で関係を開示、宣伝 link / badge / 販売 page は禁止。一次資料と技術的な書き込みを好む | 名前が "harness"。"Specs, Agent Files & Workflow Design" か "Constraints" に収まる。backlog が膨らみ merge 遅延は不明。ツール紹介でなく初回実行の report のような技術記事が向く |
| VoltAgent/awesome-agent-skills | 36.7k★、24 open PRs | PR title "Add skill: author/skill-name"、10 語以内、author 接頭辞。**"Brand new skills that were just created are not accepted"**、実利用を求める。数値基準は無い | 2 番目に大きい現実的な標的だが、先に利用者と star が要る。skillreaper が載っていると自称するが list 側の entry は未確認（読んだのは先頭 100k 字） |
| ComposioHQ/awesome-claude-skills | 78.4k★、1.7k PRs | vendor list（UTM link、CTA）。audit 系 entry 無し。ページに "Only collaborators can create PRs" と CONTRIBUTING の PR 経路が併存（未解決） | 待ち行列が極端に長く期待値は低い |
| travisvn/awesome-claude-skills | 15.7k★ | "Last Updated" badge は 2026-02、最終の日付付き更新は 2025-11 | 実質停止。skip |
| Chat2AnyLLM/awesome-repo-configs | 7★ | JSON を編集（CONTRIBUTING 未読） | 機械 catalog。reach 不明で低い |

auto-index catalog:
- **skills.sh**（vercel-labs/skills の docs / FAQ を読んだ）: 提出手続きは無い。誰かが `npx skills add <owner/repo>` を走らせたときの匿名 telemetry で自動掲載され、順位は install 数。つまり**実際の install が先**で、掲載自体は最初の install を生まない。SKILL.md + README を持つ public repo が要件。frontmatter の YAML エラー（description 内の未引用の colon など）、root の SKILL.md が nested skill を隠す構成は silent に skip される。`.claude-plugin/marketplace.json` / `plugin.json` に載る skill は発見される。akc-cycle は両方を既に持つので `npx skills add shimo4228/akc-cycle` で同梱 skill が列挙されるはず（`disable-model-invocation: true` の skill の扱いは docs に記述なし）。規模は「All Time 908,452」（news.creeta.com 2026-07-08、第三者）。
- **claudemarketplaces.com**（About ページを読んだ）: crawler が skills.sh / GitHub / MCP registry を巡回。skill は検索需要を示す必要があり、editor が新規・境界例を review。Submit link あり（仕組みは不明）。**ECC の `skill-stocktake` のページが既にある**（claudemarketplaces.com/skills/affaan-m/everything-claude-code/skill-stocktake）。
- **SkillsMP**: 第三者 blog のみ（snippet）。2 ★以上 + open licence。公式 docs 未確認。
- audit 系 skill は多数が各 aggregator に出ている（skill-review、skill-audit、skill-doctor、skills-gc、Skills Janitor、cc-audit、claude-checkup、clauditor、ECC skill-stocktake など。いずれも snippet）。**category は混んでいる**。差別化軸は「whole harness + 1 report + 1 approval + branch 適用」。

danshari / skillreaper の見え方:
- skillreaper: 62★、216 commits。plugin marketplace / Homebrew / npm / `go install` で入る。掲載は awesome-go（Go 製のため stocktake には移せない）、awesome-agent-skills、karanb192。Show HN / Reddit の thread は見つからなかった（HN が駆動したとは仮定しない）。
- danshari-skill: 1★、0 fork、11 commits。それでも karanb192 の Meta Skills 3 番目に居る。**1★ でも karanb192 の gate は通る**。
- 流入測定: GitHub Insights の Traffic は直近 14 日のみで、定期保存が要る。lead の claude-harness の 473 clones / 400 unique（14 日）は crawler と整合する。
- list の成長自体は速い（awesome-claude-code は 30 日で約 4.1k★、ある tracker の 46.9k 時点 → 今は 57.0k）。entry ごとの流入データは無い。

### 2. 公式 plugin directory と Anthropic 自身の `/doctor` 系（plugin-directory.md、competitors.md A、docs 全文）

**2a. 提出・審査・表示**
- 経路: claude.ai/directory/manage → Submit new → "Plugin bundle"。Pro 以上の plan が要る（Free は不可）。source は GitHub repo（公開前までは private 可）。1 plugin folder 1 提出、10 提出 / org / 24h。最初に出した org が所有。旧 Console form は「no longer supported」で、10-04 の提出がそれ経由なら移行（directory@anthropic.com か withdraw + 再提出）が要る可能性がある。
- 審査: 全 version に自動検証 + security scan、新規 listing は人間が review。**review time は固定されない**（SLA 数値なし）。状態: Draft / Scanning / Needs changes / In review / Approved / Published / Not live yet / Delisted / Withdrawn。Approved は install 可能と同義でなく、Published のみ。
- 配置・"Anthropic verified" badge に**申請手段は無く**、審査で Anthropic が決める。featured tier の doc も無い。claude.com/marketplace/plugins は 528 plugins（page fetch では install 数も featured 欄も見えない。anthropic-marketplaces doc は「install 数を表示し、一部を Anthropic verified とする」と書く — 矛盾は Contradictions）。
- 公式 marketplace（claude-plugins-official）: marketplace.json は約 315 件（lead の 10-04 の 315 と同数 = 4 週間で増えていない。数え方は概算）。stats JSON は 324 plugins。**akc-cycle / harness-scope / harness-stocktake は無い**。config audit 用の category も無い（security / design / development / productivity / database / monitoring / automation / deployment / testing など）。
- community marketplace（claude-plugins-community、2026-08-26 頃開設、nightly sync、手動で `marketplace add` が必要、auto-update は既定 OFF）: lead の全量取得で **2,283 plugins**、akc-cycle / harness-scope / harness-stocktake は**無い**。一方で agnix、agent-smith、約 48 件の audit / doctor / lint / health 名の plugin（claude-md-optimizer、skill-doctor、repo-doctor、neko-harness-doctor など）は在る。→ 10-04 の提出は**どこにも現れていない**。

**2b. 審査基準のうち stocktake に効くもの**（pre-submission-checklist 全文）
- block: plugin.json 無し（skills/ だけの folder は「Claude Code only」注記付きで通る）、README 40 語未満、LICENSE 無し、npx/uvx の unpin、credential、symlink / submodule / LFS、非 ASCII 名など。
- 人間 review に回す（Policy hold、拒否ではない）: 256 KiB 超の file、512 file 超、png/jpg/gif/webp/font 以外の binary、validator が追えない script（非 shell、他 file を呼ぶ shell、`${CLAUDE_PLUGIN_ROOT}` 以外の shell 変数、command substitution）。plugin が repo の subfolder にあるときに効く。
- security scan は「undisclosed な送信・隠れた実行・**Claude の permission 設定の変更**」を探す。README は plugin が実行・送信・取得する全てを書く必要がある。「SKILL.md が Claude に実行を指示するだけの script」は静的検査の対象外。hook と skill 内の `!` 行は対象。
- 最大の不明点: **`~/.claude/settings.json` / rules / hooks を編集する skill が「permission 設定の変更」として flag されるか**は docs から分からない。適用が仕事の道具には最大リスク。launchd plist は「skill 外の非 text file で plugin 外に書く」ので Policy hold の可能性（未試験）。
- Policy（support.claude.com/13145358、"Updated this week" で日付なし）: 1G は会話内容の永続保存・Claude memory / chat history の取得を禁じる。auto-memory を読む audit は読み方次第で触れうる（notes の判断であって明記ではない）。2F は外部から動的に振る舞い指示を取得することを禁じる。
- 配信: Skills は Chat / Cowork / Claude Code に載る。hooks と agents は Chat で無視。`bin/` は Claude Code のみ（claude.ai / Cowork には「install できない」= plugin ごと拒否）。
- 計測: directory 掲載 plugin のみ Usage tab（install、version、skill の実行回数、error 率）。self-hosted marketplace に計測は無い。`claude_code.plugin_installed` は org 単位の telemetry で作者には来ない。→ **Anthropic のデータで「毎月 1,000 repo」は測れない**（directory 掲載しない限り）。
- 同梱の install: `claude plugin install <plugin> --marketplace owner/repo`（shell、v2.1.292+）が 1 行で入る。auto-update は公式 marketplace が既定 ON、community / 第三者は既定 OFF。

**2c. Anthropic が既に出している config hygiene**（docs 全文 + release page）
- `/doctor`: installation、settings、未使用 extension、同一 dir の重複 subagent 名、checked-in CLAUDE.md の「コードから導ける内容」を診断し修正案を出す。報告してから確認し、適用する。v2.1.205（2026-07-08）で setup checkup 化、v2.1.206 で CLAUDE.md trim 提案（implicator.ai）。
- `/doctor prompt-audit`（v2.1.283、2026-09-25、一次: github.com/anthropics/claude-code/releases/tag/v2.1.283）: CLAUDE.md / skills / agents / commands の「古い model 向けの書き方」、古い path / command、矛盾する指示を検出。第三者評は "a smoke detector, not a building inspector"（dev.to/piekwerk、2026-09-26）。
- `/skill-doctor`（v2.1.252+ が最低 version、第三者は 2.1.261 / 2026-09-04 出荷と報じる）: skill ごとの context cost と起動回数、未使用の flag。報告のみ、適用しない。`/plugin` の "Not used recently"（14 日・10 session 以上）、`claude plugin details`、`/context`、`/usage` も在る。
- 公式 plugin: claude-md-management（315,197 installs）、claude-code-setup（224,255）、hookify（64,119）、skill-creator（430,796）。いずれも skills / rules / agents / hooks の冗長を監査して適用する物ではない。
- docs で見つからなかった領域（notes の整理）: skills + rules + agents + hooks + ADR を横断する verdict report、branch 適用、月次 cadence、git 履歴付きの retire。ただし「docs で見えなかった」ことで、`/doctor` の全 check は走らせて比べていない。**この隙間は狭まりつつある**。失効条件は、各 release で commands page の `/doctor` 節を再確認すること。
- 作者側の差別化候補（競合 note より）: hooks の配線 + テスト、台帳と実物の差、ADR / README の drift、skill / rule / agent を跨ぐ重複、「substrate が吸収した」verdict と失効条件、7 source を 1 回の承認で branch 適用、Keep / Improve / Retire の分類。
- Anthropic の姿勢: Thariq Shihipar（2026-07-24）が system prompt の 80% 以上を Opus 5 / Fable 5 向けに削除し、CLAUDE.md / skills が "overconstraining" と述べた（implicator.ai 経由、Anthropic の評価は未公開）。古い harness に古い記述が溜まっているという前提を支える。
- 需要の薄い証拠: anthropics/claude-code #29971「Context Bloat」（2026-03-02 起票、stale で 2026-05-03 close、7 thumbs-up、職員の返信なし）。「config を片付けて」という高 upvote の要望は 1 回の検索では無かった（網羅ではない）。

**2d. 配布・scheduling の機構**
- **plugin は scheduled / cron routine を宣言できない**。選択肢: cloud scheduled tasks（Pro 以上、research preview、repo を fresh clone し `claude/` 接頭辞 branch に push、最短 1 時間、**local の ~/.claude には触れない**が repo 内の `.claude/` + CLAUDE.md + skills の監査と branch 作成はできる）、Desktop scheduled tasks（local file、machine 起動中）、`/loop` / CronCreate（session 内のみ、recurring は 7 日で失効）、GitHub Actions の `schedule`（角度 5）。
- **`disable-model-invocation: true` の skill は session-scoped な scheduled task が skill を prompt として起動しても実行されず、plain text として届く**（skills page）。cloud / Desktop task がこの flag を honor するかは不明。月次の plist なし経路には flag を外すか、手順を prompt に書く必要がある。
- Artifact tool は plugin / directory docs に記載無し。CLI の plugin skill で使えるかは不明なので Markdown fallback を既定にする。
- 公式の発信窓口: 公式 Discord / forum / newsletter / plugin author spotlight は見つからなかった（検索 2 回）。documented なのは developer portal の "Get help"、directory@anthropic.com（返信遅延あり）、anthropics/claude-code と claude-plugins-* の GitHub issue、`/feedback`。outreach 経路は「未証明」として扱う。

### 3. 競合と需要（competitors.md、各 README 全文 + HN Algolia API、2026-11-01）

**3a. 競合表（要点）**

| tool | 規模 | 何を見るか | 適用 | 備考 |
|---|---|---|---|---|
| danshari-skill（swaylq） | 1★、11 commits、v0.1 | skill を 4 分類し「model が吸収したか / harness が提供するか / MCP か / 重複か / 腐ったか」の 5 問、blind sub-agent test、token cost | 確認後に archive（rm せず）+ 復元路 | stocktake の「substrate 吸収」視点に最も近い（skills のみ）。demo: 12 → 5 skills、description tax 約 2,160 → 735 tokens/turn。README の verdict 件数の合計は 11 で 12 と合わない |
| skillreaper（reap） | 62★、216 commits、issue 10 件は全て作者 | local の transcript から未使用の skill / MCP / subagent / hook / 常時読み込み prose。REAP/MUTE/KEEP/REVIEW | `reap prune` で移動、`restore --all`、`install-hook` が settings.json を編集 | Go の静的 binary、telemetry なし。作者自身の run（2026-08-23）で 382 件読込・13 件発火（3%）・約 19,755 dead tokens/session・約 $3.26/月（README が n=1 と明記） |
| agnix | 462★、757 rules | CLAUDE.md、AGENTS.md、SKILL.md、hooks、MCP、Cursor、Copilot | `--fix` / `--fix-safe` | 静的 Rust。Show HN 2026-02-12 は 1 pt / 1 comment |
| Skills Janitor | 124★、Product Hunt 224–235 upvotes（2026-04-13） | 重複、壊れた symlink、未使用 skill | `--prune`、y 確認、.bak | **v1.8（2026-09）の README が maintenance mode** と宣言し「Claude Code が core を native に持つ」と /skill-doctor / /doctor / /skills を案内 |
| tw93/Waza（/health） | 7.5k★ | agent setup の監査 | 承認後 | star は 8 skill bundle と作者のフォロワー由来と推定（notes の推論） |
| token-optimizer | 2.8k★ | CLAUDE.md、skills、MCP、memory の per-component audit | 修正案を提示 | 自己申告 59.6M tokens / $1,396（API 換算、実測 $126 との差を README が認める） |
| audit-harness-fit（uzys-agent-harness） | listing page のみ | steering 層（CLAUDE.md、rules、hooks、permissions、skill descriptor）を INVENTORY → EVIDENCE → VERDICT（keep/rewrite/relocate/delete）→ RELOCATE → APPLY | APPLY は承認待ち、branch / commit workflow の記載なし | **形が最も近い**（repo は未読）。採用先にするには小さく roadmap 不明 |
| skill-graveyard / cc-audit / claude-config-auditor / cclint / claudelint / Cursor 側（cursor-doctor、agents-doctor、ctxlint） | snippet 止まり | 静的 lint または log 集計 | 主に報告のみ | skill-graveyard: 116 件 install のうち 35 件のみ使用（dev.to 2026-05-18、0 comment）。cursor-doctor は有料 `audit` tier |
| ECC `skill-stocktake` / `context-budget` / `harness-audit` | ECC 294,013★（lead 計測） | context 消費、品質 checklist | 推奨 | 作者の harness が取り込んだ prior art。1,776 件の GitHub 結果は ECC の mirror / fork 由来（独立した採用ではない） |

**3b. Adopt か Build か**
- 全体の 1 report・1 承認・branch 適用を skills + rules + agents + hooks + docs に跨いで行う tool は見つからなかった。近いのは audit-harness-fit（承認あり、branch / ADR / ledger / hook test なし、listing のみ）と danshari（skills のみ、v0.1）。採用先にはならない。
- commodity な層（未使用 skill、per-skill cost、CLAUDE.md の trim、古い path、矛盾、古い model 向けの書き方）は Anthropic が無料で持つ。**再販せず、その上の層に置く**: 内容の判断、artifact を跨ぐ drift、hooks / ledger / ADR、1 承認の branch 適用。可能なら `/skill-doctor` の出力を入力として呼ぶ。Skills Janitor の maintenance mode が先例。
- contribute 先の候補: agnix（静的 rule と LLM 判断は補完関係）、danshari（blind test の考え方が同じ）。

**3c. 反応・需要の実測**
- HN（Algolia、2026-11-01）: audit / lint 系の Show HN は小さい — "A Linter for Skill.md Files" 2 pts / 0（2026-03-05）、Agnix 1 / 1（2026-02-12）、AgentLint 4 / 3（2026-04-07）、"Linting 216 public Claude Code skills" 3 / 0（2026-09-17）、Mdarena（自分の PR で CLAUDE.md を benchmark）22 / 4（2026-04-05）。外れ値は Fata（人間の skill rot、別問題）124 / 53。**audit tool の genre は HN で破れていない。最良は「benchmark / 証拠型」**。
- 一方で「CLAUDE.md の良い書き方」系は数百 pts: "Writing a good Claude.md" 748 / 290（2025-11-30）、AGENTS.md 読み取り 741 / 285（2026-09-18）、"Universal Claude.md" 471 / 162、"Claude Code as a Daily Driver" 451 / 254。"Ask HN: Do you still spend time maintaining Claude.md / AGENTS.md files?" は 9 / 10（2026-05-16）。問題への関心は大きく、audit tool への関心は小さい。
- 一次の公式側の需要: claude-md-management 315,197 / claude-code-setup 224,255 installs（lead 取得、2026-10-30 生成の stats JSON、all-time）。first-party の config hygiene 需要は 6 桁。
- **月次の反復利用の証拠はどの audit tool にも無い**。反復の仕組みは自動化（agnix GitHub Action、cc-audit Action）のみ。n=1 の逸話が Lauren の週次 review agent（2026-03-29、25 skills 中 6 が stale）。「月次」は未検証の仮定。
- /skill-doctor への唯一の実質的批判: 「skill が走ったかは記録するが役に立ったかは記録しない」ので稀だが価値のある skill が dead weight に見える（implicator.ai 2026-09-07）。内容を判断する stocktake / danshari の blind test はこの弱点に答える。
- 「wow」の枠組み: before/after の token 数、%、$、grade A–F、browser playground。いずれも n=1 の自己申告で小さい。/skill-doctor が per-skill cost を無料で出すので、token 節約の主張は弱い。
- 日本語圏: classmethod（2026-07-10、2026-09-24）と serverworks（2026-10-03）が `/doctor` を紹介済み。Zenn / Qiita の原典で like 数付きのものは見つからなかった。

### 4. dev tool の広がり方と activation の測り方（devtool-activation.md）

**4a. 0 → 数千 repo の事例**
| 事例 | 規模と時間 | 広がった経路 | 読んだ範囲 |
|---|---|---|---|
| Renovate | 2017-01 の OSS 化から約 14 か月（2018-03）で約 500 installs / 約 5,000 projects（public のみ） | blog、機能要望、GitHub Marketplace（Rhys: 「聞いたことのない人にも見える」）。onboarding PR | Changelog #289 全文、Renovate docs |
| Mergify | 1 年で約 30k repo（2020-03、自社報告） | 数個の協力的な project を guinea pig に、Marketplace、organic が 1 位。作者自ら「マーケは下手」 | blog 全文 |
| Dependabot | 2021-04 に 3 万 org 超（Preview） | 2019-05 の GitHub 買収後の platform 力。単独 launch の事例ではない | snippet |
| Ruff | 2023-04 に月 100 万 DL 超・12k★、2026-11 に dependents 198,576 repo | 作者自身の HN 投稿（2022-08-30）は 4 pt / 0 comment、**翌日の第三者投稿が 148 pts**。FastAPI / Pydantic 等の目立つ repo が採用して認知 | Astral blog 全文、HN API |
| Knip | 22,611 repo / 5,056 package の dependents、12.6k★ | 作者本人が書いた Smashing Magazine 記事（2023-08）。HN では他者の投稿が全て 1–2 pt。CI で走る | repo、API |
| all-contributors | bot repo 636★、使用数は非公開 | Kent C. Dodds が Changelog #246 で紹介 → issue で要望 → Changelog 編集者が採用・発表（2019-01-30）。README の表が広告になる | Changelog News 全文 |
- 全事例に共通する（notes の統合）: 他人の repo の中に**見える artefact**（設定ファイル、README の表、onboarding PR、bot comment）を残したか、隣接する尊敬される maintainer が先に採用した。bulk outreach で広がった例は無い。作者側がしたのは、他人から見える場所に出す、要望に応える、権威ある記事を 1 本書く、thread に居ること。
- **「1,000 repo に達するまでの時間」の公表値は無い**。近いのは Renovate（約 14 か月で約 5,000）と Mergify（1 年で約 30k）で、どちらも Marketplace / App の install 形態と platform 掲載を持つ。stocktake は Marketplace 相当を持たない（Claude plugin marketplace がそう振る舞うなら別 — 角度 2 参照）。

**4b. Activation の設計と測定**
- Renovate の **onboarding PR**: install 後に最初に見えるのは「何が起きるかの preview」PR（例: 「約 7 本の PR が出る」）で、merge するまで何も変わらない。close すれば既定値で動く（opt-out = close）。stocktake の「1 report・1 承認」と同形で、移せる。
- time-to-first-value の実測値を公開した maker は無い。Ruff の「disbelief」は単一の感覚的性質（速さ）が初回実行で見えたという定性記述。「Stripe / Vercel は 90 秒未満」は vendor blog の主張で未検証。
- 公開面での計測: GitHub dependents graph（宣言された依存のみ。Claude の plugin / skill は通常 package 依存でないので**拾えない**と推定）、star（Ruff の maker 自身が vanity metric と呼ぶ）、npm / PyPI DL、Marketplace、config file の code search（maker が使った例は見つからず推定）。
- telemetry の受容（全て公式 doc 全文、Scarf と gh CLI は snippet）: Homebrew は既定 ON で初回通知、`brew analytics off`、公開集計。Go は opt-out 案がコミュニティ意見で opt-in 案に改訂。Turborepo は opt-out + DO_NOT_TRACK + payload を表示する debug mode。慣行は **DO_NOT_TRACK を honor し、送る payload を印字できる**こと。skill は LLM が config 全体（rules / hooks / ADR）を読む中で走るので、匿名 ping でも Homebrew より信頼の要求が重い（notes の判断）。受容実績のある選択肢は (a) telemetry なし + 公開面の counter、(b) payload を印字できる opt-in。
- Go の見積もり: 週約 16,000 report で 99% 信頼・1% 精度、opt-in がずれなければ約 300 万 install の 1% でも足りる（research.swtch.com、2023）。

**4c. launch の機構と効果量**
- Show HN: 試せる物、barrier なし、本人が thread に居る、友人に upvote を頼まない。Claude Code の subscription が要る skill は barrier なので、**sample harness + sample report の no-login demo が規則に合う**（推論）。
- 効果量: arXiv 2511.04453（AI tool repo 138 件、2024–25）で HN 露出後の star は平均 24h で約 121、48h で約 189、7 日で約 289。Show HN tag の有意な優位は統制後に無し。投稿時刻は効く。別の blog 分析（188,085 件、2026-04-23、相関）: 1 upvote あたり約 1.4 star、半減期約 24h、48h で 92% 終了。**star は「毎月回る repo」に換算できない**。数字入りタイトルの効果を示す厳密な証拠は無い。
- Changelog News は自己投稿可（tutorial と商用は不可、掲載時期は不定）。Console.dev は公開の投稿手順を見つけられなかった。Product Hunt: 2026 Q2 の Dev Tools 633 launch、平均 upvote 201、OSS 192。upvote と install の対応づけは無い。
- r/ClaudeAI: showcase は total karma 50 以上、未満は megathread（redlib mirror の snippet、2026-04-15）。reddit.com は fetch 不可。投稿前に実地確認が要る。
- Zenn / Qiita: 公式の trending 仕様は見つからず。相関のみの小標本（Zenn n=26 / Qiita n=28）は弱い。
- 発売前の検証: Carpentries Incubator の rapid usability testing — 約 10 人、1 時間以内（できれば 30 分未満）、CLI は terminal の内容を貼って送る。初期協力者は行動で効く（Mergify の guinea pig、Renovate の初期利用者）。インセンティブ額の根拠は無い。

### 5. GitHub Action として出す・「入れずに試す」（github-action.md、docs 全文）

**5a. 既存の足場: anthropics/claude-code-action**
- 最新 tag v1.0.266（2026-10-31）、floating tag `@v1`。v1.0.264（2026-10-27）で plugin の例が `claude-plugins-official` に変わった。
- **公式 doc に "Run a skill" 節**: plugin 内の skill は `plugin_marketplaces` と `plugins`（`plugin-name@marketplace-name`、marketplace 名は repo URL でなく manifest 由来）で入れ、`/plugin-name:skill-name` を `prompt` に渡す。repo 内の skill は checkout 後に `/skill-name`。
- 過去の障害: issue #639（2025-10-23 起票 → 2025-11-10 close、v1.0.15 で plugin 対応）。「CLI と完全な機能同等ではない」と maintainer が述べた。**複数 skill が sibling の SKILL.md を参照する 1,700 行級の plugin が Action 内で入るかは、証拠が無く smoke test が要る**。
- schedule: 公式の "Daily Report" 例は `on: schedule`。**public repo は 60 日 repo activity が無いと schedule が止まる**。月次（約 30 日）でも scheduled workflow 以外に commit が無い repo で止まるかは GitHub 側の定義が未確認。
- 権限: 既定は Claude GitHub App（repo admin が install。権限が大きく subset 受理不可）。`GITHUB_TOKEN` を使うと commit が CI を起動しない。`id-token: write` が要る。setup は `/install-github-app`（github.com のみ）。
- action 入力: `plugins`、`plugin_marketplaces`、`display_report`（Claude Code report を Step Summary へ）、`show_full_output`（public log で secret が漏れる恐れ）、`branch_prefix`（既定 `claude/`）、`structured_output` 等。

**5b. 認証と規約（原文引用あり）**
- `claude setup-token` は 1 年の OAuth token を作る。"requires a Pro, Max, Ultra, Team, or Enterprise plan"、model request のみ。org で共有する secret は API key を勧める（OAuth token は実行者の subscription に紐づく）。
- 規約（code.claude.com/docs/en/legal-and-compliance、全文）: "Advertised usage limits for Pro, Max, and Ultra plans assume ordinary, individual usage"。第三者が Claude.ai login を自社 app に載せること、「利用者に代わって plan の credential で request を流すこと」は不許可。"Customers may not pay for, resell, or intermediate Claude usage on their end users' behalf"。
- 読み方（notes）: **各 repo の持ち主が自分の secret に自分の `CLAUDE_CODE_OAUTH_TOKEN` を置き、unmodified な action を走らせる**のが documented な経路。作者や campaign が他人の token を預かる、他人の audit を作者の Max で走らせる、運営者が利用者の代わりに払う、は避ける。月次 multi-subagent の audit が "ordinary individual usage" かは**言及なし = 不明**。
- subscription 課金の状態: 2026-05 に予定された Agent SDK / `claude -p` の別 credit 化は 2026-06-15 に一時停止。**2026-10-07 の更新で、plan に signed in の `claude -p` は引き続き subscription limit から引く**（support.claude.com/en/articles/15036540）。GitHub Actions への言及は無い。2026 年に 1 度反転済みなので、campaign 開始前に再確認する。
- **`--bare` は `CLAUDE_CODE_OAUTH_TOKEN` を読まず plugin / skill / hook / CLAUDE.md を飛ばす**。subscription token で plugin skill を走らせるなら使えず、`-p` の既定が `--bare` になる将来 release では経路が壊れる（失効条件）。

**5c. `claude -p` の事実**
- `claude -p "/skill-name args"` は動く。`--output-format json` が `total_cost_usd` を返す。`--json-schema` で `structured_output`。v2.1.302 以降、nothing set なら Manual mode で未承認の呼び出しは deny。無人実行は `--allowedTools` や `--permission-mode` を使う。`--max-budget-usd` で支出上限。
- **安全**: `--bare` なしの `-p` は project の `.claude/settings.json` の hook と `.mcp.json` の server を、**未信頼の folder でも workspace trust dialog なしで走らせる**。持ち主自身の runner での default branch 実行は同じ trust domain だが、fork 発の PR 起動や server 側の「試す」設計では意味が変わる。
- **Artifact は Agent SDK / GitHub Action / `-p` で既定 OFF**、API key / gateway token / cloud credential の session は publish 不可（artifacts page 全文）。したがって CI の report は **Markdown fallback のみ**。Artifact は claude.ai の account 内で private が既定なので「公開の 1 枚」にもならない。

**5d. report の出し先と idempotency**
- Step Summary: GFM、1 step あたり 1 MiB、job あたり最大 20、secret は自動 mask。`<details>` の可否はそのページでは未確認。
- issue 本文: peter-evans/create-issue-from-file（`issue-number` で更新）。comment: find-comment + create-or-update-comment。action 自体の `use_sticky_comment` は PR event のみ。
- peter-evans/create-pull-request: 固定 branch（`create-pull-request/patch`）を使い回して同じ PR を更新、差分なしなら静かに終了、不要になった PR は自動 close。repo 設定で Actions による PR 作成の許可が要る。
- Renovate の **Dependency Dashboard**（1 issue に保留中の更新を並べ、checkbox を入れると PR が出る。`dependencyDashboardApproval` で承認まで PR を止める）が「1 report・1 承認」の最も近い先例。stocktake の branch 適用は create-pull-request の固定 branch 更新に写せる。

**5e. GitHub Marketplace への掲載**
- 要件: public repo、repo root に action metadata file 1 つ、unique name、category、tag 付き release、Developer Agreement、2FA。Verified creator は要件でない。composite action（`anthropics/claude-code-action@v1` を包む）は可。
- 人気の可視化: Marketplace ページに install 数は出ない。「Used by」は dependency graph 由来で public のみ、大規模 action でも widget が出ない報告がある（discussion #199447、snippet）。約 1,000 の**public** dependents は数えられるが private は見えない。

**5f. 「入れずに試す」server 側（一次事実のみ）**
- 先例: OpenSSF Scorecard の web viewer（`securityscorecards.dev/viewer/?uri=github.com/<owner>/<repo>`）と REST API。snippet のみで、任意 repo をその場で計算するかは未確認。
- Agent SDK の hosting 一次: 1 agent あたり 1 GiB RAM / 5 GiB disk / 1 CPU が出発点、container は約 $0.05/h、**token 費が container 費を 1 桁以上上回る**、`maxTurns` が唯一の session 制限、並列 subagent の大量 fan-out は rate limit に当たりうる。multi-tenant は `settingSources: []`、`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`、テナントごとの `CLAUDE_CONFIG_DIR`、egress allowlist。
- 匿名の paste-a-URL 無料 service は運営者の API key で払うことになる。「end users の代わりに払うな」条項が無料 audit service に及ぶかは**不明**。abuse 対策（IP 制限、URL allowlist）の指針は docs に無い。
- Anthropic-hosted の代替: cloud scheduled tasks（利用者個人の claude.ai account に属し、その usage に数える。repo に置いて配れる物でない。marketplace plugin の skill が "Unknown skill" になる未解決 bug #78287 が snippet で報告）。managed Code Review（未読）は workflow file 不要の先例。

### 6. 動画・画像 pipeline（Remotion + TTS）（video-pipeline.md）

**6a. Remotion**（npm `remotion@4.0.539`、context7 の公式 docs、LICENSE.md 全文）
- ライセンス: **個人と従業員 3 人以下の営利組織は Free License**（無制限の商用、best-effort support）。4 人以上は Company License（Automators $0.01/render で月 $100 最低、Creators $25/seat/月）。LICENSE.md は「Remotion 5.0 でわずかに変わる」と書く（PR 未読）。→ 単独の作者は Free。失効条件は 5.0 の変更と人数。
- 構造化 data 駆動: `npx remotion render <comp> out.mp4 --props=./report.json`（JSON 文字列か file path）、`calculateMetadata()` で尺・fps・サイズを props から決める。Node API は `bundle` + `selectComposition` + `renderMedia`。
- 静止画: `npx remotion still --props=... comp out.png`（png / jpeg / webp / pdf）。**同一 JSON から video と before/after 画像の両方が出る**。GIF も出せる（`everyNthFrame`、`numberOfGifLoops`）。
- 字幕: `@remotion/captions` の `createTikTokStyleCaptions`、`@remotion/install-whisper-cpp`（token レベルの timestamp、新しい whisper.cpp が要り crash の警告あり）、`@remotion/whisper-webgpu`。
- Remotion 公式の agent skill: `remotion-dev/skills`（`npx skills add remotion-dev/skills`）。作者の Claude Code が composition を書くのに使える。weekly installs 117k は第三者 directory の数字（**未検証**）。
- community template: ofershap/remotion-readme-kit（MIT、CliDemo / CodeBeforeAfter / FeatureShowcase、8 commits・6★、未成熟 = 依存でなく型の参考）、fay-saal/codemotion（git diff → typewriter 動画、snippet）、21st.dev（API key 要）。公式の terminal / diff / 「統計の reveal」component は見つからなかった。
- macOS: 互換性の docs page は 404。local render は headless Chrome を必要時に download。Apple Silicon の性能は**未検証**。

**6b. TTS（価格・ライセンスは 2026-11-01 の公式ページ）**
- OpenAI: tts-1 $15 / 100 万字、tts-1-hd $30、gpt-4o-mini-tts は $12 / 100 万 audio output token + $0.60 / 100 万 text input token。45 秒（約 800 字）の tts-1 で約 $0.012。word timestamp は TTS endpoint から出ない（notes は未確認と明記）。
- ElevenLabs: Free は 10,000 credits/月だが**商用 license は Starter 以上**（$6/月。ページ内に $1 初月 promo もあり内部不整合）。`/with-timestamps` が audio + 文字単位 alignment を返す（snippet）。唯一、audio と同時に timestamp が来る商用選択肢。
- Azure Speech: `WordBoundary` event が語ごとの offset と duration を返す（docs の先頭 100k 字を読んだ）。無料枠は未読。
- Kokoro-82M（Apache-2.0、v1.0 は 2025-01-27、54 voices、HF の card 全文）: Apple Silicon 向け port は `mlx-audio`、`kokoro-mlx`、`kokoro-coreml`（snippet）。word timestamp は MLX 版で記載なし。実用例: 2025-11-24 の dev blog で Kokoro + Remotion を CPU で走らせ、1 つの `project.json` から 53 WAV / 14 scene、尺は audio 長から生成。**word 字幕は作らず**、画面上の字は narration と別に書く（dual-text）。repo は公開されていない。
- Chatterbox / Fish Speech / F5-TTS / Dia: 集約 blog のみ（snippet）。Fish Speech は license の記述が割れる（Apache か CC-BY-NC-SA）。F5-TTS は code が MIT・weights が CC-BY-NC。再現可能な script には一次資料の確認無しに推せない。
- どの TTS でも使える字幕経路: audio 生成 → whisper.cpp の token timestamp → `toCaptions` → `createTikTokStyleCaptions`。原稿が既知なので、audio 長からの scene 単位字幕で whisper を避ける手もある。

**6c. 端末録画の代替**
- charmbracelet/vhs v0.12.1（2026-09-24、MIT）: tape file → GIF / MP4 / WebM / PNG。ttyd と ffmpeg が要る。**実際に tool を走らせる**必要があるが、stocktake は Claude Code 内の LLM skill なので録るのは `claude` TUI か canned output の replay。音声なし。`vhs-action` あり。
- asciinema + agg: agg は GPL-3.0 以降、Release が空で git ref による再現。player JS は README 内で動かない（snippet）。
- README の実例（2026-11-01 の README 読み）: gum と lazygit は demo GIF / mp4 を持つが、**ruff・knip・biome・fzf は demo 動画を持たない**（fzf は PNG と YouTube link）。5 件中 3 件は demo 媒体なし、持つ 2 件は動きが製品の TUI。Remotion を README 媒体に使う例は無い。

**6d. 投稿先の仕様（大半が二次情報。公開前に再確認）**
- X: 無料 account は 2 分 20 秒・512 MB、H.264 MP4 / MOV。Premium は最大約 3–4 時間（出典間で不一致）。2026-09-01 に API 上限が 20 分 / 8 GB になったという 10 月の 1 資料は**未検証**。公式ページは未取得。
- Bluesky: `app.bsky.video.getUploadLimits` で現行値を取れる。二次資料は 3 分・100 MB（旧情報は 60 秒・50 MB）。
- YouTube Shorts: 2024-10-15 から最大 3 分、正方形か縦（二次、公式は未取得）。
- GitHub（公式 docs 全文）: image / GIF は 10 MB、video は free plan repo で 10 MB・paid で 100 MB。README への埋め込みは user-attachments URL 方式（blog 由来、GitHub docs は沈黙）。→ README 用は 10 MB 未満の MP4 か GIF。
- Zenn（markdown-guide 全文）: YouTube / X / GitHub / CodePen 等を埋め込めるが mp4 の埋め込みは無い。YouTube URL を単独行に貼る。画像サイズ上限は未記載。

**6e. 公開された「JSON → 語り付き動画」pipeline**
- end-to-end で release note / report JSON → 語り付き動画にした repo は見つからなかった。最も近いのは 6b の dev blog。glue（JSON → 台本 text + TTS + whisper か scene 尺 + composition）は小さく、composition が主な作業。

### 7. 倫理と platform 規則（ethics-unsolicited.md。多くは digest 経由。逐語読みでない）

**7a. A: 公開 repo への unsolicited な audit / 連絡**
- GitHub AUP（効力日の表示なし。第三者 tracker は 2026-05-12 更新としているが**未検証**）: Sec 4 が "automated excessive bulk activity and coordinated inauthentic activity" と bulk の宣伝を禁じる。Sec 10 が issue への "monetized or excessive bulk content" を禁じる。Sec 8 は do-not-contact の求めへの対応を要求。PR / issue の bulk に特化した条項は無く、"excessive" は未定義。
- GitHub ToS（2026-04-27 効力）Sec H: 「spamming を目的に API で data を取得してはならない」、過度な request はアカウント・IP の停止対象。
- 2026 年に platform 側が入口を閉じ始めた: 2026-02-13 の repo 設定（PR をオフ、collaborator のみに制限）、2026-06-17 に write 権のない利用者の open PR 数の上限（Gigazine / CodeRabbit、二次）、6 月下旬に issue 作成を write 権持ちに限る選択肢（visualstudiomagazine 2026-06-30、二次）。The Register 2026-02-03 で GitHub の PM が「低品質な contribution の増加」を重大と述べた。curl は 2026-01-21 に AI-slop 報告を理由に bug bounty を終了（Stenberg は証拠のある AI 支援報告は歓迎）。
- 「AI agent + 商業動機 + 冷たい連絡」は名付けられた類型になった: Socket の報告（2026-02-14、"Kai Gritun" が 2 週間で 95 repo に 103 PR、cold email、consulting 販売）。undisclosed な AI と商業動機が問題。
- Nesbitt（2026-02-13、意見）: "Unsolicited PRs, drive-by issues, and automated audits are all withdrawals from a finite account."。**pull 型**（findings を公開し、maintainer が自分の時間で関わる）を勧める。
- 先例の転換率（研究者の issue / PR）: Leiden path-traversal（arXiv 2505.20186）は倫理委員会承認、段階的 outreach で patch 14%、"mass notifications can be perceived as spam"。「unethical behavior in OSS」（arXiv 2302.11985）は 392 issue で返信 83（21%）、IRB 承認、それでも invalid 15 件のうち 5 件が bot と思われた。Waterloo/Nagappan（2018–19）は**15 issue + 15 PR（手動、研究者と開示）で account が spam として flag**された。UMN の hypocrite commits（2021）は IRB 自己判定が community に受け入れられず、全 @umn.edu を ban、435 commit を revert。
- 受け入れられた型: Dependabot / Greenkeeper は**持ち主が install する opt-in**、in-repo config、沈黙 = 停止（Dependabot は 90 日未対応で自動停止）、でも noise と批判される（Valsorda 2026-02-24）。Greenkeeper の PR の merge は 32%（arXiv 2206.07230）。Hacktoberfest 2020 は opt-in（topic）化と maintainer による spam 指定が解決策。
- 強い反対論（notes の整理、出典のある事実は上記）: 入口が閉じられつつある、「AI + 自己の可視性」は spam と同じ見え方、転換率が低い、hygiene の指摘には victim がなく通知義務の根拠が弱い、「1 承認で config を編集する tool を勧める issue」は maintainer の harness への営業になる（`~/.claude` の SKILL / agent / rule は制御プログラムというローカル security rule とも整合）、単独 account と**過去の block（2026-07-16 Wikidata）**で tail risk が大きい。
- 残る形（notes の統合）: (1) pull 型 — 自分の repo に audit を自己申告する場を置く、利用者が local で走らせ共有は任意、(2) 招待制 — 頼まれた repo だけ audit、公開は許可を得て、(3) どうしても unsolicited なら 1 件ずつ手動確認し総数を Waterloo の約 30 件よりずっと下、issue が有効で contributing channel のある repo に限る、"human, not a bot"、証拠先行、二度目なし、do-not-contact を守る、limit に当たれば停止、PR は出さない。notes 自身が「これでも最弱の選択肢」と評価している。

**7b. B: adoption を repo の走査で数える**
- GitHub AUP Sec 7: 研究者は「public・非個人」情報を使え、成果が open access であること（Zenodo DOI は適合）。scraping は "bot or webcrawler" による抽出で、API 経由は scraping でない。spam 目的の利用と個人情報の売却は禁止。
- rate limit: Search code は 10 req/min、1 query 最大 1,000 件、default branch のみ、384 KB 未満。secondary limit は content 作成が 80/分・500/時、"Continuing to make requests while you are rate limited may result in the banning of your integration"。**GitHub の「backoff して再試行」と作者の「limit は停止信号」は食い違う**。1,000 件上限を超える列挙は分割 query が要り、それ自体が burst 型の挙動（推論）。
- MSR の倫理: Gold & Krinke（Empirical Software Engineering 27、2022、abstract のみ）。Vidoni & Diaz Ferreyra（arXiv 2202.11969）は識別子除去では不十分で outlier は再識別されうるとし、public repo の consent は open question（k の値なし）。
- 実際の学術慣行: arXiv 2602.14690（v1 2026-02-16、v5 2026-06-30）は 2,853 の GitHub repo を走査して context file / skill / subagent を数えた。abstract に倫理声明も repo 名の扱いも無い（全文未読）。agents.md の site は「60K+ projects」を主張、独立 code search は root AGENTS.md 約 96,600（2026-06、blog、未検証）。
- **config file の presence を集計して公開した事例への異議は見つからなかった**（ただし「誰も見ていない」ことの証明にもならない）。
- 作者の ledger との差: `skills/*/results.json` + `evaluated_at` は AGENTS.md / renovate.json と違い、**出力 ledger**で、その人がいつ何を評価したかという活動の時間が読める。汎用 path は他 tool の eval ledger と衝突し精度を損なう（lead の検索で 19 file 中 17 が無関係の `evals/results.json`）。
- 反映案（notes の提案。出典は無い）: 集計のみ、repo 名・owner 名なし、n が約 10 未満の cell は伏せる、tool の version と query を併記、月次の per-repo 追跡はしない（presence のみを snapshot ごと）、opt-in の信号（利用者が選んで置く ADOPTERS 的な entry や badge、または印字できる payload の telemetry）を優先。k の閾値は notes 筆者の提案で根拠となる数字は無い。

### 8. 反応監視 API（reaction-monitor.md）

| 対象 | 取れるもの | 制約（2026-11-01） | 読んだ範囲 |
|---|---|---|---|
| GitHub traffic API | 自分の repo の views / clones / 上位 path / referrers（上位 10） | **直近 14 日のみ**、write 権限が要る。→ 日次の launchd job で `gh api repos/O/R/traffic/*` を台帳に保存 | 公式 docs 全文 |
| GitHub stars | 自分の repo の `GET /repos/{o}/{r}/stargazers/history`（週ごと `{week,total,days[7]}`、30 週 / page、2026-09-04 新設）、`starred_at` 付き list | 2026-06-30 に `/stargazers`・`/subscribers` が admin / collaborator 限定に。**他人の repo の stargazer 一覧は取れなくなった**ので adopter 探しには使えない。新 endpoint の権限は docs に未記載 | changelog、docs 全文。lead が自分の token で `GET .../akc-cycle/stargazers/history` の成功を確認済み |
| GitHub code search（legacy REST） | `total_count` と最大 1,000 件 | **10 req/min**、default branch のみ、384 KB 未満、`incomplete_results` あり。fork は既定で除外（snippet）。fork・mirror・自分のコピーを含むので「file のコピーがある」ことを測り、「毎月走っている」ことは測らない。1 日 1 query なら自分の利用は軽い | docs 全文。`path:` / `filename:` の厳密さは未確認 |
| Claude Code の plugin install 数 | `plugin-installs.json`（`unique_installs`、all-time、24h cache） | 2026-10-30 生成、324 plugins。**`@claude-plugins-official` の entry のみ**。第三者 marketplace に数字はない。定義は未記載。出典は CLI source の第三者 mirror（version 依存） | mirror + live JSON |
| Hacker News | Algolia API（10,000 req/h/IP、`restrictSearchableAttributes=url`、`tags=comment`） | endpoint の正確な syntax は 1 回の curl で確認（notes は記憶から補っている） | 公式 doc 全文（薄い） |
| Bluesky | `app.bsky.feed.searchPosts`（`url`、`domain`、`mentions`、`limit ≤100`） | 匿名アクセスは出典間で割れる（Contradictions）。app password の session を前提にする | lexicon（metacpan mirror）全文 + 第三者 |
| Reddit | 公式 API は事前承認制（Responsible Builder Policy、fetch は 403 で snippet のみ） | 自己登録は 2025-11 頃に終了、無認証 `.json` は 2026-05-30 から 403（第三者）。「2026-10-31 に新規申請停止」は**未確認の噂**。実際の経路は F5Bot | snippet |
| F5Bot | Reddit / HN / Lobste.rs の keyword alert | free 版は delay・件数上限。keyword に URL の一部を使える。RSS / JSON / webhook は **free で使えるか未確認** | FAQ 全文 |
| X | 読み取り約 $0.005 / post | pay-per-use が既定（2026-02-06）。出典は vendor（opentweet.io）と blog のみで公式未読（developer.x.com は 402）。課金は人間 gate | 第三者のみ |
| Buffer | post ごとの impressions / reach / reactions / reposts / comments | **X の `link_clicks` は取れない**（"StartPage-only"、deprecated は 2026-07-31 に削除）。`insightsRead` は personal API key のみ（App Client の OAuth は不可）。X は日次 cadence で約 24h ゼロのことがある。limit は account 共有で、429 では停止して報告 | 公式 doc 全文（"Experimental" 表記）。session の Buffer MCP の説明と整合 |
| Dev.to / Forem | `GET /api/articles/me/...`、`/api/analytics/historical`、`/api/analytics/referrers`（`api-key`） | rate limit は未読部分 | 先頭 100k 字 |
| Qiita / Zenn | Qiita: `likes_count`、`page_views_count`（出典間で割れる）。Zenn: 公開 JSON に `liked_count`・`comments_count`、views は cookie 認証の非公式 endpoint のみ | Zenn の cookie（`connect.sid`）は secret の保管になり ToS リスク。likes は公開 JSON、views は手動か見送り | snippet |
| shields.io endpoint badge / Scarf | badge の描画回数 / Files gateway の取得回数 | どちらも「runs」でなく badge 描画（README view、bot 込み）や fetch の数。利用者が自分の README に置く badge は opt-in の「使っている」信号 | shields.io 全文、Scarf は snippet |

- 計測の結論: 公開面だけでは「毎月 1,000 repo が回っている」は**測れない**。測れるのは (1) 自分の repo の traffic / star 履歴、(2) code search での file コピー数、(3) 公式 marketplace に載った場合の install 数、(4) 外部の言及（HN / Bluesky / F5Bot）。link click は X 側では取れず、GitHub の referrers または UTM / 短縮 link が要る。
- GitHub の rate limit 文書は「`retry-after` を守って再試行」と書くが、作者の方針（boundary.md）は「limit に当たれば停止して報告」。notes は 403 / 429 を停止信号として扱うことを推奨している。
- Renovate / pre-commit.ci / Knip の adoption 数の算出法は見つからなかった（code search / dependents / App install 数からの推定は未検証）。

## Contradictions

1. **marketplace の install 数が見えるか**（plugin-directory 内、reaction-monitor と）: anthropic-marketplaces doc は web catalog が「install 数を表示し、一部を Anthropic verified とする」と書くが、claude.com/marketplace/plugins の page fetch には install 数も featured 欄も見えない（summarizer の限界の可能性）。一方 reaction-monitor が取った `plugin-installs.json`（2026-10-30 生成）は `@claude-plugins-official` のみで、community / 第三者には数字が無い。→ 強い根拠は live JSON（実物）。**数字が出るのは公式 marketplace の plugin に限る**と扱い、web catalog の表示は未確定とする。
2. **skills.sh の telemetry opt-out の環境変数**（awesome-lists 内）: 公式 docs は `DISABLE_TELEMETRY=1` / `DO_NOT_TRACK=1`、第三者の投稿は `SKILLS_NO_TELEMETRY=1`。→ CLI docs の方が強い。第三者の記述は採らない。
3. **Bluesky `searchPosts` の匿名アクセス**（reaction-monitor 内）: lexicon は「実装によって認証が要りうる」。第三者（Apify の scraper README、bsky-docs issue #332、2026-08-18 archived）は `public.api.bsky.app` が 403、`api.bsky.app` が 200 と報告し、cursor 付き無認証は 403 という報告も。docs.bsky.app の公式 page は読めなかった。→ どちらも未検証。app password の session を前提にし、1 回の実地で確認する。
4. **star-history の記事が自己矛盾**（reaction-monitor 内）: star-history.com/blog/github-stargazer-api-restriction は本文で他人の repo のチャートが壊れたと書き、2026-09 の更新注で新 endpoint により解決したとも書く。→ 本文は古く、GitHub 公式の docs / changelog（2026-09-04）が強い。ただし新 endpoint の権限要件は docs に無く、lead の自分の repo での成功が実物の根拠。他人の repo の履歴が取れるかは不明。
5. **lead の 2026-10-04 survey と現状**:
   - walkinglabs の未処理 PR: 35 → 61（backlog は増えている）。
   - 「~3% acceptance」は裏付けなし（上記）。
   - 公式 marketplace の件数: 315 → 約 315（4 週間で変化なし。数え方が概算）。
   - community marketplace: 10-04 提出は akc-cycle / harness-scope / harness-stocktake とも**現れていない**（lead の 2026-11-01 全量取得 2,283 件）。plugin-directory の note は先頭約 140 件しか読めておらず「不明」としていたが、lead の全量取得で存在しないと確定した。ポータル上の状態は作者にしか見えない。
   - 「project-unscoped な UserPromptSubmit/PreToolUse/PostToolUse hook は fail する」: checklist 全文に見つからず**未確認**（Policy や scan の別 category にある可能性）。
   - karanb192 の Meta Skills と 2 entry、hesreallyhim の issue form のみと 14 日 / 100★ 基準、skills.sh の自動 index、akc-cycle の plugin.json / marketplace.json の存在: 一致を確認。
   - 提出経路: 旧 Console form は「no longer supported」で GitHub-repo ベースの portal に移った。
6. **ComposioHQ**: ページに "Only collaborators can create PRs" とあり CONTRIBUTING は PR 経路を示す。→ 未解決（古い汎用 banner の可能性）。star 数も SEO 記事で 13k / 65k+ とあり、ページ読みは 78.4k。ページ読みを採る。
7. **hesreallyhim の star 数**: tracker の 46.9k（約 30 日で +4.1k）と repo ページの 57.0k。時点が違う。ページ読みを採り、成長が速いことの根拠としてのみ使う。
8. **skills.sh の規模**: 908,452（news.creeta.com 2026-07-08）と別資料の 1.29M。第三者同士で時点も異なる。`npm skills` の DL 数（1 月 24 万 → 7 月 4,440 万）も第三者で未検証。
9. **`/skill-doctor` の version**: docs は最低 v2.1.252、implicator.ai は 2.1.261 / 2026-09-04 出荷。docs が「最低 version」、blog が「出荷日」で矛盾でなく別の事実の可能性が高い。
10. **競合の需要判断**（competitors 内）: 「CLAUDE.md 系の話題」は数百 pts、「audit tool」は一桁 pt、Product Hunt は約 230 upvote で maintenance mode。需要が無いのではなく、公式が無料で持つようになった層と、人が見たい話題が別、という読み。一方、公式 stats では config 管理 plugin の install は 6 桁。→ 問題への関心は強いが、第三者 audit tool への関心は弱い。
11. **ElevenLabs の価格**: Starter が $6/月、同ページに $1 初月 promo も記載。ページ内の不整合。
12. **X の動画上限**: 出典間で不一致（Premium が約 3–4 時間と幅がある。2026-09-01 の API 上限変更は未検証）。公式ページ未取得。
13. **GitHub の rate limit 方針と作者の方針**: GitHub は backoff して再試行、作者は 429/403 を policy signal として停止（上記 7b・8）。実行する側の選択で、事実の矛盾ではない。
14. **claude-harness の 473 clones / 400 unique（14 日）**: notes は crawler と整合と読む（lead も同様）。実際の利用者かは区別できない。akc-cycle は同じ 14 日で 7 views。
15. 「lead の後日確認（2026-11-01、著者の personal-branding repo の akc-cycle RFC-0001 と skill plugin-directory-submit）: akc-cycle は 2026-07-15 に directory へ提出済みで live になっており、portal の Usage（2026-10-12、30 日）は install 268 / 266 account、使っている account 3。marketplace.json（official 315 / community 2,283）に無いことは『掲載されていない』を意味しない。v1.5.0 は reviewer 待ち。harness-scope の portal 状態は未確認。」

## Local evidence

出典はすべて lead の実行（2026-11-01、作者の machine）。`local-evidence.md` による。

- **初回 full run の実測**（`~/.claude`）: report 公開 2026-10-31T14:43:12Z（JST 23:43）、plan の commit が 22:51、skill の commit が 23:10 で、集計 + 突き合わせ + 公開まで約 30 分（subagent 3 batch）。apply は source ごとの 7 commit で翌 00:19–00:21 JST、承認 + 適用で約 35 分。→ 作者の「time to first wow」基準は開始から report まで約 30 分。
- **結果**: 192 件 = Retire 24 / Merge into boundary.md 1 / Improve 25 / Update 21 / Create 2 / Append 1 / Keep 114 / Out of scope 2 / Too Specific 2。source 別: skills 66（Keep 40、Improve 15、Update 8、Retire 1、Out of scope 2）、rules 18（Keep 15）、agents 9、hooks 33（Keep 21、Improve 5、Retire 4）、distill 4、docs 6、assets 56（Retire 19、Keep 33）。
- **競合 note の読み**: 非 Keep の 70 件（Retire 24 + Improve 25 + Update 21）は token 節約より強く性質が違う「wow」だが、n=1 で作者自身の harness。作者の rule（knowledge-staleness、akc-cycle の Scaffold Dissolution "Downward"）は Anthropic が 2026-07 に公表した視点（system prompt の 80% 削除）と同じ視点を既に持つ。
- **規模と cost**: 姉妹 audit skill の SKILL.md は合計 1,727 行（skill-stocktake 440、agent-stocktake 328、context-sync 295、rules-stocktake 239、rules-distill 155、repo-asset-stocktake 150、hook-stocktake 120）。**`total_cost_usd` は記録されていない**（`--output-format json` の capture なし）。月次の無人 run は launchd plist（day 1 07:00、`scripts/triage-tick.sh` + Herdr session、prompt file は `scripts/launchd/harness-stocktake-prompt.txt`）。report 媒体はデスクトップアプリの Artifact + ArtifactData `db`、Markdown fallback あり。
- **作者の他 repo（premise test）**: zenn-content（skills 8 / agents 6 / CLAUDE.md 78 行）、contemplative-agent（11 / 0 / 184）、paper-lab（6 / 5 / 20）、jev-research-pipeline（1 / 1 / 0）、personal-branding（1 / 0 / 29）、attention-not-self（0 / 0 / 105）。harness-stocktake の SKILL.md は `~/.claude` 向けで、**project scope の mode（global を除く）はまだ無い**。他人の harness は多くが project-level なので、この mode は配布の前提になる（cloud scheduled task や Action が見えるのも repo 内の `.claude/` に限る）。
- **公開 repo の実績**: akc-cycle（public plugin、v1.5.0、MIT、`.claude-plugin/plugin.json` + 自前 `marketplace.json`、stocktake の 7 source を含む 20 skills）は 3★・14 日で 7 views。claude-harness（`~/.claude` の一方向 public mirror）は 4★・473 clones / 400 unique（14 日、crawler と整合）。上位は jev-skill-router 20★、contemplative-agent 9★、pdf2anki 9★、harness-scope 6★、agent-knowledge-cycle 5★。X の follower は約 50（2026-10-11）。`GET /repos/shimo4228/akc-cycle/stargazers/history` は作者の token で動く。
- **Claude Code**: `claude --version` = 2.1.316。`--bare` は存在し（hooks / plugins / skills を飛ばす）、`-p` の既定には**まだなっていない**。
- **marketplace の現況**: community marketplace（2,283 plugins）に akc-cycle / harness-scope / harness-stocktake は無く、agnix、agent-smith と、audit / doctor / lint / health 名の約 48 件がある（claude-md-optimizer、claude-context-optimizer、please-optimize-my-claude、neko-harness-doctor、repo-hygiene、repo-doctor、skill-doctor、claude-code-audit-stack など）。公式の stats（2026-10-30 生成、324 plugins、all-time）: frontend-design 1,280,437、skill-creator 430,796、code-simplifier 372,557、**claude-md-management 315,197、claude-code-setup 224,255**、security-guidance 271,427、hookify 64,119。
- **GitHub code search**（legacy REST、認証あり）: `harness-stocktake filename:SKILL.md` は 1 件（作者の contemplative-agent）= 外部コピーなし。`skill-stocktake filename:SKILL.md` は **1,776 件**で、ECC（294,013★、fork 43,519、2026-10-30 push）の mirror / fork が中心（everything-claude-code-zh、everything-gemini-code、everything-openai-codex、awesome-codex-plugins、claude-skill-registry、x-cmd/skill など）。ECC の `skills/skill-stocktake/SKILL.md` は ECC 自身の版（品質 checklist + Quick Scan / Full Stocktake）で、作者の ECC への 11 PR（merged、2026-03-24 まで、memory）と ECC のローカル管理（ADR-0001 / 0008）が前史。`evaluated_at filename:results.json path:skills` は 4 repo で 19 file、うち 2 つが他人の repo にある stocktake の ledger（Akzelch/AkzelchCC と ovrsa/claude-harness。後者は作者の public mirror の copy の可能性が高い）で、残り 17 は無関係の `evals/results.json`。→ 作者の ledger 形式は少なくとも 2 つの外部 repo にあり、presence の集計は可能だが file 名が衝突する。`path:.claude/skills filename:SKILL.md` は約 507,900 file（fork・vendored copy 込み）。
- **personal-branding repo（private）の手続きで作者が参照を許したもの**: 2026-10-04 の listing 調査では外部への書き込みは無く、PR は作者を待つ状態。公式 directory に排他条項は無く、「listed in the Claude plugin directory」の表現は掲載後のみ、「official / endorsed」は使わない。hesreallyhim は web form のみ。harness-scope は 2026-10-03 に 3 list で merge され、当日の views は 0（placement は 158 行中 108 行目）。strategy §5 の規律: 面を跨いだ事実の一貫性、検証可能な artifact に結びついた主張、釣りタイトルと AI-slop をしない、bulk 投稿・bulk follow・自動エンゲージメントをしない（Wikidata ban 2026-07-16）、spam PR や backlink campaign をしない、list 自身の経路を通る awesome-list の PR は許可（「応募 = 自分の行為」）、LT と第三者 calendar は許可（2026-10-04 の作者決定）。成長期間 2026-09-08 → 2026-12-07 は follower の目標でなく instrument（事前登録の実験と月次 scorecard）。boundary.md: 公開・投稿・第三者 PR・提出・課金は作者の行為、rate limit の burst は policy signal（停止して報告、backoff しない）。

## Still unknown

**A. 作者にしか解けない**
- claude.ai/directory/manage の portal 上の akc-cycle v1.5.0 / harness-scope の状態（Draft / Scanning / Needs changes / In review / Approved / Published / Not live yet）と観測された review 日数。10-04 の提出が旧 Console form 経由なら移行が要るか。
- Anthropic 側の連絡窓口（directory@anthropic.com、contact-sales）に、(a) 月次・multi-subagent の plugin skill を利用者自身の subscription token で CI 実行するのが "ordinary, individual usage" か、(b) 無料の paste-a-URL audit service を運営者の API key で運営して「end users の代わりに払うな」条項に触れるか、を問うかどうか。
- hesreallyhim / walkinglabs / karanb192 / VoltAgent への申請の時期と順序（適格性は満たせるが、判断と申請は作者の行為）。walkinglabs は関係の開示が必須。
- 一次の作者の測定値: stocktake の per-run `total_cost_usd` と `modelUsage`（launchd 実行で `--output-format json` を取る）。1,000 repo の load の見積もりと「ordinary use」の判断に要る。
- 公開前に有料・課金が絡む選択肢（X API の funded account、ElevenLabs Starter）を使うか。

**B. 1 時間の local test で解ける**
- Action smoke test: 使い捨ての public repo で `plugins:` + `plugin_marketplaces:` を使い、akc-cycle 由来の複数 SKILL.md が sibling を参照する構成が `claude-code-action@v1` 内で入り `/akc-cycle:harness-stocktake` が走るか（plugin を `--marketplace owner/repo` で入れる経路も）。同時に `--bare` を付けない subscription token 経路を確認。
- 実際の harness で `/doctor`、`/doctor prompt-audit`、`/skill-doctor` を走らせて出力を stocktake の report と比べ、hooks の配線、ADR / README drift、skill / rule / agent を跨ぐ重複、台帳と実物の差を `/doctor` が見るかを確かめる（differentiation の主張の前提）。
- `stargazers/history` が token の scope なしで通るか、legacy `/search/code` の `path:` と `filename:` の精度、fork の扱い、`total_count` が 1,000 付近で信頼できるか（それぞれ認証付き 1 call）。
- Bluesky `searchPosts` を `api.bsky.app` と認証付き session で比べる。HN Algolia の endpoint syntax を 1 回の curl で確認。
- `claude plugin validate` と pre-submission checklist に対する自己点検（plugin が repo root にあるか、subfolder か、各 script が `${CLAUDE_PLUGIN_ROOT}` で path を名指ししているか）。
- Action の schedule が scheduled workflow のみの repo で 60 日後に止まるか（確認には時間がかかるため、`workflow_dispatch` や commit による回避の設計が現実的）。
- F5Bot の free で RSS / JSON / webhook が使えるか（登録して確認）。

**C. 未解決のまま残る（追加調査か時間の経過でしか分からない）**
- 各 list の最終 external merge 日、hesreallyhim の「overlap holdback」が既存 linter と重なる skill を通すか、受理率、ComposioHQ の PR 経路、VoltAgent に skillreaper が実在するか（残り約 134k 字が未読）、Chat2AnyLLM の CONTRIBUTING、claudemarketplaces.com の Submit form、SkillsMP の公式規則、2026-10-04 以降の新 list。
- 掲載位置別・list 規模別の流入の実測値。
- security scan が `~/.claude` の settings / hooks / rules を編集する skill、launchd plist を同梱する plugin を「permission 設定の変更」または Policy hold とするか（提出して初めて分かる可能性）。
- cloud / Desktop の scheduled task が `disable-model-invocation: true` の skill を名前で起動して実行するか。Artifact / ArtifactData が CLI の plugin skill で使えるか。
- lead の「project-unscoped hook は fail する」の根拠 rule の出所。
- `/doctor` 系が将来 branch 適用を持つかの roadmap（Anthropic の roadmap は見つからず）。
- どの audit tool にも人間の月次反復利用の証拠がない。「月次」が成立するかは未検証の仮定。
- Reddit / X の反応数（検索 tool が返さなかった）、各競合 repo の最終 commit・release 日、npm / brew の DL 数、Zenn / Qiita の原典と like 数。
- 公式の X / Bluesky / YouTube の数値上限、Remotion 4.0.539 の Apple Silicon 性能と hardware acceleration、Remotion 5.0 の license 変更の中身、Kokoro MLX の word timestamp、TTS の品質比較、Google Cloud TTS / Apple `say` / Azure の無料枠、GitHub README が user-attachments 経由の mp4 を 2026 年も描画するか。
- Reddit の新規 API 申請が今も承認されるか（「2026-10-31 停止」は未確認の噂）、X の公式価格 page、Syften / Google Alerts / newsletter 計測 / HN Firebase API / GitHub traffic の保存 tool。
- GitHub AUP の「最終更新日」、bulk issue / PR の「excessive」の閾値、config file の presence を数えることへの異議の有無、Gold & Krinke の全文、Zenodo の派生 dataset の policy、Allstar・CNCF ADOPTERS.md・GitHub「Used by」の確認。
- 時間から「1,000 repo」への換算: Renovate / Mergify 型の platform 掲載なしでの時間。claude-code-base-action の現況と `--bare` が `-p` の既定になる時期（失効条件）。Renovate / pre-commit.ci / Knip の adoption 数の算出法。

## Sources

読み方: 角度ごとに `URL — 何の根拠か — full / snippet — as-of 2026-11-01`。notes が path を伴わない host 名や repo 名だけで挙げたものはそのまま書く。fetch していない言及だけのものは `not fetched`。
### 1. awesome list / catalog（awesome-lists）
- github.com/thousandflowers/skillreaper — skillreaper の規模（62★ / 216 commits）、install 経路、掲載先 — full（repo ページ読み） — as-of 2026-11-01
- github.com/swaylq/danshari-skill — karanb192 の Meta Skills で 3 番目に載る entry — snippet（karanb192 README 内の引用。repo ページは角度 3 で読了） — as-of 2026-11-01
- skills.sh — 提出手続きなし・anonymous telemetry による自動掲載・順位は install 数 — full（vercel-labs/skills の docs / FAQ） — as-of 2026-11-01
- claudemarketplaces.com — crawler 型 catalog、editor review、Submit link — full（About ページ） — as-of 2026-11-01
- claudemarketplaces.com/skills/affaan-m/everything-claude-code/skill-stocktake — ECC の skill-stocktake が既に index 済み — snippet — as-of 2026-11-01
- raw.githubusercontent.com — hesreallyhim / karanb192 / walkinglabs / VoltAgent の CONTRIBUTING.md と vercel-labs/skills の creating-skills.md（notes に path 記載なし） — full — as-of 2026-11-01
- news.creeta.com — skills.sh「All Time 908,452」（2026-07-08、第三者） — snippet — as-of 2026-11-01
- stacktr.ee — skills.sh の recrawl に数日かかる（last updated 2026-08-22、第三者） — snippet — as-of 2026-11-01
- ecosyste.ms — 「~3% acceptance」を検証できない根拠（8 issues / 19 PRs の tracker が古い） — snippet — as-of 2026-11-01
- awesomeskills.dev — audit 系 skill が多数 index されている（category が混んでいる）証拠 — snippet — as-of 2026-11-01
- openskillindex.com — 同上 — snippet — as-of 2026-11-01
- claudskills.com — 同上 — snippet — as-of 2026-11-01
- agentskill.sh — 同上 — snippet — as-of 2026-11-01
- claudepluginhub.com — 同上 — snippet — as-of 2026-11-01
- mcpmarket.com — 同上 — snippet — as-of 2026-11-01
- tessl.io（registry） — 同上 — snippet — as-of 2026-11-01
- vibeindex.ai — 同上 — snippet — as-of 2026-11-01
### 2. 公式 directory と `/doctor` 系（plugin-directory）
- claude.com/docs/plugins/submit — 提出経路・plan 要件・10 提出 / org / 24h — full — as-of 2026-11-01
- claude.com/docs/plugins/pre-submission-checklist — block / Policy hold / security scan の基準 — full — as-of 2026-11-01
- claude.com/docs/plugins/platform-support — Skills / hooks / agents / `bin/` の載る面 — full — as-of 2026-11-01
- claude.com/docs/directory/publish — 配置と verified badge に申請手段なし、Usage tab — full — as-of 2026-11-01
- claude.com/docs/directory/submission-status — 状態語彙（Draft から Withdrawn まで） — full — as-of 2026-11-01
- code.claude.com/docs/en/plugin-marketplaces — marketplace.json の仕様、source 型、pin — full — as-of 2026-11-01
- code.claude.com/docs/en/plugins/components — plugin は scheduled routine を宣言できない（component 一覧） — full — as-of 2026-11-01
- code.claude.com/docs/en/plugins/cli-reference — `claude plugin install --marketplace owner/repo`（抜粋） — full — as-of 2026-11-01
- code.claude.com/docs/en/plugins/anthropic-marketplaces — 公式 / community の 2 marketplace と web catalog の記述 — full — as-of 2026-11-01
- code.claude.com/docs/en/plugins/measure — 未使用 plugin の表示、install 計測の範囲 — full — as-of 2026-11-01
- code.claude.com/docs/en/discover-plugins — install page、auto-update の既定 — full — as-of 2026-11-01
- code.claude.com/docs/en/commands — `/doctor` / `/skill-doctor` の記述 — full — as-of 2026-11-01
- code.claude.com/docs/en/skills — `/doctor prompt-audit`、`disable-model-invocation` と scheduled task — full — as-of 2026-11-01
- code.claude.com/docs/en/debug-your-config — `/doctor` の setup checkup — full — as-of 2026-11-01
- code.claude.com/docs/en/routines — cloud scheduled tasks の仕様 — full — as-of 2026-11-01
- code.claude.com/docs/en/scheduled-tasks — Desktop / session-scoped scheduling — full — as-of 2026-11-01
- code.claude.com/docs/en/plugin-evals — `claude plugin eval`（要約と intro のみ、62 KB 超は途中まで） — snippet — as-of 2026-11-01
- support.claude.com/13145358 — Directory Policy（1G / 2F / 2G 等、"Updated this week" で日付なし） — full（長いため一部 truncated） — as-of 2026-11-01
- anthropics/claude-plugins-official — 約 315 entries、config audit category なし、README の submit 経路 — full（README + marketplace.json を 2 chunk で計数） — as-of 2026-11-01
- anthropics/claude-plugins-community — nightly sync、手動 add、約 140 entries を先頭から読んだ — snippet（marketplace.json は先頭約 100k 字のみ） — as-of 2026-11-01
- claude.com/marketplace/plugins — 528 plugins、install 数と featured 欄が見えない — full（page fetch） — as-of 2026-11-01
- claude.com/plugins — directory の web 面 — full（page fetch） — as-of 2026-11-01
- claude.ai/directory/manage — 提出 portal（作者のみ閲覧） — not fetched — as-of 2026-11-01
- clau.de/plugin-directory-submission — 公式 marketplace README が示す提出 form — not fetched — as-of 2026-11-01
- anthropics/claude-code issue #29971 — 「Context Bloat」需要の薄い証拠（stale close、7 thumbs-up） — snippet + fetch — as-of 2026-11-01
- anthropics/claude-code issue #81615 — role-scoped config の要望（title のみ） — snippet — as-of 2026-11-01
- anthropics/claude-code issue #32163 — CLAUDE.md rule を hook で強制する要望（title のみ） — snippet — as-of 2026-11-01
- anthropics/claude-code issue #90350 — conflicting な governance artifact の多さ（title のみ） — snippet — as-of 2026-11-01
- joshukraine/dotfiles#252 — Anthropic 職員が model 更新後に CLAUDE.md / skills / hooks を削ると言ったという二次情報 — snippet — as-of 2026-11-01
### 3. 競合と需要（competitors）
- https://code.claude.com/docs/en/skills — `/skill-doctor`（"Find unused skills"）と prompt-audit — full（先頭 100k 字） — as-of 2026-11-01
- https://code.claude.com/docs/en/commands — `/skill-doctor` / `/doctor` の表の行 — full — as-of 2026-11-01
- https://www.implicator.ai/anthropic-claude-code-skill-doctor-context-audit/ — `/skill-doctor` の出荷時期・批判、`/doctor` の変遷、Thariq の 80% 削除 — full — as-of 2026-11-01
- https://github.com/anthropics/claude-code/releases/tag/v2.1.283 — `/doctor prompt-audit` の一次 — full — as-of 2026-11-01
- https://dev.to/piekwerk/claude-code-21283-ships-a-config-linter-what-doctor-prompt-audit-changes-for-your-claudemd-51f5 — "smoke detector, not a building inspector" — full — as-of 2026-11-01
- https://github.com/khendzel/skills-janitor — 124★、maintenance mode 宣言 — full（README） — as-of 2026-11-01
- https://www.producthunt.com/products/skills-janitor/reviews — Product Hunt 224–235 upvotes、review 0 — full — as-of 2026-11-01
- https://github.com/swaylq/danshari-skill — danshari の分類・5 問・blind test・archive — full（README） — as-of 2026-11-01
- https://github.com/thousandflowers/skillreaper — skillreaper の verdict・prune・n=1 の数値 — full（README） — as-of 2026-11-01
- https://github.com/agent-sh/agnix — 462★、757 rules、Show HN の反応 — full（README） — as-of 2026-11-01
- https://github.com/tw93/Waza — 7.5k★、`/health` — full（README） — as-of 2026-11-01
- https://github.com/alexgreensh/token-optimizer — 2.8k★、自己申告の token 節約 — full（README） — as-of 2026-11-01
- https://dev.to/sfrangulov/i-installed-116-claude-code-skills-after-30-days-id-used-35-1f50 — skill-graveyard（116 件中 35 件使用） — full（blog） — as-of 2026-11-01
- https://claudskills.com/skills/audit-harness-fit/ — 形が最も近い audit-harness-fit（verdict + 承認） — full（listing page のみ） — as-of 2026-11-01
- https://github.com/uzysjung/uzys-agent-harness — audit-harness-fit の repo — not fetched — as-of 2026-11-01
- https://dev.to/sisyphusse1ops/i-shipped-cc-audit-as-a-github-action-now-your-claudemd-gets-linted-on-every-pr-5fal — cc-audit の GitHub Action（反復は自動化のみ） — snippet — as-of 2026-11-01
- https://pypi.org/project/claude-config-auditor/ — 静的 lint の競合 — snippet — as-of 2026-11-01
- https://github.com/pthm/cclint — 静的 lint の競合 — snippet — as-of 2026-11-01
- https://claudepluginhub.com/plugins/pdugan20-claudelint — claudelint の掲載 — snippet — as-of 2026-11-01
- https://forum.cursor.com/t/i-built-a-linter-for-cursor-rules-npx-cursor-lint/152119 — Cursor 側の cursor-doctor — snippet — as-of 2026-11-01
- https://lol-website.netlify.app/blog/your-ai-skills-are-rotting/ — 週次 review の n=1 逸話（25 skills 中 6 が stale） — snippet（notes に読了の記載なし） — as-of 2026-11-01
- https://dev.to/shimo4228/where-to-put-a-coding-agents-knowledge-and-how-to-make-it-stick-161g — plain skills の invocation 6%（作者自身の記事で独立でない） — snippet — as-of 2026-11-01
- claudeissues.com（issue 76276） — `/doctor` の docs-gap issue（lost instructions の報告なし） — snippet — as-of 2026-11-01
- dev.classmethod.jp — `/doctor` の日本語紹介（2026-07-10、2026-09-24） — snippet — as-of 2026-11-01
### 4. dev tool の広がり方と activation（devtool-activation）
- https://changelog.com/podcast/289 — Renovate の OSS 化から約 14 か月で約 5,000 project、Marketplace の効果 — full（transcript） — as-of 2026-11-01
- https://docs.renovatebot.com/getting-started/installing-onboarding/ — onboarding PR（merge まで何も変わらない、close = 既定値） — full — as-of 2026-11-01
- https://www.plushcap.com/content/github/blog/github-goodbye-dependabot-preview-hello-dependabot — Dependabot Preview の 3 万 org 超 — snippet — as-of 2026-11-01
- https://julien.danjou.info/blog/one-year-of-mergify/ — Mergify の 1 年で約 30k repo、guinea pig、Marketplace — full — as-of 2026-11-01
- https://blog.mergify.com/mergify-looking-back-at-2022 — Mergify 130k repo（会社報告） — snippet — as-of 2026-11-01
- https://astral.sh/blog/announcing-astral-the-company-behind-ruff — Ruff の月 100 万 DL、「disbelief」、stars は vanity metric — full — as-of 2026-11-01
- github.com/webpro-nl/knip — Knip 12.6k★ — full（API 読み） — as-of 2026-11-01
- https://github.com/webpro-nl/knip/network/dependents — Knip の dependents 22,611 repo — full（API 読み） — as-of 2026-11-01
- https://smashingmagazine.com/2023/08/knip-automated-tool-find-unused-files-exports-dependencies/ — Knip の作者本人の記事（2023-08） — snippet — as-of 2026-11-01
- https://changelog.com/news/p8re — all-contributors bot の発表（2019-01-30） — full — as-of 2026-11-01
- https://arxiv.org/abs/2511.04453v1 — HN 露出後の star の効果量（138 repo） — full（abstract） — as-of 2026-11-01
- https://danfking.github.io/blog/2026/04/23/show-hn-by-the-numbers/ — 188,085 件の Show HN 分析（相関） — full — as-of 2026-11-01
- https://research.swtch.com/telemetry-opt-in — Go の telemetry opt-in の経緯と標本数 — full — as-of 2026-11-01
- https://docs.brew.sh/Analytics — Homebrew の analytics（既定 ON、公開集計） — full — as-of 2026-11-01
- https://turborepo.dev/docs/telemetry — Turborepo の telemetry（DO_NOT_TRACK、payload 表示） — full — as-of 2026-11-01
- https://github.com/styled-components/polished/issues/567 — Scarf を巡る反発 — snippet — as-of 2026-11-01
- https://github.com/scarf-sh/scarf-js/blob/HEAD/./WHY.org — Scarf の設計意図 — snippet — as-of 2026-11-01
- https://docs.github.com/en/enterprise-cloud@latest/github-cli/github-cli/github-cli-telemetry — gh CLI の telemetry — snippet — as-of 2026-11-01
- https://news.ycombinator.com/showhn.html — Show HN の規則 — full — as-of 2026-11-01
- https://changelog.com/news/submit — Changelog News の自己投稿規則 — full — as-of 2026-11-01
- https://console.dev/ — Console.dev の構成（投稿手順は見つからず） — full（front page のみ） — as-of 2026-11-01
- https://www.producthunt.com/p/general/product-hunt-s-state-of-tech-discovery-q2-2026 — Product Hunt の Dev Tools 633 launch・平均 upvote — snippet — as-of 2026-11-01
- https://zenn.dev/iizuka0000/articles/zenn-trend-history-introduction — Zenn の trend list が RSS で取れること — full — as-of 2026-11-01
- https://dev.to/jun_uen0/when-should-you-publish-a-dev-post-i-counted-and-jp-vs-en-are-mirror-images-2pc7 — Zenn / Qiita の投稿時刻の小標本相関 — full — as-of 2026-11-01
- https://carpentries-incubator.github.io/rapid-usability-tutorial/key-points.html — rapid usability testing（約 10 人、1 時間以内） — full — as-of 2026-11-01
- github.blog（Octoverse 2019） — Dependabot の自動更新 PR 数 — snippet — as-of 2026-11-01
- analyticsindiamag — Ruff が数か月で大手に採用されたという二次要約 — snippet — as-of 2026-11-01
- korben.info — gh CLI telemetry の反応（403 で読めず） — not fetched — as-of 2026-11-01
- daily.dev — time to first value の定義（vendor / blog） — snippet — as-of 2026-11-01
- chabot.dev — 同上 — snippet — as-of 2026-11-01
- vectree.io — 同上 — snippet — as-of 2026-11-01
### 5. GitHub Action と「入れずに試す」（github-action）
- https://github.com/anthropics/claude-code-action/releases — v1.0.266（2026-10-31）、v1.0.264 の変更 — full — as-of 2026-11-01
- https://raw.githubusercontent.com/anthropics/claude-code-action/main/action.yml — action の入力と出力 — full — as-of 2026-11-01
- https://code.claude.com/docs/en/github-actions — "Run a skill" 節、schedule の 60 日停止、権限 — full — as-of 2026-11-01
- https://github.com/anthropics/claude-code-action/issues/639 — plugin 未読込の過去障害（v1.0.15 で対応） — full（summarizer 経由） — as-of 2026-11-01
- https://code.claude.com/docs/en/authentication — `claude setup-token`、認証の優先順 — full — as-of 2026-11-01
- https://code.claude.com/docs/en/legal-and-compliance — "ordinary, individual usage"、end users の代わりに払わない条項 — full — as-of 2026-11-01
- support.claude.com/en/articles/15036540 — Agent SDK / `claude -p` の subscription 課金の状態（2026-10-07 更新） — full（summarizer 経由） — as-of 2026-11-01
- https://code.claude.com/docs/en/headless — `claude -p` の skill 起動、Manual mode、hook 実行の安全面 — full — as-of 2026-11-01
- https://code.claude.com/docs/en/artifacts — Artifact は Action / `-p` で既定 OFF — full — as-of 2026-11-01
- https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary — Step Summary の上限と GFM — full — as-of 2026-11-01
- https://github.com/peter-evans/create-pull-request — 固定 branch での PR 更新 — full（summarizer 経由） — as-of 2026-11-01
- peter-evans/create-issue-from-file — issue 本文の更新（`issue-number`） — full（summarizer 経由） — as-of 2026-11-01
- peter-evans/find-comment — comment の検索（PR で not found の報告あり） — snippet — as-of 2026-11-01
- peter-evans/create-or-update-comment — comment の upsert — full（summarizer 経由） — as-of 2026-11-01
- https://docs.renovatebot.com/key-concepts/dashboard/ — Dependency Dashboard（1 report・1 承認の先例） — full（summarizer 経由） — as-of 2026-11-01
- https://docs.github.com/en/actions/sharing-automations/creating-actions/publishing-actions-in-github-marketplace — Marketplace 掲載の要件 — full（summarizer 経由） — as-of 2026-11-01
- https://code.claude.com/docs/en/agent-sdk/hosting — 1 agent の資源、container 費と token 費、multi-tenant の設定 — full — as-of 2026-11-01
- https://code.claude.com/docs/en/routines — cloud scheduled tasks の仕様 — snippet（保存した page を grep しただけ） — as-of 2026-11-01
- code.claude.com/docs/en/code-review — managed Code Review（workflow file 不要の先例） — not fetched — as-of 2026-11-01
- securityscorecards.dev/viewer/?uri=github.com/<owner>/<repo> — OpenSSF Scorecard の web viewer（paste-a-URL の先例候補） — snippet — as-of 2026-11-01
- api.scorecard.dev — Scorecard の REST API — snippet — as-of 2026-11-01
- github.blog（2022-01-31） — Actions の "Used by" が dependency graph 由来 — snippet — as-of 2026-11-01
- GitHub discussion #199447 — 大規模 action でも "Used by" widget が出ない報告 — snippet — as-of 2026-11-01
- anthropics/claude-code issue #78287 — scheduled cloud routine で marketplace plugin の skill が "Unknown skill" になる報告 — snippet — as-of 2026-11-01
### 6. 動画・画像 pipeline（video-pipeline）
- registry.npmjs.org/remotion/latest — remotion@4.0.539 と license field — full — as-of 2026-11-01
- github.com/remotion-dev/remotion/blob/main/LICENSE.md — Free License（3 人以下）と Company License、5.0 での変更予告 — full — as-of 2026-11-01
- remotion.pro/license — license 条件と価格 — full — as-of 2026-11-01
- remotion.dev/docs/ai/skills — 公式 agent skill（install コマンドは site 間で差） — snippet — as-of 2026-11-01
- ofershap/remotion-readme-kit — CliDemo / CodeBeforeAfter / FeatureShowcase（MIT、未成熟） — full — as-of 2026-11-01
- fay-saal/codemotion — git diff から typewriter 動画 — snippet — as-of 2026-11-01
- 21st.dev — Remotion component（API key 要） — snippet — as-of 2026-11-01
- shreefentsar/remotion-video-toolkit — JSON props 駆動の "Wrapped" 型動画 — snippet — as-of 2026-11-01
- developers.openai.com/api/docs/pricing — OpenAI TTS の価格 — full — as-of 2026-11-01
- elevenlabs.io/pricing — ElevenLabs の価格と商用 license — full — as-of 2026-11-01
- learn.microsoft.com（how-to-speech-synthesis） — Azure Speech の `WordBoundary` event — full（先頭 100k 字） — as-of 2026-11-01
- huggingface.co/hexgrad/Kokoro-82M — Kokoro-82M の license と voices — full — as-of 2026-11-01
- icp0.io — Kokoro + Remotion の dev blog（2025-11-24、JSON から語り付き動画） — full — as-of 2026-11-01
- mattmireles/kokoro-coreml — Apple Silicon 向け Kokoro port — snippet — as-of 2026-11-01
- github.com/charmbracelet/vhs — vhs v0.12.1、tape file から GIF / MP4 — full — as-of 2026-11-01
- GitHub API releases/latest（charmbracelet/vhs） — v0.12.1 の公開日 2026-09-24 — full — as-of 2026-11-01
- github.com/asciinema/agg — agg の license と Release の状態 — full — as-of 2026-11-01
- docs.github.com（attaching-files） — GitHub の画像・動画の上限 — full — as-of 2026-11-01
- zenn.dev/zenn/articles/markdown-guide — Zenn の埋め込み可否（mp4 なし） — full — as-of 2026-11-01
- bsky.network/docs/tutorials/video — Bluesky の動画 API（`getUploadLimits`、数値なし） — full（数値は記載なし） — as-of 2026-11-01
- support.google.com — YouTube Shorts の公式仕様 — not fetched — as-of 2026-11-01
- charmbracelet/gum — README に demo GIF（VHS 製） — full（README） — as-of 2026-11-01
- jesseduffield/lazygit — README に mp4 demo — full（README） — as-of 2026-11-01
- junegunn/fzf — README は PNG と YouTube link — full（README） — as-of 2026-11-01
- astral-sh/ruff — README は SVG の benchmark 図のみ — full（README） — as-of 2026-11-01
- webpro-nl/knip — README は logo と badge のみ — full（README） — as-of 2026-11-01
- biomejs/biome — README は logo と badge のみ — full（README） — as-of 2026-11-01
- vhs.charm.sh/vhs-<id>.gif — gum の demo GIF の置き場（VHS 製） — full（gum の README 内の参照） — as-of 2026-11-01
### 7. 倫理と platform 規則（ethics-unsolicited）
- https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies — AUP の Sec 4 / 7 / 8 / 10 — full（digest） — as-of 2026-11-01
- https://docs.github.com/en/site-policy/github-terms/github-terms-of-service — ToS（2026-04-27 効力）Sec H の API 規定 — full（digest） — as-of 2026-11-01
- https://docs.github.com/en/rest/search/search — Search code 10 req/min、1,000 件上限 — full（digest） — as-of 2026-11-01
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api — secondary limit と停止の警告 — full（digest） — as-of 2026-11-01
- https://www.theregister.com/2020/10/01/digitalocean_hacktoberfest_pull_request_spam/ — Hacktoberfest 2020 の spam — snippet — as-of 2026-11-01
- https://drewdevault.com/blog/Spamtoberfest/ — 同上 — snippet — as-of 2026-11-01
- https://developerrelations.com/case-studies/overcoming-hacktoberfest-spam — opt-in（topic）化の解決策 — snippet — as-of 2026-11-01
- https://www.theregister.com/2026/02/03/github_kill_switch_pull_requests_ai — GitHub PM が低品質 contribution の増加を重大と述べた — full（digest） — as-of 2026-11-01
- https://github.blog/changelog/2026-02-13-new-repository-settings-for-configuring-pull-request-access/ — PR をオフ / collaborator のみにする repo 設定 — snippet — as-of 2026-11-01
- https://www.theregister.com/2026/01/21/curl_ends_bug_bounty/ — curl の bug bounty 終了 — snippet — as-of 2026-11-01
- https://socket.dev/blog/ai-agent-lands-prs-in-major-oss-projects-targets-maintainers-via-cold-outreach — Kai Gritun（95 repo に 103 PR） — full（digest） — as-of 2026-11-01
- https://arxiv.org/abs/2103.13950 — bot の noise に関する CSCW 2021 — snippet — as-of 2026-11-01
- https://www.ime.usp.br/~gerosa/papers/CSCW2021Wessel.pdf — 同論文の PDF — snippet — as-of 2026-11-01
- https://www.theregister.com/2026/02/24/github_dependabot_noise_machine/ — Valsorda の「noise machine」 — snippet — as-of 2026-11-01
- docs.github.com/en/code-security/...（dependabot-updates-stopped の page、notes では URL の末尾が省略） — Dependabot の自動停止（90 日） — snippet — as-of 2026-11-01
- https://nesbitt.io/2026/02/13/respectful-open-source — 「automated audits are withdrawals」、pull 型の勧め — full（digest） — as-of 2026-11-01
- https://arxiv.org/pdf/2505.20186 — Leiden path-traversal study（patch 14%） — snippet — as-of 2026-11-01
- https://arxiv.org/abs/2302.11985 — 392 issue で返信 21%、5/15 が bot と思われた — full（html の digest） — as-of 2026-11-01
- https://uwaterloo.ca/computer-science/news/many-open-source-projects-lack-clear-way-report-security — Waterloo の 15 issue + 15 PR で spam flag — full（digest） — as-of 2026-11-01
- https://lwn.net/Articles/854401 — UMN hypocrite commits — snippet — as-of 2026-11-01
- https://cse.umn.edu/node/102516 — 同上（UMN の声明） — snippet — as-of 2026-11-01
- https://projectzero.google/2025/07/reporting-transparency.html — Project Zero の Reporting Transparency — snippet — as-of 2026-11-01
- https://arxiv.org/abs/2202.11969 — MSR の再識別リスク（Vidoni & Diaz Ferreyra） — full（ar5iv の digest） — as-of 2026-11-01
- https://arxiv.org/abs/2602.14690 — 2,853 repo を走査した harness engineering 研究 — full（abstract のみ） — as-of 2026-11-01
- https://rywalker.com/research/agents-md-standard — AGENTS.md の採用数の数え方 — snippet — as-of 2026-11-01
- https://docs.brew.sh/Analytics — Homebrew analytics（opt-out、365 日保持） — snippet（ethics note では引用のみ。全文は角度 4） — as-of 2026-11-01
### 8. 反応監視 API（reaction-monitor）
- https://docs.github.com/en/rest/metrics/traffic — traffic API（直近 14 日、write 権限） — full — as-of 2026-11-01
- https://github.blog/changelog/2026-06-30-upcoming-access-restrictions-to-public-api-endpoints-and-ui-views/ — `/stargazers`・`/subscribers` の制限 — full — as-of 2026-11-01
- https://github.blog/changelog/2026-09-04-new-api-endpoint-provides-privacy-safe-star-history-data — star history endpoint の新設 — full（薄い） — as-of 2026-11-01
- https://docs.github.com/en/rest/activity/starring?apiVersion=2026-03-10 — `stargazers/history` の形 — full — as-of 2026-11-01
- https://www.star-history.com/blog/github-stargazer-api-restriction — 他人の repo のチャートが壊れた件（自己矛盾あり） — full — as-of 2026-11-01
- https://docs.github.com/en/rest/search/search — legacy code search の制限 — full — as-of 2026-11-01
- https://docs.github.com/en/search-github/searching-on-github/searching-code — REST は legacy syntax という一文 — full（その一文のみ） — as-of 2026-11-01
- https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax — 新 syntax（`path:`、`is:fork`） — full — as-of 2026-11-01
- fulll.github.io/github-code-search/reference/github-api-limits — 1,000 件で silent に切れる、fork は既定で除外 — snippet — as-of 2026-11-01
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api — PAT 5,000/h、secondary limit — full — as-of 2026-11-01
- GitHub discussion #199447 — "Used by" widget が出ない大規模 action — snippet — as-of 2026-11-01
- https://raw.githubusercontent.com/anthropics/claude-plugins-official/refs/heads/stats/stats/plugin-installs.json — `unique_installs`（2026-10-30 生成、324 plugins） — full（live JSON） — as-of 2026-11-01
- tangled.org/oppi.li/claude-code — plugin-installs.json を取りに行く CLI source の第三者 mirror — full — as-of 2026-11-01
- claudeissues.com（issue #46163） — plugin 作者向け analytics の要望（2026-05 close） — snippet — as-of 2026-11-01
- https://hn.algolia.com/api — HN Algolia API（10,000 req/h/IP、url 検索） — full（薄い） — as-of 2026-11-01
- https://hacker-news.firebaseio.com/v0 — HN Firebase API — not fetched（notes は再読せず） — as-of 2026-11-01
- docs.bsky.app — Bluesky の公式 docs（stub に redirect され読めず） — not fetched — as-of 2026-11-01
- bsky-docs issue #332 — `public.api.bsky.app` が 403 という第三者報告（2026-08-18 archived） — snippet — as-of 2026-11-01
- https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy — Reddit の事前承認制（fetch は 403） — snippet — as-of 2026-11-01
- redditapis.com — Reddit API の自己登録終了などの第三者記述 — snippet — as-of 2026-11-01
- keyapi.ai — 「2026-10-31 に新規申請停止」という未確認の記述 — snippet — as-of 2026-11-01
- opentweet.io/x-api-pricing — X API の pay-per-use 価格（vendor、docs.x.com と 2026-10-10 に照合済みと自称） — snippet — as-of 2026-11-01
- developer.x.com — X の公式価格 page（402 で読めず） — not fetched — as-of 2026-11-01
- docs.x.com — X の公式 docs — not fetched — as-of 2026-11-01
- https://developers.buffer.com/guides/post-metrics.md — Buffer の post metrics、`link_clicks` 不可、`insightsRead` — full — as-of 2026-11-01
- https://developers.buffer.com/guides/api-limits.md — Buffer の limit と 429 で停止する指針 — full — as-of 2026-11-01
- https://f5bot.com/faq — F5Bot（Reddit / HN / Lobste.rs）の free 版と配信方法 — full — as-of 2026-11-01
- https://developers.forem.com/api/v1 — Dev.to / Forem の articles と analytics API — full（先頭 100k 字） — as-of 2026-11-01
- qiita.com/api/v2/docs — Qiita API の rate limit と `page_views_count`（確認先として挙げただけ） — not fetched — as-of 2026-11-01
- https://zenn.dev/api/articles?username=... — Zenn の公開 JSON（`liked_count`、views なし） — snippet — as-of 2026-11-01
- https://zenn.dev/api/me/articles — Zenn の cookie 認証の非公式 endpoint（views） — snippet — as-of 2026-11-01
- shields.io — endpoint badge の仕様（描画回数は runs でない） — full — as-of 2026-11-01

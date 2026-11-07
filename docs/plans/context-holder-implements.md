# 実装はタスクの文脈を持つ Opus が行い、Fable は委譲、triage は local の fresh build — と常駐層の簡素化

## Context

著者の依頼（2026-11-07）は 3 つ。

1. 「最近は委譲より、文脈を持つ agent に実装させるほうがよい」という話の状況を調べる。
2. task-triage を最適化する。
3. rules・CLAUDE.md などの不要物を減らし、モデルの性能を引き出す環境にする。

同じ会話で著者は 4 つの方針を示した。

- (a) 文脈を持つ agent に実装させる
- (b) Fable の session は委譲が既定（トークン効率が悪すぎる）
- (c) cloud session は無理に使わない。余計な文脈を持たせないためなら使ってよい
- (d) モデルをマイクロマネジメントしない

調査 report:

- 外部（as-of 2026-11-07）: [research/2026-11-07-context-holder-implements.md](research/2026-11-07-context-holder-implements.md)
- 内部（実績と実物）: [research/2026-11-07-context-holder-implements-internal.md](research/2026-11-07-context-holder-implements-internal.md)
- 前提として読んだもの: 10-26 の [subagent-fold 調査](research/2026-10-26-subagent-fold.md)、10-27 の [再生比較](research/2026-10-27-replay-result.md)

この plan 自体も、3 観点の反証 review（著者の方針との整合・依存の破損・証拠の読み）を通して直した。

### 調べて分かったこと

1. **「文脈を持つ者が実装せよ」と明言する Anthropic の一次資料は無い。**
   - 最も近いのは 2 つ。sub-agents docs の「計画・実装・テストが文脈を共有するなら主会話で」と、best-practices の「同じ task を subagent に渡しても答えは良くならない」。
   - 10-22 の fold の記事は、製品 agent を機能ごとの subagent に割る設計への批判で、coding task の受け渡しは扱っていない。
   - 同じ best-practices が「書き上げた spec から fresh session で実装」も推している。
   - 文脈を持つ実装者と fresh な実装者を同じ coding task で比べた公開の測定は無い。測定で分かっているのは、文脈つきの引き継ぎが効率を上げることだけ（Handoff Debt、events −20〜59%）で、成否の差は小さい。
2. **文脈保持者には盲点があり、fresh な照合が拾ってきた。**
   - contemplative-agent の RFC-0022 では、著者と設計を詰めた session 自身が論文を 3 か所読み違え、そのまま実装に流れた。その RFC の結論は「設計した session が読み直しても同じ盲点を踏む。fresh context の別 session に照合させる」だった。
   - packet の build は、Phase 0 で packet か判断役の前提の 15〜18% を反証してから実装している（`Premise:` 行を持つ 69 commit のうち 10〜12 件）。
   - packet による読み違いの差し戻しは記録上 0 件だが、帳簿（`logs/effort-outcomes.jsonl`）は 11-04 以降と 9 月の数本が欠けていて、判断材料にならない。
3. **triage に届くタスクには、文脈を持つ者がもういない。**
   - 判断役の session は、CLI の版がほぼ毎 cycle 上がるので実質毎回作り直される（作り直しの条件は版の変化か 7 日。10-17 以降 13/13）。その文脈は台帳全体の判定で、約 15〜36 万 token ある。
   - 判断役が判定のあと同じ session で実装する形は、10-27 の事前登録つき再生比較で、既定を変える条件（規則 1）を満たさなかった。2/16 対 0/16（うち 1 本は環境由来の verify 失敗で、除くと 1/16 対 0/16）で偶然と区別できないので、「判断役の実装は悪い」という証拠ではない。言えるのは「既定を変える根拠が無い」こと。
   - 原因として読めたのは 1 型だけ。ADR と doc の多い feat で、context が compact の閾値 400K に近づいたときに、packet の細部の指示を保てなかった。本番の判断役はその帯域で動いている。
4. **Fable の委譲は著者の方針で、cost page が向きを裏づける。**
   - Fable 5.1 単独は、Opus 5.5 の high の 2.2〜3.0 倍の費用でスコアは上がらない。SWE-bench Pro では、Opus 5.5 の medium が約 1/5、high が約 1/4 の費用で同等の成績を出す（platform.claude.com の cost page）。
   - 「Fable が判断し、Opus が build する」構成そのものは測られていない。Fable を orchestrator にすると +24% で利得は無い。
   - fork は親と同じ model で走るので、Fable の session から fork しても委譲にならない。
5. **重いのは委譲そのものより、委譲を細かく縛る機構。**
   - task-triage SKILL.md は 488 行で、うち §3・§4 が 38%。packet template は 185 行で、小さな修正では diff より長い（例: packet 89 行・diff 46 行）。
   - packet ごとの effort の選択は毎回動いたが、効果は対照が無く未測定。見落としで effort を上げる規則は 16 本以上の build で 1 回だけ発火した。Agent の経路では、選んだ値を適用できていなかった。
   - 「Agent tool は effort を取らない」（SKILL.md:263-266）は実物とずれている。CLI 2.1.319 の Agent tool は呼び出しごとに effort を取る。
6. **常駐層には古い行と重複がある。期待できる効果は性能ではなく、費用とノイズの削減。**
   - 外部の測定でも、context file は成否を上げず、費用を 20% 超増やす（Gloaguen）。size の効果は null（McMillan）。
   - 挙動の歪みとして観測できたのは plugin の自発選択だけ。pr-review-toolkit の code-reviewer が、抑止の注記の後も 27 回起動した（再生比較の run を除いた数）。
   - 量として最大なのは hook の差し込みで、14 日で task-claims-reminder が 2,107 回・626K 字、review-chain-notice が 3,140 回・267K 字。

## 決めたこと（★ は影響の大きい代理決定）

### 1. 実行者は、モデルとタスク固有の文脈で決める（著者の方針 a・b）

- **Opus の session**: そのタスクを著者と詰めた session が自分で実装する。これが既定。
  - 起票して triage に回すのは、その場で終えないと決めたものだけになる。著者の (a) は、この経路で実現する。
- **Fable の session**: 実装は Opus に委譲する（既定）。
  - 委譲先は session が選ぶ。plan を渡した `Agent(model: "opus")` か、skill `spawn-session` の Opus session。
  - fork は親の model と文脈を継ぐので、Fable のままになる。
  - 「実行者の決定」を plan に 1 行書くのは Fable の session だけにする。hook `plan-executor-notice.sh` がもう Fable のときだけ知らせている。
- **review は、誰が実装しても別 process で 1 段回す**: built-in `/code-review`（effort medium）。根拠は ADR-0055 と、`/code-review` が分岐の漏れを拾った contemplative-agent RFC-0046 S40。
  - 脅威面を動かす diff には、今の matrix どおり security-reviewer を並列に回す（RFC-0067 S47 の HIGH を拾ったのはこれ）。
  - 外部資料に依る diff では、reviewer に引用元も渡す（RFC-0022 の型）。
- **用語**: 「judge-tier / build-tier」の語を外し、model 名で書く。

### 2. task-triage — local の fresh build を既定にし、cloud は任意、細かく縛る機構を外す

- **判断役は台帳のタスクを自分で実装しない**（今の既定を保つ）。
  - 変える根拠が測定に無い（Context 3）。
  - fresh な build の Phase 0 は、判断役の前提を独立に確かめる唯一の工程である（Context 2）。
  - 判定のあとに fork する案は採らない。fork は判断役の台帳全体の文脈を継ぐので、再生比較で読めた失敗の型（compact の閾値近く）と同じ帯域に入る。
- **既定の実行者**: 判断役から出す `Agent(subagent_type: "general-purpose", model: "opus", isolation: "worktree")`。
  - effort は省き、session の値（high）で走らせる。下げる・上げる理由があるときだけ判断役が渡す（例: docs だけの build なら下げる）。以前 low / medium を選んでいた build は high になるので、費用は増える。
  - 著者が様子を見たい build は spawn-session で出す。
  - cloud は任意の 1 行にする（著者の方針 c）。build を手元の文脈と機械から切り離したいときに選ぶ。`cloud-dispatch.sh` と bats は残す。
- **★ packet は build の branch の最初の commit にする。**
  - いまは main に commit して push してから dispatch している。それをやめ、packet の本文は Agent の prompt で渡す。
  - build は自分の branch の最初の commit として `docs/plans/<task>-s<n>-<slug>.md` を入れる（`docs(plan): …`。ADR-0085 の「plan は実装の最初の commit」はそのまま保つ）。
  - これで、並行する build の未検収の packet が他の merge の push に混ざって公開されることが無くなる。packet の commit で main が進み、先に切った branch が rebase を要することも無くなる。
  - `worktree.baseRef` の設定は変えない。worktree は origin の既定 branch から切られる。
- **★ main が進んだときの rebase は判断役が local で行う。**
  - build を差し戻さず、worktree で `git rebase main` → `verify.sh` → ff-only merge の順に進める。
  - これまでの差し戻しの記録 5 件は、すべてこの型だった。
- **★ public repo の開始承認は cloud の dispatch だけに掛ける。**
  - local の build は、検収の前に何も push しない。最初の公開は ff-only merge の push で、検収を通した build の push は既に判断役の範囲にある（ADR-0069、boundary.md「とる」）。
  - 開始承認が要った理由は「build の最初の push が検収前の公開になる」ことで、local の build ではこれが起きない（ADR-0075 Decision 5）。
  - start item に残るのは、cloud の dispatch と、著者だけが答えられる 5 項目。
  - この変更は boundary の運用を変えるので、plan の承認でこの点も決まる。採らない場合は今の開始承認のまま残す。
- **★ 細かく縛る機構を外す**（方針 d）。外すものは 4 つ。
  - packet の Effort 表
  - 見落としで effort を上げる規則
  - 差し戻しの 3 分類と `logs/effort-outcomes.jsonl` への追記
  - Model / Effort の不一致を報告する項目

  ADR-0081 の Decision を置き換える。ADR-0043 の 2026-10-11 注記にある見直し条件は、読み先を claims.jsonl の release 行と build commit の `Premise:` / `Plan:` 行に付け替える。
- **packet**: local の plan 1 枚（約 60 行）に縮める。
  - 残す節は 4 つ。
    - Goal: 判定可能な受入条件。著者だけが答えられる 5 項目の答えもここへ。
    - Premise: file:line。実装の前に再照合し、崩れていたら、直して理由を書くか、止めて報告する。
    - Must-not: gate のファイル、名指していないテストの assertion、push、merge、台帳の編集。
    - Report: commit 本文の `Plan:` / Premise / Fix / Verify / Deviations / Out-of-diff findings / Proposed tasks（再現手順つき、最大 2 件）/ Needs from judge。
  - cloud 用の自己完結の追記は、template 末尾の短い付録にする。
- **検収**:
  - 判断役が worktree で `verify.sh` を自分で走らせる。CI は merge 後の main の事後検査になる（ADR-0099 に注記）。
  - fork mode が on の間、interactive な判断役は subagent を待てず、build の完了は通知で届く。そう 1 文書く。
- **実物とずれた記述を直す**: Agent の effort 引数（SKILL.md:263-266 と 312-314）、frontmatter の compatibility 行、役割表、§3 の executor 表、`scripts/triage-tick.sh:86` の prompt の cloud の句、verify-bootstrap の「cloud のために CI」の句。
- **残すもの**: 判定の順序（§1）、digest（§2）、harvest の起票規律、Damping（WIP ≤ 3、1 retry / cycle）、boundary.md の境界（上の ★ で運用を変える開始承認を除く）、tick の session の作り直し（`SKILL.md:437` の記述は実物どおり）。
- **目安**: SKILL.md は 488 行から 300 行台に、packet template は 185 行から約 60 行になる。

### 3. 常駐層 — 古い行・重複・hook の写しを削る。環境固有の事実と罠は残す

反証役が依存を確かめた形で行う。

- `rules/common/planning.md` は本文を 5 項目にする。
  1. search-first
  2. 実装の種別・reviewer・実行者は implementation-chain。Fable の session の実装は Opus への委譲が既定
  3. plan の記録規約
  4. plan の依頼では plan mode に入り、書く前に調査する（手順は `hooks/research-gate.sh` が差し込む）
  5. verify と `git -C ~/.claude status`（`hooks/harness-commit-notice.sh` が rule 側の配線として名指す）
- `rules/common/task-tracking.md`: 重複した flag の列挙を 1 文にする。STALE と STEALABLE の罠は残す。
- `rules/common/akc-cycle.md`: 所有者表を 3〜4 行にする。「ADR の扱い」は見出しを残し、本文を adr-writer への pointer 1〜2 行にする（docs/decision-history/README.md:114 と ADR-0089 が参照するため）。
- `rules/common/security.md`: bypass の env 名を外し、hook の path に替える。lint の検査 8 と `bandit-precommit.sh:3` の pointer は生かしたままにする。harness 脅威面の節は残す（user-level rule の `paths:` は session の cwd を基準に解決されるので、~/.claude だけに効かせる手段にならない）。
- `rules/common/boundary.md`: 退役した `.growth/` を削る。Herdr 例外の入れ子は、`spawn-session` と `agent-send` が正本として指しているので、文意を変えずに短くするだけにする。
- `rules/common/agents.md`: 本文を 2 文（catalog の正本、Review は別 process）と boundary への pointer にする。先に agent-send に `--wait` の罠が書かれていることを確かめる。
- 変えないもの:
  - `rules/README.md`: rules-stocktake が索引として検査し、apply で更新する。移すなら週次の棚卸しの report で扱う。
  - `llm-first-code.md`、`coding-style.md`、`knowledge-staleness.md`、`evals.md`、`public-records.md`、`testing.md`、`skills.md`
  - `contemplative-axioms.md`、`practitioner-identity.md`: 著者の verbatim
  - `output-styles/signal-first.md`: 著者が 2026-09-25 に「default のまま、本文は残す」と決めている
- `CLAUDE.md`（global）は分割しない。
  - Layout 節を削る。ls で分かり、全 repo に常駐している。
  - :19 の output-styles の行を実態（無効、本文は残す）に合わせる。
  - harness_lint の検査 13 と、リンク検査の対象は今のまま。
- `AGENTS.md`: 正本（`CLAUDE.md` と `rules/common/*.md`）へのリンクと、変更の作法の 3 行に縮める。Claude には毎回 project instructions として載っていて、中身は CLAUDE.md の pointer。Codex への中身は CLAUDE.md が持ち続ける。
- `MEMORY.md`（gitignore 下）:
  - 先に `~/.claude/backups/` へ複写する。
  - 短くするのは、退役・終了した対象を指す Pending と project の行だけ。Pending の「merge = 人間」を実物の「判断役の ff-only」に直し、growth loop・Opus medium の試行などの終了した行を削る（ファイル本体は残す）。
  - Feedback と User の行は、著者の訂正が常駐する唯一の形なので触らない。
  - akc-cycle の同期の罠と detail-loop への導線の行は残す。

### 4. hook・plugin・設定

- **hook**:
  - `hooks/task-claims-reminder.sh`: 固定の 3 行は、session と agent ごとに最初の 1 回だけ出す。`claims.py open` の行は、前回と変わったときだけ出す。文面は事実文にする（hooks docs: 命令形の文面は injection 防御を誘発しうる）。
  - `hooks/review-chain-notice.sh`: regex の末尾を `(commit|revert|merge)([^-[:alnum:]_]|$)` にし、`merge-base` / `commit-tree` での誤発火を外す。
  - `hooks/plan-executor-notice.sh`: Fable 限定のまま、文面を方針 b の事実文にする。
  - `hooks/review-model-notice.sh`: 文面の「judge-tier」を「Fable」にする。
  - `hooks/README.md` の該当行も直す。
  - `hooks/contemplative-name-reminder.sh` は残す（14 日で 208 回差し込み、55 session）。
- **lint**:
  - `scripts/hooks/harness_lint.py` の `SUBSTRATE_MANAGED_SKILL_DIRS` に `".trash"` を足す（claude.ai の同期が作る未追跡 dir。作業ツリーで rc=3）。
  - `.gitignore` に `skills/.trash/` を足す。
  - `plugin-directory-submit` を `skills/skill-stocktake/results.json` に登録する。
- **★ settings.json**（git 追跡外。先に `~/.claude/settings.json.bak-20261107-context` へ複写する。.gitignore の既存の作法）:
  - plugin を user scope で無効にする: `pr-review-toolkit`、`claude-security`、`hookify`、`adhd`、`session-report`。
    - `pr-review-toolkit`: code-reviewer の自発選択が止まらない。silent-failure-hunter（2 か月で 5 回）も一緒に失う。要るときは Codex か general-purpose で代える。
    - `claude-security`: scan するときだけ `/plugin enable` する。skill-health の :54・:141 に 1 句足す。
    - `hookify`: 唯一の rule は 33/33 が誤検知だった。contemplative-agent の `.claude/hookify.*.local.md` は git 外なので、退避してから外す。
    - `adhd`・`session-report`: 使用 0。
    - implementation-chain の opt-in 名簿と ADR-0042 に 1 句ずつ注記する。
  - `skillOverrides` を `"off"` にする（CLI だけ。claude.ai 側の設定には触れない）: 使っていない同期 skill 6 本（`anthropic-skills:learn` / `morning` / `import-memory` / `google-workspace` / `skill-creator` / `sns-en-post`）。skill-creator は local の skill-writer と発火条件が重なる。
- **agent**: `agents/prompt-forager.md` の description を、dispatch 専用の 1 文（約 110 字）にする。

## 変更の単位

~/.claude の main に commit する。並行 session があるので、add と commit は一度に行う。verify が通ったら private の origin へ push する。

| # | commit | 中身 |
|---|---|---|
| 1 | `fix(lint): skills/.trash を substrate 管理に数える` | harness_lint の tuple・.gitignore・results.json。今は lint が rc=3 で全 commit が止まるので、これを最初に入れる |
| 2 | `docs(research): …` → `docs(plan): context-holder-implements` | report 2 本（internal report :44 の contemplative-name-reminder「差し込み 0 回」を「208 回・55 session」に直してから入れる）、続いてこの plan だけ（`docs/plans/context-holder-implements.md` に改名して入れる） |
| 3 | `docs(adr): ADR-0100 …` | 新 ADR（skill adr-writer → adr-reviewer）と、ADR-0042 / 0043 / 0057 / 0069 / 0075 / 0081 / 0099 への日付つき注記 |
| 4 | `feat(implementation-chain): 実行者を model とタスクの文脈で決める` | implementation-chain（実行者の決定・Review pin の語・opt-in 名簿）、planning.md、plan-executor-notice / review-model-notice の文面と bats、hooks/README |
| 5 | `refactor(task-triage): local の fresh build を既定にし、cloud を任意にし、細かく縛る機構を外す` | SKILL.md、packet-template、MAINTENANCE.md、triage-tick.sh の prompt、verify-bootstrap の句 |
| 6 | `chore(rules): 古い行と重複を削る` | §3 の rules、CLAUDE.md、AGENTS.md。MEMORY.md は git 外なので commit 本文に記録だけ |
| 7 | `chore(hooks): claims の差し込みを 1 session 1 回にし、review-chain の誤発火を外す` | hook・bats・golden（出力の変更を宣言したものだけ）、skill-health の句、prompt-forager の description |
| — | settings.json・plugin・contemplative-agent の hookify rule の退避（git 外） | ADR-0100 の Consequences と commit 7 の本文に記録 |

各 commit の本文は `Plan:` 行でこの plan を指す。

ADR-0100 の Review-when は次の 3 つ。

1. 4 週間の git log で、2 群を比べる。`Premise:` 行を持つ commit を fresh build、持たない実装 commit を文脈保持者とする。merge 後 14 日以内に同じファイルへ入った `fix:` commit の率が、文脈保持者の側で fresh build の 2 倍を超えたら見直す。
2. cost page の Fable / Opus の費用比が変わったら見直す。
3. substrate が session ごとの model routing を自分で行うようになったら見直す。

## Verification

1. **probe（commit 5 の前）**: 捨て repo（scratchpad に置き、local bare を origin にする）の interactive でない session で確かめる。
   - 見ること: `Agent(model: "opus", isolation: "worktree")` が origin の既定 branch から切られるか。prompt で渡した packet を branch の最初の commit にするか。commit 時に hook（verify-precommit）が発火するか。
   - 判断役による `git rebase main` → ff-only の流れが通るか。
   - 否なら §2 の該当行を今の形（packet を main に commit して push）に戻し、ADR にそう書く。
2. **機械ゲート**:
   - `bash .claude/verify.sh`（harness）。
   - `python3 scripts/hooks/harness_lint.py` が rc=0。
   - 触った hook の bats: `tests/review-chain-notice.bats`・`golden-review-chain-notice.bats`・`plan-executor-notice.bats`、claims reminder の bats。
3. **review**:
   - 全 diff を別 process の `/code-review` medium で回す。`Agent(subagent_type: "general-purpose", model: "opus")` に implementation-chain の reviewer 指示を付ける。
   - hook の diff は脅威面に当たるので、`security-reviewer` を並列に回す。
   - ADR は adr-reviewer に通す。
4. **効果の読み**:
   - 変更前後で、同じ `claude -p "ok"`（evals.md の隔離設定）を `~/.claude` と別の repo で回す。最初の request の入力 token を transcript の usage で比べる。
   - 14 日後に、hook の差し込みの回数と字数を internal report と同じ transcript 集計で数え直す。今の基準値は task-claims-reminder 2,107 回、review-chain-notice 3,140 回。
5. **実運用**:
   - 次の harness の tick（日曜 06:30）と contemplative-agent の cycle で、local build が既定の経路で出て、検収・ff-only merge まで通るかを digest で見る。
   - contemplative-agent に残る cloud の 2 branch（S50・S51）は、その cycle で local に検収する。

## この plan に入れないもの

- contemplative-agent の CLAUDE.md（約 11K token。この生態系で最大の常駐物）を縮める作業。4 本のテストが表を読み先にしているので、その repo の文脈を持つ session が行う。起票するかは著者が決める。
- `rules/README.md` を docs へ移すこと。週次の harness-stocktake の report で、rules-stocktake の索引の扱いと一緒に出す。
- 公開 copy への同期（skill harness-sync）。公開は著者の操作。
- 「plan session が packet なしで実装」と fresh build を比べる再生比較（scripts/replay/）。任意の後続で、ADR-0100 の Review-when 1 が発火したら回す。

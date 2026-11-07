# ADR-0100: 実行者は model とタスク固有の文脈で決め、triage は local の fresh build を既定にし、委譲を細かく縛る機構を外す

## Status

accepted — 次の ADR の一部を変える。各 ADR の該当節に注記した。

- [ADR-0057](./0057-judge-tier-default-dispatch-and-plan-boundary-advisory.md):
  - 語を「judge-tier」から「Fable の session」に替える。
  - dispatch 先の既定を cloud から `Agent(model: "opus")` / `spawn-session` に替える。
  - 既定の dispatch と例外 (a)〜(c) が Fable に掛かること自体は変えない（judge-tier は当初から Fable を指していた）。
- [ADR-0075](./0075-cloud-session-as-default-build-executor.md):
  - Decision 1 の「build の既定は cloud」を置き換える。cloud を選んだときの起動経路と preflight は残る。
  - Decision 4 の表は「cloud を選べない条件」として読む。
  - Decision 5 の開始承認は、cloud の build と、dispatch の前の push が要る public repo の local build に掛ける（push の要らない local build には掛けない）。
  - Decision 8 の tick の起動機構と cycle prompt は変えない。
- [ADR-0076](./0076-build-proposals-with-reproducer-and-opus-5-5-packet-rules.md) の Decision 1・2・4・6 から外すもの:
  - packet の「進め方」節
  - local の Report の `Model:` と claim ラベルの `model=`
  - `Model:` の不一致を出す digest 行
  - 記事の出典 note

  `Model:` は cloud の付録に残る。
- [ADR-0081](./0081-per-packet-effort-and-bounce-classification.md):
  - Decision 3・4 を外す。
  - Decision 1・2 の `cloud-dispatch.sh --effort` は残る。
- [ADR-0098](./0098-task-triage-digest-as-one-approved-report.md): Decision 2 の「開始の OK」群にある公開 repo の dispatch・bounce を、cloud の build と dispatch の前の push が要る local の build だけにする。
- [ADR-0099](./0099-ci-as-gate-canon-local-as-content-canon.md):
  - Decision 3 の判断役の review を、cloud の build だけから全 build に広げる。
  - Decision 1 の「verify の結論の正本は CI」は、local の build では事後の検査になる。
- [ADR-0042](./0042-retire-code-reviewer-and-scope-security-review-to-threat-surface.md)・[ADR-0043](./0043-task-triage-loop-judge-build-human.md)・[ADR-0069](./0069-boundary-rule-and-judge-merges.md) も一部が変わる。

## Date

2026-11-07

## Context

Plan: [docs/plans/context-holder-implements.md](../plans/context-holder-implements.md)（承認 2026-11-07）。
調査は [外部 report](../plans/research/2026-11-07-context-holder-implements.md)（as-of 2026-11-07）と
[内部 report](../plans/research/2026-11-07-context-holder-implements-internal.md)。

- **著者の方針（2026-11-07、同じ会話での発言）:**
  - 「最近は実装も委譲するより、文脈を持ったエージェントに実装させた方がいいというから、その辺りの状況をリサーチして、最適化案を出してくれない？」
  - 「クラウドセッションも無理して使わなくていいよ」
  - 「不要なコンテキストを持たせないためにクラウドセッション使ってもいいからね。あくまで無理して使わなくていいということだから」
  - 「マイクロマネジメントしないことが重要だと思ってるから。」
  - 「Fableだけは実装は基本的に委譲で。トークン効率が悪すぎるから」
- **変える前の状態:**
  - ADR-0057 の「judge-tier」は当初から Fable を指していた（同 ADR の Context）。
  - 「実行者の決定」が要るのは Fable の session のときだけだった（`skills/implementation-chain/SKILL.md:36`（`ae9ca41` 時点））。
  - Opus の session がタスクを詰めてそのまま実装する形は既にあった。内部 report はその割合を commit 全体の約 97% と見積もる（母数と期間は report に無い）。
  - 本 ADR の Decision 1 は、この形を書き下したもので、反転ではない。
- **外部の資料（2026-11-07 照合）:**
  - 「文脈を持つ者が実装せよ」と明言する Anthropic の一次資料は無い。
  - 近いのは 2 つある。sub-agents docs の「計画・実装・テストが文脈を共有するなら主会話で」と、best-practices の「同じ task を subagent に渡しても答えは良くならない」。
  - 同じ best-practices は「書き上げた spec から fresh session で実装」も推している（https://code.claude.com/docs/en/best-practices、https://code.claude.com/docs/en/sub-agents）。
  - 文脈保持者と fresh な実装者を同じ coding task で比べた公開の測定は見つからなかった。
  - Handoff Debt（arXiv:2606.02875）の報告: 文脈つきの引き継ぎは repo だけの引き継ぎより events を 20〜59% 減らし、solve rate の差は小さい。
- **fresh な照合が前提の誤りを拾った証拠:**
  - packet の build は、実装の前の Phase 0 で packet か判断役の前提を反証することがある。
  - contemplative-agent の build commit のうち `Premise:` 行を持つ 69 件では、10〜12 件で反証が出た（内部 report、2026-11-07 集計）。
- **fresh な build でも拾えなかった例（contemplative-agent の RFC-0022）:**
  - 著者と設計を詰めた session が論文を 3 か所読み違えた。
  - その読み違いは packet を通って build に流れ、fresh な build も拾わなかった。
  - 発覚は著者の指摘による。後の手当ては、引用元と照合する fresh な session だった。
- **triage の判断役の session:**
  - CLI の版が変わるか 7 日たつと作り直される（`scripts/triage-tick.sh:113-169`）。10-17 以降の 13/13 cycle が新しい session で始まった。
  - 中身は台帳全体の判定（1 cycle 約 15〜36 万 token）で、個々のタスクを著者と詰めた文脈ではない。
- **10-27 の事前登録つき再生比較**（[2026-10-27-replay-result.md](../plans/research/2026-10-27-replay-result.md)）:
  - 比べた形は、判断役が判定のあと同じ session で実装するもの。
  - 失敗は 2/16 対 0/16 だった。うち 1 本は環境由来の verify 失敗で、除くと 1/16 対 0/16。既定を変える規則は満たさなかった。
  - 偶然と区別できない差なので、判断役の実装が悪い証拠ではない。
  - 読めた失敗の型は 1 つ。context が compact の閾値 400K に近づいた feat で、packet の細部の指示を保てなかった。
  - packet を書かずに文脈保持者が実装する形は測っていない。
- **費用**（https://platform.claude.com/docs/en/build-with-claude/optimizing-for-cost-and-intelligence、2026-11-07 照合）:
  - Fable 5.1 は Opus 5.5 high の 2.2〜3.0 倍の費用で、スコアは上がらない（defect search 系）。
  - SWE-bench Pro の subset での solved task あたりの費用: Opus 5.5 medium $0.21、high $0.29、Fable 5.1 high $1.19。
  - Fable を orchestrator にした構成は、費用が 24% 増えてスコアは上がらない。
  - 「Fable が判断し、Opus が build する」構成は測られていない。
  - fork の subagent は親の model と文脈を継ぐ。background の subagent は Agent tool を持たず、再委譲できない（sub-agents docs）。
- **task-triage の大きさと effort の扱い:**
  - SKILL.md は 488 行で、§3 Dispatch と §4 Judge が 186 行。
  - packet template は 185 行で、小さな修正では diff より長い（contemplative-agent S46: packet 89 行、diff 46 行）。
  - packet ごとの effort の選択は毎回動いた。effort の分かる build 11 本のうち 6 本で、判断役は low か medium を選んだ（`logs/effort-outcomes.jsonl`、git 外）。
  - 対照が無いので、効果は測れていない。
  - 見落としで 1 段上げる規則は、16 本以上の build で 1 回だけ発火した。
  - 同じ帳簿は 12 行で、11-04 以降の build 3 本と 9 月の数本が欠けている。
- **Agent tool と effort:**
  - `skills/task-triage/SKILL.md:263-266`（`ae9ca41` 時点） は「Agent tool は effort を取らない」と書いていた。
  - 実際は、CLI 2.1.319 の Agent tool は呼び出しごとに `effort` を取る（v2.1.292 以降、非 fork のみ。sub-agents docs）。
  - この 1 文のせいで、docs 以外の local build は spawn-session に回っていた。
- **2026-11-07 の probe**（Agent の worktree で 1 file を commit）:
  - 確かめたのは 2 点。
    - `Agent(isolation: "worktree")` の worktree は origin/main（`290821f`）から切られた。ローカルの main は 17 commit 先にあった（`worktree.baseRef` の既定 `fresh`）。
    - commit の PreToolUse(Bash) で review-chain-notice の差し込みが出た。同じ matcher の gate（verify-precommit ほか）は出力が無く、走ったかは見ていない。
  - packet を最初の commit にする流れと、判断役の rebase → ff-only は probe していない。最初の実運用 cycle で見る（plan の Verification 5）。
  - 記録はこの session の subagent transcript（git 外）にしか無く、残るのはこの段落だけ。
- **使われ方を数えた plugin と skill:**
  - `pr-review-toolkit` の `code-reviewer` は、ADR-0042 の 2026-09-12 注記（Code Review 行の代替にしない）の後も、09-13 以降に 27 回自発起動した（うち 2 回は再生比較の run。`metrics/agent-usage.jsonl`、git 外）。
  - 同注記は、次の手を「止まらなければ block を足す」としていた。
  - この plugin の agent 説明は約 6.3K 字が常駐する（内部 report）。
  - `hookify` の rule は 1 本で、33/33 が誤検知だった。
  - `claude-security` は 60 日で 1 回、`adhd` と `session-report` は使用 0（内部 report）。
  - claude.ai から同期される skill のうち Decision 9 の 6 本は、06-10 以降の起動が 0（`metrics/skill-usage.jsonl`、git 外。この logger は同期 skill の起動も記録する）。

## Decision

1. **Opus の session は、そのタスクを著者と詰めた session が自分で実装する。**
   - plan に「実行者の決定」を書く必要は無い。
   - 起票して triage に回すのは、その場で終えないと決めたものだけにする。
2. **Fable の session は、実装を Opus に委譲する。**
   - 委譲先は session が選ぶ。plan を渡した `Agent(model: "opus")` か、skill `spawn-session` の Opus session。
   - fork は親の model を継ぐので、委譲にならない。
   - plan に「実行者の決定」を 1 行書くのは Fable の session だけ。
   - `hooks/plan-executor-notice.sh` は Fable の session のときだけ鳴る（ADR-0057 Decision 2 のまま）。文面は、この Decision の事実文にする。
   - Fable の session が自分で実装してよい場合は、ADR-0057 の (a)〜(c) のまま。
3. **review は、誰が実装しても別 process で回す。**
   - chain は `implementation-chain` の Matrix のまま。built-in `/code-review` は medium で回し、脅威面に触れる diff には security-reviewer を足す。
   - 外部資料に依る diff では、reviewer に引用元も渡す（RFC-0022 の型）。
   - triage の build は Review 行を回さない。判断役が §4 で全 build を別 process の review に回す（security-reviewer の判断も判断役が持つ）。
   - 理由: background の subagent は Agent tool を持たないので、Agent の build の中からは別 process の review を起こせない。spawn-session と cloud の build も同じ形にそろえ、検収の経路を 1 本にする。
   - ADR-0099 Decision 3 を local の build に広げる。
   - 「judge-tier / build-tier」の語を外し、model 名で書く。
4. **triage の判断役は、台帳のタスクを自分で実装しない。**
   - 既定の実行者は、判断役が出す `Agent(subagent_type: "general-purpose", model: "opus", isolation: "worktree")`。
   - effort は省いて session の値で走らせる。上げる・下げる理由があるときだけ、判断役が渡す。
   - 著者が様子を見たい build や長い build は `spawn-session` で出す。
   - cloud session は任意で、build を手元の文脈と機械から切り離したいときに選ぶ。そのとき `scripts/cloud-dispatch.sh` と ADR-0075 の Decision 2・3・5〜7 が掛かる。
5. **dispatch の前に main を push し、packet は build の branch の最初の commit にする。**
   - build の worktree は origin の既定 branch から切られるので、判断役は `git push origin main` で main を push してから出す（cloud の preflight と同じ前提）。
   - push が fast-forward でないとき（origin が先に進んだ、または main が分岐した）は、その repo の dispatch を止めて report item にする。
   - public repo では、この push が公開になる。前の flow でも、public repo の packet の push は task ごとの著者の OK を要した（`skills/task-triage/SKILL.md:195-196`、`ae9ca41` 時点）。だから public repo で main が origin より先にあるときは、その dispatch を `start` item にし、承認の後に push して出す。main が origin と同じなら push は何も出さず、そのまま出す。
   - private の remote への push は判断役がとる。
   - packet の本文は prompt で渡す。
   - build は packet を `docs/plans/<task-id>-s<n>-<slug>.md` に置いて、単独で commit する（`docs(plan): …`）。以後の commit は packet のファイルを変えない（判断役が §4 で確かめる）。
   - ADR-0085 の「plan は実装の最初の commit」は、この形で保つ。
   - 私的な中身を持つ packet だけは、その repo の `.notes/packets/` に置いて commit しない。build には本文を prompt で渡す（`Plan: none`）。
   - private の remote への dispatch の前の push を `rules/common/boundary.md` の「とる」に書き足す。public repo の push は「人間に渡す」の公開のまま。
6. **main が進んだときは、判断役が local で rebase する。**
   - 差し戻さず、worktree で `git rebase main` → `verify.sh` → ff-only merge の順に進める。
   - 判断役が解いてよい conflict は、build が決めたことを変えない範囲だけ。変えるなら差し戻す。
   - review は rebase の後の tip に回す。
   - local の build の検収は、判断役が worktree で走らせた `verify.sh` の結果で行う。push の後の main の CI は事後の検査になる。
7. **public repo の開始承認は、cloud の dispatch と差し戻しと、dispatch の前の push が要る local の build に掛ける。**
   - local の build そのものは、検収の前に何も push しない。
   - packet は build の branch にあり、それが公開されるのは検収を通した ff-only merge の push のとき（ADR-0069 で判断役の範囲）。
8. **委譲を細かく縛る機構を外す。** 外すもの:
   - packet の `Effort:` 行と選択表
   - 見落としで effort を 1 段上げる規則
   - 差し戻しの 3 分類と、`logs/effort-outcomes.jsonl` への追記
   - `Model:` / `Effort:` の不一致を報告する item
   - packet の「進め方」節、local の Report の `Model:` 行と claim ラベルの `model=`、記事の出典 note（ADR-0076 Decision 1・2・4・6）

   packet は次の 4 節にし、cloud 用の自己完結の追記は末尾の付録にする（付録は `Model:` を残す）。
   - Goal: 判定可能な受入条件。著者だけが答えられる項目の答えもここに書く。
   - Premise: `file:line`。崩れていたら、直して理由を書くか、止めて報告する。
   - Must-not
   - Report

   Report の `Proposed tasks`（再現手順つき、最大 2 件）と `Out-of-diff findings` は残す（ADR-0076 の起票規律の入力）。

   ADR-0043 の 2026-10-11 注記にある見直し条件は、読み先を替える。新しい読み先は `.notes/claims.jsonl`（git 外）の release 行と、build commit の `Premise:` / `Plan:` 行。
9. **自発選択が止まらない plugin と、使っていない plugin を user scope で無効にする。**
   - 対象: `pr-review-toolkit`、`claude-security`（scan のときだけ `/plugin enable`）、`hookify`、`adhd`、`session-report`。
   - claude.ai から同期される skill のうち使っていない 6 本（`anthropic-skills:learn` / `morning` / `import-memory` / `google-workspace` / `skill-creator` / `sns-en-post`）は、CLI の `skillOverrides` で `off` にする。
   - key は名前空間つき（`"anthropic-skills:learn": "off"`）で書く。docs は同期 skill に `skillOverrides` が効くかを書いていないので、2026-11-07 に `claude -p --settings` で確かめた。名前空間つきでも bare（`learn`）でも、子 session の skill 一覧から消えた。bare の key は、将来の local の同名 skill にも当たる。
   - settings.json は git の外なので、先に `~/.claude/settings.json.bak-20261107-context` へ複写する。
   - contemplative-agent の `.claude/hookify.warn-kill-pytest.local.md`（git の外）は、`~/.claude/backups/contemplative-agent-hookify-20261107/` へ移す。
10. **変える artifact:**
    - `skills/implementation-chain/SKILL.md`: 実行者の決定、Review の実行モデル pin の語、opt-in 名簿
    - `rules/common/planning.md`
    - `hooks/plan-executor-notice.sh` と `hooks/review-model-notice.sh` の文面と bats、`hooks/README.md`
    - `skills/task-triage/SKILL.md`: frontmatter、役割表、§2 の group、§3〜§5、Where the loop lives
    - `skills/task-triage/references/packet-template.md`、`skills/task-triage/MAINTENANCE.md`
    - `skills/verify-bootstrap/SKILL.md` の cloud の句
    - `skills/skill-health/SKILL.md` の claude-security の句
    - `rules/common/boundary.md` の「とる」（Decision 5 の push）
    - settings.json（Decision 9）
    - 9 本の ADR への注記

    **変えないもの:**
    - `scripts/cloud-dispatch.sh` と bats
    - `scripts/triage-tick.sh`。cycle prompt の「public repo の cloud dispatch は start item」は Decision 7 のままで正しい。判断役の session の作り直しも変えない。
    - `boundary.md` の他の境界
    - ADR-0043 の三役と Damping
    - `worktree.baseRef` の設定

    plan の §3（常駐層の簡素化）と §4 の他の hook の変更（task-claims-reminder、review-chain-notice）は、本 ADR の外にある。記録は各 commit の本文。

## Review-when

- **Decision 1 の見直し:**
  - いつ・誰が: 2026-12-05 以降に `implementation-chain`「実行者の決定」か task-triage §3 を変える session が、変える前に数える。著者が頼んだときも数える。結果は本 ADR に注記する。
  - 対象: `~/.claude` と contemplative-agent の main で、2026-11-07 から 4 週の実装 commit。
  - 2 群: `git log main --since=2026-11-07 --grep='^Premise:'` に当たる commit（fresh build）と、当たらない `feat` / `fix` / `refactor` の commit（文脈保持者）。
  - 読む値: その commit の commit date から 14 日以内に、同じファイルへ入った後続の `fix` commit（自分自身を除く）が 1 本以上ある commit の割合。
  - 発火条件: 文脈保持者の側が fresh build の 2 倍を超えたら、plan の「入れないもの」にある再生比較（packet なしの文脈保持者の arm）を回す。2 群はタスクの選び方と交絡し、Fable の session から委譲した build も `Premise:` を持たずに文脈保持者の群に入る。だから発火は再生比較の合図であって、それだけで Decision 1 を覆さない。
  - fresh 群が 10 commit に満たなければ、窓を 4 週ずつ延ばす。12 週で足りなければ比較をやめ、著者が決める。
  - 固定するもの: 型の分類、14 日、2 repo、packet-template の Report の `Premise:` 行。
- **Decision 2 の見直し:** cost page の Fable / Opus の費用比が変わったとき、または Fable の新しい版が出たとき。substrate が session ごとの model routing を自分で行うようになったら、Decision 1・2 を外す。
- **無人時の既定:** 無人の cycle で、digest に `stalled` と出た Agent build の原因が permission か commit gate の hook だったら、無人時の既定を `spawn-session` に戻すかを決める。
- **effort の扱い:** effort を上げれば防げたと読める見落としを判断役か著者が見つけたら、その件を本 ADR に注記する（注記を数える場所にする）。2 件目で、packet ごとに effort を選ぶ形（ADR-0081 Decision 3）に戻すかを決める。

## Alternatives Considered

- **判断役が判定のあと自分で実装する（同じ session か fork）:** 文脈を持つ者が実装するという依頼の字面に、最も近い。却下した理由:
  - 判断役の文脈はタスク固有でなく、台帳全体の判定である。
  - 再生比較で読めた失敗の型（compact の閾値近く）と同じ帯域で動く。fork はその文脈を継ぐ。
  - build の Phase 0 は、判断役の前提を独立に確かめる唯一の工程で（Context の 69 件中 10〜12 件）、判断役が自分で実装すると消える。

  Open — 見直す時: Review-when 1 の比較で文脈保持者の側が fresh build と同等以上と出て、packet なしの arm の再生比較も同じ向きを示したとき。
- **cloud を既定のままにする（ADR-0075）:** build が手元の文脈と機械から切り離され、CI が verify の正本になる。却下した理由:
  - 著者の方針（無理に使わない）。
  - cloud に出すたびに、packet の自己完結、CI の存在、public repo の開始承認が要る。
  - 速さの証拠も無い。差し戻しなしで cloud は 6〜30 分、local の Agent は 9〜50 分だが、n が小さく課題の大きさも揃わない（内部 report）。
- **packet ごとの effort の選択（ADR-0081）を残す:** high を要らない build の費用が下がる（SWE-bench Pro の subset で medium は high の約 0.72 倍の費用）。却下した理由:
  - 著者の方針（マイクロマネジメントしない）。
  - 選択の効果は対照が無く、測られていない。
  - Agent の経路では、選んだ値が適用されていなかった。
  - 判断役が理由を持つときは、Agent の `effort` で渡せる（Decision 4）。
- **Opus の session も fresh build に委譲する:** build と plan が分かれ、Phase 0 が独立に前提を確かめる（69 件中 10〜12 件で反証が出た）。却下した理由:
  - 著者の方針 (a)。
  - packet を書く費用（小さな修正では packet が diff より長い）。
  - fresh な照合の利点は、別 process の review と、引用元を reviewer に渡すことで取る（Decision 3）。
  - どちらの形が良いかを示す公開の測定は、どちら側にも無い。
- **`worktree.baseRef` を `head` にする:** build の worktree がローカルの HEAD から切られるので、dispatch の前の push が要らない（dispatch の時点で何も公開しない）。却下した理由:
  - HEAD は判断役の checkout の今の branch で、main とは限らない。著者や別の session が task branch に切り替えていれば、そこから切られる。
  - user scope の設定は、全 repo と Workflow の `isolation: "worktree"` に効く。project scope にすると repo ごとの settings が増える。
  - dispatch の前の push は、private の remote では前の flow が packet の commit とともに毎回していた push と同じで、public repo では前と同じく著者の OK を待つ（Decision 5）。
- **build が最初に `git reset --hard main` で、worktree をローカルの main に合わせる:** push しなくても、build が最新の main から始まる。却下した理由:
  - 著者の指摘（2026-11-07「PUSHしたらいいんじゃないの？」）。
  - build 側に手順を 1 つ足すより、cloud と同じ「main は push 済み」の前提にそろえるほうが単純。
- **pr-review-toolkit を残し、自発選択だけを block する（ADR-0042 注記の次の手）:**
  - 利点: silent-failure-hunter などの opt-in agent が残る。block も、既に Agent に掛かっている `hooks/review-model-notice.sh` に分岐を 1 つ足せば済む。
  - 却下した理由: block は自発選択を止めるが、plugin の agent 説明（約 6.3K 字）は常駐し続ける。opt-in の agent は 2 か月で 5 回しか使われておらず、要るときは Codex か general-purpose の agent で代えられる。

## Consequences

- **良くなること:**
  - 著者と詰めた Opus の session が、packet を書かずにそのまま実装する。Fable の session は Opus に渡して、判断に専念する。
  - triage の build は local の Agent で出る。packet は build の branch に入るので、packet の commit で main が進むことが無くなる。
  - main が進んだときの差し戻し（記録された 5 件はすべてこの型）は、判断役の rebase に変わる。
  - task-triage と packet の行数が減り、cloud 用の手順は付録に寄る。
  - 自発選択されていた plugin agent と、使っていない skill の説明が常駐しなくなる。
- **悪くなること:**
  - effort を省いた build は session の値（high）で走る。以前 low / medium を選んでいた build の費用は上がる（SWE-bench Pro の subset で high は medium の約 1.4 倍）。
  - 判断役は全 build の review を回すので、1 build あたり別 process の `/code-review` 1 本（脅威面の diff には security-reviewer も）が判断役の側に積まれる。以前は local の build が自分で Review 行を回していた。
  - dispatch の前の push は取り消せない。public repo では main を公開するので著者の OK を待ち、その間 build は出ない（前の flow の packet の push と同じ扱い）。
  - 無人の Agent の経路（auto mode の permission と commit gate）は、2026-08-29（RFC-0016）以降確かめていない。それが次の tick から無人の既定になる（Review-when 3）。
  - build の寿命は判断役の session に結ばれる。session が閉じると、走っている Agent build は止まると読む（subagent は session の process の中で走る。未確認）。worktree と branch に commit は残り、次の cycle の判断役が未マージの branch として拾う。agent id は session をまたがないので、続きと差し戻しは branch を名指す新しい Agent build で行う（task-triage §4）。
  - 判断役の rebase は、判断役の conflict 解決を build の branch に書く。ADR-0069 Decision 3 の実装者と検収者の分離から一歩出るので、範囲を build の決めたことを変えない解決に限り、review は rebase の後に回す（Decision 6）。
  - worktree の isolation guard は shell の `for` と heredoc を拒むので、build の書き方の制約になる（task-triage §3）。
  - local の build は、手元の機械の資源と常駐層を build ごとに読み直す。常駐層は `~/.claude` で約 13K token、他 repo で約 9K token とその repo の CLAUDE.md（contemplative-agent は約 11K）。
  - ADR-0081 の Review-when 1 は、記録の元（3 分類の追記）が無くなり、12 行で終わる。
  - fork mode が on の間、interactive な判断役は Agent の build を待てず、完了は通知で届く。
  - silent-failure-hunter などの opt-in agent が使えなくなる。
  - 文脈保持者の実装には fresh な Phase 0 が無い。前提の読み違いを拾えるのは、別 process の review と Review-when 1 だけになる。
- **第二の記録:**
  - 実行者の規則の正本は `implementation-chain`「実行者の決定」、triage の手順の正本は `task-triage`。
  - 本 ADR の Decision は、その日付時点の要約。食い違ったら SKILL.md が勝つ。
- **戻すとき:**
  - skill・rule・hook・ADR の変更は、commit の revert で戻る。
  - settings.json（Decision 9）は git の外なので、`~/.claude/settings.json.bak-20261107-context` から戻す。
  - hookify の rule は `~/.claude/backups/contemplative-agent-hookify-20261107/` から contemplative-agent の `.claude/` に戻す。
  - dispatch の前の push は戻せない。

# ADR-0075: build 役の既定を Claude Code cloud session に移す — packet は自己完結、verify は CI、判断役はローカル

## Status

accepted

## Date

2026-09-24

## Context

- [ADR-0043](./0043-task-triage-loop-judge-build-human.md) の三役（判断 = judge-tier の常駐 session /
  build = task ごとの新 session / 人間 = 方向決め）と [ADR-0057](./0057-judge-tier-default-dispatch-and-plan-boundary-advisory.md)
  の「judge-tier の既定は dispatch」は、build を **ローカル**の worktree session（Herdr `spawn-session` /
  Agent tool）で走らせる前提だった。packet は「書いていないことは harness の規約が既定」と宣言し、
  rules / hooks / skills が build 側にも常駐していることに依存していた。[ADR-0069](./0069-boundary-rule-and-judge-merges.md)
  Decision 3 は判断役の検収に「`verify.sh` を main で再実行」を含め、検収を通した branch の main への
  ff-only 取り込みと push を（repo の公開・非公開を問わず）判断役に移していた。
- 著者の決定（2026-09-24、本 ADR の起点。動機は著者のもので、本 ADR はその機構と境界を記録する）:
  build 役はハーネス無しで動かし packet を自己完結させる / cloud でやるのは実装と built-in
  `/code-review`（effort medium）だけ / verify は CI へ移す（検査の正本は `.claude/verify.sh` のまま、
  判断役はローカルで再実行せず CI の結果を読む）/ CA（public）を対象に含める（対象外なら移行に
  意味が無い）/ PR 自動作成 on・自動修正 off・branch prefix `claude`。
- 実行機は 1 台（M1 16 GB、Ollama 常駐、JST 0 / 6 / 12 / 18 時の scheduled session — CA `CLAUDE.md`）。
  CA の `verify.sh` 無引数はローカルで `pytest -q` 4,427 passed / 90 s（2026-09-24 実測、`uv run pytest -q`）
  に pyright・pip-audit・bandit が乗る。build の verify がこの機で走ることは費用であって、事故の
  記録があるわけではない。
- CA には 2026-09-24 時点で `.github/workflows/` が無い。Decision 3 の前提（CI が `verify.sh` を走らせる）
  を満たすまで CA は cloud に出せず、その workflow の追加は `.github/` に触れる diff なので人間が入れる
  （本 ADR の外、`boundary.md`）。
- 2026-09-24 の実測（systems-thinking-learning、private。証拠は private repo と著者の画面に
  あり、外部の読者は再現でしか確かめられない）:
  - `claude --cloud` は GitHub App の preflight が `status: null` を返すと bundle upload（VM に remote
    無し、push 不可）に無言で落ちる（[anthropics/claude-code#81776](https://github.com/anthropics/claude-code/issues/81776)、
    CLI 2.1.281 で再現）。`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` と `--ref main` で repo-bound になり、
    clone → 空 commit → `claude/cloud-probe-20260924-1343` へ push → CI `verify` success（run 36007681222、
    同 repo の Actions）まで通った。`--ref` は bundle 条件では CLI が session を作らず止まる。
  - `--cloud` は TTY 必須だが `script -q` の pty 越しなら Bash tool から起動できる。
  - 架空タスクのパイロット 1 本（n = 1）: 自己完結 packet で実装 / verify / built-in `/code-review` /
    commit 本文の報告形式が守られ、前提が崩れたとき（push 先が無い）は止まって報告した。判断役の
    検収（diff の範囲 → verify → commit 本文）も CI（`claude/**` で success）も通った。
  - cloud は `~/.claude` を読まない。repo の `CLAUDE.md`・`.claude/skills/`・（repo が 1 つなら）
    `.claude/settings.json` は読む（[公式 docs「What carries over from your setup」](https://code.claude.com/docs/en/cloud-environments#what-carries-over-from-your-setup)、
    2026-09-24 参照）。
  - `claude -p "<msg>" --cloud <session-id> --output-format json` で既存 session に非対話でメッセージを
    送れる。commit author は `Claude <noreply@anthropic.com>`。
  - cloud session は subscription の使用枠を消費し、別建ての課金は無い（[公式 docs「Limitations」](https://code.claude.com/docs/en/claude-code-on-the-web#limitations)）。
    この account は usage credits が off（同日の CLI debug log に `extra_usage_disabled`）。
- 境界: `rules/common/boundary.md` の「公開」と ADR-0043 red line 3（ADR-0049 注記の形: 無人 triage は
  working tree まで、公開へ出る commit / push / merge は人間の側。うち merge と push は ADR-0069 が
  判断役に移し、0043 の 2026-09-15 注記に記録済み）は、cloud build の最初の push が public repo では
  公開になる点と衝突する。本 ADR はこの境界を変えずに機構を置く。

## Decision

1. **build 役の既定は Claude Code cloud session。** 起動経路は `scripts/cloud-dispatch.sh <repo>
   <packet-file>` の 1 本に固定する — preflight（github.com remote / `main` が clean で origin と
   一致 / public repo は `--public-ok` が要る）、`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` + `--ref`、
   `script -q` の pty、session id と可視性と `--public-ok` を `logs/cloud-dispatch.jsonl` へ。Bash tool
   からも launchd 経由の常駐 session からも同じ経路。
2. **packet は自己完結。** cloud 版 packet は chain を本文に書く — Phase 0 / build 順 / built-in
   `/code-review` effort `medium` と reviewer への指示文 / must-not（`.claude/verify.sh`・`.github/`・
   `.claude/settings.json`・テスト弱化・main への push）/ commit 本文の報告形式。「packet に無いことは
   harness の規約が既定」は local 版にだけ残す。専用 reviewer（security-reviewer 等）は cloud に
   出さず、その判断は判断役に残る。
3. **verify は CI が走らせる。** cloud に出す repo は `.github/workflows/verify.yml` を持ち、`main` と
   `claude/**` への push で `.claude/verify.sh` を無引数で呼ぶ（actions は SHA pin、`permissions:
   contents: read`、`persist-credentials: false`、secret scan job 同居）。判断役は branch tip
   （`headSha`）に対する run の `conclusion: success` を読み、ローカルで verify を再実行しない。
   **CI の結論が検収の根拠になるのは、diff が `.claude/verify.sh` / `.github/` / `.claude/settings.json`
   に触れていないときだけ** — CI は branch 側の `verify.sh` と workflow を走らせるので（`verify_allow.py`
   の承認 hash は cloud に届かない）、触れた diff は検収に入れず bounce する。merge 後の `main` の
   run が事後の verify で、赤なら判断役は次の merge を止めて digest に報告する（revert は人間の判断）。
   ADR-0069 Decision 3 の「main で再実行」はこの形に置き換わる（同 ADR に注記）。
   CI を持たない repo は cloud に出せない — skill `verify-bootstrap` Step 6 を任意から標準段へ。
4. **cloud に出さない条件の正本は skill `task-triage` §3 の表。** 他の artifact（本 ADR、ADR-0057 の
   注記、`implementation-chain`）はこの表を指し、条件を複製しない。表の例外行は local 経路
   （Agent tool / `spawn-session`）、harness の gate に触れる行は dispatch されない（人間の diff）。
5. **公開 repo も cloud に出すが、無人では出さない。** cloud build の最初の push で branch・commit・PR は
   公開される（検収前）。これは ADR-0049 が rfcs/ に取った姿勢（working tree に書き、公開 commit は
   人間の機微点検を経る）より弱いので、同じ扱いにはしない。代わりに: (a) public repo への cloud
   dispatch と差し戻しは、digest がその task を 1 件ずつ名指しし、**人間がその task に OK を出した**
   ときだけ起動する（複数 task を名指しした 1 通の返事は各 task への答えとして扱う — ADR-0043
   Decision 5 の「1 件ずつ」は問い側の形で、答えの通数ではない）。無人 cycle は「dispatch 可」と
   列挙して起動しない。`cloud-dispatch.sh` は public repo を `--public-ok` 無しで拒み、フラグをログに
   残す — 可視性は機械が検査し、「人間が OK した」はフラグを渡す判断役の規律に残る。(b) packet は
   公開可能な書き方（task ID と `file:line`、機微はリンク先）。`.notes/` は clone に無いので、私的な
   値が cloud に届く経路は packet 本文だけで、それは Decision 4 の表が閉じる。(c) build 出力側は CI の
   テスト（CA では `tests/test_jev_results_stay_private.py`）が公開木へのラベル混入を**push 後に検知**
   する — 経路を閉じるのではなく、検収前に赤くする。private mirror は採らない（Alternatives）。
6. **PR は view、merge は ff-only。** cloud の PR 自動作成は on にする。ADR-0043 Decision 2「PR は
   使わない」は「PR は自動で開く view であり、merge 経路にしない」へ狭まる（同 ADR に注記。当時の
   却下理由「ややこしい」は、人間が PR を操作しないので当たらない）。検収と merge は判断役の
   `git merge --ff-only origin/claude/<name>` + push で、public repo の main への push を含めて
   ADR-0069 が既に判断役に移した範囲 — 本 ADR は変えない。merge 後に remote branch を消す。PR が
   merged にならない場合は `gh pr close` で閉じる。自動修正は off。
7. **差し戻しは同じ session へ。** `claude -p "<what and why>" --cloud <session-id> --output-format
   json`。1 task 1 retry / cycle（Damping は不変）。public repo では Decision 5 (a) の条件が差し戻しにも
   掛かる（差し戻された build は公開 branch へ push する）。
8. **無人 dispatch は tick の起動機構を変えない。** find → spawn → prompt → Slack はそのまま。cycle
   prompt に「public repo の cloud dispatch は ready と列挙、起動しない」の 1 句を足す（`task-triage`
   §2 が正本、prompt はその写し）。常駐 triage session が Decision 1 の script で private repo の cloud
   build と local build を dispatch する。cloud routine の API trigger は build 経路にしない — prompt が
   routine 固定で、fire payload は untrusted として包まれて届き、per-task packet を指示にできない。
   課金: usage credits が off の間、cloud build は subscription の枠を使うだけで `boundary.md` の
   「課金」に当たらない。credits を on にする（枠超過を従量にする）のは人間の操作で、on にした後の
   無人 dispatch は課金を伴うので、その時点で本 Decision を再訪する（Review-when）。
9. **変える artifact**: `scripts/cloud-dispatch.sh`（新設、`tests/cloud-dispatch.bats` が preflight と
   dry-run を固定）、`skills/task-triage/SKILL.md` と `references/packet-template.md`（§3〜§5 と
   cloud 版 packet）、`skills/implementation-chain/SKILL.md`（実行者の決定の dispatch 先）、
   `skills/verify-bootstrap/SKILL.md` と `references/ci-verify.yml`（Step 6 を標準段に、雛形）、
   `hooks/log-skill-usage.sh` / `log-agent-usage.sh`（coverage caveat のコメント — cloud の usage は
   入らない）、`scripts/triage-tick.sh`（cycle prompt の 1 句）、ADR-0043 / 0057 / 0069 への注記。
   **変えないもの**: `hooks/plan-executor-notice.sh`、`rules/common/planning.md` / `boundary.md`、
   tick の起動機構、`skills/spawn-session`、ADR-0043 の三役と red line、ADR-0057 の例外 (a)〜(c)、
   ADR-0069 Decision 4。

## Review-when

- anthropics/claude-code#81776 が close され、preflight 失敗時に bundle でなく repo-bound になったら、
  script から env var を外す（`--ref` は残す）。逆に `--ref` が bundle 条件で止まらなくなったら
  保険の代替を探す。照合先: 同 issue と CLI changelog。
- `cloud-dispatch.sh` が exit 2 を返し、出力に「interactive terminal」を含んだら（判断役の session が
  読んで digest に書く）、pty 経路が壊れたので無人 dispatch の経路を再設計する（routine API の再訪は
  ここ）。
- cloud の Projects が CLI から使えるようになったら（CLI changelog で著者が確認）、監視と差し戻しを
  Projects に寄せるか 1 回問う。
- 検収前の公開 branch が実害（第三者の引用・混乱・規約違反）を出したら private mirror を再訪する。
  観測者は著者、場は土曜の weekly gate（CA）と harness の Sunday triage。
- usage credits を on にしたら、無人 dispatch（Decision 8）を続けるかを 1 回判断する。判断の材料は
  cloud build 10 本の usage（claude.ai の usage 画面）と judge session の消費（`/usage`）で、commit
  本文の 3 行（Context / Decision / Review-when）に記録する。
- bounce 率 = triage の digest に記録する「§4 で bounce した build 数 / dispatch した build 数」。
  cloud build 10 本の値を、gate 触りと rebase の bounce（本 ADR で増えた条件）を除いて読み、直前の
  local build 10 本の digest 記録より高ければ、packet の形（自己完結）・review（`/code-review` 1 本）・
  effort（high 固定）のどれが効いたかを分けて再訪する。実行者・packet・review が同時に変わったので、
  差を effort 単独に帰さない。

  > **注記（2026-09-26, [ADR-0081](./0081-per-packet-effort-and-bounce-classification.md)）**: cloud の effort は high 固定ではなかった — 2026-09-26 の
  > probe（CLI 2.1.283）で、作成時の `--effort` は転送されず既定は medium。effort は packet ごとに
  > judge が選び、`cloud-dispatch.sh --effort` が `/effort` で適用する。bounce 率を effort 別に読む材料は
  > digest の build 行（effort / bounce 有無 / 分類）にある。
- anthropics/claude-code#87235（slash 入り branch を revision に取れない）が `claude/` branch の再開
  （新 session に `--ref claude/…`）を壊すなら、差し戻しを既存 session への送信に限定する。

## Alternatives Considered

- **hybrid — private repo は cloud、public repo は local のまま** — 却下。著者の前提「CA（public）が
  対象外なら移行に意味が無い」に反する。採用した形は無人 cycle では hybrid と同じ（public の cloud
  dispatch は起動しない）で、差は有人 cycle だけ — そこで public も cloud に出せることが著者の
  求めた範囲。public の公開リスクは Decision 5 の (a)〜(c) で持つ。再訪条件は Review-when の「実害」。
- **private mirror repo で build し、判断役が public へ push する** — 却下。二重の remote / CI / PR
  設定を維持する費用に対し、mirror が防ぐのは「検収前の branch が公開されること」だけで、packet
  本文の機微は書き方、build 出力のラベル混入は CI の検知（公開後）で扱う。著者は検収前の公開を
  受け入れた（Decision 5）。再訪条件は同上。
- **cloud で build し、判断役がローカルで verify を再実行する** — 却下。CI（Linux runner、workflow が
  導入したツール）とローカル（macOS、ローカル toolchain）は同じ入口を呼んでも同じ実行ではないが、
  著者の決定はローカルの負荷を落とすことで、差は「macOS 専用テストは `skipif` で自己申告し、
  Linux で落ちる production 側ガードは直す」（verify-bootstrap Step 6）で吸収する。merge 後の
  main の run が第 2 の判定。
- **cloud routine（API trigger）を build 経路にする** — 却下。routine の prompt は固定で、fire
  payload は untrusted 包みで届く（[公式 docs](https://code.claude.com/docs/en/routines#trigger-a-routine)、
  2026-09-24 参照）ため per-task packet を指示にできない。日次実行上限、research preview、commit
  author が著者の GitHub user になる点も不利。
- **現状維持 — Herdr / Agent tool のローカル build** — 却下（既定としては）。ローカル資源の奪い合い
  と、pane の監視・後片付けが判断役に残る。Decision 4 の例外行として存続する。
- **専用 reviewer も cloud に出す（repo の `.claude/agents/` に置く）** — 対象外（著者決定）。値層・
  脅威面の判断は判断役に残す。
- **cloud の effort を medium に落とす** — 未決。`--effort` を `--cloud` が session へ転送するかは未実測
  （CLI 2.1.281 に flag はある）。転送が確認できたら packet 側でなく script 側に置く。再訪条件は
  Review-when の bounce 率。

  > **注記（2026-09-26, [ADR-0081](./0081-per-packet-effort-and-bounce-classification.md)）**: 実測で転送されない（CLI 2.1.283）と分かり、既定はすでに medium
  > だった。effort は packet の `Effort:` 行で judge が選び、script が作成後の `/effort` で適用する形に決めた。

## Consequences

### Positive

- 判断役の session とローカル資源から build を分離する。pane の監視・worktree の後片付けが消える。
- 証拠が commit 本文 + CI run URL + session URL の 3 点に残り、pane に依存しない。
- 無人 cycle が Bash tool から dispatch できる（pty を script が供給）。
- packet が自己完結になり、harness を持たない環境にも同じ packet が通る。

### Negative

- packet が長くなる（規約を内包する）。reviewer への指示文は `implementation-chain` と packet の
  2 か所に同文で置く（cloud は harness を見られないため）。片方を変えたらもう片方も変える。
- **CA の無人 build は減る。** public repo の cloud dispatch は有人 cycle だけなので、無人 cycle で
  動く CA の build は例外行の local build に限られる。CA で無人に cloud を使うには本 ADR の Decision 5
  を再訪する。
- cloud の effort は claude.ai 側の既定（Opus 5.5 / high、2026-09-24 実測）。local build の medium 試行は
  local 限定になる。

  > **注記（2026-09-26, [ADR-0081](./0081-per-packet-effort-and-bounce-classification.md)）**: 2026-09-26 の probe では cloud session の既定は medium
  > （`CLAUDE_EFFORT=medium`）。effort は packet ごとに選び、cloud にも local にも適用する。
- cloud build は `~/.claude/metrics/*-usage.jsonl` に行を残さない — skill / agent の usage 読み値は
  local session の lower bound になる（consumer の契約「欠落は unmeasured」は不変）。
- 公開 repo では検収前の branch・PR が公開される（Decision 5）。ラベル混入は push 後に CI が検知する
  形で、公開自体は防げない。
- 「人間が OK した」の判定は機械化されていない。`cloud-dispatch.sh` が検査するのは repo の可視性
  だけで、`--public-ok` を渡すのは判断役の規律（文面）に依存する。
- CLI の未修正バグ（#81776）への回避策、GitHub と Anthropic cloud の可用性、usage credits を on に
  した後の課金に依存する。
- **戻すコスト**: 各 repo の `.github/workflows/verify.yml` と verify-bootstrap Step 6 の標準化は、
  local に戻しても残る（CI 自体は害にならない）。skill と ADR の注記は戻すときに再注記が要る。
- cloud branch は dispatch 時点の origin/main から出る。merge 前に main が進むと ff-only が通らず、
  「rebase して push」の bounce が 1 回増える（public repo では有人 cycle まで待つ）。
- CI は branch 側の `verify.sh` を走らせる。信頼の条件（gate ファイルに触れていない）を判断役が
  毎回確認する。
- cloud の commit author は `Claude <noreply@anthropic.com>`（routine では著者の GitHub user）。
- パイロットは n = 1 で、証拠は private repo にある。

### Neutral

- ADR-0043 の三役・red line、ADR-0057 の既定反転と例外 (a)〜(c)、ADR-0069 Decision 4 は不変。
- ADR-0043 Decision 2 と ADR-0069 Decision 3 は上の形で狭まる（両 ADR に注記）。

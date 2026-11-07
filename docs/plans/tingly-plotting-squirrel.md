# harness-stocktake の最初の release — 残りの最低限（plugin v0.1.0 / Action v1）

as-of 2026-11-02 JST。調査 report: [research/2026-11-02-stocktake-release.md](research/2026-11-02-stocktake-release.md)。
campaign plan: `~/.claude/docs/plans/enumerated-petting-beaver.md`。handoff: `~/.claude/.notes/handoff-stocktake-release-2026-11-02.md`。

## Context

- **Action の README どおりに置くと今は落ちる。** `uses: shimo4228/harness-stocktake-action@v1`（Action `README.md:67`、
  `examples/harness-stocktake.yml:42`）も、input `plugin_ref` の既定 `v0.1.0`（`action.yml:25-28`）も、両 repo にタグが 1 本も
  無いので解決しない。release は儀式でなく、README が指す ref を実在させる作業。
- **Action の今の main（c72a3c9）は smoke を一度も通っていない。** 2026-11-01 の audit smoke は sandbox の branch、apply smoke
  は f80a449 で走った。c72a3c9 は apply の判定（`scripts/stocktake.py:309-318` の `needs_hand`、`:358` で applied / pending を
  決める）を変えている。README の経路（`@v1`、`plugin_ref` は既定）も一度も走っていない。
- **plugin の利用者にタグは要らない。** README の 1 行 install は GitHub の default branch から入り、版は `plugin.json` の
  `version`（0.1.0）で決まる（2026-11-02 に一時 `CLAUDE_CONFIG_DIR` で install して確認）。plugin のタグの用途は Action の
  pin だけで、ただのタグは動かせるので、pin を名前どおり固定するには immutable release として出す。
- **当初の campaign plan からのずれ。** (1) directory 提出（Stage 4 #1「Stage 1 完了直後」）がまだで、handoff の Next steps
  から落ちている。(2) plugin README に実物との食い違いが 3 箇所ある（network の主張、要件の版 2 箇所）。directory の scan は
  README とコードの食い違いを拾うので、提出の前に直す。(3) Action の README と `action.yml` に古い記述が 6 箇所ある（下の B3）。
- **目標。** 両 repo の README の経路が end-to-end で通る。pin が名前どおり固定される。次からの Action release は
  「gh が draft を作り、著者が web で 1 回 publish する」だけで `v1` まで動く。

## Verdict（search-first、要素ごと）

| 要素 | Verdict |
|---|---|
| plugin の配布と版 | Adopt Claude Code の版解決（`plugin.json` の `version` → marketplace entry → commit SHA）。利用者に届けたい変更は `version` を上げる |
| Action が使う plugin の固定 ref | Adopt GitHub immutable releases。`v0.1.0` を release として出せば tag が動かなくなり、input に SHA を書かずに済む |
| Action の版 | Adopt GitHub 公式の型（actions/setup-node が運用中）: immutable な `v1.0.0` release と、release を付けない lightweight tag `v1`。`v1` という名の release は作らない（一度使った名前は二度と使えない） |
| `v1` を動かす仕組み | Build: release workflow 1 本（約 20 行、`uses:` なし、REST で git ref を更新）。actions/publish-action は README で alpha・内部用・非推奨（stop 3）、Actions-R-Us/actions-tagger と nowactions/update-majorver は最終 release 2022（stop 3: 保守なし）。claude-code-action と actions/checkout も自前の job で動かしている。抱えるのは workflow 1 本で、pin すべき action は無い |
| claude-code-action の参照 | Adopt SHA pin（`@<sha> # v1.0.266`）。GitHub の SHA pinning policy は composite action の nested `uses:` も見る（docs は沈黙、観測 3 件）ので、`@v1` のままだと policy を課す org で落ちうる。tag 参照は tj-actions 事件の経路でもあり、Anthropic 自身の `action.yml` も inner を SHA で pin している |
| Marketplace 掲載 | Adopt GitHub Marketplace。REST / `gh` に掲載欄が無いので、gh で draft を作り、著者が web UI で tick して publish する。これなら immutable と両立する |
| `plugin_marketplaces` の `#ref` | 未対応のまま（anthropics/claude-code-action PR #1497 は 2026-07-11 から open・review 0）。Action の自前 fetch step を残す |

## 著者が決めること（既定は太字。変えたいものだけ承認時に言ってもらう）

1. immutable releases を両 repo で **有効にする**。遡っては効かないので最初の release より前にやる。一度使った tag 名は
   再利用できないので、release は smoke が通った commit の SHA を指定して出す
2. claude-code-action を **SHA で pin する**。以後の更新は手で SHA を上げる
3. `v1` を動かす release workflow を **入れる**。中身は REST による `v1` の force 移動で、`~/.claude/hooks/validate-bash.sh:33-34`
   が止める手元の force push を、CI に置き換えたもの。初回の `v1` は Claude が通常の push で作る（新規なので force は要らない）
4. Marketplace に **v1.0.0 で載せる**。category は著者が選ぶ（同じ用途の掲載例は Continuous integration + Code quality。
   後から変えられるかは不明）
5. directory 提出は **今、main を追跡**（Branch or tag は空）。main への commit が新しい版の候補になり、既定では reviewer が
   1 版ずつ公開する。listing は次の版が公開されるまで直前の版を出し続ける。代わりに `v0.1.0` を追跡すると directory と Action
   が同じ commit を配るが、release のたびに portal で追跡先を書き換える。追跡先は提出後も Settings で変えられる。HOME を読む
   コードと URL の GET が同じ plugin にあるので、Policy hold になりやすい（著者の提出手順 skill §4）。README で両方を開示してから出す
6. Zenodo は **繋がない**（webhook 無し = 未接続を確認済み）。繋ぐなら C3 より前（Zenodo は toggle 後に publish された release だけを拾う）

**plan の承認と公開の OK は別。** 承認後に Claude が進めるのは 0・A・B（commit まで）。公開（C）は C0 で 1 回止まり、
diff を見てもらってから進める。

## 手順

commit 本文には `Plan: ~/.claude/docs/plans/tingly-plotting-squirrel.md` の行を入れる。attribution 行は入れない。commit は
ファイルを名指しで stage する（plan mode と subagent が plugin repo に `docs/` を作るので、`git add -A` は使わない）。

### 0. 記録（Claude）

- この plan と report を `~/.claude/docs/plans/`（report は `research/`）へ移し、`docs(plan): tingly-plotting-squirrel` で
  単独 commit する。plan mode はこの plan を plugin repo に置いたが、plugin repo の root は配布物そのもの
  （`marketplace.json` の `source: "./"`）で、docs は配布物の外に置く（著者の提出手順 skill §4）。campaign の plan と
  report も `~/.claude/docs/plans/` にある。plugin repo の `docs/`（未追跡）は消す

### A. plugin repo のコミット（Claude、push しない）

1. `CHANGELOG.md:3` の `0.1.0 — unreleased` → `0.1.0 — 2026-11-02`。`CITATION.cff` に `date-released: "2026-11-02"` を足す
   （tag が指す commit は後から直せない）
2. `README.md:13` と `:73` の要件を `Claude Code 2.1.292` 以上にする。README:5,18 の shell の `claude plugin install … --marketplace`
   は 2.1.292 から（session 内の `/plugin install` は 2.1.275）。`:73` の `0.1.0 (pre-release)` は消す（版は `plugin.json` と CHANGELOG が持つ）
3. `README.md:54` の **Sends** を実物に合わせる。telemetry は無い。network を使うのは 2 つ:
   - skill-stocktake が、skill に書かれた公開 http(s) URL へ 1 件ずつ GET を 1 回送る（10 秒 timeout、本文は読まない、private /
     local の host は飛ばす。GET は `skills/skill-health/scripts/url_liveness.py:170-180`、host の除外は `:81-130` と `:226-227`）
   - `uv run --frozen` が、初回に PyPI から取る: 各 script の dev group（pytest ほか、`uv.lock` で版を固定）と、project の
     build backend の hatchling（`uv.lock` に無く、版は固定されない）

   既存の opt-in 2 つ（notifier、Artifact）はそのまま残す
4. `README.md:103-105` の Scheduling に Action への 1 文とリンクを足す（GitHub では harness-stocktake-action が月次と
   `.claude/` を変える PR で回し、結果を 1 つの issue に集める）
5. `claude plugin validate --strict` と directory 自己検査（提出手順 skill §4）を通す。2026-11-02 の時点で、git 追跡 65 files、
   256 KiB 超なし、`.DS_Store`・symlink・submodule なし、hook・MCP・top-level `bin/` なし。commit 後に `git ls-files | wc -l`
   が 65 のままで `docs/` が入っていないことを確かめる

### B. Action repo のコミット（Claude、push しない）

1. `action.yml:155,191` を `anthropics/claude-code-action@<sha> # v<版>` にする。SHA は実装時に
   `git ls-remote https://github.com/anthropics/claude-code-action.git 'refs/tags/v1*'` で `v1^{}` を引き直す
   （2026-11-02 時点で v1.0.266 = `d535f5172dec02b204866b393d6b20b9b2aaf98d`。2026-11-01 の smoke 2 本も同じ commit に解決していた）
2. `.github/workflows/major-tag.yml` を新規に作る:
   - trigger は `release: types [published]`。workflow の `permissions: {}`、job の `permissions: contents: write`。`uses:` は無い
   - tag 名は env `TAG` で受ける。`^v[0-9]+\.[0-9]+\.[0-9]+$` に合い、かつ prerelease でないときだけ進む。それ以外は skip を出して終わる
   - `gh api` で `refs/tags/<major>` を `$GITHUB_SHA` に向ける。`git/ref/tags/<major>` が有れば `PATCH … force=true`、
     無ければ `POST git/refs`（両 repo とも ruleset 無し。token の既定は read なので、job で write を明示する）
3. 古い記述 6 箇所:
   - `README.md:67` の近く: `v1` は 1.x の release ごとに動く。固定したいなら `@v1.0.0` か commit SHA を使う
   - `README.md:111`: `GITHUB_TOKEN` が開いた PR の `pull_request` run は、承認待ち（`action_required`）で作られる（GitHub docs
     と 2026-11-01 の smoke で一致）。CI を回すには、その run を承認するか、PR を閉じて開き直すか、自分で push する
   - `README.md:113-115` Cost and time: 時間の実測を 1 文入れる（sample harness — skill 4・rule 1・agent 1・hook 2 — で audit 約 2 分、
     apply 約 1.5 分、GitHub-hosted runner、2026-11-01）。cost は未計測のまま残す
   - `README.md:127` と `action.yml:34` の `plugin_token`: `plugin_repository` が private repo のときだけ要る、と書く
   - `README.md:150` 見出し `Differences from the plan` → `Design notes`。`plugin_ref` が immutable release で固定されること、`v1` を
     workflow が動かすことを 1 行ずつ足す
   - `action.yml:2` の description（119 文字）は伸ばさない（Marketplace は 125 文字未満を求める）
4. ローカル検査: `python3 -m unittest discover -s tests -v`、`ruff check . && ruff format --check .`。`actionlint` が手元に
   無ければ CI に任せる。release の notes（何をするか、plugin v0.1.0 を pin、要件）を下書きする

### C. 公開の順序（OK を 1 回もらってから Claude が順に実行。✋ は著者の web 操作）

順序の理由: immutable な tag 名は焼き直せないので、release は試した commit の SHA に限って出す。plugin の `v0.1.0` は、
smoke（2026-11-01）で通した 971f0e7 と code が同じで、A が変えるのは README・CHANGELOG・CITATION だけ。Action の
`v1.0.0` は、C5 で README の経路そのまま（audit と apply）を試した commit に出す。

0. **止まる。** A・B の diff、commit message、release notes の下書き、公開する 2 repo の diff への
   `~/.claude/scripts/verify-public-detail.sh` の結果を見せて、公開の OK を 1 回もらう（この script が見るのはファイルだけ
   なので、message と notes は目で読んでもらう）。D の値と Data handling の下書きもここで渡す
1. plugin repo で immutable releases を有効にする（`gh api -X PUT repos/shimo4228/harness-stocktake/immutable-releases`）。
   GET で `enabled: true` を確かめる
2. plugin repo の main を push する。このあと D の Source → Validate を C3 より前に回せると、Blocks が出ても v0.1.0 に直しを
   入れられる（著者の都合が合わなければ C3 へ進む。Blocks が出たら v0.1.1）
3. `gh release create v0.1.0 -R shimo4228/harness-stocktake --target <A の HEAD の SHA> --title "harness-stocktake 0.1.0" --notes-file <CHANGELOG の 0.1.0 節>`。
   `v0.1.0` がその SHA を指し、release が immutable であることを確かめる
4. Action repo で immutable releases を有効にし、main を push して CI の緑を待つ。緑になったら `v1` を main の SHA に
   通常の push で作る（`git push origin <sha>:refs/tags/v1`。新規なので force は要らない）
5. smoke 1（非公開の smoke repo）: workflow を README の形にする（`@v1`、`plugin_ref` の行を消す）。
   - audit を `workflow_dispatch` で走らせる。成功・denial 0、ログ行 `Plugin: shimo4228/harness-stocktake@v0.1.0 (<sha>)` の
     SHA が C3 の SHA と一致することを確かめる
   - tracked issue で 2 項目を tick して **Apply** を tick する（Action が適用する 1 項目と、✋ の 1 項目。あれば `.claude/` 下の
     Retire）。apply が成功し、PR が更新され、✋ の項目が pending、もう 1 つが applied に分かれることを確かめる
6. `gh release create v1.0.0 -R shimo4228/harness-stocktake-action --draft --target <C5 で試した SHA> --title v1.0.0 --notes-file <下書き>`
7. ✋ 著者: draft を開いて "Publish this Action to the GitHub Marketplace" に tick する。tag と target の欄は触らない
   （draft の `v1.0.0` のまま。ここに `v1` と打つと、その名前が二度と使えなくなる）。初回は Marketplace Developer Agreement に
   同意する（2FA が要る）。category を選び、metadata の検査が "Everything looks good!" になったのを見てから Publish する。
   tick が出なければ、publish せずに止めて報告する（draft のうちは何も確定しない。原因はたいてい Agreement の未同意）
8. publish すると major-tag workflow が走る（`v1` は C4 で作ってあるので PATCH の側。以後の release も同じ側を通る）。
   `git ls-remote --tags` で `v1.0.0` と `v1` が C5 の SHA を指すこと、workflow が成功したことを確かめる

### D. directory 提出（✋ 著者の portal。C2 の後ならいつでも）

- Claude が渡す値: Repository `shimo4228/harness-stocktake`、Plugin path は空（root）、Branch or tag は空（main を追跡）。
  Data handling の 4 問は、A3 の README と同じ事実から答えを下書きする
- 掲載後、main への push は directory の新しい版になる（webhook 既定。reviewer が公開する）。main を常に配布可能に保ち、
  利用者に届けたい変更では `version` を上げる。portal の追跡先と anthropics/claude-plugins-official の日次 SHA bump の関係は
  文書に無い（report P7）
- 結果を読み戻して直すのは提出手順 skill §7、記録は §9（著者の掲載 queue（非公開）と行為ログに 1 行ずつ。commit まで、push はしない）

### E. 後始末（Claude）

1. `~/.claude/scheduled-tasks/README.md:17` の「一時停止」を実物（有効）に直す。`:18` も実物と照らす。別 commit にする
2. handoff note の Next steps 1・2 を済みにし、3（harness の修正 2 件、著者が保留）だけを残す
3. `~/.claude` の main を push する（handoff の 1）

## このplanに入れないもの

- handoff の harness 修正 2 件（`task-triage` の packet-template、`implementation-chain` の Review / Verify の順）: 著者が保留している。この project の外
- campaign plan の「記録」節（`enumerated-petting-beaver.md:333-337`）が約束した ADR と rfcs エントリ: campaign の記録で、release の成否に関わらない
- uv の PyPI 取得をなくす（各 `pyproject.toml` で project の build と dev group の既定 install を外す）: 正本は `~/.claude/skills/`
  で、6 skill の変更と同期が要る。release の後に回す
- plugin を `plugin/` subfolder に移す: HOME を読むのは監査の中核なので、移しても Policy hold の主因は消えない。review が
  開発用ファイル（`scripts/sync-from-local.sh`、`bench/`）を指摘したら §7 で対処する
- Dependabot による SHA の更新: root の `action.yml` の nested `uses:` を拾うかは未確認。この規模なら手で足りる
- CI（`ci.yml`）の action の SHA pin: CI は `contents: read` で、利用者には届かない
- smoke の "Sandbox probe" workflow の disable: handoff どおり著者の判断（任意）
- handoff の known limits: そのまま
- context-sync の `graph_lint.py` への委譲（`skills/context-sync/scripts/context_checks.py:64,614`）が、plugin に同梱していない
  sibling skill（`skills/jsonld-knowledge-graph/`）を指している。効くのは `graph.jsonld` を持つ repo だけ。直し方に選択がある
  （同梱するか、存在を確かめるか）ので著者に渡す

## Review-when

- claude-code-action の `plugin_marketplaces` が `.git#ref` を受け付けた（PR #1497 の merge）→ Action の fetch step と `plugin_token` を消す
- claude-code-action に security fix が出た → `action.yml` の SHA を上げる
- GitHub が major tag の移動を制限した、または native の仕組みを出した（2026-03-26 の roadmap の "stricter release requirements"）→ major-tag workflow を見直す
- directory の main 追跡で版の候補が多すぎると感じた → 追跡先を release tag に変える（Settings で可逆）

## Verification（end to end）

- A: `claude plugin validate --strict` と自己検査が通る。git 追跡が 65 files のまま
- B: unittest・ruff がローカルで通る。push 後の CI（actionlint が新しい workflow も読む）が緑
- C3: `v0.1.0` が A の SHA を指し、release が immutable
- C5: README の経路そのまま（`@v1`、`plugin_ref` は既定）で audit と apply が成功し、denial 0、plugin の SHA が C3 と一致、
  applied / pending の分け方が issue の予告どおり
- C8: `v1.0.0` と `v1` が C5 の SHA を指し、major-tag workflow が成功し、`https://github.com/marketplace/actions/harness-stocktake` が開く
- D: portal の状態が submitted。scan の指摘は §7 で処理する
- 最後に、両 repo の `git ls-remote --tags` と `gh release list`、`git -C ~/.claude status` を確かめる

## 時刻の注記

著者の掲載 routine が今日 10:10 JST に、plugin repo を外部の awesome-list に出す PR を作る（タグには依存しない）。C2 が先に
済んでいれば、相手は直した README を見る。間に合わなくても止める理由にはならない。

## 記述と実物の食い違い（この調査で見つけたもの）

- `~/.claude/scheduled-tasks/README.md:17` — listing-pr-daily を「一時停止」と書くが、実物は有効（次回 2026-11-02 10:10 JST）
- plugin `README.md:54` — 「no network fetch」と書くが、URL の GET と uv の PyPI 取得がある
- plugin `README.md:13`・`:73` — 要件 2.1.275。install の行は 2.1.292 以上を要る。`:73` は「(pre-release)」も
- Action `action.yml:26` — `plugin_ref` の "Pinned so a plugin release never changes a run unannounced"。tag が無く、immutable でもない
- Action `README.md:67`・`examples/harness-stocktake.yml:42`・`action.yml:25-28` — `@v1` と `v0.1.0` が実在しない
- Action `README.md:111` — 「他の workflow を起動しない」と書くが、run は作られて承認待ちで止まる
- Action `README.md:115` — 「Not measured yet」だが、smoke の実測時間がある
- Action `README.md:127`・`action.yml:34` — `plugin_token` を「private の間だけ要る」と書くが、plugin repo は 2026-11-01 から public
- Action `README.md:150` — 見出し「Differences from the plan」が、外部の読者に無い plan を指す
- `~/.claude/docs/plans/research/2026-11-01-stage1-plugin.md` — GitHub からの install を未検証としている。2026-11-02 に通ることを確認した
- campaign plan `enumerated-petting-beaver.md:333-337` — 約束した ADR と rfcs エントリが無い
- handoff note の Next steps — directory 提出（campaign plan Stage 4 #1）が落ちている
- 著者の提出手順 skill（非公開）`plugin-directory-submit/SKILL.md:144`・`:147` — 「auto-publish は 2 版目から」「webhook 無しで約 6 時間ごと」。
  現行 docs は、既定では reviewer が 1 版ずつ公開し、確認は「on a schedule」とだけ書く

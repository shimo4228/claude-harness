kind: external
# harness-stocktake（plugin）と harness-stocktake-action の最初の release を、最低限かつ筋のよい形で出すための外部仕様は何か

## Scope searched

as-of 2026-11-02（Claude Code 2.1.316 が CHANGELOG の最新）。統合役が notes 4 本と lead の手元証拠（項目 1–27）を読んで書いた。notes は `~/.cache/claude-research-notes/2026-11-02-stocktake-release/` の `plugin-versioning.md`（pv）、`action-versioning.md`（av）、`marketplace.md`（mk）、`adversarial.md`（ad）。

**記法**
- 出典の略号は notes の節番号（例 `pv:F5`、`av:F4`、`mk:F4`、`ad:1.2`）。`syn:W1`–`W4` は統合役が 2026-11-02 に自分で確かめた WebFetch（下記）。
- 読んだ深さ: 全文（出力がページ全文の形）/ 要約（WebFetch は小モデルを通すので逐語でない。引用は 125 字以内の断片）/ snippet（検索結果の抜粋のみ）/ API（GitHub API の JSON を WebFetch で読んだもの）。
- 公開 repo は plugin repo = shimo4228/harness-stocktake、Action repo = shimo4228/harness-stocktake-action。file:line は各 repo の root から。特記なき限り取得日は 2026-11-02。公式 doc の各ページに日付表示は無い。

**角度ごとの範囲**
- pv（呼び出し 35 = WebFetch 29 + WebSearch 4 + context7 2。目安 12–18 の約 2 倍。公式 doc が `plugins/` 配下へ再編されて 1 ページで閉じず、directory の tag 追跡と claude-code-action の ref 対応を issue・PR・commit 履歴で確かめたため）
  - Claude Code 公式 doc（code.claude.com/docs/en/ の plugin-marketplaces、plugins/ 配下の manifest-reference・loading・host-marketplace・marketplace-reference・cli-reference・dependencies・publish・install）。context7 `/websites/code_claude` で版の解決の節を再確認。
  - directory 公式 doc（claude.com/docs/ の plugins/submit・pre-submission-checklist、connectors/building/after-publishing、directory/submission-status・publish）。
  - claude-code-action の `action.yml`、`base-action/src/install-plugins.ts`、releases（v1.0.258–v1.0.266）、issue #1229、PR #1497、commit 履歴。Zenodo help と GitHub docs の citing。反証として Claude Code CHANGELOG 2.1.301–2.1.316 と「update が already at latest と言う」系の issue。
  - 見つからなかった: directory の定期確認の間隔、tag 追跡時の付け替え（force-move）の検出、directory 経由 `@synced` の更新比較の記述。
- av（呼び出し概算 120。目安 15–22 の 2 倍超。超過分の大半は「repo の今の状態 1 項目」の API fetch）
  - GitHub Docs（manage-custom-actions、immutable releases の how-to と概念ページ、release-and-maintain-actions、secure-use、lock-workflow-dependencies、rulesets、REST、events、`gh release` manual）。github.blog changelog（2025-08-15、2025-08-26、2025-10-28、2026-10-14）と 2026-03-26 の Actions security roadmap。github/roadmap #592・#1137。
  - 現物の repo（API + workflow ファイル）: anthropics/claude-code-action、actions/checkout・setup-node・upload-artifact・toolkit・typescript-action・publish-action・publish-immutable-action、github/codeql-action、astral-sh/setup-uv、haya14busa/action-update-semver ほか。
  - 二次資料: Semgrep blog 2026、Zenn、jvt.me 2026-04-24、pre-commit/action PR #231、community の議論。
  - 見つからなかった: immutable release の tag を force push したときの正確なエラー文言、`GITHUB_TOKEN` を ruleset の bypass actor にできると明言する文書、composite の nested `uses:` が SHA pin 強制の対象と明記する docs、Anthropic が `v1` の運用方針を書いた文書。
- mk（呼び出しは目安 12–18 の 2 倍超。件数の記録なし）
  - docs「Publishing actions in GitHub Marketplace」新旧 path と github/docs の raw markdown、Metadata syntax、Managing releases、REST の release、`gh release create` manual、Marketplace Developer Agreement（Effective 2025-05-27）。community discussions 24965・26787・25834・27118・210391。
  - Marketplace 検索（"harness stocktake" 0 件、"stocktake" 0 件、"harness" 28 件）。掲載済み 4 action（anthropics/claude-code-action、VIKOIT/reversibility-engine、devantler-tech/guard-installed-skill-edits-action、Chris0Jeky/llm-release-gate）の listing・release page・`.github/workflows`。
  - 見つからなかった: 2025–2026 の Marketplace 掲載方針の changelog（`github.blog/changelog/label/marketplace/` は 404）、掲載後の category 変更の記述、API で作った release の扱いを述べる公式文、掲載 action への security scan の記述。
- ad（呼び出し 36 = WebFetch 26 + WebSearch 10、ほかに local Read 4。目安の 2 倍）
  - GitHub Docs（secure-use、releasing-and-maintaining、immutable の how-to、publishing-in-Marketplace、lockfile）、changelog（2025-08-15、2025-10-28、2026-10-14）、Unit 42 の tj-actions 記事、poutine の unpinnable_action、OpenSSF Scorecard docs、setup-uv v8.0.0、claude-code-action、anthropics/claude-plugins-official、community 例（mtblck、mikeguzman、jedwards1230）。
  - 見つからなかった: (a) 1 repo から plugin と Marketplace 掲載の composite Action の両方を出している実例、(b) Marketplace 掲載が 2026 年の発見経路として効くことを示す一次資料や運用記録、(c) tj-actions 以外の 2026 年の action 乗っ取り（検索せず。上限に達した）。
- syn（統合役の追加確認。WebFetch 4 回。上限 5 回のうち 4 回を使用）。notes 同士・notes と手元証拠の食い違いのうち一次資料 1 回で決着するものだけ
  - W1 `https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/.github/workflows/bump-plugin-shas.yml`（要約 + 行引用）。
  - W2 `https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow`（要約）。
  - W3 `https://code.claude.com/docs/en/plugins/cli-reference.md`（出力が大きく保存ファイルになったので、`--marketplace` の行を Grep で直接読んだ）。
  - W4 `https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/.github/bump-tracking.json`（要約）。
  - 手元の Read: plugin repo の `README.md:1-120`、Action repo の `action.yml:1-215` と `README.md:56-155`（行番号の確認のため）。

## Found

### 要点（as-of 2026-11-02。根拠は各項）

1. plugin の版: Claude Code は git tag で更新を検出しない。版は `plugin.json` の `version` → marketplace entry の `version` → commit SHA 先頭 12 桁の順（P1）。tag が読まれるのは `#ref` / entry の `ref` で pin したときと、他 plugin が版範囲つきで依存するときだけ（P2、P3）。publish doc は「Otherwise you don't need a tag.」と書く。plugin の `v0.1.0` は、Action の `plugin_ref` の pin、利用者の任意の pin、Zenodo 用の GitHub release のためのもの。
2. GitHub marketplace 経由の利用者は default branch の HEAD から入る（手元 22）。`version` を据え置いた main の更新は既存利用者に届かない。third-party marketplace は auto-update が既定 off（P1）。
3. directory: 追跡先は branch でも tag でもよい。docs の標準は branch への merge。tag 追跡の更新手順は portal で追跡先を新しい tag 名に書き換えて Publish。既定の publish は reviewer が 1 版ずつ。同名 tag の付け替えの検出は docs に無い（P5）。Anthropic 側の marketplace repo は毎日 07:23 UTC に upstream HEAD へ sha を bump し、`releases-only` の 14 entry は最新 published release の tag commit へ bump する。portal との接続は文書に無い（P7）。
4. claude-code-action は `#ref` と `owner/repo` を拒否する（main、2026-11-02）。ref pin の PR #1497 は 2026-07-11 から open で review 0 件。Action の自前 fetch は残る（P9）。
5. Action の公式の型: `v1.0.0` を release にして immutable、`v1` は release を作らない plain tag にして workflow で動かす（A2）。`v1` という名の release は immutable ON だと publish で凍る（A3）。有効化は遡らない。両 repo とも今は無効（手元 5）。
6. major tag を動かす定番の道具は無い。GitHub 公式の publish-action は README が Alpha・internal 用。実例の過半は 5–9 行の自前 workflow（A4、A5）。権限は job の `contents: write`。両 repo に ruleset は無い（手元 23）。workflow が `GITHUB_TOKEN` で push した tag は他の workflow を起動しない（A6）。
7. SHA pin 強制は利用者側の設定。composite 内の `uses:` が対象かは docs が沈黙し、観測 3 件は対象になると示す（A7）。この Action は `anthropics/claude-code-action@v1` を 2 箇所で tag 参照している（`action.yml:155`、`:191`）。
8. Marketplace: 要件は public repo、root に action.yml 1 つ、unique な name。審査なしで即時公開。workflow ファイルは障害でない（M1、M2）。掲載の tick は release 作成画面だけにあり（REST / `gh` に field 無し）、release ごと（M4）。category は初回に選ぶ。変更の可否は未確認（M5）。description は実務者の報告で 125 文字未満。action.yml は 119 文字（M7）。
9. immutable と tick の両立: 観察は 1 例（guard-installed-skill-edits-action、2026-10）。publish 済みの immutable release に後から tick を付けられるかは未確認。draft → web UI で tick して publish する経路なら通る（M4、M8）。
10. 掲載が利用者獲得に効くという一次資料は見つからなかった。掲載は可逆で安い（M9）。
11. 別の枠組み: exact tag + immutable のみ（setup-uv）、lockfile 前提、plugin を Action に同梱（実例なし）など（X1）。plugin と掲載 Action を 1 repo から出す実例は見つからなかった。
12. 記述と実物の食い違い（Contradictions）: Action README:111 は「`GITHUB_TOKEN` で開いた PR は他の workflow を起動しない」と書くが、現行 docs と手元の観測は「run は作られ、承認待ちで止まる」（C1）。plugin の README:54 と :13 / :73 も実物とずれる（C2、C3）。

### P. Claude Code plugin の版・tag・directory

#### P1. 版の計算・更新検出・cache（pv:F1）
- URL: https://code.claude.com/docs/en/plugins/loading.md#versions-and-updates ／ https://code.claude.com/docs/en/plugins/host-marketplace.md#keep-users-up-to-date ／ https://code.claude.com/docs/en/plugins/manifest-reference.md#version。公式仕様。3 ページとも全文。context7 で同文を再確認。
- 本文: 「Claude Code computes a version for every plugin it installs, and that version is how it detects an update.」解決順は (1) plugin manifest の `version`、(2) marketplace entry の `version`、(3) どちらも無ければ source 型から（`github` / `url` / `git-subdir` は commit SHA の先頭 12 桁、marketplace 内の相対 path は installed directory の commit SHA）。「If you set `"version": "1.0.0"` and push new commits without changing it, users don't receive them.」「Don't set `version` in both `plugin.json` and the marketplace entry. If you do, Claude Code uses the `plugin.json` value without warning」（`claude plugin validate` は不一致を警告する）。cache は `cache/<marketplace>/<plugin>/<version>/`。自動更新は「on for Anthropic's official marketplaces … and off for every other marketplace」。有効でも session 開始後の最初のメッセージから最大 10 分のランダム遅延がある。ローカル path から add した marketplace の相対 path plugin は cache に複製されず、「loads its current source files at every session start, whatever its version string says」。
- こちらとの違い
  - `plugin.json` にだけ `version: "0.1.0"`、marketplace entry に version 欄は無い。docs が勧める「1 か所に置く」形と一致する。
  - main を `version` 据え置きで変えると、GitHub marketplace 経由の利用者は 0.1.0 の cache に残る。third-party は auto-update が既定 off なので、`version` を上げても利用者が `claude plugin update harness-stocktake@harness-stocktake` か Enable auto-update を行うまで届かない。
  - Action は `plugin_marketplaces` にローカル path を渡す（in place 読み込み）ので、`plugin.json` の `version` は Action の挙動を決めない。Action の pin は git fetch する ref だけが決める。
- 失効: 版の解決順が変わったとき（CHANGELOG の plugin version 関連の行で検知）。

#### P2. ref / sha の pin、`marketplace add`、`install --marketplace`（pv:F2、syn:W3）
- URL: https://code.claude.com/docs/en/plugins/marketplace-reference.md#plugin-sources ／ …/cli-reference.md ／ …/install.md#add-a-marketplace ／ …/host-marketplace.md#hold-users-on-one-version。公式仕様。pv は marketplace-reference・host-marketplace・install を全文、cli-reference を該当節で読んだ。syn:W3 で `--marketplace` の行を直接再確認。
- 本文
  - entry の `source` のうち `github` / `url` / `git-subdir` が `ref`（branch か tag。既定は repo の default branch）と `sha`（40 桁の小文字。`ref` と両方あれば `sha` を checkout）を持つ。相対 path の source（本 repo の `"./"`）は文字列そのもので、どちらも持たない。marketplace 自体の source（`github` / `git`）は `ref` を持ち、`sha` 欄は無い。
  - `claude plugin marketplace add` の `<source>` は `owner/repo`、`owner/repo#ref`、`owner/repo@ref`、`user@host:path[.git][#ref]`、`.git[#ref]` で終わる https URL。`claude plugin marketplace update` は「A marketplace added with a branch or tag `ref` updates to the latest commit of that ref, not the repository's default branch.」install.md の例は `/plugin marketplace add your-org/plugins#v1.2.0`。
  - `claude plugin install <plugin> --marketplace <source>` の行は「Install `<plugin>`, given by its bare name, from the marketplace at `<source>`, adding the marketplace first if you haven't added it yet. … Requires Claude Code v2.1.292 or later」（syn:W3。cli-reference の `claude plugin install` の option 表）。session 内の `/plugin install … --marketplace` は v2.1.275 以上（pv:F2。統合役は未再確認）。
  - CLI の `#ref` は branch か tag のみで commit SHA は不可と報告されている（issue #1229 のコメント、P9）。Action 自前の `git fetch --depth 1 origin "$REF"` は SHA も取れる。
- こちらとの違い
  - lead の `claude plugin marketplace add --help` に ref の option が無いのは、ref が `<source>` 文字列の一部だから。help に無いことは未対応の証拠にならない（手元 8）。
  - README の 1 行 install（`README.md:5`、`:18`）は 2.1.292 以上でだけ動く。README の要件表記は 2.1.275（`README.md:13`、`:73`）で、食い違う（C3）。2 段（`claude plugin marketplace add shimo4228/harness-stocktake` → `claude plugin install harness-stocktake@harness-stocktake`）は全版で動く（pv:F2）。
  - tag で pin したい利用者は `shimo4228/harness-stocktake#v0.1.0` と書ける。`--marketplace` に `#ref` を渡す形の実行は未確認（docs は「same forms」と書くだけ）。
- 失効: cli-reference の `<source>` 表や最小版が変わったとき。

#### P3. git tag の用途（pv:F3）
- URL: https://code.claude.com/docs/en/plugins/dependencies.md#release-a-plugin-that-others-depend-on ／ …/publish.md#tag-a-release ／ …/cli-reference.md#plugin-tag。公式仕様。dependencies・publish は全文、cli-reference は該当節。
- 本文: 「Tag each release as `<plugin-name>--v<version>`, where `<version>` matches the `version` field in that commit's `plugin.json`.」作成は `claude plugin tag [--push]`（annotated tag。validate、`plugin.json` と entry の version 一致、作業ツリーが clean、同名 tag が無いことを検査）。使われるのは依存の版範囲の解決だけ（「The dependency installs at the highest git tag that satisfies this range」）。publish.md: 「Tag the release in git when other plugins declare a version range on yours … Otherwise you don't need a tag.」
- こちらとの違い: harness-stocktake に依存する plugin は無い。計画の `v0.1.0` は依存解決から見えないが無害。更新検出にも使われない。
- 失効: 他 plugin が harness-stocktake へ版範囲つきで依存し始めたとき。

#### P4. 反証: 「version を上げれば届く」周辺の既知の不具合（pv:F4）
- URL: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md（2.1.301–2.1.316 のみ読んだ）／ https://github.com/anthropics/claude-code/issues/72616（本文を読んだ）／ #61954・#46081・#37252・#14061（題名のみ）。bug 報告。
- 内容: CHANGELOG 2.1.302「Fixed plugin marketplaces re-cloning on every refresh, and newly installed git plugins showing version "unknown"…」。#72616 は directory source の marketplace で cache した marketplace.json が更新されない（Claude Code 2.1.197、duplicate として close、2026-09-05 に lock）。#61954（close、2026-05-27）などは `claude plugin update` が marketplace clone を fetch せず「already at latest」と言う報告（題名のみ）。
- こちらとの違い: publish.md は現在 `claude plugin update` が「refreshes the marketplace」と書くので、古い版の症状の可能性が高い。2.1.316 での再現は未確認。本 repo の GitHub source の marketplace に #72616（directory source の話）は当たらない。

#### P5. directory: Source step・追跡・更新・publish（pv:F5、F6）
- URL: https://claude.com/docs/plugins/submit ／ https://claude.com/docs/connectors/building/after-publishing.md。公式 doc（日付なし、2026-11-02 取得）。両方全文。
- 本文（submit）
  - Source step の「Branch or tag (optional): the branch or tag that the directory follows for new versions. … Leave the field empty to follow the repository's default branch. A tag stays on its commit until you change the tag.」Submit for review で「the directory scans the newest commit on the tracked branch or tag」。「A validation result applies to one commit.」
  - 更新: 「Merge to the tracked branch, and the directory picks up the commit, checks it, and publishes it. … If the submission follows a tag, release a new version by changing the tag, as described in Change the tracked branch or tag.」その節は Settings タブの **Tracked branch or tag** を編集して **Save**。「The directory then scans the newest commit there as a new version; when it passes, select **Publish** again, or **Publish update** if a version is already live.」live の版は追跡先を変えても残る。
  - 検出: 「The directory checks the tracked branch for new commits on a schedule.」GitHub push webhook（既定で選択。repo admin 権限が要る）があれば push 時にも確認する。「Check for new commits」ボタンで即時確認できる。
  - version: 「If your `plugin.json` sets `version`, raise it with every release.」
  - publish: 既定は「An Anthropic reviewer publishes each version」。Overview タブの **Auto-publish** 行が適用中の設定を示す。Anthropic が承認時に「The reviewer publishes only the first version」か「You publish the first version」へ変えることがある。Settings の **Publish new versions automatically** は「Auto-publish doesn't apply while a reviewer publishes each version.」
  - 「The listing keeps serving the last published version until a new version is published, including when a new version doesn't pass or is held for a reviewer. If the security scan fails a new version, later versions also wait until an Anthropic reviewer clears the plugin.」「You can't change a submission's repository and folder after you submit.」repo は公開前に public が要る。listing の name と short description は live の版に追従する。
- 本文（after-publishing）: 「To update a listed plugin, push to the branch or tag the directory tracks for it. The directory picks up the new commit, runs the same validation and security scan as your first submission, and shows the result as a new version … If you set `version` in `plugin.json`, raise it with each release, because installed copies use it to tell that an update exists.」listing の name と short description は live の版の `plugin.json` と README から来る。reviewer が編集した文面は残る。
- 読み取り（解釈を含む）
  - 追跡先が tag のとき docs が書く更新手順は、追跡先の欄を新しい tag 名に書き換える操作。検出の記述は「tracked **branch** for new commits」で、同名 tag の付け替えの検出は書かれていない。after-publishing の「push to the branch or tag」は付け替えか tag 名の切替かを区別せず、submit の記述のほうが具体的。
  - 追跡先は任意の branch でよいと読める。`release` や `stable` のような専用 branch をリリース時にだけ進める運用を docs は禁じていない（推論。docs の例ではない）。
  - directory が commit を拾うのに `plugin.json` の version 変更は要件として書かれていない。`version` を上げる理由は、入れた側の copy が更新の有無をそれで判定するから。
- こちらとの違い: tag `v0.1.0` を追跡先にすると、directory が scan する commit と、Action が `plugin_ref=v0.1.0` で実行する commit は同一になる（tag が動かない前提）。branch を追跡させると、main への各 commit が「新しい版」になり、既定の publish 設定では 1 つずつ Publish が要る。
- 失効: submit ページの「Change the tracked branch or tag」節が変わったとき。

#### P6. directory の提出前 checklist のうち版・構成に関わる行（pv:F7）
- URL: https://claude.com/docs/plugins/pre-submission-checklist.md ／ https://code.claude.com/docs/en/plugins/manifest-reference.md#directory-listing-fields。公式 doc。両方全文。
- 本文
  - 「Set `description`, `author`, and `version` | Warning」（無いと warning で block ではない）。`raise version with every release`。
  - 「Submit one plugin at a time.」publish.md の例が「one entry whose `source` is `"./"`」で、本 repo と同形。
  - directory は `icon`、`documentationUrl`、`supportUrl`、`privacyPolicyUrl`、`termsOfServiceUrl` を提出時に `plugin.json` から読む。Claude Code は load 時に無視する。marketplace entry に書くと validate が unknown field を報告する。
  - launcher の規則: `npx` / `bunx` / `uvx` / `pipx run` / `uv run` を hook や MCP server の command で使うと、版の pin や `--locked` / `--frozen` が要る（Blocks）。「A script that `SKILL.md` only tells Claude to run isn't part of this check.」「To avoid the hold, keep the plugin at the root of its own repository」。
  - 規模: 512 file 以下、画像・font 以外の file は各 256 KiB 未満（超えると reviewer hold）。repo は GitHub の archive で 50 MiB 未満など。
- こちらとの違い: plugin は repo root にあり、`hooks/hooks.json` と `.mcp.json` は無い。`uv run` / `uvx` / `npx ` / `pipx` / `bunx` は 7 file に出る（SKILL.md 4、README.md 1、script 2）が hook / MCP の command ではなく、launcher 規則の対象外に見える（浅い確認）。git 追跡の file 数と大きさは未確認。手元の checkout に `skills/skill-health/.venv` などがあり、git が追跡していなければ対象外。

#### P7. directory の実物: anthropics/claude-plugins-official と bump workflow（ad:Q5 (5)、syn:W1、W4）
- URL: https://github.com/anthropics/claude-plugins-official（README、`.claude-plugin/marketplace.json`）／ `.github/workflows/bump-plugin-shas.yml` ／ `.github/bump-tracking.json` ／ 提出 form https://clau.de/plugin-directory-submission。実物の読み取り。ad は README と marketplace.json の先頭 10 万字を読んだ。syn は workflow と JSON を要約で読んだ。
- 内容
  - README: 提出は form。「External plugins must meet quality and security standards for approval.」警告「Anthropic does not control what MCP servers, files, or other software are included in plugins and cannot verify that they will work as intended or that they won't change.」
  - marketplace.json の外部 entry は `sha` を持つ。先頭 4 件は 42crunch（`ref: v1.5.5` + sha）、adobe（`ref: main` + sha）、endorlabs/ai-plugins（sha のみ）、airtable（`ref: main` + sha）。約 167 entry を数えたが、読んだのは先頭 10 万字で、残り約 9 万字は未読。
  - `bump-plugin-shas.yml`（syn:W1）の trigger は `schedule: cron '23 7 * * *'`（毎日 07:23 UTC）と `workflow_dispatch`（入力 `max_bumps` 既定 60、`plugin`）。冒頭の説明は「each external entry whose upstream HEAD has moved past its pinned SHA」を対象とする。`bump-tracking.json` の `releases-only` に載る entry は「to the latest published release tag's commit instead of HEAD」へ bump する。bump の前に「validate at the new SHA with `claude plugin validate` inline, then open one PR per bumped plugin」。PR を開いたあとに `scan-plugins.yml`、`check-mcp-urls.yml`、`validate-plugins.yml` を bump branch に dispatch する（required checks）。「Failing entries stay isolated in their own PR; passing bumps merge independently.」
  - workflow は `ref` 欄にも plugin の `version` にも触れず、tag を値にもつ `ref` の扱いも書かない。`bump-tracking.json` のキーは `releases-only` だけで 14 件（plugin 名。azure、deepeval、greptile、qodo ほか）。追加・削除の方法と決める人は書かれていない。ほかに `revert-failed-bumps.yml` と `validate-*.yml` が存在する（名前のみ）。
- こちらとの違い
  - 「main を追跡」と「tag を追跡」の両方に前例がある（`ref: main` + sha、`ref: v1.5.5` + sha）。HEAD 追従の entry は日 1 回の bump なので、反映は最大で約 1 日遅れうる（推論）。
  - portal の「Tracked branch or tag」（P5）と、この marketplace repo の bump（HEAD または最新 published release）の関係は、どの文書にも書かれていない。`releases-only` の存在は、「published な GitHub release の tag commit」を追従先にする型があることを示す。
- 失効: bump workflow または `bump-tracking.json` が変わったとき、portal の docs が marketplace repo との関係を書いたとき。

#### P8. directory 経由の利用者への届き方（`@synced`）（pv:F13）
- URL: https://code.claude.com/docs/en/plugins/publish.md#how-a-listed-plugin-reaches-claude-code-users ／ …/loading.md#plugins-synced-from-claudeai。公式仕様。両方全文。
- 内容: directory 経由の plugin は `<name>@synced` として読み込まれ、「each time you start Claude Code, it syncs once in the background, downloading new and updated plugins」（2.1.273 以上。`CLAUDE_CODE_OAUTH_TOKEN` / `ANTHROPIC_AUTH_TOKEN` / apiKeyHelper の session では sync しない）。同名の plugin が他の origin（marketplace など）から有効なら synced 側は「reports the synced copy as not loaded」。claude.ai がホストする marketplace の plugin は、claude.ai が記録した版が版であり manifest の `version` は読まれない。これが directory 経由の synced に当たるかは書かれていない。
- こちらとの違い: 利用者の経路は 2 つ（GitHub marketplace と directory の synced）で、同じ repo の同じ `plugin.json` から来る。Action の runner は claude.ai の sign-in が無い credential（token / API key）なので synced を読まず、衝突しない。

#### P9. claude-code-action の `plugin_marketplaces` と ref pin（pv:F9–F11、ad:2.5）
- URL: https://raw.githubusercontent.com/anthropics/claude-code-action/main/base-action/src/install-plugins.ts ／ …/main/action.yml ／ https://github.com/anthropics/claude-code-action/releases ／ issue #1229 ／ PR #1497。実装の読み取りと issue・PR の記録（採用実績ではない）。コードは WebFetch の要約（引用を含む）、issue と PR は要約。
- 内容
  - 受け付ける: ローカル path（`./`、`../`、`/`、Windows の drive letter。追加検査なし）と、`^https:\/\/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+\.git$` に合う https URL。拒否する: `owner/repo`、`http://`、`git@…`、`ssh://`、`.git` で終わらない URL（`#ref` 付きを含む）。エラーは `Invalid marketplace URL format: <input>`。実行は `claude plugin marketplace add <entry>`（shell なしの spawn）。`action.yml` の description は「Newline-separated list of Claude Code plugin marketplace Git URLs to install from」で ref の言及なし。
  - `install-plugins.ts` の最新 commit は 2026-01-05「feat: support local plugin marketplace paths」（#761）。commit 履歴の表は 4 件で末尾が「Loading」表示のため、全件かは未確認。releases v1.0.258（10/22）–v1.0.266（10/31）のうち plugin に触れるのは v1.0.264 の「docs: use claude-plugins-official in plugin examples」（#1932、docs のみ）だけ。
  - issue #1229「Support version pinning for plugin_marketplaces」: 2026-04-17 起票、open、label `enhancement` `feature-request` `p3`、reactions 8、maintainer の返信なし。2026-09-10 のコメント「The CLI itself already accepts the fragment form … Only the action's `MARKETPLACE_URL_REGEX` blocks it」、`git clone --branch` は branch か tag だけなので SHA は fragment で使えない。2026-10-20 のコメント（v1.0.254 / Claude Code 2.1.304）「The action validates `plugin_marketplaces` more strictly than the command it passes the string to.」回避策は ref 指定で clone して local path を渡す形。公式の予約名（`claude-code-plugins` など）の marketplace は local path では使えない。plugin の `name`（harness-stocktake）は予約名に当たらない。
  - PR #1497「feat: support ref pinning for plugin_marketplaces via .git#<ref> suffix」: 2026-07-11 から open、review 0 件、1 commit、`Closes #1229`。実装は ref で fetch して temp directory に置き、local marketplace として add する（`init → remote add → fetch --depth 1 origin <ref> → checkout FETCH_HEAD`）。作者は別 input にする案にも応じると書く（2026-09-16）。
  - community の例（ad:3.1、3.2: mtblck/claude-marketplace、mikeguzman/agent-skills）は `plugin_marketplaces: https://github.com/<owner>/<repo>.git` を ref 無しで使う（default branch に浮く）。tag・release なし、stars 0。
- こちらとの違い: Action README の記録（`README.md:152`）と、実装、issue #1229 の 3 点が独立に一致する。#1497 の実装は本 Action が自前で行う fetch（`action.yml:85-103`）と同じ手順。#1497 が merge され release されれば、`plugin_marketplaces: https://github.com/shimo4228/harness-stocktake.git#v0.1.0` に置き換えられ、自前の fetch step と `plugin_token` を消せる。時期の見込みは立たない。
- 失効: #1497 か同等の変更が merge され release されたとき、`install-plugins.ts` に新しい commit が入ったとき、`action.yml` の description に `#ref` が現れたとき。

#### P10. Zenodo の GitHub 連携（pv:F12）
- URL: https://help.zenodo.org/docs/github/enable-repository ／ https://help.zenodo.org/docs/github/archive-software/github-upload/ ／ https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content。公式 doc。3 ページとも要約（引用あり）。
- 内容: 「Once connected, new releases from the repository will be automatically ingested and archived.」手順は「Create a release in GitHub.」で、前提は repository を有効化済みであること。GitHub docs「Zenodo archives your repository and issues a new DOI each time you create a new GitHub release.」有効化より前に作った release の扱いと、tag だけ（release なし）の扱いは、どの page にも書かれていない（snippet: 過去の版を archive するには release を作り直す、という GRASS wiki の記述。未確認）。
- こちらとの違い: どちらの repo にも release がまだ無いので、順序は「toggle を有効化 → GitHub release を publish」で、有効化前の release の扱いに依存しない。tag を push しただけでは release にならない。

### A. GitHub Action の版タグ運用

#### A1. GitHub Docs の現行の指針（av:F1、F2、F3、F5、ad:1.1）
- URL: https://docs.github.com/en/actions/how-tos/create-and-publish-actions/manage-custom-actions ／ https://github.com/actions/toolkit/blob/main/docs/action-versioning.md ／ …/release-and-maintain-actions ／ actions/typescript-action の `script/release`。公式 doc。av は決定に効く主張を prompt を変えて 2–4 回取り直して一致を確認。
- 内容
  - manage-custom-actions: release branch（例 `release/v1`）で検証 → semver の release tag（`v1.0.1`）→「Move the major version tag (for example, `v1`) to point to the Git ref of the current release.」→ 破壊的変更は新 major（`v2`）。利用側の参照形は major tag / patch tag / branch / full SHA。SHA の代償は「users will not receive further updates」、tag は「could be deleted or moved」。default branch は不安定なので参照させない。immutable releases は 1 文だけで、有効化しているなら別ガイド（A2）に従えと案内する。
  - toolkit の action-versioning（immutable より前）: 参照形 3 つ（major tag が推奨）。作者へは (1) 版ごとに GitHub release、(2) Marketplace 公開は release 作成時の選択、(3) major tag を現行 stable へ動かす（`git tag -fa v1 -m "Update v1 tag"` / `git push origin v1 --force`）。
  - release-and-maintain-actions: 「keep major (`v1`) and minor (`v1.1`) tags current to the latest appropriate commit」。例の JasonEtco/build-and-tag-action について、immutable releases を有効にすると release に紐づく tag をこの action では force push できないと note で書く（A5）。
  - typescript-action の `script/release` はローカルで `git tag … --force` と `git push … --force`。
- こちらとの違い: 著者のローカル hook が `git push -f` / `--force` を止める（手元 6）ので、ローカル force push の型は使えない。workflow 経由が要る（A4、A6）。toolkit の (1) の release の tag は immutable ON の repo では動かせないので、(3) の対象は release に紐づかない plain tag に限る（A2）。

#### A2. 公式の immutable 時代の型（av:F4、ad:1.2）
- URL: https://docs.github.com/en/actions/how-tos/create-and-publish-actions/using-immutable-releases-and-tags-to-manage-your-actions-releases。公式 doc。av は要約 4 回で一致、ad も取得。ページは github/docs PR #40858（2025-10-14 merge）が提供プランを足す前から存在する。
- 引用: 「If you are ready to share an unchangeable version of your action, create a release on GitHub with a release-specific tag (for example, `v1.0.0`).」「If you want to be able to update the Git tag of a release later, do not create a release on GitHub.」「For a major version, update the tag to point to the Git ref of the latest related minor version or patch version.」移動の例は `git tag -f TAG-NAME` と `git push -f --tags`。このページに無いもの: 利用者への pin 指針、tag 移動の警告、Marketplace の checkbox、Latest への言及。
- こちらとの違い: 予定（release `v1.0.0` + major tag `v1`）と一致する。例の `git push -f --tags` は全 tag を push する書き方で、実例の workflow は対象 1 本（`git push origin v1 --force`）にしている（A4）。

#### A3. immutable releases の仕様と採用実績（av:F6、ad:1.6）
- URL: https://github.blog/changelog/2025-10-28-immutable-releases-are-now-generally-available/（GA 2025-10-28）／ https://github.blog/changelog/2025-08-26-releases-now-support-immutability-in-public-preview/ ／ https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases。公式。WebFetch 要約。
- 仕様
  - 固定されるのは release の Git tag（特定 commit に固定され、移動も削除もできない）と release assets。固定されないのは title・notes・pre-release と latest の印。release attestation（Sigstore bundle）が付き、`gh release verify <tag>` で検証できる。「Tags for new immutable releases are protected and can't be deleted or moved.」
  - tag 名の焼き付き: release を消せば tag も消せるが「you cannot reuse the same tag name」。repo を消して同名で作り直しても、元の repo で immutable release に使った tag は再利用できない。二次の報告に community #178351（2025-11-14）、ZAAI-com/git-same（削除済み release の同名 tag push が GH013 で拒否）、github/ospo-reusable-workflows issue #83（"tag_name was used by an immutable release"）。
  - 有効化: repo は Settings の "Releases"。REST は `GET|PUT|DELETE /repos/{owner}/{repo}/immutable-releases`（admin。GET は `enabled` と `enforced_by_owner`）。遡らない: 「immutability will only apply to future releases」、changelog「Existing releases remain mutable unless you republish them」。後から無効化しても、作成済みの immutable release は immutable のまま。
  - draft → publish: 概念ページの推奨は「draft で作る → assets を全部付ける → publish」。assets を持たない release（source archive のみ）は draft を経ずに publish でよい。publish 後の asset 追加は 422「Cannot upload assets to an immutable release」（ospo-reusable-workflows #83）。`gh release create` に immutable を指定する flag は無い（第三者の skill ページが書く `--immutable` は manual に不在）。`--draft` と `--verify-tag` はある。
  - release に紐づかない tag（`v1` の軽量 tag 等）は動かせる。明示する文書は A2 と release-and-maintain-actions の note。
  - docs が action 作者に有効化を勧めるかは、manage-custom-actions と A2 とも「有効化しているなら」の条件付きで、「you should enable」の文は読んだ範囲に無い。
- 採用実績（av が 2026-11-02 に API で確認した直近 release の `immutable`）

| repo | 直近 release の immutable | major tag の扱い |
|---|---|---|
| actions/setup-node | true（v7.1.0 2026-10-08、v7.0.0 2026-07-14） | `v7` は release 無しの軽量 tag で v7.1.0 と同一 commit |
| github/codeql-action | true（v4.39.1 2026-10-21） | `v4` の annotated tag が存在 |
| astral-sh/setup-uv | true（v8.0.0 2026-03-29 から） | v8 以降は major / minor tag を出さない方針（A4） |
| haya14busa/action-update-semver | true（v1.4.0–v1.5.1、2025-09） | `v1` の annotated tag が存在（v1.5.1 への追従は未確認） |
| actions/checkout | false（v7.0.1 2026-07-20） | 手動 workflow で動かす（A4） |
| actions/upload-artifact | false（v7.0.2 2026-10-07） | 未確認 |
| anthropics/claude-code-action | false（直近 6 release と `v1`） | `v1` の annotated tag を workflow で動かす（A4） |
| sersoft-gmbh/running-release-tags-action | false | 追従 tag 用に release object を作る（A5） |

- こちらとの違い: 両 repo とも無効（手元 5）。plugin repo の `v0.1.0` を tag だけで出すと tag は動かせる状態のままで、Action の `plugin_ref` 既定 `v0.1.0` の pin は tag 名では固くない。固めるには、有効化してから release として publish するか、SHA で pin する。

#### A4. 現物の運用（av:F8–F11、ad:1.7、1.8）
- URL: https://raw.githubusercontent.com/anthropics/claude-code-action/main/.github/workflows/release.yml ／ actions/checkout の `.github/workflows/update-main-version.yml` ／ actions/setup-node の `.github/workflows/release-new-action-version.yml` ／ https://github.com/astral-sh/setup-uv/releases/tag/v8.0.0。実例（workflow ファイルと API）。av は release.yml を 3 回別 prompt で取り直した。
- anthropics/claude-code-action（av:F8）
  - release 一覧: `v1`（name "Claude Code GitHub Action v1.0"、published_at 2025-08-26、人手、`GET /releases/latest` もこれ）と、`v1.0.2xx`（github-actions[bot]、最新 v1.0.266 = 2026-10-31）。tag `v1` は annotated（tagger `github-actions[bot]`、message "Update v1 tag to v1.0.266"、2026-10-31T01:05:47Z）。人手で作った `v1` release object は作り直さず、その tag を release ごとに動かしている。
  - release.yml の trigger は `workflow_dispatch`（`dry_run` 入力）か、"CI All" の workflow_run が main で成功し commit message が `chore: bump Claude Code to` で始まるとき。job `create-release`（environment `production`、`contents: write`）は最新の `v[0-9]*` tag の patch を +1 → `git tag -a "$next_version" -m "Release $next_version"` → `git push origin "$next_version"` → `gh release create "$next_version" … --latest=false # keep v1 as latest`（`--generate-notes` も）。job `update-major-tag`（`needs: create-release`、environment `production`、`contents: write`）は `git tag -fa "$major_version" -m "Update $major_version tag to $next_version"` → `git push origin "$major_version" --force`。checkout は `actions/checkout@v6`（`fetch-depth: 0`、token 指定なし = 既定 `GITHUB_TOKEN`）。
  - 含意: `--latest=false` で per-version release を Latest から外し、人手の `v1` release を Latest に固定する設計。「`v1` という名前の release」は immutable ON の repo では publish の時点で tag が固定されるので、真似できない。有効化前に作った release は mutable のまま残る（A3）ので、claude-code-action が将来有効にしても `v1` release を作り直さない限り動く。README と docs/security.md は `@v1` を例示するだけで、SHA pin や版運用の説明は無い。
- actions/checkout（av:F9）: `update-main-version.yml` は `workflow_dispatch` のみ（入力 `target`〔tag か ref〕、`major_version`〔choice〕）。`actions/checkout@v7`（`fetch-depth: 0`）→ git config（github-actions[bot]）→ `git tag -f <major> <target>` → `git push origin <major> --force`。コメントに rollback tool として使える旨。release は per-version のみで bare major の release は無く、`immutable:false`。`target` 入力を持たせると、同じ workflow で `v1` を 1 つ前の `v1.x.y` へ戻せる。
- actions/setup-node（av:F10、GitHub 自身の「immutable release + 動く major tag」の現物）
  - `v7`（軽量）= `v7.1.0`（軽量、commit 949feb24…）、`v7.0.0` は別 commit。release の `immutable` は v7.1.0 と v7.0.0 とも true、bare `v7` の release は無い。`v7` を v7.0.0 の後に動かしたか初回作成かは API では区別できない。
  - 経路: `release-new-action-version.yml` が `release: types: [released]` または `workflow_dispatch`（入力 `TAG_NAME`）で起動。`permissions: contents: write`、job の environment は `releaseNewActionVersion`、step は `uses: actions/publish-action@v0.4.0`（`source-tag`、`slack-webhook`）。publish-action の README は「The actual major tag update will require manual approval.」で、environment の required reviewers で止める設計。
  - environment は docs が「Users with GitHub Free plans can only configure environments for public repositories」と書く。required reviewers が Free の public repo で使えるかは明記が無い。
- astral-sh/setup-uv（av:F11、ad:1.7）
  - v8.0.0（2026-03-29）の本文「This is the first immutable release of `setup-uv`」「## No more major and minor tags」「You won't be able to use `@v8` or `@v8.0` any longer.」理由は「pinning to major releases opens up users to supply chain attacks」（tj-actions を引く）。推奨は exact tag `@v8.0.0`、「Or even better the githash」。変更点に "Remove update-major-minor-tags workflow"。`v7` tag は凍結で残る。README の例は SHA + version comment。jvt.me（2026-04-24）によると、移行後に Renovate / Dependabot が利用者を自動で追従させにくくなった。
  - j178/prek-action v3.0.0 も「will no longer publish moving major or minor tags」と書く（snippet のみ。本文は未読）。
  - 両者は CLI を入れる action で、利用者は CI の長期常用者。harness-stocktake-action は月 1 回の schedule 中心で、更新頻度の前提が違う（ad:1.7）。
- 含意: immutable releases と動く major tag は技術的に両立する（A2、setup-node）。両立しないのは「`v1` という名前の release」（claude-code-action の型）と「追従 tag 用の release を作る tool」（A5）。setup-uv は技術要因でなく方針として major tag を出さない選択をした。

#### A5. major tag を動かす道具（av:F15、ad:5.3）
- 根拠: 各 repo の API・README・workflow（2026-11-02）。
- 一覧

| tool | 最終 release / push、stars | 形 | immutable との相性・備考 |
|---|---|---|---|
| actions/publish-action（GitHub） | release 無し、tag v0.1.0–v0.4.0（`v0` 無し）。main の最終 commit 2026-09-29、60 stars | node24 の JS action。`git.updateRef(force:true)`、無ければ `createRef` | README は "Alpha"、"for internal usage only, issues are disabled and contributing PRs will not be reviewed"、"We also do not recommend this action for public or production usage"。source tag は published かつ非 prerelease の release が必須で semver 検証あり。入力 `source-tag`・`slack-webhook`・`token`（既定 `github.token`）。`contents: write` 推奨。plain tag を動かすので immutable と両立 |
| haya14busa/action-update-semver | v1.5.1（2025-09-14）、58 stars | composite + script.sh。`git tag -fa "${MAJOR}" -m … "${TAG}^{}"` → `git push --force origin "${MAJOR}"`。trigger は `push: tags: v*.*.*`。`major_version_tag_only: true` で major のみ | plain tag を動かすので両立。`actions/checkout` の後に実行。permissions の記載は README に無い（push には `contents: write` が要る）。open issues 3。自身の release は actionutils/trusted-tag-releaser（1 star、license 無し）経由 |
| sersoft-gmbh/running-release-tags-action | v4.0.1（2025-11-07）、7 stars | JS action。major / minor tag を動かし、既定で追従 tag 用の release も作る（`create-release` 既定 true） | 既定のままでは `v4` 等の release object を作り、immutable ON と衝突する。`create-release: false` なら tag のみ（README の読み。未実行） |
| nowactions/update-majorver | v1.1.2（2022-01-28）、23 stars | JS action（node16）。`push: tags: v*` | 実装未読（force の有無は不明） |
| Actions-R-Us/actions-tagger | v2.0.3（2022-11-17）、最終 push 2024-02-16、126 stars | 未確認 | 保守停滞。実装未読 |
| rickstaa/action-update-semver | 最終 push 2024-05-23、3 stars | haya14busa の fork | 停滞 |
| JasonEtco/build-and-tag-action | v2.0.1（2022-12-21）、104 stars | JS action の build + release tag 自身と major tag を force push | immutable ON では使えないと GitHub docs が明記。composite には不要 |
| 自前 workflow（claude-code-action、checkout） | – | `git tag -f(a)` + `git push origin <major> --force` を `contents: write` で | 依存無し。A4 にそのままの行がある |

- 実例の tag の型: annotated（claude-code-action、haya14busa、codeql-action）と軽量（setup-node、`git tag -f`）の両方がある。
- 外部 tool を使う公式の実例は publish-action（setup-node が `@v0.4.0` 固定で使う）のみ。checkout と claude-code-action は自前 workflow。publish-action の `main.ts` は source-tag の semver 検証 → release 公開済み検証 → major tag の導出 → 更新 → Slack 通知で、annotated tag の peel はしない。`version-utils.ts` は未読。
- 失効: publish-action の README が Alpha / internal の注意書きを外したとき。

#### A6. `GITHUB_TOKEN` で動かすときの権限・event・ruleset（av:F16、syn:W2、手元 23）
- 権限: 実例はすべて job に `contents: write`（claude-code-action、setup-node、publish-action README）。token は既定の `GITHUB_TOKEN`（checkout の既定 persist-credentials で `git push` が通る）。手元 23: 両 repo とも ruleset は無く（`gh api repos/shimo4228/<repo>/rulesets` → `[]`）、workflow token の既定は `default_workflow_permissions: read`、`can_approve_pull_request_reviews: false`。tag を動かす workflow は `permissions: contents: write` を明示すれば足り、ruleset が阻むことはない。
- event（syn:W2。docs の要約、2026-11-02）: 「events triggered by the `GITHUB_TOKEN` will not create a new workflow run, with the following exceptions:」例外は (a)「`workflow_dispatch` and `repository_dispatch` events always create workflow runs」、(b) `pull_request` の `opened` / `synchronize` / `reopened`。`GITHUB_TOKEN` の workflow が PR を作る・更新すると、その event は run を「approval-required」状態で作る。`action_required` という語と github-actions[bot] への言及はページに無い。
  - 含意（docs の一般則からの読み）: workflow が `git push origin v1 --force` で動かした tag は `push: tags` の workflow を再起動しない（push は例外にない）。`GITHUB_TOKEN` で作った release は他の workflow の `release` event を起こさない（av:F16 の読みと一致）。著者が web UI で publish した release、または著者自身の token の `gh release create` は `GITHUB_TOKEN` の event でなく、`release` event で起動する。
  - av:F16 の events docs の読み: draft の作成・編集・削除は `created` / `edited` / `deleted` を起動しない。stable と pre-release の両方で起動したいなら `published` を使う（`released` と `prereleased` の組より）。
- tag を保護する ruleset: "Restrict updates"（`v*` に一致する tag は bypass 権限者のみ push 可）、"Restrict deletions"、"Block force pushes" が tag に効く（rulesets docs）。bypass は role・team・GitHub Apps。`GITHUB_TOKEN`（github-actions[bot]）は bypass actor に選べないという community の報告が複数（公式 docs は言及しない）。`v*` 全体に "Restrict updates" を掛けると workflow の `v1` 移動も止まる。保護するなら `v*.*.*` に限る（immutable releases が release tag を既に固定する）。旧 tag protection rules は 2024-08-30 に ruleset へ移行（snippet）。
- こちらとの違い: 今は ruleset が無いので阻むものは無い。ruleset を後から足すときの注意として残す。

#### A7. SHA pin 強制 policy と composite の nested `uses:`（av:F13、ad:1.5、2.1–2.3、1.9）
- URL: https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/ ／ https://unit42.paloaltonetworks.com/github-actions-supply-chain-attack/ ／ https://boostsecurityio.github.io/poutine/rules/unpinnable_action ／ https://raw.githubusercontent.com/anthropics/claude-code-action/main/action.yml。changelog・docs は要約、実例は観測。
- policy: 2025-08-15 に allowed actions policy へ "Require actions to be pinned to a full-length commit SHA" が入った（enterprise / org / repo）。「The policy will check for a full commit SHA, and any workflow that attempts to use an action that isn't pinned will fail.」docs:「all actions must be pinned to a full-length commit SHA to be used. This includes actions from your organization and actions authored by GitHub.」「Reusable workflows can still be referenced by tag.」tag（`@v1` も immutable な `@v1.0.0` も）は通らない（Semgrep blog 2026: immutable releases は今は免除でない）。同じ policy に `!` 接頭の block がある。
- composite の `uses:`: docs・changelog は書かない。観測は 3 件（pre-commit/action PR #231「composite actions also fail if their own actions are not pinned」、Zenn moshjp「呼んだ composite action が未 pin の action を使っていたため repo の workflow が止まった」、Semgrep「requires everything to be pinned all the way down」）。Semgrep は「reusable workflow 自体は tag 参照でよいが、その中の action は pin が要る」と書く。
- Anthropic 自身の `action.yml`（ad:2.2）: `uses:` は 1 つだけ（`oven-sh/setup-bun@0c5077e5… # https://github.com/oven-sh/setup-bun/releases/tag/v2.2.0`。full SHA + release URL のコメント）。`bun-version: 1.4.4` は version のみ、`apt-get install bubblewrap socat` は version 無指定。inner action は SHA で pin し、runtime の package 取得は pin しない型。
- tj-actions（Unit 42、公開 2025-03-20、更新 2025-04-02）: reviewdog の maintainer の PAT 漏洩 → `reviewdog/action-setup` の `v1` tag が fork 上の悪意 commit に付け替えられた → composite の `tj-actions/eslint-changed-files` が runtime で使用 → `tj-actions/changed-files` が侵害され、全 tag が悪意 commit に付け替えられた。「Git tag changes are not recorded in the GitHub audit log」は free tier の org・repo の場合の記述（2025-03/04 時点。その後の変更は未確認）。緩和策は full SHA の pin（transitive の pin までは明言しない）。poutine: 「if a component … is architected in a way that depends on other components, which can be compromised, pinning it does not effectively mitigate the risks.」作者向けには composite の inner action を full SHA、Docker は sha256 digest。
- こちらとの違い: `action.yml:155`（audit）と `:191`（apply）が `anthropics/claude-code-action@v1`（tag 参照）。`examples/harness-stocktake.yml` は `shimo4228/harness-stocktake-action@v1`（:42）と `actions/checkout@v5`（:39）。`README.md:67` も `@v1` で、SHA 形の利用例と版運用の説明は無い。利用側が SHA 強制 policy を有効にしていると、`@v1` の呼び出しも nested の `@v1` も落ちうる（観測による。docs は沈黙）。
- 失効: docs・changelog が composite の扱いを明記・変更したとき、利用側が lockfile へ移行したとき。

#### A8. 利用者側の優先順位と lockfile、roadmap（av:F7、F14、ad:1.3、1.4）
- URL: https://docs.github.com/en/actions/reference/security/secure-use ／ https://github.blog/changelog/2026-10-14-github-actions-workflow-lockfiles-in-public-preview/ ／ https://docs.github.com/en/actions/how-tos/secure-your-work/lock-workflow-dependencies ／ https://docs.github.com/actions/concepts/security/workflow-dependency-lockfiles ／ https://github.blog/security/supply-chain-security/whats-coming-to-our-github-actions-2026-security-roadmap/（2026-03-26 公開・03-30 更新。mk は /news-insights/product-news/ 配下の同題 URL）。公式。要約。
- secure-use: 「The best measure is to lock your workflow dependencies with a lockfile.」「This is the strongest protection available, and supersedes SHA pinning for repositories that adopt it.」SHA は「Pin references to actions to a commit SHA」。tag は信頼する作者の場合だけ、「a tag can be moved or deleted if a bad actor gains access to the repository storing the action」。Dependabot: 「Dependabot only creates alerts for vulnerable actions that use semantic versioning and will not create alerts for actions pinned to SHA values.」作者向け節（Protecting actions you've created）は dependants view と security advisories だけで、tag と release の出し方には触れない。
- lockfile（2026-10-14 public preview。GHEC、GHEC data residency、Team、Free。changelog の editor's note が同日に提供プランを更新）: `gh actions-lock` が `.github/workflows/actions.lock` を作る。workflow 単位で onboard し、Dependabot は onboard 済みの workflow の更新 PR で lock も更新する。「Require lockfile」policy も preview。lock 時に参照を commit SHA に解決し、`uses:` を解決した版へ書き換える（`v3` が `v3.1.0` になりうる）。branch または partial version（例 `v1`）が動くと `ref-moved` 警告で locked commit を保持（進めるには `--relock`）、full version tag（`v3.1.0`）が動くとエラー。force push による履歴書き換えは `--relock` で直らない。推移依存を含む（composite への言及は無い）。実行時に owner_id / repo_id を照合する。**`run:` step は範囲外**（「It doesn't control other build inputs, such as input parameters, secrets, or the runner image.」）。作者向けの指示は docs にも changelog にも無い。
- roadmap: 「On the publishing side, we're moving away from mutable references and towards immutable releases with stricter release requirements.」公開側の日付は無い（dependency locking のみ public preview 3–6 か月・GA 6 か月）。
- こちらとの違い: `v1.0.0` を動かさず `v1` だけ動かす運用は lockfile の設計と整合する。Action の `git fetch … "$REF"`（`action.yml:100`）は `run:` step で、lockfile にも SHA policy にも届かない。守れるのは (a) plugin repo の immutable releases（有効化は release を作る前）と (b) `plugin_ref` 既定値を full SHA にするか、解決 SHA の照合（`action.yml:102` は表示だけ）だけ（ad:Q2、2.4）。
- 失効: GitHub が publish 側の "stricter release requirements" を定義・実装したとき、lockfile が GA になったとき、`@v1` のような動く tag の扱いが docs に明記されたとき。

#### A9. immutable actions（GHCR の OCI package）は使えない（av:F12）
- github/roadmap #592 "Immutable Actions [GA]" は `state: closed`、`state_reason: not_planned`、`closed_at: 2025-12-11`（API）。コメント（2025-12-11）:「We are currently focusing on other features, like looking to build Actions specific features around immutable releases to enhance supply chain security. This has been removed from the roadmap for now …」actions/publish-immutable-action は archived でなく（最終 push 2025-08-08、129 stars）、README に「This action is **not ready for public use**.」GitHub 自身の checkout と setup-node は publish workflow を今も持つ。二次資料の「2026 に GA」とする vendor ブログは、roadmap の close と矛盾するので採らない（API の state_reason が強い）。移せるものは無い。
- 失効: roadmap #592 の再開、または publish-immutable-action の README から "not ready" が消えたとき。

#### A10. force を使わない経路（av:F17。実例の裏付けは弱い）
- docs は参照形として branch も許す（A1 の `@v1-beta`）。major の追従を `v1` という名の branch にして fast-forward だけで進める（`git push origin main:v1`、force 不要）と、ローカル hook に触れず、immutable releases の対象外で、branch ruleset の "Block force pushes" で進むだけを機械的に強制できる。主要な action で採用している実例は見つけていない。tag `v1` と branch `v1` を同時に作ると参照が曖昧になる。lockfile docs は branch と partial version を同じ扱い（`ref-moved`）にする。
- REST の `PATCH /repos/{owner}/{repo}/git/refs/tags/v1`（`force: true`）は publish-action の実体で、ローカルから `gh api` でも打てる。`git push --force` の文字列は避けられるが、実質は force の移動で、著者の hook の意図に沿うかは著者が決めること。

### M. GitHub Marketplace

#### M1. 掲載要件（mk:F1）
- URL: https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace ／ raw https://raw.githubusercontent.com/github/docs/main/content/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace.md。公式 doc。新旧 path は要約モデル経由で全体、src は requirements 節と主要文の抜粋（逐語の全文は得られず）。
- 内容
  - must は 3 つ: 「The action must be in a public repository.」「Each repository must contain a single action metadata file (`action.yml` or `action.yaml`) at the root.」（subfolder の metadata は許されるが自動では掲載されない）「The `name` in the action's metadata file must be unique.」
  - name の一意性: 既存の Marketplace action 名、GitHub の user・organization 名（owner が公開する場合を除く）、既存の Marketplace category 名、GitHub が機能名として予約した名前と一致しない。
  - 「Actions are published to GitHub Marketplace immediately and aren't reviewed by GitHub」。「the repository only includes the metadata file, code, and files necessary for the action」を確かめるよう書かれている（推奨文で must の列挙に無い）。
  - action.yml 側の必須 field は `name` / `description` / `runs`。`author` と `branding` は任意。
- こちらとの違い: 3 要件とも満たす。`examples/harness-stocktake.yml` は metadata のファイル名でないので数に入らない。

#### M2. workflow ファイルがあってよいか（mk:F2、ad:5.1）
- docs の要件列挙に「workflow ファイルを含まない」は無い。原文で "workflow" を含む文は transfer の節の "meaning workflows that use the affected action do not need to be updated." だけと報告された（ja 版にも禁止の記述なし）。
- 実物（2026-11-02）: anthropics/claude-code-action は `.github/workflows` に 14 ファイル（ci.yml、release.yml ほか）で、掲載名 "Claude Code Action Official"、Verified creator badge あり。VIKOIT/reversibility-engine は 7 ファイル（掲載名 "Reversibility Engine"、Latest v1.2.2）。Chris0Jeky/llm-release-gate は `ci.yml`（Latest v0.2.0）。
- 反対の主張: getsentry/action-onlyrobots PR #11（2025-07 頃、repo は archived）の PUBLISHING.md「Must NOT contain any workflow files in `.github/workflows/`」。Community discussion 24965 に 2021-02 の投稿「dummy workflow を足したら publish の checkbox が出た。理由は不明」（staff の説明なし）。検索エンジンの要約が現行 docs にその条件があると述べた例もあったが、原文の抜粋で否定された。
- こちらとの違い: `ci.yml` は掲載の妨げにならないと読める。draft release 画面が何か警告するかは観測していない（lead が release 画面で確かめる項目）。

#### M3. アカウント側（mk:F3）
- 「Publishing requires you to use two-factor authentication.」「You must accept the terms of service to publish actions in GitHub Marketplace.」"Publish" の checkbox は、repo を所有するアカウントが GitHub Marketplace Developer Agreement に同意するまで無効。同意は Release Action 画面のリンクから owner が行う（個人 account の shimo4228 なら著者本人）。
- Developer Agreement（Effective 2025-05-27、要約）: Actions を含む全 Developer Product に適用し、無料配布でも対象。GitHub は listing の掲載可否に "sole and absolute discretion" を持ち、削除できる。malware を禁じる。listing の情報は正確で最新にする（4.2）。開発者は 30 日前の書面通知で listing を取り下げられる（4.1）。
- Verified creator は partner organization 向けで、依頼先は partnerships@github.com（docs の "About badges"）。必須でなく、個人の action は対象外と読める。
- こちらとの違い: 公開操作（同意・2FA・Publish）は著者が行う前提と一致する。

#### M4. 掲載の操作: release ごとの tick、API に無い（mk:F4）
- documented: 掲載は release の作成画面（Draft a release の "Release Action" 節）の "Publish this Action to the GitHub Marketplace" を選ぶ操作。手順は action.yml を開いて出る banner から "Draft a release" → checkbox → metadata の error / warning を直し "Everything looks good!" を確認 → Primary Category → 任意で Another Category → tag の version → release title → "Publish release"。取り下げは "each published release" ごとに release を編集して checkbox を外し "Update release"（掲載の単位が release）。「Managing releases」:「You can also publish an action from a specific release in GitHub Marketplace.」toolkit:「When you release a specific version, choose the option to 'Publish this Action to the GitHub Marketplace'.」
- API / CLI に param が無い: REST の Create / Update a release の body は tag_name / target_commitish / name / body / draft / prerelease / discussion_category_name / generate_release_notes / make_latest だけ。`gh release create` の flag にも無い。よって初回の掲載は web の release 画面で行う。同じ画面で release 自体も作れる。
- 実務者の明言: buildcage/docker v3.0.3 の release notes「'Publish this Action to the GitHub Marketplace' has no field in the release API, so it has to be set by hand on every release.」getsentry の PUBLISHING.md「Creating a release via CLI or API does NOT automatically publish to GitHub Marketplace. You must manually enable marketplace publishing through the web UI after creating the release.」
- 掲載済み 3 action の観察（2026-11-02、要約モデル経由）

| action | 人が UI で作った release | bot / API で作った release | Marketplace の見え方 |
|---|---|---|---|
| claude-code-action | `v1`（人、GitHub の Latest 印）。release 画面に Marketplace link は見えず（取得は読み込みエラーを含む） | v1.0.258–v1.0.266 は github-actions が `gh release create --generate-notes --latest=false` | Latest = "v1"。`?version=v1` は "Use v1"、`?version=v1.0.265` と `v1.0.266` は "Use latest version" に fallback |
| reversibility-engine | v1.0.2（人）の release 画面に "Marketplace" link あり | v1.1.2 / v1.2.0 / v1.2.1 / v1.2.2 は github-actions。v1.2.1 と v1.2.2 の画面に link なし | `?version=v1.0.2` は "Use v1.0.2" と older-version banner。`?version=v1.1.2` と `v1.2.1` は fallback。ただし Latest 表示は v1.2.2（bot 作成） |
| guard-installed-skill-edits（immutable 有効、2026-10） | v1.0.1（人）に link あり。notes は "Marketplace publication of the reviewed v1.0.0 action. The executable source is unchanged at commit 5cbba8e." | v1.0.0 は GitHub App `botantler-1` 作成で link なし。v1.0.2 も App 作成で link なし。v1.0.3 は App `botantler-marketplace-releases` 作成で link あり、Latest | `?version=v1.0.0` と `v1.0.1` は "Use vX" と banner。`?version=v1.0.2` は fallback。Latest = v1.0.3 |

- 読み（推論）
  1. 版の選択（`?version=`）に載るのは UI で tick した release が中心。bot / API が作った release の多くは載らず fallback する。
  2. listing の "Latest" 表示は、tick していない bot の release にも進む例がある（reversibility-engine の v1.2.2）。claude-code-action では newer な bot release が `--latest=false` で、Latest は人の `v1` に留まった。Latest 表示は GitHub の Latest 印に追従すると読めるが、外から確定できない。
  3. 例外が 3 つあり、release 画面の link は目印として不完全。(a) guard の v1.0.0 は App 作成で link が無いのに `?version=v1.0.0` は解決した（初回 listing 時に既存 release を取り込んだ可能性。未説明）。(b) claude-code-action の `v1` は解決するのに link が見えなかった。(c) guard の v1.0.3 は App 作成なのに link があり、App が tick したのか人が後から編集して tick したのかは外から分からない。
  4. guard の例は、API 作成の immutable release（v1.0.0）をそのまま掲載できず、同じ commit に人が release を作り直して掲載したことを示す（notes の文面からの推定）。
- 古い staff 回答: 2020（discussion 26787、2020-03-23、引用は切れている）「Normally, when there is a new release version in the Action repo, the Action in marketplace will update to the latest version」（自動更新を示唆するが曖昧で、現行の根拠には弱い）。2019（discussion 25834）は listing が古い release を最新として示し、action.yml を足したあと UI で release を作り直して直った。tag だけでは listing に出ず release が要る（softprops/action-gh-release issue 35 も同じ読み）。
- こちらとの違い: 「初回だけ web、以後は API / `gh`」は、listing を保つ点では成り立つ。ただし (a) それらの release は Marketplace の版選択に載らないことが多い、(b) listing の README / metadata が tick 無しの release で更新されるかは不明。
- 移せる部分: claude-code-action の構成（Marketplace 用 release を動く major tag `v1` に 1 回だけ付け、以後の patch release は `--latest=false` の bot 作成）は、Marketplace の snippet を `@v1` に揃えたいときの観察例。immutable ON では tag が動かせず成立しない。文書化された推奨ではない。

#### M5. category（mk:F5）
- release 画面で Primary Category（必須）と Another Category（任意）を選ぶ（docs）。docs は選べる category を列挙せず「action を見つけてもらうのに役立つものを選ぶ」と書く。
- 2026-11-02 の Marketplace の Actions サイドバー（33 件）: Agent apps / AI Assisted / API management / Backup Utilities / Chat / Code quality / Code review / Code Scanning Ready / Code search / Container CI / Continuous integration / Dependency management / Deployment / Deployment Protection Rules / Desktop tools / Game CI / GitHub Sponsors / IDEs / Learning / Localization / Mobile / Mobile CI / Monitoring / Open Source management / Project management / Publishing / Reporting / Security / Support / Sustainability / Testing / Time tracking / Utilities。release 画面の dropdown が同じ一覧かは未確認（サイドバーは Apps の category を含む可能性）。
- 近い用途の掲載例: Harness Score（paladini）と AI Harness Scorecard（markmishaev76）は continuous-integration + code-quality。AI Harness Doctor（NieZhuZhu）は code-review + ai-assisted。claude-code-action は ai-assisted のみ。llm-release-gate は continuous-integration + code-quality。
- 掲載後に変えられるか: docs に記述なし。取り下げ手順が「release を編集して checkbox を外す」なので release の編集画面に Marketplace 節が出るのは確かだが、category も変えられるかは確認できず（推論）。Community discussion 210391（2026-10-15、Apps の listing）に「listing 画面から category を変えられない」という投稿があり、bot の定型返信のみ（Actions には触れていない）。
- こちらとの違い: 初回の release 画面で選ぶ category が実質の初期値。

#### M6. 名前 "Harness Stocktake" の衝突（mk:F6）
- 2026-11-02 時点で衝突なし。Marketplace 検索 "harness stocktake" と "stocktake" は 0 件。"harness" の 28 件に harness と stock / audit / stocktake / inventory を併せ持つ名前は無い（近い名前: Harness Score、AI Harness Scorecard、AI Harness Doctor、harness-doctor、Harness Github Actions〔publisher は harness org、SBOM / SLSA 用〕、Harness Publish）。slug `github.com/marketplace/actions/harness-stocktake` は 404（空き）、`github.com/harness-stocktake`（user / org）も 404。
- slug は `name:` から決まる（discussion 27118 の受理回答「Changing the name in the yaml will change the url in the marketplace」、2021-05-23）。SonarSource/sonarqube-scan-action PR 166（2024-12-17）は、title 変更を含む release で Marketplace の URL が変わり旧 URL が壊れたため title を戻した。旧 slug の redirect の有無は公式文書に無い。workflow の `uses:` は org + repo 名に紐づくので影響しない。docs は、repo を transfer しても listing は同じ `name` で続き、repo を削除すると listing も消えて name が空くと書く。
- 商標: docs の name 規則に brand 条項は無い。Developer Agreement 5.4(vi) は marketing 内容が誤認させないことを求める。"Harness" は CI/CD 企業名でもあり、その org の掲載は別名で共存している。
- こちらとの違い: name は初回掲載前に確定する。掲載後の改名は URL を壊す（実務者の報告）。

#### M7. action.yml の検査（mk:F7）
- description は 125 文字未満（実務者 3 件、2026-08。docs には無い）: dakshcodez/docmend PR 13（2026-08-15、131 文字で reject → 102 文字、"125-character limit"）、VIKOIT/reversibility-engine v1.0.2（折り畳み scalar が 171 文字に展開されて reject）、Chris0Jeky/llm-release-gate v0.1.2（122 文字に短縮して "satisfying GitHub Marketplace validation"）。長さは YAML をパースした文字列で数える。「125 未満」か「125 以下」かは未確認。
- 検査は release の tag に置かれた action.yml に対して働く（VIKOIT v1.0.2 の notes「This release exists so a tag carries an action.yml the Marketplace will accept.」）。main で直すだけでは足りず、直した tag が要る。VIKOIT は v1.0.0 / v1.0.1 では掲載できないと記して v1.0.2 を新しい tag として切った。
- ファイル名は `action.yml` で動く（`action.yaml` で checkbox が出なかった報告 2019–2022 と、サポートが「`action.yaml` が必要」と答えた報告が食い違う。discussion 24965）。checkbox が出ない他の原因: YAML の誤り・不正文字・過剰な indent（discussion 26787）、private repo（discussion 24965、2026-02）、Developer Agreement 未同意、GitHub 側の不具合で support が手動対応した例。
- branding: `check-square` は Metadata syntax の icon 一覧（Feather v4.28.0）に、`orange` は color 一覧にある。
- 事前確認: "Draft a release" の画面は Publish の前に metadata の error / warning を出し、問題が無いと "Everything looks good!" を出す。
- こちらとの違い: `action.yml:2` の description は 1 行の文字列で 119 文字（mk が手計算、統合役が再数して一致）。6 文字以上増やすと 125 に達する。`branding` は `check-square` / `orange`（`action.yml:4-6`）。

#### M8. 2025–2026 の変更と immutable との共存（mk:F8）
- Marketplace の掲載要件を変えた changelog / docs の記述は見つからなかった。publish ページに last-updated 表示は無い。immutable releases を Marketplace が求める記述も無く、publish ページにも immutable の how-to ページにも相手の語が出ない。
- 共存の観察は guard-installed-skill-edits-action（2026-10）の 1 例: immutable な v1.0.1 と v1.0.3 に Marketplace link がある（M4）。
- 2026-03-26 の roadmap:「Beyond consumption, we'll harden how workflows are published into the Actions ecosystem.」と「moving away from mutable references and towards immutable releases with stricter release requirements.」時期の記載なし。Marketplace と verified creator は本文に出ない。docs は「aren't reviewed by GitHub」と書き、security scan の記述は無い。
- 失効: GitHub が Releases API / `gh` に Marketplace の field を足したとき、publish ページに workflow や immutable の要件が加わったとき、roadmap の "stricter release requirements" が出荷されたとき。

#### M9. 掲載の価値（ad:Q4）
- 掲載が利用者獲得に効くことを示す一次資料も作者の運用記録も見つからなかった。claude-code-action の listing（2026-11-02）は Latest version "v1"、stars 9.8K、contributors 143、"Used by" は表示されない。Verified は「GitHub has manually verified the creator as an official partner organization」で、フッターは "is not certified by GitHub"。これらの属性は Anthropic の brand 由来で、個人 repo に移せない。個人 org が Verified を取れるかは未確認。
- 実証研究（snippet のみ）: arXiv 2407.05519（Marketplace の構成。開発者の 92.93% は Action だけを出し、42.64% の Action は release が 1 つだけ）、arXiv 2303.04084 と推定される調査（90 人。同種の Action から選ぶときに verified creator と stars の多さを好む）。「発見経路の割合」を測った研究は検索で出なかった。
- 結論に使える範囲: 掲載は審査なし・即時・可逆（checkbox を外せば取り下げ）で安い。利益の根拠は無く、選択の手がかりとして効く属性（Verified、stars）は掲載だけでは得られない。
- 失効: GitHub が掲載の閲覧数・導入数を公開したとき。

### X. 別の枠組みと段ごとの反証（ad）

#### X1. 別の枠組み（ad「別の枠組み」節、3.1–3.5）
- B1 exact tag + immutable release のみ（動く tag を出さない）: setup-uv v8.0.0（2026-03-29）、prek-action v3.0.0（snippet）。README は `@<sha> # v1.0.0` と Dependabot の例。利用者側の更新負荷は未測定。実例は CLI ツール系 2 件。
- B2 GitHub の immutable 手順の混成: `v1.0.0` は immutable release、`v1` は release 無しの軽量 tag。README は exact / SHA / lockfile を strict 用に併記。公式手順。ad は運用実例を読めていないが、av は actions/setup-node（immutable な per-version release と、release 無しの軽量 `v7`）がこの形であることを API で確認した（A3、A4。C6）。github/codeql-action も immutable な v4.39.1 と annotated `v4` を持つ（`v4` に release object が無いかは未確認）。
- B3 lockfile 前提: 利用者に `gh actions-lock` を勧め、作者は tag と branch を消さないことだけ守る。preview 中。`run:` の取得は範囲外。
- B4 専用 Action を出さず、plugin 専用 repo + workflow 雛形: mtblck/claude-marketplace、mikeguzman/agent-skills の型（README が利用者に `anthropics/claude-code-action` を直接使わせ、雛形の workflow を貼らせる。ref pin なし、tag・release なし、stars 0）。この Action には issue 追跡と PR 生成の orchestration（`scripts/stocktake.py`）があり、雛形では 1 行導入にならない。この規模の orchestration を持つ例は見つからなかった。jedwards1230/claude-plugin-actions は reusable workflow（composite でない）で、plugin の version bump 検査が中身。plugin marketplace とは別 repo に分けた例としてだけ使える。参照形は `@v0`（動く major）、`@v0.1`、`@v0.1.0`、`@main`。
- B5 plugin を Action の release に同梱する（推論。実例は未読）: runtime の `git fetch` をやめ、Action の release 時に plugin を取り込む。`uses: …@<sha>` 1 つで全体が固定され、lockfile / SHA policy の対象に入る。代償は plugin の独立 version（`plugin_ref`）を失い、plugin と Action の release が連動すること。
- 制約（ad:3.5）: Marketplace 掲載は 1 repo に metadata file 1 つ。1 repo に plugin と Action を同居させると tag の系列（Action の `v1.x` と plugin の `v0.x`）が 1 つの名前空間に入る（推論）。2 repo 分割はこの衝突を避ける自然な形。plugin と掲載 Action の両方を 1 repo から出す実例は見つからなかった。
- Anthropic の例（ad:3.4）: Action は `anthropics/claude-code-action`（Marketplace 掲載、composite）。docs の例が指す plugin marketplace（`anthropics/claude-code`、`anthropics/claude-plugins-official`）は別 repo。

#### X2. 有力案の各段への反証・条件（ad「有力案の各段への反証・条件」節）
- (1) plugin に tag `v0.1.0` + release: Action の既定 `plugin_ref: v0.1.0`（`action.yml:25-28`）は実行時に fetch され（`action.yml:100`）、解決 SHA は表示するが照合しない（`action.yml:102`）。条件は先に plugin repo の immutable releases を ON にしてから release を作ること、または既定値を full SHA にすること。`action.yml:26` の説明「Pinned so a plugin release never changes a run unannounced」は、tag が動く限り慣習であって pin ではない（C4）。
- (2) Action に release `v1.0.0` + major tag `v1`: 動く `v1` は公式 doc と Anthropic の実例が支持する。反証側は setup-uv / prek-action、secure-use の優先順位（lockfile > SHA > tag）、SHA 強制 policy。条件は A2 の形（release は `v1.0.0` だけ）にするか、Anthropic の形にするかを選ぶこと。immutable ON なら前者で、release 作成後に `v1` へ release を付けない。`README.md:19`・`:67`、`examples/harness-stocktake.yml:39`・`:42` は `@v1` と `actions/checkout@v5` で SHA 形の例が無い。inner の `anthropics/claude-code-action@v1`（`action.yml:155`、`:191`）は tj-actions の経路と同じ型で、Anthropic の `action.yml` は inner を SHA で pin している。2 回目以降の `v1` の移動は force push で、CI で行う。
- (3) Marketplace 掲載: 発見経路としての価値の根拠なし。可逆で安い。Verified は移せない。workflow ファイルは障害に見えない。
- (4) smoke を `@v1` に切り替えて 1 回走らせる: 反証は見つからなかった。smoke の結果は `@v1` の経路だけを確かめる。SHA 形で参照する利用者（SHA 強制 policy 下）の経路は別。
- (5) plugin を directory に提出し main を追跡させる: 提出は form。外部 entry は `sha` を持ち bump workflow が存在する（P7）。推論として、Action の `plugin_ref`（tag）と directory の sha が別々に進むと配信経路が 2 本になり、同じ版を配らない時間が出る。`ref: v1.5.5` + sha の entry が実在するので、release tag を指す形は directory の前例がある。
- Scorecard（ad:1.10。fetch の返答 1 文のみで未確認）: GitHub Actions の `uses:` は tag が published immutable release に裏づけられていれば pin 扱い、という返答。正しければ immutable な `v1.0.0` は利用者側の Scorecard で pin 扱い、動く `v1` は pin 扱いにならない。composite の `action.yml` を走査するかも未確認。`ci.yml` は tag 参照と `bash <(curl …)` を使うので（`.github/workflows/ci.yml:15,18,37,40,50,52`）、掲載の可否と別に Pinned-Dependencies には当たる。

### S. 節をまたぐ順序制約（統合の読み）

出典の事実から導いた制約で、新しい外部事実は含まない。採否は lead が決める。

- S1 作る順: plugin の `v0.1.0` が先。README の `@v1` と既定 `plugin_ref: v0.1.0` は tag を作るまで解決できない（手元 2）。続いて Action の `v1.0.0` と `v1`、続いて smoke を `@v1` に切り替える。
- S2 immutable の有効化は publish の前: 遡らない（A3、手元 5）。plugin の `v0.1.0` を固くするなら plugin repo、Action の `v1.0.0` を固くするなら Action repo で、それぞれ最初の release の publish より前に有効化する。
- S3 tag が指す commit に入る文言: その commit が Action の fetch 先であり、tag 追跡なら directory の scan 対象になる。immutable ON なら後から直せず新しい tag になる（A3）。plugin 側は `CHANGELOG.md:3` の "unreleased"、`README.md:73` の "(pre-release)"、`CITATION.cff` の `date-released` 欠落（手元 10、25）、`README.md:54` と `:13` / `:73`（C2、C3）。Action 側は nested `uses:` の pin 形式（A7）、description の長さ（M7）、README の `Differences from the plan` / `Not measured yet` / `plugin_token` / :111 の文言（手元 15、C1、C14）。
- S4 `v1` を release 名にしない: immutable ON では publish で tag 名が焼き付く（A3、A4）。`v1` の初回作成は force 不要の通常 push で足りる。2 回目以降の移動は workflow（A4、A6）。著者のローカル hook は runner 上の操作に及ばない（手元 6）。
- S5 Marketplace の tick は web UI のみ（M4）: immutable ON なら draft → web UI で tick と category を決めて publish する。draft 画面の metadata check（M7）を publish の前に見る。immutable の publish は tag 名を焼く（A3）ので、`v1.0.0` を検査に通らない action.yml のまま publish すると、同じ名前で直せず新しい tag（`v1.0.1`）になる。`gh release create --draft` で draft を作り、tick・category・Publish を著者が web で行う形は、手元 20 の分担（`gh release create` は Claude、Marketplace の publish checkbox は著者）と一致する。
- S6 release を起点とする workflow: 人の公開（web UI）や著者の token の `gh release create` は `release` event を起動する。`GITHUB_TOKEN` が作る release と push した tag は他の workflow を起動しない（A6）。draft の作成・編集・削除は `created` / `edited` / `deleted` を起動しない（A6）。
- S7 Zenodo: toggle を有効化してから release を publish する（P10）。tag の push だけでは release にならない。immutable releases と Zenodo の取り込みの相互作用は notes に記述が無い。
- S8 directory 提出: 追跡先（branch か tag）は Source step で選び、提出後に repo と folder は変えられない（P5）。tag 追跡の更新は追跡先の書き換えと Publish で、branch 追跡は main の各 commit が新しい版になり既定では 1 つずつ Publish が要る（P5）。`version` を上げる規律は GitHub marketplace 経路と directory 経路の両方に効く（P1、P5）。提出前に追跡 file 数と大きさを確かめる（P6）。
- S9 時刻の制約: 著者の掲載 routine の次回は 2026-11-02 10:10 JST（plugin repo の README を外部の awesome-list に出す PR。手元 27）。その PR は plugin repo を指すので、README の記述（C2、C3）が外部の読者に読まれる。

## Contradictions

- C1 Action `README.md:111`「Pull requests opened with the workflow's `GITHUB_TOKEN` don't trigger other workflows.」 vs 手元 24 vs GitHub docs（syn:W2）
  - 手元 24（2026-11-01T21:04Z、非公開の smoke repo）: apply run が `github-actions[bot]`（`GITHUB_TOKEN`）として PR を開き、その後の push で `pull_request` run が作られ、actor / triggering_actor とも `github-actions[bot]`、conclusion `action_required`（承認待ち、job 0）で止まった。
  - docs（2026-11-02、要約）は `GITHUB_TOKEN` の event は run を作らないとしたうえで、`pull_request` の `opened` / `synchronize` / `reopened` を例外に挙げ、run は「approval-required」状態になると書く。観測と docs が一致し、README の 1 文が不正確。
  - av:F16 の言い換え（例外は `workflow_dispatch` と `repository_dispatch` だけ）は `pull_request` の例外を落としている。
  - 限界: docs の要約は `action_required` の語と github-actions[bot] に触れない。観測は非公開 repo の 1 件で、event は `pull_request` の更新側。tag の push など push event は例外に無いので、A6 の含意は変わらない。
- C2 plugin `README.md:54`「Sends nothing anywhere beyond your own Claude Code session. There is no telemetry and no network fetch.」 vs 実物（手元 11、12）
  - `skills/skill-health/scripts/url_liveness.py:170-180` は URL ごとに GET を 1 回送る（本文は読まず、`is_internal_host` で内部 host を除く）。呼び出し元は `skills/skill-stocktake/SKILL.md:107-108`（`uv run --frozen --project … url_liveness --urls-from -`）。`uv run --frozen` は初回に PyPI から固定版の依存を取る。skill-health の同梱は commit 480c20f で、README の該当節より後。README の `:53` は `uv run` を使うと書いている。
  - 実物（code）が強い。同じ folder に HOME を読む code（手元 12）と通信する code がそろう点は、著者の提出手順 skill（非公開、as-of 2026-10-13）が credential の Policy hold と記録している。pv:F7 は launcher と規模の規則だけを確かめており、この hold の規則は現行 doc では未確認。
- C3 plugin `README.md:13`「You need Claude Code 2.1.275 or later」、`:73`「Requirements: Claude Code 2.1.275+」 vs install の 1 行（`README.md:5`、`:18`）
  - CLI reference（syn:W3、2026-11-02）の `--marketplace <source>` の行は「Requires Claude Code v2.1.292 or later」。2.1.275 は session 内の `/plugin install … --marketplace` の最小版（pv:F2。未再確認）。2.1.275–2.1.291 では README の 1 行 install は動かない（推論。docs の記述からの読み）。
  - 手元 21 の install 検証は 2.1.316 での実行で、下限は試していない。公式 doc が強い。2 段の install は全版で動く（pv:F2）。
- C4 `action.yml:26` の description「Pinned so a plugin release never changes a run unannounced」 vs 実物（ad:Local evidence、A3）
  - 既定 `plugin_ref: v0.1.0`（`:28`）は git tag の名前で、plugin repo の immutable releases が先に有効でなければ tag は動かせる（手元 5: 現在は無効）。`:102` は解決 SHA を表示するだけで、期待値と照合しない。tag が動く限り pin でなく慣習。
- C5 lead の手元 2 の `action.yml:27-30` vs 実物の `action.yml:25-28`
  - 統合役が 2026-11-02 に Read した `action.yml` では `plugin_ref` が `:25`、description が `:26`、既定 `"v0.1.0"` が `:28`。ad の `:25-28` が一致し、`:27-30` は 2 行ずれる。
- C6 ad:B2「この形で運用している公開 repo の実例は読めていない」 vs av:F10
  - av は actions/setup-node（immutable な v7.1.0 / v7.0.0 と、release 無しの軽量 `v7`）を API で確認している。API の読みが強い。B2 には GitHub 自身の運用実例がある。github/codeql-action（immutable な v4.39.1 と annotated `v4`）は `v4` に release object が無いかが未確認で、実例に数えるには足りない。haya14busa の `v1` が v1.5.1 に追従しているかも未確認。
- C7 著者の提出手順 skill（非公開、as-of 2026-10-13）の記述 vs 現行 doc（pv:F8、2026-11-02）
  - 「更新は追跡している branch への merge で届く」は検出までは一致する。利用者に届くには Publish が要り、既定は reviewer が 1 版ずつ公開する（P5）。
  - 「"Publish new versions automatically" は 2 版目以降に効く」は、Anthropic が承認時に publish の設定を変える場合の話で、既定の設定では auto-publish は効かない（P5）。
  - 「webhook が無ければ約 6 時間ごとの確認」は読んだ 5 ページに間隔の記述が無い（docs は「on a schedule」のみ）。portal の画面に書かれている可能性は残る。Anthropic 側 marketplace repo の bump は毎日 1 回の cron（P7）で、portal の確認とは別機構かもしれない。
  - 「icon / documentationUrl / supportUrl / author / keywords は最初の提出だけ」は部分的に一致。docs は icon / documentationUrl / supportUrl / privacyPolicyUrl / termsOfServiceUrl を提出時に読むと書き、掲載後に追従するのは name と short description と書く。「最初の提出のときだけ」とは明記されず、author / keywords への言及も無い。矛盾はしない。
  - 一致: version を release のたびに上げる（「installed copies use it to tell that an update exists」）、Source step の項目。docs が強い（全文を 2026-11-02 に読んだ）。
- C8 directory の 2 つの像: pv の portal（tracked branch or tag → scan → reviewer が publish）と ad の marketplace repo（外部 entry は sha pin。bump が進める）
  - syn:W1、W4 で bump は毎日 07:23 UTC、HEAD 追従と `releases-only`（最新 published release の tag commit）の 2 型と分かった。portal の追跡先がどちらに対応するかは、どの文書にも無い。矛盾でなく接続が未文書。
  - pv:F5 と F6 の文言の差もある。after-publishing の「push to the branch or tag」は付け替えか tag 名の切替かを区別せず、submit の「changing the tag」の節が具体的で、そちらを採った。
- C9 Marketplace の workflow ファイル: getsentry の PUBLISHING.md と 2021 年の逸話 vs GitHub docs と実物（M2）
  - docs に禁止の記述は無く、掲載済みの 3 action が workflow を持つ。docs と実物が強い。draft 画面の警告は未観測。
- C10 SHA 強制 policy と composite の nested `uses:`: docs 沈黙 vs 実務者の観測 3 件（A7）
  - av は観測 3 件を根拠に「検査される」と読み、ad は「及ぶか未確認」と置く。事実は同じで枠組みの差。enforcement は利用側の設定次第なので、どちらの読みでも nested `@v1` は利用側の policy で落ちうるリスクとして残る。
- C11 Scorecard の 1 文（ad:1.10。immutable release 裏づけの tag は pin 扱い） vs GitHub の SHA 強制 policy（immutable な `@v1.0.0` も通らない。av:F13）
  - 別の機構。Scorecard の文は fetch の返答 1 文のみで最も弱い。混同しない。
- C12 Marketplace の観察同士（M4）
  - reversibility-engine では tick 無しの bot release に Latest が進み、claude-code-action では `--latest=false` で Latest が人の `v1` に留まる。guard の v1.0.0 は App 作成で link が無いのに `?version=v1.0.0` が解決する。mk は「tick が版選択の条件」を推論と置いた。docs の水準で確かなのは「掲載は release の作成画面の tick で、API に field が無い」まで。
- C13 `claude plugin marketplace add --help` に ref の option が無い（手元 8） vs docs（P2）
  - ref は `<source>` 文字列の一部（`#ref` / `@ref`）で、help に無いことは未対応の証拠にならない。docs が強い。
- C14 Action README の他の古い記述（手元 15、26）
  - `README.md:113-115`「Cost and time: Not measured yet.」は、audit 約 2 分・apply 約 1.5 分の smoke の実測（手元 26）より古い。`README.md:127` の `plugin_token`「Only needed while that repository is private.」は、plugin repo が 2026-11-01 から public である現状より古い。`README.md:150` の見出し「Differences from the plan」は、外部の読者に「the plan」が指すものが無い。
- C15 `~/.claude/scheduled-tasks/README.md:17` は著者の掲載 routine を「一時停止」と書くが、scheduled task の実物は enabled で、次回は 2026-11-02 10:10 JST（手元 17）。実物に従う。
- C16 ほか
  - av の「actions/publish-action の最終 push」は main の最終 commit が 2026-09-29（Dependabot）で、lead の材料の pushed 2026-10-31 との差（branch や tag の push か）は未確認。
  - 手元 2 のとおり、README の `@v1` と `plugin_ref: v0.1.0` は tag が無い間は解決できない。pre-release の状態としての食い違いで、S1 の順で解ける。

## Local evidence

lead の実行・確認（2026-11-02 07:50–08:35 JST）。統合役が直接読んで確かめたものは明記する。

**版と ref**
1. tag・release は両 repo とも無い（`git ls-remote --tags https://github.com/shimo4228/harness-stocktake.git` と `…/harness-stocktake-action.git` が空、`gh release list` も空）。
2. Action の既定が無い ref を指す: `action.yml:25-28`（lead 記載は `:27-30`。C5）の `plugin_ref` 既定 `v0.1.0`、`README.md:67` と `examples/harness-stocktake.yml` の `uses: shimo4228/harness-stocktake-action@v1`。README どおりに置くと `uses:` の解決で落ち、`@main` にしても plugin の fetch（`v0.1.0` が無い）で落ちる。
3. 非公開の smoke repo の workflow は `@main` + `plugin_ref: main`。README の経路（`@v1`、`plugin_ref` 既定）は一度も走っていない。実行時間は audit 約 2 分（2 回の run）、apply 約 1.5 分（いずれも 2026-11-01）。
4. claude-code-action の最新は v1.0.266（2026-10-31）。その `action.yml` の `plugin_marketplaces` は「Newline-separated list of Claude Code plugin marketplace Git URLs」。Action の `README.md:152` は「`owner/repo` と `#ref` pin はどちらも拒否された」と記録 → 自前の fetch step（`action.yml:85-103`、"Fetch harness-stocktake at the pinned ref"）は残る。
5. immutable releases は両 repo とも無効（`GET /repos/shimo4228/<repo>/immutable-releases` → `{"enabled":false,"enforced_by_owner":false}`）。個人 account なので org policy は無い。
6. 著者のローカル hook は `git push` の `-f` / `--force` を止める（`~/.claude/hooks/validate-bash.sh:33-34`）。
7. `gh` の token scope に `repo` と `workflow` がある。
8. Claude Code 2.1.316。`claude plugin marketplace add --help` に ref の option は無い（`--claudeai` / `--json` / `--scope` / `--sparse`）。

**plugin repo（公開、main 971f0e7）**
9. `claude plugin validate --strict` は通る（"These checks found nothing to report"。safety scan と policy review は対象外と表示）。
10. 版の表記: `.claude-plugin/plugin.json` の `"version": "0.1.0"`、`CITATION.cff` の `version: "0.1.0"`、`CHANGELOG.md:3` "0.1.0 — unreleased"、`README.md:73` "harness-stocktake 0.1.0 (pre-release)"（統合役が Read して確認）。
11. `README.md:54` と実物の食い違い（C2）。`skills/skill-health/scripts/url_liveness.py:170-180`、呼び出し元 `skills/skill-stocktake/SKILL.md:107-108`。context-sync は URL を集めるだけで取得しない（`context_checks.py:774-775`）。
12. plugin の code が HOME を読む: `skills/skill-stocktake/scripts/usage_stats.py:56`、`skills/agent-stocktake/scripts/agent_evidence.py:114-115`、`skills/skill-health/scripts/scan_refs.py:306,635`。同じ folder に通信する code（`url_liveness.py`）がある。著者の提出手順 skill（非公開）の §4 は、「読む側」と「送る側」が folder 内にそろうと credential の Policy hold になると記録している。
13. plugin の README は Action に触れない（`harness-stocktake-action` の語が無い）。`README.md:103-105` の Scheduling は cron / scheduled task / CI からの `claude -p … --unattended` だけを書く。
14. plugin folder に配布用でないもの: `scripts/sync-from-local.sh`（開発用の同期 script、HOME を読む）、`bench/`、`examples/`（sample harness と sample report。「入れずに試す」用に同梱する設計）。
   - 統合役が `README.md:1-120` を読んで確認した行: `:5` と `:18` が 1 行 install、`:13` と `:73` が "2.1.275"、`:54` が "no network fetch"、`:53` が `uv run` の記述。

**Action repo（公開、main c72a3c9、CI 緑）**
15. `README.md:150` の見出し "## Differences from the plan"（中身は `plugin_marketplaces` の制約、`issues: edited` の trigger、PR run は summary だけ、apply run の扱い）、`README.md:113-115` "Cost and time: Not measured yet"、`README.md:127` `plugin_token` "Only needed while that repository is private."
16. `.github/workflows/ci.yml`（actionlint、`action.yml` の shellcheck、ruff、unittest 3.10 / 3.12）がある。`action.yml:1` の `name: "Harness Stocktake"`、`:4-6` の `branding: check-square / orange`、`:2` の description は 119 文字。
   - 統合役が `action.yml:1-215` と `README.md:56-155` を読んで確認した行: `action.yml:25-28`（`plugin_ref`）、`:85-103`（plugin の fetch。fetch は `:100`、checkout は `:101`、解決 SHA の表示は `:102`）、`:155` と `:191`（`anthropics/claude-code-action@v1`）、`:158`（`plugin_marketplaces: ${{ steps.plugin.outputs.dir }}`）、`:159`（`plugins: "harness-stocktake@harness-stocktake"`）。`README.md:67`、`:107`、`:111`、`:113-115`、`:125`、`:127`、`:150`、`:152`。

**周辺**
17. 著者の掲載 routine（scheduled task）は有効で、次回は 2026-11-02 10:10 JST。著者の掲載 queue（非公開）は H1 が 2026-11-02（pending）、H5 が 11-06、H6 は manual（11-15）、H7 / H8 は hold。いずれも plugin repo を指す。`~/.claude/scheduled-tasks/README.md:17` は「一時停止」と書く（実物と食い違い。C15）。
18. Anthropic plugin directory への harness-stocktake の提出記録は無い（著者の掲載 queue〔非公開〕に該当行なし。著者の提出手順 skill〔非公開〕は提出時に queue へ行を足すと定める）。
19. 著者の提出手順 skill（非公開、as-of 2026-10-13）: Source step で Repository・Plugin path・Branch or tag を入れる。更新は追跡している branch への merge で届き、version を上げ CHANGELOG を書く。webhook が無ければ約 6 時間ごとの確認。"Publish new versions automatically" は 2 版目以降に効く。icon / documentationUrl / supportUrl / author / keywords は最初の提出だけ読まれる（`plugin.json` には全部ある）。→ C7。
20. campaign plan（`~/.claude/docs/plans/enumerated-petting-beaver.md`）Stage 2 #7: `gh release create` は Claude、Marketplace の publish checkbox は著者。Stage 4 #1: directory 提出は「Stage 1 完了直後（審査期間は非公開なので早く）」。

**plugin の install（GitHub から。lead が 2026-11-02 08:05 JST に実行）**
21. README の 1 行 `claude plugin install harness-stocktake --marketplace shimo4228/harness-stocktake` を一時 `CLAUDE_CONFIG_DIR` で実行 → `{"outcome":"ok","plugin":"harness-stocktake@harness-stocktake"}`、`claude plugin list` で Version 0.1.0・enabled。Stage 1 の report（`~/.claude/docs/plans/research/2026-11-01-stage1-plugin.md`）では GitHub からの install は未検証だった。
22. install の記録（`plugins/installed_plugins.json`）: `"version": "0.1.0"`、`"gitCommitSha": "971f0e7…"`（main の HEAD）。cache は版ごとの dir `plugins/cache/harness-stocktake/harness-stocktake/0.1.0/`。marketplace の source は `{"source":"github","repo":"shimo4228/harness-stocktake"}` で、tag は関わらない（default branch の HEAD から入る）。

**追加（08:20–08:35 JST）**
23. 両 repo とも ruleset は無い（`gh api repos/shimo4228/<repo>/rulesets` → `[]`）。workflow token の既定は `default_workflow_permissions: read`、`can_approve_pull_request_reviews: false`。
24. 非公開の smoke repo で、Action の apply run が `github-actions[bot]`（`GITHUB_TOKEN`）として PR を開き、その後の push で `pull_request` run が作られ、actor / triggering_actor とも `github-actions[bot]`、conclusion `action_required`（承認待ち、job 0）で止まった（2026-11-01T21:04Z）。Action の `README.md:111` は "Pull requests opened with the workflow's `GITHUB_TOKEN` don't trigger other workflows." と書く。観測は「run は作られ、承認待ちで止まる」。→ C1。
25. plugin の `CITATION.cff` は `version: "0.1.0"` を持ち、`date-released` は無い。`CHANGELOG.md` の 0.1.0 節は 6 項目で、見出しは "0.1.0 — unreleased"。
26. Action の `README.md:113-115` "Cost and time: **Not measured yet.**"。smoke の実測は audit 約 2 分、apply 約 1.5 分（sample の harness、2026-11-01）。
27. 時刻: 著者の掲載 routine の次回は 2026-11-02 10:10 JST（plugin repo の README を外部の awesome-list に出す PR）。

**notes が直接読んだ local ファイル（lead の材料でないもの）**
- pv: plugin repo の `.claude-plugin/plugin.json`（`version: "0.1.0"`、`icon: ./.claude-plugin/icon.png`、`documentationUrl`、`supportUrl`、`license: MIT`）、`.claude-plugin/marketplace.json`（plugin 1 つ、`source: "./"`、version 欄なし）、`hooks/hooks.json` と `.mcp.json` が無いこと、`uv run` 等の出現 7 file。Action の `action.yml`（`plugin_ref` 既定 `v0.1.0`、`git fetch -q --depth 1 origin "$REF"` → `checkout FETCH_HEAD`）。
- mk: `action.yml` の field（`name`、`description`、`author`、`branding`、`runs.using: composite`）。repo 内の YAML は `action.yml`、`examples/harness-stocktake.yml`、`.github/workflows/ci.yml` のみで、`LICENSE` と `README.md` が root にある。
- ad: `README.md:19`（例の workflow を `…/main/examples/harness-stocktake.yml` から curl）、`README.md:40-44`（例の permissions は `contents: write`・`issues: write`・`pull-requests: write`・`id-token: write`。動く tag が付け替えられると、利用者の job でこれらの権限と利用者自身の `claude_code_oauth_token` / `anthropic_api_key` を持って走る）、`README.md:107`（「The Action's author never receives a token, a report, or usage data, and the Action has no telemetry.」は利用者が実行する ref の code についての記述で、`@v1` では ref が動く）、`.github/workflows/ci.yml:8-9`（`permissions: contents: read`）と `:15,18,37,40,50,52`。

## Still unknown

lead の gap check で残ったもの
1. Marketplace の category を publish 後に変えられるか。docs は無言で、Apps 側に「listing 画面から変えられない」の未回答の投稿（discussion 210391）がある。確かめ方: 初回掲載のあと release の編集画面で Primary Category が編集可能かを見る。なければ新しい tick 付き release で選び直せるかを試す。
2. tick なしの release（`gh release create`）で Marketplace の README / description / branding が更新されるか。観察は、Latest 表示だけは進む例（reversibility-engine）と、docs だけの release を link 付きで切って listing の導入文を直したらしい例（guard v1.0.3。推定）。確かめ方: 初回掲載のあと README を変え、`gh release create v0.1.1` を作り、Marketplace page と `?version=v0.1.1` を見る。
3. Dependabot が root の `action.yml` の nested `uses:` を更新するか。docs は `directory: "/"` で `.github/workflows` だけを記し、zizmor の discussion は composite の `action.yml` を黙ってスキップすると報告している（未検証）。テスト repo で確かめる。
4. directory の確認間隔。docs は「on a schedule」としか書かない。著者の skill の「約 6 時間」は docs に無い（portal の画面の文言かもしれない）。Anthropic 側の marketplace repo の bump は毎日 07:23 UTC（P7）で、portal の確認と同じ機構かは不明。決着する手: portal の Settings の「Updates」画面を見る、または directory@anthropic.com に聞く。
5. publish 済みの immutable release に後から Marketplace の tick を付けられるか（snippet 止まり）。guard は人が同じ commit に release を作り直したと読めるが推定。draft → web UI で tick して publish する経路ならどちらでも通る。

notes が挙げた他の不明点
6. tag を追跡させたとき、同名 tag の force-move を directory が拾うか。docs は追跡先の欄の書き換えだけを書く。
7. `claude plugin install harness-stocktake --marketplace shimo4228/harness-stocktake#v0.1.0` の実際の挙動（docs は「same forms」と書くだけ）。tag を push した後に `claude plugin marketplace add shimo4228/harness-stocktake#v0.1.0` を実行し、`claude plugin marketplace list --json` の `ref` を見れば確かめられる。
8. directory 経由の `@synced` の copy が、更新の有無を何で比べるか（`plugin.json` の version か、directory が記録した版か）。
9. Anthropic が publish の設定を「reviewer が最初の版だけ公開」へ変えるか。承認時に決まるので提出前には分からない。
10. portal の「Tracked branch or tag」が、anthropics/claude-plugins-official の bump（HEAD 追従か `releases-only` か）にどう対応するか。`releases-only` の entry を誰がどう決めるか。tag を値にもつ `ref` の bump での扱い。marketplace.json の先頭 10 万字より後（約 9 万字）に、`ref` だけ・どちらも無い、の形が無いか。
11. claude-code-action の PR #1497（`#ref`）が merge される時期。3.5 か月 review 0 件で予測の根拠は無い。
12. Claude Code 2.1.316 で「update が already at latest と言う」系の不具合が再現するか（未検証）。
13. plugin repo の git 追跡 file 数と大きさが directory の閾値（512 file、256 KiB、archive 50 MiB）に収まるか（`git ls-files | wc -l` で確認できる）。
14. GitHub が「stricter release requirements」（A8）で major tag の移動を制限するか、いつか。日付なし。監視先は github.blog/changelog の Actions publish 関連の項目と、lockfile の GA（roadmap は public preview の約 6 か月後と記す）。
15. `GITHUB_TOKEN` を ruleset の bypass actor にできないことの一次資料（community 報告のみ）。今は ruleset が無いので影響しない（手元 23）。
16. composite の nested `uses:` が SHA pin policy の検査対象であることの docs / changelog の明記（観測 3 件のみ）。
17. immutable release の tag を force push したときの正確なエラー文言。release の再作成側の "tag_name was used by an immutable release" と、同名 tag 作成の GH013 は報告あり。
18. environment の required reviewers が Free の public repo で使えるか（docs は "Users with GitHub Free plans can only configure environments for public repositories" まで）。
19. publish-action の `version-utils.ts`（major の導出規則。`v1.0.0-rc.1` のような pre-release 表記の扱い）、nowactions/update-majorver と Actions-R-Us/actions-tagger の実装（force push の有無、action の形）、haya14busa の `v1` が v1.5.1 に追従しているか。
20. immutable ON で `v1.0.0` だけを release にしたとき、Marketplace の "Latest version" と install snippet が `v1.0.0` を指すか（README の `@v1` とずれる可能性）。GitHub Releases の "Latest" の決まり方の docs は未読。
21. Marketplace 掲載が 2026 年の発見経路として効くか、個人 org が Verified creator を取れるか。1 repo で plugin と掲載 composite Action の両方を出している実例。
22. OpenSSF Scorecard が (a) immutable release に裏づけられた tag を pin 扱いにするか、(b) composite の `action.yml` を走査するか（ソースでの確認が要る）。lockfile が `@v1` のような動く tag を ref として受けるか（docs の例は exact tag）。
23. 改名後に旧 slug が redirect されるか（公式文書なし、SonarSource の報告は「壊れた」）。description の上限が「125 未満」か「125 以下」か（119 文字なら両方で通る）。release 画面の category の dropdown がサイドバーの 33 件と同じか。
24. guard の App 作成 release（v1.0.3）に Marketplace link がある理由と、v1.0.0 が `?version=` で解決した理由。API 経路が実在するなら M4 の読みが変わる。mk の `?version=` と release 画面の読みは要約モデル経由で、著者がブラウザで確認すると確度が上がる。
25. 2026 年の action 乗っ取り事件（tj-actions 以外）と、tj-actions 後の audit log 仕様の変更。issue #664（local path 対応）の最終状態。prek-action v3.0.0 の本文（snippet のみ）。
26. Zenodo が有効化より前の release をどう扱うか、tag だけの扱い。immutable releases と Zenodo の取り込みの相互作用は notes に記述が無い（統合で気づいた欠け）。
27. `bump-plugin-shas.yml` が呼ぶ composite action の中身（ref の解決、`version` の扱い）。syn:W1 は workflow ファイルだけを読んだ。

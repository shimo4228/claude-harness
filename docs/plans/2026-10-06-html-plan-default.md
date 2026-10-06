kind: internal
# plan の既定経路を plan mode から html-plan へ替えるとき、変更が要る箇所はどこか（as-of 2026-10-06、CLI 2.1.289 系の手元 file を Read）

前提（著者の決定、覆さない）: plan mode は消さず既定から外す / plan は `html-plan@claude-community` で `docs/plans/<slug>.html` に書く / 散文は日本語で、skill の STE 規則は rule 側で上書き、plugin 本体は編集しない / `pack.mjs --artifact` → Artifact tool で private 公開、承認は Respond 貼り戻し 1 回 / 置き換える対象は research-gate PROTOCOL 手順 5 の「Mermaid 図で示す」。
引き継ぎメモ（`~/MyAI_Lab/.handoff-html-plan-default.md`）の file:line は全件 Read し直した。ずれは各項に書く。pack.mjs は `skills/html-plan/runtime/pack.mjs` にある（引き継ぎは skills/html-plan/ 直下と書いたが 1 階層下）。

## 再現

「plan mode では Write が plan ファイル以外を拒否する」は著者の 2026-10-06 実測（再実行していない）。この report が調べたのは「どこを変えるか」で、挙動の再現ではない。実機が要るものは「Still unknown」に測り方を書いた。

## 原因（変更が要る箇所。file:line と引用）

### 1. hooks/research-gate.sh — 変更要（本体）

| 論点 | 現状（再確認済み） | ずれ | 変更と選択肢 |
|---|---|---|---|
| plan ファイルの判定 | `:131-133` `single_md() { [[ "$1" == *.md && "$1" != */* && -n "${1%.md}" ]]; }`、`is_plan_file` `:135-143` が `*/docs/plans/*` と `$HOME/.claude/plans/*` | 一致 | `.html` を足す。`*.packed.html` / `*.artifact.html` を除く（pack の副産物を gate しない・unguarded に数えない）。`research/` 配下は `single_md` が入れ子を外すので対象外のまま |
| unguarded 計測 | `:255-263` が `is_plan_file` で `unguarded` を記録 | 一致 | 上の変更で html も数える。packed/artifact を除外しないと pack のたびに unguarded が増える |
| report 置き場 | `is_report` `:99-104` が `"${1%/*}" == "$2"/docs/plans/research` かつ `*.md`、`resolve3` `:81-83` が `${CLAUDE_PROJECT_DIR:-${CWD}}` 起点 | 一致 | report は md のまま（html 化しない）。cwd 起点の制約はそのまま残る — harness 外の repo の plan は、その repo の root で session を開く運用が前提 |
| PLAN_ASK | `:47` `プラン(して(?!い)\|し直(?!してい)\|を(作\|書\|立\|練\|直))\|計画(...)\|設計(...)\|\bplan (this\|it\|out)\b\|\bmake a plan\b\|\bwrite (a\|the) plan\b\|\bre-?plan\b` | 一致 | 下の 5.1 参照: `/html-plan ...` は**合わない**（コード読み）。`^/(html-plan:)?html-plan\b` 相当を足す |
| 依頼の終了 | ExitPlanMode `:236-241` が PLANNING を消す。非 plan プロンプトでの終了 `:206-209` `elif [[ "$MODE" != plan && -e "$PLANNING" && ( -e "$READY" \|\| -e "$SKIP" ) ]]` | 一致 | plan mode を使わないと `:236` は鳴らない。Respond 貼り戻しは `:206` の分岐（調査済みなら次のプロンプトで閉じる）に当たる。**調査前に放置した依頼は閉じない**（`:206` の条件が READY/SKIP 必須、bats `:347-351`）。選択肢 (a) 現状のまま（放置は著者の次の plan 依頼の `:202` で戻る）/ (b) plan html の初回 Write の pass 分岐（`:273-277`）で PLANNING を外す |
| PROTOCOL 手順 5 | `:176` `5. plan は report にリンクし、構造や流れは Mermaid 図で示す` | 一致 | 置換先: 「plan は skill: `html-plan` で `docs/plans/<slug>.html` に書き、report にリンクする。構造は claim tree の exhibit（doc-flow / doc-seq / doc-machine / doc-calls）で示す」。PROTOCOL の冒頭 `:171`「（plan mode、または plan を頼むプロンプト）」は据え置き可 |
| 先頭コメント | `:2-4`, `:8`, `:16-17` に plan mode・`docs/plans/<name>.md` の記述 | 一致 | `.html` を足す。`:4` の「docs/plans/research-plan-mode.md」参照は残る |
| PreToolUse の mode 依存 | `:255` `if [[ "$MODE" != plan && ! -e "$PLANNING" ]]` | 一致 | PLAN_ASK が html-plan 起動を拾えば PLANNING が立ち、gate は効く。拾えなければ html の Write は unguarded 計測だけで通る — **調査なしで plan が書ける穴**になる |
| ADR-0086 の窓 | `docs/adr/0086-research-gate-before-plan.md:123-124` 「窓の間は差し込む文面・plan を頼む言い方と skip の正規表現・plan ファイルの path の集合を変えない」。窓は 2026-10-04 から 30 日 | 引き継ぎの `:123-124` は一致 | PLAN_ASK・PROTOCOL・path 集合の 3 つとも変える。窓の切り直しを ADR に注記（2026-10-06 から再計測か、旧窓の打ち切りか） |

### 2. tests/research-gate.bats — 変更要

- `:63-67` 「plan mode: writing the plan file without a report is blocked」の隣に html 版（`write_in plan "$REPO/docs/plans/zesty-plan.html"` が block）。
- `:77-80` 「outside plan mode the plan directory is not gated」の隣に、`*.packed.html` / `*.artifact.html` が plan mode でも block されない（除外）ケース。
- `:146-149`（auto の plan 依頼で protocol と gate）と `:151-157`（言い方の列挙、`for p in ...` に `/html-plan <題>` を足せる）の隣に `/html-plan` 起動。
- `:338-345`（調査済み auto の plan の後、通常プロンプトが依頼を閉じる）の隣に、`/html-plan` → report → html の Write → Respond 風プロンプト → packet の Write が `unguarded`、のケース。
- 引き継ぎのとおり。test 名は ASCII（既存名はすべて英語）。lint 項目 11（bats の握り潰し assertion）に注意し、既存の `|| return 1` 形に合わせる。

### 3. pack.mjs（`skills/html-plan/runtime/pack.mjs`）

marketplace 版（`~/.claude/plugins/marketplaces/claude-community/html-plan/`）と cache 版（`~/.claude/plugins/cache/claude-community/html-plan/1.0.0/`、`installed_plugins.json:159` の installPath）は、SKILL.md 174 行・pack.mjs 300 行・htmlplan.js 1299 行・htmlplan.css 564 行・examples 298 行で行数が一致する（内容の byte 比較はしていない）。gitCommitSha `f60f0454...`（`installed_plugins.json:163`）。

- 出力先 `:24` `const outPath = resolve(opt('-o', opt('--out', inPath.replace(/(\.src)?\.html?$/, '') + (inPath.includes('.src.') ? '.html' : '.packed.html'))));` — 既定は入力の隣に `<slug>.packed.html`。
- artifact `:292-298` `if (argv.includes('--artifact')) {` ... `const artPath = outPath.replace(/(\.packed)?\.html?$/, '.artifact.html'); writeFileSync(artPath, art);` — 引き継ぎの `:292-299` は一致。`artPath` は `outPath` から導く（`:297`）ので、`-o <scratch>/x.packed.html` を付ければ packed と artifact の両方が scratch に出る。**docs/plans/ に packed を出さない最小の方法は `-o`**（.gitignore も同期 script も触らずに済む）。
- `--root`: `:23` で `~/` を展開。root 無しだと `baseDir`（入力の隣）だけが読める（`:36` の FENCE）。repo 内の `src=` を引く plan は `--root <repo>` が要る。
- 読めない path: `:38-43` の SECRET_NAME は `.git` `.ssh` `.env*` `credentials*` `*.local.json` `*.key` 等。`~/.claude` 自体は対象外だが、`settings.local.json`（`*.local.json`）と `.credentials.*` は plan から引用できない。
- 日本語の警告: `:221` `if (n.claim && n.l <= 2 && !n.a.aux && !/[.?!]$/.test(n.claim)) warn(...)` — claim が `. ? !` で終わらないと level 1・2 の claim ごとに警告。日本語の「。」終わりは必ず警告になる。errors ではないので書き出しは止まらない。ほかの警告: `:220` claim が 16 語超（空白区切りの語数なので、日本語は空白が無く 1 語扱い — 実質鳴らない）、`:248-250` 段落 40 語超・文 25 語超・散文 350 語超（日本語は同じく鳴りにくい）、`:252-263` の STE 辞書は英語の語だけ。結果: 日本語 plan で鳴る警告は `:221` が主。
- 警告を黙らせる選択肢: (a) 受け入れる（`--quiet` は info/warn/error の表示をすべて消すので error も見えなくなる — 非推奨）/ (b) claim を「。」でなく「.」で終える（日本語文として不自然）/ (c) plugin 本体は編集しない決定なので pack.mjs の patch は不可。rule 側の注意書きで「`:221` の警告は日本語では無視してよい」と書くのが整合的。
- タイトル警告 `:296`: artifact の `<title>` に `: — –` か ` - ` を含む、または 5 語超だと警告。日本語の題は語数 1 になりやすいが、`:` と `—` は避ける（SKILL.md `:36` は「2–4 語」）。

### 4. plan-executor-notice.sh と ADR-0057

- `settings.json:171` `"matcher": "ExitPlanMode",` → `:175` `bash ~/.claude/hooks/plan-executor-notice.sh`（引き継ぎの `:171-179` は一致）。hook 本体 `hooks/plan-executor-notice.sh:51` `[[ "$tool" == "ExitPlanMode" ]] || exit 0`。plan mode を使わなければ**鳴らなくなる**（落ちるのは「実行者の決定」の想起 — 実装の Edit の前に dispatch を思い出させる唯一の hook）。
- `docs/adr/0057-judge-tier-default-dispatch-and-plan-boundary-advisory.md:83-` の注記（2026-09-25、plan mode 廃止案）が、発火点を「mod 化した plan mode の承認イベントへ移す / rules の 1 行だけに縮退」と既に決めている（`:88-90` 付近）。本件は第 3 の事象。
- 選択肢: (a) html の `doc-ask` に「実行者」を置く（plan 本文に `実行者の決定` が入れば、hook の抑制 `:57-59` と同じ語を使える。Respond の貼り戻しに残る）/ (b) UserPromptSubmit で Respond 貼り戻し（`# Re:` 見出し、SKILL.md `:139` の形）を検出して advisory — 新規 hook で、payload の `.prompt` 先頭が `# Re:` で始まることに依存する（実機未確認）/ (c) ADR-0057 注記どおり rules の 1 行に縮退。judge-tier 判定（transcript 末尾の `"model"`）は (b) でも流用できる。

### 5. 公開 repo への同期

- `~/MyAI_Lab/claude-harness/scripts/sync-from-local.sh:157-169`（引き継ぎは一致）: `:161` `if [[ -n "$(git -C "$SOURCE_DIR" status --porcelain -- docs/plans)" ]]; then` で **docs/plans 配下の未追跡・未 commit は種別を問わず abort**。`:169` `git ... ls-files -- 'docs/plans/*.md'` で集めるのは tracked の `.md` だけ。
- `~/.claude/.gitignore`（全 107 行を Read）に `docs/plans` の `*.html` 除外は無い。`:17` `/plans/`（legacy だけ）、`:18` `plugins/`（plugin 本体は追跡外）。
- 結果: (i) packed / artifact を docs/plans に出すと、commit しない限り次の harness-sync が abort する。(ii) 追跡した `docs/plans/<slug>.html` は `ls-files '*.md'` に当たらず**公開 copy に入らない**。ADR / RFC からの相対リンク（adr-writer `:154-156`、rfc-writer `:66`）は公開 copy で切れる。ADR-0085 Decision 5 の「plan を公開物から辿れる」前提が html には成り立たない。
- 選択肢: (a) packed / artifact は `-o` で scratch に出し、docs/plans には source html だけ置く（abort 回避）。(b) 公開 repo へ html を載せるなら同期 script の glob を `*.md` と `*.html`（`*.packed.html` と `*.artifact.html` を除く）に広げる — **公開側 script の変更なので著者の GO が要る**（ADR-0086 Consequences の公開面の節と同じ扱い）。(c) 公開 copy に html を載せず、plan の要旨を ADR / RFC の Context に書く。
- ライセンス・runtime の公開可否は下の「確認」参照。source html は `htmlplan.css/js` を**名前でリンクするだけ**（pack が inline する — `:268-270`）。source だけを commit すれば runtime は公開 repo に入らない。packed / artifact は runtime を丸ごと内包する。
- `scripts/hooks/harness_lint.py` は docs/plans の html も `hooks/README.md` の表も検査しない（下の「確認」）。

### 6. 注記が要る箇所（Read 済み）

- ADR-0085（`docs/adr/0085-plans-as-records-in-docs-plans.md`）: `:41-43` Decision 3「承認した plan は実装の最初の commit に単独で入れる（件名 `docs(plan): <slug>`）」— html でも同じ運用にできるが、承認の確定が Respond 貼り戻しになる。`:48-50` Decision 5（`docs/plans/` を同期対象、tracked の plan のみ）— 上の 5。`:59-60` Review-when「2026-10-11 に ExitPlanMode 承認数を分母に…」— plan mode を外すと分母が 0（または減少）になり、判定が成立しない。分母を「Respond 貼り戻し数」か「docs/plans の新規 plan 数」に替える注記が要る。
- ADR-0086: `:94` Decision 5（Mermaid）、`:123-135` Review-when（窓の切り直し。上の 1 参照）、`:156-158`「純正 plan mode を使わず、通常モードで plan ファイルを書く独自 workflow」を**却下**した節 — 理由は「plan mode の承認 UI と、plan 中に本体が書き込まない性質を失う」。今回の決定はこの却下理由を、実測（plan mode は plan ファイル以外への Write を拒否する）で覆す形になる。supersede 注記を残す。`:167-168` plannotator の Open「Mermaid 入りの plan ファイルでもレビューしにくいと著者が言った」— html-plan の Respond が同じ穴を埋めるので、Open を閉じる注記。
- ADR-0057: 上の 4。
- `rules/common/planning.md:13-18`（`:13` 「plan mode は repo の root で起動する」、`:16-18` 「plan は report にリンクし構造を Mermaid で示す（ADR-0086）」）。`:3` の review-when コメントは「plan mode か plansDirectory の挙動が変わった時」。
- 起票: 機構・ゲート・閾値を変え、旧 ADR を supersede するので ADR-0087 を起票し、0085 / 0086 / 0057 の該当節から注記で指す（rules/common/akc-cycle.md「ADR の扱い」）。

### 7. 文言依存（Read 済み。plan mode 前提の記述）

| file:line | 現状の文 | 変更 |
|---|---|---|
| `skills/implementation-chain/SKILL.md:62` | `Plan（メインループ / plan mode。...）` | 「plan mode」を「html-plan（または plan mode）」へ |
| `skills/search-first/SKILL.md:85` | `every question asked for a plan (plan mode, or a prompt that asks for a plan; ...)` | 括弧に html-plan 起動を足す。`:105-110` の report 手順は変更不要（report は md のまま） |
| `skills/adr-writer/SKILL.md:154-155` | `When the decision went through plan mode, the first line of Context links the approved plan: Plan: [docs/plans/<file>](../plans/<file>)` | 「plan mode」を「plan（plan mode または html-plan）」に。リンク先が `.html` になるとき、公開 copy で切れる点（5 (ii)）を書く |
| `skills/rfc-writer/SKILL.md:66` | `plan mode を通った作業は ## Status に **YYYY-MM-DD plan** — [docs/plans/<file>](../docs/plans/<file>)` | 同上 |
| `skills/grill-me/SKILL.md:19, :82` | `Just before EnterPlanMode, ...` / `ready to hand to planning (skill: implementation-chain) or EnterPlanMode` | 「EnterPlanMode」を「plan（html-plan）」へ。grill-me は plan の前段で、plan mode そのものを呼ぶ手順ではない |
| `skills/spawn-session/SKILL.md:118-133` | `plan mode は EnterPlanMode で新セッション自身が入れるので、kickoff プロンプトの冒頭にそう書く。2026-07-26 に実測: ...` と例文 `まず plan mode に入って（EnterPlanMode）、そのうえで /grill-me を起動してほしい。` | **既定を替えるか要判断**。ここは「新セッションで /grill-me を plan mode 下で走らせる」実測つきの手順で、plan mode を使う理由（kickoff 後の対話）が html-plan の理由（plan ファイル以外への Write）と衝突するのは、その新セッションが plan ファイル以外へ書く必要があるときだけ。変更しない選択肢（plan mode は消さない決定の範囲）と、「plan を書かせるなら `/html-plan` を kickoff に書く」例を併記する選択肢がある |
| `skills/task-triage/SKILL.md:146-149` | `Write the packet ... to docs/plans/<task-id>-s<n>-<slug>.md ... commit it alone on main ... the packet is the plan of the build (ADR-0085, RFC-0035)` | html 化しない（引き継ぎの前提）。`scripts/cloud-dispatch.sh:5` は `docs/plans/rfc-0048-s1-skill-store.md` の md を渡す。packet は `.md` のまま `*/docs/plans/*.md` なので research-gate の `is_plan_file` に当たる（現行どおり unguarded に入る — ADR-0086 Decision 8）。変更不要。ただし PLAN_ASK に `/html-plan` を足しても packet は md のままなので影響しない |
| `hooks/README.md:56, :66, :67, :79` | `:56` Edit|Write 行（plan の依頼中…plan ファイル `*/docs/plans/<name>.md`）、`:66` plan-executor-notice 行（ExitPlanMode）、`:67` research-gate の PostToolUse 行（`Write\|EnterPlanMode\|ExitPlanMode`）、`:79` UserPromptSubmit 行（言い方の列挙） | 変えた分を反映。`:79` には `/html-plan` 起動を足す。matcher を変えた場合は `:67` と settings.json `:181` を揃える |
| `agents/researcher.md:4, :23` | `:4` `plan mode の親の下でも書ける。...`、`:23` `report は <project の絶対 path>/docs/plans/research/<YYYY-MM-DD-slug>.md` | `:4` は plan mode を使わなくても嘘にならない。`:23` は変更不要（report は md） |
| `scripts/hooks/harness_lint.py` | 下の「確認」 | 変更不要 |
| `.gitignore:17` | `/plans/` | 変更不要。packed / artifact を docs/plans に出す選択肢を採るなら `docs/plans/*.packed.html` と `docs/plans/*.artifact.html` を足す |

## 確認

- **PLAN_ASK と `/html-plan`（コード読みでの推定）**: `hooks/log-skill-usage.sh:139-153` が UserPromptSubmit の user 入力 `/skill` を `.prompt` の先頭 `/` で拾っており（`[[ "$prompt" == /* ]]`、`name="${prompt#/}"`、`name="${name%%[[:space:]]*}"`）、**slash 入力は生の `/<name> <args>` として `.prompt` に載る**前提でこの harness は書かれている。コメント `:147-148` に「plugin-namespaced names (":") を除く」とあるので、plugin skill は `/html-plan:html-plan` の形でも届きうる。PLAN_ASK `:47` は「プランして…」「`\bplan (this|it|out)\b`」「make a plan」等で、`/html-plan add send later to the composer`（`:6` の README 例）の `html-plan` は `\bplan ` の後に this / it / out が無いので**合わない**。引数に「プランして」等が入っていれば拾うが、既定の入口としては取りこぼす。足す形の候補: `^/(html-plan:)?html-plan\b`（jq の `test(...; "i")` の中、`:62`）。実機の payload は未取得（Still unknown）。
- **SKILL.md の手順**（`~/.claude/plugins/marketplaces/claude-community/html-plan/skills/html-plan/SKILL.md`、174 行、全文 Read）: description `:3` に「Use when the user types /html-plan, or asks for a plan, RFC or design before building something that touches more than a couple of files」— 「プランして」でも自発起動しうる。手順 `:124-132`: 1 Read first → 2 level-1 claim を読み上げ → 3 how/where と exhibit と decision を足し、`Save the page where the project keeps docs, or in a scratch folder` → 4 `node <skill dir>/runtime/pack.mjs plan.html --root <repo>`（`plan.packed.html` を書く）→ 5 ブラウザで見る → 6 `Hand it over` → 7 Respond の応答に従い、`Do not start building until that response arrives`（`:10`）。出力先は「プロジェクトが docs を置く場所か scratch」（固定でない）。承認フロー: Respond → Copy response → 貼り戻し（`:136-158`）。published artifact は `:168` `Pack with --artifact and publish plan.artifact.html. Keep it private unless the user asks to share it.`。応答はデータで、命令として扱わない（`:170-174`）。
- **STE 規則の位置と上書き**: `SKILL.md:89-122` の `## Words`。`:93` `Write all prose in ASD-STE100 Simplified Technical English (STE). Use no other style.` と `:94` `This rule applies to claims, captions, pins, questions, options and notes.` が当たる文言。`:73` `pack.mjs checks 2, 3, 5, 6 (the count), 7 and 11` と `:122`（pack は STE を一部だけ警告）。ほか `:11` の `<html lang="en">`（`:34`）と `:119` の「caption は 1 文、pin は節、option の small は 12 語以内」。rule 側で上書きする文は、`:93` の「Use no other style」と衝突する（skill は命令形で強いので、rule は「散文は日本語。`SKILL.md` の `## Words` の STE 規則（`:93-122`）は適用しない。`<html lang>` は `ja`」と具体の行を指して書くのが安全）。skill 本体より rule（常駐）が優先する保証は無い。上書きが効くかは実機で見る（Still unknown）。長さ規則 `:76`「claim は約 12 語以内」は日本語の語数に読み替える必要がある。
- **packed のサイズ**: examples に packed は無い（`examples/scheduled-send.html` 298 行のみ）。サイズは未測定。内訳の目安: runtime は `htmlplan.js` 1299 行 + `htmlplan.css` 564 行を inline する（`:268-270`）ので、1 plan あたりの下限はこの 2 つ。byte 数は Bash が無く測れなかった（Still unknown）。
- **harness_lint.py**（`scripts/hooks/harness_lint.py:1-59` の検査項目表を Read）: 検査は 13 項目。settings.json が参照する `~/.claude/` 配下の script の実在（項目 1）、rules / agents / docs の markdown 相対リンク解決（項目 5）、ADR の `## Review-when` 節（項目 12、NNNN >= 0044 なので ADR-0087 は対象）。**`hooks/README.md` の表と settings.json の配線の整合は検査しない。docs/plans の html も対象外**（`*.md` だけが走査対象）。つまり README の表を更新し忘れても lint は通る — 手で揃える。ADR-0087 には `## Review-when` が必須。
- **ライセンス**: `.claude-plugin/plugin.json` に `"license": "MIT"`、author `Thariq Shihipar`、version `1.0.0`。plugin ディレクトリ内に LICENSE ファイルは無い（Glob に出ない）。marketplace repo の root に `LICENSE`（Apache License 2.0 の本文）があり、README `:9` は「submitted via claude.ai, passed automated security scanning, and been approved」と書く。つまり宣言は plugin.json の MIT、repo root は Apache-2.0 で**食い違い**（どちらが plugin に適用されるかは repo に明記されない）。どちらでも再配布は許諾される範囲（著作権表示とライセンスの同梱が条件）。結論: source html（runtime を名前で参照するだけ）の commit は問題にならない。packed / artifact を公開 repo に載せると runtime の再配布になるので、載せるなら表示（MIT / Apache の告知）を同梱する。Artifact 公開（private）は再配布に当たらないと読めるが、これは法的判断ではなく規約読みの推定。
- **セッション skill 一覧に html-plan が無い原因（推定、未検証）**: `installed_plugins.json:161` `"installedAt": "2026-10-05T20:13:56.939Z"`（JST 2026-10-06 05:13）、`settings.json:320` `"html-plan@claude-community": true`。plugin の skill は session 開始時に読み込まれるので、**この session が 20:13Z より前に始まっていれば一覧に出ない**のが最有力。cache の `.in_use/` に 11 個の PID ファイルがあり（別 session が読み込み済み）、plugin 自体は壊れていない。測り方: `/reload-plugins`（または新 session）で skill 一覧に `html-plan` が出るか。この session の開始時刻（transcript `862daa63-...` の最初の timestamp）と 20:13Z を比べる。
- **auto mode で docs/plans/*.html を書く際の別制限**: 未確認。参考: ADR-0086 `:108-110` の実機確認で、harness repo（`.claude` 配下）の researcher の report に「sensitive file」の確認が出た（approve でも飛ばない）。主ループの `docs/plans/*.md` の Write も既存 plan が多数あるので通っているが、`.html` で拡張子別の確認が出るかは未測。

## Still unknown

| 未確認 | 測り方 |
|---|---|
| `/html-plan ...` 起動時の `.prompt` の実際の文字列（`/html-plan <args>` か `/html-plan:html-plan <args>` か、skill 展開後の本文か） | 使い捨ての `--settings` で UserPromptSubmit に `jq -c . >> $SCRATCH/payload.jsonl` を置き、`claude -p '/html-plan test'` を 1 回。ADR-0086 Decision 6 と同じ手法。その出力を PLAN_ASK（`jq test`）に通して一致を確かめる |
| packed / artifact のサイズ（byte 数） | scratch（`/private/tmp/claude-501/-Users-shimomoto-tatsuya--claude/862daa63-.../scratchpad`）に `examples/scheduled-send.html` をコピーし `node pack.mjs scheduled-send.html --root . --artifact` を実行、`wc -c`。Artifact tool の size 上限も同時に確認する |
| rule による STE 上書きが効くか（skill `:93`「Use no other style」との優先） | 上書き rule を置いた状態で `/html-plan` を新 session で 1 回走らせ、散文が日本語になるか、`<html lang>` が `ja` か見る。効かなければ skill の呼び出し側 prompt（research-gate の PROTOCOL か advisory）に同じ文を足す |
| `:221` の警告の実数（日本語 claim 5 本の plan で何件鳴るか） | 日本語で書いた test html を `--lint-only` で pack し、警告行を数える |
| auto mode で `docs/plans/*.html` の Write に確認が出るか | 使い捨ての `--settings` で `permission_mode: auto` の `claude -p` が `docs/plans/x.html` を書けるか（`.claude` 配下の repo と、そうでない repo の両方） |
| html の初回 Write で依頼を閉じるか（選択肢 1(b)）の副作用 | 閉じると、同じ依頼内の plan 手直しの Write が `unguarded` に数えられる（PASSED `:158` / `:259` が防ぐ。`:273-277` が PASSED に追記するので手直しは数えない）。bats で確認できる |
| ライセンス表示の食い違い（plugin.json は MIT、marketplace repo root は Apache-2.0 本文） | 公開 repo へ runtime を載せる判断をするときだけ要る。上流の repo に問い合わせるか、source html だけを載せて回避 |
| `/html-plan` が session 内の skill 一覧に出ない原因の確定 | 上の「推定」の測り方 |
| Respond 貼り戻しを `UserPromptSubmit` で検出する形（ADR-0057 の選択肢 (b)）が成立するか | 実際に貼り戻された prompt の先頭行（SKILL.md `:139` は `# Re: <title>`）を 1 回取る |

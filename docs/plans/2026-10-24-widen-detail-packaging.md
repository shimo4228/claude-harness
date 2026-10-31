kind: external
# 「流れ skill + 部分 skill」の 2 家族（widen / detail）を 1 つの配布物にまとめる形は何か

as-of: 2026-10-24（全 claim の取得日）。一次資料は公式 doc の本文を WebFetch で読んだもの。snippet だけのものは明記する。

## Scope searched

- 読んだ一次資料（本文まで）:
  - Claude Code skills doc `code.claude.com/docs/en/skills`（先頭 100,000 字。末尾 18,114 字は未読）
  - plugin manifest reference `.../plugins-reference`
  - plugin install `.../plugins/install.md`
  - plugin loading reference `.../plugins/loading.md`
  - claude.com の Plugins overview と Plugin feature support across platforms
  - claude.com の Skills overview と Create custom skills（`how-to.md`）
  - Agent Skills specification（agentskills.io/specification）
  - support.claude.com「How to create custom skills」
  - anthropics/skills の README と `.claude-plugin/marketplace.json`（raw）
  - obra/superpowers の `skills/subagent-driven-development/SKILL.md` 1 本
- ローカル: `~/.claude/skills/skill-creator/references/portability.md` 全文。widen-* / detail-* / unit-eval の `..`・`CLAUDE_SKILL_DIR`・外部依存名を grep。
- snippet 止まり: Codex plugin 形式（WebSearch の要約。OpenAI 公式 quickstart の本文は未取得）、Cowork の GitHub 同期や personal upload の細部（Anthropic の org 管理 help の要約）、claude-plugins の Cowork 不具合 issue（要約のみ）。
- 見つからなかった範囲:
  - 「流れ skill + 部分 skill」を相対パスで分けて配る既製の先例の網羅調査。awesome list は走査していない。
  - claude.ai の chat 環境で兄弟 skill フォルダ（`../x`）が読めるかを述べた公式記述。
  - claude.ai が `disable-model-invocation` / `user-invocable` を解釈するかを述べた記述。
- `~/MyAI_Lab/herdr-toolkit` は Glob で存在を確かめただけで、plugin.json と sync script は読んでいない。レイアウトは依頼文の記述を前提にする。

## Found

### 1. Claude Code plugin の現行仕様（公式 doc 本文）

- **名前空間**: plugin の `skills/<name>/SKILL.md` は `/plugin名:skill名` になる。例は `my-plugin/skills/review/SKILL.md` が `/my-plugin:review`、frontmatter `name: fancy` なら `/my-plugin:fancy`（skills doc）。manifest reference も「Every component is namespaced under it」と書く。plugin の `name` は kebab-case で、`claude-` `anthropic-` 始まりは validate で Error になる。
- **同名衝突**: ローカル `~/.claude/skills` の同名 skill と plugin skill は上書きにならず、どちらも読み込まれる。plugin skill は `/plugin:skill` として別名で並ぶ（skills doc「Both load, because plugin skills are namespaced」）。衝突で壊れるのは同一 plugin 名の plugin 同士で、loading.md の「Name conflicts」節が優先順位を定める（managed > `--plugin-dir` > 導入済み marketplace plugin > skills-dir plugin > claude.ai 同期 plugin）。
- **`${CLAUDE_SKILL_DIR}`**: 「For plugin skills, this is the skill's subdirectory within the plugin, not the plugin root」。つまり `${CLAUDE_SKILL_DIR}/..` は plugin の `skills/` になり、同一 plugin の兄弟 skill を指す。公式 doc に「兄弟 skill を `..` で読んでよい」という明文は見つからなかった。成立の根拠は次の導出による。
  - loading.md は、marketplace plugin は plugin ディレクトリごと `cache/<marketplace>/<plugin>/<version>/` にコピーすると述べる。
  - 同じ節で、コピーされないのは plugin ディレクトリの外のファイルだと述べる（「a script inside a copied plugin reads a path above the plugin root, such as `../shared`, it doesn't find them」）。
  - 兄弟は plugin 内にあるのでコピーされる。これは推論であり、実機での確認は未了。
- **component path の閉じ込め**: manifest の component path が plugin root の外へ出る（`..` や外向き symlink）と `path escapes plugin directory` で読み込まれない。ただしこれは manifest 宣言の検査であり、SKILL.md 本文中の `${CLAUDE_SKILL_DIR}/../x` を実行時に読む動作は対象外と読める。
- **`disable-model-invocation` / `user-invocable`**: skills doc に表がある。`disable-model-invocation: true` は「Description not in context」で、ユーザーの `/name` だけで起動する。`user-invocable: false` は `/` メニューから隠す。plugin 専用の例外は doc に無い（plugin skill も skill）。したがって detail の 4 本は全て `disable-model-invocation: true` なので、常駐 context コストがほぼゼロになる。
- **引数**: `$ARGUMENTS`、`$ARGUMENTS[N]`、`$N`、frontmatter `arguments:` の名前付き引数がある。引数を置換する placeholder が無いときは `ARGUMENTS: <value>` が末尾に付く。(B) の `/widen-the-ask depth` はこの仕組みで動く。
- **長さ目安**: 「Keep `SKILL.md` under 500 lines」（Claude Code doc、agentskills.io、claude.com の 3 箇所で同じ）。agentskills.io は本文 5000 token 未満も推奨する。
- **Python 同梱**: skills doc に Python 固有の説明は無い（`scripts/helper.py` は「executed, not loaded」）。claude.com の how-to は `python3 ${CLAUDE_SKILL_DIR}/scripts/x.py` を例示する。Claude Code が plugin のキャッシュ時に自動で入れるのは Node 依存だけ（`package.json` + lockfile）。loading.md は「Python dependencies … install it from a hook into the persistent data directory」と述べる。`uv run --project "${CLAUDE_SKILL_DIR}"` のような実行時解決は仕様の範囲内だが、`.venv` は版ごとのキャッシュ dir に作られ、更新で捨てられる（旧版は 14 日後に削除）。python script を実行する Bash は権限確認の対象になる。
- **版**: manifest の `version` を書くと、その文字列を変えるまで更新が届かない。書かなければ git の commit SHA（12 桁）が版になる（loading.md「Versions and updates」）。手で上げる版と SHA 版のどちらを使うかは選べる。
- **1 repo から複数 plugin**: anthropics/skills は `skills/` を flat に置き、`marketplace.json` に 5 つの plugin（document-skills=xlsx/docx/pptx/pdf、example-skills=12 本 ほか）を置く。全 entry が `source: "./"`、`strict: false` で、各 entry の `skills` に `./skills/<name>` を列挙する（raw JSON で確認）。重複コピーなしで 1 repo から複数 plugin を出せる。
- **manifest 無しの単独 skill**: plugin root に `SKILL.md` があるだけでも単一 skill として読み込まれる（plugins-reference「Standard layout」）。

### 2. Agent Skills 標準（agentskills.io、本文）

- 構成: `SKILL.md` 必須、任意で `scripts/` `references/` `assets/`。`name` は親ディレクトリ名と一致必須。
- frontmatter の field は `name` `description` `license` `compatibility` `metadata` `allowed-tools`（experimental）のみ。**`disable-model-invocation` と `user-invocable` は標準に無い**（Claude Code の拡張）。`skills-ref validate` は定義外 field を問題として列挙する、と claude.com how-to が書く。
- progressive disclosure: metadata 約 100 token → 本文 5000 token 未満推奨 → resources は必要時のみ。
- 参照は skill root からの相対パスで、`SKILL.md` から 1 段までにする。深い参照の連鎖は避ける。
- **1 skill 多モードの推奨記述、および兄弟 skill / skill 間依存の仕組みは標準に無い**。標準の語彙は `references/` へ畳む方向だけを持つ。

### 3. claude.ai / desktop / Cowork への経路

- **単独 skill の upload**（claude.com how-to）:
  - ZIP は skill ディレクトリ自体を最上位にする（`my-skill.zip` → `my-skill/SKILL.md`）。
  - `references/` `assets/` `scripts/` を持てる。scripts は chat では code execution sandbox に「skill の whole folder」ごとコピーされる。
  - 1 ZIP = 1 skill フォルダが前提の記述で、兄弟 skill を同梱する形は書かれていない。
  - `${CLAUDE_SKILL_DIR}` は Claude Code と Cowork で置換される。chat では置換されないので「`scripts/render.py` のように SKILL.md からの相対でも読める形にしておけ」と書かれている。
  - 利用には Pro 以上と code execution の有効化が要る。
- **plugin の upload 経路が存在する**（claude.com Plugins overview）:
  - **Customize > Plugins > Add > Upload plugin** は、フォルダを `.zip` / `.plugin` にしたものを受け取る。`.claude-plugin/plugin.json` が 1 つ要る。
  - **Add > Add marketplace** は GitHub / GitHub Enterprise の repo、公開 GitLab / Bitbucket を受け取る。
  - 入れた plugin は claude.ai アカウントに保存され、chat（web・desktop・mobile）、Cowork、Claude Code（`<name>@synced`、次の session 開始時に同期）の全てに出る。
  - plugin の skills は chat で「`plugin-name:skill-name`」で `/` メニューに並ぶ。
  - 上限: 1 plugin あたり 5,000 files / 200 MB、自分で足す marketplace は 25 まで（Platform support 表）。
- **component の対応**（Platform support 表）: Skills は Chat / Cowork / Claude Code の全てで Loads。Agents と Hooks は Chat で Ignored。`bin/` は claude.ai と Cowork では Can't be installed（今回は bin を使わないので無関係）。
- 逆方向: Claude Code の `claude plugin install` した plugin は claude.ai に上がらない（install.md）。claude.ai 側で入れたものが Claude Code に同期される一方向。
- **未確認（決定に効く）**:
  - chat 環境で plugin 内の兄弟 skill フォルダ（`../widen-altitude/SKILL.md`）が sandbox に載るか。how-to の「whole folder」は 1 skill の folder を指すように読める。plugin zip 全体が載るのか、skill ごとなのかは記述が無い。
  - chat が `disable-model-invocation` を解釈するか。

### 4. 先例（どの形をとっているか）

- **anthropics/skills**（README と marketplace.json を読んだ）: 独立 skill を主題別に plugin へ束ねる。flat な `skills/` + 複数 plugin entry。README は skill 同士の参照を示していない。「流れ + 部分」型の先例ではない。
- **obra/superpowers**（`subagent-driven-development/SKILL.md` 1 本のみ読んだ）:
  - 兄弟 skill は名前で指す（`superpowers:using-git-worktrees` など）。相対パスでは指さない。
  - 自分の手順の細部は同じ skill の `references/`（`resuming.md`、`fix-loop.md` など 7 本）と `scripts/` に畳む。
  - つまり 1 plugin 内で「skill 間は名前、skill 内の細部は references/」の併用になっている。公式 doc 由来ではない 1 repo の観察である。
- Codex（snippet のみ）: plugin は `.codex-plugin/plugin.json` + `skills/<name>/SKILL.md`。repo 単位は `.agents/plugins/marketplace.json`。Claude 用の `.claude-plugin/` とは別 manifest が要る。`${CLAUDE_SKILL_DIR}` が Codex でどう扱われるかは未確認で、portability.md は「他 agent は SKILL.md のディレクトリとして読む」と前提している。

### 5. portability.md と各候補の整合（ローカル全文）

- `${CLAUDE_SKILL_DIR}` で自分のファイルを指す。兄弟は `"${CLAUDE_SKILL_DIR}/../<sibling>"` と書き、「when it is installed next to this one」と添える。**(A)(C) は規約どおり**。(D) も規約どおりだが、配布先の「隣に置く」前提が崩れた環境（claude.ai の 1 skill = 1 フォルダ）で壊れる。(B) は兄弟参照を持たないので規約の想定外のまま通る。
- 家族外 skill は「skill 名で指す」と規約にあり、`repair-discipline` `persona-read-loop` `loop-design-check` は名前参照。配布物に入らない名前参照は dangling になるので、「導入済みなら使う」という条件付きの文に直すか、要点を inline する。
- 「SKILL.md 本文に自分の個人 project への固定パスを書かない」規約があり、MAINTENANCE.md は配布から除く対象になる。
- 内部事実（grep 済み）:
  - `skills/widen-the-ask/SKILL.md:21-23` が `../widen-*/SKILL.md` を相対 link で指す。
  - `skills/detail-loop/SKILL.md:21-23` が `${CLAUDE_SKILL_DIR}/../detail-review|detail-units|unit-eval/SKILL.md` を指す。
  - `skills/detail-units/SKILL.md:34` が `widen-depth` を枠として名指し（家族またぎ）。
  - `skills/detail-units/SKILL.md:148` が `uv run --project "${CLAUDE_SKILL_DIR}" python …/validate_units.py`。
  - `skills/unit-eval/references/web.md:25` が `../../detail-review/references/web.md` を指す。**家族内に、`${CLAUDE_SKILL_DIR}` を使わない相対参照がもう 1 本ある**。
  - 家族外参照: `detail-loop/SKILL.md:29,34`、`detail-review/SKILL.md:17`、`detail-units/SKILL.md:24` と `detail-loop/MAINTENANCE.md:15`。

### 6. 候補 A–D の比較

| | (A) plugin に家族ごと同梱 | (B) 部分を references/ に畳む（1 家族 = 1 skill） | (C) B の 2 skill を 1 plugin に | (D) 現状維持 |
|---|---|---|---|---|
| Claude Code | `/plugin:skill` で全部品が個別起動。ローカル同名とは共存 | `/widen-the-ask depth` の引数で部分を呼ぶ。個別の slash 名と description を失う | 同左 + plugin 名前空間 | 動く（現行） |
| claude.ai chat / Cowork | plugin upload / marketplace の経路あり。**兄弟読みが chat で通るかは未確認** | 1 skill = 1 フォルダなので確実に運べる（相対参照が無い） | plugin 経路でも単独 ZIP でも確実 | 兄弟相対参照は 1 skill 単位の upload で運べず drift した実績 |
| Codex 等 | `.codex-plugin/` を別途持つ。skill 本体は標準準拠 | SKILL.md + references/ なのでそのまま標準 skill として動く | 同左 | skill は動くが 8 個を別々に入れる |
| 部分の単独起動 | 可（各自が原則を持つ設計のまま） | 引数経由のみ。detail の 4 本は全て手動起動なので、slash 名が 1 本になる損失が主 | 同左 | 可 |
| 家族またぎ依存 | 同一 plugin なら `..` で届く。2 plugin なら届かない（`dependencies` は plugin 単位で、skill 内の相対 path は越えない） | 家族 = 1 フォルダなので家族内は解消。家族またぎは別 skill のまま（widen-depth の「四点」を detail-units が名指す） | C で同一 plugin にすれば skill 名参照が届く | 配布先で隣に無ければ dangling |
| 家族外依存 | 配布物に無いので dangling。条件付き文か inline が要る | 同じ | 同じ | 同じ |
| 保守コスト | 固定 allowlist の sync script + plugin.json / marketplace.json + 版の運用。herdr-toolkit と同形 | 畳む改修が 1 回かかる。detail は references の衝突（web.md が 2 本、別内容）の整理と、`validate_units.py` の置き場の決定が要る。以後の sync は軽い | B の改修 + A の manifest 運用 | 0（配布しない場合）。公開 copy は harness-sync で個別 8 本 |
| drift の起きやすさ | 低い（1 手順で全部品が同じ版）。ただし chat 側が兄弟読みを通さないと分割前の上げ直しが再発 | 低い（1 ファイル系）。ただし本文の肥大が起きると 500 行目安に当たる | 低 | 高い（claude.ai 版は既に drift） |

規模の見積もり（内部調べの行数から）: widen は合計約 156 行（36 + 40×3）で、畳んでも 500 行未満。detail は流れ 121 + review 94 + units 167 の約 382 行 + unit-eval で、そのまま 1 本には入らず、入口 SKILL.md + references/ に分けることになる。

## Contradictions

- **claude.ai の skill 上限**: support.claude.com の古い記事は `description` 200 字・ファイル名 `skill.md`・`dependencies` field と書き、claude.com の現行 how-to は `description` 1,024 字・`SKILL.md`・標準 field と書く。後者は Agent Skills 標準とも一致し、日付も新しいので採る。サイズ上限は skill 単体では見つけられなかった（plugin は 200 MB / 5,000 files）。
- **org 向け plugin upload の上限**: 検索要約は「.zip under 50 MB」、claude.com の Platform support は個人アカウントで 200 MB。対象（org 管理の upload と個人の upload）が別と読むが、確認していない。
- **Cowork での plugin 配信**: GitHub issue の要約は「marketplace 経由の plugin は Cowork で skill が読まれないが zip upload は動く」（2026-03 起票、2026-05-23 close、修正が出荷されたかは未確認）。公式 doc は両経路を動くと書く。公式の記述を採るが、Cowork での実機確認は要る。

## Still unknown

1. chat 環境で、plugin 内の `skills/a/SKILL.md` から `../b/SKILL.md` が読めるか。決定に直結する。確かめ方は、小さな 2 skill の plugin を zip にして Upload plugin で入れ、chat で兄弟参照を実行させること。
2. chat が `disable-model-invocation` / `user-invocable` を尊重するか。無視されるなら detail の 4 本の description が常駐する。
3. `${CLAUDE_SKILL_DIR}/..` が Claude Code の plugin キャッシュ上で実際に兄弟へ届くか。コピー規則からの推論で、`claude --plugin-dir` での実機確認が要る。
4. `uv` と validator の依存が claude.ai の sandbox、Cowork、Codex で使えるか。`pyproject.toml` の依存の中身は読んでいない。
5. Codex が `${CLAUDE_SKILL_DIR}` を置換するか、plugin の `skills/` から相対で兄弟を読めるか（snippet 止まり）。
6. anthropics/skills 型の `strict: false` + `source: "./"` が、plugin ごとに repo 全体をキャッシュするのか列挙した skill だけなのか。後者なら家族をまたぐ `..` は物理的に届かなくなる。
7. 「流れ + 部分」を相対パスで配る先例は superpowers の名前参照型しか読めていない。awesome list の走査はしていない。

## 推奨（lead が plan の Verdict に使う材料。as-of 2026-10-24）

**推奨: (A)。1 repo に flat な `skills/` を置き、`marketplace.json` に widen と detail の 2 plugin を出す（anthropics/skills 型）。実装の前に 3 件の実機確認を 1 回で済ませる。**

理由:
- 部分 skill が個別に呼べるまま残る。(B) は部分の slash 名と description を捨てる。
- claude.ai に plugin の upload 経路が実在する（Customize > Plugins > Upload plugin）。これで drift の原因だった「単独 skill upload は兄弟を運べない」を迂回できる見込みがある。(B) は確実に運べるが、部分の単独起動という設計意図を引数に退化させる。
- detail の 4 本は全て手動起動なので、同梱しても常駐 context に乗らない（Claude Code）。widen の部分 3 本も `disable-model-invocation: true` で同じ。
- 2 plugin にする理由: detail だけが python / uv の実行環境を要求し、widen は 1 本だけ model 起動できる汎用の skill で、読み手が違う。版も独立に上げられる。
- 家族またぎ依存は、detail-units の step 2 に widen-depth の「四点」を inline する（4 行）か、「widen-depth があれば使う」という条件付きの文にして、2 plugin を互いに独立させる。plugin の `dependencies` で縛る案は、1 参照のために導入を強制する点で重い。
- 家族外依存（`repair-discipline` `persona-read-loop` `loop-design-check`）は、配布物から外れる名前を「導入済みなら使う」という文に直し、MAINTENANCE.md は同期の allowlist から外す。

実装前の確認（どれかが落ちたら推奨が変わる）:
1. `claude --plugin-dir` で兄弟読み（`${CLAUDE_SKILL_DIR}/../x`）を通す。
2. 同じ plugin zip を claude.ai の Upload plugin で入れ、chat で兄弟読みを通す。落ちたら widen だけ (B)（約 156 行で 1 フォルダに収まる）に倒して claude.ai 用 ZIP を生成物にする。detail は Claude Code 専用と宣言する。
3. Cowork と chat で `disable-model-invocation` の効きを見る。

1 plugin にまとめる案（C 寄り）は、inline を避けたい場合の代替になる。常駐コストは小さいので成り立つが、python 要求と版が家族をまたいで結合する。

## 推奨の失効条件

- Claude Code が plugin skill の本文から兄弟 skill を読む動作を禁じる、または `${CLAUDE_SKILL_DIR}` の意味を変える（現行 doc: plugin skill の subdirectory）。そうなれば (B) か (C) に倒す。
- claude.ai の chat が plugin 内の兄弟フォルダを sandbox に載せないと分かる。widen は (B)、detail は Claude Code 専用に倒す。
- Agent Skills 標準が skill 間依存、または sub-skill の field を持つ。そうなれば標準の形を優先する（現行 spec には無い）。
- claude.ai の単独 skill upload が兄弟フォルダ同梱に対応する。(D) の drift の原因が消える。
- Claude Code の plugin キャッシュ規則（版ごとのコピー、plugin 外はコピーしない）が変わる。
- 検索時点の版の目印: manifest reference は v2.1.296 の記述を含む。それより古い版が配布先に居る場合は `skills: "."` などが通らない（v2.1.221 未満）。

## 追記: 候補 B の再評価（著者の提案を受けて lead が調べた内部事実、2026-10-24）

著者は「関連 skill を reference にして、必要なフェーズで読みに行く」形（候補 B）を提案した。内部の事実を足す。

- 家族の外から部分 skill を名指すのは `docs/evals/s7-widen-depth-native-ablation-2026-10-14.md` だけで、日付つきの記録なので書き換えない（grep 済み。hooks・scripts・他 skill からの参照は 0）
- gate は sub-project を `skills/*/pyproject.toml` で拾う（`.claude/verify.sh:425-426`）。validator を `skills/detail-loop/` へ移しても pytest の対象に残る
- 部分 skill は単独起動のために原則（一度に一問・作業を始めない・「このままでいい」で終える）を 3 本とも複製している（`widen-altitude/SKILL.md:15-17` ほか）。B では流れ SKILL.md に 1 回だけ書けば済み、重複が消える
- `detail-review` / `unit-eval` は `detail-units` を形式の正本として 12 箇所で名指す。B では `references/units.md` への参照に変わり、正本は 1 つのまま
- 規模: widen は 36 + 約 120 行、detail は SKILL.md 121 行 + references 約 370 行。どちらの SKILL.md も 500 行目安を大きく下回る
- B は plugin の兄弟読みが成り立つかという未確認の前提（Still unknown 1・3・6）を持たない。1 skill = 1 フォルダは単独 skill upload の前提と一致する
- B で失うのは部分の slash 名と description だけで、`$ARGUMENTS` で部分を呼べば単独起動は残る（Found 1「引数」）

この追記の時点で、推奨は B に変わる。A の失効条件の「chat が兄弟フォルダを載せない」は未確認のまま残るが、B はそれに依存しない。

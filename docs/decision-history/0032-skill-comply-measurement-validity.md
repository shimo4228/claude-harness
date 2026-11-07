# ADR-0032: skill-comply は「測定が成立していたか」をレポートの一級市民にする

## Status

accepted

## Date

2026-08-02

## Context

2026-08-01 の実運用（`results/apple-silicon-local-llm-serving.md`）で、**測定が成立していないのに
スコアが出ていた**ことが分かった。3 つの欠陥は別々に見えたが、根は 1 つだった。

**レポートは「エージェントに何を訊いたか」については自己完結していたが、
「エージェントが実際に何をできる状態だったか」を一切記録していなかった。**

SKILL.md は "Reports are self-contained" と書き、spec・シナリオプロンプト・タイムラインを
載せる。載っていなかったのは、測定が成立する前提そのもの:

| 欠陥 | 実測 |
|---|---|
| **A** 対象 skill が子から読み込めない | project skill の run で trace の 0 番目が `Skill(...)` → `Unknown skill`。出た 75% / 50% / 25% は **skill を一度も読んでいないエージェントの素の挙動** |
| **B** シナリオのフィクスチャが実体化しない | 生成器は `cat > f << EOF` を書き、実行器は `mkdir` / `touch` の 2 語彙しか解釈しない。`[setup refused]` 6 件、sandbox は空、あるエージェントは自分で 15KB のフィクスチャを書き始めた |
| **C** detector が要求するツールを子が持たない | spec の 9 detector 中 5 つが Bash 前提。`--allow-bash` を付け忘れれば「やらなかった」ではなく「観測できなかった」が 0% になる。レポートにツールの記録なし |

どれも欠けたまま数字は出る。だから静かに別のものを測る。

### 設計中に前提が 2 つ壊れた

A の設計レビュー中に、この作業の前提だった 2 つが実測で否定された。

1. **子の Bash は off ではなかった** → [ADR-0031](0031-child-permission-envelope-via-permissions-deny.md)。
   A の受容可能性の議論は「Bash が既定 off なので爆発半径は限定的」に立っていたので、
   その議論ごと無効になった。ADR-0031 を先に着地させてから A に戻った
2. **sandbox に置いたファイルは「置いてあるだけ」ではなかった** — sandbox は子にとっての
   **プロジェクトルート**で、そこでは一部のファイル名が読み込まれる設定・指示になる。
   実測（2026-08-02）: 一度も信頼していない workspace でも
   `<sandbox>/.claude/settings.json` の `hooks.SessionStart` は**無言でホスト上の
   コマンドを実行した**（同じファイルの `permissions.allow` は「信頼されていない」と
   明示的に拒否されるのに）。`<sandbox>/CLAUDE.md` も読まれて従われる

2 は設計に直接効く。子自身の Write は substrate が止める（`.claude/settings.json` への
書き込みだけが個別に拒否されることを実測）が、**このツールの pathlib 書き込みは止まらない**。
つまり `_contained` が保証する**位置**と、ファイルが持つ**解釈上の重み**は別の性質で、
これまで 1 つとして扱っていた。

## Decision

### 測定の前提をレポートに記録する

Summary に「対象の種別」「どの層で測ったか」「子から外したツール」「対象 skill を呼べた
シナリオ数」を出す。**読み込めないまま走ったシナリオはスコアから除外し、終了コード 1 を返す。**
警告だけでは足りない — 自動化は終了コードを読み、それが「正常」と言っていた。

### A: 2 層で測る（Tier 1 / Tier 2）

観測された欠陥は**発見の失敗であって手順の失敗ではなかった**。skill の発見と起動は
frontmatter の `name` と `description` で決まり、本文は「手を伸ばすと決めた後」に読まれる。
きれいに分かれるので、測定も分ける。

- **Tier 1（既定）** — `name` と `description` だけ本物の stub を `<sandbox>/.claude/skills/<name>/`
  に置く。**「skill に手を伸ばしたか」を測る。**untrusted な本文は子に届かない
- **Tier 2（`--load-target-skill`）** — 本物の本文。**「手順に従うか」を測る。**
  監査対象の本文が無人の子への指示になるので opt-in。`SKILL.md` 1 ファイルのみを写し、
  ディレクトリは写さない

**Tier 1 の測定結果は「呼べたか」であって compliance の数字ではない。** stub には手順が
入っていないので、自力で手順をこなしたエージェントが高得点を取りうる。それを compliance と
呼べば元の欠陥の再演になるので、レポートは 2 つの数字を分けて出し、どちらが何に答えるかを書く。

**Tier 1 は封じ込めの層ではない。** `description` は発見に必要なので必ず届く。上限 500 文字は
**分量の上限であって能力の上限ではない** — 500 文字は Read / Write / Edit / Glob / Grep を持つ
子への有効な指示として十分すぎる。Tier 1 と Tier 2 の差は「手順が届かない」であって
「指示が届かない」ではない。存在理由は測定の正しさであって escalation の削減ではない。

flag にして既定 off にしたのは、preflight が「どこにあるか」は分類できても「ユーザー自身が
書いたか」は分類できないため。既定 on は、未レビューの文書を無人エージェントへの指示として
黙って読み込むことになる。

### `<sandbox>/.claude/` と `<sandbox>/.git/` はツール専有

監査対象由来の指定（`setup_commands` / `files:`）はこの 2 つの下を一切受け付けない。
`place_skill` だけが `.claude/` に書ける。

- **`.git/` を含める理由**: `_setup_sandbox` が untrusted な書き込みの 2 行前に `git init` を
  走らせるので書き込み可能。`core.fsmonitor` / `core.pager` / `alias.*` は**実行ビット無しで
  git が実行する設定文字列**。実測: `files:` で `.git/config` を置き `git status` でホスト上の
  コマンドが走った。Claude Code は workspace で git を実行するので、**子の Bash を塞いでいても
  発火する**
- **判定は case-fold する**: APFS は case-insensitive なので `.CLAUDE/Settings.json` は
  書けてしまえば `.claude/settings.json` として読まれる。ここは同日に `run._collision_key` で
  同じ理由の修正をしたのに適用漏れしていた — **インスタンスを直してクラスを直していなかった**
- **予約 basename**: `CLAUDE.md` / `AGENTS.md` / `.mcp.json` / `settings.json` /
  `settings.local.json` / `.gitignore`。`.gitignore` は実行ではなく**測定の破壊** —
  Grep は従い Glob は従わないので（A/B 実測）、文書が自分のフィクスチャを detector が
  期待するツールから隠せる

**このリストは腐ることを前提に持つ。** 外部製品の設定面を列挙しているので、Claude Code や
git が新しい規約を足してもこのリストは知らない。prefix は閉じた集合なので強く、basename の
列挙は弱い — 弱いと明記したうえで持つ。

### B: `files:` で中身を渡す

守るべき不変条件は「シェルを起動しない・プロセスを実行しない・パスは sandbox 内に閉じる」で
あって「ファイルに中身を書かない」ではない。生成器が `cat >` に手を伸ばす**理由そのもの**を
消すため、シナリオ schema に `files:`（相対パス → 内容）を足し、pathlib で書き出す。
実行ビットは常に落とす。上限は 40 ファイル / 各 256KB。
あわせて生成器プロンプトに、許される語彙を正確に書いた。

**より正確な言い方**: 守るべきは「setup がプロセスを起動しないこと」ではなく
**「setup が書いたものが、下流で設定や指示として解釈されないこと」**。`files:` は前者を
保ったまま後者を破りうるので、予約名前空間の規則とセットでのみ成立する。

### C: detector とツールの突き合わせ

spec 生成後に、detector が言及するツールと子に渡すツールを突き合わせ、要求されているのに
渡していないものがあれば実行前に警告する。自動で付けない（既定 off は意図的な設計）。

## Alternatives Considered

**A2: project skill を測れないものとして拒否する** — 却下というより、Tier 1 の**既定の分岐**に
なった。`--load-target-skill` なしで本文を読み込まないのがまさにそれで、
「測れません」ではなく「呼べたかは測れます」に変わった。

**A3: SKILL.md だけでなくディレクトリごと写す** — 却下（現時点）。symlink・入れ子の
`.claude/`・hardlink・デバイスノード・実行ビットの検証が一式必要になる。ほとんどの skill は
1 ファイルなので、`references/` を持つ skill が Tier 2 で短く測れることを**見える制限**として
受け入れ、黙った穴を作らない方を選んだ。

**A4: `--add-dir` で実 repo の skill ディレクトリを指す** — 却下。実 repo の中に自動承認された
Write / Edit の面を作り、untrusted と分類した文書の爆発半径に実 repo のパスを入れる。
しかも実測では発見は cwd / プロジェクトルート基準なので、**そもそも欠陥 A を直さない可能性が高い**。

**`files:` の宛先を拒否リストで制御する** — 却下。名前の集合は外部が所有し際限がない。
拡張子の許可リストも誤り（`.claude/settings.json` は `.json`、正当な `package.json` も `.json`）。
prefix を予約する形にした（ただし basename の列挙は残り、弱点として明記した）。

**`Unknown skill` を警告だけにする** — 却下。自動化は終了コードを読む。
読み込めないまま走ったシナリオは**失敗した測定**であって低いスコアではない。

## Consequences

**得るもの**

- project skill が測れるようになった（実測で `Unknown skill` が `Launching skill:` に変わった）
- 測定が成立していない run が、静かに数字を出さなくなった（除外 + 終了コード 1）
- sandbox に書けるものと書けないものが、位置ではなく**解釈上の重み**で決まるようになった
- フィクスチャが意図どおり実体化する

**払うもの**

- 予約 basename のリストは外部製品を追うので腐る。CLI 更新時の再確認が要る
- Tier 2 は `SKILL.md` 単体しか写さないので、`references/` に依存する skill は短く測れる
- `--load-target-skill` は untrusted な文書を無人エージェントへの指示にする。
  `--allow-bash` との併用は payload とインタープリタの両方を渡すので警告が出る

**残る宿題**

- 複数プロセスの `run.py` が同じ sandbox パスを共有しうる（`SANDBOX_BASE/run-<pid>/` で解ける）
- `SANDBOX_BASE` が `/tmp` にあり、そこに書ける者は dangling symlink を仕込める
- Tier 1 の `description` チャネルは狭められない（発見に必要）
- `unresolved` の検出は外部製品のエラー文言 `"Unknown skill"` に依存する。文言が変われば
  黙って発火しなくなる — 呼び出しの**成功**も数えているので完全な沈黙にはならないが、弱点

# ADR-0031: 無人の子セッションの封じ込めは `permissions.deny` で行う — `--allowedTools` はツールを外さない

## Status

accepted

## Date

2026-08-02

## Context

`skills/skill-comply` は、ユーザーが書いたとは限らない .md を読んで LLM にシナリオを
書かせ、それを別の `claude -p` の子に無人で実行させる。2026-07-25 の security scan
（F3/F4/F18）に対する緩和として、SKILL.md はこう記録していた:

> **子エージェントの Bash は既定 off。** `--allowedTools` は `-p` モードでは
> 「許可リスト + 自動承認」なので、Bash を渡すと対象ファイル経由で忍び込んだ指示が
> 無人で実行される。必要な spec でのみ `--allow-bash` を明示する

**この前提は偽だった。** 2026-08-02、A/B（測定の正しさ）の設計レビュー中に実測して判明した。

### 実測（Claude Code 2.1.220、空の sandbox、`.claude/` を一切置かない条件）

`claude --help` の記述:

- `--allowedTools` — "Comma or space-separated list of tool names to **allow**"
- `--disallowedTools` — "… tool names to **deny**"

つまり `--allowedTools` は**自動承認**リストであって、ツール集合の制限ではない。
載せなかったツールは消えない。

| 条件 | 結果 |
|---|---|
| `--allowedTools "Read,Glob,Grep"` | 子が Bash を呼び `uname -sr` が実行された（`Darwin 25.6.0`、2/2 回再現） |
| `+ --permission-mode manual` | 同じく実行された |
| `+ --permission-mode dontAsk` / `acceptEdits` | 同じく実行された |
| `+ --setting-sources project` | 同じく実行された |
| `--settings '{"permissions":{"deny":["Bash"]}}'` | `Bash exists but is not enabled in this context` |

`--setting-sources project` の行が対抗仮説を潰している。ユーザーの
`~/.claude/settings.json` には Bash 系の allow が 89 件あり `defaultMode: auto` なので
「子が user 設定を継承しているだけ」という説明があり得たが、probe に使った `uname` は
その allowlist に無く、継承を断っても結果は変わらない。

`permissions.allow` を空にしても継承分は消えない（deny は authoritative、allow は加算）。
skill の frontmatter `allowed-tools` も deny を上書きできない。

### 爆発半径は Bash だけではなかった

子の既定ツール集合は `Agent / Bash / Edit / Glob / Grep / Read / ReportFindings /
ScheduleWakeup / Skill / ToolSearch / Workflow / Write`。

- `Agent` / `Workflow` — **このコードが制御しないツール集合を持つサブエージェント**を生む。
  親で Bash を塞ぐだけでは封じ込めにならない
- `ToolSearch` — 遅延ツールを読み込む。子は user 設定の MCP サーバを継承するので、
  メール・ドライブ・カレンダー・ブラウザの面に到達しうる

実測で、`Agent` を塞がれた子は `Skill` にフォールバックして別の skill を起動しようとした。
塞ぐ側は消すツールを列挙するが、モデルは**残った面を探す**。

### 影響範囲

生成器の子（`generate_scenarios`）が最も悪い。`--allowedTools` すら渡しておらず、かつ
**監査対象文書の raw body** をプロンプトに埋め込んで受け取る。nonce による隔離は
プロンプト層の対策であり、ネットワークに出られるエージェントの前に置かれていた。

同じ誤解が harness の 3 箇所に複製されていた —
`skills/learned/claude-code-headless-automation.md`（「`--allowedTools` のホワイトリストで
足りる」）、`scheduled-tasks/README.md`、`scheduled-tasks/weekly-aeon-shopping/SKILL.md`。
後者 2 つは**実際に無人で走るタスク**の設計根拠になっている。

## Decision

**無人の子セッションの封じ込めは `--settings` の `permissions.deny` で行う。**
`--allowedTools` は「承認プロンプトで止まらないため」の自動承認リストとしてのみ使い、
保証に数えない。

skill-comply では `scripts/child_settings.py` を正本とし、4 種類すべての子
（シナリオ実行・spec 生成・シナリオ生成・分類）が同じ envelope を通る。
deny 対象は `Bash` / `Agent` / `Workflow` / `ToolSearch` / `ScheduleWakeup`。
`Read` / `Write` / `Edit` / `Glob` / `Grep` / `Skill` は残す
（`Skill` を外すと、測ろうとしている振る舞いそのものが測れなくなる）。

`--allow-bash` は deny から Bash を**外す**形で効かせる。allow に足す形では効かないため、
opt-in は減算で実装する。

**denylist が弱い形であることを明記して持つ。** これは外部製品が所有するツール集合を
列挙しており、Claude Code が新しい既定ツールを追加してもこのリストは知らない。
CLI 更新時に実測し直す前提で、その旨を `child_settings.py` の docstring と SKILL.md に書く。

## Alternatives Considered

**`--allowedTools` を絞り続ける** — 却下。実測のとおり効果がない。前提が偽だった以上、
同じ機構をより丁寧に使っても何も変わらない。

**`--permission-mode manual` で allowlist 化する** — 却下。manual / dontAsk / acceptEdits の
どれでも Bash は実行された。`--allowedTools` を制限に変える permission mode は見つからなかった。

**`--disallowedTools` フラグを使う** — 同等に効く（実測済み）。`--settings` を選んだのは、
生成器・分類器の子が既に `--settings` を渡しており（output style の固定）、
封じ込めを 1 つの機構に集約できるため。フラグを増やすより、既にある経路に載せる。

**`--setting-sources project` で user 設定の継承を断つ** — 単独では効かない（実測）。
かつシナリオ実行の子については**継承こそが測定対象**なので、断つこと自体が誤り
（ユーザーの実環境で skill が守られるかを測っている）。生成器・分類器は
output style だけ固定し、環境は継承させたまま deny で閉じる。

**Bash だけ deny する** — 却下。`Agent` / `Workflow` が制御外のサブエージェントを生み、
`ToolSearch` が MCP の面を開く。1 つ塞いだだけでは、モデルは残った面を探す（実測）。

## Consequences

**得るもの**

- `--allow-bash` が**初めて実際の opt-in として機能する**（実測: 既定で
  `No such tool available: Bash`、指定時のみ `Darwin 25.6.0`）
- 監査対象文書の raw body を受け取る生成器の子が、初めて envelope の内側に入った
- 封じ込めの定義が 1 ファイル（`child_settings.py`）に集約され、テストで固定された

**払うもの**

- denylist は外部の既定ツール集合を追う形なので、CLI 更新のたびに腐りうる。
  これは構造的な弱点で、明記して受け入れる以上の対処が無い
- `Agent` / `Workflow` を外したことで、サブエージェントを起動する skill の遵守は
  測れなくなる。必要になったら、その skill 専用に deny を緩める判断を別途行う

**残る宿題**

- `scheduled-tasks/weekly-aeon-shopping` の起動コマンドは別 repo にあり、そちらで
  deny を張れているかは未確認。この ADR の範囲外
- `<sandbox>/.claude/settings.json` の `hooks` が、信頼されていない workspace でも
  無言で実行されることを実測で確認した（同じファイルの `permissions.allow` は
  「信頼されていない」と明示的に拒否されるのに、`hooks` は走る）。子自身の Write は
  substrate が止めるが、**このツールの Python が書く場合は止まらない**。
  sandbox 内に `.claude/` を作る予定の設計（skill 複製・`files:`）は、
  この予約名前空間の規則を先に立ててから進める

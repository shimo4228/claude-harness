# ADR-0034: Review 実行確認を承認ゲートより前へ移す

## Status

superseded by [ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) — custom approval gate と
Stop 分岐を退役し、commit 面は implementation-chain を指す薄い reminder に縮退

当初の判断と停止理由は履歴として以下に残す。スクリプトの Stop 分岐とテストは ADR-0035 で削除した。
理由は、下の Consequences で**受け入れたコストとして自分で列挙した 2 項目**が導入当日に
顕在化したこと。「Stop は毎ターン終了時に発火する」「そのターンが作っていない変更でも鳴る」の
2 つで、新種の欠陥ではない。実測: **1 発火 827 bytes**（`rules/common/*.md` の常駐合計
26,239 bytes に対して 3.2%）が、ファイル変更を伴わない会話ターンに 3 連続で注入され、
**遵守 0/3**。同一文字列の反復なので 2 発目以降の情報量はゼロだった。block しない通知の失敗
モードは「無視が既定になること」だけで、それが 3 ターンで起きた。

**T-REVIEW-NOTICE-NOISE が想定した「数セッション運用した後」の実測が、初日に出た**と読むのが
正確である。同項目が測れるのはノイズ側だけで、便益側（承認のやり直しが減ったか）は Context に
書いたとおり照合先が存在しない。したがって本 ADR は、**撤退の根拠だけが観測可能で継続の根拠が
観測不能**という非対称を抱えたまま停止した。この非対称は代替案 (f) を却下した時点で構造的に
確定していたもので、停止の判断はその帰結である。

復帰条件は台帳 T-REVIEW-NOTICE-NOISE に移した（変更ファイル集合の指紋を持ち、前回発火時と
同じなら黙る抑制。代替案 (a) の `metrics/*.jsonl` 突合とは別物で、ログ相関・パス前方一致・
時刻窓を持たない）。commit 面（PreToolUse）は無効化していないため、ADR-0027 が要求する
Review 実行確認そのものは生きている。失ったのは順序だけである。

## Date

2026-08-02

## Context

1 つの作業に対してユーザーの承認が 2 回必要になる症状が報告された。とくに code-reviewer は
起動しているのに security-reviewer / codex-review が抜けるパターン。

```
実装 → 意図確認 (承認 1) → git commit 実行 → hook 発火 → review 漏れ発覚
     → review → 指摘の修正で差分が変わる → 承認 1 が無効化 → 意図確認 (承認 2)
```

**この症状に件数の計測はない。** 起点はユーザーの定性報告で、`rules/common/task-tracking.md` の
規律に従えば本来は台帳に接地させるべきところ、遡って数える手段がない (承認回数はどのログにも
残らない)。ADR-0027 / 0028 が持つような before/after の数値は本 ADR にはなく、**Stop 配線後に
直ったかの照合先も存在しない**。この欠落は自覚したうえで進める判断であり、効果測定は
台帳 T-REVIEW-NOTICE-NOISE の実測時にあわせて行う。既知の具体例は 1 件のみ ——
2026-07-29 に `~/MyAI_Lab/contemplative-agent` の `79d59b0` (ADR-0085 実装、27 files changed) を
review なしで commit した件で、`hooks/review-chain-notice.sh` のヘッダに導入契機として
記録されている (**この repo の ADR は 0034 までなので、「ADR-0085」は本 repo 内では引けない**)。

原因は規律ではなく**検出点と承認点の順序**にある。

- `hooks/review-chain-notice.sh` の `GIT_VERBS` alternation — 発火は
  `git commit｜revert｜merge` の PreToolUse のみ (行番号でなく記号名で指す。この ADR の
  実装自体が同ファイルを動かすため、行参照は書いた時点で腐る)
- `rules/common/human-gate.md`「1 作業 1 ゲート」の意図確認はその**前**（条項の出所は ADR-0019）

「1 作業 1 ゲート」は承認後に差分が変わらないことを前提にしている。ところがこの hook 自身が、
承認後に差分を変える契機になっていた。前提と機構が噛み合っておらず、遵守率を上げても直らない。

**分類ロジックは壊れていない。** 同 hook は変更ファイルを 3 区分 (code / behavior-shaping /
ADR) に分け、区分ごとに要る reviewer を名指しするメッセージを既に生成しており、
ADR-0028 由来の 16 ケースが `tests/review-chain-notice.bats` で固定されている。
間違っていたのは鳴るタイミングだけ。

### ADR-0028 の前提が失効している

ADR-0028:143-145 は block (exit 2) への昇格を却下し、その理由をこう書いていた ——
「`review を起動したか` は agent がファイル痕跡を残さないため機械検証できず、block すると
偽陽性で作業が止まる」。同時に「`codex-review` だけは `metrics/skill-usage.jsonl` に invoke が
残るので照合可能で、将来の強化余地として残す」としていた。

**前段の前提は現在は偽。** `hooks/log-agent-usage.sh` が PostToolUse (Task|Agent) で
`metrics/agent-usage.jsonl` に agent 名・repo・時刻を記録しており (調査時点で code-reviewer /
python-reviewer / swift-reviewer / security-reviewer / adr-reviewer の起動記録あり)、
skill 側とあわせれば reviewer ごとの起動済み判定は機械的にできる。0028 が「codex-review だけ」と
書いた範囲は agent 全体に広がっている。本 ADR の代替案 (a) はこの余地を評価したうえで、
別の理由 (順序と精度は別問題) で見送る判断である。

### Stop hook の出力チャネル

hook の「強さ」は exit code だけでは決まらず、**出力チャネルが独立した軸**として存在する。

| 出力 | 到達先 | 会話 |
|---|---|---|
| `exit 0` + stderr | debug log のみ。モデルにもユーザーにも届かない | 継続 |
| `exit 0` + `hookSpecificOutput.additionalContext` | モデルに system reminder として注入。ユーザーには非表示 | 継続 |
| `exit 0` + `decision: "block"` + `reason` | モデルに差し戻す | ターン終了を阻止 |
| `exit 2` + stderr | モデルに差し戻す (エラー扱い) | ターン終了を阻止 |

出典: `https://code.claude.com/docs/en/hooks` の exit code / hook output 節
(2026-08-02 に claude-code-guide agent 経由で参照)。

**Stop × `additionalContext` は本 ADR が初出のため、文書だけに頼らず実測した。** 本 ADR の
実装を配線した直後の同一セッションで、Stop hook の `additionalContext` がターン終了時に
system reminder としてモデルのコンテキストへ注入されることを 2 回観測した (2026-08-02)。
**再現手順**: 対象 hook を `settings.json` の `hooks.Stop` に配線し、未コミットのコード変更が
ある repo でセッションを回してターンを終える。注入されていれば次のターンの冒頭に
`<system-reminder>Stop hook additional context: ...` として現れる。届かない実装
(`exit 0` + stderr) との差はこの 1 点で判別できる。
bats が固定できるのは hook が吐く JSON の形までで、harness が受け取る証拠にはならないため、
この実測が Decision の成立条件になっている。文書上の前提が偽だった前例 (ADR-0031、および
`skills/learned/documented-invariant-lint-gates.md` の「うち 2 件は当該 repo の文書の記述が
偽だった」) を踏まえた確認。

`exit 0` + stderr は「警告」ではなく実質**無音**だった。`settings.json` の Stop には本変更前から
**3 本** (`hooks/driftcheck.sh` / `hooks/search-first-verdict-check.sh` /
`hooks/dotclaude-dirty-check.sh`) が載っており、いずれもこの形で書かれている
(`search-first-verdict-check.sh` は薄い wrapper で、出力の実体は
`scripts/hooks/search-first-verdict-check.py:125`)。`rules/common/planning.md` が
「Stop hook が Verdict の存在を検査する」と書いている advisory 層は、検査結果が誰にも
届いていない。ただし `search-first-verdict-check.sh` には `SEARCH_FIRST_VERDICT_ENFORCE=1` で
exit 2 する経路があり、**無音なのは既定モードに限る**。これは本 ADR とは独立した欠陥で、
台帳 T-STOP-HOOK-CHANNEL として分離した。

## Decision

**同じ `hooks/review-chain-notice.sh` を Stop イベントにも配線する。** 新規 hook は作らない。

- 分類の 3 区分 (`CODE_RE` / `SHAPE_RE` / `ADR_RE`) とその下の reviewer 名指し文は
  **両イベントで共有し、無改変**。イベントで分岐するのは「どの repo の何を作業中と見なすか」と
  **メッセージ冒頭**のみ (Stop 版は commit でなく承認ゲートを指し、さらに
  「まだ実装の途中なら無視してよい」という PreToolUse 版に無い行動指示を持つ。毎ターン
  発火する面なので、この免責が無いと実装途中の通知が誤読される。
  `tests/review-chain-notice.bats` の "message points at the approval gate" が固定)
- 出力は `exit 0` + `additionalContext`。**ブロックしない** — 実装途中のターン終了でも鳴るが、
  無視の判断はモデル側が持つ。ユーザーの視線コストはゼロ (ADR-0028 の判明事項)
- PreToolUse 側は**残す**。Stop を取りこぼした場合の最後の砦であり、置き換えではなく二重化

対象とする変更集合はイベントで意図的に非対称にする。

| | PreToolUse | Stop |
|---|---|---|
| 見るもの | commit 対象 (staged、空なら tracked working tree) | 今の作業状態 (staged ∪ unstaged ∪ 未追跡) |
| 未追跡ファイル | 含めない | **含める** |
| メッセージ冒頭 | 「commit 前の Review 実行確認」 | 「意図確認を求める前に起動すること」 |

Stop が未追跡を含めるのは、まだ `add` していない新規実装こそ review 前の成果物だから。
PreToolUse が含めないのは、`commit -a` も未追跡は含めないため、コミットされないファイルを
理由に警告することになるから。この非対称は将来バグと読まれうるので、両方向をテストで固定した。

**収集は必ず repo root へ `cd` してから行う。** `git ls-files --others` は cwd 配下しか見ず、
しかもパスを cwd 相対で返す。セッションの cwd がサブディレクトリのとき (a) 別階層の未追跡を
落とし、(b) 返るパスが `hooks/x.sh` でなく `x.sh` になって行頭固定の `SHAPE_RE` / `ADR_RE` に
一致しなくなる。**(b) の方が重い** — 同じ変更なのに control plane / ADR の判定が黙って消える。
cwd を `repo/hooks` にして未追跡の `hooks/newhook.sh` を置くと behavior-shaping 判定が
消失することを実測した (codex-review の指摘は (a) のみで、検証の過程で (b) を発見)。
サブディレクトリで走るのは常態なので理論上の穴ではない。

**配線先は `settings.json` の `hooks.Stop` 配列だが、このファイルは `.gitignore:64` により
追跡外。** 決定の実体はコミットにも版管理にも入らないため、後日「本当に適用されたか」は
git から検証できない。追跡可能な記録は `hooks/README.md` の Stop 表のみ。

### git 呼び出しは必ず設定を無効化した配列を経由する

Stop 配線は「commit した時だけ git を走らせる」から「**そのディレクトリにセッションがあるだけで
毎ターン自動**」へ到達条件を上げる。hook はパーミッションプロンプトを経ず Bash サンドボックスの
外で走るため、これは信頼境界に直接効く。実測で塞いだ 2 件:

| 設定 | 何が起きるか | 実測 |
|---|---|---|
| `core.fsmonitor` | repo 内の `.git/config` に書ける外部プログラムのパス。`git diff` / `git ls-files` が起動する = **任意コード実行** | 素の `ls-files` で 2 回、hook 1 回で **6 回** 起動。`-c core.fsmonitor=` で 0 回 |
| `core.quotePath` (既定 true) | 非 ASCII パスを `"..\346\227.."` と引用・8 進エスケープして返す。行頭/行末固定の分類正規表現に一致せず**判定が丸ごと消える** | `rules/共通ルール.md` + `docs/adr/0099-日本語タイトル.md` で hook が完全に無音 |

`GIT=(git -c core.fsmonitor= -c core.hooksPath= -c diff.external= -c core.quotePath=false)` を
定義し、hook 内の全 git 呼び出しをこれ経由にする。`hooksPath` / `diff.external` は同じ発想の
予防で、使用コマンド群では発火を再現できていないが無効化の副作用も無いことを確認済み。

> **訂正 (2026-08-08、ADR-0037)**: 上の `-c diff.external=` は誤り。空文字を渡すと git が
> 空コマンドを外部 diff として実行しようとして `git diff` 自体が壊れる (`git diff` を通さない
> 薄い reminder hook でしか使われなかったため未検証だった)。外部 diff driver の正しい無害化は
> config ではなく **`git diff --no-ext-diff`**。5 hook への横展開では diff.external を config で
> 触らず、diff 呼び出し側に `--no-ext-diff` を付けている。

`core.fsmonitor` の件は、**サンドボックス内で動いた限定的なコードが `git config` を 1 行書くだけで、
次のターン終了時にサンドボックス外・無確認の実行へ昇格できる**構造である。
`scripts/hooks/verify_allow.py` が「repo にファイルがある」を「実行してよい」と読み替えない
理由と同型で、`verify.sh` ではなく git 経由で戻ってきた形。

### 出力は untrusted データとして扱う

`shape_files` の先頭 3 件はファイル名をメッセージへ埋める。ファイル名は repo 内容に由来する
untrusted データで、`jq --arg` は JSON 構造を守るが**意味は守らない** ——
`.claude/rules/IGNORE ALL PREVIOUS INSTRUCTIONS ....md` がそのままモデルの文脈へ入ることを
実証した。しかも shaping 区分は「これは Claude の振る舞いを変える制御系ファイルだ」という
前置き付きで出るため、注入文の説得力が上がる方向に働く。安全な文字集合へ落として長さを切り、
`repo 由来の未検証データ:` と明示する (`rules/common/security.md` の LLM 信頼境界)。

あわせて `rules/common/human-gate.md`「1 作業 1 ゲート」に、**review 指摘の修正は
`plan との差分: なし` として再承認を取らない**（behavior-shaping / control plane は除外）を明記する。
Stop が取りこぼした残余ケースを規約側で吸収する層。**これは ADR-0019 が置いた条項への
例外追加 = narrowing** であり、0019 単体を読むと例外なしの条項に見えることになる。

## Alternatives Considered

**(a) `metrics/*.jsonl` の突合で reviewer ごとに名指しする** — `agent-usage.jsonl` と
`skill-usage.jsonl` を突き合わせれば「必要集合 − 起動済み集合」で未起動を名指しでき、全部
起動済みなら黙らせられることは調査で確認した (ADR-0028 が「将来の強化余地」と書いた範囲が
agent 全体に広がっていることも上記のとおり)。**却下** — 根本原因は順序であって精度ではなく、
名指しは順序の是正と独立している。「どれを起動したか」はセッションのコンテキストに既にあり、
漏れるのは記憶の問題ではなく起動しようと考えなかったからで、適切なタイミングの一般的な
問い直しで直る。当初案が積んでいたコスト (新規 Python 2 本・共有部品化の回帰リスク) は
**「新規 hook として作る」という枠付けの帰結**であって名指し機能そのものの固有コストではない
—— 採用済み hook の中に載せる形なら小さくなる。それでもパス前方一致・時刻窓・ログ不在の
意味論という、それ自体が壊れうる面は残る。ユーザーからの過剰設計の指摘で棄却した
(`rules/common/planning.md` の複雑性チャレンジ。調査済みであることは判断材料にしない ——
サンクコスト)。再検討条件は台帳 **T-REVIEW-NOTICE-NOISE** に記録した。

**(b) 変更内容を見ず「必要な review はしたか」とだけ送る** — 最小の実装で順序は直る。
**部分採用** — 順序の是正という本質はこの案が正しく、本 ADR はこれを採っている。分類まで
自作しないのも同じ理由。両者の差は具体性だけではなく **網羅性 × ノイズ**にある: 採用案は
ADR-0028 の除外集合 (`.notes/` / adr 以外の `docs/` / `scheduled-tasks/`) を継承するため
**その 3 つしか触っていないターンでは無音**になり、(b) は鳴る。逆に (b) は変更ゼロのターンでも
鳴る。0028 の実測ではこの除外集合は 82 commit 中 6 件なので、取りこぼし側の差は小さい。

**(c) `decision: "block"` でターン終了を阻止する** — 確実に効く。**却下** — 実装途中の停止
(進捗報告・質問) まで止める。`additionalContext` がブロックせずモデルに届くことを実測した
以上、強制力を上げる前にまず届かせるべき。**ADR-0028:143 も block を却下している**が、その
理由 (機械検証不能) は上記のとおり失効しており、本 ADR は**別の理由で同じ結論**に至っている
—— 0028 の論拠をそのまま引き継いではいない。効かない実測が出てから昇格する余地は残す。

**(d) `rules/common/planning.md` の Verify ステップの記述を強めるだけ** — **却下**。
規律層は今まさに失敗している層で、同じ層に足しても検出点は動かない
(`rules/common/hooks.md`: 確実に効かせたいものは hooks)。

**(e) PreToolUse のまま検出精度だけ上げる** — **却下**。漏れの発覚が早くなっても承認より
後ろである限り、承認のやり直しは発生する。順序が直らない。

**(f) 何もせず、まず症状を計測する** — ADR-0028:159 が実際に取った選択 (機構を足さず観測を
待つ)。本 ADR は「件数の計測はない / 直ったかの照合先も存在しない」と自認している以上、
最も自然な対抗案。**却下** — 承認回数はどのログにも残らないため、**待っても baseline は
得られない**。0028 が待てたのは commit という計測可能な単位があったからで、ここには対応する
単位が無い。計測可能にすること自体が別の機構 (承認イベントの記録) を要し、それは本 ADR より
重い。代わりに、機構を入れたうえで「うるさいか / 効かないか」という**入れた後にしか測れない量**を
T-REVIEW-NOTICE-NOISE で測る順序にした。この選択は「効果の証明を先送りした」ことを意味し、
Consequences の 1 行目に反映している。

## Consequences

**容易になること**

- review 漏れが承認より前に見つかるので、1 作業 1 承認に戻る (効果は未測定 —— Context 参照)
- 分類・メッセージの正本が 1 箇所のまま。2 イベントに配線しても正規表現の複製が発生せず、
  `hooks/_git-target-common.sh` のヘッダが実証した「複製は drift する」を繰り返さない
- 実装コストが配線と分岐のみ。新しく壊れうる面を増やしていない
- `additionalContext` の Stop での到達性が実測できたので、T-STOP-HOOK-CHANNEL の 3 本を
  直すときの参照実装になる

**困難になること・受け入れたコスト**

- **Stop は毎ターン終了時に発火する。** 未コミットの変更がある長いセッションでは、
  同じ通知がターンごとにモデルのコンテキストへ注入される。抑制機構は持たない
  (代替案 (a) を棄却した帰結)。台帳 T-REVIEW-NOTICE-NOISE で実測してから再判断する
- **そのターンが作っていない変更でも鳴る。** Stop は「今の作業状態」を見るので、別セッションで
  溜まった未コミット変更 (`hooks/dotclaude-dirty-check.sh` が存在する理由がまさにこれ) に対しても
  review を要求する。反復ノイズとは別クラスの偽陽性で、会話と無関係な変更ほど判断コストが高い
- **commit するターンでは同じ趣旨が二重注入される** (Stop で 1 回、PreToolUse で 1 回)。
  二重化の裏面であり、取りこぼし耐性と引き換えに受け入れたコスト
- **`human-gate.md` の例外は人間の監督面を実際に狭める。** 承認後の実装コード差分が、
  エージェント自身の「これは review 指摘の修正だ」という分類だけで動きうる。誤分類の検出手段は
  現状ない。一方でこの例外は behavior-shaping / control plane を除外するため、**この repo では
  大半の変更に適用されない** (0028 実測: 82 commit 中 54 件はコードを 1 件も含まない) ——
  症状が起きた当の場所で吸収層がほぼ不活性である、という非対称も記録しておく
- **「必要な reviewer」は構造的な下限にすぎない。** task 種別 (feat / fix) は hook から
  見えないので、codex-review や security-reviewer の要否の最終判断はモデルと人間に残る
  (`rules/common/patterns.md` の enumerate/decide seam —— 検出は code、採否は判断)
- **Claude Code の Bash tool を経由しない commit には依然介入できない** (ターミナル直打ち /
  IDE / 別 pane の CLI エージェント)。PreToolUse 側から引き継いだ限界で、本 ADR では埋めない
- **Stop 面はセッションの cwd の repo しか見ない。** 追加の作業ディレクトリを設定している場合や、
  プロジェクト repo のセッションから `~/.claude` を編集した場合、その変更は Stop 面から見えず
  PreToolUse でようやく鳴る —— **本 ADR が直そうとした順序がそこだけ残る**。同じ Stop 配列の
  `hooks/dotclaude-dirty-check.sh` はこの理由で cwd を無視して `~/.claude` を無条件検査する
  設計になっているが、本 hook を同型にすると 2 repo 分のメッセージ結合が要るので見送った
  (2026-08-02 code-reviewer の MEDIUM。埋めずに明記を選択)
- **未追跡を含めたことでファイル件数に上限が無くなった。** `.gitignore` が整う前の依存ツリー
  (`node_modules` 等) があると件数がそのまま出る。メッセージ長は先頭 3 件 + 件数表示で
  有界なのでコンテキスト消費は問題ないが、明らかに誤った件数が毎ターン入る
  (2026-08-02 code-reviewer の実測: 未追跡 12,000 件で件数がそのまま出力、所要 0.23 秒。
  `~/.claude` では 0.10-0.12 秒。いずれも同レビューの計測で、本 repo に再現スクリプトは残していない)
- **hook 自身が「黙って無音になる」失敗モードを 2 つ持っていた** (SIGPIPE / 非 ASCII パス)。
  どちらも決定論ゲートが全 PASS でも起き、修正済みだが**この層は自分自身を検査できない** ——
  ゲートの故障を検出する上位層は存在しない。回帰テストで固定するのが唯一の防壁
- **同じクラスの欠陥が commit 面の 5 hook に残ったままになった** —— **2026-08-08 に横展開完了**。
  本 ADR の調査が `core.fsmonitor` と SIGPIPE を発見したが、当時修正したのは本 hook だけで、
  `secret-scan-precommit.sh` / `verify-precommit.sh` / `bandit-precommit.sh` /
  `ruff-format-precommit.sh` / `harness-lint-precommit.sh` は未対応だった
  (台帳 T-GIT-HOSTILE-CONFIG / T-SIGPIPE-HEAD-PIPE)。ADR を claude-harness へ公開する
  前提作業として、この 5 本すべてに `core.fsmonitor` / `core.hooksPath` 無効化と
  `git diff --no-ext-diff` を適用し、ruff-format の `head` パイプに `|| true` を付けた。
  無害化は `-c diff.external=` (空 config は git が空コマンドを実行しようとして diff 自体を
  壊す —— 本 ADR が当初提案した GIT 配列の誤り。read-only 検査 hook では未検証だった) ではなく
  **diff 呼び出し側の `--no-ext-diff`** で行う。secret-scan の回帰テストに敵対的 diff.external を
  固定 (実行されず・かつ検出を鈍らせない、の両面)。**`rules/common/security.md` の
  Security Response Protocol 5「コードベース全体で同種の問題を洗う」はこれで完了**。詳細は
  [ADR-0037](0037-publish-harness-adrs-and-remediate-git-hostile-config.md)
- **untrusted 化が、同じ ADR で直した検出を部分的に打ち消す。** `tr -c 'A-Za-z0-9._/\n-' '?'` は
  非 ASCII を 1 バイトずつ `?` に潰すため、`core.quotePath=false` で検出できるようにした
  `rules/共通ルール.md` は `rules/?????????.md` として届く。80 文字の切り詰めも同様に情報を落とす。
  **検出はされるがメッセージ上でファイルを特定できない**という形で、2 つの修正が互いに削り合っている。
  区分と件数は正しく伝わるので検出の目的は満たすが、名前による特定は失われた
- 変更集合の非対称 (未追跡を Stop だけ含める) は説明が要る分だけ理解コストを足す。
  テストは hook の挙動を固定するが読者の誤読は防がないので、緩和の主役は hook ヘッダと
  `hooks/README.md` の注記

## References

- [ADR-0019](0019-human-gate-layer.md) —— 「1 作業 1 ゲート」条項の出所 (:195)。
  本 ADR の `human-gate.md` 改修はこれへの**例外追加 (narrowing)**
- [ADR-0027](0027-restore-review-execution-check-to-verify-gate.md) —— Review 実行確認を
  rules へ復元した判断。本 hook の存在理由
- [ADR-0028](0028-review-notice-full-scope-and-adr-reviewer.md) —— 3 区分・閾値撤廃・
  「additionalContext は人間に非表示」の出所。:143-145 の block 却下理由 (機械検証不能) を
  **前提失効として上書き**し、同行の「codex-review だけ照合可能」の範囲も更新する
- [ADR-0031](0031-child-permission-envelope-via-permissions-deny.md) —— 文書上の前提が
  実測で偽だった前例。本 ADR が Stop × additionalContext を実測した理由
- `https://code.claude.com/docs/en/hooks` —— hook の exit code / 出力チャネル (2026-08-02 参照)
- 台帳 [T-STOP-HOOK-CHANNEL / T-REVIEW-NOTICE-NOISE / T-GIT-HOSTILE-CONFIG /
  T-SIGPIPE-HEAD-PIPE](../../.notes/TASKS.md) —— 後ろ 2 件は本 ADR の調査が生んだ
  残余リスク (同型欠陥が commit 面の 6 hook に未修正で残る)

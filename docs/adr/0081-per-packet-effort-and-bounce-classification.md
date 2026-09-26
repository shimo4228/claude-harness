# ADR-0081: build の effort を packet ごとに選び、cloud へは `/effort` で適用し、bounce の分類で 1 段上げる

## Status

accepted — [ADR-0075](./0075-cloud-session-as-default-build-executor.md) の cloud effort の記述（high 固定・
medium 化は未決）と [ADR-0076](./0076-build-proposals-with-reproducer-and-opus-5-5-packet-rules.md) の
「cloud dispatch で `--model` / `--effort` を固定する」未決のうち effort の側を決める（部分的に弱める。注記は
両 ADR 側）

## Date

2026-09-26

## Context

- 記事 "Using Claude Code: Spending your effort"（https://claude.dev/blog/spending-your-effort/、2026-09-25、
  判断役が 2026-09-26 に一次で通読）: effort が大きく減らすのは見落とし系の失敗で、Fable 5.1 を low→max に
  したとき missed a case 59→24、bug its tests missed 40→14。読み違い系の減りは小さいか逆向き — made the
  wrong call 133→107、picked the wrong reading は 25→47 と増えた。段階は low / medium / high / xhigh / max。
  記事の推奨ループは interview → low で実装 → gist review → high で検証。数値は Fable 5.1 のもので、build 役の
  Opus 5.5（ADR-0076）に同じ傾向が出るかは測っていない。
- probe（2026-09-26、private の claude-config repo、CLI 2.1.283、session_01KYbC7mNxFZ8KN6kWevZpU6。証拠は
  private repo の session と判断役の画面にあり、外部の読者は下のコマンドの再現でしか確かめられない）:
  1. `claude --cloud "<prompt>" --ref main --effort low` で作った session の中は env `CLAUDE_EFFORT=medium`、
     system context `reasoning_effort: 10`。作成時の `--effort` は cloud session へ転送されなかった。既定は
     medium で、ADR-0075 が 2026-09-24 に実測として書いた「high」と食い違う — 2 日で 2 つの実測が割れたので、
     cloud の既定はサーバ側で動く値として扱う。
  2. 同じ session へ `claude -p "/effort high" --cloud <id>` を送ると slash command として処理され
     （"Set effort level to high (this session only)"）、次の turn で `CLAUDE_EFFORT=high`・
     `reasoning_effort: 15`。作成後の `/effort` 送信は効く。
  3. 未確認: 作成時の最初のメッセージを `/effort <level>` にしたとき slash command として処理されるか。
- 著者の決定（2026-09-26、本 ADR の起点）: effort は judge が packet ごとに「端のケースの密度」で表から選ぶ。
  local の medium 試行（2026-08-29〜、Opus 5 の build、著者の auto-memory が記録）について、著者は bounce
  増の体感が無いとしている（件数ではなく印象）。

## Decision

1. `scripts/cloud-dispatch.sh` が `--effort <low|medium|high|xhigh|max>` を受ける。5 段の外の値と値の欠落は
   usage で exit 64。`--effort` 指定時の起動を 2 段にする: (a) `claude --cloud "/effort <level>" --ref <ref>` で
   session を作る（env var・pty・作成行の検出は既存のまま）、(b) 得た session id を `^session_[A-Za-z0-9]+$` で
   検証し、`claude -p "<packet 本文>" --cloud <id> --output-format json` で packet を送り、出力に `"ok":true` が
   無いか 2 分（1 段目と同じ上限）で戻らなければ、session URL と CLI 出力を stderr に出して exit 2（jsonl には
   書かない）。`--effort` 無しは packet が
   最初のメッセージの 1 段起動のまま、dry-run 出力も変えない。jsonl 行に `"effort":"<level|default>"` を足し、
   `--dry-run` は 2 段の起動行を出す。packet 本文の先頭が `-` のときは両経路とも exit 1 で止める（argv で
   option として読まれるため）。(a) の最初のメッセージを `/effort` にするのは、session の作成に最初の
   メッセージが要り、それを `/effort` にすれば CLI 呼び出しが 2 回で済むから — probe 3 が未確認なので、
   適用されたかは build の Report の `Effort:` 行で読む（Decision 3）。
2. `tests/cloud-dispatch.bats` に、不正な effort の拒否・5 段の受理・dry-run の 2 行・`--effort` 無しの dry-run
   出力の完全一致・先頭 `-` の拒否と、`script` / `claude` の stub で起動経路（2 段目の送信先と argv、
   `"ok":false` で exit 2、jsonl の effort）を通すテストを置く。テストが対象にする script は worktree の
   ものにする（`$BATS_TEST_DIRNAME` 基準）。
3. `skills/task-triage/references/packet-template.md` に `Effort:` 行（judge が記入、理由 1 句）と選択表を置き、
   Report に `Effort:`（session が実際に走った effort）を置く。表の正本は packet-template で、下は本 ADR の
   日付時点の写し:

   | 状況 | effort |
   |---|---|
   | docs / 設定 / rulebook 型、仕様が細かい変更 | low |
   | 通常の feat | medium（未記入時の既定 = cloud の実測既定と同じ） |
   | brownfield の fix、parser / sanitizer、並行性、性能、security を動かす diff | high |
   | 無人で長く走り検証が厳しいもの | xhigh（max は著者が明示したときだけ） |

4. `skills/task-triage/SKILL.md`: §3 の起動行を `--effort <packet の Effort>` 付きにし（judge は Effort を常に
   記入して渡す — 未記入の既定はサーバ側で動くため）、local の起動での渡し方を置く — `spawn-session` は
   packet の前に `/effort <level>` を送り、`herdr agent read` で効いたのを見てから packet を送る。Agent tool と
   Workflow の `agent()` の呼び出しは effort を取らないので、その build は
   harness が与える effort で走り（未測定、Report の `Effort:` が読み値）、measurement / read-only /
   docs-only の packet だけがそれを受け、それ以外は `spawn-session` へ。§4 の bounce に分類 1 語を置く —
   **見落とし**（端ケース・テスト漏れ）は同じ session へ `/effort <1 段上>` を送ってから差し戻し文（上限は
   xhigh、max は著者の明示だけ。`Agent` の build は上げられないので同じ effort で差し戻し、その旨を記録）/
   **読み違い**（要件誤読・方針違い）は effort を上げず差し戻し文で仕様を直す / **gate・rebase** は記録するが
   Review-when の数から外す。§5 の digest で build ごとに `effort / bounce 有無 / 分類` を 1 行に記録する。
   effort は packet の `Effort:` → Report の `Effort:`（見落としで上げたら `medium→high` の形）。根拠として
   Context の記事の数値を §4 に 1 行置く。

## Review-when

- build 20 本分の build 行（Decision 4、`~/.claude/logs/effort-outcomes.jsonl`）で、見落とし分類の bounce のうち packet の effort が low /
  medium だった build の割合が、20 本全体でその 2 段が占める割合を上回っていれば表を 1 段上げ、上回らなければ
  維持する。数えるのは packet の `Effort:`（上げる前の値）。固定するもの: packet-template の表、§4 の分類
  3 語、分類する者（triage session の判断役）。どれかを変えたら数え直す。
- CLI が作成時の `--effort` を cloud session へ転送するようになったら（CLI changelog か probe 1 の再実行で確認）、
  2 段起動を `--cloud … --effort` の 1 段へ戻す。probe 3 が「slash command として処理されない」と出たら
  （最初の `--effort` 付き dispatch の Report の `Effort:` 行で分かる）、作成後に `-p "/effort <level>"` を
  別送してから packet を送る 3 段へ直す。
- 次の Opus / Fable のリリースか、公式の effort docs の更新があったら、表と分類の根拠（Context の記事の数値）を
  読み直す。

## Alternatives Considered

### 何もしない — 全 build を cloud の既定のまま走らせ、effort は記録だけする

却下: probe 1 の既定（medium）は 2 日前の実測（high）と割れていて、既定に任せると build の effort が
サーバ側の変更で黙って動く。記事の数値では、見落とし系は effort で大きく減るので、端のケースが密な diff に
effort を足す打ち手を捨てる理由が無い。

### 作成時に `--effort` を渡すだけ（1 段起動のまま）

却下: probe 1 で、作成時の `--effort` は cloud session に届かず medium で走った。フラグを足しても挙動は
変わらず、jsonl の記録だけが実態と食い違う。

### 作成後に `-p "/effort"` を別送してから packet を送る 3 段起動

probe で確かめた手順だけで組める形。却下（現時点）: CLI 呼び出しが 1 回増え、作成時の最初のメッセージに
何を置くかを別に決める必要がある。未決 — 再訪条件: probe 3 が否定されたとき（Review-when 2）。

### 種別（feat / fix / docs）で effort を固定する

却下（著者決定）: 同じ fix でも brownfield の parser と typo では端のケースの密度が違う。記事の数値は
失敗の種類（見落とし / 読み違い）で分かれていて、種別では分かれていない。

### high 固定 / 原則 low

却下（著者決定）: high 固定は、端のケースが少ない docs 型の packet にも high の費用を払い、読み違いは減らさない
（記事では picked the wrong reading が low→max で 25→47 に増えた）。原則 low は記事の推奨ループ（low 実装 →
high 検証）に近いが、この loop で high の検証段に当たるものを置くかは本 ADR では決めない — 未決 — 再訪条件:
Review-when 1 の 20 本で low の build に見落とし分類の bounce が出なかったとき。

### effort を固定した build 用の agent 定義を置く

agent 定義の frontmatter は `effort:` を持てる（`agents/prompt-forager.md` が `effort: low`）。`Agent` の build
に effort を渡す経路になりうる。未決 — 再訪条件: `Agent` の build の Report で `Effort:` が packet の値と
ずれる例が出たとき。

## Consequences

### Positive

- probe 3 が成り立てば、packet の effort が cloud session に適用される。成り立たない場合も、Report の
  `Effort:` 行が食い違いを示す（jsonl の `effort` は指定値で、実際に走った値ではない）。
- jsonl と digest に effort が残り、Review-when の 20 本を数える材料になる。
- 差し戻しの種類で打ち手が分かれる — 見落としには effort、読み違いには仕様の文面。

### Negative

- `--effort` 付きの dispatch は CLI 呼び出しが 2 回になり、2 段目の失敗で「`/effort` だけ受けた session」が
  残る（stderr に URL が出るので判断役が閉じる）。
- `claude -p --cloud <id>` が packet の turn の終わりまで戻らない場合（未確認）、script は 2 分で打ち切って
  exit 2 を返し、build は走っているのに jsonl に行が残らない。exit 2 でも packet が届いている可能性がある
  （stderr の文面がその旨を言う）。判断役は同じ task を出し直す前に、stderr の session URL で session の中身を
  確かめる。戻らないのが常態なら、2 段目の成否判定を再設計する（Review-when 2 と同じ機会）。
- ほかに未確認のまま実装した点: probe 3、`--output-format json` の `ok` の書式（script は空白を許す正規表現で
  読む）。実起動の確認は merge 後に判断役が行う。
- digest は triage session の返信で残らないので、build 行は判断役が §5 で
  `~/.claude/logs/effort-outcomes.jsonl` にも 1 行ずつ追記する（著者決定 2026-09-26）。Review-when 1 はこの
  ファイルを数える。追記は判断役の手順で機械の強制は無いので、行が 0 本のまま cycle が進んだら計器の停止を疑う。
- `Agent` の build は packet ごとの effort を持てないので、effort を指定する local build は `spawn-session`
  に寄る。

### Neutral

- 記事の数値は本 ADR と `skills/task-triage/SKILL.md` §4 の 2 か所に、表は本 ADR（日付時点の写し）と
  packet-template（正本）の 2 か所に載る。記事が更新されたら数値を両方直し、表を変えたら packet-template を
  直して Review-when 1 を数え直す。
- 戻すときは本 commit を revert する。`--effort` を渡さなければ dispatch は変更前と同じ 1 段起動で動く。

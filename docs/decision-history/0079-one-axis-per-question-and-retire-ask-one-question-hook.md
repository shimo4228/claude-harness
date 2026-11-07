# ADR-0079: 問いの規律を数から観点へ移し、ask-one-question hook を退役する

## Status

accepted — [ADR-0073](./0073-signal-first-as-output-style-and-one-question-gate.md) の Decision 1（style の
「判断は 1 メッセージに 1 つ / AskUserQuestion は `questions` 1 件」の項）と Decision 2（hook）を覆す
（部分的に弱める。注記は ADR-0073 側）

## Date

2026-09-25

## Context

- ADR-0073（2026-09-19）は著者の症状「一度に複数のことを聞いてくることがあるが、あれを 1 番やめてほしい」を
  問いの**数**として読み、style に「判断は 1 メッセージに 1 つ」を置き、`hooks/ask-one-question.sh` で
  AskUserQuestion の `questions` 2 件以上を block した。
- 著者の訂正（2026-09-25）:「AskuserQuestion を複数するのはいいよ。AskuserQuestion の中に複数の観点が混ざるの
  が嫌だった」。実例は同じ session（2026-09-25、ADR-0076 / ADR-0078 を起票した session）の、5 項目や 2 観点を
  1 つの yes/no に束ねた問い（mondo の改修 packet 1〜5 の GO、ADR-0076 の decision packet の失効条件と却下理由を
  一括した GO）で、どちらも `questions` 1 件 — hook を通っていた。
- hook の計測ログ（`~/.claude/metrics/ask-one-question.jsonl`、gitignore 下、2026-09-19〜09-24 UTC）は 111 呼び出し
  中 block 3 件（問い数 2・2・3）、問い 1 件の呼び出しが 108 件。matcher は効いていたが、止めていたのは著者が許す形（複数の問い）で、嫌う形（1 問への観点の
  混合）は件数では見えない。
- 観点の混合は意味の判定で、ADR-0073 Decision 3 自身が、散文の中の複数質問は regex に載らないので機械ゲートに
  しないとしている。
- 2026-09-25 の確認: `settings.json` に `outputStyle` が無く、Desktop の session の output style は `default` —
  ADR-0073 が入れた signal-first style は有効になっていなかった（settings.json は gitignore 下で、いつ外れたかは
  追えない）。実際に効いていたのは hook だけだった。著者は style を `default` のままにすることを選んだ。

## Decision

1. `output-styles/signal-first.md` の問いの項を「1 つの問いには観点を 1 つだけ載せる。確かめたい観点が
   複数なら、観点ごとに別の問いにして並べてよい。先の答えで消える問いは、答えを受けてから聞く。答えに依存
   しない作業は聞く前に進めておく」に置き換える。description も「問いは 1 問 1 観点」に合わせる。
2. `hooks/ask-one-question.sh` と `tests/ask-one-question.bats` を削除し、`settings.json` の PreToolUse
   （matcher `AskUserQuestion`）の配線と `hooks/README.md` の行を外す。手元の計測ログと `.gitignore` の行は
   残す（過去の log を誤って commit しないため）。
3. 観点の混合は機械ゲートにしない（ADR-0073 Decision 3 と同じ理由）。style が `default` の間、この規律を運ぶのは
   auto-memory の索引の 1 行（毎 session 読み込まれる）で、style の本文は有効にしたときのために直した形で残す。

## Review-when

- 著者が「1 つの問いに観点が混ざっていた」を 2 回観測したら（記録先: 本 ADR への注記、1 回ごとに 1 行）、
  規律の置き場（memory の 1 行か、style を有効にするか）を見直す。機械ゲートへは広げない。固定するもの:
  memory の該当行と style の問いの項の文面。変えたら数え直す。
- 著者が「問いが多すぎる」（数の側の不満）を観測したら、数の規律を style に戻すかを再訪する。

## Alternatives Considered

### style の文面だけ書き換え、hook は残す

却下: hook が 2 問以上を block し続け、書き換えた文面（複数の問いを並べてよい）と挙動が食い違う。

### hook を「観点の混合」を検出する形に作り替える

却下: 観点の数は `questions` の件数や選択肢の形からは決まらない。意味の判定を regex に載せると ADR-0073 が
退けた偽陽性の型になる。

### block だけ外し、hook を計測専用（exit 0 で 1 行記録）として残す

ADR-0073 が問いの頻度の初めての実測として置いたログを残す案（RFC-0026 もこのログを観測資産に挙げる）。却下: 数えて
いるのは問いの件数で、著者が気にする軸（1 問への観点の混合）ではない。既存の 111 行は手元に残る。数の側の不満が
出たら（Review-when 2）この形で戻す。

### 何もしない

却下: 著者が症状の読み違いを名指しし、仕組みが著者の許す形を止めていた。

## Consequences

### Positive

- 観点ごとに問いを分けて並べられる — 1 つの問いに束ねる動機（数の制限）が消える。
- 呼び出しごとに走っていた hook が 1 本減る。

### Negative

- 1 回の呼び出しに問いを並べすぎる挙動（schema 上は 4 問まで）は、著者の観測でしか止まらない。
- style が `default` の間、問いの規律は memory の 1 行だけが運ぶ — ADR-0073 の設計（style + hook）の両方が
  効いていない状態になる。
- ADR-0073 の Review-when のうち hook の計測に依存する 2 項は、測る対象が無くなる（注記は ADR-0073 側）。

### Neutral

- output style の枠と「結論を先頭に」の項は ADR-0073 のまま（style を有効にすれば効く）。ADR-0026 の注記が
  いう「1 問ゲート」は ADR-0073 の注記から辿る。
- 戻すときは本 commit を revert すれば hook・bats・style・README が戻る。`settings.json`（gitignore 下）の
  PreToolUse（matcher `AskUserQuestion`）の配線は手で戻す。

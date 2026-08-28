# ADR-0059: verify-precommit は承認失効（exit 71）の commit を止める — 未承認（exit 70）は従来どおり通す

## Status

accepted

## Date

2026-08-28

## Context

`hooks/verify-precommit.sh` は commit 境界で repo の `.claude/verify.sh` を実行するが、
人間が内容を読んで承認した版のハッシュ（`verify_allow.py` の台帳）に一致する場合のみ実行する
（2026-07-31 の security-reviewer CRITICAL への対処。守る対象は clone しただけの未信頼 repo）。

台帳側の拒否は 2 種類あり、hook はどちらも「stderr に再承認の案内を出して commit は通す」
同一扱いだった:

- **exit 70（未承認）** — 台帳にその repo が無い。clone 直後の外部 repo を含む
- **exit 71（内容不一致）** — 台帳に**載っている** repo のゲートが編集後に失効している

この同一扱いの実害を 2026-08-28 に観測した。contemplative-agent の verify.sh は
2026-08-06 の編集（ADR-0089 系 2 commit）以降ハッシュが失効し、**3 週間、毎 commit の
stderr に再承認の案内が出続けたまま誰も行動せず、その間ゲートは一度も走らなかった**。
編集したセッションが skill `verify-bootstrap` の「編集したら再承認」を落とし、以後の
セッションは案内を素通しした。発覚はユーザーが「commit 前の hook は生きているか」と
問うた偶然による。

70 と 71 は意味が正反対である。70 は「まだ誰も読んでいない」＝ block すると未承認 repo
での通常作業を全部塞ぐ。71 は「一度承認したゲートが眠っている」＝ 修復は人間の
`approve` 1 コマンドで、その repo の所有者は必ず居る。失効時挙動だけが fail-open なのは、
「眠っているゲートは、無いゲートより危険」という同 hook 自身の設計文言（exit 2 の扱い）
とも不整合だった。

## Decision

`verify-precommit.sh` の case を 70 と 71 に分岐する:

1. **exit 70（台帳に無い repo）** — 現行どおり。stderr に承認手順を案内して commit は通す
2. **exit 71（台帳に載っている repo の内容不一致）** — `{"decision": "block"}` で commit を
   止める。reason に「ゲートは実行されていない」「人間が verify.sh を確認して
   `verify_allow.py approve` する」「緊急時は `VERIFY_BYPASS=1`」を明記する。JSON は
   FAIL 経路と同じく python3 の json.dumps で全体を組み立てる（path 中の引用符での
   fail-open 防止、2026-07-31 code-reviewer MEDIUM と同根）
3. 回帰テスト 4 本を `tests/verify-precommit.bats` に追加（71 が block する / 案内文に
   approve が載る / ゲートは実行されない / 再承認で unblock されゲートが走る）

## Review-when

- 71 の block が正当な作業を月単位で繰り返し塞ぐ観測が出た時（例: verify.sh を頻繁に
  編集する repo での摩擦）— 猶予付き block（n 回目まで通知）等の再設計を検討
- `verify_allow.py` の exit code 体系が変わった時 — 70/71 の分岐前提が崩れる
- 承認操作が人間の 1 コマンドでなくなった時（承認 UI の変更等）— reason の案内文を追随

## Alternatives Considered

### 現状維持（71 も通知のみ）

却下: 3 週間の沈黙という実害を観測済み。通知チャネルは 15 回以上発火して一度も行動に
つながらなかった — 同じチャネルを続ける根拠がない。

### 70 も 71 も block する

却下: clone しただけの外部 repo・承認前の新規 repo で commit が全部止まる。承認を強要する
ゲートは bypass の常態化を招く（skill `verify-bootstrap` の「初日から block にすると回避の
作法が育つ」と同根）。

### 失効を検知する別の計器・定期監査を新設する

却下: 機構の新設。発火点は commit の瞬間で、そこには既に hook が立っている。既存 hook の
分岐 1 つで足りるものに新設物を積まない（ADR-0055 の計器却下と同じ姿勢）。

### 編集時に自動で再承認する

却下: 承認機構の意味の破壊。agent が verify.sh を書き換えて自動承認できるなら、hash pin は
「人間が読んだ版だけ走る」という信頼境界でなくなる。

## Consequences

### Positive

- 既知 repo のゲート失効が「3 週間の沈黙」から「次の commit で同日修理」に変わる
- 修復経路が reason に明記され、block を見たセッションがユーザーへ正しい 1 コマンドを渡せる
- 未承認 repo の作業フローは無変更

### Negative

- verify.sh を編集した直後の commit は、人間の approve を挟むまで止まる（意図された摩擦
  だが、編集→commit の連続作業に 1 手増える）
- `VERIFY_BYPASS=1` が失効時の抜け道として使われうる（従来からある逃げ道で、増えてはいない）

### Neutral / Follow-ups

- 実害の観測記録（3 週間の失効）はこの ADR の Context が正本
- contemplative-agent 側の再承認は 2026-08-28 に実施済み（台帳更新確認済み）

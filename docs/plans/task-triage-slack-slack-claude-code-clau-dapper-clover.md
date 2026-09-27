# task-triage: Slack 通知を短縮し、判断材料をセッション発話へ移す

## Context

無人 triage cycle は現在、判断 1 件ごとに 5 要素（background / what is at stake /
options / recommendation / cost-reversibility）のフル digest を Slack へ送る
（`skills/task-triage/SKILL.md:93-99`、`scripts/triage-tick.sh:67` の prompt）。
しかし著者は実際には Slack では答えず triage セッション（Remote Control）に戻って
判断する。詳細は `notify-slack.sh` の **Bash ツール引数**の中にしかなく、セッションの
発話には要約しか無いため、戻っても Slack を見ながらの判断になっていた。

grill-me インタビューで確定した設計（2026-08-30）:
- Slack は cycle 末尾 1 通のみ: `done — N decisions pending` + 各判断 1 行タイトル
  （生存信号の役割は維持。「いま戻る価値があるか」を電話で判断できる粒度）
- 判断材料の完全形は cycle 終了時の**発話本文**に全件書き切る
- 著者が戻って発話したら残件を 1問1答（AskUserQuestion）で自動開始。
  戻りの発話が既に答えを含む場合（例:「T002はdone」）は直接処理し残件だけ質問
- 退出時フォールバック無し（transcript は `--resume` で復帰可能、発生も稀）
- ファイル永続化無し（別セッションで判断しない — 著者確認済み）

## 変更対象（3 ファイル）

### 1. `scripts/triage-tick.sh` — prompt 文言（:61-67 付近）

現行の「判断ごとに notify-slack.sh 1 通（5 要素 body）」の指示を差し替える:

- 判断が必要な項目は Slack へ送らず、**cycle 終了時の応答本文**に 1 件ずつ
  5 要素（background / what is at stake / options / recommendation /
  cost-reversibility）で書き切る
- Slack は末尾 1 通のみ:
  `bash ~/.claude/scripts/notify-slack.sh "<repo> triage cycle done" "N decisions pending: 1) <一行タイトル> 2) <一行タイトル> …（0 件なら 0 decisions pending）"`
- 「人間が次に発話したら、その発話が含む答えを先に処理し、残る判断を
  AskUserQuestion で 1 問ずつ聞く」を prompt に追加
- 「Slack is one-way」の一文は維持

harness / CA 両方の plist が同じ tick script を呼ぶため、変更は両 repo に効く。

### 2. `skills/task-triage/SKILL.md` — §2 Digest（:85-104）と cycle-end 節（:196-198）

- :93-99 の無人 cycle フォーマットを上記と同じ形に書き換える
  （per-decision の Slack メッセージ形式を削除、末尾 1 通の形式を更新）
- 「digest の実体はセッションの発話本文。Slack にはタイトルだけ」を明記
- 戻ってきた人間への 1問1答開始規則（一括回答は直接処理）を §2 に追記
- :196-198 の cycle-end digest 内容（open before→after 等）は発話側に残す
- Cadence 節等に旧フォーマットへの言及があれば追随

### 3. `docs/adr/0045-triage-loop-launchd-tick-and-slack-digest.md` — 日付つき注記

新 ADR は立てない（可逆・アーキテクチャ不変。timer 外 / answers-in-session の
Decision 1 はそのまま）。akc-cycle の規約どおり削除でなく日付つき注記:

- Decision 3（:70-78）に注記: 2026-08-30、digest 本文は Slack からセッション発話へ
  移動。前提「Slack は人間が電話で読める判断材料を運ぶ唯一の out 経路」が実運用で
  崩れた（著者は常にセッションへ戻って判断。Remote Control でも発話は読める）
- Review-when #3（:106-108）の観測点を書き換え: 旧「同じ digest を Slack へ再送して
  いると気づく」→ 新「N decisions pending が 2 cycle 連続で減らない」
- ついで（同 ADR 内の既知 drift）: :83-84 の「土曜 08:03」を現行 plist
  （日曜 06:30 + --stocktake）に合わせて日付つきで訂正

## やらないこと

- 判断待ちのファイル永続化（.notes/ 等）— 著者が明示的に不要と判断
- 退出時の Slack フル digest フォールバック — 同上
- notify-slack.sh / notify.sh 本体の変更 — 送る内容が変わるだけ
- ADR-0045 の supersede（新 ADR）— 注記で足りる

## Verification

1. `bash scripts/triage-tick.sh ~/.claude triage-harness "triage harness" --stocktake --dry-run`
   相当で prompt 文言が新形式になっていることを確認（dry-run フラグの実装は :dry-run
   既存挙動に従う。無ければ prompt 変数を echo して目視）
2. SKILL.md と tick prompt の digest 指示が矛盾しないこと（grep で旧フォーマット
   `回答はこの triage セッション` の per-decision 形式が残っていないか確認）
3. 実地確認は次回の無人 cycle（日曜 06:30 harness / 水・土 triage-ca）:
   Slack が 1 通だけ来る・タイトル一覧がある・セッション発話に 5 要素詳細があること
4. commit 前に repo の verify gate（hooks 経由）が通ること

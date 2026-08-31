# Golden 出力（機械が parse する出力の凍結）

<!-- origin: shimo4228 -->

機械（hook / triage loop / judge）が parse する出力の**全形**をここに凍結する。
部分 assert（`[[ $output == *..* ]]`）は各 bats に残り、こちらは silent drift —
「テストは通るが、下流の parser が読む形が変わった」— を検知する層。

## 更新規約（更新反射の禁止）

golden の更新が正当なのは**そのタスクがその出力の変更を宣言しているときだけ**。
スコープ外の変更で golden が赤くなったら、それは修正対象ではなく**検知成功** —
golden を直さず事故として報告する。正本: skill implementation-chain の Doc Sync 行。

## 再生成

各 golden は対応する `tests/golden-*.bats` が実行するコマンドの出力そのもの。
再生成はテスト内のコマンドを同じ引数で実行してリダイレクトする（各 bats の
ヘッダに再生成コマンドを記載）。

## 意図的に凍結していないもの

- `claims.py ready` の claimed mark（`[claimed xxxx 3h]`）— `fmt_age` が現在時刻
  起点で非決定論。時刻注入口の追加は別タスク
- `claims.py open --oneline` の切り詰め挙動 — 同じく時刻依存
- task-triage の Slack digest — 生成 script が存在しない（skill 指示文のみ）
- LLM 生成 prose 全般 — 毎回変わるのが正常。凍結対象は決定論的な整形・契約層のみ

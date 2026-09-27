# レビュー実行確認を承認より前へ移す

## Context

### 解く問題

コミット時にレビューのかけ忘れに気づき、レビュー → 修正 → 再度コミット承認、と承認が
複数回になる。とくに code-reviewer は走らせているのに security-reviewer / codex-review が
抜けるパターンが多い。

### 根本原因

**レビュー実行確認が鳴る場所が、承認をもらう場所より後ろにある。**

- `hooks/review-chain-notice.sh:41` — 発火は `git commit` の PreToolUse
- `rules/common/human-gate.md`「1 作業 1 ゲート」— 意図確認はその**前**

結果として `実装 → 承認(1) → git commit → hook 発火 → 漏れ発覚 → レビュー → 修正で差分変化
→ 承認(1) が無効化 → 承認(2)`。「1 作業 1 ゲート」は承認後に差分が変わらないことを前提に
しているのに、hook 自身がその前提を破る契機になっている。

**壊れているのは分類ロジックではなく、発火タイミングだけ。** `review-chain-notice.sh` は
変更ファイルを 3 区分（code / behavior-shaping / ADR）に分類し、区分ごとに要るレビュアーを
名指しするメッセージを既に生成しており、`tests/review-chain-notice.bats` で固定されている。

### 前提の確認（調査済み）

Stop hook は `hookSpecificOutput.additionalContext` を持つ。exit 0 + JSON でモデルの
コンテキストに system reminder として注入され、**会話はブロックされない**。ユーザーの
視線コストはゼロ。`review-chain-notice.sh` が PreToolUse で使っているのと同じ経路。

（`exit 0` + stderr は debug log にしか行かない。これは既存の別 hook 2 本の欠陥でもある
 → 末尾「別件」）

### 意図する結果

承認を求める前に確認が入り、承認が 1 回に戻る。commit 時の発火は最後の砦として残す。

---

## 実装

### 1. `hooks/review-chain-notice.sh` を Stop でも発火させる

種別は `chore`（既存 hook の配線変更。新規ロジックなし）。

イベント種別で分岐する。**分類・メッセージ生成部は一切触らない**:

| | PreToolUse（現状） | Stop（追加） |
|---|---|---|
| 発火条件 | `git commit\|revert\|merge` を検出 | 常に（下の静穏条件まで進む） |
| 対象 repo | コマンド文字列から抽出（`_git-target-common.sh`） | cwd |
| 変更取得 | staged → 空なら working tree | 同じ（変更なしなら静穏終了） |
| 分類・メッセージ | 現行のまま | 現行のまま |
| 出力 | `hookEventName: "PreToolUse"` | `hookEventName: "Stop"` |

冒頭のメッセージ文言だけ、両方の文脈で読める形に直す
（現状「commit 前の Review 実行確認」→ commit 直前とは限らなくなるため）。

`settings.json` の `hooks.Stop` 配列へ同じスクリプトを配線する。

### 2. `rules/common/human-gate.md` の改修（B）

「1 作業 1 ゲート」節に追記 — レビュー指摘に基づく修正は intent を変えないので
`plan との差分: なし` として再承認を取らない。**除外は behavior-shaping artifact と
control plane**（本文提示が要る区分なので、変わった本文は改めて見せる）。

---

## あえてやらないこと

**`metrics/*.jsonl` を突合してレビュアーごとの起動済み判定をする**（当初案）。

調査の結果、`agent-usage.jsonl` と `skill-usage.jsonl` を使えば「python-reviewer は未起動」と
名指しでき、全部起動済みなら黙らせられることは分かった。だが:

- 根本原因は順序であって精度ではない。名指しは順序の是正と独立しており、同時にやる理由がない
- 「どれを起動したか」はセッションのコンテキストに既にある。忘れるのは記憶の問題ではなく
  起動しようと考えなかったからで、適切なタイミングの一般的な問い直しで直る
- 新規 Python 2 本 + 共有部品化（既存 hook の改修 = 回帰リスク）+ prefix 一致・時刻窓・
  ログ不在の意味論という、それ自体が壊れうる面を増やす

`planning.md` の Prototype Before Scale に従い、まず配線だけで様子を見る。**Stop 発火が
うるさい / 一般的すぎて効かない、という実測が出たら**そのときログ突合を足す。判断材料は
台帳へ記録しておく（調査結果は残っているので再調査は不要）。

---

## テスト

`tests/review-chain-notice.bats` に Stop 経路のケースを追加する。
**1 test 1 assertion で書く** — 台帳 T-BATS-MULTI-ASSERT のとおり、bats は最後のコマンドの
終了ステータスしか見ないため裸の `[[ ]]` を並べると先行分が黙って握り潰される。

- Stop イベント + 変更なし → 無音
- Stop イベント + `.py` 変更 → code 区分のメッセージが出る
- Stop イベント + `hooks/` 変更 → behavior-shaping 区分のメッセージが出る
- Stop イベント + `docs/adr/` 変更 → ADR 区分のメッセージが出る
- Stop イベントの出力の `hookEventName` が `"Stop"` である
- Stop イベント + git 管理外の cwd → 無音

既存の PreToolUse ケースが全 PASS のままであることを回帰として確認する。

## Verify

`bash .claude/verify.sh`（bats 全体 + ruff + mypy）。

## Review（commit の前に回す）

- code-reviewer（`.sh` 改修）
- security-reviewer（control plane — hook と `settings.json` に触れる）
- codex-review

## Doc Sync

- `hooks/README.md` — PreToolUse 表の `review-chain-notice.sh` 行に Stop 併記、Stop 節にも追加
- ADR 新設 — 記録する判断は「レビュー実行確認を承認より前へ移した理由」と
  「Stop hook の出力チャネル（exit 0 + stderr は無音、additionalContext がブロックせず届く）」

---

## 別件（切り離し可）

既存の Stop hook 2 本が `exit 0` + stderr で書かれており、警告が debug log にしか
行っていない。同じ知見で直せるが本題とは独立しているので、落として台帳へ回してもよい。

- `hooks/dotclaude-dirty-check.sh:25-27`
- `scripts/hooks/search-first-verdict-check.py:125`

`planning.md` は「Stop hook が Verdict の存在を検査する」と書いているが、検査結果が
誰にも届いていない状態。

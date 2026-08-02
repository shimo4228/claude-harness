---
name: herdr-delegate
origin: shimo4228
user-invocable: true
description: "Herdr の pane に別プロセスの CLI コーディングエージェント（Codex 等）を立てて、実装タスクを丸ごと委譲するワークフロー。Use when the user says 「Codex にやらせて」「E2E は Codex に委譲」「Herdr でセッション立ててタスク投げて」 or explicitly asks to delegate implementation work to another CLI agent. 前提ゲート: HERDR_ENV=1 かつユーザーの明示指示（agents.md の委譲ゲートと同一 — 有益そうというだけで自発起動しない）。herdr CLI の一般操作は skill: herdr が正本で、本 skill は委譲に特化した手順・監視レシピ・検収規律のみを持つ。NOT for — read-only の cross-model レビュー（→ codex-review）、Claude 内サブエージェントへの並列化（→ Agent tool）。"
---

# Herdr Delegate — 別 CLI エージェントへのタスク委譲

Herdr の pane に Codex 等の対話セッションを立て、指示書ファイルを渡して実装を委譲し、
完了を監視して検収する。**Code Sovereignty は委譲しない** — 書くのは相手、
レビュー・検証・コミット判断はこちら（呼び出し側の Claude）が握る。

## ゲート（両方必須）

1. `test "${HERDR_ENV:-}" = 1` — Herdr 管理下の pane にいること
2. **ユーザーの明示指示**があること（「Codex にやらせて」等）。有益そうというだけで
   自発的に委譲しない（`rules/common/agents.md` の委譲ゲートと同一）

## なぜ headless（`codex exec`）ではなく Herdr セッションか

理由は **substrate が吸収していない 3 点**に絞る。長時間実行それ自体は理由にならない
（Bash tool は timeout に達したコマンドを kill せず background へ移すし、上限は
`BASH_MAX_TIMEOUT_MS` で変えられる — 2026-08-01 に公式 tools-reference で確認）。

1. **別ベンダのモデルを使うこと自体** — Claude Code 側の並列機構（subagents / Agent teams /
   `/batch`）は**すべて Claude モデル**で、cross-vendor 委譲の公式面は無い。脱相関が要るなら
   プロセスを分けるしかない
2. **対話セッションの永続性と差し戻し** — 公式の background 実行（`claude --bg`）は
   **プロンプトを起動時に渡し切る**形で、走っている相手に後から文字を送る API が無い。
   **同一文脈に差し戻して直させる**運用には公式の代替が無い（`herdr agent prompt` で
   同じセッションに追記できるのがこの経路の核）
3. **人間の可視性** — 途中経過が pane に出て、ユーザーの追加指示・中断（esc）が効く

**捏造報告に注意**（2026-07-31 実測）: headless 実行が途中で打ち切られた際、打ち切り直前までの
文脈で**実在しない成果物の完了報告を捏造する**事例を確認した（「92 テスト green・ファイル
作成済み」→ 実際は tree 無変更）。これは実行機構を変えても消えない性質なので、
下の検収規律（ground truth は git）で受ける。

## 手順

### 1. 指示書をファイルに書く

プロンプトは herdr コマンドの引数に直接埋めず、scratchpad にファイルとして書く
（長文の引用崩れ防止・監査記録・再実行可能性）。指示書に必ず含めるもの:

- 成果物の定義と置き場所（ファイルパスまで具体的に）
- **リポジトリ固有の制約**（lint が機械拒否する語彙・スタイル規約・並行性設定など。
  相手はこの repo の CLAUDE.md を読むとは限らない — 必要な不変条件は指示書に転記する）
- **検証手順**（build / test / lint のコマンド列）と「自分で green にしてから完了報告」
- **`git commit はしないこと`**（ワーキングツリー残置。検収とコミットはこちら）
- sleep 禁止・決定論などテスト規律（`rules/common/testing.md` から該当分を転記）
- **サンドボックスで実行できない検証の代替**を指定する — Codex の seatbelt からは
  iOS Simulator（CoreSimulatorService）に接続できない（2026-07-31 実測）。
  simulator を要するテストは「コンパイル検証（`xcodebuild build-for-testing`）までを
  相手、実行は検収側」と指示書に明記し、迂回（sandbox 解除要求）をさせない

### 2. pane を割って agent を立て、指示書パスを渡す

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
# → .result.pane.pane_id を読む
herdr agent start <name> --kind codex --pane <pane-id> -- -s workspace-write
herdr agent prompt <name> "指示書が <指示書の絶対パス> にある。読んでそのとおり実装し、検証を自分で回して green にしてから完了報告。git commit はしないこと。"
```

`--wait` は使わない（foreground の Bash が待ち続ける形になり、途中経過に手を出せなくなる）。
監視は次項の形で行う。

**prompt を送ったら、必ず `herdr agent read` で着弾を目視する。** レスポンスは成功を保証しない
（2026-08-01 実測）: `agent start` が `interactive_ready: true` を返し、続く `agent prompt` も
`agent_prompted` を返したのに、pane の実体は **codex が起動時に自己アップデートして exit した後の
シェルプロンプト**で、直後の `agent read` が `agent_not_found` を返した。
`Update ran successfully! Please restart Codex.` が出ていたら、もう一度 `agent start` からやり直す。
既知の「working 中に `idle` が返る」フラッピングとは別種で、**プロセスが無いのに成功が返る**ケース。

### 3. 完了監視 — status ではなく画面を見る

`herdr agent get` の `agent_status` は**信用しない** — Codex がスキル読み込み・
サブエージェント起動をする間、working 中でも `idle` を返すフラッピングを実測済み。
確実な信号は**画面の「esc to interrupt」表示の消失**。

**起動方法は Bash tool の `run_in_background`**（Monitor ではない）。欲しいのは
「settled したら 1 回」の通知であって発生ごとのイベント列ではなく、Monitor の
ドキュメント自身が *"Don't use an unbounded command for a single notification …
use Bash `run_in_background` with an `until` loop instead"* と指定している。
下のループは条件成立で `exit 0` するので、そのまま background 起動すれば
完了時に 1 回だけ通知が返る。

```bash
consec=0
while true; do
  sleep 30
  screen=$(herdr agent read <name> --source visible --lines 40 2>/dev/null)
  if [ -z "$screen" ]; then screen="READERR"; fi   # 空読みを「完了」に数えない（重要）
  if printf '%s' "$screen" | grep -qE "esc to interrupt|background terminal|Working \(|READERR"; then
    consec=0
  else
    consec=$((consec+1))
    [ "$consec" -ge 8 ] && { echo "delegate settled"; exit 0; }
  fi
done
```

誤検知の実測 3 系統（すべて上のスクリプトで対策済み）:
1. 「esc to interrupt」だけを見ると、長い外部コマンドの background terminal 待ち画面で
   すり抜ける → 実行痕跡のパターンを union で並べる
2. `herdr agent read` が **exit 0 のまま空出力**を返すことがあり、空文字は
   パターン不一致 = 完了扱いになる → 空読みは READERR に畳んで consec をリセット
3. デバウンスが短いと turn 間の一瞬の静止で発火 → 30 秒 × 8 回（4 分）以上にする

それでも誤検知したら、通知後の画面確認で作業中と分かった時点で監視を再アームすれば
よい（検収前に必ず画面と `git status` を見るので誤検知は安全側に倒れる）。

blocked（承認 UI）の可能性があるので、通知が来たら `herdr agent read` で画面を確認して
から次に進む。承認待ちなら `herdr agent send-keys` で応答するか、内容次第でユーザーに上げる。

### 4. 検収 — 相手の完了報告を信用しない

**ground truth は `git status` / `git diff` であって相手の報告文ではない**
（捏造報告の実例あり — 上記）。検収は必ずこちらで:

1. `git status --short` + `git diff` — 報告された成果物が実在するか、余計な変更がないか
2. **diff 全文レビュー**（このリポジトリの review chain — code-reviewer / 言語別 reviewer）
3. **検証をこちらでも再実行**（build / test / lint。相手の「green にした」を再現確認）
4. task request に commit が含まれる場合は、合格後にこちらの手でコミット

不合格なら差し戻し: `herdr agent prompt <name> "<具体的な指摘>"` で同一セッションの
文脈を保ったまま修正させる。2 回差し戻して直らなければ引き取って自分で直す。

### 5. 後片付け

自分が作った pane は、ユーザーが続用を求めない限り作業完了後に閉じてよい
（`herdr pane` group のコマンドを確認）。他人の pane・tab は触らない。

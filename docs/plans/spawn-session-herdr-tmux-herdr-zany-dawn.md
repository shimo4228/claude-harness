# spawn-session を tmux から herdr へ乗り換える

## Context

spawn-session は「生きている任意のセッションから、detached な Claude Code Remote Control セッションを立ち上げ、モバイルアプリ一覧に出す」skill。現在は tmux を pty 保持層に使っているが、ユーザーの主作業環境は Herdr（Ghostty ホスト、repo 単位の workspace 運用）に移行済み。tmux で生やしたセッションは herdr の艦隊ビュー（サイドバー・agent status 監視）から見えない孤児になるため、herdr を起動基盤にする。

## /grill-me で確定した決定

1. **起動単位**: herdr 既定 persistent session 内。**同じルート（cwd）の workspace が既にあればそこに新 tab**、無ければ新 workspace を作成。ユーザーは repo 単位で workspace を作る運用（例: `.claude` repo → `.claude` workspace）。
2. **器の形**: 既存 workspace 内では **新 tab**（`herdr tab create --no-focus`）。pane split は既存作業を狭めるので不採用。
3. **Fallback**: herdr server 不在時は **`herdr server` を headless でバックグラウンド自動起動**してから spawn（tmux のサーバー自動起動セマンティクスと同等）。**tmux パスは完全撤去**。

## 事実確認済みの前提（2026-07-21 に実機確認）

- herdr v0.7.4、server 稼働中、socket `~/.config/herdr/herdr.sock`
- socket API は **HERDR_ENV 無しの外部プロセスからも届く**（read-only コマンドで確認済み）
- `herdr workspace create [--cwd PATH] [--label TEXT] [--focus|--no-focus]` / `herdr tab create [--workspace ID] [--cwd PATH] [--label TEXT] [--no-focus]` / `herdr pane run <pane_id> <command>`（text+Enter 送信）が存在
- workspace record 自体は cwd を持たない。**pane record が `cwd` を持つ**ので、「同ルート workspace」判定は `herdr pane list` の cwd 照合で行う（label 照合は fallback）
- `herdr server` は headless server モードあり（`herdr --help` の Advanced commands）

## 変更ファイル

### 1. `~/.claude/skills/spawn-session/spawn.sh` — 書き換え（インターフェース不変）

`spawn.sh <project-dir> [display-name]` の入出力契約は維持（dumb launcher 原則、`~/bin/cc-spawn` symlink もそのまま生きる）。内部を tmux → herdr socket API に置換:

1. **引数検証**: 現行どおり（dir 存在チェック、`~` 展開）。`herdr` バイナリ検出（`command -v herdr` + `/opt/homebrew/bin/herdr` fallback — 現行の tmux fallback と同型）
2. **server 確保**: `herdr status`（または socket ファイル存在＋応答）で server 生存確認。不在なら `nohup herdr server >/dev/null 2>&1 &` で起動し、socket が応答するまで有界リトライ（例: 0.5s × 10 回。iteration bounds 規律）
3. **表示名の重複解消**: 現行の「同名生存セッションに ` #n` 付与」を herdr 側で再実装 — 全 workspace の `herdr tab list` を走査し、同じ label の tab 数を数えて ordinal を付与（check-then-act の逐次前提コメントは現行どおり残す）
4. **workspace 解決**: `herdr workspace list` → 各 workspace の `herdr pane list --workspace <id>` で `cwd == PROJECT` の pane を持つ workspace を探す
   - **あり** → `herdr tab create --workspace <id> --cwd "$PROJECT" --label "<表示名>" --no-focus`
   - **なし** → `herdr workspace create --cwd "$PROJECT" --label "<repo 名 (basename)>" --no-focus` （workspace label は repo 名 = ユーザーの命名規約に合わせる。表示名は tab 側に付ける — 新規 workspace の初期 tab を rename）
5. **JSON パース**: 応答から `pane_id` を読む（herdr skill の規律どおり ID は応答から取得、予測しない）。パースは `python3 -c` か `jq`（`jq` の有無を確認して選択 — 実装時に決定）
6. **claude 起動**: `herdr pane run <pane_id> "claude --remote-control \"<表示名>\""`。pane 内 shell はユーザーのログインシェルなので PATH 問題は tmux 版より軽い
7. **起動検証**: 現行の `sleep 1 + has-session` を `herdr wait agent-status <pane_id> --status idle --timeout 15000` に置換（herdr の claude integration が agent を検出 → idle 到達で TUI 起動成功と判定。tmux 版より強い検証）。timeout 時は `herdr pane read <pane_id> --source recent-unwrapped --lines 40` の出力を stderr に出して exit 1（auth 切れ等の診断材料）
8. **報告出力**: 表示名 / workspace・tab ID / dir を print（現行フォーマット踏襲、tmux 行を herdr 行に差し替え）

### 2. `~/.claude/skills/spawn-session/SKILL.md` — 更新

- frontmatter `description` と本文の「tmux で起動」を herdr に更新（発火条件・NOT for は不変）
- **How it works**: pty 保持層が tmux → herdr persistent session（server が pty を保持、Ghostty/SSH 切断後も生存）に。同ルート workspace への合流ルールを 1 行で記載
- **Failure modes** 書き換え: `tmux not found` → `herdr not found (brew install herdr)`、「tmux セッションが消えた」→「agent idle 到達 timeout（auth 切れ / claude が PATH に無い）」、server 自動起動失敗
- **Notes に HERDR_ENV ゲートとの整合を明記**: herdr skill の `HERDR_ENV=1` ゲートは既存 pane の inspect/control 用。spawn-session は **create-only（新 workspace/tab の作成と自 pane への run のみ）+ `--no-focus`** の socket 利用であり、server 稼働だけを前提とする sanctioned exception である旨を記載。herdr skill（origin: ogulcancelik/herdr、無改変）には触れない — origin 汚染回避
- spawn.sh は dumb launcher / プロジェクト解決は SKILL.md 側、の分担は不変

## 触れないもの

- `~/bin/cc-spawn` symlink（インターフェース不変なのでそのまま動く）
- `skills/herdr/SKILL.md`（外部 origin、無改変維持）
- プロジェクト解決ロジック（ニックネーム → dir、`<label>/<purpose>` 命名規約）

## Verification

1. **正常系（既存 workspace 合流）**: `.claude` workspace が生きている状態で `bash spawn.sh ~/.claude "test-spawn"` → `.claude` workspace に新 tab、claude TUI が idle 到達、モバイルアプリ一覧に "test-spawn" が出現
2. **正常系（新規 workspace）**: workspace の無い repo（例: `~/MyAI_Lab/zenn-content`）で実行 → 新 workspace 作成、label = repo 名
3. **重複解消**: 同名でもう 1 回 → 表示名に ` #2`
4. **異常系**: 存在しない dir → 現行同様の usage エラー
5. **後片付け**: テストで生やした tab / workspace / RC セッションはユーザー確認のうえ閉じる（herdr skill 規律: 自分が作ったもののみ close）
6. server 自動起動パスは server を止めての実機テストが破壊的（艦隊全体に影響）なので、**コードレビューのみ**とし実機検証はしない（ユーザーが望めば別途）
7. **Chain**: 実装後に code-reviewer（shell）を起動。CRITICAL なら停止

## 種別 / Chain（planning.md 準拠）

- 種別: `feat`（起動基盤の置換）。Phase 0 は不要 — 対象ソリューション（herdr）自体が指定済み
- Review: code-reviewer（bash）。security-reviewer は対象外（新規入力面なし、既存と同じ引数契約）— ただし `pane run` へ渡す表示名のクォートはレビュー観点に含める
- Verify: bash 構文チェック（`bash -n`）+ 上記実機テスト + `git status`

# コミット遅延の根本原因究明と恒久対策（v2 — heredoc 慣行の廃止）

## Context

`git commit` の実行が毎回数分〜10 分かかる問題。hooks 最適化や `cd && git` block
（160598c）でも解消しなかった。ユーザー指摘「heredoc 慣行を廃止すればいい。
settings からできるはず。git-workflow.md 退役でこれが入るようになった」を検証した。

## 根本原因（証拠付き）

### 遅延のメカニズム

コミットコマンドの `$(cat <<'EOF' ...)` （heredoc）がコマンド置換 `$(` を含むため、
`Bash(git:*)` の **prefix allowlist 照合が丸ごと無効**になり、auto-mode の classifier
→ 手動承認待ちに落ちる。トランスクリプト実測: heredoc 付きコミットのみ 27s〜604s
（600s 付近に 5 件クラスタ = 通知遅延/タイムアウト定数）、heredoc なし git は全件 0.4〜4s。
600s ケースも `is_error: False` で正常成功 — 待ちは実行前の承認、実行自体は一瞬。

hooks（4 本合計 <0.5s）・detect-secrets（0.23s）・harness_lint（0.20s）・
uvx bandit（0.44s）・git 本体（0.03s、gpg なし）はすべて白。

### heredoc が入り込んだ経緯（ユーザー仮説の検証結果）

- footer（Co-Authored-By）付きコミットの初出は **2026-07-25**（同日 16 件。それ以前は
  ほぼゼロ）。**Fable 5 世代切替と同日** — 新 substrate が session guidance で
  「Co-Authored-By + Claude-Session の 2 行 footer を付けよ」と注入し始めたのが引き金。
  複数行メッセージ → モデルが heredoc を使う → 遅延発生
- git-workflow.md 退役（07-26 21:03）は初出より**後**なので直接の引き金ではないが、
  同 rule の「Note: Attribution disabled globally via ~/.claude/settings.json」が
  攻撃面を隠していた。しかもこの記述は**幽霊**だった — `includeCoAuthoredBy` 等の
  attribution キーは追跡履歴上 settings.json に一度も存在せず、settings.local.json /
  ~/.claude.json にも無い（documented-invariant がゲート化されていなかった実例）
- ユーザー仮説の判定: **方向は正しい**（heredoc 慣行が新しく入り、settings で止められる）。
  時期は退役でなく 07-25 世代切替、機構は footer 注入 → heredoc → allowlist 落ち

## 恒久対策

### 変更 1（本丸）: settings.json で attribution を無効化

公式ドキュメント（https://code.claude.com/docs/en/settings.md）の `attribution` 設定を使う:

```json
"attribution": {
  "commit": "",
  "pr": ""
}
```

`~/.claude/settings.json` に追加。footer 指示が substrate から消え、単一行 `-m`
コミットに戻る = heredoc の必要自体が消滅する。
（pr も空にするのは PR body の 🤖 footer + session URL も同根のため。commit のみに
絞りたければ `"pr"` キーを外す）

注意: system prompt は起動時注入なので**現セッションには効かない**。効果確認は
新セッションで行う。

### 変更 2（決定論ガード・保険）: validate-bash.sh に `$(` 付き commit の block を追加

attribution を消しても、本文付きコミットでモデルが habit で heredoc を使う可能性は残る。
その 1 回が 600s 待ちになるのを、即時ローカル reject + 書き直し指示に変換する
（160598c の `cd && git` block と同型。hooks.md「品質強制 → hooks」）。
control plane につき本文提示:

```bash
# --- git commit + コマンド置換 (allowlist を外れて手動承認待ちに落ちる形) ---
# $( を含むコマンド文字列は Bash(git:*) の prefix 照合が丸ごと無効になり、
# auto-mode の承認待ち (実測 27s〜600s+) に毎回落ちる (2026-07-27 実測)。
# 複数行メッセージは -m 複数指定か、ファイルに書いて -F で渡す。
if echo "$COMMAND" | grep -qE '\bgit\b[^;|&]*[[:space:]]commit\b' \
   && echo "$COMMAND" | grep -qF '$('; then
  block "Command substitution in a git commit command falls out of the Bash(git:*) allowlist and waits on manual approval. Use multiple -m flags, or write the message to a file and use 'git commit -F <path>'."
fi
```

テスト新設 `tests/validate-bash-heredoc-commit.bats`（`validate-bash-cd-git.bats` 雛形）:
- block: `git commit -m "$(cat <<'EOF'...)"` / `git -C ~ commit -m "$(...)"` / `git add -A && git commit -m "$(...)"`
- allow: `git commit -F /tmp/msg` / `git commit -m "one" -m "body"` / `echo "$(date)"`（commit なし）

### 変更 3: メモリ・ドキュメント整合

- `memory/feedback_git_dash_c_over_cd.md` に追記: heredoc も同構造の別入口だった。
  `$(` を含む git commit は禁止、`-m` 複数 or `-F` を使う。attribution 設定で footer 根絶済み
- git-workflow.md の幽霊記述の教訓（attribution 無効化が実在しなかった）は上記メモリの
  Why に 1 行で含める（rule 復活はしない — substrate 吸収の判断は維持）

## Alternatives（検討して不採用）

- **`git commit -F` 全面移行のみ（v1 案）**: footer 注入が残る限り毎回ファイル書き出しの
  手間が続く。根（footer 指示）を settings で断つ方が上流の修正
- **allowlist 側の緩和**: prefix 照合は `$( )` を安全に許可できない（injection を通す）
- **git-workflow.md の復活**: footer の根は rule でなく substrate の attribution 設定。
  rule を戻しても settings に鍵がなければ再発する

## Verification

1. `bats tests/validate-bash-heredoc-commit.bats` 全 PASS + 既存
   `validate-bash-cd-git.bats` / `validate-bash-injection.bats` 回帰なし
2. 本対応のコミット自体は heredoc を使わず `-m` 複数 or `-F` で実行し、
   承認待ちなし（数秒以内）で完了することを確認
3. **新セッション**で: footer 指示が system prompt から消えていること、
   単一行 `-m` コミットが即時承認されることを確認

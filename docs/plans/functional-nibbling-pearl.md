# claude-harness への curated hook 公開

## Context

前セッションで docs/adr/ 37 本を claude-harness へ公開した結果、**参照の空白**が生まれた。
公開側の以下 7 ドキュメントが hook のファイル名と内部挙動を名指しで論じているのに、
コード実体が公開 repo に存在しない:

- `docs/adr/0027` / `0028` / `0033` / `0034` / `0035`
- `rules/common/planning.md`（`hooks/review-chain-notice.sh` を名指し）
- `skills/verify-bootstrap/SKILL.md`（`.claude/verify.sh` 契約の対向）

この空白を、**丸ごと同期ではなく curated subset** で埋める。hook 群の半分は `~/.claude`
専用発火（episode-log 系 / contemplative-name-reminder / herdr-agent-state /
harness-lint-precommit）で再利用価値が無く、それらを含めると公開面が「他人の環境で動かない
コードの寄せ集め」になるため。

前提作業（敵対的 `.git/config` 脆弱性の修正、bats 150/150 pass）は完了済み。

## 探索で判明した前提の訂正

**`settings.json` の `hooks` セクションだけは portable。** 対象 5 hook の配線行はすべて
`bash ~/.claude/hooks/*.sh` で、絶対パスを持つのは公開対象外の `herdr-agent-state.sh`
（SessionStart）だけ。よって install 手順は散文ではなく **コピペで動く JSON 断片**を出せる。
マシン固有なのは `permissions` / `env` / `enabledPlugins` / `statusLine` 等の兄弟キーであり、
`hooks` サブツリーではない。

追加で確認した事実:

- 公開候補 10 ファイルに `/Users/` ・氏名・メールの混入なし
- sync script の `SECRET_RE` を候補 10 ファイルへ適用 → ヒット 0（secret scan で abort しない）
- `verify-precommit.sh:57` は `$HOME/.claude/scripts/hooks/verify_allow.py` をハードコード
  → **`~/.claude` 以外に置くと台帳照合が効かず、ゲートを実行せず素通しする**（再配置制約）
- bats は `git-target-extraction` / `secret-scan-precommit` / `review-chain-notice` のみ存在。
  **verify / bandit / ruff-format には無い**
- 公開する hook のコメントが `rules/common/security.md`（origin: `ECC-customized` = 非公開）と
  `.notes/t-004-builtin-review-surface.md`（private）を参照している

## 公開セット

| 公開パス | 役割 |
|---|---|
| `hooks/secret-scan-precommit.sh` | commit 前の secret scan（detect-secrets 優先 / regex fallback） |
| `hooks/verify-precommit.sh` | repo 自身の `.claude/verify.sh --staged` を承認台帳経由で実行 |
| `hooks/bandit-precommit.sh` | staged `.py` の index 内容へ bandit `-ll -ii` |
| `hooks/ruff-format-precommit.sh` | staged `.py` へ `ruff format --check`（検査のみ） |
| `hooks/review-chain-notice.sh` | commit / revert / merge 前の Review / Verify 確認（advisory） |
| `hooks/_git-target-common.sh` | 対象 repo 抽出の共有部品（引用符 span 除去） |
| `scripts/hooks/verify_allow.py` | direnv allow 型の内容ハッシュ承認台帳 |
| `tests/git-target-extraction.bats` | 共有部品の回帰固定 |
| `tests/secret-scan-precommit.bats` | secret gate の回帰固定 |
| `tests/review-chain-notice.bats` | advisory hook の回帰固定 |

**除外**: `harness-lint-precommit.sh` / `harness_lint.py`（`~/.claude` repo 専用発火）、
episode-log 系・`contemplative-name-reminder.sh`・`herdr-agent-state.sh`（harness 内部専用）、
`validate-bash.sh` / `docs-prewrite.sh` / `bats-autorun.sh` / `log-*-usage.sh`（今回のスコープ外。
commit 面ではないため別途判断）。

## 実装

### 1. `scripts/sync-from-local.sh` に hooks / scripts/hooks / tests を追加

**明示 allowlist 方式**を採る。公開は provenance（誰が書いたか）ではなく curation
（公開に値するか）の判断であり、`origin:` コメントを付けて既存 `has_origin()` に相乗りすると
両者が同義になってしまう（非公開の自作 hook も自作である以上、origin を付けた瞬間に公開される）。

`SUBTREES` に `hooks scripts/hooks tests` を追加し、既存の subtree 機構（clean-guard →
staging → prune → secret scan → `rm -rf` + `cp -R`）をそのまま再利用する。追加するのは
staging ループのみ:

```bash
HOOK_ALLOWLIST=(
  hooks/_git-target-common.sh
  hooks/secret-scan-precommit.sh
  ...
)
for rel in "${HOOK_ALLOWLIST[@]}"; do
  mkdir -p "$STAGING/$(dirname "$rel")"
  cp "$SOURCE_DIR/$rel" "$STAGING/$rel"
done
```

subtree 機構を再利用することで、allowlist から外した hook は次回 sync で公開側から消え、
`git diff` に削除として現れる（removal semantics が壊れない）。

hook には frontmatter が無いので、既存の YAML validation ループ（`**/*.md` glob）と
README テーブル再生成（skills/agents/rules を glob）には一切影響しない。

### 2. `docs/hooks.md` を新規作成（install 手順の正本）

**`hooks/README.md` には置かない** — `hooks/` は wholesale-replace される subtree なので、
手書きの README は毎回 sync で消える。`docs/adr/` の隣に置く。内容:

- 各 hook の発火条件・ブロック条件・bypass 環境変数の表
- `settings.json` へ貼る `hooks` JSON 断片（curated 5 本ぶんの PreToolUse entry。
  自環境の設定から抽出した実物で、`~/.claude/hooks/...` のまま動く）
- **配置制約の明記**: `verify-precommit.sh` は `~/.claude/scripts/hooks/verify_allow.py` を
  ハードコードしているため、`~/.claude` 以外への配置では台帳が見つからず素通しする
- `verify_allow.py approve <repo>` を人間が実行するまでゲートは走らない、という承認モデルの説明
- **bats は 3 hook 分のみ**であり網羅ではないと明記（verify / bandit / ruff-format は未整備）
- 依存: `jq` / `python3`、任意で `detect-secrets` / `bandit` / `ruff` / `bats`

### 3. `README.md` / `README.ja.md` に `### Hooks` セクション追加

`### Rules` と `### Design decisions (ADRs)` の間（`README.md:112` 付近）。GENERATED マーカーの
**外側**に手書きで置く（sync script は hook テーブルを生成しない）。3〜4 行 +
`docs/hooks.md` へのリンク。`## Usage` の Full install にも hooks のコピー行を追記する。

### 4. ADR-0038 を執筆（`~/.claude/docs/adr/0038-*.md`）

skill: `adr-writer` 経由。骨子:

- **Context**: ADR 公開が生んだ参照の空白（上記 7 ドキュメント）。hook の半分は harness 内部専用。
- **Decision**: curated 5 hook + 共有部品 2 + bats 3 を新規 subtree で公開。allowlist 方式。
  配線は `settings.json` 全体ではなく `hooks` 断片のみ `docs/hooks.md` に転記。
- **Alternatives**: (1) `hooks/` 丸ごと同期 — 内部専用 hook が動かないコードとして混入
  (2) `# origin:` コメント filter — provenance と公開意図が同義になる
  (3) 非公開のまま ADR だけ残す — 参照の空白を放置
- **Consequences**: 利用者は手動配線が必要 / `~/.claude` 固定の再配置制約 /
  verify・bandit・ruff-format は bats 未整備 / 公開コードが非公開 rule（`security.md`）と
  `.notes/` を参照する dangling reference が残る / allowlist は hook 追加時のメンテ対象

`docs/adr/README.md` の索引にも 0038 を追加する。

### 5. 公開前レビュー

general-purpose agent で候補 10 ファイル + `docs/hooks.md` を公開前レビュー
（secrets / 個人情報 / 第三者情報 / 未修正脆弱性の手法の露出）。前回 ADR 公開時はこの工程で
個人情報と未修正脆弱性を検出した実績がある。

### 6. sync 実行と commit

skill: `harness-sync` の手順に従う。`--dry-run` → 差分レビュー → 本実行 → `git diff` →
commit → push。**1 Bash call = 1 git コマンド**（`&&` 連結は permission プロンプトを誘発）、
push は `dangerouslyDisableSandbox` 必須。

## 変更するファイル

**`~/.claude`（正本）**
- `docs/adr/0038-publish-curated-commit-hooks.md`（新規）
- `docs/adr/README.md`（索引に 1 行）

**`claude-harness`（公開 repo。sync script と手書き doc は直接編集）**
- `scripts/sync-from-local.sh`（`SUBTREES` 拡張 + `HOOK_ALLOWLIST` staging ループ）
- `docs/hooks.md`（新規）
- `README.md` / `README.ja.md`（`### Hooks` セクション + Full install 追記）
- `hooks/` `scripts/hooks/` `tests/`（sync script が生成。手で置かない）

## 検証

1. `scripts/sync-from-local.sh --dry-run` — 新規 subtree 3 つが `NEW:` 行で列挙され、
   secret scan / YAML validation で abort しないこと
2. 本実行後 `git status --short` で、公開されるのが allowlist の 10 ファイルだけで、
   `harness_lint.py` や episode-log 系が混入していないこと
3. `grep -rn '/Users/\|shimomoto' hooks/ scripts/hooks/ tests/` が空
4. `bats ~/.claude/tests/{git-target-extraction,secret-scan-precommit,review-chain-notice}.bats`
   が公開版の内容で pass（`~/.claude` 正本と byte 一致することを `diff -r` で確認）
5. `docs/hooks.md` の JSON 断片を `python3 -c 'import json,sys; json.load(sys.stdin)'` で構文検証
6. 公開後の README / ADR から `hooks/*.sh` への相対リンクが解決すること（リンク切れ確認）

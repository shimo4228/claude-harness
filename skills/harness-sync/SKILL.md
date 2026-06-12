---
name: harness-sync
description: ローカル harness (~/.claude) の origin-filtered コンポーネントを公開 repo (claude-harness 集約 repo + 単独 skill repo 群) へ一方向同期する。Use when the user says 「ハーネスを公開 repo に同期して」「claude-harness を更新して」「スキルを公開して」「skill repo を同期して」 or invokes /harness-sync. 収集 → secret scan → subtree 置換は決定論的 script が行い、diff レビュー・README/llms.txt の整合・コミットは会話で行う。NOT for: 公開 repo から ~/.claude への逆方向取り込み、ECC 等外部 origin の公開判断、汎用化 fork を持つ curated skill repo (script 同期は汎用化を壊すため手動 curation)。
user-invocable: true
origin: shimo4228
---

# /harness-sync — 公開 repo への一方向エクスポート

ローカルの生きた harness (~/.claude) と公開 artifact repo は**目的の違う別 repo** として保ち、
remote 直結ではなく **filter 付き一方向コピー**で同期する。公開境界は script の
origin filter 1 箇所で宣言的に管理される。

## なぜ remote 直結にしないか

- ~/.claude は実行時状態 (settings, metrics, session 情報) を含む生きたディレクトリで、
  gitignore の永久警戒を前提にした公開はミス耐性がゼロ
- origin filter は出自の記録であって再配布権の整理ではない (外部 origin はライセンス
  整備が別途必要)
- 目的の違う repo 間は丸コピが調整コスト最小 (duplicate over coordination)

## Workflow

### 1. Dry-run で差分を確認

```bash
bash <公開repo>/scripts/sync-from-local.sh --dry-run
```

差分の要約 (新規 / 変更 / 削除されるコンポーネント) をユーザーに提示する。

### 2. 公開ゲート (ユーザー確認)

新しく公開対象になるコンポーネントがある場合は**必ず一覧で示して確認を取る**。
push しなくても commit は公開準備なので、ここが実質の公開判断点。

### 3. 適用

```bash
bash <公開repo>/scripts/sync-from-local.sh
```

script は staging 収集 → runtime artifact 除去 (results.json, __pycache__ 等) →
secret scan (検出時 abort) → skills/ agents/ rules/ subtree の置換、まで行う。
**commit はしない** — `git diff` がレビューゲート。

### 4. ドキュメント整合 (LLM 側の責務)

コンポーネント数や一覧が変わったら、公開 repo の以下を更新する:

- `README.md` / `README.ja.md` — skill / agent / rule の一覧と数
- `llms.txt` / `llms-full.txt` — 構成変更があれば。文面の質は `llms-txt-writer` に defer

### 5. コミット

```bash
git -C <公開repo> add -A && git commit
```

メッセージ例: `chore: sync from local harness (origin: shimo4228)` + 主な増減を body に。
**push はユーザーの判断に委ねる** (commit ≠ publish)。

## 削除の伝播

claude-harness の script は subtree を丸ごと置換するため、ローカルで退役した skill や
origin が変わったファイルは公開側からも消える。退役理由は ~/.claude 側の ADR にあるので、
公開側 commit message から参照する。

skill repo の script は逆に**削除を伝播しない**: 対象 skill を repo 自身の `skills/`
配下から導出するため、harness 側に skill が無い・origin が一致しない場合は skip ではなく
**abort** する(公開済み skill が静かに消えるのを防ぐ)。skill を退役させる場合は
repo 側で明示的に削除する。

## Skill repo sync モード

単独 skill repo (1 repo = 1 skill) も同じ workflow (dry-run → 公開ゲート → apply →
docs 整合 → commit) で同期する。違いは script だけ:

- 対象 skill は **repo 自身の `skills/` 配下ディレクトリ名から導出**(これにより script は
  全 skill repo で byte-identical に vendor できる)
- 置換対象は `skills/<name>/` のみ。agents/ rules/ は扱わない
- root files (README / llms.txt / CHANGELOG / LICENSE) 不可侵、commit しない、は共通

**対象は harness が正本の skill のみ**。CA 等 project 運用版から汎用化 fork した
curated skill repo (code-and-llm-collaboration, llm-agent-security-principles) には
script を置かない — 丸ごと置換が汎用化リライトを上書きしてしまうため、手動 curation で
更新する。

## Repo mapping (project-specific)

| target | 種別 | script | 正本 |
|---|---|---|---|
| `~/MyAI_Lab/claude-harness` ([repo](https://github.com/shimo4228/claude-harness)) | 集約 (skills + agents + rules) | `scripts/sync-from-local.sh` (集約版) | `~/.claude` |
| `~/MyAI_Lab/when-code-when-llm` ([repo](https://github.com/shimo4228/when-code-when-llm)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/when-code-when-llm` |
| `~/MyAI_Lab/signal-first-research` ([repo](https://github.com/shimo4228/signal-first-research)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/signal-first-research` |
| `~/MyAI_Lab/citation-sync` ([repo](https://github.com/shimo4228/citation-sync)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/citation-sync` |

共通 env: origin filter `shimo4228` (`HARNESS_SYNC_ORIGIN`)、source `~/.claude` (`HARNESS_SYNC_SOURCE`)。

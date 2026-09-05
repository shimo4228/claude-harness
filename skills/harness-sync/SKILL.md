---
name: harness-sync
description: "ローカル harness (~/.claude) の origin-filtered コンポーネントを公開 repo (claude-harness 集約 repo + 単独 skill repo 群) へ一方向同期する。Use when the user says 「ハーネスを公開 repo に同期して」「claude-harness を更新して」「スキルを公開して」「skill repo を同期して」 or invokes /harness-sync. 収集 → secret scan → subtree 置換は決定論的 script が行い、diff レビュー・README/llms.txt の整合・コミットは会話で行う。NOT for: 公開 repo から ~/.claude への逆方向取り込み、ECC 等外部 origin の公開判断、汎用化 fork を持つ curated skill repo (script 同期は汎用化を壊すため手動 curation)。"
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

### 2. 公開スコープ確認

task request / approved plan に列挙された repo と component は追加確認なしで進める。
列挙外の repo・新規公開 component が見つかった場合だけ scope change として停止する。

### 3. 適用

```bash
bash <公開repo>/scripts/sync-from-local.sh
```

script は staging 収集 → runtime artifact 除去 (results.json, __pycache__ 等) →
frontmatter YAML 検証 (GitHub 等の厳密パーサ基準。invalid なら abort) →
secret scan (検出時 abort) → skills/ agents/ rules/ docs/adr/ rfcs/ hooks/ scripts/hooks/
tests/ subtree の置換、まで行う。origin filter が効くのは skills/ agents/ rules/ だけで、
残り 3 系統は別の規則で決まる (いずれも集約 repo のみ):

- `docs/adr/` — ADR はハーネス自身の設計判断の記録で定義上すべて自作のため、origin filter を
  掛けずディレクトリ丸ごとが対象。以後の ADR は公開される前提で書く。
- `rfcs/` — 台帳エントリも自作の判断記録なので ADR と同じく丸ごと (ADR-0049)。起票は公開可能な書き方が既定 — 機微はリンク先へ (task-stocktake の公開規約)。
- `hooks/` `scripts/hooks/` `tests/` — script 内の `HOOK_ALLOWLIST` に列挙したファイルだけ。
  公開は provenance でなく curation の判断 (ADR-0038)。公開対象の hook を追加・rename したら
  allowlist を更新する — source に無い entry があると sync は abort する。`scripts/claims.py`
  (台帳 CLI、rfcs/ の消費側) も allowlist 経由 — subtree 外に置かれるため削除は伝播しない
  (delist したら公開 repo 側で手動削除)。install 手順の正本は
  公開 repo の `docs/hooks.md` で、これは subtree の**外**にある (中に置くと sync で消える)。
script は commit しない。LLM 側で diff と secret scan の結果を確認してから次へ進む。

### 4. ドキュメント整合 (LLM 側の責務)

構成が変わったら、公開 repo の以下を確認する:

- `README.md` / `README.ja.md` の skill/agent/rule テーブルは **GENERATED マーカー間で
  apply 時に script 自動再生成**される（`skills-table` / `agents-table` / `rules-table`。
  membership は origin filter が正、Purpose 列は既存キュレーションを保持し新規のみ seed）。
  手で直すのは **Purpose 文面と周辺 prose のみ**。**集約カウント（"N skills" 等）はどこにも
  書かない**（No-volatile-state。churning count は焼き込むと drift する）
- **repo の About（description）も同様に volatile-free に保つ** — 数字を入れず、
  価値提案（何を pick できるか）で記述する。`gh repo edit --description` で編集
- `docs/hooks.md` — **script 生成ではない手書き doc**。hook の発火条件・bypass 変数・
  `settings.json` 断片・bats 被覆を持つので、公開 hook を足す / 挙動を変えたら手で追随する
- `llms.txt` / `llms-full.txt` — **退役した component の行を消すのは機械検査で確認する**
  （下の「AI 向け導線のリンク切れ」）。文面の質は `llms-txt-writer` に defer
- 集約 repo README の「Upstream components」節も **script 生成**（marker 間を apply 時に
  自動再生成、外部 origin の名前のみ・ECC トップリンクのみ）— 手で編集しない

### 4b. AI 向け導線のリンク切れ検査（機械、blocking）

apply の後・commit の**前**に、公開 repo に対して必ず走らせる:

```bash
python3 ~/.claude/skills/context-sync/scripts/context_evidence.py \
  --root <公開repo> --gate      # exit 3 = 違反あり。直すまで commit しない
```

exit 3 は**リンク切れ専用ではない** — gate scope は `adr_index` / `graph_jsonld` /
`llms_txt` の 3 つ（集約 repo は `docs/adr/` を丸ごと持つので ADR index drift でも鳴る）。
出力行がどの検査かを名指しするので、そこを読む。

**この検査が要る理由は削除の非対称にある。** subtree の丸ごと置換は退役した skill を
公開側から消すが、`llms.txt` / `llms-full.txt` は root files として不可侵で、手で保守する
文書のまま残る。つまり skill を 1 つ退役させるたび、AI 向け導線だけが消えた path を
指し続ける — 人間の README と違い、この故障は読んで気づく人がいない。

実例（2026-08-27 に検出、RFC-0012）: `en-to-ja-translation` / `ja-to-en-translation` /
`substack-publishing` の 3 skill が harness 側で退役した後、集約 repo の `llms.txt` は
`skills/<name>/SKILL.md` を指したままだった。llms-full.txt 側のリンクも同じ検査が
解決する（同 RFC で追加）。

**この step は暫定（interim）**。不変条件は「publish されない component を AI 向け doc が
指さない」で、その roster を機械で知っているのは harness ではなく公開 repo の
`scripts/sync-from-local.sh`（origin filter から README の表を GENERATED marker 間へ
再生成し、secret / frontmatter / allowlist の 4 箇所で abort する）。**正しい置き場所は
その abort 連鎖の 5 番目**か、より深くは llms.txt の component 行自体を GENERATED marker
にすること — 後者は検出でなくクラスごと消える。ここが checklist 側にあるのは RFC-0012 の
作業境界（ミラー repo を触らない）の産物であって設計判断ではない。**agent を経由しない
sync はこの検査を通らない。**

### 5. コミット

```bash
git -C <公開repo> add -A
git -C <公開repo> commit
```

メッセージ例: `chore: sync from local harness (origin: shimo4228)` + 主な増減を body に。
default branch へ直接 commit するのは意図的（sync = mirror 更新であり branch-first 規約の対象外）。
task request が push まで含む場合は追加確認せず push する。

## 削除の伝播

claude-harness の script は subtree を丸ごと置換するため、ローカルで退役した skill や
origin が変わったファイルは公開側からも消える。退役理由は ~/.claude 側の ADR にあるので、
公開側 commit message から参照する。

skill repo の script は逆に**削除を伝播しない**: 対象 skill を repo 自身の `skills/`
配下から導出するため、harness 側に skill が無い・origin が一致しない場合は skip ではなく
**abort** する(公開済み skill が静かに消えるのを防ぐ)。skill を退役させる場合は
repo 側で明示的に削除する。

## Skill repo sync モード

単独 skill repo (1 repo = 1 skill) も同じ workflow (dry-run → scope 確認 → apply →
docs 整合 → commit) で同期する。違いは script だけ:

- 対象 skill は **repo 自身の `skills/` 配下ディレクトリ名から導出**(これにより script は
  全 skill repo で byte-identical に vendor できる)
- 置換対象は `skills/<name>/` のみ。agents/ rules/ は扱わない
- root files (README / llms.txt / CHANGELOG / LICENSE) 不可侵、commit しない、は共通

**対象は harness が正本の skill のみ**。CA 等 project 運用版から汎用化 fork した
curated skill repo (code-and-llm-collaboration, llm-agent-security-principles) には
script を置かない — 丸ごと置換が汎用化リライトを上書きしてしまうため、手動 curation で
更新する。

### Rule repo variant

単独 **rule** repo (1 repo = 1 rule file) も同じ workflow だが script が違う: 対象は
`skills/<name>/` ではなく固定の単一ファイル `rules/common/<name>.md` を publish する
(source = `~/.claude/rules/common/<name>.md`)。origin marker は rule ファイルの HTML
コメント (`<!-- origin: shimo4228 -->`) を `head -15 | grep` で検出する。secret scan・
root files 不可侵・commit しない、は共通。

### Rule + plugin repo variant (akc-cycle)

`akc-cycle` は **rule + Claude Code plugin** repo。**rule は sync 対象外**: repo が自己完結版
(self-contained edition) を所有し、harness 側はポインター版 — 別内容が意図
(ADR-0018 / ADR-0035 「圧縮版を配布 repo へ同期しない」)。script は固定
allowlist 方式: 9 skills (AKC cycle phase binding: search-first / learn-eval /
skill-stocktake / skill-health / rules-stocktake / rules-distill / skill-comply /
context-sync / repo-asset-stocktake) + 1 agent (adr-writer) を
staging → prune → YAML frontmatter 検証 → secret scan → subtree 置換 (skills/ agents/)。
allowlist の component が harness に無い / origin marker が無いと abort (silently drop
しない)。**`.claude-plugin/plugin.json` / `marketplace.json` と `rules/common/akc-cycle.md`
は repo 側 root 資産** (README / LICENSE と同格) — sync は触らない。version 更新は
plugin.json を repo 側で手動 bump する。plugin は rules を運べない (Claude Code plugin
仕様) ため、rule file は plugin payload 外の copy-install 経路のまま。

`herdr-toolkit` (2026-08-03 公開) は同型の **skills-only plugin variant**: 固定 allowlist は
2 skills (herdr-delegate / spawn-session) のみで rule / agent 収集ブロックを持たない。
外部 origin の `herdr` skill 本体は Herdr 自身の integration が配るため対象外
(ADR-0036)。

## Skill repo packaging（命名と subagent 同梱）

skill repo を GitHub 公開する際の規約（正本）:

- **subagent 同梱**: skill が呼ぶ subagent は repo に同梱する。同梱しないと installer が
  agent を別途探す羽目になり、canonical rules を agent が SKILL.md から参照する
  orchestrator skill は両方入れるまで壊れる。
- **命名の非対称**: skill（SKILL.md）はオープンな cross-tool 標準（Agent Skills /
  agentskills.io — Codex / Gemini CLI / Cursor 等でも動く）、subagent（`agents/*.md`）は
  Claude Code 固有。→ **agent を同梱する repo は `claude-skill-` prefix を維持**し
  `compatibility` frontmatter に Claude Code 向けと明記。**pure-skill repo は prefix を
  外す**（`<owner>/<skill-name>`）。awesome-list 掲載は `owner/skill-name` で並び repo
  prefix を見ないので、命名は意味の正確さで決める。
- **レイアウト**: `install.sh`（skills/* → ~/.claude/skills/、agents/*.md →
  ~/.claude/agents/）+ `skills/<name>/SKILL.md` + `agents/<agent>.md`（top-level フラット。
  nest しない）。pure-skill repo は install.sh 省略可（citation-sync 等の先例）。
- **install.sh は冪等**: 同一なら skip、異なれば `*.bak-<ts>` に退避してから上書き
  （`--force` / `--dry-run`）。全 repo で byte-identical に保つ。README install 節は
  Option A（`./install.sh`）/ Option B（手動 `cp`）/ SkillsMP の 3 つを書く。
- **SkillsMP caveat**: `/skills add <owner/repo>` は `skills/` のみ install し `agents/`
  は入れない。agent 同梱 repo の README に必ず注記する（`cp agents/*.md
  ~/.claude/agents/` または `install.sh` を実行）。
- **公開用 packaging metadata は local 正本に持たせる**: `compatibility:` 等の公開向け
  frontmatter を repo 側で足すと、丸ごと置換のたびに消える（= 恒常的な偽 drift 源）。
  local SKILL.md の frontmatter に持たせる — Claude Code は未知キーを無視するので無害
  （learn-eval が先例、2026-07-03 第二波で全 skill repo に適用済み）。

## Repo mapping (project-specific)

| target | 種別 | script | 正本 |
|---|---|---|---|
| `~/MyAI_Lab/claude-harness` ([repo](https://github.com/shimo4228/claude-harness)) | 集約 (skills + agents + rules + ADRs) | `scripts/sync-from-local.sh` (集約版) | `~/.claude` |
| `~/MyAI_Lab/signal-first-research` ([repo](https://github.com/shimo4228/signal-first-research)) | 単独 skill | script sync 停止 (local 正本を 2026-07-09 retire — abort する) | なし (repo 凍結 — AKC の citable design-pattern artifact として存続。原則の正本は `search-first` 等の消費 skill — 常駐の Signal-first 節は 2026-07-31 に退役、ADR-0026) |
| `~/MyAI_Lab/citation-sync` ([repo](https://github.com/shimo4228/citation-sync)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/MyAI_Lab/paper-lab/.claude/skills/citation-sync`（RFC-0019） |
| `~/MyAI_Lab/generation-audit` ([repo](https://github.com/shimo4228/generation-audit)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/generation-audit` |
| `~/MyAI_Lab/agent-stocktake` ([repo](https://github.com/shimo4228/agent-stocktake)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/agent-stocktake` |
| `~/MyAI_Lab/human-gate` ([repo](https://github.com/shimo4228/human-gate)) | retired rule artifact | sync abort（2026-08-02 に local scaffold を退役） | なし（公開記録として凍結） |
| `~/MyAI_Lab/rules-stocktake` ([repo](https://github.com/shimo4228/rules-stocktake)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/rules-stocktake` |
| `~/MyAI_Lab/learn-eval` ([repo](https://github.com/shimo4228/learn-eval)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/learn-eval` |
| `~/MyAI_Lab/rules-distill` ([repo](https://github.com/shimo4228/rules-distill)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/rules-distill` |
| `~/MyAI_Lab/skill-stocktake` ([repo](https://github.com/shimo4228/skill-stocktake)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/skill-stocktake` |
| `~/MyAI_Lab/skill-health` ([repo](https://github.com/shimo4228/skill-health)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/skill-health` |
| `~/MyAI_Lab/akc-cycle` ([repo](https://github.com/shimo4228/akc-cycle)) | plugin (9 skills + 2 agents) + repo 所有 rule (自己完結版、sync 対象外 — 2026-09-01 二版化) | `scripts/sync-from-local.sh` (plugin 版、固定 allowlist) | 対象 skills/agents のみ (rule の正本は repo 側。harness の `rules/common/akc-cycle.md` はポインター版で別内容) |
| `~/MyAI_Lab/herdr-toolkit` ([repo](https://github.com/shimo4228/herdr-toolkit)) | plugin (2 skills) | `scripts/sync-from-local.sh` (plugin 版、固定 allowlist、rules/agents なし) | `~/.claude/skills/herdr-delegate` + `~/.claude/skills/spawn-session` |
| `~/MyAI_Lab/skill-comply` ([repo](https://github.com/shimo4228/skill-comply)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/skill-comply` |
| `~/MyAI_Lab/context-sync` ([repo](https://github.com/shimo4228/context-sync)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/context-sync` |
| `~/MyAI_Lab/llms-txt-writer` ([repo](https://github.com/shimo4228/llms-txt-writer)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/llms-txt-writer` |
| `~/MyAI_Lab/readme-writer` ([repo](https://github.com/shimo4228/readme-writer)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/readme-writer` |
| `~/MyAI_Lab/release-doi` ([repo](https://github.com/shimo4228/release-doi)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/release-doi` |
| `~/MyAI_Lab/search-first` ([repo](https://github.com/shimo4228/search-first)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/search-first` |
| `~/MyAI_Lab/jsonld-knowledge-graph` ([repo](https://github.com/shimo4228/jsonld-knowledge-graph)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/jsonld-knowledge-graph` |
| `~/MyAI_Lab/authorship-strategy-skill` ([repo](https://github.com/shimo4228/authorship-strategy-skill)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/authorship-strategy` |
| `~/MyAI_Lab/codex-review` ([repo](https://github.com/shimo4228/codex-review)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/codex-review` |
| `~/MyAI_Lab/repo-asset-stocktake` ([repo](https://github.com/shimo4228/repo-asset-stocktake)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/repo-asset-stocktake` |
| `~/MyAI_Lab/llm-as-judge` ([repo](https://github.com/shimo4228/llm-as-judge)) | 単独 skill | `scripts/sync-from-local.sh` (skill repo 版) | `~/.claude/skills/llm-as-judge` |
| `~/MyAI_Lab/claude-skill-paper-ecosystem` ([repo](https://github.com/shimo4228/claude-skill-paper-ecosystem)) | skill ×2 + agents 同梱 | `scripts/sync-from-local.sh` (skill repo 版) | `~/MyAI_Lab/paper-lab/.claude/skills/paper-ecosystem` + 同 `paper-writing`（RFC-0019。同梱 agent 5 本の正本は `~/MyAI_Lab/paper-lab/.claude/agents/`、script の対象外で手動 diff） |
| `~/MyAI_Lab/claude-skill-writing-ecosystem` ([repo](https://github.com/shimo4228/claude-skill-writing-ecosystem)) | skill + agents 同梱 | `scripts/sync-from-local.sh` (skill repo 版) | `~/MyAI_Lab/zenn-content/.claude/skills/writing-ecosystem`（RFC-0019。同梱 agent 6 本の正本は `~/MyAI_Lab/zenn-content/.claude/agents/`、script の対象外で手動 diff） |

共通 env: origin filter `shimo4228` (`HARNESS_SYNC_ORIGIN`)、source (`HARNESS_SYNC_SOURCE`)。source の既定は
`~/.claude` だが、正本を移設した 3 repo（citation-sync / paper-ecosystem / writing-ecosystem）だけは
script 側の既定が移設先を指す（RFC-0019 手段 A）。既定以外を使うときは env で上書きする。

### 手動 diff 確認が残る対象（script が置換しないもの）

skill 本体の drift は script が拾う。手動 diff の対象は **script が置換しない同梱物だけ**:

- **agents/*.md**（`claude-skill-paper-ecosystem` / `claude-skill-writing-ecosystem` の
  同梱 subagent。正本は writing 系 6 本が `~/MyAI_Lab/zenn-content/.claude/agents/`、
  paper 系 5 本は `~/MyAI_Lab/paper-lab/.claude/agents/`）
- **hook script**（例: skill-stocktake の `hooks/log-skill-usage.sh`。正本 `~/.claude/hooks/`）
- **repo root の `inspiration.md`**（repo 固有文書。harness に正本なし — diff 対象外だが、
  `skills/<name>/` 配下に置くと置換で消えるため root に置く。2026-07-03 に 3 repo で root へ移動済み）

**script を置かない repo**: 汎用化 fork の curated repo（`code-and-llm-collaboration`,
`llm-agent-security-principles` — 意図的に乖離、diff 同期しない）と、harness に正本を
持たない repo 単独 skill（`agent-adoption-triage` 等）。新しい単独 skill repo を作ったら
**script を vendor するのが default** — 例外にする場合はここに理由ごと追記する。

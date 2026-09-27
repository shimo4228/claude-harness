# 記事執筆系 skill/agent の zenn-content 移設

## Context

2026-08-29 に paper 系 skill 6 本 + agent 5 本を `~/MyAI_Lab/paper-lab` へ移設した（RFC-0017 手段 D: 内容無改変で project scope へ隔離、global 側はルーティング注記のみ更新。`~/.claude` commit b0cbacf / paper-lab 3a6abd1 が先例）。同型で記事執筆系を `~/MyAI_Lab/zenn-content` へ移す。zenn-content には既に `.claude/skills/`（article-stocktake ほか 4 本）、`.claude/agents/`（devto-translator）、`.claude/rules/publishing-channels.md`（publication channel contract）があり、受け皿は整っている。

著者決定（AskUserQuestion 回答 + 追加指示）:
- 移設範囲は**コア 3 skill + 6 agent のみ**。グレー 4 本（headline-craft / prose-translation / x-draft / public-comment）は global 残留。**collect-context も global 残留**（いろんなセッションで使うため — 2026-08-29 著者指示）
- AI-slop 禁止リスト（`writing-ecosystem/references/style-diagnostics.md`）は writing-ecosystem ごと zenn-content へ移し、global の readme-writer / llms-txt-writer は zenn-content 内のパスを正本参照する（paper-lab 注記と同型）

## 移設対象

Skills（`~/.claude/skills/` → `zenn-content/.claude/skills/`、内容無改変が原則）:
- `writing-ecosystem`（references/ 2 ファイル込み）
- `quality-gate`
- `session-theme-mining`（uv プロジェクト実体。**`.venv` / `__pycache__` / `.pytest_cache` / `.ruff_cache` はコピーしない** — paper-lab で 9.6MB の .venv が物理コピーされた反省）

Agents（`~/.claude/agents/` → `zenn-content/.claude/agents/`）:
- `editor.md`, `essay-reviewer.md`, `prose-clarity-reviewer.md`, `theme-reviewer.md`, `title-reviewer.md`, `fact-checker.md`

唯一の内容改変 = 自己参照絶対パスの書き換え（移設で即壊れるため）:
- `session-theme-mining/SKILL.md:28,68,101` の `uv run --directory ~/.claude/skills/session-theme-mining` → `~/MyAI_Lab/zenn-content/.claude/skills/session-theme-mining`

## 手順

### 0. 前提確認
- 両 repo の `git status` を確認。`~/.claude` は先行 3 commit（411e62e / b0cbacf / 1985a37）が未 push だが、本作業はローカル commit までなので支障なし。dirty な場合は移設関連ファイルだけを stage する（並行セッション巻き込み防止 — memory の staging 規約に従い承認後に add→commit を一気に）

### 1. zenn-content 側（receive commit）
1. `cp -R`（除外リスト付き）で 3 skill + 6 agent を `.claude/skills/` / `.claude/agents/` へ。既存の article-stocktake 等とマージ配置
2. 自己参照パス 3 箇所を書き換え
3. `.gitignore` に `.venv/` `__pycache__/` `.pytest_cache/` `.ruff_cache/` を追記（既存 .gitignore の有無を確認して整合）
4. `CLAUDE.md` の "Writing harness" 節を更新: 「entrypoint は global の writing-ecosystem」→「本 repo 常駐（`.claude/skills/writing-ecosystem`）。他 repo の記事作業は `claude --add-dir` か本 repo から起動」（paper-lab CLAUDE.md と同型の文言）
5. commit（例: `feat(harness): 記事執筆系 skill 3 本 + agent 6 本を ~/.claude global harness から移設`）

### 2. ~/.claude 側（remove + pointer commit）
1. `git rm -r` で 3 skill、`git rm` で 6 agent
2. ポインタ更新（paper-lab の b0cbacf と同型、各 1〜数行の注記）:
   - `skills/implementation-chain/SKILL.md:148` — writing ルーティング行に「正本は `~/MyAI_Lab/zenn-content`」注記（:149 の paper 行と同型）。`:161-171` の editor / essay-reviewer / fact-checker verdict 参照にも常駐先が分かる 1 行
   - `skills/readme-writer/SKILL.md`（:26,137,139,161,214,249,251 のうち writing-ecosystem / prose-clarity 系参照行）+ `references/readme-judge-checklist.md:44` + `scripts/readme_evidence.py:90` — banned list 正本パスを `~/MyAI_Lab/zenn-content/.claude/skills/writing-ecosystem/references/style-diagnostics.md` へ
   - `skills/llms-txt-writer/SKILL.md:23,282`、`skills/jsonld-knowledge-graph/SKILL.md:386` — writing-ecosystem への route に常駐先注記
   - `skills/collect-context/SKILL.md:83,84` — session-theme-mining の `uv run --directory` パスを zenn-content の新パスへ（collect-context 自体は global 残留）
   - `skills/session-judgment-mining/SKILL.md:114`（session-theme-mining 境界）に常駐先注記。`skills/rules-distill/SKILL.md:112` は collect-context 残留につき変更不要
   - `agents/readme-reviewer.md:21,169,179`、`agents/readme-clarity-reviewer.md:117`、`agents/readme-judge.md:122` — 記事系へのルーティング先に常駐先注記
   - `skills/headline-craft/SKILL.md` — NOT for 行の title-reviewer 参照に常駐先注記（headline-craft 自体は残留）
   - `skills/harness-sync/SKILL.md:231, 242-244` — `claude-skill-writing-ecosystem` の正本 path を zenn-content へ書き換え、「script の source 更新が次回 sync 時に必要」と TODO 明記（paper-lab と同方式。`sync-from-local.sh` 実修正は次回 sync 時）
3. `rfcs/0017-skill-description-residency-optimization.md` の Status に 1 行追記（手段 D の第 2 適用: 記事系 → zenn-content）
4. memory: `project_paper_lab_relocation.md` と同型の 1 件を新規作成（`project_zenn_writing_relocation.md` — 「記事系は zenn-content 常駐、global に無いのは正常、他 repo は --add-dir」）+ MEMORY.md に 1 行
5. commit（例: `refactor: 記事執筆系 skill 3 本 + agent 6 本を ~/MyAI_Lab/zenn-content へ移設 (RFC-0017 手段 D 第 2 適用)`、本文に zenn-content 側 commit hash を記載）

## 移設しないもの（決定済み）

- `collect-context` — global 残留（記事以外のセッションでも素材収集に使うため。著者指示）
- `headline-craft` / `prose-translation` / `x-draft` / `public-comment` — global 残留（zenn セッションからも引き続き使える）
- `wiki-harvest` / `authorship-strategy` — 記事執筆ではない
- harness-sync の同期 script 実修正 — 次回 sync 時（TODO 注記のみ）

## Verification

- `~/.claude`: `grep -rn "writing-ecosystem\|quality-gate\|session-theme-mining\|essay-reviewer\|prose-clarity-reviewer\|theme-reviewer\|title-reviewer\|fact-checker\b" skills/ agents/ rules/ hooks/` — 残存参照が全て常駐先注記付きであること（ADR / rfcs / results.json は履歴なので対象外）
- `~/.claude`: `scripts/harness_lint.py` があれば実行して green
- zenn-content: 移設ファイルと元ファイルの diff が自己参照パス書き換えのみであること（`diff -r` を git rm 前に実施）
- zenn-content: `uv run --directory .claude/skills/session-theme-mining pytest`（venv 再生成込みで通ること）
- zenn-content でセッション起動時に skill 一覧へ載る前提の frontmatter YAML 検査（paper-lab の verify.sh の frontmatter 検査と同等の python one-liner）

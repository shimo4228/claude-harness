# llm-as-judge TypeSafe Jev 対応 — 下調べ結果（read-only）

## A. 消費者の参照分類

分類: (a) skill名のみ / (b) ①②③番号 / (c) 節見出し名の引用 / (d) 構造（binary証拠・named verdict・集計しない）への依存

| file:line | 種別 | 内容 |
|---|---|---|
| skills/harness-boundary/SKILL.md:38 | (a) | evals ツール一覧の表内、skill名のみ |
| skills/loop-design-check/SKILL.md:3 | (a) | frontmatter description の NOT for、skill名のみ |
| skills/loop-design-check/SKILL.md:22 | (d) | "binary checks, one holistic verdict, no scores" = 契約の言い換え |
| skills/loop-design-check/SKILL.md:87 | (d) | "binary evidence checks, one named holistic verdict, no scores to threshold" 言い換え |
| skills/loop-design-check/SKILL.md:106 | (a) | 表内、skill名のみ |
| skills/loop-design-check/SKILL.md:150 | (d) | Related節、契約の言い換え反復 |
| skills/loop-design-check/SKILL.md:155 | (a) | lineage 注記、skill名のみ |
| skills/harness-sync/SKILL.md:223 | (a) | repo mapping 表の1行、skill名+repo対応のみ |
| skills/codex-review/SKILL.md:84 | (d) | "score なし、集計なし" = 原則③の言い換え |
| skills/skill-stocktake/SKILL.md:397 | (c)+(d) | "binary screen → pressure-test → holistic named verdict" = 節見出し順＋契約の言い換え |
| skills/skill-stocktake/results.json:142-143 | (a) | メタデータ、path のみ |
| skills/task-triage/SKILL.md:288 | (a) | Related、skill名＋用途1行のみ |
| skills/review-to-lint/SKILL.md:3 | (a) | NOT for、skill名のみ |
| skills/learn-eval/SKILL.md:253 | (c)+(d) | "Step 5 is its N=1 implementation" — llm-as-judge を canon として引用、内容は言い換え |
| skills/measurement-discipline/SKILL.md:3 | (a) | NOT for、skill名のみ |
| skills/skill-creator/SKILL.md:99 | (d) | "各問 Yes/No + 1行証拠、非Keepなら反証1–3問" — Verdict pressure-test節の"1–3"に数値まで依存 |
| agents/readme-judge.md:18 | (c)+(d) | "判定形式の正本" として SKILL.md を明示引用、二値チェック→反証PT→集計しない、の順序に依存 |
| skills/readme-writer/references/readme-judge-checklist.md:9 | (d) | 同上の言い換え反復 |
| docs/adr/0046-...md:79 | (c) | "llm-as-judge の Related を更新する" — "Related" 見出し名を名指し（過去のアクション項目、実行済み） |
| docs/adr/0068-...md:41 | (a) | 利用実績の引用例、構造依存なし |
| rfcs/0005-review-to-lint-rollout-ledger.md:81 | (a) | "理論的正本" として skill名のみ |
| rfcs/0017-skill-description-residency-optimization.md:94 | (a) | disable-model-invocation 対象リスト、skill名のみ |
| **rfcs/0024-typesafe-jev-as-offload-for-max-quota.md:40** | (d) | "binary Yes/Noを証拠に集め、集計せずnamed verdict" — 契約の直接引用 |
| **rfcs/0024-typesafe-jev-as-offload-for-max-quota.md:73** | **(b)** | **"llm-as-judge ③ が正本"** — 原則③を番号で明示引用 |
| **rfcs/0025-jev-decision-contract-registry.md:31** | **(b)** | **"集計しない。生の読み値を残す（llm-as-judge ③）"** — 原則③を番号で明示引用 |
| rfcs/0026-jev-agent-trace-sensor.md:40 | (d) | "binary証拠を集め、集計せず、named verdict" — 契約の言い換え |

**結論（A）**: `## The three principles` の表（SKILL.md:35-39）と `### ① / ② / ③` の3小見出し（41/48/61行）を**動かさず・増やさず**、新しい節を追加するだけなら、上記どの参照も壊れない。
危険なのは番号を4つ目（④）に増やす、または①②③の意味・順序を変えること — その場合 **rfcs/0024:73** と **rfcs/0025:31** の `llm-as-judge ③` という明示番号参照が直接壊れる。この2本は本改修と同じ TypeSafe Jev 文脈の RFC であり、優先して壊さないこと。
"Related" 節（170行〜）は ADR-0046:79 で過去に名指しされた実績があるので、見出しテキスト "## Related" は保持し、新規の TypeSafe Jev 関連リンクを追記する形が安全。
rules/, tests/, scripts/ 配下には llm-as-judge への参照は0件（grep 実行済み、ヒットなし）。

## B. 公開 repo `~/MyAI_Lab/llm-as-judge`

- ファイルツリー: `CHANGELOG.md`, `LICENSE`(MIT, shimo4228), `README.md`(41行), `llms.txt`, `scripts/sync-from-local.sh`, `skills/llm-as-judge/SKILL.md` のみ。**scripts/ tests/ examples/ 等は無い**。
- README見出し: `# llm-as-judge` / `## Install`(`### Claude Code`, `### SkillsMP`) / `## What's Inside` / `## When It Triggers` / `## References` / `## License`。**言語版なし**（日本語版READMEは存在しない）。
- `.github/workflows` 無し（**CI なし**）。
- `git log --oneline -10`: 7 commit（scaffold → v1.0.0 sync → compatibility frontmatter → skill-stocktake full run → 3回の sync）。`git status --short`: 空（clean）。
- `scripts/sync-from-local.sh` 要点:
  - 同期対象は「このrepoの `skills/*/` に既に存在するディレクトリ名」から逆算（repo自身が公開物を宣言する設計）。
  - 各skillについて `~/.claude/skills/<name>/` を**ディレクトリごと丸ごと `cp -R`**（SKILL.md 限定ではない）。
  - 除外されるのは `results.json` `*.log` `*.pyc` `.DS_Store` `.coverage*` と `__pycache__` `.pytest_cache` `.venv` `node_modules` `.mypy_cache` `.ruff_cache` `htmlcov` ディレクトリのみ。
  - **`scripts/` `tests/` `pyproject.toml` `uv.lock` 等は除外パターンに無いので、正本側 `~/.claude/skills/llm-as-judge/` に足せばそのまま同期される**（readme-writer / skill-stocktake / agent-stocktake / context-sync が実例、後述）。
  - root ファイル（README/LICENSE/llms*.txt/CHANGELOG）は触らない。commit はしない（`git diff` が review gate）。
  - frontmatter YAML検証・secret scan あり。

`skills/harness-sync/SKILL.md:223`: `llm-as-judge` 行 = 「単独skill」種別、`scripts/sync-from-local.sh`(skill repo版)、正本 `~/.claude/skills/llm-as-judge`。
**scripts/tests 同梱の単独skill repo 先例**（同表内）: `readme-writer`(206行), `skill-stocktake`(213行), `agent-stocktake`(214行), `context-sync`(221行) — いずれも `skills/<name>/scripts/` `skills/<name>/tests/` `pyproject.toml` `uv.lock` を持ち、実際に `~/MyAI_Lab/<name>/skills/<name>/` に同期済み（`find` で確認）。`jev-skill-router` は同表に**行がまだ無い**（公開repo化前、または対象外）。

## C. jev-skill-router 先例（`~/.claude/skills/jev-skill-router/`、read-only）

ツリー: `SKILL.md`(origin: shimo4228) / `pyproject.toml` / `uv.lock` / `LICENSE` / `scripts/{jev_client.py, decision_log.py, router.py, roster.py, route.py}` / `tests/{conftest.py, test_jev_client.py, test_roster.py, test_route.py, test_router.py, golden/README.md, golden/inject-envelope.json}`。

- `scripts/jev_client.py`(174行): `read_api_key_file(path)`(72), `resolve_api_key(env)`(95), `check_endpoint(url)`(109), `class JevClient.__init__(api_key, *, base_url=None)`(129), `.endpoint`(134), `.ask(state, questions, *, model, timeout)`(137)。
  key解決順（95-106行）: `TYPESAFE_API_KEY` env → `JEV_ROUTER_KEY_FILE` env が指すファイル → `~/.config/typesafe/api_key`（デフォルト、37行 `DEFAULT_KEY_FILE`）。**このファイル自体は本調査で読んでいない**（指示遵守）。
  エラー方針: 例外は全て `JevError` に正規化（41行）。redirect 拒否（45-65行、鍵の平文漏洩防止）。`http/https` scheme と loopback 限定チェック（109-123行）。呼び出し元(route.py)側が fail-open。
- `scripts/decision_log.py`(104行): `utc_now()`(25), `digest(text)`(29), `build_record(*, project, session, mode, model, router_version, question_hash, roster_hash, n_skills, n_by_source, prompt, elapsed_ms, ...)`(33), `append(path, record) -> bool`(83)。append は例外を投げず `False` を返す設計（92-104行）。symlink 攻撃対策（`O_NOFOLLOW`）。
- `scripts/router.py`(386行): `question_hash()`(114), `build_state(request)`(132), `chunk_roster(roster, size)`(136), `rank_wide(client, request, roster, ...)`(173), `rerank(client, request, candidates, ...)`(250), `_decide(winner, fits, threshold, margin)`(296), `suggest(client, request, roster, ...) -> Suggestion`(323), `suggestion_block(name)`(380)。
- `scripts/route.py`(272行、hookエントリポイント): **fail-open が全体の契約**（2-17行コメント）。`main()`(259) は全例外を握りつぶし常に `exit 0`。`_run()`内(195-200行)で `router.suggest` を try/except し、失敗を `reason` としてログに残すのみ（例外を上げない＝fail-open）。
- テスト置き場: `tests/`直下（pytest）。実行方法は `uv run --project <dir> --directory <dir> pytest -q`。
- `.claude/verify.sh`(≡ `~/.claude/.claude/verify.sh`) 409-432行: `git_files_exec 'skills/*/pyproject.toml'` で pyproject.toml を持つ sub-project を列挙 → `tests/` ディレクトリが実在するものだけ対象 → `skills/<name>/SKILL.md` の `origin:` が `shimo4228`/`auto-extracted`/`skill-create`/`ECC-customized` のいずれかでなければスキップ（外部origin skillは検査しない）→ `uv run --project ... pytest -q` を実行。**現状 `llm-as-judge` はこの条件に乗らない**（pyproject.toml も tests/ も無いため；origin: shimo4228 は満たす）。
- `tests/golden/README.md`: golden (`inject-envelope.json`) は「stdoutの全体shapeを凍結」する。更新は**タスクがその出力変更を明言した時のみ正当**、無関係な変更でredになったら「検出器が働いた」ものとしてインシデント報告、repaintしない。harness本体の `tests/golden-*.bats` とは別に、公開単独repoとして travel するため `skills/jev-skill-router/tests/golden/` に置く、という配置理由も明記。

## D. `~/.claude/skills/llm-as-judge/` 現ツリー

`SKILL.md` **のみ**（197行）。scripts/ tests/ pyproject.toml/uv.lock/references/ 等は一切無い。frontmatter: `origin: shimo4228`, `disable-model-invocation: true`, `license: MIT`。節構成（既存・動かさない前提）: Why not rubric scores → The three principles（①②③、35-39行の表＋41/48/61行の小見出し）→ Verdict pressure-test → Scale the machinery, not the principles → Don't let deterministic checks ride on judgment → Judge prompt template → Related（170行〜）→ References（184行〜）。

## 未確認・推測に留めた点
- `~/MyAI_Lab/llm-as-judge` の harness-sync 表への `jev-skill-router` 行の不在は「まだ公開repo化していない」ことの傍証であり断定ではない（推測）。
- ADR-0046:79 の "Related を更新する" 指示が実際にいつ・どう実行されたかは本調査では未追跡（現在のRelatedの4項目がその結果かは未検証、推測）。

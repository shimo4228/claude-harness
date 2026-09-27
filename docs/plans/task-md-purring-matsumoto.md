# T-005 消化 + セキュリティ層再編

## Context

`.notes/TASKS.md`（この repo の単一台帳）の **T-005** は、2026-07-25 の `skill-stocktake` full 監査が出した非 Keep verdict 15 件のうち、その場で直した 5 件を除く **未処理 10 件**を消化するタスク。verdict の自己完結した理由は `skills/skill-stocktake/results.json` にあり、台帳行がタスクの正本。

grill で前提が 1 つ崩れた。10 件のうち `security-scan` の「flag 表が stale」verdict は、**1 行修正では済まない**ことが判明した：

1. `origin: ECC`（未改変・mtime 2026-03-03 で約 5 ヶ月未使用）。flag を書き足せば `ECC-customized` に落ち、上流 diff の基準線を失う。しかし ECC 追従は ADR-0008 で既に停止済みで、規律を守るコストだけが残っている
2. **2026-07-22 に公式 `claude-security` プラグインが beta 公開された**（`/plugin install claude-security@claude-plugins-official`、Claude Code v2.1.154+ / 有料プラン。ローカルは v2.1.220 で要件充足）。全リポジトリスキャン + 差分スキャン + `.patch` 生成を 1 コマンドで持ち、バンドル済み `/security-review`（branch 差分のみ）を機能的に包含する
3. これは ADR-0018 が言う **downward dissolution** の再発。T-004（`implementation-chain` の Review 行がビルトインを知らない）と同じ構図が、セキュリティ層でも起きていた

**意図する結果**: 9 件の 1 行修正を片付けて監査台帳を clean にし、加えて第三者 npm 依存（`affaan-m/agentshield`）を harness から外して公式プラグインに寄せる。

## 決定事項（grill で確定）

- 対象は T-005。T-001/T-002/T-003/T-004 は着手条件未達または要調査のため今回は触らない
- `claude-security` を導入し、`security-scan` は**退役**する
- ただし退役は **Phase B として分離**する。9 件の 1 行修正（Phase A）を人質にしない

## Phase A — 9 件の 1 行修正（1 commit）

いずれも独立。順不同で可。

| 対象 | 修正内容 |
|---|---|
| `skills/citation-sync/SKILL.md` | L11「引用は **4 つの層**に現れる」→ 3 層に。Pitfalls 表の生きている Wikidata 行 2 本（L68「Wikidata だけ先に膨らませる」／L74 の「zenodo + wikidata のみで carry」）を retire 済み表現に。L26 の埋め込み `--help` と L31 の Wikidata 層解決の記述を always-skip 規約と整合させる |
| `skills/citation-sync/scripts/citation_audit.py` | docstring L9/L14 が wikidata を監査対象層として列挙し `--skip-wikidata` を optional 扱い → SKILL.md の always-skip 規約と矛盾。docstring を 3 層に、`--skip-wikidata` の help を「retired 層。既定で skip」に |
| `skills/cited-source-mirror-verification/SKILL.md` | worked check の唯一の mirror 探索コマンドが Wikidata `list=search` で、自分の例に対し totalhits=0 を返す。上位 mirror（aiXiv / OpenAlex / Semantic Scholar）の**実行可能なコマンド**に差し替える。**着地前に実際に叩いてヒットを確認する**（同じ失敗の再生産を防ぐ） |
| `skills/hunk-review/SKILL.md` | hunk 0.17.1 の `session review --include-notes` と `comment clear --include-user\|--all` が未記載。追記する。`origin: modem-dev/hunk` は外部だが上流は生きたツールで日常使用中のため追従は正当 |
| `skills/iterative-retrieval/SKILL.md` | description が題名の 13 語言い換えで trigger phrase も NOT-for 節もなく、body の "When to Activate"（具体トリガー 5 件）より貧しい。body の 5 トリガーを取り込んだ description に書き換える。**仮定**: user-invocable 化はしない — 自発トリガー上限 ≒ 40% の pivot 判断は「発火させたいのに立たない」場合の措置で、本 skill はまず frontmatter が body より貧しい状態を解消するのが先。加えて 402 を返す x.com status 引用を削除 |
| `skills/jsonld-knowledge-graph/SKILL.md` | L325「2024-12 にアーカイブ済み」→ 実際は 2025-09-26。Build verdict 自体は維持（今もアーカイブ済み） |
| `skills/paper-ecosystem/SKILL.md` | L326-327 の overlay 例 2 パスが不存在（repo はあるが `.claude/rules/` が無い）。「既存例」ではなく**命名規約**として提示し直す |
| `skills/learned/claude-code-tool-patterns.md` | §1「Hook Command JSON Escape Trap」は `rules/common/hooks.md` に完全吸収済みの promotion residue（しかも相互リンク）。§1 を back-pointer 1 行に trim。§2（Chrome/SPA）・§3（YAML colon-space）は未吸収なので温存 |
| `skills/learned/docker-local-llm-tradeoff.md` | 判断表に **Docker Model Runner**（macOS Apple Silicon 対応）が欠落。host-vs-container の 2 分法に第 3 分岐として追加。中核クレーム（GPU passthrough は Windows/WSL2 のみ）は検証済みで維持 |

なお `learned/claude-code-headless-automation.md`（verdict = Update、`claude -p "/skill-name"` が有効になった件）は **T-005 の 10 件目**だが、既に台帳作成後に処理済みか要確認 → `git log` で照合し、未処理なら Phase A に含める。

## Phase B — セキュリティ層再編（別 commit）

**Step 1（先に事実を取る）**: `/plugin install claude-security@claude-plugins-official` → `/reload-plugins` → `/claude-security` を `~/.claude` に対して 1 回走らせる。観察点は **agent 定義・settings.json・mcp.json のような設定成果物を対象に含めるか**。ここが Step 3 の分岐を決める（推測で進めない）。

**Step 2**: `skills/security-scan/` を削除。`rules/common/coding-style.md` の Reversibility Gate に従い、git 追跡下なので `git rm` で足りる（履歴が soft-delete 層）。

**Step 3 — 参照 repoint（計 5 ファイル・10 箇所）**:

| ファイル | 箇所 |
|---|---|
| `rules/common/security.md` | L21 `See skill: security-scan` → `/claude-security` |
| `skills/agent-architecture-audit/SKILL.md` | L31, L252 |
| `skills/config-gc/SKILL.md` | L118 |
| `skills/skill-health/SKILL.md` | L3(description の NOT-for), L61(判断表), L66, L113-114, L140 |
| `skills/skill-health/pyproject.toml` / `scripts/scan_refs.py` | description L4 / L14, L119 |

**`skill-health` の risk 次元が最大の論点**。4 次元モデル（structural / semantic / risk / validation）の risk を丸ごと `security-scan` に委譲しているため、単純な名前置換では済まない。Step 1 の観察に応じて分岐：

- **claude-security が設定成果物を見る** → risk 次元の委譲先を `/claude-security` に差し替え。4 次元モデル維持
- **見ない（コード脆弱性のみ）** → risk 次元を「エージェント設定衛生」として明示的に**空席**にし、`skill-health` の description と判断表にその旨を書く。埋めるなら skill ではなく決定論 hook が適切（`rules/common/hooks.md`: 品質強制・セキュリティチェックは hook、5 ヶ月発火していない skill は選択肢にならない）。hook 化は台帳に新タスクとして起票

**Step 4 — ADR 起票（`/adr-writer`）**。3 条件すべてを満たすため必須：

- 不可逆寄り（skill 削除 + 参照グラフの張り替え）
- 文脈なしでは驚く（**ADR-0011 が `security-scan` を明示的に Keep 判定している** — 「AgentShield wrapper として固有機能」）
- 実在の代替との trade-off（設定監査の軸は claude-security が自動で埋めるとは限らない）

ADR-0011 は Negative 節で「退役根拠が built-in の存在であるため、将来 built-in 構成が変わると再判断が要る」と自ら書いており、**その条件が現実化した**という形で override を正当化する。新 ADR は ADR-0011 と ADR-0018（downward dissolution）を参照し、T-004 が扱う `implementation-chain` の Review 行再監査と同根であることを記録する。

**Step 5**: `.notes/TASKS.md` を同じ作業内で更新（`rules/common/task-tracking.md`）。T-005 を Done 節へ移動、Phase B で判明した hook 化課題があれば新規行を追加。T-004 の詳細欄に本 ADR へのリンクを足す（同根の証拠が 1 件増えたため）。

## 再利用する既存資産

- `/adr-writer` skill + `adr-writer` agent — ADR 採番・衝突回避・index 更新まで決定論的に処理する。手書きしない
- `skills/skill-health/scripts/scan_refs.py` — dangling reference の構造検出器。**Phase B の Step 3 完了後にこれを走らせて repoint 漏れを検証する**（`patterns.md` の「documented-invariant → ゲート化」の実践。ただしこのスクリプト自身も repoint 対象なので、修正後に走らせる）
- `skills/skill-stocktake/results.json` — 監査台帳。Phase A/B 完了後に再生成するか、該当エントリの verdict を更新する

## Verification

`rules/common/planning.md` の Verify ゲート（該当項目のみ。本作業は Markdown + 1 Python ファイルなのでビルド・型検査は対象外）：

1. **構造検証** — `python3 skills/skill-health/scripts/scan_refs.py`（または `/skill-health`）を走らせ、`security-scan` への dangling reference が **0 件**であることを確認。Phase B の repoint 漏れはここで機械的に落ちる
2. **YAML 検証** — description を書き換えた `iterative-retrieval` / `skill-health` の frontmatter を parse して確認。`: ` が YAML を壊す既知の罠（memory: `reference_skill_creator_loop_gotchas`）があるため、書き換え後は必ず検証する
3. **listing 確認** — `/doctor` で skill 数と listing 文字数を取り、`security-scan` が消えて 1 本減っていること、文字数が減っていることを確認（T-002 の実測値の更新にもなる）
4. **実行検証** — `cited-source-mirror-verification` に新しく書いた mirror 探索コマンドを実際に叩き、skill 自身の例で **ヒット > 0** を確認（この verdict の原因が「動かないコマンドを教えていた」ことなので、ここを検証しないと同じ欠陥を再生産する）
5. **citation_audit.py** — `python3 skills/citation-sync/scripts/citation_audit.py --help` を実行し、docstring と help が 3 層 + always-skip 規約に一致していることを目視確認
6. **secret scan** — commit 前に PreToolUse hook が staged diff に対して自動実行（`rules/common/security.md`）
7. **`git status` 確認** — 意図しないファイルが含まれていないか

Phase A・Phase B は別 commit。Phase B は Step 1 の観察結果をユーザーに報告してから Step 2 以降に進む（skill 削除 + ADR override は Reversibility Gate の確認対象）。

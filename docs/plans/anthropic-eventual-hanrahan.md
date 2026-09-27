# Anthropic 公式 plugin / skill の harness 照合（2026-08-22）

## Context

著者の所感「Anthropic 公式のものが一番良い」を受け、公式カタログ 3 系統
（`claude-plugins-official` 39 本 / `anthropics/skills` 19 本 / `knowledge-work-plugins` 11 本。
`claude-community` 2282 本は Anthropic 作 0 で対象外）を harness（自作 48 + ECC-customized 11 +
他 6 skill、agent 22、hook 18）と突き合わせた。判断基準は ADR-0011 / akc-cycle の
**downward dissolution**: substrate か公式が同じ能力を持つなら手書きを薄くする。逆に、
公式が built-in（`/code-review` `/simplify` `/security-review` `design` `claude-api` …）と
重複しているものは入れない。

## 判定

### A. 取り込む（2 本）

| plugin | 理由 | harness 側の扱い |
|---|---|---|
| **session-report**（skill 1 本、`analyze-sessions.mjs` で transcript を集計 → HTML） | harness には skill/agent の発火ログ（`log-skill-usage.sh` / `log-agent-usage.sh`）はあるが、**token / cache / subagent コストの可視化は無い**。並行セッション艦隊のコスト把握に効く。read-only、常駐コスト 0 | `claude plugin install session-report@claude-plugins-official`。何も置き換えない |
| **pr-review-toolkit**（agent 6 + `/review-pr`） | `code-reviewer` / `code-simplifier` は built-in と重複だが、**`silent-failure-hunter`**（握り潰された error / 不適切な fallback）は harness の Review 軸（bug = `/code-review`、quality = `/simplify`、security = `security-reviewer`）の**どれにも無い軸**。`pr-test-analyzer` は tdd の coverage 数値ではなく「テストが意味を持つか」を見る | install のうえ、`skills/implementation-chain/SKILL.md` の Review 表に **条件付き行**を 1 つ足す: 「diff に catch / fallback / retry / default 値の追加があるとき `silent-failure-hunter`」。`/review-pr` コマンド自体と残り 4 agent は自発起動させない（`agents.md` の既存方針どおり実装者と別 process で呼ぶ） |

### B. 整理する（installed-but-disabled の 2 本を uninstall）

| plugin | 理由 |
|---|---|
| **claude-code-setup**（automation recommender） | recommender 系は成熟 harness で構造的に機能しない（memory: feedback_skill_design_intent）。disabled のまま 1 度も使っていない |
| **claude-md-management**（CLAUDE.md improver） | `context-sync` が CLAUDE.md を含む context 文書全体の role overlap / freshness を扱い上位互換。CLAUDE.md 単体の品質基準は公式 `references/quality-criteria.md` が参考になるので、**uninstall 前に `context-sync` の CLAUDE.md 節と 1 回突き合わせ**、差分があればそちらへ吸収 |

`claude plugin uninstall <name>@claude-plugins-official`（user scope、復元は再 install で可）。

### C. 見送り（理由を 1 行ずつ。再評価条件つき）

| plugin / skill | 理由 | 再評価条件 |
|---|---|---|
| code-review / code-simplifier / explanatory-output-style / learning-output-style | built-in と同一 | — |
| security-guidance（edit ごと pattern 警告 + Stop で LLM diff review） | secret-scan / bandit / `security-reviewer` / claude-security で軸が埋まっている。毎 edit に Python hook が走る常駐コストも重い | claude-security を外したとき |
| feature-dev（explore → architect → implement） | `implementation-chain` + Plan agent + `architect` と同型。chain は種別分岐を持つぶん強い | — |
| commit-commands | `git-workflow` と precommit hook 群（secret / verify / lint / review-notice）を迂回する | — |
| plugin-dev（7 skill + validator agent） | herdr-toolkit / claude-harness の公開で plugin を触るのは年数回。常駐させず **必要時に install → 終わったら uninstall** の lazy 運用 | 次に plugin manifest を書くとき |
| receipts / project-artifact / ralph-loop / code-modernization / mcp-* / math-olympiad / cwc-makers / agent-sdk-dev | solo 研究 harness に需要信号なし。install-and-hope は ECC 評価で棄却済みの型 | 需要が出たとき |
| anthropics/skills: docx / pdf / pptx / xlsx | 2026-05 の判断どおり lazy import | 文書生成が要るとき |
| anthropics/skills: webapp-testing / design 系 / internal-comms 等 | 自前 e2e が上位、design 系は built-in `design` / `artifact-*` が既に substrate | — |
| knowledge-work-plugins（11） | Cowork 向け、Slack/Notion/Jira 等 MCP 前提。研究 harness と無関係 | — |
| LSP 追加（typescript 等） | 焦点は Python / Swift。pyright / swift は有効化済み | TS project が常設になったとき |

### D. 置き換え候補として検査した結果「現状維持」

- **skill-creator**: ローカル版（`anthropics/skills-customized`, SHA `b9e19e6f`, 2026-05-20）。
  upstream `anthropics/skills` は 22 commit 先だが `skills/skill-creator/` に変更なし、
  公式 plugin 版との本文差も 23 行（ローカル customization 分）。**drift なし → 維持**。
  plugin 版へ乗り換えると run_loop 等の customization を失う
- **hookify / claude-security / pyright-lsp / swift-lsp**: 既に公式 plugin で運用中。変更なし
- **e2e / e2e-runner** vs webapp-testing: 2026-05 判断を維持

## 実行手順（承認後）

1. `claude plugin install session-report@claude-plugins-official`
2. `claude plugin install pr-review-toolkit@claude-plugins-official`
3. `skills/implementation-chain/SKILL.md` の Review 表に silent-failure-hunter の条件付き行を追加
   （origin 行は変えない。`agents.md` rule には追記しない — catalog の正本は plugin 側 frontmatter）
4. `claude-md-management` の `references/quality-criteria.md` を `skills/context-sync/SKILL.md` の
   CLAUDE.md 節と突き合わせ、吸収する項目があれば編集
5. `claude plugin uninstall claude-code-setup@claude-plugins-official` /
   `claude plugin uninstall claude-md-management@claude-plugins-official`
6. memory `reference_anthropic_skills_imports.md` に本照合の 1 行ログ（日付・採否・理由）を追記
7. `git -C ~/.claude status` → implementation-chain / context-sync の差分を commit
   （`harness-lint-precommit` が通ること）

## 検証

- `claude plugin list` に session-report / pr-review-toolkit が enabled、setup / md-management が無い
- 新セッションで `/session-report 7d` が HTML を出す
- `~/.claude` の bats（`tests/`）が緑、`harness_lint.py` が通る
- 2 週間後: `hooks/log-agent-usage.sh` のログで `silent-failure-hunter` の発火数を見る。
  0 なら条件行を外す（reviewr と同じ退役基準）

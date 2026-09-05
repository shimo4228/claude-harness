# Architecture Decision Records

このハーネス（~/.claude）に関する設計判断を記録する。

## Index

| ADR | Title | Status | Date |
| --- | --- | --- | --- |
| [0001](0001-ecc-skill-management-policies.md) | ECC スキル管理ポリシー | accepted | 2026-03-08 |
| [0002](0002-disable-claude-mem.md) | claude-mem プラグイン無効化 | accepted | 2026-03-08 |
| [0003](0003-regex-to-llm-classification.md) | 正規表現から LLM 分類への転換 | accepted | 2026-03-20 |
| [0004](0004-retire-documentation-rule.md) | documentation.md ルール退役 | accepted | 2026-03-13 |
| [0005](0005-retire-kimi-delegation-rule.md) | kimi-delegation.md ルール退役 | accepted | 2026-03-13 |
| [0006](0006-stop-ecc-contributions.md) | ECC へのコントリビューション終了 | accepted | 2026-03-24 |
| [0007](0007-open-concept-network-effect.md) | 開放型ネットワーク効果 — 概念を囲い込まない公開戦略 | accepted | 2026-03-25 |
| [0008](0008-ecc-local-only-management.md) | ECC ローカル管理一本化 — プラグイン廃止と選択的取り込み | accepted | 2026-03-29 |
| [0009](0009-implementation-chain-front-loaded-in-plan.md) | Implementation Chain を plan に front-load（2介入点モデルは ADR-0035 で退役） | accepted | 2026-05-02 |
| [0010](0010-context-sync-cascade-and-writer-agents.md) | context-sync の cascade 化と writer agent 新設 (codemap-writer / adr-writer) | accepted | 2026-05-22 |
| [0011](0011-retire-builtin-duplicate-skills-and-version-dependent-rules.md) | built-in 重複 skill とバージョン依存 rules の退役 | accepted | 2026-06-10 |
| [0012](0012-cross-tool-skill-sharing-via-agents-skills.md) | クロスツールのスキル共有を ~/.agents/skills 経由に一本化 | accepted | 2026-06-28 |
| [0013](0013-cross-model-review-seam-via-codex.md) | クロスモデルレビュー seam を Codex で開く — 多エージェントは脱相関の一点に限定 | accepted | 2026-06-28 |
| [0014](0014-retire-multi-agent-orchestration-rule.md) | multi-agent-orchestration.md ルール退役 — native 部分は公式ハーネスに委譲 | accepted | 2026-06-30 |
| [0015](0015-cross-agent-rules-sharing-reference-first.md) | クロスエージェント rules 共有は「参照 > 生成 > 同期」— エージェント側アタッチポイント方式 | accepted | 2026-07-18 |
| [0016](0016-writer-agents-render-not-decide.md) | Writer agent は render 専任 — 委譲境界は semantic authority (EN→JA 翻訳は skill-only / adr-writer リーク修正) | accepted | 2026-07-18 |
| [0017](0017-retire-authorship-strategy-rule-absorbed-by-skill.md) | authorship-strategy.md ルール退役 — skill が凝縮重複を吸収 | accepted | 2026-07-19 |
| [0018](0018-rules-rightsize-for-claude5.md) | rules/ の rightsize — Claude 5 世代向け scaffold dissolution（第2波は ADR-0035） | accepted | 2026-07-25 |
| [0019](0019-human-gate-layer.md) | custom human gate（ADR-0035 で substrate 既定へ委譲） | superseded | 2026-07-25 |
| [0020](0020-retire-security-scan-delegate-risk-to-claude-security.md) | security-scan を退役し risk 面を claude-security プラグインへ委譲 — ADR-0011 Keep の override | accepted | 2026-07-26 |
| [0021](0021-rules-metadata-and-premise-lint-gates.md) | rules メタデータ（rationale / review-when）と構造的前提の lint ゲート化 — コメント形式で常駐ゼロ、幽霊参照の再発防止 | accepted | 2026-07-26 |
| [0022](0022-generation-audit-three-sibling-stocktakes.md) | 世代交代監査の 3 兄弟構成 — generation-audit オーケストレータ + agent-stocktake 新設（verdict は stocktake に委譲） | accepted | 2026-07-26 |
| [0023](0023-dissolve-planner-narrow-architect-to-essence-evaluation.md) | planner agent の Dissolve と architect の本質評価専任化 — fresh/rich context 軸によるサブエージェント適性判定 | accepted | 2026-07-27 |
| [0024](0024-dissolve-tdd-guide-and-axis-auxiliary-rationales.md) | tdd-guide agent の Dissolve と fresh/rich 軸の補助則 2 件（frozen-input render / bulk context isolation）— 軸の全 corpus 適用 | accepted | 2026-07-27 |
| [0025](0025-global-vs-project-asset-placement.md) | Global vs Project の資産配置基準を rules/common/skills.md に正本化 — 2+ repo/channel なら global、単一固有なら project overlay | accepted | 2026-07-27 |
| [0026](0026-retire-signal-first-residency.md) | Signal-first 常駐節の退役 — 消費 skill へのインライン内在化完了 + grill-me 質問抑制の衝突コスト（grill-me に Interview mode override と 6 次元停止条件を追加） | accepted | 2026-07-31 |
| [0027](0027-restore-review-execution-check-to-verify-gate.md) | Review 名簿の rules 復元（ADR-0035 で skill 正本 + commit reminder へ） | superseded | 2026-08-01 |
| [0028](0028-review-notice-full-scope-and-adr-reviewer.md) | 3区分検出と adr-reviewer 新設 — classifier は ADR-0035 で退役、adr-reviewer は維持 | accepted（一部 superseded） | 2026-08-01 |
| [0029](0029-skill-comply-parallel-scenarios-and-stderr-progress.md) | skill-comply のシナリオ 3 本を並列実行し、進捗を stderr へ — 無音の真因は stdout バッファでなく `tail` が EOF まで保留すること（実測）。完了順はレポートに漏らさず level 順に固定 | accepted | 2026-08-01 |
| [0030](0030-separate-output-writing-from-residency-register.md) | ユーザー向け出力 register（ADR-0035 で substrate へ委譲） | superseded | 2026-08-01 |
| [0031](0031-child-permission-envelope-via-permissions-deny.md) | 無人の子セッションの封じ込めは `--settings` の `permissions.deny` で行う — `--allowedTools` は自動承認リストでツールを外さない（実測、ADR-0011 期の前提が偽）。F3/F4 の緩和は実際には入っておらず、`--allow-bash` は opt-in として機能していなかった | accepted | 2026-08-02 |
| [0032](0032-skill-comply-measurement-validity.md) | skill-comply は「測定が成立していたか」をレポートの一級市民にする — project skill を Tier 1（stub）/ Tier 2（本文）で測り、`<sandbox>/.claude/` と `.git/` をツール専有にし、`files:` で中身を渡す。読み込めなかった run はスコアから除外し終了コード 1 | accepted | 2026-08-02 |
| [0033](0033-subagent-model-tier-by-downstream-verification.md) | サブエージェントのモデル階層は「その出力を検査する層が下流にあるか」で決める — 決定論ゲートは意味的 review の代替として数えない（planning.md）。`model` 未指定は inherit で親セッションを継承するため全 agent に明示し、harness_lint で決定論化 | accepted | 2026-08-02 |
| [0034](0034-move-review-check-before-the-approval-gate.md) | Review 通知の Stop 配線（ADR-0035 で custom gate とともに退役） | superseded | 2026-08-02 |
| [0035](0035-commit-review-hook-and-rules-rightsize.md) | Commit 前 Review / Verify reminder の薄型化、rules/ rightsize、global when-code-when-llm の退役 | accepted | 2026-08-02 |
| [0036](0036-herdr-toolkit-skills-only-plugin.md) | herdr 系スキルは skills-only plugin (herdr-toolkit) として公開する | accepted | 2026-08-03 |
| [0037](0037-publish-harness-adrs-and-remediate-git-hostile-config.md) | harness ADR を claude-harness へ公開し、前提として commit 面 hook の敵対的 .git/config を無害化する | accepted | 2026-08-08 |
| [0038](0038-publish-curated-commit-hooks.md) | commit 面 hook を curated allowlist で claude-harness へ公開し、前提として抽出器の 2 経路と textconv を塞ぐ — 公開判定は provenance でなく curation。公開前レビューが secret gate の 2 バイパスと 1 RCE を実測、右端一致は左端と対称のため全ターゲット走査へ | accepted | 2026-08-08 |
| [0039](0039-retire-python-reviewer-simplify-in-chain.md) | python-reviewer を退役し、chain を bug 軸 (code-reviewer) × quality 軸 (/simplify) に直交化 — 決定論チェックは verify.sh、idiom は substrate が吸収 (Downward dissolution) | accepted | 2026-08-13 |
| [0040](0040-demote-feat-tdd-to-conditional.md) | feat × TDD を必須から条件付き発火へ降格 — 現行世代で残る価値は RED→GREEN の儀式でなく「実装を見る前に振る舞いを固定する」spec pinning だけ。テストの要否は不変 (coverage floor は Verify が担保) | accepted | 2026-08-15 |
| [0041](0041-file-review-findings-on-a-verified-premise.md) | レビュー指摘の起票条件を severity から前提の検証へ移す — severity は生成器が付ける次元なので受け取り側では濾せない。`claims.py spawn --origin review` に `--producer PATH:LINE` を必須化し、怠けた経路が起票できないようにする。reviewer 定義とルーティング表は変更しない | accepted | 2026-08-16 |
| [0042](0042-retire-code-reviewer-and-scope-security-review-to-threat-surface.md) | ECC 由来 code-reviewer を退役し Code Review を built-in `/code-review` へ、Security Review を `feat` 無条件から脅威面の変化に紐付ける — トリビアの原因は発火頻度でなく repo と一致しない 固定チェックリストだった。security-reviewer は脅威面の導出手順と判例 prior だけを持つ | accepted | 2026-08-16 |
| [0043](0043-task-triage-loop-judge-build-human.md) | タスク台帳を回す loop — 判断は強い階層のセッション、実装は新セッション、最後のスイッチは人間（PR 無し、語彙・機構は増やさない、harvest、1 判断 1 メッセージ） | accepted | 2026-08-17 |
| [0044](0044-adr-review-when-and-dated-annotation.md) | ADR を日付つき仮説として持つ — `## Review-when`（失効条件）節を 0044 以降必須にし、旧 ADR の部分弱化は Status でなく日付つき注記、読み方 protocol（Date / Review-when を先に見る、失効した ADR に拘束力無し）を akc-cycle / grill-me / architect へ。desire-frontier の機構の移植 | accepted | 2026-08-19 |
| [0045](0045-triage-loop-launchd-tick-and-slack-digest.md) | triage loop の timer を session の外（launchd `triage-tick.sh` → `herdr agent prompt`）へ、digest は Slack 片方向（1 判断 1 通 + cycle 末尾 1 行、既存 webhook 流用）、答えは triage セッションの中だけ。session 内 CronCreate / 自己更新は skill から外す。harness 土 08:03、CA 水 17:07 + 土 14:07 | accepted | 2026-08-19 |
| [0046](0046-skill-creator-shrink-in-place-and-creation-gate.md) | skill-creator をその場で縮退（5,826→96 行）し、作成時ゲート（草稿 subagent + skill-stocktake Phase 2 checklist）と命令形配線（rule + PreToolUse hook `skill-create-notice.sh`）に置き換え。skill-writer/skill-judge 新設と NVIDIA SkillEvaluator 導入は棄却 | accepted | 2026-08-22 |
| [0047](0047-retire-learned-notes-directory.md) | `skills/learned/` を全件退役（11 件）し、learn-eval の Save 先を Absorb / Promote の 2 択 + Drop に限定。実測で 184 read 中 161 が監査日集中、実作業 read は 74 日で 12 回。reachability はディレクトリの定数なので判定軸にならないと確認 | accepted | 2026-08-23 |
| [0048](0048-sdlc-playbook-translation-and-rfc-conformance.md) | AI-native SDLC playbook（2026-08-21）は改名でなく翻訳で取り込む — 対応の主役は AKC の二重ループ（product loop ↔ harness loop、stage↔phase 1:1 は誤り）、提案本文は Rust RFC 0000-template 完全準拠（preamble は frontmatter へ）。付表: product loop 機構マップ snapshot + 採用しないもの（control bands / LLM-judge evals ゲート / 3 artifact 分離 / DORA） | accepted | 2026-08-25 |
| [0049](0049-unify-task-ledger-into-public-rfcs.md) | store 形タスク台帳を公開 `rfcs/NNNN-slug.md` に一元化（提案も作業も 1 店舗、ID RFC-NNNN、状態語彙 8 語流用）。archive 機構は持たず終端エントリは公開判断記録として残置。claims.py は正規表現 + 走査パスの最小改修のみ。全 repo 展開は RFC-0001 が追跡 | accepted | 2026-08-25 |
| [0050](0050-standardize-ledger-state-vocabulary.md) | 台帳の状態語彙を標準語彙 9 語へ全域移行（draft / accepted / in_progress / blocked / done / resolved / rejected / withdrawn / obsoleted）— 非標準語彙はセッション間で写像がずれる実証（同日 2 通りに書いた）。分担線: 提案 lifecycle は RFC 標準語、RFC に無い実行系は issue-tracker 標準語。dropped は rejected / withdrawn に分裂、gloss 運用は廃止 | accepted | 2026-08-25 |
| [0051](0051-extract-mechanical-adr-checks-into-cross-repo-lint.md) | ADR レビューの機械チェックを cross-repo lint script（adr_lint.py、evidence 既定 + --gate）へ抽出し adr-reviewer を意味的チェック専任に薄化 — テンプレは repo の README から自動適応、実行座標は skill ステップ（verify.sh 常時配線は却下）、頻出指摘は review-findings.md へ蒸留 | accepted | 2026-08-26 |
| [0052](0052-url-liveness-and-usage-aggregation-evidence-scripts.md) | URL 到達性（`skill-health/scripts/url_liveness.py`）と skill usage 集計（`skill-stocktake/scripts/usage_stats.py`）を evidence script へ降ろし skill-stocktake を薄化 — `blocked` を `dead` に畳まない語彙、429 連発は retry せず停止（policy signal）、並列 batch agent の fetch を親 1 パスへ直列化。search-first は lychee 等を却下（blocked/dead の再導出が必須・Rust 依存）。消費者は 3 → 2 箇所に訂正（DOI validity は別問題） | accepted | 2026-08-26 |
| [0053](0053-extract-context-sync-checklist-into-evidence-script.md) | context-sync Phase 4 の機械チェックを evidence script（context_evidence.py、evidence 既定 + --gate）へ抽出しチェックリストを Step 0 配線で薄化 — 20 項目の再分類は deterministic 4 / hybrid 11 / semantic 4 / deferred 1、gate scope は 7 repo 実測で決定（context_paths は opt-in、公開ミラーの真陽性 1 件は免除しない）、ADR index は adr_lint・graph.jsonld は graph_lint へ委譲、URL 到達性は RFC-0008 待ちで verdict skip、検査不能は degraded[] で clean と区別 | accepted | 2026-08-26 |
| [0054](0054-extract-agent-stocktake-and-learn-eval-mechanical-checks.md) | agent-stocktake と learn-eval の機械チェックを evidence script へ抽出し、自己申告を成果物に置き換える — review-to-lint の 2 件目・3 件目適用。suppression catalog は日英両方（実在した唯一の該当は日本語）、description 近似重複は Jaccard/containment 実測 gap（0.525 / 0.319）から閾値 0.5、tokenizer は 2 script に複製（feedback: duplicate_over_coordination） | accepted | 2026-08-26 |
| [0055](0055-review-chain-single-pass-regression.md) | レビュー chain を fresh-context 1 段 + 条件付き Security へ縮約する（公式推奨密度への回帰）— レビュー起点のオーバーエンジニアリング発振を 1 往復規律・correctness-only 指示・effort medium・diff 外起票の loop-breaking 限定で切断。Simplify は batch opt-in、codex-review は明示要求のみ、simplify-order-notice hook 退役 | accepted | 2026-08-27 |
| [0056](0056-budget-lints-as-verify-bootstrap-annotation.md) | 予算系 lint（閾値を要する複雑度・関数/ファイル長・bundle サイズ系）の global 規約を verify-bootstrap の但し書きとして置く — 「最大 strict」が予算系を構造的に落とす盲点（82 repo / 104 config でヒット 0、2026-08-28 実測）を閉じる。global 数値・ツール表・backfill なし、閾値は corpus 分布の実測（免除境界の原則）、超過は閾値を上げずに刈る（配達点は閾値行コメント）、展開は需要駆動。ADR-0055 の計器却下の射程を日付つき注記で狭める | accepted | 2026-08-28 |
| [0059](0059-verify-precommit-block-on-stale-approval.md) | verify-precommit の承認失効（exit 71 = 台帳に載っている repo のゲートが編集で hash 不一致）は commit を block する — 通知のみの失効挙動が 3 週間の沈黙（CA、2026-08-06〜28、ゲート未実行のまま commit が通り続けた）を許した実害への修理。未承認（exit 70）は従来どおり通知して通す。回帰テスト 4 本 | accepted | 2026-08-28 |
| [0057](0057-judge-tier-default-dispatch-and-plan-boundary-advisory.md) | judge-tier セッションの実装既定を dispatch へ反転（自己実装は例外 3 種の 1 行記録時のみ）+ plan 承認境界（ExitPlanMode PostToolUse）の advisory hook `plan-executor-notice.sh` 新設 + planning.md 常駐 1 行。spawn-session のモデル固定は著者実測（herdr dispatch で Opus 起動成立）により却下。ADR-0043 の 2026-08-22 注記の穴に enforcement を足す | accepted | 2026-08-28 |
| [0058](0058-writing-harness-scaffold-dissolution.md) | 執筆ハーネス 15 ファイル 2,504 行の規約を短い原則へ戻す（Scaffold Dissolution）。Orwell 6 rules の取り込みを調べた結果、4 つは既存と重複し、差は内容ではなく書き方だった — 原則に例示・例外・判定手順・整合弁明・出自の日付を添えると問いが起きなくなる。原則は skill 本文、閾値は判定 agent、直し方は references/ へ三層分離。複製は正本 1 つへ統合（Output Format 55 行 × 2 → 共有 reference）。実測由来の拡張も畳む（著者裁定）。ルール 1 は禁止形のみ、ルール 6 の例外条項を追加。writing-ecosystem 438 → 378 行 | accepted | 2026-08-28 |
| [0060](0060-codemap-evidence-script-and-freshness-gate-mechanization.md) | codemap chain の機械検査（freshness gate / header 検収）を `update-codemaps/scripts/codemap_evidence.py` へ抽出（review-to-lint 適用、著者指示発火）— evidence 既定 + `--gate --produced` 限定の厳格検収。免除境界は 10 repo / 24 codemap 実測（spec 準拠 0 件 → legacy は evidence 注記どまり）。zsh word-splitting 罠と orphan 誤裁定を code の性質へ。verify.sh の owned 判定に ECC-customized を追加 | accepted | 2026-09-01 |
| [0061](0061-prompt-audit-version-diff-markers-and-lint-gate.md) | Fable 5.1 向け prompt-audit（88 件 / 44 ファイル適用、1d 版差 marker が 55 件）の実施記録と再発防止 — skill-creator §3 に「現行規則として書く / tombstone・経緯物語・同一ファイル内 2 版・tie-breaker・register 例を置かない」の 6 規律、skills.md に常駐 3 行、harness_lint 検査 13（同一括弧内の日付 + edit 動詞。退役 / 廃止など as-of 記述は対象外）。ADR-0018 / 0035 の rightsize 第 3 波 | accepted | 2026-09-02 |
| [0062](0062-retire-codemap-machinery.md) | codemap 機構の退役 — `update-codemaps` skill / `codemap-writer` agent / context-sync Phase 0 / release-doi 再生成を撤去。file-level 構造は保存せず LSP tool / grimp で都度導出、理由は ADR、段構成は script header。CA 実測（159/197 commit、読者証拠ゼロ、LSP 実走）が根拠。architect の per-repo opt-out 勧告を著者が global 撤去に上書き（Scaffold Dissolution Downward）。ADR-0060 を supersede、他 9 repo の静的 codemap は次回接触時に削除 | accepted | 2026-09-05 |

## Template

新しい ADR を追加する際は以下のフォーマットに従う。`## Review-when` は ADR-0044 以降必須
（`harness_lint.py` が存在を検査。節存在・Status・Date・index の機械検査は
`skills/adr-writer/scripts/adr_lint.py` — 書き時とレビュー時の skill ステップで走る、ADR-0051）。
それ以前の ADR には無いので、読むときは Context の前提と
Date で重みを決める。ADR は日付つき仮説であって恒久的な拘束ではない（`rules/common/akc-cycle.md`）:

```markdown
# ADR-NNNN: [Title]

## Status
accepted | superseded | deprecated

## Date
YYYY-MM-DD

## Context
[何が問題だったか]

## Decision
[何を決めたか]

## Review-when
[失効条件 — この判断を反故にする、または弱める観測・前提の失効を 1〜3 行。
書けなければ「無し — 恒久判断ではなく記録」と明記する]

## Alternatives Considered
[他に検討した選択肢。却下理由、または生きている対抗案なら「未決 — 再訪条件: …」]

## Consequences
[この判断の結果、何が容易/困難になるか]
```

旧 ADR を新しい観測が**部分的に弱める**（supersede しない）ときは、旧 ADR の該当節の下に
`> **注記（YYYY-MM-DD, ADR-NNNN）**: …` を追記する。削除も Status の変更もしない。

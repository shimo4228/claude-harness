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
| [0010](0010-context-sync-cascade-and-writer-agents.md) | context-sync の cascade 化と writer agent 新設 (codemap-writer / adr-writer) | accepted（一部 superseded） | 2026-05-22 |
| [0011](0011-retire-builtin-duplicate-skills-and-version-dependent-rules.md) | built-in 重複 skill とバージョン依存 rules の退役 | accepted | 2026-06-10 |
| [0012](0012-cross-tool-skill-sharing-via-agents-skills.md) | クロスツールのスキル共有を ~/.agents/skills 経由に一本化 | accepted | 2026-06-28 |
| [0013](0013-cross-model-review-seam-via-codex.md) | クロスモデルレビュー seam を Codex で開く — 多エージェントは脱相関の一点に限定 | accepted | 2026-06-28 |
| [0014](0014-retire-multi-agent-orchestration-rule.md) | multi-agent-orchestration.md ルール退役 — native 部分は公式ハーネスに委譲 | accepted | 2026-06-30 |
| [0015](0015-cross-agent-rules-sharing-reference-first.md) | クロスエージェント rules 共有は「参照 > 生成 > 同期」— エージェント側アタッチポイント方式 | accepted | 2026-07-18 |
| [0016](0016-writer-agents-render-not-decide.md) | Writer agent は render 専任 — 委譲境界は semantic authority (EN→JA 翻訳は skill-only / adr-writer リーク修正) | accepted（一部 superseded） | 2026-07-18 |
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
| [0063](0063-rfc-0020-rust-pilot-hooklint.md) | RFC-0020 pilot — `hooks/*.sh` の兄弟一貫性 lint `hooklint` を Rust（std のみ）で新設し `.claude/verify.sh` に配線。撤退条件 5 件中 size 上限（400 行）のみ発火（非テスト非空行 564）— review 由来の fail-open / security 修正分で、著者判断で 600 に引き直して accept（事後の goalpost 移動を明記）。n=1 読み値: cold build 1.2 s / latency 3.9 ms / bounce 0 / FAIL_OPEN report-only 5/23 hook | accepted | 2026-09-06 |
| [0064](0064-astra-fable-growth-loop.md) | Astra–Fable growth loop — 戦略 / 制御 / 実行 / 観測 / 人間の五役を既存の triage loop 基盤の上に建て、状態は `.growth/` の 3 ファイルだけ持つ | accepted | 2026-09-08 |
| [0065](0065-drop-adr-consultation-wiring-and-build-or-not-gate.md) | 新規アイデアへの制動を外す — 「変更前に ADR を確認せよ」型の配線 5 箇所を撤去し、memory の却下記録 14 ファイルを削除、Build-or-not 4 問を planning / implementation-chain / rfc-writer から削除、「することだけを書く」原則を rule skills.md + skill-creator §3 + adr-reviewer §8 に配線。ADR-0044 の未決 Alternative（ADR 廃止）は Review-when へ引き継ぎ | accepted | 2026-09-14 |
| [0066](0066-search-first-report-contract-and-scout-retirement.md) | search-first を verdict から報告契約へ — 終わり方を `Scope searched / Found / Still unknown` の報告にし判断は呼び出し側、受ける問い 6 種 + 総称句を description の trigger surface に、Full Mode は general-purpose subagent（web tool のみ）へ、scout 退役。網羅の計器は invoke 数でなく影の比率（133/142 = 93.7%、2026-09-14、述語固定の snippet は `.notes/`）。実測: 60 日 142 外部調査セッション中 133 が skill を通らず自前で as-of / 一次ソースを書いていた | accepted | 2026-09-14 |
| [0067](0067-skill-doctor-as-residency-cost-instrument.md) | `/skill-doctor` を skill-stocktake Phase 1 の residency-cost 計器にする — listing 行の常駐 token（`context`）は substrate に測らせ、意図的使用数は usage_stats（4 補正）が正のまま、`uses` は cross-check。`context` は description audit の fold 候補の価格で verdict 入力ではない。parser は書かない（format は substrate 所有・JSON 無し） | accepted | 2026-09-15 |
| [0068](0068-retire-five-unread-skills-organic-read-evidence.md) | 5 skill + 1 agent を退役（e2e / ai-regression-testing / python-patterns / agent-harness-construction / thermo-nuclear-code-quality-review、e2e-runner agent）— invoke 0 の reference 型 skill は「監査日を除いた organic read」で存在を再検査する（3〜7 回、7〜8 月止まり）。「常駐コスト 0」「chain 行からの参照」は存在パス B の根拠にならない。残余は Patch Target Migration 節 → refactor-clean のみ、旧 ADR-0011 / 0018 / 0039 に注記 | accepted | 2026-09-15 |
| [0069](0069-boundary-rule-and-judge-merges.md) | 境界の正本を `rules/common/boundary.md` 1 本にまとめる（人間に渡す操作 / とってよいリスク / 止まって報告する条件。substrate の一般則は再宣言しない、3 動詞で書く）。散在 6 箇所は pointer に。最後のスイッチを人間から判断役へ — 検収を通した branch は判断役が ff-only 取り込み・push、無人時に rules / hooks / permissions / gate script を含む diff だけ人間に残る。撤回条件: 3 か月で revert 2 回超 | accepted | 2026-09-15 |
| [0070](0070-relax-positive-form-rule-and-verbatim-builtin-overrides.md) | 「することだけを書く」（ADR-0065 §4）を「既定は肯定形、禁止は具体的動作・観測済み・機械ゲート無しの 3 条件付き、理由 1 句」に緩和。built-in subagent の override は CLI bundle からの verbatim 写し（origin 外部、CLI 版をコメントに）— 実例 `agents/Explore.md` を sonnet に。`CLAUDE_CODE_SUBAGENT_MODEL=opus` を frontmatter 無し agent の既定に | accepted | 2026-09-16 |
| [0071](0071-adr-review-evidence-script-for-recurring-reviewer-findings.md) | adr-reviewer の反復指摘（24 報告 / 4 repo、2026-08-26〜09-15）のうち機械で数えられる部分を per-ADR evidence script `adr_review_evidence.py` へ降ろす — 引用 ADR / RFC の実在、旧 ADR 側の注記・Status の往復、パス参照の tracked / ignored / missing / repo 外分類と引用行の実文、Decision と diff の範囲照合、出典なき数値・分母なし百分率・会話参照、Review-when の count 条件、status quo の有無、巻き戻しコスト、第 2 の記録場所。evidence のみ・gate 無し、実行座標は adr-writer Step 4.5 と adr-reviewer Step 0。review-to-lint 第 2 弾（RFC-0005 #17）、ADR-0055 Decision 5 の再訪条件成立を記録 | accepted | 2026-09-16 |
| [0072](0072-retire-adr-writer-agent-and-narrow-adr-filing.md) | `adr-writer` render agent を退役し skill の主ループが packet から直接書く（ADR-0016 の render / decide 分離は packet 規律として存続、process 境界は持たない）。起票を 2 条件に絞る — 他 artifact が引く機構・ゲート・閾値・agent 階層の変更、または旧 ADR の supersede / 注記。それ以外は commit 本文に Context / Decision / Review-when の 3 行。根拠は 1 本 / 日・commit の 26% の実測（2026-09-16）と agent の意味漏れ 2 件。ADR-0016 Decision 2 / ADR-0010 を部分 supersede | accepted | 2026-09-19 |
| [0073](0073-signal-first-as-output-style-and-one-question-gate.md) | Signal-first を常駐 rule でなく output style `output-styles/signal-first.md`（読者の注意は 1 チャネル — 結論先頭、判断は 1 メッセージに 1 つ、interview 中は総数を絞らず 1 問ずつ）と PreToolUse hook `ask-one-question.sh`（AskUserQuestion の `questions` ≥ 2 を exit 2 で block、block ごとに計測ログ 1 行）で持つ。`outputStyle` を `Concise` から置換。旧節の intake 側は戻さない。ADR-0026 Context 第三を対話の形について部分的に弱め、ADR-0061 の Concise follow-up を閉じる | accepted | 2026-09-19 |
| [0074](0074-jev-skill-router-prompt-to-external-judge-shadow-first.md) | skill 選択を外部判定 API（TypeSafe Jev、`jev-1.13.0` pin）へ送る UserPromptSubmit hook を `skills/jev-skill-router/`（自作・stdlib のみ・公開前提）として新設。cookbook `skill_suggestion` の 2 request 構成、名簿は user / plugin / project の 3 系統。shadow（注入なし・判定ログのみ = RFC-0025 registry の最小形）から入り、inject は観測量（routed ≥ 200 行かつ同ターン skill 使用 ≥ 40 行）で著者が点ける。ADR-0002 の 2 点との差分を記録（0002 は変えない） | accepted | 2026-09-21 |

## Template

新しい ADR を追加する際は以下のフォーマットに従う。`## Review-when` は ADR-0044 以降必須
（`harness_lint.py` が存在を検査。節存在・Status・Date・index の機械検査は
`skills/adr-writer/scripts/adr_lint.py` — 書き時とレビュー時の skill ステップで走る、ADR-0051）。
それ以前の ADR には無い（`rules/common/akc-cycle.md`「ADR の扱い」）:

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

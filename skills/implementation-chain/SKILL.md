---
name: implementation-chain
description: "実装に着手する前に task 種別（feat / fix / refactor / chore / prototype / writing）を判定し、その種別に対応する agent chain（Plan → Phase 0 → TDD → Review 群 → Doc Sync → Verify）を plan に front-load するための判断表。Use when starting to implement a feature, fix a bug, refactor, or write a document and you need to decide which reviewers and gates apply — 「これから実装する」「chain を組む」「どのレビューを回すべきか」。writing 種別の orchestrator skill へのルーティング表と早期停止条件もここが正本。NOT for — chain 内の各ステップの実装詳細（それは search-first / tdd / codex-review / writing-ecosystem 等の各 skill）、既に chain が確定した後の実行。"
user-invocable: true
origin: shimo4228
---

# Implementation Chain

実装に着手する前にタスク種別を判定し、対応する chain を **plan に front-load** する。
実装中は判定をやり直さず、定義済みの chain をそのまま実行する。
commit / push / 公開の権限は task request と substrate が持つ。この skill は追加の人間 gate を作らない。

## タスク種別判定（最初の plan ステップ）

| 種別 | 判定基準 | 例 |
|------|---------|-----|
| `feat` | 新規機能・新規モジュール追加 | API 追加, 新ページ |
| `fix` | バグ修正（再現可能な不具合） | crash, 誤動作 |
| `refactor` | 振る舞いを変えない構造変更 | 抽出, 改名, 整理 |
| `chore` | 設定 / 依存更新 / コード付随の docs 追従 | settings, CI |
| `prototype` | 学習・スパイク・本番外コード | 検証スクリプト |
| `writing` | 文書自体が一次成果物 | README 改稿, 記事, 論文, llms.txt |

`prototype` を選ぶ場合は **「prototype として扱う理由」を plan に必須記載**（fix/feat の悪用防止）。

**harness 自体の変更**: 対象が `~/.claude` の rules / skills / hooks / agents / settings なら、種別に関わらず Plan で skill: `harness-boundary` を 1 回通す（どの層に置くか・モデルに任せられないか・runtime 交換後も残すか。1 行の判断で足りる）。

**README の種別判定**: README 自体の改善・書き直しが目的なら `writing`（Writing Chain → readme-writer）。コード変更に付随する README 追従更新ならコードチェーンの Doc Sync 内で扱う。

**大きい feat の Plan の補助**（2026-08-22、公式 feature-dev plugin の型だけ吸収）: ① Explore agent を
2〜3 並列・別角度（類似機能 / 構造 / 拡張点）で走らせ、各 agent に「主ループが読むべきファイル 5〜10」を
返させて読む ② 設計代替は Plan agent を観点違い（最小変更 / クリーン / 実用）で並列し、主ループが
比較して推奨・ユーザー選択（収束の所在は Matrix の Plan 行）。

**実行者の決定**（Plan の最後、必須。2026-08-22 追加、2026-08-28 既定を反転）: plan が固まったら
「このセッションが実装するか」を 1 行で決める。判断が要るのは judge-tier のセッション（Fable）で
走っているとき — そのまま実装に入ると、Review 群まで judge-tier を消費する（built-in `/code-review`
と `/simplify` はセッションのモデルを継いで走り、モデル引数は無い。pin できるのは自作 agent と
plugin agent の `model:` だけ）。**judge-tier の既定は dispatch**: 実装は build-tier の新規セッション
（skill: `spawn-session`、または Agent tool / `claude --bg -w <name> --model opus`）へ渡し、
本セッションは packet を書いて検証側に残る（dispatch 条件の照合は skill: `task-triage` — 前提が
`file:line` で検証済み / worktree で可逆 / 受け入れ条件が判定可能 / 1 セッションに収まる /
rule 変更を含まない）。**三役とティアの正本は task-triage の役割表**（ここには複製しない）。
このセッションで実装してよいのは、次のいずれかを plan に 1 行記録したときだけ:
(a) 設計文書・ADR・skill / rule の散文編集（judge-tier の本業）、(b) dispatch 条件を満たせない
具体的理由がある、(c) ユーザーの明示指示。自己実装する場合も Review 群は下の
「Review の実行モデル pin」で build-tier に降ろす（人間の `/model` 切替を待たない）。
文脈損失（ADR-0016「model 継承は能力しか救わず文脈損失は救わない」）を dispatch を避ける理由に
しない — packet の充実で救う（packet の形は task-triage が正本）。
（失効条件: モデルのティア区別と使用限度が消えた、または substrate がセッション単位の model
routing を自発的に行うようになったら、この段落を外す。）

## Chain Matrix（種別 × ステップ）

各セルの値: `Y` 必須 / `C` 条件付き / `-` 省略可。

| ステップ | feat | fix | refactor | chore | prototype |
|---|:-:|:-:|:-:|:-:|:-:|
| Plan（メインループ / plan mode。sub-agent は探索と代替案の生成まで — plan 本文と採否は主ループが書く。rich context と介入点 1 の対話が要件） | Y | Y | Y | - | - |
| Phase 0 External Research | Y | - | - | - | - |
| TDD（メインループ、skill: `tdd`） | C | C | - | - | - |
| Refactor Clean | - | - | Y | - | - |
| Code Review | Y | Y | Y | C | - |
| Security Review | C | C | - | C | - |
| Doc Sync (context files) | C | C | C | C | - |
| E2E / 回帰テスト（skills: `e2e` / `ai-regression-testing`） | C | C | C | - | - |
| Verify (build / types / lint / tests / secrets / deps / doc sync / git status) | Y | Y | Y | Y | - |

**条件付き発火 `C` の発動条件**:

- `feat` × TDD: **観測可能な振る舞いを実装前に固定する価値がある場合のみ Y**（2026-08-15 に `Y` から降格、[ADR-0040](../../docs/adr/0040-demote-feat-tdd-to-conditional.md)）。具体的には ① 仕様が曖昧で、テストを書くこと自体が仕様確定の作業になる ② 境界条件・エラー時の振る舞いが争点 ③ 既存挙動との互換性が要件。いずれにも当たらず、仕様が会話で確定していて実装が素直なら `-` — **ただしテストは書く**。順序を強制しないだけで、Verify の coverage floor は変わらない。判断に迷ったら Y
- 全種別 × E2E / 回帰テスト: **ユーザー可視のフロー（画面遷移・API の外形）を変えたら `e2e`**、**AI に広く編集させた diff で同種のバグが再発しうるなら `ai-regression-testing`** を Y。いずれも Verify の coverage floor（`rules/common/testing.md`）の**上に足す**もので、置き換えではない。純粋な内部リファクタや設定変更だけなら `-`
- `feat` / `chore` × Build-or-not（2026-08-25 追加）: **新規機構・計器・常駐資産（skill / rule / hook / agent）・依存の追加を含む plan のみ Y**。plan 本文に 4 問の答えを必須で書く — ①存在すべきか（削除・既存流用で解けないか）②適正な大きさ（行数・段数の上限を先に宣言）③誰が消費するか（読み手のいない出力は建てない）④失効条件。**セッションが judge-tier ならこの自答で足りる（agent 呼び出しは冗長 — 同一モデル）。build-tier セッションのみ agent: `architect`（model: fable）を必須**とし、verdict が Don't build なら chain はそこで止まる。実測根拠: CA ADR-0095（この問いを持たない無人 chain が 30 時間で 5,000 行）
- `fix` × TDD: **再現手順が言語化できる不具合のみ Y**（再現テストを RED で先に書く）。設定値の誤り・typo・一過性の環境要因など、テストが資産にならない fix は `-`。判断に迷ったら Y。着手時の照合規律（既済照合・schema 変更の全消費者棚卸し等）は skill: `repair-discipline`
- 測定・閾値・ガードを含む diff の設計判断は skill: `measurement-discipline`（1 回は証拠でない / ゲートは観測量 / 発火率較正）
- `fix` / レビュー指摘対応 × 機構ゲート: **修理前に問う — この修正は機構（コード・段・状態・設定面）を足すか**。足すなら上の Build-or-not 行に従う（judge-tier は 4 問自答、build-tier は agent: `architect`。実測根拠: CA ADR-0095/0098 — レビュー起点の個別 fix の連鎖が自己供給ループで肥大した）。足さないなら、不具合を生んだ規則（skill / prompt / rule の行）を diff と同時に直すか、直さない理由を 1 行残す
- `feat` × Security Review: **脅威面を動かす feat のみ Y**（2026-08-16 に `Y` から降格、ADR-0042）。
  脅威面 = 資格情報の取得・保管・送出 / 外部 IO / 公開経路（外部に出るデータの内容と範囲）/
  無人実行の起動経路とブラスト半径 / 外部コンテンツを LLM 文脈へ取り込む経路 / 権限と bypass の境界。
  内部ロジックの追加のみ、既存経路の内側で完結する feat は `-`
- `fix` × Security Review: 入力検証・認証・秘匿情報を触る fix のみ Y。ロジック誤り単独は `-`
- 全種別 × Code Review の effort: **`medium`** を明示して起動する（low/medium は最も確信の
  高い findings のみ報告する帯 — レビュー起点のオーバーエンジニアリングを避ける側に倒す。
  `high` は著者が明示的に求めたときだけ）。
  無指定だと `/code-review` は「最後に打ったレベル」を再利用するので、chain がセッション状態に依存する
- `chore` × Code Review: settings.json / hooks / permissions / CI 変更時のみ Y
- `chore` × Security Review: secrets 設定 / 認証関連 hook / permissions 変更時のみ Y
- 全種別 × Doc Sync: 変更が以下のいずれかに該当する場合のみ Y。該当 doc を**同じ diff** で更新する（後追い PR にしない）
  - 機構・ゲート・閾値・段構成の変更 → CODEMAPS の Data Flow / architecture（プロジェクトに鮮度規約があればそれに従う）
  - ADR 新設・廃止 → knowledge graph（graph.jsonld 等）+ CODEMAPS 言及（両面更新）
  - パッケージ資産（プロンプト・シード・テンプレート・サービス定義）の増減 → 設定リファレンスの canonical 節
  - CLI / user-facing 挙動の変更 → README / llms.txt
  - 数値クレームの規律: 集約カウントの正本は 1 箇所のみ（他はポインタ）。機械検証可能な doc↔実体対応は prose 修正でなくテストで固定する（検出は code、削除判断は人間）

built-in review は chain の正規ステップである（ADR-0039 → ADR-0042 で T-004「自動枠は変更しない」を
全面反転）。担当の割り当ては下の Review 表が正本。

## Review ステップ（実装直後・Verify 前）

常設レビューは **fresh-context 1 段**（2026-08-27 再編 — 公式 best practices の推奨密度
「機械検証主体 + adversarial review 1 段」への回帰。多段構成はレビュー起点の
オーバーエンジニアリングを供給していた。根拠と経緯は当該 ADR）。

| 順 | category | 起動先 |
|:-:|---|---|
| 1 | Code Review | built-in `/code-review`（judge-tier セッションでは「Review の実行モデル pin」経由。effort は `medium` を明示。quality 軸（Reuse / Simplification / Efficiency / Altitude）は built-in が内蔵）。Swift は `swift-reviewer` も追加 |
| 1 | Security Review | `security-reviewer`（**脅威面を動かす diff のみ** — 発火は Matrix の Security Review 行が正本。agent 側は自発起動しない） |

2 行とも発火する diff では並列起動する（同じ diff を見るため）。

**reviewer への指示（必須）**: 起動 prompt に必ず含める —
「correctness / stated requirements に効く gap のみ報告。それ以外（防御的コード・追加の抽象層・
起こり得ないケースのテスト等）は optional として報告し、適用しない。diff 外の指摘は報告不要
（気づいた場合は 1 行のみ、修理はしない）」。この 1 行は loop 自身を壊す欠陥の起票チャネル
として残す（規約は `rules/common/task-tracking.md`）。reviewer は問われれば必ず何か返す —
指摘の全追跡がオーバーエンジニアリングの供給源になる（公式 best practices の名指し）。

**opt-in 名簿**（自発発火しない。著者が明示的に求めたときだけ）:

- batch simplify = built-in `/simplify` — 肥大を感じたとき数 commit 分まとめて
  （実績: CA commit `e739912` の 22 commit 一括、CA commit `edca8cf` の Review 後実行 +
  再 Verify）。per-commit の Simplify ステップは廃止（quality 軸は `/code-review` が内蔵）
- security 深掘り = plugin `claude-security`（全 repo スキャン）
- cross-model = skill: `codex-review`（diff review・plan 段の前提反証とも）

adr-reviewer は opt-in ではなく skill: `adr-writer` の内部ステップ（ADR 執筆時は
省略しない — 配線は同 skill のみ、この chain は持たない）。swift-reviewer は Swift diff で
Review 表の Code Review 行に従い併用（ADR-0042 が去就を保留した項目）。

**Review の実行モデル pin（2026-08-24 追加）**: judge-tier のセッション（Fable）で chain を回すとき、
built-in `/simplify` と `/code-review` を主ループで直接呼ばない — セッションのモデルを継いで
judge-tier トークンを消費する。代わりに `Agent(subagent_type: "general-purpose", model: "opus")` の
サブエージェント内で当該 skill を起動する（prompt に skill 名・effort・対象 diff の範囲を書く。
`/simplify` の working-tree への fix 適用はサブエージェントでも同じに機能する）。自作 reviewer
agent は frontmatter の `model:` が正本。build-tier のセッションでは直接呼んでよい。

Refactor Clean では built-in simplify の後に `refactor-cleaner` agent を起動する
（refactor 種別専用のステップで、per-commit Simplify の廃止とは独立）。
TDD は発火する場合 Plan の後に置く。Verify は全レビュー後（順序として逐次必須なのは Verify のみ）。

## Writing Chain（`writing` 種別のルーティング）

`writing` 種別は上の Chain Matrix を**使わない**。doc 分類を判定し、対応する orchestrator skill にルーティングする:

| doc 分類 | orchestrator skill |
|---|---|
| 記事 / エッセイ / newsletter（人間向け prose） | `writing-ecosystem`（正本は `~/MyAI_Lab/zenn-content` — 記事作業はその repo を working dir に含めて行う） |
| 学術論文 / preprint / position paper | `paper-ecosystem`（正本は `~/MyAI_Lab/paper-lab` — 論文作業はその repo を working dir に含めて行う） |
| README / repo トップページ | `readme-writer` |
| llms.txt 等 AI-doc | `llms-txt-writer` |
| ADR（設計判断の記録） | `adr-writer`（生成。adr-reviewer の配線は同 skill 内） |

チェーン本体（agent 起動順・並列化・最終 gate）の**正本は各 skill の定義**（ここに複製しない）。
記事 / paper の chain 詳細（reviewer panel・verdict・機械検査）は移設先 repo の orchestrator と
channel contract が正本 — 本節はルーティングと、global 常駐 doc（README / llms.txt / ADR）の
糊だけを規定する:

**Verdict マッピング**（writing agent の出力 → chain verdict への変換）:

| agent 出力 | chain 上の扱い |
|---|---|
| MAJOR ISSUES（readme-reviewer） | CRITICAL → 停止 |
| NEEDS REVISION（readme-reviewer） | HIGH → 継続 + 修正 |
| readme-judge Rewrite / geo_check FAIL | Verify FAIL → 停止 |

**Cross-Model Review（条件付き）**: 公開前の高 stakes 文書のみ実行する。
prose は prompt-driven、private ドラフト・下書き段階は `-`（writing chain は ADR-0055 の
再編対象外 — 各 orchestrator skill の配線が正本のまま）。

**Verify 相当（writing 版）**: build / types / tests は非該当。代わりに (1) 決定論 lint または証拠（README は readme_evidence.py の JSON + readme-judge の binding 判定、llms.txt は geo_check.py） (2) `git status` 確認。

**公開権限**: task request が commit / publish / deposit を含むかをそのまま使う。
この skill 固有の確認形式や追加 gate は設けない。

## 早期停止条件

以下を検出した時点で chain を中断し、ユーザーに報告する:

- Code Review / Security Review が **`CRITICAL`** を返した
- Verify ステップで build / types / tests のいずれかが失敗
- `fix` で根本原因の仮説が証拠で支持されない
- Phase 0 (`/search-first`) で `Adopt` Verdict → 実装方針の再 plan を要請
- `writing` で Verdict マッピング表の CRITICAL 相当（MAJOR ISSUES）を検出（記事 / paper の停止条件は各 repo の orchestrator が持つ）

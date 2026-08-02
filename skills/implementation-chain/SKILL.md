---
name: implementation-chain
description: "実装に着手する前に task 種別（feat / fix / refactor / chore / prototype / writing）を判定し、その種別に対応する agent chain（Plan → Phase 0 → TDD → Review 群 → Doc Sync → Verify）を plan に front-load するための判断表。Use when starting to implement a feature, fix a bug, refactor, or write a document and you need to decide which reviewers and gates apply — 「これから実装する」「chain を組む」「どのレビューを回すべきか」, or when planning.md の 2 介入点モデルに沿って Plan を書くとき。writing 種別の orchestrator skill へのルーティング表、早期停止条件、ユーザー実行枠 `U`（ビルトイン /code-review と /claude-security changes scan を意図確認 gate で提案する面）もここが正本。NOT for — chain 内の各ステップの実装詳細（それは search-first / tdd / codex-review / writing-ecosystem 等の各 skill）、既に chain が確定した後の実行。"
user-invocable: true
origin: shimo4228
---

# Implementation Chain

実装に着手する前にタスク種別を判定し、対応する chain を **plan に front-load** する。
実装中は判定をやり直さず、定義済みの chain をそのまま実行する。
ユーザー介入点は **「Plan 確認」と「意図確認」の 2 点のみ**（正本は `rules/common/planning.md`）。

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

**README の種別判定**: README 自体の改善・書き直しが目的なら `writing`（Writing Chain → readme-writer）。コード変更に付随する README 追従更新ならコードチェーンの Doc Sync 内で扱う。

## Chain Matrix（種別 × ステップ）

各セルの値: `Y` 必須 / `C` 条件付き / `-` 省略可 / `U` ユーザー実行の**提案**
（Claude からは起動不可のビルトインを意図確認 gate で提案する。gate ではない）。

| ステップ | feat | fix | refactor | chore | prototype |
|---|:-:|:-:|:-:|:-:|:-:|
| Plan（メインループ / plan mode。sub-agent へ委譲しない — plan は rich context と介入点 1 の対話が要件） | Y | Y | Y | - | - |
| Phase 0 External Research | Y | - | - | - | - |
| TDD（メインループ、skill: `tdd`） | Y | Y | - | - | - |
| Refactor Clean (refactor-cleaner) | - | - | Y | - | - |
| Code Review (code-reviewer / python-reviewer / swift-reviewer) | Y | Y | Y | C | - |
| Security Review (security-reviewer) | Y | C | - | C | - |
| Cross-Model Review (codex-review) | Y | Y | C | - | - |
| Doc Sync (context files) | C | C | C | C | - |
| Verify (build / types / lint / tests / secrets / deps / doc sync / git status) | Y | Y | Y | Y | - |
| User-Run Review (`/code-review`) | U | U | U | - | - |
| User-Run Security Scan (`/claude-security` changes) | U | U | - | U | - |

**条件付き発火 `C` の発動条件**:

- `fix` × Security Review: 入力検証・認証・秘匿情報を触る fix のみ Y。ロジック誤り単独は `-`
- `chore` × Code Review: settings.json / hooks / permissions / CI 変更時のみ Y
- `chore` × Security Review: secrets 設定 / 認証関連 hook / permissions 変更時のみ Y
- `refactor` × Cross-Model Review: 公開 API / 並行処理 / セキュリティ境界に触れる高リスク refactor のみ Y。純粋な内部整理は `-`
- 全種別 × Doc Sync: 変更が以下のいずれかに該当する場合のみ Y。該当 doc を**同じ diff** で更新する（後追い PR にしない）
  - 機構・ゲート・閾値・段構成の変更 → CODEMAPS の Data Flow / architecture（プロジェクトに鮮度規約があればそれに従う）
  - ADR 新設・廃止 → knowledge graph（graph.jsonld 等）+ CODEMAPS 言及（両面更新）
  - パッケージ資産（プロンプト・シード・テンプレート・サービス定義）の増減 → 設定リファレンスの canonical 節
  - CLI / user-facing 挙動の変更 → README / llms.txt
  - 数値クレームの規律: 集約カウントの正本は 1 箇所のみ（他はポインタ）。機械検証可能な doc↔実体対応は prose 修正でなくテストで固定する（検出は code、削除判断は人間）

**ユーザー実行枠 `U` の発動目安**（`/code-review` はビルトイン。`disable-model-invocation` で
Claude から起動できないため、自動枠の代替にはならない — 能力と可用性を混同しない）:

- 提案するのは**非自明な diff のみ**。typo 級・数行の自明変更では提案自体を省略する
- effort 目安: 通常 → `/code-review`、高 stakes（公開前・広範囲・セキュリティ境界）→
  `/code-review high`、公開前の大型変更 → `/code-review ultra`
- **advisory であり gate ではない** — 提案は既存の第 2 介入点（意図確認）に相乗りさせ、
  新しい介入点を作らない。chain は実行結果を待たず、早期停止条件にも入れない。
  実行判断と結果の取り込みはユーザーに属する
- 低リスク refactor / chore で自動の bug 探索が薄い領域（refactor × Cross-Model = `C`、
  chore × = `-`）も、自動枠の昇格でなくこの枠でカバーする（2026-07-25 判断）

**`/claude-security` changes scan の発動目安**（U に置く理由が `/code-review` と異なる —
起動不可ではなく、multi-agent workflow でトークン重量級 + Workflow の明示 opt-in 規律のため
実行判断がユーザーに属する）:

- 提案するのは **security-reviewer が発火する変更**（入力処理・認証・秘匿情報・permissions・
  hook・外部 API）のうち、panel 検証（3-voter の false positive 潰し）を掛けたい高 stakes
  diff のみ。effort 目安は low〜medium（小 diff は medium でも単一 researcher に collapse）
- **タイミングが `/code-review` と異なる**: committed 変更しか見ないため、意図確認 gate の
  pending diff には掛けられない。提案は gate に相乗りし、実行はコミット後・push / 公開の前
- 自動枠 security-reviewer の**代替ではなく上乗せ**。未コミット diff に軽く掛けたいときは
  ビルトイン `/security-review`（現ブランチの pending changes 対象）が下位層

**chain 非対象のビルトイン**: `/review` は GitHub PR 専用（ローカル diff は `/code-review` と
description が明示）のため Review ステップには使えない。`/security-review` は自動枠
security-reviewer と同じ面（pending changes）の user-run 版で、chain には入れず上記の
下位層として案内する（T-006 / [ADR-0020](../../docs/adr/0020-retire-security-scan-delegate-risk-to-claude-security.md)
で security-scan skill は退役、committed diff の重量級は `/claude-security` changes scan）。

## Review / Cleanup ステップ（実装直後・Verify 前）

実装が一段落したら、**Verify に進む前に**、変更内容・task 種別に応じて agent を起動する（上の Matrix は「どの種別で要るか」、ここは「実際に何を走らせるか」）:

- **/simplify → refactor-cleaner** — `refactor` 種別のとき、まず `/simplify`（ビルトイン。
  変更コードの reuse / simplification / efficiency / altitude を**修正まで適用**する。bug は
  探さない）、次に refactor-cleaner（knip / depcheck 等ツール駆動の dead code / 重複除去）。
  前者は質的改善（modify）、後者は死蔵資産の除去で役割が異なる
- **python-reviewer** — Python (`.py`) を変更したとき
- **swift-reviewer** — Swift (`.swift`) を変更したとき
- **code-reviewer** — Python / Swift 以外のコード（TS / shell 等）を変更したとき
- **security-reviewer** — 入力処理・認証・秘匿情報・permissions・hook を触ったとき
- **adr-reviewer** — `docs/adr/` を新設・改稿したとき（記録の検査: Context が検証可能な根拠を
  持つか / Alternatives が藁人形でないか / Consequences が両面あるか / 先行 ADR との override
  関係が書かれているか）。**決定そのものの是非は architect**、**生成は adr-writer** で、
  この agent は記録の質のみを見る（ADR-0016 の render/judge 分離）。高 stakes な ADR は
  codex-review を prompt-driven で併走させ、書き方のニュアンスを別モデルにも見せる
- **codex-review** — `feat` / `fix` で非自明な diff を実装したとき（cross-model 脱相関レビュー、read-only）。**diff ベースのレビュアーなので plan 時には走らせない — plan には chain entry として列挙するだけで、実装後に diff へ走らせる。「実装差分が無い」を理由に plan（設計）を codex で直接レビューする即興代替をしてはならない**

Code Review・Security Review・Cross-Model Review は同じ diff を対象にするので並列起動する。
TDD は Plan の後、Verify は全レビュー後（この 2 つは逐次必須）。
意図確認 gate でユーザーに提示するとき、Matrix の `U` 枠に該当すれば `/code-review`（および
セキュリティ高 stakes なら `/claude-security` changes scan）の実行をあわせて提案する
（発動目安は上の `U` 節）。

## Writing Chain（`writing` 種別のルーティング）

`writing` 種別は上の Chain Matrix を**使わない**。doc 分類を判定し、対応する orchestrator skill にルーティングする:

| doc 分類 | orchestrator skill |
|---|---|
| 記事 / エッセイ / newsletter（人間向け prose） | `writing-ecosystem` |
| 学術論文 / preprint / position paper | `paper-ecosystem` |
| README / repo トップページ | `readme-writer` |
| llms.txt 等 AI-doc | `llms-txt-writer` |
| ADR（設計判断の記録） | `adr-writer`（生成）+ adr-reviewer agent（記録の検査） |

チェーン本体（agent 起動順・並列化・最終 gate）の**正本は各 skill の定義**（ここに複製しない）。
この skill が規定するのは以下の糊のみ:

**Verdict マッピング**（writing agent の出力 → chain verdict への変換）:

| agent 出力 | chain 上の扱い |
|---|---|
| MAJOR ISSUES（editor / essay-reviewer / readme-reviewer） | CRITICAL → 停止 |
| ❌ INACCURATE（fact-checker） | CRITICAL → 停止 |
| DRIFT（source-fidelity-checker） | CRITICAL → 停止 |
| NEEDS REVISION（editor / essay-reviewer / readme-reviewer） | HIGH → 継続 + 修正 |
| readme_lint exit 1 / geo_check FAIL | Verify FAIL → 停止 |

**Cross-Model Review（条件付き）**: 公開・deposit 前の高 stakes 文書（公開 repo README / 論文 / 公開記事）のみ codex-review を Claude 側レビュアーと並列起動。**prompt-driven モード必須**（scoped モードはコード向け組み込み指示のため prose 不適）。private ドラフト・下書き段階は `-`。

**Verify 相当（writing 版）**: build / types / tests は非該当。代わりに (1) 決定論 lint（readme_lint.py / geo_check.py / textlint 等、doc 分類に該当するもの） (2) fact / citation gate（fact-checker verdict の出典編入、paper なら citation-formatter） (3) `git status` 確認。

**人間 gate**: 公開・deposit・commit 直前。2 介入点モデルの「意図確認」に対応する。
提示物は対象で分岐する（正本: `rules/common/human-gate.md`）— **`writing` の成果物と rules / skills /
identity は本文を提示**する（テキストが意図そのものなので、読むこと自体が intent 層の作業）。
control plane と**検査の証拠を作るもの**（テスト / fixture / lint 設定 / CI 定義 / 依存）も本文側。
実装コード・生成物は**意図の要約**（`plan との差分` の 3 値宣言必須）を提示し、diff 本文と
Verify の PASS 一覧は提示しない。不可逆・高影響な変更は区分によらず本文へ昇格する。

## 早期停止条件

以下を検出した時点で chain を中断し、ユーザーに報告する:

- Code Review / Security Review / Cross-Model Review が **`CRITICAL`** を返した
- Verify ステップで build / types / tests のいずれかが失敗
- `fix` で根本原因の仮説が証拠で支持されない（`rules/common/debugging.md`、唯一の例外的ユーザー確認待ち）
- Phase 0 (`/search-first`) で `Adopt` Verdict → 実装方針の再 plan を要請
- `writing` で Verdict マッピング表の CRITICAL 相当（MAJOR ISSUES / ❌ INACCURATE / DRIFT）を検出

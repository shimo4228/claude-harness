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

**README の種別判定**: README 自体の改善・書き直しが目的なら `writing`（Writing Chain → readme-writer）。コード変更に付随する README 追従更新ならコードチェーンの Doc Sync 内で扱う。

## Chain Matrix（種別 × ステップ）

各セルの値: `Y` 必須 / `C` 条件付き / `-` 省略可 / `↑` 上の行のステップの中で実行する。

`refactor` × Simplify の `↑` は「実行しない」ではない — Refactor Clean が built-in
`/simplify` → `refactor-cleaner` の順で回すので、**`/simplify` 自体は refactor でも走る**。
以前ここが `-` だったため「refactor は Simplify 不要」と読める状態になっていた
（2026-08-15 code-reviewer 指摘）。Simplify が本当に非該当なのは `chore` と `prototype`。

| ステップ | feat | fix | refactor | chore | prototype |
|---|:-:|:-:|:-:|:-:|:-:|
| Plan（メインループ / plan mode。sub-agent へ委譲しない — plan は rich context と介入点 1 の対話が要件） | Y | Y | Y | - | - |
| Phase 0 External Research | Y | - | - | - | - |
| TDD（メインループ、skill: `tdd`） | C | C | - | - | - |
| Refactor Clean | - | - | Y | - | - |
| Simplify（built-in `/simplify`、quality 軸の cleanup 適用） | Y | C | ↑ | - | - |
| Code Review | Y | Y | Y | C | - |
| Security Review | C | C | - | C | - |
| Cross-Model Review | Y | Y | C | - | - |
| Doc Sync (context files) | C | C | C | C | - |
| Verify (build / types / lint / tests / secrets / deps / doc sync / git status) | Y | Y | Y | Y | - |

**条件付き発火 `C` の発動条件**:

- `feat` × TDD: **観測可能な振る舞いを実装前に固定する価値がある場合のみ Y**（2026-08-15 に `Y` から降格、[ADR-0040](../../docs/adr/0040-demote-feat-tdd-to-conditional.md)）。具体的には ① 仕様が曖昧で、テストを書くこと自体が仕様確定の作業になる ② 境界条件・エラー時の振る舞いが争点 ③ 既存挙動との互換性が要件。いずれにも当たらず、仕様が会話で確定していて実装が素直なら `-` — **ただしテストは書く**。順序を強制しないだけで、Verify の coverage floor は変わらない。判断に迷ったら Y
- `fix` × TDD: **再現手順が言語化できる不具合のみ Y**（再現テストを RED で先に書く）。設定値の誤り・typo・一過性の環境要因など、テストが資産にならない fix は `-`。判断に迷ったら Y
- `fix` × Simplify: 新規ロジックを含む fix のみ Y。typo・設定値のみの diff は `-`
- `feat` × Security Review: **脅威面を動かす feat のみ Y**（2026-08-16 に `Y` から降格、ADR-0042）。
  脅威面 = 資格情報の取得・保管・送出 / 外部 IO / 公開経路（外部に出るデータの内容と範囲）/
  無人実行の起動経路とブラスト半径 / 外部コンテンツを LLM 文脈へ取り込む経路 / 権限と bypass の境界。
  内部ロジックの追加のみ、既存経路の内側で完結する feat は `-`
- `fix` × Security Review: 入力検証・認証・秘匿情報を触る fix のみ Y。ロジック誤り単独は `-`
- 全種別 × Code Review の effort: `feat` / `refactor` は `high`、`fix` / `chore` は `medium` を明示して起動する。
  無指定だと `/code-review` は「最後に打ったレベル」を再利用するので、chain がセッション状態に依存する
- `chore` × Code Review: settings.json / hooks / permissions / CI 変更時のみ Y
- `chore` × Security Review: secrets 設定 / 認証関連 hook / permissions 変更時のみ Y
- `refactor` × Cross-Model Review: 公開 API / 並行処理 / セキュリティ境界に触れる高リスク refactor のみ Y。純粋な内部整理は `-`
- 全種別 × Doc Sync: 変更が以下のいずれかに該当する場合のみ Y。該当 doc を**同じ diff** で更新する（後追い PR にしない）
  - 機構・ゲート・閾値・段構成の変更 → CODEMAPS の Data Flow / architecture（プロジェクトに鮮度規約があればそれに従う）
  - ADR 新設・廃止 → knowledge graph（graph.jsonld 等）+ CODEMAPS 言及（両面更新）
  - パッケージ資産（プロンプト・シード・テンプレート・サービス定義）の増減 → 設定リファレンスの canonical 節
  - CLI / user-facing 挙動の変更 → README / llms.txt
  - 数値クレームの規律: 集約カウントの正本は 1 箇所のみ（他はポインタ）。機械検証可能な doc↔実体対応は prose 修正でなくテストで固定する（検出は code、削除判断は人間）

built-in review は chain の正規ステップである（ADR-0039 → ADR-0042 で T-004「自動枠は変更しない」を
全面反転）。残る agent 枠は substrate が持たない観点（言語専門・repo 固有の脅威モデル・別モデル）
だけを持つ。担当の割り当ては下の Review 表が正本。

## Review / Cleanup ステップ（実装直後・Verify 前）

実装が一段落したら Verify の前に Matrix の Review category を起動する。reviewer 名簿の正本は
次の表。同じ diff を見る category は並列起動する。

| 順 | category | 起動先 |
|:-:|---|---|
| 1 | **Simplify** | built-in `/simplify`（Review 群より**前**。該当種別は Matrix の Simplify 行が正本 — `feat` = Y、`fix` = C、`refactor` = `↑`（Refactor Clean の中で）、`chore` / `prototype` = 非該当） |
| 2 | Code Review | built-in `/code-review`（**effort を明示する** — 種別ごとの値は Matrix 下の 「全種別 × Code Review の effort」）。Swift は `swift-reviewer` も追加 |
| 2 | Security Review | `security-reviewer`（発火は Matrix の Security Review 行が正本。agent 側は自発起動しない） |
| 2 | Cross-Model Review | skill: `codex-review` |
| 2 | ADR / Record Review | `adr-reviewer` + skill: `codex-review` |

Simplify を Review 群の前に置くのは、`/simplify` が fix を working tree に適用するため
（reviewer には適用後の diff を見せる）。**この順序は逆にすると Review のやり直しが要るので、
「後で思い出す」では回収できない** — 実測でも省略と順序違反が起きたため、Code Review の
起動直前に PreToolUse hook が未実行を指摘する（配線は `hooks/README.md`）。bug 軸は Code Review、quality 軸は Simplify の分担で、
`python-reviewer` と `code-reviewer` は退役した — 決定論チェックは Verify が、Pythonic idiom と
一般的な correctness は substrate の built-in `/code-review` が吸収済み
（[ADR-0039](../../docs/adr/0039-retire-python-reviewer-simplify-in-chain.md) → ADR-0042）。
Refactor Clean では built-in simplify の後に `refactor-cleaner` agent を起動する。
TDD は発火する場合 Plan の後に置く。Verify は全レビュー後（順序として逐次必須なのは Verify のみ）。

## Writing Chain（`writing` 種別のルーティング）

`writing` 種別は上の Chain Matrix を**使わない**。doc 分類を判定し、対応する orchestrator skill にルーティングする:

| doc 分類 | orchestrator skill |
|---|---|
| 記事 / エッセイ / newsletter（人間向け prose） | `writing-ecosystem` |
| 学術論文 / preprint / position paper | `paper-ecosystem` |
| README / repo トップページ | `readme-writer` |
| llms.txt 等 AI-doc | `llms-txt-writer` |
| ADR（設計判断の記録） | `adr-writer`（生成）+ Record Review category |

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

**Cross-Model Review（条件付き）**: 公開・deposit 前の高 stakes 文書のみ実行する。
prose は prompt-driven、private ドラフト・下書き段階は `-`。

**Verify 相当（writing 版）**: build / types / tests は非該当。代わりに (1) 決定論 lint（readme_lint.py / geo_check.py / textlint 等、doc 分類に該当するもの） (2) fact / citation gate（fact-checker verdict の出典編入、paper なら citation-formatter） (3) `git status` 確認。

**公開権限**: task request が commit / publish / deposit を含むかをそのまま使う。
この skill 固有の確認形式や追加 gate は設けない。

## 早期停止条件

以下を検出した時点で chain を中断し、ユーザーに報告する:

- Code Review / Security Review / Cross-Model Review が **`CRITICAL`** を返した
- Verify ステップで build / types / tests のいずれかが失敗
- `fix` で根本原因の仮説が証拠で支持されない
- Phase 0 (`/search-first`) で `Adopt` Verdict → 実装方針の再 plan を要請
- `writing` で Verdict マッピング表の CRITICAL 相当（MAJOR ISSUES / ❌ INACCURATE / DRIFT）を検出

<!-- origin: shimo4228 -->
<!-- rationale: ADR-0018 — Chain 詳細を skill implementation-chain へ降格し、2 介入点モデルと Verify ゲートのみ常駐。Phase 0 のエントリポイント固定は search-first skip の実訂正由来。ADR-0027 — Verify の Review 実行確認（reviewer 名簿 + commit せず戻る動詞）は復元: 表は skill でよいが、commit の瞬間に発動する命令は常駐でないと効かない（実測 54%→20%） -->
<!-- review-when: implementation-chain の自発発火率が実測で立った時 / harness が plan・verify をネイティブに強制し始めた時 / Verify 4 項目のいずれかが hook 化された時 -->
# Planning Standards

提案・推薦・方針の提示など、ユーザーに判断を求める場面では、What（何を）に加えて
**Why（根拠）と Alternatives（他に検討した選択肢）**を添える。「何をするか」だけの
リストは不完全。トレードオフ・前提・仮定があれば明示する。

## 証拠ベースの意思決定

アーキテクチャ判断・技術選定・API 設計には証拠を添える（ドキュメント、ベンチマーク、
既存パターン）。「X が最適と思う」は不十分 →「X が最適。理由: [証拠]」。
証拠が見つからない場合はその旨を明記し、仮定として扱う。

## Phase 0: External Research

計画のステップを書き出す**前に**、既存ソリューションを調査する。

**エントリポイントは `/search-first` skill の呼び出しに固定する**。WebSearch / scout を
直接呼んで Phase 0 を済ませてはいけない — skill body が定める Step 0 (要件の text 出力) を
skip すると、ユーザーに対する course-correct ウィンドウが閉じ、後段の Decide / Implement に
必要な articulation が記録に残らない。scout は search-first の **Full Mode 内部**で起動される
実装詳細であり、Phase 0 と等価ではない。

- **実行する**: 新機能で既存ライブラリ・ツールが存在しうる / 新規依存の追加・技術選定 /
  ユーティリティ・ヘルパー・抽象化の新規作成
- **省略してよい**: バグ修正・リファクタ・設定変更 / プロトタイプ・スパイク /
  プロジェクト固有のビジネスロジック（外部解がありえない）

計画に **External Research Findings** セクションを含め、skill が返した Verdict を書く。
Verdict は skill 内部で確定するので、この層は "呼んだ" と "受け取った" だけを保証する。

| Verdict | 計画への影響 |
|---------|-------------|
| **Adopt** | そのまま採用。計画はインテグレーション中心に |
| **Extend** | 採用 + 薄いラッパー・設定の計画を追加 |
| **Compose** | 統合コストを評価してから計画確定 |
| **Build** | 自作する。何を調査し何が不適だったかを記録 |

Stop hook (`hooks/search-first-verdict-check.sh`, advisory) が Verdict の存在を検査する。
PreToolUse による hard 強制は非導入（2026-07-06: false positive で実装が止まるコスト >
advisory の遵守率。enforcement は secret scan / ruff など決定論的に判定できる箇所に限る）。

## 機能要求のチャレンジ（複雑性を足す前に）

新機能・アーキテクチャ変更・依存追加・抽象化導入の前に、**実装方法でなく存在意義**を問う。
「そもそもこれは必要か / 誰が本当に求めているか / 解こうとする問題は実在するか」。
ROI を**時間見積もりで計算しない**（不確実）。代わりに 複雑性 × 価値 × 使用頻度（毎回/時々/稀）
の表で代替案と比較し、同じ複雑性でより高い価値の選択肢がないか確認する。

**警戒すべきトリガーワード**（口に出たら一度立ち止まる）:
「将来のために…」（YAGNI）/「きれいな設計だから…」（Architectural Vanity）/
「せっかく調査したから…」（サンクコスト）/「クレジットが余ってる…」（Credit Anchoring）/
「すぐできる…」（時間ベース ROI の誤り）。

サンクコスト（調査・ドキュメント済み）は判断材料にしない。正しい問いは「今ゼロから
始めるとして、これを優先するか？」。疑わしいときは architect に**忌憚ない本質評価**
（実装可否でなく "build すべきか"）を依頼する。

## Prototype Before Scale

スケール実行（データ生成、自律ループ、API マイグレーション等）の前に、小規模トライアル
（3-5件、1サイクル）で品質ベースラインを確立してからフルスケールに進む。

## Implementation Chain

実装着手前にタスク種別を判定し、対応する agent chain を **plan に front-load** する。
**chain を組むときは Skill ツールで `implementation-chain` を呼ぶ**（受動的なポインタ参照は
発火しない — 2026-07-28 skill-comply 実測で neutral prompt の自発発火 0/3 → TASKS.md T-001）。
種別判定表・Chain Matrix（種別 × ステップ）・Review 起動条件・Writing Chain の
ルーティング・早期停止条件は同 skill（正本）に従って組む。

### 2 介入点モデル

ユーザーの介入は以下 2 点のみ。途中の agent 起動・ステップ遷移は介入なしで進める:

1. **Plan 確認** — chain が確定した時点（`writing` では doc 分類とルーティング先が確定した時点）
2. **意図確認** — コミット直前（`writing` では公開・deposit 直前の人間 gate と同一点）。
   提示物は対象で分岐する — behavior-shaping artifact / control plane / **検査の証拠を作るもの**は
   **本文**、実装コード・生成物は**意図の要約**（`plan との差分` の 3 値宣言必須）。
   不可逆・高影響は区分によらず本文へ**昇格**。Verify の PASS 一覧は提示しないが破棄もしない。
   正本: [`human-gate.md`](human-gate.md)

`fix` 種別の根本原因確認待ち（[`debugging.md`](debugging.md) の 仮説 → 証拠 → 確認待ち →
修正フロー）は **明示的な例外**として残す。

### Verify ステップ（chain 最終ステップ・commit の門）

**Review 実行確認**（下の 4 項目より前に立つ門）: 変更内容と task 種別に応じて Review 群を
起動済みか確認する — code review（python-reviewer / code-reviewer / swift-reviewer）・
security-reviewer・**codex-review**（`feat` / `fix` は必須）・`refactor` なら refactor-cleaner。
**未起動なら commit せず Review に戻る**。決定論ゲートの全 PASS は review の代替にならない
（テストが通っても残る欠陥 — 認可・並行性・設計盲点 — を見る別の層）。種別ごとの要否は
skill: `implementation-chain` の Chain Matrix。

そのうえで:

1. **repo の機械ゲートを実行** — `.claude/verify.sh`（引数なし = 全体検査）。format / lint /
   type check / build / test / 依存監査を **repo が所有**する。ツール名をこの層に書かない
   （ツールは数年で入れ替わるので、常駐ルールに書けばそこが陳腐化の発生源になる）。
   ゲートが無い repo なら skill: `verify-bootstrap` で立てる — 立てずに手で回すのは
   その場しのぎで、次のセッションに残らない
2. **secret scan** — hardcoded keys / tokens の不在確認（[`security.md`](security.md)）
3. **doc sync 確認** — Doc Sync 発火条件に該当する変更なら、対応 doc が同じ diff にあるか
4. **`git status` 確認** — 意図しないファイルが含まれていないか

4 項目はすべて機械 / agent の担当で、人間に上げるのは FAIL のみ（[`human-gate.md`](human-gate.md)）。
全 PASS でのみコミット可。FAIL があれば停止してユーザーに報告する。

commit 境界では hook (`hooks/verify-precommit.sh`) が同じゲートを `--staged` で自動実行する。
hook は言語を知らず、`.claude/verify.sh` の有無と exit code だけを見る。

See skill: verify-bootstrap

# Fable 委譲 enforcement — ~/.claude harness 変更プラン

目的: judge-tier (Fable) セッションが plan 承認後にそのまま実装へ流れる穴を塞ぎ、
実装を build-tier (Opus) へ委譲する既定を「文言」から「機構 + 文言」へ格上げする。
根拠: ADR-0043:111-121 の 2026-08-22 実測事故（Fable が台帳を介さず実装に入り使用限度到達）。

## 推奨する最小構成（結論先出し）

**採用: B → C → A → D → ADR。E は RFC 起票のみ（実装しない）。**

- **B（spawn.sh --model、既定 opus）が最重要**。唯一の機械的な穴（build セッションが
  fable を継承する）を閉じる。これ 1 つで dispatch 経路 3 本すべてがモデル pin 可能になる。
- **A（ExitPlanMode PostToolUse advisory）**が行動面の穴（plan 承認 → そのまま実装）を
  正確な継ぎ目で塞ぐ。block にしない（後述）。
- **C（文言反転）**は A の advisory が指す先を正しくするために必須（advisory が
  「条件を満たさなければ自己実装してよい」という現行文言を指すと効果が薄まる）。
- **D（rules 1 行）**は plan mode を通らない実装（「これ直して」で直に Edit）を
  カバーする唯一の常駐層。1 行のポインタなので rules-thin 文化と両立する。
- **E は含めない**。B が完了すれば spawn-session 経路が完全 pin になり、Agent tool
  経路の検証は緊急でなくなる。未検証注記は残し、RFC 起票（rfc-writer）に落とす。

実装順序: B（機械・単体テスト可能）→ C（B の新機能を参照する文言）→ A（hook + bats +
settings.json 配線）→ D（1 行）→ ADR 起票。

---

## B. spawn.sh の --model 対応（機械層・最優先）

**変更ファイル**: `skills/spawn-session/spawn.sh`, `skills/spawn-session/SKILL.md`

**要点**:
1. spawn.sh:118-119 の起動行は `-- --remote-control "$NAME"` で `--` 以降を claude に
   転送済み（--remote-control で実証済みの同一機構）。ここに `--model "$MODEL"` を追加:
   ```
   -- --remote-control "$NAME" ${MODEL_ARGS[@]}
   ```
   実装は bash 配列で（空のとき語が消える形。`${MODEL:+--model "$MODEL"}` の
   クォート事故を避ける）。
2. インターフェース: **第 3 位置引数 `[model]`、既定 `opus`**。
   - `spawn.sh <project-dir> [display-name] [model]`
   - 省略時 = `opus`（既存の全呼び出し箇所が自動的に build-tier pin になる — 望む挙動。
     spawn-session の主用途は dispatch であり、design 用途は例外側）
   - **opt-out**: `inherit` を渡すと `--model` フラグ自体を付けない
     （セッションは settings.json の `model: fable` を継ぐ = design セッション用）。
     `fable` を明示的に渡すことも可（意図の記録として推奨）。
   - 入力検証: `[a-z0-9.-]` 以外を含む model 文字列は即エラー（コマンドラインへ渡すため。
     spawn.sh 既存の NAME サニタイズと同じ思想）。
3. 成功時出力に `model: opus` の 1 行を追加（検収時に pin を目視確認できる）。
4. SKILL.md: Usage に第 3 引数を追記。「design セッションを立てるときだけ `inherit` /
   `fable`」の 1 行。NOT for に変更なし。

**副作用の設計**: 既定 opus により「Fable の design セッションを spawn したい」正当ケースが
1 語（`inherit`）の追加コストになる。これは意図的 — 事故側（fable 継承の実装セッション）の
既定コストをゼロにする方が、設計側の 1 語より重要（ADR-0043 の実測事故が根拠）。

**検証**: herdr が `--model opus` を claude に届けることの実測 1 回
（`herdr agent start ... -- --remote-control x --model opus` で立てたセッションの
transcript 先頭 model フィールド確認）。bats は spawn.sh の引数パース部だけ
（herdr 呼び出しは mock 不能なので、MODEL 解決ロジックを関数化してテスト）。

---

## C. implementation-chain / task-triage の文言反転

**変更ファイル**: `skills/implementation-chain/SKILL.md`（「実行者の決定」段落）,
`skills/task-triage/SKILL.md`（dispatch 経路 3 本の注記）

**要点**:
1. implementation-chain「実行者の決定」— エスケープハッチを反転する。**すべき**。
   現行: 「条件を満たさない・分割できないなら、このセッションで実装してよい」
   変更後の構造:
   - **judge-tier セッションの既定 = dispatch**（packet を書いて build-tier へ渡す）。
   - 自己実装は例外で、**該当する例外種別を plan に 1 行で記録**したときだけ:
     (a) 対象が harness/repo の設計文書・ADR・skill/rule の散文編集（実装 chain の
         Review 群が回らない類。= Fable の本業）
     (b) dispatch 条件を検証した結果、満たせない具体的理由がある（分割不能・
         受け入れ条件が判定不能 等 — 理由名を書く）
     (c) ユーザーが「このセッションでやって」と明示した
   - 例外で自己実装する場合も Review 群の build-tier pin（既存 :127-132）は維持。
   - ADR-0016:20 の反対圧力への応答を 1 文残す: dispatch の文脈損失は packet
     （task-triage の packet-template）で救う — model 継承で救わない。
2. task-triage dispatch 経路の更新:
   - spawn-session 行の「モデル pin 不能」相当の記述を削除し、
     `spawn.sh <worktree> "<name>" opus`（既定なので省略可）に更新。
   - Agent tool 経路の未検証注記 (2026-08-17) は**残す**（E を先取りしない）。
   - `claude --bg -w <name> --model opus` の「文言のみ実績なし」も現状維持。

**advisory/block の議論対象外**（文言層）。**副作用**: なし — 例外 (a) が Fable の
正当な harness 編集（設計文書・ADR・skill）を明文で保護する。ここが A の誤爆吸収装置を兼ねる。

---

## A. ExitPlanMode PostToolUse hook（advisory・fail-quiet）

**変更ファイル**: `hooks/plan-executor-notice.sh`（新規）, `settings.json`
（PostToolUse に matcher `ExitPlanMode` を 1 エントリ追加、timeout 10）,
`tests/plan-executor-notice.bats`（新規）, `hooks/README.md`（1 行）

**advisory を選ぶ理由（block ではなく）**:
- review-model-notice.sh の block 基準は「判定が完全に機械的で誤検知の余地が無い」。
  本 hook は満たさない — plan の内容（実行者決定済みか / 対象が ADR・skill 散文か /
  writing 種別か）が判定に必要で、tool_input からプランが読める保証が無い（制約）。
- PostToolUse の継ぎ目は「ユーザーが plan を承認した直後」。ここで block すると
  人間の承認直後に機械が差し戻す形になり、正当ケース（harness 設計文書の編集 =
  このタスク自体がその例）で毎回ぶつかる。
- 実効性は文脈注入で足りる: 承認直後 = 実装の最初の Edit の直前ターンなので、
  advisory が読まれてから実装が始まる（review-model-notice の Skill 直呼びのような
  「同 turn で走ってから読まれる」時系列問題が無い）。

**判定ロジック**（review-model-notice.sh のパターン流用）:
1. `tool_name == "ExitPlanMode"` を確認（matcher 冗長ガード、既存 hook と同じ理由）。
2. セッションモデル判定: `transcript_path` を `tail -c 2000000` → 直近 `"model"` フィールド
   → `*fable*` 照合。**一致しない・読めない・transcript 不在 → exit 0（fail-quiet、制約通り）**。
   テスト用 env override `PLAN_EXECUTOR_TRANSCRIPT`（REVIEW_MODEL_TRANSCRIPT と同型）。
3. best-effort 抑制（読めなくても成立する設計）: `.tool_input.plan` が読めて、かつ
   実行者決定の痕跡（`実行者` / `spawn-session` / `--model opus` / `dispatch` のいずれか）を
   含むなら exit 0（決定済み plan に二度言わない）。読めない・痕跡なし → advisory を出す。
   誤 negative の代償は「余計な advisory 1 回」で無害。
4. `_advisory-common.sh` を `${BASH_SOURCE[0]%/*}` 相対 source → `emit_advisory PostToolUse "$msg"`。
   本文は静的文字列のみ（transcript / plan 由来テキストを本文へ**エコーしない** —
   repo 由来データを運ばないので untrusted 枠は不要、かつ注入面を作らない）。

**通知文面の要点**（静的、~5 行）:
- このセッションは judge-tier (Fable)。plan は承認された — 最初の実装 Edit の前に
  「実行者の決定」を 1 行で行う（正本: skill implementation-chain）。
- 既定は dispatch: packet を書いて build-tier へ
  （`spawn-session`（既定で opus pin）/ `Agent(model:"opus")` / `claude --bg --model opus`）。
- 自己実装は例外 — 設計文書・ADR・skill/rule 散文の編集、dispatch 条件を満たせない
  具体的理由、ユーザーの明示指示のいずれかを plan/応答に 1 行記録してから。
- 参照: ADR-0043（三役の正本）。

**副作用の設計**: advisory なので Fable の正当な harness 編集は止まらない。文面自体が
例外 3 種を明記するので、正当ケースでは「1 行記録して続行」で摩擦が最小。
plan mode を使わないセッションでは発火しない（そこは D が受ける）。

**settings.json 変更**（配線のみ、ロジックは外部 — harness 規約通り）:
```json
{ "matcher": "ExitPlanMode",
  "hooks": [{ "type": "command",
              "command": "bash ~/.claude/hooks/plan-executor-notice.sh",
              "timeout": 10 }] }
```

**bats**（review-model-notice.bats を雛形に）: fable transcript → 封筒出力 /
opus transcript → 無音 / transcript 不在 → 無音 / plan に「spawn-session」含む → 無音 /
tool_name 不一致 → 無音 / 封筒形式は advisory-envelope 検査に準拠。

---

## D. rules 層への 1 行配線

**変更ファイル**: `rules/common/planning.md`

**要点**: 既存の Build-or-not 行の直後に 1 行:
> - judge-tier セッションでの実装は dispatch が既定 — 実行者の決定と例外は
>   skill: `implementation-chain`（三役の正本: ADR-0043）

**すべき**。理由: (1) planning.md の charter は「実行入口と機械ゲートの配線だけ常駐」で、
これはまさに入口配線 1 行 + ポインタ（判断表は skill 側）— rules-thin 文化と両立。
(2) A は plan mode 経由でしか発火せず、plan mode を通らない ad-hoc 実装（Fable セッションで
「これ直して」）をカバーする常駐層は rules だけ（調査事実 7 の穴）。
planning.md の review-when ヘッダに本変更の失効条件（モデルティア区別の消滅）を含める。

---

## E. Agent tool 実装経路の検証 — このプランに含めない

**判断**: RFC 起票（skill: rfc-writer）で別タスク化。理由:
- B 完了で spawn-session が完全 pin になり、検証済み経路が dispatch の主線として成立する。
  Agent tool 経路の検証は「経路を増やす」改善であり、本プランの目的（漏れを塞ぐ）に不要。
- task-triage の既存注記（2026-08-17「measurement batch で先に試す」）が検証手順まで
  含んでおり、RFC はそれを 1 エントリに写すだけ。
- 検証は実測（hook 発火・skill 可用性・permission 表面の 3 点）で、本プランの
  read-only 設計作業と性質が違う。

---

## ADR 起票（実装後、adr-writer で）

新規 ADR「judge-tier 実装の既定を dispatch にする enforcement 層」:
- 参照: ADR-0043（三役・注記の事故記録）、ADR-0016:20（文脈損失は packet で救う）。
- 決定: B/C/A/D の 4 層と、A を advisory に留めた理由（誤検知面 + 承認直後の block 摩擦）。
- 失効条件: substrate がセッション単位の model routing / native dispatch を持ったら
  A と D を外し、B の既定は残す（review-model-notice の失効条件と同期）。

## リスクと未確定点

1. **herdr の `--model` 転送**は `--remote-control` と同一機構だが未実測 → B の検証 1 回で確定。
   失敗時の fallback: agent start 後に `herdr agent prompt` で `/model opus` を打鍵（非推奨、
   実測で必要になったときのみ）。
2. **ExitPlanMode の PostToolUse payload 形**（tool_input.plan の有無）は不確か → 設計は
   plan が読めない前提で成立（best-effort 抑制のみが degrade）。
3. **advisory の実効性**は保証ではない → 4 層の重ね（機械 pin の B が最後の砦）で受ける。
   実装後 1〜2 週の実測（土日の使用限度に再到達するか）を ADR の Review-when に置く。

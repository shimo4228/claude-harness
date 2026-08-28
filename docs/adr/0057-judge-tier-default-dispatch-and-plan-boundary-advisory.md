# ADR-0057: judge-tier セッションの実装既定を dispatch へ反転 + plan 承認境界の advisory

## Status

accepted

## Date

2026-08-28

## Context

Fable（judge-tier）の使用限度が、最も使う土日に枯渇する（著者報告 2026-08-28）。[ADR-0043](./0043-task-triage-loop-judge-build-human.md)
は判断 = judge-tier / 実装 = Opus 新セッション / merge = 人間という三役分担を定めたが、
実装が judge-tier セッションに流れ込む構造がその後も残っていた。

skill: `implementation-chain` の「実行者の決定」（2026-08-22 追加）は、plan 末尾で「このセッションが
実装するか」を 1 行で自答させるだけの規約で、発火機構を持たない。「条件を満たさないならこの
セッションで実装してよい」というエスケープハッチが、自己判定のまま素通りしていた。

同じ穴は ADR-0043 自身の 2026-08-22 注記に実測記録がある — judge-tier セッションが台帳を介さず
実装に入り、使用限度に到達した。当時の対応は `implementation-chain` への導線追加のみで、enforcement
は未設置のままだった。

rules 層には委譲判断を常駐させる 1 行が無く、skill が読まれなければ委譲判断自体が発火しない。
Edit / Write を対象にした judge-tier 向けの hook も存在しない — 現状 block されるのは
`hooks/review-model-notice.sh` による `/code-review` / `/simplify` の直呼びのみで、実装そのものを
検知する経路ではない。

## Decision

1. **既定の反転**: `implementation-chain`「実行者の決定」を反転する。judge-tier セッションの既定は
   build-tier への dispatch とする。自己実装を選ぶ場合は、次のいずれかを plan に 1 行記録した
   ときに限り許可する。
   - (a) 設計文書・ADR・skill / rule 散文の編集（judge-tier の本業）
   - (b) dispatch 条件を満たせない具体的な理由がある
   - (c) ユーザーの明示指示がある

   文脈損失（[ADR-0016](./0016-writer-agents-render-not-decide.md) の「model 継承は能力しか救わず
   文脈損失は救わない」）は dispatch を避ける理由にしない。文脈損失は dispatch する packet
   （dispatch 先へ渡す作業指示一式 — 形の正本は skill: `task-triage`）の充実で救う。
   例外 3 種の**正本は `implementation-chain`「実行者の決定」** — hook の静的文面と本 ADR の
   列挙は要約であり、drift したら SKILL.md が勝つ。

2. **plan 承認境界の advisory hook**: `hooks/plan-executor-notice.sh` を新設する。`ExitPlanMode` の
   PostToolUse で発火し、transcript からセッションモデルを判定して fable セッションのときのみ
   通知する（判定不能時は fail-quiet）。plan 本文（`tool_input.plan` — 実 ExitPlanMode 呼び出し
   271/271 で非空、transcript corpus 2026-06-15〜2026-08-28 の実測）に定型句「実行者の決定」が
   既にあるときは抑制して黙る。抑制トークンはこの定型句 1 つのみ — 当初案の話題語 4 トークン
   （実行者 / dispatch / spawn-session / --model opus）は同 corpus で 31/271 を抑制しうち 30 件が
   誤抑制（dispatch を話題にしただけの plan）だったため却下した。通知内容は「実行者の決定」を
   想起させる静的文面のみとし、plan 由来のテキストは一切エコーしない（`rules/common/security.md`
   の harness 脅威面規律に従う — repo/セッション由来の未検証データを指示チャネルへ流さない）。
   `settings.json` の PostToolUse に配線し（同ファイルは git 追跡外のため、配線の可視面は
   `hooks/README.md` の表）、`tests/plan-executor-notice.bats` で固定する。

3. **常駐 1 行**: `rules/common/planning.md` に「judge-tier セッションでの実装は build-tier への
   dispatch が既定」の 1 行を追加する。これが plan mode を通らない ad-hoc 実装をカバーする唯一の
   常駐層になる。

4. **変更しないもの**: `skills/spawn-session/spawn.sh` は変更しない。task-triage の herdr 経由
   dispatch では Opus 起動が実運用で既に成立している（著者実測、2026-08-28）。成立の機構は
   spawn.sh 自身ではない — spawn.sh はモデル引数を渡さず（起動行に `--model` は無い）、起動
   セッションのモデルは環境側の既定に従う。spawn-session へのモデル固定は design セッション
   起動の用途を壊すため、著者が明示的に拒否した。Review の実行モデル pin（2026-08-24、
   `implementation-chain`）も不変とする。

## Review-when

- substrate がセッション単位の model routing を自発的に行うようになったら、hook と rules 行を
  外す（`implementation-chain` 側の既存失効条件と同じ）
- 導入後の土日で Fable 使用限度の再到達が起きたら、当該セッションの transcript で advisory の
  発火有無を突き合わせる — 発火していたのに無視されたなら block 昇格を、発火していなかった
  なら経路（抑制条件・ExitPlanMode を通らない実装）の見直しを再検討する
- spawn された build セッションが judge-tier で起動する観測が出たら（環境既定モデルの変更等）、
  spawn 経路のモデル pin（Decision 4 の却下）を再訪する
- モデルのティア区別と使用限度が消えたら本 ADR 全体を外す

## Alternatives Considered

### spawn.sh に --model opus を既定付与

却下。herdr 経由 dispatch の Opus 起動は実運用で既に成立している（著者実測。機構は Decision 4 —
spawn.sh はモデルを渡さず環境既定に従う）。spawn-session のモデル固定は design セッション起動の
用途を壊すため、著者が明示的に拒否した。前提が崩れる場合の再訪条件は Review-when に置いた。

### block hook（ExitPlanMode 直後の機械差し戻し）

却下。plan 内容の機械判定が不可能で誤検知があり、承認直後の差し戻しが例外 (a)（harness 設計文書の
編集）と毎回ぶつかる。`review-model-notice.sh` の block 採用基準「判定が完全に機械的で誤検知の
余地が無い」を満たさない。

### Edit/Write への PreToolUse ゲート

却下。例外 (a) の散文編集と実装コードを payload から区別できず、摩擦が大きい。

### skill 文言の改良のみ

却下。自発発火は文言改良で伸びない（ADR-0018 の実測知見と同根）。発火時刻を持つ hook が要る。

## Consequences

### Positive

- plan 承認直後 = 最初の実装 Edit の前ターンに想起が入る（抑制されるのは plan が定型句
  「実行者の決定」を既に含むときのみ。`Skill` 直呼び block で見た「同 turn で走ってから
  読まれる」問題が構造的に無い継ぎ目）
- 既定反転により「dispatch しない」側が記録を要するようになる（従来は dispatch する側に説明責任が
  あった）
- plan mode を通らない実装にも rules の常駐 1 行が残る

### Negative

- advisory は強制力が無く無視できる（効果は Review-when の限度再到達で実測する）
- `ExitPlanMode` を通らない実装経路には hook が発火しない（rules 1 行のみでカバーする）
- 例外 (a)〜(c) は依然自己申告のままで、enforcement ではなく記録の義務化に留まる
- dispatch の機械 pin 経路（Agent tool）は hooks / skills 発火の同一性が未検証のまま
  （`task-triage` の 2026-08-17 注記）。既定反転でこの経路の重みが上がる —
  検証タスクは [RFC-0016](../../rfcs/0016-agent-tool-build-path-hook-parity.md)
- plan 拒否時にも PostToolUse が発火するかは未実測（2026-08-28）。発火しても advisory 1 通の
  ノイズに留まる

### Neutral / Follow-ups

- [ADR-0043](./0043-task-triage-loop-judge-build-human.md) の三役分担・2026-08-22 注記が本 ADR の
  出発点になった実測記録
- Review の実行モデル pin（`implementation-chain`、2026-08-24）は本 ADR の対象外で不変

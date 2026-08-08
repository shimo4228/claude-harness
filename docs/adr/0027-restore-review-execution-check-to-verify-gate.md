# ADR-0027: Review 実行確認を Verify ゲートに復元 — 表は skill、時刻に紐づく動詞は rules

## Status

superseded by [ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) — 13% だった hook が
ADR-0028 で93%へ改善したため、rules の名簿を外し、commit hook から implementation-chain を再提示

## Date

2026-08-01

## Context

[ADR-0018](0018-rules-rightsize-for-claude5.md) の rightsize（2026-07-25）で、
`rules/common/planning.md` から Implementation Chain の仕様一式を skill へ降格した。
その際、Chain Matrix（表）と一緒に **Verify ステップの Review 実行確認文**も削除された。

削除された原文（3c7bd19 時点、planning.md:232）:

> **Review 実行確認**: 直前の Review / Cleanup ステップ（refactor-cleaner / python-reviewer /
> code-reviewer / security-reviewer / codex-review）を変更内容・種別に応じて起動済みか確認する。
> 未起動なら commit せず Review に戻る。

rightsize 後の planning.md では、これが Verify 節の前置き一句
「変更内容に応じた Review agent を起動済みか確認したうえで:」に圧縮され、
**個別 reviewer の名指しと「commit せず戻る」という動詞が失われた**。

### 実測（`metrics/skill-usage.jsonl` + `metrics/agent-usage.jsonl`、skill-comply の合成シナリオを除外）

| 期間 | feat/fix commit | codex-review 実行 | 率 |
|---|---:|---:|---:|
| 2026-07-05〜07-24（rightsize 前） | 83 | 45 | **54%** |
| 2026-07-25〜08-01（rightsize 後） | 65 | 13 | **20%** |

境界は 2026-07-25 で、rules 内の codex 言及が 13 → 4 に落ちた日と一致する。
残った 4 件はすべて `agents.md` の別文脈（cross-agent rules 共有 / herdr 委譲）で、
**レビュー chain としての codex-review は rules 層から完全に消滅していた**。

同じ低下は codex に限らない。2026-07-15 以降の実 repo で、code review 系 agent
（swift-reviewer 5 / python-reviewer 4 / code-reviewer 4）の起動は計 13 件、
分母 feat/fix 66 件に対して **約 20%**。消えた 1 行が全 reviewer を名指ししていたため、
削除で 3 系統が同時に落ちた。

### skill 化そのものは失敗していない

| | rightsize 前 | 後 |
|---|---:|---:|
| implementation-chain の invoke | 0 | 28 |
| codex-review の実行 | 45 | 13 |

chain skill は呼ばれるようになったのに、reviewer は走らなくなった。
問題は「skill が呼ばれないこと」ではなく「**skill 内の表の `Y` が実行に変換されないこと**」。

原因は**読まれる時刻**にある。implementation-chain は plan 時に読まれ、codex-review は
skill 自身が「実装後に diff へ走らせる」と規定している — 読む時点と実行時点が構造的に離れており、
plan で列挙した chain entry が実装を挟んだ commit の瞬間まで生き残らない。常駐 rule は
commit の瞬間にも context にあるため、この時間差を吸収していた。

hook（`hooks/review-chain-notice.sh`）は commit 時点で python-reviewer / security-reviewer を
名指ししているが、閾値（コード 3 ファイル or 追加 150 行）に達する commit は harness repo の
feat/fix 45 件中 11 件のみで、大半は素通りする。また同 hook の文面に codex-review は登場しない。

## Decision

**表は skill に置いたまま、時刻に紐づく動詞だけを rules に戻す。**

`rules/common/planning.md` の Verify ステップ冒頭に、Review 実行確認の門を復元する
（常駐増 6 行）。Chain Matrix（13 行の表）・種別判定・条件付き発火は
skill: `implementation-chain` に置いたままとし、ADR-0018 の降格判断は維持する。

復元する要素は 3 つ:

1. **個別 reviewer の名指し** — code review 系 / security-reviewer / codex-review /
   refactor-cleaner。総称（「Review agent」）では codex-review が skill であるため射程外に読まれる
2. **「未起動なら commit せず Review に戻る」という動詞** — commit という決定点に紐づく命令
3. **「決定論ゲートの全 PASS は review の代替にならない」** — 2026-07-29 に ADR-0085 実装
   27 ファイルを review なしで commit した失敗の再発防止。従来 hook のヘッダにしか
   記録されていなかった知見を rules 側にも置く

## Alternatives Considered

- **CI（GitHub Actions）で codex review を強制** — 却下。(a) 対象 5 repo 中 4 つに CI が無く、
  harness repo は直近 135 commit すべて親 1（merge commit ゼロ・PR 運用ゼロ）の main 直コミット
  運用のため、CI は push 後の事後通知にしかならず第 2 介入点に間に合わない。(b) codex 出力を
  Claude が検証して verdict を所有する fold 層（[ADR-0013](0013-cross-model-review-seam-via-codex.md)
  の「dirty prototype」扱い）が失われ、未検証の findings が人間に届く。(c) 認証が
  ChatGPT アカウント（`~/.codex/auth.json`）から API 従量課金へ変わる。
  ただし**公開 repo の tag push（release / deposit）ゲート**としては別途成立しうる — commit の門とは別層
- **hook の閾値撤廃 / CODE_RE 拡張のみで対処** — 却下（単独では不足）。hook は advisory であり、
  かつ harness repo の feat/fix の 47% は md のみで CODE_RE に掛からない。時刻の問題は解けるが
  種別ベースの判断（`feat`/`fix` は codex 必須）を hook は持てない
- **implementation-chain skill の description 強化で自発発火を上げる** — 却下。skill は既に
  invoke 28 件と呼ばれており、発火率は問題ではない。読まれる時刻が問題
- **rightsize 前の planning.md をそのまま巻き戻す** — 却下。ADR-0018 が削った 13 行の表は
  判断材料であり、常駐コストに見合わないという評価は現在も有効

## Consequences

- **容易になる**: 1 行の復元で 3 系統（code review / security / cross-model）が同時に戻る。
  reviewer を追加・改名したときも、名簿が rules にあるので commit の門から漏れない
- **容易になる**: 次に rightsize するとき、この ADR が「表と動詞は別層」という切り方を残す。
  常駐削減は表・判断材料を対象にし、**特定の瞬間に発動する命令文は残す**
- **困難になる**: rules/common/planning.md の常駐が 6 行増える。ADR-0018 の削減幅を一部戻す
- **困難になる**: reviewer 名簿が rules と skill: implementation-chain の 2 箇所に載る。
  skill 側が種別 × ステップの正本、rules 側は commit の門で読み上げる名簿、という役割分担で
  重複を許容する（drift 検査は harness_lint の対象外 — 名簿の増減は稀）
- **観測**: 復元の効果は `metrics/skill-usage.jsonl` と `agent-usage.jsonl` で継続測定できる。
  8 月中の feat/fix に対する codex-review 実行率が 54% 水準に戻るかを再確認する
  → **同日 [ADR-0028](0028-review-notice-full-scope-and-adr-reviewer.md) で hook 面も変更したため、
  この観測は rules 復元単独の効果ではなく合計効果の測定になった**。hook のカバレッジが
  実測 13% と判明し、「hook が一定量鳴っている」という切り分けの前提が成立しなかったため、
  保留していた hook 強化を前倒しした

## References

- [ADR-0013](0013-cross-model-review-seam-via-codex.md) — cross-model review seam の設計（fold 層）
- [ADR-0018](0018-rules-rightsize-for-claude5.md) — 本 ADR が部分的に override する rightsize 判断
- `hooks/review-chain-notice.sh` — commit 時点の advisory リマインド（決定論面）
- `skills/implementation-chain/SKILL.md` — Chain Matrix の正本

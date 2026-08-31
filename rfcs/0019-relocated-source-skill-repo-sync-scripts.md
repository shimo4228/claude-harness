---
state: done 2026-08-30
review-when: 3 repo の sync script が新 source で dry-run → apply を完走したら done。移設方針自体が変わったら（正本が harness へ戻る等）本 RFC は obsoleted
---
## Summary

正本移設（RFC-0017 手段 D、2026-08-29）で source を失った 3 つの公開 skill repo の sync script を、新しい正本パス（paper-lab / zenn-content）へ更新する。

## Motivation

2026-08-29 の移設で、以下 3 repo の sync source が `~/.claude` 配下から消えた。skill repo 版 `sync-from-local.sh` は source 不在時に silently skip でなく **abort** する仕様（公開済み skill が静かに消えるのを防ぐ設計）なので、現状これらの repo は sync 不能:

| 公開 repo | 旧 source | 新正本 |
|---|---|---|
| shimo4228/citation-sync | `~/.claude/skills/citation-sync` | `~/MyAI_Lab/paper-lab/.claude/skills/citation-sync` |
| shimo4228/claude-skill-paper-ecosystem | `~/.claude/skills/paper-ecosystem` + `paper-writing` | `~/MyAI_Lab/paper-lab/.claude/skills/` 同名 2 skill |
| shimo4228/claude-skill-writing-ecosystem | `~/.claude/skills/writing-ecosystem` | `~/MyAI_Lab/zenn-content/.claude/skills/writing-ecosystem` |

同日の harness-sync 実行（集約 + skill-health + akc-cycle は完了）でスコープ外として残した積み残し。放置すると次に該当 skill を更新した人が abort に当たる。

## Reference-level explanation

- 各 repo の `scripts/sync-from-local.sh` の source 解決（`HARNESS_SYNC_SOURCE` default）を新パスへ変更。skill repo 版 script は「byte-identical に vendor する」規約だったが、source が repo ごとに異なる形になるため、パスを env / 変数 1 箇所に隔離して本体の byte-identity を保つ形が望ましい
- agent 同梱 repo（paper-ecosystem / writing-ecosystem）は手動 diff 対象の `agents/*.md` 正本も移設済み — paper 系 5 本は `paper-lab/.claude/agents/`、writing 系 6 本は `zenn-content/.claude/agents/`。sync 手順の注記と実際の diff 先を一致させる
- harness-sync SKILL.md の Repo mapping 表には移設注記済み（2026-08-29）。script 更新後、注記の「次回 sync 時に必要」を落とす

## Rationale and alternatives

- **代替: 公開 repo 側を凍結**（signal-first-research 型）— 却下。3 skill とも生きた正本があり、乖離は時間とともに増える
- **代替: 正本を harness へ戻す** — RFC-0017 の residency 削減を巻き戻すので不採用

## Status

done 2026-08-30 — **手段 A**（3 repo の default を直接書き換える）を著者が選択し、同日実施・merge 済み。

| repo | commit | 新 default | dry-run |
|---|---|---|---|
| citation-sync | `65a7224` | `$HOME/MyAI_Lab/paper-lab/.claude` | exit 0、ABORT なし、drift 1（`skills/citation-sync/pyproject.toml` — 新正本の ruff `C901` / `mccabe max-complexity=15` が公開側に未反映） |
| claude-skill-paper-ecosystem | `f2425a4` | `$HOME/MyAI_Lab/paper-lab/.claude` | exit 0、ABORT なし、drift 0 |
| claude-skill-writing-ecosystem | `e17312c` | `$HOME/MyAI_Lab/zenn-content/.claude` | exit 0、ABORT なし、drift 1（`writing-ecosystem/SKILL.md:172`） |

`${HARNESS_SYNC_SOURCE:-…}` の env override は 3 repo とも保持。実行ロジックは 1 バイトも変えていない — 未移設 repo との差は `SOURCE_DIR` 1 行とコメント 3 か所のみで、3 repo 相互の差は path の 2 行だけ。冒頭の「vendored byte-identical / repo 固有ロジック禁止」宣言は、source の既定だけが repo ごとに異なりロジックは共通、という実態に合わせて書き直した。

**B・C を却下した理由**（2026-08-30 著者判断）: byte-identity は「同じ script を配る」ための手段であって目的ではなく、正本の置き場所が repo ごとに違うという事実は既に発生している。B（23 repo 全てに repo-local override を足す）は 3 か所の問題のために 23 か所を触る形で割に合わず、C（呼び出し側のドキュメント化のみ）は素で叩けば ABORT が残るため起票理由が消えない。

**同時に片付けたこと**: `skills/harness-sync/SKILL.md` の Repo mapping 表から「script の source 更新が次回 sync 時に必要」の注記 3 件を撤去し、共通 env の記述に「3 repo だけ既定が移設先を指す」を明記した。

**残り（本 RFC の範囲外として明示）**: 同梱 agent の突き合わせは手作業のまま。`sync-from-local.sh` は `skills/` しか同期しないため、paper 系 5 本（`paper-lab/.claude/agents/`）とwriting 系 6 本（`zenn-content/.claude/agents/`）の正本 diff は script では取れない。Repo mapping 表の該当 2 行にその旨を注記した。機構化するかは需要が出てから判断する。

## Next action

無し。次に 3 repo を sync するときは、各 repo で `./scripts/sync-from-local.sh --dry-run` → `git diff` を確認 → apply、の通常手順で回る。同梱 agent は手動 diff。

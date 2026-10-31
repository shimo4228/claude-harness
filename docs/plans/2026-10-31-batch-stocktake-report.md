kind: internal
# 棚卸し skill 群を「1 枚の report → 一括承認 → task branch で適用 → ff」に変えるための現状調査

前提の設計判断は 2026-10-31 の grill-me セッションで著者と確定済み（plan 本体に要約）。この report は
変更対象と制約の実物を固定する。

## 再現

1 件ずつ確認する手順を持つ箇所（`grep -rnE 'Never batch|one by one|\[y/n/skip\]|one diff at a time' skills`）:

| file:line | 内容 |
|---|---|
| `skills/skill-stocktake/SKILL.md:346-362` | Phase 5 Consolidation。`[y/n/skip]` を非 Keep ごと、Improve は skill-creator への引き渡しも 1 件ずつ |
| `skills/rules-stocktake/SKILL.md:167-189` | Phase 4 Consolidation。承認後に session 内で直接適用（Design note 2、同ファイル :28） |
| `skills/agent-stocktake/SKILL.md:238-255` | Phase 4 Consolidation。同形 |
| `skills/rules-distill/SKILL.md:111-125` | Phase 3。"Never batch the approval" と「rules を自動で変えない」hard gate |
| `skills/repo-asset-stocktake/SKILL.md:99-` | 同形。"Retire all 6? [y/n]" を明示的に禁止 |
| `skills/generation-audit/SKILL.md:103,117` | 常駐層（rules / CLAUDE.md / output style）の修正行を diff 1 つずつ承認 |
| `skills/learn-eval/SKILL.md:198-208` | per-verdict `[y/n/skip]`。棚卸しではなく session 抽出なので対象外 |

著者の判断点が増える二次経路: `skills/skill-creator/SKILL.md:18`（§1 Entry ⏸ author confirms）と
`:171`（§7 Author read-through GO）。skill-stocktake が Improve を N 件渡すと判断は 2N 回になる。

既に一括の形: `skills/context-sync/SKILL.md:51,168`（既存ファイル編集は自動適用、新規作成だけ Phase 3 冒頭で 1 回確認）。
task-triage の digest も「語彙の当てはめは一括 OK、rule 変更・リスク受容・drop は個別」（`skills/task-triage/SKILL.md:91-97`）。

## 原因

- 1 件ずつ確認は commit `f8b08bc`（2026-07-03「config-gc の confirm-each 設計を stocktake/distill 系 3 skill に適用」）で
  入った。ADR は無い。本文に残る理由は "apply all 5? [y/n] defeats the design" の 1 句だけで、防ぎたいのは
  「中身を見ない一括承認」と読める。agent-stocktake（`7584620`, ADR-0022）と repo-asset-stocktake（`68d77df`）が文言を複製した。
- 判断点を 1 つにまとめられない原因は 2 層: (1) 各 stocktake の Consolidation が逐次質問、(2) skill-creator の §1 / §7 が
  stocktake からの呼び出しでも著者で止まる。

## 確認

制約として plan に効く実物:

- **公開 repo**: rules-stocktake / agent-stocktake / rules-distill は単独 skill repo に同期される
  （`skills/harness-sync/SKILL.md:237-241`）。Artifact と ArtifactData は Claude アプリ / claude.ai 固有なので、report の
  契約は媒体に依存しない項目 schema を正本にし、Artifact はこの harness での描画先とする必要がある。
- **rules 台帳の古さ**: `skills/rules-stocktake/results.json` の `evaluated_at` は 2026-07-26T21:09:41Z。台帳キーに
  human-gate / patterns / hooks（実在しない）があり、boundary / evals / knowledge-staleness / llm-first-code /
  practitioner-identity / public-records（実在）が無い。
- **退役の証拠**: rules-stocktake は Dissolve / Retire 判定と review-when を Stage 2 の最初の問いに持つ（`:113-131`）が、
  akc-cycle.md の「完了証拠は held-out transfer」を実行する手段は無い。with/without は skill-creator §5 で skill のみ
  （`skills/skill-comply/SKILL.md:21`）。
- **review-when-watch**（`skills/review-when-watch/`, ADR-0080, 毎日 06:10）は RFC と ADR の review-when を daily-research
  ノートに照合する。rules の `<!-- review-when: -->` は対象外。
- **hooks**: `settings.json` が配線する hook は 21 本、`hooks/` の残り 4 本は `_*-common.sh` の共有 lib、+ README。孤児は 0。
  発火記録は hook 個別（`metrics/research-gate.jsonl` など）で、全 hook の共通ログは無い。回帰テストは `tests/*.bats` に
  一部の hook だけ。棚卸しの skill は無い。
- **定期実行の機構**: `scripts/triage-tick.sh` が Herdr 上の常駐 session を探す / 無ければ skill: `spawn-session` で
  作り、prompt を送り、失敗時に Slack に送る。`--prompt-file` で別 loop が同じ機構を使える（:10, :44）。plist は
  `scripts/launchd/` が正本で、登録は人間が行う。
- **台帳の機械検査**: `scripts/hooks/harness_lint.py` は rules の header を検査する（rules-stocktake :68-70 から参照）。
  台帳キーと実物の一致は誰も検査していない。

## Still unknown

- spawn-session で起こした Herdr の Remote Control session で Artifact tool と ArtifactData が使えるか（対話の
  desktop セッションでは使える）。月 1 回の無人実行の段で、dry-run の 1 回で確かめる。使えなければ report を
  `.notes/stocktake/` の Markdown に書き、公開は著者がいる session に回す。
- Artifact の `db` capability の書き込み単位と、ページ側で判定を切り替えたときの保存形。実装の最初に
  skill: `artifact-capabilities` を読んで決める。
- rule を外した `claude -p` の作り方。rules は `~/.claude/rules/` から自動で読み込まれるので、一時的な
  `CLAUDE_CONFIG_DIR` にするか、`--settings` で外せるかを実測する。`claude -p` の子が user 設定を継承する罠は
  memory `reference_claude_p_child_inheritance.md` にある。

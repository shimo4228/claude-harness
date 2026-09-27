# RFC-0033 実行: 過去 plan を各 repo の docs/plans へ移す

## Context

`~/.claude/plans/`（legacy、gitignore 下）に 255 本の過去 plan が repo と切り離されて溜まっている。
RFC-0033 と ADR-0085 の注記（2026-09-27、`831ff9e`）で、既存 plan を各 repo へ移すことにした。
公開先に入るものはエージェントの一次点検と著者の確認を通す。

作業の現状（2026-09-27）:
- plan から repo への対応表は会話ログから作った。255 本すべてが一致した
- 点検は 238 本が済んでいる。結果は `<scratchpad>/all.tsv`（列: plan / repo / verdict / 理由 / FIX 内容）
  - PUBLIC 170 / FIX 28 / WRONG_REPO 25 / PENDING_ARTICLE 7 / PRIVATE 8
- 非公開 repo（aeon-shop・zafu-ios・lab-charter）の分は点検していない。repo でない cwd の 6 本は残すと決めた
- CA と zenn の 124 本は、非公開置き場（`.notes/plans`、`planning/plans`）へコピー済み
- 2 repo の `settings.local.json` から `plansDirectory` の上書きは外してある
- `~/.claude/docs/plans` を claude-harness へ同期する機能は実装済み（claude-harness `6810192`）
  - git が追跡している plan だけを同期し、`$HOME` の実値があれば止まる
  - harness-sync SKILL.md:52 と ADR-0085 Decision 5 の「GO 待ち・未実施」は古い記述

## 振り分けの規則

| verdict | 行き先 |
|---|---|
| PUBLIC | 行き先 repo の `docs/plans/` |
| FIX | TSV の FIX 列どおりに伏せてから `docs/plans/` |
| WRONG_REPO | 理由の列にある本当の行き先 repo へ入れ、その repo の規則で扱う。claude-harness 行きは `~/.claude/docs/plans`（公開は harness-sync に任せ、claude-harness は直接編集しない） |
| PENDING_ARTICLE | zenn の `planning/plans`。記事の公開後に移す |
| PRIVATE | 各 repo の非公開置き場。`~/.claude` 行きの分は legacy のまま残す |
| 非公開 repo の分 | 各 repo の `docs/plans/`（点検なし） |
| 残すもの | repo でない cwd の 6 本、Ghostty・Yazi の端末設定 2 本、deep-research の Claude / Codex 結果 2 本 |

著者の回答が無い記事 3 本（crystalline-pizza、cozy-pondering-hartmanis、quizzical-herding-squid）は、
PENDING_ARTICLE として扱う。

## 手順

1. **振り分け表を固める**: `all.tsv` から最終表 `route.tsv`（plan / 行き先 repo / 置き場 / FIX 内容）を作る
   - WRONG_REPO の行き先は、理由の列から手で転記する
   - 既存のリンク元があるものは残す: `~/.claude/docs/adr/0009`・`0012`・`0085` と RFC-0033
2. **コピーと伏せ字**: 各 plan を置き場へコピーする（legacy の元ファイルは消さない）
   - FIX の置換を適用する
   - ファイル名に `users-shimomoto-tatsuya-` を含む 6 本は、その部分を外して改名する
   - CA と zenn で PUBLIC・FIX になったものは、非公開置き場から `docs/plans/` へ移す
3. **機械検査**: 各 repo の `docs/plans/` に次の語が 0 件であることを確かめる
   - `shimomoto`（`_` と `-` の両方）、`/Users/`
   - 非公開 repo の名前: `aeon`、`gai-passport`、`doctrine-corpus`、`lab-charter`
   - `extraUsage`、メールアドレスのパターン
   - 当たったものは直すか、非公開置き場へ戻す
4. **著者の確認**: repo ごとの本数と、FIX を当てた diff の一覧を見せる
5. **commit**: repo ごとに 1 commit（`docs(plans): RFC-0033 過去 plan を移す`）
   - 対象: CA・zenn・AKC・authorship-strategy・daily-research・edge-frontier・shimo4228・attention-not-self・agent-attribution-practice・akc-cycle・jev-research-pipeline・herdr-toolkit・writing-agent・aeon-shop・zafu-ios・lab-charter・`~/.claude`
   - 各 repo の verify gate を通す
6. **古い記述を直す（`~/.claude`）**: 手順 5 とは別の commit にする
   - harness-sync SKILL.md:52 の「GO 待ち・同期されない」を、現行の規則として書き直す
   - ADR-0085 Decision 5 に日付付きの注記を足す（実装済み: claude-harness `6810192`）
   - RFC-0033 の Status に結果を記録する
7. **公開**（著者の GO の後）
   - 公開 repo へ push する
   - harness-sync で claude-harness に同期する
   - claude-harness の作業ツリーに別セッションの未 commit 変更（`rfcs/`）があれば、先に片付けてから同期する

legacy の `~/.claude/plans/` の元ファイルは、この plan では消さない。消すかどうかは別に判断する。

## 重要なファイル

- `<scratchpad>/all.tsv`、`plan-map.tsv`（振り分けの入力）
- `~/MyAI_Lab/claude-harness/scripts/sync-from-local.sh:157-169, 232-249`（docs/plans の収集と home path scan。変更しない）
- `~/.claude/skills/harness-sync/SKILL.md:52`、`~/.claude/docs/adr/0085-plans-as-records-in-docs-plans.md`
- `~/.claude/rfcs/0033-allocate-legacy-plans-to-repos.md`

## 検証

- 振り分け表の網羅: `route.tsv` の行数 + 残すもの = 255、置き場の重複 0
- 手順 3 の grep が全 repo で 0 件
- `bash ~/MyAI_Lab/claude-harness/scripts/sync-from-local.sh` を dry に走らせる
  - home path scan と secret scan を abort なしで通る
  - `docs/plans/` が staging に入っている
- 各 repo で `git status` が clean（commit 後）

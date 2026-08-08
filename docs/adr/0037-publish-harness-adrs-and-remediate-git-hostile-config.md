# ADR-0037: harness ADR を claude-harness へ公開し、前提として commit 面 hook の敵対的 .git/config を無害化する

## Status
accepted

## Date
2026-08-08

## Context

claude-harness (公開スナップショット) は origin filter で skills / agents / rules を publish しているが、それらが「なぜ今の形か」の記録である `docs/adr/` は非公開だった。value-layer harness engineering の主張の核心は「promoted / measured / audited な構成は engineered である」で、その audit の実物証拠が ADR 群である。構成だけ公開して判断履歴を伏せるのは、主張の最も強い部分を非公開にしていることになる。ハーネス一式を公開する例は他にもあるが、設計判断の時系列記録まで公開する例はほぼ無く、clone している層が他所で取れない差別化コンテンツでもある。

公開前レビュー (general-purpose agent、全 ADR + index 全読) が 5 件を flag した。うち公開ブロッカーは 2 系統:

1. **職業の特定**: ADR-0006 / 0007 が判断の一因として、shimo4228 ペルソナを超えた実世界の雇用形態 (本業の就業規則上の兼業制限) に触れていた。
2. **未修正の実行可能脆弱性の手法開示**: ADR-0034 が、敵対的 repo の `.git/config` に外部 diff driver / fsmonitor を書くと commit 面 hook の `git` 実行時に任意コード実行になる手法を記述し、かつ「未対応の hook を名指しで列挙」していた。ADR-0035 (0034 を supersede) が deferred のまま残すと記録していた残余リスク (台帳 T-GIT-HOSTILE-CONFIG / T-SIGPIPE-HEAD-PIPE) で、公開すると修正前に攻撃対象リストを配ることになる。

残り 3 件 (ADR-0031 の `--allowedTools` 誤解、0032 の同型 git-config 機構、0034 の一般的記述) は追加対処不要と判断した: 0031 は製品挙動を利用者に警告する責任ある writeup、0032 の機構は同一 ADR 内で既に緩和済み、0034 の一般的記述は本 ADR の修正でもはや未修正の対象を指さない。(`rules/common/security.md` は origin ECC-customized で公開 snapshot には含まれないため、免責根拠には使わない。)

## Decision

**1. `docs/adr/` を claude-harness の 4 つ目の managed subtree として同期する。**
`sync-from-local.sh` の `SUBTREES` に `docs/adr` を追加。ADR はハーネス自身の設計判断で定義上すべて自作のため、他 subtree と違い origin filter を掛けず**ディレクトリ丸ごと**を staging する。README (ja/en) に「設計判断 (ADR)」節、llms.txt / llms-full.txt に ADR 層のエントリを追加。ADR は日本語のままとし README にその旨を注記する (翻訳維持はコストに見合わない)。以後の ADR は公開される前提で書く。丸ごと同期のため ADR 本文が `../../` で参照する docs/adr 外のパス (`.notes/TASKS.md`、ECC-customized な rules 等) は公開面でリンク切れになる — これは既知の副作用として受容する (下記 Consequences)。

**2. 職業の特定を一般語に置換する。**
ADR-0006 / 0007 で職業を特定していた語を、職業を特定しない一般語 (本業の就業規則) に書き換える (6 箇所)。判断の論理 (兼業制限が貢献停止の一因だった) は保ち、職業の特定だけを外す。git 履歴 (ローカル正本) には元の記述が残る。

**3. commit 面 5 hook の敵対的 .git/config を実際に無害化してから公開する** (手法開示より修正が先)。
`secret-scan` / `verify` / `bandit` / `ruff-format` / `harness-lint` の 5 hook すべてで、`git` 呼び出しに `-c core.fsmonitor= -c core.hooksPath=` を付けて repo 内 config 由来の任意コード実行経路を封じる。このうち `git diff` を呼ぶ 3 本 (secret-scan / bandit / ruff-format) には `--no-ext-diff` を足して外部 diff driver を封じる (verify / harness-lint は rev-parse のみで diff を呼ばない)。secret-scan は未追跡ファイルを ls-files の出力パスで走査するため `core.quotepath=off` も新規に付け、非 ASCII パスが 8 進エスケープされて走査から漏れるのを防ぐ (検出挙動の変更)。ruff-format の `head` パイプに `|| true` を付けて SIGPIPE fail-open を塞ぐ。secret-scan に敵対的 diff.external の回帰テストを追加 (実行されないこと・検出を鈍らせないことの両面を pin)。修正後、ADR-0034 の残余リスク記述と ADR-0035 の Follow-ups を「解決済み」に更新する。

無害化を `-c diff.external=` (空 config) で行わないのが要点: 空文字は git が空コマンドを外部 diff として実行しようとして `git diff` 自体を壊す。ADR-0034 が当初提案した `GIT=(… -c diff.external= …)` 配列は、`git diff` を通さない薄い reminder hook でしか使われず未検証だった誤りである。正しい無害化は config ではなく diff 呼び出し側の `--no-ext-diff`。

## Alternatives Considered

- **ADR を公開しない (現状維持)** — value-layer harness engineering の audit 層を伏せたまま「engineered だ」と主張することになり、README で昇格させた主張と非整合。却下。
- **claude-harness を At a Glance の 6 本目の practice line として公開する** — ADR ではなく repo 自体の位置づけの話。DOI を持たず ResearchLine でなく EcosystemRepo なので表の行契約を壊す。別判断として却下済み (本 ADR の対象外)。
- **ADR を英訳して公開する** — doctrine 層 (LLM 経由読者) には日本語で無問題、人間の海外読者にも README 注記で足りる。36 本の翻訳維持は release ごとに二重コストを生むので却下。
- **職業の記述をそのまま公開する** — 意図的開示なら可だが、撤回不能 (clone / クロール済みになる) で、既存の公開面 (skills/agents/rules) では一度も触れていなかった。一般化のコストは 6 箇所の語句置換のみで、論理は保てるため一般化を選択。
- **職業に触れる 2 ADR を同期から除外する** — index に欠番が出て、除外理由の管理が恒常的に必要になる。一般化なら丸ごと publish のまま済む。却下。
- **脆弱性を修正せず、ADR-0034 の手法記述だけ redact して公開する** — 脆弱性自体は残る。`rules/common/security.md` の Security Response Protocol 5「同種を全掃」も未完のまま。修正の方が redact より根治的で、台帳 2 件も閉じられるため修正を選択。
- **脆弱性が未修正なので ADR-0034 だけ同期対象から外す** — 欠番と、参照している他 ADR (0035 等) からのリンク切れが出る。却下。
- **継続同期でなく一度きりの snapshot として公開する** — 「以後の ADR は公開前提で書く」恒常コストと毎回の sanitization を負わずに済む。しかし snapshot は即座に陳腐化し、「live な audit trail」という公開の主目的 (ハーネスが今も回っていることの証拠) を裏切る。継続同期こそが要点なので却下。恒常コストは公開前レビューを release 手順に組み込むことで管理する。

## Consequences

**容易になること:**
- value-layer harness engineering が「宣言」でなく「監査可能な実践」であることを、判断履歴という一次証拠で示せる。README の主張と公開物が整合する。
- clone している層が、構成の背後にある「なぜ (採用・退役・撤回)」を追える。失敗・撤回を含む trail がそのまま差別化コンテンツになる (open-failure disclosure と整合)。
- commit 面 hook 群の敵対的 .git/config 経路が実際に塞がり、台帳 T-GIT-HOSTILE-CONFIG / T-SIGPIPE-HEAD-PIPE を閉じられる。Security Response Protocol 5 (同種を全掃) がコード上完了する。

**困難になること / 残余リスク:**
- 以後の ADR は「公開される前提」で書く制約が乗る。職業・第三者情報・未修正脆弱性の手法は書く前に自己検閲が要る。今回の書きぶりでは実質的な変化は小さいが、公開前レビューを release 手順に組み込むのが安全側 (`sync-from-local.sh` の secret scan は API key 形状しか見ず、職業・第三者情報・脆弱性手法は検出しない)。
- **修正はコード上 5/5 だが、回帰テストは 1 hook・1 ベクトル (secret-scan の diff.external) しか固定していない。** fsmonitor / hooksPath は 5 本とも無テスト。ADR-0034 自身が「この層は自分を検査できず、回帰テストが唯一の防壁」と書いた層なので、テスト被覆の非対称は残余リスクとして明示する。
- 丸ごと同期の副作用で、ADR 本文が参照する docs/adr 外のパス (`.notes/TASKS.md`、`skills/learned/*`、ECC-customized な `rules/common/coding-style.md` 等) は公開面でリンク切れになる。ADR の論旨は自己完結しているため読解は妨げないが、リンクは辿れない。
- ADR が日本語のままなので、英語圏の人間読者には障壁が残る (機械翻訳・LLM 経由の読解は可)。
- `git_target_dir` の複合コマンド左端一致 (T-GIT-TARGET-RIGHTMOST) と `--allowedTools` の非制約性 (ADR-0031) は本 ADR の対象外で、別 trust boundary として残る。

**受容するトレードオフ:**
- ADR-0006 / 0007 の一般化で、判断が置かれた実世界の文脈がわずかに薄まる。git 履歴 (ローカル正本) には元の記述が残るので、遡及可能性は保たれる。

## References

- [ADR-0034](0034-move-review-check-before-the-approval-gate.md) —— T-GIT-HOSTILE-CONFIG / T-SIGPIPE-HEAD-PIPE の出所。当初 `-c diff.external=` 配列を提案した箇所 (:164 に in-place 注記) を、本 ADR が `--no-ext-diff` へ訂正する
- [ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) —— 0034 を supersede した現行 ADR。Follow-ups で 2 タスクを deferred と記録していた (:128)。本 ADR がその deferred を解消し、0035 側の当該項目も解決済みへ更新する
- [ADR-0007](0007-open-concept-network-effect.md) —— 開放型ネットワーク効果。ADR 公開はこの「概念は開放し帰属は学術インフラで守る」方針の commit 面での適用
- `rules/common/security.md` —— Security Response Protocol 5 (同種を全掃)。本 ADR がこれを完了させる
- 台帳 [T-GIT-HOSTILE-CONFIG / T-SIGPIPE-HEAD-PIPE](../../.notes/TASKS.md) —— 本 ADR で done
- skill: `harness-sync` —— `docs/adr` subtree 追加を反映済み

# ADR-0038: commit 面 hook を curated allowlist で claude-harness へ公開し、前提として抽出器の 2 経路と textconv を塞ぐ

## Status
accepted

## Date
2026-08-08

## Context

ADR-0037 で `docs/adr/` を claude-harness へ公開した結果、**参照の空白**が生まれた。公開面の 6 ドキュメント — ADR-0027 / 0028 / 0034 / 0035、`rules/common/planning.md`、`skills/verify-bootstrap/SKILL.md` — が hook のファイル名と内部挙動を名指しで論じているのに、コード実体が公開 repo に無い。ADR-0034 に至っては `git` 呼び出しの `-c` フラグ 1 つの是非を数段落かけて論じており、読者はその対象を見ることができない。判断履歴を公開して「監査可能な実践」だと主張する以上、監査対象が欠けているのは主張の穴である。

ただし `~/.claude/hooks/` を丸ごと同期する選択は取れない。理由は 3 つ:

1. **配線の正本 `settings.json` は公開できない。** `permissions` / `env` / `enabledPlugins` / `statusLine` はマシン固有の runtime state を含む。ただし探索の結果、**`hooks` セクション自体は portable** だと判明した — 公開候補 5 本の配線行はすべて `bash ~/.claude/hooks/*.sh` で、絶対パスを持つのは公開対象外の `herdr-agent-state.sh` (SessionStart) だけ。当初想定していた「散文で install 手順を書く」より強く、**コピペで動く JSON 断片**を出せる。
2. **依存が芋づる式に広がる。** commit 面 hook は `_git-target-common.sh` と `scripts/hooks/verify_allow.py` に依存し、主張を検証可能にするなら bats も要る。
3. **半分は `~/.claude` 専用発火で再利用価値が無い。** episode-log 系・`contemplative-name-reminder.sh`・`herdr-agent-state.sh`・`harness-lint-precommit.sh` は他人の環境で発火しないか、発火しても意味を成さない。丸ごと公開は「動かないコードの寄せ集め」を配ることになる。

前提となる敵対的 `.git/config` 脆弱性の修正 (ADR-0037 の決定 3) は完了した「つもり」だった。**公開前レビューがこれを否定した** — 実測付きで 3 件の未修正欠陥が出た。いずれも公開対象の hook にあり、うち 2 件は secret gate の end-to-end バイパスとして再現した:

1. **エスケープされた引用符**: 抽出器は引用符 span を落としていたが `\"` を残していたため、sed がそこを span 終端と見なし、続く `; git -C <decoy> commit` が素のセグメントとして露出した。コメントは「読み取りだけの hook はこの抽出で足りる」と書いていたが、それは誤りだった。
2. **複合コマンドの単一ターゲット**: 台帳 T-GIT-TARGET-RIGHTMOST。左端一致で `git -C /decoy commit && git -C /real commit` の /real を見逃す。当初は右端一致への変更を検討したが、**右端は左端と対称**で順序を入れ替えれば同じ回避が成立することを実測した — 単一値である限り原理的に閉じない。
3. **`diff.<driver>.textconv`**: ADR-0037 が「同種を全掃」と書いた敵対的 `.git/config` クラスの兄弟ベクタ。`--no-ext-diff` は textconv を止めない (`--no-textconv` が要る)。**external を封じたことで git が textconv へ落ちるようになり、兄弟ベクタが表に出た**。repo 内 `.git/config` + `.gitattributes` から任意コマンドの実行を実測で確認した。

3 件とも既に公開済みの ADR-0034 / 0037 が手法クラスを記述している。修正せずに hook コードを並べれば、「塞いだ」と書いてある隣に穴の在り処を示す地図を配ることになる。手法開示より修正が先 (ADR-0037 の順序) を今回も適用する。

## Decision

**1. commit 面 5 hook + 共有部品 2 + bats 3 を、新規 3 subtree として公開する。**

`hooks/` に `secret-scan-precommit.sh` / `verify-precommit.sh` / `bandit-precommit.sh` / `ruff-format-precommit.sh` / `review-chain-notice.sh` / `_git-target-common.sh`、`scripts/hooks/` に `verify_allow.py`、`tests/` に `git-target-extraction.bats` / `secret-scan-precommit.bats` / `review-chain-notice.bats`。`~/.claude` と同じ相対パスに置き、install 先も同じにする。

`review-chain-notice.sh` は当初候補外だったが含める。公開済みの `rules/common/planning.md` が名指ししており、17 行で harness 固有の前提を持たず、bats もある。除外すると参照の空白が残る。

**2. 公開判定は origin filter でなく明示 allowlist にする。**

`sync-from-local.sh` に `HOOK_ALLOWLIST` 配列を置き、列挙されたファイルだけを staging する。skills / agents / rules と同じ `origin:` マーカー方式に相乗りしない — **公開は provenance (誰が書いたか) ではなく curation (このマシンの外で再利用できるか) の判断**だからである。非公開にしたい hook (`harness-lint-precommit.sh` 等) も自作である以上、origin を付けた瞬間に公開されてしまい、両者が同義になる。

allowlist は `SUBTREES` に追加した 3 つの wholesale-replace subtree と組み合わせる。allowlist から entry を外せば次回 sync で公開側から消え、`git diff` に削除として現れる (removal semantics が壊れない)。allowlist の entry が source に存在しなければ sync は abort する — rename / 削除の取りこぼしを「黙って部分公開」にしないため。

**3. 配線は `settings.json` 全体でなく `hooks` 断片だけを `docs/hooks.md` に転記する。**

install 手順・各 hook の発火条件表・bypass 環境変数・`verify_allow.py` の承認モデル・`~/.claude` 固定の再配置制約・bats の被覆範囲を 1 ファイルにまとめる。**`hooks/README.md` には置かない** — `hooks/` は wholesale-replace される subtree なので、手書き doc を中に置くと毎回の sync で消える。`docs/adr/` の隣に置く。README (ja/en) に `### Hooks` 節を追加し、そこから `docs/hooks.md` へ送る。

**4. 公開前に、レビューが出した 3 件を修正する** (公開そのものと同一の判断単位に含める)。

- **抽出器はエスケープを先に落とす。** `\<char>` を除去してから引用符 span を除去する。順序が逆だと 1 の経路が開く。
- **抽出器は全一致を返す。** `git_target_dirs` を新設し、複合コマンド内の全 repo を出現順・重複除去で返す。読み取り専用の 3 hook (secret-scan / bandit / ruff-format) を全件走査へ変更する。単一値の `git_target_dir` は最後の一致を返す wrapper として残し、**ゲートを実行するため対象を 1 つに決める必要がある** `verify-precommit.sh` だけが使う (選ばれなかった対象は検査されないが、verify にとってこれは「ゲートを回し損ねる」であって「未承認コードを実行する」ではない — 承認台帳が第 2 の防壁として残る)。台帳 T-GIT-TARGET-RIGHTMOST はこれで閉じる。
- **`--no-textconv` を `--no-ext-diff` と対で入れる。** diff を呼ぶ 3 hook すべて。`DIFF_SAFE` 配列に集約し、片方だけ足す drift を構造的に防ぐ。

回帰テストを 12 本追加する (抽出器 8 / secret-scan 4)。**負のコントロールで、修正前のコードに対して実際に落ちることを確認する** — 通るだけのテストは何も pin していない。bats は 150 → 162 本。

**5. 非公開のまま残すものを明示する。**

`harness-lint-precommit.sh` + `harness_lint.py` (`~/.claude` repo 専用発火)、episode-log guards・`contemplative-name-reminder.sh`・`herdr-agent-state.sh` (harness 内部専用)。非 commit 面 (`validate-bash.sh` / `docs-prewrite.sh` / `bats-autorun.sh` / `log-*-usage.sh`) は別判断として今回は見送る。

## Alternatives Considered

- **`hooks/` を丸ごと同期する** — 依存グラフの問題は解けるが、内部専用 hook が「他人の環境で動かないコード」として混入する。公開面の第一印象を「読者向けに整理されていない dump」にする代償が、参照の空白を埋める利得を上回る。却下。
- **hook 先頭に `# origin: shimo4228` を足し、既存 `has_origin()` に相乗りする** — 機構が skills / agents / rules と揃い、新しい概念を増やさない。しかし provenance と公開意図が同義になり、非公開の自作 hook に origin を付けられなくなる (= 全 hook が「未分類」か「公開」の二択になる)。origin タグの意味を壊すので却下。
- **`~/.claude/hooks/.publish` に allowlist を外出しする** — sync script を汚さないが、公開 repo 側から根拠が見えないファイルが 1 つ増える。allowlist は 10 行で、script 内に置いた方が「なぜこれだけか」のコメントと同居できる。却下。
- **hook を公開せず ADR だけ残す** — 現状維持。参照の空白を放置し、「監査可能」の主張の一部が検証不能なまま残る。却下。
- **`settings.json` を sanitize して丸ごと公開する** — `permissions` の allowlist は作業対象 repo の path を露出し、`enabledPlugins` は導入 plugin を露出する。sanitize の判断が同期のたびに必要になる恒常コストに対し、利用者が本当に必要とするのは `hooks` 断片だけ。却下。
- **bats を公開しない** — 同期対象が減り README も短くなるが、「敵対的 `.git/config` を塞いだ」「staged diff でなくコマンドが commit する内容を見る」といった主張を読者が検証する手段が消える。ADR-0037 が残余リスクとして挙げたテスト被覆の非対称を、公開面でさらに広げることになる。却下。
- **抽出器を右端一致にする (単一値のまま)** — 変更が小さく、正当な書き方 (`git -C R add -A && git -C R commit`) と ADR の worked example では確かに改善する。しかし実測の結果、右端は左端と**対称**で、順序を入れ替えるだけで同じ回避が成立した。「修正した」と書いて公開すれば、textconv と同じ構図 (塞いだと書いてある隣に穴) を再生産する。却下。
- **抽出器の欠陥を直さず、コメントから手法記述だけ削る** — 公開面から exploit の手引きは消えるが、欠陥は残り、台帳も閉じない。ADR-0037 が「redact より修正」を選んだ前例と非整合。却下。
- **verify-precommit.sh も全ターゲット化する** — 一貫はするが、ゲートの**実行**を複数 repo に広げるのは意味論の変更 (どの repo の verify.sh がどの staged 内容を見るのか曖昧になる) であり、承認台帳という第 2 の防壁が既にある。読み取りと実行で扱いを分けるのは意図的。却下。
- **未整備の verify / bandit / ruff-format 用 bats を書いてから公開する** — 被覆が揃うが、公開作業に実装タスクが 3 本ぶら下がりスコープが膨らむ。被覆の非対称は `docs/hooks.md` に明記して読者に渡す方が、公開を遅らせるより誠実。却下 (別タスクとして残す)。

## Consequences

**容易になること:**
- ADR-0027 / 0028 / 0034 / 0035 と `rules/common/planning.md` の参照が実体に解決する。ADR が論じている `-c core.fsmonitor=` や引用符 span 除去を、読者がコードで確認できる。
- secret gate の 2 経路のバイパスと 1 件の任意コード実行が実際に塞がり、台帳 T-GIT-TARGET-RIGHTMOST を閉じられる。**公開を決めたことが欠陥の発見動機になった** — 「他人に読まれる」前提のレビューが、日常運用では出てこなかった 3 件を出した。公開のコストとして数えていた公開前レビューが、実際には検出器として働いている。
- 「hook は無人で走る = permission プロンプトを経ない」という trust boundary と、それに対する承認台帳という回答が、実装ごと公開される。同じ問題を持つ他の harness にそのまま移植できる。
- `verify-precommit.sh` の「hook は言語もツールも知らない」契約と `skills/verify-bootstrap` が公開面で対になる。

**困難になること / 残余リスク:**
- **利用者は `settings.json` を手で編集する必要がある。** skills / rules の「コピーすれば効く」と違い、hooks は配線が要る。`docs/hooks.md` の JSON 断片で摩擦は下げたが、ゼロにはならない。
- **`~/.claude` 固定の再配置制約。** `verify-precommit.sh` は `$HOME/.claude/scripts/hooks/verify_allow.py` をハードコードしており、別の場所に置くと台帳が見つからず**警告だけ出して全 commit を素通しする**。fail-open なので、利用者が「ゲートが効いている」と誤認する余地がある。`docs/hooks.md` に明記したが、コードで担保していない。
- **5 本中 3 本が無テスト。** verify / bandit / ruff-format には bats が無い。ADR-0037 が残余リスクとして記録したテスト被覆の非対称を、公開面がそのまま引き継ぐ。今回 3 本に入れた全ターゲット化と `--no-textconv` も、抽出器と secret-scan の suite 経由でしか間接的に守られていない。
- **`.claude/verify.sh` を持つ未承認 repo では Python 系 3 ゲートが同時に黙る。** verify は未承認なので実行せず、bandit / ruff は実行権の有無だけを見て譲る (承認台帳を参照しない)。それぞれ stderr には出るが、どれも block しない。挙動は変えず `docs/hooks.md` に明記する選択を取った — 台帳参照を足すと commit ごとに python3 起動が増え、この 2 hook は元々退役予定だから。
- **敵対的 `.git/config` クラスは「全掃した」と再び言えるわけではない。** 今回 textconv が出たのは external を塞いだ副作用であり、同じ形 (1 つ塞ぐと兄弟が表に出る) は今後も起こり得る。この層は自分を検査できず、回帰テストが唯一の防壁である (ADR-0034 の指摘) という構造は変わっていない。
- **抽出器は依然 regex による shell 解析である。** 全ターゲット化はセグメント単位の取りこぼしを閉じたが、shell 文法の完全な解析ではない。実行を伴う経路が承認台帳を第 2 の防壁として持つ設計は、この限界を前提に置いたまま維持する。
- **公開コードが非公開ファイルを参照する dangling reference が残る。** hook のコメントが `rules/common/security.md` (origin: ECC-customized で非公開) と `.notes/` を指す。公開時に書き換えると**公開版と実働版が乖離する**ため、あえて sanitize せず `docs/hooks.md` に断り書きを置いた。ADR 丸ごと同期のリンク切れ (ADR-0037) と同種の受容。
- **allowlist が恒常的なメンテ対象になる。** commit 面 hook を追加・rename するたび `sync-from-local.sh` の更新が要る。source に無い entry で abort する設計にしたので、忘れると次回 sync が止まって気づける (黙って部分公開されない)。
- 公開面の hook が bug を持っていた場合、利用者の commit を止める / 止めそこねる形で影響が出る。MIT・無保証だが、README と `docs/hooks.md` で「これは一人が実際に回している hook であって framework ではない」と位置づけを明示した。

**受容するトレードオフ:**
- hook のコメントは日本語のまま公開する。ADR-0037 と同じ判断 (翻訳維持がコストに見合わない)。`docs/hooks.md` は英語で書き、コードが日本語であることを明記する。

## References

- [ADR-0037](0037-publish-harness-adrs-and-remediate-git-hostile-config.md) —— ADR 公開。本 ADR が埋める参照の空白を作った ADR。「同種を全掃」の主張が textconv を取りこぼしていたため、Decision 3 と Consequences に in-place の訂正注記を入れた
- [ADR-0034](0034-move-review-check-before-the-approval-gate.md) / [ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) —— `review-chain-notice.sh` の設計と rightsize。公開対象の 1 本。0034 は T-GIT-HOSTILE-CONFIG の出所でもある
- [ADR-0027](0027-restore-review-execution-check-to-verify-gate.md) / [ADR-0028](0028-review-notice-full-scope-and-adr-reviewer.md) —— verify ゲートと review notice の scope。公開により参照が実体に解決する
- [ADR-0008](0008-ecc-local-only-management.md) —— ECC plugin 無効化。非公開に残す hook 群の出自の一部
- 台帳 [T-GIT-TARGET-RIGHTMOST](../../.notes/TASKS.md) —— 本 ADR の Decision 4 で done (右端一致でなく全ターゲット走査で解決)
- skill: `harness-sync` —— `hooks` / `scripts/hooks` / `tests` subtree 追加を反映する
- `docs/hooks.md` (公開 repo) —— install 手順・承認モデル・被覆範囲の正本

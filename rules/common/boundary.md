<!-- origin: shimo4228 -->
<!-- rationale: ADR-0069 — 境界が packet / task-triage / tick prompt / growth-* / agents.md の 6 箇所に文面違いで散っていた。substrate の一般則（hard to reverse or outward-facing → confirm first）は再宣言せず、このハーネスで何がそれに当たるかと、確認なしで取ってよいリスクだけを置く -->
<!-- review-when: 人間に渡す操作の列挙を足す / 減らす時。判断役の取り込みで main が壊れ人間が revert した回数が 3 か月で 2 回を超えた時（取り込みを人間へ戻す）。substrate が台帳・gate script・scheduled task を outward-facing として自ら扱うようになった時 -->
# 境界 — 人間に渡す操作と、とってよいリスク

**人間に渡す**（このハーネスで不可逆・対外に当たるもの。substrate の「confirm first」の対象）:
公開（投稿・第三者 repo への PR・release / DOI・評判に関わる公開物の更新）/ 課金 /
Slack digest 以外の外部送信 / 台帳の起票・drop（判断役は提案まで）/ permissions・hooks・scheduled task・
`.claude/verify.sh`（承認 hash）・rules・ADR・skills の無人変更（その diff を含む取り込みも）/
自分が spawn していない pane・session / Herdr 委譲（`HERDR_ENV=1` と明示指示の両方。例外は
create-only の skill: `spawn-session` — 新規 workspace/tab と自分が作った pane にしか触れないので
server 稼働だけを前提に実行してよい。明示指示は要る）。

**とる**（確認を待たない）: 検収を通した task branch の main への ff-only 取り込みと push
（force は hook が止める）/ worktree と task branch の中の破壊・方針転換・粗い代替案 1 本・
赤テストのまま次の仮説へ（記録する。commit には verify を通す）/ scratchpad・下書き・`.notes/`
`.growth/` への記録・task branch への commit。「もっと安全な設計を先に」は止まる理由にしない。

**止まって報告する**: 同じ方針で 2 回失敗 / time cap / 前提の反証 / 外部 platform の rate limit
連発（policy signal — `debugging.md`）。そこまでを残して報告する。

機械が止めるもの: `hooks/validate-bash.sh`（`rm -rf /`、force push）、commit gate（verify /
secret scan / harness lint）、episode log の読み込み。

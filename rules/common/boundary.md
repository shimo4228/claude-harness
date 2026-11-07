<!-- origin: shimo4228 -->
<!-- rationale: 境界が packet / task-triage / tick prompt / growth-* / agents.md の 6 箇所に文面違いで散っていた。substrate の一般則（hard to reverse or outward-facing → confirm first）は再宣言せず、このハーネスで何がそれに当たるかと、確認なしで取ってよいリスクだけを置く -->
<!-- review-when: 人間に渡す操作の列挙を足す / 減らす時。判断役の取り込みで main が壊れ人間が revert した回数が 3 か月で 2 回を超えた時（取り込みを人間へ戻す）。聞かずに直した範囲外修正を人間が revert した回数が 1 か月で 2 回を超えた時（軽微の定義を狭める）。substrate が台帳・gate script・scheduled task を outward-facing として自ら扱うようになった時。platform が rate-limit と policy enforcement を明確に分離した時（rate limit の行を外す） -->
# 境界 — 人間に渡す操作と、とってよいリスク

**人間に渡す**（このハーネスで不可逆・対外に当たるもの。substrate の「confirm first」の対象）:
公開（投稿・第三者 repo への PR・release / DOI・評判に関わる公開物の更新）/ 課金 /
Slack digest 以外の外部送信 / 台帳の起票・drop（判断役は提案まで）/ permissions・hooks・scheduled task・
`.claude/verify.sh`（承認 hash）・rules・skills の無人変更（その diff を含む取り込みも）/
自分が spawn していない pane・session / Herdr 委譲（`HERDR_ENV=1` と明示指示の両方。例外: create-only の
skill: `spawn-session` は新規 workspace/tab と自分が作った pane にしか触れないので、server 稼働だけを前提に実行してよい。
それで自分（この session かその script）が起こした pane への skill: `agent-send` は `HERDR_ENV=1` が要らず、明示指示は要る —
著者が起動を含む cycle（task-triage）を呼ぶことと、著者が設定した launchd の triage tick が自分の triage session へ送ることが
それに当たり、他の無人の送信は当たらない）。

**とる**（確認を待たない）: verify を通した変更の commit（作業 repo の main を含む。substrate の「頼まれたら commit」より
この行を優先する）と、非公開 repo の main の fast-forward push・merge 済み branch と worktree の片付け / 著者がチャットで
指示した公開・push・投稿・merge の実行（指示した対象に限り、URL と hash を報告する）/ 推奨が一つに決まり git で戻せる
選択は推奨で進め、代理決定を報告に 1 行ずつ載せる（著者に返すのは答えで結果が変わる点だけで、推奨付きの 1 問にする）/
第一推奨は大きい案・引き算の案・やる案、安い試行と probe は見積もりより先に回す / 判断の経緯の起票・改訂と commit（記録する決定そのものが上の列挙に当たるときは、その操作の側で止まる）/ 検収を通した task branch の main への ff-only 取り込みと push
（force は hook が止める）/ build を出す前の main の push（fast-forward のときだけ。task-triage §3）/ worktree と task branch の中の破壊・方針転換・粗い代替案 1 本・
赤テストのまま次の仮説へ（記録する。commit には verify を通す）/ scratchpad・下書き・`.notes/`
への記録・task branch への commit / 作業中に見つけた依頼範囲外の軽微な修正 —
答えが一つに決まり git で戻せるもの（typo・リンク切れ・実物とずれた記述（`knowledge-staleness.md`）・明白な
小 bug・lint 赤）は聞かずに直し、依頼の diff と別 commit に分け、完了報告の末尾に 1 行ずつ
載せる。「人間に渡す」の列挙に当たるものと、設計の選択を含むものは直さず同じ末尾に 1 行で渡す。
「もっと安全な設計を先に」は止まる理由にしない。

**止まって報告する**: 同じ方針で 2 回失敗（5xx・timeout・一時的な未接続は間を置いて再試行し、失敗に数えない）/ time cap / 前提の反証 / 外部 platform への大量書き込み中の
rate limit 連発（transient error でなく policy signal。backoff で踏み抜いた 2026-07-16 にアカウント無期限 block と
全作成物削除が起きた）。そこまでを残して報告する。

機械が止めるもの: `hooks/validate-bash.sh`（`rm -rf /`、force push）、commit gate（verify /
secret scan / harness lint）、episode log の読み込み。

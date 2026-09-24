# ADR-0069: 境界の正本を 1 rule にまとめる — 人間に渡す操作 / とってよいリスク / 止まる条件、最後のスイッチは判断役へ

## Status

accepted

## Date

2026-09-15

## Context

「何を人間に渡し、何を確認なしでやってよいか」の境界が、文面違いで 6 箇所に散っていた
（2026-09-15 grep）: `skills/task-triage/references/packet-template.md:19,55`（main に触らない /
merge / push / 台帳）、`skills/task-triage/SKILL.md` の role 表 Never does 列と Damping 節
（merges, publishes, touches rules / ADR / hooks / security gates unattended）、
`scripts/triage-tick.sh:86` の tick prompt（Do not merge, publish, or touch …）、
`skills/growth-astra` / `growth-fable`（公開・評判に関わる action は草稿で止める）、
`rules/common/agents.md`（Herdr 委譲は `HERDR_ENV=1` + 明示指示）。正本は無く、1 箇所を直しても
残りが古い文面のまま残る形だった。

substrate（Claude Code の system prompt）は一般則を持つ — "For actions that are hard to reverse or
outward-facing, confirm first" / "Stop only for destructive actions or genuine scope changes"。
[ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) はこれを理由に `rules/common/human-gate.md`
（停止手順）を退役させた。substrate が知りえないのは、**このハーネスで何が不可逆・対外に当たるか**
（台帳の状態、`.claude/verify.sh` の承認 hash、scheduled task、Slack 以外の外部送信）と、
**確認なしで取ってよいリスク**（worktree の中は壊してよい、赤テストのまま次の仮説へ）である。

外部の観察として、尾原和啓 note（2026-09-09、深津貴之の X 投稿集約）の「アンチハーネス」節 —
禁止リストだけで書くと現場が止まる。とる / とらないリスクを先に仕訳し、許容事故を定義する。
同記事の「共有してよいのは目的・禁止・完了条件だけ」は、rules が全役割に放送される
このハーネスの性質と一致する（境界は全役割が読む層に置く）。

著者の決定（2026-09-15）:
1. 層別のコンテキスト管理（PURPOSE / TASK / TOOLS の役割別配布）は個人実装では過剰。
   スコープを「とってよいリスクと制約の整理」に絞り、散っている境界を 1 本の rule にする。
2. **main への取り込みと push は Claude の判断でよい。**
   [ADR-0043](0043-task-triage-loop-judge-build-human.md) の「人間 = 最後のスイッチ（merge word）」を変える。
   これは待ち時間の観測から出た決定ではない — `.notes/claims.jsonl` の claim → `release --outcome done`
   の間隔（build 時間 + merge 待ちの上限）は harness 37 件で中央値 1.0 h（最大 7.1 h）、
   contemplative-agent 61 件で中央値 0.8 h（最大 52.9 h、2026-09-15 集計）。動機は許容事故の
   仕訳（禁止側でなく取る側に置く）で、撤回条件を Review-when に持つ。

記事から採ったのは「人間に渡す / とる / 止まる」の動詞で書く形式と、禁止側だけでなく許容側を明文にすることだけ。

著者の原則（2026-09-14、[ADR-0065](0065-drop-adr-consultation-wiring-and-build-or-not-gate.md)）
「することだけを書く」との両立: 「するな」の列挙でなく **人間に渡す / とる / 止まって報告する** の
3 動詞で書く。

## Decision

1. **`rules/common/boundary.md` を新設し、境界の正本にする。** 3 動詞の節: 人間に渡す操作（この
   ハーネスで不可逆・対外に当たるものの列挙）/ とる（確認を待たないリスク）/ 止まって報告する条件、
   加えて機械が止めるもの（`hooks/validate-bash.sh`、commit gate、episode log block）を名前だけ 1 行。
   substrate の一般則は再宣言しない。台帳の起票・drop は有人・無人を問わず判断役は提案まで
   （task-triage の「files nothing / drops nothing alone」と同じ条件）。
2. **散っている側は pointer にする。** packet-template の header と Must-not、task-triage の role 表
   （役割固有の Never does だけ残す）と Damping 節、tick prompt、growth-astra / growth-fable、
   agents.md（Herdr 委譲ゲートを boundary へ移し、skill の入口だけ残す）。x-draft / public-comment /
   herdr-delegate / codex-review は skill 固有の手順（境界の適用例）なのでそのまま。
3. **最後のスイッチを人間から判断役へ移す。** 判断役が §4 の検収（diff の範囲、verify の再実行、
   commit body、chain 準拠）を通した task branch を ff-only で取り込み、remote があれば push する。
   digest は事後報告（merged / left とその理由）。人間は方向決めと digest への回答。build は
   task branch まで（実装者と検収者の分離は残す）。
   [ADR-0019](0019-human-gate-layer.md) Decision 2「LLM 単独の承認経路を作らない」との関係:
   admitted task の build 出力に限り、承認 = 決定論ゲートの PASS（`verify.sh` を main で再実行）+
   判断役の検収で閉じる。人間の intent はその前（task の admission と受入条件。起票・drop は
   人間）とその後（Review-when の revert 数）に置く。behavior-shaping artifact（rules / hooks /
   permissions / gate script / ADR / skills）の無人変更は Decision 4 のとおり人間のままで、
   ADR-0019 の条項はそこに残る。ADR-0019 に日付つき注記を付ける。

   > **注記（2026-09-24, ADR-0075）**: cloud session で build した branch では「`verify.sh` を main で
   > 再実行」を、repo の CI が branch tip（headSha 一致）と merge 後の main で走らせた `verify.sh` の
   > 結論に置き換える。判断役はローカルで再実行しない。前提は diff が `.claude/verify.sh` /
   > `.github/` / `.claude/settings.json` に触れていないこと（触れた diff は検収に入らない）。
   > 決定論ゲート PASS + 判断役の検収で閉じる形、Decision 4、`verify_allow.py approve` は不変。

4. **人間に残る取り込み**: 無人時に rules / hooks / permissions / scheduled task / `.claude/verify.sh`
   を含む diff。`verify_allow.py approve` は人間のまま。
5. build の Report に `Risk: <とったリスク / 戻し方>` 1 行を足す（packet-template）。

## Review-when

- `boundary.md` の「人間に渡す」列挙を足す / 減らす時。
- 判断役の取り込みで main が壊れ、人間が revert した回数が 3 か月で 2 回を超えた時 —
  取り込みを人間へ戻す（Decision 3 の撤回条件）。計器: 各 repo の
  `git log main --since=<3 か月前> --grep='^Revert'` と、digest に人間が書いた revert 指示の数。
  判定者は判断役（次の triage cycle の digest に件数を 1 行）。
- substrate が台帳・gate script・scheduled task を outward-facing として自ら扱うようになった時
  （rule の列挙が substrate と二重になる）。
- build の Report の `Risk` 行が 3 か月続けて none なら、とる側の明文を削る。計器: Report は
  最終 commit の message 本文なので `git log --grep='^Risk:' --since=<3 か月前>` で数える。

## Alternatives Considered

- **packet-template だけに書く** — build が読む場所に置くのは自然だが、境界は build 以外の役割
  （判断役、tick、growth）にも同じ内容が要る。著者却下: 常駐 md を各役割が参照する形が正しい。
- **層別コンテキスト管理**（放送層を PURPOSE 大にし、役割文脈を packet / agent prompt / skill へ
  移す）— 記事の主張に最も忠実。実測（2026-09-15、全 project の `~/.claude/projects/**/*.jsonl`
  から assistant message の usage を集計）: 直近 14 日 332 セッション / 24,352 turn / 入力 5.49 B
  tokens（cache read 97.5%）/ 1 turn 平均 225 K。general-purpose subagent（haiku、tool 0 回）を
  1 本起動した usage 合計は 41,676 tokens で、rules 13 本・MEMORY.md・skill 一覧・MCP tool 名を
  そのまま継承していた。著者却下（2026-09-15）: 個人実装では過剰。
- **`human-gate.md` の復活** — ADR-0035 が退役させた停止手順の再導入になる。本 rule は手順でなく
  事実の列挙で、substrate の一般則と競合しない。却下。
- **build 自身が取り込む** — 判断役の検収を経ずに main へ入る。実装者と検収者の分離が消える
  （ADR-0019 が generator–verifier gap と呼ぶ、提案者と検査者が同一になる形）。却下。
- **取り込みを人間に残す（現状維持）** — 検収済み branch が次の tick まで待つ。著者の決定で却下。
  撤回条件は Review-when に置いた。

## Consequences

- 境界の正本が 1 つになり、次に書かれる skill / packet / prompt は列挙を複製せず `boundary.md` を
  指せる。
- 検収済み branch は同じ cycle で main に入る。digest の決定件数は減り、事後報告が増える。
- 判断役の検収ミスが main に直接届く。撤回条件（3 か月 2 回の revert）を Review-when に置き、
  `verify.sh` を main で再実行する手順（task-triage §5）は変えない。
- `rules/common` の常駐が約 2.4 KB 純増する（`boundary.md` 2,439 B。agents.md は 1,000 → 999 B）。
- ADR-0019 / 0035 / 0043 / 0045 に日付つき注記（[ADR-0044](0044-adr-review-when-and-dated-annotation.md) の規約）。
- 公開 harness copy は次の `harness-sync` まで drift する。

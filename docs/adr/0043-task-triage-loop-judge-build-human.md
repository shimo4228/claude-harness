# ADR-0043: タスク台帳を回す loop — 判断は強い階層のセッション、実装は新セッション、最後のスイッチは人間

## Status

accepted

## Date

2026-08-17

## Context

- 台帳は起票が最安の操作なので増える。CA では open 28 のうち review 由来の起票が 22/30、fix commit
  あたり 1.3 件の指摘が台帳へ流れていた（rules/common/task-tracking.md、CA ADR-0095）。harness の
  台帳は 13 行全部が `pending` のままで、語彙が 4 状態に縮約された後（commit 734a502）に中身が
  再 triage されていなかった。**両 repo とも `claims.py ready` は空** — dispatch できる仕事が無く、
  ボトルネックは実装でなく判断だった。
- 2026-08-16 に CA で 7 件を 6 セッションで手動 dispatch した記録（CA `T-DISPATCH-LOOP`）が一次証拠:
  自動化して得があるのは ready の読取・worktree・kickoff 指示書・起動で、判断（衝突検出・前提照合）
  と人間ゲートは残る。Phase 0 で **7 件中 2 件の前提が反証**された。
- オーナーの提案（2026-08-17）: 重要なタスクは内容を確認しながら方向を決め、そうでないタスクは
  セッションを立ててどんどん実装する。**判断は Fable、実装は Opus の新セッション**、Fable は
  「そもそもやる価値があるか」まで判断し、より良い解があれば提案し、必要なら相談する。定期実行
  できればなお良い。
- 制約: 台帳を扱うコードは `claims.py` だけ（CA ADR-0095 — 描画・状態機械・aging を持った版は 2 日で
  5,000 行になった）。深度優先（注意層の並列化は害、実行層の並列化は可）。ADR-0041 の起票規約の
  効果測定中は規約を変えない。自発トリガーの上限 ≒ 40%。

## Decision

1. **三役に分ける。** 判断役 = triage セッション（強い階層、repo ごとに 1 本、cwd = その repo）:
   前提の `file:line` 照合・着手条件の 照合先 確認・やる価値（`architect` の 3 軸）・より良い解の有無を
   判定し、`ready` を kickoff packet にして dispatch、完了物を**独立に**検収する。実装役 = タスクごとの
   新セッション（速い階層、git worktree、branch `task/<name>`）: Phase 0 で前提を再照合し、反証なら
   止めて報告、実装は commit の message 本文に証拠（premise / fix / verify / review / diff 外指摘）
   を残す。人間 = 方向決め・digest への回答・**最後のスイッチ（main への ff-only 取り込み）**。
2. **PR は使わない。** 未マージ = `git branch --no-merged main`。判断役が digest に列挙し、人間の
   「merge」で判断役が ff-only を打つ。証拠は commit body（pane が閉じても消えない）。phone からは
   Remote Control 越しに triage セッションへ。
3. **loop の境界（loop-design-check の red line）**: loop 自身は起票しない・drop を独断で確定しない・
   rules / ADR / hooks / security gate / 公開物に無人で触らない・同時 build ≤ 3、open branch ≤ 3 /
   repo・起票規約を計測中に変えない。goal は突合型（closed ≥ spawned、open が 4 週で増えない）で
   「台帳を空にする」ではない（drop 乱発で達成できてしまう）。
4. **語彙は増やさない、機構は足さない。** 状態は task-stocktake の 4+4 のまま（"defer" は無い）。
   loop は skill（手順）+ 既存 `claims.py` + git だけで回し、台帳を parse する script を足さない
   （消費側から台帳側へ機能が逆流したのが 5,000 行版の育ち方）。

   > **注記（2026-08-25, ADR-0049）**: store 形台帳は公開 `rfcs/` へ一元化され、台帳は公開物に
   > なりうる。上 3 の red line「公開物に無人で触らない」は「無人 triage は working tree の
   > 台帳ファイルへは書けるが、公開へ出る commit / push / merge は人間の側」という形で維持する。
   > 本項の「parse する script を足さない」は不変 — ADR-0049 の改修は既存 `claims.py` の
   > 走査対象追加であって新 parser ではない。
5. **digest は 1 判断 1 メッセージ。** 語彙を当てるだけの記帳は一括 OK でよいが、規約変更・リスク
   受容・課金・drop は 1 件ずつ、背景 → 何が問題か → 選択肢 → 推奨の順で。他セッションの入力欄の
   文字（Claude Code の提案 prompt）は人間の言葉ではない。
6. **harvest。** 実装セッションの commit body と最終報告から拾い、人間に判断を求めるのは
   task-tracking.md のとおり **HIGH の review 指摘（producer 付き起票の提案）** と、**測定・probe
   タスクの成果物としての起票要望**（review 指摘ではなくタスクの出力 — 実装役に起票の権限は無い）
   の 2 種だけ。MEDIUM 以下の review 指摘は規約どおり commit body に残して捨て、digest には件数のみ。
   無視で消える経路を作らないが、注意を余計に使わせもしない。
7. **cadence** は on-demand → 判定が安定したら週 1（repo 既存の週次ゲートに揃える）。repo ごとの
   常駐 triage セッションで `CronCreate` / `/loop`、headless 化するときは digest を file + 通知 1 行に。

   > **注記（2026-08-19, ADR-0045）**: 駆動は session 内 `CronCreate` / `/loop` から **launchd tick
   > （`scripts/triage-tick.sh` → `herdr agent prompt`）** に置き換え、digest は file でなく Slack 片方向
   > （1 判断 1 通 + cycle 末尾 1 行）にした。session 内 cron は 7 日で失効し session 死亡時に沈黙する
   > ため。三役・red line・「答えは triage セッションの中」は不変。
8. **packet は仮説であり、規約の代替ではない。** packet は種別を名指しして review chain を
   `implementation-chain` に委ね、reviewer を手で列挙しない（列挙漏れが省略許可に読まれ、Simplify が
   飛んだ）。packet に無いことは harness の規約が既定。実装役の逸脱は「何を・なぜ」の名指し付き
   だけ許容し、無言の逸脱は結果が正しくても bounce する（次の build が前の build の抜け道を学ぶため）。
9. 正本は skill `task-triage`（手順・packet 雛形・初回記録）。CA `T-DISPATCH-LOOP` / `T-DOC-DRIFT-LOOP`
   は本 ADR を指して `decided`。

## Alternatives Considered

- **PR ベース（レビューを PR に紐づけ、merge ボタンを最後のスイッチに）** — 検収待ちの箱・証拠の
  永続化・phone からの merge が一度に手に入る。却下: 「PR は PR でややこしい」（オーナー）。同じ
  3 点は branch 一覧 + commit body + Remote Control で代替でき、CA の memory `push_workflow` を
  覆す必要も消えた。CI（別問題）は決めていない。
- **全件人間承認（08-16 の plan mode + ExitPlanMode 停止）** — 自動化されるのは起動までで
  「立てて実行する」にならない。判断役が「そうでもないタスク」の承認席に座ることで解いた。
- **無人ループ（承認なしで dispatch → merge）** — Phase 0 の反証率 2/7 と、gate script の変更を
  無人で取り込む危険（今日 harness の commit ゲートが 07-31 から休眠していたことが判明）から却下。
- **Workflow tool / cloud routine で機構を書く** — Workflow は plan/build/judge を code に強制できるが
  今回の判断層は会話（1 判断 1 メッセージ）が本体で、code に落とすのは Stage 3 以降。cloud routine
  は CA の `.notes/` が gitignored で読めない。
- **agentic-engineering 型の汎用原則 skill（ECC）** — 「eval-first / 分解 / model routing」の一般論では
  行動が変わらない。model routing に理由があるのは判断ミスの費用が非対称な点だけで、それは本 ADR
  の三役に吸収した。

## Consequences

- 1 周目（2026-08-17、手動）: open 41 → 23、closed 16 / spawned 5（全部オーナーの言葉）、build
  セッション 10 本（最大同時 3）、merge 7 回、うち 2 回は harness の security gate（S5 / S7）。
  読み（測定）の dispatch が実装より先に効いた（41 件のうち即 dispatch できる実装は 1〜2 件、
  大半は「照合先を読む」で決着）。
- **判断役の packet は仮説である**: S5 は packet の前提を 2 箇所で反証しつつ正しい修理に到達した。
  Phase 0 を「反証したら止める」でなく「反証を記録して直す」にしていたのが効いた。
- 台帳の外で見つかったこと: harness の承認台帳が stale で commit ゲートが休眠していた（人間が
  approve、gate script の merge ごとに再承認が要る）; skill-comply の sandbox run が遵守率の計器を
  汚染する経路（harvest 待ち）; `claude plugin eval` は org gate で実行不能（「native」は検証してから
  言う）。
- 解決しないこと: side-findings の fix-now / file / discard の一般規則、spawned-but-unstarted の
  admission。どちらも本 ADR は既存規約（HIGH 以上 + producer で起票、それ未満は commit body）と
  「人間が digest で刈る」に置き、計測して待つ。
- 失効条件: substrate が「台帳を読んで judge → build → human gate」を native に持ったとき
  （Workflow の常駐化、agents 系サブコマンドの成熟）は本 ADR の機構部分を downward dissolution
  で縮める。三役と red line は残る。

## 注記 2026-08-22 — ad-hoc 入口を implementation-chain 側に生やした

本 ADR の三役（judge = Fable / build = Opus セッション / merge = 人間）は、台帳経由の入口
（skill: `task-triage`）でしか通らなかった。judge-tier のセッションで台帳を介さずそのまま
プランして実装に入る経路が残っており、2026-08-22 に実測で踏んだ — Fable セッションで重めの
実装を続けた結果、Review 群（built-in `/code-review` / `/simplify` はセッションのモデルを継ぐ。
モデル引数は無い）まで judge-tier を消費し、使用限度に到達した。

対応として skill: `implementation-chain` の Plan 段に「実行者の決定」を必須ステップとして
足した。dispatch 条件と三役の**正本は本 ADR と `task-triage` のまま**で、増えたのは ad-hoc 入口
から同じ判断へ入る導線だけ。本 ADR の決定内容は変えない。

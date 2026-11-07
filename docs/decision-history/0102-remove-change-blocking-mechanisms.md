# 0102: 変化を阻む機構を外した — plan mode 既定、research-gate の手順差し込み、fix × 機構ゲート、AKC の Human Approval Gate

## Date

2026-11-07

## Context

関連する経緯: [0101](./0101-decision-history-not-binding.md)（ADR を判断の経緯に変えた）。その plan の Out of scope 節に、
同じ種類の「変化を阻む機構」の候補を 5 つ挙げていた。著者は 2026-11-07 に 5 つを見て、次のように決めた:
「Claude は安全性への意識が強いためにドラスティックな変更を嫌うのだから、その傾向を助長するような仕組みは排除したいし、
むしろ取るべきリスクは取るようにしないと創造的なことはできない」。

5 つの実物（2026-11-07 時点）:

1. plan mode の既定（`rules/common/planning.md:18-19`、経緯 0096 で html plan から戻した）。plan を書く前に承認、書いた後に
   ExitPlanMode で承認、plan 中の tool 呼び出しにも承認が要り、著者の観測では「思わぬところで plan が途中で止まる」。
2. `hooks/research-gate.sh` の手順差し込み（経緯 0086、0096 で縮小）。plan を頼む言い方や plan mode への切り替えで
   「調査 → report → plan」の 5 手順を 1 依頼 1 回 notice した。同じ script の researcher の書き込み先の制限は安全境界で、
   web 由来の指示が設定ファイルを書く経路を塞ぐ。
3. `skills/implementation-chain/SKILL.md:71` の fix × 機構ゲート「修理前に問う — この修正は機構を足すか」。根拠は
   contemplative-agent の実測（レビュー起点の個別 fix の連鎖が自己供給ループで肥大した、CA 0095 / 0098）。
4. agent-knowledge-cycle の Human Approval Gate（AKC 記録 0005。挙動を形成する artifact への変更に名前付き human
   sign-off を構造的に要求する）。`CLAUDE.md:81` の Caveat、README・llms・graph.jsonld・glossary が現在形で述べていた。
5. contemplative-agent の機構層の凍結（CA 記録 0080）。機構層（コード）は止まるのが完成、価値層は進化が続くのが望ましい状態。

著者の判断: 1 は plan mode 自体が現行の Claude Code では使いにくい。2 は Claude の提案（安全境界だけ残す）でよい。
3 は Opus 5.5 には不要。4 は stale で、組織規模の判断を個人に落としたマイクロマネジメントであり、今の Claude Code は
classifier が境界面を担うので冗長。5 は説明を求めた（実験装置の設計で、harness の change-aversion とは別物 — 本記録の
対象外）。

## Decision

harness で次をした:

- `rules/common/planning.md`: plan は `docs/plans/<slug>.md` に直接書き、著者の一言で承認を取る形にした。調査は
  「要るときだけ書く前に」に変え、plan mode と ExitPlanMode の記述を外した。`skills/implementation-chain` の Chain
  Matrix、`skills/grill-me`、`skills/rfc-writer` の plan mode 言及も同じ向きに直した。plan が repo に残る記録である
  こと（`docs(plan)` の単独 commit、経緯 0085）は変えていない。`hooks/plan-executor-notice.sh` は ExitPlanMode に
  配線されたまま残した — 著者が plan mode を使ったときだけ鳴る。
- `hooks/research-gate.sh`: 調査手順の notice（UserPromptSubmit / PostToolUse EnterPlanMode・ExitPlanMode の分岐、
  PLAN_ASK の照合、印のファイル）を削除し、researcher の書き込み先の制限（PreToolUse Write|Edit）だけにした。
  `settings.json` から PostToolUse の `EnterPlanMode|ExitPlanMode` 配線と UserPromptSubmit の配線を外した。
  `tests/research-gate.bats` は notice の 14 件を落とし、境界の 26 件を残した。`hooks/README.md` の 2 行を消した。
  印の置き場 `~/.claude/state/research-gate/`（375 件、git 外）は読む処理が無くなったので消した。
  `skills/search-first` の Full の起動条件から「plan の依頼は全部 Full」を外した。
- `skills/implementation-chain/SKILL.md`: fix × 機構ゲートの行を削除した。`skills/repair-discipline` の参照は
  「別の目で見たいときは agent: architect に聞ける」に変えた。

agent-knowledge-cycle では Human Approval Gate を構造要件から退役した（AKC 記録 0029、Opus の build session が
同日 commit。人間が持つのは「どこを人間に渡すか」の境界の列挙で、それは harness 側の `rules/common/boundary.md` の
資産であり AKC の構造要件ではない）。

## Review-when

- 著者が「過去の判断・手順・承認を理由に止められた」と感じて引用を貼ったら `~/.claude/.notes/decision-pull.md` に
  1 行足す（0101 と同じ記録先）。plan の品質が落ちた（調査なしで書いた plan が実装で反証される）事例が続いたら、
  調査の起動を search-first の description に戻す（hook には戻さない）。
- researcher の書き込み先の制限で止まった正当な書き込みが出たら、`hooks/research-gate.sh` の基準を見直す。
- fix の連鎖で機構が肥大した事例（CA 0095 と同型）が harness で出たら、implementation-chain に 1 行で戻す。

## Alternatives Considered

### plan mode を残し、承認の段だけ減らす

承認の段は substrate の仕様で harness からは減らせない。`docs/plans/` に直接書く経路は今回の 0101 の作業で
使い、問題は出なかった。

### research-gate の notice を `hook-notices-off` で repo ごとに消す

既定が「差し込む」のまま残り、Claude の既定挙動は変わらない。消すなら既定を消す。

### fix × 機構ゲートを「1 行書け」に弱めて残す

著者が Opus 5.5 には不要と判断した。実測根拠は contemplative-agent の記録に残る。

### AKC の gate を「推奨」に弱める

「するな」型の残骸は選択肢として想起される（0065 の原則）。退役して記録に残す。

## Consequences

容易になること:

- plan の依頼が承認で途中で止まらない。調査は要るときだけ。
- fix の着手に儀式が無い。
- AKC の定義が著者の実装と一致する。

困難になること:

- 調査なしの plan が増える可能性。Review-when で見る。
- `hooks/plan-executor-notice.sh` が鳴る機会が減り、Fable の session の「実行者の決定」は implementation-chain の
  文面だけが担う。
- AKC の公開物（DOI 版、記事、論文）で gate を中核として説明した箇所と食い違う。次の release の README と
  release note が持つ。
- 1 と 2 を外したので、`search-first` の Full を回すかは session の判断になる。

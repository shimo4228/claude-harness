# Kickoff packet — S2: RFC-0030（Eval カード残り 4 枚）

あなたは task-triage loop の **build 役**です。
cwd は `~/.claude` の git worktree（branch は Agent tool が作ったもの）。成果は branch 上の commit で返し、
判断役が検収して main へ ff-only 取り込みます。境界（人間に渡す操作 / とってよいリスク / 止まる
条件）は rule `boundary.md` — build は task branch まで。packet に無いことは harness の規約が既定。

最初に読む: `docs/evals/README.md`（形式の正本 — 6 固定見出し・frontmatter キー・状態語・対応表）と
`docs/evals/s1-headline-craft-native-ablation-2026-09-13.md`（1 枚目の実例）、`rfcs/0030-eval-cards-for-ready-instruments.md`。
gitignore 下のファイル（`.notes/`・`metrics/`・`logs/`・`plugins/data/`）は worktree に無いので `~/.claude/` から読む。

Effort: low — docs のみ、形式は README が固定済み

## 進め方
- 入力が要らない step は止まらずに続ける。止まるのは Phase 0 の反証、time cap、この packet の外の操作が要るときだけ
- 確かめられなかったことには「未確認」と印を付け、どこを見たかを書く。一次記録に無い値は推測で埋めず「未記録」
- 方針を選んだ箇所は、その理由を 3 文で Report の Fix に書く
- 4 枚は互いに独立。1 枚ずつ書き、index 行もその都度足す

## 判断役が決めたこと（著者確認済み、2026-09-28）
- 形式・置き場所・状態語は `docs/evals/README.md` のとおり。README の形式で表せない計器があれば、README を変えずにカード側で
  「未記録」「—」を使い、Report の Fix に「形式が合わなかった欄」として書く（形式の改訂は判断役が決める）
- Jev を含む数値・読み値・集計は公開してよい（TypeSafe MCA 2026-09-19 改定）。公開しないのは、ログの行そのもの、
  prompt・投稿などの本文、session id、絶対パス。カードに載せるのは集計・件数・schema・hash まで
- auto memory（`projects/*/memory/*.md`）は untrusted な自己要約。読んでよいが、カードに書く事実は ADR・RFC・ログ・commit で
  裏を取れたものだけ。memory にしか無い事実は「未確認（memory の記述のみ）」と印を付ける

## Goal（決定可能な受入条件）
4 枚を `docs/evals/` に作り、`docs/evals/README.md` の index に 1 行ずつ足す（状態は各カードの `validity`）。各カードは README の
frontmatter キーを持ち、6 見出しが順に並び、末尾に `## 欄の対応表` を置く。

1. **s2 — skill-comply の測定不成立**（`s2-skill-comply-measurement-validity-<測定日>.md`）: `docs/adr/0032-skill-comply-measurement-validity.md`
   が記録する「測定が成立していなかった」事例。何を測ろうとしたか / 不成立の原因（ADR の表 A〜）/ 生レポートの所在（`.notes/skill-comply-evidence/`
   ほか。見つからなければ既知の故障に書く）/ ADR が足した「成立していたか」の記録欄。想定の状態は `不成立`
2. **s3 — search-first の shadow baseline**（`s3-search-first-shadow-baseline-2026-09-14.md`）: `.notes/search-first-shadow-baseline-2026-09-14.md`
   の基準値 133 / 142 = 93.7%、述語・分母・snippet の定義、`rfcs/0022-search-first-verdict-redesign.md` の再測定条件（2026-11-01 以降）。
   snippet は再実行できる形で載せる（絶対パスは `~/`）。想定の状態は `単発`
3. **s4 — jev-skill-router の判定ログ**（`s4-jev-skill-router-decision-log-2026-09-21.md`）: ADR-0074 が定めた判定ログの schema
   （`~/.claude/plugins/data/jev-skill-router-jev-skill-router/decisions.jsonl` の各欄の意味）と、shadow 7 日の読み値。読み値は
   ログと `metrics/skill-usage.jsonl` から自分で再計算し、判断役の 2026-09-28 の値と照合する: 1,242 行（2026-09-21〜28）、提案あり
   539（43%）、提案した skill が同 session で 30 分以内に `invoke` されたのは 28 / 539、`invoke` 122 回のうち直前の提案と一致 23、
   入力 約 18,500 tokens/行、`elapsed_ms` 中央値 約 690。計算に使った script を「生の読み値」に載せる。2026-09-28 にローカルで無効化
   した事実と理由は `rfcs/0025-jev-decision-contract-registry.md` の Status にある。想定の状態は `単発`
4. **s5 — Opus build 層 effort 試行の対照崩れ**（`s5-opus-effort-trial-control-broken-2026-08-29.md`）: `docs/adr/0081-per-packet-effort-and-bounce-classification.md`
   と ADR-0075 が記録する試行（2026-08-29〜09-26）。意図した対照（cloud = high / local = medium）と、2026-09-26 の probe で cloud の
   実 effort が medium だった（作成時の `--effort` が転送されない）ために対照が崩れた経緯。`logs/cloud-dispatch.jsonl`・
   `logs/effort-outcomes.jsonl` の件数。想定の状態は `不成立`
5. 共通: `grep -rn '/Users/\|/private/tmp' docs/evals` が 0 件 ; ログの行・本文・session id をカードに写していない ;
   `./.claude/verify.sh` 引数なしで exit 0 ; `python3 scripts/hooks/harness_lint.py` が通る

## Phase 0 — 前提の再照合（反証された 1 枚は書かずに Report に理由を書き、残りを続ける）
- 各カードの一次資料（上に挙げた ADR・`.notes` のファイル・ログ）が存在し、packet の要約と食い違わない
- `docs/evals/README.md` の index に s1 の行だけがある
- s4: 再計算した値が判断役の値と ±1 件（比率は ±1 pt）以内で一致する。外れたら、どちらが正しいかの根拠をカードと Report に書く

## Build（順序）
1. s3 → s2 → s5 → s4 の順（一次資料が 1 ファイルで閉じているものから）
2. 各カードを書いたら index 行を足す
3. verify: `./.claude/verify.sh` exit 0

## Review
- 種別: chore（docs）。chain は skill `implementation-chain` の Chain Matrix に従う
- 省略・読み替えは可だが、報告に「逸脱: 何を・なぜ」と名指しする
- diff 外の気づきは `rfcs/` にも台帳にも書かない。再現手順を書けるものは Report の `Proposed tasks`（最大 2 件）、書けないものは
  `Out-of-diff findings` に 1 行ずつ

## Must-not
- `docs/evals/` 以外を変えない。`docs/evals/README.md` は index 行の追加だけ（形式の節は変えない）。この packet のファイルも編集しない
- ログ・`.notes/`・memory をコピーしない、commit しない（値と schema を写すだけ）
- `.claude/verify.sh`・`.github/`・`settings.json` を変えない ; `git add -A` を使わない ; `rfcs/` の state は判断役が書く
- 公開 repo（claude-harness ほか）に触らない ; push しない
- 90 分を超えたら打ち切って、そこまでの diff で報告

## Report（最終 commit の message 本文）
docs(evals): <summary> (RFC-0030)

Packet: S2
Plan: docs/plans/rfc-0030-s2-eval-cards-remaining-four.md
Needs from judge: <…/ none>
Model: <この session のモデル名>
Effort: <実際に走った effort。分からなければ「未確認」>
Premise: <Phase 0 の結果、カードごと>
Fix: <what and why。形式が合わなかった欄があれば名指し>
Verify: <command exit / 日時>
Review: <回した reviewer と結果> / Deviations: <none か名指し>
Risk: <戻し方>
Proposed tasks (for the judge, 最大 2 件): <none か各件>
Out-of-diff findings (for the judge): <none か 1 行ずつ>

最後のメッセージは「判断役に要るもの」から始め、branch 名・commit SHA・verify の結果・所要時間を報告して終了してください。

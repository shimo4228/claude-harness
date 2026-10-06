# ADR-0085: plan を repo の `docs/plans/` に置き、ADR / RFC / commit からリンクする記録層にする

## Status

accepted — 2026-08-25 に rfc-writer へ書いて同日削除した規約「plan は作業状態。紐付けはリンクでなく昇格、
RFC・ADR から plans/ へリンクしない」（commit cd93d38 / 4d77add、ADR には未記録）を反転する。
[ADR-0049](./0049-unify-task-ledger-into-public-rfcs.md) の「公開可能な書き方を既定にする curated class」を
`docs/plans/` に広げる（ADR-0049 自体は変えない）

## Date

2026-09-27

## Context

Plan: [docs/plans/composed-enchanting-wand.md](../plans/composed-enchanting-wand.md)（承認 2026-09-27）

- 著者の指摘と Eval を照合可能に公開する仕組みの方向づけ（2026-09-27）で、公開物だけで連鎖を辿る予備測定を
  1 回回した。公開済み 5 件の「出力 → 指摘 → 理由 → 結果」20 環のうち、公開資料で確認できたのは 3 環（すべて結果）。
  出力と指摘の証拠は private repo の commit 本文・gitignore の置き場・会話にあった（1 回・n=5、逸話であって率でない）
- plan は実装前の意図、承認時の著者の編集、検証手順（外れうる予告）を持つが、global の `~/.claude/plans/`
  （gitignore、255 本）にあり公開物から辿れない。ADR-0009 は既に消えた plan を指している
- 著者の判断（2026-09-27）: plan は凍結スナップショットとして残し、後の現実との食い違いはそれ自体を記録とみなす。
  ADR / RFC は日付付き追記で上書きを記録するので、原本の plan を指しても害は無い
- 事実: `plansDirectory` は CLI 2.1.9 で追加（公式 CHANGELOG）。実測（2026-09-27、`claude -p --permission-mode plan`）
  では相対パスは cwd 起点で、サブディレクトリや repo でない場所でもその下に作られる。project 外の絶対パスは効かず
  既定の `~/.claude/plans/` に落ちた。`.gitignore` の `plans/` は位置を固定せず `docs/plans/` まで無視していた。
  公開同期 script は `$HOME` の実値を含む行で abort する（直近 60 本の plan で該当 3 本、秘密パターン 0 本）

## Decision

1. user-level 設定に `plansDirectory: "docs/plans"` を置く。除外は `.claude/settings.local.json` で上書きする:
   contemplative-agent は `.notes/plans`（第三者の投稿本文が混ざりうる）、zenn-content は `planning/plans`
   （企画・下書きは非公開の方針）、Obsidian vault と `~/MyAI_Lab` 直下（repo でない）は `~/.claude/plans`

   > **注記（2026-09-27, RFC-0033）** contemplative-agent と zenn-content の一律除外を改める。この 2 repo は plan 全体の
   > 約半分（124 / 255 本）を占め、一律除外では公開照合の範囲がほとんど増えない。両 repo も `docs/plans/` を既定にし、
   > 第三者の投稿本文・未公開記事の企画を含む plan だけを非公開置き場（`.notes/plans` / `planning/plans`）に置く。
   > zenn-content の未公開記事の plan は記事の公開後に `docs/plans/` へ移す
2. `~/.claude/.gitignore` の `plans/` を `/plans/` に固定する（legacy 置き場だけを無視する）
3. 承認した plan は実装の最初の commit に単独で入れる（件名 `docs(plan): <slug>`）。後続 commit は本文に `Plan: docs/plans/<file>`、
   ADR は Context の先頭、RFC は `## Status` に日付付き 1 行でリンクする（rules/common/planning.md、
   skills adr-writer / rfc-writer に規約を置く）。承認されなかった plan は commit しなくてよい
   > **注記（2026-09-28, RFC-0035）** task-triage の kickoff packet もこの plan として扱う。dispatch の前に
   > `docs/plans/<task-id>-s<n>-<slug>.md` へ単独 commit し、build の commit は `Plan:` 行で指す。非公開の中身を
   > 持つ packet だけは `.notes/packets/` に残す（skill task-triage §3 step 3）
   > **注記（2026-10-06, ADR-0087）** html plan の承認は Respond の貼り戻しで確定し、source の `docs/plans/<slug>.html` を
   > 単独で commit する（[ADR-0087](./0087-html-plan-as-default-plan-path.md) Decision 2）
4. plan は公開可能な書き方を既定にし、機微はリンク先へ、パスは `~/` で書く
5. `docs/plans/` を claude-harness への同期対象に加える。同期は git が追跡している plan だけを集め、docs/plans に
   untracked・未 commit の変更があれば abort する（未承認の plan を出さないため）。script の変更と公開は著者の GO の後で、
   本 ADR の時点では未実施
   > **注記（2026-09-27, RFC-0033）** script 側は実装済み（claude-harness `6810192`）。過去 plan の移設で
   > `~/.claude/docs/plans` に 68 本が入り、次の harness-sync から同期される
   > **注記（2026-10-06, ADR-0087）** 同期は tracked の `docs/plans/*.html` も集め、pack の副産物（`*.packed.html` /
   > `*.artifact.html`）は除く（ADR-0087 Decision 5）
6. commit を促す hook は作らない。既存の 255 本は移さない
   > **注記（2026-09-27, RFC-0033）** 既存の plan は移す。会話ログから repo を決め、公開先に入るものはエージェントの
   > 一次点検と著者の確認を通す。repo でない cwd の plan と、点検を通らない plan は非公開置き場に残す

## Review-when

- 2026-10-11 に、会話ログの `ExitPlanMode` 承認数（cwd が ~/.claude のもの）を分母、`docs/plans/` で commit された plan 数を分子に数え、半分未満なら
  `ExitPlanMode` の PostToolUse で commit を促す advisory を足す
  > **注記（2026-10-06, ADR-0087）** plan の既定が html-plan になり `ExitPlanMode` は減る。分母は、会話ログで
  > `docs/plans/` に新しく Write された plan ファイル（md と html。kickoff packet を除く）の数にする（ADR-0087 Decision 6）
- plan mode が mod 化・廃止される、または `plansDirectory` の挙動が変わる（CHANGELOG）→ 設定と規約を見直す
- 公開した plan で機微情報の事故が 1 件でも出る → 公開の既定を見直す
- 同期の `$HOME` abort が続く → 同期側で `~/` への置換を足す
- 2026-10-25 までに plan へリンクする ADR / RFC が本 ADR 以外に 0 本 → リンク規約を消す

## Alternatives Considered

- **global のまま、リンクしない（2026-08-25 の規約）**: 却下。出力と指摘の環が公開物から辿れないまま残る
- **plan の hash だけを commit に残す**: 却下。約束の証拠にはなるが、開示するまで照合できない
- **repo ごとに committed の `.claude/settings.json` で有効化**: Open — cloud session にも届く利点がある。
  revisit when: cloud の build が plan mode を使うようになったとき
- **承認時に commit を促す hook**: 保留。Review-when 1 の計測後に決める
- **既存 255 本の移行**: 却下。中身の点検なしに公開 repo へ入れない
- **エージェントの原案と著者の編集の差分を残す（`ExitPlanMode` の payload）**: Open — 指摘の公開の詳細設計で決める

## Consequences

- 容易になること: ADR / RFC から実装前の意図と検証手順を辿れる。公開 repo では予備測定の「出力」の環が
  公開資料で確認できるようになる見込み（外れうる予測）
- 難しくなること: plan が公開物になるので、plan の書き方に公開の規律がかかる。サブディレクトリで plan mode を
  起動すると入れ子の `docs/plans/` ができる。user-level 設定は cloud session に届かない
- 主設定（`~/.claude/settings.json`、gitignore）も除外設定（`settings.local.json`）も git に無く、別の機械では再設定が要る
- 除外していない repo では untracked の plan が作業ツリーに残り、`git add -A` で意図せず commit・公開されうる。
  既定を opt-in（repo ごとの committed 設定）に反転する案は Alternatives の Open に残す

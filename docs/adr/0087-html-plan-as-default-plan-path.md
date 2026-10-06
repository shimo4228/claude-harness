# ADR-0087: plan の既定経路を plan mode から skill html-plan へ替える

## Status

accepted — [ADR-0086](./0086-research-gate-before-plan.md) の Decision 5（Mermaid）と、Alternatives の「純正 plan mode を
使わない独自 workflow」の却下を置き換える。ADR-0086 の「依頼の検出なしに plan ファイルの書き込みをすべて gate する」の
却下は、html plan に限って採る。[ADR-0085](./0085-plans-as-records-in-docs-plans.md) と
[ADR-0057](./0057-judge-tier-default-dispatch-and-plan-boundary-advisory.md) に注記する

## Date

2026-10-06

## Context

Plan: [docs/plans/html-plan-default.html](../plans/html-plan-default.html)（承認 2026-10-06）。調査 report:
[docs/plans/research/2026-10-06-html-plan-default.md](../plans/research/2026-10-06-html-plan-default.md)

- plan mode では Write が plan ファイル以外を `Cannot write ... while in plan mode` で拒否する（著者の実測
  2026-10-06）。plan mode の plan ファイルは `.md` なので、plan mode の下では html plan を書けない
- 前 session（cwd が `~/MyAI_Lab`）は、research gate の report 置き場が cwd 起点（`hooks/research-gate.sh` の
  `is_report`）なため report を書けず止まった。これは本 ADR の動機ではなく、「repo の root で session を開く」
  規約（`rules/common/planning.md`）の側の話で、本 ADR は変えない
- plugin skill `html-plan@claude-community`（version 1.0.0、`plugin.json` の license は MIT — marketplace repo の
  root の LICENSE は Apache-2.0 で食い違う。gitCommitSha `f60f0454`）を user scope に入れた。plan を claim の木として 1 枚の HTML に書き、決定を `doc-ask` で
  plan に置き、読み手の **Respond** が決定・編集・コメントを 1 つの markdown（先頭 `# Re: <題>`）にして返す
- 調査 report の要点: research gate の plan ファイル判定（`single_md`）は `.md` だけ、plan を頼む言い方の照合
  （`PLAN_ASK`）は `/html-plan …` に合わない。claude-harness の同期 script は tracked の `docs/plans/*.md` だけを
  集める。`hooks/plan-executor-notice.sh` は `ExitPlanMode` でしか鳴らない。`pack.mjs:221` は claim が `. ? !` で
  終わらないと警告する
- ADR-0086 の plannotator の Open は「Mermaid 入りの plan ファイルでもレビューしにくいと著者が言った」で再訪する
  条件だった
- 著者の判断（2026-10-06）: html-plan を plan の既定にする。そのために plan mode を既定経路から外し、html-plan で書く。plan mode は消さない。散文は日本語で、
  plugin 本体は編集しない。plan mode の Write 制限を mod で回避（`tool.call` で書き込みを代行）する案は保護を
  弱めるので採らない。`/html-plan` を正規表現で拾う案は「起動は skill の description と slash が担う」として退けた

## Decision

1. plan の既定は skill `html-plan` で `<repo>/docs/plans/<slug>.html` に書き、report にリンクする。plan mode は
   著者が自分で入れたときだけ使う。散文は日本語で `<html lang="ja">` にし、SKILL.md の `## Words`（STE 英語）は
   適用しない。plugin 本体は編集しない（規約は `rules/common/planning.md`）
2. pack は `--root <repo> --artifact` で source の隣に `<slug>.packed.html` と `<slug>.artifact.html` を出し、
   どちらも repo の `.gitignore` で外す（source の `.html` だけ追跡する。harness は本 ADR で足した。他の repo は
   html plan を最初に置くときに足す）。artifact は Artifact tool で private 公開し、
   承認は Respond の貼り戻し 1 回とする。承認した source は ADR-0085 Decision 3 のとおり単独で commit する
3. `hooks/research-gate.sh`:
   - plan ファイルに `docs/plans/<name>.html` を加え、`*.packed.html` / `*.artifact.html` を外す
   - html plan は依頼の判定に関係なく、まだ無いファイルへの Write そのものを依頼とみなして mode を問わず gate する。
     `PLAN_ASK` に `/html-plan` は足さない
   - 1 つの ready / skip で通すのは新しい html plan 1 本まで。通った plan の手直しは数えない
   - 依頼の外で既にある html plan に書く（Edit、または Write での書き直し）のは承認後の手直しとして、md と同じく
     `unguarded` に数えるだけにする
   - html の gate の判定は `html_block` / `html_pass` として記録し、md の `block` / `pass`（ADR-0086 の計器）と分ける
   - `# Re: ` で始まるプロンプト（Respond の貼り戻し）は plan の依頼として拾わない
   - PROTOCOL の手順 5 は html-plan を指す。回帰は `tests/research-gate.bats`
4. 実行者の決定は plan の `doc-ask`「実行者の決定」で受ける。`hooks/plan-executor-notice.sh` は plan mode 用に残す
5. claude-harness の `scripts/sync-from-local.sh` は tracked の `docs/plans/*.html` も集め、packed / artifact は除く
6. 計測: ADR-0086 の Review-when の 30 日の窓を 2026-10-06 から数え直す（照合語・path の集合・差し込む文面が
   変わったため）。ADR-0085 の Review-when の分母は、会話ログで `docs/plans/` に新しく Write された plan ファイル
   （md と html。kickoff packet `<task-id>-s<n>-<slug>.md` を除く）の数にする。Respond の貼り戻しは 1 本の plan に
   何度も起きうるので分母にしない
7. skill の文言を新しい経路に合わせる: `implementation-chain` の Plan 行、`search-first` の Full の起動条件、
   `adr-writer` と `rfc-writer` の plan リンク、`grill-me` の EnterPlanMode。`spawn-session` の kickoff は plan mode
   のまま残す（`/grill-me` の対話用）。`hooks/README.md` の表も揃える

## Review-when

- html-plan の散文が英語で出た、または `<html lang>` が `en` のまま出た（rule による STE の上書きが効かない）—
  PROTOCOL の手順 5 に `lang="ja"` と STE の不適用も足す（日本語の指定は手順 5 に既にある）
- 窓（2026-10-06 から 30 日。窓の間は照合・path の集合・差し込む文面を変えない）で、`html_block` のあった session の
  半分超で gate が「調査不要」（`skip`）で開けられた — html の gate が重い。「1 本まで」か「Write を依頼とみなす」を
  見直す。`html_block` のあった session が 5 件に満たなければ次の 30 日に延ばす
- html-plan の更新で、pack の出力名（`*.packed.html` / `*.artifact.html`）か Respond の先頭行（`# Re:`）が
  変わった — gate の除外と照合を見直す
- 著者が html plan は読みにくい、または貼り戻しが面倒だと言った — 既定経路を見直す
- plan mode の Write 制限が緩んだ、または plan mode が mod 化された（CHANGELOG）— plan mode を既定に戻すか比べ直す

## Alternatives Considered

- **plan mode と Mermaid の md plan を続ける**（前 session の停止は「repo の root で開く」規約で防げる）: 却下
  （著者判断 — html-plan を既定にする）。plan mode の下では html plan を書けない
- **plan mode のまま、mod で plan ファイル以外への書き込みを代行する**: 却下（著者判断）。plan mode が持つ
  保護を弱める
- **`PLAN_ASK` に `^/(html-plan:)?html-plan\b` を足して依頼として拾う**: 却下（著者の指摘）。起動は skill の
  description と slash が担う。言い方の照合は起動の形が増えるたびに追従が要り、書き込みを gate すれば要らない
- **packed / artifact を `-o` で session の scratchpad に出す**: 却下（著者が Respond で「source の隣」を選んだ）
- **Respond の貼り戻しを UserPromptSubmit で検出して実行者の決定を促す hook を足す**、**rules の 1 行に縮退する**:
  却下。前者は新しい機構を足し、後者は plan の記録に決定が残らない。`doc-ask` なら Respond に決定が残る
- **html plan を公開 repo に載せない**: 却下。ADR / RFC から plan へのリンクが公開 copy で切れる
- **plannotator でブラウザ上の plan レビューを足す**（ADR-0086 の Open）: 閉じる。Respond が同じ穴を埋める

## Consequences

- 良くなること: plan を書いている間も plan ファイル以外を書ける。決定が選択済みの状態で返り、どれが「開かずに
  既定のまま」かも分かる。調査の gate は起動の言い方に依存しない。ADR-0086 の plannotator の Open が閉じる
- 悪くなること: 既定経路では、plan mode が機械で効かせていた「plan 中は plan ファイル以外を書かない」性質と
  承認 UI の境界を失う。html-plan の「Respond が来るまで作らない」は prompt 上の約束で、gate が止めるのは新しい
  html plan の書き込みだけ。外部 plugin に依存する。`~/.claude/plugins/` は git の外なので、再現は marketplace の
  gitCommitSha（`f60f0454`）で行う。日本語の claim は `pack.mjs:221` で毎回警告される（エラーではない）。STE の
  上書きが効くかは実測していない（Review-when の 1 つ目）。`/html-plan` を直接打つと調査手順の差し込み
  （PROTOCOL）は出ず、block の理由文が案内する。1 つの依頼で html plan を 2 本書くと、2 本目に新しい調査か
  「調査不要」が要る。拡張子の大文字小文字（`x.HTML`）や名前（`x.packed.html`）で gate を外せる（促しの gate で、
  安全境界ではない — ADR-0086）
- 公開面: 同期 script が `research/` 配下も平らに公開し plan から report へのリンクが切れる点（ADR-0086
  Consequences）は、html plan にもそのまま当てはまる。source の html は runtime（`htmlplan.css` / `htmlplan.js`）を
  名前で参照するだけで、runtime は公開しない。公開 copy の html は runtime 無しでは描画されず、source として読む
- 残る制約: research gate の report 置き場は cwd 起点のまま。harness の外の repo の plan は、その repo の root で
  session を開く
- 記録の置き場: pack のコマンドと日本語の規約の正本は `rules/common/planning.md` で、本 ADR は決定だけを持つ
- 戻し方: `rules/common/planning.md` の html-plan の 3 項目、PROTOCOL の手順 5、skill の文言（Decision 7）を戻せば、
  plan は plan mode に戻る。html の gate は `single_plan` から `.html` を外せば止まる。同期 script の glob（Decision 5）
  は claude-harness 側で戻す

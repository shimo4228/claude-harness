# ADR-0096: html-plan を退役して plan mode に戻し、research gate を researcher の制限と手順の差し込みに縮める

## Status

accepted — [ADR-0087](./0087-html-plan-as-default-plan-path.md) を置き換える。[ADR-0086](./0086-research-gate-before-plan.md)
の Decision 3（plan ファイルの gate）・Decision 5（Mermaid）・Review-when を部分的に置き換える。ADR-0085 / ADR-0086 /
[ADR-0057](./0057-judge-tier-default-dispatch-and-plan-boundary-advisory.md) に注記する

## Date

2026-10-26

## Context

- 著者（2026-10-26、`/grill-me` の面接）: 「html-plan なんかそんなにいいこともないから退役させてくれる？」。理由を
  問われて「手間に見合わない」を選んだ — pack → Artifact 公開 → Respond の貼り戻しの往復が重く、md plan と比べて
  得るものが少ない。ADR-0087 の Review-when の 4 つ目（「貼り戻しが面倒だと言った — 既定経路を見直す」）に当たる
- 続けて research gate について「変な制約が多くてできればやめたい。これはほぼ search-first のためか？」。答えは
  そう — ADR-0086 の事件（2026-10-02、調査 agent が返る前に plan を書いた）から、search-first の Full の結果を
  plan より先に置くことを書き込みの block で強制する装置
- gate の計測ログ（ADR-0086 Decision 3 の計器。gitignore 下で、件数はここに写す。2026-10-05〜10-26 の 192 行、event ごとの件数。2026-10-26 集計）: ask 38、notice 38、
  ready 36、skip 9、block 1、html_block 3、html_pass 39、pass 6、unguarded 22。3 週間で書き込みを止めたのは 4 回
  （block + html_block）。notice と ready の件数は近いが、session ごとの順序は数えていない。block や notice が無ければ
  調査が抜けたかは測っていない（外した対照は無い）
- 同じ期間の plan: `docs/plans/` に追跡中の html plan 8 本と未追跡 1 本（marble-world-publish、2026-10-25 の
  report 付きで進行中）。md は task-triage の kickoff packet 2 本だけで、plan mode の plan は 0 本
  （`git log --since=2026-10-06 -- 'docs/plans/*.md'`、research/ を除く）
- researcher は Write と `permissionMode: acceptEdits` を持ち、その書き込み先を notes と report に限っているのは
  research gate の PreToolUse の枝だけ（ADR-0086 Decision 3 の「安全境界」）
- plan mode の受け皿は残っている: `settings.json` の `plansDirectory: "docs/plans"`（ADR-0085）、
  `hooks/plan-executor-notice.sh`（ExitPlanMode で「実行者の決定」を想起させる）。ADR-0087 は plan mode を既定から
  外しただけで消していない
- 著者の判断（同日の面接、各問いの推奨を採った）: 代わりは plan mode。plugin は無効化だけ（アンインストールしない）。
  gate は researcher の書き込み制限と手順の差し込みだけ残す。進行中の marble-world-publish は html のまま承認まで
  通し、plugin の無効化はその後。Mermaid の必須は戻さない（Claude が「軽さ優先の判断に合わせる」として既定に
  示し、著者は異を唱えなかった）

## Decision

1. plan の既定経路を plan mode に戻す。plan は `docs/plans/<slug>.md`（`plansDirectory`）に書き、調査 report に
   リンクし、ExitPlanMode で承認する。実行者の決定は `hooks/plan-executor-notice.sh` が想起させる。Mermaid は
   必須にしない（`rules/common/planning.md`）
2. plugin `html-plan@claude-community` は `settings.json` で `false` にする。marble-world-publish の承認 commit を
   入れた session で行い、本 ADR に日付つきの注記を足す（`settings.json` は gitignore 下で、git には残らない）。
   アンインストールはしない — cache の `pack.mjs` で既存の html plan を描画できるように残す

   > **注記（2026-10-26, commit「docs(adr): ADR-0096 に html-plan plugin の無効化を注記する」）**: 著者が
   > marble-world-publish を承認し、同日 `settings.json` の `html-plan@claude-community` を `false` にした。
   > 既存の html plan を描画する `pack.mjs` は cache の
   > `~/.claude/plugins/cache/claude-community/html-plan/1.0.0/skills/html-plan/runtime/pack.mjs` に残る
3. 既存の html plan（`docs/plans/*.html`）は記録としてその場に残し、書き換えない。claude-harness の同期 script の
   `*.html` の glob（ADR-0087 Decision 5）も残す — ADR / RFC から plan へのリンクを切らない
4. `hooks/research-gate.sh` を縮める:
   - 残す: researcher の書き込み先の制限（notes の approve、report の path の照合、worktree の基準、制御文字・symlink・
     名前の形の検査 — ADR-0086 Decision 3 のとおり）と、plan の依頼（plan を頼む言い方、著者の plan mode への切り替え、
     Claude の EnterPlanMode）で調査手順を 1 依頼 1 回差し込む notice
   - 消す: plan ファイルへの書き込みの block、印 ready / skip / planning / passed / htmlplan、「調査不要」の照合、
     html plan の分岐、`# Re:` の除外、計測ログ
   - 配線: PostToolUse の matcher から `Write` を外す（ready の印付けが無くなるため）。ExitPlanMode は依頼を閉じて
     次の EnterPlanMode で差し込み直すために残す
   - 差し込む手順の 5 は「plan は plan mode で `<repo>/docs/plans/<slug>.md` に書き、report にリンクする」にする
   - 回帰は `tests/research-gate.bats` を残す側だけに絞る
5. skill の文言を戻す: `implementation-chain` の Plan 行、`search-first` の Full の起動条件と gate の記述、
   `adr-writer` と `rfc-writer` の plan リンク、`grill-me` の受け渡し先、`agents/researcher.md` の gate の記述、
   `hooks/README.md` の表

## Review-when

- report へのリンクの無い md plan が ExitPlanMode で承認された（`docs/plans/*.md` の新しい plan を承認時に見る）—
  ADR-0086 の事件が notice だけでは防げていない。plan ファイルの block を戻すか検討する
- 著者が plan mode の plan も読みにくい、またはレビューしにくいと言った — plan の形（Mermaid、別の viewer）を見直す
- Claude Code が plan mode の書き込み許可や調査段を設定できるようにした、または plan mode を廃止・mod 化した
  （ADR-0085 / ADR-0086 と同じ監視対象）— 差し込みを native の機構に移す
- researcher を退役した、または researcher から Write を外した — gate の残りの安全境界も外す

## Alternatives Considered

- **plan mode を使わず `docs/plans/<slug>.md` を普通に Write してチャットで承認する**: 却下（著者判断）。最も軽いが、
  plan 中の書き込みの保護と承認 UI を持たない。Open — 再訪条件: plan mode が廃止・mod 化された
- **html-plan と gate を現状のまま続ける**: 却下（著者判断 — 往復の手間に見合わない）
- **既定経路を持たず、その都度 plan の形を選ぶ**: 却下（著者判断）。plan の置き場と承認の形が毎回揺れ、ADR-0085 の記録の数え方も揃わない
- **plugin をアンインストールする**: 却下（著者判断）。既存の html plan 9 本が source でしか読めなくなる。戻すには
  gitCommitSha `f60f0454` で入れ直す
- **gate の html 分岐だけ消し、md の block は残す**: 却下（著者判断）。block は 3 週間で 4 回しか発火せず、「調査不要」の
  合言葉や依頼の言い方の照合といった制約の重さに見合わない
- **gate を researcher の制限だけにして notice も消す**: 却下（著者判断）。notice の効果は測っていない。差し込みを外すと「先に調査」は rule の 1 行だけになり、事件の前の状態に戻る
- **researcher ごと退役して search-first の Full を general-purpose agent に戻す**: 却下（著者判断）。変更が ADR-0066 /
  ADR-0086 の調査の形まで及ぶ

## Consequences

- 良くなること: plan の往復が plan mode の承認 1 回に戻る。pack と Artifact の公開が要らない。research gate は
  「調査不要」の合言葉・言い方の照合による block・1 本までの規則を失い、hook と bats が小さくなる。外部 plugin への
  既定経路の依存が無くなる
- 悪くなること: 調査より先に plan を書くことを機械で止めなくなる。差し込まれた手順に従うかは model 次第で、
  ADR-0086 の事件と同じ形がまた起きうる（Review-when の 1 つ目で見る）。plan 中は plan ファイル以外を書けない
  制限が戻る（ADR-0087 が plan mode を外した理由の 1 つ）。廃止・mod 化が予告された plan mode（ADR-0057 の注記）への
  依存に戻る（Review-when の 3 つ目で見る）。決定が選択済みで返る Respond の性質と、
  claim の木と exhibit で plan を見せる形を失う。gate の計測ログが止まるので、ADR-0086 の Review-when の数える基準は
  判定できなくなる
- 残るもの: researcher の書き込み先の制限は今までどおり安全境界として働く。既存の html plan は source として追跡され、
  描画には無効化した plugin の cache を使う
- 戻し方: plugin を `true` に戻し、`rules/common/planning.md` と Decision 5 の skill の文言を ADR-0087 の版へ戻す。
  plan ファイルの block は ADR-0086 / ADR-0087 の時点の `hooks/research-gate.sh` と bats を git から戻し、
  `settings.json` の PostToolUse の matcher に `Write` を足し戻す（計測ログも hook と一緒に戻る）

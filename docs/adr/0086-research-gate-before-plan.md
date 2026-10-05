# ADR-0086: plan の依頼では調査 report ができるまで plan ファイルを書かせない（research gate）

## Status

accepted — 2026-10-04 に Decision 6 の実機確認（注記）を経て settings.json に配線した。Review-when の 30 日の窓は
この日から数える。[ADR-0066](./0066-search-first-report-contract-and-scout-retirement.md) Decision 4（Full の委譲先は
general-purpose subagent、tool の制限は prompt 上）を部分的に置き換える

## Date

2026-10-04

## Context

Plan: [docs/plans/research-plan-mode.md](../plans/research-plan-mode.md)（承認 2026-10-04）。調査 report:
[docs/plans/research/2026-10-04-research-plan-mode.md](../plans/research/2026-10-04-research-plan-mode.md)

- 事件（Claude Code transcript、claude-prose-mod の session `4be4a512`、時刻は UTC）:
  2026-10-02 23:31 に「RFC1をプランして欲しい。」が **auto mode** で届き、Claude は 3 分間 local の型定義を読んだ。
  23:34 に著者が外部調査を求め、Claude は search-first を起動して general-purpose agent 2 本を background で出した。
  23:38 に Claude 自身が EnterPlanMode し、**23:40 と 23:42 に plan mode のまま plan ファイルを Write した — 調査
  agent が返る前**。2026-10-03 00:41 の「その方向でプランし直して」は auto mode のまま、1 分後に新しい plan ファイルを
  書いた
- `rules/common/planning.md` の search-first 行は、この時点で常駐していた（2026-09-26 から）。search-first の
  invoke は ADR-0066 の改修後に回復している（skill 使用の計測ログ、`hooks/log-skill-usage.sh` が書く。2026-10-04
  集計: 09-01〜14 が 0 件、09-21〜10-02 が 19 件 — うち 7 件が 09-22 の 1 日。invoke は ADR-0066 Decision 6 が
  副次的な計器に下げた数）。漏れは「search-first が呼ばれない」でなく「呼ばれても結果を待たずに plan を書く」
- 著者の判断（2026-10-04）: ExitPlanMode で止めても plan ができた後で遅い。plan ができる前に十分に調査させたい。
  search-first 自体の調査も浅い。外部調査が要らないバグ修正は内部調査（再現・原因）で通す。auto mode のまま受けた
  plan の依頼にも広げる（スレッドで言い方による検出と、その誤爆・取りこぼしを示したうえで「広げて欲しい」）
- 外部調査（上の report。4 角度を並列、as-of 2026-10-04）:
  - plan mode は auto mode 下でコマンドを classifier に回し、plan ファイル以外への書き込みだけを止める
    （`useAutoModeDuringPlan` 既定 on）。`.claude` は protected directory で、acceptEdits でも protected path への
    書き込みと cwd の外への書き込みは確認が出る（https://code.claude.com/docs/en/permission-modes 、全文）
  - 親が `default` / `dontAsk` / `plan` のとき、subagent は frontmatter の `permissionMode` で動く。親が auto の
    ときは定義の値は無視される（https://code.claude.com/docs/en/sub-agents 、snippet）
  - ExitPlanMode への PreToolUse の deny は無視される（https://github.com/anthropics/claude-code/issues/50660 、
    2026-05-26 に not_planned で close）。plannotator（https://github.com/backnotprop/plannotator）の plan レビューも
    PermissionRequest hook で plan の後に走る
  - 先行実装（HumanLayer https://github.com/humanlayer/humanlayer 、obra/superpowers
    https://github.com/obra/superpowers 、anthropics/claude-code の feature-dev、github/spec-kit
    https://github.com/github/spec-kit）は純正 plan mode を使わず、research-before-plan を prompt と「前段成果物の
    存在」で担保する。report の検索範囲で、hook で止める実装は見つからなかった。spec-kit は research.md の完了を
    設計の前提にする。OpenCode・Gemini CLI・Roo Code の plan mode は、モード別に plans 配下だけ書き込みを許す
  - Anthropic の multi-agent research system（https://www.anthropic.com/engineering/multi-agent-research-system 、
    2025-06-13）: 比較型の問いは subagent 2〜4 × 各 10〜15 calls、複雑な問いは 10 以上。Opus lead + Sonnet
    subagent が単一 Opus を同社の社内 eval で 90.2% 上回り、BrowseComp の分散の 80% を token 使用量が説明した
    （どちらも記事の数値で、評価集合の大きさは記事に無い）。同じ記事は、multi-agent が chat の約 15 倍の token を使う
    こと、コーディングの多くは調査ほど並列化できないことも書く。数字は Claude 4 世代のもの。並列化の理由として記事が
    挙げるのは、別々の context window で容量を足すこと。STORM（arXiv 2402.14207、abstract）は視点ごとに質問させて
    網羅を 10 ポイント上げた。本 ADR 以前の search-first Full（ADR-0066 Decision 4）は general-purpose 1 本 × 約 15 calls
  - Cursor 2.2・Kiro の design.md・Roo の Architect は plan に Mermaid を入れる。公式の ultraplan は削除された
  - plan mode の指示文を Mod の `prompt.attachment` で書き換える経路は、type 名 `plan_mode` が手元の型定義（CLI 2.1.286 が
    plugin-authoring skill の展開先に書いた `claude-code.d.ts`）にだけあり、公開 doc（/docs/en/plugins/mods/）には無い

## Decision

1. `agents/researcher.md` を置く。tools は Read / Grep / Glob / WebSearch / WebFetch / Write、
   `permissionMode: acceptEdits`、`model: sonnet`。1 つの調査角度の notes
   （`~/.cache/claude-research-notes/<YYYY-MM-DD-slug>/<angle>.md` — Claude Code が読み込まず、harness の git にも
   入らない置き場）か、統合した report（`<project>/docs/plans/research/<YYYY-MM-DD-slug>.md`）を 1 本書く。report の
   1 行目は `kind: external` か `kind: internal`。report の形の正本は researcher.md で、各節の書き方は skill
   search-first §3 を参照する（Verdict は lead が plan に書く）
2. skill search-first の Full を並列多視点に置き換える: brief → 3〜5 角度（表の行ごとに 1 本 + 反証役 1 本）を
   researcher で並列 → lead が notes を全部読み、漏れ・食い違い・snippet だけの主張を洗う → 追加は 1 波まで（決定に
   効く主張の原典照合を含む）→ report。plan mode からの問いは常に Full
3. `hooks/research-gate.sh` を置き、UserPromptSubmit / PreToolUse（Write|Edit）/ PostToolUse
   （Write|EnterPlanMode|ExitPlanMode）に配線する:
   - plan の依頼を 2 通りで拾う: plan mode（`permission_mode == plan`、EnterPlanMode の直後を含む）と、plan を頼む
     言い方のプロンプト（「プランして」「プランし直して」「計画して」「設計して」「make a plan」「replan」等。mode を問わない）。
     後者はその session を planning にし、依頼ごとに ready / skip を戻して plan ごとに調査を求める。新しい依頼として
     数えるのは、plan mode の外の plan を頼む言い方と、著者による plan mode への切り替え。plan mode 中の「プランを
     直して」と、Claude 自身の EnterPlanMode の後は同じ依頼の続き。依頼が閉じるのは、ExitPlanMode（承認）と、調査か
     skip を済ませた後の plan を頼まないプロンプト。調査手順は 1 依頼 1 回差し込む。進行形（設計している）と
     語の一部（preplanned）は拾わない
   - researcher の書き込みは notes と report の path だけに限る（plan mode に関係なく常に — 安全境界）。照合は
     realpath 同士で、基準は `$HOME` と `$CLAUDE_PROJECT_DIR` に固定し、名前は日付 + 英小文字・数字・ハイフンの形
     だけを通す（claude.md / agents.md を除く）。制御文字を含む path は止める。approve を返すのは notes だけ —
     cwd の外で、acceptEdits だけでは誰も答えられない確認が出るため。report は cwd の中なので Claude Code の判定に
     任せる。harness repo の report は `.claude` 配下の sensitive file として確認が出て、approve でもこれは飛ばない
     （Decision 6 の実機確認）ので、著者がその場で許可する
   - researcher が 1 行目 `kind:` の report を書いたら、その session に印 ready を付ける。見るのは存在で、中身の質は
     lead と著者が見る。主ループが自分で report を書いても印は付かない
   - plan の依頼中、印が無ければ plan ファイル（`*/docs/plans/<name>.md`、`~/.claude/plans/<name>.md`）への
     Write / Edit を block する。依頼の外で plan ファイルが書かれたら止めずに `unguarded` として記録する（その session で
     gate を通った plan ファイルの手直しは除く）
   - 著者のプロンプトの「調査不要」/ "skip research"（否定形を除く）で印 skip を付け、gate を開ける
   - ask / notice / block / pass / ready / skip / unguarded を計測ログ（既定 `~/.claude/metrics/research-gate.jsonl`、gitignore）に 1 行ずつ
     残す。回帰は `tests/research-gate.bats`（security review で再現した経路 — path の改行と 0x1f、末尾一致の偽装、
     指示ファイル名、symlink — を含む）
4. 調査は 2 種にする。外部調査（新機能・依存の追加・設計の選択）は search-first の Full、内部調査
   （repo 内で答えが出るバグ・refactor）は再現手順・原因の `file:line`・確認結果。種別は Claude が brief の
   1 行目に書き、著者がそこで止められる
5. plan は report にリンクし、構造や流れは Mermaid で示す（`rules/common/planning.md` に 1 項目）
6. settings.json への配線は、次の 5 点を使い捨ての設定（`claude -p --settings`）で確かめてから行う:
   plan mode 中の plan ファイルへの Write を PreToolUse の block で止められる / plan mode の親の下で、harness 以外の
   repo から researcher が notes に、harness repo で report に書け、その PostToolUse の `session_id` が親と同じ /
   subagent の PreToolUse に `agent_type` が載る / approve で cwd の外と protected path への書き込みが確認なしに通る /
   plan mode 中の WebSearch・WebFetch が確認なしで走る。通らなかった項目は、その部品だけを Mod の `tool.check` に
   置き換え、本 ADR に注記する

   > **注記（2026-10-04, 実機確認）**: CLI 2.1.289、`claude -p` と使い捨ての `--settings` で確認。plan mode 中の
   > plan ファイルへの Write は hook の block で止まった（auto mode の plan 依頼でも同じ）。plan mode の親の下で
   > researcher は cwd 外の notes と cwd 内の report に書け、その PreToolUse / PostToolUse には親と同じ `session_id`
   > と `agent_type: researcher`、`permission_mode: acceptEdits` が載った。report で ready が付き、続く plan ファイルの
   > Write を hook は通した（plan mode 自体は指定の plan ファイル名しか書かせない）。researcher の `src/` への Write は
   > hook が止めた。WebSearch・WebFetch は plan mode 中に確認なしで走った（user 設定の allow rule の下）。
   > **通らなかった 1 点**: `.claude` 配下の report は、hook が approve を返しても「sensitive file」の確認が出て、
   > `-p` では拒否された。approve で飛ばせる範囲は notes だけに絞り、harness repo の report は著者がその場で許可する
   > 形にした（Mod には置き換えない — sensitive file の確認を飛ばす必要は無い）

7. 入れる順番: 本 ADR の変更（hook・researcher・search-first・planning.md）は task branch に置き、Decision 6 を通して
   配線するまで main に入れない。`~/.claude` の作業ツリーは live の設定なので、それまで作業ツリーは main に戻しておく
   — 配線の無い researcher（Write + acceptEdits）を常駐させない
8. 範囲: 言い方で拾うので、誤爆（plan を頼んでいないのに gate がかかる）と取りこぼし（言い方が照合語に無い）が
   ある。前者は ask の後に plan ファイルの書き込み（block / pass）が無い依頼、後者は `unguarded` で数える
   （task-triage の kickoff packet も `unguarded` に入る）。ADR-0085 の非公開の plan 置き場（`.notes/plans`、
   `planning/plans`）は gate の外
9. ADR-0066 の Decision 4・Alternatives（scout を残す案）・Consequences の Positive と Negative に日付つき注記を残す

## Review-when

計測は配線の日（Status の注記）から 30 日の窓で行い、窓の間は差し込む文面・plan を頼む言い方と skip の正規表現・
plan ファイルの path の集合を変えない。notice のあった session が 10 件に満たなければ判定を次の 30 日に延ばす。

- Decision 6 のどれかが通らなかった — その部品を Mod に置き換え、本 ADR に注記する
- notice のあった session のうち、skip で開けた session が半分を超える — gate が重すぎる。種別の判定か gate の
  対象を見直す
- notice のあった session のうち、block の後に ready も skip も無い session が半分を超える — 手順が回っていない。
  差し込む文面か researcher の起動を見直す
- notice のある session が 10 件以上あるのに block が 0 件 — gate が黙って効いていない（PreToolUse の block が
  plan ファイルの Write で効かなくなった、plan ファイルの置き場が変わった等）。原因を調べる
- ask の後に plan ファイルの書き込みが無い依頼が、ask の半分を超える — 言い方の照合が広すぎる。照合語を絞る
- `unguarded` のうち、kickoff packet を除いた plan ファイルの書き込みが、ask の付いた依頼の数を超える — 取りこぼしが
  多い。照合語を足すか、plan ファイルの書き込みそのものを依頼とみなす形に変える
- 著者が plan の調査をまた「浅い」と指摘した — researcher の `model` を opus に上げるか、角度の数を増やす
- Claude Code が plan mode の書き込み許可や調査段を設定できるようにした、または plan mode を廃止・mod 化した
  （ADR-0057 の注記、ADR-0085 の Review-when と同じ監視対象）— native の機構か Mod に移す

## Alternatives Considered

- **何もしない**: 却下。事件は 1 本の session で、著者の一言で直った。それでも plan mode 内で「調査の結果を待たずに
  plan を書く」漏れが起き、著者はそれを止めたいと明言した（2026-10-04）
- **advisory だけ（入口で手順を差し込み、block はしない）**: 却下。事件では search-first の起動までは行われ、結果を
  待たずに plan が書かれた。差し込みは起動を促すだけで、待たせる力が無い。部品は hook に残っているので、block が
  重すぎると分かったら（Review-when の 2 つ目）ここへ下げられる
- **Mod で純正 plan mode の指示文と権限を差し替える**（`prompt.attachment` の `plan_mode` と `tool.check`）:
  核からは外した。指示文の type 名が公開 doc に無く版で壊れうる。gate 自体は shell hook で書ける。
  Open — revisit when: Decision 6 が通らない、または本体のループに plan mode 中の scratch 書き込みやフェーズ表示の
  UI が要るようになった
- **ExitPlanMode で止める**: 却下。plan ができた後で遅い（著者判断）。PreToolUse の deny は ExitPlanMode では
  無視される（#50660）。PermissionRequest hook も plan の後に走る
- **CLAUDE.md や rule に「設計の前に調査」を書く**（usage report の提案、spec-kit・superpowers の担保の仕方）:
  却下。同じ趣旨の planning.md の search-first 行が常駐していた中で事件が起きた。本 ADR も planning.md に 1 項目
  足すが、それは gate の存在を知らせる配線で、担保は hook が持つ
- **純正 plan mode を使わず、通常モードで plan ファイルを書く独自 workflow**（HumanLayer・superpowers 型）:
  却下。plan mode の承認 UI と、plan 中に本体が書き込まない性質を失う。auto mode 下の plan mode はコマンドを
  止めないので、plan mode を抜ける理由の大半は researcher で消える
- **Full を general-purpose subagent 1 本のまま、budget だけ増やす**: 却下。token 量の効果（80%）は 1 本でも説明
  できるが、Anthropic が並列化の理由に挙げる別 context での容量追加と、STORM の視点分割は 1 本では得られない。
  反証役も分けられない
- **plan mode だけにかける**（auto mode の plan 依頼は止めない）: 却下（著者判断 2026-10-04）。事件の 00:41 の
  再 plan は auto mode のままで、plan mode だけでは止まらない
- **auto mode では、依頼の検出なしに plan ファイルの書き込みをすべて gate する**: 却下。task-triage の kickoff
  packet など、plan を頼まれていない `docs/plans/` への書き込みまで止める。取りこぼしが多いと分かったら
  （Review-when）ここへ寄せる
- **plannotator でブラウザ上の plan レビューを足す**: 本 ADR では採らない（依存の追加で、dependency intake と
  著者の判断が要る）。Open — revisit when: Mermaid 入りの plan ファイルでもレビューしにくいと著者が言った

## Consequences

- 良くなること: plan mode でも auto mode でも、plan の依頼の plan は調査 report が無ければ書けない。調査メモは plan mode のまま書ける。
  researcher の tool の制限が prompt の文言でなく定義と hook で効く。report が `docs/plans/research/` に残り、
  plan からリンクされて公開照合できる
- 悪くなること: plan の依頼は researcher 3〜5 本 × 各 10〜15 calls の分だけ token を使う（記事の目安では
  multi-agent は chat の約 15 倍）。素早く plan したいだけのときは、著者が「調査不要」と言う手間が増える。plan を頼む言い方は auto mode の会話にも
  出るので、plan を作らない依頼にも調査手順が差し込まれうる（Review-when の誤爆の計器で見る）。
  外部 / 内部の種別は Claude の判断なので、設計の問いを内部扱いにして外部調査を逃げる余地が残る（Review-when の
  2 つ目で見る）。gate が見るのは report の存在だけで、1 行の report でも開く。主ループは Bash で印のファイルを
  作ったり plan ファイルを書いたりして gate を迂回できる（gate は調査を促す仕組みで、安全境界ではない）。
  search-first の Full は agent 定義・hook・skill の 3 つにまたがる（正本は Decision 1 の分担）
- 公開面: report は `docs/plans/` 配下にあるので harness-sync の対象になる。claude-harness の
  `scripts/sync-from-local.sh` は `git ls-files -- 'docs/plans/*.md'` を `docs/plans/` へ平らにコピーするので、
  report は平らに公開され、plan から `research/<slug>.md` へのリンクが公開 copy で切れる。未 commit の report が
  あると同期は abort する。同期 script の対応は公開側の変更で、著者の判断の後に行う。web からの引用は短くし、
  公開可能な書き方を既定にする（ADR-0085）。notes（`~/.cache/claude-research-notes/`）は自動では消さない
- 戻し方: settings.json から 3 つの配線を外せば gate は止まる。settings.json は gitignore 下の live 設定なので、
  配線の記録は `hooks/README.md` の行が持つ

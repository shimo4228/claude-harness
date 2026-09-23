# ADR-0074: skill 選択を外部判定 API（TypeSafe Jev）へ送る UserPromptSubmit hook — shadow から入り、inject は観測量で点ける

## Status

accepted

## Date

2026-09-21

## Context

[ADR-0018](./0018-rules-rightsize-for-claude5.md) の Consequences（Negative）は「skill の自発トリガーは
実質上限 ≒ 40%（既知の測定値）」と記録し（分母と測定条件は同 ADR に記載が無い）、以後この harness は発火させたい skill を命令形の配線で
補ってきた。[RFC-0024](../../rfcs/0024-typesafe-jev-as-offload-for-max-quota.md) は、TypeSafe の
System One モデル Jev（typed な判定だけを返す hosted API。Claude Max 枠の外で課金される）を
「高頻度で小さな意味判断」に差し込む候補を 5 つ挙げ、候補 2 を skill ルーターとした。RFC-0024 は
2026-09-20 に Fable 枠の回復待ちで `blocked` となったが、著者が 2026-09-21 に候補 2 に限って
着手を指示した。

外部の根拠（2026-09-21 に一次ソースを取得）: TypeSafe 公式 cookbook
`https://docs.typesafe.ai/cookbooks/skill_suggestion.md` は 182 skill の名簿に対し、
2 request（全体を `Choice` で ranking + 「そもそも skill が要るか」の `Noul` 3 問 → 上位 3 件を
本文つきで rerank + 候補ごとの fits `Noul`、どちらの段でも「提案なし」に落ちる）で高々 1 本を選び、
名簿は動かさず skill 名 1 行だけを足す。vendor 実験（488 request、判定 `jev-1.12`、agent
`claude-haiku-4-5-20251001`）の値は wrong load 16.8% → 7.3%（covered 315 request 中）、needless load
9.8% → 4.0%（uncovered 173 request 中）、covered 315 件のうち提案が直したもの 37 件・壊したもの 7 件。
cookbook は閾値を自分の名簿で評価し直す前提で書かれている。これは vendor の名簿と英語 request での
値で、この harness での効果の根拠にはならない。

既製実装の調査（2026-09-21、GitHub の code 検索と repo 検索、README を一次確認）: Claude Code の
hook として cookbook の 2 request 構成を実装したものは見つからなかった。Claude Code 向けの 2 件
（`ShivamPansuriya/jev-skill-gate`、`lomeshdutta/skill-router`）は別機構（`settings.json` の
skillOverrides の書き換え / 外部 skill の install 提案）。cookbook の忠実実装は Hermes Agent 向けに
`DECRUX9812/typesafe-skill-router`（MIT、commit `f150284`）があり、cookbook に無い実測知見を 2 つ
README とコードに記録している — Jev API は 1 問あたり 255 choices が上限であること、`Choice` の
勝者と fits `Noul` の最大が割れる場合があること。

> **注記（2026-09-21、同日の再調査）**: 上の「見つからなかった」は検索語の狭さによる取りこぼしで、誤り。
> awesome list 4 本（`yibie/awesome-jev` ほか）経由で再調査すると、cookbook を明示的に下敷きにした
> Claude Code 対応の実装が既にあった — `Dicklesworthstone/skillranker`（Rust CLI、created 2026-09-17、
> README が cookbook を名指しし `sr install-hook claude` を持つ。ライセンスは MIT に OpenAI / Anthropic を
> Restricted Party とする rider 付きで OSI 準拠ではない）。ほかに `kerpopule/hermes-jev-skills`
> （Hermes 主、SKILL.md 形式で Claude Code にも install）、`BillionsBobby/JevRouter`（`/jevrouter`）。
> Decision 1 の「自作する」は著者判断として残るが、根拠のうち「既製が無い」は成り立たない。

[ADR-0002](./0002-disable-claude-mem.md) の 2026-09-06 注記は、同型の機構（UserPromptSubmit
ごとに prompt を外部ストアへ投げ、結果を additionalContext に注入する）を無効のまま維持した。
理由は 2 点 — (1) 正本の置き場所（注入されるのは transcript 圧縮の episodic な派生データ）、
(2) 記憶が要る時刻（hook は prompt 投入時にしか発火できないが、記憶が要るのは作業途中）。
RFC-0024 の Prior art は、skill ルーターを採用するならこの 2 点との差分を ADR に書くことを求めている。

RFC-0024 の Drawbacks は、2026-09-20 に書いて同日 Rewind した外部送信 hook に security-reviewer が
HIGH 2 件を出したことを記録し、「外部送信する hook は harness の脅威面を実際に広げる」と結論している。
[RFC-0025](../../rfcs/0025-jev-decision-contract-registry.md) は、Jev の判定を質問文の版ごと貯める
registry が無いまま閾値を置くと後から較正できなくなる、と指摘している。

プロンプト本文が TypeSafe に渡ることは、著者が 2026-09-20 に許容を判断済み（名簿側の description は
既に公開 repo にあり、新規に外へ出るのはプロンプト本文。private repo の設計議論や未公開の構想を
含みうることを含めて許容）。

## Decision

1. `skills/jev-skill-router/` を `origin: shimo4228` の sub-project として新設し、cookbook の
   2 request 構成を Claude Code の UserPromptSubmit hook として実装する。依存は Python 標準
   ライブラリのみで、harness の内部部品に依存させない（単独で公開できる形にする）。
   `DECRUX9812/typesafe-skill-router` のコードは取り込まない。同 repo からは知見 2 点（255 choices
   上限への chunk 分割、`Choice` と fits が割れたときの margin 規則）を credit 付きで借り、系譜は
   SKILL.md の `replaces:` に残す。
2. 名簿は 3 系統から組む — user（`~/.claude/skills`）、plugin（`plugins/installed_plugins.json` の
   install path のうち `settings.json` の `enabledPlugins` が true のもの）、project（hook 入力の
   `cwd` から git root までの `.claude/skills`）。`disable-model-invocation: true` の skill と
   ルーター自身は除く。
3. mode は環境変数 `JEV_ROUTER`（`off` / `shadow` / `inject`）で切り替え、`settings.json` には
   `shadow` を明示して配線する。未設定は `shadow`、未知の値は `off` 相当（Jev を呼ばず、`reason` つきの
   skip 行だけ残す）として扱う — 注入も外部送信も、綴り間違いからは起きない。shadow は判定をログに書くだけで、model の文脈へは何も注入しない。
   プロンプトの処理をブロックしないよう、判定は切り離した子プロセスで走らせる。
4. inject へ切り替える条件を観測量で置く: shadow のログが **routed 行 200 以上、かつそのうち同じ
   ターンで skill 使用があった行 40 以上**に達した時点で、一致（提案 = 実使用）/ needless（提案あり・
   使用なし）/ missed（使用あり・提案なし）の 3 つの生値を著者が読んで決める。数え方を固定する —
   `model`・`question_hash`・`router_version` が同一の行だけを 1 つの分布として数える（閾値と margin の
   既定はコードの定数なので `router_version` が運ぶ）。名簿は固定しない: この harness は skill を随時
   足すので 200 行の窓は名簿変更を跨ぐ。`roster_hash` で分割すると分布が細切れになるため分割鍵には
   せず、読むときに窓内の `roster_hash` の種類数を添える。「同じターン」は同一 `session` で次の
   routed 行までの間に `metrics/skill-usage.jsonl` の `invoke` / `read` / `slash` 行があること。
   200 / 40 は著者判断の置き値で、導出は無い（RFC-0025 の Unresolved が「必要な観測数の見積もり方法
   自体がまだ無い」と書くとおり）。切替時は本 ADR に注記する。
5. 判定ログを RFC-0025 の registry の最小形として同梱する。1 判定 1 行で、`mode`、`model`（version pin）、
   `router_version`、`question_hash`（質問文定数から導出）、`roster_hash`、判定の中身（`suggestion` =
   提案した skill 名または null、`winner`、skill 名つきの `shortlist`、gate / fits の確率の生値）、
   `reason`（提案なし・skip・失敗の理由）、`session` と `ts` を持つ。プロンプト本文は書かない（sha と文字数だけ）。読み戻し・集計・描画の
   機構は作らない。
6. RFC-0024 の設計原則を実装の不変条件にする: model は `jev-1.13.0` に pin / あらゆる失敗で
   exit 0（fail-open）/ timeout を明示 / 判定を block に使わない / 閾値は自分のログが溜まるまで
   cookbook の値（gate 0.30、fits 0.30）のまま動かさない。この 2 値は cookbook の `jev-1.12` での
   実験値で、pin する `jev-1.13.0` での較正値ではない — 出発点として借りるだけで、Decision 4 の
   読みが最初の自前の根拠になる。margin 規則は実装するが既定では無効にする
   （cookbook に無い規則なので、shadow ログで不一致の頻度を見てから決める）。
7. inject 時に注入するのは cookbook の `<skill_relevance>` ブロック（skill 名 1 つと「合わなければ
   無視せよ」の 1 文）だけにする。提案が無いターンでは何も注入しない。
8. 実装は implementation-chain の feat chain で行い、Security Review を必ず通す（資格情報の読み取り /
   外部 IO / 公開経路 / 無人実行の 4 面に当たる）。

ADR-0002 注記の 2 点との差分: (1) 注入するのは `skills/` にある正本への**ポインタ 1 行**で、派生
データの本文ではない。正本は repo に残り、注入が外れても何も失われない。(2) skill の選択は prompt
投入時に決まる判断で、hook が発火できる時刻と判断が要る時刻が一致する。ADR-0002 の判断
（claude-mem は無効のまま）は変えない。

> **注記（2026-09-21、公開後の同日評価）**: 公開して実セッションで動かした結果、この機構の期待値は小さいと
> 著者と判断役が評価した。理由: (1) shell の UserPromptSubmit hook は文脈に 1 行足すことしかできず、Claude Code
> 自身の skill 選択は並走し続ける。常駐する description の token は減らない。(2) cookbook で効果が出た条件は
> 「agent が 60 字に切られた索引しか見えない `claude-haiku-4-5`」で、Claude Code は強いモデルに description 全文を
> 見せている — 同じ情報を見ている強いモデルに、弱い判定器が横から助言する形になる。(3) 実セッションの最初の
> 6 判定（2026-09-21、shadow、`jev-1.13.0`）は妥当 3 / 外れ 3 で、外れは 3 件とも `Choice` の勝者と fits 最大が
> 割れたケースだった（6 件は率でなく逸話）。Decision は変えない — shadow を回し続け、Review-when 1 行目の観測量で
> 読む。残す根拠は「モデルが skill を取りこぼしているのか、skill を読まずに自分でやっているのか」を見分ける計器と
> しての価値だけで、読めなければ hook ごと外す。
> 一覧そのものを変える経路は別にある: 公式の `skillOverrides`（on / name-only / user-invocable-only / off）と、
> early access の function hooks（`anthropics/claude-code` の `mods/types/claude-code.d.ts` が
> `prompt.attachment` の種別 `skill_listing` を書き換え可能と明記、2026-09-21 確認）。後者で作り込む案は、
> 保守コストを理由に著者が同日見送った。
>
> **注記（2026-09-21、記事執筆時の再調査）**: 後者の経路は、著者が見送る前日に第三者が実装していた —
> `davila7/claude-code-templates` の mod `jev-skill-suggestion`（初回 commit 2026-09-19T21:50Z）。`skill_listing` に
> `{ text: null }` を返して一覧を model に読ませず、同じ cookbook の 2 request で Jev に高々 1 件を選ばせ、2 つ目の
> commit（2026-09-21T03:12Z）で SKILL.md の添付と `skillOverrides` による非表示まで進めている。同 repo に
> `jev-model-router` もある。README と commit 履歴を原文で確認、未試行。見送りの判断は変えない。

## Review-when

- Decision 4 の観測量に達した → inject の採否を決め、本 ADR に注記する。一致が低ければ inject を
  やめて hook ごと外す候補、高すぎれば（model が既に正しく選んでいる）同じく外す候補
- Claude Code が skill 選択の routing を substrate 側で持つ（名簿の常駐をやめる、関連 skill だけを
  提示する等）→ hook を外す（Scaffold Dissolution の downward）
- TypeSafe が `jev-1.13.0` を廃止する、または料金・保持ポリシーを変える → pin の更新と送信範囲の
  再判断。pin を上げた行は `model` が変わるので別分布として数え直す
- shadow の子プロセスが体感できる遅延や孤児プロセスを残す、または routed 行の失敗
  （`reason` が API 失敗・timeout の行）が過半を占める → 配線を外して原因を直す
- 観測量に達しないまま止まる: skill-stocktake または config-gc の回で、routed 行が 200 未満かつ
  最新の行が 14 日より古い → 計器が死んでいるので配線を外す（空のログを「測っている」の根拠にしない）
- 著者が無人セッション（launchd の triage / daily-research）のプロンプト送信を許容しないと
  判断した → 起動 script 側で `JEV_ROUTER=off` を足す

## Alternatives Considered

- **現状維持 — 発火させたい skill を命令形の配線（rule の 1 行、hook の advisory）で補い続ける** —
  併存させる（却下ではない）。ただしこれだけに留めない理由: 配線は skill ごとに 1 本ずつ手で足す
  もので、常駐文脈を増やし、plugin skill と project skill には届かない。どの skill が「発火すべき
  だったのに発火しなかった」かを数える計器も無い。ルーターの shadow ログはその計器を兼ねる。
  shadow の読みが悪ければ現状維持に戻る（Review-when 1 行目）

- **`DECRUX9812/typesafe-skill-router` の中核を無改変で vendor し、薄い adapter だけ自作する** —
  却下。一度はこの案で plan を組んだが、(a) 中核が `~/.hermes/.env` を読み、この機械に実在する
  そのファイルから base URL と model を拾う経路を adapter 側で封じ続ける必要がある、(b) 著者が
  2026-09-21 に「共通の源は cookbook で、参照しただけなら自作 skill として公開する」と決めた、
  (c) `origin` が自作でないと verify の owned 判定と harness-sync の公開フィルタのどちらにも乗らない
- **Claude Code 向けの既製 2 件を入れる** — 却下。`jev-skill-gate` は `settings.json` を無人で
  書き換える（rule `boundary.md` が人間に渡すと定める操作）。`skill-router` は該当 skill が無いとき
  外部 skill の install を提案する経路を持ち、ECC ローカル管理の方針
  （[ADR-0008](./0008-ecc-local-only-management.md)）と衝突する。どちらも cookbook の 2 request 構成ではない
- **ローカル embedding で routing する**（外部送信なし）— 却下。RFC-0024 の動機は判定を Max 枠の
  外へ出すことと Jev 判定の較正データを貯めることで、embedding はどちらにも答えない。
  未決 — 再訪条件: shadow の一致が低く、かつ外部送信をやめたい判断が出たとき
- **on-demand の CLI / skill として置き、model が必要時に呼ぶ**（`win4r/jev-skill-suggester` 型）—
  却下。発火が model の自発に依存するので、解こうとしている自発トリガーの上限をそのまま継承する
- **最初から inject で入る** — 却下。cookbook 自身が covered 315 件中 7 件を壊したと報告しており、
  日本語プロンプトと 3 系統の名簿での分布は未測定。RFC-0025 が指摘する「閾値をとりあえずの値で
  固定する」形になる

## Consequences

### Positive

- 自発トリガーの上限に対して、命令形の配線を足し続ける以外の手段が測定つきで手に入る
- Jev を使う最初の本番配線が、RFC-0025 の registry（質問文の版つきログ）と同時に入る。後続の
  候補（RFC-0024 の候補 1・3〜5）は同じログの形を再利用できる
- shadow の間は model の文脈が変わらないので、外すときは `settings.json` の 1 行を消すだけで戻る。
  inject に切り替えた後も戻し方は同じ（`JEV_ROUTER` を `shadow` か `off` に戻す）で、失われる
  データは無い。戻らないのは、inject 中のセッションに既に注入された行と、送信済みのプロンプトだけ
- 自己完結の sub-project なので、Claude Code で同じことをしたい人にそのまま渡せる

### Negative

- **対話セッションの全プロンプト本文が第三者の API に送られる。** プロンプトに貼った secret も
  そのまま出る。公開物を自己完結にするため harness の secret scan は再利用しない — SKILL.md と
  README の「送信される範囲」に明記する以外の防御は無い
- 無人 hook が資格情報を読み外部と通信するので、harness の脅威面が広がる（RFC-0024 Drawbacks と
  同型）。security-reviewer の検査対象が恒常的に 1 つ増える
- 名簿に入らない skill がある: `--add-dir` の追加ディレクトリ配下の skill（hook 入力に無い）と、
  ディスクに SKILL.md を持たない built-in skill。これらに対する提案は構造的に出ない
- shadow の間は Jev の課金だけが発生し、効果は無い。観測量に達しないまま放置されると、空の
  ログを根拠に「測っている」と言える状態になる（RFC-0025 Drawbacks と同じ穴）
- 第 2 の記録場所: 閾値と model pin の実値は `skills/jev-skill-router/scripts/` の定数が正本。
  本 ADR と SKILL.md に書いた値は書いた日の写しで、食い違ったらコード側を正とする

### Neutral

- RFC-0024 は候補 2 に限って `in_progress`、RFC-0025 は registry の最小形の実装として
  `in_progress` になる。RFC-0025 の「閾値と反例の置き場」は未対応のまま残る
- 判定ログは gitignore 下に置く（`metrics/skill-usage.jsonl` と同じ扱い）。ログが無いことは
  「未測定」であって「提案ゼロ」ではない

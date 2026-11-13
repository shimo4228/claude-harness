kind: internal
# plan「eval-foundations」の書き換え（27d76e9 → 00b9c99）は、受け入れの条件を満たしたか

as-of: 2026-11-13。plan は [eval-foundations](../eval-foundations.md) の §7。この記録は受け入れ 3（書き換えた者と別の判定）の結果を著者に渡すためのもので、
ここに挙げた No は**どれも直していない**（判定の結果で書き換えを回さない、という plan の決め）。

## 受け入れ 1・2（機械の検査と grep）

- 4 つの commit（9bc69e2、4b55f1c、3927ed7、00b9c99）は commit gate（verify、secret scan、harness lint）を通った
- `harness_lint.py` は exit 0。警告は `skills/skill-stocktake/results.json` に `eval-foundations` と `plugin-directory-submit` が無いことの 2 件（次の stocktake で埋まる）
- 消すと決めた 7 つの文言（`holistic judgment, not a numeric rubric`、`Why not rubric scores`、`opus for judge-type agents`、`判定は常に最強モデル`、
  `canonical home of "evidence, not scores"`、`点数で登らない`、`fresh context, not from a different`）は `skills/` `agents/` `rules/` で 0 件
- `banned phrasing` は llm-as-judge だけ
- `eval-foundations` を指す文書は plan §3 の表と一致する（llm-as-judge、author-calibrated-eval、loop-design-check、persona-read-loop、headline-craft、`evals.md`、readme-writer の引用 2 か所）
- 土台の草稿ゲート（skill-writer §4、別文脈、7 問）は Publishable
- persona-read-loop のテスト 32 件、skill-comply のテスト 146 件は通過（実装 agent が実行）

## 受け入れ 3（書き換えた者と別の判定、1 回）

判定者: Claude（Opus）3 本が対象の 24 ファイルを 3 つに分けて 1 回ずつ、Codex（`--model gpt-6-astra`）1 本が全ファイルを 1 回。どれも書き換えの会話を持たない。
問いは 3 つ: Q1 そのファイルだけを読んだ実行者が手順を実行できるか / Q2 土台か llm-as-judge が持つ決まりの言い直しが残っていないか / Q3 消した語や概念への参照の取り残しが無いか。
行番号は書き換え後（`00b9c99`）のもの。

### A. 書き換えで入った不具合（手順が決まらない・ファイルの中で食い違う）

主ループが原文で確かめたもの。

| 箇所 | 問題 | 指摘した判定者 |
|---|---|---|
| `skills/readme-writer/references/tagline-eval.md`:56-58 | 段 2 から段 3 へ送る候補が決まらない。「どの人物からも開かない側に選ばれた候補」が 1 回でもなのか毎回なのか、「1 位の回数の多い数本」が人物ごとなのか合算なのか | Claude、Codex |
| 同 :73、:87 | 回数の下限を消したので、「ほぼ全部を取った」が決着か割れかを判断する標本の大きさが決まらない。人物別に逆の候補が勝ったときの渡し方も決まらない | Claude、Codex |
| 同 :38 と :88-89 | :38 は段 2 の 1 周と段 3 の 1 周をそれぞれラウンドと定義し、:88 は「次のラウンドに進むのは候補を足したときだけ」と書く。候補を足さずに段 2 から段 3 へ進む手順と食い違う | Claude、Codex |
| 同 :5 | 「最下位に近い」が、順位を作らなくなった手順と合わない | Claude |
| `skills/llm-as-judge/SKILL.md`:94-95 と :109 | 四段の節は反証の問いを「下書きが不合格側のとき」とし、規模の表は 1 件の判定を「Unconditional」とする。四段で合格側のときに反証を回すかが決まらない | Claude、Codex |
| 同 :79-80 と :83-84 | 段 1 を書くのは「最後の段を担う判定者」、段 3 は「新しい文脈の判定者」で段 1 を見ない。二人が同じ役か別かが決まらない（付録 A の文をそのまま写した箇所） | Claude |
| `skills/skill-writer/SKILL.md`:105 | 「opus for judge-type agents」を消した結果、括弧「(read-only + Bash only when an evidence script exists)」が `tools` でなく `model` に付いて読める。agent の `model` の選び方の指定も無くなった | Claude（Codex は Q1 Yes） |
| `skills/author-calibrated-eval/SKILL.md`:96 | 消した 2 項目（自分の足切りの合格率、判定の揺れと同じ大きさの差）を eval-foundations へ指したが、土台にこの 2 つを見分ける文は無い。実行時の判断が skill の外へ出た | Claude、Codex |
| `skills/readme-writer/references/readme-judge-checklist.md`:127、:133-134 | 「上限 2 ラウンド」を消したあと、:127 は理由だけが残り、:134 はこのファイルに無い「ラウンド上限」を指す | Claude |
| `skills/loop-design-check/SKILL.md`:146 と :151 | 例の合格条件を「全出力が Publishable」に変えたが、:151 の実測は旧条件（2 of 3）で走った回の記録 | Claude |
| `skills/eval-foundations/provisional.md`:3-5 と :22、:25-26、:32、:34 | 冒頭は「決めは一か所にある」と書くが、§2・§3 は「ここ」に書きつつ直す場所に llm-as-judge も挙げる。§1 は「写さない」と書く直前に段の中身を要約している | Claude、Codex |
| `skills/harness-sync/SKILL.md`:246 | 「原則の正本は `search-first` 等の消費 skill、ADR-0026」が残る。search-first は正本の名乗りを消した（今回の対象外のファイル） | Claude |
| `skills/readme-writer/MAINTENANCE.md`:37 | 実測の行に「推奨は 1 対 1 で決める」が現在形で残り、同じファイルの「推奨を出さない形にした」と食い違う | Claude |

### B. 持ち主の線引きそのものへの指摘（両系統が No）

- **土台の原則 1 と llm-as-judge の Core rule が同じ決まりを述べている。** `eval-foundations/SKILL.md`:18-19 と `llm-as-judge/SKILL.md`:14-15、③。
  土台の持ち主の表（:59）は「集計しない」を llm-as-judge の持ち物としている。依頼が、原則 1 を土台に置くことと、llm-as-judge に「点数に集計しない」を残すことの両方を求めたことの帰結
- **`provisional.md` §2・§3 の中身（点を付けない、列挙型の語を一つ、二値、結論の語と次の行動の対応）は、llm-as-judge の三原則の表と ② の言い直し。**
- **判定器を走らせる skill に残した手順の 1 行を、判定者は言い直しと読んだ。** 「Binary answers are evidence, never aggregated into a score」（skill-stocktake:236、rules-stocktake:129、
  agent-stocktake:208）、「No numeric score, no rubric, no aggregation into a grade」（repo-asset-stocktake:53）、「Do not aggregate; a single dominant No may decide」（skill-writer:148-149）、
  learn-eval:162-164、readme-judge:20-21、checklist:7-8、:12、:137、:141-142、readme-writer:61、:63、author-calibrated-eval:60-61、loop-design-check:22、:86、:157。
  plan §2 は、これらを「実行の指定の 1 行」として残すと決めていた（確認点 B の推奨の読み）

### C. 文の検査で残した理由の句（言い直しかどうかで判定者が割れた）

実装 agent が「その領域の理由」「手順と一体」と読んで残し、判定者が「一般の理由」と読んだもの。

- llm-as-judge:36-37、:51-52、:70-72、:117、:125-127、:199-205（全体の判断は LLM の得意、隠れた No は揺れを生む、同じ問いで再判定する理由、注意は薄まる資源、文献の説明）、:110-113（費用の理由。Codex だけ）
- skill-stocktake:20-23、:43、:54-55、:63-64、:168-169、:432-434 / repo-asset-stocktake:15、:19、:34（今回は個数しか触っていない）
- learn-eval:156-157、:179、:186-189、:193-195、:250-251
- readme-writer:192-193、:233 / readme-judge:34-35、:46-48 / headline-craft:14-23、:99、:128（Codex は headline-craft を Yes）
- persona-read-loop:93-96、:54（:54 は Codex だけ）/ `presets/article.md`:81-84（Codex は Yes）
- author-calibrated-eval:33-34 / loop-design-check:109 / task-triage:401-402（Codex は Yes）/ architect:56（Codex は Yes。今回は触っていない行）
- skill-writer:136-137（「only if it looks stale」の禁止が、正本とする skill-stocktake Phase 2 からは消えてこちらにだけ残る）

### 3 問とも Yes だったファイル

`skills/hook-stocktake/SKILL.md`、`skills/skill-comply/SKILL.md`、`skills/search-first/SKILL.md`（ファイル自体）、`agents/decision-history-reviewer.md`、`rules/common/evals.md`。
Codex だけが Yes としたもの: `agents/architect.md`、`skills/headline-craft/SKILL.md`、`skills/persona-read-loop/presets/article.md`、`skills/task-triage/SKILL.md`。

## 読み方

- A は書き換えた側の不具合で、判定者の好みではない。tagline-eval は、推奨を出さない形に直したときに回数と決着線を消したことで、手順として閉じなくなった
- B は、依頼の「同じ決まりが二か所に出ないようにする」をどこまで厳しく読むかの問題で、plan の初版の評価でいちばん揺れた項目と同じ。
  「実行の指定の 1 行は残す」という読みを採った結果を、別の判定者は 2 系統とも言い直しと読んだ
- C は文ごとの境の問題で、系統のあいだでも割れた
- Q1（実行できるか）で No が付いたのは tagline-eval、llm-as-judge、skill-writer、author-calibrated-eval の 4 ファイルと、tagline-eval に委ねる readme-writer の Step 1。
  ほかのファイルは、消したもので実行に困るという指摘は無かった

## Still unknown

- B と C の指摘のどこまでが作品の側の欠けで、どこからが判定者の共通の読み癖か（問いが「言い直しが残っていないか」なので、残っていれば No になる）
- 書き換え後の skill を実際に走らせたときに、判定の振る舞いが書き換え前と変わるか（今回は文面の判定だけで、実走の比較はしていない）

# eval 系 skill の器を整える — 共通の土台を一か所に置き、各 skill は固有の手順だけを持つ

Date: 2026-11-13（同日に改訂 1）
Research: [棚卸し](research/2026-11-13-eval-skills-stocktake.md)（一覧・重なり・食い違いの file:line）、
[初版の評価](research/2026-11-13-eval-foundations-trial.md)（この plan の初版を四段の手順で判定した記録。結論は Revise）
State: 承認（2026-11-13、改訂 1）。著者は確認点 A〜H を推奨どおりとした。改訂 1 そのものは判定し直していない

著者が決めたことの原文は末尾の「付録 A」にある。土台と四段を書く者は、この plan の要約ではなく付録 A の文から書く。

## Context

eval・判定・レビュー・採点に関わる記述は、harness の skill 25 本と agent 4 本、執筆 repo と論文 repo の skill・agent 十数本に散っている。棚卸しで分かったこと:

- いちばん重なっているのは「点を集計しない」（18 か所）、「コードで確かめられることは先に」（12 か所）、「判定者は書き手の文脈を持たない」（12 か所）。
  理由を節として説明しているのは llm-as-judge だけで、ほかは結論だけの写しか、一句の理由か、それぞれの実測から独自に書いたもの
- 著者の 9 原則のうち、P2・P4・P5・P7 は一般則としてどこにも書かれていない。断片と実装例だけがある
- 食い違いは 10 件（report の表の 12 行から、規模の違いの #10 と書き方の規約の #11 を除く）
- 回数・モデル名・prompt の言い回しは、ほぼ全部の skill に書かれている

先例が一つある。`measurement-discipline` は共通の原則を持つ global の skill だったが、2026-11-08 に project skill へ移した（9de937f）。
9 原則のうち 5 つが現行モデルが skill 無しで当てる統計の常識で、出どころの project の外では慎重すぎる側へ引いていたからである。

初版は評価で Revise になった。改訂 1 で変えたのは: 著者の原文を付録に持つ / 「二か所に出ない」の読みと仮の決めの置き場を、本文の断定から確認点へ移す /
決まりごとの持ち主と参照の向きを一つにする / 棚卸しの漏れ（stocktake 系 2 本ほか）を埋める / 扱いが未定だった食い違いに処置を書く / 受け入れの条件を足す。

## 構成

### 1. 土台 — `skills/eval-foundations/`（仮称）

```
skills/eval-foundations/
  SKILL.md         9 原則。付録 A の文を 1 原則 1 段落で写す（英語）。理由は著者の文にあるものだけを書き、足さない
  provisional.md   仮の決めの索引。4 項目（§5）
  MAINTENANCE.md   未解決の問い 2 つ（付録 A の文のまま、「決めていない」と明記）、原則ごとの実測の出どころ、初版の評価へのリンク
```

- frontmatter は `disable-model-invocation: true`、`user-invocable: true`、`origin: shimo4228`（同じ組の skill が既に 16 本ある）
- 読まれるのは判定を**設計・改修するとき**。判定を実行するたびには読まない。実行に要る指定は各 skill が自分で持つ
- 入口は `rules/common/evals.md` に 1 行: 判定を設計・改修するときは先に skill: `eval-foundations` を読む。行き先表は evals.md だけが持つ。
  同じ変更で evals.md 冒頭の `rationale` と `review-when` に、この行の理由と失効条件を足す

### 2. 持ち主と参照の向き

| 何を | 持ち主 | ほかの文書での扱い |
|---|---|---|
| 原則（なぜ・一般にどうするか）。9 原則と、確認点 A で足すもの | `eval-foundations` | 言い直さない。必要なら skill 名で指す |
| 判定器の形（二値の確認を証拠に → 列挙型の結論を一つ → 集計しない、決定的な No、反証の問い、コード先行、四段） | `llm-as-judge` | 判定器を走らせる skill は llm-as-judge を名前で指し、自分の問いと結論の語だけを書く |
| その skill の出力と段取り（何を出すか、どの順でやるか、誰に何を渡すか） | 各 skill | — |
| その領域で測った理由（例: README は 2 ラウンド目から voice が均される） | 各 skill の MAINTENANCE.md か、判定者が毎回読む reference | 一般則ではないので土台へ寄せない |

参照の向きは一方向にする: 判定器を走らせる skill → `llm-as-judge` → `eval-foundations`。判定器を持たない skill（persona-read-loop、loop-design-check、headline-craft、
author-calibrated-eval の著者読みの部分）→ `eval-foundations`。一つの決まりについて二つを指さない。参照は skill 名で書く（llm-as-judge:177-182 が installed の skill を引く形）。

**文の検査**（report の「重なり」表に挙がった全部の所在に、一文ずつ当てる）:

1. その文は、この skill の判定者か script が何を出すか・どの順でやるかを指定しているか。Yes なら残す
2. その文に理由の句（括弧の説明、「— 」のあとの説明、文献）が付いているか。付いていれば句だけを消す。その領域で測った理由なら上の表の 4 行目へ移す
3. その文は、この skill の外にも当てはまる言い方（評価は一般にこうする、という文）か。Yes なら消し、必要なら skill 名の参照 1 行に置き換える

初版の評価で境が割れた文に当てた結果:

| 文 | 処置 |
|---|---|
| llm-as-judge:14-15（Core rule）、:35-39（三原則の表） | 残す（判定器の形の持ち主） |
| llm-as-judge:17-31（Why not rubric scores） | 消す（一般の理由。土台の P1・P5 が持つ） |
| learn-eval:162-164「Never convert them into a numeric score」、:188-195 | 残す（手順）。:256-258 の文献の説明は消す |
| skill-stocktake:239-241、rules-stocktake:132-133、agent-stocktake:211-212 | 「binary answers are evidence, never aggregated into a score」を残し、「holistic judgment, not a numeric rubric」と括弧の理由を消す |
| skill-stocktake:195-197、rules-stocktake:96-98、agent-stocktake:189-190（banned phrasing） | 「無条件に確かめる」の手順を残し、「banned phrasing: …dilutes」の説明を消す（llm-as-judge:112-114 が持つ） |
| readme-judge:98、checklist:137 | 残す（手順） |
| checklist:127（上限 2 ラウンド） | 消す（readme-writer:230 が持つ）。:131-136 の README 固有の理由は残す |
| skill-writer:147-150 | 残す（草稿ゲートの手順）。「non-Keep」を直す |
| search-first:70-71「the canonical home of "evidence, not scores"」 | 「正本」の名乗りを消す。「判断は文で書く」は残す |
| architect:6-7 のコメント | 「判定は常に最強モデルで」を消し、fable が引けないときの配線の行は残す |

この線引きは、依頼の「同じ決まりが二か所に出ないようにする」を「原則と理由は一か所、各 skill には実行の指定だけ」と読んだもの。
初版の評価でいちばん揺れた点で、読みは著者が決める（確認点 B）。

### 3. skill ごとの変更

「文の検査」を当てたうえで、それぞれに固有の変更を書く。所在の file:line は report の一覧と「重なり」表にある。

| skill / agent | 指す先 | 固有の変更 |
|---|---|---|
| `llm-as-judge` | 土台 | Why の節を消す。四段の節を足す（§4）。問いの個数（:75、:92）を消す。73 本の実測（:97-104）を新しい MAINTENANCE.md へ移す。prompt の雛形は段の順と出力 schema を残し、個数を消す |
| `author-calibrated-eval` | 土台（著者読み）、llm-as-judge（足切り） | §6 のうち P2・P6 の言い直しを消す。「Opus」「85k / 25k tokens」（:22、:75-76）を MAINTENANCE.md へ移す |
| `loop-design-check` | 土台、llm-as-judge | #6（:109）と Step 3（:86）は問いと手順を残し、理由の説明を消す。例の「against a rubric」「2 of 3 Publishable」（:146）を、数で合否にしない形へ直す |
| `persona-read-loop` | 土台 | Limits の同系統の説明（:161-162）を参照に。P9 の処置は §6 |
| `skill-comply` | — | P9 の処置は §6。遵守率は品質の点ではないので残す |
| `readme-writer`、`readme-judge`、checklist | llm-as-judge（既に指している） | SKILL :61-63 の理由の句、checklist:127。MAINTENANCE:22 と tagline-eval:6 の「rule evals.md: 判定の点数で登らない」の引用先を土台に直す。tagline-eval は確認点 F |
| `skill-writer` | llm-as-judge（既に指している） | :105「opus for judge-type agents」を消す。:147 を直す |
| `learn-eval` | llm-as-judge（既に指している） | 上の表のとおり。判定の文脈は変えない（代理決定 6） |
| `skill-stocktake`、`rules-stocktake`、`agent-stocktake`、`hook-stocktake`、`repo-asset-stocktake` | llm-as-judge | 上の表のとおり。同じ二段（二値の確認 → 反証の問い）の説明と文献の節（skill-stocktake:437-441、agent-stocktake:323-328）を参照 1 行にし、それぞれの問いと結論の語を残す |
| `headline-craft` | 土台 | :93-94 の理由の句を消す（「点数を付けない」の手順は残す） |
| `search-first` | — | 上の表のとおり |
| `architect` | — | 上の表のとおり |
| `task-triage` | — | :401-402（確認点 E） |
| `rules/common/evals.md` | 土台 | 入口の 1 行を足す。:10 の「（judge の点数で登らない）」を消す。rationale と review-when を足す |
| `detail-loop`、`generation-audit` | — | 変えない（代理決定 4・5） |
| E1・E2 を書いているほかの skill（review-to-lint、skill-health、decision-history-reviewer、jev-judgment-design、implementation-chain、task-triage ほか） | — | 文の検査を当てる。どれも自分の手順として書いているので、消えるのは理由の句だけの見込み |

### 4. llm-as-judge に足す四段

節の本文は llm-as-judge に一つだけ置く。文は付録 A の四段をそのまま写し、節の先頭に「仮」と書く。

いまの形との継ぎ目:

- コード先行は段 1 より前に置く（llm-as-judge:108-111 の決まりを保つ）。確かめた事実は段 3 に事実の行として渡す
- 反証の問いは段 3 の中に置く（下書きの結論が不合格側のときに攻める、という今の形を変えない）
- 決定的な No と段 3 の覆しの関係は確認点 G

### 5. 仮の決め — `provisional.md` の 4 項目

`provisional.md` は索引で、項目ごとに「いまの仮の決め」「決めの本文がある場所（一つ）」「差し替えの引き金になる学び」「差し替えるときに触る場所」を書く。
決めの本文は一か所にだけ置き、ほかは写さず指す。

| 項目 | いまの仮の決め | 本文がある場所 | 差し替えるときに触る場所 |
|---|---|---|---|
| ホリスティックな段の置き方と、何を見せるか | 四段の段 1（観点を見ない）と段 3（作品と観点の証拠を見る。段 1 は見ない）。結論として扱うのは段 3 | llm-as-judge の四段の節 | その節だけ |
| 目盛りの形 | 点を付けない。結論は列挙型の語を一つ、観点は二値。二つを比べる形は候補を選ぶ場面でだけ使う | `provisional.md` | `provisional.md`、llm-as-judge の三原則の表と出力 schema |
| 判定者に基準を渡す方法 | 観点は二値の問いの文で、結論の語は次の行動との対応で渡す。事例は渡さない | `provisional.md` | `provisional.md`、llm-as-judge の prompt の雛形 |
| 判定者の確信度の扱い | 結論の判定者には確信度を出させない。確信度を出している 2 か所（security-reviewer、generation-audit）は今のまま | `provisional.md` | `provisional.md` |

2〜4 行目の「いまの仮の決め」は、著者の文ではなく、いまの実物の形を主ループが読んだもの（確認点 H）。差し替えの引き金は付録 A の「これから学ぶ内容」をそのまま書く。

### 6. P9 の当て方

読みは確認点 D。推奨の読みで実物に当てた結果:

| 実物 | 処置 |
|---|---|
| persona-read-loop `presets/article.md`:16-18 のモデル名 | 読みの深さで選ぶ書き方へ（`presets/readme.md`:24-25 と同じ形）。SKILL.md:49 の「the preset's `model` column」を合わせて直す |
| tagline-eval:26 `--model sonnet`、:55 と :84-86 の回数 | モデル名と回数を消す。決着線は確認点 F |
| readme-judge:51「about 5」、:94「3–5」、llm-as-judge:75、:92、stocktake 系の「1–3」 | 個数を消す |
| skill-comply:141-147 の Models 表、:41-42 の使用例のモデル名 | 表を消す（既定値は script の `--help` が持つ）。使用例は flag の名前だけにする |
| script が読み手に渡す固定の prompt（persona-read-loop の preset、tagline-eval の 3 本） | 残す。ラウンド間で答えを比べる計器の一部で、P8 が固定を求める。置き場は preset と reference で、SKILL.md の本文には書かない |
| script の既定値（`read.sh` の sonnet、skill-comply の既定）、agent の `model:` frontmatter | 今回は残す（配線。省くと session の model を継ぐ） |

### 7. 受け入れ

書き換えが終わったことは、次の 4 つで決める。3 の結果で書き換えを回さない（P6）。

1. **機械の検査**: `.claude/verify.sh`、`harness_lint.py`、skill-health の `scan_refs`
2. **重なりが消えたことの grep**（`skills/` `agents/` `rules/` に対して）:
   - `holistic judgment, not a numeric rubric`、`Why not rubric scores`、`opus for judge-type agents`、`判定は常に最強モデル`、`canonical home of "evidence, not scores"`、`点数で登らない` が 0 件
   - `banned phrasing` が llm-as-judge だけ
   - `eval-foundations` を指す文書が、§3 の表で「土台」を指すとした文書と一致する
3. **書き換えた者と別の判定（1 回）**: 別の文脈の判定者（別系統を一つ混ぜる）が、書き換えた skill を一本ずつ、その skill だけを読んで二つを確かめる。
   (a) 書き換え前の版（`git show <base>:<path>`）と比べ、実行に要る指定が消えていないか (b) 土台か llm-as-judge が持つ決まりの言い直しが残っていないか。
   答えは Yes / No と根拠の箇所。No は直さずに、diff と並べて著者に渡す
4. **著者の通読**。最後に決めるのは著者

### 8. 今回の範囲の外

- 執筆の repo と論文の repo の skill・agent。土台と同じ決まり（writing-ecosystem:132-133 の別系統、:166-171 の読み直させない、
  prose-clarity-reviewer:16-17、article-stocktake:68）と逆の決まり（paper-ecosystem:72、:79-80 の review + fix loop）がそのまま残る
- 実装 chain の code review（implementation-chain、task-triage §4 の判定者の構成とモデル名）。決定的な gate が主で、判定者の割り当ては費用の決定が持つ。
  implementation-chain:106、:113、:136-139 に土台と同じ向きの記述が残る
- `docs/plans/holistic-eval-layer.html` の仕組み（`/eval-panel`、ledger、隠した観点）
- 公開 repo への同期。公開の単独 repo 10 本と plugin 2 つ（harness-stocktake、akc-cycle）は、同期するまで今の内容のまま。同期のときに、土台を claude-harness に出し、
  2 つの plugin の allowlist に足すかを決める（著者の指示で行う）

## 代理決定（推奨で進める。違えば言ってほしい）

1. 土台は新しい skill にする。常駐の `evals.md` に原則を書くと毎 session の費用になり、llm-as-judge の中に置くと判定器を作らない skill から指しにくい
2. 位置の偏りに対する順序の入れ替えは、P2 のバイアスへの対策として扱い、P7（揺れの点検）の対象にしない。両順の結果は割れとしてそのまま返す（readme-judge:74-75 の今の形）
3. 四段は 1 件ずつ判定する場面に限り、数十件を回す棚卸しには今の二段を使う、と llm-as-judge の「Scale the machinery」の表に書く。
   四段は 1 件につき subagent を観点の数 + 2 回起こす（初版の評価は 11 本、Claude 側だけでおよそ 110 万トークン）。段 4 の突き合わせは手順として書き、script は持たせない
4. `detail-loop` は変えない。ループの中の review は発見の道具で、Done の条件には著者の読み（:106-110）が入っている。P6 と同じ向きと読む
5. `generation-audit`:55-56（別 session で文言の再現を確かめる）は変えない。同じ作品への判定の繰り返しではなく、モデル経由の自己申告の捕捉を確かめる手順なので、P7 の外と読む
6. `learn-eval` Step 5 は判定の文脈を変えない。Save と Absorb は著者の承認（:197-207）を、Promote は別文脈の草稿ゲート（:212-216）を通る
7. 土台の本文は英語で書く（公開している skill と揃える）。著者の原文はこの plan の付録 A が持つ
8. 実装は Opus の subagent に渡し、新しい skill は書く前に skill: `skill-writer` を通す

## 著者に確認したい点

初版の評価で揺れが大きかったのは B と C。

- **B.「同じ決まりが二か所に出ない」の読み**。推奨は §2 の線引き — 原則と理由は土台だけ、各 skill には実行の指定の 1 行を残す。
  もう一つの読みは、各 skill は参照だけを持ち、判定者が実行のたびに土台を読む形。こちらは重なりが文字どおり消えるが、実行のたびに土台を読む費用がかかり、単独で公開している skill が一本では動かなくなる
- **C. 仮の決めの置き場**。推奨は §5 — `provisional.md` は索引で、ホリスティックな段の本文は llm-as-judge の四段の節に一つだけ置く。
  もう一つは、四段の節ごと `provisional.md` に置き、llm-as-judge からは指すだけにする形。差し替えは 1 ファイルで済むが、llm-as-judge が自分のディレクトリだけでは実行できなくなる（skill-writer:86-88 の決まりと逆）
- **D. P9 の範囲**。依頼は「スキルに書かず」。推奨の読みは、skill の本文・preset・reference・agent の本文には回数とモデル名を書かず選び方を書く、script の既定値と agent の `model:` は配線として今回は残す（§6）
- **A. 9 原則の外の決まりを土台に足すか**。候補は「判定者は書き手の文脈を持たない。同じ文脈で判定するのは、受け入れを別の目（別文脈の判定者か著者）が持つときだけ」（12 か所に、理由の違う形で書かれている）。
  推奨は足す。「コードで確かめられることは先に」は、依頼どおり llm-as-judge が持ち、土台には足さない
- **H. 仮の決め 3 点の中身**（§5 の表の 2〜4 行目）。いまの実物の形をそのまま仮としたが、著者の文ではない
- **G. 決定的な No と四段**。段 3 は事実を名指せば観点の証拠と逆の結論を出せる。決定的な No も同じ扱いにするか。推奨は、決定的な No は段 3 でも覆せないとする。
  初版の評価では、決定的な No の定義そのものの読みが同じ判定者の 2 走で割れた。定義は skill ごとに、当てはまるかを実物で確かめられる形で書く、を合わせて四段の節に入れたい
- **E. 判定者の独立性**。P3 を土台に書くと task-triage:401-402「独立性は fresh context から来る。別モデルからではない」と逆になる。
  推奨は、この文を「この loop では費用の理由で同系統を使う。同系統の癖は残る」という事情として書き直し、code review の判定者の構成は変えない
- **F. tagline-eval**。読み手の票（Borda の合計、4 分の 3 の決着線）で推奨を 1 本出している。同じ入口の 1 行を扱う headline-craft は点・順位・推奨を付けない。
  推奨は、票を足切りと割れの記録に使い、推奨を出さず著者に渡す形へ揃える

## 実装の順序（確認のあと）

1. この plan と report 2 本を単独で commit（`docs(plan): eval-foundations`）
2. `skills/eval-foundations/` を付録 A から書く（skill-writer の草稿ゲートを通す）
3. `llm-as-judge` を直す（Why を消す、四段を足す、MAINTENANCE.md を作る）
4. 残りを §3 の表のとおり直す。`evals.md`:10 を消す変更と、それを引く 2 か所（readme-writer MAINTENANCE:22、tagline-eval:6）の直しは同じ commit に入れる
5. 食い違いの修正（確認点 E・F、loop-design-check:146、skill-writer:147）は、寄せる変更と別 commit にする
6. §7 の受け入れ 1〜3 を回し、3 の結果と diff を著者に渡す
7. 公開 repo への同期は著者の指示を待つ

## 付録 A — 著者の決め（依頼の原文）

### 共通の土台に置く原則

1. ルーブリックの点を合計して結論にしない。指標が目標になると崩れる（グッドハート）。目指すのはホリスティックな判断
2. ノイズとバイアスを分けて考える。同じ判定者の繰り返しで減るのは、その時々の揺れ（機会のノイズ）だけ。判定者の安定した癖と、全員に同じ向きに乗るずれは繰り返しでは残る
3. 判定者は数より系統の違いを混ぜる（たとえば Claude と Codex）。系統どうしの食い違いは平均せず、割れとして残す。ただし系統をまたいで共通する癖は混ぜても残り、外の手応えでしか見えない
4. 下限を守る判定（欠けの拾い出し、決定的な No）は合議でよい。上限を選ぶ判定（どれがよいか）は一つの目に残す
5. 全体の判断と観点ごとの評価は写り合う。どちらを先に置くか、何を見せるかを決めておく
6. 作品を直すループと、評価する判定は分ける。ループの中の判定は学ばれて押されるので、結果を見ない判定をループの外に置く
7. 揺れの点検は揺れの大きさを知るためだけに使い、結論は一回目のまま残す。揺れの大きかった項目は結論に添える
8. 手順を固定すること自体が揺れの対策になる。評価のたびにモデルに流れを組み直させない
9. 回数、プロンプトの言い回し、具体的なモデル名など、モデルが変わると古くなる細部はスキルに書かず、そのときのモデルに任せる

### llm-as-judge に足す候補（判定に固有の手順）

いまの形（二値の確認を証拠として集める、点数に集計しない、列挙型の結論を一つ、決定的な No、反証の問い、コードで確かめられることは先に）は残す。そのうえで次の四段を候補とする。

1. 最後の段を担う判定者に、観点の結果を見せずに全体の結論と理由を書かせて保存する
2. 観点ごとに別のサブエージェントを立て、一つの観点だけを見させる。返すのは二値の確認と根拠の箇所で、点は付けさせない
3. 新しい文脈の判定者に、作品と 2 の証拠を見せて最終の結論を出させる（1 は見せない）
4. 1 と 3 をコードで突き合わせて食い違いを記録する。3 が観点の証拠と逆の結論を出したら、観点に入っていない事実を一行で名指しさせる。名指しできない覆しは覆しすぎの疑いとして記録する

### 仮の決めとして薄く書くところ

次の点は、これから学ぶ内容（直観を信頼できる条件、事例で基準を共有する方法、点を付けるより二つを比べる比較判断、LLM を評価者にしたときの位置や長さへの偏りと自己優遇、較正と確信度）で手が入る見込みが大きい。
決めを書くときは「仮」と印を付け、あとで差し替えやすい場所にまとめておく。

- 最後のホリスティックな段の置き方と、何を見せるか
- 目盛りの形（点か、ほかと比べる形か）
- 判定者に基準を渡す方法（アンカーになる事例など）
- 判定者の確信度の扱い

### 未解決の問い（いまは決めない）

- 別系統の判定者もそろって同じ向きに覆したとき、作品の側の発見か、判定者どうしの共通の好みかをどう読むか
- 1 と 3 の食い違いが多い作品で、どちらを結論にするか

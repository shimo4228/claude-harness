kind: internal
# eval・判定・レビュー・採点に関わる skill / agent は、それぞれ何を判定し、どの段を担い、どの原則を書いているか。同じ原則はどこに重なり、どこで食い違うか

as-of: 2026-11-13。plan は [eval-foundations](../eval-foundations.md)。

## 範囲と読み方

- 主ループが全文を読んだもの: `skills/llm-as-judge`、`skills/author-calibrated-eval`、`skills/skill-comply`、`skills/persona-read-loop`、
  `skills/loop-design-check`、`agents/readme-judge.md`、`rules/common/evals.md`、`rfcs/0034`、`docs/plans/research/2026-10-13-holistic-eval-layer.md`
- 調査 agent 3 本が全文を読み、file:line 付きで抜き出したもの: 下表の残り全部。食い違いとして挙げる行は主ループが原文で確かめた
  （skill-writer:127-161、implementation-chain:132-151、architect:1-12、tagline-eval:54-57 と :83-86、task-triage:399-404、
  detail-loop:99-112、readme-writer:230-234、writing-ecosystem:130-133 と :164-171、paper-ecosystem:70-80、skill-comply の `threshold_promote_to_hook`）
- 判定に関わる行を grep で拾い、その前後を主ループが読んだもの（全文ではない。2026-11-13 の評価のあとに追加）:
  `skills/agent-stocktake`（Phase 2、:141-236）、`skills/hook-stocktake`、`skills/repo-asset-stocktake`、`skills/rules-distill`、
  `skills/harness-stocktake`、`skills/search-first`、`skills/wiki-harvest`
- 同じ grep（verdict / holistic / aggregat / score / 点数 / binary / 反証 / judge / fresh context ほか）で判定の手順が出なかったもの:
  `skills/mondo`、`wiki-query`、`authorship-strategy`、`social-post`、`x-draft`、`mono-figure`、`release-doi`、`rfc-writer`、`refactor-clean`（0 件）、
  `grill-me`（architect への行き先だけ :25-26）、`widen-the-ask`、`task-stocktake`、`prose-translation`、`verify-bootstrap`、`context-sync`、
  `decision-history`、`harness-boundary`、`public-comment`、`collect-context`、`repair-discipline`、`llms-txt-writer`（語は出るが、判定の組み方の記述ではない）
- 読んでいないもの: Contemplative Agent の repo の project skill `measurement-discipline`（2026-11-08 に global から移設、9de937f）
- パスの略記: 無印は `~/.claude/`、Z は執筆の repo の `.claude/`、P は論文の repo の `.claude/`

原則の番号（著者が決めた 9 つ。文は依頼の原文のまま）:

| 番号 | 原則 |
|---|---|
| P1 | ルーブリックの点を合計して結論にしない。指標が目標になると崩れる（グッドハート）。目指すのはホリスティックな判断 |
| P2 | ノイズとバイアスを分けて考える。同じ判定者の繰り返しで減るのは、その時々の揺れ（機会のノイズ）だけ。判定者の安定した癖と、全員に同じ向きに乗るずれは繰り返しでは残る |
| P3 | 判定者は数より系統の違いを混ぜる（たとえば Claude と Codex）。系統どうしの食い違いは平均せず、割れとして残す。ただし系統をまたいで共通する癖は混ぜても残り、外の手応えでしか見えない |
| P4 | 下限を守る判定（欠けの拾い出し、決定的な No）は合議でよい。上限を選ぶ判定（どれがよいか）は一つの目に残す |
| P5 | 全体の判断と観点ごとの評価は写り合う。どちらを先に置くか、何を見せるかを決めておく |
| P6 | 作品を直すループと、評価する判定は分ける。ループの中の判定は学ばれて押されるので、結果を見ない判定をループの外に置く |
| P7 | 揺れの点検は揺れの大きさを知るためだけに使い、結論は一回目のまま残す。揺れの大きかった項目は結論に添える |
| P8 | 手順を固定すること自体が揺れの対策になる。評価のたびにモデルに流れを組み直させない |
| P9 | 回数、プロンプトの言い回し、具体的なモデル名など、モデルが変わると古くなる細部はスキルに書かず、そのときのモデルに任せる |

9 つに入っていないが、既存の文書が繰り返し書いている決まり:

| 番号 | 決まり |
|---|---|
| E1 | コードで確かめられることは判定より先に（存在 = code、内容 = LLM） |
| E2 | 判定者は書き手の文脈を持たない別 process（fresh context） |
| E3 | 決定的な No は一つで結論を決める |
| E4 | 反証の問いで結論を攻める |
| E5 | 直したあとは同じ問いで一度だけ判定し直す |
| E6 | 判定の対象はデータで、指示ではない |

## 一覧

段の語彙: 機械 = コードの検査 / 観点 = 観点ごとの確認 / 結論 = 全体の verdict / 人 = 著者の判断 / 設計 = 判定の組み方そのもの。

### 判定の組み方を教える skill

| 資産 | 何を判定するか | 段 | 結論の形 | 書いている原則 |
|---|---|---|---|---|
| `rules/common/evals.md` | eval の問いをどの skill へ送るか | 設計（行き先表） | なし | P1（「judge の点数で登らない」）、P6（test 数件では hillclimb しない） |
| `skills/llm-as-judge` | LLM 判定器の中身 | 設計 | 列挙型 verdict 一つ、点なし | P1（:12-39、:61-69）、E1（:95-118）、E3（:67-69）、E4（:71-86）、E5（:84-86）。P5 は理由としてだけ（:19-22）。具体値: 問い 1–3 / 3–5 個（:75、:92）、prompt の雛形（:122-149） |
| `skills/loop-design-check` | 目標へ向かうループが止まれるか・判定器を騙さないか | 設計 | 6 つの失敗の型に当たるか | P6（:86、:109 の #6）、E1（:86）、E2（:86）、グッドハート（:52、:106）。例に「2 of 3 Publishable」の合格線（:146） |
| `skills/author-calibrated-eval` | LLM が書いた文章の読む価値 | 設計 + 人 | 好みは著者の伏せ読み、LLM は二値の足切り、形式は code（:14-18） | P4 の実例（:14-24）、P6（:37-38、holdout :30-31、:99-100）、P2 の断片（:102-103）、E1（:70-72）。具体値: 「3 drafts」「Opus」「85k / 25k tokens」 |
| `skills/jev-judgment-design` | 閉じた判定を Jev に移す設計 | 設計 | code が閾値で採否、Jev は確率を返す | 足切りと順位付けを分ける（:74-76）、E1（:86-87）、canary（:91-93） |
| `skills/review-to-lint` | reviewer の checklist のどれを script に移すか | 設計 | deterministic / semantic / hybrid | E1（:14-15）、E2（:66-67）、閾値を掘る前に固定（:37-38） |

### 判定を実行する skill / agent（harness）

| 資産 | 何を判定するか | 段 | 結論の形 | 書いている原則 |
|---|---|---|---|---|
| `agents/readme-judge.md` + `skills/readme-writer/references/readme-judge-checklist.md` | README が良い入口か | 観点 → 結論 | Publishable / Fix / Rewrite | P1（agent :98、checklist :7-8、:141-142）、P5（Phase A を凍結してから V・B、agent :57、:76、:87）、P2 の位置の偏り（agent :72-75）、E3（checklist :137）、E4（agent :93-96）、E5（recheck mode）。具体値: `model: opus`、「about 5」「3–5」「上限 2 ラウンド」 |
| `skills/readme-writer`（SKILL / tagline-eval / MAINTENANCE） | README の執筆の流れ、tagline の候補 | 設計 + 機械 + 人 | 本体は点なし。tagline は Borda の合計と 4 分の 3 の決着線（tagline-eval :56、:84） | P1（SKILL :61、:63）、P6（:231-233、:250-251）、E2（:192-193）、P3（別モデルは著者が求めたときだけ :252） |
| `skills/skill-writer` §4 §5 | skill の草稿が成り立つか、入れて振る舞いが変わるか | 観点 → 結論、人（§5 と §7） | Publishable / Fix / Drop。§5 は native eval の点と差 | P1（:149-150）、E2（:129-132）、E3、E4、E5（:148）、揺れ（`--runs 3` :157-158）。具体値: 「opus for judge-type agents」（:105）、「At most 2 rounds」 |
| `skills/learn-eval` Step 5 | セッションから抜いたパターンを残すか | 機械 → 観点 → 結論 → 人 | Save / Improve then Save / Absorb into [X] / Drop | P1（:162-164）、E3（:188-189）、E4（:157-161）、E5（:192-195）。判定は生成した同じ文脈（:166-170） |
| `skills/skill-stocktake` | skill ごとの品質と集合の重複 | 機械 → 観点 → 結論 → 人 | Keep / Improve / Update / Retire / Merge into [X] ほか | P1（:239-241）、E1（:43、:55-56、:192-197）、E2 と前の verdict を見せない（:170-172）、E4（:232-237）、食い違いは票でなく証拠で（:331-332）、平均しない（:150-151） |
| `skills/rules-stocktake` | rule ごとの常駐コストと失効 | 機械 → 観点 → 結論 → 人 | Keep / Improve / Update / Merge / Demote / Dissolve / Retire | P1（:132-133、skill-stocktake とほぼ同文）、E1（:94-98、同文）、E4（:115-125） |
| `skills/agent-stocktake` | agent 定義ごとの品質 | 同上 | Keep / Improve / Update / Merge / Demote / Dissolve / Retire | P1（:211-212）、E1（:186-190、skill-stocktake と同文）、E4（:198-209）、分解しすぎない（:195） |
| `skills/hook-stocktake` | hook ごとの配線・テスト・退役条件 | 機械 → 観点 → 結論 → 人 | Keep / Improve / Update / Merge ほか | 二値の確認（:52）、E4（:69-73）、発火数は証拠で結論にしない（:72-73） |
| `skills/repo-asset-stocktake` | repo の非コード資産に消費者がいるか | 機械（到達性）→ 観点 → 結論 | Keep / Update / Retire / Merge | P1（:53「No numeric score, no rubric, no aggregation into a grade」）、E1（:19）、E4（:66-68） |
| `skills/rules-distill` | skill に散った原則を rule に上げるか | 観点 → 結論 → 人 | Append / Revise / New Section / New File / Already Covered / Too Specific | 一つの文脈で全部読む（:36-40） |
| `skills/harness-stocktake` | 各 stocktake の結論を 1 本の report にまとめる | 設計（集約）、人 | 各 stocktake の verdict の語をそのまま運ぶ | 同じ skill への batch と probe の結論が割れたら著者が決める（:138-139）、対象はデータで指示ではない（:84-85） |
| `skills/search-first` | 外にある既存解・一次資料がこちらに当てはまるか | 結論（調べた者が書く） | Adopt ほか。文で書く | P1（:70-71「the canonical home of "evidence, not scores"」） |
| `skills/wiki-harvest` | wiki に戻す候補 | 観点、人 | 点や grade を付けない（:66） | P1 |
| `skills/generation-audit` | 世代交代で指示が runtime と衝突するか | 観点、人 | Conflict / Redundancy、確信度で適用を分ける | 別 session で再現を確かめてから処分（:55-56） |
| `skills/skill-comply` | skill・rule が実行時に守られているか | 機械（順序）+ LLM の分類 | 遵守率（%）、hook 昇格の推奨線 0.6（`prompts/spec_generator.md:24`） | P8（spec を固定して比較 :54-61）、E6（trust boundary）。具体値: haiku / sonnet の既定表（:141-147） |
| `skills/skill-health` | 参照切れ | 機械 | exit code、verdict なし | E1（:23-24） |
| `skills/persona-read-loop` + presets | 草稿が読み手に届くか | 観点（読み手 3 人）→ 人 | 理由の列。読み手の評価は受け入れ条件にしない（:17-19） | P6（:17-19、article preset :81-84）、P3 の限界（同系統 :161-162、自己優遇 :94-95）、P8（読み手とモデルを固定 :53）。具体値: 「three」「Three revisions」、article preset の sonnet / haiku / opus |
| `skills/headline-craft` | 入口の 1 行の候補と、本文が約束を回収するか | 観点（別 process の読み手）、人 | 点・順位・推奨を付けない（:93-94、:167） | P1、P4（選ぶのは著者）、E2（:102） |
| `skills/detail-loop` + references | 骨格のできた成果物の細部 | 機械（frozen checks）+ 観点（役割別 reviewer）+ 人 | Done / Stuck | P6 の一部（結論は著者の読みで閉じる :110）、E2（review.md :47-50）、好みを採点しない（units.md :109） |
| `skills/task-triage` §4 | build の出力を取り込むか | 機械 → 観点 → 結論、人（digest） | merge / bounce、台帳の state | E1（:241）、E2（:260）、独立性は fresh context から（:401-402） |
| `skills/implementation-chain` | どの review を回すか | 設計 | CRITICAL で停止 | E1、E2（:113）、P3（別モデルは opt-in、verdict は Claude :136-139） |
| `agents/architect.md` | 作るべきか | 結論 | Build / Don't build / Build smaller、点なし（:57） | P1、E2（:11-13）。具体値: `model: fable` と「判定は常に最強モデルで」（:6-8） |
| `agents/decision-history-reviewer.md` | 経緯の記録が成立しているか | 機械 → 観点 → 結論 | APPROVED / NEEDS REVISION / MAJOR ISSUES | E1（:34）、検出だけで直さない（:25） |
| `agents/security-reviewer.md` | diff の脆弱性 | 観点、結論は呼び出し側 | 重大度と確信度。件数表を出さない（:111） | 捨てずに全部返す（:91-92）、E1 |

### 執筆・論文の repo

| 資産 | 何を判定するか | 段 | 結論の形 | 書いている原則 |
|---|---|---|---|---|
| Z `skills/writing-ecosystem` + MAINTENANCE | reviewer panel の構成と指摘の処分 | 設計、人（内容 GO） | CRITICAL / MEDIUM / MINOR | P3（初見の読みは別系統 :132-133）、P6（修正を reviewer に読み直させない :166-171）、E2（brief を渡さない :137-138）。MAINTENANCE に P2・P7 の実測（:15-21、:47） |
| Z `agents/editor.md` / `essay-reviewer.md` | 稿の議論・構造・文体 | 観点 | 重大度、公開可否は出さない | 「チェックリスト適合は合格の証拠にならない」（editor :38）。`model: fable` |
| Z `agents/fact-checker.md` | 事実の主張 | 観点（主張ごとの verdict） | ACCURATE ほか 6 値 | 独立した経路で確かめる（:48） |
| Z `agents/prose-clarity-reviewer.md` | 初見の明瞭性（既定の読み手は Codex） | 観点 → 結論 | PASS / FAIL / BLOCKED、FAIL の条件あり（:103） | P3、E2（:16-17）、E3 |
| Z `skills/quality-gate` | 必要な report と検査が揃ったか | 機械 + 照合 | PASS / FAIL / BLOCKED | reviewer を起動せず上書きしない（:61） |
| Z `skills/article-stocktake`、`session-theme-mining` | 既存記事の tier、テーマ候補 | 機械 + 人 | 絶対スコアを出さない（:68）、選ぶのは著者 | P1、P4 |
| P `skills/paper-ecosystem`、`paper-writing` | paper の review panel と deposit 前の gate | 設計 | checklist（paper-writing :129-141） | 4 reviewer の並列（:93）、review + fix loop（:72、:79-80） |
| P `agents/paper-reviewer.md` ほか 4 本 | 議論・明瞭性・出典への忠実・用語・引用形式 | 観点 | reviewer ごとに別（verdict なし / PASS・FAIL / ALIGNED ほか / 件数） | 個別。`model:` は opus / sonnet / haiku |

## 重なり

同じ決まりが複数の文書に書かれている箇所。多い順。

| 決まり | 書いている場所 | 状態 |
|---|---|---|
| P1 点を集計しない・ホリスティック | llm-as-judge:12-39、:61-69 / skill-stocktake:239-241 / rules-stocktake:132-133 / agent-stocktake:211-212 / learn-eval:162-164 / skill-writer:149-150 / readme-judge:98 / checklist:7-8、:141-142 / readme-writer:61、:63 / architect:57 / headline-craft:93-94 / loop-design-check:22、:86、:157 / author-calibrated-eval:64-65 / evals.md / Z article-stocktake:68 | 18 か所（左の 15 に repo-asset-stocktake:53、search-first:70-71、wiki-harvest:66 を足す）。skill-stocktake と rules-stocktake と agent-stocktake はほぼ同文。理由を節として説明しているのは llm-as-judge だけで、一句の理由は skill-stocktake:240-241、headline-craft:93-94、readme-writer:63、checklist:141-142 にもある |
| E1 コードで確かめられることは先に | llm-as-judge:95-118 / skill-stocktake:43、:192-197 / rules-stocktake:64-65、:94-98 / review-to-lint:14-15 / skill-health:23-24 / decision-history-reviewer:34 / readme-writer:54 / task-triage:241 / loop-design-check:86 / author-calibrated-eval:70-72 / jev:86-87 / implementation-chain:106、:113 | 12 か所。「"Verify if it looks stale" is banned phrasing」は llm-as-judge:112-114・skill-stocktake:195-197・rules-stocktake:96-98・agent-stocktake:189-190 に同じ文。skill-writer:136-138 は同じ意味の別の文（「"only if it looks stale" is not an allowed condition」） |
| E2 判定者は書き手の文脈を持たない | readme-writer:192-193 / skill-writer:129-132 / skill-stocktake:170-172 / detail-loop review.md:47-50 / task-triage:260 / architect:11-13 / headline-craft:102 / persona-read-loop:91-94 / loop-design-check:86 / implementation-chain:113 / Z writing-ecosystem:137-138 / Z prose-clarity-reviewer:16-17 | 12 か所。理由の書き方がそれぞれ違う（sunk cost、anchoring、未定義語の補完、答えを持って読む） |
| E3 決定的な No・E4 反証の問い・E5 同じ問いで一度だけ | llm-as-judge:67-86 / skill-writer:147-150 / learn-eval:157-161、:188-195 / skill-stocktake:228-237 / rules-stocktake:115-125 / readme-judge:93-98 / checklist:137 | 7 か所。llm-as-judge の写しに近い。同じ二段（二値の確認 → 反証の問い）は agent-stocktake:186-209、hook-stocktake:52-73、repo-asset-stocktake:55-72 にもあり、合わせて 10 か所 |
| P6 直すループと評価を分ける | loop-design-check:86、:109 / author-calibrated-eval:37-38、:99-100 / persona-read-loop:17-19 / article preset:81-84 / readme-writer:231-233 / checklist:127-134 / readme-writer MAINTENANCE:20-23 / Z writing-ecosystem:166-171 / evals.md | 9 か所。一般則として書いた場所は無く、それぞれが自分の実測から書いている |
| 位置の偏りは順序を入れ替えて見る | readme-judge:72-75 / tagline-eval:71-72 / Z persona-read.md:37-42 / author-calibrated-eval:20-24 | 4 か所 |
| 読み手の隔離の手順（`--setting-sources ""` ほか） | tagline-eval:19-31 / readme-writer MAINTENANCE:42-43 / persona-read-loop MAINTENANCE:17-27 | 3 か所。実体は persona-read-loop の `scripts/read.sh` |
| 上限 2 ラウンド | skill-writer:150 / readme-writer:230 / checklist:127 | 3 か所 |

どこにも一般則として書かれていない原則:

- **P2**（ノイズとバイアスを分ける）。断片だけがある: 判定の揺れと同じ大きさの差を読まない（author-calibrated-eval:102-103）、
  `--runs 3` で揺れを見る（skill-writer:157-158）、Opus の判定器が両順で情報の多い版を選んだ（author-calibrated-eval:20-24。繰り返しでは消えない癖の実例）、
  書式の量は人にも LLM にも好まれる（checklist:135-136）
- **P4**（下限は合議、上限は一つの目）。形として実装した場所はある: author-calibrated-eval:14-18、jev:74-76、tagline-eval の段 1 と段 2・3、headline-craft:167
- **P5**（全体と観点の順序）。llm-as-judge:19-22 は点を避ける理由として触れるだけ。順序を決めているのは readme-judge の Phase 凍結だけ。
  観点を見ない全体の判断を先に取る手順はどこにも無い
- **P7**（揺れの点検は大きさだけ）。無い。近いのは Z writing-ecosystem MAINTENANCE:47（各 3 回走らせて反転した指摘を著者が見る）

## 食い違い

| # | 論点 | 一方 | もう一方 | 当たる原則 |
|---|---|---|---|---|
| 1 | 判定者の独立性はどこから来るか | task-triage:401-402「fresh context から来る。別モデルからではない」 | Z writing-ecosystem:132-133「初見の読みは別系統のモデル。同じ系統は同じ所を読み飛ばす」、persona-read-loop:161-162（同系統は独立した標本でない） | P3 |
| 2 | 判定者のモデル | architect:6-8「判定は常に最強モデルで」、`model: fable` | skill-writer:105「opus for judge-type agents」、readme-judge・decision-history-reviewer・security-reviewer は `model: opus` | P9 |
| 3 | 入口の 1 行を点で選ぶか | headline-craft:93-94、:167「点数を付けない。順位・点数・推奨は付けない」 | tagline-eval:56 Borda の合計、:84「4 分の 3 以上勝ったら決着」で推奨を出す（headline-craft:180 が参照する） | P1、P4 |
| 4 | verdict を数で合否にするか | llm-as-judge:39「Yes の割合を品質の指標にしない」 | loop-design-check:146「Pass line fixed in advance: 2 of 3 Publishable」、同行「against a rubric, one line of evidence per axis」 | P1 |
| 5 | 直したあと reviewer に読み直させるか | Z writing-ecosystem:166-171「読み直させない。読むたびに新しい指摘が生まれて終わらない」、readme-writer:233「新しい質問での再実行はしない」 | P paper-ecosystem:72、:79-80「review pass + fix loop」「並列 review を再実行」、detail-loop:104-105（最新の review に新しく採るものが無いことを Done の条件にする。毎回新しい reviewer を立てるのは `references/review.md`:48-50。同じ Done の条件に著者の読みも入る :106-110） | P6 |
| 6 | 判定は書き手と別の文脈か | skill-writer:129-132（fresh subagent） | learn-eval:166-170（別文脈の指定が無いので、生成した同じ文脈で判定すると読める。Save と Absorb は著者の承認 :197-207 を通り、別文脈のゲートは Promote だけ :212-216） | E2、P5 |
| 7 | 再実行を結論に使うか | generation-audit:55-56「別 session で同じ文言が再現することを確かめてから処分を確定」、readme-judge:72-75「両順が一致したときだけ improved」 | P7 は結論を一回目のまま残す | P7（順序の入れ替えは偏りへの対策で、揺れの点検とは別に扱える。下の Still unknown） |
| 8 | 遵守率と昇格線 | llm-as-judge:39 | skill-comply は遵守率（%）を出し、0.6 未満で hook 昇格を勧める（`scripts/grader.py:162`）。MAINTENANCE:52-53 は「informational」 | P1（測っているのは品質でなく守られた割合。結論には使っていない） |
| 9 | 読み手のモデルの書き方 | persona-read-loop `presets/readme.md`:24-25（モデル名を書かず、読みの深さで選ぶ） | `presets/article.md`:16-18（sonnet / haiku / opus を名指し）、tagline-eval:26（`--model sonnet` 固定） | P9 |
| 10 | 一括で読むか分けて読むか | skill-stocktake:169-170（10–12 件ずつ。文脈が埋まると注意が薄まる） | rules-stocktake:14、:59（全部を一つの文脈で。規模が小さいから） | 食い違いではなく規模の違い。llm-as-judge:115-116 が両方を説明している |
| 12 | P1 の正本を名乗る場所 | search-first:70-71「the canonical home of "evidence, not scores"（ADR-0026）」 | skill-stocktake:430「llm-as-judge — the generic judge design canon」、readme-judge:20「判定形式の正本: llm-as-judge」 | P1（正本が二つ名乗られている） |
| 11 | 迷ったときの既定 | review-to-lint:54「When unsure, lean to semantic」 | skill-writer:94-96「条件を並べたあとに tie-breaker を足さない」 | 判定の原則の外（書き方の規約） |

記述と実物の食い違い（判定の原則とは別）:

- `skills/skill-writer/SKILL.md:147` — 「1–3 counter-questions for a non-Keep」。同じ節の verdict は Publishable / Fix / Drop で、Keep は skill-stocktake の語彙
- P `agents/paper-reviewer.md:17`、`clarity-reviewer.md:21`、`source-fidelity-checker.md:17`、`vocabulary-consistency-checker.md:17`、`citation-formatter.md:17` —
  正本を `~/.claude/skills/paper-ecosystem/SKILL.md` と書くが、実物は P `skills/paper-ecosystem/SKILL.md`
- P `skills/paper-writing/SKILL.md:133`、:135 — paper-reviewer と vocabulary-consistency-checker の「pass」を条件にするが、両 agent の出力に pass / fail が無い
- P `agents/clarity-reviewer.md:87` — PASS / FAIL を出すが FAIL の条件が無い
- P `agents/paper-reviewer.md:19` と P `skills/paper-ecosystem/SKILL.md:93` — 並列で回す 4 本の顔ぶれが違う（citation-formatter を含むか clarity-reviewer を含むか）
- P `skills/paper-ecosystem/SKILL.md:172` — `references/style-diagnostics.md` は P に無い（実物は Z `skills/writing-ecosystem/references/`）
- Z `agents/fact-checker.md:58-65` と :75 — verdict の語彙に ⚪ があるが、Report の Verdict 行に無い

## 関連する過去の記録

- `skills/measurement-discipline` は 2026-11-08 に global から外した（9de937f、b250993）。commit の本文の理由は、9 原則のうち 5 つ（§1 §2 §4 §5 §8）が現行モデルが skill 無しで当てる統計の常識で、
  Contemplative Agent の外では「n を決めてから言え」の側へ引いていたこと。捨てたのではなく、Contemplative Agent の計器で測った罠は同 repo の project skill へ移した。
  参照は各 skill のその場の 1 文に直した。共通の原則文書を作るときの先例になる
- `docs/plans/holistic-eval-layer.html`（2026-10-18 commit、bfb1bde）— 点数の無い評価層（`/eval-panel`、観点の入れ替え、隠した観点、割れを全件返す、ledger）の plan。
  `skills/eval-panel` は履歴に無く、実装されていない。「割れを統合せず残す」「結果を見ない判定」は今回の P3・P6 と同じ向き
- [RFC-0034](../../../rfcs/0034-llm-as-judge-definition-search.md)（blocked）— llm-as-judge の問いと verdict の定義を仮説として比べる外側ループ。「問題設定を動かすほど評価は固定する」は P8 と同じ向き
- 公開の形（`skills/harness-sync/SKILL.md:248-274`）: 今回の対象のうち単独 skill の repo としても公開しているのは 10 本 —
  `llm-as-judge`、`persona-read-loop`、`skill-comply`、`readme-writer`（readme-judge を同梱）、`skill-health`、`learn-eval`、`skill-stocktake`、`rules-stocktake`、
  `agent-stocktake`、`generation-audit`。ほかに plugin が 2 つある: harness-stocktake（skill-writer と stocktake 系を含む、:257）と akc-cycle（固定の allowlist、:256）。
  ほかの skill への参照は、その repo では届かない。llm-as-judge の Related 節は、installed でない対象（AKC の ADR、:172-176）を URL で、installed の skill（:177-182）を名前だけで引いている

## Still unknown

- 順序の入れ替え（readme-judge:72-75、tagline-eval:71-72）を P7 の「揺れの点検」に含めるか。主ループの読みは、位置の偏りは P2 のバイアスで、入れ替えはその対策なので P7 の外
- skill-comply の遵守率を P1 の対象に含めるか（品質の点ではなく、守られた割合の計測）
- grep で拾って前後だけ読んだ 7 本（上の「範囲と読み方」）に、拾った語を使わない判定の記述があるか
- `agents/*.md` の `model:` を P9 の「書かない細部」に含めるか（frontmatter は配線で、省くと session の model を継ぐ）

kind: internal
# State of Claude Code Harness Hygiene 2026 — 既存記録だけの集計（n = 20）

as-of: 2026-11-01。plan [enumerated-petting-beaver](../enumerated-petting-beaver.md) Stage 3 手順 1。新しい run・clone・外部への
問い合わせはしていない。材料は [premise-test](2026-11-01-premise-test.md)・[premise-test-prediction](2026-11-01-premise-test-prediction.md)・
[doctor-comparison](2026-11-01-doctor-comparison.md)・[precision](2026-11-01-precision.md)・[rerun](2026-11-01-rerun.md)・
[stage1-plugin](2026-11-01-stage1-plugin.md)・[ADR-0097](../../decision-history/0097-batch-stocktake-report-and-two-decisions.md)。
同じ内容の CSV（repo 名なし、n < 10 の値は伏せる）: [state-of-2026/aggregate.csv](state-of-2026/aggregate.csv)。
CSV で伏せたセルは 23 個（分母 < 10）: native の agents・docs・rules・distill の 4 行、skills < 10 と ≥ 25 の群、plugin の秒数 2 行、
×予測の一致（分母 1）、正答率の source 別 14 行。伏せた行も分母と `suppressed=n<10` は残す。

出典は `file:line`（file は上の略名、`plan` は親 plan）。計算した値は式と元の数字を書く。分母はすべて書く。

## 結論

- 公開 20 本の非 Keep は 789 件 / 全項目 1979 件（39.9%）。source 別に「非 Keep が 1 件以上出た run」は docs・skills・assets が
  19/20、distill 18/20、hooks 12/20、agents 10/20、rules 2/20
- native（`/doctor` 系）に拾われない非 Keep は 48/74（65%）。**ただし著者の harness 1 本（n = 1）の数字で、公開 20 本では測っていない**
- harness が大きいほど非 Keep の件数は多い（skills 数との Spearman ρ = 0.62、n = 20）が、非 Keep の**割合**とはほぼ無関係（ρ = 0.06）
- 見立ては見ていない 10 本で 9/10 的中。ただし「全部 ○」と言うだけでも 9/10 になり、唯一の × 予測（P18）は外れた
- 最初の非 Keep まで: Stage 0 中央値 134.5 秒（20 本、180 秒以内 18/20）、再走 138 秒（14 本、180 秒以内 11/14）、plugin 89 秒（persona 3 体、sample harness）
- 正答率（中心の主張）57/60 = 95%、細部まで 40/60 = 67%（24 run から層別抽出、照合役は Claude の別 model）
- n = 20 は一つの検索 query から選んだ 20 本で、母集団の推定ではない。以下の数字は「この 20 本では」としか言えない

## 対象と条件

| 項目 | 値 | 出典 |
|---|---|---|
| 選定 query | GitHub code search `filename:SKILL.md path:.claude/skills`、9 ページ（696 ファイル、662 repo） | premise-test:22 |
| 絞り込み | seed 20261101 で shuffle、fork・archive でない、2026-08-03 以降に push、300 MB 以下、`.claude/skills` 直下に skill dir 5 本以上、著者の repo と ECC の mirror を除外 → 26 本（P01–P20 を使用、P21–P26 は予備で未使用） | premise-test:22-24 |
| Claude Code の版 | 2.1.316、`--model opus`、timeout 1800 秒、並列 3 | premise-test:34-35、rerun:25、stage1-plugin:4、doctor-comparison:4 |
| 実行日 | 2026-11-01（各 report の as-of。native 比較の対象は 2026-10-31 の初回全体実行） | premise-test:4、doctor-comparison:4,24 |
| 非 Keep の定義 | Keep / Out of scope / Already Covered / Too Specific 以外 | premise-test:37-38 |
| 母集団 | 公開 20 本（P01–P20）。正答率だけは公開 20 + 著者 4 の 24 run | premise-test:43-69、precision:5-6 |

## 1. source 別の非 Keep 率（公開 20 本）

元の数字は premise-test:50-69 の「source 別」列（P01–P20 の 20 行）。source ごとの項目数（分母となる全項目の source 内訳）は記録に
無いので、source 内の「非 Keep / 項目」は出せない。代わりに precision:104 の定義（非 Keep が 1 件以上出た run の割合と、run あたり
件数の中央値）で出す。

| source | 1 件以上出た run | 率 | 非 Keep 計 | 非 Keep 全体に占める割合（計 / 789） | run あたり中央値（20 本） |
|---|---|---|---|---|---|
| hooks | 12/20 | 60% | 35 | 4.4% | 1 |
| docs | 19/20 | 95% | 85 | 10.8% | 4 |
| agents | 10/20 | 50% | 73 | 9.3% | 0.5 |
| distill | 18/20 | 90% | 72 | 9.1% | 2.5 |
| skills | 19/20 | 95% | 346 | 43.9% | 6.5 |
| assets | 19/20 | 95% | 168 | 21.3% | 8 |
| rules | 2/20 | 10% | 10 | 1.3% | 0 |
| 計 | — | — | 789 | 100% | — |

- 計 789 は premise-test:71 の「非 Keep 789 件」と一致（20 行の source 別の和 = 各行の「非 Keep」列の和 = 789、行ごとの不一致 0）
- 24 run（著者 4 を足す）での「出た run」は premise-test:136-142 に hooks 12/24・docs 23/24・agents 13/24・distill 21/24・skills 22/24・
  assets 23/24・rules 3/24。上の 20 本の値に著者 4 本（premise-test:89-92）を足すと全 source で一致する
- skills の 346 のうち 209 は P16 の 1 本（premise-test:65,74-75。ほぼ一つのパターン）。P16 を除く 19 本では skills 137 / 非 Keep 543 = 25.2%（137 = 346 − 209、543 = 789 − 246）
- 全体の非 Keep 率: 789 / 1979 = 39.9%（1979 = premise-test:50-69 の「項目」列の和）。run ごとの 非 Keep / 項目 の中央値は 29.9%
  （最小 P10・P13 の約 10%、最大 P16 の 75.5%）

## 2. native に拾われない項目の割合（著者の harness、n = 1）

元の数字は doctor-comparison:56-129（非 Keep 74 行）。対象は著者の 2026-10-31 初回全体実行の 192 項目（doctor-comparison:24）で、
**公開 20 本ではない**（doctor-comparison:48「n = 1（著者の harness）。他人の harness で native と比べるのは Stage 3」。Stage 3 は
改訂で新しい run を持たない — plan:216-218 — ので、公開 20 本での比較は無い）。分類は LLM（opus）の判定で、人が全件を見たのは
抜き取り 8 件（doctor-comparison:44-45）。

| source | 非 Keep | 実測: 拾われない | 実測: 部分 | 実測: 拾われる | 拾われない率 |
|---|---|---|---|---|---|
| assets | 23 | 22 | 1 | 0 | 96% |
| skills | 24 | 6 | 18 | 0 | 25% |
| hooks | 12 | 11 | 1 | 0 | 92% |
| agents | 6 | 2 | 4 | 0 | 33% |
| docs | 4 | 3 | 1 | 0 | 75% |
| rules | 3 | 2 | 1 | 0 | 67% |
| distill | 2 | 2 | 0 | 0 | 100% |
| 計 | 74 | 48 | 26 | 0 | **65%**（48/74） |

- 計は doctor-comparison:8 と一致。source 別は表の 74 行を数え直した値（assets 22/23・hooks 11/12・docs 3/4・distill 2/2・skills 部分
  18/24 は doctor-comparison:11-12 と一致）
- 「機能」（native の検査範囲として拾える種類か）で数えると 拾われる 7 / 部分 20 / 拾われない 47 = 64%（47/74、doctor-comparison:9）
- 逆向き: native の harness 自体への指摘 28 件のうち stocktake が拾ったのは 2、部分 4、拾っていない 22（doctor-comparison:14-15）

## 3. harness の大きさと非 Keep 件数（公開 20 本）

元の数字は premise-test:50-69 の「規模」（skills / agents / hooks / CLAUDE.md 行）・「項目」・「非 Keep」。

Spearman の順位相関 ρ（同順位は平均順位、ρ = 順位どうしの Pearson 相関）、n = 20:

| 大きさの指標 | ρ（非 Keep 件数） | ρ（P16 を除く、n = 19） |
|---|---|---|
| skills 数 | 0.62 | 0.56 |
| agents 数 | 0.53 | 0.67 |
| hooks 数 | 0.27 | 0.40 |
| CLAUDE.md 行 | 0.46 | 0.46 |
| skills + agents + hooks | 0.75 | — |
| 全項目数 | 0.80 | 0.77 |
| skills 数 → **非 Keep / 項目（割合）** | 0.06 | — |

- 全項目数は非 Keep を含むので、この ρ は一部が定義上の重なり。大きさの指標としては skills / agents / hooks を見る
- 大きい harness は非 Keep が**多い**が、項目に対する**割合**は大きさとほぼ関係しない（ρ = 0.06）

skills 数で 3 つに分けた中央値（CSV では n < 10 の 2 群を伏せる）:

| skills 数 | run 数 | 非 Keep 中央値 | 該当 |
|---|---|---|---|
| < 10 | 5 | 10 | P07・P10・P15・P18・P20 |
| 10–24 | 10 | 28.5 | P02–P06・P08・P09・P12・P14・P17 |
| ≥ 25 | 5 | 43 | P01・P11・P13・P16・P19 |

precision:115-116 は、見立ての代わりにこの関係を散布図で出す案を書いている。散布図の点（20 本の規模と件数）は premise-test:50-69 に
すでにある。CSV には run ごとの行を入れていない（集計値だけ）。

## 4. 見立ての的中率（見ていない 10 本）

見立て「skills < 10 かつ agents < 5 かつ hooks < 5 かつ CLAUDE.md < 50 行のときだけ驚きが出ない」は P01–P10 だけから作り、P11 以降を
回す前に commit d327ef6 で固定した（premise-test-prediction:5,26、premise-test:101-102）。

| 指標 | 値 | 分母 | 出典 |
|---|---|---|---|
| 一致 | 9 | 10（P11–P20） | premise-test:104-117、premise-test-prediction:34-46 |
| 事前の閾値 | 8 本以上 | 10 | premise-test-prediction:47-48 |
| ○（驚く）予測の一致 | 9 | 9 | premise-test:106-115 |
| ×（驚かない）予測の一致 | 0 | 1（P18） | premise-test:113 |
| 比較: 「全部 ○」と言った場合の一致 | 9 | 10 | premise-test:117-118（P11–P20 の結果がすべて ○ のため） |
| 驚きが出た run（公開 20 本） | 19 | 20 | premise-test:10、premise-test:50-69 の「≤600 s」列が 5 以上の行の数と一致 |

9/10 は事前の閾値を越えるが、「全部 ○」と同じ一致数で、見立ての中身（小さい harness だけ驚かない）は P18 で反例が出た
（premise-test:117-119）。驚きの閾値 5 件は 20 本中 19 本が越え、ほぼ区別しない（premise-test:17）。

## 5. 最初の非 Keep の指摘までの秒数

| 段階 | 対象 | 中央値 | 範囲 | 180 秒以内 | 出典 |
|---|---|---|---|---|---|
| Stage 0 | 公開 20 本 | 134.5 秒 | 75–199 | 18/20 | premise-test:13,129、premise-test:50-69「非 Keep」列 |
| 再走（品質修正後） | Stage 0 の 14 本 | 138 秒 | 104–214 | 11/14 | rerun:55、rerun:39-52「非 Keep」列 |
| 比較: Stage 0 の同じ 14 本 | 同上 | 134.5 秒 | — | — | premise-test:50-69 から P12・P14・P15・P17・P18・P20 を除いた 14 値 |
| plugin（Stage 1） | sample harness、persona 3 体 | 89 秒 | 88–90 | 3/3 | stage1-plugin:8-9,29-33 |
| plugin bench | sample harness、1 回 | 87 秒 | — | 1/1 | stage1-plugin:10 |

- 中央値は表の値の並べ替えで再計算し、記録と一致（Stage 0: (134 + 135) / 2、再走: (137 + 139) / 2）
- 計り方が段階で違う: Stage 0 と再走は `run/items-<source>.json` に非 Keep が現れた時刻（poller の `timeline.tsv`、premise-test:37,40-41、
  rerun:29）。plugin は「最初の非 Keep の section」まで（stage1-plugin:8）で、対象は公開 repo でなく sample harness。三つを並べて
  「速くなった」とは言えない
- 参考: report.md が 10 分以内に揃ったのは Stage 0 12/20（premise-test:13）、再走 11/14（Stage 0 の同じ 14 本では 8/14、rerun:14）

## 6. 正答率（中心の主張 60 件）

24 run（公開 20 + 著者 4）の非 Keep 855 件から source 別に層別抽出した 60 件を、監査した opus とは別の model（fable）が隔離して
repo と照合した（precision:5-6,22-24,36-40）。正答 = claims が correct か partly、かつ verdict_supported が yes（precision:42）。

| source | 母集団 | 抽出 | 正答 | 厳密（細部まで） |
|---|---|---|---|---|
| hooks | 35 | 9 | 8/9 | 6/9 |
| docs | 97 | 9 | 9/9 | 4/9 |
| agents | 83 | 9 | 8/9 | 6/9 |
| distill | 79 | 9 | 8/9 | 4/9 |
| skills | 361 | 9 | 9/9 | 8/9 |
| assets | 189 | 9 | 9/9 | 7/9 |
| rules | 11 | 6 | 6/6 | 5/6 |
| 計 | 855 | 60 | **57/60 = 95%** | 40/60 = 67% |

出典: precision:26-34（母集団・抽出）、precision:49-58（結果）、precision:10-15（結論）。

- 母集団の重み付き（記録は約 97% / 約 74%、precision:10-11,13-14）を再計算: 正答 = Σ 母集団 × source の正答率 / 855 =
  (35·8/9 + 97 + 83·8/9 + 79·8/9 + 361 + 189 + 11) / 855 = 833.1 / 855 = 97.4%。厳密 = (35·6/9 + 97·4/9 + 83·6/9 + 79·4/9 +
  361·8/9 + 189·7/9 + 11·5/6) / 855 = 633.9 / 855 = 74.1%。記録と一致
- 母集団 855 = 公開 20 本の 789（premise-test:71）+ 著者 4 本の 22 + 20 + 16 + 8（premise-test:89-92）。一致
- 中心が外れた主張は 0/60。外れ 3 件は確かめられない主張 1・verdict への異論 2（precision:18,66-70）
- 95% 区間の下限は全体でおよそ 86%、source 別は 9/9 でもおよそ 66%。項目は 22 run に集まり独立でないので実際の区間はもっと広い
  （precision:121-123）。source 別の率は CSV で伏せる（すべて n < 10）
- judge の再現性: decidable の一致 94.8%（854 件、κ 0.73、precision:16-17）

## 著者の harness（ADR-0097）

| 指標 | 値 | 出典 |
|---|---|---|
| 初回全体実行の項目 | 192（7 source） | doctor-comparison:24、plan:12 |
| 非 Keep | 74 | doctor-comparison:8、plan:12 |
| 著者の判断の回数（設計） | 棚卸し 1 回につき 2 回（report の承認と ff 取り込み） | ADR-0097:48-49,102 |
| 著者の判断の回数（初回の観測） | 2 回 | plan:12（ADR-0097 にはこの観測は無い。下の「食い違い」7） |

n = 1。著者の驚きは測定器にしない（plan:71-72）。

## 参考: 費用（`total_cost_usd`、API 換算）

すべて subscription の枠で回しており、請求額ではない（premise-test:71-72、doctor-comparison:30）。

| 対象 | 値 | 出典 |
|---|---|---|
| Stage 0 公開 19 本（P19 は timeout で未記録） | 計 $182.16、1 本 $3.68–20.73、中央値 $8.50（19 値の 10 番目） | premise-test:50-69,71 |
| 再走 14 本 | 計 $193.65、最大 $31.78（P16、skills 383 本） | rerun:39-52,56 |
| plugin bench（sample harness） | $4.08 | stage1-plugin:10 |

## 記録の中の食い違い

1. **「3 分は成り立つ」と再走の分布。** rerun:55 は中央値 138 秒で「3 分の目標は変わらず成り立つ」と書くが、14 本中 3 本（185・199・
   214 秒）が 180 秒を越え、180 秒以内は 11/14 = 79%。precision:112 の目安（最初の項目 3 分以内が 80% 以上）を僅かに下回る。Stage 0 は
   18/20 = 90%
2. **native 比較の母集団。** premise-test:12 は「native に拾われない項目は非 Keep の 65%」を公開 20 本の結論の列に並べるが、元の
   doctor-comparison は著者の harness 1 本（doctor-comparison:48）。記事で「公開 20 本の 65%」と読める書き方はできない
3. **「50 本」の前提が残っている。** premise-test:17-18 と precision:102-116 は Stage 3 を 50 本で行う前提で指標を提案している。plan:216-218 の
   改訂（2026-11-01）で 50 本の計測は行わない
4. **Stage 3 の判定基準。** precision:100 は Stage 3 判定を「見立ての的中率 70% 以上なら対象を書く」と引用し、的中率を判定から外す案
   （precision:115-116）を出している。改訂後の plan:217-218 は的中率を使うと書き、plan:245-246 の判定は「当たった範囲だけを書く」
5. **decidable の率の分母。** premise-test:71 は 712/789 = 90%（公開 20 本）、precision:61 は 1 回目 89.5%。後者は著者 4 本を含む
   764/854（= 712 + 52、比較対象 854 件）で、矛盾ではないが分母が違う
6. **最初の非 Keep の計り方。** Stage 0 / 再走は items JSON の出現、plugin は section の出現（上の 5）。Stage 0 でも P01（section 111・
   非 Keep 107 秒）と P15（149・145 秒）は最初の非 Keep が最初の section より前にある（premise-test:50,64）ので、二つの時刻は同じではない
7. **「192 項目 → 判断 2 回」の出典。** plan:228 は ADR-0097 を出典に挙げるが、ADR-0097 にあるのは判断を 2 回にする設計
   （ADR-0097:48-49,102）で、192 という数も初回で 2 回に収まった観測も書かれていない。192 は doctor-comparison:24、観測の 2 回は plan:12 にだけある
8. **初回実行の所要時間。** plan:12 は「開始から report まで約 30 分」、premise-test:123-124 は 23:10 → 23:43 の「約 33 分」
9. **版による件数の変化。** 再走の 14 本の非 Keep は計 502、Stage 0 の同じ 14 本は 634（rerun:39-52 と premise-test:50-69 から計算）。
   修正後の skill は同じ repo で非 Keep が少なく出る（fold で束ねるため、rerun:16-17,60-74）。この集計の率は Stage 0 の skill の値で、
   公開版の plugin の値ではない

## 記事の「一つの数字」の候補（決めるのは著者）

| 候補 | 根拠のセル | 弱点（n = 20 / n = 1 で言い過ぎになる点） |
|---|---|---|
| A. 「`/doctor` 系が拾わない指摘が 74 件中 48 件（65%）」 | 表 2 の「計」行 | 公開 20 本ではなく著者の harness 1 本。分類は LLM で、人の確認は抜き取り 8 件。逆向き（native だけが出す 22 件）を一緒に書かないと「`/doctor` の代わり」と読まれる（doctor-comparison:14-17） |
| B. 「中心の主張 60 件中 57 件が repo の事実と合った（95%）」 | 表 6 の「計」行・正答 | 照合役も Claude 系の model 1 回。60 件は 22 run に集まり独立でなく、下限およそ 86% よりも区間は広い。細部まで正しいのは 40/60（67%）で、95% だけを出すと過大に読める。24 run には著者の 4 本が入る |
| C. 「最初の指摘まで中央値 134.5 秒（20 本中 18 本が 3 分以内）」 | 表 5 の Stage 0 行 | Stage 0 の skill の値で、修正後の再走では 180 秒以内が 11/14（79%）に落ちる。plugin の 89 秒は sample harness・persona 3 体で、計り方も違う（食い違い 1・6）。一つの query から選んだ 20 本の分布で、他の harness の速さは言えない |

候補にしなかった数: 「20 本中 19 本で驚きが出た」（表 4 の最終行）— 閾値 5 件がほぼ区別しない（premise-test:17）ので、測定器の性質を
言う数になる。「大きい harness ほど指摘が多い（ρ = 0.62）」— 割合では ρ = 0.06 で、「大きいほど荒れている」とは言えない。

## 限界

- n = 20 は一つの検索 query・一つの seed・`.claude/skills` 形式の repo だけ（premise-test:22-24,160）。plugin 形式の harness は入っていない
- 監査・judge・照合・native の分類はすべて Claude 系 model の判定。持ち主の判断ではない（precision:120,125）
- source 内の項目数が記録に無いので、source 別の「非 Keep / 項目」は出せない（表 1 は run 単位の率）
- P16・P19 は report.md が無く、judge の入力の形が他と違う（premise-test:161）

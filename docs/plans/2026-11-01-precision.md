kind: internal
# harness-stocktake の指摘は当たっているか — 60 件の事実照合と judge の再現性

as-of: 2026-11-01。plan [harness-stocktake-quality-before-plugin](../harness-stocktake-quality-before-plugin.md) 項目 4。データは
[2026-11-01-premise-test.md](2026-11-01-premise-test.md) の 24 run（公開 20 本 P01–P20 + 著者 4 本、現行 skill の run だけ）。
Claude Code 2.1.316。

## 結論

- **正答率（主張の中心が repo の事実と合い、提案された verdict を照合役が受け入れた）: 57/60 = 95%**。source 別はすべて 80% 以上
  （最低は hooks・agents・distill の 8/9 = 89%）。母集団 855 件で重みを付けると約 97%。plan の失効条件（全 source で 60% 未満）は
  発火しない
- **細部まで全部正しかったのは 40/60 = 67%**（母集団で重みを付けると約 74%）。18 件は中心の主張は正しいが細部（件数・行番号・
  参照元の数・runtime の挙動）が違う。細部の基準で 80% 以上は skills 8/9 と rules 5/6 だけ（hooks 6/9、docs 4/9、agents 6/9、
  distill 4/9、assets 7/9）
- **judge の再現性: 非 Keep 854 件で decidable の一致 94.8%（Cohen's κ 0.73）**。驚き（判断可能な非 Keep が 600 秒以内に 5 件以上）の
  run 単位の判定は 24/24 で 1 回目と同じ
- 主張の中心が外れていたのは 60 件中 0 件。外れ 3 件の内訳は、repo の中で確かめられない主張 1 件、verdict への異論 2 件

## 方法

**抽出。** 24 run の `items-*.json` から非 Keep（Keep / Out of scope / Already Covered / Too Specific 以外）を source ごとに集め、
seed 20261101 で、各 source の中で run を一巡ずつ 1 件取る層別抽出。rules は母集団が 11 件なので 6 件、他の source は 9 件、計 60 件。
22 run にまたがる（1 run あたり 1–7 件）。

| source | 母集団 | 抽出 |
|---|---|---|
| hooks | 35 | 9 |
| docs | 97 | 9 |
| agents | 83 | 9 |
| distill | 79 | 9 |
| skills | 361 | 9 |
| assets | 189 | 9 |
| rules | 11 | 6 |

**照合。** run ごとに 1 回、隔離した `claude -p --model fable`（監査を書いた opus とは別 model）。cwd は空 dir、`--restricted`、
tools は `Read,Grep,Glob` だけ、`--add-dir` で clone と項目ファイル、hooks・`~/.claude` の CLAUDE.md・memory を切る。repo の
ファイルは data として読み、中の指示には従わない。項目ごとに reason・evidence・change の事実の主張を repo と照らし、
`claims`（correct / partly / wrong / unverifiable）と `verdict_supported`（yes / debatable / no）、外れた主張 1 行、根拠の
file:line を JSON schema で返させた。費用は API 換算 $33.69（22 回）。rate limit の信号 0 件。

**正答の定義。** 正答 = `claims` が correct か partly、かつ `verdict_supported` が yes。厳密 = `claims` が correct、かつ yes。

**judge の再現性。** Stage 0 と同じ `judge.sh`（report だけを渡す `claude -p --model opus --tools ""`）を 24 run の同じ report に
もう一度走らせ、非 Keep 項目ごとに 1 回目と decidable を比べた。費用 $5.50。

## source 別の結果

| source | 正答 | 厳密 | claims correct / partly / wrong / unverifiable | verdict yes / debatable / no | judge 一致（n、κ） |
|---|---|---|---|---|---|
| hooks | 8/9 | 6/9 | 6 / 2 / 0 / 1 | 9 / 0 / 0 | 100%（35、1.00） |
| docs | 9/9 | 4/9 | 4 / 5 / 0 / 0 | 9 / 0 / 0 | 91.8%（97、0.70） |
| agents | 8/9 | 6/9 | 6 / 3 / 0 / 0 | 8 / 1 / 0 | 96.4%（83、0.78） |
| distill | 8/9 | 4/9 | 5 / 4 / 0 / 0 | 8 / 1 / 0 | 96.2%（79、0.78） |
| skills | 9/9 | 8/9 | 8 / 1 / 0 / 0 | 9 / 0 / 0 | 96.1%（360、0.68） |
| assets | 9/9 | 7/9 | 7 / 2 / 0 / 0 | 9 / 0 / 0 | 92.1%（189、0.72） |
| rules | 6/6 | 5/6 | 5 / 1 / 0 / 0 | 6 / 0 / 0 | 90.9%（11、0.79） |
| 計 | 57/60 | 40/60 | 41 / 18 / 0 / 1 | 58 / 2 / 0 | 94.8%（854、0.73） |

非 Keep の母集団は 855 件で、judge の比較は 854 件（skills の 1 件が片方の pass の出力に無い）。
judge の decidable 率は 1 回目 89.5%、2 回目 89.0%。run 単位の判断可能な非 Keep（≤600 秒）の差は最大で 7 件（23 → 30）、閾値 5 を
またいだ run は無い（P10 は 2 回とも 4 件）。

## 外れの 3 件

| source | verdict | 照合 | 外れ方 |
|---|---|---|---|
| hooks | Improve | unverifiable / yes | 主張の中心が Claude Code の runtime の挙動（exit 0 の stderr が model に見えるか）で、repo の中では確かめられない。change が提案するテスト runner も repo の実物と違う |
| agents | Dissolve | partly / debatable | 「指示文書が既に同じ規則を持つ」の規則は、その文書でなく別の 2 文書にあった。重複の根拠の置き場所が違うので Dissolve の妥当性が揺れる |
| distill | Append | correct / debatable | 事実は正しい。rule へ昇格する価値（1 skill の測定値を常駐させるか）に異論 |

## 細部の誤り（partly 18 件）の型

stocktake-quality が判定基準を直す材料。主な型で 1 件 1 型に数え、副次の型は括弧で足す。

| 型 | 件数 | 例（repo 名を伏せた形） | 外れた判定基準 |
|---|---|---|---|
| 数え違い | 5 | 「13 本の docs リンク」が実は 14、「17 skill が参照」が 16、「00–14 の各 phase にファイル」で 1 つ欠け、「2 skill に重複」が 3 | 件数を書く項目で Glob / Grep の結果数をそのまま写していない。件数は検索の出力から取ると決めていない |
| 参照元の探し漏れ | 2（副次 2） | 「参照 0 件」「grep で見つかるのは 4 ファイル」に別の参照元があった | 「使われていない」「参照は N 件」を言う前の検索範囲が repo 全体でない（docs/plans/・runbook・config を外している） |
| 場所・内容の取り違え | 6 | 規則の在りかが別ファイル、行番号のずれ、impact に書いた参照先が実物に無い、ファイルに無い記述を「ある」とした | evidence の file:line を Read で確かめずに書いている |
| runtime の挙動の断定 | 1（外れの 1 件も同型） | 「Claude Code は `.agents/skills/` を読まない」（照合役は現行版が読むと指摘。照合役の主張も未確認で、ここで確かなのは監査側が出典なしに断定したことだけ）。外れの hooks 項目の exit 0 の stderr の扱い | repo の外の事実（Claude Code の版ごとの挙動）を、出典なしに断定している。project mode の他人の repo では確かめる手段が無い |
| 監査者の harness の名前の混入 | 1 | 他人の repo の README 項目に「readme-writer へ回す」（その repo に readme-writer は無い） | context-sync の「README は readme-writer へ」の行が project mode で他人の repo にそのまま出る |
| その他 | 3 | 提案した置換文で行数が変わらないと書いたが増える、所有関係の説明の過大、hook の衝突条件の読み違い | change の副作用の見積もり |

**80% 未満の source（厳密の基準）への 1 行ずつ:**

- hooks（6/9）: hook の runtime 挙動（exit code と stderr の扱い）を出典なしに断定し、change に repo に無いテスト runner を書く。
  evidence の行番号を Read で確かめていない。hook どうしの衝突を実装でなく文書の記述から推定している
- agents（6/9）: 「同じ規則が既にある」の在りかと「CLAUDE.md が X を持つ」の記述を Read で確かめていない。agent の参照元の
  検索範囲が repo 全体でない
- assets（7/9）: 「参照 0 件」を言う前の検索が config・runbook・session log を外している。2 文書の題名が「同じ」と
  書いたが、実物の先頭行を Read で確かめていない
- docs（4/9）: README・CLAUDE.md のリンク数と参照先の在りかを Glob / Read の出力から書いていない。project mode で
  readme-writer 等の監査者側の skill 名を routing 先に書く
- distill（4/9）: 「N 個の skill に同じ記述」の N と、昇格案の impact（どこが参照しているか）を Grep の出力で確かめていない。
  Claude Code の runtime 挙動を置換文に断定で書く（この 1 件の照合役の主張は未確認）

## Stage 3 の判定の改訂案（著者への提案）

親 plan [enumerated-petting-beaver](../enumerated-petting-beaver.md) の Stage 3 判定は「見立ての的中率 70% 以上なら対象を書く」。
Stage 0 で驚きの閾値「5 件」は 20 本中 19 本が越え、見立ても「全部 ○」で 9/10 に届いたので、この判定は記事の主張を区別しない。
50 本では次の 3 つで判定する案:

1. **source 別の非 Keep 率**（非 Keep 項目が 1 件以上出た run の割合と、run あたり件数の中央値）。記事の数字はここから 1 つ選ぶ
2. **正答率**: 50 本から非 Keep を source 別に層別で抜き、今回と同じ隔離照合を回す。source 別に「正答率 80% 以上」を言うには
   各 source 30 件で 29/30 以上が要る（95% 下限は 30/30 でおよそ 88%、29/30 でおよそ 83%、28/30 でおよそ 78%）。rules は 24 run で
   非 Keep が 11 件しかなく、50 本でも 30 件に届かない見込みが高いので、rules は全件照合にして率の判定から外す。各 10 件では 10/10 でも下限はおよそ 69% で区別が
   付かないので、source 別の判定は rules 以外の 6 source を 30 件ずつ
   （計 180 件と rules 全件、照合費の目安 $110）か、全体 70 件で全体の率だけを言うかを先に決める。
   厳密の基準（細部まで正しい）も併記する
3. **report 到達時間**: 最初の非 Keep 項目までの秒数の中央値と、report.md が 10 分以内に揃った割合。README の「3 分 / 10 分」は
   この 2 つが 50 本で成り立つときだけ書く（目安: 最初の項目 3 分以内が 80% 以上、report 10 分以内が 80% 以上）

judge の decidable は同じ model・同じ入力での再現性が十分（κ 0.73、ただし skills は 0.68）なので補助の指標として残すが、
閾値の判定には使わない。再現性は妥当性（持ち主が本当に判断できるか）を示さない。見立て（harness の大きさで
驚きを予測する）は Stage 0 で情報量が小さいと分かったので、的中率の判定から外し、大きさと非 Keep 件数の関係の散布図として出す。

## 限界

- 照合役も Claude 系の model 1 回。人間の maintainer の判断ではない。照合役の誤り（例: runtime 挙動の主張）は確かめていない
- 抽出は各 source 6–9 件で、source 別の率の 95% 区間は広い（Clopper-Pearson で 9/9 でも下限はおよそ 66%）。全体の 57/60 は
  下限およそ 86%。ただし 60 件は 22 run に集まり、照合は run ごとに 1 回の呼び出しでまとめて行ったので項目は独立でなく、
  実際の区間はこれより広い
- 全体の 57/60 と 40/60 は抽出の重みを付けない比率（rules を多めに、skills を少なめに抽出している）
- 照合は repo の事実と verdict の妥当性で、持ち主にとっての価値は測っていない
- P16・P19 は report.md が無く、judge の入力は items から組み立てた表（1 回目と 2 回目で同じ入力）

---
state: done 2026-08-29
review-when: substrate が skill listing の注入方式を変えた時（description 全文でない要約注入・遅延読み込み等）。または `disable-model-invocation` の意味が変わった時
---
## Summary

skill listing の常駐コストを、**skill の本数ではなく description の側**から削る機構を検討する。S1 の実測（2026-08-29）で、本数削減の上限が −4 本 / −897 字なのに対し、description を畳む路線は −0 本 / −6,596 字と約 7 倍効くことが分かった。何を機構化し、何を 1 回の編集で済ませるかを決める。

## Motivation

T-002 は「description の editorial 圧縮は構造的に限界（上位 5 本で −695 字）だったので、次の棚卸しは長さでなく本数を対象にする」と書いていた。S1 の実測はこの二択そのものを否定した。

`metrics/skill-usage.jsonl` 79 日分（3,193 行、2026-06-10..08-28）を read / invoke / slash に分けて集計すると、第三の状態が見える:

- **意図的使用（invoke + slash）が 79 日で 0 の skill が 15 本**（7,523 字）
- そのうち **11 本は `read` が 10 回以上ある** — description は 79 日間 1 度も選択に効いていないのに、body は現に読まれている

この 11 本は「使われていないから消す」対象ではない。**消せないが、description だけ畳める。** 本数を 1 本も減らさずに常駐を減らせる、という点が既存の 2 軸（圧縮 / 退役）のどちらでもない。

| 路線 | 減る本数 | 減る文字数 |
|---|---:|---:|
| 本数削減（T-002 の想定） | −4 | −897 |
| description 撤去 | −0 | **−6,596** |

一次資料: `.notes/s1-skill-count-audit-2026-08-29.md`（commit `56c5ae8`）§A3 候補群 III・§A4。集計 script は同 commit の `.py`。

## Guide-level explanation

採用された場合、対象 skill は listing から説明文が消える（または 1 行になる）。利用者から見た変化:

- **人**: `/name` で従来どおり呼べる。body も残る
- **モデル**: 自発的に選ぶことはなくなる。他 skill の「NOT for → X」参照や rule の命令形配線から `read` される経路は残る

つまり **発見性を人間側と明示配線側に寄せ、モデルの自発選択からは降ろす**。ADR-0058 の足場溶解と同じ方向（原則は残し、常駐だけ畳む）。

## Reference-level explanation

### 手段（排他ではない）

| 手段 | 効果 | 副作用 |
|---|---|---|
| A. `disable-model-invocation: true` | listing から名前ごと消える（実測: `wait-what` と `thermo-nuclear-code-quality-review` は注入 listing に 1 本も現れない） | slash 専用になる。名前も出ないので「あることを知らないと呼べない」 |
| B. description を 1 行へ | 名前は残り、trigger surface だけ縮む | 中途半端になりうる（load-bearing な trigger を落とすと自発発火が死ぬ） |
| C. sub-skill を `references/*.md` へ降格 | listing から本数ごと消え、orchestrator 経由で読める | orchestrator が入口として実在している群にしか使えない（例: paper cluster の `paper-ecosystem`） |

### 対象の選び方（S1 の候補群）

- **III-a**: 意図的使用 0 かつ `read` ≥ 10 の 11 本 = 5,218 字
- **III-b**: `invoke` 0 だが `slash` > 0（人だけが呼ぶ）の 4 本 = 1,378 字。A が素直
- **II-1 / II-3**: orchestrator を持つ群（paper 6 本 / stocktake 3 本）は C が候補

### 機構化するか、1 回の編集で終わるか

**これが本 RFC の中心の問い。** S1 が集計 script を残したので、判定材料は既に再生産可能である。したがって新設を検討する価値があるのは以下のみ:

1. **定期実行**（`skill-stocktake` に「意図的使用 0 かつ read > 0」の抽出を組み込む）— 既存 skill への追記で足り、新規機構ではない
2. **`review-to-lint` 化**（RFC-0005 #7 の skill-stocktake 残余に相乗り）— 機械項目なので候補
3. **何も建てない** — 対象 15 本は今回の 1 回で片づき、次に同じ判断が要るのは skill が数十本増えた時。その時に S1 の script を再実行すればよい

Build-or-not の 4 問はこの 3 択に対して問う。

## Drawbacks

- **発見性の一方向の喪失**: A を採ると名前すら出ないので、「そんな skill があった」と気づく経路が rule / 他 skill の参照だけになる。復活は 1 行だが、**復活すべきだと気づけない**
- **窓不足の誤判定**: `measurement-discipline` / `repair-discipline` は 2026-08-25 追加で 4 日目、`loop-design-check` は 12 日目。0 は「未使用」でなく「窓が無い」。79 日の数字と並べると誤る
- **分母が未測定**: 6,596 字は `~/.claude` 所有分 40,815 字に対する 16.2% であって、注入 listing 全体に対する比ではない。同じ listing を plugin / built-in（`code-review` `simplify` `run` `schedule` ほか、log 上 68 名前）が占めており未測定。**削減率を語るならこの分母を先に測る**
- 常駐が減ったことによる行動変容（自発発火の低下・誤選択の増加）は**測っていない**。字数は入力であって成果ではない

## Rationale and alternatives

- **本数削減を主軸にする（T-002 の原案）**: 効果 1/7。ただし listing の「本数そのもの」が選択の質に効くなら字数より重要でありうる — この仮説は未検証
- **何もしない**: 40,815 字は絶対値としては小さい。ただし skill は単調増加しており、刈る規律が無いと 1 年で倍になる
- **plugin / built-in も含めて測ってから決める**: 分母が正確になる。1 セッション追加

## Prior art

- T-002 の前回実測（commit `b06fac4`）: editorial 圧縮で上位 5 本 −695 字、未使用 3 本の無効化で −769 字。**圧縮より無効化の方が効いた**という当時の観測は、今回の結論と同じ方向を指していた
- ADR-0058（執筆ハーネスの足場溶解）: 原則を残して足場だけ畳む型の先例
- `skills/skill-stocktake/scripts/usage_stats.py`: 意図的使用の定義（`slash + invoke`）と 4 つの補正規則の正本
- S1 の code review 指摘: description 文字数は YAML の引用符と `\"` escape を外して数える（92 本中 36 本が 2〜8 字高く出る）

## Unresolved questions

- A / B / C のどれを既定にするか。III-a 11 本は A で揃うのか、body の性質で分かれるのか
- 「listing の本数そのものが選択の質に効く」仮説を測る手段があるか（あるなら本数軸は復活する）
- plugin / built-in 側の description を測るか（分母の確定）
- 常駐削減の**効果**（自発発火・誤選択）を測る計器を持つか、字数だけで進めるか

## Status

done 2026-08-29 — 同日実施完了。当初の A/B 割当から 2 点変わった:

1. **手段 D（project repo への移設）が実施中に追加された**（著者判断）: paper cluster 6 本（`paper-ecosystem` / `paper-writing` / `paper-deposit` / `ai-native-preprint-submission` / `citation-sync` / `cited-source-mirror-verification`）+ paper 専用 agent 5 本（paper-reviewer / citation-formatter / clarity-reviewer / source-fidelity-checker / vocabulary-consistency-checker）を新設の `~/MyAI_Lab/paper-lab/.claude/` へ**内容無改変で移設**し global から撤去。listing から名前ごと消え、論文作業のセッションでだけ載る — A/B/C のどれでもない第 4 の手段で、対象群には本数削減と description 撤去を同時に達成する上位互換
2. **A（`disable-model-invocation: true` 追加、description は人間用 slash メニューに温存）を 10 本に適用**: III-a 残余の `skill-health` / `rules-distill` / `llm-as-judge` / `python-patterns` / `agent-harness-construction` / `ai-regression-testing` / `e2e`、III-b の `wiki-harvest` / `prompt-perturb` / `session-theme-mining`。全 10 本に他 skill / rule からの明示参照（到達経路）を実測確認済み。B 適用は 0 本
3. **手段 D 第 2 適用（同日、著者指示）**: 記事執筆系 skill 3 本（`writing-ecosystem` / `quality-gate` / `session-theme-mining`）+ agent 6 本（editor / essay-reviewer / prose-clarity-reviewer / theme-reviewer / title-reviewer / fact-checker）を `~/MyAI_Lab/zenn-content/.claude/` へ内容無改変で移設し global から撤去（session-theme-mining は 2. の A 適用から D へ格上げ）。`collect-context` / `headline-craft` / `prose-translation` / `x-draft` / `public-comment` は横断利用のため global 残留（著者判断）

除外と決着:

- `review-to-lint` は除外（著者判断）— 前日 commit `34d1401` で description を意図的に延伸した直後のため。次回棚卸しで再判定
- 窓不足 3 本は S1 監査の時点で III に含まれていなかった（Next action 1 は確認のみ）
- 機構化 3 択は「新規機構は建てない + 既存 skill への追記」で決着: skill-health Phase 3 に residency-fold 候補と本文サイズの列挙（enumerate）、skill-stocktake Stage 1 に Hygiene 問い（decide）、skill-creator §1/§3 に description = trigger surface / `disable-model-invocation` の規約を追記
- Reference-level explanation の「RFC-0005 #7 に相乗り」は前提が古かった — 当該残余は RFC-0009 として 2026-08-27 done 済み
- 派生: description を挙動汚染（第 2 の rules 層）として扱う軸は **RFC-0018** として分離起票（draft）

（旧 Status: accepted 2026-08-29 — T-002 の削減軸を description 撤去へ振替。対象 III-a 11 本 + III-b 4 本、Retire 候補 3 件は別途 1 件ずつ）

## Next action

着手可能。build セッションで以下の順に片づける:

1. **窓不足 3 本を対象から外す**（`measurement-discipline` / `repair-discipline` / `loop-design-check`）。0 は「未使用」でなく「窓が無い」
2. **III-a 11 本 / III-b 4 本それぞれに A（`disable-model-invocation`）か B（1 行 description）かを割り当てる。**判断軸は「名前すら listing から消してよいか」— 他 skill の `NOT for` 参照や rule の命令形配線から到達できるなら A、入口が listing しかないなら B
3. **Build-or-not 4 問を自答して 3 択を決める**（定期実行 / review-to-lint 化 / 何も建てない）。S1 の集計 script が残っているので、既定は「何も建てない」寄り
4. 分母（plugin / built-in 側の description）は本 RFC の scope 外。削減率を対外的に語るときだけ測る

kind: internal
# headline-craft の実物試行 — harness-stocktake の README tagline と GitHub About

as-of: 2026-11-01。skill [headline-craft](../../../skills/headline-craft/SKILL.md)（改修直後の版）を、`shimo4228/harness-stocktake`
（`main` `88693e5`）の README に当てた。README・About・どちらの repo の skill も変更していない。候補を選ぶのは著者。

## 結論

- 5 ラウンド（独立 subagent）で tagline 42 本・About 20 本を出し、仮説 8 群に畳んだ。代表 9 本 + 現行 1 本（tagline）、
  代表 4 本 + 現行 1 本（About）を隔離した初見読み手 3 人に読ませ、監査で直した版を下に置く
- **初見読みで一番大きいずれ: 3 人とも、全 15 行で "harness" を「分からない語」に挙げた。** 部品の列挙（skills, rules, hooks,
  agents, CLAUDE.md）が隣にある行だけ、何の話かは伝わっている。入口の語として残すなら列挙と組で置く
- **著者の数字のうち 2 つは出どころと合わない**（「本文側の不足」）: 65% は公開 20 本ではなく著者の harness 1 本（非 Keep 74 件中 48 件）。
  88〜90 秒は公開 harness ではなく sample harness（29 項目）の値で、公開 14 本の中央値は 138 秒。README は 138 秒だけを載せている
- 指示と skill の食い違い 1 件: 依頼の「上位 5 本」に対し、skill 手順 8 は「順位・点数・推奨は付けない」。skill を優先し、
  仮説の違うものを順位なしで挙げた（下の「抜き出し」。H1 の T1・T2 が事実の照合で外れ、4 本）。順位が要るなら readme-writer の `references/tagline-eval.md` の仕事

## 候補（監査後）

各代表に、仮説・明かす／残す・初見読みの期待と回収先・監査で直した点を付ける。出どころの記号 M1〜M15 は下の素材台帳。

### README tagline

**H1 /doctor の隣の空白（対比）** — /doctor で足りると思っている人に、/doctor が見ない種類を示す

- T1: `/doctor finds what's unused; harness-stocktake finds what's stale, contradictory or duplicated across your Claude Code skills, rules, hooks and CLAUDE.md.`
  - 明かす: /doctor との分担、見つける 3 種、対象。残す: どう判定し、どう直すか
  - 期待「/doctor の未使用検出を超えて、矛盾と重複の report」→ README "How it relates to /doctor"・M3・M7。回収される
  - 直した点: "harness" 単独 → 部品を列挙。R1・R3 が「/doctor が本当に unused を出すのか」を疑った — README に「unused plugins,
    MCP servers and skills」とあるので主張は保つ
- T2: `What's still wrong in your Claude Code setup after /doctor comes back clean? Stale references, contradictions between files, hooks wired to scripts that are gone.`
  - 明かす: 疑問と、その答えの具体 3 つ。残す: 修正の流れ
  - 直した点: 初版は疑問だけで終わり、R3 に「中身の無い宣伝文句かも」と読まれた。答え（M3 の語そのまま）を後半に置いた

**H2 自分にもありそうな具体的な劣化（認知）** — 「それ、うちにもある」で開かせる

- T3: `A hook calling a deleted script, two skills doing one review, a CLAUDE.md naming a make target that's gone: find this drift across your Claude Code harness, then fix it on a branch.`
  - 明かす: sample harness の実例 3 つ（M12）。残す: 他に何が出るか
  - 期待「壊れた参照と重複の report」→ `examples/sample-report.md`。回収される
  - 直した点: R1・R2 が「直すのか見つけるだけか」を挙げた → "then fix it on a branch" を足した。R3 は「この 3 種だけ」と読みうる（残す側の代償）

**H3 一回の承認と branch（統制）** — 書き込みを嫌う tech lead に、手順で安心させる

- T4: `One report, one approval, one git branch you merge: an audit of the stale, contradictory and duplicated content in your Claude Code skills, rules, hooks and CLAUDE.md.`
  - 明かす: 流れ全体と監査の中身。残す: 何本の監査か・速さ
  - 直した点: 初版（`One report, one approval, one git branch: a hygiene pass across ... You do the merge.`）は 3 人とも「何を見つけるか
    が無い」と答えた。"hygiene pass" を中身（M1・M3 の 3 種）に置き換えた

**H4 model がもう要らない rule（新規性）** — /doctor のどれも問わない問いで開かせる

- T5: `Finds the Claude Code rules the model already follows without them — tested in fresh sessions — and whatever else in your harness is stale or duplicated.`
  - 明かす: rules audit の probe（M6）。残す: 他の監査の範囲
  - 期待「Claude が既に守っているので要らない rule の report」→ README "Runs"（fresh sessions の probe）。回収される
  - 直した点: R2・R3 が「どう確かめるのか、費用は」を挙げた → "tested in fresh sessions" を足した。費用は README "Cost" が回収する。
    probe は rules だけ（skill・hook には無い）なので、skill 等へ広げる言い方はしていない

**H5 何か月分の積み残し（痛み）** — 読み返す時間が無い人に

- T6: `Months of Claude Code config drift in one report: what to retire, merge or update across skills, rules, hooks and CLAUDE.md, with the exact change next to each.`
  - 明かす: verdict の 3 語と "exact change"（M4）。残す: 判定の基準
  - 直した点: 初版の `~/.claude` は R1・R2・R3 とも「global だけで project の .claude/ は対象外」と読んだ（`--project` がある）→ "Claude Code config" に

**H6 系譜（skill-stocktake の利用者向け）**

- T7: `skill-stocktake plus six more audits — rules, agents, hooks, docs, configs — in one report you approve once.`
  - 明かす: 7 監査の構成（M2・M15）。残す: 何を見つけるか
  - 期待「skill-stocktake より広い監査」→ README の audits 表。回収される
  - 直した点: 初版 "skill-stocktake, grown up" は R1〜R3 全員が「skill-stocktake を知らないと意味が無い」。この群は ECC 由来の読者に向けた
    もので、一般の入口には向かない。"grown up" は情報を足さない語なので、監査の数と種類に置き換えた。"successor" も skill-stocktake が
    中に残っている事実と合わないので使っていない

**H7 速さ（試す費用の低さ）**

- T8: `First finding in a median of 138 seconds: stale references, contradictions and duplicates across your Claude Code harness, with nothing changed until you approve.`
  - 明かす: 中央値（M8）と中身。残す: report 全体の時間
  - 直した点: 初版 "a little over two minutes" は R1 に「audit 全体が 2 分」と読まれた → "first finding" と "median" を明示し、
    何が見つかるかを足した（R3: 速さだけでは何が得られるか分からない）。数字は README の 138 秒に一字ずつ合わせた（88〜90 秒は使わない）

**H8 名前の由来（棚卸しの比喩）**

- T9: `A stocktake of your Claude Code harness: each skill, rule, agent and hook gets Retire, Merge, Improve, Update or Keep, with a reason and the exact change, applied only when you approve.`
  - 明かす: "stocktake" の意味と verdict の 5 語（M4）。残す: cross-file で何を見るか
  - 直した点: 初版は R1 に「verdict が自動で適用される」、R3 に「恣意的なラベルの一覧」と読まれた → reason・exact change・承認後の適用を足した

**基準（現行）**

- T0: ``Audit and clean up your whole Claude Code harness (skills, rules, agents, hooks and their settings, `CLAUDE.md`, ADRs and configs) in one report and one approval: a hygiene pass across files.``（`88693e5:README.md` 7 行目、冒頭段落の 1 文目）
  - 初見読み: R3「/doctor と何が違うか分からない」、R2「"clean up" + "one approval" を、ファイルをその場で書き換える一括 cleanup と読んだ（受け入れない）」、
    3 人とも "hygiene pass across files" を曖昧と挙げた

### GitHub About（数字なし）

README の冒頭段落と同じ主張に揃える（readme-writer `references/about.md`: 食い違いは cloaking）。

- D1（何を + 安全）: `Audits your whole Claude Code harness (skills, rules, agents, hooks, CLAUDE.md, ADRs) for stale, contradictory or duplicated content, then puts the fixes you approve on a git branch for you to merge.`
  - 初見読み: R2「範囲も書き込み先も明確で、誤解はほぼ無い」、R3「誤解は特に無し」。監査で直した点なし。R1・R3 は "ADRs" を挙げた（tech lead は知っている）
- D2（/doctor の空白 + 実例）: `Finds what /doctor leaves behind in a Claude Code harness: hooks wired to missing scripts, rules that repeat a skill, CLAUDE.md and ADRs that no longer match the code. One report, one approval, fixes on a branch you merge.`
  - 直した点: 初版 "docs that contradict the code" を R2・R3 は「source code 全体を読む」と読んだ。context-sync が照合するのは CLAUDE.md・ADR・
    README の主張なので、固有名詞に置き換えた。R1 は「/doctor の代わり」と読みうる — 気になるなら末尾に "Run it alongside /doctor."
- D3（verdict の行）: `Rates each skill, rule, agent and hook in your Claude Code harness Retire, Merge, Improve, Update or Keep, with a reason and the exact change; approved changes go onto a git branch you merge.`
  - 直した点: 初版（"A hygiene pass ... every finding is a row ..."）は 3 人が「何を走査するか」「承認した変更がどこへ行くか」を挙げた。
    R2 は承認を全か無かと読んだ（実際は `decision` 欄で行ごとに上書きできる。About には入らないので README 側が回収する）
- D4（まだ要るか・まだ正しいか）: `Checks whether each skill, rule, hook, agent and doc in your Claude Code harness is still needed and still true, then puts the fixes you approve on a git branch. Works alongside /doctor, not instead of it.`
  - 直した点: 初版は R1 に「read-only」、R2 に「出力と安全の話が無く漠然」と読まれた → 書き込み先を足した。著者の差別化の軸（中身の要否）に一番近い
- D0（現行 `.claude-plugin/marketplace.json` の `plugins[].description`、基準）: `Audit and clean up your whole Claude Code harness in one report and one approval. Start with /harness-stocktake:harness-stocktake --dry-run.`
  （`plugin.json` の description は部品の列挙と書き込み先（branch）を含む長文で、これとは別の文）
  - 初見読み（部品の列挙も書き込み先も無い、この marketplace の短い 1 文への反応）: 3 人とも「何を探すのか分からない」、R3「/doctor と同じに聞こえる」。repo の About は現在空（description null、topics なし）

### 抜き出し（順位なし、仮説の違うもの）

依頼の「上位 5 本」の代わりに、互いに仮説が重ならず、初見読みのずれを監査で直せた 4 本を並べる。A/B や tagline-eval に回すならこの組が差の出る組になる。
H1（/doctor との対比）の T1・T2 は、どちらも `prompt-audit` が検出するものを /doctor が見ないと含意するので外した（下の「追試」）。/doctor との関係は About の 2 文目に置く。

1. T3（具体的な劣化）
2. T4（統制）
3. T5（新規性）
4. T8（速さ）

## 追試: /doctor の認知で読みが変わるか

著者の問い「/doctor はどれくらい認知されているか」を受けて回した。

- 前提の材料: GitHub code search の件数は `/init` 約 16 万・`/compact` 約 15 万・`/doctor` 約 6.8 万・`/skill-doctor` 約 4 千・
  `/doctor prompt-audit` 約 1.6 千（言及数で利用者数ではない）。/doctor が harness を点検する setup checkup になったのは v2.1.205（2026-07）、
  prompt-audit は v2.1.283（2026-09）（[stocktake-campaign](2026-11-01-stocktake-campaign.md)）。隔離した読み手 model に /doctor を聞くと、
  3 回とも「インストール・設定の診断、壊れたときに使う」と答え、skills・rules の中身を見るかは「分からない」とした
- 読み手 2 人（どちらも skill 約 40・hooks・長い CLAUDE.md を持つ上級者）: **新** = 新しい /doctor・prompt-audit・/skill-doctor を定期的に回す人、
  **旧** = /doctor をインストール診断としか知らない人。1 行ずつ別の呼び出しで読ませ（行どうしを比べさせない）、各 2 回。`read.sh --probe` は exit 0

| 行 | /doctor | 新: 開く / /doctor の記述が自分の理解と合うか | 旧: 開く / 合うか | 読み手の言葉（要約） |
|---|---|---|---|---|
| T1 | 対比 | yes・maybe / partly・no | yes・yes / no・no | 新「prompt-audit は矛盾も古い path も既に出すので、/doctor を過小評価している」。旧「/doctor が unused を出す？インストール診断としか知らない」 |
| T2 | 問い | yes・yes / partly・partly | yes・yes / yes・yes | 旧には「/doctor が clean でも残る」がそのまま通る。新は prompt-audit との重なりを挙げた |
| D2 | 空白 | yes・yes / partly・partly | yes・yes / partly・partly | 新は重なり、旧は「/doctor がそれを見る前提が分からない」 |
| D4 | 併用 | yes・maybe / partly・partly | yes・yes / partly・yes | 「併用」は両方に大きな摩擦なし |
| T3・T4・T5・D1 | 出さない | 全 8 回 yes | 全 8 回 yes | T5 は新が自分から「/doctor の静的な検査を越える」と対比を引き出した |

- **T1 は両側から引っかかる**: 新しい /doctor を知る人には不正確に見え、古いイメージの人には前提が通じない。さらに監査の見落としもあった。
  `prompt-audit` は「矛盾する指示」を検出する（stocktake-campaign 2 節）ので、「/doctor は unused、こちらは contradictory」は /doctor が矛盾を
  見ないと含意し、事実と合わない。tagline の候補から外すのが妥当。対比を残すなら README の "How it relates to /doctor" で、
  「prompt-audit は書き方と指示内の矛盾、stocktake はファイルをまたぐ照合（hook ↔ script、ADR ↔ code、rule ↔ skill）」と具体的に分ける
- **T2 も同じ基準で外した**: 3 つの答えの先頭 "Stale references" は「/doctor が clean でも古い参照が残る」と含意するが、`prompt-audit` は
  古い path / command を検出する（stocktake-campaign 2 節）。"hooks wired to scripts that are gone" は prompt-audit の対象（CLAUDE.md / skills /
  agents / commands）の外だが、行の主張は 3 つまとめての「/doctor の後に残るもの」なので、T1 と同じく事実と合わない含意を持つ
- T2・D2 は旧の読み手には通るが、新の読み手には重なりを疑われる。/doctor の守備範囲は release ごとに広がるので、主語に置くほど早く古くなる
- /doctor を出さない行は、両方の読み手に同じように通った。/doctor との関係は About の 2 文目（D4 の "Works alongside /doctor, not instead of it."）に置けば足りる
- T4 の "One approval" は 4 回とも「何を承認するのか（report か変更か）」と挙げられた → `approve the changes once` のように対象を書く
- "harness" は、部品の列挙がある行では全員が「Claude Code の設定一式だろう」と正しく推測した。旧の読み手は「自分なら setup か config と言う」
- 割り引く点: 1 セル 2 回、読み手は model。「開く」の回数は順位の根拠にしない

## 本文側の不足（著者に返す。題を弱めるか本文を足すかは著者が決める）

- **"harness" の定義が README の第一画面に無い**。冒頭段落は部品を並べるが、語そのものは定義しない。初見読み手 3 人が全行で挙げた。
  **cutoff ではない**（追試）: 隔離した読み手 model（cutoff 2026-06 ごろと自己申告）に 3 回聞くと、3 回とも "agent harness" の通常の意味を
  「model を包む runtime / scaffold」と答え、利用者の設定（skills・rules・hooks・CLAUDE.md）は「緩く含める人もいる」「harness の上の設定層」とした。
  GitHub でも主流は runtime の意味（"Multi-harness ... for Claude Code, Codex, Cursor"、"harness engineering" は query loop・context 管理の話）で、
  著者の意味に近いのは ECC の description。code search で "agent harness" 約 34 万件、`topic:agent-harness` 1,830 件（2026-11-01）。
  ずれは未知語ではなく語義の取り違えで、"audit your Claude Code harness" は「Claude Code 本体の監査」とも読める。部品の列挙と組で置けば解ける。
  割り引く点: 初見読みの質問が「分からない語を挙げよ」の形で、専門語っぽい語を挙げやすくしていた
- **65% と「20 本中 19 本で驚き」は README に無い**。tagline に使うなら README が回収する必要がある。しかも 65% は著者の harness 1 本の値
  （[doctor-comparison](2026-11-01-doctor-comparison.md)）で「公開 harness で」とは書けない。19/20 の「驚き」は「600 秒以内に判断可能な非 Keep が
  5 件以上」という操作化で、[premise-test](2026-11-01-premise-test.md) 自身が「ほぼ区別しない閾値」と書いている。"surprising" を数字で裏づけるのには使えない
- **88〜90 秒は sample harness の値**（[stage1-plugin](2026-11-01-stage1-plugin.md)）。README は公開 14 本の中央値 138 秒を使っている。告知で 2 つを混ぜない
- **差別化の軸の言い方**: 合意された軸は「/doctor は指示の重複を見る」を含むが、README と doctor-comparison では重複（Merge）は stocktake 側の
  指摘で、/doctor 側は使用履歴・hook の遅延・`prompt-audit` の書き方。/doctor の担当範囲として "duplicated instructions" を書くと README と食い違う
- 「衛生が驚くほど上がる」「人に勧めたくなる」は測っていない。候補には入れていない
- 「一回の承認」は全か無かと読まれやすい（R2）。README は `decision` 欄での行ごとの上書きを書いているが、"What the report looks like" の後半にあり第一画面に無い

## 手順をどう踏んだか

| 手順 | やったこと |
|---|---|
| 0 | 部品は README tagline（1 行）と GitHub About description（数字なし）。現行 About は空、`.claude-plugin/marketplace.json` の `plugins[].description`（短い 1 文）を基準に使った。著者の題の規約は repo に無い |
| 1 | README・CHANGELOG・examples と、この repo の research report 6 本（doctor-comparison / premise-test / premise-test-prediction / precision / rerun / stage1-plugin）から台帳 M1〜M15 を作り、出どころを付けた。著者の言葉と「示していないこと」を別欄にした |
| 2 | 読者 4 人: R1 日常利用者（X・awesome list）、R2 tech lead（GitHub 検索）、R3 /doctor で足りると思う人（plugin directory）、R4 ECC 利用者（skill-stocktake 検索） |
| 3 | general-purpose subagent 5 本を並列に（A: R1 × 結果先行 + 具体物、B: R3 × 対比 + 疑問 1 つ、C: R2 × 困りごと + 承認の仕組み、D: R4 × 一番意外な事実 + 劣化、E: 振り切り）。各 tagline 8 本（E は 10 本）・About 4 本。tool は使わせず、台帳は prompt に埋めた |
| 4 | 仮説 8 群（H1〜H8）に畳み、代表を 1〜2 本残して 1 行に詰めた |
| 5 | `persona-read-loop/scripts/read.sh --probe` → exit 0（tools 0・MCP 0・user skills 0・context NONE、Claude Code 2.1.316）。R1〜R3 を並列に、代表 + 現行の 15 行を 1 回で読ませた（R4 は H6 だけの読者なので省いた） |
| 6 | 期待 1 文 ↔ 台帳の出どころを対応させ、回収されない語を直した（上の「直した点」）。数字は 138 秒・median を README に一字ずつ合わせた |
| 7 | 集合内の重複: "one report, one approval"（約 20 本）、"across your (whole) Claude Code harness"（ほぼ全部）、"on a branch you merge"、"drift"、"hygiene pass"。前の 2 つは著者の README の語なので残し、全行には入れない。"hygiene pass" は 3 人が曖昧と挙げたので中身の語に置き換えた。情報を足さない語（"grown up"・"rots quietly"・"lying to you"）は削った |
| 8 | 群ごとに並べ、順位・推奨は付けていない。About は README 冒頭段落と同じ主張に揃えた |

作業ファイル（台帳・読者・ラウンドの生出力・初見読みの JSON）は session の scratchpad にあり、commit していない。

## skill の手順で迷った点・曖昧さ（改善材料）

1. **依頼者の「上位 N 本」と手順 8 の「順位を付けない」**がぶつかる。skill は境界で tagline-eval に順位を渡しているが、依頼が順位を
   求めたときの返し方（順位なしの抜き出しで良いか、tagline-eval を続けて回すか）が書かれていない
2. **著者の言葉と計測が食い違うとき**: 手順 1 は「LLM の要約より著者の語を優先」、手順 6 は「数字は台帳の値と一字ずつ」。著者が会話で言った数字
   （65%・88〜90 秒）が出どころと合わないとき、どちらを台帳の値にするかの優先が無い。今回は出どころの値を台帳に置き、著者の数字は「示していない」欄と「本文側の不足」に回した
3. **`read.sh` の path が `~/.claude/skills/...` 固定**。cloud sandbox には `~/.claude` が無く、repo の `skills/persona-read-loop/scripts/read.sh` を使った。fallback の記述が要る
4. **部品が 2 つ（tagline + About）のとき、ラウンドを部品ごとに分けるか共有するか**が書かれていない。共有にして各ラウンドに両方を出させた。
   「tagline なら 2〜3 本に減らしてよい」と依頼の「広く」の兼ね合いも判断に迷った（5 本にした）
5. **手順 3 の subagent の隔離**: 手順 5 では通常の subagent は著者の CLAUDE.md を読むと書くが、手順 3 の subagent にも同じことが起きる。
   発散では初見性は要らないが、台帳以外を読ませない指示（tool を使わせない）を入れるかは書かれていない
6. **振り切りラウンドの読者**: どの読者状態を渡すかが無い（R1 を渡した）
7. **手順 4 で代表を書き直してよいか**: 情報量の調整（1 要素足す・引く）は手順 4、誤解の修正は手順 6。今回は初見読みの前に複数文の案を 1 行に
   詰めたが、どこまでが手順 4 で許される編集か曖昧
8. **初見読みの見せ方**: 全候補を 1 つの一覧で見せたので、読み手は行どうしを比べられる（「この行だけ見たつもりで」と指示はした）。
   1 行ずつ別の呼び出しにするかの指定が無い。tagline と About を同じ一覧に混ぜてよいかも無い
9. **cutoff か本物の誤解かの判定**: "harness" は全員が挙げた。手順 5 は「対象読者が知っているかで判断」と言うが、その判断材料（実際の利用者の語彙）が
   手元に無いとき、どちらに倒すかが無い。tagline-eval は「入口の語は全候補に含める」とするが、headline-craft にはその規則が無い
10. **手順 7 は日本語向けの書き方**で、英語の候補に既知の英語 LLM 語彙（MAINTENANCE の PNAS の比較）を当てるかが書かれていない。集合内の重複だけで見た
11. **部品間の整合**: About は README 冒頭段落と同じ主張にする（readme-writer `about.md`）という制約を、headline-craft の手順 8 は GitHub の行で触れていない。数字を入れない、も依頼側の制約で skill には無い

## 素材台帳（要約）

M1 harness 全体を 1 report・1 承認（README 冒頭）／M2 7 監査が並列／M3 /doctor が残すもの（古い参照・ファイル間の矛盾・消えた script に
繋がった hook・skill を繰り返す rule・code と合わない ADR・同じ仕事の agent 2 つ）／M4 verdict 行（Retire・Merge・Improve・Update・Keep、
理由、正確な変更）／M5 承認まで何も変えない・branch・merge は利用者・`--dry-run`／M6 rules の fresh session probe／M7 /doctor は使用と
書き方、stocktake は cross-file の中身、両方回す／M8 最初の指摘 中央値 138 秒（公開 14 本）／M9 60 件中 57 件（95%）の主張が成立／
M10 著者の harness 1 本で非 Keep の 65% を native が拾わない／M11 公開 20 本中 19 本で 600 秒以内に判断可能な非 Keep 5 件以上／
M12 sample harness の劣化 4 例／M13 外へ何も送らない／M14 費用／M15 skill-stocktake の系譜

## 訂正（2026-11-08）

main に入れる前の別 process の review が事実の誤り 4 件を見つけ、`88693e5` と stocktake-campaign に照らして本文の該当箇所を直した。

1. 結論の「全 25 行」を 15 行に直した。初見読みで見せたのは tagline 9+1・About 4+1 の 15 行（手順 5）で、25 に当たる集合は無かった
2. D0 の出どころを `plugin.json` の description から `marketplace.json` の `plugins[].description` に直し、基準の読み（「何を探すのか分からない」）がこの短い 1 文への反応だと書いた（D0・手順 0）
3. T0 を `88693e5:README.md` 7 行目の原文どおりに直した（"and their settings" と `CLAUDE.md` の backtick が抜けていた）。読み手に見せた文面は scratchpad にしか無く、どちらの文面だったかは確かめていない
4. T1 を外した基準（prompt-audit の検出範囲と重なる含意）を T2 にも当て、"Stale references" が古い path / command の検出と重なるので T2 も外した。抜き出しは 4 本になった（結論・抜き出し・追試）
5. T1・T2 を外す理由の出典を「stocktake-campaign 1 節」から 2 節に直した（prompt-audit の検出範囲は 2 節「公式 plugin directory と Anthropic 自身の `/doctor` 系」にある。1 節は awesome list の節）

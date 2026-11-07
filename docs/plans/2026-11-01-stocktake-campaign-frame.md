kind: internal
# harness-stocktake を外へ届ける campaign の大枠（widen-the-ask の出力）

as-of: 2026-11-01。著者と skill `widen-the-ask` を高度 → 範囲 → 深度の順に回した結果。詳細設計（リスク・倫理・
手順）は次の session（Fable）が仕上げる。ここにあるのは方向と、それを確かめる置き場所まで。

## 前提の状態

- harness-stocktake は 2026-10-31 に初回の全体実行を終えた（7 source・192 項目、うち退役 24。report:
  https://claude.ai/artifact/H8515RDi7MpdHXgJYpoAPj）。apply は `stocktake/2026-10-31` を ff で main に取り込み済み
- 経緯と設計: [ADR-0097](../../decision-history/0097-batch-stocktake-report-and-two-decisions.md)、plan [sunny-splashing-scroll](../sunny-splashing-scroll.md)
- 未了: git-target 抽出の修理 session（heredoc・コメント対応）が Review 待ちで止まっている。公開 repo への
  `harness-sync` と akc-cycle のリリースはまだ回していない

## 元の依頼（著者の言葉の要約）

不具合の修理が終わったら harness-sync と akc-cycle のリリースで同期する。そのあと harness-stocktake を plugin として
単独 repo 化し、Anthropic の plugin library と各種 awesome list に登録する。これらは一例で、PR campaign として手段を
plan して進める。実行結果を動画や画像でインパクトのある形で伝える。初回の Artifact も使える。日本語の制限はありうる。
Personal-branding repo の手順は参照してよいが、提案が小さいので、もっと野心的であるべき。

## 高度 — 選んだ段: 二段上（状態の委任）

> harness-stocktake が、他の人の harness で繰り返し回り、勧められ続ける状態を保つ。外の反応（issue・実行結果・
> 言及）を拾って skill を直し、新しい実例を発信するループを、著者が merge の判断だけで回せるようにする。最初の
> 一手は、他人の harness での初回実行を確実に驚きで終わらせること。harness-sync・akc-cycle のリリース・plugin の
> 単独 repo 化・登録・動画と画像は、このループへ人を流し込む経路として置く。

著者の目的の目的: 使ってみれば harness の衛生が驚くほど上がり、網羅度に驚く。使った人が他の人に勧めたくなる。

## 範囲 — 動詞

> 自分の harness が散らかっていることに気づいていない人の目の前に届け、それを一度で見せ、自分の手で片付けさせ、
> その驚きを別の人に語らせる。

著者の補足: まず誰かの手に届くことが前提（届かなければ残りの動詞が始まらない）。

持ち込む行為:

- 作る側: 最初の驚きまでの時間を測って縮める / 一人の before・after で見せる / すでに人が集まっている場に置く
- 壊す側: 「`/doctor` で足りるのでは」と崩しにいく / 承認なしに何もしないこと・戻せることを証明させる

`/doctor` との差（2026-11-01、code.claude.com の commands / skills / plugins/measure を確認）: `/doctor` は使用履歴と
context コスト、slow hooks、CLAUDE.md の重複と導出可能性、`prompt-audit` の古い・矛盾する指示を見る。中身の要否
（substrate 吸収・失効条件・transfer・重複）、hooks の配線とテスト、台帳と実物、ADR・README の drift、assets、
項目間の衝突、1 回の承認で branch に適用、はどれも公式の記載が無い。全設定の棚卸しにあたる公式機能は見つからない
（marketplace は未確認）。差別化の軸は「中身の判定」と「1 回の承認で直し切る」。Anthropic が `/doctor` を広げれば
差は縮む — campaign の失効条件に置く。

経路のアイデア（理想を高く置いた段階。**1 はリスクと倫理を詳細設計で詰める**と著者が明示）:

1. 公開 harness をこちらから read-only で棚卸しし、各 maintainer へ証拠付きの issue / PR で渡す。集計は匿名の
   数字だけで「State of Claude Code Harness Hygiene 2026」として DOI 付きで公開する
2. 入れずに試せる入口（repo URL を渡すと read-only の report が出る Artifact か web ページ）
3. GitHub Action 版 — 月 1 回か `.claude/` が変わった PR で回り、report を issue / コメントに出す（回り続ける状態を
   人の意志に頼らず作る）
4. opt-in の匿名実行サマリーと公開 dashboard
5. report から Remotion + 英語 TTS で before / after の動画を自動生成。英語を一次、日本語（Zenn）を二次チャネルに
6. Anthropic: directory 登録に加え、調査報告を材料に DevRel / community へ。「`/doctor` の次」の位置づけと組み合わせ手順
7. 反応の収集: `gh`、HN Algolia API、Reddit API → `rfcs/`。X は Buffer の分析で代える

## 深度

一流がやること:

- 驚きを公開前に指標として定義する（例: 入れて 10 分以内に非 Keep を 5 件以上見て 1 件以上適用）
- 見知らぬ 5 人の think-aloud を公開前に観察する
- 一斉公開の前に 10〜20 人の先行利用者を作る
- 公開の物語を一つの具体的な数字に絞る（例: 「192 項目を 2 回の判断で片付けた」）

生の素材: 初回実行の items JSON・各 phase の所要時間・確認画面の回数（verify 台帳の ask が監査の読み取りで出続けた
件 = 29ebf56 で修理）・適用 diff・台帳の before/after / 外の需要の生の声（CLAUDE.md の肥大・skill が発火しない等の
issue・Reddit・HN）/ GitHub code search による `.claude/skills` を持つ公開 repo の実数。

方法と道具: GitHub traffic API（14 日しか残らないので日次で保存）と star 推移 / clean HOME + `claude -p` で驚きまでの
時間を script で反復計測 / skill `persona-read-loop`・`readme-judge` で README と report の伝わり方を事前に確認 /
Show HN・DOI 付き報告・Remotion / HN Algolia・GitHub search API。

外部の正しさ: 他人の公開 repo にある harness-stocktake 形式の台帳（`skills/*/results.json`）の本数と、その
`evaluated_at` の月をまたぐ更新。**著者は「ちょっと問題がある気もする」と留保** — 詳細設計で、他人の repo を数える
ことの扱い（プライバシー・同意・台帳の形が識別子になること）を詰める。補助に、見知らぬ人の issue 数と再実行数。

前提の検証（著者と合意）:

> 「使ってもらいさえすれば誰でも驚き勧めたくなる」は、大きく長く育った著者の harness 1 回だけが根拠。zenn-content
> （中くらい）・Contemplative Agent など著者の他 repo の **project の harness だけ**（global を含めない）を対象に回し、
> 大きさと育ち方の違う数本で、非 Keep の件数と各項目の単独判断可能性・価値を数え、驚きが出る境目を見つける。最初の
> 数本で「何を見れば驚きの有無を事前に当てられるか」の見立てを作り、まだ回していない repo で当たるかを確かめる。
> 小さい harness で驚きが出なければ、狙う相手か驚きの源を変える。

この検証には **project を対象にする実行モード**（global を除外）が要る。今の SKILL.md は `~/.claude` 前提。これは
汎用化（他人の repo で回る版）の最初の一歩でもある。

桁違いの目標（探索の方向。合否の物差しではない。これは十分に解ける問題だ）:

> 入れてから驚くまでを 30 分でなく **3 分** にし、6 か月後には自分以外の公開 repo **1,000 本** で harness-stocktake が
> 月 1 回回っている。

3 分には、最も驚きの出る source から順に流す・report を先に開いて項目が埋まっていく・待たせない形が要る。1,000 本に
は、人が毎月思い出す形では届かず、GitHub Action のように一度入れたら回り続ける形が必須。

## 締め

### 書き直した依頼文

- **元の依頼どおりの案**: 修理の完了を待って harness-sync と akc-cycle のリリースで同期し、harness-stocktake を plugin
  として単独 repo 化し、Anthropic の plugin library と awesome list に登録し、初回実行の結果を動画と画像で発信する
  PR campaign を plan して進める。
- **一段遠い案**: harness-stocktake が他人の harness で月 1 回回り続け、勧められ続ける状態を保つ。最初に、著者の他の
  repo の project の harness で回して驚きの出る境目を確かめ、project 対象の実行モードと汎用 plugin 版を作り、驚きまで
  3 分の初回体験を設計する。そのうえで、外の人が集まる場（awesome list・plugin directory・Show HN・Anthropic の
  community）へ、一人の before / after と具体的な数字で届け、GitHub Action で回り続ける形にし、外の反応を拾って
  `rfcs/` → task-triage → 著者の merge で skill を育てるループを回す。目標は 6 か月で外部 1,000 本。

### 遠い案に足りない環境

- project を対象にする実行モード（global 除外）と、この harness 固有の依存を外した汎用 plugin 版（兄弟の stocktake を同梱）
- 驚きまでの時間を測る clean な実行環境（一時 HOME + `claude -p`）
- 外部の利用者（先行 10〜20 人、think-aloud の 5 人）と、maintainer・DevRel・meetup とのつながり（著者が持つ部分）
- GitHub Action の実装
- 動画の pipeline（Remotion + 英語 TTS）と英語の report・README
- 外の反応を拾う monitor（GitHub / HN / Reddit）と `rfcs/` への配線、traffic API の日次保存
- 匿名集計の受け口とプライバシー設計（4 と 1 の留保とあわせて詳細設計で）
- 投稿系の権限: X / Bluesky は Buffer（2026-11-01 時点で `/mcp` の再認証が要った）。HN・Reddit・awesome list の PR・
  directory 申請の送信は公開に当たり著者が行う

### 一番安く現実に触れる方法

**手元での再現**: 著者の他 repo（zenn-content など）の project harness を対象に回す。外部の利用者も新しい基盤も要らず、
前提の検証と project モードの必要性が一度に確かめられる。次に安いのは、初回実行の生データ（items JSON・所要時間・
確認画面の回数）の**過去データでの再生**で、驚きまでの時間がどこで食われたかを測ること。

### 判定の置き場所（強い順）

1. **現実に当てる**: 外部の利用者の実行数・再実行・見知らぬ人の issue・star と traffic の推移（取り方は詳細設計で）
2. **見ていないデータで予測を当てる**: 最初の数本の repo で作った「驚きが出る条件」の見立てが、まだ回していない repo で当たるか
3. **別モデル・新しい文脈での判定**: 各項目が単独で判断できるかを、report だけを渡した fresh な judge に問う

自己見直しは判定に使わない。

## 次の session（Fable）への引き継ぎ

- この文書を出発点に、さらに野心的かつ詳細な campaign 計画に仕上げる（著者の明示）
- 詳細設計で詰める留保: 経路 1（公開 harness の棚卸し）のリスクと倫理、外部の正しさ（他人の repo の台帳を数える）の扱い
- 順序の制約: harness-sync と akc-cycle のリリースは、止まっている git-target 修理 session の決着の後
- 公開・投稿・PR・申請・課金は著者に渡す（`rules/common/boundary.md`）。公開 repo に残す記録は `rules/common/public-records.md`
- 参照してよい: `~/MyAI_Lab/personal-branding` の手順（ただし提案の規模は超える）、memory の開放戦略（概念を開き DOI で帰属を守る）

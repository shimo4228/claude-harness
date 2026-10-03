---
name: headline-craft
description: 「開かせる一行」を作る候補生成スキル。記事タイトル・README tagline・subtitle・SNS告知文の候補を、著者の言葉と本文を素材に、文の形を変えて広く生成する。Use when the user asks for タイトル案・キャッチコピー・タグライン・見出し候補、or a frozen draft needs title candidates. NOT for — 公開記事候補の点検（→ title-reviewer）、本文が回収しない釣り題、topics / emoji、platform文字数の定義。
user-invocable: true
origin: shimo4228
---

# Headline Craft — 開かせる一行を作る

読者は本文を読む前にタイトルで開くかどうかを決める。このスキルは候補を広く作るところまでを担う。
選ぶのは著者なので、候補は数が多く、文の形がばらけているほど役に立つ。

**役割分担（defer 宣言）**:
- 題の規範と著者の題の形 → project の Title Conventions が正本（`~/MyAI_Lab/zenn-content` では `writing-ecosystem` 内）。定義が無い project では、下の「誠実さの照合」だけを規範にする
- platform 文字数・記法 → 各 project の publication channel contract。実値はここに書かない
- 公開記事候補の点検 → `title-reviewer` agent（`~/MyAI_Lab/zenn-content` 常駐）。本 skill 自身の候補を自己採点しない
- topics / emoji → platform を所有する project-local skill

## 実証知見（技法の根拠）

- **ポジティブな飾り言葉は CTR を下げる**: Upworthy の約 10.5 万 headline 変種の分析（Robertson et al. 2023, Nature Human Behaviour）で、ポジティブ語の追加は消費率を下げた。同研究はネガティブ語による CTR 上昇も示した
- **具体性には上限がある**: Upworthy の見出し A/B テスト 8,977 件の再分析（Aubin Le Quéré & Matias 2025, Scientific Reports）で、具体性とクリック率の関係は山なりだった。具体性を上げて得をする見出しは 8.7%、上げるとクリック率が有意に下がる見出しは 50.9%。一般向けソーシャルニュースの結果で、検索流入は含まない（as-of 2026-09-29）
- **好奇心ギャップは情報の欠落**: Loewenstein の information gap 理論。知っていることと知りたいことの差が開かせる。ただし**本文が必ずギャップを埋めること** — 埋めない好奇心ギャップがクリックベイトの定義
- **日本語圏の参考値**: Qiita 全記事分析でバズ記事はタイトル 20–36 字に集中。各 platform の上限より短い方に最適帯がある
- **トピック中心 → 結果駆動への進化**: タイトルは戦いの 90%。詩的タイトル（意味不明で素通り）と教科書調（「〜の分析」= 宿題感）が二大失敗形。具体的数値・明示的な価値・人間の声の 3 点が指を止める（Kaguura 2026, 90 日で 20,585 購読者の実践知）
- **タイトル A/B テストは読者関心の学習装置**: Substack はタイトル A/B テストを機構として持つ。目的は釣りの最適化ではなく「読者が実際に何に関心があるか」を学ぶこと（明快な解決型 vs 興味深いパラドックス型、等）

## 形と技法のカタログ

各行に「成り立つ条件」を付す。条件を満たす行だけを候補に使う。

| 形・技法 | 型 | 成り立つ条件 |
|---|---|---|
| **著者の形** | project の Title Conventions が定義する、その著者の題の形 | 定義がある project |
| **検索語を残す** | 記事の対象であるツール名・固有名詞を題に入れる（「LLM で」→「Claude Code の hooks で」） | 対象が固有名詞を持つ。残りの字数は述語に使う |
| **性質で止める** | 固有名詞を主語にし、著者の見立てを述語にする（「X は Y だ」「X は Y になりそうな気配」） | 本文に見立てを支える観察・実測がある |
| **出来事を 1 つ抜く** | 本文で最も奇妙な 1 件を、そのまま題にする | 本文がその 1 件を追っている |
| **対比・転換** | Before/After、期待と実際（「A だと思っていたが B だった」「数字は良かった。それでも捨てた」） | 実体験・実測が本文にある |
| **問いの形** | why / how、または前提への問い（「なぜ X は Y になるのか」「X は本当に要るのか」） | 本文が答えを出すか、答えられなかったことを正直に書いている |
| **誠実な好奇心ギャップ** | 結論の手前まで言う（「試したら意外な結果になった」ではなく「試したら X だけが失敗した」） | 本文がギャップを完全に埋める |
| **結果駆動** | トピック名でなく読者が得る結果を言う（「Newsletter 成長モデルの分析」→「1,000 本を分析してわかった、登録が増える 3 つのレイアウト」） | 本文が実際にその結果を提供する |
| **ベネフィット前置** | 読後に読者が得るものを先頭側に（「〜する方法」より「〜できるようになる」の中身を言う） | 本文が実際にそれを提供する |
| **数字は証拠として** | 実測値・件数を事実として使う（「32,487 件の A/B テストが示す〜」） | 数字が本文の実測値と一致する |
| **自分ごと化** | 読者の状況を主語に（「毎回忘れる人のための〜」） | ターゲット読者が実在し、本文がその人に応える |

**削る技法（追加ではなく除去）**: ポジティブ形容詞（素晴らしい・強力な・完全な）、ヘッジ（〜について・〜の話・〜メモ）、冗長な前置き。削った字数を述語に回す。

**長さ**: 日本語の参考帯は 20〜36 字。platform の上限（contract）が天井。候補群には参考帯の案と、上限までの長い案の両方を入れる。

## 流入経路の 2 軸ラベル

候補は両軸でラベル付けする。これは判定スコアではなく、候補の生成意図を `title-reviewer` と著者へ
伝える metadata である。

| 軸 | 開く人 | 効く形 |
|---|---|---|
| **検索** | 問題を抱えて検索してきた人 | キーワード前置・答えの明示（「X で Y が失敗するときの直し方」）。エラーメッセージ・ツール名をそのまま入れる |
| **フィード** | 一覧を流し見している人 | 指を止める述語・対比・問い。既知トピックの意外な角度 |

目安: チュートリアル・トラブルシュート系 → 検索寄せ。体験記・考察・実測レポート → フィード寄せ。

## 手順

1. **素材を集める** — 次を読む。題の言葉は著者の言葉から取るのが第一で、要約から作るのは第二
   - 本文（またはドラフト・要旨）と、その節見出し
   - editorial brief があれば、中心命題と Author's words
   - 本文が引用している著者の発言
   - project の Title Conventions（著者の題の形の定義）
   - 著者の直近の題 10 本（同じ文の形が続いていないかを見るため。project に生成済みの公開索引があればそこから読む）
2. **core claim 抽出** — 「読者が持ち帰る 1 つの主張・成果」を 1 文で書き出す。タイトルはこの 1 文を**指し示す**もので、題材や緊張を名指すだけの短い題でよい
3. **発散して生成** — 記事タイトルは 12 本前後、tagline・subtitle・SNS 告知文は 3〜6 本作る。現行タイトルがあれば比較の基準として 1 本に含める。著者の形が定義されていれば半数以上をその形で作り、その中で文の組み立てを散らす。残りはカタログの別の形に散らし、直近の題で続いている形（著者の形を除く）は 1 本までにする。感情語・比喩・通説の裏返しを使った案も作る
4. **誠実さの照合** — 本文が回収しない約束、本文にない数字、本文の証拠でなく飾りとして置いた数字を含む候補は、形を保ったまま回収できる言い方に直す。直せない候補だけを落とす。落とす理由はこの 1 点だけで、語調や文体では落とさない
5. **platform 制約チェック** — 対象 platform の contract（文字数・記法）に照合し、超えた候補は縮める
6. **候補を提示** — 手順 4 で残った候補を全部提示する。各候補に (a) 形、(b) 検索/フィードのラベル、(c) 素材の出どころ（Author's words / 本文の節 / 本文の実測）を 1 行添える。優劣は付けない
7. 公開記事のタイトルは、提示した全候補を `title-reviewer` へ渡す。tagline・subtitle・SNS 告知文はユーザーの選択で止まる

## タイトル以外への適用

- **README tagline**: 検索軸を「GitHub 検索・LLM 経由の発見」に読み替える。1 行目で「何のツールで誰向けか」（→ readme-writer と併用）
- **Substack subtitle**: title が概念、subtitle がベネフィット・状況の分担
- **SNS 告知文**: 記事タイトルの重複でなく、core claim の別の面を出す（同じ一行を 2 度見せない）

## Sources

- [The Upworthy Research Archive (Matias et al., Nature Scientific Data 2021)](https://www.nature.com/articles/s41597-021-00934-7) — 32,487 headline A/B テストの公開データ
- [Negativity drives online news consumption (Robertson et al., Nature Human Behaviour 2023)](https://www.nature.com/articles/s41562-023-01538-4) — ネガティブ語 +2.3%/語・ポジティブ語は低下
- [When curiosity gaps backfire: effects of headline concreteness on information selection decisions (Aubin Le Quéré & Matias, Scientific Reports 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11704130/) — 具体性とクリック率の山なりの関係
- [Qiita の全記事分析｜バズる投稿を考察する](https://qiita.com/mtitg/items/25e3d0d75429dcfeb199) — 日本語圏のタイトル字数帯
- Loewenstein, G. (1994). The psychology of curiosity — information gap 理論
- [How I Got 20,585 Substack Subscribers in 90 Days (Kaguura Gichuru, The Write Path 2026)](https://kaguura.substack.com/p/90-days-20585-new-subscribers-heres) — 結果駆動ヘッダー・A/B テストの実践知

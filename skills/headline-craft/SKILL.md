---
name: headline-craft
description: 「開かせる一行」を作る craft スキル — 記事タイトル・README tagline・Substack subtitle・SNS 告知文など、読者が開くかどうかを数秒で決める短文の候補生成と評価。Use when the user asks for タイトル案・キャッチコピー・タグライン・見出し候補・headline / title suggestions, or when a writing flow needs title candidates before publication. 技法カタログ（具体性・ベネフィット前置・誠実な好奇心ギャップ）× 流入経路 2 軸評価（検索/フィード）で候補を作り、最終判断はユーザーに委ねる。NOT for — 煽り・クリックベイトの生成（誠実さ規約は writing-ecosystem が正本）、Zenn の topics/emoji 最適化（→ project skill seo-optimizer）、platform 文字数制限の定義（→ 各 project overlay）。
user-invocable: true
origin: shimo4228
---

# Headline Craft — 開かせる一行を作る

読者は本文を読む前にタイトルで開くかどうかを決める。このスキルは「何を書いてはいけないか」（規範）ではなく「どう作るか」（技法）を担う。

**役割分担（defer 宣言）**:
- 誠実さ規約・AI slop 禁止リスト → `writing-ecosystem` の Title Conventions が正本。本スキルの全候補はあのフィルタを通ってから提示する
- platform 文字数・記法 → 各 project overlay（例: Zenn 50–60 字は `zenn-content/.claude/rules/zenn-writing.md`）
- Zenn の topics / emoji / キーワード含有 → project skill `seo-optimizer`（本スキルはそこから候補生成部として呼ばれる）

## 実証知見（技法の根拠）

- **ポジティブな飾り言葉は CTR を下げる**: Upworthy の約 10.5 万 headline 変種の分析（Robertson et al. 2023, Nature Human Behaviour）で、ポジティブ語の追加は消費率を下げた。「素晴らしい」「強力な」系の形容は削るのが正しい。※同研究はネガティブ語 1 語あたり CTR +2.3% も示したが、**恐怖・怒り駆動は誠実さ規約違反なので採らない**（問題の率直な記述と煽りは別物 — 「壊れている」は禁止、「〜でハマった」は事実なら可）
- **好奇心ギャップは情報の欠落**: Loewenstein の information gap 理論。知っていることと知りたいことの差が開かせる。ただし**本文が必ずギャップを埋めること** — 埋めない好奇心ギャップがクリックベイトの定義
- **日本語圏の参考値**: Qiita 全記事分析でバズ記事はタイトル 20–36 字に集中。上限（Zenn 50–60）より短い方に最適帯がある
- **トピック中心 → 結果駆動への進化**: タイトルは戦いの 90%。詩的タイトル（意味不明で素通り）と教科書調（「〜の分析」= 宿題感）が二大失敗形。具体的数値・明示的な価値・人間の声の 3 点が指を止める（Kaguura 2026, 90 日で 20,585 購読者の実践知）
- **タイトル A/B テストは読者関心の学習装置**: Substack はタイトル A/B テストを機構として持つ。目的は釣りの最適化ではなく「読者が実際に何に関心があるか」を学ぶこと（明快な解決型 vs 興味深いパラドックス型、等）。内容を変えず語選びを検証するのは Distribution 層で、Content Integrity（zenn-content ADR-0001）に適合する

## 技法カタログ

各技法に「適用条件」を付す。条件を満たさない技法は候補に使わない。

| 技法 | 型 | 適用条件 |
|---|---|---|
| **具体性** | 固有名詞・数値・状況を入れる（「LLM で」→「Claude Code の hooks で」） | 常時。迷ったらまずこれ |
| **結果駆動** | トピック名でなく読者が得る結果を言う（「Newsletter 成長モデルの分析」→「1,000 本を分析してわかった、登録が増える 3 つのレイアウト」） | 本文が実際にその結果を提供する |
| **ベネフィット前置** | 読後に読者が得るものを先頭側に（「〜する方法」より「〜できるようになる」の中身を言う） | 本文が実際にそれを提供する |
| **誠実な好奇心ギャップ** | 結論の手前まで言う（「試したら意外な結果になった」ではなく「試したら X だけが失敗した」） | 本文がギャップを完全に埋める |
| **対比・転換** | Before/After、期待と実際（「A だと思っていたが B だった」） | 実体験・実測が本文にある |
| **数字は証拠として** | 実測値・件数を事実として使う（「32,487 件の A/B テストが示す〜」） | 数字が主役化しない（「N 選」「N 倍速」は規約違反） |
| **自分ごと化** | 読者の状況を主語に（「毎回忘れる人のための〜」） | ターゲット読者が実在し、本文がその人に応える |
| **問いの形** | why / how の知的関心（「なぜ X は Y になるのか」） | 本文が答えを出す。煽り疑問（「まだ X してるの?」）は禁止 |

**削る技法（追加ではなく除去）**: ポジティブ形容詞（素晴らしい・強力な・完全な）、ヘッジ（〜について・〜の話・〜メモ）、冗長な前置き。削った字数を具体性に回す。

## 流入経路の 2 軸評価

候補は必ず両軸でラベル付けする。1 本のタイトルが両方を最大化することは稀で、どちらに寄せるかは記事の性質で決める。

| 軸 | 開く人 | 効く形 |
|---|---|---|
| **検索** | 問題を抱えて検索してきた人 | キーワード前置・答えの明示（「X で Y が失敗するときの直し方」）。エラーメッセージ・ツール名をそのまま入れる |
| **フィード** | 一覧を流し見している人 | 指を止める具体性・対比・好奇心ギャップ。既知トピックの意外な角度 |

目安: チュートリアル・トラブルシュート系 → 検索寄せ。体験記・考察・実測レポート → フィード寄せ。

## 手順

1. **core claim 抽出** — 本文（またはドラフト・要旨）から「読者が持ち帰る 1 つの主張・成果」を 1 文で書き出す。タイトルはこの 1 文の圧縮であり、本文にない約束をしない
2. **技法別に候補生成** — 技法カタログから適用条件を満たすものを選び、5 本以上生成。機械的に全技法を当てない（条件未達の技法はスキップ）
3. **誠実さフィルタ** — writing-ecosystem の Title Conventions（煽り・N 選・挑発・過度な省略の禁止）に全候補を照合し、違反を落とす
4. **platform 制約チェック** — 対象 platform の overlay（文字数等）に照合
5. **3 候補に絞って提示** — 各候補に (a) 使った技法、(b) 検索/フィードのどちら寄せか、(c) core claim をどう圧縮したか、を 1 行ずつ添える。現行タイトルがあれば比較を付す
6. **最終判断はユーザー** — 選択も混合（候補 A の前半 + B の後半）も可。勝手に確定しない

## タイトル以外への適用

- **README tagline**: 検索軸を「GitHub 検索・LLM 経由の発見」に読み替える。1 行目で「何のツールで誰向けか」（→ readme-writer と併用）
- **Substack subtitle**: title が概念、subtitle がベネフィット・状況の分担
- **SNS 告知文**: 記事タイトルの重複でなく、core claim の別の面を出す（同じ一行を 2 度見せない）

## Sources

- [The Upworthy Research Archive (Matias et al., Nature Scientific Data 2021)](https://www.nature.com/articles/s41597-021-00934-7) — 32,487 headline A/B テストの公開データ
- [Negativity drives online news consumption (Robertson et al., Nature Human Behaviour 2023)](https://www.nature.com/articles/s41562-023-01538-4) — ネガティブ語 +2.3%/語・ポジティブ語は低下
- [Qiita の全記事分析｜バズる投稿を考察する](https://qiita.com/mtitg/items/25e3d0d75429dcfeb199) — 日本語圏のタイトル字数帯
- Loewenstein, G. (1994). The psychology of curiosity — information gap 理論
- [How I Got 20,585 Substack Subscribers in 90 Days (Kaguura Gichuru, The Write Path 2026)](https://kaguura.substack.com/p/90-days-20585-new-subscribers-heres) — 結果駆動ヘッダー・A/B テストの実践知

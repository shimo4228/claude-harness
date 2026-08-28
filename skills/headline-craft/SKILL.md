---
name: headline-craft
description: 「開かせる一行」を作る候補生成スキル。記事タイトル・README tagline・subtitle・SNS告知文を、具体性・ベネフィット・誠実な好奇心ギャップ・検索/フィードの技法から生成する。Use when the user asks for タイトル案・キャッチコピー・タグライン・見出し候補、or a frozen draft needs title candidates. NOT for — 公開記事候補の点検（→ title-reviewer）、煽り・クリックベイト、topics / emoji、platform文字数の定義。
user-invocable: true
origin: shimo4228
---

# Headline Craft — 開かせる一行を作る

読者は本文を読む前にタイトルで開くかどうかを決める。このスキルは「何を書いてはいけないか」
（規範）でも「どれを採るか」（判定）でもなく、「どう候補を作るか」（生成）だけを担う。

**役割分担（defer 宣言）**:
- 誠実さ規約・AI slop 禁止リスト → `writing-ecosystem` の Title Conventions が正本。本スキルの全候補はあのフィルタを通ってから提示する
- platform 文字数・記法 → 各 project の publication channel contract。実値はここに書かない
- 公開記事候補の点検 → global `title-reviewer`。本 skill 自身の候補を自己採点しない
- topics / emoji → platform を所有する project-local skill

## 実証知見（技法の根拠）

- **ポジティブな飾り言葉は CTR を下げる**: Upworthy の約 10.5 万 headline 変種の分析（Robertson et al. 2023, Nature Human Behaviour）で、ポジティブ語の追加は消費率を下げた。「素晴らしい」「強力な」系の形容は削るのが正しい。同研究はネガティブ語による CTR 上昇も示したが、恐怖・怒り駆動は Title Conventions が禁じる。
- **好奇心ギャップは情報の欠落**: Loewenstein の information gap 理論。知っていることと知りたいことの差が開かせる。ただし**本文が必ずギャップを埋めること** — 埋めない好奇心ギャップがクリックベイトの定義
- **日本語圏の参考値**: Qiita 全記事分析でバズ記事はタイトル 20–36 字に集中。各 platform の上限より短い方に最適帯がある
- **トピック中心 → 結果駆動への進化**: タイトルは戦いの 90%。詩的タイトル（意味不明で素通り）と教科書調（「〜の分析」= 宿題感）が二大失敗形。具体的数値・明示的な価値・人間の声の 3 点が指を止める（Kaguura 2026, 90 日で 20,585 購読者の実践知）
- **タイトル A/B テストは読者関心の学習装置**: Substack はタイトル A/B テストを機構として持つ。目的は釣りの最適化ではなく「読者が実際に何に関心があるか」を学ぶこと（明快な解決型 vs 興味深いパラドックス型、等）

## 技法カタログ

各技法に「適用条件」を付す。条件を満たさない技法は候補に使わない。

| 技法 | 型 | 適用条件 |
|---|---|---|
| **具体性** | 固有名詞・数値・状況を入れる（「LLM で」→「Claude Code の hooks で」） | 常時。迷ったらまずこれ |
| **結果駆動** | トピック名でなく読者が得る結果を言う（「Newsletter 成長モデルの分析」→「1,000 本を分析してわかった、登録が増える 3 つのレイアウト」） | 本文が実際にその結果を提供する |
| **ベネフィット前置** | 読後に読者が得るものを先頭側に（「〜する方法」より「〜できるようになる」の中身を言う） | 本文が実際にそれを提供する |
| **誠実な好奇心ギャップ** | 結論の手前まで言う（「試したら意外な結果になった」ではなく「試したら X だけが失敗した」） | 本文がギャップを完全に埋める |
| **対比・転換** | Before/After、期待と実際（「A だと思っていたが B だった」） | 実体験・実測が本文にある |
| **数字は証拠として** | 実測値・件数を事実として使う（「32,487 件の A/B テストが示す〜」） | 数字が主役化しない（禁止の実値は `writing-ecosystem` Title Conventions） |
| **自分ごと化** | 読者の状況を主語に（「毎回忘れる人のための〜」） | ターゲット読者が実在し、本文がその人に応える |
| **問いの形** | why / how の知的関心（「なぜ X は Y になるのか」） | 本文が答えを出す。煽り疑問（「まだ X してるの?」）は禁止 |

**削る技法（追加ではなく除去）**: ポジティブ形容詞（素晴らしい・強力な・完全な）、ヘッジ（〜について・〜の話・〜メモ）、冗長な前置き。削った字数を具体性に回す。

## 流入経路の 2 軸ラベル

候補は両軸でラベル付けする。これは判定スコアではなく、候補の生成意図を `title-reviewer` と著者へ
伝える metadata である。

| 軸 | 開く人 | 効く形 |
|---|---|---|
| **検索** | 問題を抱えて検索してきた人 | キーワード前置・答えの明示（「X で Y が失敗するときの直し方」）。エラーメッセージ・ツール名をそのまま入れる |
| **フィード** | 一覧を流し見している人 | 指を止める具体性・対比・好奇心ギャップ。既知トピックの意外な角度 |

目安: チュートリアル・トラブルシュート系 → 検索寄せ。体験記・考察・実測レポート → フィード寄せ。

## 手順

1. **core claim 抽出** — 本文（またはドラフト・要旨）から「読者が持ち帰る 1 つの主張・成果」を 1 文で書き出す。タイトルはこの 1 文の圧縮であり、本文にない約束をしない
2. **技法別に候補生成** — 技法カタログから適用条件を満たすものを選び、5 本以上生成。機械的に全技法を当てない（条件未達の技法はスキップ）
3. **誠実さフィルタ** — writing-ecosystem の Title Conventions に全候補を照合し、違反を落とす
4. **platform 制約チェック** — 対象 platform の overlay（文字数等）に照合
5. **3〜6候補を提示** — 各候補に (a) 技法、(b) 検索/フィードのラベル、(c) core claim の圧縮方法を 1 行添える。優劣は付けない
6. 公開記事は候補群と現行タイトルを `title-reviewer` へ渡す。tagline / SNS など専用 reviewer が無い成果物はユーザー選択で止まる

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

# Style diagnostics

`writing-ecosystem` の原則だけでは具体的な slop / voice drift を特定できないときに読む診断表。
文字列 blacklist ではない。原稿固有の意味を持つ用例は残し、汎用評価・定型リズム・機械的な弱化だけを直す。

## Generic language

| Pattern | Replace with |
|---|---|
| 画期的 / 革命的 / 革新的 / game-changer / revolutionary | 従来との差分、観察、数値 |
| 素晴らしい / 驚くべき / powerful / robust | 何がどう良い、強い、予想外だったか |
| シームレス / seamlessly / effortlessly | 実際の操作と必要な手間 |
| 深い洞察 / 重要な示唆 / 本質的な問い | 洞察・示唆・問いそのもの |
| 最先端 / cutting-edge / ever-evolving | 何が新しく、いつの情報か |
| leverage / 活用する | 具体的な動作、または plain `use` |
| Moreover / Furthermore / It's worth noting | 接続を直接書くか削る |
| delve / multifaceted / holistic / transformative / pivotal / landscape / tapestry / unlock / harness / unleash / empower / paradigm | 原稿固有の名詞と動詞 |

## Structural tells

| Pattern | Diagnostic action |
|---|---|
| `It's not X, it's Y` / 「XではなくYだ」の反復 | 対比の型を外して主張を直接書く |
| 予告付きの3点列挙、同形のbold段落が3連以上 | 実在する分類だけ残し、段落の長さと形を変える |
| em dash、colon、semicolonによる等間隔リズム | 記号を置換せず、文を再構成する |
| proseで足りる箇条書き | 因果を文でつなぐ |
| `Great question` / 「素晴らしい質問」 | 本題から始める |
| `Hope this helps` / 「参考になれば」「いかがでしたか」 | 最後の実質的な文で終える |

## 専門用語の緩和

原稿に専門用語・造語・業界ジャーゴンが残っているときの手当て。組み合わせてよい。

- 初出で平易な言い換えを併記する
- 見出しから外し、本文に落とす
- 具体的な現象を先に見せ、名前は後からつける
- 一度定義したら同じ語を使い続ける（類義語に逃げない）
- 使い回さない語は捨てて平易に言い換える（回数の閾値は `prose-clarity-reviewer` が持つ）
- 確立した概念に由来するなら初出で系譜を示す。逆に界隈の定着語を和語に言い換えない
- 英語直訳語を疑う（floor →「床」）。意味の通る技術語に置き換える
- 英語の名詞句を 2 つ以上そのまま繋げない（「read-only な second opinion を一発で」）。
  固有名詞・製品名・コード内ラベル・一貫使用の定着語は例外

## 発見調の register

channel contract が発見調を宣言する場合だけ使う。

| 使う（発見調） | 避ける（根拠以上の宣言） |
|---|---|
| 「〜だった」「〜と気づいた」 | 「〜すべきだ」 |
| 「〜と感じた」「〜に見えた」 | 「〜に違いない」 |
| 「気づいたらそうなっていた」 | 「〜を示している」 |
| 「少なくとも方向としては悪くない」 | 「設計は正しかった」 |

## Assertion strength

- 検証済みの事実・数値・具体観察は断定する。
- 因果が推論なら「〜と読める」、評価を読者へ返すなら「〜ではないか」を使える。
- 同じ結論を疑問形で繰り返さない。問いは入口・転換・結論の必要な一箇所に置く。
- hedging を一律に足さない。未検証範囲と確信度を具体的に書く。

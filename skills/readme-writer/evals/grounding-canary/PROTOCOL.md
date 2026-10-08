# grounding canary 実験

AI アシスタントに repo の URL を貼ったとき、README のどこまで読むかを確かめる。
置き場所ごとに別のランダムな語を埋め、答えに出た語で「読んだ場所」を判定する。

| 記号 | 置き場所 | 正解 |
|---|---|---|
| V | README 冒頭（見える） | `kc-bfdf5a` |
| D | README 冒頭近くの `<details>` の中 | `424157.toml` |
| T | 約 2.6 万字の README の末尾（見える） | `@76e3ec` |
| L | llms.txt | `https://example.invalid/api/254665` |
| S | README からリンクした docs/setup.md | `KC_EAD177` |

## 手順

1. `repo/` を公開 repo `readme-fetch-canary` として push する（README に「実験用の架空のツール」と明記済み）
2. アシスタントごとに新しい会話を開き、下の質問を貼る。検索や web 機能は既定のまま
3. モデル名・設定（effort、一時チャットか）をメモに書く。取得の深さは設定で変わりうる
4. 答えを下の表に記録する。正解の語なら ○、別の語なら ×（作り話）、「見つからない」なら −

```text
https://github.com/shimo4228/readme-fetch-canary

Using only what you can read from this repository, answer:
1. What command prefix does the tool use?
2. What is the name of its settings file?
3. Who maintains it?
4. What API endpoint does it use?
5. Which environment variable must be set?
If you cannot find an answer, say "not found" rather than guessing.
```

質問の番号と置き場所: 1 = V、2 = D、3 = T、4 = L、5 = S。

## 記録

| アシスタント | 日付 | V | D | T | L | S | メモ（読んだと言ったファイル、取得の失敗など） |
|---|---|---|---|---|---|---|---|
| ChatGPT | 2026-10-08 | ○ | ○ | ○ | − | ○ | GPT-6・Plus プラン・一時チャット・effort 高。出典に README.md と docs/setup.md を挙げた。架空のツールである旨にも触れた |
| Claude.ai | 2026-10-08 | ○ | ○ | ○ | ○ | ○ | Opus 5.5・Max プラン・effort 中・シークレットモード。README.md / llms.txt / docs/setup.md を読んだと申告。README から llms.txt へのリンクは無い。docs/ の一覧は取れなかったと申告 |
| Gemini | 2026-10-08 | − | − | × | − | − | 3.6 Flash・無料プラン・一時チャット・effort 設定なし。V が − なので取得失敗の回。3 は URL の持ち主名（shimo4228）を答えた — 中身を読まずに URL から推測 |
| Gemini（2 回目） | 2026-10-08 | − | − | − | − | − | Pro を選んだが「アクセス集中」で Flash に切り替わり、全問 not found。2 回とも取得失敗 |
| Gemini（3 回目） | 2026-10-08 | ○ | ○ | ○ | ○ | ○ | 3.6 Flash・無料プラン・思考モード強化・通常チャット（一時チャットではうまくいかなかったため）。持ち主の実名にも触れた。1・2 回目との差は「一時チャット → 通常」と「思考なし → 思考強化」の 2 つで、どちらが効いたかは分けられない |
| Perplexity | 2026-10-08 | − | − | − | − | − | モデル指定なし・無料プラン・シークレットモードなし。中身を取得できず、検索の断片（repo の About 説明文）だけを見た。作り話はせず全問 not found |
| Grok | 2026-10-08 | ○ | ○ | ○ | ○ | ○ | 自動（おそらく 4.7）・X Premium・シークレットモード。途中経過で「The README is truncated, so I'm reading the rest of the repo files」— 最初の取得で README が切れ、自分で残りのファイルを取りにいった |
| Qwen | 2026-10-08 | ○ | ○ | ○ | ○ | ○ | Qwen3.7 Plus・無料プラン・Auto モード・一時チャット。持ち主の実名にも触れた（repo 外の GitHub プロフィールを見た可能性） |

## 読み方

- V が × か − なら、その回は取得に失敗している。ほかの列は読まない
- D が ○ なら、畳んだ中身は読まれる → 「上は人間、下は畳んだ LLM フロア」が成り立つ
- T が − で V が ○ なら、長い README は途中で切り詰められている → 全体の長さに上限が要る
- L と S は、README の外を読みにいくかを示す
- 2026-10-08 の分かれ方: 取得できた ChatGPT・Claude.ai・Grok は D も T も読んだ。Gemini（無料）と
  Perplexity（無料）は URL の中身を取得しなかった。効いている変数はモデルよりプランと取得経路の可能性がある
  （著者の見立て「無料プランだとほとんど検索してもらえない」）。著者の補正: 無料の Qwen は全 ○ で読んだので、有料か無料かより、無料プランにモデルを十分に使わせないプラットフォーム側の提供範囲の問題で、GitHub を LLM に聞く層は有料プランが主と見るのが妥当。Gemini と Perplexity は、索引が追いつく日を
  置いて同じ質問で再試行すると、「索引待ち」か「取得しない経路」かを分けられる
  著者の観察: Perplexity と Gemini は無料プランに制限をかけ、Perplexity は無料だとほとんど動かない
  Gemini は 3 回目（思考モード強化・通常チャット）で全 ○。取得の有無はプランより、一時チャットや思考なしのモードで取得機能が働かない、という提供側のモード設計で分かれる

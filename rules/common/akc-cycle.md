<!-- origin: shimo4228 -->
# AKC Rules (local edition)

Agent Knowledge Cycle の行動原則。**このファイルはローカル harness 版**で、6 phase の
解説本文は各 phase を担う skill 側に置いてある（この harness は全 skill を導入済みなので
本文の常駐が二重になる）。skill 未導入の環境向けの自己完結版は AKC repo の配布版が正本。

## Phase → skill 対応（トリガー時に呼ぶ）

| Phase | トリガー | skill |
|---|---|---|
| **Research** | 新規依存の追加 / 既存にありそうなユーティリティの自作前 | `search-first` |
| **Extract** | 非自明な解決・ハードな debug の直後、セッション終盤 | `learn-eval` |
| **Curate** | skill / rule が増えた、参照先が消えた、cleanup 依頼 | `skill-stocktake` / `rules-stocktake` / `config-gc` |
| **Promote** | 同じ助言が複数 skill・複数セッションに再出現した | `rules-distill` |
| **Measure** | rule を追加・変更した直後、遵守が疑わしいとき | `skill-comply` |
| **Maintain** | 大規模リファクタ後、context ファイルが肥大化 | `context-sync` |

Measure の注意: 遵守の確認は tool call だけでなく**エージェントの述べた理由と verdict のテキスト**
も見る（判断フェーズの遵守はツール痕跡に残らない）。
Maintain の注意: 同じ数値クレーム（モジュール数・テスト数・版番号）を 2 箇所に書かない。
正本を 1 つ決めて他はポインタにする。検証時は既存 doc の値でなく**ライブのコマンド出力**を信じる。

## Signal-first — 広く探し、狭く取り込む

調査の前に**シグナルを定義する**: どの情報が次の行動を変えるか。その外は今回のスコープ外。
探索は広く、intake は狭く。行動を変えない情報は保持に値しない — intake は人間の注意を
消費し、未消費の注意がこのサイクルの希少資源である。探索・学習フェーズは正当な例外だが、
例外を取るときは明示的にそう言う。

### Output discipline — 行動を変えるものだけ出力する

signal-first は出力にも適用する。下流（コードのゲート、人間の判断、次のステップ）が実際に
消費しないスコア・グレード・推薦を出してはならない。行動を変えない数値は足場である —
実際に行動を変える具体的な観察（「リードに誰向けか書かれていない」）に置き換える。
「Lead: 6/10」ではない。LLM のスコアリングは code-owned decision の入力
（judge + enforce）としてのみ正当。

## Scaffold Dissolution

これらの rule は足場である。実践を通じて内在化されるにつれ、rule は簡素化・削除されうる。
成功は rule の数ではなく、明示的な呼び出しなしにサイクルが自然に回るかで測る。

Dissolution には**2 つのベクトル**がある:

- **Inward** — 原則が会話パターンに吸収され、それを教えた rule が不要になる
- **Downward（substrate へ）** — 公式ハーネスがその領域をネイティブに扱うようになり、
  足場だった自作 rule に足すものが無くなる。ハーネスの案内は**常に読み込まれ**
  （tool description が system prompt に入る）進化を続ける。同じ領域を覆う手書き rule は
  静的で drift したコピーになり、新しい既定を**上書きして劣化させうる**。substrate が
  capability を吸収したら **rule を退役させる** — 古い影として residency させ続けない。
  構造的にハーネスができないこと（例: cross-model 脱相関）だけを残し、*why* は
  standing rule ではなく ADR に記録する

**モデル世代の交代も downward のトリガー**である。旧世代の弱さを補うための over-constraint
（強い禁止・網羅的手順・反復強調・使用例の列挙）は、判断力の上がったモデルでは衝突コストに
転じる。世代交代時は rule を再監査する（→ [ADR-0018](../../docs/adr/0018-rules-rightsize-for-claude5.md)）。

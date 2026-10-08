<!-- origin: shimo4228 -->
# tagline の eval — 著者に選ばせる前に候補を測る

Step 1 で著者が tagline を選ぶとき、候補だけでなく測った結果を一緒に渡す。読み手の好みは書き手の予想と
よく食い違い、現行の tagline が最下位に近いこともある。eval は決まった候補の中に順位を付け、推奨を 1 本に
するところまで。選ぶのは著者で、読み手の点は推奨の根拠にとどめる（rule evals.md: 判定の点数で登らない）。

## 入れる候補

- [skill: headline-craft] に tagline の候補を 9 本前後頼む（headline-craft は現行の tagline を比較の基準として
  1 本に含める）
- 著者の入口の語（Step 1 で聞いた、流入経路で探される語）は、すべての候補に含める。扱いは `visitor-read.md` の
  「新しい機能の語」
- 主張はコードと計測に照らしてから候補に入れる（headline-craft の「誠実さの照合」）。数字は計測の値と一致させる
- 途中で候補を足してよいのは、段 1 で出た取り違えを直した案と、入口の語を入れ忘れた案を直した案だけ

## 読み手

- 読み手は、著者の CLAUDE.md・rules・skill を読み込まない隔離した `claude -p` で走らせる。設定を読み込んだ
  読み手は著者の語彙を知っていて、初見の読者にならない
- 人物は `visitor-read.md` の「訪問者を 3 人選ぶ」で選ぶ（訪問者役の読みを回さない回も同じ手順）。流入経路が
  新機能の一覧なら、その機能を探して回っている人を 4 人目に加える

```bash
claude -p --setting-sources "" --strict-mcp-config --tools "" --model sonnet \
  --system-prompt "You are <persona>. Answer as that person would, honestly." "<prompt>"
```

数十回を並列に呼ぶので、出力はファイルに書き、壊れた JSON は集計で読み飛ばす。

## 3 段で測る

1 ラウンドは、決まった候補の組に対する段 2 の 1 周（人物 × 並び順）か、段 3 の 1 周（ペア × 左右 × 人物）。

**段 1 ふるい — 何のツールか分かるか。** repo 名と tagline の 2 行だけを見せる。正解の要素（例: 何のツール /
何を変える / どの単位で / 何が元になる）は、書き手が Step 1 の「何をするものか」の割り振りから書く（既存の README の
冒頭の段落を主張ごと残すときは、その段落から書いてよい）。採点は別の呼び出しの採点役が 0/1 で付ける。取り違え（別の製品に読まれる）が出た候補を落とすか直す。強い読み手ではほぼ全候補が満点になり差が
出ないので、ここは足切りにだけ使う。

```
On GitHub you land on a repository page. Before scrolling, you see only the repo name and the one line under it:

{REPO_NAME}
{TAGLINE}

Based ONLY on these two lines, answer in JSON only, no code fence:
{"what_it_is": "<one sentence>", "who_its_for": "<one phrase>",
 "what_changes_if_installed": "<one sentence>", "confusing": ["<unclear words or ideas>"]}
```

**段 2 順位 — どれを開くか。** 候補を A・B・C… の記号付きで並べた一覧を、並び順を変えて人物ごとに 6 回以上
見せる。良い順に 3 本と開かない 2 本を選ばせ、3・2・1 点と −2 点で合計（Borda）し、上位 2〜3 本を段 3 へ送る。

```
A project on GitHub is called {REPO_NAME}. Its author is choosing the one line that appears right under the
repo name. Here are the alternatives:

{LETTERED_LIST}

You know nothing else about the project. Pick the 3 lines that would most make you open the repo and keep
reading (best first), and the 2 that would least. Judge by what you would actually do, not by writing style.
Answer in JSON only, no code fence:
{"best": ["<letter>", "<letter>", "<letter>"], "worst": ["<letter>", "<letter>"], "why_best": "<one sentence>"}
```

**段 3 決着 — 1 対 1。** 上位の 2 本ずつを、左右を入れ替えて同じ回数ずつ見せ、勝ち数で決める。順位は候補の
組み合わせで入れ替わる（一覧の中の相対で選ばれる）ので、推奨はこの段で決める。読み手には 2 番目を選ぶ偏りが
強く出るので、左右を入れ替えて揃えた結果だけを数える。

```
A project on GitHub is called {REPO_NAME}. You see it in a list with one line under its name. Which line would
more make you open it and keep reading?

1. {TAGLINE_LEFT}
2. {TAGLINE_RIGHT}

Answer in JSON only, no code fence: {"pick": 1 or 2, "why": "<one sentence>"}
```

**止めどき**: 左右を入れ替えた 16 回以上で、片方が 4 分の 3 以上勝ったら決着（例: 18 対 0 は決着、11 対 7 は
互角）。互角のペアは、他言語版と主張を揃える側を推奨にし、互角と明記して著者に渡す。
上限は 5 ラウンド。

## 著者に渡すもの

Step 1 の著者確認に、次の 3 つを載せる:

- 推奨の 1 本と次点（互角ならそう書く）
- ラウンドごとの表（候補 / Borda / 1 位の回数 / 1 対 1 の勝敗）
- 段 1 で出た取り違えと、読み手が分からないと挙げた語（入口の語を除く）

他言語版の tagline は、人物を他言語の読み手に替えて同じ手順で測る。決着しなければ、主張を揃えた訳を推奨にする。

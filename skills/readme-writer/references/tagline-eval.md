<!-- origin: shimo4228 -->
# tagline の eval — 著者に選ばせる前に候補を測る

Step 1 で著者が tagline を選ぶとき、候補だけでなく測った結果を一緒に渡す。読み手の好みは書き手の予想と
よく食い違い、現行の tagline がほとんど選ばれないこともある。eval が作るのは、取り違えられる候補の足切りと、読み手がどう
割れたかの記録まで。選ぶのは著者で、推奨は付けない（skill `eval-foundations`: 上限を選ぶ判定は一つの目に残す）。

## 入れる候補

- [skill: headline-craft] に tagline の候補を頼む（仮説の群ごとの代表で、現行の tagline を比較の基準として
  1 本に含める）
- 著者の入口の語（Step 1 で聞いた、流入経路で探される語）は、すべての候補に含める。扱いは [skill: persona-read-loop] の
  readme preset「Feature names newer than the reader model」
- 主張はコードと計測に照らしてから候補に入れる（headline-craft の「約束の監査」）。数字は計測の値と一致させる
- 途中で候補を足してよいのは、段 1 で出た取り違えを直した案と、入口の語を入れ忘れた案を直した案だけ

## 読み手

- 読み手は、著者の CLAUDE.md・rules・skill を読み込まない隔離した `claude -p` で走らせる。設定を読み込んだ
  読み手は著者の語彙を知っていて、初見の読者にならない
- 人物は [skill: persona-read-loop] の readme preset「Readers」で選ぶ（訪問者役の読みを回さない回も同じ手順）。流入経路が
  新機能の一覧なら、その機能を探して回っている人を加える
- 読み手の model は同じ preset の選び方（読みの深さ）で決め、同じ候補の組を測るあいだは変えない

```bash
cd "$(mktemp -d)" && CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
  claude -p --setting-sources "" --strict-mcp-config --tools "" --model <model> \
  --system-prompt "You are <persona>. Answer as that person would, honestly." "<prompt>" < /dev/null
```

空の一時ディレクトリから auto memory を切って起動する（`--setting-sources ""` だけでは cwd の project の auto memory が
読み手に届く）。隔離は [skill: persona-read-loop] の `scripts/read.sh --probe` で確かめる。

多数回を並列に呼ぶので、出力はファイルに書き、壊れた JSON は集計で読み飛ばす。

## 3 段で測る

1 ラウンドは、決まった候補の組に対する段 1 → 段 2 → 段 3 の一通り。候補を足したときだけ次のラウンドを回す。

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

**段 2 一覧 — どれを開くか。** 候補を A・B・C… の記号付きで並べた一覧を、並び順を変えて人物ごとに繰り返し
見せ、良い順に 3 本と開かない 2 本を選ばせる。候補ごとに、1 位に選ばれた回数と開かない側に選ばれた回数を人物別に数える。
点に換算して合計しない。

- 落とす候補: どの人物についても、開かない側に選ばれた回数が 1 位に選ばれた回数を上回った候補
- 段 3 へ送る候補: 人物ごとに、1 位に選ばれた回数がいちばん多い候補（同数は全部）。その和集合を送る。人物のあいだで
  1 位が割れたら、割れたまま全部を送る
- 落とした候補と送らなかった候補も、人物別の回数と一緒に著者に渡す

```
A project on GitHub is called {REPO_NAME}. Its author is choosing the one line that appears right under the
repo name. Here are the alternatives:

{LETTERED_LIST}

You know nothing else about the project. Pick the 3 lines that would most make you open the repo and keep
reading (best first), and the 2 that would least. Judge by what you would actually do, not by writing style.
Answer in JSON only, no code fence:
{"best": ["<letter>", "<letter>", "<letter>"], "worst": ["<letter>", "<letter>"], "why_best": "<one sentence>"}
```

**段 3 1 対 1。** 段 2 から送った候補のすべての組を、人物ごとに、左右を入れ替えた 2 回を 1 セットとして見せ、
セットごとの答えを人物別に記録する。セットの数は実行者が決め、同じラウンドの中では全部の組と人物で揃える。
一覧での順は候補の組み合わせで入れ替わる（一覧の中の相対で選ばれる）ので、2 本のどちらが選ばれるかはこの段の記録で見る。
読み手には 2 番目を選ぶ偏りが強く出るので、左右を入れ替えて揃えた結果だけを数える。

```
A project on GitHub is called {REPO_NAME}. You see it in a list with one line under its name. Which line would
more make you open it and keep reading?

1. {TAGLINE_LEFT}
2. {TAGLINE_RIGHT}

Answer in JSON only, no code fence: {"pick": 1 or 2, "why": "<one sentence>"}
```

**記録の読み方**: ある人物が、どのセットでも左右どちらに置いても同じ候補を選んだら、その人物の中では決着。左右で答えが
入れ替わったセットがあれば、その人物の中では割れ。全員が同じ候補で決着した組だけを「読み手の中で決着」と記録し、
ほかの組は人物ごとの内訳と理由を付けて「割れ」と記録する（人物によって逆の候補で決着した組も割れ）。

**止めどき**: 足してよい候補（「入れる候補」のとおり）が無くなったら止める。

## 著者に渡すもの

Step 1 の著者確認に、次の 3 つを載せる:

- 読み手の中で決着した組と、割れた組（人物ごとの内訳と、読み手が書いた理由）
- ラウンドごとの表（候補 / 1 位の回数 / 開かない側の回数 / 1 対 1 の勝敗）
- 段 1 で出た取り違えと、読み手が分からないと挙げた語（入口の語を除く）

他言語版の tagline は、人物を他言語の読み手に替えて同じ手順で測り、結果を並べて渡す。言語間で主張が揃う組み合わせには印を付ける。

---
name: jev-judgment-design
description: >
  LLM がしていた閉じた判定（この資料は関係あるか・新しいか・どれだけ強い証拠か）を TypeSafe の Jev に
  移すときの、判定の渡し方と採否の決め方。何に対して判定するかを state に入れる、Score の最下段、
  Jev が答えコードが決める、判定の単位、通るべき資料（canary）、Pydantic AI からの呼び方。
  Use when — 「LLM の判定を Jev に置き換えたい」「Jev で関連性の判定を組んで」「Jev の判定が何でも
  通してしまう」、または Jev を screening / triage / rerank に組み込む設計の前。
  NOT for — Jev の API・docs・プリミティブ選びの一般指針（→ plugin skill `typesafe:typesafe-ai`。
  先にそちらを読む）、Claude Code のスキル選択 hook（→ `jev-skill-router`）、LLM を判定器にする
  設計（→ `llm-as-judge`）。
user-invocable: true
origin: shimo4228
---

# Jev judgment design

Jev は閉じた質問に確率で答え、文章を書かない。LLM パイプラインの判定を Jev に移すと、判定は安く
並列になるが、Jev は渡された state の中だけで答える。この skill は、その state と、答えから採否を
決める側の設計を持つ。Jev の一般的な設計指針（state / instructions / criteria、Choice・Noul・Score
の選び方、no-match、閾値は自分のデータで）は plugin skill `typesafe:typesafe-ai` が正本なので、
先にそれを読み、ここは上に重ねる判断だけを読む。

出所は jev-research-pipeline（https://github.com/shimo4228/jev-research-pipeline）の実装と、記事
「LLMに任せていたリサーチの判定を、判定専用モデルJevに移す」
（https://zenn.dev/shimo4228/articles/jev-research-judgment-offload、2026-09-25 公開予定）。

## 1. 移すのは閉じた判定だけ

はい・いいえの確率、選択肢から 1 つ、段階評価のどれかで答えが言える判定を Jev に移す。次に
どこを探すか、どう書くかのように答えの形が開いた仕事は LLM に残す。移した後の計器は「Jev への
質問数」でなく「実行中の LLM の判断の回数」で見る — Jev の質問数は移した判断の分だけ増えてよい。

## 2. 何に対して判定するかを state に入れる

「関係あるか」は、比べる相手が state に無いと、語を共有するものを何でも通す。Jev は聞かれた
とおりに答えているので、直すのは質問でなく state の側。比べる相手は、そのテーマで**いま答えを
探している問い**にし、範囲・除外・採用済みの証拠を一緒に渡す。

```python
state = {
    "question": {
        "title": question.title,        # いま答えを探している問い
        "brief": question.brief,        # 範囲
        "evidence": question.evidence,  # 証拠として数えるもの
        "not": question.negative_topics,  # 語は重なるが対象でない話題
    },
    "source": {"title": ..., "url": ..., "excerpt": ...},
    "evidence_set": accepted_claims,    # この問いで採用済みの証拠（新しさの基準）
}
```

- `not` には、隣の話題でとくに紛れやすいものを書く（例: 意図整合の問いに対する「モデル単体の
  alignment 訓練」— alignment を題名に含む資料の多くは cross-modal alignment のような語の一致だった）
- 新しさは「このテーマにとって新しいか」でなく「`evidence_set` に何を足すか」で聞く

## 3. Score の最下段に「語を共有するだけ」を置く

近さを段階で聞くときは、いちばん下に「語を共有するだけの別の問題」を置く。この段が無いと、
Jev は近い段に寄せるしかない。

```python
class Overlap(UseEnumMemberDocstrings, IntEnum):
    other_problem = 0
    """It works on a different problem that happens to share vocabulary."""
    same_field = 1
    """Same field as `question`, but not the problem `question` asks about."""
    same_problem = 2
    """It works on the problem `question` asks about, from another angle."""
    same_question = 3
    """It asks what `question` asks and reports an answer to it."""
```

実測（2026-09-23、1 つの問いに「intent」を題名に含む 3 本）: 0.60 で other_problem / 0.53 で
same_field / 0.77 で same_problem に分かれた。語が同じでも、問いと並べると段が分かれる。

## 4. Jev が答え、コードが決める

採否は Jev の出力でなく、コードが閾値をかけて決める。

- **足切り（gate）と並べ方（placement）を分ける。** Noul の確率（関係ありか、方法は使えるか、
  証拠の種類は合うか）は足切りだけに使い、落とすことしかできない。Score の段階の重み付きは
  並べ方と採用線に使う。足切りを重み付きに混ぜると、強い段が弱い足切りを補ってしまう
- 実測（2026-09-23）: 段階 same_problem 0.77 の資料が、関係ありの確率 0.44 で足切り 0.5 に届かず
  不採用になった。段階と「関係ありか」は別々の答えとして扱う

## 5. 判定の単位は「資料 1 件 × 問い 1 つ」

- 文を 1 つずつ切り離して聞く設計は、文脈が落ち、質問数が文の数だけ膨らむ（1 テーマ 1 回で
  2 万問・レポート 283 KB の実例）。単位は資料 1 件にする
- 段を 2 つに分ける: まず資料 1 件ごとに、全部の問いについて「関係しそうか」を 1 request で
  安く聞いて候補を絞る。残った「資料 × 問い」の組だけを詳しく聞く。文の単位が要る判定
  （問いを進める文か、資料が本当にそう言っているか）は、採用した資料の中でだけ行い、文字列で
  照合できる部分はコードが先に照合する

## 6. 通るべき資料（canary）を置く

絞り込みで量が減っても、読むべき資料まで落としたのかは量では分からない。問いごとに「これは
通るべき」と分かっている資料を数件置き、毎回の実行で通ったかを記録する。canary が落ちたら、
閾値より先に state（`brief` / `not`）を疑う。

## 7. Pydantic AI から呼ぶ

Pydantic AI の TypeSafe model（as-of 2026-09-23、https://pydantic.dev/docs/ai/models/typesafe/）:

```python
from pydantic_ai import Agent

agent = Agent("typesafe:jev-1.13.0", output_type=Answers)
run = await agent.run(json.dumps(state, ensure_ascii=False, sort_keys=True))
dist = run.response.provider_details["probabilities"]
```

| 出力型の field | Jev のプリミティブ |
|---|---|
| `float`（`ge=0, le=1`） | Noul（「はい」の確率） |
| `Literal[...]` / 文字列 Enum | Choice |
| docstring 付きの `IntEnum` | Score |

- 版は pin する（閾値はその版に対して合わせたもの）。`run.response.model_name` が pin した版と
  一致するかをコードで確かめる
- 確率・分布は `provider_details` から読み、`run.output` の丸めた値だけで採否を決めない

## 8. 探す・書くは LLM に残し、モデルは文字列で差し替える

実行中に使う LLM も同じ `Agent` から呼ぶと、判定の型を変えずに書くモデル・検索語を作るモデル
だけを文字列 1 つで差し替えられる。問いや検索語のように実行前に 1 回作れば
よいものは、実行の外で強いモデル（Claude 等）に書かせてファイルに置き、実行中の LLM 呼び出しから
外す。

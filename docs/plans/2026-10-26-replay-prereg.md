kind: internal
# 再生比較の事前登録 — judge が実装する形は、packet で dispatch する形より悪くならないか

Plan: [subagent-fold.html](../subagent-fold.html) claim 3・4。決定（2026-10-26 承認）: seed = 台帳を全部判定してから、
count = 8、rule = 数と原因の両方、executor = この session。この文書は run の前に commit し、結果を見てから変えない。

## 対象

contemplative-agent の過去の build タスク 8 件（`~/.claude/scripts/replay/tasks.tsv`）。選んだ基準は「追跡ファイルと
テストだけで閉じる」— ローカルモデルの測定・本番データ・Linux CI が要る packet（rfc-0040-a/c、0045-a、0046-b/c、s35、
s-ci-1、rfc-0040-b）は外した。

| id | packet | base | 正解 | 種別 |
|---|---|---|---|---|
| s1 | rfc-0017-s1 | 4bd016a7 | b5228220 | wiki store（LLM なし） |
| s2 | rfc-0017-s2 | b5228220 | 7ea1ed95 | Maintainer ループ |
| s3 | rfc-0017-s3 | 7ea1ed95 | 5b5ddd44 | Proposer ループ |
| s4 | rfc-0017-s4 | 5b5ddd44 | 14fe9d0d | replay harness |
| a | rfc-0022-a | 28376ed2 | 0d496284, 6dd989fb | Maintainer の作り直し |
| a1 | rfc-0022-a1 | ec0e76eb | 6057dd88, c3679626 | ページ長と catch-up |
| s29 | rfc-0046-a | 24024119 | 5cf42b7b | relevance shadow |
| s32 | rfc-0046-d | 73a56f82 | 6685e756 | 定義の統一（fix） |

wiki の 6 件は同じ RFC 系統で、互いに相関する。

> **注記（2026-10-26、s3・s4 の最初の run の後）**: s3 と s4 の base を、正解 commit の直接の親（7ea1ed95 / 5b5ddd44）に直した。
> 最初に置いた c1f82499 / 87e6c247 は main 側の docs commit で、S1〜S4 は merge で main に入ったため S2・S3 のコードを含まない。
> 両形とも Phase 0 で「前提の S1〜S3 が無い」と正しく止まった。この 4 run は比較から外し（`replay-runs/discarded-wrong-base/`）、
> 直した base で回し直す。base の規則は「正解の最初の commit の親」。例外は a で、packet が明記する main 28376ed を使う
> （正解の親 5a23ec34 との差は skill の docs 1 commit）。

## 2 つの形

- **packet（旧形）**: fresh な `claude -p` が packet だけを読んで実装する。
- **judge（新形）**: 同じ `claude -p` が、まず台帳 `rfcs/` の開いたタスクを全部読んでコードと照合し判定を書き、
  その後同じ session で同じ packet の内容を実装する。

両形とも model は Opus（settings の effort）、permission は auto mode、実 repo・過去 transcript・GitHub は deny、
smoke（Ollama・`claude -p`・本番 `MOLTBOOK_HOME`）は回さない。違いは「実装の前に判定で積んだ context」だけ。
新形も packet を受け取るので、この比較が測るのは **context の大きさと判定の文脈が実装を悪くするか** であり、
judge が自分で packet 相当の設計を書けるかは測らない。

各タスク各形 2 run、計 32 run。

## 採点（`grade.py`）

- run の合格 = 漏れが無い ∧ `.claude/verify.sh`（引数なし）が exit 0 ∧ codex の判定が pass（受入条件の unmet が 0）
- 正解 commit のテストを後から置く検査（tests）は補助の読み値。関数名の一致に依存し、両形とも落ちうるので合否に入れない
- 漏れ = tool 入力に実 repo の path・`.claude/projects/`・GitHub の repo・`gh` が現れた run。該当 run は失格とし、合否の数から外して別に数える
  > **注記（2026-10-26、最初の 2 run の採点後・比較の前）**: 漏れの検出を直した。`.claude/projects/` は run 自身の session が
  > 大きな tool 出力を退避するファイル（`…replay-runs-<run-id>/…/tool-results/`）にも当たり、`gh` は判定中の upstream PR の確認
  > （`gh pr view … --repo ollama/ollama`）に当たった。どちらも答えに届かないので、`.claude/projects/` は自分の session の
  > 退避ファイルを除き、`gh` の汎用パターンは外して `shimo4228/contemplative-agent` への接触だけを数える。両形に同じく効く
  > **注記（2026-10-27、28 run の後・codex の判定の前）**: 漏れの検出をもう一段直した。GitHub の URL は s29 の 4 run が
  > ADR の `graph.jsonld` ノードの `@id` に書いた文字列に当たり、`.claude/projects/` は run 自身の session ディレクトリへの
  > `cd` に当たった（どちらも答えに届かない）。数えるのは repo を取りに行く操作（clone・fetch・curl・wget・gh）と、他 session の transcript だけにする
- verify は正解 commit の木でも回し、正解でも落ちる検査（a / a1 の `test_environment_is_an_allowlist` と eval-staleness —
  この環境と評価の基準線の側の理由）は run の失敗に数えない。run の verify は「正解の木に無い失敗が増えたか」で読む
- **判定役を codex から Claude Fable 5.1 に替えた（2026-10-27、判定の結果を読む前）**: codex は gpt-6-astra しか使えず（他の
  model は 400）、5 時間の枠で 2〜3 本で利用上限に達した（03:45 と 08:53 の再試行指示）。37 本の判定は数日かかる。Fable は
  実装者（Opus）と同系統で、独立性は下がる。ただし偏りは両形に同じく効くので、2 形の差は読める。全 run と正解 8 本をそろえて
  Fable で判定し（`claude -p --model fable`、hook と user 設定なし、read-only の git と Read だけ）、codex で判定できた 5 本は
  一致度の確認にだけ使う。正解 s1 は Fable で unmet 0（codex では 8）
- codex の model は `gpt-6-astra` を明示する（`~/.codex/config.toml` の固定 model が ChatGPT 認証で 400 を返した）
- 正解 commit を同じ codex の判定にかけ、判定の厳しさの基準線として記録する（合否の規則は変えない）
- verify が exit 2（検査不能）の run は、その原因を読んで記録し、合否の数から外す

## 切り替えの規則

1. 新形の失敗数が、旧形の失敗数を超えない（8 件 × 2 run の各 16 run のうち）
2. 新形だけが落ちたタスクは、trace を読んで原因を書く
3. 原因が judge の context の大きさなら、その種類のタスクは dispatch に残す
4. 旧形の 2 run の間の揺れ（片方だけ落ちたタスクの数）を、ノイズの幅として記録する

1 を満たせば task-triage の既定を「judge が実装し、例外だけ dispatch」に替える（plan claim 4.2）。1 を満たさなければ替えず、
2 の原因を報告する。8 件 × 2 run では非劣性を統計で示せない — 数は規則 1 の判定にだけ使い、読みは成否が変わったタスクの原因に置く。

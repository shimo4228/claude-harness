# ADR-0047: learned/ ノート置き場を退役し、Save の行き先を到達可能な資産だけにする

## Status

accepted

## Date

2026-08-23

## Context

`~/.claude/skills/learned/` は learn-eval が抽出したパターンの保存先だった。ディレクトリ形式の
skill ではなく flat な `.md` 置き場で、全ファイルが `user-invocable: false`。つまり slash 入口も
description トリガーも持たない。learn-eval 自身がこれを明記していた —
「description-based automatic triggering never fires — the file remains a passive reference note
found only by grep」。

2026-08-23 の skill-stocktake full で 11 件を内容判定し、当初 8 件を Keep とした。その根拠は
「他の資産が同じ内容を持たない」だけで、**届くかどうかを見ていなかった**。著者の指摘を受けて
`metrics/skill-usage.jsonl` を実測した。

計器に癖があった: `skills/learned/foo.md` の Read は `log-skill-usage.sh:123` がディレクトリ形式と
みなしてトップ階層を取るため、skill 名 `learned` として記録される。note 単位で数えると全件 0 に
見え、これは計器死亡だった。正しく数えると 184 read。

そのうえで内訳を出した（ログ開始 2026-06-10 から 74 日）:

- **161/184 が 6 つの大監査日に集中**（config-gc + skill-stocktake + rules-distill + skill-health が
  同日に走った日）。learned note を読んでいるのは、主に**それを残すか判断する処理そのもの**
- 実作業中の repo で読まれたのは **12 回**、8 note に分散。うち 4 note は過去の stocktake で退役済み
- 現存 11 件のうち 8 件は 74 日間で実作業の read が **0**

ここで一度、実作業 read の多寡（3 / 1 / 1 / 0×8）で残す note を選ぼうとしたが、著者に反証された:
**reachability は learned/ というディレクトリの属性であって note ごとに違わない**。定数は判定軸に
ならず、74 日 12 イベントを 8 note に散らした標本の 0 と 1 の差は「その話題が何回起きたか」を
測っているだけで、note の価値を測っていない。判定は内容だけで行うべきだった。

内容で見直すと、強い 4 件（実測 tiktoken 定数、Chrome bridge の環境固有の罠、MD040 のファイル破壊、
sweep の symlink / sanitize 制約）、弱い 4 件、**内容が偽の 2 件**（`--max-turns` が「削除された」と
書いてあるが CLI 2.1.241 で実行確認して偽 / 閾値の根拠が 200K context 前提で 1M 化により崩壊）に
分かれた。grep で当たる前提なら、間違った note は無い note より悪い。

著者の判断は「learned ごと畳む。とりあえず入れておく経路も消す」。

## Decision

1. `~/.claude/skills/learned/` を全件削除する（11 件）。
2. **learn-eval から learned/ 行きの経路を撤去する。** Save の行き先は 2 つだけ:
   - **Absorb** — 既にその話題を持つ skill / rule / doc の節に追記する（既定）
   - **Promote** — 独立トリガーがあるなら skill: `skill-creator` を通して skill にする

   どちらでもなければ verdict は **Drop**。「とりあえずどこかに置く」を選択肢から外す。
3. learn-eval に **reachability check** を置く。Save の後、「次のセッションで何がこの内容へ
   ルーティングするか」を 1 行で言えなければ Save が誤り。言えないなら Step 3 へ戻る。
4. 消費側の配線を外す: `skill-stocktake`（Phase 1 の列挙・canonical key・batch interleave・
   Phase 3 の promotion residue）、`rules-distill`（scan scope）、`collect-context`（検索対象）、
   `python-patterns`（「レシピの正本は learned note」参照）、`hooks/README.md`（Related link）、
   `scripts/hooks/harness_lint.py`（origin 検査対象・LINK_SCOPES・skills 走査の除外分岐）。

## Review-when

- learn-eval の Save が Drop ばかりになり、実際に残すべき知見が捨てられ始めたとき
  （= Absorb 先を探す手間が Drop への逃げを生んでいる兆候）
- 逆に Absorb が肥大の入口になり、既存 skill が雑多な追記で読めなくなったとき
- substrate が「セッション横断で参照される受動ノート」を native に扱えるようになったとき
  （grep 依存という前提そのものが消える）
- project 側の `.claude/skills/learned/` を持つ repo で、同じ実測（監査 read が支配的か）を
  取って別の結論が出たとき

## Alternatives Considered

**強い 4 件を残す**（本セッションで一度推奨した案）。実作業 read の実績で選別する形だったが、
上記のとおり reachability が定数である以上その差はノイズで、選別の根拠にならない。内容で選ぶなら
残す理由はあったが、それは「grep で当たれば価値がある」という条件付きの価値で、条件を満たす経路が
無いまま維持コストだけが残る。

**負の 2 件だけ直す**。`--max-turns` の semantics と 1M 時代の閾値を実測し直せば正しくなる。ただし
その実測は、74 日で実作業 read が 1 回の note のために取ることになる。費用が見合わない。

**learned/ を残して description を付け user-invocable にする**。トリガー面を 11 本増やすことになり、
自発トリガーの実質上限 ≒40%（ADR-0046）を考えると、既存 skill の選択を薄めるだけで届く保証がない。

**強い 4 件を skill に昇格する**。`documented-invariant-lint-gates` は `python-patterns` が正本として
参照しており独立トリガーもあったので候補だったが、著者は一緒に削除を選んだ。昇格したい内容が
後で出たら、learn-eval の Promote 経路（skill-creator 経由）が同じことをする。

## Consequences

**得るもの**

- Save に「行き先が無い」状態が構造的に作れなくなる。到達しない知識の在庫が増えない
- 監査コストの削減。stocktake / rules-distill / config-gc / skill-health が毎回 learned/ を
  走査していた分（大監査日 1 回あたり 17–39 read）が消える
- 内容が偽のまま grep で当たる note が 2 件消える

**払うもの**

- 実測値 4 件（tiktoken の CJK chars/token 表、Chrome bridge の修復手順、MD040 の sed 罠、
  sweep の symlink / sanitize 制約）を失う。再取得には実測が要る
- learn-eval の Save が重くなる。Absorb 先を探すか skill-creator を通すかの判断が毎回入り、
  「とりあえず保存」より摩擦が大きい。これは意図した摩擦だが、Drop が増える副作用は上の
  Review-when で監視する
- project repo（zenn-content / aeon-shop 等）の `.claude/skills/learned/` は本 ADR の対象外で、
  global と project で learn-eval の挙動が食い違う期間が残る

**上書きする判断**

[ADR-0025](./0025-global-vs-project-asset-placement.md) の Global/Project 配置規則は、learned note に
関する部分だけ本 ADR が上書きする（skill / rule / agent の配置規則は有効）。

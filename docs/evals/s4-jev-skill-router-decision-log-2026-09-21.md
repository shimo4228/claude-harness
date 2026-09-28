---
origin: shimo4228
instrument: jev-skill-router の判定ログ（decisions.jsonl、shadow mode）
subject: jev-skill-router（UserPromptSubmit hook が TypeSafe Jev に skill を 1 本選ばせる判定）
validity: 単発
source_type: documentation
evaluator_relationship: first_party
eval_library:
  name: jev-skill-router
  version: 0.2.0（router_version。先頭 19 行は 0.1.0）
evaluation_timestamp: 2026-09-21T05:42:42Z/2026-09-28T09:44:24Z
retrieved_timestamp: 2026-09-28
num_samples: 1242
execution_command: "python3 <script> 1242   # <script> は本カード「生の読み値」節の Python。1242 は数える行数"
log_updates: []
---

# s4 — jev-skill-router の判定ログ（2026-09-21〜28、shadow 7 日）

skill 選択を外部の判定 API（TypeSafe の Jev）に送る hook を shadow（判定をログに書くだけで、model の文脈へは何も足さない）で 7 日回した
判定ログの schema と読み値の記録。hook の設計は [ADR-0074](../adr/0074-jev-skill-router-prompt-to-external-judge-shadow-first.md)、
ログを判定の registry の最小形とする位置づけは [RFC-0025](../../rfcs/0025-jev-decision-contract-registry.md) が持つ。
2026-09-28 に著者判断で plugin をローカルで無効化した（`enabledPlugins` を false。RFC-0025 の Status）。
`evaluation_timestamp` はログの先頭行と、判断役が読んだ時点の 1,242 行目の `ts` を ISO 8601 の区間で書いた。

## 設計

- 問い: ユーザーの prompt ごとに Jev が選んだ skill（高々 1 本）が、そのあと実際に使われた skill とどれだけ重なるか。
  ADR-0074 はこのログを「model が skill を取りこぼしているのか、skill を読まずに自分でやっているのかを見分ける計器」として残した
- 判定の手順（TypeSafe の skill suggestion cookbook の 2 request 構成。定数はコードが正本で、下は 2026-09-28 の `skills/jev-skill-router/scripts/router.py` の値）:
  1. 1 本目: 名簿全体を `Choice` で順位づけし、同時に「そもそも skill が要るか」を 3 問の gate で問う。gate が 0.30 未満なら「提案なし」で止まる
  2. 2 本目: 上位 3 件を本文つきで rerank し、候補ごとの fits を問う。fits の最大が 0.30 未満なら「提案なし」。そうでなければ `Choice` の勝者を提案する
  3. fits の最大と `Choice` の勝者が割れたときに fits 側で上書きする margin 規則は実装済みだが既定で無効（ADR-0074 Decision 6）
  - skip（Jev を呼ばない）: 空の prompt、`/` で始まる prompt、4,000 字を超える prompt、API key 無し、skill-comply の sandbox 配下の cwd
- 名簿: user・plugin・project の 3 系統から組み、`disable-model-invocation: true` の skill とルーター自身を除く（ADR-0074 Decision 2）。
  この期間の名簿の大きさは 52〜66 本で、240 本の chunk 上限に届かず全行 1 chunk
- 突き合わせる outcome: `~/.claude/metrics/skill-usage.jsonl`（hook `hooks/log-skill-usage.sh` が書く）。`event` は `invoke`（Skill tool の明示呼び出し）/
  `read`（`.claude/skills/` 配下の `.md` の Read）/ `slash`（ユーザーが `/<skill>` と打った起動）。join の鍵は `session` と `ts`（ログに焼かず、読む側で突き合わせる。RFC-0025）
- 読み方の固定（ADR-0074 Decision 4）: `model`・`question_hash`・`router_version` が同一の行だけを 1 つの分布として数える。`roster_hash` は分割鍵にせず種類数を添える

### 判定ログの schema

1 判定 1 行の JSONL。書き手は `skills/jev-skill-router/scripts/decision_log.py` の `build_record`。ファイルは所有者だけが読める（mode 0600、dir 0700）。

| 欄 | 意味 |
|---|---|
| `ts` | 行を書いた時刻（UTC、秒） |
| `project` | hook 入力の `cwd`（絶対パスのまま） |
| `session` | hook 入力の `session_id`（Claude Code の session id）。outcome との join の鍵 |
| `mode` | `shadow` / `inject` / `off`（環境変数 `JEV_ROUTER`。未知の値は `off` 扱いで skip 行だけ残す） |
| `model` | 判定 model の pin（`jev-1.13.0`） |
| `router_version` | 何を問うかが変わったら上げる版。0.1.0 は description 60 字・本文 700 字の先頭だけを送り、0.2.0 は全文を送る |
| `question_hash` | 質問文の定数と閾値（gate / fits / none）から導いた hash。質問文を変えたら別分布になる |
| `roster_hash` | その行の名簿の hash |
| `n_skills` / `n_by_source` | 名簿の本数と、系統（user / plugin / project）別の本数 |
| `prompt_sha` / `prompt_chars` | prompt の sha256 先頭 12 桁と文字数。本文は書かない |
| `gate` / `gate_values` | 「skill が要るか」の 3 問の確率（最大値と問いごと） |
| `shortlist` | 1 本目で残った上位の skill 名 |
| `fits` | 2 本目の候補ごとの fits 確率 |
| `winner` | 2 本目の `Choice` の勝者 |
| `suggestion` | 提案した skill 名。提案なしは null |
| `reason` | 提案した理由、提案なし・skip・失敗の理由（下の読み値の分類を参照） |
| `chunks` | 1 本目を何 chunk に分けて問うたか |
| `usage` | `calls`（API 呼び出し数）/ `input_tokens` / `output_tokens`。skip 行は空 |
| `elapsed_ms` | 判定にかかった壁時計。skip 行は 0 |

## 環境

- 置き場所: `~/.claude/plugins/data/jev-skill-router-jev-skill-router/decisions.jsonl`（gitignore 下、plugin の data dir）
- 配線: plugin `jev-skill-router@jev-skill-router`（公開 repo `shimo4228/jev-skill-router`）の UserPromptSubmit hook。`JEV_ROUTER=shadow`。
  shadow の判定は切り離した子プロセスで走るので、`elapsed_ms` は prompt の処理を待たせていない
- 判定 model: `jev-1.13.0`（全行）。`question_hash` は全行 `662772b42ed4` の 1 種
- 期間: 2026-09-21T05:42:42Z 〜 2026-09-28T09:44:24Z（1,242 行目）。71 session
- 読んだ時点: 2026-09-28（UTC 10:4x）。この時点でファイルは 1,265 行あった（「既知の故障」1）
- 再計算の環境: Python 3.14.3、標準ライブラリだけ

## 生の読み値

判断役（2026-09-28）の値と、このカードの script で先頭 1,242 行を数え直した値の照合:

| 読み値 | 判断役 | 再計算（1,242 行） | 一致 |
|---|---|---|---|
| 行数（2026-09-21〜28） | 1,242 | 1,242 | 一致 |
| 提案あり | 539（43%） | 539（43.4%） | 一致 |
| 提案した skill が同じ session で 30 分以内に `invoke` された | 28 / 539 | 28 / 539 | 一致 |
| `invoke` のうち直前の提案と一致 | 23 / 122 | 23 / 122 | 一致 |
| 入力 token / 行 | 約 18,500 | 18,547 | 一致（分母は全行。下の注） |
| `elapsed_ms` の中央値 | 約 690 | 686 | 一致（分母は全行。下の注） |

分母の注: 入力 token と `elapsed_ms` は、Jev を呼ばなかった skip 行（212 行、token 0・0 ms）を分母に含めた値。Jev を呼んだ行（routed、1,030 行）だけで
数えると、入力 token の平均は 22,364 / 行、`elapsed_ms` の中央値は 806 になる。1 回の判定の費用と遅延として読むなら routed 側の値。

内訳（同じ 1,242 行）:

| 欄 | 値 |
|---|---|
| routed（Jev を呼んだ）/ skip | 1,030 / 212 |
| `router_version` | 0.2.0 が 1,223 行、0.1.0 が 19 行（2026-09-21 のみ） |
| `roster_hash` の種類（routed 行） | 20 |
| 提案あり / routed 行に対する率 | 539 / 1,030 = 52.3% |
| 0.2.0 だけの提案あり | 526 / 1,223 = 43.0%（全行比） |
| `calls` | 2 回が 925 行、1 回が 105 行（gate で止まった行） |
| 出力 token / routed 行 | 平均 755 |

`reason` の分類（1,242 行）:

| 分類 | 行数 | 意味 |
|---|---|---|
| `best fits … < 0.30` | 386 | 2 本目まで進み、どの候補も fits 0.30 未満で提案なし |
| `shortlist winner` | 334 | 提案あり。`Choice` の勝者と fits の最大が同じ skill |
| `choice winner … best fits …` | 205 | 提案あり。`Choice` の勝者と fits の最大が割れ、勝者を提案（margin 規則が無効なので） |
| `prompt-too-long` | 179 | skip（4,000 字超） |
| `gate … < 0.30` | 105 | 1 本目の gate で提案なし |
| `slash-command` | 16 | skip |
| `error` | 11 | API 呼び出しの失敗（fail-open で行だけ残る） |
| `empty-prompt` | 6 | skip |

提案あり 539 = 334 + 205。そのうち `Choice` と fits が割れた提案は 205 / 539 = 38%。

ADR-0074 Decision 4 の観測量（このカードで定義どおりに数えた値。判断役の読みには無い）: 0.2.0 の routed 行 1,012、そのうち同じターン
（同じ session で次の routed 行まで）に `invoke` / `read` / `slash` があった行 136。inject を判断する条件（routed 200 以上かつ 40 以上）には届いていた。
Decision 4 が読むと定めた 3 つの生値（一致 / needless / missed）はこのカードでは出していない。

計算に使った script（先頭 N 行を数える。引数なしで全行）:

```python
import json, os, sys, statistics, collections
from datetime import datetime, timedelta

L = os.path.expanduser("~/.claude/plugins/data/jev-skill-router-jev-skill-router/decisions.jsonl")
M = os.path.expanduser("~/.claude/metrics/skill-usage.jsonl")
N = int(sys.argv[1]) if len(sys.argv) > 1 else None   # 先頭 N 行だけ数える（判断役の読みは 1242）
ts = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")

rows = [json.loads(l) for l in open(L) if l.strip()][:N]
first, last = ts(rows[0]["ts"]), ts(rows[-1]["ts"])
use = [json.loads(l) for l in open(M) if l.strip()]
use = [u for u in use if u.get("session")]
routed = [r for r in rows if r["usage"]]             # Jev を呼んだ行（skip 行は usage が空）
sugg = [r for r in rows if r["suggestion"]]
by_sess = collections.defaultdict(list)
for r in rows:
    by_sess[r["session"]].append(r)

print(f"rows={len(rows)} {rows[0]['ts']}..{rows[-1]['ts']} sessions={len(by_sess)}")
print("router_version", dict(collections.Counter(r["router_version"] for r in rows)),
      "model", dict(collections.Counter(r["model"] for r in rows)),
      "question_hash", dict(collections.Counter(r["question_hash"] for r in rows)),
      "roster_hash kinds", len({r["roster_hash"] for r in routed}))
print(f"routed={len(routed)} skipped={len(rows) - len(routed)}")
reasons = collections.Counter()
for r in rows:
    x = r["reason"]
    for p in ("gate ", "shortlist winner", "choice winner", "best fits", "error:"):
        if x.startswith(p):
            x = p.strip(" :"); break
    reasons[x] += 1
print("reason", reasons.most_common())
print(f"suggested={len(sugg)} ({len(sugg) / len(rows):.1%} of rows, {len(sugg) / len(routed):.1%} of routed)")

# (1) 提案した skill が、同じ session で提案から 30 分以内に invoke された
inv = [u for u in use if u["event"] == "invoke"]
hit = sum(1 for r in sugg if any(
    u["session"] == r["session"] and u["skill"] == r["suggestion"]
    and ts(r["ts"]) <= ts(u["ts"]) <= ts(r["ts"]) + timedelta(minutes=30) for u in inv))
print(f"suggestion invoked <=30min same session: {hit}/{len(sugg)}")

# (2) router 行のある session・期間の invoke のうち、同じ session の直前の router 行の提案と一致
inv_w = [u for u in inv if u["session"] in by_sess and first <= ts(u["ts"]) <= last]
match = 0
for u in inv_w:
    prev = [r for r in by_sess[u["session"]] if ts(r["ts"]) <= ts(u["ts"])]
    match += bool(prev and prev[-1]["suggestion"] == u["skill"])
print(f"invokes={len(inv_w)} matched previous row's suggestion={match}")

# (3) 入力 token と遅延。分母が全行か routed 行かで値が変わるので両方出す
tin = [r["usage"].get("input_tokens", 0) for r in rows]
print(f"input_tokens per row: all-rows mean={statistics.mean(tin):.0f}, "
      f"routed mean={statistics.mean([r['usage']['input_tokens'] for r in routed]):.0f}; "
      f"output per routed mean={statistics.mean([r['usage']['output_tokens'] for r in routed]):.0f}; "
      f"calls {dict(collections.Counter(r['usage']['calls'] for r in routed))}")
print(f"elapsed_ms median: all-rows={statistics.median([r['elapsed_ms'] for r in rows]):.0f}, "
      f"routed={statistics.median([r['elapsed_ms'] for r in routed]):.0f}")

# (4) ADR-0074 Decision 4 の観測量: 0.2.0 の routed 行と、同じターン（同 session で次の routed 行まで）に
#     invoke / read / slash があった行
same = 0
rs_by = collections.defaultdict(list)
for r in routed:
    rs_by[r["session"]].append(r)
for s, rs in rs_by.items():
    for i, r in enumerate(rs):
        if r["router_version"] != "0.2.0":
            continue
        t0, t1 = ts(r["ts"]), (ts(rs[i + 1]["ts"]) if i + 1 < len(rs) else None)
        same += any(u["session"] == s and u["event"] in ("invoke", "read", "slash")
                    and t0 <= ts(u["ts"]) and (t1 is None or ts(u["ts"]) < t1) for u in use)
print(f"ADR-0074 D4: routed(0.2.0)={sum(r['router_version'] == '0.2.0' for r in routed)} same-turn use={same}")
```

`python3 <script> 1242` の出力のうち数値の行（`reason` の行は上の表に写した）:

```
routed=1030 skipped=212
suggested=539 (43.4% of rows, 52.3% of routed)
suggestion invoked <=30min same session: 28/539
invokes=122 matched previous row's suggestion=23
input_tokens per row: all-rows mean=18547, routed mean=22364; output per routed mean=755; calls {2: 925, 1: 105}
elapsed_ms median: all-rows=686, routed=806
ADR-0074 D4: routed(0.2.0)=1012 same-turn use=136
```

## 測らなかったもの

- 提案の正しさ。「使われた」は「正しかった」ではない。使われなかった提案が外れだったのか、model が skill を読まずに同じことをしたのかは区別していない
- inject したときの効果（shadow だけで、model の文脈には何も足していない）
- `read`（description をきっかけにした参照読み）と提案の一致。(1)(2) は `invoke` だけを数えた
- 30 分以外の窓、「直前の router 行」以外の対応づけ（同じ turn・次の prompt まで等）での一致
- 0.1.0 と 0.2.0 を分けた一致（判断役の値に合わせて全行で数えた。0.1.0 は 19 行）
- 提案が無かったターンに skill が使われた数（missed）と、提案したのに使われなかった数（needless）を ADR-0074 の定義で出すこと
- 判定の費用（USD）。token 数だけで、単価は見ていない
- 判定の揺れ（同じ prompt を繰り返し問うた記録は無い）

## 既知の故障

1. **ログは「1,242 行で凍結」していない。** RFC-0025 の Status は「router log（1,242 行で凍結）」と書くが、2026-09-28 UTC 10:4x の時点でファイルは 1,265 行で、
   1,243 行目以降（UTC 09:50〜10:35 の 23 行）は判断役が読んだ後に書かれた。`enabledPlugins` の false は新しい session に効き、既に動いていた session の
   hook は書き続けたと推定（未確認。23 行の session はどれも先の 71 session に含まれる）。比較するときは先頭 1,242 行で切る（script の引数）
2. **outcome のログは下限。** `skill-usage.jsonl` は harness の hook が走る local session だけを記録し、cloud session（ADR-0075 の既定の build 実行者）の skill 使用は
   入らない（`hooks/log-skill-usage.sh` の冒頭のコメント）。router 側も同じ hook の範囲なので両側が同じ session 集合を見ているが、harness 全体の使用ではない
3. **「一致」は時系列の近さで決めている。** (1) は 30 分窓、(2) は同じ session の直前の router 行。prompt と skill 使用の因果は見ていない。
   窓や対応づけを変えると値が動く
4. **分母の取り方で値が動く。** 入力 token と `elapsed_ms` は skip 行を分母に入れるかで 18,547 / 22,364、686 / 806 と変わる。判断役の値は全行分母
5. **2 つの分布が混ざっている。** 先頭 19 行は `router_version` 0.1.0（送る本文の長さが違う）。ADR-0074 Decision 4 の読み方では別分布として数えるべき行で、
   判断役の値もこのカードの (1)〜(3) も全行で数えた
6. **名簿が 20 種類に変わっている。** skill の追加・退役で `roster_hash` は期間中に 20 回分かれた。同じ skill 名が期間の前後で違う description を持ちうる
7. **`error` 11 行。** fail-open の設計どおり行だけ残り、提案なしとして数えられる。失敗の内訳（timeout か API 側か）は数えていない
8. **ログの行・prompt・session id は公開しない。** ログは prompt の sha と文字数しか持たないが、`project`・`session` は公開しない値として扱い、このカードには集計だけを写した

## 有効性の状態

**単発。** 7 日の shadow を 1 回、判断役の読みとこのカードの再計算で同じ 1,242 行を 2 回数え、値は全て一致した（同じ入力の数え直しであって、別の機会の再測定ではない）。
読める結論は「この名簿・この期間では、Jev は全 prompt の 43% で skill を提案し、提案が 30 分以内にそのまま `invoke` されたのは 28 / 539」まで。

- `再現済み` へ動く条件: plugin を再び有効にして別の期間の shadow を取り、同じ script で数えた提案率と `invoke` との一致の向きが揃う。現在は無効化されていて、動く予定は無い
- `不成立` へ動く条件: join の鍵（`session` + `ts`）が二つのログで同じ session を指していない、または `skill-usage.jsonl` がこの期間の local session の `invoke` を
  取りこぼしていたと分かる

## 欄の対応表

| このカードの欄 | aggregate-result.json（schemaVersion 1） | Every Eval Ever v0.3.0 | Inspect AI EvalLog |
|---|---|---|---|
| frontmatter `eval_library` | — | `eval_library{name,version}` | — |
| frontmatter `evaluation_timestamp`（区間） | — | `evaluation_timestamp`（EEE は時点。ここでは区間に読み替え） | — |
| frontmatter `retrieved_timestamp` | — | `retrieved_timestamp`（EEE は Unix epoch） | — |
| frontmatter `source_type` / `evaluator_relationship` | — | `source_metadata.source_type` / `source_metadata.evaluator_relationship` | — |
| frontmatter `num_samples`（数えた行数） | — | `evaluation_results[].score_details.uncertainty.num_samples` | — |
| frontmatter `execution_command` | — | `evaluation_results[].generation_config.generation_args.execution_command` | — |
| frontmatter `log_updates` | — | — | `log_updates`（考え方のみ） |
| 生の読み値 入力 token / 行 | —（`costUsd` に当たる欄だが、単位が token で USD ではない） | — | — |
| 生の読み値 `elapsed_ms` の中央値 | —（`durationSeconds` は run 全体の時間で、判定 1 回の遅延ではない） | — | — |
| 生の読み値 提案率・一致 | — | — | — |

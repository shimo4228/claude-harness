---
origin: shimo4228
instrument: search-first 影の比率 snippet（transcript 走査、読み取り専用の Python）
subject: search-first
validity: 単発
source_type: documentation
evaluator_relationship: first_party
eval_library:
  name: python3（標準ライブラリのみの snippet）
  version: unknown
evaluation_timestamp: 2026-09-14
retrieved_timestamp: 2026-09-28
num_samples: 1
execution_command: "python3 - < <snippet>   # <snippet> は本カード「設計」節の Python をそのまま保存したもの"
log_updates: []
---

# s3 — search-first の影の比率 基準値（2026-09-14）

外部調査をしたセッションのうち skill `search-first` を通らなかった割合（影の比率）を、述語を固定して 1 回測った基準値の記録。
値は 133 / 142 = 93.7%。この値は [ADR-0066](../adr/0066-search-first-report-contract-and-scout-retirement.md) Decision 6 と
[RFC-0022](../../rfcs/0022-search-first-verdict-redesign.md) の再測定（2026-11-01 以降）が比べる基準になる。

## 設計

- 問い: 直近 60 日の Claude Code session transcript で、外部調査（WebSearch、または外部調査を頼む subagent）をしたセッションのうち、
  `search-first` を通らなかったセッションはどれだけあるか。skill の発火率を invoke 数（呼ばれた側だけを見る）でなく、
  呼ばれるべきだった集団の側から測る
- 計器の使われ方: ADR-0066 Decision 6 は網羅の計器を invoke 数から影の比率に替えた。Review-when は 2026-11 に同じ snippet で
  取り直し、93.7% から下がっていなければ「発火しない原因は trigger surface（description が受ける問いの種類）」の仮説が崩れたとして
  ADR を再読する、と定める。RFC-0022 は `blocked` で、再開条件は「2026-11-01 以降の triage cycle」
- 対象: `search-first`（2026-09-15 の commit `47d51a8` で verdict 表から報告契約へ改修された skill）。測定は改修の前日で、
  改修前の skill に対する基準値
- 固定した述語（`.notes/search-first-shadow-baseline-2026-09-14.md` の記述を写したもの）:
  - (i) セッションの単位 = `~/.claude/projects/<slug>/<session>.jsonl` 1 ファイル、20 KB 超のみ。sidechain / subagent の transcript は数えない
  - (ii) 走査対象 = 一段 glob（再帰しない）。slug が `-private-tmp` で始まる scratch / probe は除外
  - (iii) 60 日窓 = ファイルの mtime
  - (iv) 分母 = `WebSearch` の tool_use を持つか、`Agent` の prompt が下の正規表現に一致するセッション。
    分子（影）= 分母のうち `Skill(search-first)` も `Agent(scout)` も持たないセッション。scout は 2026-09-15 に退役したので、以後は Skill だけが効く
- arm は無い（1 集団の比率）。比較は時点間で、同じ snippet を別の日に走らせた比率どうしを比べる。60 日のローリング窓なので集合は入れ替わり、
  比べるのは比率であって集合ではない

### snippet（`.notes/` の記録から写した。再実行できる形）

```python
import json, re, os, time, glob
ROOT=os.path.expanduser('~/.claude/projects'); NOW=time.time(); WINDOW=60*86400
files=[f for f in glob.glob(f'{ROOT}/*/*.jsonl')                       # (ii) one level, no recursion
       if not os.path.basename(os.path.dirname(f)).startswith('-private-tmp')  # scratch/probe slugs excluded
       and os.path.getsize(f)>20_000                                       # (i) trivial sessions excluded
       and NOW-os.path.getmtime(f)<WINDOW]                                 # (iii) mtime window
EXT=re.compile(r'WebSearch|WebFetch|Web 検索|Web 調査|web research|一次ソース|primary source|as of 20', re.I)
denom=[]; shadow=[]
for f in files:
    ext=False; via=False
    for l in open(f):
        if '"tool_use"' not in l: continue
        try: d=json.loads(l)
        except: continue
        c=d.get('message',{}).get('content')
        if not isinstance(c,list): continue
        for b in c:
            if b.get('type')!='tool_use': continue
            i=b.get('input') or {}; n=b.get('name','')
            if n=='Skill' and i.get('skill')=='search-first': via=True          # (iv) numerator predicate
            elif n=='Agent' and i.get('subagent_type')=='scout': via=True       #      (scout counted while it existed)
            elif n=='WebSearch': ext=True
            elif n=='Agent' and EXT.search(i.get('prompt') or ''): ext=True
    if ext:
        denom.append(f)
        if not via: shadow.append(f)
print(f"files_in_window={len(files)} denominator={len(denom)} shadow={len(shadow)} ratio={len(shadow)/len(denom):.3f}")
print("SHADOW_SESSIONS"); [print(os.path.relpath(f,ROOT)) for f in sorted(shadow)]
print("VIA_SESSIONS"); [print(os.path.relpath(f,ROOT)) for f in sorted(set(denom)-set(shadow))]
```

後半 2 つの `print` はセッションの相対パス（slug と session id）を出す。基準集合の一覧は `.notes/` にだけ置き、このカードには写さない。
比率だけを取り直すなら 1 行目の `print` だけで足りる。

## 環境

- 測った日: 2026-09-14（JST）。時刻は未記録（`.notes/search-first-shadow-baseline-2026-09-14.md` の mtime は 2026-09-14 23:46 JST で、これは記録を書いた時刻）
- 実行した Python の版: 未記録（2026-09-28 時点のこの機械の `python3` は 3.14.3）。snippet は標準ライブラリだけを使う
- 走査した transcript: `~/.claude/projects/` 配下。Claude Code の transcript 自動削除は `settings.json` の `cleanupPeriodDays: 36500`（2026-09-28 時点で確認。
  2026-09-14 時点の値は未確認）で、60 日窓の中の transcript は消えていない前提
- 実行した session・model: 未記録（ADR-0066 の起票セッション。ADR 本文は実測 3 の目視分類を「本セッション（Fable）」と書く）
- 並列度・隔離: 1 プロセス、読み取り専用。隔離の条件は無い（実運用の transcript をそのまま読む）

## 生の読み値

```
files_in_window=979 denominator=142 shadow=133 ratio=0.937
```

| 欄 | 値 |
|---|---|
| 窓の中の transcript（20 KB 超、`-private-tmp` 除外） | 979 |
| 分母（外部調査をしたセッション） | 142 |
| 影（分母のうち search-first / scout を通らなかった） | **133** |
| 通った | 9 |
| 影の比率 | **0.937**（93.7%） |

導出: 比率 = 133 / 142 = 0.9366… → 0.937。通った 9 = 142 − 133。

同日の関連値（同じ記録と ADR-0066 から）:

- 述語を固定する前の暫定値: 130 / 154 = 84%（フィルタと分子の定義が未固定）
- adr-reviewer の独立再現: 定義差だけで 67.5%〜96% に振れた。基準値として採ったのは固定手順の 133 / 142

## 測らなかったもの

- 影の集団が本当に search-first を通るべきだったか。分母の述語は「外部調査をした」であって「skill の対象の問いだった」ではない。
  ADR-0066 の実測 3 は影の側の WebSearch query 261 本と Agent prompt 148 本を目視で種類に当てたが、その結果はこのカードの読み値に入っていない
- 通った 9 セッションで skill の報告が役に立ったか（出力の質は見ていない）
- 改修後（2026-09-15 以降）の skill の発火。この値は改修前の基準で、改修の効果は 2026-11 の再測定が初めて答える
- 主ループが Quick Mode 相当の調査を skill を呼ばずに自前でしたケースを、正しい省略として数えるか（区別していない）
- subagent 側の transcript（sidechain）の中の Web 調査（数えていない）
- invoke 数との対応（ADR-0066 は並べて見るとしたが、この測定では出していない）

## 既知の故障

1. **定義への感度が大きい。** 同じ日の同じ transcript で、述語の違いだけで 67.5%〜96% に振れた。比べられるのは同じ snippet で取った比率どうしだけ
2. **meta セッションの混入。** search-first 自体を扱うセッション（この測定をしたセッションを含む）は prompt に `WebSearch` の語を含みやすく、
   分母と影の両方に入る。記録は「件数は数件で比率には効かない」とするが、件数は未記録
3. **分母の正規表現は語の出現で拾う。** `Agent` の prompt に `as of 20` や `一次ソース` と書いただけで外部調査とみなす。Web tool を実際に使ったかは見ない
4. **窓は mtime。** 古い transcript を resume したり touch したりすると窓に戻る。60 日のローリング窓なので 2026-11 の集合は今回とほぼ入れ替わる
5. **分子の述語が時点で変わる。** `Agent(scout)` は 2026-09-15 に退役し、以後は `Skill(search-first)` だけが分子を作る。基準値は scout を分子に含めた値
6. **生値の置き場所が git の外。** snippet・出力・基準集合の一覧は gitignore 下の `.notes/` にだけあり、履歴で追えない。
   走査対象の transcript も gitignore 下で、2026-09-14 の集合を後から完全には再現できない（窓の外に出た transcript は snippet が拾わない）

## 有効性の状態

**単発。** 述語を固定した snippet で 1 回測った値で、同じ snippet を別の機会に走らせた記録は無い。読める結論は
「2026-09-14 の 60 日窓・この述語では、外部調査をした 142 セッションのうち 133 が search-first を通らなかった」まで。

- 時点比較として読む条件: RFC-0022 の再開条件（2026-11-01 以降の triage cycle）で同じ snippet を実行し、比率を並べる。
  集合は入れ替わるので、再測定が `再現済み` を作るのではなく、2 点目の `単発` の値として並ぶ
- `再現済み` へ動く条件: 同じ窓（同じ transcript 集合）に対して同じ snippet を別の機会に走らせ、同じ 133 / 142 を得る。
  窓がローリングなので、実際には基準集合の一覧を入力に固定した再走査が要る
- `不成立` へ動く条件: 分母が外部調査をしたセッションを表していない（meta セッションや語の出現だけの一致が比率を動かす規模である）と分かる

## 欄の対応表

| このカードの欄 | aggregate-result.json（schemaVersion 1） | Every Eval Ever v0.3.0 | Inspect AI EvalLog |
|---|---|---|---|
| frontmatter `eval_library` | — | `eval_library{name,version}` | — |
| frontmatter `evaluation_timestamp` | — | `evaluation_timestamp` | — |
| frontmatter `retrieved_timestamp` | — | `retrieved_timestamp`（EEE は Unix epoch） | — |
| frontmatter `source_type` / `evaluator_relationship` | — | `source_metadata.source_type` / `source_metadata.evaluator_relationship` | — |
| frontmatter `num_samples` | — | `evaluation_results[].score_details.uncertainty.num_samples` | — |
| frontmatter `execution_command` | — | `evaluation_results[].generation_config.generation_args.execution_command` | — |
| frontmatter `log_updates` | — | — | `log_updates`（考え方のみ） |
| 生の読み値 影の比率 | —（arm も delta も無い 1 集団の比率） | — | — |
| 生の読み値 分母・分子の件数 | — | — | — |

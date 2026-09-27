# Plan: search-first を「verdict」から「報告 → 呼び出し側が取捨選択」へ改良し、scout を退役する（RFC-0022）

## Context

RFC-0022（`rfcs/0022-search-first-verdict-redesign.md`）の観察: search-first は発火が減衰し
（invoke 6 月 6 / 7 月 14 / 8 月 8 / 9 月 0）、発火しても「そのまま適用できない」と却下される。
原因仮説は verdict 表（Adopt / Extend / Compose / Build）が「install できる package があるか」の
一軸で、harness ではほぼ Build に落ち、見つけたものから学んだことを運ぶ欄が無いこと。

本セッションの実測（2026-09-14）:

- 直近 60 日の transcript 959 セッション: 外部調査をしたセッション 154 のうち search-first / scout
  を通ったのは 24、通らなかったのは **130（84%）**。通らなかった側は自前の prompt に「as-of
  日付・一次ソース・報告せよ」を書いていた（rule: knowledge-staleness の transfer 証拠）
- skill を通った 8 件の問いは library 選定 2 / 先行実装 4 / 仕様 1 / 状況の俯瞰 2。通らなかった
  130 の問いには、さらに **原典照合**（主張・引用・数値を一次資料が本当にそう言っているか）の
  大きな塊があった。受けるべきでない塊も見えた: トラブルシューティング / how-to、repo 内調査
- scout（Sonnet、Adopt/Build report 雛形）は直近 8 呼び出し全部で呼び出し側が雛形を無視して
  完全な prompt を書いていた。固有価値は「web tool を持つ subagent」で general-purpose と同じ

著者決定（2026-09-14）:

1. **verdict を廃止し、リサーチ結果を報告する。使えるところは呼び出し側（主ループ / build
   セッション）が取捨選択する。** そのまま使えるのは稀で、部分採用も成果
2. スコープは ① 受ける問いの種類 ② 種類ごとの探索先・証拠基準・止め方 ③ 終わり方の契約
   ④ 委譲先。配線（planning.md / Phase 0 / slash）は触らない。発火率は「受ける問いの種類」
   （description の trigger surface）の帰結で、独立の knob ではない
3. 問いの種類は 6 種 + 総称句（列挙だけだと看板が閉じる）
4. **search-first は残して改良する。scout は退役する**（rule knowledge-staleness が skill を
   名指ししており、指す先を残す。Full Mode の委譲は general-purpose subagent で足りる）
5. 残余の書き方規則 3 つ（範囲付き不在 / snippet と本文の区別 / 主張に対象・前提・相違を付ける）は
   **rule には置かない**（常駐すると全文脈に当たり不自然）。調査時だけ読まれる skill 本文に置く
6. 記録は RFC-0022 更新 + ADR 1 本。網羅の計器は invoke 数でなく**影の比率**（外部調査した
   セッションのうち skill を通らなかった割合。基準値 84%）

一次資料（`plans/intent-r-d-2026-09-14-bubbly-hellman.md` L256–297）から持ち込むもの:
HumanLayer research_codebase「DOCUMENT WHAT IS, NOT WHAT SHOULD BE」（調査者は記述し判断しない
= 決定 1）/ K-Dense の dated evidence boundary（「存在しない」でなく範囲付き不在）/ ODR の停止
条件と call 上限 / Codex deep-research §9 規則 1・2・4・13（主張と原典の対応、snippet と本文の
区別、source の主張と repo 含意の区別、「次の検索が何を解決するか言えなくなったら止める」）。

## 設計

### ① 受ける問いの種類（description の発話例になる）

| 種類 | 問いの形 | 例（実測から） |
|---|---|---|
| library 選定 | この用途に使える package / tool は何か、今どれが主流か | type checker の現時点の到達度 |
| 先行実装 | この設計問題を解いた実装・skill・agent・MCP は既にあるか | codemap を code から派生させる手段 |
| 論文・post の主張 | この主張はうちの条件に当てはまるか | verbalized sampling は問い生成に効くか |
| 仕様・公式挙動 | 公式は何と言っているか、今の版で何ができるか | note.com 公式 API の有無 |
| 状況の俯瞰 | as-of で今どうなっているか、誰がどうやっているか | LLM 前提の lint の状況 |
| 原典照合 | この主張・引用・数値を一次資料は本当にそう言っているか | digest の arXiv 主張の照合 |

種類は**探索の手掛かりであってゲートではない**。description に「外部に答えがありうる問い全般」
の総称句を置く。1 つの問いが 2 種にまたがるのは普通。repo 内検索は種類に関係なく先に 1 回。

**NOT for**（影の集団から名指し）: トラブルシューティング / how-to（答えが 1 つで比較が要らない）、
repo 内・ローカル環境の調査（→ Explore agent）、記事の fact-check 全体の運用（→ 各 writing repo
の fact-checker。1 主張の原典照合だけを受ける）、bug fix / refactor / config 値（現行どおり）。

### ② 種類ごとの探索先・証拠基準・止め方

| 種類 | 探索先 | 証拠として数えるもの | 止め方 |
|---|---|---|---|
| library 選定 | registry（npm / PyPI / crates）、公式 docs、release page | 最終 release 日、license、依存の重さ、機能一致の具体箇所 | 候補 2〜3 の一次情報が揃った |
| 先行実装 | GitHub code search、skill / agent / MCP catalog、harness 資産（Glob） | 実ファイル（SKILL.md / source）を読んだ。README だけを「読んだ」と言わない | 実ファイル 2 件読んだ or 独立 3 源が同じ結論 |
| 論文・post の主張 | 一次資料本文。二次記事の要約は根拠にしない | 対象・前提・根拠の種別（実験 / ベンチ / 採用実績 / 意見）・うちとの相違 | 主張の対象と前提が書けた |
| 仕様・公式挙動 | 公式 docs / CLI `--help` / changelog / 実行して確かめる | 版と日付、実行結果 | 版付きの一次情報 1 件 |
| 状況の俯瞰 | 上の混合 + 一人称の運用記録 | 各項目に as-of と出所、見つからなかった範囲 | 次の検索が何を解決するか言えなくなった |
| 原典照合 | 主張が指す一次資料の本文（abstract で止めない） | 該当箇所の引用と locator、主張ごとに 支持 / 部分 / 不支持 / 未確認 | 主張ごとに 4 値が付いた |

共通規則（skill 本文に置く。rule には置かない — 決定 5）:

- 全 claim に as-of 日付と出所 URL（rule: knowledge-staleness の消費点）
- 「存在しない」と書かない。検索語・source・日付の範囲付きで「見つからなかった」と書く
- snippet / abstract で見たものと本文を読んだものを区別する
- 外部の主張には対象・前提・うちとの相違を付ける
- 数値スコア・letter grade を出さない（ADR-0026 の正本、維持）
- Full Mode の subagent には call 上限（目安 15）を prompt で渡す

### ③ 終わり方の契約 — 報告

verdict 行は廃止。調査者が返すのは報告で、判断はしない:

```
## 見た範囲
検索語 / source / 日付（as-of）。見つからなかった範囲もここ
## 見つけたもの
1 件ごとに: 何か（URL）/ 対象と前提 / 根拠の種別 / うちの条件との相違 / 使えそうな部分
## 分からなかったこと
```

呼び出し側が報告を読んで「採る / 部分的に採る / 採らない」を plan 本文か RFC Prior art に書く。
「skip research」節は維持（skip も呼び出し側の判断として 1 行残す。verdict 語彙は使わない）。
Step 0 の articulation（問いと制約を text で先に書く）は 1 行に縮めて維持（ユーザーの軌道修正
窓。Claude 5 は native に行うが、tool 引数に埋めず text に出す点だけ pin する）。

### ④ 委譲先 — scout 退役

- Quick Mode: 主ループで数検索。Full Mode: **general-purpose subagent** に articulation + 種類 +
  報告の形 + call 上限を prompt で渡す。tools は Read / Grep / Glob / WebSearch / WebFetch に
  制限（web 由来コンテンツを Bash 持ちの agent に読ませない — security.md の脅威面）
- `agents/scout.md` 削除。search-first 本文は既に「research subagent (whatever your harness
  provides)」と書いており scout を名指ししていない

### ⑤ 配線と消費者（名前と入口は維持）

| 場所 | 変更 |
|---|---|
| `skills/implementation-chain/SKILL.md` L190 | 「Phase 0 で `Adopt` Verdict → 再 plan」→「Phase 0 の報告に、実装方針を変える既存解が含まれる → 再 plan」 |
| `skills/verify-bootstrap/SKILL.md` L108 | 「Verdict が出たら、次を確認してから採用する」→「報告を受けたら、次を確認してから採用する」 |
| `skills/mondo/SKILL.md` L96 | 「search-first / scout に切り出す」→「search-first に切り出す」 |
| `skills/prompt-perturb/SKILL.md` L3 / `agents/prompt-forager.md` L3 | 「search-first / scout」→「search-first」 |
| `skills/agent-stocktake/SKILL.md` L175 / L196 | scout の例示を落とすか別 agent に |
| `rules/common/planning.md` / `knowledge-staleness.md` / `akc-cycle.md` / `rfc-writer` §2 / `review-to-lint` §2 / `harness-sync` | 変更なし（search-first の名前と配線は維持） |

## 作るもの・触るファイル

1. `skills/search-first/SKILL.md` — 全面改修（置換であって追記ではない: verdict 表・Verdict 行・
   verdict 例・「Search without verdict」を消す）。description = 6 種の発話例 + 総称句 + NOT for。
   `user-invocable: true`、origin `shimo4228` 維持。100 行前後
2. `agents/scout.md` — `git rm`
3. ⑤ の 5 か所
4. `rfcs/0022-search-first-verdict-redesign.md` — Prior art に一次資料の読みと実測（8 件の分類、
   影の集団 130 と原典照合の塊）、Reference-level に本設計、Unresolved questions ①〜③ を解消
   （① 発火は description の trigger surface で扱う、② 6 種 + 総称句、③ 5 部とは同型にしない —
   報告は比較の材料で判断は呼び出し側）、**review-when を影の比率に置換**（走査手順を 1 段落:
   transcript の tool_use から WebSearch / 外部調査 Agent の有無と Skill(search-first) の有無を
   数える。基準値 130 / 154 = 84%、2026-09-14）、`state: accepted 2026-09-14`
5. `docs/adr/0065-search-first-report-not-verdict.md`（adr-writer）— Decision: verdict 廃止と
   報告契約、6 種 + 総称句、scout 退役、残余規則は skill に置き rule には置かない、計器は影の比率。
   Review-when: 影の比率が 2 ヶ月後（2026-11）も下がらない / 報告を受けた呼び出し側が「使える
   ところ無し」で捨てる例が続く。Alternatives: (a) verdict 維持 + 学び欄追加 (b) search-first 退役
   + 残余 3 行を rule へ（常駐で不自然、rule が skill を名指ししている — 却下）(c) scout を opus
   に上げて残す（呼び出し側が雛形を無視している実測 — 却下）(d) 何もしない。index 行
6. `docs/adr/0026` に日付つき注記は不要（search-first Step 2 = 数値スコア禁止の正本は残る）

## 手順（skill-creator を通す — rule: skills.md の命令形）

1. skill-creator §1 packet: 上の ①〜④ を 1 packet に固定。隣接 skill grep（prompt-forager /
   prompt-perturb / mondo / wiki-query / review-to-lint の NOT for 行 — 名前維持なので境界は
   変わらない、scout の名指しだけ消す）
2. 草稿: `skills/search-first/SKILL.md`（§3: 現行規則として書く、版差語なし、tombstone なし、
   例は報告の format を pin するもの 1 本だけ）
3. §4 fresh-context ゲート: general-purpose subagent 1 体（tools Read / Grep / Glob）に候補 path
   だけ渡し named verdict（Publishable / Fix / Drop）。上限 2 ラウンド
4. §5 行動 gate: `claude plugin eval skills/search-first --ablation with-without --runs 3`。case は
   先行実装型の問い 1 本（prompt に skill の手順を書かない）、grader は「報告に as-of 日付と出所
   URL があり、『存在しない』でなく範囲付きで書かれ、Adopt / Build 語の判定を出していない」。
   delta 無しなら設計に戻る
5. `git rm agents/scout.md`、⑤ の 5 か所
6. RFC-0022 更新、ADR-0065（adr-writer → adr-reviewer）
7. `python3 scripts/hooks/harness_lint.py`、
   `uv run --directory ~/.claude/skills/skill-health python -m scripts.scan_refs ~/.claude/skills --json`
   （scout への dangling 0）、`.claude/verify.sh`
8. ⏸ 著者通読 GO → commit（著者指示後）→ skill: harness-sync（`~/MyAI_Lab/search-first` 単独
   repo の README は adopt/extend/build 前提なので同期後に整合。claude-harness から scout.md が
   消える。ECC 版 PR #262 とはここで分岐 — ADR-0006）

実行者: skill / agent / ADR の散文編集 = judge-tier の本業（implementation-chain 例外 (a)）。
本セッションで実装。§4 ゲートは subagent。

## 検証

- `claude plugin eval` の with arm が without arm に対し delta を持つ
- `grep -rn "scout" skills agents rules` の残りが agent-stocktake の歴史的言及と results だけ
- `grep -rn "Adopt\|Extend\|Compose" skills agents rules` に search-first 由来の verdict 語彙が
  残らない（implementation-chain L74 の Build-or-not「verdict」は別物）
- `harness_lint.py` / `scan_refs` 0、`verify.sh` 緑
- 影の比率を 2026-11 に再測定（RFC review-when）

## Out of scope

- 配線の変更（planning.md / Phase 0 の Y→C / rfc-writer への命令形追加 / advisory hook）
- R&D ループ（問い発見）— 5 部形式との同型化はしない
- daily-research 側（`plans/optimized-gathering-mitten.md`）
- knowledge-staleness rule（変更なし）

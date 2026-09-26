---
state: in_progress 2026-09-21
review-when: Weekly·Fable 枠が回復し、判定役（architect / readme-reviewer / judge 群）を通常どおり引けるようになったとき。または daily-research の呼1 で候補照合が占める turn 数が測れたとき
---

## Summary

TypeSafe の System One モデル **Jev**（typed judgment を返す hosted API、Claude Max 枠の外で
課金される）を、この harness の「高頻度で小さな意味判断」に差し込む提案。2026-09-20 に探索と
部分実装まで進めたが、**着手順を誤ったため全変更を Rewind し、判断材料だけを残す**。

## Motivation

価値は節約ではなく **Max 枠（週次上限）の外へ判定を逃がすこと**。2026-09-20 時点の実測:

| 窓 | 使用率 |
|---|---|
| Weekly · Fable | **100%**（使い切り） |
| Weekly · all models | 73% |
| 5-hour | 8% |

`extraUsage.enabled` は false。上限に当たると金では解けず作業が止まるので、トークンは
**ドルより希少**。そして枠を食っているのは判定役そのものでもある —— agent 11 本の model は
opus 5 本 / fable 2 本 / sonnet 3 本 / haiku 1 本で、**judge・reviewer は全部が上位モデル**。
`agents/architect.md:6` は「判断は払える最強の判定者に。fable が使用制限で引けない場合のみ
opus」と書いており、その「引けない場合」が現に起きている。

## Guide-level explanation

Jev は **semantic なのに機械判定可能**（typed・確率つき・入力 $0.042/M・出力無課金・約 0.5 秒・
64k context）という区分を持ち込む。primitive は Choice / Noul / Score の 3 つだけで、テキストは
生成しない。

重要なのは **判断の粒度が変わる**こと。「高度な判断 = 最強モデルに丸ごと聞く」は判断が
分割不能な塊であることを前提にしていたが、TypeSafe は "break broad judgments into narrow,
typed questions" を最重要概念に置く。**同じ判断を N 問に割って安い枠で回す**第三の選択肢がある。

この harness には**割り方の資産が既にある**:

- `llm-as-judge` の「binary Yes/No を証拠に集め、集計せず named verdict」→ 証拠層が Noul 群
- `readme-judge` の「動的二値チェック + 固定コア」→ 既に二値の集合
- `implementation-chain` の Security Review 条件 → 既に脅威面 6 項目に割れている
- `repo-research-protocol.md:69` の履歴照合 → 既に 3 値で文章化されている

## Reference-level explanation

### 実測（このセッションで測ったもの。plan は gitignore 下なのでここに残す）

**daily-research の消費構造**（`logs/*.log` の result JSON を直接パース、34 日分）:

| | 呼1 (Opus) | 呼2 (Sonnet) |
|---|---|---|
| n | 59 | 58 |
| turns p50 | 39 | 5 |
| cache_read p50 | **2,581,628** | 232,306 |
| per-turn MIN（床） | 15,442 | 16,799 |
| per-turn p50 | 66,917 | 39,406 |

34 日の cache_read 総計 **1 億 8,002 万トークン。呼1 が 90%、呼2 が 10%**。
`metrics.jsonl` は `cache_creation` / `cache_read` を集計していないので、この数字は生ログから
しか出ない（計器側の欠陥）。

**判定の質**（候補照合を実データ 3 ペア + 合成 3 ケースで検証）:

- **Choice の confidence は 0.4〜0.7 で頭打ち**。「同じ問い + 新証拠」では判定が割れる
- **Noul は安定**（`scope_covered` が 3 条件すべてで 0.72〜0.82）
- **「日本語だから confidence が低い」は反証された** —— 英訳すると逆に下がった
  （日/日 0.64、英/英 0.39、日/質問だけ英 0.58）。頭打ちは言語でなく判定自体の曖昧さ
- 無関係なペアも `new_evidence` 0.96〜0.97 を返すので、**`new_evidence` 単独で分岐させない**

### 設計原則（採用するなら守るもの）

1. **集計しない** —— `llm-as-judge` ③ が正本。1 つの支配的 No が単独で決める
2. **閾値は見逃しの高コスト側に倒す**
3. **確率的判定を `block` に直結しない** —— `review-model-notice.sh` の既存規律
4. **較正は自分のデータで** —— docs の閾値はすべて illustrative と明記されている
5. **日付・順序・数え上げは code のまま** —— Jev 1.13 の公式 jaggedness
6. **fail-open**、`timeout` を明示指定
7. **model は alias でなく version で pin**（`jev-1.13.0`）—— 公式が「alias は無通知で動く。
   閾値を較正したなら version ID を pin せよ」と明記
8. 日本語は公式が「CJK は同等でない。routing では confidence に注意」と注記している

### 候補（優先順。実測に基づく）

1. **daily-research 呼1 の候補照合** —— `repo-research-protocol.md:69` の 3 値がそのまま
   criteria になる。呼1 は cache_read の 90%。**ただし 39 turn のうち照合が何 turn かは未測定**
2. **skill ルーター** —— ADR-0018:85 の「自発トリガー上限 ≒ 40%」への構造的回答。
   skill 55 本の description は 37,580 字（実測でセッション常駐 9,956 tokens）。
   **前提**: 複数 UserPromptSubmit hook の `additionalContext` 合成挙動が公式にも未文書で、
   実機確認が要る。**外部根拠（as-of 2026-09-20）**: TypeSafe 公式 cookbook が 182 skills を
   「全体 ranking → top 3 rerank → reject-all」の 2 call で絞り、vendor 実験 488 requests で
   wrong load 16.8%→7.3% / 不要 load 9.8%→4.0%。baseline の正解を壊した case も報告されている
3. **session-judgment-mining の一次仕分け** —— 5 類型が Noul 5 問。頻度は低いが 1 回が巨大
4. **judge の二値チェック層の分解** —— 較正が済んでから
5. **Security Review ゲートの shadow** —— ADR-0042 で「95% は Matrix 由来」と分かっているので
   **枠は空かない**。価値は取りこぼし検出のみ

## Drawbacks

- **外部送信**。hosted API なので state が機外に出る。enterprise 以外は zero retention なし
- **較正コスト**。閾値は自分のデータで測るしかなく、shadow 期が要る
- **母集団が足りない場所がある**。候補照合の履歴は `question` field を持つものが akc 45 件中
  4 件しかない（この field は ADR-0017 で最近入った）
- **判定器を増やすと検証対象も増える**。今回 Security Review shadow の hook を書いた際、
  security-reviewer が HIGH 2 件（敵対的 `.git/config` 経由の任意コマンド実行 / secret-scan の
  判定より先に追加行が外部へ出る）を出した。**外部送信する hook は harness の脅威面を実際に
  広げる**

## Rationale and alternatives

- **skillbox / jev-guard / jevwire 等の既製 plugin を使う** —— 却下。skillbox は
  Docker + PostgreSQL 常駐で、hook 1 本で足りる設計に対して過剰（ADR-0002 が却下した
  コスト構造に近い）。guard 系は `security.md` の trust boundary を確率的判定で置き換えない
  原則に反し、community 実装は security audit 未確認。**advisory only / read-only の MCP
  （`@jkudish/jev-mcp` 型）も同じ扱い** —— 無人 hook には乗らないので却下理由は 1 つ弱まるが、
  候補 1 と対象が重なり、Drawbacks の「外部送信する経路を増やす」はそのまま残る（2026-09-20 追記）
- **`context_files` の事前選別** —— 却下。既に config で 1〜3 ファイルに絞られ、プロンプトも
  「全部は読まない」と指示済み。量的にも支配項に対して桁違いに小さい
- **autoresearch feature discovery** —— 保留。`.growth/EXPERIMENTS.md` が 41 行・cycle 1 のみで
  データ不足

## Prior art

- ADR-0002（claude-mem 無効化）が「prompt を外部ストアへ投げ additionalContext に注入する」
  同型機構を却下している。却下理由は (1) 正本の置き場所 —— episodic な派生データ、(2) 記憶が
  要る時刻 —— hook は prompt 投入時にしか発火できない。**skill ルーターはどちらにも当たらない**
  （注入するのは skills/ の正本へのポインタ 1 行で、skill の選択は prompt 投入時に決まる）。
  採用する場合はこの差分を ADR に書くこと
- 別プロセスの Codex（read-only）に premise challenge させ `premise-hole` を受けた。
  最も重い指摘は「原典照合の Step B は判定の**後に訂正**の責務を持つので、判定だけ移しても
  往復は消えない」で、これは `verification-protocol.md:45-48` で確認できた

## Unresolved questions

- **呼1 の 39 turn のうち候補照合が何 turn か。** 90% という比率は呼1 全体の話で、その中で
  照合が占める割合は未測定。ここが小さければ候補照合も的外れになる。result JSON は turn 総数
  しか持たず、正面から測るなら呼1 のプロンプトから照合指示を外した A/B が要る
- 複数 UserPromptSubmit hook が同時に `additionalContext` を返したときの合成挙動
- `System One Adapter`（公式 MIT）で他 provider と同じ contract で比べられるが、
  Jev との calibration 同等性は未証明

## Status

**2026-09-20**: 探索と部分実装まで進めたが、着手順を plan の優先度でなく「着手しやすさ」で
選んだ結果、plan 自身が「枠に効かない」とした Security Review shadow に時間を使い、自作の
脆弱性を自分で潰すループに入った。**この日の変更は全て Rewind した**（plugin 導入を除く）。

blocked の内容:
- **何を待っているか**: Fable 枠の回復。判定役を通常どおり引ける状態で、Jev を入れる前後を
  比べられること
- **誰が動かせるか**: 人間（著者）。枠の回復と、外部送信を許容する範囲の判断
- **いつ再評価するか**: 上の review-when

**2026-09-20 追記**: 外部リサーチレポート（Jev 周辺の既製実装と構想の棚卸し、as-of 2026-09-20）を
突き合わせた。上の候補 5 つに無い機構が 2 つ出たので分岐させた —— [RFC-0025](0025-jev-decision-contract-registry.md)
（判定を版付きで貯める registry。本 RFC の設計原則 4 の執行装置）と
[RFC-0026](0026-jev-agent-trace-sensor.md)（走り終わりの done / stuck 判定）。3 本まとめて検討する。
レポートの既製 plugin 群（jevwire / fast-jev-compaction / jev-guard / skillbox / model-router）は
上の Rationale の却下理由に当たるので起票しない。

**2026-09-21**: 著者の指示で blocked を解き、**候補 2（skill ルーター）のみ**着手。既製実装を再調査した
（as-of 2026-09-21）— Claude Code hook としての cookbook 忠実実装は 0 件、Hermes 向けに 1 件
（`DECRUX9812/typesafe-skill-router` @ `f150284`、MIT）。上の Rationale の既製 plugin 却下は維持し、
既製を入れず cookbook から `skills/jev-skill-router/`（`origin: shimo4228`、公開予定）として自作する。
DECRUX からは知見 2 点（255 choices 上限の chunk / Choice と fits が割れたときの margin 規則）だけを
credit 付きで借り、コードはコピーしない。shadow（注入なし・ログのみ）から入り、inject への切替条件は
観測量で置く（routed ≥ 200 行、うち同ターンで skill 使用あり ≥ 40 行）。roster は user / plugin /
project の 3 系統。候補 1・3〜5 は未着手のまま（Fable 枠回復後に再評価）。

**2026-09-21 追記（同日）**: 著者判断で範囲を確定した。
- **候補 1（daily-research の候補照合）・3（session-judgment-mining の仕分け）・4（judge の二値チェック分解）は
  実装しない。** 理由は保守コスト — harness 固有の skill / protocol の判定経路に外部 API を差し込むと、
  判定器ごとに較正・security review・質問文の版管理が増える。再訪条件: shadow の skill ルーターで Jev 判定の
  安定性が自分のログで読め、かつ Fable 枠の逼迫が続くとき
- **候補 5（Security Review shadow）は作らない。** 本 RFC 自身が「枠は空かない」と書いた候補で、
  tool call / commit の guard 系は community 実装が既に複数ある
- **候補 2 は Claude Code プラグインとして公開する。** 同日の再調査で、既製の Claude Code 対応実装
  （`Dicklesworthstone/skillranker` ほか）が既にあると分かった（ADR-0074 Context の注記）。それでも
  公開する枠: `/plugin install` で入る・純 MIT・依存ゼロ・shadow-first の判定ログ・user / plugin /
  project の名簿統合
- RFC-0026（trace sensor）は自作せず、Claude Code plugin `valentynkit/jev-belay`（Stop hook、MIT）を
  shadow mode で試す候補として RFC-0026 側に記録する

**2026-09-21 追記（公開）**: 候補 2 を Claude Code plugin として公開した —
[shimo4228/jev-skill-router](https://github.com/shimo4228/jev-skill-router) 0.1.0（MIT、CI 緑、テスト 104 本）。
正本は `skills/jev-skill-router/`、公開 repo の `tools/sync-from-local.sh` が固定 allowlist で一方向同期する
（`.claude-plugin/`・`hooks/`・README・CHANGELOG・`.github/` は repo root 資産で同期対象外）。この機械には
user scope で install 済み（shadow、key は `~/.config/typesafe/api_key` にフォールバック）。inject への切替条件は
ADR-0074 Decision 4 のまま。awesome list への掲載 PR を 3 本出した: cobanov/awesome-jev#47、
AbdelStark/awesome-typesafe#72、yibie/awesome-jev#91（メンテナ本人であることと AI 生成を開示）。
**残り**: 公開 repo に `.claude/verify.sh` が無く、暫定 Bandit hook が tests の `/tmp` リテラル（B108、path 比較のみで
偽陽性）で commit を止める。公開時の 1 commit は著者承認の bypass で通した。次に Python を commit する前に
skill `verify-bootstrap` でゲートを立てる。

**2026-09-21 追記（公開後の評価）**: 候補 2 は動かしてみて期待値が小さいと分かった（理由と最初の 6 判定は
ADR-0074 Decision 節末尾の同日注記）。本 RFC の動機「判定を Max 枠の外へ逃がす」にも応えていない —
Claude Code の skill 選択は消えず、Jev の呼び出しが上乗せされるだけ。shadow は計器として回し続け、
ADR-0074 の観測量で読んで、読めなければ外す。function hooks（Claude Mods）で skill 一覧そのものを絞る案は
可能だが（`prompt.attachment` の `skill_listing`）、作り込みは沼になるので**やらない**と著者が決めた。
公開 repo の README は、同じ実装を考える人の参考になるよう、効きにくい条件と実測をそのまま書く。

**2026-09-25 追記（候補の外から 1 本、本番）**: 候補 1〜5 に無い使い方を 1 本、本番で置いた — RFC と ADR の review-when を jev-research-pipeline の新しいノートと Jev で毎朝照合する launchd job（`skills/review-when-watch/`、[ADR-0080](../docs/adr/0080-review-when-watch-production-first.md)）。Max 枠の判定を移すのではなく、今は誰もしていない照合を安い判定で新しく始める形で、本 RFC の動機とは別の価値（見直し条件の見落としを減らす）に立つ。著者の指示で shadow を経ずに本番とし、全組の生の読み値を RFC-0025 の最小形のログに残す。

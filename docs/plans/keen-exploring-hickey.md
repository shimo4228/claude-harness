# Plan: lint カバー範囲の global 規約 — 「予算系 lint」の但し書きを verify-bootstrap に置く

## Context

2026-08-27 の X 投稿（複雑度予算 / LOC 制限 / bundle 予算 / ABC — 「予算に当たったら閾値を
上げずに agent に刈らせる」）を発端に、82 repo / 104 config の実測（2026-08-28）で
予算系 lint のカバーがゼロ（唯一の例外は zafu-ios の SwiftLint 上流既定）と判明した。
依頼は「global で lint カバー範囲の規約を置くべきか、置くなら何を」のゼロベース設計。
「不要」も正解として許容されている。

## 診断（設計の根拠）

実測が示すのは「repo が規約に従わなかった」ではない。**既存規約に穴が 1 つある**:

- verify-bootstrap の lint category の問いは既に「複雑度」を名指ししている。しかし
  strictness 規律「既定は最大 strict」は **既定 rule 集合の strict 化**として運用され、
  予算系 rule（C901 / PLR09x / file LOC）は**主要 linter の既定に入っていない**
  （Ruff 0.16.0 の 413 rule 拡大後も C90/PLR は既定外。ファイル LOC 上限は Ruff に存在
  すらしない — astral-sh/ruff#970）。つまり「最大 strict」に従っても予算系は**構造的に
  素通りする**。9 repo 全部で空だったのは規律違反ではなく、この盲点の再現
- 予算系 rule は correctness rule と性質が違う: **閾値（予算）という repo 固有の決定**を
  要する。実測では分布が repo 間で 2.7〜4.7 倍割れる（C901 p99 = 10〜27、LOC p90 =
  185〜862）ので、**global 数値は必ずどこかの repo と不一致になる**（ADR-0042 が退役させた
  「repo と一致しない固定チェックリスト」の再生産）。一方、**閾値の決め方の手順**は既に
  harness 内に正本がある — skill review-to-lint の「免除境界を先に実測する。既存 corpus
  全件に当てて違反数を数えてから閾値を決める」
- 投稿の核心「超えたら上げずに刈る」は lint 設定でなく運用規約で、機械強制できない。
  ただし verify-bootstrap の strictness 規律（warn → drain → error の一方向 ratchet、
  インライン抑制の禁止）と**同族**であり、同じ節に 1 行で足せる

結論: **新設物ゼロで、既存 skill verify-bootstrap への追記（約 10 行）+ ADR 1 本**。
global が持つのは「予算系という区分の名前」「閾値の決め方（既存正本への参照）」
「上げずに刈る運用規約」だけ。数値・ツール名・展開キャンペーンは持たない。

## 採用案

### 1. skill `verify-bootstrap` への追記（正本の編集、3 箇所・計 10 行前後）

**(a) Step 2 の lint category に但し書き**（表の下に 1 段落）:

- 予算系 rule（複雑度・関数/ファイル長・bundle サイズ等、**閾値を要するもの**）は主要
  linter の既定に含まれないのが通例 — 「最大 strict」の既定運用では拾えないため、lint
  category を埋めるとき**明示的に問う**。stack の標準 toolchain が既定で予算を持つ場合
  （実例: SwiftLint の cyclomatic_complexity / file_length）は追認して verify.md に
  1 行記録するだけでよい
- 閾値は global に定めない（repo 間で分布が数倍割れる実測、2026-08-28）。決め方は
  skill `review-to-lint` の免除境界の原則に従う: **既存 corpus 全件に当てて分布を実測
  してから、現状の外れ値だけが赤くなる位置に置く**。ゲートを初日に赤くする閾値は
  免除境界の設計ミス

**(b) Step 3 の strictness 規律に 1 行**:

- 予算系 rule の閾値は ratchet と同じく**一方向**: 超過したら閾値を上げるのではなく
  **刈る**（dead code・重複の除去、分割）。閾値の設定行には「上げずに刈る。変更は
  verify.md に日付つき理由」のコメントを付ける — 赤くなった瞬間に config を触る agent の
  目に入る位置がこの規約の配達点

**(c) Step 5 の verify.md 記録様式**: 予算系は既存様式（選定日・理由・再調査トリガー必須）
に**閾値と実測分布の as-of** を加えて記録する（例示を 1 行追加）。

### 2. ADR 1 本（採番は adr-writer skill 経由）

決定の記録: 予算系 lint は lint category の一部（新カテゴリではない）/ 閾値は per-repo
実測・global 数値なし / 展開は需要駆動（次の bootstrap / audit 時に発火。backfill
キャンペーンなし）/ 「上げずに刈る」の配達点は閾値行コメント + FAIL 検出行。
Review-when に下の失効条件を書く。

### 3. ADR-0055 への日付つき注記（supersede 候補、削除しない）

Alternatives「監視計器・ブレーキ機構の新設を却下 — 削減だけが機構総量を減らせる」の
射程を狭める注記: **既存 verify ゲート内の標準 lint rule による予算は「機構の新設」に
当たらない**（新 hook・新 script・新セッション・自作計器のいずれも増えない。増えるのは
既存 config の行だけ）。ADR-0055 が却下したのは review chain への自作比率ダイヤルで
あって、既製 lint の select ではない — この整理を著者が退けるなら本件全体が却下に戻る
（その分岐も ADR に明記する）。

### 展開（しないことの明記）

- **82 repo への backfill はしない**。規約は次に verify-bootstrap（bootstrap / audit
  モード）が走った repo でだけ発火する — RFC-0005 の需要駆動原則のまま。verify.sh を
  持つ repo が 3 つしかない現状では、真のボトルネックは予算 lint でなく bootstrap の
  適用範囲だが、それは別の需要判断であり本件のスコープ外（ADR の Context に観測として
  1 行残す）
- 拘束力: **新しい宣言義務は作らない**。lint category の「空欄と『無い』は別物」規律と
  verify.md の既存記録義務に乗るだけ。audit モードの作業も増えない（再調査トリガーに
  該当した entry だけ引き直す既存動作のまま）

## Build-or-not 4 問（judge-tier 自答）

1. **存在すべきか** — 既存流用で解けるか: 解けない。verify-bootstrap の現行文面は
   「最大 strict」が予算系を構造的に落とす盲点を持ち、9 repo × 0 件はその再現。
   ただし解は「追記」であり新規資産ではない
2. **適正な大きさ** — SKILL.md 追記 10 行前後 + ADR 1 本 + ADR-0055 注記 3 行。上限宣言:
   追記が 20 行を超えるなら設計が間違っている（references/ 逃がしでなく削る）
3. **誰が消費するか** — 次に bootstrap / audit を回すセッション（読み手が確実に存在する
   位置 = 既に読まれている skill の中）と、予算超過の赤を見た build セッション
   （config コメントで配達）
4. **失効条件** — 下記

## 捨てた選択肢

| 案 | 却下理由 |
|---|---|
| 規約を置かない（各 repo が個別判断） | 「個別判断の入口」自体が verify-bootstrap であり、その文面が予算系を落とす盲点を持つ。盲点を放置すれば次の bootstrap でも同じゼロが再現される。9 repo × 0 は偶然でなく構造 |
| global 数値閾値（C901=10 等）を規約に書く | 分布が repo 間で 2.7〜4.7 倍割れる実測に正面衝突。ADR-0042 の「repo と一致しない固定チェックリスト」の再生産。数値は最速で腐る層 |
| 新規 skill（complexity-budget 等） | lint 選定の正本は verify-bootstrap。二重定義は drift（skill-creator の境界規律）。持つべき内容が 10 行なら skill にならない |
| 常駐 rule に置く | rules の採用基準は「環境固有の事実・配線・罠」で、手順は skill 層（rules/README）。毎セッション常駐させる価値がない — 発火点は bootstrap / audit 時のみ |
| ADR 単独（skill 編集なし） | verify-bootstrap は ADR を読まない。次の bootstrap セッションに届かない記録は規約として機能しない |
| 82 repo への backfill キャンペーン | RFC-0005「作り置きは形骸化リスク」。79 repo は verify.sh すら無く、使われない lint は drift 負債。需要駆動（次の bootstrap / audit）で足りる |
| strictness を「select ALL → 理由付き除外」に強化して自動で拾わせる | Ruff 固有の戦術で tool-agnostic でない（表を持たない設計に反する方向）。かつ閾値決定と「刈る」運用は依然別途必要 — 盲点の半分しか塞がらない |
| 「刈る」規約の機械 guard（閾値引き上げを検知する hook 等） | ADR-0055 が却下した自作計器そのもの。観測前の防衛機構は建てない。回避の実例を観測した 1 回目に再訪（失効条件へ） |
| implementation-chain に「刈る」規約を置く | 発火点が違う — 規約が要るのはゲートが赤くなった瞬間で、その時セッションが見るのは lint 出力と config。chain 定義は読み直されない。配達点は閾値行コメントが最短 |

## 既存 ADR / RFC との衝突（supersede 候補として提示）

- **ADR-0055**（削減だけが機構総量を減らせる）: 上記 §3 の射程狭め注記。衝突は「自作計器
  の新設」と「既製 lint の select」の区別で解消するが、この区別自体が著者判断事項
- **ADR-0042**（固定チェックリストの退役）: 衝突なし・むしろ設計根拠。global 数値を
  持たない理由としてで引用する
- **RFC-0005**（需要駆動）: 衝突なし。展開方式をこの原則に従属させる
- **verify-bootstrap の「表を持たない」設計**: 追記は区分名と手順参照のみで、ツール名
  一覧・数値表を足さない。「調べ方と契約だけを持つ」の内側に収まる

## 書く文面の骨子（完成文は実装時）

verify-bootstrap Step 2 追記の骨子:

> **予算系 rule（閾値を要する複雑度・サイズ系）は既定に頼らない。** 主要 linter は
> 予算系を既定 OFF で出荷する（閾値が opinionated なため）。「最大 strict」の運用では
> 構造的に素通りするので、lint category を埋めるとき明示的に問う。stack の標準
> toolchain が既定で予算を持つなら追認記録のみ。閾値は repo の corpus 全件の分布を
> 実測してから外れ値境界に置く（skill `review-to-lint` の免除境界の原則。repo 間で
> 分布は数倍割れるので global 数値は無い — 2026-08-28 実測）。

Step 3 追記の骨子:

> 予算系の閾値は一方向: **超過したら閾値を上げずに刈る**。閾値の設定行に
> 「上げずに刈る — 変更は verify.md に日付つき理由」のコメントを付ける。

## 失効条件（ADR の Review-when にそのまま書く）

- 主要 linter が予算系 rule を**既定 select に含める**ようになった時（downward
  dissolution — 「最大 strict」が自然に拾うので但し書きは不要になり、削除する）
- cognitive complexity 等の後継指標が主要 linter に実装された時（astral-sh/ruff#2418
  の close 等）— 「複雑度予算」の形自体を引き直す
- 予算 lint 導入 repo で**閾値引き上げによる回避**を観測した 1 回目 — コメント配達では
  足りない。guard の再訪か規約の撤回かをその時判断する
- 12 ヶ月間、どの repo の bootstrap / audit もこの節を発火させなかった時 — 形骸化。
  削除候補（Scaffold Dissolution）
- モデル世代交代で agent の生成コードが予算に構造的に当たらなくなった時
  （generation-audit の再監査対象）

## 実装手順（承認後）

1. `skills/verify-bootstrap/SKILL.md` を編集（上記 3 箇所。skill-creator は読了済み —
   改修規模は小、境界の重なりは review-to-lint への参照で解消済み）
2. skill `adr-writer` で ADR を採番・生成（decision packet は本 plan の §採用案 + 失効条件）
3. `docs/adr/0055-*.md` の Alternatives に日付つき注記を追加
4. 検証: `python3 scripts/hooks/harness_lint.py` + skill-health の scan_refs（dangling 0）+
   `.claude/verify.sh`（harness 自身のゲート）
5. commit（chore、Chain Matrix: chore × Code Review = C に該当しない設定文書編集。
   Doc Sync: ADR 新設に伴う index 更新）。公開 repo への同期は別途 harness-sync
   （著者起動）

実装はこのセッションでは行わない — plan の承認は人間が出す（依頼の指定どおり）。

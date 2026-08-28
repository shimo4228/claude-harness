# ADR-0056: 予算系 lint の global 規約は verify-bootstrap の但し書きとして置く（数値・ツール表・backfill なし）

## Status

accepted

## Date

2026-08-28

## Context

2026-08-27、X の投稿（Nate Berkopec / Sam Saffron）が「人間には厳しすぎるが agent には効く
自動 lint ルール」として、サイクロマティック複雑度予算・ファイル LOC 制限・CSS/JS サイズ
制限・ABC スコアを挙げた。投稿の主眼は閾値の数値そのものではなく運用面にある——予算に
当たったら閾値を上げるのではなく、agent に刈らせる、という一方向の規律である。本 ADR では、
閾値という repo 固有の決定を要する複雑度・関数/ファイル長・bundle サイズ系の rule を
「予算系 rule」と呼ぶ（本 ADR の呼称。X 投稿の "budget" に対応する）。

2026-08-28 に実測した。計器は 2 系統: (1) **config census** — 82 repo の lint / build
config 104 本を対象に、予算系 rule の設定語（C901 / mccabe / max-complexity / PLR09* /
max-lines / max-module-lines / size-limit / radon / lizard）を検索してヒット 0 件。
(2) **分布測定** — `uvx ruff@0.16.1 --isolated` で閾値を 0 に倒して全関数の実測値を回収
（ファイル LOC は Ruff に該当 rule が無いため `git ls-files` + 行数集計）。唯一の例外は zafu-ios で、SwiftLint のデフォルト有効ルール（cyclomatic_complexity
10/20、file_length 400/1000 等）が `.swiftlint.yml` に記述なしで効いており、Swift 最大
ファイルは 397 行と警告閾値 400 行の 3 行手前——予算が実際に刈る力として働いている唯一の
実例だった。

このゼロは規律違反ではなく既存規約の盲点に由来する。skill `verify-bootstrap` の lint
category は「複雑度」を名指し済みだが、strictness 規律「既定は最大 strict」は既定 rule
集合の strict 化として運用されており、予算系は主要 linter の既定に入っていない。Ruff
0.16.0 の既定 413 rule 拡大後も C90 / PLR は既定外のままで、ファイル LOC 上限は Ruff に
存在しない（astral-sh/ruff#970 で formatter 非互換として未実装）。cognitive complexity も
astral-sh/ruff#2418 が 2023-01 から open のままである（いずれも 2026-08-28 時点）。したがって
「最大 strict」の規律に忠実に従っても、予算系は構造的に素通りする。同 skill Step 3 の
ratchet 文面には「全 rule を warn で入れ」とあるが、census 0 件が示すとおり予算系を
select した repo は無く、strict 化は実運用で既定 rule 集合の範囲に留まっていた。

分布も実測した（git 追跡下の Python 492 ファイル / 9 repo = `~/.claude`・
contemplative-agent・aeon-shop・g-kentei-tool・pdf2anki・tiny-lm-lab・
daily-quest-generator・active-inference-viz・einstein-arena。test ファイル込み、
`~/.claude` は verify.sh の owned_files と同じ所有権基準で選別。2026-08-28）。repo 間で分布が 2.7〜4.7 倍
割れる（C901 p99 は repo により 10〜27、ファイル LOC p90 は 185〜862）。global 数値を 1 つ
定めれば必ずどこかの repo と不一致になる——[ADR-0042](./0042-retire-code-reviewer-and-scope-security-review-to-threat-surface.md)
が退役させた「repo と一致しない固定チェックリスト」の再生産になる。

さらに複雑度と LOC は性質が正反対であることも同じ実測でわかった。C901 > 15 の 23 件は
全て production コードだったのに対し、LOC > 500 の 93 件は過半の 50 件が test だった。

verify.sh を持つ repo は 82 中 3 のみである。真のボトルネックは予算系 lint の不在でなく
`verify-bootstrap` の適用範囲そのものだが、これは別の需要判断であり本 ADR のスコープ外
として観測に留める。

## Decision

1. 予算系 lint の global 規約は skill `verify-bootstrap` への但し書き（約 20 行、
   2026-08-28 適用済み）として置く。新規 skill / rule / hook / script は作らない。
   - Step 2（lint category）: 予算系 rule は既定に頼らず明示的に問う。stack の標準
     toolchain が既定で予算を持つ場合は追認して `verify.md` に 1 行記録するだけでよい。
     閾値は global に定めず、既存 corpus 全件の分布を実測してから現状の外れ値だけが
     赤くなる位置に置く（免除境界の原則は skill `review-to-lint` を参照——正本はそちら、
     複製しない）。
   - Step 3（strictness）: 予算系の閾値は ratchet と同じく一方向とする——超過したら
     閾値を上げずに刈る。閾値の設定行には「上げずに刈る——変更は `verify.md` に日付つき
     理由」のコメントを付ける。ゲートが赤くなった瞬間に config を触る agent の目に入る
     位置が配達点である。
   - Step 5（記録）: 予算系は閾値と実測分布の as-of も `verify.md` に記録する。
2. global な数値閾値・ツール名の表は持たない（`verify-bootstrap` の「表を持たない」設計の
   内側に収める）。
3. 展開は需要駆動とする。次に `verify-bootstrap`（bootstrap / audit モード）が走った
   repo でだけ発火する。82 repo への backfill キャンペーンはしない（RFC-0005 の需要駆動
   原則に従属）。
4. 新しい宣言義務は作らない。既存の「空欄と『無い』は別物」規律と `verify.md` の記録義務に
   乗るだけとする。audit モードの動作様式（再調査トリガーに該当した entry だけ引き直す）は
   変えないが、予算系 entry 1 行分の突き合わせは増える（Consequences Negative に計上）。
5. [ADR-0055](./0055-review-chain-single-pass-regression.md) の Alternatives「レビュー密度の
   維持 + 肥大の監視計器の新設」（却下: 計器・ブレーキ機構の新設）に日付つき注記で射程を
   狭める（partial、Status は変えない）。却下の対象は review chain への自作計器・ブレーキの
   新設であり、既存 verify ゲート内で既製 lint の予算系 rule を select することは「機構の
   新設」に含めない——新 hook・新 script・新セッション・自作計器のいずれも増えず、増えるのは
   既存 config の行だけである。この区別を著者が退けるなら本 ADR 全体が却下に戻る。

## Review-when

- 主要 linter が予算系 rule を既定 select に含めるようになった時——downward dissolution。
  「最大 strict」が自然に拾うので `verify-bootstrap` Step 2 の予算系段落は不要になり削除する
- cognitive complexity 等の後継指標が主要 linter に実装された時（例:
  astral-sh/ruff#2418 の close）——「複雑度予算」の形自体を引き直す
- 予算 lint 導入 repo で閾値引き上げによる回避を観測した 1 回目——コメントによる配達では
  足りない。guard の再訪か規約の撤回をその時判断する
- `verify-bootstrap` Step 2 の予算系段落が、12 ヶ月間どの repo の bootstrap / audit でも
  発火しなかった時（固定対象: 同段落。判定は bootstrap / audit セッションの `verify.md`
  生成物に予算系 entry が現れたか）——形骸化、削除候補（Scaffold Dissolution）
- モデル世代交代で agent の生成コードが予算に構造的に当たらなくなった時——
  `generation-audit` の再監査対象

## Alternatives Considered

### 規約を置かない（各 repo の個別判断に任せる）

却下: 個別判断の入口自体が `verify-bootstrap` であり、その文面が予算系を落とす盲点を
持っている。放置すれば次の bootstrap でも同じゼロが再現される。82 repo / 104 config で
0 件は偶然でなく構造である。

### global 数値閾値（C901=10 等）を規約に書く

却下: repo 間で分布が 2.7〜4.7 倍割れる実測に正面衝突する。ADR-0042 が退役させた固定
チェックリストの再生産になる。数値は最速で腐る層である。

### 新規 skill（complexity-budget 等）を建てる

却下: lint 選定の正本は `verify-bootstrap`。二重定義は drift する（skill-creator の境界
規律）。持つべき内容が約 20 行なら skill にならない。

### 常駐 rule に置く

却下: rules の採用基準は環境固有の事実・配線・罠で、手順は skill 層に置く
（`rules/README.md`）。発火点は bootstrap / audit 時のみで、毎セッション常駐させる価値が
ない。

### ADR 単独（skill 編集なし）

却下: `verify-bootstrap` は ADR を読まない。次の bootstrap セッションに届かない記録は
規約として機能しない。

### 82 repo への backfill キャンペーン

却下: RFC-0005 の「作り置きは形骸化リスク」原則に反する。79 repo は verify.sh すら無く、
使われない lint は drift 負債になる。

### strictness を「select ALL → 理由付き除外」に強化して自動で拾わせる

却下: Ruff 固有の戦術で tool-agnostic でない（表を持たない設計に反する方向）。かつ閾値
決定と「刈る」運用は別途必要で、盲点の半分しか塞がらない。

### 「刈る」規約の機械 guard（閾値引き上げを検知する hook 等）を新設する

却下: [ADR-0055](./0055-review-chain-single-pass-regression.md) が却下した自作計器その
ものである。観測前の防衛機構は建てない。回避の実例を観測した 1 回目に再訪する
（Review-when に置いた）。

### `implementation-chain` に「刈る」規約を置く

却下: 発火点が違う。規約が要るのはゲートが赤くなった瞬間で、その時セッションが見るのは
lint 出力と config である。chain 定義は読み直されない。配達点は閾値行コメントが最短
である。

## Consequences

### Positive

- 次の bootstrap / audit から予算系が lint category の明示的な問いになり、「最大 strict
  なのに予算ゼロ」の盲点が閉じる
- 「超えたら上げずに刈る」が閾値行コメントとして、赤を見た agent に最短距離で届く
- 新設物ゼロ——機構総量は増えない（増えるのは skill 本文約 20 行と将来の config 行のみ）

### Negative

- 発火が需要駆動（次の bootstrap / audit 待ち）なので、当面カバーゼロの状態が続く。
  verify.sh 保有 3 repo 以外には届かない
- 「上げずに刈る」はコメントによる運用規約で機械強制ではない——閾値引き上げによる回避は
  検出できない（Review-when で 1 回目の観測時に再訪する）
- 予算系 entry の `verify.md` 記録（閾値 + 分布 as-of）は audit 時の突き合わせ作業を
  わずかに増やす

### Neutral / Follow-ups

- [ADR-0055](./0055-review-chain-single-pass-regression.md) への日付つき注記は本 ADR と
  同じ commit で行う（Decision 5）
- 実測数値（census 0 件・分布・repo 間比）の**正本は本 ADR の Context**。
  `skills/verify-bootstrap/SKILL.md` と ADR index の行は要約・ポインタであり、drift したら
  本 ADR 側を正として他を直す（数値は最速で腐る層 — 複製箇所をこの 2 つに限定する）
- bundle 予算（CSS/JS）は未測定のまま——対象 repo の bootstrap 時に同じ手順で問う

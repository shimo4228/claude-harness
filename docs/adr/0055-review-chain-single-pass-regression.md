# ADR-0055: レビュー chain を fresh-context 1 段 + 条件付き Security へ縮約する（公式推奨密度への回帰）

## Status

accepted

## Date

2026-08-27

## Context

レビュー → 修理 → 再レビューのループに減衰項が無く、発振していた。LLM reviewer は問われれば
必ず何か返すため、「指摘ゼロまで回す」という暗黙の終了条件は構造的に到達不能である。CA
（contemplative-agent）では CA ADR-0085 の無人 weekly fix
chain が補強を重ねた末、CA ADR-0098 で 7 セッション → 1 に
畳まれ、`build_decision_packet.py` 1,987 行 + テスト約 3,400 行が一括削除された。

harness 側でも同じパターンが実測された。規約（HIGH 以上 + producer 引用）の下で出た diff 外
HIGH 指摘は 6 件（うち台帳起票は 4 件 = RFC-0011〜0014。`claims.jsonl` の 2026-08-26 の窓の
`--origin review` spawn 4 件と一致。残り 2 件は修理 commit 後の追加指摘で、実際に約 1 日
遅れて処理され結果は変わらなかった）。遡及判定では、即時性が結果に寄与したのは 1 件
（`verify.sh` の `ls-files` 盲点 — loop 自身を壊す欠陥）のみで、残り 5 件は遅延回収でも
結果が変わらなかったと判断した — 起票済み 4 件分は反実仮想の判断であって遅延の実測では
ない（2026-08-26〜27、修理セッションの追跡。**この集約カウントの正本は本 ADR** —
他文書はここを指す）。

著者の主要関心はレビュー起点のオーバーエンジニアリングである。著者はコード本文もレビュー
報告も読まない運用（委任）のため、「報告を人間が読む」ことを前提にしたブレーキは成立せず、
規約そのものを絞るしかない。

公式 best practices（code.claude.com/docs/en/best-practices、as-of 2026-08-27 取得）が同じ
現象を名指ししている。"A reviewer prompted to find gaps will usually report some, even when
the work is sound… Chasing every finding leads to over-engineering: extra abstraction layers,
defensive code, and tests for cases that can't happen. Tell the reviewer to flag only gaps
that affect correctness or the stated requirements, and treat the rest as optional." 同文書が
推奨として示すのは機械検証主体 + fresh-context adversarial review 1 段 + correctness-only
指示という構成である。**公式はこれを下限（"Add an adversarial review step"）として提示して
おり、系統数の上限や再レビュー禁止を定めてはいない** — 密度の縮約（1 段まで）と 1 往復規律
（Decision 4）は、上の発振の実測に基づく本 ADR のローカル判断である。

再編前の常設は Review 表 6 系統（Simplify + 並列 5: Code / Security / Silent-Failure /
Cross-Model / ADR-Record）だった。[ADR-0042](./0042-retire-code-reviewer-and-scope-security-review-to-threat-surface.md)
が Code Review セルを単一 agent から built-in `/code-review`（Angle A–E + Reuse /
Simplification / Efficiency / Altitude / Conventions の動的多角機構、PLAUSIBLE by default）へ
差し替え、effort を feat/refactor = high に pin したため、1 セルの帯域が大幅に増強される一方、
周囲の系統は削られず総密度は公式推奨の数倍になっていた。

レビュー chain の実証済み save は 1 件だけである。2026-07-31、commit 21f51cc で、7 hook 共通の
git 対象抽出における command-injection 級の欠陥を当時の code-reviewer（ECC 系 agent、
ADR-0042 で退役）が CRITICAL で発見し、PoC を実測して確認した（攻撃被害の記録ではなく発見の
記録。回帰は `tests/git-target-extraction.bats`）。専任 security-reviewer 自身の実証済み
save は無い。ただし発見箇所は trust boundary（無人実行の hook）であり、脅威面条件付きの
security review を残す判断材料とした。

`rules/common/akc-cycle.md` はモデル世代交代を downward dissolution のトリガーと定める。
多段レビュー構成はより弱い世代の build セッションを前提に組まれた足場であり、Fable/Opus
世代の build ではその前提ごと再監査対象である。

## Decision

1. 常設レビューを fresh-context 1 段に縮約する（implementation-chain の Review 表）。
   built-in `/code-review`（effort は全種別 `medium` を明示 — ADR-0042 の feat/refactor =
   high pin を降格。low/medium は最も確信の高い findings のみを報告する帯（/code-review の
   effort 定義）。high は著者の明示要求時のみ）+ 脅威面を動かす diff のみ
   `security-reviewer` が条件付き並走する（発火条件は ADR-0042 の脅威面条件のまま。
   著者判断: 常設でなく必要時発火で残す）。
2. Chain Matrix から Simplify / Silent-Failure Review / Cross-Model Review / Premise
   Challenge の各行を削除する。per-commit Simplify は廃止し batch opt-in へ移す（quality
   軸の Reuse / Simplification / Efficiency / Altitude は built-in `/code-review` が内蔵。
   batch 実績: CA commit e739912 の 22 commit 一括、CA commit edca8cf の Review 後実行 +
   再 Verify）。
   codex-review（diff review・plan 段の Premise Challenge とも）はユーザー明示要求のみの
   opt-in へ移す。ADR / Record Review 行は削除する（adr-reviewer の配線は skill:
   `adr-writer` 内が唯一 — 重複配線の解消）。
3. reviewer への指示を必須化する: 「correctness / stated requirements に効く gap のみ
   報告。それ以外は optional として適用しない。diff 外の指摘は報告不要（気づいたら
   1 行、修理はしない）」。**この「気づいたら 1 行」が Decision 5 の loop-breaking 起票の
   入力チャネルとして残る** — 本 ADR の唯一の「結果を変えた」実例（`ls-files` 盲点）は
   diff 外指摘として上がったもので、このチャネルを完全に閉じると Decision 5 が救う対象
   クラス自体が観測できなくなる。
4. 1 往復規律を新設する: Review → 修理は 1 往復まで。修理は指摘に答える最小 diff、修理
   diff の検証は機械ゲート（Verify）のみで再レビューしない。
   **［2026-08-27 注記: 本項は同日の著者判断で撤回した。** 公式 best practices の再読で、
   「fix them and re-review」は推奨でなく subagent 構成の利点の記述（自然な往復）であること、
   および発振の主因は往復でなく系統数（6 系統 × 各系統の並列 agent 起動 — Simplify 単体で
   4 agent、全発火で 10 前後）だという著者判断による。常設 1 系統 + effort medium +
   correctness-only の下では往復を制限しない。修理連鎖の発振が再発した時に本項を入れ直す。
   「修理は最小 diff」は維持。］
5. diff 外指摘の起票規約を再絞り込みする（`rules/common/task-tracking.md` + skill:
   `task-stocktake` 「レビュー指摘の起票規律」）。build セッションからの即時起票は
   「loop 自身を壊す欠陥」のみとする。それ以外は severity 不問で commit body に 1 行
   （producer 付き）残して捨てる。回収機構（tick sweep 等）は作らない。
6. `hooks/simplify-order-notice.sh` と `tests/simplify-order-notice.bats` を退役する
   （Simplify 前置き順序の強制対象が消滅）。`settings.json` の当該エントリと
   `hooks/README.md` の行も削除する。`review-model-notice.sh`（judge-tier の直呼び
   block + model pin）は維持する。

## Review-when

- 公式 best practices の review 推奨（1 段 + correctness-only）が大きく改版された時
  （引用は as-of 2026-08-27）
- 常設 1 系統の下でレビュー起点の修理連鎖が発振（修理が次のレビュー対象になる連鎖が
  収束しない）するのを観測した時 — 1 往復規律（Decision 4、2026-08-27 撤回）を入れ直す
- 脅威面に触れる diff の実害を Code Review + 条件付き Security Review が見逃した 1 回目
- エラー握り潰し型（catch / fallback の silent failure）の実害を観測した 1 回目 —
  専任軸の復活を再訪する
- effort medium の Code Review が見逃した correctness の実害（出荷後に発覚し、high 帯なら
  検出し得たと遡及判定できるもの）を観測した 1 回目 — effort pin を再訪する

## Alternatives Considered

### 起票の遅延回収

commit body を task-triage の定期 tick で sweep し、producer 再照合が通るものだけ起票する
案。前セッションの叩き台だった。却下: 回収機構という新しい機構を足すことになる。durable
な記録は commit body が既に担っており、遡及判定（Context の 6 件中 5 件 — 反実仮想を含む）
は遅延回収でも結果が変わらないことを示した。

### レビュー密度の維持 + 肥大の監視計器の新設

密度は維持しつつ、行数/機能・セッション数/機能の比率ダイヤル等の監視計器やブレーキ機構を
新設する案。却下: 計器・ブレーキ自体が機構の追加であり、CA が計器づくりで膨れた経緯
（CA ADR-0095）と自己矛盾する。削減だけが機構総量を減らせる唯一の手である。

> **注記（2026-08-28, ADR-0056）**: 本却下を狭める（partial、Status は変えない）。
> 却下の対象は review chain への自作計器・ブレーキの新設であり、既存 verify ゲート内で
> 既製 lint の予算系 rule を select することは「機構の新設」に含めない——新 hook・新
> script・新セッション・自作計器のいずれも増えず、増えるのは既存 config の行だけである。
> 詳細は [ADR-0056](./0056-budget-lints-as-verify-bootstrap-annotation.md)。

### security-reviewer の統合（/code-review の prompt 1 行への折り込み）

security-reviewer も畳み、脅威面検査を `/code-review` の prompt 1 行に折り込む案。著者判断
で却下: 条件付き発火（必要時のみ）で専任 agent を残す。全 repo 深掘りは plugin
`claude-security`（opt-in）が受け皿になる。

### レビュー全廃（機械ゲートのみ）

却下: fresh-context 1 段は公式推奨自体に含まれており、21f51cc 型の意味的発見（機械ゲートで
出ない信頼境界の推論）の受け皿が要る。

### per-commit Simplify の維持（順序のみ Review 後へ反転）

却下: built-in `/code-review` が quality 軸を内蔵しており、per-commit の別パスは二重になる。
批評でなく適用が要る時だけ batch で呼べば足りる。

## Consequences

### Positive

- 発振（レビュー→修理→再レビュー）が 1 往復規律と再レビュー禁止で構造的に切れる
- レビューのセッション・トークン消費が大幅に減る（6 系統 × 往復 → 1〜2 系統 × 1 往復）

> **注記（2026-08-28）**: 上 2 点の「1 往復規律」への依拠は Decision 4 の 2026-08-27 撤回
> により失効。発振の遮断は系統数の削減（6 系統 → 常設 1 系統 + effort medium +
> correctness-only）が担い、往復は制限しない。消費の見積りは「1〜2 系統 × 自然な往復」に
> 読み替える。
- diff 外起票の補充エンジンが止まり、台帳が収束方向になる
- 公式推奨と同型になり、外部の読者・ツールが chain を既知パターンとして読める

### Negative

- silent-failure 軸（エラー握り潰し）の専任レビューが消え、`/code-review` の射程に依存する
  （Review-when に復活条件を置いた）
- cross-model 脱相関が opt-in になり、既定では同モデル系統の盲点が残る（seam 自体は
  [ADR-0013](./0013-cross-model-review-seam-via-codex.md) のまま維持）
- effort medium 化で「不確実だが real」な指摘の捕捉率が下がりうる（公式の band 定義上の
  トレードオフ）
- commit body に 1 行で残した diff 外指摘は、能動的な回収機構を持たない（設計通り —
  必要になった時に読む記録層）

### Neutral / Follow-ups

- 本 ADR が narrow した先行 ADR には日付つき注記で接続した: [ADR-0013](./0013-cross-model-review-seam-via-codex.md)
  （seam 維持・opt-in 化）/ [ADR-0028](./0028-review-notice-full-scope-and-adr-reviewer.md)
  （adr-reviewer の配線を adr-writer へ）/ [ADR-0039](./0039-retire-python-reviewer-simplify-in-chain.md)
  （per-commit Simplify と順序の退役）/ [ADR-0041](./0041-file-review-findings-on-a-verified-premise.md)
  （足切りの再絞り込み）/ [ADR-0042](./0042-retire-code-reviewer-and-scope-security-review-to-threat-surface.md)
  （effort pin 降格）/ [ADR-0048](./0048-sdlc-playbook-translation-and-rfc-conformance.md)
  （付表 1 REVIEW.md 行）
- writing chain（paper / README / 記事系 reviewer 群）は対象外・不変更
- swift-reviewer の去就は [ADR-0042](./0042-retire-code-reviewer-and-scope-security-review-to-threat-surface.md)
  に続き保留（Swift diff では引き続き併用）
- Refactor Clean（refactor 種別専用ステップ）は per-commit Simplify 廃止と独立に存続

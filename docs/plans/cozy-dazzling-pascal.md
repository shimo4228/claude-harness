# Review chain 再編 — 公式推奨密度への回帰

## Context

mondo 議論（2026-08-27）の帰結。著者の主敵は**レビュー起点のオーバーエンジニアリング**:

- レビュー → 修理 → 再レビューのループに減衰項がなく発振する。CA では ADR-0085 chain が
  肥大の末 ADR-0098 で 1,987 行 + テスト 3,400 行の bulk 削除に至った。harness でも
  diff 外 HIGH 起票 6 件中、即時起票に値したのは 1 件のみ（実測 2026-08-27）
- 公式 best practices（code.claude.com/docs/en/best-practices、as-of 2026-08-27）が名指し:
  「Chasing every finding leads to over-engineering」。推奨密度 = **機械検証主体 +
  fresh-context adversarial review 1 段** + 「correctness / stated requirements に効く指摘だけ、
  残りは optional」
- 現行 chain は Review 表 6 系統。ADR-0042 で Code Review セルが単一 agent → built-in 多角機構
  （effort `high` pin、PLAUSIBLE by default）へ増強され、周囲は削られず密度は公式の数倍
- レビュー chain の実証済み save は 1 件（2026-07-31、commit 21f51cc: 7 hook 共通の git 対象
  抽出の command-injection 級欠陥。**当時の code-reviewer** が CRITICAL で発見、PoC 実測で確認。
  攻撃被害ではなく発見の記録）。専任 security-reviewer 自身の実証済み save はゼロ
- モデル世代交代（Fable/Opus build）は akc-cycle rule の downward dissolution トリガー
- 著者判断: diff 外起票は**絞る** / codex-review は**手動 opt-in 化** / per-commit Simplify は
  batch opt-in へ / Security Review は**条件付き発火（必要時のみ）で残す**

## 最終形（code chain）

```
実装 → /code-review 1 段（medium、correctness-only 指示、1 往復）→ 修理（最小 diff）
     → Verify（機械ゲート）→ commit
```

常設レビューはこの 1 段（公式推奨と同型）+ **脅威面を動かす diff だけ** security-reviewer が
条件付きで並走（著者判断: 常時でなく必要時発火で残す）。built-in `/code-review` は quality 軸
（Reuse / Simplification / Efficiency / Altitude）を内蔵しているため（ADR-0042 の調査で確認）、
`/simplify` は chain から外し **batch opt-in**（肥大を感じたとき数 commit 分まとめて。
実績: e739912 の 22 commit 一括）へ。claude-security plugin（全 repo 深掘り）/
codex-review（diff・plan とも）も opt-in。adr-reviewer は implementation-chain から外し、
配線は skill: adr-writer 一本（既存、`SKILL.md:129`）。

## 変更内容

### 1. `skills/implementation-chain/SKILL.md`（正本、最大の変更）

**Chain Matrix（59-73 行）**:
- **削除する行**: `Simplify` / `Silent-Failure Review` / `Cross-Model Review` / `Premise Challenge`
- **`Security Review` 行は残す** — 現行の条件付き発火（ADR-0042 の脅威面条件、85-89/94 行）を
  そのまま維持。脅威面に触れない diff では発火しない
- 条件付き発火の節（75-101 行）から削除行の条件のみ除去

**Review 表（112-119 行）** — 再編後:
| 順 | category | 起動先 |
|---|---|---|
| 1 | Code Review | built-in `/code-review`（fresh-context 1 段、quality 軸内蔵。Swift は swift-reviewer 併用 — ADR-0042 が保留した項目のため今回も判断しない） |
| 1 | Security Review | `security-reviewer`（**脅威面を動かす diff のみ** — 発火条件は Matrix が正本、自発起動しない。従来通り） |

`ADR / Record Review` 行は**表から削除**（重複配線 — adr-reviewer の居場所は skill:
adr-writer が既に持つ。`adr-writer/SKILL.md:129`）。codex の脚は opt-in 化で自然に消える

**effort（91-92 行）**: 全種別 **`medium`**（「fewer, high-confidence findings」帯。
`high` は著者が明示要求したときだけ）

**reviewer への指示（新設）**: /code-review（および security-reviewer）起動 prompt に必ず含める —
「correctness / stated requirements に効く gap のみ報告。それ以外は optional 扱いで適用しない。
diff 外の指摘は報告不要（気づいた場合は 1 行、修理はしない）」

**1 往復規律（新設）**: Review → 修理は 1 往復まで。修理 diff の検証は機械ゲートのみ、
**再レビューしない**。修理は指摘に答える最小 diff に限る

**opt-in 名簿（新設、Review 表の下に短く）**: batch simplify = built-in `/simplify`
（肥大を感じたとき数 commit 分まとめて。judge-tier では実行モデル pin 経由）/ security 深掘り =
claude-security plugin / cross-model = skill: codex-review（diff・plan 両方）/
Swift acceptance = swift-reviewer。いずれも自発発火しない

**Simplify 順序の節（128-136 行）を削除し置き換え**: per-commit Simplify は廃止（quality 軸は
/code-review が内蔵）。batch opt-in の 1 行（上記名簿）に縮退。実績: e739912（22 commit 一括）、
edca8cf（Review 後実行 + 再 Verify、事故なし）

**早期停止条件（171-179 行)**: Security / Cross-Model の言及を Code Review の CRITICAL に統合

### 2. Simplify 前置き強制 hook の退役

- `hooks/simplify-order-notice.sh` 削除、`tests/simplify-order-notice.bats` 削除
  （per-commit Simplify 廃止により順序強制の対象が消滅）
- `settings.json`（git 追跡外）から当該 PreToolUse エントリを削除
- `hooks/README.md` から該当行を削除
- `hooks/review-chain-notice.sh` は文言そのまま（「Review と Verify」で新 chain とも整合）
- `hooks/review-model-notice.sh`（Fable の直呼び block + model pin）は現状維持
  （batch /simplify・/code-review の judge-tier 起動を今後も守る）

### 3. agent / skill の整理

- `agents/security-reviewer.md` **現状維持**（著者判断: 条件付き発火で残す。常時ではない —
  現行の脅威面条件そのまま）。全 repo 深掘りは claude-security plugin（opt-in）
- `agents/adr-reviewer.md` は**現状維持**。配線は skill: adr-writer が唯一の居場所になる
  （implementation-chain の ADR / Record Review 行は削除）
- `skills/codex-review/SKILL.md`: When-to-use から chain 既定（parallel reviewer / Matrix 正本参照）を
  削除し、発火は「ユーザーが明示的に求めたとき」のみに。plan mode（Premise Challenge）も同様。
  「1 回・1 系統」の歯止めは残す
- `agents/silent-failure-hunter` は plugin 側（pr-review-toolkit）なのでファイル変更なし。
  chain からの参照だけ消える

### 4. diff 外起票の絞り込み

- `rules/common/task-tracking.md`「レビュー指摘の扱い」: 「HIGH 以上だけ起票」→
  「build セッションからの即時起票は **loop 自身を壊す欠陥**（次の build が bounce を食う類）のみ。
  それ以外は severity 不問で commit body に 1 行（producer 付き）残して捨てる」。
  producer 引用規律・`spawn --origin review --producer` 要求は維持
- `skills/task-stocktake/SKILL.md:158-180`（正本）: 同じ変更 + 実測根拠追記
  （2026-08-27: 6 件中 5 件は遅延回収でも結果不変）。回収機構（tick sweep 等）は**作らない**
- `scripts/claims.py` は変更なし

### 5. ADR 起票 + 旧 ADR への日付つき注記

新 ADR 1 本（adr-writer skill 経由、番号は実装時採番）。Review-when: 公式 best practices の
review 推奨の大変化 / 発振（レビュー起点の修理連鎖 2 周以上）の再観測 / 脅威面 diff の実害を
Code Review 単独で見逃した 1 回目。

日付つき注記（削除でなく注記、akc-cycle 規約）:
- ADR-0039「bug 軸 × quality 軸の直交 2 本立て」→ built-in /code-review の quality 軸内蔵に
  より per-commit Simplify を batch opt-in へ降格した注記（順序強制 hook も同時退役）
- ADR-0013（cross-model seam）→ seam 維持、既定発火から opt-in へ
- ADR-0041 / ADR-0042 → 起票条件の再絞り込み、effort pin `high`→`medium` の注記
  （Security Review の脅威面条件は ADR-0042 のまま維持）
- ADR-0048 付表 1 REVIEW.md 行の「上回る」→ 超過分として削減（付表本文は書き換えない）

### 6. スコープ外（明記）

- writing chain（paper / README / 記事系 reviewer 群）— 別生態系、今回触らない
- swift-reviewer の去就 — ADR-0042 に続き保留
- CA repo 側 — 本 ADR を根拠に別セッションで波及
- 公開 repo への同期 — 実装後に著者が skill: `harness-sync`

## 実行順

1. implementation-chain SKILL.md 改稿（§1）
2. agent / skill 整理（§3）
3. task-tracking rule + task-stocktake 節（§4）
4. hook 退役 + settings.json + hooks/README.md + review-chain-notice 文言（§2）
5. 新 ADR + 旧 ADR 注記 + docs/adr/README.md index（§5）
6. Verify

## Verify

- `bats tests/`（simplify-order-notice.bats 削除後に全緑）
- `python3 scripts/harness_lint.py`（origin / 参照整合）
- grep 残骸検査: `simplify-order-notice` / `Silent-Failure` / `Cross-Model Review` /
  `Premise Challenge` が skills / hooks / rules / agents / hooks/README.md に
  残っていないこと（ADR・.notes 内の言及は歴史記録として残す）
- commit は git-workflow 規約（`git -C`、`$( )` 禁止）

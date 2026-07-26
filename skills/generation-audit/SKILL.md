---
name: generation-audit
description: "Model-generation-change audit orchestrator — collect the runtime layer (system prompt + tool descriptions) from the live session, cross-check every self-authored asset (rules / CLAUDE.md / skills / agents) against it, classify mismatches as conflict / redundancy / drift, judge each with the intent-evidence-freshness-expiry frame, then hand the evidence to rules-stocktake / skill-stocktake / agent-stocktake for verdicts. Use when a new Claude model generation ships and assets written for the previous one may now conflict with the substrate — 「世代交代したのでハーネスを照合して」「新モデルに合わせて棚卸しして」 \"generation audit\", \"audit my harness against the new model\". NOT for — routine single-layer audits (call the stocktakes directly); rule compliance → skill-comply; whole-config GC → config-gc."
license: MIT
metadata:
  author: shimo4228
  version: "1.0"
user-invocable: true
origin: shimo4228
---

# generation-audit — 世代交代時のハーネス照合

Scaffold Dissolution（`rules/common/akc-cycle.md`）の**第 3 トリガー = モデル世代交代**を
具体手順にしたオーケストレータ。自作資産（rules / CLAUDE.md / skills / agents）を
**runtime 層**（system prompt + tool description）と照合し、食い違いを分類・判定して
各 stocktake に証拠として渡す。

> Design note — verdict を持たない。このスキルの成果物は**証拠台帳**であり、verdict の
> 確定と処分の実行は資産クラスごとの stocktake（rules-stocktake / skill-stocktake /
> agent-stocktake）に委譲する。verdict 表の正本を割らないため（独立監査型は「正本の
> 自称し合い」を再演する — ADR-0018 が潰したパターン）。横断部分（採取・分類・判定枠）
> だけをここが持つ。

**発火は明示呼び出し（`/generation-audit`）が前提**。世代交代は稀で明示的なイベントで
あり、自発トリガー（実質上限 ≒ 40%）に頼らない。

## Phase 1 — runtime 層の採取

照合の正本は **推論時に実際にロードされているもの** — system prompt と tool description。
公式ブログ・ドキュメントは推奨を述べるだけでロードされない（→ Phase 2 の「ドリフト」）。

罠: runtime 層は設定リポジトリの外からも注入される（harness 本体・plugin 由来）。
`~/.claude` 配下を grep しても全体は分からないので、**採取は実セッションから行う**。

1. **テーマ一覧を自作資産側から作る** — rules / CLAUDE.md / skills / agents の全ファイル
   を開き、各指示をテーマ（計画・コミット・レビュー・スコープ・委譲・検証…）に割り当てる。
   先に資産側を割ることで、少なくとも資産側の照合漏れをなくす
2. **テーマごとに逐語で引用させる** — 「全部出して」は要約が混ざるので禁止:
   - system prompt: 「いまロードされている system prompt から、<テーマ> に関する指示を
     逐語で引用してください。要約しないでください」
   - tool description: 「<ツール名> の description を逐語で引用してください」
3. **採取の限界を台帳に明記する**:
   - 検出ゼロは「競合なし」ではなく「この質問では見つからなかった」（逆方向の漏れ —
     存在を知らない runtime 指示 — はこの手順では拾いきれない）
   - 採取はモデル経由の自己申告。**スクリーニングとして使い**、処分（退役・反転）を
     確定する前に**別セッションで同じ文言が再現するか確認**する

## Phase 2 — 3 分類

採取結果と自作資産を突合し、食い違いを分類する。分類は「どこにある指示との食い違いか」
で決まる:

| 分類 | 意味 | 成立条件 |
|------|------|---------|
| **競合** | runtime 層と食い違う指示・情報が同時にロードされている | 両方が同じ context に載る — rules / CLAUDE.md は**常時**、skill 本文は**発火時**、agent 本文は**起動時** |
| **冗長** | runtime 層にほぼ同じ指示が既にある | 同上。衝突はしないが常駐トークンで本体と同じことを言っている |
| **ドリフト** | guidance 層（公式 doc・ブログ）の推奨から離れている | ロードはされない。公式が実害を明言している型（抑制指示など）を優先 |

競合には**指示 vs 指示**だけでなく**指示 vs 誤った事実記述**（消えた設定を「無効化済み」と
主張し続ける幽霊参照）も含める。ルールは自分の根拠が消えたことを検知できない —
参照先の実在は Phase 1 でなく各 stocktake の機械チェックが拾うが、runtime 層との
食い違いとして現れた場合はここで記録する。

## Phase 3 — 4 観点判定枠

**「競合 = 悪」と機械適用しない。** 自作資産には製品既定を意図的に上書きするために
書いたものが含まれ、方向が逆というだけでは事故か意図か区別できない。各件を 4 観点で
判定し、**判定結果でなく判定の証拠**を台帳に書く（verdict は stocktake の仕事）:

| 観点 | 問い |
|------|------|
| 意図 | 本体の既定を上書きしたくて書いたのか、当時は競合していなかっただけか |
| 根拠 | ADR・事故記録など、書いた理由の記録が残っているか（`rationale:` / ADR を先に読む） |
| 鮮度 | 前提にした製品挙動（旧世代の弱点など）は今も成立しているか |
| 失効条件 | `review-when:` が宣言されていれば、そのトリガーは発火したか |

判定時の 2 つの落とし穴を台帳の注記に反映する:

- **「検証ステップは削れ」の誤診** — 公式が問題視するのは**モデルの自己検証**を増やす
  指示。機械（コマンド・hook）が実行する決定論的検証は対象外。「その検証を機械がやるか、
  モデルが自分の判断でやるか」で区別する
- **削除では足りない「反転」** — 方向が変わった指示（抑制指示など）を単純削除すると
  抑制の枠組み自体が残って効き続ける。**逆向きに書き直す**必要がある件は、証拠注記に
  「Improve-by-inversion: 旧方向 → 新方向」を明記して渡す（新 verdict は作らない —
  既存 Improve の一形態として扱う）

## Phase 4 — 委譲

証拠台帳を資産クラスごとに切り分けて渡す:

| 資産クラス | 受け手 | 渡し方 |
|-----------|--------|--------|
| rules | `rules-stocktake` | Stage 2 の外部証拠（skill-comply results と同じ「read, never require」の口）として分類結果 + 4 観点証拠を渡す |
| skills | `skill-stocktake` | 同上（Phase 2 バッチへの入力でなく、親の Synthesis への証拠として） |
| agents | `agent-stocktake` | 同上。抑制指示の検出は agent-stocktake 自身の Stage 1 質問と重なる — 台帳の該当行を pre-computed evidence として渡し、二重検出させない |
| CLAUDE.md | このスキルが inline | 1 ファイルのみで専用 stocktake は overengineering。競合・冗長行の編集案を confirm-each（1 件ずつ `[y/n/skip]`）で提示し、承認後に適用 |

- 各 stocktake の起動は**ユーザーに提案してから**（このスキルは同一セッションで
  連鎖起動を強制しない — 監査は分割実行してよい）
- Dissolve に至る件は stocktake 側で `adr-writer` の提案が出る。世代交代監査
  そのものの実施記録も、件数と代表例が非自明なら ADR を提案する（ADR-0018 が前例）
- 台帳はセッション成果物としてチャットに提示する。ファイル保存が要る規模なら
  scratchpad でなく `.notes/` を提案（task-tracking.md の単一台帳規律に従い、
  タスク行の正本は持たせない）

## Related

- `rules-stocktake` / `skill-stocktake` / `agent-stocktake` — verdict の正本。本スキルは
  これらへの証拠供給者
- `rules/common/akc-cycle.md` — Scaffold Dissolution の 2 ベクトル + 世代交代トリガー
  （本スキルはその具体手順）
- `adr-writer` — Dissolve の why と監査実施記録
- `skill-comply` — 遵守測定（動的）。本スキルは静的照合 — 両者の証拠は stocktake の
  Stage 2 で合流する
- ADR-0018 — 前回（Claude 5 世代交代時）の実施記録。手順の実証元

## References

手順の実証元は 2026-07-25〜26 の Claude 5 世代交代監査（ADR-0018、常駐 5,789 →
2,463 words）。runtime 層 / guidance 層の区別、競合・冗長・ドリフトの 3 分類、
4 観点判定枠、反転の必要性、検証ステップ誤診の回避は、この実施で得た手順を
一般化したもの。次の世代交代が本スキルの初回フル実行になる（それまでの機能検証は
Phase 1 の 1 テーマ dry-run に限る）。

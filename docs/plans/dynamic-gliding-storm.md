# ヒューマンゲートの層を rule として立てる

## Context

このハーネスの持ち主は **実装コードの diff を逐一読まない**。artifact 層の検証（成果物が正しいか）は
lint / hook / review agent / テストに降ろす方針で、手厚いレビュー体制はそのための投資である。
人間のゲートはもう一段上 — **何を志向し、結果として何がどう変わるか** に置かれる。

### 調査で判明したこと

**思想層は一貫している。** `coding-style.md:34-35` の判定 3 問（「品質を機械検証できるか」が Yes なら
人間を呼ばない）、`patterns.md:18-21` の enumerate/decide seam、`ADR-0010:65`、`ADR-0016:49` が同じ方向を向く。

**第 2 介入点の正本が 2 つあり、別の層を指している** — これが最大の問題:

| 正本 | 記述 |
|---|---|
| `rules/common/planning.md:82` | 「**Verify 結果確認** — コミット直前」（対象が未規定） |
| `skills/implementation-chain/SKILL.md:122` | 「公開・deposit・commit 直前の **diff 承認**」 |

乖離の起点は `ADR-0009:24` の「コミット前に最終チェックを私がするだけ」という対象未規定の一文。
ADR は歴史記録なので書き換えず、live な doc 側を正す。

**病因は「第 2 軸に正本がないこと」。** ハーネスが名前を与えているゲートの軸は
可逆性（`coding-style.md` Reversibility Gate = **いつ**止まるか）だけで、
層（止まったとき人間は**何を**判断するか）には正本がない。だから各実装が自分の解釈で埋めた。

### 論文との衝突と、その解決（計画の中核）

`Harness Alignment and Harness Drift`（DOI 10.5281/zenodo.20578272）§2.1(b) はゲートをこう定義する:

> the proposing system produces **a diff or proposal** and stops, and the operator **reviews**, edits if needed, and commits

§6.2 は gate complacency への構造的防御として「a diff reviewed, possibly edited, and committed under the
operator's name — structurally heavier than a yes/no click」を挙げる。**「意図の要約のみ」は公開済み定義と衝突する。**

さらに、意図の要約は**提案した当人が書いた自己申告**であり、`ADR-0005` の generator–verifier gap が
artifact 層から語りの層へ移動するだけになりうる（脚注 4: intent has no verifier outside the operator,
*even, and especially, when the agent's guess is plausible*）。

**解決 — 対象で分ける。** 論文 §5 のゲートは元々 **behavior-shaping write に限定**されている
（episode log / knowledge store は承認不要、rule / skill / identity は sign-off 必須）。
そして **rule / skill / identity の diff は「実装の差分」ではなく「意図そのものの本文」**である。
それを読むのは artifact 検査ではなく **intent 層の作業**。よって論文を改訂せずに矛盾が解ける。

**意図する結果**: 第 2 軸に正本ができ、ゲートで人間に届くものが対象によって正しく分岐する。
ゲートのタイミング（2 介入点）は変えない。

### 語彙の状態（新語を作らない根拠）

| 語 | 状態 |
|---|---|
| **harness alignment** | AKC `ADR-0017:41` で定義済み。paper 題名、**DOI 10.5281/zenodo.20578272**、lineage 監査済み |
| **value-layer harness engineering** | 2026-07-03 に hub の through-line として確立（concept page / vocab / graph / index.html の 4 面） |
| **line of approval** | AKC `glossary.md:46-57`。軸は*アーティファクト種別*で、層軸とは直交。今回の分岐はこの 2 軸の交点 |
| intent の非自動化論証 | AKC `glossary.md:186-195` / 論文 §3。今回の原則の理論的裏付け |
| artifact / intent の区別 | AKC `ADR-0016:65` が **Measure 計器**に命名済み。**ゲートに適用する記述は空席** |

`ADR-0017:41,106` は "value" を AI-safety value-alignment との誤読リスクとして明示排除しているため、
rule 本文では "value" を主語にせず harness alignment 側の語彙に寄せる。

## 決定事項（インタビューで確定）

1. **新規 rule を `rules/common/human-gate.md` に立てる**
2. **新語は coin しない。既存語に anchor**（`ADR-0010` Vocabulary Discipline: Coin Sparingly, Anchor Densely）
3. **ゲートは対象で分岐する** — behavior-shaping artifact は本文を読む / 実装は意図の要約
4. **作業範囲は rules まで。** AKC への昇格は別作業（台帳に 1 行引き継ぐ）

## 変更内容

### A. `rules/common/human-gate.md` を新設（目安 200 words 以内）

- **2 軸を明示** — 可逆性（いつ止まるか → `coding-style.md` Reversibility Gate へポインタ）×
  層（何を判断するか = 本ファイル）
- **artifact 層 → 機械。** 成果物の正しさは lint / hook / テストが持つ。人間は積極的に降ろす
- **留保** — review agent は LLM judge であり **generator–verifier gap** を持つ（AKC `ADR-0005:86-90`）。
  **検査は担えるが承認は担えない**。承認は「決定論ゲートの PASS」＋「人間の intent 判断」で構成し、
  LLM 単独の承認経路を作らない
- **ゲートの 2 区分**:
  - **behavior-shaping artifact**（rules / skills / identity / 憲法 / 公開ドキュメント）→ **本文を読む**。
    テキストが意図そのものなので、読むこと自体が intent 層の作業
  - **実装コード・設定・生成物** → **意図の要約**。「何を志向し、結果として何がどう変わるか」。
    diff 本文・検査結果の一覧は提示しない
- **自己申告への対処** — 意図の要約は**介入点 1 で人間が承認した plan と照合**する。
  自由記述として読まない（照合先を人間由来の referent に固定し、自己申告の検証にしない）
- **anchor** — harness alignment（AKC ADR-0017 / DOI 10.5281/zenodo.20578272）、
  line of approval（AKC glossary）へのリンクのみ。定義本文は複製しない

### B. `rules/common/planning.md` — 第 2 介入点の再定義（正本の確定）

L77-82 の介入点 2 を「**意図確認**」に改名し、A の 2 区分に従って何が提示されるかを明示。
L87-101 の Verify ステップに、8 項目が機械/エージェントの担当であり人間に上がるのは FAIL のみである旨を 1 行。
`human-gate.md` へポインタ。

### C. `skills/implementation-chain/SKILL.md:122` — 一律削除ではなく**対象で分岐**

「公開・deposit・commit 直前の diff 承認」は、**rule / skill を書き換える chain では正しい**。
実装コードの chain で層を取り違えている。A の 2 区分に沿って条件を書き分ける。

### D. 残滓（再評価の結果、3 箇所に減った）

| ファイル | 再評価 | 方針 |
|---|---|---|
| `skills/release-doi/SKILL.md:298-300` | **残滓** — HF commit 時刻の前後比較は完全に機械判定可能 | `patterns.md:23-26` に従い、同 doc 内で 1 行のコマンド照合に置き換える |
| `skills/paper-deposit/SKILL.md:228` | **残滓** — 「eyeballed」はフォント描画の検査 | 機械チェック可能な部分（フォント埋め込みの有無）と著者が意図として引き受ける部分に分離 |
| `skills/readme-writer/SKILL.md:177-179` | **部分的に正当** — README は公開・不可逆だが、直前に readme_lint + readme-reviewer が済んでいる | ゲートの理由を「artifact 検査」から「公開判断」に書き換える（削除しない） |
| `skills/harness-sync/SKILL.md:46` | **残滓ではない** — 対象が skills/rules（behavior-shaping artifact）かつ外部公開 | **変更しない。** なぜ diff を読むのかの理由を 1 行添えるに留める |

### E. 混在記述 2 箇所

- `rules/common/coding-style.md:31` — 「payload や**差分**を提示し」。L32 の「件数とスコープを明示」と
  整合させ、A の 2 区分へポインタ
- `skills/public-comment/SKILL.md:62-64` — 「全文を読んで承認」は文言上 artifact だが、
  日本語訳併記の理由が「ニュアンスを確認」＝ intent 判断。文言を実質に合わせる

### F. `rules/common/debugging.md:8-10`

「証拠 — 具体的なコード行を示す」は**エージェント側の規律として残す**（根拠なき修正を防ぐため）。
人間に求めているのは「その原因究明の方向で進めてよいか」であり、提示コード行の検査ではない旨を明記。

### G. 付随

- `rules/README.md` のツリーに 1 行追加（14 → 15 ファイル）、語数の記述を更新
- `docs/adr/0019-*.md` — なぜ rightsize 直後に rule を 1 本増やすのか、および
  **論文 §2.1(b) との整合をどう取ったか**を記録（将来の読者が必ず問う点）
- `.notes/TASKS.md` に AKC 昇格タスクを 1 行

## 対象外（発見したが今回は触らない）

- **AKC への concept/ADR 昇格** — 別作業。AKC `.notes/TASKS.md:11` T3 が
  「**対称性論証では ADR を立てない**（観測事例が n を満たすまで再提起しない）」という証拠基準を課しており、
  運用実績の蓄積が先
- **hub と AKC の "value" 語の不整合** — hub は `value-layer harness engineering` を使うが、
  AKC `ADR-0017:41,106` は "value" を明示排除。発見事項として記録のみ
- `coding-style.md:32`（承認は batch 化で償却されない）と `ADR-0010:39`（batch confirmation 許容）の矛盾
- `metrics/costs.jsonl` の孤児化（読み手 0 件、最終更新 2026-03-09）、
  `skills/skill-health/results.json` が規定されているのに存在しない件
- 評価の起動自動化（測定を無言で回して乖離だけを上げる機構）

## 検証

1. `python3 ~/.claude/scripts/hooks/harness_lint.py` — doc リンク / See-skill ポインタの整合
2. **層の一致確認** — `planning.md` の第 2 介入点と `implementation-chain/SKILL.md:122` が
   同一の語・同一の 2 区分を指すこと（正本 2 本の食い違いの解消）
3. **論文との整合** — `human-gate.md` の記述が論文 §2.1(b) / §5 / §6.2 と矛盾しないことを、
   3 節それぞれと突き合わせて確認（behavior-shaping write でのゲートが弱まっていないこと）
4. 残存チェック — `grep -rn "目視\|eyeballed" ~/.claude/skills` が 0 件
5. **常駐コスト** — `wc -w rules/common/*.md` で ADR-0018 時点の 2,314 words からの増分を報告
   （目標 +200 words 以内。超えたら本文を削る）
6. `git status` / `git diff` — 新規ファイルが `human-gate.md` と ADR-0019 の 2 本のみで、
   ゲートのタイミング・手順・機構が変わっていないこと

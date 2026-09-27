# AKC 蓄積効果測定器 — NullHarness 反実仮想 × prefix 長プローブ

## Context

今朝の daily-research ノート（`2026-08-04_akc_temporal-memory-contamination-...`）が、AKC の frontier question
「skill/rule 蓄積の効果測定」への具体的計器として、arXiv:2605.17830 の **NullMemory 反実仮想 + prefix 長
read-only スナップショットプローブ** の転用を提案した。目的は 2 つ:

1. **計器を作る** — AKC が「Measure できる」と言い続けてきた蓄積効果に、初めて数字を出す
2. **doctrine を試す** — 書き込み単位の human-approval-gate（ADR-0005）が原理的に見えない失敗モードが
   自分のハーネスにも存在するか、実測で確かめる（存在しなければそれも記録に値する結果）

実装は harness 側（`~/.claude`）。AKC repo には **stage 1 では何も書かない**（理由は §3）。

---

## 1. 一次確認の結果（プラン作成中に実施済み）

`arxiv.org/abs/2605.17830` と `arxiv.org/html/2605.17830` を fetch。ノートの中核はすべて裏取りできた。
**数値・手順は以下が一次確認済みの実体**（ノートの二次要約ではなくこちらを実装の根拠にする）:

| 項目 | 一次確認した実体 |
|---|---|
| 著者 | Al-Tawaha, Gu, Niu, Jia, Jin |
| 事象構造 | 前提条件 P_a（取得文脈に汚染情報）→ トリガー（ℓ でのプローブ）→ 違反 U_a。`U_a=1 ⟹ P_a=1` |
| NullMemory | 同一ベースモデル・同一デコードパラメータで `y_mem`（retrieval あり）と `y_∅`（retrieval 空）を生成 |
| ラベル条件（3 つ **すべて**） | ①judge が `y_mem` を unsafe、②対応する null run が safe、③不安全内容が取得記憶に **span-matching で意味的に遡れる** |
| プローブ集合 | `T_base`（無害クエリ、ベースレート）と `T_hard`（pilot 由来の違反誘発、**チェックポイントあたり \|T\|=40**）の 2 種 |
| スナップショット | 先頭 ℓ 件のみから構築、プローブは **書き戻さない**。synthetic は 200 相互作用刻み |
| 指標 | `q_a(ℓ) = E_{x~Unif(T)}[U_a(x,ℓ)]`。**trigger-conditional であって deployment prevalence ではない** |
| judge | Claude Sonnet 3.5。855 ペアで人間と ~91% 一致。**recall 0.95–1.00 / precision 0.50–0.69 → q_a は上限値** |
| 結果 | synthetic で 0.3–0.5、ST は 0.1–0.2 で平坦。Claw 系は 7 構成すべてで ℓ 単調増、Haiku 最急・Opus 最緩。**検出率はゼロ** |
| 順序 ablation | ブロック shuffle(B=50) でも全 shuffle(B=1) でも上昇傾向は残る。ただし MemTree は全 shuffle で大きく低下 → **順序は二次的な調整因子** |
| 緩和策 | 取得フィルタ / メモリ分離 / アクセス制御（すべて **取得時・生成時**）。retrieval-time monitor は recall 0.970–0.984 |

**ノートとの差分 1 点**: ノートは順序 ablation を「効果は蓄積量に駆動される」と単純化しているが、
一次は「蓄積量が主、順序は二次的な modulator（構造依存のアーキテクチャでは順序も効く）」。
本計器の設計では **順序 ablation を落とさない**（§2.4）。

**残タスク（stage 1 の頭で 15 分）**: 医療 13 storyline / Enron 1,867 通など scale の細部と Algorithm 1 の
擬似コードを PDF で確認。実装の可否は変えないが、比較を書くときの分母 qualification に要る。

---

## 2. AKC 文脈への翻訳

### 2.1 何が「蓄積」か

論文の蓄積 = ユーザー相互作用の追記ストリーム。AKC/harness の蓄積 = **`~/.claude` の
skills / rules / agents / memory**。git 履歴は 293 commit・2026-02-26 〜 2026-08-04（約 5.5 か月）ある。

**ただし重大な非対称**（ここを外すと計器が嘘をつく）:

> 論文のストリームは append-only で単調増加。harness の蓄積は **curate されている** —
> 2026-07-25 の generation review で rules 層は 43,971 → 19,240 字に縮んだ（ADR-0023）。
> git 履歴を素朴に prefix として使うと、測るのは exposure length ではなく **「ハーネスのバージョン」** になる。

### 2.2 prefix の作り方（2 系統・両方走らせる）

- **A: 合成蓄積ラダー（主系統）** — 現在の skills/rules corpus から、**入れ子の部分集合** L_1 ⊂ L_2 ⊂ … ⊂ L_full を
  作る。順序は「初出コミット日時」（= 実際の蓄積順の再構成）。これで内容を現行版に固定したまま **量だけ** 動かせる。
  ℓ は「常駐文字数」と「skill 個数」の 2 通りで記録する。
- **B: 履歴 prefix（対照系統）** — git worktree で過去コミットのハーネスを復元。A のような統制は効かないが、
  「実際に起きた蓄積」での再現性を見る。A と B が食い違ったら、それ自体が curation の効果の証拠。

スナップショットは **read-only**：worktree に checkout → プローブ実行 → 破棄。プローブは書き戻さない
（memory への書き込みも hook も止める。§4 の `--bare` / `permissions.deny` を使う）。

### 2.3 NullHarness 対照条件

論文の `r_∅ = ∅` に対応するのは **rules/skills/memory を一切ロードしない素のセッション**。
実装レバーは調査済み:

- `skill-comply` の runner は `subprocess.run(..., cwd=sandbox)` で **env を継承する** →
  `CLAUDE_CONFIG_DIR` を差し替えれば子セッションのハーネスを丸ごと入れ替えられる（**要 step 0 実証**）
- 補助レバー: `claude --bare`（CLAUDE.md 自動探索 / auto-memory / hooks を skip）、`--setting-sources`、
  `--settings` の `permissions.deny`（`child_settings.py` に既存）

同一モデル・同一プロンプト・同一 sandbox で `y_ℓ` と `y_∅` をペア生成する（論文の同一デコード条件に対応）。

### 2.4 outcome 指標

論文の「安全違反」はそのままでは AKC に来ない。AKC の蓄積が壊すのは safety ではなく
**無関係な文脈への constraint の漏れ出し**。2 指標を分けて取る:

**(a) cross-context misfire rate `q(ℓ)`** — 判定は論文の 3 条件を移植:
1. ℓ-run が、プローブの領域と無関係な skill/rule 由来の制約を持ち込んだ（判定は LLM judge + rubric）
2. 対応する **null run はそれをしていない**
3. 持ち込まれた内容が ℓ スナップショット内の **特定ファイルに遡れる**（skill 名・rule 見出しの span match）

**(b) reconciliation overhead** — ℓ-run と null-run の **ターン数・出力トークン・skill 起動回数の差分**。
judge を通さない決定論的指標。これは狙って取りに行く価値がある: **ADR-0023 が「metric がない」と
明示的に open にした conflict cost** に、初めて数字が付く候補だから。

judge バイアス対策（論文が precision 0.50–0.69 を自認しているので必須）: 全ペアの **最低 20%
を著者が手で裁定** し、一致率を報告に載せる。一致率が低ければ `q(ℓ)` は上限値としてのみ扱う。

### 2.5 ablation（論文から必ず持ってくる）

順序シャッフル: 同じ ℓ で「初出順」と「ランダム順」の 2 通りの部分集合を作り、傾向が残るか見る。
残れば量が効いている、消えれば順序（＝ curation の構造）が効いている。**どちらの結果も情報がある**。

---

## 3. 実装の形と置き場所

### 結論: **AKC repo には置かない。harness 側の使い捨て probe から始める。**

repo 内調査で判明した拘束（推測ではなく明文）:

- **ADR-0016**「No reference instrument in AKC」— AKC は Measure 計器の *要件* を述べ、計器は出荷しない
- **ADR-0022** は「EvoAgentBench 型の transfer 計器を AKC に組み込む」案を **明示的に却下**
- CLAUDE.md の mechanism-only rule — 具体 instance は `examples/` 限定

→ AKC `examples/` に置く案もあるが、`examples/minimal_harness` は依存ゼロ・ネットワークなしの
~500 行 reference という性格で、`claude -p` を回す測定器はそこに馴染まない。**stage 1 では AKC を触らない。**

置き場所（stage 1）:

```
~/.claude/skills/skill-comply/experiments/accumulation-dose/   # 新規、gitignore はしない
  snapshot.py     # 蓄積ラダー生成（A: 部分集合 / B: git worktree）→ CLAUDE_CONFIG_DIR 用ディレクトリ
  probes.yaml     # 固定プローブ集合（T_base / T_hard の 2 種、手書き）
  runrun.py       # 各 (probe, ℓ, arm) を skill-comply の runner で実行しトレース保存
  judge.py        # 3 条件ラベリング（classifier.py の呼び出しパターンを踏襲、rubric は新規）
  analyze.py      # q(ℓ) 曲線 + overhead 差分 + 手裁定サンプルの一致率
  RESULTS.md      # 生の数字と手裁定ログ
```

再利用する既存資産（新規に書かない）:
`scripts/runner.py`（sandbox 生成・`claude -p`・stream-json パース）、`scripts/child_settings.py`
（`permissions.deny` による封じ込め — Bash/Agent/Workflow/ToolSearch/ScheduleWakeup）、
`scripts/parser.py`、`scripts/classifier.py` の LLM 呼び出し形。

**昇格パス**（stage 1 の結果が生きていたら）: 独立 repo 化 → AKC には ADR + graph binding だけを入れる。
これは既に確立した経路（`claude-skill-comply` / `agent-stocktake` / `human-gate` / `generation-audit` と同型）。

---

## 4. doctrine への含意 — 判断分岐点

**stage 1 では ADR も graph も一切書き換えない。** 以下は「どの結果が出たらどの改訂候補が立つか」の
事前登録（結果を見てから物語を作らないため）。

| 観測 | doctrine 上の意味 | 起こすアクション（別途・人間承認） |
|---|---|---|
| `q(ℓ)` が ℓ に対し単調増、手裁定一致率も十分 | 良性蓄積だけで無関係文脈への漏れが増える現象が **自分のハーネスで再現**。ADR-0005 の書き込み単位ゲートが原理的に見えない領域が実在 | ADR 新規候補: **retrieval/セッション時点の第二チェックポイント**。ADR-0005 に addendum（ゲートの適用範囲 = 個々の diff、非適用範囲 = 蓄積総量）。ADR-0015 の「ground 層は守れば安全」の切り分けに反例として addendum |
| overhead 差分だけが増え misfire は増えない | ADR-0023 の **conflict cost に初めてローカル計器が付いた**（0023 は「metric がない」と自認）。ADR-0005 への挑戦は成立しない | ADR-0023 に「local instrument が構成可能」の addendum + generation review の enumerate 半分の自動化 |
| どちらも平坦（null 結果） | curation（Curate 相 + gate）が蓄積劣化を実際に抑えている **積極的な証拠**。論文の結果は curate されないメモリに固有 | ADR は立てない（証拠基準: n=1 の対称性論証で ADR を立てない — 2026-06-06 の ADR-0016 取り下げの教訓）。RESULTS.md に負の結果として保存し、ADR-0022 の「reference construction が無い」open question への部分回答として保持 |
| A（合成ラダー）と B（履歴 prefix）が食い違う | curation が交絡ではなく **効果そのもの**。AKC の主張（cycle は decay を防ぐ）に対する直接の測定 | ADR-0022/0023 の evidence class 群に「dose」軸を足す提案の種 |

**先に決めておく分岐点**: 手裁定一致率が 70% を切ったら `q(ℓ)` は上限値としてのみ報告し、
doctrine 改訂の根拠には使わない（overhead 指標のみ使う）。

---

## 5. 見積りと最小実験

### Stage 1 — プロトタイプ（3〜4 時間、API コストは中規模の 1 セッション相当）

| # | 内容 | 目安 |
|---|---|---|
| 0 | **feasibility 実証**: `CLAUDE_CONFIG_DIR` を差し替えた `claude -p` が実際に別ハーネスをロードするか、1 プローブで確認。**ここが通らなければ全体を再設計**（代替: `--bare` + `--add-dir` で明示注入） | 20 分 |
| 1 | プローブ集合を手書き: **8 本**（うち T_hard 相当 5 本 = 蓄積した skill/rule の領域と無関係だが表層語彙が近いタスク、T_base 3 本） | 40 分 |
| 2 | 蓄積ラダー A を 3 段: `ℓ=0`(=NullHarness) / `ℓ≈1/3` / `ℓ=full` | 30 分 |
| 3 | 実行: 8 probes × 3 arms = **24 run**（並列 3 で 30〜45 分） | 45 分 |
| 4 | judge rubric + ラベリング + **著者が 6 ペアを手裁定** | 60 分 |
| 5 | `q(ℓ)` と overhead 差分を RESULTS.md に。傾向の有無だけを見る（有意性は主張しない） | 30 分 |

**stage 1 が答える問い**: 「傾向があるか、計器が動くか」だけ。効果量は主張しない。

### Stage 2 — 拡張（stage 1 で傾向が見えた場合のみ）

- プローブを 40 本へ（論文の `|T|=40` に合わせる）、ℓ を 5〜6 段へ
- 順序シャッフル ablation（§2.5）と履歴 prefix 系統 B を追加
- 各セルを 3 反復してばらつきを出す（stage 1 は 1 反復なので分散が見えない）
- 独立 repo 化 + AKC への ADR 昇格判断（人間承認）

---

## 検証（stage 1 の完了条件）

1. `python snapshot.py --level 0` が空ハーネスの config dir を作り、`claude -p` がそこで
   **rules を 1 つもロードしていない**ことをトレースで確認できる（step 0 の実証と同じ手段）
2. 24 run すべてトレースが保存され、null-run とペアが 1:1 で対応している
3. judge のラベルと著者の手裁定 6 件の一致数が RESULTS.md に書かれている
4. `q(ℓ)` 曲線と overhead 差分が 3 点そろって出力される
5. `git -C ~/.claude status` が experiments/ 以外に差分を出していない（プローブが書き戻していない証拠）
6. AKC repo は `git status` clean（stage 1 は AKC を触らない）

## 非目標（stage 1 で **やらない**こと）

- AKC の ADR / graph.jsonld / README の変更
- 統計的有意性の主張、論文との数値比較
- 恒久 instrument 化・独立 repo 化
- wiki への書き込み

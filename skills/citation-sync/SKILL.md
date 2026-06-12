---
name: citation-sync
description: "研究 repo の引用 4 層 (docs 実引用 → .zenodo.json references → graph.jsonld ExternalReference → Wikidata P2860) を監査し、下層から順に同期する orchestrator。Use when the user says 「参考文献が少ない/足りない」「引用がずれてる」「citation を同期して」「引用文献を Wikidata/graph に反映して」, when new external papers were cited in ADR/glossary/empirical docs, before a release of a DOI-registered repo, or when a repo's Wikidata item shows fewer cited works than its docs. 単層の実装は release-doi (.zenodo.json) / jsonld-knowledge-graph (graph) / wikidata-federation (Wikidata) に defer し、本 skill は層間の divergence 検出・curation 基準・同期順序だけを持つ。NOT for: 論文 (paper item) 自体の reference list 整備 (paper-deposit / wikidata-federation が担当)、引用を含まない repo。"
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
user-invocable: true
origin: shimo4228
---

# Citation Sync

研究 repo が外部文献を引用するとき、その引用は 4 つの層に現れる。層はそれぞれ別の audience に向けて伝播するため、**どれか 1 つに書いて終えると残りの層では引用が存在しないことになる**。本 skill はこの 4 層の divergence を検出し、下層から順に揃える。

| 層 | 担体 | 伝播先 | 実装 skill |
|---|---|---|---|
| 1. docs | ADR / glossary / empirical / README 内の引用 | 人間 + LLM crawler | (執筆時に発生) |
| 2. zenodo | `.zenodo.json` `related_identifiers` (`relation: references`) | DataCite → OpenAIRE / Scholix (次 release 時) | `release-doi` |
| 3. graph | `graph.jsonld` の `ExternalReference` ノード | LLM ingest / HF mirror / knowledge-graph crawler | `jsonld-knowledge-graph` |
| 4. wikidata | repo item の P2860 (cites work) | Scholia / CC0 dump / 被引用研究者の citation 面 | `wikidata-federation` Phase 4.5 |

**docs 層が source of truth**。上の層は docs に実在する引用だけを carry する (捏造辺の禁止)。逆に docs に引用を足したら、上 3 層への反映はこの skill の同期で行う — 「repo markdown に引用を書くだけでは citation graph に不可視」というのが authorship-strategy の citation-graph federation tactic の出発点。

## Phase 0: Audit (read-only)

```bash
python3 ~/.claude/skills/citation-sync/scripts/citation_audit.py REPO_DIR [REPO_DIR ...]
#   --skip-wikidata   Wikidata 層を省略 (offline / 高速)
#   --json OUT.json   機械可読の結果も保存
# exit 0 = 全 repo converged, 1 = divergence あり, 2 = fatal
```

repo ごとに identifier × 層のマトリクスを出す。Wikidata 層は graph self-node の sameAs から repo QID を自動発見し、P2860 先の P818/P356 を解決して identifier 比較する。

**先に audit、議論はそれから。** どの層が欠けているかを推測で語らない — 今日の層別カバレッジは repo ごとに本当にバラバラで、直感は外れる (実例: ある repo は zenodo refs が空、別の repo は graph と zenodo が互いに素の集合を指していた)。

## Phase 1: Curate (判断層)

audit が出した docs 層の identifier を、repo の公式引用に昇格させるか判定する。機械抽出は過剰検出を含むので、**この phase だけは人間判断 (または明示基準の適用) が必要**:

- **公開 docs のみ**: `.notes/` (paper 草稿・scratch) は repo の引用ではない。paper 草稿の references は paper item 側の federation が担当する (二重計上しない)
- **引用文脈であること**: 文献として参照している言及だけを採る。例の中の ID、CHANGELOG の作業記録、tool 出力の貼り付けは引用ではない
- **external のみ**: sibling repo の Zenodo DOI は ecosystem cross-link であって external citation ではない (audit が別枠で報告する)
- **識別子と内容の一致を検証する**: 昇格前に arXiv API / Crossref でタイトルを引き、docs の引用文脈と照合する。LLM が書いた引用 link の arXiv ID は hallucination しうる (実例: 「GlassWorm」への引用が無関係な Novel View Synthesis 論文の ID を指していた — 正しい出典は arXiv ではなくベンダーのセキュリティレポートだった)。不一致なら昇格せず、docs 側の引用を正す
- 迷う識別子は出現箇所を `grep -rn` で開いて文脈を見る。昇格させない判断も記録する (次回 audit で同じ識別子を再審査しない)

## Phase 2: Sync `.zenodo.json` (層 2)

curate 済みの引用を `related_identifiers` に追加する。entry 形式・arXiv の DataCite DOI 形 (`10.48550/arXiv.NNNN.NNNNN`)・重複排除は **`release-doi` skill の citation surface 同期 section が正本**。注意: `.zenodo.json` は **次の release 時に** DataCite metadata として propagate する (commit しただけでは外に出ない — それでも commit しておくのが正しい。release 時に自動で乗る)。

## Phase 3: Sync `graph.jsonld` (層 3)

curate 済みの引用を `ExternalReference` ノードとして graph に追加する。ノード形状 (@id = arXiv abs URL / @type / identifier / datePublished) は **`jsonld-knowledge-graph` skill が正本**。description には「なぜこの repo がこれを引くか」を 1-3 文で書く — anchor-densely (vocabulary discipline) の実践であり、LLM ingest 時に引用関係の意味が残る。push 後は HF mirror (`hf-sync`) も同期する。

## Phase 4: Federate to Wikidata (層 4)

**`wikidata-federation` skill の Phase 4.5 が正本**。手順の要点だけ:

1. cited work の重複チェック (P818 / P356 / label) → 不在なら bibliographic skeleton 作成
2. repo item に P2860 辺 (software / dataset でも constraint-clean — 検証済み)、reference は repo の DOI resolver URL
3. graph の ExternalReference ノードに sameAs QID 注入 (`add_qid_sameas.py`)
4. **post-write constraint check 必須**: `federation_lint.py --items @touched_qids.txt`

## Phase 5: Verify

Phase 0 の audit を再実行し、全 repo `CONVERGED` を確認してから完了報告する。divergence が残る場合は、それが意図的 (例: graph には載せるが zenodo は次 release でまとめる) かを明記する。

## Pitfalls

| Pitfall | 回避 |
|---|---|
| 層が時期差で乖離する (graph は今日足したが zenodo は半年前のまま) | 引用を 1 本でも足したらこの skill を通す。release 前は必ず Phase 0 を回す |
| docs の機械抽出を無批判に昇格させる | Phase 1 の curation 基準を適用。`.notes/` 由来と非引用文脈を落とす |
| paper の references を repo 層に混ぜる (またはその逆) | paper item の P2860 は paper の reference list から、repo item の P2860 は repo docs の引用から。担体が違う |
| Wikidata だけ先に膨らませる | 上流 (zenodo / graph) が空のまま Wikidata に辺を張ると、次の audit でまた divergence になる。必ず下層から |
| sibling DOI を external citation として数える | ecosystem cross-link は別枠。audit script が自動で分離する |
| graph に既存の内部 bibliography 規約があるのに新ノードを追加して重複させる | Phase 3 の前に graph 内を被引用文献の名前でも grep する（例: `ans:ref/sharf-2014` が既にあるのに DOI @id の新ノードを足してしまった）。既存ノードがあれば identifier / url / sameAs を**追記**する方が正しい |
| `add_qid_sameas.py` が 1 行ノード形式の graph で JSONDecodeError | text surgery が複数行形式前提。1 行ノードの graph は手動 Edit（または Python 文字列置換 + json 検証）で注入する。失敗時はファイル無傷（書き込み前 validation）|
| docs が識別子無しで引用 (名前のみ) → audit が docs 層欠落として DIVERGED を報告 | 識別子ベース比較の既知の限界。引用が docs に実在するなら**意図的残差**として完了報告に明記すれば良い（docs に ID を書き足す義務はない）|

## Related skills

- `release-doi` — 層 2 の正本。release workflow 内の citation surface 同期
- `jsonld-knowledge-graph` — 層 3 の正本。ExternalReference ノード設計
- `wikidata-federation` — 層 4 の正本。skeleton 作成 / P2860 / sameAs / lint
- `hf-sync` — 層 3 更新後の mirror 反映

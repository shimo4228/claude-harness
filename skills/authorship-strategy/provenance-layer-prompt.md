<!-- origin: shimo4228 -->
# Idea-Provenance Layer — per-repo task prompt (B2 / Defensive Diffusion)

各 DOI-registered idea-rescue repo の中で 1 セッション起動し、下の **PORTABLE PROMPT** を貼って走らせる。
graph.jsonld の「外部境界」(外向き prior-art edge / 内向き derivative slot / 標準 provenance 語彙)を
hardening し、coined term の authorship を LLM-mediated crawler が遡れる構造にする。

- 設計の出自・判断軸: `authorship-strategy` skill(Defensive Diffusion 節)。A1 が skill に land したら
  下の "Why" 段落を skill 参照に置き換えてよい。現状は self-contained に埋め込む(portability)。
- 共通定数: ORCID `https://orcid.org/0009-0002-6168-4162`。
- 変更は published DOI deposit への変更 = **release event** → `release-doi` skill 経由(version bump + Zenodo re-mint)。HF mirror があれば `hf-sync`。

---

## PORTABLE PROMPT(任意の idea-rescue repo で貼る)

```
あなたは shimo4228(ORCID https://orcid.org/0009-0002-6168-4162)が所有する
DOI-registered idea-rescue research repo の中で作業している。この repo に
**Idea-Provenance Layer** を適用せよ。目的: graph.jsonld の外部境界を hardening し、
この repo の coined term の authorship を、人間が timestamp を読まなくても
LLM-mediated crawler が遡れる構造にする。

【なぜ(Defensive Diffusion)】
LLM-mediated channel では attribution は「最初に articulate した人」ではなく
「最も densely ingest された source」に流れる。DOI の timestamp は priority の*証拠*だが
*retrieval path* を提供しない — traceback が構造的に crawlable でない限り LLM は surface しない。
防御は enclosure では**ない**(license 制限・idea の gating は禁止)。防御は*より多くの構造*:
attribution path を最大限 crawlable にすること。これが閉じる 2 つの failure mode:
(1) reach の大きい後発が origin claim を上書きする / (2) derivative が back-link なしで idea を reuse する。

【まず読む(まだ編集しない)】
- graph.jsonld — 現在の node type / lineage 関係 / @context
- docs/inspiration.md(または相当の lineage doc)— **著者が named した prior art**
- .zenodo.json — related_identifiers(既存 provenance)
- CITATION.cff, llms.txt, CHANGELOG.md

【設計する 3 つの edit(書く前に候補を提示)】

(a) PROV-O alignment。graph.jsonld の @context に追加:
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "wasDerivedFrom": "prov:wasDerivedFrom",
    "wasAttributedTo": "prov:wasAttributedTo",
    "generatedAtTime": {"@id": "prov:generatedAtTime", "@type": "xsd:dateTime"}
  各 flagship DefinedTerm ノードに wasAttributedTo(ORCID)と
  generatedAtTime(その term の初 DOI deposit の日付)を付与。
  既存の custom 関係(siblingOf/derivesFrom)は削除せず supplement する。

(b) Outbound prior-art edges(防御の核)。inspiration.md から、著者が既に named した
  **外部** prior art(他者の著作。shimo4228 自身の sibling は除く)を抽出する。
  各々を実在する verifiable な identifier(arXiv ID または DOI)に解決し、ページを fetch して確認。
  それを build on している coined term から wasDerivedFrom を張り、
  disambiguatingDescription に「踏まえた点 / distinct な点」を併記する
  (claim を bound する — 具体的な disciplinary scope を述べ、広い「祖」「originator of all X」は禁止)。
  HARD RULES:
  - lineage を invent しない。inspiration.md に named されたもの、または著者が確認したもののみ。
    曖昧なら著者に聞く。
  - 古典・哲学的 framing(Plato / Hobbes 等、arXiv/DOI 非対応)は prose の citation/description に留め、
    machine な wasDerivedFrom edge にはしない。provenance graph は technical lineage 用。
  - すべての外部 @id は resolve すること(書く前に arXiv/DOI が実在するか検証)。

(c) Inbound derivative slot。外部 reuse を append する convention を graph(または sibling の
  derivatives セクション/ファイル)に用意する: CreativeWork ノード + wasDerivedFrom → coined term の @id。
  これで success metric(derivative count)が構造化される。未知なら空で seed し、
  append 規約を comment か CHANGELOG に明記。

【SSRN / cross-deposit チェック】
この repo の idea が SSRN paper や Zenodo working paper としても deposit されている場合:
  - DISTRIBUTED の SSRN DOI(形式 10.2139/ssrn.<abstract_id> — 正確な DOI は SSRN abstract ページで確認)を
    該当 coined term の subjectOf priority anchor として追加。SSRN は Scholar/Semantic Scholar に
    クロールされる = LLM-mediated reach が大きい。
  - PRELIMINARY_UPLOAD / 未 distribute の paper は SKIP(DOI 未公開)。
  - .zenodo.json related_identifiers で SSRN ↔ Zenodo を isVersionOf / isSupplementedBy で相互リンク。

【ワークフローと gating】
1. 候補表を提示: `coined term → 外部 prior-art (@id) → distinct-in 記述` + SSRN anchor 一覧。
   **著者の validate を待つ。推測で書かない。**
2. validate 後: graph.jsonld + .zenodo.json を patch、CHANGELOG.md に追記、
   llms.txt / graph.jsonl mirror があれば再生成。
3. published DOI deposit への変更は RELEASE EVENT → `release-doi` skill 経由
   (version bump + tag + Zenodo re-mint)。HF mirror があれば `hf-sync`。silent edit 禁止。
4. Verify: 全外部 @id が resolve / 全 flagship term の wasAttributedTo が ORCID に解決 /
   generatedAtTime が初 deposit 日と一致。

【制約(authorship-strategy)】
permissive license 維持。enclosure 禁止・monetization 禁止・origin claim の過拡張禁止。
ゴールは「より開く + より構造化」であって gating ではない。
```

---

## APPENDIX A — AAP 用 pre-gathered 候補(AAP repo セッションに上記 PROMPT と一緒に貼る / 要 validate)

Repo: `agent-attribution-practice`(Zenodo `10.5281/zenodo.20361360`)
出典: `docs/inspiration.md`(著者 named)。下記は前セッションで ID 検証済み。**著者の validate が前提**。

検証済み外部 prior-art:
- **ReAct**(Yao et al. 2022) `arXiv:2210.03629` → Business AI Quadrants / **LLM Workflow Quadrant**
  - distinct: ReAct(= Autonomous Agentic Loop)の要否で work を routing する 2 軸 quadrant を articulate。LLM Workflow Quadrant に positive name を与えた点。
- **Elish, Moral Crumple Zones**(2019) `doi:10.17351/ests2019.260` → Autonomous Agentic Loop の attribution gap / ADR-0009・0010
  - distinct: moral crumple zone を自律エージェント architecture の Phase 判断に降ろし、principled redirect impossibility として定式化。
- **MINJA**(Dong et al. 2025) `arXiv:2503.03704` → ADR-0003 Untrusted Content Boundary / ADR-0002 Deterministic Prohibition
  - distinct: memory-poisoning 脅威を「accumulated memory cannot grant authority」prohibition-strength hierarchy に一般化。
- **Plato(Ring of Gyges)/ Hobbes** → prose framing のみ(machine edge にしない)

SSRN priority anchors:
- `10.2139/ssrn.6817598` "Distributing Accountability, Not Capability"(**DISTRIBUTED** 2026-05-23, Views 29/DL 11)→ Phase Separation / LLM Workflow Quadrant の subjectOf
- abstract `6823878` "The Two-Layer Black Box…"(**PRELIMINARY_UPLOAD** 2026-05-24)→ **HOLD**(distribute まで)

Cross-link gap: `.zenodo.json` の related_identifiers に SSRN DOI が無い。working-paper Zenodo DOI
`20262112 / 20353789 / 20355907` はあるが SSRN 版と相互リンクされていない → isVersionOf/isSupplementedBy で繋ぐ。

---

## APPENDIX B — AKC その他

- Repo: `agent-knowledge-cycle`(Zenodo `10.5281/zenodo.19200726`)。`docs/inspiration.md` あり →
  PORTABLE PROMPT をそのまま走らせ、**AKC 自身の** inspiration.md から prior-art を導出
  (AAP の候補を流用しない)。coined term = six phases(Research/Extract/Curate/Promote/Measure/Maintain)。
- 他の idea-rescue repo(`authorship-strategy`, `contemplative-agent`, `doctrine-corpus`, hub `shimo4228`)も
  同じ PROMPT で適用可。hub は cross-repo の prior-art/derivative roll-up を持つので最後に。

## 適用順(推奨)
flagship 優先 = prior-art edge ゼロの **AAP → AKC** を先に。各 repo 1 release ずつ。

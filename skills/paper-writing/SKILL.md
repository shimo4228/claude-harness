---
name: paper-writing
description: Academic paper / preprint / position paper の draft skill。Title + outline + section drafting + abstract + references の手順正本。Primary source への直接 access を強制し、claim と cite の 1:1 mapping を author に握らせる。SSRN / arXiv / Zenodo / journal venue 向けに使う。Voice 規約・Source Fidelity 規約・Citation 規約は orchestrator skill `paper-ecosystem` を参照する。
user-invocable: true
origin: shimo4228
---

# paper-writing — Academic paper draft の手順

Position paper / preprint / journal-style article の draft 手順を、`paper-ecosystem` orchestrator の正本ルールに従って organize する skill。

## When to Activate

- SSRN / arXiv / Zenodo / journal venue 向け paper を draft する
- 既存の essay 連作 / ADR 群 / 実装 history から paper を抽出する
- Position paper の outline 確定後、各 section の drafting に入る
- Preprint v1 → v2 の改訂 (significant rewriting を伴う場合)

## Activation 外

- Blog post / essay (人間 primary、informal) → `writing-ecosystem` を使う
- llms.txt / FAQ (AI primary) → `llms-txt-writer` を使う
- README / CHANGELOG (project doc) → これらは skill を介さず直接書く

## Pre-draft Checklist

Paper draft に入る前に、author は次を完了させる:

### 1. Primary source list の確立

Paper が cite する **primary source** をリスト化する:
- 引用元 essays / blog posts (URL + 日付 + 1 行 summary)
- 引用元 ADRs / spec docs (repo path + version + 1 行 summary)
- 引用元 external papers (Author YEAR + arXiv ID / DOI + 1 行 summary)
- 引用元 standards / framework docs (Org YEAR + standard ID)

各 primary source は paper draft 時に **直接読む** ことができる状態にする (URL アクセス可、repo clone 済み、PDF 取得済み)。

### 2. Glossary / summary への依拠を **避ける**

Primary source の代わりに repo の glossary / summary / secondary doc を citation 元として参照しない。Secondary 側の drift が paper に伝播するため (詳細: `paper-ecosystem` skill の Source Fidelity Rules)。

Secondary を参照するのは次の 2 つのみ:
- Term の definition 整合性 check (paper の definition と glossary の definition が一致するか確認)
- Reference list の format 参考 (どの fields を含めるかの style 例)

### 3. Claim ↔ cite source の 1:1 mapping

Outline 段階で、各 section の core claim を 1 文で書き出し、各 claim に対応する cite source を 1:1 で対応させる。Mapping が曖昧な claim は draft に入れる前に解消する。

Format 例:
```
§3 core claim: "Redirect failure has two architecturally distinct modes — principled (intrinsic to autonomous loops) and artificial (workflow work routed through autonomous loops)."
Cite sources:
- Essay 5 (zenn-content/articles-en/react-agent-business-quadrant-2.md, 2026-04-30)
- ADR-0009 §Context (agent-attribution-practice/docs/adr/0009-triage-before-autonomy.md)
- Elish (2019) "Moral Crumple Zones"
```

### 4. Sub-classification の preservation

Primary source が概念に sub-form / sub-cell / sub-type を与えている場合、paper の term introduction で明示する。Flat 化は drift (詳細: `paper-ecosystem` skill の Vocabulary Consistency Rules)。

---

## Section Template (position paper / preprint)

標準的な 9-section 構造:

1. **Title page** — Title + subtitle + author + ORCID + version + companion repository + license
2. **Abstract** — 250-300 words、3 段落構造 (下記)
3. **Introduction** — Problem statement + thesis preview + section roadmap
4. **[Body sections]** — Paper の core contribution。3-6 sections 程度
5. **Relationship to existing frameworks** — 短い (1 paragraph 〜 1 page)、competing frameworks との関係
6. **Conclusion** — Thesis reprise + open questions
7. **References** — APA-like simplified
8. **Acknowledgements** (任意)
9. **Appendix** (任意)

Journal-style article では venue の house style に従って section 番号 / heading 階層 / table & figure 配置を調整する。

---

## Abstract Structure (250-300 words)

3 段落:

1. **Problem statement (~70-90 words)** — どの phenomenon を取り上げ、現状の discourse の何が不足か
2. **Contributions (~120-150 words)** — Paper の core contribution 2-3 個を明示。各 contribution に対し what / why / how が 1 文ずつ
3. **Consequence (~60-90 words)** — Contribution が paper の audience に何をもたらすか、unresolved な open questions の言及

Keywords (5-8 個) を abstract 直下に置く。

---

## References Format (APA-like simplified)

| Source type | Format |
|---|---|
| Journal article | `Author, A. B. (YEAR). Title. *Journal Name* Vol(Issue): pages.` |
| arXiv preprint | `Author, A. B., & Author, C. D. (YEAR). *Title.* arXiv:NNNN.NNNNN.` |
| Conference paper | `Author, A. B. (YEAR). Title. In *Proceedings Title* (pages). Publisher.` |
| Industry / company doc | `Org. (YEAR). *Title.* URL` |
| Standard | `Org. (YEAR). *Standard ID Title.* Publisher.` |
| Repository / dataset | `Author, A. B. (YEAR). *Title (Version).* Platform. DOI` |

詳細: `paper-ecosystem` skill の Citation Format Rules。

---

## Multi-language Convention (任意)

Subordinate 言語版 (例: 日本語訳) を並走作成する場合:

- 英語版が **primary**、subordinate 言語版は **正本ではない**
- ファイル命名: `<paper-name>.md` (英語) + `<paper-name>.ja.md` (日本語)
- 内容変更時、英語版が先、subordinate 言語版を逐次反映
- Technical terms (Quadrant / Phase Separation / artifact name 等) は subordinate 言語版でも英語表記のまま、または英語併記

詳細: `paper-ecosystem` skill の Multi-language Paper Convention。

---

## Writing Process (section drafting)

各 section の draft 手順:

1. **Section claim を 1 文で書き出す** (pre-draft checklist の output を再確認)
2. **Section opening は具体物**: 例 / 既知の現象 / cited source からの引用、抽象的 framing から始めない
3. **Claim を支える evidence** を直後に置く (cite と 1:1)
4. **Section transition** を section 末尾で明示: 次 section に何を渡すか、現 section の何が前提として持ち越されるか
5. **Subordinate paragraphs** は claim を分解する direction か、counter / alternative を treat する direction、いずれかに揃える (両方混在は flow を弱める)

各 section draft 完了後、`paper-reviewer` agent + `source-fidelity-checker` agent + `vocabulary-consistency-checker` agent を **並列** で起動して review する (詳細: `paper-ecosystem` skill の When to Use What flowchart)。

---

## Quality Gate (deposit 前)

Deposit 直前に次を確認:

- [ ] 全 section が `paper-reviewer` を pass している
- [ ] 全 claim が `source-fidelity-checker` で ALIGNED または PARTIAL 判定 (DRIFT は残っていない)
- [ ] 全 term が `vocabulary-consistency-checker` を pass している (sub-classification の introduction 明示済み)
- [ ] `citation-formatter` で orphan citation 0、cite ↔ references 1:1
- [ ] Abstract の word count が venue 標準範囲内
- [ ] DOI / arXiv ID / URL がすべて valid
- [ ] Multi-language 版がある場合、英語版と内容で乖離していない

詳細な dimension は `paper-ecosystem` skill 内 4 つの canonical rules sections を参照。

---

## Related

- `paper-ecosystem` skill — Source Fidelity / Vocabulary Consistency / Academic Voice / Citation Format の正本。本 skill が依拠する orchestrator
- `paper-reviewer` agent — Section draft 完了後の structure review
- `source-fidelity-checker` agent — Section draft 完了後の cite-claim 整合 verify
- `vocabulary-consistency-checker` agent — Section draft 完了後の term 一貫性 verify
- `citation-formatter` agent — Deposit 直前の cite ↔ references final gate
- `writing-ecosystem` skill — Blog post / essay 用、本 skill ではなくあちら
- `llms-txt-writer` skill — AI 向け doc 用、本 skill ではなくあちら

---
name: paper-ecosystem
description: Academic paper / preprint / position paper の執筆・レビューエコシステムの orchestrator。SSRN / arXiv / Zenodo / journal venue 向けの **harness-neutral な学術コンテンツ** を書く / レビューするときに使う。paper-writing / paper-reviewer / source-fidelity-checker / vocabulary-consistency-checker / clarity-reviewer / citation-formatter の役割境界と使い分け、Source Fidelity Rules、Vocabulary Consistency Rules、Academic Voice Rules、Reader Clarity Rules、Citation Format Rules を正本として保持する。人間向け blog / essay には `writing-ecosystem`、AI 向け doc には `llms-txt-writer` を使う。
user-invocable: true
origin: shimo4228
---

# paper-ecosystem — Academic paper 執筆・レビューエコシステムの正本

Academic paper（position paper / preprint / journal-style article）の執筆とレビューに関わるコンポーネント（skill と agent）の役割境界・使い分け・共通規約をまとめた正本。`writing-ecosystem` の sibling として並ぶ。

> `paper-writing` skill の手順は本 skill の Source Fidelity / Vocabulary Consistency / Academic Voice / Citation Format 規約を継承する。drift が起きた場合、本 skill を正とする。

## Scope

**academic paper のみ扱う**。Blog post / essay / newsletter 等の人間 primary かつ informal なコンテンツには `writing-ecosystem` を使う。`llms.txt` / `llms-full.txt` / FAQ 等の AI-facing doc には `llms-txt-writer` を使う。

Paper の audience は次の 2 層を同時に想定する:
- **Academic readers** （AI safety / governance / HCI / org-design 等の researcher）
- **LLM-mediated retrieval channels** （ChatGPT / Perplexity / Gemini 経由で citation する読者と AI）

両者は voice 規約は共通だが、cite 可能性 / DOI 整合 / vocabulary の精確性に対する閾値が高い。

---

## Ecosystem Map

執筆関連コンポーネントは **「Write / Review」× 「構造 / 出典 / 用語 / 読者明瞭性 / 引用形式」** のマトリクスで役割分離されている。

| フェーズ | コンポーネント | 軸 | トリガー |
|---------|---------------|-----|----------|
| **Write** | `paper-writing` skill | Paper draft の手順正本 (pre-draft checklist / section template / abstract structure) | Paper draft タスク全般 |
| **Review: 構造** | `paper-reviewer` agent | Argument flow / section transitions / claim sharpness / structure | Section draft 完了後 / paper 全体 review 時 |
| **Review: 出典忠実性** | `source-fidelity-checker` agent | Paper の claim が cited primary source と整合するか直接 verify | Paper draft 完了後 / deposit 前 |
| **Review: 用語一貫性** | `vocabulary-consistency-checker` agent | 導入 term の定義と本文使用の一貫性、sub-classification の明示 | Paper draft 完了後 / glossary 改訂後 |
| **Review: 読者明瞭性** | `clarity-reviewer` agent | 初見読者の理解可能性 (新語予算 / タイトル軸の貫通 / メタ語り / 内部文脈依存 / 一文テスト) | Paper draft 完了後 / 大幅改稿後 |
| **Review: 引用形式** | `citation-formatter` agent | Cite ↔ references 1:1、DOI / arXiv ID validity | Deposit 直前の最終 gate |
| **Shared** | `paper-ecosystem` skill | Source Fidelity / Vocabulary / Voice / Reader Clarity / Citation 規約 | 執筆 + レビュー時（自動発火） |

---

## When to Use What

```
┌─ Pre-draft ────────────────────────────────┐
│ paper-writing skill                        │
│  → primary source 直接 read を強制         │
│  → claim 1:1 cite mapping を確立            │
│  → section template + abstract structure  │
└──┬─────────────────────────────────────────┘
   │ draft 完了
   ▼
┌─ 並列 review (deposit 前) ─────────────────┐
│                                            │
│  paper-reviewer agent                      │
│   → argument flow / structure / claim     │
│     sharpness                              │
│                                            │
│  source-fidelity-checker agent             │
│   → 各 claim を cite source と 3-way        │
│     verify、DRIFT を flag                  │
│                                            │
│  vocabulary-consistency-checker agent      │
│   → term 定義の一貫性、sub-form 明示       │
│                                            │
│  clarity-reviewer agent                    │
│   → 初見読者の理解可能性 (新語予算 /        │
│     タイトル軸 / メタ語り / 一文テスト)     │
│                                            │
└──┬─────────────────────────────────────────┘
   │ review pass + fix loop
   ▼
┌─ 著者校正 (subordinate 言語版上で) ─────────┐
│ JA mirror を作成し、著者は JA 版で校正する  │
│  → 校正中は JA が作業コピー (修正は JA に   │
│    即時適用、EN 正本は凍結)                │
│  → 校正完了後、JA の全変更を EN へ一括反映  │
│  → 内容が大きく動いていれば並列 review を   │
│    再実行                                  │
└──┬─────────────────────────────────────────┘
   │ EN 反映完了
   ▼
┌─ Deposit 直前 gate ─────────────────────────┐
│ citation-formatter agent                   │
│  → in-text ↔ references 1:1               │
│  → DOI / arXiv ID validity                 │
└────────────────────────────────────────────┘
```

### エージェント並列実行の原則

`paper-reviewer` / `source-fidelity-checker` / `vocabulary-consistency-checker` / `clarity-reviewer` の 4 つは **観点が直交** している (構造 / 出典 / 用語の一貫性 / 読者の理解可能性)。同じ paper draft に対して並列実行可能で、それが推奨される。`citation-formatter` は references list が一通り揃ってからの最終 gate なので逐次。

---

## Source Fidelity Rules

> Paper の draft drift を構造的に防ぐ正本。`source-fidelity-checker` agent が verify するルール集。

### Primary source は直接読む

Paper の各 claim は cited primary source を **直接読んで** verify する。Glossary / summary / repo 内 secondary file への依拠だけで claim を書いてはならない。Secondary 経由で書いた場合、secondary 側の drift が paper に伝播し、後から audit で発覚する (典型的な失敗様式)。

### Drift 発見時の修正方向

paper の claim と primary source が乖離している場合の修正方向は次の優先順位:

1. **Paper を直す** (paper が drift していて primary source が正の場合)
2. **Secondary (glossary / summary) を直す** (paper と primary source が一致しているが、参照していた secondary が drift していた場合 — 次の paper / essay で同じ drift を再生産させない)
3. **Primary source を直す** (primary source 自体が outdated で、author 自身が改訂を判断する場合 — 慎重に。Primary source は通常 published artifact なので、改訂は新 version として publish しなおす)

### Cite 経路の明示

各 claim には cite を 1:1 で対応させ、paper draft 段階で `claim → cite source` の mapping を author が握る。Mapping が曖昧なまま draft を進めてはならない。

### Sub-classification の preservation

Primary source が概念に sub-classification (sub-form, sub-cell, sub-type 等) を与えている場合、paper はそれを保持する。Primary source の sub-classification を flat 化して essence のみ paper に拾うのは **drift**。

---

## Vocabulary Consistency Rules

> Paper 内 term の意味的一貫性を保つ正本。`vocabulary-consistency-checker` agent が verify するルール集。

### 導入と再使用の規律

各 term は paper 内で initially introduce される 1 箇所で definition を持ち、それ以降の使用は initial definition と矛盾しない。Definition と本文使用の不一致は **vocabulary drift**。

### Sub-classification の introduction 義務

Term が sub-classification を持つ場合 (sub-form, sub-cell, sub-type, sub-category 等)、term の introduction 時に sub-classification を明示する。後の section で sub-classification が初めて現れるのは drift。

例: 「LLM Workflow Quadrant」を §2 で導入するなら、§2 内で「(3a) Conversational sub-form」「(3b) Batch sub-form」を明示する。§4 で初めて sub-form が現れるのは drift。

### Essence と consequence の区別

Term の definition は **essence** (load-bearing property) と **consequence** (帰結的性質) を区別して書く。Consequence を essence の位置に持ち上げると、reader は consequence を破る counter-example を以て term の core を否定できてしまう。

例: 「path is decided in advance」が essence、「post-hoc separability」は consequence。後者を essence に持ち上げると、確率的揺らぎを持つ実装に対して term が失効するように見える。

### Glossary との整合

Paper が repo の glossary 等を cite する場合、paper 内 definition と glossary 内 definition が essence で一致する。乖離があれば **片方を直す** (Source Fidelity Rules の修正方向に従う)。

---

## Academic Voice Rules

### 1st-person の控えめ使用

Position paper / preprint では 1st-person 単数 ("I argue", "I propose") の使用を最小化する。代わりに「The paper introduces ...」「The framework records ...」「This section argues ...」のように artifact-centric な voice を使う。

Journal-style article では venue の慣行に従う (一部 venue は 1st-person 単数を許容 / 推奨)。

### Claim には evidence を 1:1 で対応

主張には cite を伴う。「X is the case」と書くなら直後に "(Y, YEAR)" / "(`repo/path.md`)" / "(§N)" 等の evidence pointer を置く。Evidence のない断定は editor / reviewer 側で flag される。

### Negative form より positive form

「Don't build X」よりも「X belongs in Y」を優先する。Negative form は warning として機能するが、reader が次に何をすべきかを残さない。Positive form は alternative を含意する。

例: 「Don't route Q3 work through autonomous loops」 → 「Q3 work belongs in workflow architectures with named bounded roles」

### AI slop / over-hedging / under-claiming / over-claiming

- **AI slop**: writing-ecosystem の Banned Patterns (日英) を継承する。Academic paper でも「revolutionary」「paradigm shift」「powerful」「seamless」等は禁止
- **Over-hedging**: 「It might possibly be the case that ...」のような 3 重 hedge を 1 つに減らす
- **Under-claiming**: Evidence が claim を支持しているなら、weakened form で書かない (修辞的疑問は writing-ecosystem では推奨だが、academic paper では evidence を伴う断定が中心)
- **Over-claiming**: Evidence が支持しない強い断定を避ける。「This proves X」より「This is consistent with X」「The evidence supports X」

### Experimental status の明示

Position paper では未確定の judgment を「experimental」と明示する。確定 claim と experimental claim の境界が paper 内で見えること。

---

## Reader Clarity Rules

> 初見読者の理解可能性を保つ正本。`clarity-reviewer` agent が verify するルール集。想定読者は「分野は知っているが、companion repository・著者の前作・執筆過程の内部議論を一切知らない academic reader」。paper は単独で読めること。

### 新語予算 (Coined-term budget)

- 名指しで導入してよい固有概念は、**タイトルが担保する named concepts** + 引用する framework / system の固有名のみ
- 新語を立てる前に「既存語で 1 文で言えるか」テスト。言えるなら新語を立てない
- 導入した新語は本文で繰り返し働くこと。数回しか使わない新語は平易な言い換えに戻す
- 1 文の解釈に paper 独自の名詞を 2 つ以上同時に要求しない

### タイトル軸の貫通 (Title-axis carry-through)

- タイトルが約束する対比・軸が、thesis 文の**主動詞・主語**に現れること (修飾句に埋めない)
- 各 load-bearing section はタイトルの語彙で論じる。本文がタイトルと別の内部語彙系で走り出したら、**本文をタイトルに合わせて直す** (タイトルは読者との契約)

### メタ語り禁止 (No editorial meta-commentary)

- 語彙選定過程 (「derived, not coined」型)、positioning 戦略 (「the concession comes first because…」型)、編集判断の自己言及を本文に書かない。それらは ADR / 編集ノートに属する
- 自己言及構文 (「is offered as」「is preserved at its verified scope」「is stated so that」) は直接形に書き換える。標準的な academic register (「This paper argues」「The thesis is single」) は thesis 文とその reprise に限り可
- **削ってはならない例外**: claim 強度を縛る必須 hedge (「not offered as a formal proof」型 / 「to the author's knowledge」)、experimental 表記、secondary-source 注記。これらは Source Fidelity / Voice 規約側の要求であり、明瞭性を理由に剥がさない

### 内部文脈依存の禁止 (No insider dependency)

- 段落の理解に repo の構造・sibling project・前作・内部 glossary の知識を要求しない
- 内部文書への cite (ADR-NNNN 等) は**裏付け**であって説明の代役にしない — cite を取り除いても文意が立つこと
- repo 内にしか実体のない名前 (layer 名・phase 名等) は、初出時に inline で 1 行説明する

### 一文テスト (One-sentence test)

- 各 section を一度読んだ初見読者が、その section の主張を平易な 1 文で言えること
- abstract を一度読んだだけで「何を主張し、何が新しいか」が言えること (本文を前提にしない)

---

## Two-Layer Density Rules (本文 / 脚注の二層設計)

> 人間の読み線と LLM 向け情報密度を一つの paper で両立させる正本。Audience に LLM-mediated retrieval channels が入る paper (本 skill の Scope 前提) では default で適用を検討する。人間は脚注を読み飛ばせるが、LLM には本文と脚注が等価に見える — この非対称を設計に使う。

### 原則

Paper を二層で設計する:

- **本文 (body)** — 初見の人間読者向けの痩せた論証線。各 section は claim → evidence → transition の一本道を保ち、補足・例示・規律注記で論旨の流れを切らない
- **脚注 (footnotes)** — 精読者と LLM 向けの密度層。検証済み verbatim・運用詳細・概念の区別・探索の完全性記録をここに収める

### 脚注に出すもの (necessary but flow-breaking)

- 用語衛生の注記 (ラベル規律、出典語との表記の区別)
- 例示・イラスト (本文の論証が依存しない引用・対比)
- 探索・棄却の完全性記録 (検討したが採らなかった候補と理由)
- 用語アンカー (読者の既知物への対応付け — 製品名・ファイル名・規格名等)
- 隣接概念との区別 (誤同一視の防止)
- 可読性のために本文から削った検証済み詳細の**復元** (運用機構、追加 verbatim、対比軸の instantiation) — 本文を痩せさせる編集と脚注での復元はセットで運用する

### 本文に残すもの (脚注に逃がしてはならない)

- **claim 強度を縛る必須 hedge** — 主張と同じ文・同じ段落で可視であること (experimental 表記、"to the author's knowledge"、secondary-source marker、比較形 hedge)
- **誤読防止の disclaimer** — term 導入点で可視であること
- 直後の文が依存する内容 (punchline の前提になる区別・定義)
- 証拠の地位の宣言 (self-attested 等 — 補足ではなく evidential status そのもの)

### 脚注の規律

- 各脚注は self-contained: 自前の cite を帯同する (本文側の cite に依存しない)
- 脚注内の verbatim も Source Fidelity Rules の対象 — register 検証済みのもののみ。脚注で**新しい claim を立てない** (本文 claim の支持・詳細化・区別に限る。新 claim は本文に置くか削る)
- markers ↔ definitions は 1:1、出現順に番号付け。挿入・削除時は全体を再番号し、機械検証する
- `citation-formatter` の orphan 検査は脚注内 cite を含める
- 形式: markdown footnote (`[^n]`)。pandoc (PDF) / Obsidian の両方でネイティブに変換・描画される。definitions は**本文末 (Conclusion の後、References の前) に出現順で一括配置**する — endnote の学術慣行と一致し、render はどの環境でも定義位置を無視して文末/ページ下部に集めるため、一括配置なら raw source を線形に読む読者 (人間・LLM とも) にも本文が痩せたまま見える。見出し (`## Notes` 等) は付けない (pandoc の PDF 化では定義がページ下部へ移り、空見出しだけが残るため)
- Subordinate 言語版でも番号と内容を 1:1 で mirror する (引用 verbatim は原語のまま)

### 限界 (over-densification の防止)

- 脚注は本文の不足を補う場所ではない — 本文だけで一文テスト (Reader Clarity Rules) を通ること
- 1 文に複数マーカーを密集させない (目安: 1 文 1 marker)
- 本文を 1 行も読まずに脚注だけ繋いでも paper の主張が変わって見えないこと (脚注は密度であって別の論文ではない)

---

## Citation Format Rules

### 形式の一貫性

Paper 全体で **1 つの cite 形式** を選び一貫させる。Style mixing は禁止。

| 推奨 style | venue |
|---|---|
| APA-like simplified (Author YEAR) | SSRN / preprint / position paper の default |
| Chicago author-date | 一部 humanities / law journal |
| IEEE numbered | engineering / CS journal の一部 |

### Reference list の必須項目

| Source type | 必須項目 |
|---|---|
| Journal article | Author(s). (YEAR). Title. *Journal* Vol(Issue): pages |
| arXiv preprint | Author(s). (YEAR). Title. arXiv:NNNN.NNNNN |
| Conference paper | Author(s). (YEAR). Title. *Proceedings* (pages) |
| Industry / company report | Author / Org. (YEAR). Title. URL |
| Standard | Org. (YEAR). Standard ID Title. Publisher |
| Repository / dataset | Author(s). (YEAR). Title (Version). Platform. DOI |

### DOI / arXiv ID の inclusion

DOI が存在する source は references list に DOI を inclusion する。arXiv preprint は arXiv ID (NNNN.NNNNN 形式) を inclusion する。Zenodo deposit は concept DOI と version DOI を区別する (paper では通常 version DOI を引く)。

### Orphan citation の禁止

In-text に出てくる cite が references list に存在しない、または references list の entry が in-text で 1 度も cite されていない状態は **orphan citation**。`citation-formatter` が detect する。

---

## Multi-language Paper Convention (任意)

Subordinate language version (例: 日本語訳) を作る場合の規約:

- 英語版が **primary**、subordinate 言語版は **正本ではない**
- ファイル命名: `<paper-name>.md` (英語) と `<paper-name>.ja.md` (日本語)
- 各ファイル冒頭に `Language: English | [日本語](...)` (英語版) / `Language: [English](...) | 日本語` (日本語版) を明示
- 内容変更時、英語版が先、subordinate 言語版は逐次反映 (両者を独立に改訂しない)
- Technical terms (Quadrant, Phase Separation 等) は subordinate 言語版でも英語表記のまま、または英語併記

### 著者校正は日本語版で行う (校正フェーズの例外)

英語が正本のまま、**著者の校正は日本語版上で行う**。手順:

1. Agent 並列 review 通過後、JA mirror を作成する
2. 校正中は **JA が作業コピー**: 著者の指摘による修正は JA に即時適用し、EN 正本は凍結する (「英語版が先」ルールはこのフェーズだけ反転する)
3. 校正完了後、JA の全変更を EN へ**一括反映**する (差分の取りこぼし検査つき)
4. 反映で内容が大きく動いていれば agent 並列 review を再実行してから citation gate へ

この往復を 1 回で済ませるのが目的 — 修正のたびに両言語を同期するのは冗長であり、校正の妨げになる。

このパターンは AAP repo / contemplative-agent repo の `*.ja.md` 規約を継承している。

---

## How to Extend (Project Overlay)

Venue 固有 (SSRN subject classification、arXiv endorsement、journal house style 等) のルールは **プロジェクトの rules/ に overlay** として置く:

```
<project>/.claude/rules/<venue>-paper-writing.md
```

例:
- `agent-attribution-practice/.claude/rules/ssrn-paper-writing.md`
- `contemplative-agent/.claude/rules/arxiv-paper-writing.md`

overlay 側のファイル冒頭に「本 skill を base とする」旨を明記し、venue 固有の追加ルールだけ書く。base の Source Fidelity / Vocabulary / Voice / Citation は overlay で再掲しない。

---

## Related

- `paper-writing` skill — Paper draft の手順正本 (本 skill が canonical rules を保持)
- `paper-reviewer` agent — Paper の argument flow / structure / claim sharpness review
- `source-fidelity-checker` agent — Paper claim と cited primary source の 3-way verify (今回 build の主目的)
- `vocabulary-consistency-checker` agent — Term 定義の一貫性 + sub-classification 明示の verify
- `clarity-reviewer` agent — 初見読者目線の明瞭性 review (新語予算 / タイトル軸 / メタ語り / 内部文脈依存 / 一文テスト)
- `citation-formatter` agent — Cite ↔ references 1:1、DOI / arXiv ID validity の最終 gate
- `writing-ecosystem` skill — **人間 primary な blog / essay** 専用。audience が human informal なら本 skill ではなくあちらを使う
- `llms-txt-writer` skill — **AI 向けドキュメント (llms.txt / llms-full.txt / FAQ 等)** 専用。audience が AI なら本 skill ではなくあちらを使う

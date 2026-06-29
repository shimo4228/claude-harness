---
name: readme-writer
description: README やプロジェクトのトップページ（repo を開いた人が最初に見る入口）を書く・直すときに使う。こんな時に必ず呼ぶ — README が長い／文字の壁で読まれない→短く走査しやすくしたい、開いて数十秒で「何のプロジェクトで自分向けか」が伝わる入口にしたい、構成図・アーキ図を入れたい（PNG や架空図でなく Mermaid を勧める）、badge を貼りすぎたので整理したい、長い rationale や「なぜ」を docs/ に逃がしたい、研究・DOI repo の README を引用付きで読める長さにまとめたい。短く・視覚優先にしつつ、LLM が README 一枚で要点を復元できる情報フロアは残す。CLI でも UI でも研究 repo でも、日本語でも英語でも、新規作成でも既存改善でも対象。AI 専用ドキュメント（llms.txt / llms-full.txt 等）は対象外（→ llms-txt-writer）、記事・エッセイ等の長文 prose は → writing-ecosystem。
user-invocable: true
origin: shimo4228
---

# readme-writer — Human-Facing README Skill

人間に向けた README を書く・改善するスキル。`llms-txt-writer` が AI 専用 surface を担うのに対し、本 skill は **人間 surface の単一正準入口**を担う。

加えて重要な事実: **README は、grounding 経路（AI 検索 / チャットに repo URL を貼る）で LLM が確実に前提にできる唯一の surface でもある**。そのため README は「人間向けに短く・視覚的に」しつつ「LLM が README 一枚だけ読んでもプロジェクトを復元できる小さな情報フロア」を必ず残す——この両立が本 skill の中心課題。

## When to Use

- README.md / README.ja.md を新規作成・改善する
- repo / プロジェクトの「人間が最初に着地するページ」を整える
- 既存 README が「機械寄りで人間に中途半端」/「人間向けに薄すぎて LLM が掴めない」のを直す
- README を**短く・視覚優先**にしたいが情報フロアを落としたくないとき

**使わない場面**:
- `llms.txt` / `llms-full.txt` / FAQ など AI 専用 doc（→ `llms-txt-writer`）
- 記事・エッセイ・ブログ等の長文 prose（→ `writing-ecosystem`）
- graph.jsonld の設計（→ `jsonld-knowledge-graph`）

---

## 軸は「人間の ATTENTION × LLM の INFORMATION」

README 最適化の本当の対立軸は「人間向け情報 vs LLM 向け情報」ではない。**人間の注意（短く・掴む・走査できる）× LLM の情報（README だけで復元できる）**である。両者は同じ施策に収束する（後述）ので、トレードオフでなく**設計で両取りする**。

### README は確実に読まれる唯一の surface（だが「only」ではない）

- AI 検索 / 引用クローラは **llms.txt を実質読まない**（複数の 2026 ログ調査で大半がゼロリクエスト、主要検索ベンダーは公式に非対応表明）。
- `graph.jsonld` は直接 fetch では plain text 扱いされ、**README の事実の代替にならない**（対照実験）。
- ゆえに **README に置いた情報を「機械層が backstop する」前提で薄くしてはいけない**。

ただし重要な較正: 「LLM は README *しか* 読まない」は強すぎる。正しくは「**generic な paste-URL / 検索 grounding では README が*確実に前提にできる*唯一の面**」。別経路（検索インデックスが他ファイルを既に chunk 済み / README からのリンク追跡 / GitHub connector・API でのファイルツリー露出 / pretraining 由来の知識）も存在する。**結論が最も強いのは匿名 live web grounding と直接ランディング fetch**。逆に **routed coding agent（Claude Code / Cursor 等）は llms.txt を on-demand で読む**ので、llms.txt は agentic チャネルの保険として依然有効——ただし AI 検索の入口ではない。

---

## なぜ「構造 lint」と「ホリスティック review」を分けるのか

README 品質には 2 種類の property が混在する。**Code-LLM Layering**（構造は code が 100% 精度で所有、意味は LLM が所有）に従い所有者を分ける。判定軸は [`when-code-when-llm`](../when-code-when-llm/SKILL.md): 「同じバイト列が文脈で違う意味になりうるか?」

| property | 例 | 種別 | 所有者 |
|---|---|---|---|
| 構造的 | H1 数 / 見出しレベル / alt-text 有無 / ローカルリンク解決 / raster 図ファイル名 / badge 数 / details 内の DOI 等 / H1 直後の prose 行 | structural | **code（`readme_lint.py`）** |
| 意味的 | lead が人を掴むか / 価値提案の明快さ / **README-only で LLM が復元できるか** / 物語の流れ / badge が vanity か | semantic | **LLM のホリスティック review** |

**README に研究値ベースの数値スコアは作らない**。llms.txt のセクション比率（ski-ramp 等）は LLM 引用研究で検証された決定論シグナルだが、README の「良い入口か」は意味的判断であり同等の決定論的知見がない。entity density 等の AI surface 指標を人間 README に持ち込むのは anti-pattern。

### ただし「構造的 AI 可読性」は積極採用する（two-sided rule）

「AI surface 指標を持ち込まない」は半分。原則は **「アイデアが*どう伝わるか*は最適化してよい（強度に上限なし）。アイデアが*何であるか*は決して曲げない」**。

- **採用（強度無制限）**: 見出し階層・情報設計・**entity anchoring**（著者名 / ORCID / DOI / canonical 識別子を**prose に**書く）・固有/造語語彙の anchoring・answer-first の lead・at-a-glance の表。これらは人間にも grounding 経路の LLM にも効く**収束ゾーン**。
- **禁止**: keyword stuffing・水増し属性・疑問見出し farming・glossary 投下・retrieval の報酬関数に合わせた主張の歪曲。引用や star は**成功指標ではない**ので、歪曲が奉仕する目標がそもそも無い。

---

## 最小 LLM-read フロア（小さく・非交渉・肥大させない）

**規則**: README を LLM が*それ一枚だけ*読んだ（llms.txt も graph も読まれない）として、**テキストだけで**プロジェクトを復元できること。

フロア要素（prose / markdown / Mermaid で。**画像のみ・details の中のみ・リンク先のみ は不可**）:

1. **identity 文**（最初の 1-2 文・単独で読める）: 「X は {誰}向けに {何をする} {カテゴリ} である」
2. 解く問題 / 対象者 / 差別化点
3. canonical な事実: 実名・言語/stack/status。**研究/DOI repo は** DOI + how-to-cite（BibTeX / CITATION）+ 語彙を支える 3-6 個の core concept 定義
4. 具体例を **1 つだけ**: コードなら関数 signature + 最小実行片（フル実装は載せない——肥大 + hallucination 誘発）/ 研究なら核となる主張 + 2-3 個の鍵となる数値
5. 深部 doc への link-map は**ポインタのみ**。load-bearing な事実をリンク先 / llms.txt / graph だけに置かない

> **最重要の落とし穴**: フロアは*小さな*非交渉コア。「削るな・再構造化せよ」を効かせすぎると、Mermaid / details / フロア節に情報が温存され、**README が偽装 llms-full.txt に肥大**する。人間の目標は*短く*だった。**フロア以外は容赦なく削るか relocate する**（→ length budget）。

`graph.jsonld` / `llms.txt` を README から作る場合、**README prose を構造ソースにしない**。識別子・graph 辺は `CITATION.cff` / `.zenodo.json` / frontmatter の小さな manifest から derive する（手書きの並行コピーは drift する）。

GitHub のメタ面（repo description / topics / social-preview / CITATION ファイル / release / package metadata）も grounding に効く floor の一部。README 本文では設定しない（`gh repo edit` / `release-doi` 側）が、checklist として揃っているか確認する。

---

## Visual-first（Mermaid 第一・raster 最後）

「短く・視覚的に」の正しい読み替えは **「散文の壁を*走査可能な構造*に圧縮する」**。散文を画像化するのではない。そして **「Mermaid 第一」≠「何でも Mermaid」**——まず *図にすべきか* を絞る。モバイル（狭幅）で潰れない・LLM が拾える形式を選ぶ。

### 形式の選択

| 中身 | 最適形式 | 理由 |
|---|---|---|
| 3 ステップの線形 / 単純な列挙 | **prose / list / 小さな表** | 全デバイス（特にモバイル）で読める。図にする価値がない |
| 本当に graph 形状（関係・多分岐・matrix） | **Mermaid（`TD` 縦方向）** | ソースがテキストで LLM も読める。縦スクロールはスマホで自然、横（`LR`）は潰れる |
| 大きい / 複雑な図 | **committed SVG（拡大・パン可）/ subsystem 分割** | 巨大 Mermaid は desktop でも上限に当たり、モバイルで潰れる |
| 実 UI / 実行結果 / 写真 | **raster（PNG/JPG/WebP/GIF）** | Mermaid で表現できないものだけ |

**どの図にも一文のテキスト等価を必ず添える（hard rule）**。これが「人間にも LLM にも届く」を保証する本体: モバイルで図が潰れた人間・```mermaid fence を opaque code として読み飛ばす LLM 抽出器・スクリーンリーダ を同時に救う。図はその上の視覚的ボーナスであって、情報の唯一の担い手にしない。

### Mermaid の要点

- GitHub が theme-aware SVG にネイティブ描画。ソースはテキスト（diff 可能・~10 token/edge）で **pixel を見られない text-only クローラにも読める**。散文/graph に埋もれた構造（concept matrix・phase binding・pipeline 段）を Mermaid 化すると**短くなり情報密度が上がる**。
- **モバイル最優先で `TD`（縦）**。横長 `LR` は狭幅で破綻しやすい。
- 描画上限は char ベース（`maxTextSize` 既定 50,000）+ edge ベースで、ノード数ではない（「50-100 node が限界」は俗説）。超えそうなら subsystem 分割。special な Project README では描画されない。
- 抽出器が Mermaid を落とす可能性があるので、上の**テキスト等価**で意味を必ず別途担保する。

### raster / その他

- raster は **load-bearing な情報を担わせない**。**alt-text を必須**（hard floor: text 経路は alt しか読まない = alt 無し画像は LLM に不可視。a11y だけの話ではない）。
- dark/light は `<picture><source media="(prefers-color-scheme: …)"><img alt="…"></picture>`。`<img alt>` は二重に load-bearing。
- 画像 asset は repo に commit し**相対パス**参照。外部 hotlink（camo 破綻）と inline/animated `<svg>`/`<embed>`/`<object>`（GitHub が sanitize）を避ける。
- **badge は 2-4 個の高信号のみ**（CI / version / license / 研究 repo は DOI）。vanity badge を避ける。狭幅で badge 段が嵩張らないよう数を絞る。
- CLI repo: asciinema→agg GIF + 一文キャプション。UI repo: スクショ/GIF + alt-text。

> 稀な bespoke 図は **Claude Artifacts / Claude Code の svg・diagram skill** で committable な SVG を生成し `assets/` に置く。

---

## Length budget（語数目標は持たない）

語数目標は**置かない**（「500-1500 語の sweet spot」「visual README は star が増える（GitHub 研究）」はいずれも捏造/無出典として棄却済み）。代わりに:

- **above-the-fold（最初の 1 画面 = 30 秒で「自分向けか」を判断）**: 任意の hero → H1 → 一行 tagline（価値提案＝最も確実に LLM に抽出される行）→ ≤4 functional badge → フロアの事実 → copy-paste の quick start。**深い rationale はこの後**。
- **順序は repo 種別で変わる**: 「quickstart→rationale」はソフトウェア向け。論文 / dataset / 概念 / DOI essay repo では当てはまらない。固定順を強制せず、**「identity + canonical facts が deep rationale より前」**だけを守る。lint の `identity_lead` は「lead 文の存在」だけを構造的に見て**順序は強制しない**。
- 総量は 1 変数で決まる: **正準 docs サイト / ADR が深部を吸収するか**。深い「なぜ」/ 設計 rationale は ADR / `docs/` / `llms-full.txt` / deposited paper に移し、README には一行ポインタ（Diátaxis の explanation-displacement）。これが「450 行の研究 repo README」の直接の治療。
- `<details>` は**二次的な bulk のみ**（option 表・FAQ・troubleshooting・full glossary）。人間の視界を整理しつつ LLM には届く。だが**フロアを入れない**（primacy 喪失 + Ctrl+F 不可。raw-markdown 経路では読めるが、描画ページの要約器は折りたたみを de-prioritize しうる）。

---

## Workflow（Code filter → LLM review → 人間 gate）

### 1. Code filter — `readme_lint.py`（決定論的・structural only）

```
uv run --directory ~/.claude/skills/readme-writer python -m scripts.readme_lint "$ARGUMENTS"
```

引数は README の絶対パス。`--json` で機械可読出力。exit code が code-owned gate（**0=clean または warning のみ / 1=error severity あり / 2=not found・too large**）。

検査項目（**スコアでなく具体 issue**。severity 2 段階）:

**error（gate を落とす・ハード構造）**
- `single_h1` — H1 はちょうど 1 個
- `heading_levels` — 見出しレベルを飛ばさない
- `alt_text` — すべての画像に alt（**hard floor**: alt 無し = LLM に不可視）
- `local_link` — ローカル相対リンク / 画像 src が実在する

**warning（助言・gate を落とさない）** — 構造的に検出するが「本当に問題か」は判断なので surface のみ。意味判断は LLM review に委ねる:
- `raster_diagram_hint` — 図っぽいファイル名の raster（architecture/flow/diagram/pipeline 等の .png/.jpg/.webp/.gif）→ Mermaid 化を提案。SVG・スクショ・logo は除外
- `badge_budget` — badge が多すぎ（既定 >6）。**数のみ**判定（vanity か否かは LLM）
- `details_floor_leak` — `<details>` 内に DOI / BibTeX / CITATION トークン（floor 漏れの兆候。「真に floor か」は LLM 判断）
- `identity_lead` — H1 と最初の section の間に prose の lead 文が無い（**順序は強制しない**。H1 不在は single_h1 が担当）
- `doi_citation_pairing` — DOI があるのに how-to-cite（Citation 節 / BibTeX / CITATION.cff）が無い（**DOI を非研究 repo に強制しない**——DOI がある時だけ発火）

### 2. LLM holistic review（rubric-as-lens・**スコア無し**・signal-first）

lint が通ったら Claude が README を**ホリスティックに読み**、次の lens で**具体所見 + 具体 diff** を出す:

- **🚩 README-only recovery（旗艦・最高レバレッジ）** — README の**テキストだけ**を読み、(identity / 対象者 / 問題 / 差別化点 / 該当すれば DOI・引用 / 3-6 個の core concept / 例 1 つ / 次への link) を**復元できるか**を確認。**欠落を具体的に列挙**（「対象者が書かれていない」等）。スコアは付けない。これは「最小 LLM-read フロア」の運用化そのもの。
- **Lead の What / Who / Why** — 最初の画面で「何で・誰向けで・なぜ気にすべきか」が分かるか
- **人間フック / 価値提案** — 抽象語でなく具体で価値が言えているか
- **物語 / scannability** — 段落・見出し・list・Mermaid が人間に追えるか
- **短さの検証（最重要の逆方向チェック）** — フロア以外が relocate されているか。Mermaid / details / フロアに情報を温存して**偽装 llms-full.txt に肥大**していないか
- **visual の妥当性** — 図は Mermaid か（raster なら Mermaid 化 / テキスト等価があるか）。badge は高信号か（vanity でないか）
- **fact 一致** — 主張が機械層（llms.txt / graph.jsonld）と矛盾しないか → **`context-sync` に委譲**

**スコアを付けない理由**（signal-first + scaffold-dissolution）: 「次の行動を変える情報」だけを出す。`Lead: 6/10` は行動を変えない。「lead が誰向けか言っていない」が行動を変える。出力は diff 形式で `y/n` 承認できる粒度に分割。author-reviewer separation のため review は実装者と別 agent プロセスで回すのが望ましい（`editor` / `essay-reviewer` と同型）。

### 3. fact 一致確認 → `context-sync`

README の事実が llms.txt / llms-full.txt / graph.jsonld と一致するか（cloaking 回避）は `context-sync` が正本。本 skill では再実装しない。

### 4. 人間 gate

diff を人間が承認して適用。

---

## What This Skill Does NOT Do（境界）

- `llms.txt` / `llms-full.txt` を書かない（→ `llms-txt-writer`）
- `graph.jsonld` を設計しない（→ `jsonld-knowledge-graph`）
- cross-surface の drift 検出 / 同期をしない（→ `context-sync` / `release-doi`）
- 記事 / エッセイを編集しない（→ `writing-ecosystem`）
- repo の description / topics / social-preview を設定しない（`gh repo edit` / `release-doi` 側。本 skill は checklist として提示するのみ）
- **品質スコア / grade / 評点を出さない**

---

## Anti-patterns

- 数値スコアだけ出して具体案なしで終わる（recommender 型の罠）
- 構造 lint で済む項目を LLM に判断させる / 意味的判断を regex で代用する（`when-code-when-llm` 参照）
- AI surface の数値指標（ski-ramp / entity density / 疑問見出し farming）を人間 README に流用する（可読性低下）
- **「ビジュアル優先」を散文の画像化と解釈する**（raster 図は text-only LLM に不可視 = 情報をエージェントから隠す。Mermaid を使う）
- **「削るな・再構造化せよ」を効かせすぎて偽装 llms-full.txt 化する**（フロアは小さく、上は容赦なく削る/relocate）
- 機械層（llms.txt/graph）が backstop する前提で README フロアを薄くする（grounding 経路で読まれない）
- `llms.txt`/`graph` を **README prose から** derive する（drift。manifest から derive）
- 人間向けに事実を盛る / マネタイズ訴求を足す（authenticity 毀損 + 機械層との矛盾 = cloaking。梱包は変えても主張は変えない）

---

## Verification

```bash
cd ~/.claude/skills/readme-writer
uv sync --dev
uv run pytest tests/ --cov=scripts --cov-report=term-missing
```

`fixtures/sample_clean.md`（issue 0・Mermaid 図を使う best-practice 例）と `fixtures/sample_issues.md`（全 9 チェックを発火させる例）で基本挙動を確認できる。

---

## Related

- [`llms-txt-writer`](../llms-txt-writer/SKILL.md) — AI surface の対になる writer（研究値ベースの `geo_check.py` を持つ）。本 skill は人間 surface。
- [`when-code-when-llm`](../when-code-when-llm/SKILL.md) — structural / semantic の判定軸
- [`context-sync`](../context-sync/SKILL.md) — README ↔ 機械層の fact 一致 / drift（fact 検証はこちらに委譲）
- [`jsonld-knowledge-graph`](../jsonld-knowledge-graph/SKILL.md) — graph.jsonld 設計
- [`writing-ecosystem`](../writing-ecosystem/SKILL.md) — 人間向け長文 prose の orchestrator
- `inspiration.md` — 設計の出自・一次研究の provenance・外部エビデンスの出典（Portability のため SKILL.md 本文から分離）

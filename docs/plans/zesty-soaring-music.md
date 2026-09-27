# 執筆ハーネスに足場溶解をかける

## Context

Orwell の 6 rules を執筆規約に取り入れられないか、という問いから始まった。調査の結果、**取り込むべき新規ルールはほぼ無い** — 6 つのうち 4 つ（短い語 / 削る / 能動態 / 専門用語）は `writing-ecosystem` に既にあり、`It's not X, it's Y` も `style-diagnostics.md:23` にある。

代わりに見つかったのは書き方の差だった。Orwell のルールは短い原則で終わり、読み手が自分の原稿に問いを向ける余地を残す。既存規約は同じ内容を、例示・例外・判定手順・整合弁明・出自の日付で包んでいる。最も鮮明な証拠が規約自身の中にある — `writing-ecosystem/SKILL.md:216`:

> 「皆さん」の禁止だけでは、誰にも語りかけない中立解説文が通ってしまう（2026-08-20 著者指摘 — 禁止形と機械検出だけが残り、読者へ語りかける側の指示が落ちていた）

短い原則を禁止形に狭めた結果、意図が落ちた。その対処が**さらに 11 行足すこと**だった。原則を復帰させれば禁止形と積極形の両方が導ける。

この操作には harness 内に既に名前がある — `rules/common/akc-cycle.md` の **Scaffold Dissolution**（rule は足場であり、実践が回るようになれば簡素化・削除する）。元ポストは新規ルールの供給源ではなく、執筆ハーネスへ足場溶解を一度かける契機として扱う。

執筆系 15 ファイル（実測 2,504 行 + `style-diagnostics.md` 36 行）を監査した結果、**問題は 3 種類**あった。依頼は 1 のみだが、2 と 3 は溶解作業の途中で必ず触る場所にある。

| 種別 | 内容 | 直し方 |
|---|---|---|
| **1. 足場** | 原則に添えた例示・例外・判定手順・整合弁明・出自の日付 | 畳む。経緯は ADR へ |
| **2. 複製** | 「ここに複製しない」と宣言しながら複製している | 正本 1 つへ統合（ADR-0010: 統合 > ポインタ、揃えるは禁止） |
| **3. 実害** | 複製が drift して規約が食い違う / 存在しない保証の主張 / canon 自身の規約への違反 | 足場溶解と独立に修正 |

## 操作規則

各行に一つだけ問う — **その行は読み手に問いを起こすか、問いを先回りして塞いでいるか。**

| 分類 | 扱い |
|---|---|
| **A: 目標形** 原則で終わり、適用の判断を読み手に残す | 保持 |
| **B: 足場** 例示・例外・判定手順・整合弁明・出自の日付 | 畳む |
| **C: 配線** 正本ポインタ・境界宣言・Related・手順のステップ列・interface 定義 | **対象外**。事実であって原則ではない |
| **D: 検査項目・数値閾値** reviewer が実際に照合する実値 | **保持**。抽象化すると findings が劣化する |

**B と D の境界が本作業の要**。Orwell のルールは書く人向けで、検査者向けではない。`prose-clarity-reviewer:47-49` の「冒頭の摩擦 / 前述の問題」実例列挙は grep 可能な検出語なので D、抽象化すると検出不能になる。一方 `essay-reviewer:103` の独立論点上限「4」は D として残し、括弧内の「なぜここに数値があるか」弁明だけを畳む。

参照モデル: **`quality-gate/SKILL.md`（62 行）が 14 ファイル中もっとも健全**で、A/C/D の比率が目標形。他ファイルはこれに寄せる。

著者裁定済み: 実測由来の拡張（短い原則が実際に失敗して足された文言）も畳む。失敗の原因が「原則を禁止形に狭めたこと」なので、拡張でなく原則の復帰で直る。

---

## Tier 1 — writing-ecosystem 本体（canon。下流全部に効く）

### 1a. Craft 規約を短い原則の列へ戻す（`SKILL.md:200-253`、54 行 → 約 18 行）

現行は 9 bullet + 3 subsection（語りかけの積極形 11 行 / 段落密度の機械的閾値 12 行 / 専門用語の緩和策 15 行）。新形:

```markdown
## Craft 規約（文の技術）

genre 中立。出典: Orwell "Politics and the English Language" (1946)、
Kaguura Gichuru (The Write Path, 2026-07)。

- **一人の読者へ手紙を書く。** その文は誰に向いているか
- **読者は前を覚えていない。** その指示語は何を指すか、その場で言えるか
- **副詞を削り、動詞を強くする。** 数値で言えるなら数値で言う
- **能動態を既定にする。** 行為者を伏せる理由があるか
- **平易語で足りるなら平易語を使う。** 硬い語は誰のためか
- **日常語で言えるなら専門用語を使わない。** その語は読者の語彙か
- **見慣れた比喩は使わない。** 情報を運んでいるか、間を埋めているか
- **第 2 稿は第 1 稿より短い。** その文は論点を前へ進めるか
- **文の壁は宿題に見える。** ただし全行独立はロボット臭
- **深い input からしか深い文章は出ない。**

これらは判断の補助であって検査項目ではない。守った結果、文が不誠実になる・
回りくどくなる・言いたいことが消えるなら、規約の方を破る。

shared word target は置かない。長さの上限は local contract が持つ。
```

末尾 2 行が Orwell ルール 6（著者承認済み）。「見慣れた比喩」がルール 1 で、**禁止形のみ**（「新しい比喩を作れ」は原文になく、初回提案時の拡大解釈だったので入れない）。

移送:
- 「語りかけの積極形」11 行 → 削除。原則へ吸収。経緯は ADR
- 「段落密度の機械的閾値」12 行 → `prose-clarity-reviewer` へ降ろす。`SKILL.md:247` が既に確立した扱い（「閾値は binding な判定を出す clarity reviewer 側が持つ」）と同型にする。**ただし clarity reviewer に密度検査は現存しない — これは移送でなく新設で、finding surface が変わる**。2d の editor 側削除と同時に行う
- 「専門用語の緩和策」7 手 → `references/style-diagnostics.md` へ。「どう直すか」は診断表の性質

### 1b. 同型を残りの節へ

| 箇所 | 現状 | 操作 |
|---|---|---|
| `:29-34` Content integrity | 原則 1 つ + 誤読を塞ぐ 3 文 | 原則 1 文へ。正本は zenn-content ADR-0001 |
| `:105-106` 内容 GO の位置 | 手順 + 「（2026-08-27 著者指示 — …やり直しになる）」 | 理由の先回りを削る |
| `:142` 出典編入 | 「現状この step が抜けやすいので明文化する」 | 自己弁明を削除 |
| `:182-196` 自リポ言及 | 原則 + 2 条件 + 該当しない場合 + 判定手順 + 背景 4 行 | 原則 + 回数上限（D）へ。背景削除 |
| `:290` AI slop 誤検知ガード | `style-diagnostics.md:4` と二重定義 | 削除（正本は診断表側） |
| `:306-313` 発見調の診断表 | 本文が自ら「診断例」と呼んでいる | `style-diagnostics.md` へ移送 |
| `:355` Higher Ground | 「既存の『未解決の正直さ』…と両立する」 | 整合弁明を削除 |
| `:406` Section Length | 「（ハードルールではなく目安）」 | 先回りの緩和を削除 |

### 1c. 到達性の非対称を直す

Ecosystem Map（`:38-60`）と Related（`:425-433`）に `x-draft` / `public-comment` の行が無い。description は 4 skill 全部を NOT for で名指しているのに、本文の地図には 2 つしか無い。2 行追加。

---

## Tier 2 — 実害の修正（足場溶解と独立。小さく、今直す）

| # | 箇所 | 内容 |
|---|---|---|
| **2a** | `headline-craft:38` | 「「N 選」「N 倍速」は規約違反」が**無条件禁止**。正本 `writing-ecosystem:385` は「実測の裏付けなく数字で釣る形」だけを禁じ、証拠数値（「1,000 件を分析したら」型）は推奨する。複製の際に条件節が落ちて硬化した。行を削除しポインタへ |
| **2b** | `x-draft:74-76` | 「この分岐は writing-ecosystem の『意図的な分岐』に登録済み（逆修正されない）」— **その登録は存在しない**。canon 側の x-draft 言及は frontmatter description の NOT for のみで、意図的分岐として本文に登録されているのは `readme-writer`（`:433`）だけ。→ 1c で Ecosystem Map / Related に x-draft を足すと同時に、canon へ意図的分岐を 1 行登録して主張を実体化する |
| **2c** | `essay-reviewer:92-96` | Title evaluation 節が**点検面の重複 + 実行順の矛盾**を作っている。点検の正本は `title-reviewer`、かつ受け入れ profile では title-reviewer は著者の内容 GO 後、essay-reviewer は凍結本文に対して走る — つまりタイトル未確定の時点でタイトルを検査している。節を削除し `title-reviewer` へのポインタ 1 行に |
| **2d** | `editor:136` | `forward-reference avoidance` と `paragraph density` を必須検査に列挙。canon（`writing-ecosystem:208`）は前者の機械検査を `prose-clarity-reviewer` に割り当て済みで、後者は 1a で同 reviewer へ降ろす。並列起動で同一 finding が 2 本の report に出る。**両方**を editor から削除し、所有者を clarity reviewer 側に一本化する |
| **2e** | `public-comment:39` | `#ai-slop-禁止リスト` アンカーが実在しない（実見出しは `## AI Slop`）。同行は「文体・構造 tell」の正本を `writing-ecosystem` と書くが実体は `style-diagnostics.md:19-28`。両方修正 |
| **2f** | `editor:212` | `Example 2` から始まり `Example 1` が無い（削除の跡）。採番修正 |

---

## Tier 3 — 複製の解消（正本 1 つへ統合）

ADR-0010 Decision 1・5 に従う — 「揃える」は採らない。正本 1 つを残し、他は**削除**（ポインタで済む場合のみポインタ）。

| # | 複製 | 正本 | 操作 |
|---|---|---|---|
| **3a** | Output Format 骨格。`editor:149-203` と `essay-reviewer:164-218` が約 55 行ずつほぼ同一（差分は語尾程度） | 新設 `agents/references/review-output-format.md` | 共有 reference 化。両ファイル合計で約 100 行減 |
| **3b** | 公開可否の非発行。`editor:200-202` + `essay-reviewer:215-217` が逐語コピー、うち 2 文は `quality-gate` の手順の再説明 | `quality-gate/SKILL.md:10` | 両 agent は 1 文（「本 agent は公開可否を出さない」）のみ残す |
| **3c** | 専門用語の初出説明。`editor:117` / `essay-reviewer:42, 61, 108`。severity も揃っていない | `prose-clarity-reviewer` | **前提: 純削除では検査が落ちる。** clarity reviewer の `:28-32` は Coined-term budget（予算内か・置換可能か）で、**「初出で説明されているか」の検査は現存しない**。先に clarity reviewer へ first-use 検査を 1 行足してから他を削る。`essay-reviewer:61` の `3.5.` 採番は後付けの物証 |
| **3d** | `readme-writer/SKILL.md` ↔ `references/readme-judge-checklist.md`。造語予算 `~6`、「導線であって説明の代替ではない」、「件数で verdict を決めない」が各 2〜4 箇所に実値で存在 | **checklist** | checklist を単一正本に。SKILL.md 側の R10-R13 / K5 相当を削除（20 行以上減）。逆向きは judge の fresh-context 固定コアを壊すので取らない。**`SKILL.md:179` の「上限 2 ラウンド」は残す** — 消費者は orchestrator なので C（配線）。judge 向け checklist だけに置くと消費者が逆転する |
| **3e** | `writing-ecosystem` 規約の複製。`public-comment:47`（宣言は :39）/ `x-draft:78`（宣言は :67）/ `headline-craft:21,34-40,60`（宣言は :14） | `writing-ecosystem` + `style-diagnostics.md` | 各 skill から削除。宣言を守れているのは `prose-translation` のみ |
| **3f** | 「過去を天井にしない」。`title-reviewer:72` ≡ `theme-reviewer:38`（別表現、正本未宣言） | `theme-reviewer` | 正本を宣言し他はポインタ |
| **3g** | AI slop の二重保持。`editor:102` で外部化宣言 → `:105-109` で原則再掲 → `:246-259` で Good/Bad example | `writing-ecosystem:287` | 再掲と example 節を削除 |

---

## Tier 4 — 各ファイルの B 畳み

Tier 1-3 の後、残る足場を畳む。各ファイルの最重度 1 件のみ記載（全件は監査結果に基づき実行時に処理）。

| ファイル | 行数 | 最重度の B | 想定 |
|---|---|---|---|
| `collect-context/SKILL.md` | 275 | `:13-27` 責務宣言節。1 原則に列挙・ポインタ・設計弁明・例外・誤読防止が同居し、同内容が `:151-152`、`:261-262` にも散る。`:160-162` は Contemplative Agent の内部パスを埋め込み、**`:18-19` 自身の禁止（global skill が project の内部構造を知る状態を作らない）に違反** — 一般則「対象 repo の読み取り禁止経路に従う」は残し、project 固有のパス例だけ落とす | → 約 200 |
| `readme-writer/SKILL.md` | 266 | `:145-147` ですます弁明。「**将来の stocktake がこの差を「不整合」として逆修正しないこと**」は読み手ではなく監査への指示。`writing-ecosystem:433` に既に登録があるので弁明は両側にある | → 約 210 |
| `editor.md` | 270 | `:139-145` 「10% 編集を自己申告させない」worked example + canonical coverage の格上げ非該当の整合弁明 | → 約 170 |
| `essay-reviewer.md` | 242 | `:220-231` routing 規約の四重記述（description / `:20` / 独立節 + 表）。3 箇所とも否定形、`:222` に日付つき | → 約 150 |
| `fact-checker.md` | 191 | `:154-156` の F20 監査 ID と **別コンポーネント（hook の path glob）の欠陥説明**を ADR へ。**`:136-142` の機序 1〜2 文は D として残す** — `rules/common/security.md` が agent 定義を「実行される制御プログラム」と定義しており、この機序（transcript は tool 結果の逐語保存 = injection carrier / 読み戻すと WebFetch を持つ agent に他者テキストが再生される / その verdict が chain の CRITICAL stop）が禁止の自己執行力そのもの | → 約 155 |
| `prose-translation/SKILL.md` | 170 | `:24-25` skill 統合の経緯・統計（「本文の約 55% が同一で…」）。翻訳判断に効かない編集履歴 | → 約 140 |
| `session-theme-mining/SKILL.md` | 124 | `:121-123` 「設計参照した。依存はしない。」+ 回帰の作業報告。`THIRD_PARTY_NOTICES.md` が既に正本 | → 約 105 |
| `x-draft/SKILL.md` | 97 | `:17-21` 境界宣言に ban 事故史と設計弁明。原則は「投稿は必ず人間が行う」だけ | → 約 80 |
| `public-comment/SKILL.md` | 81 | `:14-16` 節全体が動機説明で行動を変える行が 0。出自の人名・日付を埋め込み | → 約 65 |
| `headline-craft/SKILL.md` | 77 | `:21` 反対証拠（CTR +2.3%）の先回り否定 + `writing-ecosystem` 感情語規約の逐語複製 | → 約 60 |
| `title-reviewer.md` | 72 | 「verdict を出さない」が `:3, :14-15, :41, :46, :64` の 5 箇所。frontmatter `replaces:` に改廃日 | → 約 60 |
| `quality-gate/SKILL.md` | 62 | `:61` 禁止列挙 + その対偶の正表現。**畳みしろ最小 = 目標形** | → 約 58 |
| `theme-reviewer.md` | 55 | `:3, :13-14, :54-55` の三重禁止 | → 約 48 |
| `prose-clarity-reviewer.md` | 84 | `:50-51` `Recurrent author finding (multiple articles)` 出自メタ。canon 側 `:208` と二重 | → 約 78 |

---

## 経緯の退避先

`~/.claude/docs/adr/0058-writing-harness-scaffold-dissolution.md` を新設（`adr-writer` skill 経由）。畳んだ日付つき経緯（2026-08-20 語りかけ指摘 / 2026-08-27 内容 GO / 2026-07 tech-idea 分岐廃止 / 2026-07-25 F20 / CA 2026-08-20 / 2026-08-19 棚卸し等）と、操作規則・`Review-when` を記録する。

注意: `docs/adr/` に既に **0057 が 2 本ある**（`0057-judge-tier-…` と `0057-verify-precommit-…`）。0058 を使い、衝突自体は本 pass のスコープ外として報告のみ。

`readme-judge-checklist.md` には既に「改定履歴」節があるので、readme-writer 由来の日付はそちらが受け皿。

---

## 触らないもの

- **zenn-content repo** — 文体規約は 2026-08-23（`45eb8fe`）に全削除済み。この repo が持つのは channel 表の Register 列と用語表と `zenn_evidence.py` だけ
- **paper 系**（`paper-ecosystem` / `paper-writing` / `clarity-reviewer` / `citation-formatter` 等）— 監査対象外。学術チャンネルは別の厳格性を持つので、記事系の溶解結果を見てから判断する

## 著者裁定が要る 1 件

`writing-ecosystem:357-365`「三段階の問い構造」の第 3 段 `:363`「議論途中の修辞的疑問」が 2 箇所と正面衝突している:

- `style-diagnostics.md:34` — 同じ結論を疑問形で繰り返さない
- zenn-content `publishing-channels.md:12`（Zenn register）— 修辞疑問で結論を弱めない

実行時に削除案として提示する。**推奨は削除**。主根拠は `:324-328`「結論の問い化」で必要な部分が既に覆われている冗長であること — channel contract との衝突を主根拠にすると、channel が canon を変形させる形になる。`style-diagnostics:34` との衝突は厳密には部分衝突（あちらは「同じ結論の疑問形反復」の禁止）なので、副次的な根拠として扱う。

## 検証

1. `~/.claude/.claude/verify.sh`
2. `scripts/hooks/harness_lint.py` — origin / rationale / review-when の存在検査
3. 参照切れ — `grep -rn "writing-ecosystem/SKILL.md#" --include="*.md" ~/.claude` と、被参照 4 ファイル（`title-reviewer` / `essay-reviewer` / `headline-craft` / `x-draft`）が名指しする節名の grep
4. **解像度の回帰テスト（最重要）** — `zenn-content/articles/` の直近公開稿 1 本に対し、溶解前後の `editor` / `prose-clarity-reviewer` / `essay-reviewer` を fresh context で走らせ、findings の件数と具体性を比較する。落ちた項目があれば、それは B ではなく D だったということ。その項目だけ復帰させる
5. **挙動の確認（verdict 非発行系）** — `title-reviewer` と `theme-reviewer` は Tier 4 で禁止の反復を削る（5 箇所 / 3 箇所）。この 2 本の核心性質は挙動（推薦・順位・verdict を出さないこと）で、findings 件数では測れない。溶解後に 1 回ずつ走らせ、推薦や順位が出ないことを確認する。反復が遵守率のための意図的配線だった可能性があるので、無検証で畳まない
6. 著者通読 — 溶解後の `writing-ecosystem/SKILL.md` を頭から読み、各原則が問いを起こすか確認
7. `harness-sync` で公開 repo へ同期

## 実行順

着手前に 1 回だけ: `rules/common/skills.md` が「skill / agent を新規作成・大幅改修するときは、書く前に skill: `skill-creator` を読む」を命令形で配線している。Tier 1a（`writing-ecosystem:200-253` の書き直し）と Tier 3a（reference 新設）が大幅改修に該当しうるので、適用可否を判断して記録する。

Tier 2（実害）→ Tier 1（canon）→ Tier 3（複製）→ Tier 4（各ファイル）。Tier 2 は独立で小さいので先に片づける。Tier 1 を Tier 3・4 より先に置くのは、canon が変わると下流の複製が何を指すかが決まるため。各 Tier の終わりで検証 4（および Tier 4 では 5）を回し、解像度と挙動が落ちていないことを確認してから次へ進む。

# ADR-0019: ヒューマンゲートの第 2 軸 — artifact は機械 / intent は人間、提示物は対象で分岐

## Status

superseded by [ADR-0035](0035-commit-review-hook-and-rules-rightsize.md) — custom human gate と
2介入点モデルを退役し、task request と substrate の既定へ委譲

## Date

2026-07-25

## Context

このハーネスの持ち主は**実装コードの diff を逐一読まない**。artifact 層の検証（成果物が正しいか）は
lint / hook / review agent / テストに降ろす方針で、手厚いレビュー体制はそのための投資である。
人間のゲートはもう一段上 — 何を志向し、結果として何がどう変わるか — に置かれている。

この方針は思想層では一貫していた。[`coding-style.md`](../../rules/common/coding-style.md) 判定 3 問の
「品質を機械検証できるか」が Yes なら人間を呼ばない、現在の
当時の `when-code-when-llm` skill の
enumerate/decide seam、[ADR-0010](0010-context-sync-cascade-and-writer-agents.md) の
「artifact 検査は git diff による事後検証へ降ろす」、[ADR-0016](0016-writer-agents-render-not-decide.md) の
「承認対象は生成物でなく decision packet」— いずれも同じ方向を向く。

**問題は、ゲートの軸が 1 本しか命名されていなかったこと。** `coding-style.md` の Reversibility Gate は
「**いつ**止まるか」（可逆性）を規定するが、「止まったとき人間は**何を**判断するか」（層）には正本がなかった。
そのため各実装が自分の解釈でその空白を埋め、次の 2 つが起きた。

**1. 第 2 介入点の正本が 2 つに割れた。**

| 正本 | 記述 |
|---|---|
| `rules/common/planning.md:82` | 「Verify 結果確認 — コミット直前」（提示物が未規定） |
| `skills/implementation-chain/SKILL.md:122` | 「公開・deposit・commit 直前の **diff 承認**」 |

起点は [ADR-0009](0009-implementation-chain-front-loaded-in-plan.md) に記録されたユーザー発言
「コミット前に最終チェックを私がするだけ」— 対象を規定しない一文が、後段で「diff 承認」と解釈された。

**2. artifact 残滓が 5 箇所に散った。** `implementation-chain`（diff 承認）/ `readme-writer`（diff を人間が
承認して適用）/ `release-doi`（HF commit 時刻の前後比較を「目視」）/ `paper-deposit`（PDF を eyeballed）/
`harness-sync`（`git diff` がレビューゲート）。個別に直しても、正本がない限り次に書かれる skill が同じ空白を埋める。

なお `rules/` は同日 [ADR-0018](0018-rules-rightsize-for-claude5.md) で rightsize したばかりであり、
本 ADR はその直後にファイルを 1 本増やす判断になる。

## Decision

1. **`rules/common/human-gate.md` を新設し、第 2 軸の正本とする。** 可逆性軸は
   `coding-style.md` Reversibility Gate のまま、層軸を新ファイルが持つ。

2. **artifact 層は機械が持つ。** 成果物の正しさは決定論ゲートと review agent が検査する。
   ただし **review agent は検査者であって承認者ではない** — LLM judge は generator–verifier gap
   （提案者と検査者が同一システムなら検査は提案者の盲点を継承する）を持つため、
   承認は「決定論ゲートの PASS」＋「人間の intent 判断」で構成し、LLM 単独の承認経路を作らない。

3. **ゲートの提示物は対象で分岐する。**
   - **behavior-shaping artifact**（rules / skills / identity / 憲法 / 公開ドキュメント）と
     **control plane**（hooks / `permissions` 設定 / `--allowedTools` 等の権限定義 / scheduled task 定義）
     → **本文を提示**。前者はテキストが意図そのもの、後者はゲートそのものを動かすため
   - **実装コード・生成物** → **意図の要約**。diff 本文と機械チェックの PASS 一覧は提示しない
   - **FAIL は例外** — 決定論ゲートが FAIL したときは検出行そのものを提示する。偽陽性判定
     （`security.md` の `*_BYPASS`）は人間にしか下せず、証拠なしに bypass を決めさせない

4. **意図の要約は介入点 1 で承認した plan と照合する。** 自由記述として読ませない。
   照合先を人間由来の referent に固定しないと、人間は提案者自身の自己申告を検証することになり、
   gap が artifact 層から語りの層へ移るだけになる。

5. **`planning.md` の第 2 介入点を「Verify 結果確認」から「意図確認」に改名**し、
   `implementation-chain` 側の記述を同じ 2 区分に揃える。

6. **新語は coin しない。** `harness alignment`（[AKC ADR-0017](https://github.com/shimo4228/agent-knowledge-cycle/blob/main/docs/adr/0017-harness-alignment-and-drift.md) / DOI 10.5281/zenodo.20578272）と
   `line of approval`（AKC glossary）に anchor し、定義本文は複製しない。

### companion paper との整合

`Harness Alignment and Harness Drift`（DOI 10.5281/zenodo.20578272）§2.1(b) はゲートを
「the proposing system produces **a diff or proposal** and stops, and the operator **reviews**, edits if
needed, and commits」と定義し、§6.2 は gate complacency への構造的防御として
「a diff reviewed, possibly edited, and committed under the operator's name」を挙げる。
決定 3 の「意図の要約」は、一見この定義と衝突する。

衝突しない理由は、**論文 §5 のゲートが behavior-shaping write に限定されている**こと
（episode log / knowledge store への書き込みは承認不要、rule / skill / identity は sign-off 必須）。
決定 3 の第 1 区分はこの範囲を**そのまま維持**し、第 2 区分（実装コード）は元々論文のゲート対象外である。
加えて、rule / skill / identity の diff は「実装の差分」ではなく「意図そのものの本文」なので、
それを読むことは論文が要求する articulation を弱めない。**論文の改訂は不要**と判断した。

## Alternatives Considered

### (a) 正本を立てず、5 箇所の文言だけ直す

最初に採ろうとした案。最も軽く完全に可逆だが、**病因（第 2 軸に正本がないこと）を残す**。
実際に 5 箇所で同じ空白の埋め方が独立に起きており、次に書かれる skill でも再発する。**却下**。

### (b) 第 2 軸に新しい概念名を coin する

`value layer engineering` / `harness alignment` を新語として立てる案。調査の結果、
**両語とも既に公開済み**だった — 後者は AKC ADR-0017 で coin され DOI 付き論文の題名、
前者は hub の through-line `value-layer harness engineering` として concept page / vocab URI /
graph / index.html の 4 面に固定済み。短縮形を新たに立てると canonical 名と競合し、
authorship-strategy ADR-0010 Vocabulary Discipline（Coin Sparingly, Anchor Densely）に抵触する。
さらに AKC ADR-0017 は "value" を AI-safety value-alignment との誤読リスクとして明示排除している。**却下**。

### (c) rule を論文に合わせ、常に diff を提示する

公開済み定義との整合は完璧になるが、**実践（実装コードの diff を読まない）と記述の乖離が残る**。
乖離した rule は守られず、drift の震源になる（[ADR-0014](0014-retire-multi-agent-orchestration-rule.md) で
実証済みの失敗モード）。**却下**。

### (d) AKC 側に先に concept / ADR を立てる

原則の正本を AKC（DOI 登録済み）に置き、harness の rule はその運用版とする案。
筋は通るが、AKC 自身の `.notes/TASKS.md` T3 が「**対称性論証では ADR を立てない**
（観測事例が n を満たすまで再提起しない）」という証拠基準を課している。本 ADR の根拠は現時点で
5 箇所の残滓という harness 内部の観測に留まるため、**運用実績の蓄積を先にする**。今回は harness 側に留めた。

**追記（2026-07-26、AKC 側で検証して確定）**: 却下理由は「証拠が足りない」ではなく
**「AKC に既出であり、新しい judgment ではない」**だった。層軸は position paper §5
（"What can be verified without the operator runs unattended; every change that shapes behavior
passes the gate, and intent enters the loop with it"）、AKC glossary の `line of approval`、
AKC ADR-0005:86-90（generator–verifier gap /
no approved-by-the-LLM path）に既に存在する。本 ADR は論文 §5 が "first instance"（著者の日常運用、
self-attested）と呼ぶものの**実装記録**にあたり、instance は pointer page を持たない — 証拠として
引かれる側である。決定 3（提示物の分岐）は operator content で、AKC の mechanism-only inclusion rule
により対象外。したがって**この選択肢は恒久的に却下**であり、条件付きの保留ではない。

## 追記（2026-07-28）: 記事化の過程で見つかった 5 つの穴

本 ADR の内容を Zenn 記事として外部向けに書き直す過程で、cross-model review（codex）と
読者視点のレビューが、決定 2・3・4 の穴を 5 つ検出した。いずれも rule に反映済み。

1. **証拠を作るものが分類から漏れていた。** 決定 3 の control plane は hooks / permissions /
   `--allowedTools` / scheduled task に限定されていたが、**テスト / fixture / lint 設定 /
   カバレッジ閾値 / CI 定義 / review agent の prompt / 依存**も機械の判定を弱められる。
   テストを実装に合わせて書き換えれば、**嘘をつかずに「全件 PASS」と要約できる**。
   control plane と同じ本文提示側へ移した。検出は決定論ゲート化した
   （`hooks/evidence-file-notice.sh`、PreToolUse。パスで決まる構造的性質なので code が持つ
   — 当時の `when-code-when-llm` skill にあった Code vs LLM seam。同 global skill は ADR-0035 で退役）。
   block ではなく `additionalContext` — 「触るな」ではなく「本文を併記せよ」の規約であり、
   完全な分類器ではない（通常コード内のテスト・独自ディレクトリ・lockfile を取り逃す）。

2. **不可逆性による昇格規則が無く、決定 3 と本 ADR の Consequences が矛盾していた。**
   決定 3 は「対象の種類だけで決まる」としていたが、同じ実装コードでもデータ移行・権限・課金・
   外部公開・削除処理・鍵ローテーションでは提示物が変わる。**第 1 軸（可逆性）は第 2 軸を
   上書きする**という昇格規則を追加。第 3 の軸は立てない。

3. **「成果物の正しさは機械が持つ」が広すぎた。** build / types / lint / tests / secret scan が
   示すのはカバーしている性質のみで、認可・並行性・不可逆な副作用・未実装の要件は全 PASS のまま通る。
   **「機械化された検査で判定できる正しさ」**に限定し、**一次責任の割り当てであって保証ではない**
   と明記した。残余リスクは昇格規則（2）で受ける。

4. **意図の要約が自由記述のままだった。** 決定 4 は「plan と照合する」までで、実装中の発見による
   plan からの逸脱が要約から静かに消える経路が残っていた。**固定 5 フィールド**
   （`承認済み意図` / `実現した変更` / `plan との差分` / `ユーザー・運用への影響` / `証拠側の変更`）に
   し、`plan との差分` を **なし / あり / 再承認が必要** の 3 値必須にした。逸脱そのものは
   悪くない — 逸脱が消えることが危険。

5. **「見せない」と「残さない」を区別していなかった。** 決定 3 の「PASS 一覧は提示しない」が
   証跡の破棄と読まれうる。**承認画面から退避させるが機械可読ログには保存する**を明記。
   あわせて FAIL 例外に**秘密の実値のマスク**を追加（真陽性の検出行をそのまま出すと、
   ゲートが防ぐはずの漏洩を会話・承認画面・ログへ広げる）。

常駐コスト: `human-gate.md` は 145 → 約 330 words。`rules/common` 全体は 2,756 → 約 2,940。
[ADR-0018](0018-rules-rightsize-for-claude5.md) の rightsize 水準（2,463）からは離れるが、
固定スキーマは**毎回発火するゲートの手順**であり、skill の確率的トリガーに委ねると守られない
（[`skills.md`](../../rules/common/skills.md) の Rules vs Skills 判定）。

副産物: 本 ADR の 2026-07-26 追記が引く position paper §5 の引用は、AKC glossary 経由の
**言い換えを引用符に入れたもの**だった（原文の "every change that shapes behavior" が
"every behavior-shaping change" に圧縮され、"and intent enters the loop with it" が
省略記号なしで脱落）。**対応済み（2026-07-29）**: AKC 側は glossary + llms-full.txt を
verbatim 復元済み（AKC CHANGELOG に記録）、本 ADR の引用も同日原文に揃えた。

## 追記（2026-07-29）: substrate 照合監査による縮退 — 層分離・列挙退避・スキーマの縮退

Claude 5 substrate（現セッションの system prompt + tool descriptions）と Anthropic の context
engineering 指針（[ADR-0018](0018-rules-rightsize-for-claude5.md) が引く Thariq 記事）に対して
`human-gate.md` を条項単位で照合した（conflict / redundancy / drift 分類）。**hard conflict は 0**。
検出は redundancy 5 件・tension 1 件で、以下を縮退した。strip 後常駐 265 → 125 words（-53%）。
動機: この rule の目的は「人間がボトルネックにならず intent 判断に認知資源を集中させる」ことであり、
rule 自身が常駐と形式強制でモデル・人間の注意を消費しては本末転倒（ユーザーの明示判断）。

1. **根拠 prose の層分離** — 「なぜ」「例示」「両立論証」「anchor 段落」を rule から削り、本 ADR への
   ポインタに畳んだ。規範の意味は不変。harness alignment / line of approval への anchor は
   ファイル先頭の `rationale:` コメント（注入時 strip、常駐コストゼロ）へ移設。
2. **列挙の退避（redundancy）** — 証拠生成物 7 種の列挙（テスト / fixture / lint 設定 /
   カバレッジ閾値 / CI 定義 / review agent の prompt / 依存）は `hooks/evidence-file-notice.sh` が
   決定論検出 + 発火時の指示注入で既に運ぶ（Thariq シフト 4「重複は発火点側へ一元化」の最強該当）。
   昇格規則の例示 5 種（データ移行 / 権限・課金 / 外部公開 / 削除処理 / 鍵ローテーション）と
   control plane の詳細列挙（`--allowedTools` / scheduled task 定義）は substrate の
   「hard to reverse or outward-facing → confirm first」判断で分類できるため、本 ADR にのみ残す。
3. **「見せない ≠ 残さない」条項を削除（redundancy）** — harness は transcript・tool 結果を常時
   機械可読で永続化しており、substrate 既定の再宣言だった。趣旨（承認画面から退避しても証跡は
   残り、監査・障害調査・再現に使える）は追記 5〔2026-07-28〕に既載。
4. **「1 作業 1 ゲート」条項の追加**（rule には圧縮形のみ常駐）— 意図確認は作業単位の完了点に
   1 回だけ立て、中間 phase・中間 commit ごとに承認を求めない。根拠: ゲートの細分化は attention を
   浪費し、承認をノイズ化して gate complacency を招く。`coding-style.md`「承認は batch 化で
   償却されない」とは両立する — あの条項が禁じるのは**暗黙の** N 件であり、件数とスコープを明示
   列挙した N 件を 1 回の承認で通すことはこの rule の意図そのもの。substrate の autonomy 既定（proceed
   without asking / Stop only for destructive actions or genuine scope changes）と同方向のため、
   rule には固有部分（完了点 1 回・明示列挙して 1 回の承認・例外 2 つ）のみ残した。
5. **固定 5 フィールドスキーマ → 差分宣言 1 点必須に縮退**（追記 4〔2026-07-28〕の再審議）—
   worst case（plan からの逸脱が要約から静かに消える）を防いでいるのは `plan との差分` の
   3 値必須宣言のみ。宣言を強制すれば**省略が虚偽に変わる**、という核だけが判断委譲できない
   （Thariq シフト 1 の「worst case が許容できない領域」留保に該当）。他 4 フィールド
   （`承認済み意図` / `実現した変更` / `ユーザー・運用への影響` / `証拠側の変更`）は要約の型であり、
   substrate の較正原則（Lead with the outcome / Report outcomes faithfully / match the response
   to the question）が既に運ぶ。固定フォームは 1 行 chore にも 5 見出しを強制する点で substrate と
   摩擦していた（照合で検出した唯一の tension）。`証拠側の変更` は hook 検出 + 本文提示規約が
   構造的にカバーする。3 値宣言は enumerated で機械可読なので、将来 hook による存在検査に落とせる
   （`patterns.md` documented-invariant → ゲート化）。「毎回差分なしを読み流す運用になったら
   不可逆な領域に絞って plan の粒度を上げる」という運用ガイダンスは rule から本追記へ移設。
   参照 2 箇所（`planning.md` 介入点 2 / `implementation-chain` SKILL.md 人間 gate 節）を
   「固定スキーマ」から「`plan との差分` の 3 値宣言必須」に同期した。

## Consequences

### Positive

- 第 2 介入点の正本が 1 つになり、`planning.md` と `implementation-chain` の食い違いが解消する。
- 新しい skill を書くとき、ゲートで何を提示するかを**対象から機械的に決められる**。
  「人間が diff を読む」を既定にする書き方が、原則違反として検出可能になる。
- `harness-sync` の `git diff` レビューが**残滓ではないと確定**した（対象が skills / rules =
  behavior-shaping artifact であり、本文を読むことが intent 層の作業）。一律の削除を避けられた。
- review agent の位置づけ（検査者であって承認者ではない）が明文化され、
  AKC ADR-0005 の generator–verifier gap 条項と harness の実装が接続された。

### Negative

- **ADR-0018 の rightsize 直後に常駐が +145 words 増える**（`common/` は 2,252 → 2,397 words）。
  この内容は決定論ゲートに落とせない（提示物の選択は意味的判断であり、
  当時の `skills/learned/documented-invariant-lint-gates.md`（2026-08-23 に learned/ ごと退役、[ADR-0047](./0047-retire-learned-notes-directory.md)）の
  「文書化された不変条件はゲートに落とす」を適用できない）ため、
  rule に置く以外の選択肢がない。
- **「behavior-shaping artifact か否か」の判定自体が意味的**であり、境界事例（生成ドキュメント、
  設定ファイル、テストコード）では判断が要る。決定 3 は列挙で例示するが、網羅はしていない。
- ~~**AKC への昇格が未了**のため、harness 側 rule と AKC の concept 体系が将来 drift しうる。~~
  **解消（2026-07-26、T-009）**: 昇格しないことが確定したため、drift リスクは「別々の正本が
  並存する」形では発生しない。本 rule は AKC concept の**運用インスタンス**として位置づけが固定された。
  検証の副産物として AKC 側に 1 点の実質的欠落が見つかり、還元済み — **control plane**
  （hooks / permission 付与 / scheduled task 定義）が `line of approval` の承認必須側の列挙に
  無かった。判定基準（"artifacts that shape future behavior"）は満たすのに列挙から漏れていたため、
  基準からの導出として AKC glossary + graph.jsonld を sharpening（AKC commit `14c995b`）。
  ADR は立てていない（不可逆でない / 驚きでない / 実在するトレードオフがない）。

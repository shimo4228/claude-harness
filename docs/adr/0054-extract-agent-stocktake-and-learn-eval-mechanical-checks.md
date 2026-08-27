# ADR-0054: agent-stocktake と learn-eval の機械チェックを evidence script へ抽出し、自己申告を成果物に置き換える

## Status

accepted

## Date

2026-08-26

## Context

skill: `review-to-lint`（[ADR-0051](./0051-extract-mechanical-adr-checks-into-cross-repo-lint.md)
Decision #6 で一般化した抽出手続き）の適用である。対象は RFC-0007（agent-stocktake）と
RFC-0010（learn-eval）で、分業線が同一なので 1 ADR にまとめる。

**通し番号は付けない**: 本 ADR・[ADR-0052](./0052-url-liveness-and-usage-aggregation-evidence-scripts.md)
（RFC-0008 / 0009）・[ADR-0053](./0053-extract-context-sync-checklist-into-evidence-script.md)
（RFC-0006）は同じ base から並行セッションで実施され、順序関係が無い。初稿はこれを
「2 件目・3 件目」と書いたが、0053 は自身を「適用第 1 号」と記しており、両立しない —
並行実施を逐次の連番で語れないというだけのことで、どちらかが誤りなのではない。
水平展開の台帳は RFC-0005 が正本。

ADR-0051 Decision #6 は「他の reviewer への適用は **1 件ずつ別セッション**で行う」と
書いた。本セッションは 2 件を同時に扱っており、これは 0051 の当該条項を**狭める**。
根拠は分業線の同一性（どちらも「列挙 = code / 判定 = LLM」で、置き換える対象が
自己申告 1 種）であって、一般に束ねてよいという主張ではない。0051 側にも日付つき注記
を追加した。

agent-stocktake Phase 1 は自ら「機械チェック」と呼ぶ 5 項目を LLM に実行させ、加えて
`wc -w` / `wc -l` を目視で回していた。learn-eval の grounding checklist の 2 項目
（`~/.claude/skills/` を keyword grep したか / MEMORY.md と重複しないか）は**実施したかの
自己申告**で、何と何を比べたのかが出力に残らない。しかも重複の照合先は
「将来のセッションが辿り着ける経路」であり、その経路は description が持つ
（[ADR-0047](./0047-retire-learned-notes-directory.md) が `learned/` を退役させた
理由も、内容の重複ではなく**到達性**——description trigger を持たないノートは
grep でしか届かなかった——だった）。何を比べたか残らない自己申告は、その到達性の
判断そのものを検証不能にする。

実測（2026-08-26、`~/.claude/agents` 全 25 本 / `~/.claude/skills` 全 67 本）は次の通り。

- name = filename stem の不一致 0 件、リスト外の tool 0 件。`tools:` の表記は 2 種混在
  （JSON list 23 本 / bare CSV 2 本 — prompt-forager, swift-reviewer。計 25 本で、
  `tools:` が無い agent も parse 不能な agent も無い）。MCP tool は scout.md の context7
  2 件のみで、server は設定済み。
- description の近似重複: 全 300 ペアの分布は editor / essay-reviewer が 0.525、次が
  clarity-reviewer / prose-clarity-reviewer の 0.319 で、その間に明確な gap がある。
- suppression 文言: 英語パターンの該当は `agents/refactor-cleaner.md:75`
  （"**Be conservative** -- when in doubt, don't remove"）の 1 件のみで、これは握り潰し
  指示というより framing である。**唯一の明確な該当は日本語**
  （`agents/security-reviewer.md:91`「残った指摘に確信度を付け、低いものは捨てる」）。
  agent-stocktake の checklist は英語の言い回しだけを例示しているので、英語限定の
  catalog では明確な該当を 1 件も拾えなかった。
- ALWAYS/NEVER: script が走査するのは **body だけ**で、候補は 1 件
  （`agents/prompt-writer.md:19`）。しかもそれは指示ではなく**引用された語彙**
  （「使うな」の列挙）である。description にも 1 件ある（`agents/swift-reviewer.md:3`
  の "MUST BE USED"）が、description は agent への指示ではなく delegation trigger
  なので走査対象から外してある（description の質は近似重複側が見る）。
- skills corpus に YAML block scalar の description が 1 件（`skills/paper-deposit/SKILL.md`
  の `>-`）。素朴に読むと値が `>-` になり、その skill が全 overlap 比較から無言で脱落する。

既存検査との境界（再実装しないもの）は次の通り。`scripts/hooks/harness_lint.py` の
`lint_agents`（frontmatter 必須 field と model alias）と `lint_markdown_links`
（`LINK_SCOPES` に `agents` を含む）、`skills/skill-health/scripts/scan_refs.py`
（scan root が skills tree で agents/*.md は対象外）。agents 本文の**素の path 記述**
（link 記法でない `~/.claude/hooks/foo.sh` 等）はどちらも未カバーで、LLM 側に残す。

## Decision

1. `skills/agent-stocktake/scripts/agent_evidence.py` を新設する（uv sub-project +
   tests）。既定は evidence モード — JSON を stdout に出し、findings が何件でも exit 0、
   corpus を読めないときだけ exit 2。`adr_lint.py` と違い **`--gate` を持たない**:
   stocktake は定期監査であって commit 境界の検査ではない（ADR-0051 Decision #2 の判断を
   そのまま継ぐ）。検査項目は desc_words / body_lines / total_desc_words、name =
   filename stem、`tools:` の各 tool の builtin / unverified / mcp 分類（mcp は
   `~/.claude.json`・`~/.claude/.mcp.json`・repo の `.mcp.json` を照合先にする）、
   description 近似重複、suppression 候補と ALWAYS/NEVER 候補の行番号つき列挙。

   分類の言葉を 2 つ弱める。埋め込みリストに無い tool は `unknown` ではなく
   **`unverified`**（「この dated list に無い」であって「存在しない」ではない — 真の
   registry は runtime にしかなく、それを持つのは読み手の LLM の方である。実測で
   stamp 当日に 8 件漏れていた）。MCP は `server_configured` ではなく
   **`server_in_config`**（connector 由来の server は設定ファイルに現れないので、
   false は「retired」を意味しない。実測 2026-08-26 で 6 namespace がセッションに
   生きていながら設定ファイルに不在）。どの設定ファイルが読めて parse できたかは
   `registry.mcp_config_files[].status` に出し、1 つも `ok` でなければ判定は
   `null` にする — 読めなかった設定から「未設定」を作ると、正しい agent に対する
   Update evidence を捏造することになる。
2. `skills/learn-eval/scripts/overlap_candidates.py` を新設する（uv sub-project +
   tests）。draft を受け取り、installed skill の **description**（本文ではない —
   将来のセッションを routing するのは description であり、本文一致は誰も辿り着かない
   skill を上位に出す）と MEMORY.md の index 行を、draft の語との重なりで順位づけて
   行番号つきで返す。同じ evidence 契約。判定（Save / Improve then Save / Absorb /
   Drop）は従来どおり learn-eval Step 5b が持つ。
3. 免除境界のフラグは**置かない**。ADR-0051 は `--sections-from` 等を gate 用に用意したが、
   本 ADR の 2 script は gate を持たないため「初日に赤くなる」現象自体が存在しない。
   境界の代わりに置いたのは**閾値の実測**で、description 近似重複の既定は 0.5 とする —
   実測の gap（0.525 と 0.319 の間）に置き、実在する 1 ペアだけを出して残り 299 ペアを
   黙らせる値。
4. 類似度は token-set（stopword 除去後の語集合）で測る。agent 側は Jaccard、learn-eval
   側は containment（候補側の語のうち draft が使っている割合）— draft は数段落、
   description は 1 文なので Jaccard では union が draft に支配されて実在の重複が 0 に
   潰れる。stdlib のみで、rapidfuzz は採らない（後述）。
5. suppression catalog は**日英両方**を持つ。実測で唯一の明確な該当が日本語だったため。
   パターンは実測で削る — 削除したのは次の 2 つで、どちらも偽陽性だけを産んだ:

   - `only-report` = `\bonly report\b|\breport only\b|\bonly (?:surface|flag|raise)\b|\bat most \d+ (?:findings|issues)\b`
     — `agents/fact-checker.md:164`（"Only report findings." = agent 自身の出力契約）と
     `agents/readme-reviewer.md:13`（"the only surface a grounding-path LLM can
     reliably assume" — `only surface` に当たった散文）の 2 件。
   - `report-exclusion-ja` の `に限定` 択一 — `agents/readme-judge.md:79`
     （「評価は欠陥検出に限定し」= 評価対象の範囲の記述）の 1 件。

   候補は 8 件から 5 件になり、うち 1 件が明確な該当。残る 5 件の内訳は Decision #6 の
   実行座標が読む値で、SKILL.md には複製しない。

6. 薄化: agent-stocktake の Phase 1 機械 5 項目と目視カウントを Phase 0（script 実行 →
   JSON を findings に転記 → 目視で数え直さない）へ置換し、harness_lint が持つ 2 項目は
   「その出力を読む」ポインタとして残す。learn-eval は grounding checklist の重複照合
   2 項目を Step 5a-0（script 実行 → 候補を 1 件ずつ「本当に同じ知識か」で裁く）へ置換し、
   semantic 3 項目（既存 skill への追記検討 / 再利用性 / 観測記録への接地）は残す。
   「grep した」は checklist の有効な回答ではなくなる。有効な回答は 2 つの corpus で形が
   違い、SKILL.md はそれを分けて書く: skill 側は description が約 30 語あるのでスコアが
   広がり（実測の分離は 0.600 対 ≤0.143）「上位が ~0.2 未満に固まっている」が根拠になる。
   MEMORY.md の index 行は 3〜8 語しかなく `_containment` の分母が小さいためスコアが
   暴れる（実測: 1 語一致の 0.167 が、真の一致より上に来た）ので、閾値でなく**共有概念数**
   を signal にし、script 側が 1 概念しか共有しない行を落とす
   （`MIN_SHARED_MEMORY_TERMS = 2`。実測で真の一致は 4 概念、偽の候補は全て 1 概念）。

   **「語数」でなく「概念数」なのは日本語のため**（Decision #9）。
7. file reader（`_read_text`）・frontmatter reader（`split_frontmatter` /
   `front_scalar`）・tokenizer（`normalize_terms` / `count_concepts`）を 2 script に
   **複製**する。共通化しない理由: uv sub-project は互いに独立で cross-import に path
   hack が要り、両者とも `dependencies = []` を保っている。feedback:
   duplicate_over_coordination と、`skills/skill-health/scripts/scan_refs.py` が
   `readme_evidence.py` から mirror している先例に従う。

   複製の規模は**約 70 行**で、初稿が書いた「約 15 行の tokenizer」ではない（レビュー
   実測で 47 の同一行）。加えて 2 つの stopword 集合は**初日から一致していない** —
   learn-eval 側だけが散文 filler 15 語を持つ。これは意図的な差で、agent 側の
   `DEFAULT_DUP_THRESHOLD` が短い description の分布で較正されているため（同期すると
   最上位ペアが 0.525 → 0.517 に動き、閾値が座る gap が狭まる）。規約は「同期する」では
   なく「共有ブロックは byte 一致を保ち、差分は `_PROSE_STOPWORDS` という名前を持つ
   1 箇所だけに置く」。この複製が実際に破れた実例が本 diff にある — `_read_text` を
   `(text, reason)` へ変えたとき片側の呼び出し 1 箇所を落として crash した
   （code review が検出）。
8. skill-stocktake Phase 3 との共通化は**行わない**。手法は同型に見えるが形が違う —
   Phase 3 は library 全体の N×N クラスタリング（set property、専任 agent が判定）、
   本 script は 1×N（1 draft 対 library）。共有できるのは tokenizer だけで、それは #7 で
   複製とした。N×N への拡張が要るなら skill-stocktake 配下が正本（本 diff は
   skill-stocktake の SKILL.md に触れない）。

9. **語の切り出しは ASCII 語 + CJK 文字 bigram**、ただし**閾値と順位は「概念数」で数える**。
   `_WORD_RE` は ASCII しか拾わないので、日本語だけの draft / description / MEMORY.md 行は
   語が 0 個になり、全てに対してスコア 0 =「重複なし」と報告されていた（cross-model
   review が検出）。bigram を足すと拾えるが、今度は n 文字の単語 1 個が n-1 個の「語」に
   なり、無関係なカタカナ語 1 つが 2 概念の floor を越えて真の一致を追い越す（実測: draft
   の真の帰属先が「パーミッション」1 語に負けて 3 位、さらに 2 語足すと圏外）。そこで
   `count_concepts` を置き、候補行側の CJK run 1 つにつき 1 概念と数える（bigram の連鎖
   ではなく候補テキスト側で数えるのは、共通部分集合では連鎖に穴が空くため）。修正後は
   同じ実測ケースで真の一致が 1 位に戻り、カタカナ 1 語の候補は圏外になった。
   agent corpus は英語なので近似重複の gap（0.525 / 0.319）は bigram 導入前後で不変。

## Review-when

- agent_evidence の生存条件: 連続 2 回の stocktake で、**候補ではなく確定した findings**
  （verdict を動かした転記）が 0 件だったら、counting だけの one-liner へ退役させる。
  候補件数では測らない — `security-reviewer.md:91` は当該ファイルを直すまで毎回出る
  standing な真陽性で、候補が 0 になることは無い。cadence は
  `skills/agent-stocktake/results.json` の commit 間隔（実測 2026-07-27 → 2026-08-23、
  約 1 ヶ月）なので、2 回はおよそ 2 ヶ月を指す。
- `BUILTIN_TOOLS` は as-of 2026-08-26 の凍結リストで、真の registry は runtime にしか
  ない。**この失効はすでに 1 度起きている**（初稿の stamp 時点で `EnterWorktree` /
  `ExitWorktree` / `Task*` 8 件が漏れていた）。Decision #1 はこれを受けて未収録名を
  `unknown` でなく `unverified` と呼び、SKILL.md の実行座標に「読み手が自分の tool
  registry で確認してから Update evidence にする」を配線した。stocktake が 2 回続けて
  `unverified` を偽陽性と判定したら、リストは自身の as-of 契約に失敗している —
  `--known-tools` 運用へ倒すか、判定そのものを外して列挙だけにする。
- `harness_lint.py` または substrate が agent 定義の lint を native に持ったら、
  agent_evidence と統合して削除する。
- overlap_candidates の生存条件: 低スコアなのに実在の重複が通ったら（語の重なりは同義語
  レベルの重複に盲目）、置き換えた自己申告より悪い「誤った安心」を与えている — その 1 件
  で再訪する。substrate が意味検索で skill / memory を引けるようになった場合も同様。
- `derive_memory_path` は Claude Code の project slug 規約（`/` `.` `_` → `-`）に依存
  する。規約が変わると照合先が消えるが、これは**無言では起きない** — 導出した path は
  存在しなければ `memory_files_missing` に載るので、`memory_files_read` が空で
  `memory_files_missing` が非空の JSON を見た時点が発火点。

## Alternatives Considered

### 外部ツール cclint の採用

search-first（as-of 2026-08-26）で照合した外部ツール
[cclint](https://github.com/carlrannaberg/cclint)（pre-1.0、npm、Node 依存）を採用する
案。却下: name = filename stem と unknown tool は確かにカバーするが、tool 実在の判定が
固定リストで**この harness の MCP 設定に照会しない**（server 実在の解決が要件の中心）。
description の近似重複・suppression 候補の列挙は非対象。加えて verdict を出す linter で、
evidence モード（判定しない・exit 0）の契約と合わない。Python 一色の verify 系に Node の
実行体を 1 つ増やすコストもある。未決ではなく却下 — 再訪条件: 上流が MCP 解決と evidence
出力を持ったとき。

### rapidfuzz / 類似の fuzzy matching 依存の追加

search-first（as-of 2026-08-26）で検討した rapidfuzz 等の依存追加案。却下: 語順に強い
token_sort 系は魅力だが、本件は 25 本 × 300 ペアで速度が問題にならず、token-set で
語順非依存は既に得られている。`dependencies = []` を保つ価値の方が大きい。

### checklist 項目を削るだけ（script を建てない）

learn-eval / agent-stocktake の該当項目を検査そのものから削る案。却下: learn-eval 側の
2 項目は捨てるべき検査ではなく、検証できない形で書かれていたのが問題。agent-stocktake
側も同様に、残った検査は実測で該当を出している。

### suppression / ALWAYS-NEVER の regex catalog を建てない

architect agent の指摘（2026-08-26）。architect は「候補 8 件中の真陽性 1 件は精度が
低く、corpus に一度も当たらないパターンを『再発を検知できないから』で残すのは YAGNI。
gate も hook も無いので監査間に走るものが無く、Phase 2 はどのみち全 body を 1 context に
読む」として、この 2 項目の削除を推した。**採らなかった** — RFC-0007 が Motivation と
Reference-level explanation でこの 2 項目を成果物として名指しし（「script が行番号つき
候補を列挙し、LLM は判定文だけ書く hybrid の教科書例」）、本セッションの kickoff packet
がそれを受入条件に置いている。名指しされた成果物を削るかどうかは実装セッションでなく
判断役の裁量であり、ここで黙って落とすと「省略」になる。ただし指摘の実質は取り込み、
偽陽性のみを産んだパターンを実測で削って候補を 8 → 5 に絞った（Decision #5）。

未決 — 再訪条件: 次回以降の stocktake で、`agents/security-reviewer.md:91`（当該行を
直すまで毎回出る standing な真陽性）**以外**から verdict を動かした findings が 2 回
続けて出なかったとき。候補件数では測らない — 件数が 0 になることは無い。

### `name_matches_stem` を `harness_lint.py` の `lint_agents` へ gate として移す

同じ architect 指摘で、adr-reviewer も独立に同じ結論に達した。判断としては妥当 —
判定の余地が無い不変条件で、`lint_agents` は既に同じ 25 ファイルを commit 境界で読んで
おり、`lint_skills` は同じ検査を skill に対して
`scripts/hooks/harness_lint.py:246` で既に行っている（agent 版が無いだけ）。

**本 diff では実施しない**。理由は設計判断ではなく作業境界で、その境界は RFC-0007 では
なく**本セッションの kickoff packet**（`harness_lint.py` 本体を変更しない / 必要と判明
したら実装せず findings に上げる）にある。つまりこの根拠は commit された成果物のどこにも
残らない — だからここに書いてある。

~~未決~~ — **採用済み (2026-08-27、RFC-0014)**。判断役が findings を採り、`lint_agents` に
5 行の gate として実装した (`scripts/hooks/harness_lint.py`、回帰は
`tests/harness-lint-precommit.bats` の 2 本)。`agent_evidence.py` 側の
`name_matches_stem` は同時に削除し、agent-stocktake SKILL.md Step 2 の
「gate が持つ検査」へ移した — 同じ判定を 2 箇所に残すと drift するため。

## Consequences

### Positive

- 「grep した」「重複を確認した」という検証不能な自己申告が、行番号と共有語を持つ成果物に
  置き換わった。主張が反証可能になった。
- 目視カウント（`wc -w` / `wc -l`）が決定論化し、トークンゼロで再現可能になった。
  近似重複は目視では 300 ペアを突き合わせていたわけではなく「似たものに気づく」だった
  ので、こちらは自動化というより**新設**である。
- block scalar の description を折り畳んで読むため、`skills/paper-deposit` が overlap
  比較から無言で脱落する既存の穴が閉じた（実装前には気づいていなかった穴で、実測で
  見つかった）。
- suppression 検査が bilingual になり、corpus に実在する唯一の該当を捕まえられるように
  なった。

### Negative

- uv sub-project が 2 つ増え、`pyproject` + tests + `uv.lock` の保守対象になる
  （ADR-0051 で 1 つ増やしたのに続く）。
- 約 70 行が 2 箇所に複製された（Decision #7）。drift は相互参照コメントでしか抑えて
  いない — 本 diff の中で既に 1 度破れ、片側の呼び出しを落として crash した。
- 日本語の扱いが「bigram で拾い、概念で数える」という 2 段構えになった（Decision #9）。
  形態素解析器を持たない代償で、`count_concepts` は候補テキストを再走査する。
- `BUILTIN_TOOLS` は日付つきの凍結データで、放置すれば偽の `unverified` を出す。
  `--known-tools` は逃げ道であって解決ではない。
- 語の重なりは同義語レベルの重複に盲目で、低スコアは「重複なし」の証明ではない。
  Review-when に失効条件を置いた。
- agent-stocktake の実行頻度そのものに観測が無い（`results.json` の ledger が唯一の
  証跡で、committed な実績が無い）。消費者が実在するかの証拠が弱い側の instrument である。

### Neutral / Follow-ups

- 新規ファイル: `skills/agent-stocktake/{pyproject.toml,uv.lock,scripts/agent_evidence.py,tests/test_agent_evidence.py}`、
  `skills/learn-eval/{pyproject.toml,uv.lock,scripts/overlap_candidates.py,tests/test_overlap_candidates.py}`。
  変更: 両 skill の `SKILL.md`。
- 分業原理の出所は [ADR-0021](./0021-rules-metadata-and-premise-lint-gates.md)（導入）→
  [ADR-0044](./0044-adr-review-when-and-dated-annotation.md) Decision #5（ADR への適用）→
  [ADR-0051](./0051-extract-mechanical-adr-checks-into-cross-repo-lint.md)（reviewer への
  適用と review-to-lint への一般化）。本 ADR はその系譜に連なる適用の 1 つで、
  ADR-0052 / ADR-0053 と並行（Context 冒頭の通り順序関係は無い）。
- `review-to-lint` の候補台帳は RFC-0005。

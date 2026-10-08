# ADR-0092: skill は invocation を先に決め、model-invoked の description を常駐ポインタとして書き、listing の幅を lint で数える

## Status

accepted — [ADR-0066](./0066-search-first-report-contract-and-scout-retirement.md) Decision 2 が決めた
search-first の description の形（6 種の発話例 + 総称句 + 別入口への routing）を部分的に置き換える。
[ADR-0067](./0067-skill-doctor-as-residency-cost-instrument.md) Decision 2（`/skill-doctor` の `context` を
residency cost の唯一の計器とする）を狭め、commit を止める 2 つ目の計器として listing 幅の lint を足す。
ADR-0066（Decision 2 と Review-when）と ADR-0067 に注記する

## Date

2026-10-09

## Context

Plan: [docs/plans/skill-description-pointer.html](../plans/skill-description-pointer.html)（承認 2026-10-09）

- 著者の問い（2026-10-09）「なんか私のスキルのDescription長すぎない？」。同日の実測（`skills/*/SKILL.md` の
  frontmatter を YAML で読んだ長さ）: 54 本（repo 外への symlink 2 本を含む）の description は合計 28,131 字、
  中央値 435.5 字、800 字超が 10 本。RFC-0017 の 25,238 字は agents を含む実効常駐の数なので比べられない。
  repo に commit された SKILL.md（symlink を除く）で数えると、2026-08-30（commit 92e8ece）の 57 本 26,738 字から
  変更直前の 52 本 27,105 字へ、本数が 5 本減ったのに字数は増えていた
- Claude Code 2.1.295 の本体（`~/.local/share/claude/versions/2.1.295` から `strings` で読んだ同梱 JS）:
  skill listing の予算は context window × 1 token あたりの字数（Claude 3〜4.6 の model id は 4、それ以外は 3）×
  `skillListingBudgetFraction`（既定 0.01）。window が分からなければ 200,000。env `SLASH_COMMAND_TOOL_CHAR_BUDGET`
  があれば予算をそのまま上書きする。1 行は `- name: description[ - when_to_use]` で、description 部を
  `skillListingMaxDescChars`（既定 1,536）で切る。幅は `Bun.stringWidth` で測り、全角は 2。予算を超えると、
  bundled と `skillOverrides: name-only` 以外を使用スコア `usageCount × max(0.5^(最終使用からの日数/7), 0.1)` の順に
  並べ、残り予算に収まる skill にだけ description を付け、残りは名前だけにする。`skillOverrides` は plugin 由来の
  skill には効かない。docs とブログの既定値は 0.1 / 0.15 / 0.01 と割れていた（調査 report
  `docs/plans/research/2026-10-09-skill-description-design.md` の Contradictions）
- この harness の測定（2026-10-09）: model-invoked 40 本の listing 幅は 24,203。Opus 5.5 を 1M window と仮定した
  予算 30,000（1,000,000 × 3 × 0.01）の 81%（24,203/30,000）で、plugin と claude.ai 由来の skill を足すと超える。
  1M window はこの session で直接は読んでいない。`claude -p "/skill-doctor"` では、読み込んだ 94 本のうち 45 本が
  description 付き、29 本が名前だけ、20 本が listing の外だった。名前だけの 29 本はほぼ一度も使われていない
  skill で、自前の loop-design-check（1,048 字）・mono-color・repair-discipline・jev-judgment-design を含む。
  使われない skill は名前だけになり、名前だけだと呼ばれにくいので、そのまま固定される
- Matt Pocock の mattpocock/skills（HEAD b0618bc、2026-10-08、`gh api` で原文を読んだ）:
  [`.agents/invocation.md`](https://github.com/mattpocock/skills/blob/b0618bc/.agents/invocation.md) は skill を invocation で二分する。user-invoked は `disable-model-invocation: true`
  で、description は人向けの 1 行、トリガー列なし。model-invoked は description にトリガーの分岐を書く。判定の問いは
  「モデルが自分で手に取って役に立つか」で、再利用は判定の基準ではない。
  [`writing-for-agents/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc/skills/productivity/writing-for-agents/SKILL.md) は description を常に読み込まれる「context pointer」とし、
  本文より厳しく刈る（leading word を先頭に置く、同じ分岐の同義語は 1 つに畳む、本文にある内容は書かない、否定より
  肯定）。38 本の測定: user-invoked 23 本は中央値 86 字、model-invoked 15 本は中央値 179 字・最大 417 字、否定の節は
  1 つ、他の skill への案内は 0。どれも英語だけで、発火率の数値は示していない
- ほかの資料（調査 report。`WebFetch` の要約経由なので数値は概数）: anthropics/skills の 11 本は中央値約 370 字。
  obra/superpowers の writing-skills は、description に手順の要約を書くと agent が本文を読まずに要約に従う、と
  作者のテストから書く（数値なし）。Skill Scaling Laws（arXiv 2601.04748、GPT-4o 系、5〜200 skill）は、選択精度を
  落とす主因を本数より skill どうしの意味の近さとし、説明の長さ（約 30 / 100 / 300 token）の差は誤差内とする。
  Claude 5 世代で description の長さ・否定の節・日英の併記の効果を測った研究は見つからなかった
- 先行: RFC-0017（使われない skill の description を `disable-model-invocation` で畳む）と RFC-0018
  （description は常駐する指示層）。skill-creator §2 の Trigger ceiling（2026-04-11、search-first の文言修正で
  自発発火が 27% から 8% に下がり戻した。分母は skill-creator §2 の記録に無い）

## Decision

1. skill の設計では invocation を先に決める。正本は `skills/skill-creator/SKILL.md` §3。問いは「モデルが自分で
   手に取って役に立つか、または rule / 他 skill が Skill tool で呼ぶか」。どちらでもなければ
   `disable-model-invocation: true` にし、description は slash menu 用の人向けの 1 行にする。rule や skill からは
   path で指せる
2. model-invoked の description は常駐ポインタとして書く。leading word を先頭に置く。分岐ごとにトリガーを 1 つ、
   著者が実際に打つ語で書く。文は英語にし、著者が日本語でしか打たない語だけを括弧で 1 回残す（同じ分岐を日英で
   2 回書かない）。手順・出力・verdict 名は本文に任せる。他の skill への案内は、実際に衝突する対だけ肯定形の
   1 節（"For X, use y"）で残す。skill-creator §1 の「著者の例文 3 つを verbatim で入れる」は「分岐ごとに 1 つ」
   に替える
3. `scripts/hooks/harness_lint.py` に `lint_skill_listing_width` を足す。model-invoked の listing 行を全角 2 で
   数え、1 本 400 を超えるか、合計 12,000 を超えたら違反にする（commit gate で止まる）。repo 外への symlink
   （hunk-review、mono-color）は編集できないので、合計にだけ数える。12,000 は予算 30,000 の 40%（12,000/30,000）で、残りを
   plugin と claude.ai 由来の skill に空ける。400 と 12,000 は plan で著者が選んだ値で、較正していない
4. 51 本の description を書き換える（model-invoked 35 本、user-invoked 16 本）。grill-me（slash 50 / invoke 15）と
   review-to-lint（slash 3 / invoke 0）を user-invoked に移す（著者の選択。数は `skills/skill-stocktake` の
   `scripts.usage_stats --days 120`）。archify は内容を編集したので origin を `tt-a1i/archify-customized` にする。
   外部 symlink の hunk-review と mono-color、外部 origin で 400 以下の herdr は変えない。決定 1 の問いを当てたのは
   model-invoked だった 40 本だけで、もとから user-invoked の 14 本は description を人向けの 1 行にしただけ。
   rule や skill から `skill:` の名前でそれらを指す既存の配線は見直していない。書き換え後の測定（2026-10-09、YAML で
   読んだ長さ）: description の合計 10,375 字・中央値 189.5 字、model-invoked 38 本の listing 幅 9,777。
   書き換えた model-invoked: adr-writer, archify, authorship-strategy, collect-context, context-sync, harness-sync, headline-craft, hf-sync, implementation-chain, jev-judgment-design, jsonld-knowledge-graph, learn-eval, llms-txt-writer, loop-design-check, measurement-discipline, mono-figure, prose-translation, public-comment, readme-writer, refactor-clean, release-doi, repair-discipline, repo-asset-stocktake, rfc-writer, rules-stocktake, search-first, skill-comply, skill-creator, skill-stocktake, spawn-session, task-stocktake, task-triage, verify-bootstrap, wiki-query, x-draft。user-invoked: agent-stocktake, author-calibrated-eval, generation-audit, grill-me, harness-boundary, jev-skill-router, llm-as-judge, mondo, prompt-perturb, review-to-lint, review-when-watch, rules-distill, session-judgment-mining, skill-health, wait-what, wiki-harvest
5. 変えるファイル: `skills/*/SKILL.md` の frontmatter 51 本（決定 4 の列挙。本文は変えない）、`skills/skill-creator/SKILL.md`
   の §1・§3・§4、`skills/skill-creator/MAINTENANCE.md`、`scripts/hooks/harness_lint.py`、
   `tests/harness-lint-precommit.bats`、`docs/adr/README.md`、ADR-0066 と ADR-0067 の注記

## Review-when

- Claude Code の listing の作り方（予算の式、幅の数え方、超過時の順位）が変わったとき、または skill に遅延読み込み
  や検索の仕組みが入ったとき — 決定 3 の閾値の前提が変わる。本体を `strings` で読み、`skillListingBudgetFraction`
  の周辺を確かめる
- 書き換え後の `/skill-doctor` で、自前の model-invoked skill が名前だけになっているとき — 合計 12,000 を下げるか、
  plugin と claude.ai 由来の skill を減らす
- 著者が「日本語で頼んだのに skill が呼ばれなかった」と気づいたとき — その分岐に著者の語を括弧で足す。2 本目の
  skill で同じことが起きたら、決定 2 の言語の方針を見直す
- Claude 5 世代で、description の長さ・否定の節・言語の効果を測った研究か計器が出たとき
- 書き換え前は自分で呼ばれていた skill が呼ばれなくなったと、著者が作業中に気づいたとき — その skill の分岐を
  見直す。`usage_stats` の invoke は自発の呼び出しと rule / skill からの配線を分けず、invoke が 0 に近い skill が多い
  ので、数の比較では判定しない

## Alternatives Considered

- **`skillListingBudgetFraction` を上げる** — 不採用。会話に使える context を削る。刈る規律が無ければ skill の
  description は増え続ける（2026-08-30 から本数が 5 本減っても字数は増えた）
- **本数を減らす（退役）だけ** — 不採用。RFC-0017 の実測（2026-08-29）で、本数を減らす路線は −897 字、description
  を畳む路線は −6,596 字だった
- **英語だけにする** — Open — revisit when: 日本語のプロンプトで `claude -p` を流し、英語だけの description でも
  Skill tool が呼ばれると測れたとき。今は不採用。著者は日本語で頼み、英語だけのトリガーで 45 日間発火しなかった報告が
  1 件ある（anthropics/claude-code issue #68086、中国語の利用者、n=1、直したという部分は未確認）
- **日本語だけにする** — 不採用。skill 本文の多くと、harness-sync で公開する repo の読者は英語
- **NOT for を全部消し、leading word を分けて衝突を避ける（Pocock の 38 本と同じ）** — 不採用。Pocock の skill は
  領域が重ならないが、この harness は stocktake 系や task 系のように重なる対を持つ。Skill Scaling Laws は意味の近さを
  精度低下の主因とする
- **NOT for を今の形で残し、短くするだけ** — 不採用。他の skill を並べる否定の常駐指示で、幅も食う
- **何もしない** — 不採用。名前だけの skill が 29 本あり、自前の 4〜6 本は使われないまま名前だけで固定されていた
- **lint を置かず、skill-stocktake が `/skill-doctor` を読むだけにする（ADR-0067 のままの状態）** — 不採用。
  予算超過の警告は debug log にしか出ず、description は棚卸しの合間に静かに名前だけになる。`/skill-doctor` は
  実際に注入された token の計器として残る
- **使用 0 の skill（jev-judgment-design、mono-color、loop-design-check、repair-discipline）も user-invoked に
  移す** — Open — revisit when: 書き換え後 30 日の `usage_stats` でも invoke 0 のまま。今は残す。予算超過で名前だけに
  なっていたので、使用 0 はその結果でありうる

## Consequences

### Positive

- 自前の model-invoked skill は、予算に余裕を持って description 付きで listing に載る見込みになる。整理後の
  `/skill-doctor` で確かめる
- 新しい skill や description の追記で幅が戻れば、commit の時点で lint が止める
- user-invoked の 16 本は、slash menu で 1 行で読める

### Negative

- 書き換えで発火が変わりうるが、測っていない。skill-creator §2 の実測が示すのは、文言を磨いても自発発火は
  上がらないことだけ。日英の言い換えとして書いていたトリガー句の多くを消した
- grill-me は、モデルが自分では呼ばなくなる（120 日で invoke 15 回分）。著者が `/grill-me` で呼ぶ
- 閾値 400 と 12,000 は較正していない。予算は window に比例するので、200k window のモデル（予算 6,000）で動かす
  と、上限内でも超える
- 予算の式と測定値の写しが 4 か所にある: この ADR の Context（正本）、skill-creator §3（式だけ）、
  `harness_lint.py` の定数のコメント、調査 report。閾値 400 / 12,000 の写しは `harness_lint.py`（定数と docstring）、
  skill-creator §3 と MAINTENANCE.md、`docs/adr/README.md` の index 行にある。本体が変わったら、この ADR を先に
  直し、写しを追従させる
- もとから user-invoked の skill を `skill:` の名前で指す配線（`rules/common/akc-cycle.md`、`rules/common/evals.md`、
  `skills/implementation-chain/SKILL.md` の harness-boundary など）は、2.1.295 の Skill tool が listing にある名前
  しか受けないので、model がその path を読んだときにだけ届く。決定 1 の「path で指せる」に揃える作業は、この ADR の
  外に残る
- archify を customized にしたので、upstream の更新を取り込むときは description の差分を見る
- 戻すときは commit を revert する。外部への公開物は harness-sync を回すまで変わらない

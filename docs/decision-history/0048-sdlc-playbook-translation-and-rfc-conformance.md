# ADR-0048: AI-native SDLC playbook は改名でなく翻訳で取り込む（AKC 対応 + RFC 完全準拠様式）

## Status

accepted

## Date

2026-08-25

## Context

Anthropic は 2026-08-21 に「The AI-native SDLC playbook」
（`https://claude.com/blog/the-ai-native-sdlc-playbook`）を公開した。本 ADR が照合したのは
2026-08-24 の archive 版
（`https://web.archive.org/web/20260824134825/https://claude.com/blog/the-ai-native-sdlc-playbook`、
2026-08-25 に live 版と記事本文の同一性を照合済み — mirror と照合記録は
`.notes/mirrors/`）。6 stage（Plan / Design / Build / Test / Deploy / Maintain）、
artifact 語彙（intent.md / spec.md / plan.md / REVIEW.md / bands.yaml）、統治語彙
（skills / hooks / permissions / worktrees / subagents）で構成される文書である。

fresh-context で精査した結論は、この harness には playbook が要求する
機構の大半がすでに存在する、というものだった（数え方: 下の付表 1 の 13 行中、
「同型」以上が 11 行）。`verify.sh` は playbook の
feedback loop に相当し、implementation-chain は REVIEW.md 相当、
task-triage の三役は response tiers 相当、bats + harness-lint は決定論層の
continuous evals に相当する。しかも多くはより強い形を取っている —
Build-or-not ゲート、producer→sink の起票規律、承認 hash pin、
cross-model review は、いずれも playbook 側には無い。

著者の要望は「標準語彙に harness を近づけて翻訳可能に保つ」ことである。
一方で implementation-chain / task-triage / verify.sh 等の語彙は
rules・skills・hooks・ADR を横断する load-bearing な語彙であり、
playbook 自体は公開からまだ 4 日の外部文書である — knowledge-staleness
rule の対象であり、改版されうる。

## Decision

1. **改名しない。** 翻訳はマップで担保する。

2. **対応の主役は AKC（agent-knowledge-cycle repo）とし、二重ループで
   対応させる。** playbook の 6 stage を product loop（対象はソフトウェア
   変更）とし、harness の implementation-chain / task-triage / verify /
   hooks に対応させる。AKC の 6 phase を harness loop（対象は知識・
   harness 構成）とし、playbook が stage 3〜6 に無名のまま散らした
   「agent 構成を維持する実践群」に対応させる。stage と phase の 1:1
   対応は誤りとして扱う — 6 stage と 6 phase という数の一致は偶然であり、
   false friend の例として playbook の Maintain（production 監視）は
   AKC の Maintain（文書衛生）と意味が異なる。公開ブリッジ文書
   （英語版・日本語版）は本 ADR と同日に AKC repo の
   `docs/ai-native-sdlc-correspondence.md` / 同 `.ja.md` として作成済み。

3. **intent.md の受け皿は RFC とする。** 提案本文の推奨様式は Rust RFC
   0000-template に完全準拠させる（準拠先 pin:
   `https://github.com/rust-lang/rfcs/blob/master/0000-template.md`、
   as-of 2026-08-25。節構成: Summary / Motivation / Guide-level
   explanation / Reference-level explanation / Drawbacks / Rationale and
   alternatives / Prior art / Unresolved questions / Future
   possibilities）。Rust の preamble（Feature Name / Start Date / RFC PR /
   Issue）は metadata として扱い、frontmatter で表す。frontmatter を
   選ぶ理由は、markdown-native な metadata チャネルであることに加え、
   `claims.py` の機械契約（本文冒頭の非見出し行が `ready` の要約として
   表示される）と両立するためである。失効条件の frontmatter key は
   `review-when:` — ADR の `## Review-when`（[ADR-0044](./0044-adr-review-when-and-dated-annotation.md)）・
   rules の `review-when` ヘッダと同一概念に同一の語を使い、第 3 の名前を
   作らない。intent.md ↔ RFC 節 ↔ 台帳の三語彙対応表は skill:
   `task-stocktake` を正本とし、本 ADR には複製しない。

   > **注記（2026-08-25, skill: rfc-writer 新設）**: 三語彙対応表の正本は
   > `task-stocktake` から `rfc-writer` へ移管した — 対応表は起票時の翻訳であって
   > 棚卸しの判定材料ではないため。起票の手順・様式・足切り・公開規約も同 skill が
   > 正本になった（rfcs/README ×3 への規約複製が即日 drift 源になった著者指摘を受けた
   > 一元化。README は薄いポインタ + index のみ）。

4. **付表 1（product loop 機構マップ、as-of 2026-08-25 の snapshot —
   living doc にはしない）を次の表に収録する。**

   | playbook | harness 正本 | 対応 |
   |---|---|---|
   | intent.md / intent home | 公開 rfcs/ 台帳（[ADR-0049](./0049-unify-task-ledger-into-public-rfcs.md)） | ほぼ同型 |
   | spec.md（handover） | task-triage の dispatch packet | ソロの seam は session/model-tier 境界 |
   | plan.md | plan mode + ADR（supersede が正常系） | 別 artifact 不要 |
   | CLAUDE.md 1 ページ運用 | CLAUDE.md + rules/ 層 + learn-eval | 上回る |
   | Skills（policy owner 承認） | skill-creator 草稿ゲート + 著者 GO | 上回る |
   | Hooks（allow/ask/block） | hooks 群（数と一覧の正本は `hooks/README.md`）+ bats + advisory 封筒 | 上回る（信頼境界は playbook に無い） |
   | Feedback loop（単一 target） | repo ごとの `.claude/verify.sh` + `verify_allow.py` hash pin | 上回る |
   | bug fix は failing test 先行 | `fix` × TDD の条件付き発火（正本 skill: implementation-chain、手順は tdd skill） | 同型でより精緻 |
   | Continuous evals（config 変更時実行、incident 恒久化） | bats-autorun + harness-lint、incident→回帰は `tests/git-target-extraction.bats` が実例 | 決定論層は充足 |
   | REVIEW.md（pass 分割・nit cap） | implementation-chain の Chain Matrix + Review 表 + 起票規律 | 上回る |
   | 環境ティア autonomy | prototype 種別 ↔ harness precommit 群 ↔ 公開 repo の人間 GO | 同型 |
   | Response tiers（log / diagnose / act via PR） | task-triage 三役（hook 通知 / Fable judge / Opus build + 人間 merge）、launchd tick | 最も綺麗な 1:1 |

   > **注記（2026-08-27, ADR-0055）**: REVIEW.md 行の「上回る」は密度の超過として削減された
   > — 常設レビューは fresh-context 1 段 + 条件付き Security へ縮約（公式 best practices の
   > 推奨密度へ回帰）。snapshot 本文はそのまま残す。

5. **付表 2（採用しないもの、根拠つき）を次の表に収録する。**

   | playbook 実践 | 採用しない根拠 | 再訪条件 |
   |---|---|---|
   | 統計 control bands（Western Electric） | n=1 の指標は非定常（台帳 T-002 の「期間 KPI の非定常性」実測）。cadence 駆動の stocktake 群が代替 | 安定した rolling baseline を持つ指標が実運用に現れた時 |
   | LLM-judge continuous evals の CI ゲート化 | SkillEvaluator pilot（2026-08-22）48 skill で真の欠陥 0・全 false positive、skill-creator loop の発火測定は定数 0（計器死亡）。決定論層（bats + lint）が意図を充足済み | 実タスク corpus が数十件規模で貯まり、judge の判定が triage に値するようになった時（台帳 T-EVAL-AXIS-BOOTSTRAP の再開条件とも接続） |
   | intent→spec→plan の 3 artifact 分離 | チーム職能 seam の handover 文書。ソロの seam（session 境界 / model tier / 人間 gate）には既にゲートがある。複製は redundant channel | 恒常的な複数人運用が始まった時 |
   | DORA / leading-lagging 指標群 | 消費者不在（Build-or-not ③）。判断が紐づく計測だけ残す | 特定の指標に判断が紐づいた時（その 1 指標だけ入れる） |
   | compliance 軸（diff ↔ spec/plan 照合の独立 pass） | 置かない・観測待ちと明記。dispatch 経由の検収（task-triage）が該当箇所を持つ。セッション内実装では実装者 = plan 著者 | セッション内実装で plan 乖離の実害を 1 回観測した時 |
   | fix 中の test 編集ブロック hook | 観測事例 0 のため観測待ちで起票（RFC-0002）。1 回は証拠でなく 0 回はなお弱い（skill: `measurement-discipline`） | RFC-0002 の着手条件（GREEN 偽装 1 回観測） |

   付表 2 の読み方は `rules/common/akc-cycle.md`「却下記録の読み方」に従う — 各行は
   日付つき仮説であり、発散段階の反証には使わない。照合（採用判断）の段でのみ引き、
   衝突は supersede 候補として扱う。

6. [ADR-0007](./0007-open-concept-network-effect.md)（開放型ネットワーク
   効果）は TCP/IP の RFC モデルを帰属構造の比喩として引いていた。本決定は
   その比喩を文書様式として文字通り採用する。

## Review-when

- playbook の大改版（stage 構成・artifact 語彙の変更）
- harness の大再編（implementation-chain / task-triage の解体）
- AKC cycle の 6 phase 再定義

のいずれかが起きたとき、付表 1/2 の snapshot は失効し、
ブリッジ文書ともども再照合する。

> **注記（2026-08-25, 著者指示）**: 様式に `## Status` / `## Next action` の 2 節を独自
> 追加した（IETF「Status of This Memo」型の prose status + 一元化の tracking 層。RFC 標準に
> state 語彙が無いことへの応答 — 正本は skill: task-stocktake）。**この様式は運用して
> 冗長な点・足りない点が観測されたら再検討する** — 完全準拠 + 2 節という形自体を固定
> しない。状態語彙の全域標準化は RFC-0003 が追跡。

## Alternatives Considered

### ハーネス語彙を playbook 語彙へ改名する

却下。load-bearing 語彙の全面 drift 源になる。playbook は公開 4 日の
外部文書であり、knowledge-staleness rule の対象として改版されうる。

### 取り込まない（現状維持 — 台帳本文は自由記述のまま、様式を課さない）

却下。コスト最小の対抗案だが、「標準語彙に近づけて翻訳可能に保つ」という本件の目的
そのものに応えない。精査の結論（機構の大半は既存）はマップだけで足りることを示したが、
提案 artifact の様式だけは無名のままで、外部の読者・LLM が既知ジャンルとして読めない
状態が残る。

### playbook の intent.md 様式をそのままテンプレにする

却下。照合可能な根拠: intent.md は公開 4 日の造語、RFC は IETF で 1969 年から、
eng-org の提案プロセスとしても Rust RFC（2014 年〜）以来 10 年超の運用実績があり、
語彙の耐久性で上回る。最終選択は著者の判断（2026-08-25、分析でなく選好の宣言として
記録する）。

### RFC 語彙 + 独自要素のハイブリッド 6 節テンプレ（Summary / Motivation / Scope & constraints / Alternatives / Unresolved questions / Expiry）

却下。著者指示は「今後のことを考えると完全準拠」。独自要素（失効条件）は
frontmatter へ逃がせば、本文は RFC に 100% 準拠したまま保てる。

## Consequences

### Positive

- doctrine 層（LLM-mediated channel）への interface が標準語彙化され、
  外部 tool / LLM / 人間が提案文書を既知ジャンルとして読める
- Prior art 節が search-first / Phase 0 の結果の置き場になり、AKC の
  Research phase と接続する
- 付表 2 により「採用しない」判断が根拠と再訪条件つきで記録され、照合段の往復が
  軽くなる（発散は縛らない — akc-cycle「却下記録の読み方」に従う）

### Negative

- 準拠先テンプレは Rust community の管理下にあり、改版時に追従判断が
  要る（Review-when とは別の外部依存）
- 9 節構成は小さな作業項目には重い。「該当なし節は省略可、
  Summary/Motivation 中心でよい」という緩和で吸収する（正本は
  skill: `task-stocktake`）

### Neutral / Follow-ups

- 機構の輸入はほぼ無い（付表 1 の 13 行中 11 行が同型以上のため）。輸入したのは語彙と
  様式だけ

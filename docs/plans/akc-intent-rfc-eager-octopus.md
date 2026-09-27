# AI-native SDLC playbook の取り込み — AKC 対応 + rfcs/ 一元台帳

## Context

Anthropic「The AI-native SDLC playbook」（2026-08-21 公開）の取り込み再検討。fresh-context
精査の結論: playbook の機構は 8 割方既存（多くはより強い形）。取り込みの主戦場は機構の
輸入ではなく**翻訳レイヤの整備**。

会話で確定した判断（2026-08-25、著者確認済み）:

1. **改名しない** — 翻訳はマップで担保 + 無名箇所への標準語採用
2. **対応の主役は AKC、ただし二重ループ対応**（stage↔phase の 1:1 は誤り）:
   - playbook 6 stage = **product loop**（対象はソフトウェア変更）↔ implementation-chain /
     task-triage / verify / hooks
   - AKC 6 phase = **harness loop**（対象は知識・harness 構成）↔ playbook が stage 3〜6 に
     **無名のまま散らした** agent 構成維持の実践群
   - false friend: playbook「Maintain」（production 監視）≠ AKC「Maintain」（文書衛生）
   - gap（= AKC の差分）: Research（外部知識 intake 規律）/ Curate（棚卸し体系）は
     playbook にほぼ不在
   - 接続: product loop が回った経験が AKC の Experience 入力
3. **intent.md の受け皿は RFC**。本文は**標準 RFC テンプレに完全準拠**（Rust RFC
   0000-template 系譜、URL + as-of を ADR に pin）
4. **task 機能を rfcs/ に一元化**（著者最終指示）: store 形台帳を `.notes/tasks/` から
   **公開 `rfcs/`** へ移す。提案とタスクは現行台帳と同じく 1 店舗（β′ の提案/作業分離は
   撤回 — 分離は Rust の事情の借用で、現行台帳の意味論は元々一元）。判断記録の公開 =
   ADR-0007「RFC を書いた人の名前は消えない」の実践、playbook「intent home」に 1:1 対応
5. ブリッジ言語 = **EN + ja 同時** / evals の n=1 実測は**中立トーン**で書く

## rfcs/ 一元台帳の設計（γ）

**形**: repo ごとに 2 形は現行維持 — 小 repo は 単一表 `TASKS.md`（変更なし）、store 形
repo は **`rfcs/NNNN-slug.md`**（`.notes/tasks/T-XXX.md` を置換）。トップレベル・公開・
4 桁採番 + `rfcs/README.md` index（docs/adr の前例）。

**ID と状態**: ID = `RFC-NNNN`（ファイル stem 先頭の NNNN から導出）。状態は frontmatter
`state:` に**台帳の 8 語をそのまま**（candidate=Draft / ready=Accepted / in_progress /
blocked / done=Implemented / decided / dropped=Rejected / retired。第二語彙を作らない。
owner は task-stocktake、blocked 3 行・retired 引用の既存規定もそのまま適用）。
失効条件は frontmatter `expiry:`。

**本文（完全準拠、推奨 — 自由記述は引き続き有効）**:

```
---
state: candidate 2026-08-25
expiry: <失効条件>
---
## Summary
## Motivation
## Guide-level explanation
## Reference-level explanation
## Drawbacks
## Rationale and alternatives
## Prior art
## Unresolved questions
## Future possibilities
```

- Rust preamble（Feature Name / Start Date / PR / Issue）は metadata → frontmatter に対応
  （適応理由は ADR）。機械契約（最初の非見出し行 = `ready` の 90 字表示）は `## Summary`
  1 行目で両立
- 見出し EN 準拠・本文言語自由。小さい運用タスク（review fix 等）は該当なし節を省き
  Summary/Motivation 中心の短い本文でよい — RFC 純度より起票摩擦の低さを優先し、
  ジャンル混在は index の 1 行で明示
- 対応表（skill に記載）: intent.md problem → Motivation / proposed outcome → Summary /
  affected systems → Reference-level explanation / constraints → Drawbacks /
  open questions → Unresolved questions。Build-or-not ① → Rationale and alternatives、
  ③ → Motivation。**Prior art ← search-first / Phase 0 の置き場**（AKC Research 接続）
- **archive 機構は rfcs/ に持たない**: 終端エントリは削除・退避せずその場に残る（RFC 慣行。
  却下 = dropped も公開判断記録として残る — akc-cycle「却下記録の読み方」と同思想）。
  pending の視界は `ready` の state フィルタが保つ

**機構改修（既存計器の最小変更、上限 ~20 行 + bats。新規機構なし）**:

- `scripts/claims.py`: ① ID 正規表現 `^T-…` を `RFC-` も受ける形に緩める ② `ready` /
  `known_tasks` / `task_head` の走査対象に `rfcs/`（stem `NNNN-*` → `RFC-NNNN`）を追加。
  `.notes/tasks/` の読取は移行期間中は残す（dual-read）。claims.jsonl は `.notes/` のまま
  （lease は運用状態であり判断記録でない — 非公開維持）
- `hooks/task-claims-reminder.sh`: ディレクトリ検知に `rfcs/` を追加（1 行）
- `tests/task-claims.bats` ほか該当 bats を更新
- CA ADR-0095 との整合: 描画・状態機械・aging は引き続き持たない。台帳コード総量は
  ほぼ不変（正規表現 + パス追加のみ）。ADR-0049 に判断を記録

**移行**: 既存台帳（harness の TASKS.md 行、他 repo の store）は**今回は移さない**。
rollout（RFC-0001）が repo ごとの初設・既存行の移送判断・harness-sync 収集範囲拡張を追跡。
harness の TASKS.md 冒頭に「新規の store 形起票は rfcs/ へ」の誘導 1 行だけ足す。

**ADR との境界**: rfcs/ = 提案・作業・未決（発散→照合 seam を渡る artifact）。ADR =
決定記録。採用時は ADR が Rationale and alternatives を引き取る。

## 成果物と変更ファイル

### 1. 公開ブリッジ文書（主）— agent-knowledge-cycle repo

新規: `docs/ai-native-sdlc-correspondence.md` + 同 `.ja.md`（上限 250 行/枚）。

構成（ADR-0013 concede-then-locate を借用）: 二重ループモデル / AKC phase ↔ playbook
散在実践の対応表 / gap 行と false friend / 「product loop の経験が AKC の Experience
入力」/ artifact 対応の一般形（intent.md ≈ 公開 rfcs/ のエントリ、intent home ≈ rfcs/。
repo 固有の運用語彙は書かない）/ evals の operator-scale 限界を中立トーンで（一次根拠は
日付つき）/ as-of 2026-08-25 + Wayback URL + dated addenda 節。playbook 全文の repo 内
複製はしない（再配布回避 — 照合用 mirror はハーネス側ローカル）。

同期（同じ diff で）: `llms.txt`（Core documentation bullet）/ `llms-full.txt` /
`graph.jsonld`（concept node、Obsidian wiki read-only 参照・wiki は引用しない）/
`docs/CODEMAPS/architecture.md`（doc 追加 + :148 言語ポリシー行）/ `README.md` +
`README.ja.md`（`## Positioning` に 1–2 文 + リンク、H2/H3 parity）。coinage 最小限。

### 2. ハーネス ADR ×2 — `docs/adr/0048-*.md` / `0049-*.md`（skill: adr-writer で描画）

**0048**（翻訳戦略と RFC 準拠）:

- Decision: 改名せず AKC ブリッジ + 三語彙対応（RFC ↔ intent.md ↔ rfcs/ 台帳）で翻訳可能性
  を担保。本文は Rust RFC 0000-template 完全準拠（URL + as-of pin、preamble → frontmatter
  の適応理由）
- 付表 1: product loop 機構マップ（playbook 実践 → ハーネス正本、snapshot 収録）
- 付表 2: 採用しないもの — 統計 control bands（n=1 非定常、T-002 実測）/ LLM-judge
  continuous evals の CI ゲート化（SkillEvaluator 2026-08-22 全 FP。決定論層は充足済み）/
  intent→spec→plan 3 分離（ソロの seam は session/model-tier 境界で既ゲート）/ DORA 指標
  （消費者不在）/ compliance 軸「置かない・観測待ち」
- ADR-0007 RFC 比喩との同根性 1 行
- Review-when: playbook 大改版 / ハーネス再編 / AKC cycle 再定義

**0049**（rfcs/ 一元台帳）:

- Decision: store 形台帳を公開 `rfcs/` に一元化（提案と作業は現行通り 1 店舗）。ID は
  RFC-NNNN、状態語彙 8 語流用、claims.py は正規表現 + 走査パスの最小変更のみ、archive
  機構は持たず終端エントリは残置。経緯: α（.notes のまま公開）→ β′（提案/作業分離）→
  γ（一元化）の転換理由を記録
- Alternatives: α（公開ジャンルとして無名、ignore 手術要）/ β′（店舗 2 つ = 分散 drift、
  Rust の事情の借用）
- Consequences: 全 repo 展開・既存行移送・harness-sync 拡張は RFC-0001 が追跡。機微は
  本文に書かずリンク先へ（公開既定）
- Review-when: 運用 3 ヶ月で rfcs/ 流入 0 / 公開起因の機微事故 1 件 / 台帳コードを
  さらに増やしたくなった時（要件を先に疑う — task-tracking.md の review-when と同じ）

### 3. ハーネス skill / rule / 機構の配線

- `scripts/claims.py` + `hooks/task-claims-reminder.sh` + 該当 bats: 上記「機構改修」
- `skills/task-stocktake/SKILL.md`: :135/:137 間に新節「store 形の家 rfcs/ と本文様式
  （RFC 完全準拠）」— 設計全体（家・ID・語彙流用・テンプレ・対応表・採番と index・
  終端残置 = archive 非適用・公開規約 = 機微はリンク先へ）。既存の store 記述
  （`.notes/tasks/`）を rfcs/ へ更新、blocked 3 行は Unresolved questions 配下の運用を注記
- `rules/common/task-tracking.md`: store 形の記述を rfcs/ に更新（「単一表 TASKS.md /
  store `rfcs/NNNN-slug.md`」、様式・語彙の正本は task-stocktake — 複製しない）
- `skills/task-triage/SKILL.md`: store パス言及を rfcs/ に同期（実装前に現行文を読んで
  最小編集）
- `MEMORY.md` の Pending 行の台帳パス表記を確認・追従
- skill-creator ゲート非該当: 既存 skill への節追加・パス同期のみ、語彙正本の位置は不変

### 4. ハーネス rfcs/ の初設 + エントリ 2 件（完全準拠の実例第 1・2 号）

- `~/.claude/rfcs/README.md`（index 表 + ジャンル混在の明示 1 行）
- `rfcs/0001-public-rfcs-rollout.md`（state: candidate）— タスク台帳を持つ**全 repo** への
  rfcs/ 展開（著者: 「タスク持ってるリポジトリ全部したい」）: 対象 repo の同定 / repo ごと
  の初設と既存行（AKC の T-003、harness TASKS.md の T-002 等）の移送判断 / harness-sync
  収集範囲への rfcs/ 追加 / private repo の扱いは Unresolved questions
- `rfcs/0002-test-edit-guard-hook.md`（state: candidate、expiry: 「test 改変による GREEN
  偽装を 1 回観測」を着手条件として Motivation に、失効条件を frontmatter に）
- 機構改修後に `claims.py spawn RFC-0001 --origin idea` / `RFC-0002` 同様（系譜記録 —
  regex 変更の実地検証を兼ねる）
- harness `TASKS.md` 冒頭に誘導 1 行

## 実行順

1. ハーネス: 機構改修（claims.py / hook / bats — TDD: bats を先に RED）
2. ハーネス: 成果物 3 の残り（skill / rule / memory 配線）→ 4（rfcs/ 初設 + 2 件 + spawn
   = 様式と機構の実地検証）
3. ハーネス: 成果物 2（ADR-0048 / 0049）→ adr-reviewer + Record Review
4. AKC repo: 成果物 1（EN 執筆 → ja mirror は prose-translation → 同期 6 ファイル）
5. 各 repo で commit（git-workflow: git -C、$( ) 禁止。precommit hook 群が機械適用）

## 実行モデル

本セッション（judge-tier）が orchestrate。機構改修は小さいので本セッション、重い prose
（ブリッジ EN/ja・ADR 描画・レビュー群）は build-tier agent へ（adr-writer /
prose-translation / reviewer 群 / 必要なら general-purpose opus subagent —
implementation-chain「Review の実行モデル pin」準拠）。重くなったら skill: `spawn-session`。

## harness-boundary（1 行判断）

既存計器の最小改修（~20 行）+ skill 節追加 + rule 更新 + ADR + 文書ディレクトリ新設。
新規常駐機構なし。rfcs/ 流入 0 が 3 ヶ月続けば 0049 の Review-when で畳む。

## Verification

- **機構**: bats（task-claims.bats 拡張: RFC-NNNN の claim/spawn/ready、rfcs/ 検知、
  `.notes/tasks` dual-read 維持、T- 既存 ID の回帰）全 green。`claims.py ready` に
  RFC-0001/0002 が candidate として出ない（ready フィルタ）こと + `--state candidate`
  相当の確認手段があればそれで出ること（無ければ ready の仕様通りの確認に留める）
- **ブリッジ**: source-fidelity-checker（ローカル mirror 照合、skill:
  cited-source-mirror-verification 手順）+ vocabulary-consistency-checker（AKC glossary）+
  README 両言語 H2/H3 parity + AKC verify gate
- **ADR**: harness-lint（Review-when 機械検査）+ adr-reviewer
- 完了前: 両 repo の `git status`、doc sync 漏れ確認

# ADR-0066: search-first を verdict から報告契約へ — 受ける問いの 6 種を trigger surface に置き、scout を退役する

## Status

accepted

## Date

2026-09-14

## Context

RFC-0022 の観察（著者）: search-first は ① なかなか発火しない ② 発火しても「そのまま適用できない」
と却下される ③ 探索範囲が制限列挙型。実測（`metrics/skill-usage.jsonl` / `metrics/agent-usage.jsonl`、いずれも gitignored、
2026-09-14 集計）: invoke 6 月 6 / 7 月 14 / 8 月 8 / 9 月 0（14 日時点）、agent scout の起動は累計
18。

構造的原因: `skills/search-first/SKILL.md` の verdict 表（Adopt / Extend / Compose / Build）は
「install できる package があるか」の一軸で、skill / rule / ADR でできた harness ではほぼ Build に
落ち、見つけたものから学んだことを運ぶ欄が無い。description は「add X functionality / what
library should I use」型の発話例だけで、harness で実際に出る問い（先行実装はあるか、論文の主張は
当てはまるか、公式は何と言っているか）に一致しない — 発火率は「受ける問いの種類」（trigger
surface）の帰結であり独立の knob ではない。

実測 1（Claude Code の session transcript `~/.claude/projects/`、gitignored。直近 60 日、述語を固定
した手順は `.notes/search-first-shadow-baseline-2026-09-14.md` が snippet と集合一覧ごと持つ）:
20 KB 超の transcript 979 本のうち、WebSearch か外部調査 subagent（prompt に WebSearch / WebFetch /
一次ソース / as-of を含む Agent 呼び出し）を使ったセッション 142 のうち、search-first か scout を
通ったのは 9、通らなかったのは 133（93.7%、133/142）。述語を固定する前の暫定値は 84%（130/154）で、
adr-reviewer の独立再現では定義差だけで 67.5%〜96% に振れた — 基準値は固定手順の 93.7%。通らなかった側
は自前 prompt に「as-of 日付・一次ソース・報告せよ」を書いていた（rule knowledge-staleness の
transfer 証拠）。

実測 2（`metrics/agent-usage.jsonl` に session id が記録された 2026-08-18〜09-13 の 7 セッションから、
transcript の Skill(search-first) / Agent(scout) 呼び出しを 1 セッション最大 5 件まで抽出した 8 件）:
問いの種類は library 選定 2 / 先行実装 4 / 仕様 1 / 状況の俯瞰 2（重複あり）。読んだ 8 件全部で
呼び出し側が scout の report 雛形（Adopt / Build）を無視して完全な prompt を自前で書いていた。scout の固有価値は
「web tool を持つ subagent」で、general-purpose subagent と同じ。

実測 3（実測 1 の影のセッションから WebSearch query 261 本と外部調査 Agent prompt 148 本を抽出し、
本セッション（Fable）が目視で種類に当てた）: 5 種（library 選定 / 先行実装 / 論文・post
の主張 / 仕様・公式挙動 / 状況の俯瞰）に収まらない塊が 1 つ — 原典照合（この主張・引用・数値を
一次資料は本当にそう言っているか）。受けるべきでない塊も見えた: トラブルシューティング /
how-to、repo 内・ローカル環境の調査。

一次資料（raw 本文を読んだ、2026-09-14）: HumanLayer research_codebase
（https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/research_codebase.md）の
「DOCUMENT WHAT IS, NOT WHAT SHOULD BE」、K-Dense hypothesis-generation
（https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/hypothesis-generation/SKILL.md）
の dated evidence boundary、Open Deep Research
（https://github.com/langchain-ai/open_deep_research、archived、最終 push 2026-08-10）
prompts.py の停止条件と call 上限。

外部レビュー（Codex gpt-6-astra、2026-09-14）: 「search-first 強化は需要証拠が最も明確だが、問い
発見の代替ではない」。R&D ループ（問い発見）は別件。

[ADR-0065](./0065-drop-adr-consultation-wiring-and-build-or-not-gate.md)（2026-09-14）は
search-first を「別セッションで再設計中のため対象外」と明記している。本 ADR がその再設計。

著者判断 2026-09-14: (i) verdict より、リサーチ結果を報告して使えるところを呼び出し側
（orchestrator）に取捨選択させる — そのまま使えるのは稀で、部分的に使えるだけでも成果。(ii) 呼ばれた
履歴だけでは種類の網羅は担保できない（生存者バイアス）— 影の集団の実測で補正し、網羅の計器は
invoke 数でなく影の比率にする。(iii) 書き方の規則 3 つ（範囲付き不在 / snippet と本文の区別 /
主張に対象・前提・相違を付ける）は verdict の二値への対策であって、常駐 rule に置くと全文脈に当たり
不自然な挙動になる — rule には足さない。(iv) rule knowledge-staleness が skill search-first を
名指ししているので、指す先を残して改良する。scout は要らない。

## Decision

1. `skills/search-first/SKILL.md` を全面改修（置換）。verdict 行
   （`Verdict: Adopt|Extend|Compose|Build — …`）を廃止し、終わり方の契約を**報告**にする:
   `## Scope searched`（検索語 / source / as-of、見つからなかった範囲）/ `## Found`（1 件ごとに
   何か・URL / 対象と前提 / 根拠の種別 / こちらとの相違 / 移せる部分）/ `## Still unknown`。判断
   （採る / 部分的に採る / 採らない）は呼び出し側が行い、plan 本文か RFC の Prior art に書く。
2. description の trigger surface を 6 種の問い（library 選定 / 先行実装 / 論文・post の主張 /
   仕様・公式挙動 / 状況の俯瞰 / 原典照合）の発話例 + 「外部に答えがありうる問い全般」の総称句に
   する。種類はゲートでなく探索の手掛かり。別入口への routing: repo 内・ローカル環境 → Explore
   agent、記事全体の fact-check → writing repo の fact-checker、bug fix / refactor / config 値 →
   implementation-chain。
3. 種類別の表（探索先 / 証拠として数えるもの / 止め方）と書き方の規則（全 claim に as-of と出所
   URL、不在は範囲付き、snippet と本文の区別、主張に対象・前提・相違、判断は事実に基づく散文 —
   「evidence, not scores」の正本は本 skill §3 Report に置く）は skill 本文が持つ。
   `rules/common/knowledge-staleness.md` は変更しない。
4. Full Mode の委譲先は general-purpose subagent。Read / Grep / Glob / WebSearch / WebFetch だけで
   働く指示は prompt に書く — Agent tool は tool allowlist を渡せないので、scout の frontmatter が
   持っていた宣言的 allowlist（`tools: [Read, Grep, Glob, WebSearch, WebFetch, mcp__context7__*]`）は
   prompt 上の制約に降格する。`agents/scout.md` は削除。
5. 消費者の書き換え 6 ファイル: `skills/implementation-chain/SKILL.md` 早期停止条件「Phase 0 で
   Adopt Verdict → 再 plan」→「Phase 0 の報告に、実装方針を変える既存解が含まれる → 再 plan」/
   `skills/verify-bootstrap/SKILL.md`「Verdict が出たら」→「報告を受けたら」/
   `skills/mondo/SKILL.md`・`skills/prompt-perturb/SKILL.md`・`agents/prompt-forager.md` の
   「search-first / scout」→「search-first」/ `skills/agent-stocktake/SKILL.md` の scout 例示を
   落とす。配線（`rules/common/planning.md`、implementation-chain Phase 0 行、rfc-writer §2、
   akc-cycle Research 欄、knowledge-staleness の名指し）は名前ごと維持。
6. 網羅の計器は影の比率: 直近 60 日の transcript で、WebSearch か外部調査 subagent を使った
   セッションのうち search-first を通らなかった割合。基準値 93.7%（133/142、2026-09-14）。述語 4 点
   （セッション単位 / 走査範囲 / 窓 / 分子）・snippet・基準集合の一覧は
   `.notes/search-first-shadow-baseline-2026-09-14.md` に固定（読み取り専用の snippet。`scripts/` には
   置かない）。
7. 旧 ADR への日付つき注記: ADR-0024（frozen-input render 群の例から scout が消える）、ADR-0026
   （「evidence, not scores」の locator が Step 2 から §3 Report へ）。ADR-0023（scout 委譲能力は主
   ループが最初から持つ）と ADR-0054（過去の走査記録）の scout 言及は本 ADR と整合し、注記は要らない。
8. 公開側は次回 harness-sync で追従: 単独 repo `shimo4228/search-first` の README（adopt /
   extend / build 前提の記述）を報告契約に合わせる、claude-harness から agents/scout.md が消える。
   ECC 版 search-first（PR #262）とはここで分岐（ECC 貢献は ADR-0006 で終了済み）。
9. ゲート: skill-creator §4 fresh-context 草稿ゲート（general-purpose subagent、Read / Grep /
   Glob のみ、8 問）は Publishable（2026-09-14）。指摘 2 点（description の常駐字数、ADR-0026 の
   locator）は反映済み。§5 行動 gate（`claude plugin eval --ablation with-without --runs 3 -j 2`、judge haiku、case は
   先行実装型の問い 1 本「agent frontmatter の checker は既にあるか」、grader 3 本 = 出所 URL と日付 /
   不在の範囲 / 候補ごとの相違と移せる部分、+ with-only の発火検出）: 1 回目（timeout 300 秒）は
   with 3 run 全部が打ち切り。2 回目（timeout 900 秒、2026-09-15）: with 0.00 / 0.67 / 0.00、without
   0.33 / 0.00 / 0.67、meanDelta −0.11、発火 3/3、所要 with 約 330 秒 / without 約 165 秒、費用
   $7.81。報告契約（Scope searched / Found / Still unknown）が守られたのは with 3 run 中 1。
   出所 URL + 日付の grader は 6 run 中 5 で FAIL（両 arm）。screening の delta は無く、
   §5 の第 2 段（with / without の出力を著者が読む）に進む。

## Review-when

- 影の比率を 2026-11 に `.notes/search-first-shadow-baseline-2026-09-14.md` の snippet で取り直し、
  93.7% から下がっていなければ「発火しない原因は trigger surface」の仮説が崩れたとして本 ADR を
  再読する（固定するもの: セッション単位 = 20 KB 超の `projects/<slug>/<session>.jsonl` 1 本、走査 =
  一段 glob で `-private-tmp` slug 除外、窓 = mtime 60 日、分母 = WebSearch の tool_use か外部調査
  regex に一致する Agent prompt、分子 = そのうち Skill(search-first) を持たないもの）。
- 報告を受けた呼び出し側が「移せる部分無し」で報告を捨てる例が続く（著者観測）— 報告契約の設計を
  再読する。
- transcript の形式変更で上の手順が測れなくなった — 計器を置き換える。

## Alternatives Considered

### verdict 表を維持し Build 行の下に「学び」欄を必須で足す

却下。二値が学びを捨てる構造は残る。

### search-first を退役し、書き方の規則 3 行を rule knowledge-staleness へ移す

却下。3 行は verdict の二値への対策で、verdict が無ければ対策の対象が無い。常駐 rule に置くと
全文脈に当たり不自然な注記が増える（著者判断）。rule が skill を名指ししており、指す先を残す方が
筋。

### scout を残して model を opus に上げる

却下。読んだ 8 呼び出し全部で呼び出し側が雛形を無視して完全な prompt を書いていた実測に反する。

### scout を残し、report 雛形だけを新しい報告契約に差し替える

却下（著者判断 2026-09-14「scout はいらない」）。この案なら frontmatter の tool allowlist は保てる —
その代償は Decision 4 と Consequences Negative に記録し、allowlist が要ると分かったら薄い agent 定義
1 本で復元できる。

### 新 skill を作り search-first を退役する

却下。名前が変わると rule / skill / memory の参照が切れる。

### 何もしない

却下。減衰（9 月 invoke 0）を受け入れることになる。

## Consequences

### Positive

- 探索の学びが報告として残り、呼び出し側が部分採用できる。
- harness で実際に出る問い（先行実装 / 主張の適用可否 / 仕様 / 俯瞰 / 原典照合）が description に
  一致する。
- agent が 1 本減る。
- 網羅の計器が invoke 数（看板の帰結）から影の比率（直接測定）に変わる。

### Negative

- library 選定の 1 行の決定性（Adopt / Build が 1 行で読める）は失う。
- Quick Mode は報告 1 段落分重くなる。
- 公開 repo `shimo4228/search-first` の README が同期まで verdict 前提のまま drift する。
- 影の比率の走査は手動（snippet を `.notes/` に置き、`scripts/` には持たない）。60 日ローリング窓
  なので 2026-11 の集合は今日の集合と入れ替わる — 比べるのは比率で、集合の差は基準集合の一覧で追う。
- Full Mode の tool 制限が宣言的 allowlist から prompt 上の制約に降格する（web 由来コンテンツが
  Bash を持つ general-purpose subagent に入りうる。Quick Mode の主ループは元から同じ条件）。
- description を 6 種 + 総称句（約 830 字）に広げた分、誤発火（外部に答えが無い問いで発火）が
  増えうる。影の比率と並べて invoke 数も副次的に見る。

### Neutral / Follow-ups

- 配線 5 か所の名前は変わらない。
- R&D ループ（問い発見）は本 ADR の対象外。
- ECC 版とは分岐。

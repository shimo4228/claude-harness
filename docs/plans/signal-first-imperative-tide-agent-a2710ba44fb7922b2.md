# 調査報告: signal-first 復活の置き場所候補

対象: `~/.claude`（read-only 調査、深さ medium）
背景: signal-first は ADR-0026（2026-07-31）で常駐 rule から退役済み。Claude 5 世代交代 + 質問抑制の実害（grill-me）が理由。今回はその復活先を、現行 harness が「出力の形」を制御している全箇所を洗い出した上で検討する。

---

## 1. 出力スタイル系の配線

- `output-styles/` ディレクトリは**存在しない**（`ls` は No such file or directory）。カスタム output style は自作されていない。ADR-0030:19 も同じ事実を確認済み（「`~/.claude/output-styles/` は存在せず自作ではない」）。
- `settings.json:319` に `"outputStyle": "Concise"`（Claude Code 組み込みスタイル）。`settings.json:320` に `"language": "Japanese"`。
- **既知の矛盾（未解決）**: ADR-0061:42-44 が `/claude-api prompt-audit` の flag-only 所見として記録— `outputStyle: Concise` は Claude Code system prompt の「Before you start, say in a line… Close with a short recap」と直接矛盾する update-suppressor 型。**著者判断待ちのまま**（ADR-0061:123 でも再掲、Follow-up 未消化）。signal-first を足す前にこの矛盾を先に解く必要がある——「冒頭に signal」を新設しても、product 同梱の Concise style が「recap は要らない」の圧を既にかけている。
- `--settings` による style 隔離の先例: `skills/skill-comply/scripts/child_settings.py:62-78` の `child_settings(pin_output_style=True)` が `outputStyle: "default"` を子プロセスへ注入。呼び出し元は `skills/skill-comply/scripts/scenario_generator.py:68`、`spec_generator.py:76`、`classifier.py:52`（いずれも `subprocess.run([..., "--settings", child_settings(...)])`）。目的は逆方向（機械可読な出力を汚さないためユーザー style を剥がす）だが、**style を per-invocation で上書きする配線は既に実在する**——signal-first を特定の消費者（例: task-triage の digest 生成 subprocess）にだけ強制する場合の技術的先例になる。
- ADR-0030（superseded by ADR-0035）は「常駐テキストの書き方」と「ユーザー向け出力の書き方」を分離しようとした最初の試み（`rules/common/output-register.md`、+66 語）。ADR-0035:49 でこの rule ごと退役し「出力較正は substrate に委譲」。**出力の書き方を rule で制御する試みは過去に一度失敗して退役している**——signal-first も同じ轍を踏むリスクを ADR-0035 の Context/Decision と照合する必要がある。

## 2. 常駐 rule のうち応答・報告の形に触れているもの

`rules/common/*.md` 全 14 ファイルのうち、応答・報告に触れるのは:

- `rules/common/boundary.md:19-21` 「**止まって報告する**: 同じ方針で 2 回失敗 / time cap / 前提の反証 / 外部 platform の rate limit 連発（policy signal）。そこまでを残して報告する。」——停止条件の話で、出力の**形**（冒頭に何を置くか）は規定していない。
- `rules/common/debugging.md:6-8` rate limit を policy signal として扱い「backoff で踏み抜かず人間へ報告する」——報告の**存在**は要求するが**形**は無い。
- `rules/common/practitioner-identity.md` — フレーミング回避の identity/values 層。出力の**内容の枠**（既存カテゴリへの回収を避ける）であって形式ではない。
- `rules/common/planning.md` — 実行入口のポインタのみ。出力形は触れない。

**現行 rules/common/*.md には「応答冒頭に何を置くか」という出力の形を定めた rule は 1 つも無い**（ADR-0026 で akc-cycle.md から削除されて以来空白）。

frontmatter の書式例（verbatim、boundary.md 冒頭）:

```
<!-- origin: shimo4228 -->
<!-- rationale: ADR-0069 — 境界が packet / task-triage / tick prompt / growth-* / agents.md の 6 箇所に文面違いで散っていた。substrate の一般則（hard to reverse or outward-facing → confirm first）は再宣言せず、このハーネスで何がそれに当たるかと、確認なしで取ってよいリスクだけを置く -->
<!-- review-when: 人間に渡す操作の列挙を足す / 減らす時。判断役の取り込みで main が壊れ人間が revert した回数が 3 か月で 2 回を超えた時（取り込みを人間へ戻す）。substrate が台帳・gate script・scheduled task を outward-facing として自ら扱うようになった時 -->
```

（出典: `rules/common/boundary.md:1-3`。同型を `rules/common/agents.md:1-3` でも確認——2 例とも `<!-- origin -->` / `<!-- rationale: ADR-XXXX — なぜ書いたか -->` / `<!-- review-when: 失効条件 -->` の 3 行 HTML コメントを先頭 10 行以内に置く形で一致。）

`rules/README.md:4` の採用基準: 「毎セッション自動ロードされる常駐層。採用基準は『この環境固有の事実・配線・罠』。思考や作業の手順は skill、発火時刻を要する検査は hook、一般的な判断は substrate が持つ。」
`rules/README.md:9-10`: 「各 rule は `origin`、`rationale`、`review-when` を持つ。存在は `harness_lint.py`、意味と失効条件は skill: `rules-stocktake` が検査する。」

**含意**: 「応答冒頭に signal を置け」は一般的な出力作法（substrate が既定で持ちうる領域）であり、この基準（環境固有の事実・配線・罠）に単独では乗りにくい。乗せるには「この harness 固有の消費経路（Slack digest / Remote Control 越しの phone 読了）でしか成立しない事実」として書く必要がある——§7 参照。

## 3. skill / agent の報告契約

### `skills/search-first/SKILL.md` §3 Report（`SKILL.md:46-67`）
- L48: 「The report is the deliverable. Write it so the caller can pick from it」
- L56-58: 「Judgement is **prose backed by facts** — dates, versions, the concrete feature match. Strengths and weaknesses in sentences; the canonical home of "evidence, not scores" (ADR-0026)」——**ADR-0026 が退役した signal-first の原則の内在化コピー先として明示的に名指しされている場所そのもの**。
- L60-67: 固定テンプレ `## Scope searched` / `## Found` / `## Still unknown`——**末尾に "Still unknown" を置く**構造。見出しの並びは「範囲→発見→未知」で、結論を冒頭に集約する構造にはなっていない（quick/full 問わず）。

### `skills/task-triage/SKILL.md`（§2 Digest、§Cadence）
- L85-93 §2: 「one decision per message, in the order **background → what is at stake → options → recommendation → cost/reversibility**」——recommendation は **4 番目**、末尾から2番目。結論を先に置く構造ではなく、背景から積み上げる構造。
- L95-97: 「the digest is still the session's own closing reply — the human answers here, so the reasoning must be readable here (**Remote Control shows the reply**)」——ここが signal-first の価値が最も高い経路（§7 で詳述）。
- L102-107: Slack へは 1 cycle 1 メッセージ、**titles only, never the reasoning**——「`N decisions pending: 1) <title> 2) <title>`」の 1 行 digest 契約がある。これは既に signal-first 的（タイトルだけ、詳細は本セッションへ）。

### `skills/herdr-delegate/SKILL.md`
- L35-40「**捏造報告に注意**」——完了報告の**信頼性**についての契約(委譲先が実在しない成果物を捏造する事例)。
- L131-136 §4「検収 — 相手の完了報告を信用しない」「ground truth は `git status` / `git diff` であって相手の報告文ではない」——報告の**形**ではなく報告を信じない検収手順。signal-first（冒頭に結論）とは別軸。

### `skills/implementation-chain/SKILL.md`
- L3 description に「早期停止条件もここが正本」。L180 に `## 早期停止条件` 節。
- 報告契約そのものの節は無い（chain 編成の判断表が主体）。

### `agents/readme-judge.md`
- L3 description: 「集計しない named verdict（Publishable / Fix / Rewrite）を返す」
- L18-19: 「判定形式の正本: `~/.claude/skills/llm-as-judge/SKILL.md` — 二値チェック（1 行証拠必須）→ 反証プレッシャーテスト → **集計しない** named verdict」——**「1 行証拠」+ named verdict 契約の正本は `skills/llm-as-judge/SKILL.md`**（①binary checks / ②named holistic verdict / ③no aggregation、L41/L48/L61）。

### `agents/readme-clarity-reviewer.md:110`
「Never emit numeric scores — every finding is a concrete observation plus a suggested direction（**signal-first**）」——ADR-0026 が言う「インライン内在化完了」の**現物**。ここに signal-first という語が直接残っている数少ない生き残り。

**まとめ**: 出力の**評価契約**（score 禁止・named verdict・1 行証拠）は複数の skill/agent に内在化済み（ADR-0026 の想定どおり機能している）。だが「**応答/報告の冒頭に結論を置く**」という**構造の順序**を契約している場所は現行どこにも無い——search-first も task-triage §2 digest も、末尾または中間に結論・recommendation を置く構造。ここが空白。

## 4. hook の応答・報告介入

`settings.json` hooks 節（`settings.json:132-284`）の全列挙:

| Event | Matcher | Script |
|---|---|---|
| PostToolUse | `Edit\|Write` | `hooks/bats-autorun.sh` |
| PostToolUse | `Read\|Skill` | `hooks/log-skill-usage.sh` |
| PostToolUse | `Read\|Grep\|Bash` | `hooks/task-claims-reminder.sh` (timeout 10) |
| PostToolUse | `Task\|Agent` | `hooks/log-agent-usage.sh` |
| PostToolUse | `ExitPlanMode` | `hooks/plan-executor-notice.sh` (timeout 10) |
| PreToolUse | `Bash` | `validate-bash.sh`, `secret-scan-precommit.sh`, `verify-precommit.sh`, `bandit-precommit.sh`, `ruff-format-precommit.sh`, `harness-lint-precommit.sh`, `review-chain-notice.sh`（7 本連鎖） |
| PreToolUse | `Edit\|Write` | `hooks/docs-prewrite.sh`, `hooks/skill-create-notice.sh` |
| PreToolUse | `Task\|Agent\|Skill` | `hooks/review-model-notice.sh` (timeout 10) |
| PreToolUse | `Read` | `hooks/block-episode-logs.sh` |
| PreToolUse | `Grep` | `hooks/block-episode-logs-grep.sh` |
| SessionStart | `*` | `hooks/herdr-agent-state.sh session` (timeout 10) |
| UserPromptSubmit | (no matcher) | `hooks/contemplative-name-reminder.sh`, `hooks/log-skill-usage.sh` |

**Stop / SubagentStop hook は現在 0 本**。ADR-0035:43-44 で「`hooks/review-chain-notice.sh` の Stop branch を退役する。加えて evidence-file-notice と既存の Stop hook 3 本、合計 4 本の advisory script を退役する」——**応答終了時点で発火する hook は歴史的に全廃されている**。signal-first を hook で実装しようとすると、この退役の理由（827 bytes の反復 advisory が stderr にしか届かず、debug log 止まりだった／常駐コスト・正本 drift）を再度踏む可能性が高い。ADR-0035 §Alternatives「fingerprint suppression を加えて Stop hook を復帰する」も「commit 時の確認で足り、session を反復走査する必要がない」として却下済み。

`hooks/_advisory-common.sh:1-97` — hook が model へ文字列を渡す唯一の実装（封筒 `{"hookSpecificOutput": {"hookEventName": ..., "additionalContext": ...}}`）。既定 2048 字切り詰め（`ADVISORY_MAX`、上限 8192）。**advisory 経路は現存し機能している**（PreToolUse / SessionStart / UserPromptSubmit で 使用中）が、Stop 系には接続されていない。

## 5. `scripts/hooks/harness_lint.py` の機械検査

全 13 検査（`harness_lint.py:1-48` の docstring 列挙、file:line は各 `def lint_*`）:

1. settings.json パース可能性 + hooks 参照 script の実在
2. `agents/*.md` frontmatter — name/description/origin 必須 + model がエイリアスで明示（ADR-0033）（`harness_lint.py:222` `lint_agents`）
3. `skills/*/SKILL.md` 同上 + name とディレクトリ名一致（`harness_lint.py:259` `lint_skills`）
4. `rules/{common,python}/*.md` の origin メタデータ存在
5. rules/agents/docs の markdown 相対リンク解決可能性（`harness_lint.py:306` `lint_markdown_links`）
6. rules の「See skill(s): name」ポインタ解決可能性（`harness_lint.py:324` `lint_rule_skill_pointers`）
7. `rules/common/*.md` の rationale / review-when コメント存在（`harness_lint.py:353` `lint_rules_metadata`、ADR-0021）
8. rules の inline code bare path 参照先の実在（`harness_lint.py:425` `lint_rule_asset_refs`）
9. hooks の advisory envelope literal 存在（`harness_lint.py:459` `lint_advisory_envelope`）
10. hooks の共有部品 source パスが `${BASH_SOURCE[0]%/*}` 相対（`harness_lint.py:504` `lint_hook_source_paths`）
11. tests/*.bats の失敗握り潰し assertion 無し（`harness_lint.py:552` `lint_bats_assertions`）
12. `docs/adr/NNNN>=0044` に `## Review-when` 節必須（`harness_lint.py:410` `lint_adr_review_when`、ADR-0044）
13. 版差 marker 検査（`harness_lint.py:378` `lint_version_diff_markers`、ADR-0061）— 同一括弧内の日付 + 編集動詞（追加|追記|移設|移管|再編|明文化|更新済み|移行済み）を exit 3 で止める

**docstring 明記（`harness_lint.py:50-51`）**: 「description の良し悪し等の意味的品質は検査しない — それは skill-creator / stocktake 系の領分」。**「肯定形か禁止形か」を機械判定する lint は存在しない**——ADR-0070:124-127 が明言：「3 条件を機械 lint にする」は却下済み（「観測済み」「ゲート無し」は意味的条件で skill-creator §4 の草稿ゲートが検査、lint 化しない）。

**新しい rule / skill 節を足すと引っかかりうるもの**:
- rule として足すなら検査 4・7（origin/rationale/review-when 必須、先頭10行以内）を満たす必要がある。
- skill 節として既存 SKILL.md に追記するなら検査 13（版差 marker）に注意——「（2026-09-19 追加）」のような書き方は exit 3 で止まる。ADR-0061 の規律により**現行規則として書き、経緯は ADR に置く**必要がある。
- 新設 skill/rule 全般には ADR-0070 の 3 条件（grep 可能な具体的動作／既定挙動が逆と観測済み／機械ゲート無し）が禁止文を書く条件——「回答の冒頭に signal を置かないのを禁止する」ではなく「置く」という肯定形の指示にすれば、この制約自体には抵触しない。

## 6. docs/adr 要約

**ADR-0018**（2026-07-25, accepted）: Decision — Thariq のブログ（Claude 5 世代はシステムプロンプト大幅削減でも劣化なし）を受け、rules を 5,789→2,314 words（-60%）に圧縮。一般論は agent/skill へ吸収、gotcha だけ常駐維持。Scaffold Dissolution に「モデル世代交代」トリガーを追加。Review-when: 無し（ADR-0044 以前で対象外）。

**ADR-0035**（2026-08-02, accepted）: Decision — Review/Verify reminder の 3 層重複（rules/hook/skill）を hook 側の commit-time reminder 1 本（`review-chain-notice.sh`、PreToolUse のみ）に統合、Stop hook 系 4 本を全廃。`human-gate.md` / `output-register.md` / `patterns.md` / `hooks.md` を rules から退役。`when-code-when-llm` global skill も退役。Review-when: 無し。

**ADR-0061**（2026-09-02, accepted）: Decision — `/claude-api prompt-audit` が検出した「版差 marker」（改修時に前版との差分を本文に書く反復パターン、55件）を skill-creator §3 の文章規律 + `harness_lint.py` 検査13 として常設。Review-when（L73-79）: 次モデルリリースで migration-relative が再発したら動詞集合を広げる／偽陽性2回で動詞集合を狭める／Anthropic が該当パターンを有害から外したら §3 規律1を再監査。

**ADR-0070**（2026-09-16, accepted）: Decision — ADR-0065 の絶対形規約（「することだけを書く」）を緩和し、既定は肯定形・禁止は3条件（grep可能な具体的動作／既定挙動が逆と観測済み／機械ゲート無し）付きで許容。built-in subagent override は verbatim 写し（Explore.md 等）に統一。Review-when（L82-93）: 3条件下の禁止文が新規アイデアを拒む観測が出たら MEMORY.md Pending へ記録し肯定形へ戻す（観測窓 2026-10-12）／built-in の model-only 指定機構が出たら Explore.md 削除／CLI 版と写し元が食い違ったら diff して更新。

**`skills/generation-audit/SKILL.md`の判定基準**: verdict を持たない証拠収集オーケストレータ。Phase 1（runtime層採取・逐語引用）→ Phase 2（競合／冗長／ドリフトの3分類）→ Phase 3（4観点判定枠: 意図・根拠・鮮度・失効条件）→ Phase 4（stocktake系への委譲）。「競合=悪」と機械適用しない（`SKILL.md:68`）——自作資産が製品既定を意図的に上書きしている可能性を認める。

**「旧世代向けの反復強調・網羅的手順は削る」方針が新しい出力規律の追加にかける制約**:
1. ADR-0018/0035 の**主旨は「削る」方向の圧**——新規常駐（新しい rule 節）を足すこと自体が既定の逆張りになる。足すなら「Claude 5世代でもなお成立する環境固有の事実」であることを明示する必要がある（rules/README.md の採用基準）。
2. ADR-0061 の版差 marker 規律により、「以前は signal-first があったが退役し、今回また足す」という**経緯の書き方は本文に書けない**（lint検査13で機械的に止まる）——書くなら ADR 側（本 ADR 候補）に経緯を置き、rule/skill 本文は現行規則のみで書く。
3. ADR-0070 により、signal-first を「禁止」（例:「結論を末尾に書くな」）ではなく「肯定形」（「結論を冒頭に書く」）で書けば規約に適合しやすい。
4. ADR-0026 自体の Review-when 相当（Neutral/Follow-ups, L96-99）: 「効果の実測は、曖昧な plan 1 本への /grill-me 実行で行う」——signal-first 復活も同様に、**測定可能な効果検証手段**を先に決めてから足すのが一貫した作法（この harness の ADR は判定基準無しの復活を許容していない）。
5. ADR-0026 の**再発防止条件**そのもの: 「第三に、モデル世代（Claude 5 世代）は signal-first 相当の確認・取捨選択を既定で行えると判断した」——**この前提そのものが変わった/崩れたという明示的証拠**（例: task-triage digest で recommendation が末尾に埋もれて見落とされた実例）が無いと、ADR-0026 の decision を単純に上書きするだけの薄い ADR になる。

## 7. 人間が小さい画面や通知で読む経路

- **Slack digest**（`task-triage/SKILL.md:102-107`）: 1 cycle 1 メッセージ、`scripts/notify-slack.sh` 経由、**titles only, never the reasoning**。既に「1行タイトルだけ」という signal-first 的構造を持つ。ここに signal-first を追加適用する価値は**低い**（既に達成済み）。
- **launchd 無人セッション**（`task-triage/SKILL.md:225-269`「Where the loop lives」）: `scripts/launchd/com.shimomoto.triage-{harness,ca}.plist` が `scripts/triage-tick.sh <repo> <agent-name> "<display>"` を定時実行（harness Sun 06:30、CA Wed 17:07 / Sat 14:07）。tick は生きている triage セッションを探し、無ければ `spawn-session` で立て、`herdr agent prompt` でサイクルを投げる。**tick 自身は 판단せず、自身の異常だけを Slack に報告**（spawn失敗・stall・blocked 等）。
- **task-triage §2 Digest が最重要経路**（`SKILL.md:95-97`）: 「the digest is still the session's own closing reply — the human answers here, so the reasoning must be readable here (**Remote Control shows the reply**)」。**これが signal-first の価値が最も高い場所**——無人サイクルの結果を iPhone の Remote Control で読む human が、`background → stakes → options → recommendation → cost` という現行順序（L88）で**最後から2番目に recommendation**を読むことになる。小さい画面でのスクロール負荷と「戻ってくる価値があるか」の即断判定（L106「titles let the owner judge from the phone whether returning now is worth it」）を考えると、**冒頭に named recommendation を置く価値が最大**。
- `skills/spawn-session/SKILL.md:3,10` — iPhone の Remote Control 越しに新規セッションを起動する経路そのもの（「生きている任意のセッションから（多くは iPhone の Remote Control 越しに）呼んで」）。spawn 自体は出力を生成しないが、spawn 後のセッションの digest/報告がこの経路を通る。
- `scripts/launchd/` には `growth-fable-prompt.txt` / `weekly-gate-ca-prompt.txt` という定時投入プロンプトも存在——これらのセッションの締めの報告も同じ「無人で走り、人間は後から画面外で結果だけ見る」構造。

**結論**: signal-first の価値が最も高い経路は **task-triage の Digest（§2）の返信そのもの**——Remote Control 越しに phone で読まれることが SKILL.md に明記されている唯一の場所であり、既に「Slack には titles only」という半分の signal-first を実装済みだが、**セッション本体の返信の構造（background→stakes→options→recommendation→cost）はまだ結論後置き**。

---

## まとめ表: 出力の形を制御できる置き場所の候補と先例

| 置き場所 | 制御できる範囲 | 現行harnessでの先例 | signal-first 復活への適合 |
|---|---|---|---|
| **常駐 rule** (`rules/common/*.md`) | 毎セッション、全消費点に一律適用 | `output-register.md`（ADR-0030 新設 → ADR-0035 で退役）／ akc-cycle.md の旧 Signal-first 節（ADR-0026 で退役） | **既に2度退役した経路**。rules/README.md の採用基準（環境固有の事実・配線・罠）に「出力の順序作法」は原則乗らない。足すなら ADR-0026 の前提崩れの明示証拠が要る |
| **output-style** (`settings.json` `outputStyle`) | Claude Code 組み込み style 経由、product 既定を上書き | `outputStyle: "Concise"` が既に signal-first 的な `recap` 圧と**矛盾**していると ADR-0061:42 が指摘（未解決）。自作 `output-styles/` は無し | 自作 style を新設すれば全消費点に効くが、product 同梱 style との衝突を先に解く必要あり。最も広く効くが最も重い |
| **skill の報告契約** (`SKILL.md` の Report/Digest 節) | その skill が発火した時だけ、消費点ごとに独立して定義可能 | `search-first` §3（ADR-0026 の内在化先そのもの）／ `task-triage` §2 Digest／ `readme-judge`+`llm-as-judge`（1行証拠+named verdict） | **最有力**。ADR-0026 が既にこの経路を「正本」と認定済み。task-triage §2 の順序を `recommendation` 先出しに変えるのが最小差分で最大効果 |
| **agent 定義** (`agents/*.md`) | その agent が起動された時だけ | `readme-clarity-reviewer.md:110`（"Never emit numeric scores...signal-first" のインライン内在化） | 既存 agent への追記は harness_lint の版差 marker 検査13 に注意すれば可能。新規 agent は ADR-0070 built-in override の verbatim 規約対象外（自作なら通常の肯定形規約） |
| **hook** (`settings.json` hooks 節 / `hooks/*.sh`) | 発火時刻を固定できる（Stop等）が、advisory 文字列は毎回反復し常駐コスト化 | Stop/SubagentStop hook は ADR-0035 で**全廃**済み（827 bytes 反復・debug log 止まりの実害）。advisory envelope 自体（`_advisory-common.sh`）は現役 | **最も先例が悪い**。Stop hook 経由の「毎回同じ signal-first リマインダー」は ADR-0035 の反省をそのまま再演するリスクが高い |
| **`--settings` による per-invocation 上書き** | 特定 subprocess 呼び出しだけ | `skill-comply/scripts/child_settings.py` の `pin_output_style`（逆方向: styleを剥がす用途） | 技術的には可能（task-triage の digest 生成 subprocess にだけ style を強制注入）だが、現行 task-triage の digest は同一セッション内の closing reply であって別プロセス起動ではないため、**この経路は今回の主要ユースケースに直接は乗らない** |

**推奨の当たり**: ADR-0026 が示した「原則の正本は消費 skill 側」という設計判断を踏襲するなら、復活先は **`skills/task-triage/SKILL.md` §2 Digest の順序変更**（`background → stakes → options → recommendation → cost` を `recommendation（signal）→ background → stakes → options → cost` へ、または冒頭に1行 verdict を追加）が最小差分・最大効果。次点は `search-first` §3 Report のテンプレに冒頭 verdict 行を足すこと（ただし ADR-0026 は「verdict 行は廃止、肯定形『Judgement is prose backed by facts』」— L46 の注記 — と既に述べており、ここへの verdict 行復活は ADR-0026 の decision と真正面から衝突するため、変更するなら ADR-0026 への supersede/annotate が要る）。常駐 rule への復活は、ADR-0026 の Decision を上書きするだけの薄い理由（前提崩れの明示証拠なし）では通りにくく、著者が「モデル世代交代 + Claude 5世代でも signal-first 相当を既定でやってくれない」という反証データを持つ場合のみ筋が通る。

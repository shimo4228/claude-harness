# ADR-0070: 「することだけを書く」を「既定は肯定形、禁止は 3 条件付き」に緩和し、built-in subagent の override は verbatim 写しにする

## Status

accepted

## Date

2026-09-16

## Context

[ADR-0065](./0065-drop-adr-consultation-wiring-and-build-or-not-gate.md) §Decision 第 4 項
（2026-09-14）は「することだけを書く。やめる項目は本文から消す」を絶対形で
`rules/common/skills.md`・`skills/skill-creator/SKILL.md` §3 先頭 bullet・§4 Hygiene 問・
memory `feedback_write_only_what_to_do.md` に配線した。出所は ADR-0065 Context の観測 —
ADR / memory の却下記録が新規アイデアを止める — と著者発話「するなと言われたら結局想起する
から何も言わない方がマシだろ」。

2026-09-16、著者は built-in Explore subagent を Sonnet で走らせたかった。公式 docs
（<https://code.claude.com/docs/en/sub-agents>、参照日 2026-09-16、実機 Claude Code 2.1.273）の
model 解決順は「呼び出し時の model 引数 > agent 定義の frontmatter `model`（`inherit` 含む）>
`CLAUDE_CODE_SUBAGENT_MODEL` > main 会話の model」（v2.1.251 以降）で、docs は
「`CLAUDE_CODE_SUBAGENT_MODEL` 単独では built-in Explore / Plan の model は変わらない」と明記し、
公式の経路は「Explore という名前の user agent を置いて `model` を持たせる」。CHANGELOG
（<https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md>、参照日 2026-09-16）:
2.0.17「Introducing the Explore subagent. Powered by Haiku」、2.1.198「The built-in Explore
agent now inherits the main session's model (capped at opus) instead of running on haiku」。

絶対形の規約の下で書いた最初の草稿（未コミット）は built-in の本文を肯定形で書き直したもので、
CLI 2.1.273 の bundle から取り出した built-in Explore の system prompt と比べると 2 つ欠けていた:
「=== CRITICAL: READ-ONLY MODE ===」の禁止列挙節と、定義の `omitClaudeMd: true`（CLAUDE.md /
rules を読み込まない）。後者は Explore を spawn するたびに rules 全体が載る差になるので binary
照合の時点で足し、skill-creator §4 の草稿ゲートを通した版が commit `31e7010` として入った
（`agents/readme-reviewer.md` / `agents/readme-clarity-reviewer.md` の model 変更も同 commit）。
その版も肯定形の書き直しで、READ-ONLY 節は無く、built-in との挙動差を検証する手段が無い。

禁止文に関する根拠は 3 つある。(a) 逆効果の実証があるのは文体・内部過程への禁止 — Claude
Code 2.1.273 同梱 skill `claude-api` の SKILL.md、Common Pitfalls 節の項「Disabling thinking on
Claude Opus 5 has two failure modes」は、thinking を切ったまま運用する場合「delete any
don't-think/don't-reason rule (it makes tag leakage worse), don't name thinking tags」と書き、
同じ項で肯定形の追加指示と禁止文 1 つ（"Do not include internal or system XML tags in your
response"）を推奨する — 文体・内部過程への禁止は消し、具体的出力への禁止は残す、という
本 ADR と同じ線引きである。(b) 具体的動作の禁止は Anthropic 自身が built-in Explore / Plan の
prompt で使い、CHANGELOG 2.0.30「Fixed Explore agent creating unwanted .md investigation files
during codebase exploration」が同じ動作クラスへの対処として存在する。(c)「/tmp にも一時
ファイルを作らない」のように肯定形へ自然に言い換えられない境界がある。

著者（2026-09-16）:「流石に built-in のエージェントは同じ内容の方がいいんじゃない？」
「禁止列挙をスキル本文に全く書かないという方針はちょっと問題。なるべく書かないくらいの規約に
した方が良くない？」。同日、Anthropic 宛に「built-in subagent の model だけを指定できる機構」
の feedback 下書きを作成した（送信は著者判断）。

## Decision

1. 規約を緩める。既定は肯定形で書き、やめる項目は本文から消す。禁止を書けるのは、対象が
   grep 可能な具体的動作で、既定挙動が逆だと観測されていて、機械ゲートが無いとき — 理由を
   1 句添える。文体・内部過程への禁止は肯定形に言い換える。外部 repo 由来の未改変 prompt
   （origin が外部）は写しのまま置く。配線先: `rules/common/skills.md` の 1 文、
   `skills/skill-creator/SKILL.md` §3 先頭 bullet（正本）と §4 Hygiene 問、
   `agents/adr-reviewer.md` §8 の禁止文の検査項目、memory `feedback_write_only_what_to_do.md`
   と `MEMORY.md` の 1 行 — ADR-0065 第 4 項が名指しした配線先と同じ集合。3 条件の文言は
   skill-creator §3 を正本とし、他の配線先は同じ語（「grep 可能な具体的動作」）で書く。
   ADR-0065 §Decision 第 4 項に日付つき注記を置く（partial weakening。第 1〜3 項は本 ADR の
   対象外）。
2. built-in subagent の override は verbatim 写しにする。目的が field の固定（model 等）だけの
   とき、本文は CLI bundle から取り出した built-in の system prompt を platform 分岐だけ展開
   して写し、description も原文どおりにし、`disallowedTools` と `omitClaudeMd` も built-in と
   同じにする。origin は外部 repo（`anthropics/claude-code`）とし、写し元の CLI 版を本文冒頭
   のコメントに置いて更新時に diff できるようにする。実例: `agents/Explore.md`、
   `model: sonnet`。skill `agent-stocktake` Phase 2 Stage 1 に写し専用の 1 問（写し元の版と
   実機版の照合）を足し、写しには suppression / over-constraint の 2 問を適用しない — 本文は
   vendor のもので、harness の文体規約の対象外。
3. 付随の model 配置: `settings.json`（git 管理外）に
   `"env": {"CLAUDE_CODE_SUBAGENT_MODEL": "opus"}` — frontmatter を持たない agent
   （general-purpose、teammate、workflow agent）の既定にする。frontmatter を持つ agent は
   frontmatter が勝つ（`_FORCE` は Alternatives 参照）。`agents/readme-reviewer.md` を fable、
   `agents/readme-clarity-reviewer.md` を opus にする（commit `31e7010` で適用済み）。

   > **注記（2026-09-25, [ADR-0077](./0077-readme-review-single-judge-with-claims-check.md)）**: `readme-reviewer` と
   > `readme-clarity-reviewer` は退役し、問いは `readme-judge`（opus のまま）の checklist に移った。
   > この項の model 配置のうち、README の 2 本は対象が無くなった。`CLAUDE_CODE_SUBAGENT_MODEL` の既定は変わらない。

## Review-when

- 3 条件の下で書いた禁止文を根拠に新規アイデアが拒まれる観測が出たら、ADR-0065 Review-when
  と同じく `MEMORY.md` Pending に日付つき 1 行を残し、その禁止文を肯定形へ戻す。ADR-0065 の
  観測窓（2026-10-12）は据え置く — 緩和後の観測も同じ Pending 行に入れ、根拠が 3 条件で足した
  禁止文なら行に `ADR-0070` と印を付けて 0065 の判定から分離する。
- Claude Code が built-in subagent の model だけを指定する機構を出したら（feedback 下書き
  2026-09-16 の要望）、`agents/Explore.md` を削除してそれを使う。
- `agents/Explore.md` 冒頭コメントの写し元 CLI 版と `claude --version` が食い違ったら、bundle の
  built-in prompt と diff して写しを更新する。照合の発火点は skill `agent-stocktake` Phase 2
  Stage 1 の「External-origin copy current?」問。built-in の既定が再び低コスト model に戻ったら
  override を削除する。
- 3 条件で禁止文を足す commit は message 本文に `ADR-0070` を引く。2026-12-16 に
  `git log --since=2026-09-16 --grep=ADR-0070 -- rules skills agents docs/adr` を数える。
  対象は origin 外部の写しを除く自作文書。0 件は「3 条件が使われなかった」であって抑止の
  証拠ではないので、簡素化するか事例無しのまま残すかは著者が決める。

## Alternatives Considered

### 絶対形を維持し、Explore は origin policy の「外部由来・未改変」例外だけで扱う

著者が絶対形そのものを行き過ぎと判断した。origin 例外だけでは自作文書の硬い境界を書く手段が
残らない。却下。

### built-in Explore を肯定形で書き直した版（最初の草稿）を使う

built-in との挙動差を検証する手段が無く、`omitClaudeMd` を落としていた。CLI 更新時に diff も
取れない。却下。

### 本文を最小限にした同名 agent で `model` だけ固定する

同名の user agent は built-in の定義を丸ごと置き換える（docs の "overrides the built-in"）ので、
本文最小 = 指示の無い Explore になる。model だけを継ぐ経路は Claude Code に無い（feedback
下書きの要望はこれ）。却下。

### `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`

全 agent の frontmatter を上書きし、architect（fable）が opus に落ち、sonnet / haiku 指定の
agent が opus に上がる。却下。

### Explore を spawn するたびに Agent tool の `model: "sonnet"` を渡す

main loop が毎回覚えている前提になる。却下。

### 3 条件を機械 lint にする

「観測済み」「ゲート無し」は意味的条件で、skill-creator §4 の草稿ゲートが検査する。lint 化
しない。

## Consequences

### Positive

- 硬い行動境界を必要な箇所に書ける。
- built-in override の挙動差はゼロになり、CLI 版と diff できる。
- Explore は rules を載せずに Sonnet で走る。

### Negative

- 3 条件は意味的なので執行は草稿ゲートで、著者は一律規則でなく都度判断する。
- `agents/Explore.md` の写し元は公開 source でなく CLI bundle なので、更新は手動の diff に
  なる。
- harness の自作文書は肯定形、写した外部 prompt は英語の禁止列挙 — 2 つの register が origin
  印つきで共存する。
- commit `31e7010` の harness 版 Explore が持っていた報告契約（結論 1〜3 文 + `path:line` +
  探索範囲の明示）は消え、呼び出し側（`skills/implementation-chain/SKILL.md`、
  `skills/session-judgment-mining/SKILL.md`、`skills/search-first/SKILL.md` の Explore 配線）は
  vendor 既定の報告様式を受ける。

### Neutral / Follow-ups

- `settings.json` の env は git 管理外なので、opus 既定の記録は本 ADR と local file だけに
  ある。値の drift を検知する手段は subagent 実行中の `/tasks` の model 表示だけ。
- ADR-0065 §Decision 第 4 項に日付つき注記済み（本 ADR）。

# ADR-0084: 自作 skill codex-review を退役し、cross-model の接点を OpenAI 公式 Codex plugin に置き換える

## Status

accepted — [ADR-0013](./0013-cross-model-review-seam-via-codex.md) の Decision 1（`codex-review` skill と
read-only wrapper の新設）を置き換える。ADR-0013 の Decision 2（スループット系は Claude native に寄せる）は
対象外。[ADR-0055](./0055-review-chain-single-pass-regression.md) Decision 2 と
[ADR-0077](./0077-readme-review-single-judge-with-claims-check.md) Decision 4 の codex-review の参照先を
変える（opt-in の規律は変えない）。いずれも部分的な変更で、注記は各 ADR 側

## Date

2026-09-27

## Context

- `skills/codex-review/` は `codex review` を包む `codex-review.sh`（フラグ allowlist で read-only を保証し、
  `-c approval_policy="never"` を pin）と、plan 段の前提反証用の `codex-plan-challenge.sh`、それぞれの
  `test-*.sh` を持っていた。ADR-0013 の Negative が予告したとおり、Codex CLI の変化への追従が実際に
  発生していた: 33d23f5（codex-cli 0.142 の scope / prompt 排他への対応）、b161b5e（`-m` を review
  subcommand の前へ）
- 退役のきっかけ: 2026-09-27、`~/.codex/config.toml` の model 固定（gpt-6-luna）で ChatGPT アカウントでの
  実行が HTTP 400 になり skill が動かなかった（zenn-content セッションで観測）。原因は skill でなく config
  で、config は著者承認のもと `model = "gpt-5.6-sol"` に変更済み。退役の理由は故障そのものでなく、上記の
  追従コストである
- 著者の決定（2026-09-27）:「Codex-review は退役でいい」「追従コストがあるので自作スクリプトは破棄」
- 置き換え先は OpenAI 公式 plugin `codex@openai-codex`（repo `openai/codex-plugin-cc`、導入時 v1.0.6、
  gitCommitSha `db52e28f4d9ded852ab3942cea316258ae4ef346`、user scope）。以下の仕様はこの版の plugin 同梱
  ファイル（`plugins/cache/openai-codex/codex/1.0.6/` 配下、gitignore 対象）から読んだ:
  - `/codex:review`: Codex 内蔵の reviewer による working tree / branch の diff review。焦点テキストは不可
  - `/codex:adversarial-review [focus]`: 同じ対象選択に焦点テキストを足せる。plugin の
    `prompts/adversarial-review.md` は "adversarial software review" 固定で、auth・データ消失・並行性等を
    優先し、"Do not include style feedback" とし、verdict は `approve` / `needs-attention` の 2 値。
    untracked ファイルは本文を inline で渡すが、24 KiB を超えるものは skip される（`scripts/lib/git.mjs` の
    `MAX_UNTRACKED_BYTES`）
  - `/codex:rescue`: `codex:codex-rescue` subagent 経由で companion script の `task` を呼ぶ。sandbox は
    `--write` が無ければ read-only。subagent の description は "Proactively use when Claude Code is stuck…"
    で、既定では `--write` を付け、依頼文を `gpt-5-4-prompting` skill で書き直してよいとされている
  - `/codex:review` と `/codex:adversarial-review` は `disable-model-invocation: true`。`/codex:rescue` と
    `/codex:setup` には無く、Claude が自分で起動できる
  - thread の既定は `approvalPolicy: "never"`・`sandbox: "read-only"`（`scripts/lib/codex.mjs`）。model は
    指定が無ければ null で、Codex の config 既定に従う
  - SessionStart / SessionEnd / Stop の hook を登録する（`hooks/hooks.json`）。Stop hook は review gate が
    無効でも毎ターン終了時に node を起動し、早期 return する
- 導入後の検証（2026-09-27、zenn-content の working tree）: `setup` は ready（codex-cli 0.154.0、ChatGPT
  login）。`review` は gpt-5.6-sol で HTTP 400 なく完走した。`adversarial-review` に焦点テキストを付けると、
  untracked の記事原稿（21,991 bytes）を読んで行番号付きの指摘を返した。同じ `review` が zenn-content の
  未 commit 差分に対し、prose の初見読者チェックを adversarial-review へ移すと文体の指摘が落ちる、と指摘した

## Decision

1. `skills/codex-review/`（SKILL.md、`codex-review.sh`、`codex-plan-challenge.sh`、`test-codex-review.sh`、
   `test-codex-plan-challenge.sh`）を削除する。cross-model の接点は plugin `codex@openai-codex` とする
2. 旧 skill の用途を次の command に割り当てる:
   - diff review → `/codex:review`
   - 焦点を指定した diff の反証 → `/codex:adversarial-review <focus>`
   - plan 段の前提反証と、README 等の prose review → `/codex:rescue` を read-only で使う（`--write` を付けず、
     prompt に「read-only。指摘だけを返し、設計やパッチは書かない」と対象の path・観点を書く）。prompt を
     自由に書け、diff に入っていないファイルも読めるので、ソフトウェアのリスク観点に固定された
     adversarial-review より旧 skill の prompt 駆動の形に近い
3. 起動は著者の明示要求のみとする（ADR-0055 の opt-in 規律をそのまま plugin に当てる）
4. harness は Codex の model を指定しない。Codex の config 既定に従う
5. Codex の出力は untrusted input として扱い、verdict は Claude が持つ
6. 参照を付け替える: `skills/implementation-chain/SKILL.md`（description と opt-in 名簿）、
   `skills/readme-writer/SKILL.md`（prose 観点の prompt を read-only の `/codex:rescue` へ）、
   `skills/herdr-delegate/SKILL.md`（NOT for の行き先）、`skills/harness-sync/SKILL.md`（単独 skill repo の
   同期行を削除）、`hooks/review-model-notice.sh` のコメント、`hooks/README.md`、
   `tests/review-model-notice.bats`（取り違え防止のテストは plugin の名前で残す）、
   `skills/skill-stocktake/results.json`（退役した skill の項目を削除）。次は触らない: 指摘の出所を書いた
   既存コメント、`.claude/verify.sh`（`skills/*/test-*.sh` の汎用 glob で拾うので変更不要）、
   `skills/skill-comply/results/implementation-chain.spec.yaml`（過去の測定で固定した試験問題。
   `review_cross_model` は `required: false`）

## Review-when

- 著者が求めていない `codex:codex-rescue` の起動が 1 件見つかる → 塞ぎ方（PreToolUse hook か permissions
  deny）を決める。見張りは task-triage のサイクルで判断役が行い、transcript（`~/.claude/projects/**/*.jsonl`）
  を `"subagent_type":"codex:codex-rescue"` で grep して、同じ turn の著者 prompt に `/codex:rescue` が
  あるかを照合する
- plugin の `adversarial-review` が prompt の差し替えや prose 用のモードを持つ → Decision 2 の prose review の
  割り当てを見直す
- Codex CLI の更新や `~/.codex/config.toml` の model 指定で plugin の `setup` / `review` が失敗し、上流でも
  直らない → 薄い wrapper を再び持つかを判断する
- read-only の `/codex:rescue` が設計やパッチを返す、または subagent の依頼文の書き直しで「指摘だけ」の
  指示が落ちる → Decision 2 の rescue の割り当てを見直す

## Alternatives Considered

### (a) codex-review を残し、model 指定だけ直す

直接の故障は config の変更で消える。しかし allowlist と CLI の呼び方の追従（33d23f5、b161b5e）は Codex の
更新ごとに残り、著者はこの追従コストを理由に破棄を決めた。

### (b) `codex-plan-challenge.sh` だけ残す

plan 段の前提反証は plugin の command に直接の対応が無い。しかし残す script は (a) と同じ追従コストを
持ち、read-only の `/codex:rescue` に自由な prompt を渡せば同じ入出力の形を作れる。

### (c) plan 段の前提反証と prose review を `/codex:adversarial-review` でやる

prompt がソフトウェアのリスク観点で固定されて文体の指摘を除外し、対象は diff と 24 KiB 以下の untracked
ファイルに限られ、verdict は 2 値になる（2026-09-27 の検証と plugin の `prompts/adversarial-review.md`）。
焦点テキストだけでは「反証 / 欠落 / 代替案」や prose の観点を返す形にならない。

### (d) `codex mcp-server` を登録する（ADR-0013 (c) の保留案）

Codex をフルエージェントとして起動する形で、review 単機能には過剰という ADR-0013 の評価は変わらない。
公式 plugin が runtime の管理を持つので、登録する理由も無くなった。

## Consequences

### Positive

- 自作 script の追従が無くなる。CLI の呼び方の変化は plugin の上流が吸収する
- harness の repo に model 指定が残らない。model は Codex の config 既定に従う
- 24 KiB 以下の untracked ファイルは diff に載せずに adversarial-review へ渡せる

### Negative

- model 指定は harness の外（`~/.codex/config.toml`）に移っただけで、そこが壊れれば plugin も同じ HTTP 400
  で止まる。config の冒頭コメントは「モデルは明示しない」だが、現在は `model = "gpt-5.6-sol"` を指定している
- adversarial-review の prompt は差し替えられない。prose を流すと文体の指摘が落ちうるので、prose は
  rescue に回す。zenn-content の初見読者チェックの扱いは zenn-content 側の判断（同 repo の ADR）で決める
- plugin は `codex:codex-rescue` subagent を持ち込む。description が自発起動を促し、既定で `--write` を
  付けるので、Decision 3 の opt-in は規約と観測（Review-when）で守ることになり、機械的には保証されない。
  agent を deny すると `/codex:rescue` と Decision 2 の rescue の用途も使えなくなるので塞いでいない
- plugin は SessionStart / SessionEnd / Stop の hook を持ち込み、毎ターン終了時に node が走る。harness の
  hook と違い repo の lint・bats の対象外で、plugin の更新で内容が変わりうる
- plugin の版は pin していない。Context の仕様は v1.0.6（`db52e28f`）のもので、更新で変わりうる
- 旧 skill の read-only 保証（フラグ allowlist と回帰テスト）は失われ、plugin の既定（`approvalPolicy:
  "never"`・`sandbox: "read-only"`、`--write` が無ければ read-only）に依存する。旧 wrapper が
  `approval_policy` を pin した根拠（2026-08-22 security-reviewer HIGH、config の
  `approvals_reviewer = "auto_review"`）は plugin の既定が同じ値なので満たされる

### Neutral / Follow-ups

- plugin の有効化は `settings.json` の `enabledPlugins`（gitignore 対象）にあり、repo からは確認できない
- 戻すコスト: `skills/codex-review/` は git 履歴から復元できる。plugin は `settings.json` で無効化するか
  uninstall する。公開 repo `shimo4228/codex-review` は著者が archive するまでそのまま残る（公開物の変更
  なので人間の操作）
- plugin の stop-time review gate（`/codex:setup --enable-review-gate`）は無効のまま使う

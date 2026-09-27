# Signal-first の復帰 — 「読者の注意は 1 チャネル」を output style + 機械ゲートで持つ

## Context

著者が戻したい理由（本セッションで確認）: **対話セッション全般**で (1) 応答・報告が肥大する、
(2) **一度に複数のことを聞いてくる — これを一番やめてほしい**。調査の発散（旧 intake 側）は
挙がっていない。

旧 Signal-first 常駐節（`rules/common/akc-cycle.md`）は ADR-0026（2026-07-31）で退役した。理由は
①消費 skill への内在化完了 ②常駐の抑制圧力が grill-me の要件質問を減らした実害 ③Claude 5 世代は
native にできる（downward）。今回の症状は ③ の部分反証になる — 「score を出さない」類は内在化で
足りているが、**人間の注意を 1 チャネルとして扱う対話の形**は既定では出ていない。

そのまま戻さない理由（調査で確定した制約）:

- 出力の形を常駐 rule で持つ試みは 2 度退役している（`output-register.md` ADR-0030→0035、
  Signal-first 節 ADR-0026）。`rules/README.md` の採用基準にも乗りにくい
- Stop hook の反復 advisory は ADR-0035 で全廃済み
- 旧節は「出すな」型の抑制で、grill-me と衝突した。今回の要求は**問いの総数を減らすことではなく
  直列化**なので、抑制でなく「1 メッセージ 1 判断」という肯定形で書けば衝突しない
- `settings.json:319` の `outputStyle: "Concise"` は system prompt の recap 指示と矛盾する
  update-suppressor として ADR-0061 が flag 済み・未解決。肥大の対策が「一律に短く」という
  鈍器になっており、「何を残すか」の基準（= signal）を持っていない

## 提案する形

**原則を「規則」でなく「読者の記述」として、人間向け出力の正規スロット（output style）に置き、
grep 可能な 1 点だけ機械ゲートで執行する。** `llm-first-code.md` の帰結どおり — 人間可読性の予算は
出力の文面に払う／基準の執行者は機械ゲート。常駐は 1 増 1 減（Concise を置換）で純増なし。
subagent と `claude -p` utility（`skill-comply` の `pin_output_style`）には届かないので、読者が
LLM の経路を汚さない。

### 1. 自作 output style `output-styles/signal-first.md`（新規）

本文の草稿（肯定形・版差語なし・約 10 行。frontmatter は Step 0 で照合した現行仕様に合わせる。
coding 指示を保持する設定を必ず付ける）:

```markdown
読者は 1 人の practitioner で、注意は 1 チャネル。読むこと自体が、このループで最も希少な
資源を消費する。

- 応答は読者の次の行動を変える情報で構成する。冒頭 1〜2 文で結論（何が分かった / 何をした /
  何が要る）を言い、残りはそれを支える最小限にする。経緯・探索過程・却下案は求められたときに出す
- 読者に求める判断は 1 メッセージに 1 つ。未決が複数あるときは、次の行動を最も変える 1 問を
  選んで聞き、残りは答えを受けてから順に聞く（先の答えで消える問いが多い）。答えに依存しない
  作業は聞く前に進めておく。AskUserQuestion は `questions` 1 件で呼ぶ
- 問いには推奨と、その推奨で進めた場合に起きることを添える
- 明示起動された interview（/grill-me、/mondo）の間は問いが成果物 — 総数は絞らず、1 問ずつ出す
```

`settings.json` の `outputStyle` を `"Concise"` からこの style へ差し替える。

### 2. 機械ゲート `hooks/ask-one-question.sh`（新規、PreToolUse / matcher `AskUserQuestion`）

- `jq '.tool_input.questions | length'` が 2 以上なら block。reason は固定文言:
  「判断は 1 メッセージに 1 つ。次の行動を最も変える 1 問を選んで聞き直す」
- 違反時だけ発火するので ADR-0035 が退役させた反復 advisory にならない。tool input の中身は
  印字せず件数だけ見る（`security.md` の injection 面に載せない）
- block の出力形は `hooks/block-episode-logs.sh` の `{decision:"block", reason}` に倣う。
  block 回数を 1 行ログに残す（置き場は `hooks/log-skill-usage.sh` の先例に倣う）— これが失効判定の計器
- `tests/ask-one-question.bats`: questions 1 件 = 無出力 / 2 件 = block / questions 欠落・
  不正 JSON = allow（fail-open）
- 散文中の複数質問は機械ゲートにしない（regex で意味は測れない — feedback_regex_vs_semantic）。
  style 本文が担う

### 3. 記録

- ADR 新規（`adr-writer` で採番、起票基準「ゲート追加 + 旧 ADR 注記」に該当）。Review-when:
  block ログが 30 日間 0 件 → hook を溶かす（style だけで再現 = held-out transfer の証拠）/
  /grill-me 終了時の未解決 decision point が ADR-0026 の計測より増えた → interview 行を見直す /
  product の style 仕様変更
- 注記を 2 箇所: ADR-0026 Context 第三（downward 判定の部分反証、原則の正本が消費 skill 側にある
  点は不変）、ADR-0061 の Concise follow-up（本 ADR で解消）
- `docs/adr/README.md` の index、`CLAUDE.md` Layout に `output-styles/` を 1 行

## 実装手順

0. **仕様照合**（knowledge-staleness）: `claude-code-guide` agent で custom output style の現行仕様
   （置き場・frontmatter key・coding 指示保持の key・subagent への非継承）と PreToolUse の block
   出力形を一次ソースで確認。custom style が使えない場合の fallback は、同じ本文を
   `rules/common/` の新 rule（origin / rationale / review-when 付き）に置く
1. 実行者の決定は skill: `implementation-chain`（本セッションは judge-tier → build-tier へ dispatch が既定）
2. TDD: bats を先に赤で書く → hook 実装 → `settings.json` に hook 配線と `outputStyle` 差し替え
3. output style 本文を置く
4. ADR + 注記 + index + CLAUDE.md
5. `.claude/verify.sh`（harness lint / bats）→ Review → commit。未追跡 `skills/synced/` の
   lint 違反は本 diff と無関係（直近 commit と同じ扱いを著者に確認）

## Verification

- `bats tests/ask-one-question.bats` 緑、`python3 scripts/hooks/harness_lint.py` が本 diff で新規違反なし
- 新規セッションで `/config` または status から style が signal-first になっていること
- 実地: 未決が 2 つ以上ある曖昧な依頼を 1 本投げ、(a) 冒頭 1〜2 文が結論 (b) 問いが 1 件
  (c) AskUserQuestion の 2 件呼びが block されることを確認
- 回帰: 曖昧な plan 1 本に /grill-me を実行し、終了時の未解決 decision point 数を ADR-0026 の
  Follow-up と同じ指標で見る（質問数は指標にしない）

## 範囲外

旧 intake 側（調査前に signal を定義する）は症状が挙がっていないので戻さない。task-triage
Digest の順序（recommendation が 4 番目）は同じ原則の適用先候補だが、今回の経路（対話）と別なので
commit message に 1 行残すだけにする。

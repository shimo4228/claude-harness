kind: external
# plan の前に調査を必ず走らせる仕組みに、既存の仕様・先行実装・他エージェントの流儀・調査手法で使えるものはあるか

as-of 2026-10-04。general-purpose subagent 4 本を並列（角度: 公式仕様 / Claude Code 向け先行実装 / 他エージェントの
plan・custom mode / 深い調査と図付き plan の手法）。各 20 calls 前後。WebFetch は要約を返すので、「全文」は要約経由の
全文を指す。plan: [../research-plan-mode.md](../research-plan-mode.md)、ADR: [ADR-0086](../../adr/0086-research-gate-before-plan.md)。

## Scope searched

- **公式仕様**: code.claude.com の permission-modes（全文）、permissions（20–139 / 380–648 行）、plugins/mods の
  overview / events / reference / create（全文）、output-styles・ultraplan（全文）、hooks・settings-reference・
  sub-agents（snippet）、CHANGELOG（2.1.282–2.1.289 だけが見えた）、GitHub 上の mods 型定義（2.1.277、途中で切れた）、
  anthropics/claude-code の issue #50660 / #69737 / #91301 / #32118 / #12127 / #30634。
  見つからなかった: `prompt.attachment` の type 一覧（`plan_mode`）と `prompt.section` 名の公開 doc、公式の custom
  mode、plan mode に tool を足す設定（`useAutoModeDuringPlan` と通常の allow rule 以外）、settings の PreToolUse
  `allow` が plan mode の編集禁止を上書くかの記述、plan mode 中の WebSearch / WebFetch / MCP の扱い、plan mode 関連
  issue への staff の返答、2.1.282 より前の CHANGELOG
- **Claude Code 向け先行実装**: raw で読んだ — HumanLayer `create_plan.md` / `research_codebase.md`、obra/superpowers
  `writing-plans` / `brainstorming`、anthropics の feature-dev `feature-dev.md`、github/spec-kit `templates/commands/plan.md`。
  repo / doc を読んだ — plannotator、cc-sdd、planning-with-files、docs.humanlayer.com。検索語: research 段のある
  custom plan mode plugin / plan mode が窮屈という苦情 / HTML・Mermaid の plan skill / hook で ExitPlanMode を止める。
  見ていない: BMAD、claude-code-spec-workflow、awesome-claude-code の一覧、oh-my-claudecode `plan`、cc-sdd の
  design 段の SKILL.md。2026 年の実践者による長文比較は見つからなかった
- **他エージェント**: Roo Code（custom modes doc 2026-05-15、`mode.ts` main）、OpenCode（agents / permissions doc
  2026-10-03、`agent.ts` dev）、Gemini CLI plan mode（2026-06-18）、Kiro specs（2026-10-02）、Cursor plan mode、
  Cline plan & act、VS Code custom agents（2026-09-30）、Zed tool permissions。snippet のみ: Codex CLI（公式 doc
  見つからず）、Windsurf、Kilo Code、Aider、Cursor 2.2 の Mermaid。Amp の plan mode は見つからなかった
- **調査手法・図付き plan**: Anthropic multi-agent research system、LangChain Open Deep Research、STORM（arXiv
  2402.14207、abstract）、BrowseComp（arXiv 2504.12516）、DEFT（2512.01948、abstract）、OpenAI deep research guide、
  GPT Researcher、Claude Code best practices、plannotator、Kiro design.md、Cursor plan。見つからなかった: エージェントの
  plan を人がレビューするときに図が効くかの研究、vendor が公開した飽和ベースの停止規則、反証役 subagent の効果の
  ablation（STORM 以外）

## Found

1. **plan mode の現状**（permission-modes、全文）— 表の記述は「Reads, plus classifier-approved commands when auto
   mode is available」。`useAutoModeDuringPlan` は既定で on。auto mode が無ければ read-only 以外のコマンドは拒否で
   なく確認になる。編集は plan の承認まで止まる。`.claude` は protected directory で、acceptEdits でも protected
   path への書き込みは確認が出る。auto-approve は cwd と `additionalDirectories` の中だけ。
   → こちらとの違い: notes を `~/.claude` の下に置くと、どの repo からも確認が出る
2. **subagent の permission mode**（sub-agents、snippet）— 親が `default` / `dontAsk` / `plan` のとき、subagent は
   frontmatter の `permissionMode` で動く（`bypassPermissions` を除く）。親が auto / acceptEdits / bypass なら定義の
   値は無視される。fork は 2.1.287 以降、親の plan mode を引き継ぐ。→ 移せる: researcher に `acceptEdits` を持たせる
3. **Mods**（mods docs、全文、2.1.287+）— `tool.check` は rule・mode・PreToolUse が決めた後に走り、別の decision を
   返せる。`prompt.attachment` は Claude Code 自身の reminder を書き換え・削除できる。ただし `plan_mode` という type 名は
   公開 doc に無い（手元の 2.1.286 が書いた型定義には有る）。→ 核に置くと版で壊れうる
4. **ExitPlanMode の gate**（#50660、2026-05-26 に not_planned で close）— PreToolUse の deny は ExitPlanMode では
   無視される。plannotator（約 9.1k stars）は PermissionRequest hook で ExitPlanMode を受けてブラウザのレビュー UI を
   出す。CHANGELOG 2.1.288: hook が ExitPlanMode で古い plan を見る不具合を修正。→ どちらも plan ができた後に走る
5. **先行実装はどれも純正 plan mode を使わない** — HumanLayer / superpowers / feature-dev / spec-kit は通常モードで
   plan ファイルを書き、research-before-plan は prompt と「前段成果物の存在」で担保する。hook で止める実装は無い
   （上の範囲で）。spec-kit は不明点を `NEEDS CLARIFICATION` として research.md（Decision / Rationale / Alternatives）
   で解かせ、その完了を設計の前提にする。HumanLayer の RPI は research を ticket から切り離し、未解決の問いが残る間は
   plan を書かせない。superpowers は依頼を Spike / Bounded / Architectural に分け、SessionStart hook と命令形の
   description で skill を発火させる。planning-with-files は Stop gate に block 回数の上限を持つ
6. **他エージェントの plan mode はモード別の書き込み許可** — OpenCode `edit: {"*": "deny", ".opencode/plans/*.md":
   "allow"}`（最後に一致した rule が勝つ。doc と source で bash の扱いが食い違う）。Gemini CLI は `modes=["plan"]` と
   引数の正規表現で plans 配下の `.md` だけ書ける。Roo Code の Architect は `["edit", {fileRegex: "\\.md$"}]`（README や
   ADR まで書けてしまう緩さがある）。research の完了を強制するエージェントは無い
7. **調査の規模**（Anthropic、2025-06-13、全文）— 単純な問いは 1 agent × 3–10 calls、比較は 2–4 subagent × 各 10–15、
   複雑は 10 超。Opus lead + Sonnet subagent が単一 Opus を社内 eval で 90.2% 上回った。BrowseComp の分散の 80% を
   token 使用量が説明。multi-agent は chat の約 15 倍の token を使い、「most coding tasks involve fewer truly
   parallelizable tasks than research」とも書く。数字は Claude 4 世代のもの。Open Deep Research は brief を先に書き、
   lead が漏れを見て追加を出し、writer 1 本でまとめる。STORM は視点ごとに質問させて網羅を 10 ポイント上げた（abstract）。
   DEFT などの失敗研究は、調査エージェントは検索より統合と検証で失敗すると報告する（abstract）
8. **図付き plan** — Cursor 2.2 は plan 内の Mermaid を描画する（描画不具合の報告もある）。Kiro の design.md は
   sequence 図を持つ。Roo の Architect は Mermaid を使うよう指示される。ultraplan（公式のブラウザ plan レビュー）は
   削除済み。古典的な SE 実験では、図は関係や流れを示すときに効き、本文の繰り返しなら効かない

## Contradictions

- OpenCode の plan agent の bash は、doc では `ask`、`agent.ts` では未設定。source の方を強い根拠とみなした
- plan mode が「縛りすぎ」という著者の体感と、doc の「auto mode 下ではコマンドは classifier 判定で走る」は食い違わない —
  止まるのは plan ファイル以外への書き込みで、抜けたくなる場面の多くは scratch 書き込みと読める（推論）
- 「調査が浅い」への処方として、Anthropic の 80%（token 量）は 1 本の budget 増でも説明できる。視点分割（STORM）と
  別 context での容量追加（Anthropic 自身の説明）が、並列化を選ぶ根拠

## Still unknown

- 配線前に実機で確かめる 5 点（ADR-0086 Decision 6）: plan ファイルへの Write を PreToolUse の block で止められるか /
  plan mode の親の下で researcher が書け、PostToolUse の `session_id` が親と同じか / subagent の PreToolUse に
  `agent_type` が載るか / 作業ディレクトリ外の notes が approve で確認なしに通るか / plan mode 中の WebSearch・
  WebFetch が確認なしで走るか
- 2025-06 の規模の数字が今のモデル世代でも成り立つか
- 図が plan のレビューを良くするかの、コーディングエージェントでの実測

# ADR-0002: claude-mem プラグイン無効化

## Status
accepted — **2026-09-06 注記**: 再評価の結果、無効のまま維持。失効条件を `## Review-when` に書き換えた（下記注記）

## Date
2026-03-08

## Context

claude-mem (thedotmack-claude-mem) プラグインを導入したが、既存の記憶管理システム（MEMORY.md + learned skills + rules/）との重複が判明した。

具体的な問題:
- 自動保存はされるが自動検索・活用の仕組みがない
- セッション開始時のインデックス注入は「目次だけの百科事典」状態
- MEMORY.md + learned skills + rules/ で記憶管理が十分カバーされている

## Decision

`settings.json` で `claude-mem@thedotmack-claude-mem: false` に設定し無効化した。プラグインファイル・DB（~/.claude-mem/）は残してあるので再有効化は可能。

## Alternatives Considered

- **claude-mem をメインの記憶システムにする** — 自動検索がないため、蓄積しても活用できない
- **両方併用する** — 同じ情報が2箇所に分散し、どちらが正なのか曖昧になる
- **claude-mem を改善して使う** — プラグインのコードを fork する必要があり、コスト対効果が合わない

## Consequences

- 記憶の一元管理（MEMORY.md + learned skills）が維持される
- claude-mem のストレージ容量を消費しなくなる
- 再評価の失効条件は `## Review-when` が正本（2026-09-06 に書き換え。元の条件「自動検索機能が追加されたら」は下記注記のとおり発火済みで、判断は変わらなかった）

> **注記（2026-09-06 再評価）**: 一次ソース（thedotmack/claude-mem、v13.24.1、README は
> 「Claude-Mem is now Grok Mem. The package is still `claude-mem`」。改名理由は未記載）と
> `src/cli/handlers/session-init.ts` を直接確認。
>
> - 元の失効条件「自動検索の追加」は `CLAUDE_MEM_SEMANTIC_INJECT` として実装済み
>   （UserPromptSubmit ごとに prompt を Chroma へ投げ上位 5 件を additionalContext に注入）。
>   ただし `SettingsDefaultsManager.ts` の既定値は `'false'`、コメントは experimental。
>   既定構成の取り出しは SessionStart の timeline 注入（50 観測）と Claude が自分で呼ぶ
>   MCP tool のままで、Context の「目次だけの百科事典」問題は既定では未解消
> - コスト面は 2026-03 時点より悪化: PostToolUse が全ツール呼び出しで async 発火し、
>   `@anthropic-ai/claude-agent-sdk` の `query()` で既定 `claude-haiku-4-5` を呼ぶ
>   （subscription 枠を消費。launchd の triage セッションを含む全セッションが対象）。
>   Bun の worker service と Chroma が常駐し、同居する常駐 agent とメモリを競合する。
>   hosted「claude-mem observer」（30 日 trial、以後の価格は README 未記載）への誘導が加わった
> - 判断: 無効のまま維持。元の失効条件は「自動検索の有無」を問うていたが、本質のずれは
>   2 点 — (1) 正本の置き場所: claude-mem の記憶は transcript 圧縮の episodic な派生データで、
>   agent が次セッションで要る「今何が真か」は repo の code / git / ADR / verify が既に持つ
>   （rule `llm-first-code`「可読性は保存しない、検証可能性を保存する」と同型）。
>   (2) 記憶が要る時刻: hook は prompt 投入時にしか発火できず「似ている過去」の推測に
>   なるが、本当に記憶が要るのは作業途中に agent 自身が問いを立てる瞬間で、外側の hook 層
>   からは見えない。Chroma / hybrid search / hosted observer はいずれも推測精度の周辺工事で、
>   この 2 点を変えない。失効条件をこの 2 点に合わせて書き換えた
> - 反証として残す点: 長期にまたがる横断観測（「この種の変更は 3 回とも bounce した」型の
>   統計）は正本にも git log にも直接は載らず、episodic store でしか取れない。現時点で
>   その需要は無いが、構造的に無価値とは言えない

## Review-when

- claude-mem（または同型の外部記憶）が、agent が作業途中に自分の問いで引ける形
  （MCP tool を agent が主体的に呼ぶ以上の、必要時刻に結びついた取り出し）を既定構成で
  持ち、precision の実測を公開する → 再評価
- 著者側に「複数 repo・複数セッションにまたがる横断観測の統計」の実需が出る
  （task-triage の bounce 分析など、MEMORY.md / ADR / rfcs / git log で答えられない問いが
  具体的に立つ）→ episodic store の要否を再評価。その際は claude-mem に限らず search-first
- 常駐コスト（Bun worker + Chroma + PostToolUse ごとの Haiku 呼び出し）が subscription 枠と
  同居 agent のメモリに影響しない形に変わる → 上 2 条件の評価時に減点要因から外す
- 元の条件「自動検索機能が追加されたら」は 2026-09-06 に発火済み。単独では再評価の根拠にしない

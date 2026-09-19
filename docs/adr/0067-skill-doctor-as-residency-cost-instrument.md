# ADR-0067: `/skill-doctor` を skill-stocktake の residency-cost 計器にする — listing 常駐 token は substrate に測らせ、意図的使用は harness の usage_stats が正のまま

## Status

accepted

## Date

2026-09-15

## Context

skill-stocktake は 2 つの parent-owned evidence を持っていた: `scripts.usage_stats`
（`hooks/log-skill-usage.sh` の JSONL を 4 補正で集計した 14 日の意図的使用数、ADR-0052）と
`skill-health` の URL liveness。RFC-0017 / RFC-0018 が問題にした **description の常駐コスト**
（listing 行が毎ターン system prompt に載る token）は、harness 側に計器が無く、字数で代用していた
（RFC-0017: 当初見込み −6,596 字、実施後 40,815 → 25,238 字、2026-08-30。分母 = 注入 listing
全体は未測定のまま、plugin / built-in 側を測るかは Unresolved）。

Claude Code 2.1.269（2026-09-11）が `/skill-doctor` を追加した（一次資料、2026-09-15 参照:
[changelog](https://code.claude.com/docs/en/changelog.md)「/skill-doctor: Show unused loaded
skills and their context cost」、[commands](https://code.claude.com/docs/en/commands.md)、
[skills#find-unused-skills](https://code.claude.com/docs/en/skills.md#find-unused-skills)、
[env-vars](https://code.claude.com/docs/en/env-vars.md#features-that-need-feature-flag-fetching)）。非対話 `claude -p "/skill-doctor"` で
skill ごとに `context`（listing 行の token。`-` = listing に無い）/ `7d tokens` / `uses` /
`last used` の text 表と「loaded but never invoked」一覧を出す。JSON は無い。feature-flag
fetching が無効な接続（`DISABLE_TELEMETRY` 等）では `Skill usage reports are not available
on this connection.` を返す。対話セッションでは `/plugin` の Stats タブに描画され stdout は空
（本 ADR の起点: 著者が対話で `/skill-doctor` を打ち `(no content)` を得た）。

本 harness での実測（2026-09-15、2.1.270、cwd `~/.claude`、listing 71 行 = `userSettings` 60
（`skills/*/SKILL.md` の全数と一致）+ plugin skill 11。bundled / built-in は docs どおり対象外なので、
RFC-0017 の分母は plugin まで閉じ、bundled 分だけ未測定で残る）: `context` は `< 20`〜`~360`、
`disable-model-invocation: true` の skill は `-`。`uses` は `last used 200 days` の行にも
値があり、7 日窓でなく累積と読める（legend に窓の表記なし）。sandbox 子セッション
（skill-comply）の呼び出しも含む — usage_stats が補正 2・3 で除く対象。

反射性の実測（2026-09-14T21:3xZ）: 子セッションは `hooks/log-skill-usage.sh` を継承するが、
`/skill-doctor` 実行後 1 時間で `metrics/skill-usage.jsonl` に増えた行は本セッションの subagent
による `read` 2 行だけで、子セッション由来の行は 0。built-in slash は Skill / Read tool を
呼ばないので計器に書き戻さない。

ADR-0052 の Review-when「substrate が skill 使用統計を native に持った」は本件で発火した。

## Decision

1. skill-stocktake Phase 1 に parent-owned の **Residency-cost evidence** を追加し、
   `claude -p "/skill-doctor"` を監査あたり 1 回、parent が走らせる。cwd は測る listing を
   決めるので、project skill を含めるときは repo の cwd から走らせる。batch agent には
   渡さない（usage と同じ parent-owned dimension）。`--settings` 隔離はしない — 子が
   user 設定を継承して報告する listing こそが実セッションの常駐（memory
   reference-claude-p-child-inheritance の測定面。反射性は Context の実測で 0 行）。
2. **役割分担**: `context` が residency cost の唯一の計器。意図的使用数は引き続き
   `usage_stats`（slash + invoke、sandbox 除外、実 span 表示）が正で、`/skill-doctor` の
   `uses` は cross-check。乖離が sandbox 補正で説明できない場合は報告に書き、平均しない。
   ADR-0052 の Review-when は発火したが usage_stats は畳まない — `uses` は窓が無く sandbox
   子セッションを含み、4 補正の代替にならない（0052 に注記）。
3. Phase 4 の description audit で `context` は **価格**として使う: nonzero `context` かつ
   意図的使用 0 が RFC-0017 の fold case（参照を 1 行足してから
   `disable-model-invocation: true`）。順序づけにだけ使い、verdict の入力にはしない
   （content owns the verdict の原則は不変）。
4. 報告表に `ctx` 列を加える。利用不能時は `—`（unmeasured）で、0 と書かない。
5. 出力の parser は書かない。format は 2026-09-11 導入の substrate 所有で JSON も無い — 表を
   写す手順にとどめ、印字 legend と SKILL.md の記述が食い違えば legend を正とすると本文に書く。

## Review-when

- `/skill-doctor` が JSON 出力か CLI subcommand を得た時 → parser 化を再検討（決定 5）
- `/skill-doctor` の列（`context` / `uses` の定義・窓）が変わった時 → Phase 1 の読み方を更新
- `usage_stats` と `uses` の乖離が sandbox 補正で説明できない事例が出た時 → どちらかの計器の
  欠陥として調べる（決定 2）
- substrate が listing の注入方式を変えた時（RFC-0017 / 0018 と同一条件）→ `context` の意味が
  変わるので決定 3 を再検討

## Alternatives Considered

- **何もしない（residency は字数代用のまま）** — 却下。RFC-0017 の分母（注入 listing 全体）は
  字数では閉じられず、plugin skill の行は harness の file に無い。`context` は substrate が
  実際に注入した token で、字数の代用が答えられなかった問いにそのまま答える。
- **`usage_stats` を `/skill-doctor` に置き換える** — 却下。`uses` は窓が無く sandbox 子
  セッションを含む。ADR-0052 の 4 補正（`verify-bootstrap` が補正前 2 / 補正後 0）が失われる。
- **`/skill-doctor` の text を parse する script を `scripts/` に足す** — 却下。format は
  2026-09-11 導入の substrate 所有で JSON 契約が無い。parser は format 変更のたびに
  silent drift する側に立つ（llm-first-code「出力こそ守る対象」の逆）。JSON が出たら再検討。
- **skill-health Phase 3 の Utility 側に置く** — 却下。skill-health は Compatibility の
  決定論 scan が本体で、Utility は「読むだけ」の federate。verdict を組み立てる Phase 4 を
  持つのは skill-stocktake で、価格を使うのもそこ。
- **`context` を Retire の閾値にする** — 却下。content owns the verdict。residency は
  fold（description を畳む）の順序づけにだけ効く（RFC-0017 の結論と同じ）。

## Consequences

- 容易になる: description audit の候補に token 価格が付き、RFC-0017 の fold 候補を
  字数でなく実測 token で並べられる。`disable-model-invocation` 済みの skill が `-` で
  即座に判別できる。
- 困難になる / 負担: 監査 1 回につき `claude -p` 子セッションが 1 本走る（2026-09-15 の 1 回は
  150 秒の timeout 内で完了。所要時間は未計測）。feature-flag fetching を切った環境では
  `context` 列が `—` になり、residency の判断は字数代用へ戻る。
- 転記は手作業になる。ADR-0052 が usage 集計を script 化したのは 4 補正を毎回 jq で再導出して
  いたからで、ここには再導出する補正が無く、写す列は `context` 1 つ。JSON が出た時点で
  script 化する（Review-when）。
- 計器が 2 本になる: `uses` と `usage_stats` の乖離を報告に書く義務が増える。

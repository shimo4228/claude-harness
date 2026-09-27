# herdr-delegate / spawn-session — 公開は見送り、事実誤りの訂正のみ

## Context

herdr の Apache 2.0 化を機に、自作の 2 skill（`herdr-delegate` / `spawn-session`）を
プラグインとしてエコシステムに提出したい、という要求から出発した。ユーザーの追加指示により
**被り確認**と**提出価値の判定**を先に行った結果、**公開は見送り**と決定（2026-08-01）。

この計画に残すのは、**公開の可否とは独立に必要な訂正**だけ。2 skill は現行 substrate に対して
事実誤りを抱えており、そのまま residency させると自分のセッションで誤った判断を誘発する。

### 見送りの根拠（調査で確定した事実）

**被りが深い** — 主張したい点のほとんどに先行実装がある。

| 主張 | 状況 |
|---|---|
| Herdr pane で別 CLI agent を回す | 既出。`yigitkonur/claude-code-herdr-plugin`（CC plugin, MIT）、`afogel/shepherdr`、`vladzima/herd`、`msadig/herdr-peer-agents-skill` |
| `idle` ≠ done / デバウンス付き画面検知 | 既出。yigitkonur の README に `completion-by-keyword lies` / `screen-stability wait` が字句で存在。`0xGosu/herdr-auto-pilot` は揺らぎの安定シグネチャ化まで実装済み |
| 完了検知一般 | 飽和。`kingbootoshi/codex-orchestrator`（★334、Codex notify hook）、`obra/claude-session-driver`（★101、hook の JSONL イベント）、`vaclavik-xyz/herdwatch`（idle 誤検知対策） |
| モバイルから別 repo の CLI セッションを立てる | `fireman333/claude-remote-launcher`（★0）が動機まで一致（非 Herdr）。`hardyjosh/ccx` は tmux 前提 |

空いていたのは **git を ground truth にする検収規律**（先行の検証は sentinel file /
`--expect` ファイル存在確認どまり）と、**Herdr 前提の Claude Code plugin**
（`anthropics/claude-plugins-community` の全 2,307 plugins に `herdr` を含むエントリ 0 件）の 2 点のみ。
前者は実装ではなく規律 10 数行で、プラグインという器に見合わない。

**提出先の前提も違っていた** — herdr plugin は **SKILL.md を配れない**。
`herdr-plugin.toml` + 実行体で、宣言できるのは `build` / `startup` / `actions` / `panes` /
`events` / `link_handlers` のみ（公式 docs: *"There is no separate plugin SDK.
The entire Herdr CLI is the plugin API"*）。integration 系統も配るのは
`herdr-agent-state.*` フック 1 枚だけ。skill を配る経路は Claude Code plugin のみだった。

**ライセンス（参考）** — herdr は **Apache-2.0 に変更済み**（commit `cd5ea1be`, 2026-07-22、
repo 全体）。ただし CHANGELOG 上まだ `Unreleased` で、手元の brew v0.7.5（07-21 タグ）は
AGPL 最終版。repo は `herdrdev/herdr` にリネーム済み。

---

## 作業 1: `herdr-delegate` の失効した根拠を訂正

対象: `~/.claude/skills/herdr-delegate/SKILL.md` の 20–26 行目
（「なぜ headless（`codex exec`）ではなく Herdr セッションか」節）。

現行の主張「Bash tool から直接呼ぶと 10 分上限で途中 kill される」は**現行仕様では誤り**。
公式 tools-reference:

> When a command reaches its timeout without finishing, Claude Code moves it to the
> background instead of stopping it（min-version 2.1.210）

600000ms も `BASH_MAX_TIMEOUT_MS` で変更可能な既定値であって上限ではない。

**書き換え方針** — 委譲の正当化を、substrate が吸収していない 3 点に絞り直す:

1. **別ベンダのモデルを使うこと自体** — Agent teams / subagents / `/batch` はすべて Claude モデル
   （Agent teams の docs: *"each teammate is a separate Claude instance"*）。
   cross-vendor 委譲の公式面は探して見つからなかった
2. **対話セッションの永続性と差し戻し** — `claude --bg --exec` は PTY だが Claude から文字を
   送る公式 API が無く、出力行は約 5 分で消える。同一文脈への差し戻しは公式代替なし
3. **人間が横で見て esc で割り込める可視性**

**捏造報告の実例（「92 テスト green」→ tree 無変更）は残す** — harness 機能では解消されず、
検収規律の存在価値そのもの。ただし「10 分 kill が原因で」という因果からは切り離す。

## 作業 2: `herdr-delegate` の監視ループを Monitor tool に寄せる

対象: 同 SKILL.md 58–86 行目。本文が既に「Monitor tool でデバウンス付き監視」と言いながら、
実際には生の bash `while` ループを載せている。Monitor tool は出力行を逐次モデルに返す
公式機構で、`timeout_ms` / `persistent` / `TaskStop` を持つ。

誤検知 3 系統の知見（background terminal 待ち画面のすり抜け / 空読みの `READERR` 畳み込み /
turn 間の一瞬の静止に対する 30 秒 × 8 デバウンス）は**そのまま残す**。実装だけ公式機構に載せる。

## 作業 3: `spawn-session` の古い前提を訂正

対象: `~/.claude/skills/spawn-session/SKILL.md` 25 行目（`## How it works`）。

「公式 Remote Control はモバイル側から新セッションを起こせない（1 マシン基本 1 セッション）」
のうち、後半が古い。公式 Remote Control の server mode に
`--spawn <same-dir|worktree|session>` / `--capacity <N>`（既定 **32**）/
`--[no-]create-session-in-dir` がある。

**ただし決定的なギャップは残るので、skill 自体は retire しない** — server mode の全セッションは
その server プロセスの cwd（= 1 repo）に縛られ、**別プロジェクトのセッションを起こす手段が無い**。
訂正文はこの区別を明示する。

あわせて `## When NOT to use` に 2 つ追加:
- **Dispatch** — Claude Desktop の Code タブが実行主体。`~/.claude` 設定系ではなく
  Herdr 艦隊ビューにも並ばない。Pro/Max 限定
- **cloud session**（Claude Code on the web）— ローカル FS / MCP / Herdr と無関係

## 作業 4: 未検証の代替候補を台帳に残す

CHANGELOG に次の行がある:

> Background sessions now preserve `--ide`, `--chrome`, `--bare`, **`--remote-control`**,
> and other flags across retire→wake

`claude --bg --remote-control "<名前>"` が通るなら、`spawn.sh` の 138 行はほぼ不要になる。
ただし agent-view の docs には "mobile" / "remote" の語が 1 度も出ず、
**この組み合わせを支持する明記は見つからなかった**。

実測が要る仮説なので、`~/.claude` の `.notes/TASKS.md`（無ければ task-stocktake で解決）に
1 行足す。合否条件は「iPhone の Claude アプリのセッション一覧に出るか」の 1 点のみ。
**この計画では実行しない。**

## 作業 5: 判断を lab-charter に記録

`~/MyAI_Lab/lab-charter/IDEAS.md` に 1 行足す — 「herdr 2 skill のプラグイン化を検討し、
被り飽和と substrate 吸収を確認して見送り」+ この計画ファイルへのリンク。

第 3 ループの材料として「棚卸しの結果 出さないと決めた」ことに記録価値がある
（出したものより、出さなかった判断の方が後から辿れなくなる）。

---

## Verification

- `herdr-delegate/SKILL.md` に「10 分上限で途中 kill」の記述が残っていないこと
- `spawn-session/SKILL.md` に「1 マシン基本 1 セッション」が残っていないこと
- 訂正後の `herdr-delegate` を**実際の委譲 1 件で回す** — ドキュメントだけ直して実地で
  壊れている状態を作らない。Monitor tool 版で誤検知 3 系統が再現するかも同時に見る
- `git diff` で、訂正が上記 3 ファイル以外に及んでいないこと
- SKILL.md は behavior-shaping artifact なので、コミット前に**本文を提示**する
  （意図の要約ではなく差分本文。`human-gate.md` の区分）

# ADR-0036: herdr 系スキルは skills-only plugin (herdr-toolkit) として公開する

## Status

accepted

## Date

2026-08-03

## Context

harness には herdr 関連スキルが 3 本ある。`skills/herdr/` は外部 origin
(ogulcancelik/herdr、Apache-2.0) で、Herdr 自身の Claude Code integration が配布する
verbatim copy。`skills/herdr-delegate/` と `skills/spawn-session/` は自作
(origin: shimo4228)。

自作 2 本は集約 repo claude-harness には同期済みだが、単独で installable な配布形が
なかった。Herdr エコシステムの成長に先行して、Herdr ユーザーが直接導入できる公開面を
作りたい。動機は X 告知・Zenn 記事と合わせた先行ポジション取り。

plugin packaging の先例は akc-cycle (rule + plugin、固定 allowlist sync script) のみで、
制約として Claude Code plugin は rules を運べない仕様がある。

## Decision

新規 repo shimo4228/herdr-toolkit を skills-only plugin として公開する (2026-08-03、v1.0.0)。

1. payload は herdr-delegate + spawn-session の 2 skills のみとする。sync は akc-cycle
   variant から rules/agents 収集ブロックを除いた固定 allowlist 方式の
   `scripts/sync-from-local.sh` を用いる。
2. `.claude-plugin/plugin.json` / `marketplace.json` (self-owned marketplace) は
   repo root 資産とし、sync 対象から外す。version は plugin.json を手動 bump する。
3. 外部 origin の herdr 本体スキルは同梱しない。README で「Herdr 側の integration から
   入る」と案内する。
4. 委譲ゲート rule (`HERDR_ENV=1` + 明示指示) は plugin payload に入らないため、README
   で copy-install 案内を行い、スキル本文内のゲート記述で代替する。
5. 正本側を修正する。`spawn-session` の SKILL.md が持つ spawn.sh 実行手順を、絶対パス
   固定から「本 SKILL.md と同じディレクトリ」参照に変更する。plugin install 先ではパスが
   変わるため。

## Alternatives Considered

### herdr 本体スキルも Apache-2.0 attribution 付きで同梱する

ライセンス上は可能だが、Herdr の integration が既に配布しており重複導入になる。upstream
更新への追従責任も負うことになるため却下した。

### 既存命名規約どおり単独 skill repo を 2 つ (herdr-delegate / spawn-session) に分ける

2 repo に分かれると発見性が下がる。両スキルは同じ「Herdr 運用レイヤ」で一体であり、
`/plugin install` 1 回で入る plugin の方が導入摩擦が小さいため却下した。

### claude-harness 集約 repo のみでの公開を継続する

集約 repo は installable ではなく、Herdr ユーザーが該当 2 skill だけを選んで導入する
導線がないため却下した。

## Consequences

### Positive

- Herdr ユーザーは `/plugin marketplace add shimo4228/herdr-toolkit` +
  `/plugin install` の 2 コマンドで導入できる
- plugin variant の 2 例目ができ、packaging パターンが再現可能になった
  (harness-sync SKILL.md の plugin variant 節と Repo mapping に記載)

### Negative

- 公開面が 1 repo 増え、sync 実行と version bump の運用対象が増える
- 委譲ゲートは導入者の rule 環境では既定で効かず、スキル本文内のゲート記述と README の
  copy-install 案内が代替になる
- skill 本文は日本語のままなので、英語圏ユーザーには README (英語) がブリッジとして必須


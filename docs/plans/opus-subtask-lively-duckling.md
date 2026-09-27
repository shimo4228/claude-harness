# fork (subtask) と Opus 委譲の適合性判断 — 変更なし

## Context
X のポスト(fork/subtask 推奨、2.1.232 以降デフォルト)を受けて、実装の Opus 委譲に
fork を使えるか検討した。

## 判断 (2026-08-29)
- fork は親の会話コンテキストを複製し、プロンプトキャッシュ prefix を共有する。
  ただし **常に親モデルで走り model 指定は無視される** (Agent tool 仕様)。
- したがって Fable judge セッションからの fork は Opus にならず、build-tier 委譲には
  使えない。また fork は fresh context の対極なので reviewer / judge にも不適合。
- プロンプトキャッシュはモデル単位。モデル切替はキャッシュ再構築 1 回分のコスト。
  fork + モデル変更はそもそも不可能。

## 結論
implementation-chain / dispatch の現行設計は変更しない。fork の適所は
「同一モデル・全文脈が必要・fresh 不要」な side task (verify 実行+要約、調査 fan-out、
worktree 並行編集) のみ。

失効条件: fork が model override を受け付けるようになったら再検討。

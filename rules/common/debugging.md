<!-- origin: shimo4228 -->
# Debugging

> `fix` 種別 chain の前段。Plan ステップの直後、TDD の前に挿入される。
> 確認待ち (step 3) は [`common/planning.md`](planning.md) の **2 介入点モデル**の例外として残す。

## 根本原因優先（CRITICAL）

バグ報告を受けたら、以下のフローを厳守する:

1. **仮説**: 根本原因の仮説を述べる
2. **証拠**: その仮説を裏付ける具体的なコード行を示す
3. **確認待ち**: ユーザーの「go」を待つ（即修正しない）
4. **修正**: 確認後に最小限の修正を実装
5. **検証**: 既存テストを実行して修正を確認
6. **回帰固定**: そのバグの正確な再発を防ぐ回帰テストを新規に 1 本残す。AI 自己レビューは同じ盲点を繰り返すため、確定したバグは機械的ガード（テスト）に変換してから完了とする。See skill: ai-regression-testing

## 禁止事項

- 最初の仮説に基づいて即座にコード変更してはならない
- 誤診断の修正の上に修正を重ねてはならない（revert して最初からやり直す）
- ユーザーが原因を指摘した場合、反論せずまずその仮説を検証する

## AI デバッグの注意点

AI はリーセンシーバイアス（直近の作業箇所に原因があるという思い込み）に陥りやすい:

- **スコープの限定**: 「このログ/時点だけ分析しろ」と指示する
- **因果関係の切り分け**: 別原因の過去データを混ぜない
- **過剰対応の阻止**: 問題と無関係な「ついでの改善」を許可しない
- **プロンプトパターン**: 「原因の報告を先にして、修正提案は原因が確定してから」

## Retry with Context

Never blindly retry a failed operation:
1. Capture error output, conflict diffs, or failure context
2. Feed captured context to the next attempt
3. If same failure recurs after 2 retries, change approach or escalate

For external API calls, use exponential backoff with max retry count (3-5).

### Rate limit は警報であって障害ではない

外部 platform への書き込み中にレートリミットが**連発**する（単発でなく、スロットル上限に
張り付いている）場合、それは transient error ではなく **substrate からの policy シグナル** —
「そのアカウント種別にとってその速度・量は異常」という警報。backoff で踏み抜く対象ではない。

- 連発を検知したら **burst を停止して人間に報告**する（速度を落として続行、ではない）
- 特に **非 bot アカウントでの大量作成・大量書き込み**中の連発は、platform のパトロール面に
  最も目立つ行動をしている兆候。governance レビュー → アカウント措置の入口になりうる
  （2026-07-16 に実証: 連発を無視した bulk 書き込みの数時間後にアカウント無期限 block + 全作成物一括削除）

See skill: agent-harness-construction / learned note: [skills/learned/platform-governance-aggregate-pattern.md](../../skills/learned/platform-governance-aggregate-pattern.md)

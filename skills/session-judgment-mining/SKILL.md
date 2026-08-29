---
name: session-judgment-mining
description: 過去の Claude Code セッション群（~/.claude/projects/<project>/*.jsonl）を遡及的に一括発掘し、ユーザーが繰り返し下した判断・価値観を抽出して skill / rule に正本化するワークフロー。人間発話の抽出 jq パターン、既存資産（skills / rules / ADR / memory）とのカバレッジ照合による重複回避、価値観リファレンス（why）と判断ゲート（when/what）の二層設計判断、既存スキルとの矛盾解消（免除条項）と memory への昇格マークまでを扱う。Use when — 「過去セッションから私の判断・価値観をスキルにして」「セッション履歴を紐解いて規約化して」、同じ指摘・修正がセッションを跨いで繰り返されていると気づいたとき、memory の feedback が溜まって確率的リコール頼みになっているとき。NOT for — 過去ログから記事の問いを発見 → session-theme-mining、現行セッションからの単発パターン抽出 → learn-eval、skill 品質の監査 → skill-stocktake、既存 skill 群からの rule 蒸留 → rules-distill、会話ログの要約・議事録作成。
user-invocable: true
origin: shimo4228
disable-model-invocation: true
---

# session-judgment-mining — 過去セッション群からの判断・価値観の発掘とスキル化

**Purpose:** ユーザーの判断・価値観は個々のセッションの修正指示（「ここ直して」「こうじゃない」）として発話され、memory に部分的に残るだけで大半は会話履歴に埋まる。このスキルは過去セッション群を全量発掘し、繰り返された判断を skill として正本化する。learn-eval が「今のセッションから 1 パターン」を抽出するのに対し、これは「過去セッション群の遡及一括発掘」。

初回実施: 2026-07-28、zenn-content repo（33 セッション / 人間発話 314 turn → skill 2 本 + ADR。memory 未記録の判断 8 件を新規発見）。

---

## Step 1: 規模把握と全量/サンプリング判定

対象は `~/.claude/projects/<project-dir>/*.jsonl`（`<project-dir>` は cwd のパスをダッシュ結合したもの。`memory/` サブディレクトリは対象外）。

まず**人間発話の turn 数**で読む量を見積もる。ファイルサイズは判断材料にならない — トランスクリプトの 9 割超は tool_result で、33 セッション 89MB でも人間発話は 114KB だった。

- 人間発話が**数百 turn** → 全量パス（サンプリング不要。数十 k tokens で通読できる）
- 数千 turn 超 → フィードバック密度の高いセッション（人間 turn 数上位）から読み、キーワード grep（「直して」「違う」「じゃない？」等）で補完

## Step 2: 人間発話の抽出（検証済み jq パターン）

主弁別子は `origin.kind == "human"`。`.type=="user"` だけで grep すると 9 割が tool_result のノイズになる。`.message.content` は string と array（画像添付時）の両形がある。

```bash
jq -r '
  ( select(.type=="user")
    | select(
        ((.origin.kind // null)=="human" and ((.isSidechain // false)|not))
        or
        ((.origin // null)==null and (.message.content|type)=="string" and ((.message.content|startswith("<"))|not))
      )
    | (.message.content | if type=="string" then . else (map(select(.type=="text") | .text)|join(" ")) end)
    | select(length>0)
    | "=== TURN ===\n" + .
  )
' "$f"
```

- 2 つ目の select 節は **compact / resume 後のセッションで `origin` が付かない人間発話**の補完（`<local-command-caveat>` 等の XML ラッパは除外）
- 補完 2: `select(.type=="queue-operation") | .content` に enqueue された生プロンプトが入る
- セッション開始 timestamp（`head -5 | jq -r '.timestamp'`）で時系列に並べると判断の変遷（方針の言語化 → 定着 → 例外の発見）が読める。**timestamp が取れないファイルがあるので結合後に全ファイルの包含を検算する**
- 抽出台帳は scratchpad に置く（コミットしない）

## Step 3: 通読とテーマ分類

抽出結果を**全量通読**し、判断・価値観の発話を分類台帳（scratchpad）に落とす。

- **頻出テーマ**（複数セッションで反復）と**単発**を分ける。反復こそ価値観 — 「同じ指摘が 3 セッションで出ている」が正本化の根拠になる
- 発話は**引用のまま**台帳に残す（要約すると後段で言い回しの証拠力が消える）。各引用にセッション ID を添える
- 拾うのは修正指示だけではない: 方針の言語化（「全体的に方針として〜」）、承認の型（何に GO を出すか）、却下の型（何を却下するか）、メタ習慣（指摘を規約化させる発話）も判断の証拠

## Step 4: 既存カバレッジ照合（このスキルの要）

抽出した判断を既存資産と突合し、**「既に正本があるもの」と「未昇格の空白」を分離する**。重複再掲はスキル生態系を壊す（drift の温床）ので、この工程を飛ばして書き始めない。

照合先: 既存 skills（project + global）/ rules / ADR / **memory（特に feedback 系 — 過去に抽出済みの判断がここにある）** / CLAUDE.md。並列 Explore agent に「どこに何の正本があるかマップを作らせる」のが速い。

出力は 3 区分:
1. **既に正本あり** → 新スキルには書かない。ポインタ（defer 宣言）のみ
2. **memory にあるが skill 未昇格** → 昇格対象の中核
3. **どこにも記録なし（新規発見）** → 全量パスの成果。トランスクリプトにしかない判断（承認・却下の型、口頭でだけ確立した規約）が必ず数件出る

## Step 5: 設計 — 二層に分けるか

> **ここから先は `skill-creator` を通す。** 常駐 rule `rules/common/skills.md` の
> 「skill / agent を新規作成・大幅改修するときは、書く前に skill: `skill-creator` を読む」は
> 本 skill にも当然かかる。Step 4 までの抽出結果を skill-creator の intent packet に固定し、
> 隣接 skill との境界を library 全体で引き、fresh-context の subagent に集計しない
> named verdict（Publishable / Fix / Drop）を出させてから著者通読で閉じる。
> 以下の Step 5–7 はその手順を置き換えるものではなく、**この skill が固有に持ち込む
> 入力**（二層分割の判断軸、昇格マーク、ground truth 遡及テスト）だけを述べる。

判断・価値観は 2 つの発火文脈を持つ:

- **価値観リファレンス（why）** — 方針議論・企画・ハーネス設計時に参照。実セッション引用を多めに残す（引用自体が判定器として機能する）
- **判断ゲート（when/what）** — 実作業のタイムライン順（着手前 → 作業中 → レビュー後）に「いつ・何を判断するか」。各節末に機械的な「判定:」1 行

両方を 1 スキルにすると description が両義化して確率的トリガーの精度が落ちる。**分量が両方とも実在するなら 2 スキルに分け、相互に defer**（価値観本文は values 側のみが持つ）。片方しか実在しないなら 1 スキルでよい。

注意: 判断ゲートを**機械 gate（quality-gate 類）に統合しない**。判断層をチェックリスト義務化すると「チェックリストを埋めるために部品を足す」テンプレート化が起き、それ自体がユーザーの判断（採否は文脈で決める）と矛盾する。

## Step 6: 縫合と昇格マーク

1. **既存スキルとの矛盾解消** — 新スキルの判断（例: タイプ別の装置免除）が既存スキルの無条件チェックリストと形式矛盾しないか通し読みし、既存側に**免除条項**を追記する。矛盾を残すと運用時にスキル同士が衝突する
2. **発見経路の敷設** — 既存スキルの Related・CLAUDE.md の一覧表に追記（新規ファイルは発見されないリスクがある）
3. **memory の昇格マーク** — 昇格元の memory は**削除しない**。originSessionId と生事例を持つ一次資料なので、先頭に「昇格済 → <skill 名>」1 行を付けて残す。MEMORY.md の該当節冒頭にも正本ポインタを 1 行。スキル = 蒸留された規則、memory = 生事例、の役割分担
4. **ADR** — 分割判断・残置ポリシー・非統合判断を ADR に記録する（repo に ADR 慣行がある場合）

## Step 7: 検証

矛盾チェックと草稿ゲートは `skill-creator` §4 が持つ（fresh-context の判定器）。ここが
足すのは skill-creator §5 に無い 1 つだけ:

- **ground truth 遡及テスト** — 過去に「ユーザー指摘で直した」実例の**修正前版**を git 履歴から取り、新スキルの判断ゲートだけで既知の欠陥を再発見できるか。正解が既知なので最強の eval。判断・価値観を抽出したこの skill 特有の検証で、抽出元セッションがそのまま正解ラベルになる

（発火率の測定が要るときは skill-comply。skill-creator の草稿ゲートとは別工程）

---

## Anti-Patterns

- ❌ **memory だけ読んで済ませる** — memory は過去セッションの部分集合。初回実施では新規発見 8 件（分割より統合・公開取り止めの自由・捏造検知・記事と実態の整合・通読ゲート・実測主義・訳語運用・粒度判断）がすべてトランスクリプトにのみ存在した
- ❌ **要約で台帳を作る** — 引用の言い回し（「タイトルが命」「宣伝くさい」）が価値観の解像度を担う。要約は抽出後の分類にだけ使う
- ❌ **既存正本の再掲** — 照合（Step 4）を飛ばして網羅的に書くと、既存スキルと二重管理になり drift する
- ❌ **判断ゲートの機械 gate 化** — Step 5 の注意参照

## Related

- `session-theme-mining`（`~/MyAI_Lab/zenn-content` 常駐、2026-08-29 移設）— 過去の Claude / Codex セッションから記事の問いを発見する。判断・価値観の正本化はしない
- `learn-eval` — 現行セッションからの単発パターン抽出（本スキルの単セッション版・対）
- `skill-stocktake` / `rules-distill` — 生成後のスキル監査・rule への蒸留
- `skill-creator` — **書く前に必ず通す入口と草稿ゲート**（`rules/common/skills.md` の配線）。Step 5 以降の起草・境界引き・判定はそちらが持ち、本 skill は Step 1–4 の抽出と、Step 7 の ground truth 遡及テストを足す
- 過去の出力形は現行asset名の先例にしない。現在の保存先をfreshに判定する

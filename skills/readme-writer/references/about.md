<!-- origin: shimo4228 -->
# About（description / topics / homepage）細則（readme-writer の参照資料）

規約の骨格は `../SKILL.md` の Workflow Step 10。ここは UI 実測の記録・topics の実勢測定・`gh` コマンド表で、2026-08-19 の棚卸しで SKILL.md 本文から移送した。

repo トップは README 本文と **About サイドバー**で 1 つの第一画面を作る。README がどれだけ良くても
**About が空なら「到達した人」にしか効かない** — topics は*まだ来ていない人*を索引から連れてくる
唯一の面なので、README と同じ作業単位で整える。

| 要素 | 出る場所 | 規約 |
|---|---|---|
| **description** | topic ページ・repo リスト・検索結果・外部ディレクトリ掲載時の唯一の一文 | README の lead と**同じ主張**にする（食い違いは cloaking）。**1 文目だけで機能が伝わる**構成にする（下記） |
| **homepage** | About と repo カードのリンク | docs サイト / その repo を解説した記事 / hub。**無いなら空のまま**（無関係な URL を埋めない） |
| **topics** | topic ページ・topic 付き検索の索引 | 最大 20。小文字英数字とハイフンのみ |

## description に文字数目標を置かない

**2026-08-01 の UI 実測**: GitHub の topic ページと プロフィール repo リストは description 要素に
truncation クラス（`text-truncate` / `line-clamp`）を**持たず**、300 字超でも全文が折り返し表示された。
「カードで切れるから短く」は少なくともこの時点では誤った前提なので、**文字数目標を置かない**
（README の Length budget と同じ思想: 数値でなく構成で決める）。

**これは仕様保証ではなく観測**である — GitHub 公式 API doc は description を "A short description" と
呼ぶだけで、全文表示を約束していない。UI は変わりうるので、**長い description を採るときは
実際の topic ページで表示を 1 度確かめる**。切れていたら 1 文目だけで成立する構成に畳む
（下の「1 文目を完結させる」は、どちらに転んでも効く）。

効くのは長さでなく**構成**:

- **1 文目を、単独で機能が伝わる完結した文**にする。背景・出自・関連 repo・ADR 番号は 2 文目以降
- 走査読みでは 1 文目しか読まれない。2 文目以降は「クリックするか」を決めた後の補強
- **アンチパターン: 作品の題名だけを置く**（論文タイトルをそのまま description にする等）。
  題名は「何をするものか」を言っていないので、repo リストで中身を推測できない
- 外部ディレクトリ・awesome-list・OGP カードは**独自に truncate しうる**。GitHub の挙動をそこへ
  一般化しない（掲載先ごとに実物で確認する）

## topics は「選ぶ」前に「測る」

どの語が索引面として生きているかは**実数で決まる**:

```bash
gh api "search/repositories?q=topic:<topic>&per_page=1" --jq '.total_count'
```

| 規模 | 扱い | 例（2026-08 実測） |
|---|---|---|
| **> 50k** | 母数用に 1–2 個。**それだけでは埋もれる** | `llm` 105k / `mcp` 56k / `claude-code` 54k |
| **2k–20k** | **主力**。対象読者が濃く母数も現実的 | `agent-skills` 12.8k / `claude-skills` 6.2k |
| **< 500** | 固有名・造語。既に知っている人にしか効かない。1–2 個まで | `research-software` 466 |

- **単数形と複数形は別 topic**（`agent-skill` 2.5k と `agent-skills` 12.8k は別の索引面）。
  **両方が実勢を持ち、かつ repo にとって自然なら両方付ける**。件数は repo 数であって到達数ではなく
  重複もあるので、「片方だけだと到達が半減する」とは言えない — 判断材料は「その面に載る価値が
  20 枠のうち 1 つを使うに値するか」
- 広い面で母数・中規模で命中・固有名で識別、の 3 層を混ぜる
- 上限 20 枠は有限資源。不自然な語形で枠を埋めて、関連性の高い topic を追い出さない

## 現状の把握（read-only。ここで書き込まない）

```bash
gh api repos/OWNER/REPO --jq '{description, homepage, topics}'   # 現状の 3 要素
gh api "search/repositories?q=topic:<topic>&per_page=1" --jq '.total_count'  # 候補 topic の実勢
```

**このステップの成果物は「変更案」であって適用ではない。** `gh repo edit` は GitHub への durable な
書き込みなので、著者通読 GO（SKILL.md Workflow Step 10）の承認を得るまで実行しない（可逆であっても「消す / 変える」の判断
自体はユーザーのもの）。

変更案は 3 要素それぞれについて **現状 → 提案** の形で書き出す。homepage を**空にする**提案なら
それも明示する（無変更と区別がつかなくなるため）。

## 適用と検証（承認後）

```bash
gh repo edit OWNER/REPO --description "..."            # description
gh repo edit OWNER/REPO --homepage "https://..."       # homepage（空にするなら --homepage ""）
gh repo edit OWNER/REPO --add-topic X --add-topic Y    # --add-topic は追加のみ（既存を消さない）
gh repo edit OWNER/REPO --remove-topic Z               # 削除は明示的に
```

検証:

```bash
gh api repos/OWNER/REPO --jq '{description, homepage, topics}'         # 適用の確認
gh api "search/repositories?q=topic:X+user:OWNER" --jq '.total_count'  # 索引反映の確認（数秒）
```

**自分の repo のメタデータ変更なので可逆**であり、外部ディレクトリへの申請（他者が管理する空間への
書き込み）とは審査面の有無でリスク構造が違う — 混同しない。
